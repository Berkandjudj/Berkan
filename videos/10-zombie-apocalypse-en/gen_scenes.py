# Zombie-Apokalypse (EN). Erzeugt alle Szenen (compositions/*.html), hud.json und scenes.json aus assets/timing.json.
# Neue Stimme → place_voice.py → dieses Skript → svg_parts.py . → build_hud.py . → build_index.py → build_captions.py .
import json, random, os

P = os.path.dirname(os.path.abspath(__file__))
tm = json.load(open(os.path.join(P, "assets/timing.json")))
L = {l["id"]: l for l in (tm["lines"] if isinstance(tm, dict) else tm)}
w = lambda lid, i: L[lid]["words"][i]["start"]
st = lambda lid: round(L[lid]["start"] - 0.1, 2)
r2 = lambda x: f"{x:.2f}"

order = [("hook", 0.0), ("fact", st("fact")), ("day1", st("d1_mark")), ("day2", st("d2_mark")), ("day3", st("d3_mark")),
         ("day5", st("d5_mark")), ("day7", st("d7_mark")), ("frage", st("frage")), ("outro", st("cta"))]
TOTAL = round(L["cta"]["end"] + 3.1, 2)
SC = {}
for i, (n, s) in enumerate(order):
    e = order[i + 1][1] if i + 1 < len(order) else TOTAL
    SC[n] = (s, round(e - s, 2))
loc = lambda sc, t: round(t - SC[sc][0], 2)


def beats(sc, starts):
    s0, d = SC[sc]
    l = [round(x - s0, 2) for x in starts] + [d]
    return [(l[i], round(l[i + 1] - l[i], 2)) for i in range(len(starts))]


def comp(cid, body, js, css=""):
    return f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; background: #131824; }}
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


def title(i, html, top=400, size=150):
    return f'      <div id="{i}" class="title" style="top: {top}px; font-size: {size}px">{html}</div>'


def chip(i, text, top=400, cls="", size=60):
    return f'      <div id="{i}" class="chip-row" style="top: {top}px"><span class="chip {cls}" style="font-size: {size}px">{text}</span></div>'


slam = lambda sel, t: f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 1.8, filter: "blur(8px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.16, ease: "power4.in" }}, {r2(t)});'
popc = lambda sel, t: f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.2, ease: "back.out(2.5)" }}, {r2(t)});'
push = lambda sel, s, d, a=1.0, b=1.08: f'    tl.fromTo("{sel}", {{ scale: {a} }}, {{ scale: {b}, duration: {r2(d)}, ease: "none" }}, {r2(s)});'
shake = lambda sel, t: f'    tl.fromTo("{sel}", {{ x: 0 }}, {{ x: 14, duration: 0.04, repeat: 5, yoyo: true }}, {r2(t)});'
bounce = lambda sel, t, n=5, stg=0.07: f'    tl.fromTo("{sel}", {{ y: 0 }}, {{ y: -36, duration: 0.18, repeat: {n}, yoyo: true, ease: "power2.out", stagger: {stg} }}, {r2(t)});'

ME = 'jacket="#3d6b8f" pants="#2a2f3b" hair="#2a1a10" skin="#f1c7a0" style="short"'


def sparkles(cls, pts, col="#f7c548"):
    return "".join(f'<g transform="translate({x} {y}) scale({sc})"><path class="{cls}" d="M0 -40 L10 -10 L40 0 L10 10 L0 40 L-10 10 L-40 0 L-10 -10 Z" fill="{col}" /></g>' for x, y, sc in pts)


def rings(gid, x, y, n=3, r0=160, gap=70):
    return f'<g transform="translate({x} {y})"><g id="{gid}">' + "".join(f'<circle class="{gid}-c" r="{r0 + i * gap}" fill="none" stroke="#e8412f" stroke-width="12" opacity="0.8" />' for i in range(n)) + '</g></g>'


ring_js = lambda gid, t, rep=3: f'    tl.fromTo(".{gid}-c", {{ scale: 0.7, opacity: 0.9, transformOrigin: "50% 50%" }}, {{ scale: 1.25, opacity: 0, duration: 0.9, repeat: {rep}, stagger: 0.2, ease: "none" }}, {r2(t)});'


def card(bid, s, d, day, sub):
    svg = '          <rect width="1080" height="1920" fill="#1a1f2b" />\n          <circle cx="540" cy="760" r="420" fill="#232a3a" />'
    return beat(bid, s, d, svg, title(f"{bid}-day", f'<span class="o">Day {day}</span>', top=520, size=270) + "\n" + chip(f"{bid}-chip", sub, top=850))


card_js = lambda bid, s: slam(f"#{bid}-day", s + 0.06) + "\n" + popc(f"#{bid}-chip", s + 0.22)
files = {}

Z = lambda zid, x, y, s, extra="": f'<!--@zombie id="{zid}" x="{x}" y="{y}" s="{s}" {extra}-->'


def skyline_bg(prefix, y=1250, lit="0", seed="3"):
    return f'<!--@skyline id="{prefix}" y="{y}" lit="{lit}" seed="{seed}" color="#0b0f16" win="#f7c548"-->'


