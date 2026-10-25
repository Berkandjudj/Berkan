#!/usr/bin/env python3
"""Baut compositions/hud.html (Tag | Uhrzeit | Status-Pille, Messbalken) aus hud.json.

Aufruf: python3 -I build_hud.py PROJEKT_DIR        (liest PROJEKT_DIR/hud.json)

hud.json (alle Zeiten GLOBAL in Sekunden):
{
  "start": 11.0, "end": 49.05,               # sichtbar von/bis (= Host data-start/-duration)
  "label": "VORRÄTE", "pill": "⚡ STROM",
  "days": [ {"t": 11.0, "day": 1, "clock": "07:00", "pct": 100}, ... ],
  "alert": {"t": 36.6}                       # optional: Pille wird rot (z. B. Stromausfall)
}
Die Uhr tickt alle ~1,4 s eine Minute weiter. pct ≤ 15 → Balken rot, ≤ 40 → orange-Text.
"""
import json, os, sys

TICK = 1.4

CSS = """  <style>
    #root { position: absolute; inset: 0; pointer-events: none; }
    #hud-box { position: absolute; left: 52px; top: 196px; width: 520px; height: 142px; border-radius: 16px;
      background: rgba(16, 18, 24, 0.86); box-shadow: 0 8px 26px rgba(0,0,0,.45);
      font-family: "Oswald", sans-serif; font-weight: 700; color: var(--ink); }
    .hud-row { position: absolute; left: 22px; right: 22px; height: 60px; }
    #hud-r1 { top: 10px; } #hud-r2 { top: 76px; }
    .hud-slot { position: absolute; top: 0; height: 60px; line-height: 60px; font-size: 46px; }
    .hud-slot > span { position: absolute; left: 0; top: 0; white-space: nowrap; }
    #hud-day { left: 54px; width: 130px; color: var(--orange); }
    #hud-time { left: 212px; width: 130px; }
    #hud-sep { left: 186px; color: #737a88; font-size: 46px; }
    #hud-sun { position: absolute; left: 0; top: 8px; width: 44px; height: 44px; }
    #hud-pill { position: absolute; left: 352px; top: 10px; height: 40px; padding: 0 12px; border-radius: 8px;
      background: #3a3f4b; font-size: 28px; line-height: 40px; color: #c7ccd6; letter-spacing: 0.04em; white-space: nowrap; }
    #hud-lab { position: absolute; left: 0; top: 0; line-height: 52px; font-size: 30px; letter-spacing: 0.04em; color: #c7ccd6; }
    #hud-track { position: absolute; left: 150px; top: 18px; width: 200px; height: 18px; border-radius: 9px; background: #343945; overflow: hidden; }
    #hud-fill { position: absolute; left: 0; top: 0; width: 200px; height: 18px; border-radius: 9px; background: var(--orange); transform-origin: left center; }
    .hud-tick { position: absolute; top: -4px; width: 5px; height: 26px; border-radius: 2px; background: #e8412f; }
    #hud-pct { left: 370px; width: 110px; font-size: 40px; line-height: 52px; height: 52px; }
  </style>"""

SUN = """        <svg id="hud-sun" viewBox="0 0 44 44">
          <circle cx="22" cy="22" r="9" fill="#f4a62a" />
          <g stroke="#f4a62a" stroke-width="4" stroke-linecap="round">
            <line x1="22" y1="2" x2="22" y2="8" /><line x1="22" y1="36" x2="22" y2="42" /><line x1="2" y1="22" x2="8" y2="22" /><line x1="36" y1="22" x2="42" y2="22" />
            <line x1="8" y1="8" x2="12" y2="12" /><line x1="32" y1="32" x2="36" y2="36" /><line x1="8" y1="36" x2="12" y2="32" /><line x1="32" y1="12" x2="36" y2="8" />
          </g>
        </svg>"""


def add_min(clock, n):
    h, m = map(int, clock.split(":"))
    t = (h * 60 + m + n) % (24 * 60)
    return f"{t // 60:02d}:{t % 60:02d}"


