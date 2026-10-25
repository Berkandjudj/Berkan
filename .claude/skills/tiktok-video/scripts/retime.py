#!/usr/bin/env python3
"""Alle Szenen-Zeiten eines fertigen Projekts an eine neue Sprachaufnahme anpassen.

Aufruf: python3 -I retime.py PROJEKT_DIR ALT_timing.json NEU_timing.json [--tail 5.5]

Baut aus den Zeilen (alter Start/Ende → neuer Start/Ende) eine stückweise lineare Zeitabbildung f und wendet sie an auf:
  - index.html: Szenen-Hosts (data-start/-duration), HUD-Host, SFX-<audio> data-start, Root-Länge
  - compositions/*.html (außer captions/hud): data-start/-duration der Beats und GSAP-Positionen `}, 2.75);`
    (auch `2.75 + i * 0.3`); Tween-Dauern bleiben, nur Einsatzzeiten wandern mit.
  - hud.json: alle "t"-Werte, start/end
Danach: build_hud.py und build_captions.py neu laufen lassen. --tail = Länge der Outro-Szene nach der letzten Zeile.
"""
import argparse, bisect, glob, json, os, re


def mapping(old, new):
    o = {l["id"]: l for l in old["lines"]}
    pts = [(0.0, 0.0)]
    for l in new["lines"]:
        if l["id"] in o:
            pts += [(o[l["id"]]["start"], l["start"]), (o[l["id"]]["end"], l["end"])]
    pts = sorted(set(pts))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]

    def f(t):
        if t <= xs[0]:
            return ys[0] + (t - xs[0])
        if t >= xs[-1]:
            return ys[-1] + (t - xs[-1])
        i = bisect.bisect_right(xs, t) - 1
        x0, x1, y0, y1 = xs[i], xs[i + 1], ys[i], ys[i + 1]
        return y0 + (t - x0) * (y1 - y0) / (x1 - x0 or 1)
    return f


def r3(x):
    return f"{round(x, 3):g}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("old"); ap.add_argument("new")
    ap.add_argument("--tail", type=float, default=None)
    a = ap.parse_args()
    old, new = json.load(open(a.old)), json.load(open(a.new))
    f = mapping(old, new)
    idx_p = os.path.join(a.project, "index.html")
    idx = open(idx_p, encoding="utf-8").read()

    # Szenen-Hosts: id -> (alter Start, neuer Start)
    hosts = {}
    def host(m):
        tag = m.group(0)
        sid = re.search(r'data-composition-id="([^"]+)"', tag).group(1)
        s0 = float(re.search(r'data-start="([\d.]+)"', tag).group(1))
        d0 = float(re.search(r'data-duration="([\d.]+)"', tag).group(1))
        if sid == "captions":
            return tag
        s1, e1 = f(s0), f(s0 + d0)
        hosts[sid] = (s0, s1)
        tag = re.sub(r'data-start="[\d.]+"', f'data-start="{r3(s1)}"', tag)
        return re.sub(r'data-duration="[\d.]+"', f'data-duration="{r3(e1 - s1)}"', tag)
    idx = re.sub(r'<div id="[^"]+" data-composition-id="[^"]+" data-composition-src="[^"]+"[^>]*>', host, idx, flags=re.S)

    # Outro bis Videoende, Root-Länge
    order = sorted((v[1], k) for k, v in hosts.items() if k != "hud")
    last_id = order[-1][1]
    root_old = float(re.search(r'id="root"[^>]*?data-duration="([\d.]+)"', idx, re.S).group(1))
    last_s_new = hosts[last_id][1]
    tail = a.tail if a.tail else max(4.0, root_old - hosts[last_id][0])
    total = round(max(last_s_new + tail, new["duration"] + 2.5), 2)
    idx = re.sub(rf'(<div id="{last_id}" [^>]*?data-duration=")[\d.]+(")', rf'\g<1>{r3(total - last_s_new)}\2', idx, flags=re.S)
    idx = re.sub(r'data-duration="' + re.escape(f"{root_old:g}") + '"', f'data-duration="{r3(total)}"', idx)
    idx = re.sub(r'data-duration="' + re.escape(str(int(root_old))) + '"', f'data-duration="{r3(total)}"', idx)

    # SFX
    def sfx(m):
        tag = m.group(0)
        s0 = float(re.search(r'data-start="([\d.]+)"', tag).group(1))
        return re.sub(r'data-start="[\d.]+"', f'data-start="{r3(max(0, f(s0)))}"', tag)
    idx = re.sub(r'<audio id="sfx-[^>]*>', sfx, idx)
    open(idx_p, "w", encoding="utf-8").write(idx)

    # Szenen
    for p in glob.glob(os.path.join(a.project, "compositions", "*.html")):
        sid = os.path.basename(p)[:-5]
        if sid in ("captions", "hud") or sid not in hosts:
            continue
        s0, s1 = hosts[sid]
        loc = lambda t: f(s0 + t) - s1
        src = open(p, encoding="utf-8").read()

        def clip(m):
            tag = m.group(0)
            st = float(re.search(r'data-start="([\d.]+)"', tag).group(1))
            du = float(re.search(r'data-duration="([\d.]+)"', tag).group(1))
            n0, n1 = loc(st), loc(st + du)
            tag = re.sub(r'data-start="[\d.]+"', f'data-start="{r3(max(0, n0))}"', tag)
            return re.sub(r'data-duration="[\d.]+"', f'data-duration="{r3(n1 - max(0, n0))}"', tag)
        src = re.sub(r'<[^>]*class="clip"[^>]*data-start="[\d.]+" data-duration="[\d.]+"[^>]*>', clip, src)

        def pos(m):
            return m.group(1) + r3(max(0, loc(float(m.group(2))))) + m.group(3)
        src = re.sub(r'(\},\s*)(\d+(?:\.\d+)?)(\s*(?:\+\s*i\s*\*\s*[\d.]+)?\s*\);)', pos, src)
        src = re.sub(r'(\[)([\d.]+(?:,\s*[\d.]+)*)(\]\.forEach\(\(t\))',
                     lambda m: m.group(1) + ", ".join(r3(loc(float(x))) for x in m.group(2).split(",")) + m.group(3), src)
        open(p, "w", encoding="utf-8").write(src)

    # HUD
    hp = os.path.join(a.project, "hud.json")
    if os.path.exists(hp):
        h = json.load(open(hp, encoding="utf-8"))
        h["start"], h["end"] = round(f(h["start"]), 3), round(f(h["end"]), 3)
        for d in h["days"]:
            d["t"] = round(f(d["t"]), 3)
        if h.get("alert"):
            h["alert"]["t"] = round(f(h["alert"]["t"]), 3)
        json.dump(h, open(hp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"neu getimt: Szenen {len(hosts)}, Videolänge {total} s")
    for k, (o_, n_) in sorted(hosts.items(), key=lambda x: x[1][1]):
        print(f"  {k:8s} {o_:6.2f} → {n_:6.2f}")


if __name__ == "__main__":
    main()