# ===================== HOOK: stille Stadt → Kratzen an der Tür =====================
(a, ad), (b, bd) = beats("hook", [0.0, st("hook2")])
svgA = f'''          <defs><linearGradient id="h-a-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1a22" /><stop offset="0.7" stop-color="#2a4a4a" /><stop offset="1" stop-color="#6a7a5a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#h-a-sky)" />
          {skyline_bg("h-a-sk", 1150, "0", "4")}
          <rect y="1150" width="1080" height="770" fill="#1a2026" />
          <polygon points="420,1150 660,1150 1080,1920 0,1920" fill="#262c34" />
          <g stroke="#c7ccd6" stroke-width="14" opacity="0.4" stroke-dasharray="60 70"><line x1="540" y1="1170" x2="540" y2="1920" /></g>
          <g transform="translate(250 1560) rotate(-8)"><rect x="-170" y="-110" width="340" height="120" rx="30" fill="#8a2a22" /><path d="M-110 -110 l40 -70 h150 l50 70 z" fill="#6a2018" />
            <path d="M-60 -170 l30 -4 l10 60 h-50 z" fill="#9fc4d8" opacity="0.5" /><circle cx="-100" cy="10" r="40" fill="#14161c" /><circle cx="110" cy="10" r="40" fill="#14161c" /></g>
          <g id="h-a-smoke" fill="#3a4048" opacity="0.6"><ellipse cx="780" cy="900" rx="120" ry="80" /><ellipse cx="820" cy="780" rx="150" ry="100" /><ellipse cx="760" cy="640" rx="180" ry="110" /></g>
          <g fill="#c7ccd6" opacity="0.5">{"".join(f'<rect class="h-a-paper" x="{x}" y="{y}" width="40" height="28" />' for x, y in [(620, 1500), (820, 1700), (420, 1800)])}</g>
          {Z("h-a-z", 860, 1260, "0.32", 'pose="hang"')}
          {rings("h-a-rg", 860, 1150, 3, 70, 40)}'''
scratches = "".join(f'<path class="h-b-sc" d="M{x} {y} l{dx} {dy}" stroke="#d9c8a8" stroke-width="7" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" />' for x, y, dx, dy in [(420, 980, 40, 160), (460, 970, 40, 170), (500, 990, 36, 150), (640, 1080, -30, 140), (676, 1090, -30, 130)])
svgB = f'''          <rect width="1080" height="1920" fill="#14100c" />
          <rect x="210" y="520" width="660" height="1120" rx="12" fill="#5a3a20" />
          <rect x="260" y="580" width="250" height="420" rx="10" fill="#4a2e18" /><rect x="570" y="580" width="250" height="420" rx="10" fill="#4a2e18" />
          <rect x="260" y="1060" width="250" height="520" rx="10" fill="#4a2e18" /><rect x="570" y="1060" width="250" height="520" rx="10" fill="#4a2e18" />
          {scratches}
          <g transform="translate(790 1080)"><g id="h-b-handle"><rect x="-10" y="-60" width="40" height="120" rx="12" fill="#c7ccd6" /><rect x="-110" y="-16" width="130" height="34" rx="16" fill="#f4a62a" /></g></g>
          <rect x="210" y="1640" width="660" height="14" fill="#f7c548" opacity="0.6" />
          <g id="h-b-shadow" fill="#000" opacity="0.7"><rect x="380" y="1642" width="70" height="12" /><rect x="560" y="1642" width="70" height="12" /></g>
          <rect y="1654" width="1080" height="266" fill="#0e0a08" />'''
body = "\n".join([beat("h-a", a, ad, svgA, title("h-a-title", 'Zombie<br /><span class="r">Apocalypse</span>', top=330, size=150)),
                  beat("h-b", b, bd, svgB, title("h-b-title", '<span class="r">Scratch.</span>', top=330, size=170))])
sc = loc("hook", w("hook2", 6))
js = "\n".join([push("#h-a-cam", a, ad, 1.0, 1.08), ring_js("h-a-rg", 0.2, 3),
                f'    tl.fromTo("#h-a-smoke", {{ y: 0 }}, {{ y: -120, duration: {r2(ad)}, ease: "none" }}, {r2(a)});',
                f'    tl.fromTo(".h-a-paper", {{ x: 0, rotation: 0 }}, {{ x: 120, rotation: 40, duration: {r2(ad)}, ease: "none" }}, {r2(a)});',
                f'    tl.fromTo("#h-b-cam", {{ scale: 1.1 }}, {{ scale: 1.0, duration: {r2(bd)}, ease: "power1.out" }}, {r2(b)});',
                f'    tl.fromTo(".h-b-sc", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.25, stagger: 0.12, ease: "power2.in" }}, {r2(sc - 0.1)});',
                f'    tl.fromTo("#h-b-handle", {{ rotation: 0, transformOrigin: "80% 50%" }}, {{ rotation: -14, duration: 0.12, repeat: 5, yoyo: true }}, {r2(sc + 0.3)});',
                f'    tl.fromTo("#h-b-shadow", {{ x: -40 }}, {{ x: 40, duration: 0.5, repeat: 3, yoyo: true }}, {r2(b)});',
                slam("#h-b-title", sc - 0.05), shake("#h-b-cam", sc + 0.1)])
files["hook"] = comp("hook", body, js)

# ===================== FAKT: CDC 2011 → Wasser, Essen, Plan =====================
(a, ad), (b, bd) = beats("fact", [SC["fact"][0], st("fact2")])
svgA = '''          <rect width="1080" height="1920" fill="#1a1f2b" />
          <g transform="translate(540 1000) rotate(-4)"><rect x="-300" y="-400" width="600" height="760" rx="20" fill="#f4efe4" />
            <rect x="-90" y="-430" width="180" height="60" rx="14" fill="#8d93a1" />
            <rect x="-250" y="-330" width="500" height="80" fill="#1d4a6a" /><text x="0" y="-276" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="52" fill="#fff">PREPAREDNESS 101</text>
            <text x="0" y="-170" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="64" fill="#8a2a22">ZOMBIE</text>
            <text x="0" y="-100" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="64" fill="#8a2a22">APOCALYPSE</text>
            <g fill="#c7ccd6"><rect x="-240" y="-30" width="480" height="18" rx="9" /><rect x="-240" y="20" width="420" height="18" rx="9" /><rect x="-240" y="70" width="450" height="18" rx="9" /><rect x="-240" y="120" width="380" height="18" rx="9" /></g>
            <g id="f-a-stamp" transform="translate(140 190) rotate(-14)"><rect x="-120" y="-50" width="240" height="100" rx="12" fill="none" stroke="#e8412f" stroke-width="10" /><text x="0" y="22" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="60" fill="#e8412f">REAL</text></g></g>'''
