# Erzeugt alle Szenen (compositions/*.html) und scenes.json aus assets/timing.json.
# Neue Stimme → place_voice.py → dieses Skript → build_index.py →
# build_captions.py . --style legende --skip s3,s7 --key-color "#ffd25a"
# Bewusst ohne Gesichter/Figuren: nur Symbole (Tür, Laterne, Tasbih, Kette, Moschee-Silhouette).
import json, random, os, math

P = os.path.dirname(os.path.abspath(__file__))
tm = json.load(open(os.path.join(P, "assets/timing.json")))
L = {l["id"]: l for l in (tm["lines"] if isinstance(tm, dict) else tm)}
w = lambda lid, i: L[lid]["words"][i]["start"]
st = lambda lid: round(L[lid]["start"] - 0.12, 2)
r2 = lambda x: f"{x:.2f}"

order = [("hook", 0.0), ("scham", st("s1")), ("hadith", st("s2")), ("kampf", st("s4")), ("tuer", st("s6")), ("koran", st("s7")),
         ("disziplin", st("s8")), ("tasbih", st("s10")), ("weg", st("s11")), ("frei", st("s12")), ("ende", st("end"))]
TOTAL = round(L["cta"]["end"] + 3.4, 2)
SC = {}
for i, (n, s) in enumerate(order):
    e = order[i + 1][1] if i + 1 < len(order) else TOTAL
    SC[n] = (s, round(e - s, 2))
loc = lambda sc, t: round(t - SC[sc][0], 2)


def beats(sc, starts):
    s0, d = SC[sc]
    l = [round(x - s0, 2) for x in starts] + [d]
    return [(l[i], round(l[i + 1] - l[i], 2)) for i in range(len(starts))]


GOLD, GOLD_D, INK = "#ffd25a", "#7a4a0a", "#f4f1ea"
CSS_BASE = f'''    #root {{ position: absolute; inset: 0; background: #050a10; }}
    .beat {{ position: absolute; inset: 0; overflow: hidden; }}
    .lt {{ font-family: "Montserrat", sans-serif; font-weight: 800; text-transform: uppercase; }}
    .gold {{ color: {GOLD}; text-shadow: 0 6px 0 {GOLD_D}, 0 0 50px rgba(255, 190, 80, 0.45); }}
    .red {{ color: #e8412f; text-shadow: 0 6px 0 #5a1208, 0 0 40px rgba(232, 65, 47, 0.4); }}
    .quote {{ position: absolute; left: 90px; width: 900px; text-align: center; padding: 50px 44px 40px; border-radius: 18px;
      background: rgba(6, 12, 18, 0.78); border: 3px solid rgba(255, 210, 90, 0.75); box-shadow: 0 0 60px rgba(0,0,0,.5);
      font-family: "Playfair Display", Georgia, serif; font-style: italic; font-weight: 600; font-size: 58px; line-height: 1.25; color: {INK}; }}
    .quote .q {{ display: inline; }}
    .quote .k {{ color: {GOLD}; }}
    .quote .src {{ display: block; margin-top: 26px; font-family: "Montserrat", sans-serif; font-style: normal; font-weight: 800;
      font-size: 30px; letter-spacing: 0.12em; text-transform: uppercase; color: {GOLD}; }}
    .pill {{ position: absolute; left: 0; width: 1080px; text-align: center; }}
    .pill span {{ display: inline-block; padding: 14px 34px; border-radius: 18px; background: rgba(10, 14, 18, 0.88);
      border: 3px solid {GOLD}; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 40px; color: {INK}; }}'''


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
fade = lambda sel, t, dur=0.5: f'    tl.fromTo("{sel}", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: {dur}, ease: "power2.out" }}, {r2(t)});'
slam = lambda sel, t: f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 1.5, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.25, ease: "power3.in" }}, {r2(t)});'


def star8(x, y, r, fill="none", stroke=GOLD, sw=3, op=0.18, cls=""):
    s = r * 0.72
    return (f'<g transform="translate({x} {y})" opacity="{op}" class="{cls}"><rect x="{-s:.0f}" y="{-s:.0f}" width="{2 * s:.0f}" height="{2 * s:.0f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" />'
            f'<rect x="{-s:.0f}" y="{-s:.0f}" width="{2 * s:.0f}" height="{2 * s:.0f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" transform="rotate(45)" /></g>')


def pattern(y0, y1, step=180, op=0.08):
    return "".join(star8(x + (row % 2) * step / 2, y, step * 0.42, op=op) for row, y in enumerate(range(y0, y1, step)) for x in range(0, 1181, step))


def arch(x, yb, wdt, h, spring):
    hw = wdt / 2
    return (f"M{x - hw} {yb} V{spring} C{x - hw} {spring - h * 0.55:.0f} {x - wdt * 0.1:.0f} {spring - h * 0.8:.0f} {x} {spring - h} "
            f"C{x + wdt * 0.1:.0f} {spring - h * 0.8:.0f} {x + hw} {spring - h * 0.55:.0f} {x + hw} {spring} V{yb} Z")


def mosque(x, y, s, col):
    return f'''<g transform="translate({x} {y}) scale({s})" fill="{col}">
            <rect x="-260" y="-160" width="520" height="160" /><path d="M-170 -160 q0 -190 170 -200 q170 10 170 200 z" /><rect x="-6" y="-420" width="12" height="70" /><circle cx="0" cy="-430" r="14" />
            <path d="M-250 -160 q0 -90 70 -96 q70 6 70 96 z" /><path d="M110 -160 q0 -90 70 -96 q70 6 70 96 z" />
            <rect x="-360" y="-520" width="44" height="520" /><path d="M-370 -520 h64 l-32 -80 z" /><rect x="-372" y="-400" width="68" height="16" />
            <rect x="316" y="-520" width="44" height="520" /><path d="M306 -520 h64 l-32 -80 z" /><rect x="304" y="-400" width="68" height="16" /></g>'''


