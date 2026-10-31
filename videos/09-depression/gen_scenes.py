# Erzeugt alle Szenen (compositions/*.html) und scenes.json aus assets/timing.json.
# Neue Stimme → place_voice.py → dieses Skript → svg_parts.py . → build_index.py →
# build_captions.py . --style legende --skip help,s11 --key-color "#ffd25a"
# Inhaltlich nach Empfehlungen für Berichte über psychische Erkrankungen: keine Methoden, Hilfe & Behandelbarkeit betonen.
import json, random, os, math

P = os.path.dirname(os.path.abspath(__file__))
tm = json.load(open(os.path.join(P, "assets/timing.json")))
L = {l["id"]: l for l in (tm["lines"] if isinstance(tm, dict) else tm)}
w = lambda lid, i: L[lid]["words"][i]["start"]
st = lambda lid: round(L[lid]["start"] - 0.12, 2)
r2 = lambda x: f"{x:.2f}"

HOLD = 6.5  # Hilfe-Karte am Ende zum Screenshotten
order = [("hook", 0.0), ("gefuehl", st("s1")), ("alltag", st("s3")), ("kopf", st("s6")), ("mut", st("s8")),
         ("hilfe", st("s9")), ("nummern", st("help")), ("ende", st("end"))]
TOTAL = round(L["cta"]["end"] + HOLD, 2)
SC = {}
for i, (n, s) in enumerate(order):
    e = order[i + 1][1] if i + 1 < len(order) else TOTAL
    SC[n] = (s, round(e - s, 2))
loc = lambda sc, t: round(t - SC[sc][0], 2)


def beats(sc, starts):
    s0, d = SC[sc]
    l = [round(x - s0, 2) for x in starts] + [d]
    return [(l[i], round(l[i + 1] - l[i], 2)) for i in range(len(starts))]


GOLD, INK, BLUE = "#ffd25a", "#f4f1ea", "#7fb0d8"
CSS_BASE = f'''    #root {{ position: absolute; inset: 0; background: #0a0e14; }}
    .beat {{ position: absolute; inset: 0; overflow: hidden; }}
    .lt {{ font-family: "Montserrat", sans-serif; font-weight: 800; text-transform: uppercase; }}
    .gold {{ color: {GOLD}; text-shadow: 0 6px 0 #7a4a0a, 0 0 50px rgba(255, 190, 80, 0.45); }}
    .blue {{ color: #bfe0ff; text-shadow: 0 6px 0 #1a2a40, 0 0 40px rgba(127, 176, 216, 0.4); }}
    .red {{ color: #e8412f; text-shadow: 0 6px 0 #5a1208, 0 0 40px rgba(232, 65, 47, 0.4); }}
    .green {{ color: #7fe0a0; text-shadow: 0 6px 0 #10402a, 0 0 40px rgba(127, 224, 160, 0.4); }}
    .pill {{ position: absolute; left: 0; width: 1080px; text-align: center; }}
    .pill span {{ display: inline-block; padding: 12px 30px; border-radius: 18px; background: rgba(10, 14, 18, 0.88);
      border: 3px solid {GOLD}; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 38px; color: {INK}; }}
    .card {{ position: absolute; left: 80px; width: 920px; padding: 44px 40px; border-radius: 28px; text-align: center;
      background: rgba(8, 12, 18, 0.9); border: 4px solid {GOLD}; box-shadow: 0 20px 60px rgba(0,0,0,.5);
      font-family: "Montserrat", sans-serif; font-weight: 800; color: {INK}; }}
    .card .h {{ font-size: 46px; letter-spacing: 0.04em; text-transform: uppercase; color: {GOLD}; }}
    .card .n {{ font-size: 104px; line-height: 1.1; margin: 14px 0; letter-spacing: 0.01em; white-space: nowrap; }}
    .card .s {{ font-size: 36px; color: #c7ccd6; font-weight: 700; }}
    .res {{ position: absolute; left: 60px; width: 960px; padding: 34px 40px; border-radius: 26px; background: rgba(8, 12, 18, 0.92);
      border: 4px solid {GOLD}; font-family: "Montserrat", sans-serif; color: {INK}; }}
    .res .t {{ font-weight: 800; font-size: 42px; text-transform: uppercase; color: {GOLD}; text-align: center; margin-bottom: 18px; }}
    .res .r {{ display: flex; justify-content: space-between; align-items: baseline; gap: 20px; padding: 22px 0; border-top: 2px solid rgba(255,255,255,.12); }}
    .res .l {{ font-weight: 700; font-size: 34px; color: #c7ccd6; }}
    .res .v {{ font-weight: 800; font-size: 46px; white-space: nowrap; color: {INK}; text-align: right; }}
    .res .v small {{ display: block; font-size: 30px; color: #c7ccd6; font-weight: 700; }}'''