items = [("water", 2, '<rect x="-50" y="-150" width="100" height="220" rx="24" fill="#7fb0d8" /><rect x="-24" y="-190" width="48" height="44" rx="8" fill="#3d7bb3" /><rect x="-50" y="-60" width="100" height="40" fill="#bfe0ff" />'),
         ("food", 3, '<rect x="-70" y="-130" width="140" height="190" rx="14" fill="#c7ccd6" /><rect x="-70" y="-80" width="140" height="80" fill="#e8412f" /><ellipse cx="0" cy="-130" rx="70" ry="16" fill="#e9eef2" />'),
         ("plan", 6, '<rect x="-100" y="-120" width="200" height="170" fill="#e9dcc0" /><path d="M-100 -120 l60 20 l60 -20 l80 20 v170 l-80 -20 l-60 20 l-60 -20 z" fill="#d9c8a0" /><path d="M-70 10 q40 -80 120 -40" stroke="#e8412f" stroke-width="8" fill="none" stroke-dasharray="14 10" /><circle cx="50" cy="-30" r="14" fill="#e8412f" />')]
svgB = '          <rect width="1080" height="1920" fill="#1b232f" />\n' + "".join(f'          <g transform="translate({200 + i * 340} 1060)"><g id="f-b-{k}">{g}</g></g>\n' for i, (k, _, g) in enumerate(items))
extraB = "\n".join(chip(f"f-b-c{i}", k.upper(), top=1200, cls="o" if i < 2 else "r", size=56).replace('class="chip-row" style="top: 1200px"', f'class="chip-row" style="top: 1180px; left: {i * 340 - 340}px"') for i, (k, _, _) in enumerate(items))
body = "\n".join([beat("f-a", a, ad, svgA, title("f-a-title", '<span class="o">2011</span>', top=330, size=200) + "\n" + chip("f-a-chip", "CDC", top=560, cls="r", size=64)),
                  beat("f-b", b, bd, svgB, extraB)])
js = [push("#f-a-cam", a, ad), slam("#f-a-title", loc("fact", w("fact", 6)) - 0.05), popc("#f-a-chip", loc("fact", w("fact", 8)) - 0.05),
      f'    tl.fromTo("#f-a-stamp", {{ opacity: 0, scale: 2 }}, {{ opacity: 1, scale: 1, duration: 0.18, ease: "power4.in" }}, {r2(loc("fact", w("fact", 18)) - 0.05)});',
      push("#f-b-cam", b, bd, 1.0, 1.05)]
for i, (k, wi, _) in enumerate(items):
    t = loc("fact", w("fact2", wi)) - 0.08
    js += [f'    tl.fromTo("#f-b-{k}", {{ opacity: 0, y: 60 }}, {{ opacity: 1, y: 0, duration: 0.25, ease: "back.out(2)" }}, {r2(t)});', popc(f"#f-b-c{i}", t + 0.05)]
files["fact"] = comp("fact", body, "\n".join(js))

# ===================== DAY 1: kein Netz, TV, Nachbar =====================
(a, ad), (b, bd), (c, cd), (d, dd) = beats("day1", [SC["day1"][0], st("d1"), round(w("d1", 5) - 0.12, 2), st("d1b")])
svgB = '''          <rect width="1080" height="1920" fill="#141a22" />
          <rect x="300" y="560" width="480" height="960" rx="60" fill="#05070a" /><rect x="324" y="596" width="432" height="888" rx="40" fill="#1a2430" />
          <g transform="translate(540 820)"><g fill="#3a4a5a"><rect x="-90" y="20" width="36" height="40" rx="4" /><rect x="-36" y="-10" width="36" height="70" rx="4" /><rect x="18" y="-40" width="36" height="100" rx="4" /><rect x="72" y="-70" width="36" height="130" rx="4" /></g>
            <path id="d1-b-x" d="M-110 -80 L130 80 M130 -80 L-110 80" stroke="#e8412f" stroke-width="18" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" /></g>
          <text x="540" y="1040" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="56" fill="#8d93a1">NO SERVICE</text>'''
svgC = '''          <rect width="1080" height="1920" fill="#0e1218" />
          <rect x="100" y="600" width="880" height="620" rx="24" fill="#05070a" /><rect x="130" y="630" width="820" height="560" fill="#2a0e0e" />
          <rect id="d1-c-band" x="130" y="760" width="820" height="150" fill="#e8412f" />
          <text x="540" y="862" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="88" fill="#fff">EMERGENCY ALERT</text>
          <text x="540" y="1010" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="60" fill="#f4efe4">STAY INSIDE</text>
          <text x="540" y="1090" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="48" fill="#c7ccd6">DO NOT OPEN THE DOOR</text>
          <rect x="460" y="1220" width="160" height="60" fill="#05070a" /><rect x="360" y="1280" width="360" height="20" rx="10" fill="#05070a" />'''
svgD = f'''          <rect width="1080" height="1920" fill="#0a0d12" />
          <defs><clipPath id="d1-d-win"><rect x="160" y="560" width="760" height="980" /></clipPath></defs>
          <g clip-path="url(#d1-d-win)">
            <rect x="160" y="560" width="760" height="980" fill="#3a4a4a" />
            <rect x="160" y="1200" width="760" height="340" fill="#2a3036" />
            <g fill="#232a30"><rect x="160" y="700" width="200" height="500" /><rect x="380" y="800" width="160" height="400" /><rect x="720" y="660" width="200" height="540" /></g>
            {Z("d1-d-z", 560, 1530, "0.8", 'pose="hang" shirt="#3d6b8f"')}
          </g>
          <rect x="160" y="560" width="760" height="980" fill="none" stroke="#3a2a1e" stroke-width="30" /><path d="M540 560 V1540 M160 1050 H920" stroke="#3a2a1e" stroke-width="20" />
          <rect x="120" y="1540" width="840" height="40" fill="#4a3a2a" />'''