def crescent(x, y, r, col=GOLD, mid="moon"):
    return (f'<defs><mask id="{mid}"><circle cx="{x}" cy="{y}" r="{r}" fill="#fff" /><circle cx="{x + r * 0.38:.0f}" cy="{y - r * 0.18:.0f}" r="{r * 0.86:.0f}" fill="#000" /></mask></defs>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}" mask="url(#{mid})" />')


def stars(rng, n, y1=900, cls="st"):
    return "".join(f'<circle class="{cls}" cx="{rng.uniform(0, 1080):.0f}" cy="{rng.uniform(0, y1):.0f}" r="{rng.uniform(1.2, 3.4):.1f}" fill="#fff6dc" opacity="{rng.uniform(.3, .9):.2f}" />' for _ in range(n))


def lantern(x, y, s, gid):
    return f'''<g transform="translate({x} {y}) scale({s})"><path d="M0 -260 v60" stroke="#8a6a2a" stroke-width="6" />
            <path d="M-50 -200 h100 l20 40 h-140 z" fill="#b8892e" /><path d="M-70 -160 h140 l-20 200 h-100 z" fill="#3a2a10" />
            <g id="{gid}"><path d="M-56 -150 h112 l-16 180 h-80 z" fill="#ffb84a" opacity="0.9" /><ellipse cx="0" cy="-60" rx="22" ry="40" fill="#fff2c4" /></g>
            <path d="M-60 -150 l40 180 M60 -150 l-40 180 M0 -160 v200" stroke="#b8892e" stroke-width="6" fill="none" />
            <path d="M-50 40 h100 l-14 30 h-72 z" fill="#b8892e" /></g>'''


files = {}

# ===================== HOOK: das letzte Mal → wieder =====================
(a, ad), (b, bd) = beats("hook", [0.0, st("hook2")])
svgA = f'''          <defs><radialGradient id="h-lamp" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffcf8a" stop-opacity="0.55" /><stop offset="1" stop-color="#ff8a3c" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#0b1118" />
          {pattern(0, 1920, op=0.05)}
          <circle cx="540" cy="900" r="620" fill="url(#h-lamp)" />
          <rect x="190" y="560" width="700" height="900" rx="14" fill="#1c2733" stroke="#3a4a58" stroke-width="14" />
          <rect x="214" y="584" width="652" height="852" fill="#24323f" />
          <path d="M260 640 L460 1380" stroke="#fff" stroke-width="30" opacity="0.05" />
          <g transform="translate(560 960) rotate(-4)"><g id="h-note"><rect x="-230" y="-190" width="460" height="380" fill="#f7e27a" /><rect x="-230" y="-190" width="460" height="40" fill="#e9cd5a" />
            <text x="0" y="-40" text-anchor="middle" font-family="Playfair Display" font-style="italic" font-weight="600" font-size="58" fill="#2a2010">Das war das</text>
            <text x="0" y="50" text-anchor="middle" font-family="Playfair Display" font-style="italic" font-weight="600" font-size="58" fill="#2a2010">letzte Mal.</text>
            <path d="M-150 100 q150 30 300 -10" stroke="#2a2010" stroke-width="6" fill="none" /></g></g>'''
svgB = f'''          <rect width="1080" height="1920" fill="#08090c" />
          <circle cx="540" cy="1000" r="460" fill="#2a0e0a" opacity="0.6" />
          <g transform="translate(540 1000)"><rect x="-300" y="-220" width="600" height="440" rx="30" fill="#14161c" stroke="#3a3f4b" stroke-width="8" />
            <text x="0" y="-120" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="44" fill="#8e939d" letter-spacing="6">TAGE OHNE</text>
            <g id="h-n1"><text x="0" y="120" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="230" fill="{GOLD}">6</text></g>
            <g id="h-n0" opacity="0"><text x="0" y="120" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="230" fill="#e8412f">0</text></g>
            <path id="h-crack" d="M-300 -60 L-120 -10 L-40 -90 L60 20 L160 -40 L300 30" stroke="#e8412f" stroke-width="8" fill="none" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" /></g>'''
body = "\n".join([beat("h-a", a, ad, svgA), beat("h-b", b, bd, svgB, title("h-b-title", "Wieder.", top=330, size=170, cls="red"))])
wd = loc("hook", w("hook2", 4))
js = "\n".join([f'    tl.fromTo("#h-a-cam", {{ scale: 1.12 }}, {{ scale: 1.0, duration: {r2(ad)}, ease: "power2.out" }}, {r2(a)});',
                f'    tl.fromTo("#h-note", {{ rotation: 0, transformOrigin: "50% 0%" }}, {{ rotation: 2, duration: 0.8, repeat: 2, yoyo: true, ease: "sine.inOut" }}, {r2(a)});',
                push("#h-b-cam", b, bd, 1.0, 1.08),
                f'    tl.fromTo("#h-n1", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.08 }}, {r2(wd - 0.05)});',
                f'    tl.fromTo("#h-n0", {{ opacity: 0, scale: 1.4, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.15, ease: "power3.in" }}, {r2(wd - 0.02)});',
                f'    tl.fromTo("#h-crack", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.2, ease: "power2.in" }}, {r2(wd)});',
                f'    tl.fromTo("#h-b-cam", {{ x: 0 }}, {{ x: 12, duration: 0.04, repeat: 5, yoyo: true }}, {r2(wd + 0.12)});',
                slam("#h-b-title", wd)])
