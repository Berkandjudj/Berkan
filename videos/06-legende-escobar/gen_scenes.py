# Erzeugt alle Szenen (compositions/*.html) und scenes.json aus assets/timing.json.
# Neue Stimme → place_voice.py → dieses Skript → svg_parts.py → build_index.py → build_captions.py. Kein retime nötig.
import json, random, os, sys

P = os.path.dirname(os.path.abspath(__file__))
tm = json.load(open(os.path.join(P, "assets/timing.json")))
L = {l["id"]: l for l in (tm["lines"] if isinstance(tm, dict) else tm)}


def w(lid, i):
    return L[lid]["words"][i]["start"]


def st(lid):
    return round(L[lid]["start"] - 0.1, 2)


r2 = lambda x: f"{x:.2f}"

# ---- Szenenplan ----
order = [("hook", 0.0), ("cards", st("card1")), ("herkunft", st("s1")), ("kartell", st("s4")), ("reich", st("s7")),
         ("krieg", st("s9")), ("gefaengnis", st("s10")), ("ende", st("s12")), ("reveal", st("reveal"))]
TOTAL = round(L["reveal"]["end"] + 3.3, 2)
SC = {}
for i, (n, s) in enumerate(order):
    e = order[i + 1][1] if i + 1 < len(order) else TOTAL
    SC[n] = (s, round(e - s, 2))


def loc(scene, t):
    return round(t - SC[scene][0], 2)


def beats(scene, starts):
    """starts: globale Startzeiten der Beats (erster = Szenenstart) → [(lokaler Start, Dauer)]"""
    s0, d = SC[scene]
    loc_ = [round(x - s0, 2) for x in starts] + [d]
    return [(loc_[i], round(loc_[i + 1] - loc_[i], 2)) for i in range(len(starts))]


def dots(rng, n, x0, x1, y0, y1, cols, r0, r1, cls, op=(0.5, 1.0)):
    out = []
    for _ in range(n):
        out.append(f'<circle class="{cls}" cx="{rng.uniform(x0, x1):.0f}" cy="{rng.uniform(y0, y1):.0f}" '
                   f'r="{rng.uniform(r0, r1):.1f}" fill="{rng.choice(cols)}" opacity="{rng.uniform(*op):.2f}"/>')
    return "\n".join(out)