body = "\n".join([card("d1-a", a, ad, 1, "6 AM"),
                  beat("d1-b", b, bd, svgB, title("d1-b-title", '<span class="r">No Signal</span>', top=400, size=150)),
                  beat("d1-c", c, cd, svgC, title("d1-c-title", 'Stay<br /><span class="r">Inside</span>', top=390, size=110)),
                  beat("d1-d", d, dd, svgD, title("d1-d-title", '<span class="r">Staring</span>', top=390, size=150))])
js = "\n".join([card_js("d1-a", a), push("#d1-b-cam", b, bd),
                f'    tl.fromTo("#d1-b-x", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.25 }}, {r2(loc("day1", w("d1", 3)) - 0.05)});',
                slam("#d1-b-title", loc("day1", w("d1", 3)) - 0.05),
                push("#d1-c-cam", c, cd, 1.0, 1.06),
                f'    tl.fromTo("#d1-c-band", {{ opacity: 1 }}, {{ opacity: 0.55, duration: 0.25, repeat: {int(cd / 0.25) // 2 * 2 + 1}, yoyo: true }}, {r2(c)});',
                slam("#d1-c-title", loc("day1", w("d1", 10)) - 0.05),
                f'    tl.fromTo("#d1-d-cam", {{ scale: 1.0 }}, {{ scale: 1.18, duration: {r2(dd)}, ease: "power1.in" }}, {r2(d)});',
                slam("#d1-d-title", loc("day1", w("d1b", 10)) - 0.05)])
files["day1"] = comp("day1", body, js)

# ===================== DAY 2: Strom weg, Glas, Schritte =====================
(a, ad), (b, bd), (c, cd) = beats("day2", [SC["day2"][0], st("d2"), round(w("d2", 11) - 0.12, 2)])
shards = "".join(f'<path class="d2-b-sh" d="M{x} {y} l{dx} {dy} l{dy // 2} {-dx // 2} z" fill="#bfe0ff" opacity="0.8" />' for x, y, dx, dy in [(500, 1100, 40, 60), (560, 1080, -30, 50), (620, 1120, 50, 40), (460, 1140, -40, 30), (580, 1160, 30, 70), (520, 1180, -50, 40)])
svgB = f'''          <defs><linearGradient id="d2-b-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a2838" /><stop offset="1" stop-color="#3a4a5a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#d2-b-sky)" />
          {skyline_bg("d2-b-sk", 1300, "1", "6")}
          <rect y="1300" width="1080" height="620" fill="#0a0d12" />
          <rect id="d2-b-dark" width="1080" height="1920" fill="#000" opacity="0" />
          <defs><radialGradient id="d2-b-gl" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffe2a0" stop-opacity="0.8" /><stop offset="1" stop-color="#ffb35c" stop-opacity="0" /></radialGradient></defs>
          <path d="M540 0 V720" stroke="#14161c" stroke-width="8" />
          <circle id="d2-b-glow" cx="540" cy="800" r="420" fill="url(#d2-b-gl)" />
          <rect x="510" y="700" width="60" height="40" rx="6" fill="#3a3f4b" />
          <circle id="d2-b-bulb" cx="540" cy="790" r="56" fill="#fff2c4" />
          <circle cx="540" cy="790" r="56" fill="none" stroke="#8d93a1" stroke-width="5" />
          <g transform="translate(540 1120)"><g id="d2-b-crash" opacity="0">{shards}<path d="M-120 0 l40 -20 l30 30 l50 -40 l40 30 l60 -10" stroke="#fff" stroke-width="6" fill="none" transform="translate(-540 -1120)" /></g></g>'''
stairs = "".join(f'<rect x="{100 + i * 0}" y="{760 + i * 120}" width="{880}" height="120" fill="{["#1a2028", "#1e242c", "#222830", "#262c34", "#2a3038", "#2e343c", "#32383f"][i]}" /><rect x="100" y="{760 + i * 120}" width="880" height="8" fill="#4a525c" />' for i in range(7))
svgC = f'''          <rect width="1080" height="1920" fill="#06080b" />
          {stairs}
          <g id="d2-c-light"><path d="M540 560 L120 1600 L960 1600 Z" fill="#f7c548" opacity="0.08" /></g>
          <g id="d2-c-zw" opacity="0.85">{Z("d2-c-z", 540, 1240, "0.75", 'skin="#6a8a5a" shirt="#2a2630"')}</g>
          <g fill="#000" opacity="0.6"><ellipse cx="540" cy="1640" rx="300" ry="30" /></g>'''
body = "\n".join([card("d2-a", a, ad, 2, "Power out"),
                  beat("d2-b", b, bd, svgB, title("d2-b-title", '<span class="r">Power Out</span>', top=400, size=140)),
                  beat("d2-c", c, cd, svgC, title("d2-c-title", '<span class="r">Dragging</span>', top=400, size=150))])