def main():
    proj = sys.argv[1] if len(sys.argv) > 1 else "."
    cfg = json.load(open(os.path.join(proj, "hud.json"), encoding="utf-8"))
    t0, t1 = cfg["start"], cfg["end"]
    L = lambda t: round(t - t0, 3)
    days = cfg["days"]
    day_spans, time_spans, pct_spans, js = [], [], [], []
    clocks = []  # (id, start, end)
    for i, d in enumerate(days):
        ds, de = L(d["t"]), L(days[i + 1]["t"]) if i + 1 < len(days) else L(t1)
        hidden = '' if i == 0 else ' style="opacity: 0"'
        day_spans.append(f'<span id="hud-d{i}"{hidden}>TAG {d["day"]}</span>')
        pct_spans.append(f'<span id="hud-p{i}"{hidden}>{d["pct"]} %</span>')
        n, t = 0, ds
        while t < de - 0.05:
            cid = f"hud-t{len(clocks)}"
            te = min(de, t + TICK)
            clocks.append(cid)
            style = '' if len(clocks) == 1 else ' style="opacity: 0"'
            time_spans.append(f'<span id="{cid}"{style}>{add_min(d["clock"], n)}</span>')
            js.append(f'tl.set("#{cid}", {{ opacity: 1 }}, {round(t, 3)}); tl.set("#{cid}", {{ opacity: 0 }}, {round(te, 3)});')
            n += 1; t = te
        if i > 0:
            js.append(f'tl.set("#hud-d{i-1}", {{ opacity: 0 }}, {ds}); tl.set("#hud-d{i}", {{ opacity: 1 }}, {ds});')
            js.append(f'tl.set("#hud-p{i-1}", {{ opacity: 0 }}, {ds}); tl.set("#hud-p{i}", {{ opacity: 1 }}, {ds});')
            js.append(f'tl.fromTo("#hud-day", {{ scale: 1.35 }}, {{ scale: 1, duration: 0.25, ease: "back.out(2)", immediateRender: false }}, {ds});')
        pct = d["pct"]
        col = "#e8412f" if pct <= 15 else "#f4a62a"
        txt = "#e8412f" if pct <= 15 else ("#f4a62a" if pct <= 40 else "#f4efe4")
        js.append(f'tl.set("#hud-p{i}", {{ color: "{txt}" }}, {ds});')
        if i == 0:
            js.append(f'tl.set("#hud-fill", {{ scaleX: {max(pct, 1) / 100}, backgroundColor: "{col}" }}, 0);')
        else:
            js.append(f'tl.to("#hud-fill", {{ scaleX: {max(pct, 1) / 100}, backgroundColor: "{col}", duration: 0.6, ease: "power2.out" }}, {ds});')
    if cfg.get("alert"):
        ta = L(cfg["alert"]["t"])
        js.append(f'tl.to("#hud-pill", {{ backgroundColor: "#e8412f", color: "#ffffff", duration: 0.05, repeat: 5, yoyo: true }}, {ta});')
        js.append(f'tl.set("#hud-pill", {{ backgroundColor: "#e8412f", color: "#ffffff" }}, {round(ta + 0.35, 3)});')
        js.append(f'tl.set("#hud-sun", {{ opacity: 0.35 }}, {ta});')
    html = f"""<template>
{CSS}
  <div id="root" data-composition-id="hud" data-width="1080" data-height="1920">
    <div id="hud-box">
      <div id="hud-r1" class="hud-row">
{SUN}
        <div id="hud-day" class="hud-slot">{"".join(day_spans)}</div>
        <div id="hud-sep" class="hud-slot">|</div>
        <div id="hud-time" class="hud-slot">{"".join(time_spans)}</div>
        <div id="hud-pill">{cfg.get("pill", "⚡ STROM")}</div>
      </div>
      <div id="hud-r2" class="hud-row">
        <div id="hud-lab">{cfg.get("label", "VORRÄTE")}</div>
        <div id="hud-track" data-layout-allow-overflow>
          <div id="hud-fill"></div>
          <div class="hud-tick" style="left: 60px"></div><div class="hud-tick" style="left: 20px"></div>
        </div>
        <div id="hud-pct" class="hud-slot">{"".join(pct_spans)}</div>
      </div>
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.fromTo("#hud-box", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.3, ease: "power3.out" }}, 0.05);
    {chr(10).join("    " + j for j in js).strip()}
    window.__timelines["hud"] = tl;
  </script>
</template>
"""
    out = os.path.join(proj, "compositions", "hud.html")
    open(out, "w", encoding="utf-8").write(html)
    print(f"{out}: {len(days)} Tage, {len(clocks)} Uhrzeiten, Host: data-start={t0} data-duration={round(t1 - t0, 3)}")


if __name__ == "__main__":
    main()