files["hook"] = comp("hook", body, js)

# ===================== SCHAM: Regen am Fenster, leerer Gebetsteppich =====================
rng = random.Random(1)
s0, d = SC["scham"]
rain = "".join(f'<line class="sc-r" x1="{x:.0f}" y1="{y:.0f}" x2="{x - 10:.0f}" y2="{y + 60:.0f}" stroke="#9fc4e0" stroke-width="3" opacity="{rng.uniform(.25, .6):.2f}" />' for x, y in [(rng.uniform(240, 860), rng.uniform(440, 1100)) for _ in range(60)])
svg = f'''          <rect width="1080" height="1920" fill="#070c14" />
          <path d="{arch(540, 1150, 620, 300, 640)}" fill="#0e1e30" stroke="#2a3a4a" stroke-width="16" />
          <g clip-path="url(#sc-clip)">{rain}</g>
          <defs><clipPath id="sc-clip"><path d="{arch(540, 1150, 620, 300, 640)}" /></clipPath></defs>
          <path d="M540 340 V1150 M230 760 H850" stroke="#2a3a4a" stroke-width="12" />
          <rect x="0" y="1150" width="1080" height="770" fill="#0b121a" />
          <g transform="translate(540 1560)"><path d="M-260 -60 L260 -60 L330 140 L-330 140 Z" fill="#5a1a22" />
            <path d="M-220 -40 L220 -40 L280 120 L-280 120 Z" fill="none" stroke="{GOLD}" stroke-width="5" opacity="0.6" />
            <path d="M-60 -40 q60 -60 120 0" fill="none" stroke="{GOLD}" stroke-width="5" opacity="0.6" />
            {"".join(f'<line x1="{x}" y1="140" x2="{x - 6}" y2="164" stroke="#c9a96a" stroke-width="4" />' for x in range(-320, 330, 24))}</g>
          <ellipse cx="540" cy="1100" rx="420" ry="220" fill="#9fc4e0" opacity="0.04" />'''
js = "\n".join([push("#sc-a-cam", 0, d, 1.0, 1.08),
                f'    tl.fromTo(".sc-r", {{ y: -200 }}, {{ y: 500, duration: 0.9, repeat: {int(d / 0.9) + 1}, ease: "none", stagger: {{ each: 0.015, repeat: -1 }} }}, 0);'.replace(', stagger: { each: 0.015, repeat: -1 }', ', stagger: 0.015')])
files["scham"] = comp("scham", beat("sc-a", 0, d, svg), js)

# ===================== HADITH 1: Moschee im Morgenlicht + Zitat =====================
(a, ad), (b, bd) = beats("hadith", [SC["hadith"][0], st("s3")])
svg = f'''          <defs><linearGradient id="hd-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c1a2e" /><stop offset="0.55" stop-color="#5a4a6a" /><stop offset="0.8" stop-color="#e8a05a" /><stop offset="1" stop-color="#ffd28a" /></linearGradient>
            <radialGradient id="hd-sun" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff2c8" stop-opacity="0.9" /><stop offset="1" stop-color="#ffb35c" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="url(#hd-sky)" />
          {stars(random.Random(2), 50, 800, "hd-st")}
          <circle id="hd-sun" cx="540" cy="1560" r="520" fill="url(#hd-sun)" />
          {mosque(540, 1600, 1.15, "#0d1520")}
          <rect x="0" y="1600" width="1080" height="320" fill="#0d1520" />'''
q1 = loc("hadith", L["s3"]["start"]); q2 = loc("hadith", w("s3", 5))
quote = f'''      <div id="hd-q" class="quote" style="top: 380px">
        <span id="hd-q1" class="q">„Alle Kinder Adams machen Fehler.</span>
        <span id="hd-q2" class="q">Und die Besten von ihnen sind die, die <span class="k">bereuen</span>.“</span>
        <span id="hd-src" class="src">Überliefert bei at-Tirmidhi</span>
      </div>'''
pre = title("hd-pre", "Der Prophet ﷺ sagte", top=330, size=60)
body = beat("hd-a", 0, SC["hadith"][1], svg, pre.replace("ﷺ", "<span style=\"font-family: 'Amiri', serif; text-transform: none\">ﷺ</span>") + "\n" + quote)
js = "\n".join([push("#hd-a-cam", 0, SC["hadith"][1], 1.0, 1.08),
                f'    tl.fromTo("#hd-sun", {{ y: 120 }}, {{ y: 0, duration: {r2(SC["hadith"][1])}, ease: "power1.out" }}, 0);',
                fade("#hd-pre", 0.1),
                f'    tl.to("#hd-pre", {{ opacity: 0, duration: 0.3 }}, {r2(q1 - 0.35)});',
                f'    tl.fromTo("#hd-q", {{ opacity: 0, scale: 0.96 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "power2.out" }}, {r2(q1 - 0.2)});',
                f'    tl.fromTo("#hd-q1", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {r2(q1 - 0.05)});',
                f'    tl.fromTo("#hd-q2", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {r2(q2 - 0.05)});',
                f'    tl.fromTo("#hd-src", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {r2(q2 + 0.4)});',
                f'    tl.fromTo(".hd-st", {{ opacity: 0.2 }}, {{ opacity: 0.9, duration: 0.6, repeat: 7, yoyo: true, stagger: 0.03 }}, 0);'])
files["hadith"] = comp("hadith", body, js)