po, gb = loc("day2", w("d2", 1)), loc("day2", w("d2", 7))
js = "\n".join([card_js("d2-a", a), push("#d2-b-cam", b, bd),
                f'    tl.fromTo(".d2-b-sk-win", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.05, stagger: {{ each: 0.01, from: "start" }} }}, {r2(po - 0.1)});',
                f'    tl.fromTo("#d2-b-dark", {{ opacity: 0 }}, {{ opacity: 0.5, duration: 0.3 }}, {r2(po)});',
                f'    tl.fromTo("#d2-b-glow", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.06, repeat: 3, yoyo: true }}, {r2(po - 0.35)});',
                f'    tl.to("#d2-b-glow", {{ opacity: 0, duration: 0.05 }}, {r2(po)});',
                f'    tl.fromTo("#d2-b-bulb", {{ fill: "#fff2c4" }}, {{ fill: "#3a3f4b", duration: 0.05 }}, {r2(po)});',
                slam("#d2-b-title", po - 0.05),
                f'    tl.fromTo("#d2-b-crash", {{ opacity: 0, scale: 0.5, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1.3, duration: 0.25, ease: "power3.out" }}, {r2(gb - 0.05)});',
                shake("#d2-b-cam", gb),
                f'    tl.fromTo("#d2-c-cam", {{ scale: 1.0 }}, {{ scale: 1.12, duration: {r2(cd)}, ease: "power1.in" }}, {r2(c)});',
                f'    tl.fromTo("#d2-c-zw", {{ y: -260, scale: 0.7, transformOrigin: "50% 100%" }}, {{ y: 120, scale: 1.15, duration: {r2(cd)}, ease: "none" }}, {r2(c)});',
                f'    tl.fromTo("#d2-c-z-head", {{ rotation: -6, transformOrigin: "50% 90%" }}, {{ rotation: 6, duration: 0.5, repeat: 5, yoyo: true, ease: "sine.inOut" }}, {r2(c)});',
                f'    tl.fromTo("#d2-c-light", {{ opacity: 1 }}, {{ opacity: 0.3, duration: 0.15, repeat: 7, yoyo: true }}, {r2(c + 0.5)});',
                slam("#d2-c-title", loc("day2", w("d2", 17)) - 0.05)])
files["day2"] = comp("day2", body, js)

# ===================== DAY 3: Wasser, 400 m, Dutzende =====================
(a, ad), (b, bd), (c, cd) = beats("day3", [SC["day3"][0], st("d3"), round(w("d3", 5) - 0.12, 2)])
svgB = '''          <rect width="1080" height="1920" fill="#141a22" />
          <g transform="translate(540 1050)"><path d="M-110 -300 h220 v40 q60 40 60 120 v500 q0 40 -40 40 h-260 q-40 0 -40 -40 v-500 q0 -80 60 -120 z" fill="#bfe0ff" opacity="0.25" stroke="#bfe0ff" stroke-width="6" />
            <rect x="-60" y="-370" width="120" height="70" rx="12" fill="#3d7bb3" />
            <rect id="d3-b-lvl" x="-166" y="320" width="332" height="80" rx="20" fill="#3d7bb3" opacity="0.85" /></g>'''
rng = random.Random(9)
zdots = "".join(f'<g class="d3-c-zd" transform="translate({rng.uniform(260, 820):.0f} {rng.uniform(820, 1500):.0f})"><circle r="16" fill="#8fae7a" /><circle r="26" fill="none" stroke="#e8412f" stroke-width="4" opacity="0.6" /></g>' for _ in range(28))
svgC = f'''          <rect width="1080" height="1920" fill="#1a2026" />
          <g fill="#262c34">{"".join(f'<rect x="{x}" y="{y}" width="200" height="200" rx="10" />' for x in (60, 820) for y in range(560, 1700, 260))}</g>
          <rect x="300" y="520" width="480" height="1200" fill="#2a3038" />
          <g transform="translate(540 1640)"><circle r="34" fill="#3d7bb3" stroke="#fff" stroke-width="6" /><text x="0" y="90" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="44" fill="#f4efe4">YOU</text></g>
          <g transform="translate(540 640)"><rect x="-120" y="-60" width="240" height="110" rx="12" fill="#5f8f5c" /><text x="0" y="10" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="48" fill="#fff">STORE</text></g>
          <path d="M540 1600 V700" stroke="#f7c548" stroke-width="8" stroke-dasharray="20 18" />
          {zdots}'''
body = "\n".join([card("d3-a", a, ad, 3, "Thirst"),
                  beat("d3-b", b, bd, svgB, title("d3-b-title", '<span class="r">Almost gone</span>', top=400, size=130)),
                  beat("d3-c", c, cd, svgC, title("d3-c-title", '<span class="o">400 m</span>', top=390, size=150) + "\n" + chip("d3-c-chip", "Dozens of them", top=1500, cls="r", size=64))])
js = "\n".join([card_js("d3-a", a), push("#d3-b-cam", b, bd),
                f'    tl.fromTo("#d3-b-lvl", {{ scaleY: 3, transformOrigin: "50% 100%" }}, {{ scaleY: 0.4, duration: 1.2, ease: "power2.inOut" }}, {r2(b + 0.2)});',
                slam("#d3-b-title", loc("day3", w("d3", 3)) - 0.05),
                push("#d3-c-cam", c, cd, 1.0, 1.06),
                slam("#d3-c-title", loc("day3", w("d3", 9)) - 0.05),
                f'    tl.fromTo(".d3-c-zd", {{ scale: 0, opacity: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, opacity: 1, duration: 0.15, stagger: 0.03, ease: "back.out(2)" }}, {r2(loc("day3", w("d3", 12)) - 0.1)});',
                popc("#d3-c-chip", loc("day3", w("d3", 16)) - 0.05)])
files["day3"] = comp("day3", body, js)