def comp(cid, css, body, js):
    return f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; background: #05080b; }}
    .lt {{ font-family: "Montserrat", sans-serif; font-weight: 800; }}
    .beat {{ position: absolute; inset: 0; overflow: hidden; }}
{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="1080" data-height="1920">
{body}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{cid}"] = tl;
  </script>
</template>
'''


def beat(bid, s, d, svg, extra=""):
    return f'''    <div id="{bid}" class="beat clip" data-start="{r2(s)}" data-duration="{r2(d)}" data-track-index="0">
      <div id="{bid}-cam" class="cam">
        <svg class="full" viewBox="0 0 1080 1920">
{svg}
        </svg>
      </div>
{extra}
    </div>'''


def title(id_, html, top=330, size=130, extra=""):
    return f'      <div id="{id_}" class="title lt" style="top: {top}px; font-size: {size}px;{extra}">{html}</div>'


def push(sel, s, d, a=1.0, b=1.08, y0=0, y1=-20):
    return f'    tl.fromTo("{sel}", {{ scale: {a}, y: {y0} }}, {{ scale: {b}, y: {y1}, duration: {r2(d)}, ease: "none" }}, {r2(s)});'


def pop_in(sel, t, dur=0.3):
    return f'    tl.fromTo("{sel}", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: {dur}, ease: "power3.out" }}, {r2(t)});'


def slam(sel, t):
    return f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 1.7, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.2, ease: "power4.in" }}, {r2(t)});'


files = {}

# =========================== HOOK: eigenes Gefängnis über der Stadt ===========================
rng = random.Random(1)
d = SC["hook"][1]
svg = f'''          <defs>
            <linearGradient id="h-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#03060d" /><stop offset="0.45" stop-color="#0c2532" /><stop offset="1" stop-color="#1b4644" /></linearGradient>
            <radialGradient id="h-flood" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#e9fff6" stop-opacity="0.9" /><stop offset="1" stop-color="#9ff0dc" stop-opacity="0" /></radialGradient>
            <radialGradient id="h-warm" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffb35c" stop-opacity="0.7" /><stop offset="1" stop-color="#ff6a1f" stop-opacity="0" /></radialGradient>
            <filter id="h-neon" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
          </defs>
          <rect width="1080" height="1920" fill="url(#h-sky)" />
          {dots(rng, 50, 0, 1080, 0, 620, ["#dff6ff", "#ffffff"], 1.2, 3.2, "h-star", (0.3, 0.9))}
          <path d="M0 900 L140 820 L280 870 L420 760 L540 700 L700 780 L860 720 L1080 830 L1080 1920 L0 1920 Z" fill="#0a1a22" />
          <path d="M40 1090 Q290 860 450 805 L650 795 Q830 860 1060 1090 Z" fill="#0e242b" />
          <!-- Gefängnis auf dem Berg -->
          <g>
            <rect x="380" y="718" width="300" height="86" fill="#1b2c31" />
            <path d="M370 722 L530 690 L690 722 Z" fill="#142226" />
            <g fill="#ffc56b">{"".join(f'<rect class="h-win" x="{400 + i * 34}" y="748" width="16" height="22" />' for i in range(8))}</g>
            <rect x="338" y="640" width="40" height="164" fill="#16252a" /><rect x="324" y="618" width="68" height="30" fill="#1f3338" />
            <circle id="h-tl" cx="358" cy="612" r="7" fill="#ff5a4a" />
            <path d="M300 806 H780" stroke="#2c4248" stroke-width="5" />
            <g stroke="#2c4248" stroke-width="4">{"".join(f'<line x1="{x}" y1="806" x2="{x}" y2="782" />' for x in range(300, 781, 30))}</g>
          </g>
          <ellipse id="h-fglow" cx="790" cy="836" rx="270" ry="120" fill="url(#h-flood)" opacity="0" />
          <polygon points="650,812 910,812 965,884 600,884" fill="#1f6a45" />
          <g fill="none" stroke="#dff6e8" stroke-width="3" opacity="0.7"><polygon points="660,818 900,818 950,878 612,878" /><line x1="780" y1="818" x2="781" y2="878" /></g>
          <g fill="#0f1a1d"><rect x="626" y="700" width="8" height="112" /><rect x="926" y="700" width="8" height="112" /></g>
          <g><rect class="h-lamp" x="606" y="690" width="48" height="18" rx="4" fill="#f2fff9" opacity="0.25" /><rect class="h-lamp" x="906" y="690" width="48" height="18" rx="4" fill="#f2fff9" opacity="0.25" /></g>
          <g id="h-bar" opacity="0.12" filter="url(#h-neon)">
            <rect x="420" y="660" width="120" height="44" rx="8" fill="#14060a" stroke="#ff4d6d" stroke-width="4" />
            <text x="480" y="695" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="34" fill="#ff7088">BAR</text>
          </g>
          <!-- Stadt im Tal -->
          <ellipse cx="540" cy="1310" rx="760" ry="260" fill="url(#h-warm)" opacity="0.55" />
          {dots(rng, 260, 0, 1080, 1100, 1480, ["#ffb35c", "#ffd28a", "#f7c548", "#ff8a3c"], 2, 5, "h-city", (0.35, 0.9))}
          <!--@fog id="h-fog" y="1160" color="#bff5e6" opacity="0.12" seed="4"-->
          <path d="M0 1600 Q300 1560 540 1620 Q800 1680 1080 1600 L1080 1920 L0 1920 Z" fill="#04070a" />
          <!--@man id="h-m" x="790" y="1850" s="0.72" shirt="#e9e2d0" pants="#22262f" rim="#ffb35c"-->
          <!--@embers id="h-emb" n="28" seed="3" y0="1000" y1="1900" color="#ffd28a" r="3"-->'''
fb, bar, blick = w("hook1", 8), w("hook1", 9), w("hook1", 11)
js = "\n".join([
    f'    tl.fromTo("#h-a-cam", {{ scale: 1.14, y: 40 }}, {{ scale: 1.0, y: 0, duration: {r2(d)}, ease: "power1.out" }}, 0);',
    f'    tl.fromTo(".h-star", {{ opacity: 0.2 }}, {{ opacity: 0.9, duration: 0.5, repeat: 9, yoyo: true, stagger: 0.04 }}, 0);',
    f'    tl.fromTo("#h-tl", {{ opacity: 0.2 }}, {{ opacity: 1, duration: 0.4, repeat: 11, yoyo: true }}, 0);',
    f'    tl.fromTo("#h-fglow", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25, ease: "power2.out" }}, {r2(fb - 0.05)});',
    f'    tl.fromTo(".h-lamp", {{ opacity: 0.25 }}, {{ opacity: 1, duration: 0.2 }}, {r2(fb - 0.05)});',
    f'    tl.fromTo("#h-bar", {{ opacity: 0.12 }}, {{ opacity: 1, duration: 0.07, repeat: 4, yoyo: true }}, {r2(bar - 0.05)});',
    f'    tl.fromTo(".h-city", {{ opacity: 0.25 }}, {{ opacity: 1, duration: 0.3, stagger: {{ each: 0.003 }} }}, {r2(blick - 0.1)});',
    f'    tl.fromTo(".h-emb-p", {{ y: 0 }}, {{ y: -320, duration: {r2(d)}, ease: "none" }}, 0);',
])
files["hook"] = comp("hook", "", beat("h-a", 0, d, svg), js)

# =========================== CARDS ===========================
s0, d = SC["cards"]
k2 = loc("cards", L["card2"]["start"] - 0.08)
anruf = loc("cards", w("card2", 4))
files["cards"] = f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; background: #000; }}
    .k-card {{ position: absolute; left: 90px; width: 900px; top: 860px; text-align: center;
      font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 76px; line-height: 1.12;
      text-transform: uppercase; color: #f4f1ea; text-shadow: 0 0 18px rgba(255,255,255,.08); }}
    .k-card .r {{ color: #e8412f; display: inline-block; }}
  </style>
  <div id="root" data-composition-id="cards" data-width="1080" data-height="1920">
    <div id="k-1" class="k-card clip" data-start="0.05" data-duration="{r2(k2 - 0.05)}" data-track-index="0">Doch am Ende</div>
    <div id="k-2" class="k-card clip" data-start="{r2(k2)}" data-duration="{r2(d - k2)}" data-track-index="0">verriet ihn ein<br />einziger <span class="r">Anruf</span></div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.fromTo("#k-1", {{ opacity: 0, scale: 0.94 }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: "power2.out" }}, 0.05);
    tl.fromTo("#k-2", {{ opacity: 0, scale: 0.94 }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: "power2.out" }}, {r2(k2)});
    tl.fromTo("#k-2 .r", {{ scale: 1 }}, {{ scale: 1.12, duration: 0.12, repeat: 3, yoyo: true, ease: "power2.out" }}, {r2(anruf)});
    window.__timelines["cards"] = tl;
  </script>
</template>
'''

# =========================== HERKUNFT: 1949, Eltern, Friedhof ===========================
rng = random.Random(2)
(a, ad), (b, bd), (c, cd) = beats("herkunft", [SC["herkunft"][0], st("s2"), st("s3")])
ridge = lambda y, amp, col, seed: (lambda R: f'<path d="M0 {y} ' + " ".join(f"L{x} {y - R.uniform(0, amp):.0f}" for x in range(60, 1141, 90)) + f' L1080 1920 L0 1920 Z" fill="{col}" />')(random.Random(seed))
svgA = f'''          <defs>
            <linearGradient id="c-a-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#10263a" /><stop offset="0.5" stop-color="#4a5a6a" /><stop offset="0.62" stop-color="#e88a4a" /><stop offset="1" stop-color="#f4b56a" /></linearGradient>
            <radialGradient id="c-a-sun" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff2c8" stop-opacity="1" /><stop offset="0.3" stop-color="#ffd28a" stop-opacity="0.7" /><stop offset="1" stop-color="#ff8a3c" stop-opacity="0" /></radialGradient>
          </defs>
          <rect width="1080" height="1920" fill="url(#c-a-sky)" />
          <g id="c-a-sun"><circle cx="540" cy="1000" r="420" fill="url(#c-a-sun)" /><circle cx="540" cy="1000" r="96" fill="#fff0c4" /></g>
          {ridge(1060, 220, "#3c6a5a", 11)}
          {ridge(1180, 180, "#2a5446", 12)}
          {ridge(1320, 150, "#1d4034", 13)}
          {ridge(1480, 110, "#132c24", 14)}
          <g fill="#0e241c">{"".join(f'<ellipse class="c-a-bush" cx="{x}" cy="{y}" rx="38" ry="26" />' for y in range(1620, 1921, 70) for x in range(30 + (y // 70 % 2) * 40, 1081, 90))}</g>
          <g transform="translate(720 1470)"><rect x="-90" y="-90" width="180" height="90" fill="#e9dcc0" /><path d="M-110 -86 L0 -150 L110 -86 Z" fill="#b5442e" />
            <rect x="-30" y="-56" width="34" height="56" fill="#5a3a22" /><rect x="30" y="-70" width="36" height="30" fill="#ffd28a" /></g>
          <g id="c-a-birds" fill="none" stroke="#1d2a30" stroke-width="5" stroke-linecap="round">
            <path d="M200 620 q14 -12 28 0 q14 -12 28 0" /><path d="M280 580 q12 -10 24 0 q12 -10 24 0" /><path d="M760 660 q14 -12 28 0 q14 -12 28 0" /></g>
          <!--@fog id="c-a-fog" y="1300" color="#ffe2b8" opacity="0.18" seed="5"-->'''
svgB = f'''          <defs>
            <linearGradient id="c-b-bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a1a14" /><stop offset="0.6" stop-color="#7a4a28" /><stop offset="1" stop-color="#2a1a10" /></linearGradient>
            <radialGradient id="c-b-glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffb35c" stop-opacity="0.6" /><stop offset="1" stop-color="#ff6a1f" stop-opacity="0" /></radialGradient>
          </defs>
          <rect width="1080" height="1920" fill="url(#c-b-bg)" />
          <circle cx="540" cy="1100" r="620" fill="url(#c-b-glow)" />
          <rect x="0" y="1560" width="1080" height="360" fill="#24160e" />
          <!-- Tafel der Mutter -->
          <rect x="580" y="560" width="420" height="250" rx="6" fill="#6b4f2a" /><rect x="596" y="576" width="388" height="218" fill="#1f3a2e" />
          <text x="790" y="690" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="72" fill="#e9e6da" opacity="0.85">A B C</text>
          <path d="M640 740 q60 -20 120 0 t120 0" stroke="#e9e6da" stroke-width="5" fill="none" opacity="0.6" />
          <!-- Feldhacke des Vaters -->
          <g transform="translate(460 1380)"><g id="c-b-hoe"><path d="M0 0 L60 -420" stroke="#6b4f2a" stroke-width="14" stroke-linecap="round" /><path d="M48 -430 l70 18 l-8 30 l-66 -12 z" fill="#8d93a1" /></g></g>
          <!--@person id="c-b-f" x="320" y="1580" s="1.0" jacket="#6b5a2a" pants="#3a3428" hair="#1e140c" skin="#c98d62" hat="#d8b46a" beard="mustache"-->
          <!--@person id="c-b-m" x="790" y="1580" s="1.0" jacket="#8a3a4a" pants="#2a2230" hair="#1e140c" skin="#c98d62" style="long" mood="happy"-->
          <!--@embers id="c-b-dust" n="20" seed="9" y0="500" y1="1500" color="#ffd28a" r="3"-->'''
graves = []
for row, (yy, sc, col) in enumerate([(1180, 0.55, "#2a333c"), (1340, 0.75, "#36414b"), (1560, 1.0, "#46525d")]):
    for i, x in enumerate(range(80 + row * 30, 1081, int(220 * sc))):
        if row == 2 and i == 3:
            graves.append(f'<rect x="{x - 50}" y="{yy - 10}" width="100" height="22" fill="#1a120c" />')
            continue
        hgt = 150 * sc
        graves.append(f'<g transform="translate({x} {yy}) scale({sc})"><path d="M-46 0 V-120 q46 -46 92 0 V0 Z" fill="{col}" /><path d="M-46 -120 q46 -46 92 0" stroke="#9fb4c4" stroke-width="4" fill="none" opacity=".5" />'
                      f'<rect x="-6" y="-110" width="12" height="60" fill="#1d252c" /><rect x="-24" y="-92" width="48" height="12" fill="#1d252c" /></g>')
svgC = f'''          <defs>
            <linearGradient id="c-c-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#03060d" /><stop offset="0.6" stop-color="#132a3a" /><stop offset="1" stop-color="#1e3a44" /></linearGradient>
            <radialGradient id="c-c-moon" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#e9f2ff" stop-opacity="0.8" /><stop offset="1" stop-color="#9fc4e0" stop-opacity="0" /></radialGradient>
          </defs>
          <rect width="1080" height="1920" fill="url(#c-c-sky)" />
          <circle id="c-c-glow" cx="820" cy="420" r="300" fill="url(#c-c-moon)" /><circle cx="820" cy="420" r="70" fill="#eef4ff" />
          <path d="M0 1120 q80 -120 160 -10 q60 -160 160 -20 q90 -90 170 10 q80 -150 180 -10 q100 -120 200 0 q80 -80 210 -20 V1920 H0 Z" fill="#0a141a" />
          <rect x="0" y="1160" width="1080" height="760" fill="#101c22" />
          {"".join(graves)}
          <!--@fog id="c-c-fog" y="1450" color="#cfe3ff" opacity="0.16" seed="6"-->
          <g id="c-c-walk">
            <!--@man id="c-c-t" x="420" y="1820" s="0.62" pose="walk" shirt="#2a3440" pants="#161a22" rim="#cfe3ff"-->
            <g transform="translate(540 1560) rotate(10)"><path d="M-34 0 V-80 q34 -34 68 0 V0 Z" fill="#6b7682" /><rect x="-4" y="-74" width="8" height="40" fill="#2a333c" /></g>
          </g>'''
body = "\n".join([beat("c-a", a, ad, svgA, title("c-a-title", "1949", size=150)), beat("c-b", b, bd, svgB), beat("c-c", c, cd, svgC)])
js = "\n".join([
    push("#c-a-cam", a, ad), f'    tl.fromTo("#c-a-sun", {{ y: 60 }}, {{ y: 0, duration: {r2(ad)}, ease: "power1.out" }}, {r2(a)});',
    f'    tl.fromTo("#c-a-birds", {{ x: -60 }}, {{ x: 140, duration: {r2(ad)}, ease: "none" }}, {r2(a)});',
    pop_in("#c-a-title", loc("herkunft", w("s1", 2)) - 0.05),
    f'    tl.fromTo("#c-b-cam", {{ scale: 1.08 }}, {{ scale: 1.0, duration: {r2(bd)}, ease: "power1.out" }}, {r2(b)});',
    f'    tl.fromTo("#c-b-hoe", {{ rotation: -8, transformOrigin: "50% 100%" }}, {{ rotation: 6, duration: 0.6, repeat: 3, yoyo: true, ease: "sine.inOut" }}, {r2(b)});',
    f'    tl.fromTo(".c-b-dust-p", {{ y: 0 }}, {{ y: -140, duration: {r2(bd)}, ease: "none" }}, {r2(b)});',
    push("#c-c-cam", c, cd, 1.0, 1.07, 0, -10),
    f'    tl.fromTo("#c-c-walk", {{ x: -40 }}, {{ x: 50, duration: {r2(cd)}, ease: "none" }}, {r2(c)});',
    f'    tl.fromTo("#c-c-glow", {{ opacity: 0.7 }}, {{ opacity: 1, duration: 0.8, repeat: 3, yoyo: true, ease: "sine.inOut" }}, {r2(c)});',
])
files["herkunft"] = comp("herkunft", "", body, js)

# =========================== KARTELL: Flugzeug, Polizeifoto, Karte ===========================
rng = random.Random(3)
(a, ad), (b, bd), (c, cd) = beats("kartell", [SC["kartell"][0], st("s5"), st("s6")])
plane = '''<path d="M-120 0 q20 -26 150 -22 l60 -40 h24 l-24 46 q30 6 30 16 q0 10 -30 14 l24 46 h-24 l-60 -40 q-130 4 -150 -20 z" fill="#d9dde2" />
              <path d="M-120 0 q20 -26 150 -22 l4 24 q-130 18 -154 -2 z" fill="#aab2ba" /><rect x="-130" y="-34" width="18" height="40" fill="#e8412f" />
              <g fill="#3a5a7a"><circle cx="-40" cy="-6" r="7" /><circle cx="-14" cy="-8" r="7" /><circle cx="12" cy="-9" r="7" /></g>'''
svgA = f'''          <defs>
            <linearGradient id="m-a-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#02070a" /><stop offset="0.6" stop-color="#0f3236" /><stop offset="1" stop-color="#1b4a40" /></linearGradient>
            <radialGradient id="m-a-moon" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#e9fff6" stop-opacity="0.7" /><stop offset="1" stop-color="#9ff0dc" stop-opacity="0" /></radialGradient>
          </defs>
          <rect width="1080" height="1920" fill="url(#m-a-sky)" />
          <circle cx="300" cy="700" r="320" fill="url(#m-a-moon)" /><circle cx="300" cy="700" r="60" fill="#effff8" />
          <path d="M0 1240 q120 -140 240 -30 q100 -120 220 -10 q120 -160 260 0 q120 -110 360 10 V1920 H0 Z" fill="#071a14" />
          <polygon points="470,1260 610,1260 1000,1920 80,1920" fill="#3a2a1c" />
          <g>{"".join(f'<circle class="m-a-rl" cx="{540 + sgn * (70 + (yy - 1260) * 0.7):.0f}" cy="{yy}" r="{4 + (yy - 1260) / 80:.1f}" fill="#ffd28a" />' for yy in range(1290, 1921, 90) for sgn in (-1, 1))}</g>
          <g fill="#04100c">
            <path d="M0 1920 V1000 q60 30 80 140 q30 -120 120 -150 q-40 100 -30 230 q60 -60 130 -40 q-80 40 -100 180 L260 1920 Z" />
            <path d="M1080 1920 V960 q-70 40 -90 150 q-40 -120 -130 -140 q50 110 40 240 q-70 -50 -140 -30 q90 40 110 190 L820 1920 Z" /></g>
          <g transform="translate(200 1620)">{"".join(f'<g transform="translate({dx} {dy})"><rect x="-60" y="-50" width="120" height="70" rx="6" fill="#8a6a42" /><path d="M-60 -16 H60 M0 -50 V20" stroke="#5a4428" stroke-width="8" /></g>' for dx, dy in [(0, 0), (130, 0), (65, -74), (260, 10)])}</g>
          <g transform="translate(300 1330)"><g id="m-a-plane">{plane}</g></g>
          <!--@fog id="m-a-fog" y="1250" color="#bff5e6" opacity="0.12" seed="8"-->'''
heights = "".join(f'<line x1="0" y1="{y}" x2="1080" y2="{y}" stroke="#c9d2dc" stroke-width="3" opacity=".35" /><text x="40" y="{y - 10}" font-family="Montserrat" font-weight="800" font-size="28" fill="#c9d2dc" opacity=".55">{200 - (y - 560) // 6}</text>' for y in range(560, 1561, 120))
mug = 'x="540" y="1660" s="1.25" jacket="#d9d2c0" pants="#2a2f3b" hair="#1a1210" skin="#c98d62" style="curly"'
svgB = f'''          <rect width="1080" height="1920" fill="#4a5462" />
          {heights}
          <rect x="0" y="1560" width="1080" height="360" fill="#2a3038" />
          <!--@person id="m-b-p1" {mug} mood="neutral"-->
          <!--@person id="m-b-p2" {mug} mood="happy"-->
          <g><rect x="370" y="1270" width="340" height="150" rx="6" fill="#14161c" />
            <text x="540" y="1312" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="28" fill="#c9d2dc">MEDELLÍN</text>
            <text x="540" y="1396" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="78" fill="#f4f1ea">1976</text></g>'''
na = "M120 220 L360 150 L640 170 L900 230 L960 360 L860 470 L800 640 L720 720 L690 820 L620 860 L560 900 L470 860 L380 760 L300 640 L200 520 L130 400 Z"
ca = "M560 900 L620 950 L680 1030 L720 1110 L700 1140 L640 1080 L580 1000 L540 940 Z"
sa = "M700 1140 L820 1180 L940 1290 L960 1420 L900 1560 L820 1700 L760 1860 L730 1920 L680 1920 L660 1760 L620 1580 L600 1400 L620 1260 Z"
co = "M700 1140 L748 1150 L800 1172 L812 1210 L836 1256 L800 1290 L770 1334 L726 1318 L690 1336 L652 1310 L628 1262 L660 1200 Z"
routes = [((720, 1230), (520, 560), (380, 980)), ((720, 1230), (700, 640), (860, 900)), ((720, 1230), (360, 600), (300, 1000))]
paths = "".join(f'<path class="m-c-rt" d="M{s[0]} {s[1]} Q{q[0]} {q[1]} {e[0]} {e[1]}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" />' for s, e, q in routes)
planes = "".join(f'<g transform="translate({s[0]} {s[1]})"><g id="m-c-pl{i}"><path d="M0 -22 L14 10 L0 4 L-14 10 Z" fill="#f7c548" /></g></g>' for i, (s, e, q) in enumerate(routes))
svgC = f'''          <defs><linearGradient id="m-c-sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#071a24" /><stop offset="1" stop-color="#0d2e3a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#m-c-sea)" />
          <g stroke="#1d4a56" stroke-width="2" opacity=".5">{"".join(f'<line x1="{x}" y1="0" x2="{x}" y2="1920" />' for x in range(0, 1081, 120))}{"".join(f'<line x1="0" y1="{y}" x2="1080" y2="{y}" />' for y in range(0, 1921, 120))}</g>
          <g fill="#1f4a3e" stroke="#3f8a70" stroke-width="4"><path d="{na}" /><path d="{ca}" /><path d="{sa}" /></g>
          <path id="m-c-co" d="{co}" fill="#e8412f" opacity="0.75" />
          <path d="M470 700 L520 560 L700 620 L760 720 L620 780 Z" fill="#2f6a56" opacity=".6" />
          <g fill="none" stroke="#f7c548" stroke-width="6" stroke-linecap="round">{paths}</g>
          {planes}
          <text x="540" y="470" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="72" fill="#f4f1ea">USA</text>
          <text x="760" y="1420" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="46" fill="#f4f1ea">KOLUMBIEN</text>'''
body = "\n".join([beat("m-a", a, ad, svgA, title("m-a-title", '<span class="r">Medellín-</span><br />Kartell', size=104)),
                  beat("m-b", b, bd, svgB, '      <div id="m-b-flash" class="full" style="background: #fff; opacity: 0"></div>'),
                  beat("m-c", c, cd, svgC)])
smile = loc("kartell", w("s5", 7))
js = [push("#m-a-cam", a, ad),
      f'    tl.fromTo("#m-a-plane", {{ x: -200, y: 60, scale: 1.0 }}, {{ x: 520, y: -560, scale: 0.45, duration: {r2(ad - 0.3)}, ease: "power1.in" }}, {r2(a + 0.2)});',
      f'    tl.fromTo(".m-a-rl", {{ opacity: 0.25 }}, {{ opacity: 1, duration: 0.25, repeat: 13, yoyo: true, stagger: 0.04 }}, {r2(a)});',
      slam("#m-a-title", loc("kartell", w("s4", 11)) - 0.1),
      push("#m-b-cam", b, bd, 1.0, 1.05, 0, -10),
      f'    tl.fromTo("#m-b-flash", {{ opacity: 0 }}, {{ opacity: 0.9, duration: 0.06 }}, {r2(b + 0.15)});',
      f'    tl.to("#m-b-flash", {{ opacity: 0, duration: 0.35 }}, {r2(b + 0.21)});',
      f'    tl.fromTo("#m-b-p2", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25 }}, {r2(smile - 0.1)});',
      push("#m-c-cam", c, cd, 1.0, 1.06, 0, 0),
      f'    tl.fromTo("#m-c-co", {{ opacity: 0.4 }}, {{ opacity: 0.9, duration: 0.4, repeat: 5, yoyo: true }}, {r2(c)});',
      f'    tl.fromTo(".m-c-rt", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 1.4, ease: "power1.inOut", stagger: 0.35 }}, {r2(c + 0.2)});']
for i, (s, e, q) in enumerate(routes):
    js.append(f'    tl.fromTo("#m-c-pl{i}", {{ x: 0, y: 0, rotation: 0 }}, {{ x: {e[0] - s[0]}, y: {e[1] - s[1]}, rotation: {-20 + i * 20}, duration: 1.4, ease: "power1.inOut" }}, {r2(c + 0.2 + i * 0.35)});')
files["kartell"] = comp("kartell", "", body, "\n".join(js))

# =========================== REICH: Geld, Nilpferde, Häuser ===========================
rng = random.Random(4)
(a, ad), (b, bd), (c, cd) = beats("reich", [SC["reich"][0], round(w("s7", 9) - 0.12, 2), st("s8")])
stacks = []
for row, n in enumerate([7, 6, 5, 4, 3]):
    for i in range(n):
        x = 540 + (i - (n - 1) / 2) * 136
        y = 1760 - row * 80
        stacks.append(f'<g transform="translate({x:.0f} {y})"><rect x="-64" y="-76" width="128" height="76" fill="#3f7a4a" /><rect x="-64" y="-76" width="128" height="10" fill="#5fa06a" />'
                      f'<rect x="-14" y="-76" width="28" height="76" fill="#d8c28a" /><path d="M-64 -40 H64" stroke="#2f5a38" stroke-width="3" /></g>')
bills = "".join(f'<rect class="g-a-bill" x="{rng.uniform(40, 1000):.0f}" y="{rng.uniform(-300, 200):.0f}" width="70" height="34" rx="3" fill="#5fa06a" opacity=".9" />' for _ in range(26))
svgA = f'''          <defs><radialGradient id="g-a-glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffd25a" stop-opacity="0.75" /><stop offset="1" stop-color="#ff8a2a" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#0e0a06" />
          <circle cx="540" cy="1400" r="760" fill="url(#g-a-glow)" />
          <rect x="0" y="1760" width="1080" height="160" fill="#1a120a" />
          {"".join(stacks)}
          {bills}
          <!--@embers id="g-a-emb" n="30" seed="12" y0="900" y1="1800" color="#ffd25a" r="4"-->'''
palms = "".join(f'<g transform="translate({x} {y}) scale({sc})"><path d="M0 0 q-10 -200 20 -380" stroke="#3a2a1a" stroke-width="22" fill="none" />'
                + "".join(f'<path d="M20 -380 q{dx} {dy} {dx * 2} {dy + 70}" stroke="#1f4a2e" stroke-width="26" fill="none" stroke-linecap="round" />' for dx, dy in [(-90, -40), (90, -40), (-60, -90), (70, -90), (0, -110)])
                + "</g>" for x, y, sc in [(90, 1400, 1.1), (990, 1380, 1.0), (180, 1330, 0.7)])
svgB = f'''          <defs>
            <linearGradient id="g-b-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a2a3a" /><stop offset="0.55" stop-color="#e88a4a" /><stop offset="1" stop-color="#f4c27a" /></linearGradient>
            <linearGradient id="g-b-wat" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a6a6a" /><stop offset="1" stop-color="#0e2a2e" /></linearGradient>
          </defs>
          <rect width="1080" height="1920" fill="url(#g-b-sky)" />
          <rect x="0" y="1200" width="1080" height="720" fill="#3a5a2a" />
          <!-- Tor der Hacienda mit Flugzeug -->
          <g><rect x="250" y="760" width="60" height="460" fill="#e9e2d0" /><rect x="770" y="760" width="60" height="460" fill="#e9e2d0" />
            <rect x="230" y="720" width="620" height="70" fill="#f4efe4" /><rect x="230" y="782" width="620" height="10" fill="#c9bfa8" />
            <text x="540" y="770" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="44" fill="#1d3a5a">HACIENDA NÁPOLES</text>
            <g transform="translate(540 640) scale(0.9)"><g id="g-b-plane">{plane}</g></g></g>
          {palms}
          <ellipse cx="540" cy="1640" rx="620" ry="190" fill="url(#g-b-wat)" />
          <!--@hippo id="g-b-h1" x="250" y="1540" s="0.62" color="#6d6a7a"-->
          <g id="g-b-h2w"><!--@hippo id="g-b-h2" x="760" y="1700" s="0.66" flip="1" color="#7a7686"--></g>
          <path d="M-80 1680 Q540 1600 1160 1680 V1920 H-80 Z" fill="#1f4a46" opacity="0.92" />
          <g stroke="#9fe0d4" stroke-width="4" fill="none" opacity=".5"><path id="g-b-r1" d="M620 1660 q140 -24 280 0" /><path d="M120 1720 q120 -20 240 0" /></g>'''
houses = []
cols = ["#e8412f", "#f4a62a", "#3d7bb3", "#5f8f5c", "#f4efe4", "#c96b9a"]
for row in range(5):
    for i in range(7):
        x = 60 + i * 160 + (row % 2) * 60
        y = 820 + row * 150 - i * 18
        houses.append(f'<g transform="translate({x} {y})"><g class="g-c-h"><rect x="-56" y="-80" width="112" height="80" fill="{cols[(i + row * 2) % 6]}" />'
                      f'<path d="M-66 -76 L0 -120 L66 -76 Z" fill="#7a2a1a" /><rect x="-14" y="-46" width="28" height="46" fill="#2a1a10" /><rect x="22" y="-64" width="22" height="20" fill="#ffd28a" /></g></g>')
crowd = "".join(f'<g class="g-c-c"><!--@person id="g-c-p{i}" x="{x}" y="1880" s="0.52" jacket="{j}" pants="#2a2f3b" hair="#1e140c" skin="{sk}" arms="up" mood="happy"--></g>'
                for i, (x, j, sk) in enumerate([(120, "#3d7bb3", "#c98d62"), (320, "#e8412f", "#a8714a"), (540, "#f4a62a", "#c98d62"), (760, "#5f8f5c", "#a8714a"), (960, "#c96b9a", "#c98d62")]))
svgC = f'''          <defs><linearGradient id="g-c-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a6a8a" /><stop offset="1" stop-color="#f4c27a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#g-c-sky)" />
          <path d="M0 760 Q540 560 1080 700 V1920 H0 Z" fill="#6a8a4a" />
          {"".join(houses)}
          <rect x="0" y="1560" width="1080" height="360" fill="#4a3a2a" />
          {crowd}'''
body = "\n".join([beat("g-a", a, ad, svgA, title("g-a-title", "Milliardär", size=120, extra=" color: #ffd25a; text-shadow: 0 7px 0 #7a4a0a, 0 0 50px rgba(255,190,80,.5);")),
                  beat("g-b", b, bd, svgB), beat("g-c", c, cd, svgC)])
hip = loc("reich", w("s7", 13))
js = "\n".join([
    f'    tl.fromTo("#g-a-cam", {{ scale: 1.12 }}, {{ scale: 1.0, duration: {r2(ad)}, ease: "power2.out" }}, {r2(a)});',
    f'    tl.fromTo(".g-a-bill", {{ y: 0, rotation: 0 }}, {{ y: 1500, rotation: 220, duration: 2.6, ease: "none", stagger: 0.04 }}, {r2(a)});',
    f'    tl.fromTo(".g-a-emb-p", {{ y: 0 }}, {{ y: -300, duration: {r2(ad)}, ease: "none" }}, {r2(a)});',
    slam("#g-a-title", loc("reich", w("s7", 4)) - 0.1),
    push("#g-b-cam", b, bd, 1.0, 1.06, 0, -10),
    f'    tl.fromTo("#g-b-h2w", {{ y: 120 }}, {{ y: 0, duration: 0.35, ease: "back.out(2)" }}, {r2(hip - 0.15)});',
    f'    tl.fromTo("#g-b-h1", {{ x: 0 }}, {{ x: 40, duration: {r2(bd)}, ease: "none" }}, {r2(b)});',
    push("#g-c-cam", c, cd, 1.0, 1.05, 0, -10),
    f'    tl.fromTo(".g-c-h", {{ scale: 0, transformOrigin: "50% 100%" }}, {{ scale: 1, duration: 0.3, ease: "back.out(2)", stagger: {{ each: 0.025 }} }}, {r2(c + 0.1)});',
    f'    tl.fromTo(".g-c-c", {{ y: 0 }}, {{ y: -40, duration: 0.25, repeat: 7, yoyo: true, ease: "power2.out", stagger: 0.08 }}, {r2(loc("reich", w("s8", 6)) - 0.1)});',
])
files["reich"] = comp("reich", "", body, js)

# =========================== KRIEG ===========================
rng = random.Random(5)
s0, d = SC["krieg"]
flames = "".join(f'<g transform="translate({x:.0f} {y:.0f}) scale({sc:.2f})"><path class="w-fl" d="M0 0 q-60 -40 -30 -130 q10 50 30 40 q-10 -90 40 -150 q0 90 40 120 q30 -40 20 -80 q60 80 0 200 z" fill="#ff7a1f" />'
                 f'<path class="w-fl" d="M10 0 q-30 -30 -10 -80 q10 30 20 20 q0 -40 20 -70 q10 60 20 80 q20 30 -10 50 z" fill="#ffd25a" /></g>'
                 for x, y, sc in [(160, 1300, 1.2), (420, 1260, 0.9), (700, 1300, 1.3), (930, 1270, 1.0), (300, 1330, 0.7), (580, 1330, 0.8)])
smoke = "".join(f'<ellipse class="w-sm" cx="{rng.uniform(60, 1020):.0f}" cy="{rng.uniform(800, 1200):.0f}" rx="{rng.uniform(120, 220):.0f}" ry="{rng.uniform(60, 110):.0f}" fill="#1a0e0c" opacity="{rng.uniform(.5, .8):.2f}" />' for _ in range(10))
svg = f'''          <defs>
            <linearGradient id="w-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c0404" /><stop offset="0.5" stop-color="#4a120a" /><stop offset="1" stop-color="#c2461e" /></linearGradient>
            <filter id="w-blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="30" /></filter>
          </defs>
          <rect width="1080" height="1920" fill="url(#w-sky)" />
          <g filter="url(#w-blur)">{smoke}</g>
          <!--@skyline id="w-sk" y="1330" lit="1" seed="7" color="#0a0507" win="#ff9a3c"-->
          {flames}
          <rect x="0" y="1330" width="1080" height="590" fill="#0a0507" />
          <!--@embers id="w-emb" n="50" seed="5" y0="900" y1="1800" color="#ff9a3c" r="5"-->'''
body = beat("w-a", 0, d, svg, title("w-a-title", '<span class="r">Tausende</span>', size=140) + '\n      <div id="w-flash" class="full" style="background: #ffb35c; opacity: 0"></div>')
js = "\n".join([
    f'    tl.fromTo("#w-a-cam", {{ scale: 1.14, x: 0 }}, {{ scale: 1.0, x: 0, duration: {r2(d)}, ease: "power2.out" }}, 0);',
    f'    tl.fromTo("#w-flash", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.05 }}, 0.05);',
    f'    tl.to("#w-flash", {{ opacity: 0, duration: 0.5 }}, 0.1);',
    f'    tl.fromTo(".w-fl", {{ scaleY: 0.85, transformOrigin: "50% 100%" }}, {{ scaleY: 1.12, duration: 0.16, repeat: 23, yoyo: true, ease: "sine.inOut", stagger: 0.03 }}, 0);',
    f'    tl.fromTo(".w-sm", {{ y: 0 }}, {{ y: -260, duration: {r2(d)}, ease: "none" }}, 0);',
    f'    tl.fromTo(".w-emb-p", {{ y: 0 }}, {{ y: -500, duration: {r2(d)}, ease: "none" }}, 0);',
    slam("#w-a-title", loc("krieg", w("s9", 9)) - 0.1),
])
files["krieg"] = comp("krieg", "", body, js)

# =========================== GEFÄNGNIS: La Catedral 1991, Flucht ===========================
(a, ad), (b, bd) = beats("gefaengnis", [SC["gefaengnis"][0], st("s11")])
wire = "M120 1180 " + " ".join(f"l15 -14 l15 14" for _ in range(28))
svgA = f'''          <defs><linearGradient id="p-a-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a2a44" /><stop offset="0.6" stop-color="#c26a4a" /><stop offset="1" stop-color="#f4a66a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#p-a-sky)" />
          <path d="M0 1000 L200 860 L380 920 L560 780 L760 880 L1080 760 V1920 H0 Z" fill="#3a3a4a" />
          <path d="M0 1200 Q540 980 1080 1180 V1920 H0 Z" fill="#2a3a2e" />
          <g><rect x="200" y="920" width="680" height="240" fill="#cfc4ae" /><path d="M180 930 L540 840 L900 930 Z" fill="#8a3a2a" />
            <g fill="#3a2a1a">{"".join(f'<rect x="{230 + i * 64}" y="980" width="30" height="46" />' for i in range(10))}</g>
            <g fill="#ffd28a">{"".join(f'<rect class="p-a-w" x="{230 + i * 64}" y="1070" width="30" height="40" />' for i in range(10))}</g>
            <rect x="130" y="820" width="70" height="360" fill="#9a907c" /><rect x="112" y="790" width="106" height="44" fill="#6a604c" />
            <rect x="880" y="820" width="70" height="360" fill="#9a907c" /><rect x="862" y="790" width="106" height="44" fill="#6a604c" /></g>
          <path d="M100 1190 H980" stroke="#2a2a2a" stroke-width="6" /><path d="{wire}" stroke="#2a2a2a" stroke-width="4" fill="none" />
          <polygon points="200,1300 880,1300 1000,1560 80,1560" fill="#2f7a4a" />
          <g fill="none" stroke="#e9f6ee" stroke-width="5" opacity=".8"><polygon points="214,1310 866,1310 980,1550 100,1550" /><line x1="540" y1="1310" x2="540" y2="1550" /><ellipse cx="540" cy="1430" rx="90" ry="40" /></g>
          <rect x="0" y="1560" width="1080" height="360" fill="#1f2a22" />'''
heli = '''<path d="M-90 0 q0 -50 70 -50 h40 q50 0 60 40 l120 -10 v20 l-120 10 q-10 30 -60 30 h-50 q-60 0 -60 -40 z" fill="#0a0e12" />
              <rect x="-120" y="-70" width="240" height="8" fill="#0a0e12" /><rect x="-4" y="-64" width="8" height="16" fill="#0a0e12" />
              <circle id="p-b-hl" cx="-60" cy="20" r="8" fill="#ff4a3a" />'''
svgB = f'''          <defs><linearGradient id="p-b-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#02050a" /><stop offset="1" stop-color="#0e2230" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#p-b-sky)" />
          <g opacity="0.16" fill="#e9f6ff">
            <g transform="translate(200 1500)"><g id="p-b-s1"><path d="M0 0 L-160 -1200 L160 -1200 Z" /></g></g>
            <g transform="translate(880 1500)"><g id="p-b-s2"><path d="M0 0 L-160 -1200 L160 -1200 Z" /></g></g></g>
          <path d="M0 1300 q80 -150 160 -20 q70 -180 170 -30 q90 -120 180 0 q80 -170 190 -10 q100 -140 200 0 q80 -90 180 -20 V1920 H0 Z" fill="#06120e" />
          <g transform="translate(120 720)"><g id="p-b-heli"><path d="M-60 30 L-260 900 L140 900 Z" fill="#e9f6ff" opacity="0.1" />{heli.replace('#0a0e12', '#3a4654')}</g></g>
          <g id="p-b-run"><!--@man id="p-b-m" x="540" y="1560" s="0.42" pose="walk" shirt="#2a3440" pants="#161a22" rim="#cfe3ff"--></g>
          <rect x="0" y="1560" width="1080" height="360" fill="#040a08" />
          <g stroke="#3a4a52" stroke-width="5">{"".join(f'<line x1="{x}" y1="1580" x2="{x}" y2="1920" />' for x in range(0, 1081, 60))}{"".join(f'<line x1="0" y1="{y}" x2="1080" y2="{y}" />' for y in range(1600, 1921, 60))}</g>
          <path d="M380 1920 L420 1640 L560 1620 L640 1700 L620 1920 Z" fill="#040a08" />'''
body = "\n".join([beat("p-a", a, ad, svgA, title("p-a-title", "1991", size=150) + '\n      <div id="p-a-chip" class="chip-row" style="top: 520px"><span class="chip lt" style="font-size: 50px">La Catedral</span></div>'),
                  beat("p-b", b, bd, svgB, title("p-b-title", '<span class="r">16</span> Monate', size=130))])
js = "\n".join([
    push("#p-a-cam", a, ad, 1.0, 1.08, 0, -20),
    pop_in("#p-a-title", loc("gefaengnis", w("s10", 0)) - 0.05),
    pop_in("#p-a-chip", loc("gefaengnis", w("s10", 0)) + 0.4),
    f'    tl.fromTo(".p-a-w", {{ opacity: 0.4 }}, {{ opacity: 1, duration: 0.3, stagger: 0.08 }}, {r2(a + 0.5)});',
    f'    tl.fromTo("#p-b-cam", {{ scale: 1.1 }}, {{ scale: 1.0, duration: {r2(bd)}, ease: "power1.out" }}, {r2(b)});',
    f'    tl.fromTo("#p-b-s1", {{ rotation: -25, svgOrigin: "0 0" }}, {{ rotation: 20, duration: 1.6, repeat: 1, yoyo: true, ease: "sine.inOut" }}, {r2(b)});',
    f'    tl.fromTo("#p-b-s2", {{ rotation: 20, svgOrigin: "0 0" }}, {{ rotation: -25, duration: 1.4, repeat: 1, yoyo: true, ease: "sine.inOut" }}, {r2(b)});',
    f'    tl.fromTo("#p-b-heli", {{ x: -200, y: 0 }}, {{ x: 900, y: -60, duration: {r2(bd)}, ease: "none" }}, {r2(b)});',
    f'    tl.fromTo("#p-b-hl", {{ opacity: 0.2 }}, {{ opacity: 1, duration: 0.2, repeat: 15, yoyo: true }}, {r2(b)});',
    f'    tl.fromTo("#p-b-run", {{ x: -260 }}, {{ x: 300, duration: {r2(bd)}, ease: "none" }}, {r2(b)});',
    slam("#p-b-title", loc("gefaengnis", w("s11", 5)) - 0.1),
])
files["gefaengnis"] = comp("gefaengnis", "", body, js)

# =========================== ENDE: Anruf geortet, Dach in Medellín ===========================
(a, ad), (b, bd) = beats("ende", [SC["ende"][0], st("s13")])
blinds = "".join(f'<rect x="620" y="{y}" width="360" height="22" fill="#f4c27a" opacity=".35" />' for y in range(420, 1000, 44))
rings = "".join(f'<circle class="e-a-ring" cx="0" cy="0" r="{60 + i * 70}" fill="none" stroke="#9fe0d4" stroke-width="6" />' for i in range(4))
radar = '''<circle r="200" fill="#071a14" stroke="#3f8a70" stroke-width="5" /><circle r="130" fill="none" stroke="#3f8a70" stroke-width="3" /><circle r="60" fill="none" stroke="#3f8a70" stroke-width="3" />
              <path d="M-200 0 H200 M0 -200 V200" stroke="#3f8a70" stroke-width="3" />
              <g id="e-a-sweep"><path d="M0 0 L0 -200 A200 200 0 0 1 120 -160 Z" fill="#5fe0a8" opacity=".35" /></g>
              <circle id="e-a-blip" cx="70" cy="-60" r="16" fill="#e8412f" />'''
svgA = f'''          <rect width="1080" height="1920" fill="#0a0d12" />
          <rect x="600" y="400" width="400" height="620" fill="#1a1410" />{blinds}
          <rect x="0" y="1500" width="1080" height="420" fill="#07090c" />
          <g transform="translate(660 1190)"><g id="e-a-rings">{rings}</g></g>
          <!--@man id="e-a-m" x="540" y="1880" s="0.95" pose="phone" shirt="#2f5a8a" pants="#1a1e26" rim="#f4c27a"-->
          <g transform="translate(540 560)"><g id="e-a-radar" opacity="0">{radar}</g></g>'''
roofs = []
rng = random.Random(8)
for row, (yy, sc) in enumerate([(1100, 0.6), (1300, 0.8), (1560, 1.1)]):
    for x in range(-60 + row * 50, 1141, int(260 * sc)):
        hh = rng.uniform(140, 220) * sc
        roofs.append(f'<g transform="translate({x} {yy})"><rect x="{-110 * sc:.0f}" y="{-hh:.0f}" width="{220 * sc:.0f}" height="{hh + 400:.0f}" fill="{["#e9dcc0", "#d9c8a8", "#cdb894"][row]}" />'
                     f'<path d="M{-126 * sc:.0f} {-hh:.0f} L0 {-hh - 70 * sc:.0f} L{126 * sc:.0f} {-hh:.0f} Z" fill="{["#9a4a32", "#a8442a", "#b5442e"][row]}" />'
                     f'<rect x="{-30 * sc:.0f}" y="{-hh + 30 * sc:.0f}" width="{36 * sc:.0f}" height="{44 * sc:.0f}" fill="#3a2a1a" /></g>')
svgB = f'''          <defs><linearGradient id="e-b-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a1a3a" /><stop offset="0.55" stop-color="#a84a4a" /><stop offset="1" stop-color="#f4a66a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#e-b-sky)" />
          <path d="M0 980 Q270 760 540 900 Q800 760 1080 920 V1920 H0 Z" fill="#4a3a5a" />
          {"".join(roofs)}
          <g transform="translate(860 800)"><g id="e-b-heli">{heli.replace('id="p-b-hl"', 'id="e-b-hl"')}</g></g>
          <g opacity="0.14" fill="#fff4d6"><path id="e-b-beam" d="M800 840 L560 1600 L860 1600 Z" /></g>'''
body = "\n".join([beat("e-a", a, ad, svgA, title("e-a-title", '<span class="r">Geortet</span>', top=820, size=110)),
                  beat("e-b", b, bd, svgB, title("e-b-title", '2. Dezember<br /><span style="font-size: 170px">1993</span>', size=96)
                       + '\n      <div id="e-b-dark" class="full" style="background: #000; opacity: 0"></div>')])
ort = loc("ende", w("s12", 9))
js = "\n".join([
    push("#e-a-cam", a, ad, 1.0, 1.06, 0, -10),
    f'    tl.fromTo(".e-a-ring", {{ scale: 0.6, opacity: 0.8, transformOrigin: "50% 50%" }}, {{ scale: 1.4, opacity: 0, duration: 1.0, repeat: 3, stagger: 0.25, ease: "none" }}, {r2(a)});',
    f'    tl.fromTo("#e-a-radar", {{ opacity: 0, scale: 0.6, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, {r2(ort - 0.2)});',
    f'    tl.fromTo("#e-a-sweep", {{ rotation: 0, svgOrigin: "0 0" }}, {{ rotation: 720, duration: 2.0, ease: "none" }}, {r2(ort - 0.2)});',
    f'    tl.fromTo("#e-a-blip", {{ scale: 0.6, transformOrigin: "50% 50%" }}, {{ scale: 1.5, duration: 0.2, repeat: 7, yoyo: true }}, {r2(ort)});',
    f'    tl.fromTo("#e-a-title", {{ opacity: 0, scale: 1.5 }}, {{ opacity: 1, scale: 1, duration: 0.2, ease: "power4.in" }}, {r2(ort + 0.15)});',
    push("#e-b-cam", b, bd, 1.0, 1.08, 0, -20),
    f'    tl.fromTo("#e-b-heli", {{ x: 0, y: 0 }}, {{ x: -260, y: 40, duration: {r2(bd)}, ease: "none" }}, {r2(b)});',
    f'    tl.fromTo("#e-b-beam", {{ x: 0 }}, {{ x: -260, duration: {r2(bd)}, ease: "none" }}, {r2(b)});',
    f'    tl.fromTo("#e-b-hl", {{ opacity: 0.2 }}, {{ opacity: 1, duration: 0.2, repeat: 19, yoyo: true }}, {r2(b)});',
    pop_in("#e-b-title", loc("ende", w("s13", 1)) - 0.1),
    f'    tl.fromTo("#e-b-dark", {{ opacity: 0 }}, {{ opacity: 0.55, duration: 1.2, ease: "power1.in" }}, {r2(loc("ende", w("s13", 4)))});',
])
files["ende"] = comp("ende", "", body, js)

# =========================== REVEAL ===========================
rng = random.Random(9)
s0, d = SC["reveal"]
svg = f'''          <defs>
            <linearGradient id="r-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#03060b" /><stop offset="0.5" stop-color="#0f2e36" /><stop offset="1" stop-color="#1c4a44" /></linearGradient>
            <radialGradient id="r-gold" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffd25a" stop-opacity="0.7" /><stop offset="1" stop-color="#ff8a2a" stop-opacity="0" /></radialGradient>
          </defs>
          <rect width="1080" height="1920" fill="url(#r-sky)" />
          <ellipse cx="540" cy="1250" rx="760" ry="320" fill="url(#r-gold)" opacity="0.6" />
          {dots(rng, 300, 0, 1080, 1050, 1500, ["#ffb35c", "#ffd28a", "#f7c548", "#ff8a3c"], 2, 5, "r-city", (0.35, 0.95))}
          <!--@fog id="r-fog" y="1200" color="#ffe2a0" opacity="0.12" seed="9"-->
          <path d="M0 1560 Q540 1500 1080 1560 V1920 H0 Z" fill="#04070a" />
          <!--@man id="r-m" x="540" y="1860" s="1.0" shirt="#e9e2d0" pants="#22262f" rim="#ffd25a"-->
          <!--@embers id="r-emb" n="40" seed="13" y0="900" y1="1900" color="#ffd25a" r="4"-->'''
css = '''    #r-name { position: absolute; left: 0; width: 1080px; top: 330px; text-align: center; font-family: "Montserrat", sans-serif;
      font-weight: 800; text-transform: uppercase; line-height: 0.98; color: #ffd25a;
      text-shadow: 0 7px 0 #7a4a0a, 0 0 60px rgba(255, 190, 80, 0.6); }
    #r-name .a { display: block; font-size: 120px; color: #f4f1ea; text-shadow: 0 6px 0 rgba(0,0,0,.6), 0 0 40px rgba(0,0,0,.6); }
    #r-name .b { display: block; font-size: 160px; }
    #r-follow { position: absolute; left: 0; width: 1080px; top: 690px; text-align: center; }
    #r-follow span { display: inline-block; padding: 14px 34px; border-radius: 18px; background: rgba(10, 14, 18, 0.88);
      border: 3px solid #e8412f; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 44px; color: #f4f1ea; }'''
extra = '      <div id="r-name"><span class="a">Pablo</span><span class="b">Escobar</span></div>\n      <div id="r-follow"><span>Folg für mehr Legenden!</span></div>'
na_, nb_ = loc("reveal", w("reveal", 9)), loc("reveal", w("reveal", 10))
js = "\n".join([
    f'    tl.fromTo("#r-a-cam", {{ scale: 1.15, y: 40 }}, {{ scale: 1.0, y: 0, duration: {r2(d)}, ease: "power2.out" }}, 0);',
    f'    tl.fromTo(".r-city", {{ opacity: 0.3 }}, {{ opacity: 1, duration: 0.5, repeat: 5, yoyo: true, stagger: {{ each: 0.003 }} }}, 0);',
    f'    tl.fromTo(".r-emb-p", {{ y: 0 }}, {{ y: -600, duration: {r2(d)}, ease: "none" }}, 0);',
    f'    tl.fromTo("#r-name .a", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }}, {r2(na_ - 0.05)});',
    f'    tl.fromTo("#r-name .b", {{ opacity: 0, scale: 1.8, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.2, ease: "power4.in" }}, {r2(nb_ - 0.15)});',
    f'    tl.fromTo("#r-follow", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }}, {r2(nb_ + 1.2)});',
])
files["reveal"] = comp("reveal", css, beat("r-a", 0, d, svg, extra), js)

for n, html in files.items():
    open(os.path.join(P, "compositions", n + ".html"), "w").write(html)

# ---- scenes.json (Szenen + Geräusche) ----
g = lambda n: SC[n][0]
sfx = [["sfx-w1", "whoosh", g("cards"), 0.3], ["sfx-call", "impact-bass-1", w("card2", 4), 0.25],
       ["sfx-w2", "whoosh-short", g("herkunft"), 0.28], ["sfx-w3", "whoosh", g("kartell"), 0.28],
       ["sfx-ti", "impact-bass-2", w("s4", 11), 0.22], ["sfx-flash", "click-soft", L["s5"]["start"] + 0.05, 1.2],
       ["sfx-smile", "pop", w("s5", 7), 0.6], ["sfx-w4", "whoosh-short", g("kartell") + beats("kartell", [g("kartell"), st("s5"), st("s6")])[2][0], 0.26],
       ["sfx-w5", "whoosh", g("reich"), 0.28], ["sfx-gold", "impact-bass-1", w("s7", 4), 0.18], ["sfx-hip", "pop", w("s7", 13), 0.8],
       ["sfx-w6", "whoosh-short", g("krieg"), 0.3], ["sfx-boom", "impact-bass-2", g("krieg") + 0.05, 0.35], ["sfx-gl", "glitch-3", g("krieg") + 0.08, 0.2],
       ["sfx-tau", "impact-bass-1", w("s9", 9), 0.3], ["sfx-w7", "whoosh", g("gefaengnis"), 0.26],
       ["sfx-w8", "whoosh-short", st("s11"), 0.26], ["sfx-16", "impact-bass-1", w("s11", 5), 0.22],
       ["sfx-w9", "whoosh", g("ende"), 0.26], ["sfx-ort", "error", w("s12", 9) + 0.15, 0.35],
       ["sfx-w10", "whoosh-short", st("s13"), 0.26], ["sfx-date", "impact-bass-2", w("s13", 1), 0.22],
       ["sfx-riser", "riser", w("reveal", 10) - 0.15, 0.2], ["sfx-name", "impact-bass-1", w("reveal", 10) - 0.15, 0.32]]
sfx = [[a_, b_, round(t, 2), v] for a_, b_, t, v in sfx]
json.dump({"total": TOTAL, "scenes": [[n, SC[n][0], SC[n][1]] for n, _ in order], "sfx": sfx},
          open(os.path.join(P, "scenes.json"), "w"), indent=1)
print("Szenen:", ", ".join(f"{n} {SC[n][0]}+{SC[n][1]}" for n, _ in order), "| Länge", TOTAL)