# ===================== KAMPF: kein Sprint, fallen & aufstehen =====================
(a, ad), (b, bd) = beats("kampf", [SC["kampf"][0], st("s5")])
road = "M540 1820 Q160 1720 420 1600 T560 1400 T420 1250 T540 1100 T500 1010"
svgA = f'''          <defs><linearGradient id="k-a-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c1424" /><stop offset="0.6" stop-color="#3a3a5a" /><stop offset="1" stop-color="#c26a4a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#k-a-sky)" />
          {stars(random.Random(3), 40, 700, "k-st")}
          <path d="M0 1100 L220 760 L400 900 L560 620 L760 860 L900 740 L1080 940 V1920 H0 Z" fill="#1c2236" />
          <path d="M0 1300 L260 1020 L520 1180 L780 980 L1080 1200 V1920 H0 Z" fill="#141a2a" />
          <path d="{road}" stroke="#c9a96a" stroke-width="30" fill="none" stroke-linejoin="round" opacity="0.7" />
          <path id="k-a-walk" d="{road}" stroke="{GOLD}" stroke-width="12" fill="none" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" />
          {crescent(860, 560, 60, GOLD, "k-moon")}'''
steps = "".join(f'<rect x="{140 + i * 110}" y="{1700 - i * 110}" width="{940 - i * 110}" height="{110 * (i + 1) + 120}" fill="{["#1a2234", "#1e2840", "#222e48", "#263450", "#2a3a58", "#2e405e"][i]}" /><rect x="{140 + i * 110}" y="{1700 - i * 110}" width="{940 - i * 110}" height="10" fill="#c9a96a" opacity="0.5" />' for i in range(6))
svgB = f'''          <defs><radialGradient id="k-b-orb" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff2c4" stop-opacity="1" /><stop offset="0.35" stop-color="{GOLD}" stop-opacity="0.8" /><stop offset="1" stop-color="{GOLD}" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#0a1020" />
          {pattern(0, 1100, op=0.05)}
          {steps}
          <g transform="translate(200 1650)"><g id="k-b-orb"><circle r="110" fill="url(#k-b-orb)" /><circle r="26" fill="#fff6dc" /></g></g>'''
f1, u1, f2, u2 = (loc("kampf", w("s5", i)) for i in (1, 4, 6, 11))
step_xy = lambda i: (i * 110 + 60, -i * 110)
body = "\n".join([beat("k-a", a, ad, svgA, title("k-a-title", "Kein Sprint", top=330, size=140, cls="gold")),
                  beat("k-b", b, bd, svgB, title("k-b-title", "Aufstehen", top=330, size=140, cls="gold"))])
x2, y2 = step_xy(2); x4, y4 = step_xy(4); x3, y3 = step_xy(3); x6, y6 = step_xy(6)
js = "\n".join([push("#k-a-cam", a, ad, 1.0, 1.1),
                f'    tl.fromTo("#k-a-walk", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0.25, duration: {r2(ad)}, ease: "power1.inOut" }}, {r2(a)});',
                slam("#k-a-title", loc("kampf", w("s4", 1)) - 0.1),
                push("#k-b-cam", b, bd, 1.0, 1.05),
                f'    tl.fromTo("#k-b-orb", {{ x: 0, y: 0 }}, {{ x: {x2}, y: {y2}, duration: {r2(f1 - b - 0.1)}, ease: "power1.inOut" }}, {r2(b)});',
                f'    tl.to("#k-b-orb", {{ x: 0, y: 0, duration: 0.35, ease: "bounce.out" }}, {r2(f1)});',
                f'    tl.to("#k-b-orb", {{ x: {x3}, y: {y3}, duration: {r2(f2 - u1 - 0.1)}, ease: "power1.inOut" }}, {r2(u1 - 0.2)});',
                f'    tl.to("#k-b-orb", {{ x: {x2 - 110}, y: {y2 + 110}, duration: 0.35, ease: "bounce.out" }}, {r2(f2)});',
                f'    tl.to("#k-b-orb", {{ x: {x6 - 40}, y: {y6 - 60}, scale: 1.6, duration: {r2(bd - (u2 - b) - 0.1)}, ease: "power2.out" }}, {r2(u2 - 0.3)});',
                slam("#k-b-title", u2 - 0.1)])
files["kampf"] = comp("kampf", body, js)

# ===================== TÜR: die Tür ist offen =====================
s0, d = SC["tuer"]
op = loc("tuer", w("s6", 10))
svg = f'''          <defs><radialGradient id="t-light" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff2c4" stop-opacity="1" /><stop offset="0.4" stop-color="{GOLD}" stop-opacity="0.7" /><stop offset="1" stop-color="{GOLD}" stop-opacity="0" /></radialGradient>
            <clipPath id="t-clip"><path d="{arch(540, 1640, 520, 260, 900)}" /></clipPath></defs>
          <rect width="1080" height="1920" fill="#0a0f18" />
          {pattern(0, 1920, op=0.06)}
          <path d="{arch(540, 1660, 600, 300, 900)}" fill="#3a2e22" />
          <g clip-path="url(#t-clip)"><rect x="200" y="500" width="680" height="1200" fill="#fff2c4" /><circle id="t-glow" cx="540" cy="1200" r="600" fill="url(#t-light)" /></g>
          <g clip-path="url(#t-clip)">
            <g transform="translate(280 0)"><g id="t-l"><rect x="0" y="560" width="260" height="1100" fill="#5a3a1e" stroke="#2a1a0c" stroke-width="8" />
              {star8(130, 1000, 70, "none", GOLD, 6, 0.8)}<rect x="30" y="1220" width="200" height="340" fill="none" stroke="#c9a96a" stroke-width="6" opacity="0.6" /></g></g>
            <g transform="translate(800 0)"><g id="t-r"><rect x="-260" y="560" width="260" height="1100" fill="#5a3a1e" stroke="#2a1a0c" stroke-width="8" />
              {star8(-130, 1000, 70, "none", GOLD, 6, 0.8)}<rect x="-230" y="1220" width="200" height="340" fill="none" stroke="#c9a96a" stroke-width="6" opacity="0.6" /></g></g></g>
          <rect x="0" y="1660" width="1080" height="260" fill="#14100c" />
          <path id="t-floor" d="M290 1660 L790 1660 L1000 1920 L80 1920 Z" fill="{GOLD}" opacity="0" />'''