# ===================== DAY 5: Radio, Safe Zone, Brücke =====================
(a, ad), (b, bd), (c, cd) = beats("day5", [SC["day5"][0], st("d5"), round(w("d5", 13) - 0.12, 2)])
svgB = f'''          <rect width="1080" height="1920" fill="#141a22" />
          <g transform="translate(540 1050)"><rect x="-300" y="-160" width="600" height="320" rx="40" fill="#5a4a3a" /><circle cx="-150" cy="0" r="100" fill="#2a2018" />
            <g fill="#1a1410">{"".join(f'<circle cx="{-150 + dx}" cy="{dy}" r="8" />' for dx in range(-60, 61, 30) for dy in range(-60, 61, 30))}</g>
            <rect x="20" y="-90" width="220" height="80" rx="10" fill="#f7c548" opacity="0.85" /><rect id="d5-b-needle" x="90" y="-90" width="8" height="80" fill="#e8412f" />
            <circle cx="80" cy="70" r="36" fill="#2a2018" /><circle cx="190" cy="70" r="36" fill="#2a2018" /><path d="M180 -160 l60 -200" stroke="#8d93a1" stroke-width="10" /></g>
          <g fill="none" stroke="#7fe0a0" stroke-width="8" opacity="0.7"><path class="d5-b-w" d="M820 900 q60 150 0 300" /><path class="d5-b-w" d="M880 860 q90 190 0 380" /><path class="d5-b-w" d="M940 820 q120 230 0 460" /></g>'''
svgC = f'''          <defs><linearGradient id="d5-c-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a2030" /><stop offset="1" stop-color="#c26a4a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#d5-c-sky)" />
          <rect y="1180" width="1080" height="740" fill="#1d3a4a" />
          <g stroke="#9fc4d8" stroke-width="4" opacity="0.4">{"".join(f'<line x1="{x}" y1="{y}" x2="{x + 120}" y2="{y}" />' for x, y in [(80, 1400), (600, 1500), (300, 1700), (760, 1800)])}</g>
          <path d="M0 1180 L1080 1180 L1080 1220 L0 1220 Z" fill="#3a4250" />
          <g fill="#2a2f3b"><rect x="180" y="760" width="40" height="420" /><rect x="860" y="760" width="40" height="420" /></g>
          <path d="M200 760 Q540 1100 880 760" stroke="#2a2f3b" stroke-width="12" fill="none" />
          <g stroke="#2a2f3b" stroke-width="5">''' + "".join(f'<line x1="{x}" y1="{760 + 0.0014 * (x - 540) ** 2 * 0 + (340 - 340 * ((x - 540) / 340) ** 2) * 1:.0f}" x2="{x}" y2="1180" />' for x in range(240, 860, 60)) + '''</g>
          <g transform="translate(960 1180) scale(0.8)"><path d="M-60 0 h120 v-80 l-60 -40 l-60 40 z" fill="#5f8f5c" /><text x="0" y="-150" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="44" fill="#7fe0a0">SAFE ZONE</text></g>'''
body = "\n".join([card("d5-a", a, ad, 5, "Radio"),
                  beat("d5-b", b, bd, svgB, title("d5-b-title", '<span style="color: #7fe0a0">Safe Zone</span>', top=400, size=150)),
                  beat("d5-c", c, cd, svgC, title("d5-c-title", 'One<br /><span class="r">Chance</span>', top=390, size=120))])
js = "\n".join([card_js("d5-a", a), push("#d5-b-cam", b, bd),
                f'    tl.fromTo(".d5-b-w", {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.25, repeat: 7, yoyo: true, stagger: 0.12 }}, {r2(b)});',
                f'    tl.fromTo("#d5-b-needle", {{ x: -60 }}, {{ x: 100, duration: 1.2, ease: "power2.inOut" }}, {r2(b + 0.1)});',
                slam("#d5-b-title", loc("day5", w("d5", 8)) - 0.05),
                push("#d5-c-cam", c, cd, 1.0, 1.1),
                slam("#d5-c-title", loc("day5", w("d5", 16)) - 0.05)])
files["day5"] = comp("day5", body, js)

# ===================== DAY 7: Brücke voller Menschen → Biss =====================
(a, ad), (b, bd), (c, cd) = beats("day7", [SC["day7"][0], st("d7"), round(w("d7", 8) - 0.12, 2)])
crowd = "".join(f'<g class="d7-b-p"><!--@person id="d7-b-p{i}" x="{x}" y="{y}" s="{sc}" jacket="{j}" hair="{h}" skin="{sk}" style="{stl}" mood="worried"--></g>'
                for i, (x, y, sc, j, h, sk, stl) in enumerate([(160, 1660, 0.6, "#5f8f5c", "#2a1a10", "#c98d62", "short"), (380, 1700, 0.62, "#8a3a4a", "#6b4330", "#f1c7a0", "long"),
                                                              (700, 1690, 0.62, "#4a5a6a", "#1e140c", "#a8714a", "spiky"), (920, 1660, 0.6, "#c96b9a", "#2a1a10", "#f1c7a0", "long"),
                                                              (540, 1880, 0.8, "#3d6b8f", "#2a1a10", "#f1c7a0", "short")]))
svgB = f'''          <defs><linearGradient id="d7-b-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a2a3a" /><stop offset="1" stop-color="#8a6a5a" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#d7-b-sky)" />
          <path d="M0 1200 L1080 1200 L1080 1920 L0 1920 Z" fill="#3a4250" />
          <g stroke="#2a2f3b" stroke-width="14"><line x1="0" y1="1240" x2="1080" y2="1240" /><line x1="0" y1="1180" x2="1080" y2="1180" /></g>
          {crowd}'''
svgC = f'''          <rect width="1080" height="1920" fill="#1a1416" />
          <path d="M-40 1000 Q540 920 1120 1040 L1120 1360 Q540 1260 -40 1340 Z" fill="#a8714a" />
          <path d="M-40 1000 Q540 920 1120 1040" stroke="#7a4a2a" stroke-width="6" fill="none" />
          <rect x="-40" y="930" width="300" height="440" fill="#8a3a4a" />
          <g transform="translate(600 1140)"><g id="d7-c-bite"><path d="M-80 -20 q80 -50 160 0 M-80 30 q80 50 160 0" stroke="#5a1a1a" stroke-width="12" fill="none" stroke-linecap="round" stroke-dasharray="14 12" />
            <ellipse cx="0" cy="5" rx="110" ry="70" fill="#8a2a2a" opacity="0.25" /></g></g>
          {rings("d7-c-rg", 600, 1140, 3, 140, 60)}'''
