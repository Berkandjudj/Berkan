#!/usr/bin/env python3
"""Baut compositions/captions.html (Karaoke-Untertitel im Referenz-Look) aus assets/timing.json.

Aufruf: python3 -I build_captions.py PROJEKT_DIR [--max-words 3] [--max-chars 18] [--y 1365]

Look: dunkle Box mit oranger Oberkante, Oswald 700 in Versalien.
  kommendes Wort = grau · aktives Wort = gelb + Unterstrich · gesprochen = weiß · *Keyword* = rot
"""
import argparse, html, json, os, re

LEGENDE_CSS = """
    #root {{ position: absolute; inset: 0; pointer-events: none; }}
    .cap-row {{ position: absolute; left: 60px; width: 960px; top: {top}px; text-align: center; overflow: visible; }}
    .cap-box {{ display: inline-block; position: relative; font-family: "Montserrat", sans-serif; font-weight: 800;
      font-size: {size}px; line-height: 1.08; text-transform: uppercase; letter-spacing: 0.01em; color: #f4f1ea;
      text-shadow: 0 0 2px #000, 0 3px 0 rgba(0,0,0,.85), 0 0 24px rgba(0,0,0,.75), 0 0 6px rgba(0,0,0,.9); }}
    .cap-w {{ display: inline-block; position: relative; margin: 0 0.1em; color: #f4f1ea; }}
    .cap-w .ul {{ display: none; }}
    .cap-box {{ background: none; box-shadow: none; padding: 0; border-radius: 0; }}
    .cap-box::before {{ display: none; }}
"""

TEMPLATE = """<template>
  <style>
    #root {{ position: absolute; inset: 0; pointer-events: none; }}
    .cap-row {{ position: absolute; left: 0; width: 1080px; top: {top}px; text-align: center; overflow: visible; }}
    .cap-box {{ display: inline-block; position: relative; padding: 10px 24px 14px; border-radius: 10px;
      background: rgba(17, 19, 25, 0.88); box-shadow: 0 10px 30px rgba(0,0,0,.45);
      font-family: "Oswald", sans-serif; font-weight: 700; font-size: {size}px; line-height: 1.12;
      text-transform: uppercase; letter-spacing: 0.01em; white-space: nowrap; }}
    .cap-box::before {{ content: ""; position: absolute; left: 14%; right: 14%; top: 0; height: 4px;
      border-radius: 2px; background: var(--orange, #f4a62a); }}
    .cap-w {{ display: inline-block; position: relative; color: #8e939d; margin: 0 0.12em; }}
    .cap-w .ul {{ position: absolute; left: 0; right: 0; bottom: 0.02em; height: 5px; border-radius: 3px;
      background: var(--yellow, #f7c548); transform-origin: left center; transform: scaleX(0); }}
{legende}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920" data-layout-allow-caption-zone>
{groups}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    const G = {data};
    const LEG = {legjs};
    const WHITE = "#f4efe4", YELLOW = LEG ? "#f4f1ea" : "#f7c548", RED = LEG ? "#f4f1ea" : "#ef4a36", GREY = LEG ? "#f4f1ea" : "#8e939d";
    G.forEach((g) => {{
      const box = "#" + g.id + " .cap-box";
      tl.fromTo(box, {{ opacity: 0, scale: 0.9, y: 14 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.14, ease: "back.out(2.2)" }}, g.start);
      g.words.forEach((w, i) => {{
        const el = "#" + w.id, ul = "#" + w.id + " .ul";
        tl.set(el, {{ color: GREY }}, g.start);
        tl.to(el, {{ color: w.key ? RED : YELLOW, duration: 0.06 }}, w.start);
        tl.fromTo(ul, {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.12, ease: "power2.out" }}, w.start);
        tl.set(ul, {{ backgroundColor: w.key ? RED : YELLOW }}, w.start);
        if (i < g.words.length - 1) {{
          const nxt = g.words[i + 1].start;
          tl.to(el, {{ color: w.key ? RED : WHITE, duration: 0.06 }}, nxt);
          tl.to(ul, {{ scaleX: 0, duration: 0.08 }}, nxt);
        }}
      }});
      tl.to(box, {{ opacity: 0, duration: 0.08, ease: "power2.in" }}, g.end - 0.08);
      tl.set("#" + g.id, {{ visibility: "hidden" }}, g.end);
    }});
    window.__timelines["captions"] = tl;
  </script>
</template>
"""