js = "\n".join([push("#t-a-cam", 0, d, 1.0, 1.1),
                f'    tl.fromTo("#t-l", {{ scaleX: 1, transformOrigin: "0% 50%" }}, {{ scaleX: 0.12, duration: 0.9, ease: "power2.inOut" }}, {r2(op - 0.5)});',
                f'    tl.fromTo("#t-r", {{ scaleX: 1, transformOrigin: "100% 50%" }}, {{ scaleX: 0.12, duration: 0.9, ease: "power2.inOut" }}, {r2(op - 0.5)});',
                f'    tl.fromTo("#t-floor", {{ opacity: 0 }}, {{ opacity: 0.35, duration: 0.8 }}, {r2(op - 0.3)});',
                f'    tl.fromTo("#t-glow", {{ scale: 0.6, transformOrigin: "50% 50%" }}, {{ scale: 1.2, duration: 1.2, ease: "power2.out" }}, {r2(op - 0.3)});',
                slam("#t-title", op)])
files["tuer"] = comp("tuer", beat("t-a", 0, d, svg, title("t-title", "Offen", top=330, size=170, cls="gold")), js)

# ===================== KORAN: Sternennacht, geschlossener Mushaf, Zitat 39:53 =====================
s0, d = SC["koran"]
svg = f'''          <defs><radialGradient id="kq-glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{GOLD}" stop-opacity="0.5" /><stop offset="1" stop-color="{GOLD}" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#060b14" />
          {stars(random.Random(4), 120, 1920, "kq-st")}
          {crescent(860, 250, 70, GOLD, "kq-moon")}
          <circle cx="540" cy="1620" r="420" fill="url(#kq-glow)" />
          <g transform="translate(540 1640)">
            <path d="M-220 120 L0 -20 L220 120 M-220 -20 L0 120 L220 -20" stroke="#6a4a24" stroke-width="22" fill="none" />
            <path d="M-210 -40 L0 -110 L210 -40 L210 -10 L0 -80 L-210 -10 Z" fill="#1d4a3a" />
            <path d="M-200 -42 L0 -108 L200 -42" stroke="{GOLD}" stroke-width="4" fill="none" />
            {star8(-100, -62, 26, "none", GOLD, 4, 0.9)}{star8(100, -62, 26, "none", GOLD, 4, 0.9)}</g>'''
k1, k2 = loc("koran", w("s7", 4)), loc("koran", w("s7", 11))
quote = f'''      <div id="kq-pre" class="title lt" style="top: 330px; font-size: 56px">Allah sagt im Koran</div>
      <div id="kq-q" class="quote" style="top: 470px">
        <span id="kq-q1" class="q">„Verliert nicht die <span class="k">Hoffnung</span> auf Allahs Barmherzigkeit.</span>
        <span id="kq-q2" class="q">Gewiss, Allah vergibt die Sünden <span class="k">alle</span>.“</span>
        <span id="kq-src" class="src">Sure Az-Zumar 39:53</span>
      </div>'''
js = "\n".join([push("#kq-a-cam", 0, d, 1.0, 1.06), fade("#kq-pre", 0.05),
                f'    tl.fromTo("#kq-q", {{ opacity: 0, scale: 0.96 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "power2.out" }}, {r2(k1 - 0.25)});',
                f'    tl.fromTo("#kq-q1", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, {r2(k1 - 0.1)});',
                f'    tl.fromTo("#kq-q2", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, {r2(k2 - 0.1)});',
                f'    tl.fromTo("#kq-src", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {r2(k2 + 0.6)});',
                f'    tl.fromTo(".kq-st", {{ opacity: 0.2 }}, {{ opacity: 0.95, duration: 0.7, repeat: 7, yoyo: true, stagger: 0.02 }}, 0);'])
files["koran"] = comp("koran", beat("kq-a", 0, d, svg, quote), js)

# ===================== DISZIPLIN: Laterne, Weggabelung, Löschen =====================
(a, ad), (b, bd), (c, cd) = beats("disziplin", [SC["disziplin"][0], st("s9"), round(w("s9", 7) - 0.12, 2)])
svgA = f'''          <defs><radialGradient id="d-a-gl" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffcf8a" stop-opacity="0.6" /><stop offset="1" stop-color="#ff8a3c" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#070b12" />
          {pattern(0, 1920, op=0.05)}
          <circle cx="540" cy="1150" r="560" fill="url(#d-a-gl)" />
          {lantern(540, 1300, 2.0, "d-a-flame")}
          <g stroke="#9fb4c4" stroke-width="6" fill="none" opacity="0.35" stroke-linecap="round"><path class="d-a-wind" d="M60 900 q120 -30 240 0" /><path class="d-a-wind" d="M780 1100 q120 -30 240 0" /><path class="d-a-wind" d="M100 1400 q120 -30 240 0" /></g>'''