body = "\n".join([card("d7-a", a, ad, 7, "The bridge"),
                  beat("d7-b", b, bd, svgB, title("d7-b-title", '<span class="o">Survivors</span>', top=400, size=140)),
                  beat("d7-c", c, cd, svgC, title("d7-c-title", '<span class="r">Bite Mark</span>', top=420, size=150))])
bm = loc("day7", w("d7", 13))
js = "\n".join([card_js("d7-a", a), push("#d7-b-cam", b, bd),
                f'    tl.fromTo(".d7-b-p", {{ y: 0 }}, {{ y: -14, duration: 0.4, repeat: 5, yoyo: true, stagger: 0.1, ease: "sine.inOut" }}, {r2(b)});',
                slam("#d7-b-title", b + 0.15),
                f'    tl.fromTo("#d7-c-cam", {{ scale: 1.0 }}, {{ scale: 1.25, duration: {r2(cd)}, ease: "power2.in" }}, {r2(c)});',
                f'    tl.fromTo("#d7-c-bite", {{ opacity: 0, scale: 0.7, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.3 }}, {r2(bm - 0.15)});',
                ring_js("d7-c-rg", bm, 3), slam("#d7-c-title", bm - 0.05), shake("#d7-c-cam", bm + 0.1)])
files["day7"] = comp("day7", body, js)

# ===================== FRAGE =====================
s0, d = SC["frage"]
svg = f'''          <rect width="1080" height="1920" fill="#1a1f2b" />
          <circle cx="540" cy="1250" r="440" fill="#e8412f" opacity="0.08" />
          <rect y="1720" width="1080" height="200" fill="#232a3a" />
          <!--@person id="q-me" x="540" y="1760" s="1.0" {ME} mood="worried"-->
          {Z("q-z", 930, 1700, "0.6", 'flip="1"')}'''
extra = "\n".join([title("q-title", 'Warn them<br /><span class="r">or walk?</span>', top=210, size=130),
                   '      <div id="q-yes" class="q-choice" style="left: 40px"><span class="chip o">Warn</span></div>',
                   '      <div id="q-no" class="q-choice" style="left: 740px"><span class="chip r">Walk</span></div>',
                   chip("q-com", "Comments →", top=640, cls="o", size=56)])
css = '    .q-choice { position: absolute; top: 980px; width: 300px; text-align: center; }\n    .q-choice .chip { font-size: 92px; padding: 6px 44px 10px; }'
com = loc("frage", L["cta1"]["start"])
js = "\n".join([push("#q-a-cam", 0, d, 1.0, 1.06),
                f'    tl.fromTo("#q-title", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.2, ease: "power3.out" }}, 0.04);',
                popc("#q-yes", loc("frage", w("frage", 2))), popc("#q-no", loc("frage", w("frage", 9))),
                f'    tl.fromTo("#q-com", {{ opacity: 0, x: -80 }}, {{ opacity: 1, x: 0, duration: 0.25, ease: "power3.out" }}, {r2(com)});',
                f'    tl.fromTo("#q-z", {{ x: 60 }}, {{ x: -40, duration: {r2(d)}, ease: "none" }}, 0);'])
files["frage"] = comp("frage", beat("q-a", 0, d, svg, extra), js, css)

# ===================== OUTRO =====================
s0, d = SC["outro"]
css = '''    #root { background: radial-gradient(ellipse 70% 55% at 50% 48%, #4a5a4a 0%, #2a322c 60%, #161a18 100%); }
    #o-share { position: absolute; top: 700px; left: 0; width: 1080px; text-align: center;
      font-family: "Oswald", sans-serif; font-weight: 700; font-size: 70px; letter-spacing: 0.08em; color: var(--ink); text-transform: uppercase;
      text-shadow: 0 5px 0 rgba(0,0,0,.45); }
    #o-share .o { color: var(--orange); }
    #o-series { position: absolute; top: 1580px; left: 0; width: 1080px; text-align: center;
      font-family: "Oswald", sans-serif; font-weight: 700; font-size: 50px; letter-spacing: 0.2em; color: var(--ink); text-transform: uppercase; }
    #o-series .o { color: #8fae7a; letter-spacing: 0; }'''
body = f'''    <svg class="full" viewBox="0 0 1080 1920">
      <g transform="translate(540 1000)"><g id="o-gear"><circle r="360" fill="#3a443c" /><circle r="320" fill="#4a564c" />
        <g fill="#8fae7a"><circle r="56" /><circle cx="0" cy="-130" r="70" /><circle cx="113" cy="65" r="70" /><circle cx="-113" cy="65" r="70" /></g>
        <g fill="#4a564c"><circle r="30" /><circle cx="0" cy="-150" r="40" /><circle cx="130" cy="75" r="40" /><circle cx="-130" cy="75" r="40" /></g></g></g>
      <path id="o-arrow" d="M880 1010 q60 40 20 110 l-10 -36 m10 36 l-36 -6" fill="none" stroke="#f4a62a" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <div id="o-part" class="title" style="top: 190px; font-size: 140px"><span class="o">Part 1</span></div>
    <div id="o-q" class="title" style="top: 360px; font-size: 118px"><span class="r" style="color: #ff5a45">Warn them<br />or walk?</span></div>
    <div id="o-share">Share <span class="o">→ Part 2</span> ↗</div>
    <div id="o-follow" class="chip-row" style="top: 1050px"><span class="chip o" style="font-size: 64px; border-radius: 40px; padding: 6px 40px 10px">Follow for Part 2</span></div>
    <div id="o-series"><span class="o">☣</span> Zombie Apocalypse</div>'''