def comp(cid, body, js, css=""):
    return f'''<template>
  <style>
{CSS_BASE}
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


def title(i, html, top=330, size=130, cls=""):
    return f'      <div id="{i}" class="title lt {cls}" style="top: {top}px; font-size: {size}px">{html}</div>'


push = lambda sel, s, d, a=1.0, b=1.06: f'    tl.fromTo("{sel}", {{ scale: {a} }}, {{ scale: {b}, duration: {r2(d)}, ease: "none" }}, {r2(s)});'
fade = lambda sel, t, dur=0.45: f'    tl.fromTo("{sel}", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: {dur}, ease: "power2.out" }}, {r2(t)});'
slam = lambda sel, t: f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 1.4, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.25, ease: "power3.in" }}, {r2(t)});'
popc = lambda sel, t: f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 0.5, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: "back.out(2)" }}, {r2(t)});'

ME = 'jacket="#5a6a7a" pants="#2a2f3b" hair="#3a2a1e" skin="#e9c0a0" style="short"'


def cloud(cid, x, y, s=1.0, col="#6a7280", rain=True):
    drops = "".join(f'<line class="{cid}-r" x1="{dx}" y1="40" x2="{dx - 8}" y2="90" stroke="{BLUE}" stroke-width="5" stroke-linecap="round" />' for dx in range(-90, 100, 36)) if rain else ""
    return (f'<g transform="translate({x} {y}) scale({s})"><g id="{cid}">{drops}<g fill="{col}"><circle cx="-70" cy="0" r="56" /><circle cx="0" cy="-30" r="76" />'
            f'<circle cx="74" cy="0" r="58" /><rect x="-126" y="0" width="256" height="56" rx="28" /></g></g></g>')


rain_js = lambda cid, t, d: f'    tl.fromTo(".{cid}-r", {{ y: -20, opacity: 0.9 }}, {{ y: 60, opacity: 0, duration: 0.5, repeat: {max(1, int(d / 0.5))}, stagger: 0.08, ease: "none" }}, {r2(t)});'
files = {}

# ===================== HOOK: außen lachen, innen unter Wasser =====================
(a, ad), (b, bd) = beats("hook", [0.0, st("hook2")])
svgA = f'''          <defs><radialGradient id="h-a-gl" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffcf8a" stop-opacity="0.45" /><stop offset="1" stop-color="#ff8a3c" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#2a2a3a" />
          <circle cx="540" cy="1050" r="640" fill="url(#h-a-gl)" />
          <rect y="1800" width="1080" height="120" fill="#1e1e2a" />
          <!--@person id="h-a-f1" x="200" y="1840" s="0.78" jacket="#e8412f" hair="#1e140c" skin="#c98d62" style="long" mood="happy"-->
          <!--@person id="h-a-f2" x="880" y="1840" s="0.78" jacket="#3d7bb3" hair="#6b4330" skin="#f1c7a0" style="spiky" mood="happy"-->
          <!--@person id="h-a-me" x="540" y="1860" s="0.9" {ME} mood="happy"-->'''
bubbles = "".join(f'<circle class="h-b-bub" cx="{random.Random(i).uniform(100, 980):.0f}" cy="{random.Random(i + 9).uniform(1300, 1900):.0f}" r="{random.Random(i + 3).uniform(8, 26):.0f}" fill="none" stroke="#bfe0ff" stroke-width="4" opacity="0.6" />' for i in range(26))
svgB = f'''          <defs><linearGradient id="h-b-sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a5a7a" /><stop offset="1" stop-color="#06121e" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#h-b-sea)" />
          <g fill="#bfe0ff" opacity="0.08">{"".join(f'<path d="M{x} 0 L{x + 120} 0 L{x - 140} 1920 L{x - 300} 1920 Z" />' for x in (200, 560, 900))}</g>
          <path id="h-b-surf" d="M0 120 q90 -30 180 0 t180 0 t180 0 t180 0 t180 0 t180 0" stroke="#bfe0ff" stroke-width="6" fill="none" opacity="0.4" />
          <g id="h-b-float"><!--@person id="h-b-me" x="540" y="1860" s="0.9" {ME} mood="sad"--></g>
          {bubbles}'''
body = "\n".join([beat("h-a", a, ad, svgA), beat("h-b", b, bd, svgB, title("h-b-title", "Unter Wasser", top=330, size=130, cls="blue"))])
js = "\n".join([push("#h-a-cam", a, ad, 1.0, 1.06),
                f'    tl.fromTo(["#h-a-f1", "#h-a-f2", "#h-a-me"], {{ y: 0 }}, {{ y: -18, duration: 0.22, repeat: {int(ad / 0.22) // 2 * 2 + 1}, yoyo: true, ease: "sine.inOut", stagger: 0.07 }}, {r2(a)});',
                f'    tl.fromTo("#h-b-cam", {{ scale: 1.08 }}, {{ scale: 1.0, duration: {r2(bd)}, ease: "power1.out" }}, {r2(b)});',
                f'    tl.fromTo("#h-b-float", {{ y: 0, rotation: -2, transformOrigin: "50% 50%" }}, {{ y: -30, rotation: 2, duration: 1.2, repeat: 1, yoyo: true, ease: "sine.inOut" }}, {r2(b)});',
                f'    tl.fromTo(".h-b-bub", {{ y: 0 }}, {{ y: -700, duration: {r2(bd)}, ease: "none", stagger: 0.02 }}, {r2(b)});',
                slam("#h-b-title", loc("hook", w("hook2", 8)) - 0.1)])
files["hook"] = comp("hook", body, js)

# ===================== GEFÜHL: Depression (Wolke), Berg =====================
(a, ad), (b, bd) = beats("gefuehl", [SC["gefuehl"][0], st("s2")])
svgA = f'''          <rect width="1080" height="1920" fill="#1c222c" />
          <g fill="#262e3a">{"".join(f'<rect x="{x}" y="{y}" width="{wd}" height="{1700 - y}" />' for x, y, wd in [(0, 700, 220), (240, 860, 180), (440, 600, 200), (660, 780, 190), (870, 680, 210)])}</g>
          <rect y="1800" width="1080" height="120" fill="#14181e" />
          <!--@person id="g-a-me" x="540" y="1860" s="0.9" {ME} mood="sad"-->
          {cloud("g-a-cl", 540, 1000, 1.1)}'''
svgB = f'''          <defs><linearGradient id="g-b-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a2230" /><stop offset="1" stop-color="#3a4a5a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#g-b-sky)" />
          <path id="g-b-mtn" d="M-100 1500 L360 640 L520 820 L700 520 L1180 1500 Z" fill="#4a5a6a" />
          <path d="M700 520 L620 640 L680 620 L720 680 L760 610 Z M360 640 L320 720 L370 700 L400 740 Z" fill="#dfe8f0" opacity="0.7" />
          <rect y="1500" width="1080" height="420" fill="#20262e" />
          <rect x="160" y="1420" width="760" height="200" rx="30" fill="#6a7a8a" /><rect x="140" y="1300" width="60" height="320" rx="20" fill="#3a2a1e" />
          <g transform="translate(560 1470) rotate(-90)"><!--@person id="g-b-me" x="0" y="0" s="0.55" {ME} mood="sad"--></g>
          <rect x="300" y="1440" width="620" height="140" rx="40" fill="#8a9aaa" />
          <g transform="translate(900 1330)"><rect x="-70" y="-50" width="140" height="100" rx="20" fill="#14161c" /><text x="0" y="16" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="44" fill="#e8412f">07:00</text></g>'''
body = "\n".join([beat("g-a", a, ad, svgA, title("g-a-title", "Depression", top=330, size=130, cls="blue")),
                  beat("g-b", b, bd, svgB, title("g-b-title", "Wie ein Berg", top=330, size=120, cls="blue"))])
js = "\n".join([push("#g-a-cam", a, ad, 1.0, 1.06), rain_js("g-a-cl", a, ad),
                f'    tl.fromTo("#g-a-cl", {{ x: -10 }}, {{ x: 10, duration: 0.8, repeat: 1, yoyo: true, ease: "sine.inOut" }}, {r2(a)});',
                slam("#g-a-title", loc("gefuehl", w("s1", 3)) - 0.1),
                push("#g-b-cam", b, bd, 1.0, 1.06),
                f'    tl.fromTo("#g-b-mtn", {{ scale: 0.85, transformOrigin: "50% 100%" }}, {{ scale: 1.08, duration: {r2(bd)}, ease: "power1.out" }}, {r2(b)});',
                slam("#g-b-title", loc("gefuehl", w("s2", 5)) - 0.1)])
files["gefuehl"] = comp("gefuehl", body, js)

# ===================== ALLTAG: egal, erschöpft, keine Kraft =====================
(a, ad), (b, bd), (c, cd) = beats("alltag", [SC["alltag"][0], st("s4"), st("s5")])
svgA = f'''          <rect width="1080" height="1920" fill="#20262e" />
          <g id="t-a-col">
            <g transform="translate(300 1100) rotate(-20)"><ellipse cx="0" cy="120" rx="120" ry="140" fill="#e88a3c" /><circle cx="0" cy="110" r="40" fill="#3a2a1e" /><rect x="-18" y="-320" width="36" height="320" fill="#6b4a2a" /><rect x="-30" y="-380" width="60" height="70" rx="10" fill="#3a2a1e" /></g>
            <g transform="translate(760 960)"><circle r="120" fill="#f4f1ea" /><path d="M0 -50 l48 34 l-18 56 h-60 l-18 -56 z" fill="#14161c" /></g>
            <g transform="translate(560 1420)"><rect x="-180" y="-70" width="360" height="140" rx="70" fill="#3d7bb3" /><circle cx="-100" cy="0" r="26" fill="#14161c" /><circle cx="100" cy="-20" r="16" fill="#e8412f" /><circle cx="130" cy="14" r="16" fill="#f7c548" /></g>
          </g>
          <rect id="t-a-grey" width="1080" height="1920" fill="#20262e" opacity="0" />'''
svgB = f'''          <rect width="1080" height="1920" fill="#161b22" />
          <g transform="translate(540 1020)"><rect x="-200" y="-110" width="400" height="220" rx="30" fill="none" stroke="#c7ccd6" stroke-width="18" /><rect x="200" y="-40" width="30" height="80" rx="8" fill="#c7ccd6" />
            <rect id="t-b-fill" x="-180" y="-90" width="360" height="180" rx="16" fill="#e8412f" /></g>
          <text x="540" y="1270" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="60" fill="#c7ccd6">10 Std. geschlafen</text>'''
msgs = "".join(f'<g class="t-c-m" transform="translate(0 {i * 130})"><rect x="300" y="640" width="480" height="104" rx="22" fill="#2a3442" /><circle cx="350" cy="692" r="30" fill="{["#3d7bb3", "#e88a3c", "#5f8f5c", "#c96b9a", "#8d93a1"][i % 5]}" />'
               f'<rect x="400" y="668" width="{220 + (i * 37) % 120}" height="18" rx="9" fill="#8d93a1" /><rect x="400" y="700" width="{140 + (i * 53) % 100}" height="14" rx="7" fill="#5a6474" /></g>' for i in range(6))
svgC = f'''          <rect width="1080" height="1920" fill="#12161c" />
          <rect x="260" y="520" width="560" height="1080" rx="60" fill="#05070a" /><rect x="282" y="556" width="516" height="1010" rx="40" fill="#1a212b" />
          {msgs}
          <g transform="translate(790 560)"><g id="t-c-badge"><circle r="56" fill="#e8412f" /><text x="0" y="18" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="50" fill="#fff">27</text></g></g>'''
body = "\n".join([beat("t-a", a, ad, svgA, title("t-a-title", "Egal", top=330, size=170, cls="blue")),
                  beat("t-b", b, bd, svgB, title("t-b-title", "Erschöpft", top=330, size=140, cls="blue")),
                  beat("t-c", c, cd, svgC, title("t-c-title", "Keine Kraft", top=330, size=130, cls="blue"))])
eg = loc("alltag", w("s3", 10))
js = "\n".join([push("#t-a-cam", a, ad, 1.0, 1.06),
                f'    tl.fromTo("#t-a-col", {{ opacity: 1 }}, {{ opacity: 0.25, duration: 1.8, ease: "power1.inOut" }}, {r2(a + 0.6)});',
                f'    tl.fromTo("#t-a-grey", {{ opacity: 0 }}, {{ opacity: 0.35, duration: 1.8 }}, {r2(a + 0.6)});',
                slam("#t-a-title", eg - 0.1),
                push("#t-b-cam", b, bd, 1.0, 1.06),
                f'    tl.fromTo("#t-b-fill", {{ scaleX: 0.6, transformOrigin: "0% 50%" }}, {{ scaleX: 0.04, duration: 1.2, ease: "power2.inOut" }}, {r2(b + 0.2)});',
                slam("#t-b-title", loc("alltag", w("s4", 2)) - 0.1),
                push("#t-c-cam", c, cd, 1.0, 1.05),
                f'    tl.fromTo(".t-c-m", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.2, stagger: 0.3 }}, {r2(c + 0.1)});',
                f'    tl.fromTo("#t-c-badge", {{ scale: 1, transformOrigin: "50% 50%" }}, {{ scale: 1.2, duration: 0.15, repeat: 9, yoyo: true }}, {r2(c + 0.3)});',
                slam("#t-c-title", loc("alltag", w("s5", 13)) - 0.1)])
files["alltag"] = comp("alltag", body, js)

# ===================== KOPF: der Satz – und die Wahrheit =====================
(a, ad), (b, bd) = beats("kopf", [SC["kopf"][0], st("s7")])
head = '<path d="M380 1500 C380 1300 300 1250 300 1060 C300 820 480 680 660 700 C840 720 920 860 900 1000 L960 1110 L900 1130 L910 1230 C900 1290 820 1290 780 1290 L780 1500 Z" fill="#05070a" stroke="#3a4a5a" stroke-width="6" />'
lines = "".join(f'<text class="k-a-l" x="{540 + dx}" y="{y}" text-anchor="middle" font-family="Playfair Display" font-style="italic" font-weight="600" font-size="{fs}" fill="#c7ccd6" opacity="{op}">Ich bin allen nur eine Last.</text>'
                for dx, y, fs, op in [(0, 1000, 54, 0.9), (-30, 900, 40, 0.45), (40, 1100, 40, 0.45), (-20, 820, 30, 0.25), (30, 1180, 30, 0.25)])
svgA = f'''          <rect width="1080" height="1920" fill="#07090d" />
          {head}
          <g clip-path="url(#k-clip)">{lines}</g>
          <defs><clipPath id="k-clip"><path d="M300 700 H960 V1290 H300 Z" /></clipPath></defs>'''
svgB = f'''          <rect width="1080" height="1920" fill="#0b0f16" />
          {head}
          <text x="560" y="1010" text-anchor="middle" font-family="Playfair Display" font-style="italic" font-weight="600" font-size="54" fill="#c7ccd6">Ich bin allen nur eine Last.</text>
          <path id="k-b-x" d="M330 990 L790 1000" stroke="#e8412f" stroke-width="16" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" />
          <circle id="k-b-glow" cx="560" cy="1000" r="300" fill="{GOLD}" opacity="0" />'''
body = "\n".join([beat("k-a", a, ad, svgA),
                  beat("k-b", b, bd, svgB, title("k-b-title", "Das stimmt<br /><span class=\"gold\">nicht</span>", top=330, size=120)
                       + '\n      <div id="k-b-pill" class="pill" style="top: 1500px"><span>Das ist die Krankheit, die da spricht</span></div>')])
js = "\n".join([push("#k-a-cam", a, ad, 1.0, 1.08),
                f'    tl.fromTo(".k-a-l", {{ x: -20, opacity: 0 }}, {{ x: 20, opacity: 0.8, duration: 0.9, repeat: 2, yoyo: true, stagger: 0.25, ease: "sine.inOut" }}, {r2(a + 0.3)});',
                push("#k-b-cam", b, bd, 1.0, 1.04),
                f'    tl.fromTo("#k-b-x", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.3, ease: "power2.in" }}, {r2(loc("kopf", w("s7", 1)))});',
                slam("#k-b-title", loc("kopf", w("s7", 2)) - 0.15),
                f'    tl.fromTo("#k-b-glow", {{ opacity: 0 }}, {{ opacity: 0.12, duration: 0.6 }}, {r2(loc("kopf", w("s7", 2)))});',
                fade("#k-b-pill", loc("kopf", w("s7", 3)))])
files["kopf"] = comp("kopf", body, js)

# ===================== MUT: keine Schwäche, 1 von 5 =====================
(a, ad), (b, bd) = beats("mut", [SC["mut"][0], st("fact")])
svgA = f'''          <rect width="1080" height="1920" fill="#1c2430" />
          <rect y="1800" width="1080" height="120" fill="#151b24" />
          <!--@person id="m-a-me" x="540" y="1860" s="0.9" {ME} mood="neutral"-->
          {cloud("m-a-cl", 540, 1000, 1.0, "#7a8290", False)}'''
icons = "".join(f'<g transform="translate({140 + i * 200} 1240)"><g class="m-b-i" id="m-b-i{i}"><circle cx="0" cy="-200" r="56" fill="{"#ffd25a" if i == 2 else "#4a5666"}" />'
                f'<path d="M-80 0 q0 -110 80 -110 q80 0 80 110 z" fill="{"#ffd25a" if i == 2 else "#4a5666"}" /></g></g>' for i in range(5))
svgB = f'''          <rect width="1080" height="1920" fill="#141c26" />
          {icons}'''
body = "\n".join([beat("m-a", a, ad, svgA, title("m-a-title", "Keine Schwäche", top=330, size=110, cls="gold")),
                  beat("m-b", b, bd, svgB, title("m-b-title", '1 von <span class="gold">5</span>', top=330, size=170)
                       + '\n      <div id="m-b-chip" class="pill" style="top: 1420px"><span style="border-color: #7fe0a0; font-size: 52px">Gut behandelbar ✓</span></div>')])
js = "\n".join([push("#m-a-cam", a, ad, 1.0, 1.05),
                f'    tl.fromTo("#m-a-cl", {{ scale: 1, opacity: 1, transformOrigin: "50% 50%" }}, {{ scale: 0.55, opacity: 0.4, duration: {r2(ad)}, ease: "power1.inOut" }}, {r2(a)});',
                slam("#m-a-title", loc("mut", w("s8", 3)) - 0.15),
                push("#m-b-cam", b, bd, 1.0, 1.04),
                f'    tl.fromTo(".m-b-i", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.25, stagger: 0.12 }}, {r2(b + 0.1)});',
                f'    tl.fromTo("#m-b-i2", {{ scale: 1, transformOrigin: "50% 100%" }}, {{ scale: 1.15, duration: 0.3, repeat: 3, yoyo: true }}, {r2(loc("mut", w("fact", 2)))});',
                slam("#m-b-title", loc("mut", w("fact", 2)) - 0.15),
                popc("#m-b-chip", loc("mut", w("fact", 15)) - 0.1)])
files["mut"] = comp("mut", body, js)

# ===================== HILFE: reden – Vertrauensperson, Hausarzt, Telefon =====================
(a, ad), (b, bd) = beats("hilfe", [SC["hilfe"][0], st("s10")])
svgA = f'''          <defs><radialGradient id="r-a-gl" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffcf8a" stop-opacity="0.35" /><stop offset="1" stop-color="#ff8a3c" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#1e2632" />
          <circle cx="540" cy="1200" r="600" fill="url(#r-a-gl)" />
          <rect y="1800" width="1080" height="120" fill="#161c24" />
          <!--@person id="r-a-me" x="380" y="1860" s="0.85" {ME} mood="sad"-->
          <!--@person id="r-a-fr" x="700" y="1860" s="0.85" jacket="#5f8f5c" hair="#1e140c" skin="#c98d62" style="long" mood="neutral"-->
          <rect x="140" y="1640" width="800" height="40" rx="10" fill="#6b4a2a" /><rect x="180" y="1680" width="24" height="140" fill="#4a3220" /><rect x="876" y="1680" width="24" height="140" fill="#4a3220" />
          <g id="r-a-b1"><path d="M560 760 h300 q30 0 30 30 v90 q0 30 -30 30 h-200 l-50 46 l8 -46 h-58 q-30 0 -30 -30 v-90 q0 -30 30 -30 z" fill="#f4efe4" /><g fill="#8d93a1"><rect x="600" y="800" width="220" height="16" rx="8" /><rect x="600" y="836" width="160" height="16" rx="8" /></g></g>
          <g id="r-a-b2"><path d="M200 900 h280 q30 0 30 30 v80 q0 30 -30 30 h-180 l-50 46 l8 -46 h-58 q-30 0 -30 -30 v-80 q0 -30 30 -30 z" fill="#bfe0ff" /><g fill="#5a7a9a"><rect x="236" y="936" width="200" height="16" rx="8" /><rect x="236" y="970" width="140" height="16" rx="8" /></g></g>'''
items = [("heart", "Vertrauensperson", 0), ("steth", "Hausarzt / Hausärztin", 6), ("phone", "Anonym am Telefon", 12)]
ico = {"heart": '<path d="M0 50 l-70 -70 a40 40 0 0 1 70 -50 a40 40 0 0 1 70 50 z" fill="#e8412f" />',
       "steth": '<path d="M-50 -60 v50 q0 50 50 50 q50 0 50 -50 v-50" stroke="#7fb0d8" stroke-width="16" fill="none" stroke-linecap="round" /><path d="M0 40 v30 q0 40 50 40 q40 0 40 -40" stroke="#7fb0d8" stroke-width="16" fill="none" /><circle cx="90" cy="60" r="22" fill="#7fb0d8" />',
       "phone": '<path d="M-60 -60 q-20 20 0 70 q40 80 120 120 q50 20 70 0 l14 -30 l-50 -40 l-30 26 q-50 -24 -80 -80 l26 -30 l-40 -50 z" fill="#7fe0a0" />'}
rows = "".join(f'<g class="r-b-row" id="r-b-row{i}" transform="translate(0 {i * 260 - 200})"><rect x="120" y="620" width="840" height="240" rx="30" fill="#1a222e" stroke="#3a4a5a" stroke-width="4" />'
               f'<g transform="translate(260 740)">{ico[k]}</g><text x="400" y="760" font-family="Montserrat" font-weight="800" font-size="46" fill="#f4f1ea">{lab}</text></g>' for i, (k, lab, _) in enumerate(items))
svgB = f'''          <rect width="1080" height="1920" fill="#141a22" />
          {rows}'''
body = "\n".join([beat("r-a", a, ad, svgA, title("r-a-title", "Reden", top=330, size=170, cls="gold")), beat("r-b", b, bd, svgB)])
js = [push("#r-a-cam", a, ad, 1.0, 1.05), popc("#r-a-b1", a + 0.4), popc("#r-a-b2", a + 1.1), slam("#r-a-title", loc("hilfe", w("s9", 7)) - 0.15),
      push("#r-b-cam", b, bd, 1.0, 1.04)]
for i, (_, _, wi) in enumerate(items):
    js.append(f'    tl.fromTo("#r-b-row{i}", {{ opacity: 0, x: -80 }}, {{ opacity: 1, x: 0, duration: 0.3, ease: "power3.out" }}, {r2(loc("hilfe", w("s10", wi)) - 0.05)});')
files["hilfe"] = comp("hilfe", body, "\n".join(js))

# ===================== NUMMERN: TelefonSeelsorge, 112 =====================
(a, ad), (b, bd) = beats("nummern", [SC["nummern"][0], st("s11")])
svgA = '''          <rect width="1080" height="1920" fill="#101820" />
          <circle cx="540" cy="900" r="520" fill="#ffd25a" opacity="0.06" />
          <g fill="none" stroke="#ffd25a" stroke-width="5" opacity="0.25"><circle cx="540" cy="1500" r="120" /><circle cx="540" cy="1500" r="200" /><circle cx="540" cy="1500" r="280" /></g>'''
cardA = '''      <div id="n-a-card" class="card" style="top: 520px">
        <div class="h">TelefonSeelsorge</div>
        <div class="n">0800 111 0 111</div>
        <div class="s">oder 0800 111 0 222 · 116 123</div>
        <div class="s" style="margin-top: 18px; color: #ffd25a">24/7 · kostenlos · anonym</div>
      </div>'''
svgB = '''          <rect width="1080" height="1920" fill="#160c0c" />
          <circle cx="540" cy="900" r="520" fill="#e8412f" opacity="0.08" />'''
cardB = '''      <div id="n-b-card" class="card" style="top: 560px; border-color: #e8412f">
        <div class="h" style="color: #ff6a55">Akute Gefahr</div>
        <div class="n" style="font-size: 220px; color: #ff6a55">112</div>
        <div class="s">Notruf · sofort · überall in Europa</div>
      </div>'''
body = "\n".join([beat("n-a", a, ad, svgA, cardA), beat("n-b", b, bd, svgB, cardB)])
js = "\n".join([push("#n-a-cam", a, ad, 1.0, 1.08), push("#n-b-cam", b, bd, 1.0, 1.08),
                f'    tl.fromTo("#n-a-card .s", {{ opacity: 0.6 }}, {{ opacity: 1, duration: 0.8, repeat: 5, yoyo: true }}, {r2(a + 0.6)});',
                f'    tl.fromTo("#n-a-card", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }}, {r2(a + 0.1)});',
                f'    tl.fromTo("#n-a-card .n", {{ scale: 1, transformOrigin: "50% 50%" }}, {{ scale: 1.06, duration: 0.25, repeat: 3, yoyo: true }}, {r2(loc("nummern", w("help", 13)) - 0.05)});',
                f'    tl.fromTo("#n-b-card", {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(1.8)" }}, {r2(b + 0.05)});',
                f'    tl.fromTo("#n-b-card .n", {{ scale: 1, transformOrigin: "50% 50%" }}, {{ scale: 1.08, duration: 0.25, repeat: 3, yoyo: true }}, {r2(loc("nummern", w("s11", 9)) - 0.05)});'])
files["nummern"] = comp("nummern", body, js)

# ===================== ENDE: nicht allein + Hilfe-Karte =====================
(a, ad), (b, bd) = beats("ende", [SC["ende"][0], st("cta")])
svgA = f'''          <defs><linearGradient id="e-a-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a3a5a" /><stop offset="0.6" stop-color="#e8a05a" /><stop offset="1" stop-color="#ffd28a" /></linearGradient>
            <radialGradient id="e-a-sun" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff6dc" stop-opacity="1" /><stop offset="0.3" stop-color="{GOLD}" stop-opacity="0.7" /><stop offset="1" stop-color="{GOLD}" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="url(#e-a-sky)" />
          <circle id="e-a-sun" cx="540" cy="1280" r="560" fill="url(#e-a-sun)" />
          <path d="M0 1800 Q540 1720 1080 1800 V1920 H0 Z" fill="#3a3040" />
          <!--@person id="e-a-me" x="540" y="1860" s="0.9" {ME} mood="happy"-->
          {cloud("e-a-cl", 540, 1000, 0.9, "#9aa2ae", False)}'''
res = '''      <div id="e-b-res" class="res" style="top: 300px">
        <div class="t">📸 Hilfe – mach einen Screenshot</div>
        <div class="r"><span class="l">TelefonSeelsorge<br />24/7 · kostenlos · anonym</span><span class="v">0800 111 0 111<small>0800 111 0 222 · 116 123</small></span></div>
        <div class="r"><span class="l">Info-Telefon Depression</span><span class="v">0800 33 44 533</span></div>
        <div class="r"><span class="l">Nummer gegen Kummer<br />Kinder &amp; Jugendliche</span><span class="v">116 111</span></div>
        <div class="r"><span class="l">Österreich · Schweiz</span><span class="v">142 · 143</span></div>
        <div class="r"><span class="l" style="color: #ff6a55">Akute Gefahr</span><span class="v" style="color: #ff6a55">112</span></div>
      </div>'''
svgB = '''          <rect width="1080" height="1920" fill="#0e141c" />
          <circle cx="540" cy="800" r="640" fill="#ffd25a" opacity="0.05" />'''
body = "\n".join([beat("e-a", a, ad, svgA, title("e-a-title", 'Du bist nicht<br /><span class="gold">allein</span>', top=330, size=120)), beat("e-b", b, bd, svgB, res)])
js = "\n".join([f'    tl.fromTo("#e-a-cam", {{ scale: 1.08 }}, {{ scale: 1.0, duration: {r2(ad)}, ease: "power2.out" }}, {r2(a)});',
                f'    tl.fromTo("#e-a-sun", {{ y: 160 }}, {{ y: 0, duration: {r2(ad)}, ease: "power1.out" }}, {r2(a)});',
                f'    tl.fromTo("#e-a-cl", {{ opacity: 0.9, x: 0 }}, {{ opacity: 0, x: 300, duration: {r2(ad * 0.8)}, ease: "power1.in" }}, {r2(a + 0.2)});',
                slam("#e-a-title", loc("ende", w("end", 3)) - 0.15),
                f'    tl.fromTo("#e-b-res", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: "power3.out" }}, {r2(b + 0.05)});',
                f'    tl.fromTo("#e-b-res .r", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.25, stagger: 0.15 }}, {r2(b + 0.3)});'])
files["ende"] = comp("ende", body, js)

for n, html in files.items():
    open(os.path.join(P, "compositions", n + ".html"), "w").write(html)

g = lambda n: SC[n][0]
sfx = [["sfx-w1", "whoosh-cinematic", st("hook2"), 0.2], ["sfx-wa", "impact-bass-2", w("hook2", 8), 0.18],
       ["sfx-w2", "whoosh", g("gefuehl"), 0.18], ["sfx-dep", "impact-bass-1", w("s1", 3), 0.16], ["sfx-w3", "whoosh-short", st("s2"), 0.16],
       ["sfx-w4", "whoosh", g("alltag"), 0.16], ["sfx-w5", "whoosh-short", st("s4"), 0.16], ["sfx-w6", "whoosh-short", st("s5"), 0.16],
       ["sfx-w7", "whoosh", g("kopf"), 0.16], ["sfx-x", "impact-bass-2", w("s7", 2), 0.2],
       ["sfx-w8", "whoosh", g("mut"), 0.18], ["sfx-w9", "whoosh-short", st("fact"), 0.16], ["sfx-ok", "pop", w("fact", 15), 0.5],
       ["sfx-w10", "whoosh", g("hilfe"), 0.18], ["sfx-p1", "pop", w("s10", 0), 0.4], ["sfx-p2", "pop", w("s10", 6), 0.4], ["sfx-p3", "pop", w("s10", 12), 0.4],
       ["sfx-w11", "whoosh-cinematic", g("nummern"), 0.18], ["sfx-w12", "whoosh-short", st("s11"), 0.18],
       ["sfx-w13", "whoosh-cinematic", g("ende"), 0.2], ["sfx-w14", "whoosh-short", st("cta"), 0.18]]
sfx = [[a_, b_, round(t, 2), v] for a_, b_, t, v in sfx]
json.dump({"total": TOTAL, "scenes": [[n, SC[n][0], SC[n][1]] for n, _ in order], "sfx": sfx}, open(os.path.join(P, "scenes.json"), "w"), indent=1)
print("Szenen:", ", ".join(f"{n} {SC[n][0]}+{SC[n][1]}" for n, _ in order), "| Länge", TOTAL)