svgB = f'''          <defs><linearGradient id="d-b-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a1020" /><stop offset="1" stop-color="#2a2a3a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#d-b-sky)" />
          <path d="M440 1920 L520 1300 L560 1300 L640 1920 Z" fill="#3a3a44" />
          <path d="M520 1300 L220 900 L280 900 L560 1300 Z" fill="#1a1a22" />
          <path d="M560 1300 L820 900 L880 900 L560 1300 Z" fill="#c9a96a" opacity="0.8" />
          <circle cx="850" cy="820" r="140" fill="{GOLD}" opacity="0.25" />
          <g transform="translate(250 760)"><rect x="-10" y="0" width="20" height="200" fill="#5a5a66" /><circle r="80" fill="#e8412f" /><rect x="-50" y="-12" width="100" height="24" fill="#fff" /></g>'''
svgC = f'''          <rect width="1080" height="1920" fill="#0a0f18" />
          <rect x="260" y="520" width="560" height="1080" rx="60" fill="#14161c" /><rect x="286" y="560" width="508" height="1000" rx="40" fill="#1e2632" />
          {"".join(f'<rect x="{320 + (i % 3) * 156}" y="{620 + (i // 3) * 170}" width="120" height="120" rx="26" fill="{["#3d7bb3", "#5f8f5c", "#c96b9a", "#f4a62a", "#8d93a1", "#3a4a5a"][i % 6]}" opacity="0.5" />' for i in range(12))}
          <g id="d-c-dlg"><rect x="300" y="900" width="480" height="300" rx="24" fill="#f4efe4" />
            <text x="540" y="990" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="46" fill="#14161c">Löschen?</text>
            <rect x="330" y="1060" width="200" height="100" rx="16" fill="#c7ccd6" /><text x="430" y="1124" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="34" fill="#14161c">Nein</text>
            <rect id="d-c-yes" x="550" y="1060" width="200" height="100" rx="16" fill="#e8412f" /><text x="650" y="1124" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="34" fill="#fff">Löschen</text></g>
          <g transform="translate(700 1200)"><g id="d-c-hand"><circle r="34" fill="#f1c7a0" opacity="0.9" /><circle r="50" fill="none" stroke="#fff" stroke-width="4" opacity="0.5" /></g></g>'''
dz = loc("disziplin", w("s8", 7))
body = "\n".join([beat("d-a", a, ad, svgA, title("d-a-title", "Disziplin", top=330, size=150, cls="gold")),
                  beat("d-b", b, bd, svgB, title("d-b-title", "Meide", top=330, size=150, cls="gold")),
                  beat("d-c", c, cd, svgC, title("d-c-title", "Löschen", top=330, size=150, cls="red"))])
tap = loc("disziplin", w("s9", 10))
js = "\n".join([push("#d-a-cam", a, ad, 1.0, 1.08),
                f'    tl.fromTo("#d-a-flame", {{ opacity: 0.7 }}, {{ opacity: 1, duration: 0.15, repeat: {int(ad / 0.15) // 2 * 2 + 1}, yoyo: true }}, {r2(a)});',
                f'    tl.fromTo(".d-a-wind", {{ x: -60, opacity: 0 }}, {{ x: 120, opacity: 0.5, duration: 1.2, repeat: 1, stagger: 0.3 }}, {r2(a)});',
                slam("#d-a-title", dz - 0.1),
                push("#d-b-cam", b, bd, 1.0, 1.08), fade("#d-b-title", b + 0.05, 0.3),
                push("#d-c-cam", c, cd, 1.0, 1.05),
                f'    tl.fromTo("#d-c-dlg", {{ opacity: 0, scale: 0.8, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: "back.out(2)" }}, {r2(c + 0.05)});',
                f'    tl.fromTo("#d-c-hand", {{ x: 160, y: 260 }}, {{ x: -50, y: -90, duration: 0.5, ease: "power2.out" }}, {r2(c + 0.2)});',
                f'    tl.fromTo("#d-c-yes", {{ opacity: 1 }}, {{ opacity: 0.55, duration: 0.08, repeat: 1, yoyo: true }}, {r2(tap)});',
                slam("#d-c-title", tap)])
files["disziplin"] = comp("disziplin", body, js)

# ===================== TASBIH: beständig, auch wenn wenig =====================
s0, d = SC["tasbih"]
N = 33
beads = "".join(f'<circle class="tb-b" cx="{540 + 300 * math.cos(-math.pi / 2 + i * 2 * math.pi / N):.0f}" cy="{1080 + 300 * math.sin(-math.pi / 2 + i * 2 * math.pi / N):.0f}" r="24" fill="#3a5a4a" stroke="#1a2a22" stroke-width="3" />' for i in range(N))
glow = "".join(f'<circle class="tb-g" cx="{540 + 300 * math.cos(-math.pi / 2 + i * 2 * math.pi / N):.0f}" cy="{1080 + 300 * math.sin(-math.pi / 2 + i * 2 * math.pi / N):.0f}" r="24" fill="{GOLD}" opacity="0" />' for i in range(N))
svg = f'''          <defs><radialGradient id="tb-gl" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{GOLD}" stop-opacity="0.35" /><stop offset="1" stop-color="{GOLD}" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#08100e" />
          {pattern(0, 1920, op=0.05)}
          <circle cx="540" cy="1080" r="520" fill="url(#tb-gl)" />
          <circle cx="540" cy="1080" r="300" fill="none" stroke="#c9a96a" stroke-width="4" opacity="0.6" />
          {beads}{glow}
          <path d="M540 1380 v80" stroke="#c9a96a" stroke-width="6" /><path d="M520 1460 h40 l10 120 h-60 z" fill="{GOLD}" />'''