def chunk_phrase(words, max_words, max_chars):
    """Teilt eine Phrase in möglichst gleich große Gruppen (keine Waisenwörter)."""
    from itertools import combinations
    n = len(words)
    chars = lambda g: sum(len(w["text"]) + 1 for w in g) - 1
    best = None
    for k in range(1, n + 1):
        for cuts in combinations(range(1, n), k - 1):
            b = (0,) + cuts + (n,)
            gs = [words[b[i]:b[i + 1]] for i in range(k)]
            if any(len(g) > max_words or chars(g) > max_chars for g in gs):
                continue
            score = (sum(len(g) == 1 for g in gs), max(chars(g) for g in gs))
            if best is None or score < best[0]:
                best = (score, gs)
        if best:
            return best[1]
    return [[w] for w in words]


def group_words(lines, max_words, max_chars):
    groups = []
    for line in lines:
        phrase = []
        for w in line["words"]:
            phrase.append(w)
            if re.search(r"[.!?,;:]$", w["text"]):
                groups += chunk_phrase(phrase, max_words, max_chars); phrase = []
        if phrase:
            groups += chunk_phrase(phrase, max_words, max_chars)
    return groups


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--max-words", type=int, default=3)
    ap.add_argument("--max-chars", type=int, default=18)
    ap.add_argument("--y", type=int, default=1365, help="vertikale Mitte der Untertitel")
    ap.add_argument("--size", type=int, default=66)
    ap.add_argument("--style", choices=["szenario", "legende"], default="szenario",
                    help="szenario = Box + Karaoke (Bunker-Stil), legende = weiße Schrift ohne Box (zeitreisehaus-Stil)")
    ap.add_argument("--key-color", default="", help="nur legende: Farbe der *Schlüsselwörter* (Standard weiß), z. B. #ffd25a")
    ap.add_argument("--skip", default="", help="Zeilen-IDs ohne Untertitel (z. B. schwarze Texttafeln), kommagetrennt")
    a = ap.parse_args()
    timing = json.load(open(os.path.join(a.project, "assets", "timing.json"), encoding="utf-8"))
    skip = set(x for x in a.skip.split(",") if x)
    if a.style == "legende":
        a.y = a.y if a.y != 1365 else 1210
        a.size = a.size if a.size != 66 else 64
    groups = group_words([l for l in timing["lines"] if l["id"] not in skip], a.max_words, a.max_chars)
    data, markup = [], []
    for gi, g in enumerate(groups):
        gid = f"cap-g{gi}"
        start = round(max(0.1, g[0]["start"] - 0.06), 3)
        nxt = groups[gi + 1][0]["start"] - 0.06 if gi + 1 < len(groups) else g[-1]["end"] + 0.6
        end = round(min(nxt, g[-1]["end"] + 0.45), 3)
        words = []
        spans = []
        for wi, w in enumerate(g):
            wid = f"{gid}-w{wi}"
            text = w["text"].rstrip(",;:") if not w["text"].endswith(("?", "!")) else w["text"]
            text = text.rstrip(".") if text.endswith(".") and not text.endswith("..") else text
            spans.append(f'<span id="{wid}" class="cap-w">{html.escape(text)}<i class="ul"></i></span>')
            words.append({"id": wid, "start": round(w["start"], 3), "key": bool(w.get("key"))})
        dur = round(end - start, 3)
        markup.append(f'    <div id="{gid}" class="cap-row clip" data-start="{start}" data-duration="{dur}" data-track-index="0">'
                      f'<div class="cap-box">{"".join(spans)}</div></div>')
        data.append({"id": gid, "start": start, "end": end, "words": words})
    top = a.y - int(a.size * 0.75)
    leg = a.style == "legende"
    out = TEMPLATE.format(top=top, size=a.size, groups="\n".join(markup),
                          data=json.dumps(data, ensure_ascii=False),
                          legende=LEGENDE_CSS.format(top=top, size=a.size) if leg else "",
                          legjs="true" if leg else "false")
    if leg and a.key_color:
        out = out.replace('RED = LEG ? "#f4f1ea"', f'RED = LEG ? "{a.key_color}"')
    os.makedirs(os.path.join(a.project, "compositions"), exist_ok=True)
    path = os.path.join(a.project, "compositions", "captions.html")
    open(path, "w", encoding="utf-8").write(out)
    print(f"{path}: {len(groups)} Gruppen")
    for d, g in zip(data, groups):
        print(f"  {d['start']:6.2f}-{d['end']:6.2f}  {' '.join(w['text'] for w in g)}")


if __name__ == "__main__":
    main()