js = "\n".join([
    '    tl.fromTo("#o-gear", { rotation: -25, scale: 0.85 }, { rotation: 0, scale: 1, duration: 1.2, ease: "power3.out" }, 0);',
    '    tl.fromTo("#o-part", { opacity: 0, scale: 1.5 }, { opacity: 1, scale: 1, duration: 0.18, ease: "power4.in" }, 0.035);',
    '    tl.fromTo("#o-q", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.22, ease: "power3.out" }, 0.21);',
    '    tl.fromTo("#o-follow", { opacity: 0, scale: 0.4 }, { opacity: 1, scale: 1, duration: 0.22, ease: "back.out(2.6)" }, 0.46);',
    '    tl.fromTo("#o-series", { opacity: 0 }, { opacity: 1, duration: 0.3 }, 0.54);',
    '    tl.fromTo("#o-arrow", { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.2 }, 0.58);',
    f'    tl.to("#o-follow", {{ scale: 1.06, duration: 0.35, repeat: {int((d - 0.8) / 0.35) // 2 * 2 + 1}, yoyo: true, ease: "sine.inOut" }}, 0.79);',
    '    tl.fromTo("#o-share", { opacity: 0, x: -60 }, { opacity: 1, x: 0, duration: 0.25, ease: "power3.out" }, 1.2);'])
files["outro"] = comp("outro", body, js, css)

for n, html in files.items():
    open(os.path.join(P, "compositions", n + ".html"), "w").write(html)

hud = {"start": SC["day1"][0], "end": SC["frage"][0], "label": "WATER", "pill": "⚡ POWER", "day_label": "DAY",
       "days": [{"t": SC["day1"][0], "day": 1, "clock": "06:00", "pct": 80},
                {"t": st("d1b"), "day": 1, "clock": "07:15", "pct": 75},
                {"t": SC["day2"][0], "day": 2, "clock": "22:40", "pct": 45},
                {"t": SC["day3"][0], "day": 3, "clock": "09:05", "pct": 5},
                {"t": SC["day5"][0], "day": 5, "clock": "18:30", "pct": 2},
                {"t": SC["day7"][0], "day": 7, "clock": "06:10", "pct": 0}],
       "alert": {"t": round(w("d2", 1), 2)}}
json.dump(hud, open(os.path.join(P, "hud.json"), "w"), indent=1)

g = lambda n: SC[n][0]
sfx = [["sfx-ring", "impact-bass-2", 0.2, 0.2], ["sfx-w1", "whoosh-short", st("hook2"), 0.25], ["sfx-scr", "glitch-1", w("hook2", 6), 0.25], ["sfx-hit", "impact-bass-1", w("hook2", 6) + 0.1, 0.3],
       ["sfx-w2", "whoosh", g("fact"), 0.28], ["sfx-2011", "impact-bass-2", w("fact", 6), 0.22], ["sfx-real", "impact-bass-1", w("fact", 18), 0.22],
       ["sfx-p1", "pop", w("fact2", 2), 0.7], ["sfx-p2", "pop", w("fact2", 3), 0.7], ["sfx-p3", "pop", w("fact2", 6), 0.7],
       ["sfx-w3", "whoosh", g("day1"), 0.3], ["sfx-w4", "whoosh-short", st("d1"), 0.24], ["sfx-ns", "error", w("d1", 3), 0.4],
       ["sfx-w5", "whoosh-short", w("d1", 5) - 0.12, 0.24], ["sfx-al", "error", w("d1", 10), 0.35], ["sfx-w6", "whoosh", st("d1b"), 0.26], ["sfx-st", "impact-bass-1", w("d1b", 10), 0.25],
       ["sfx-w7", "whoosh", g("day2"), 0.3], ["sfx-pw", "glitch-3", w("d2", 1), 0.3], ["sfx-pw2", "impact-bass-2", w("d2", 1), 0.25], ["sfx-gl", "impact-bass-1", w("d2", 7), 0.35],
       ["sfx-w8", "whoosh-short", w("d2", 11) - 0.12, 0.2], ["sfx-drag", "impact-bass-1", w("d2", 17), 0.25],
       ["sfx-w9", "whoosh", g("day3"), 0.3], ["sfx-w10", "whoosh-short", w("d3", 5) - 0.12, 0.24], ["sfx-400", "impact-bass-2", w("d3", 9), 0.22], ["sfx-doz", "riser", w("d3", 16) - 0.3, 0.12],
       ["sfx-w11", "whoosh", g("day5"), 0.3], ["sfx-rad", "glitch-1", st("d5") + 0.1, 0.18], ["sfx-safe", "pop", w("d5", 8), 0.8], ["sfx-w12", "whoosh-short", w("d5", 13) - 0.12, 0.24], ["sfx-ch", "impact-bass-2", w("d5", 16), 0.25],
       ["sfx-w13", "whoosh", g("day7"), 0.3], ["sfx-w14", "whoosh-short", w("d7", 8) - 0.12, 0.26], ["sfx-bite", "impact-bass-1", w("d7", 13), 0.4], ["sfx-bgl", "glitch-3", w("d7", 13) + 0.05, 0.25],
       ["sfx-w15", "whoosh", g("frage"), 0.3], ["sfx-q1", "pop", w("frage", 2), 0.7], ["sfx-q2", "pop", w("frage", 9), 0.7],
       ["sfx-w16", "whoosh-cinematic", g("outro"), 0.22]]
sfx = [[a_, b_, round(t, 2), v] for a_, b_, t, v in sfx]
json.dump({"total": TOTAL, "hud": [SC["day1"][0], round(SC["frage"][0] - SC["day1"][0], 2)],
           "scenes": [[n, SC[n][0], SC[n][1]] for n, _ in order], "sfx": sfx}, open(os.path.join(P, "scenes.json"), "w"), indent=1)
print("Szenen:", ", ".join(f"{n} {SC[n][0]}+{SC[n][1]}" for n, _ in order), "| Länge", TOTAL)