extra = title("tb-title", "Beständig", top=330, size=150, cls="gold") + '\n      <div id="tb-src" class="pill" style="top: 1500px"><span style="font-size: 30px">Bukhari &amp; Muslim</span></div>'
bs = loc("tasbih", w("s10", 3))
js = "\n".join([push("#tb-a-cam", 0, d, 1.0, 1.06),
                f'    tl.fromTo(".tb-g", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.1, stagger: {r2((d - 0.6) / N)} }}, 0.3);',
                f'    tl.fromTo(".tb-b", {{ scale: 1, transformOrigin: "50% 50%" }}, {{ scale: 1.15, duration: 0.1, stagger: {r2((d - 0.6) / N)} }}, 0.3);',
                slam("#tb-title", loc("tasbih", w("s10", 10)) - 0.1), fade("#tb-src", bs + 0.3, 0.4)])
files["tasbih"] = comp("tasbih", beat("tb-a", 0, d, svg, extra), js)

# ===================== WEG: Tag, Woche, Monat =====================
s0, d = SC["weg"]
cells = "".join(f'<rect class="wg-c wg-{"d" if i == 0 else "w" if i < 7 else "m"}" x="{150 + (i % 7) * 112}" y="{800 + (i // 7) * 112}" width="96" height="96" rx="14" fill="{GOLD}" opacity="0" />' for i in range(30))
grid = "".join(f'<rect x="{150 + (i % 7) * 112}" y="{800 + (i // 7) * 112}" width="96" height="96" rx="14" fill="#1a2430" stroke="#2a3a4a" stroke-width="3" />' for i in range(35))
svg = f'''          <rect width="1080" height="1920" fill="#0a1018" />
          <rect x="110" y="680" width="860" height="720" rx="30" fill="#121a24" />
          <rect x="110" y="680" width="860" height="90" rx="30" fill="#1d4a3a" />
          {grid}{cells}'''
t1, t2, t3 = (loc("weg", w("s11", i)) for i in (1, 4, 7))
extra = "\n".join(title(f"wg-t{i}", t, top=330, size=130, cls="gold") for i, t in ((1, "1 Tag"), (2, "1 Woche"), (3, "1 Monat")))
js = "\n".join([push("#wg-a-cam", 0, d, 1.0, 1.06),
                f'    tl.fromTo(".wg-d", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.15 }}, {r2(t1 - 0.1)});',
                f'    tl.fromTo(".wg-w", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.08, stagger: 0.04 }}, {r2(t2 - 0.15)});',
                f'    tl.fromTo(".wg-m", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.06, stagger: 0.025 }}, {r2(t3 - 0.15)});',
                slam("#wg-t1", t1 - 0.1), f'    tl.to("#wg-t1", {{ opacity: 0, duration: 0.1 }}, {r2(t2 - 0.12)});',
                slam("#wg-t2", t2 - 0.1), f'    tl.to("#wg-t2", {{ opacity: 0, duration: 0.1 }}, {r2(t3 - 0.12)});',
                slam("#wg-t3", t3 - 0.1)])
files["weg"] = comp("weg", beat("wg-a", 0, d, svg, extra), js)

# ===================== FREI: Kette bricht im Sonnenaufgang =====================
s0, d = SC["frei"]
link = lambda x, y, rot, cid: f'<g transform="translate({x} {y}) rotate({rot})"><g id="{cid}"><rect x="-70" y="-40" width="140" height="80" rx="40" fill="none" stroke="#8d93a1" stroke-width="22" /></g></g>'
svg = f'''          <defs><linearGradient id="fr-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a2a4a" /><stop offset="0.6" stop-color="#e88a5a" /><stop offset="1" stop-color="#ffd28a" /></linearGradient>
            <radialGradient id="fr-sun" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff6dc" stop-opacity="1" /><stop offset="0.3" stop-color="{GOLD}" stop-opacity="0.7" /><stop offset="1" stop-color="{GOLD}" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="url(#fr-sky)" />
          <circle id="fr-sun" cx="540" cy="1500" r="600" fill="url(#fr-sun)" />
          <path d="M0 1500 L300 1380 L540 1460 L800 1360 L1080 1480 V1920 H0 Z" fill="#2a2030" />
          <g id="fr-left">{link(140, 1000, 0, "fr-l1")}{link(260, 1000, 90, "fr-l2")}{link(380, 1000, 0, "fr-l3")}</g>
          <g id="fr-right">{link(700, 1000, 0, "fr-r1")}{link(820, 1000, 90, "fr-r2")}{link(940, 1000, 0, "fr-r3")}</g>
          <g transform="translate(540 1000)"><g id="fr-mid"><path d="M-70 -40 h50 M70 -40 h-50 M-70 40 h50 M70 40 h-50" stroke="#8d93a1" stroke-width="22" stroke-linecap="round" /></g></g>
          <g transform="translate(540 1000)"><g id="fr-burst" opacity="0">{"".join(f'<path d="M0 0 L{200 * math.cos(k * 0.785):.0f} {200 * math.sin(k * 0.785):.0f}" stroke="{GOLD}" stroke-width="10" stroke-linecap="round" />' for k in range(8))}</g></g>'''
br = loc("frei", w("s12", 9))
js = "\n".join([push("#fr-a-cam", 0, d, 1.0, 1.06),
                f'    tl.fromTo("#fr-sun", {{ y: 200 }}, {{ y: 0, duration: {r2(d)}, ease: "power1.out" }}, 0);',
                f'    tl.fromTo("#fr-burst", {{ opacity: 1, scale: 0.2, transformOrigin: "50% 50%" }}, {{ opacity: 0, scale: 1.6, duration: 0.6, ease: "power2.out" }}, {r2(br)});',
                f'    tl.fromTo("#fr-mid", {{ opacity: 1, scale: 1, transformOrigin: "50% 50%" }}, {{ opacity: 0, scale: 1.8, duration: 0.3 }}, {r2(br)});',
                f'    tl.fromTo("#fr-left", {{ x: 0, y: 0, rotation: 0 }}, {{ x: -300, y: 500, rotation: -30, duration: 1.2, ease: "power2.in" }}, {r2(br + 0.05)});',
                f'    tl.fromTo("#fr-right", {{ x: 0, y: 0, rotation: 0 }}, {{ x: 300, y: 500, rotation: 30, duration: 1.2, ease: "power2.in" }}, {r2(br + 0.05)});',
                f'    tl.fromTo("#fr-a-cam", {{ x: 0 }}, {{ x: 10, duration: 0.04, repeat: 5, yoyo: true }}, {r2(br + 0.02)});'.replace('"#fr-a-cam"', '"#fr-a-cam > svg"'),
                slam("#fr-title", br + 0.05)])
files["frei"] = comp("frei", beat("fr-a", 0, d, svg, title("fr-title", "Frei", top=330, size=190, cls="gold")), js)

# ===================== ENDE: Gib nicht auf + Teilen =====================
s0, d = SC["ende"]
svg = f'''          <defs><linearGradient id="en-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a1428" /><stop offset="0.6" stop-color="#3a3a5a" /><stop offset="0.85" stop-color="#e8a05a" /><stop offset="1" stop-color="#ffd28a" /></linearGradient>
            <radialGradient id="en-sun" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff2c8" stop-opacity="0.85" /><stop offset="1" stop-color="#ffb35c" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="url(#en-sky)" />
          {stars(random.Random(6), 60, 900, "en-st")}
          {crescent(540, 1020, 90, GOLD, "en-moon")}
          <circle cx="540" cy="1700" r="560" fill="url(#en-sun)" />
          {mosque(540, 1760, 1.0, "#0a1018")}
          <rect x="0" y="1760" width="1080" height="160" fill="#0a1018" />'''
extra = (title("en-title", 'Gib nicht<br /><span class="gold">auf</span>', top=330, size=150)
         + '\n      <div id="en-pill" class="pill" style="top: 700px"><span style="font-size: 34px">Schick das jemandem, der es heute braucht 🤍</span></div>')
js = "\n".join([f'    tl.fromTo("#en-a-cam", {{ scale: 1.1, y: 30 }}, {{ scale: 1.0, y: 0, duration: {r2(d)}, ease: "power2.out" }}, 0);',
                slam("#en-title", loc("ende", w("end", 2)) - 0.15),
                fade("#en-pill", loc("ende", L["cta"]["start"]), 0.4),
                f'    tl.fromTo(".en-st", {{ opacity: 0.2 }}, {{ opacity: 0.95, duration: 0.6, repeat: 7, yoyo: true, stagger: 0.02 }}, 0);'])
files["ende"] = comp("ende", beat("en-a", 0, d, svg, extra), js)

for n, html in files.items():
    open(os.path.join(P, "compositions", n + ".html"), "w").write(html)

g = lambda n: SC[n][0]
sfx = [["sfx-wd", "impact-bass-2", w("hook2", 4), 0.3], ["sfx-gl", "glitch-3", w("hook2", 4) + 0.03, 0.12],
       ["sfx-w1", "whoosh", g("scham"), 0.18], ["sfx-w2", "whoosh-cinematic", g("hadith"), 0.18],
       ["sfx-w3", "whoosh", g("kampf"), 0.2], ["sfx-sp", "impact-bass-1", w("s4", 7), 0.18],
       ["sfx-f1", "impact-bass-1", w("s5", 1), 0.14], ["sfx-f2", "impact-bass-1", w("s5", 6), 0.14],
       ["sfx-w4", "whoosh", g("tuer"), 0.2], ["sfx-riser", "riser", w("s6", 10) - 0.2, 0.16], ["sfx-of", "impact-bass-2", w("s6", 10), 0.22],
       ["sfx-w5", "whoosh-cinematic", g("koran"), 0.18], ["sfx-w6", "whoosh", g("disziplin"), 0.2], ["sfx-dz", "impact-bass-2", w("s8", 7), 0.22],
       ["sfx-w7", "whoosh-short", st("s9"), 0.2], ["sfx-w8", "whoosh-short", w("s9", 7) - 0.12, 0.2], ["sfx-tap", "click-soft", w("s9", 10), 1.0],
       ["sfx-w9", "whoosh", g("tasbih"), 0.2], ["sfx-w10", "whoosh-short", g("weg"), 0.2],
       ["sfx-p1", "pop", w("s11", 1), 0.5], ["sfx-p2", "pop", w("s11", 4), 0.5], ["sfx-p3", "pop", w("s11", 7), 0.5],
       ["sfx-w11", "whoosh", g("frei"), 0.2], ["sfx-br", "impact-bass-1", w("s12", 9), 0.3], ["sfx-gl2", "glitch-3", w("s12", 9) + 0.02, 0.12],
       ["sfx-w12", "whoosh-cinematic", g("ende"), 0.2], ["sfx-auf", "impact-bass-2", w("end", 2) - 0.15, 0.22]]
sfx = [[a_, b_, round(t, 2), v] for a_, b_, t, v in sfx]
json.dump({"total": TOTAL, "scenes": [[n, SC[n][0], SC[n][1]] for n, _ in order], "sfx": sfx}, open(os.path.join(P, "scenes.json"), "w"), indent=1)
print("Szenen:", ", ".join(f"{n} {SC[n][0]}+{SC[n][1]}" for n, _ in order), "| Länge", TOTAL)
