# Der letzte Mann. Erzeugt alle Szenen (compositions/*.html), hud.json und scenes.json aus assets/timing.json.
# Neue Stimme → place_voice.py → dieses Skript → svg_parts.py . → build_hud.py . → build_index.py → build_captions.py .
import json, random, os

P = os.path.dirname(os.path.abspath(__file__))
tm = json.load(open(os.path.join(P, "assets/timing.json")))
L = {l["id"]: l for l in (tm["lines"] if isinstance(tm, dict) else tm)}
w = lambda lid, i: L[lid]["words"][i]["start"]
st = lambda lid: round(L[lid]["start"] - 0.1, 2)
r2 = lambda x: f"{x:.2f}"

order = [("hook", 0.0), ("fact", st("fact")), ("tag1", st("t1_mark")), ("tag2", st("t2_mark")), ("tag3", st("t3_mark")),
         ("tag5", st("t5_mark")), ("tag7", st("t7_mark")), ("frage", st("frage")), ("outro", st("cta"))]
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

ME = 'jacket="#3a5a4a" pants="#2a2f3b" hair="#2a1a10" skin="#e9c0a0" style="short" beard="full"'
OTHER = lambda pid, x, y, s, jacket="#5a6070", hair="#2a2018", style="short": f'<!--@person id="{pid}" x="{x}" y="{y}" s="{s}" jacket="{jacket}" pants="#2a2f3b" hair="{hair}" skin="#d9c8b8" style="{style}" mood="happy" eyes="blank"-->'


def sparkles(cls, pts, col="#f7c548"):
    return "".join(f'<g transform="translate({x} {y}) scale({sc})"><path class="{cls}" d="M0 -40 L10 -10 L40 0 L10 10 L0 40 L-10 10 L-40 0 L-10 -10 Z" fill="{col}" /></g>' for x, y, sc in pts)


def rings(gid, x, y, n=3, r0=160, gap=70):
    return f'<g transform="translate({x} {y})"><g id="{gid}">' + "".join(f'<circle class="{gid}-c" r="{r0 + i * gap}" fill="none" stroke="#e8412f" stroke-width="12" opacity="0.8" />' for i in range(n)) + '</g></g>'


ring_js = lambda gid, t, rep=3: f'    tl.fromTo(".{gid}-c", {{ scale: 0.7, opacity: 0.9, transformOrigin: "50% 50%" }}, {{ scale: 1.25, opacity: 0, duration: 0.9, repeat: {rep}, stagger: 0.2, ease: "none" }}, {r2(t)});'


def card(bid, s, d, day, sub):
    svg = '          <rect width="1080" height="1920" fill="#1a1f2b" />\n          <circle cx="540" cy="760" r="420" fill="#232a3a" />'
    return beat(bid, s, d, svg, title(f"{bid}-day", f'<span class="o">Tag {day}</span>', top=520, size=270) + "\n" + chip(f"{bid}-chip", sub, top=850))


card_js = lambda bid, s: slam(f"#{bid}-day", s + 0.06) + "\n" + popc(f"#{bid}-chip", s + 0.22)
files = {}

JK = ["#5a6070", "#6a5a5a", "#4a5a6a", "#5a5a4a", "#6a6a74"]
HR = ["#2a2018", "#5a3a22", "#1e140c", "#6b4330"]
STY = ["short", "long", "short", "spiky"]


def crowd(prefix, rows, cls):
    """rows: [(y, s, n, x0, x1)] → Reihen von 'Anderen' (leere Augen, Lächeln)"""
    out, k = [], 0
    for y, s, n, x0, x1 in rows:
        for i in range(n):
            x = x0 + (x1 - x0) * (i + 0.5) / n + (k % 3 - 1) * 12
            out.append(f'<g class="{cls}">' + OTHER(f"{prefix}{k}", f"{x:.0f}", y, s, JK[k % 5], HR[k % 4], STY[k % 4]) + '</g>')
            k += 1
    return "\n          ".join(out)


def window_lit(x, y, w, h, gid):
    return f'<g id="{gid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#f7c548" /><path d="M{x + w / 2} {y} V{y + h} M{x} {y + h / 2} H{x + w}" stroke="#3a2a1a" stroke-width="8" /></g>'


# ===================== HOOK: Menge vor deinem Fenster → leere Augen =====================
(a, ad), (b, bd) = beats("hook", [0.0, st("hook2")])
svgA = f'''          <defs><linearGradient id="h-a-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a0f18" /><stop offset="1" stop-color="#2a3448" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#h-a-sky)" />
          <rect x="300" y="300" width="480" height="1100" fill="#1a2030" />
          {"".join(f'<rect x="{340 + c * 110}" y="{360 + r * 150}" width="70" height="100" fill="#0e1420" />' for r in range(7) for c in range(4))}
          {window_lit(560, 660, 70, 100, "h-a-win")}
          {rings("h-a-rg", 595, 710, 3, 80, 50)}
          <rect y="1400" width="1080" height="520" fill="#141a24" />
          {crowd("h-a-o", [(1560, 0.32, 9, 0, 1080), (1700, 0.4, 7, 0, 1080), (1880, 0.5, 6, -40, 1120)], "h-a-c")}'''
svgB = f'''          <rect width="1080" height="1920" fill="#10141c" />
          <circle cx="540" cy="1100" r="600" fill="#bfe8ff" opacity="0.04" />
          {OTHER("h-b-o0", 220, 1900, "1.1", "#5a6070", "#2a2018", "long")}
          {OTHER("h-b-o2", 860, 1900, "1.1", "#4a5a6a", "#6b4330", "spiky")}
          {OTHER("h-b-o1", 540, 1960, "1.35", "#6a5a5a", "#1e140c", "short")}'''
body = "\n".join([beat("h-a", a, ad, svgA, title("h-a-title", 'Der letzte<br /><span class="r">Mann</span>', top=200, size=140)),
                  beat("h-b", b, bd, svgB, title("h-b-title", '<span class="r">Nicht mehr</span><br />Menschen', top=330, size=130))])
js = "\n".join([push("#h-a-cam", a, ad, 1.0, 1.08), ring_js("h-a-rg", 0.2, 4),
                f'    tl.fromTo("#h-a-win", {{ opacity: 1 }}, {{ opacity: 0.6, duration: 0.3, repeat: 5, yoyo: true }}, {r2(a + 0.4)});',
                f'    tl.fromTo(".h-a-c", {{ y: 0 }}, {{ y: -6, duration: 1.2, repeat: 3, yoyo: true, stagger: 0.05, ease: "sine.inOut" }}, {r2(a)});',
                f'    tl.fromTo("#h-b-cam", {{ scale: 1.0 }}, {{ scale: 1.12, duration: {r2(bd)}, ease: "power1.in" }}, {r2(b)});',
                f'    tl.fromTo(["#h-b-o0-head", "#h-b-o1-head", "#h-b-o2-head"], {{ rotation: -8, transformOrigin: "50% 90%" }}, {{ rotation: 0, duration: 0.6, ease: "power2.out", stagger: 0.15 }}, {r2(b + 0.2)});',
                slam("#h-b-title", loc("hook", w("hook2", 9)) - 0.05), shake("#h-b-cam", loc("hook", w("hook2", 9)) + 0.1)])
files["hook"] = comp("hook", body, js)

# ===================== FAKT: Isolation → du bildest dir nichts ein =====================
(a, ad), (b, bd) = beats("fact", [SC["fact"][0], st("fact2")])
svgA = '''          <rect width="1080" height="1920" fill="#0c1016" />
          <rect x="240" y="600" width="600" height="900" rx="10" fill="#1a2028" stroke="#3a4250" stroke-width="10" />
          <rect x="300" y="1300" width="480" height="120" rx="20" fill="#2a3038" />
          <g fill="none" stroke="#bfe8ff" stroke-width="8" opacity="0.6"><path class="f-a-w" d="M380 900 q-60 80 0 160" /><path class="f-a-w" d="M330 860 q-100 120 0 240" /><path class="f-a-w" d="M700 900 q60 80 0 160" /><path class="f-a-w" d="M750 860 q100 120 0 240" /></g>
          <text x="540" y="1040" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="220" fill="#3a4250">?</text>'''
svgB = f'''          <rect width="1080" height="1920" fill="#141a22" />
          <rect y="1720" width="1080" height="200" fill="#1e242e" />
          <!--@person id="f-b-me" x="540" y="1760" s="1.05" {ME} mood="worried"-->'''
body = "\n".join([beat("f-a", a, ad, svgA, title("f-a-title", '<span class="o">Isolation</span>', top=330, size=150) + "\n" + chip("f-a-chip", "Wenige Tage", top=520, cls="r", size=60)),
                  beat("f-b", b, bd, svgB, title("f-b-title", '<span class="r">Kein Traum</span>', top=330, size=150))])
js = "\n".join([push("#f-a-cam", a, ad), slam("#f-a-title", loc("fact", w("fact", 1)) - 0.05), popc("#f-a-chip", loc("fact", w("fact", 9)) - 0.05),
                f'    tl.fromTo(".f-a-w", {{ opacity: 0.1 }}, {{ opacity: 0.8, duration: 0.35, repeat: 9, yoyo: true, stagger: 0.12 }}, {r2(a)});',
                push("#f-b-cam", b, bd, 1.0, 1.1), slam("#f-b-title", loc("fact", w("fact2", 4)) - 0.05)])
files["fact"] = comp("fact", body, js)

# ===================== TAG 1: Tausende, Fenster, Vorhänge =====================
(a, ad), (b, bd), (c, cd), (d, dd) = beats("tag1", [SC["tag1"][0], st("t1"), round(w("t1", 8) - 0.12, 2), st("t1b")])
svgB = f'''          <defs><linearGradient id="t1-b-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a4a5a" /><stop offset="1" stop-color="#8a9aa8" /></linearGradient></defs>
          <rect width="1080" height="1920" fill="url(#t1-b-sky)" />
          <!--@skyline id="t1-b-sk" y="1100" lit="0" seed="5" color="#2a3240" win="#f7c548"-->
          <rect y="1100" width="1080" height="820" fill="#4a525e" />
          {crowd("t1-b-o", [(1260, 0.22, 14, 0, 1080), (1380, 0.28, 12, 0, 1080), (1530, 0.36, 10, 0, 1080), (1720, 0.46, 8, -40, 1120), (1940, 0.58, 6, -60, 1140)], "t1-b-c")}'''
svgC = f'''          <rect width="1080" height="1920" fill="#1a2030" />
          <rect x="200" y="300" width="680" height="1620" fill="#2a3240" />
          {"".join(f'<rect x="{250 + c * 160}" y="{360 + r * 220}" width="100" height="150" fill="#141a24" />' for r in range(7) for c in range(4))}
          {window_lit(570, 800, 100, 150, "t1-c-win")}
          <g transform="translate(620 875)"><g id="t1-c-me"><circle cx="0" cy="-20" r="26" fill="#0a0d12" /><rect x="-30" y="6" width="60" height="70" rx="20" fill="#0a0d12" /></g></g>
          {rings("t1-c-rg", 620, 875, 3, 120, 60)}'''
svgD = f'''          <rect width="1080" height="1920" fill="#0e1218" />
          <rect x="180" y="560" width="720" height="980" fill="#2a3440" />
          <rect x="180" y="560" width="720" height="980" fill="none" stroke="#3a2a1e" stroke-width="30" />
          <g transform="translate(180 540)"><g id="t1-d-cl"><rect x="0" y="0" width="360" height="1020" fill="#6a2a2a" />{"".join(f'<path d="M{x} 0 V1020" stroke="#4a1a1a" stroke-width="10" />' for x in range(40, 360, 60))}</g></g>
          <g transform="translate(900 540)"><g id="t1-d-cr"><rect x="-360" y="0" width="360" height="1020" fill="#6a2a2a" />{"".join(f'<path d="M{-x} 0 V1020" stroke="#4a1a1a" stroke-width="10" />' for x in range(40, 360, 60))}</g></g>
          <rect x="140" y="520" width="800" height="30" rx="10" fill="#3a2a1e" />
          <g id="t1-d-ws" font-family="Playfair Display" font-style="italic" font-weight="600" fill="#bfe8ff"><text class="t1-d-w" x="300" y="1700" font-size="54" opacity="0.7">…psst…</text><text class="t1-d-w" x="620" y="1780" font-size="44" opacity="0.5">…du…</text></g>'''
body = "\n".join([card("t1-a", a, ad, 1, "6 Uhr"),
                  beat("t1-b", b, bd, svgB, title("t1-b-title", '<span class="r">Tausende</span>', top=400, size=150)),
                  beat("t1-c", c, cd, svgC, title("t1-c-title", 'Dein<br /><span class="r">Fenster</span>', top=390, size=120)),
                  beat("t1-d", d, dd, svgD, title("t1-d-title", '<span class="r">Geflüster</span>', top=390, size=140))])
js = "\n".join([card_js("t1-a", a), push("#t1-b-cam", b, bd, 1.0, 1.1), slam("#t1-b-title", loc("tag1", w("t1", 4)) - 0.05),
                f'    tl.fromTo(".t1-b-c", {{ y: 0 }}, {{ y: -4, duration: 0.9, repeat: 3, yoyo: true, stagger: 0.01 }}, {r2(b)});',
                f'    tl.fromTo("#t1-c-cam", {{ scale: 1.0 }}, {{ scale: 1.25, duration: {r2(cd)}, ease: "power1.in" }}, {r2(c)});', ring_js("t1-c-rg", loc("tag1", w("t1", 15)) - 0.1, 2),
                slam("#t1-c-title", loc("tag1", w("t1", 15)) - 0.05),
                f'    tl.fromTo("#t1-d-cl", {{ scaleX: 0.15, transformOrigin: "0% 50%" }}, {{ scaleX: 1, duration: 0.8, ease: "power2.inOut" }}, {r2(loc("tag1", w("t1b", 1)))});',
                f'    tl.fromTo("#t1-d-cr", {{ scaleX: 0.15, transformOrigin: "100% 50%" }}, {{ scaleX: 1, duration: 0.8, ease: "power2.inOut" }}, {r2(loc("tag1", w("t1b", 1)))});',
                f'    tl.fromTo(".t1-d-w", {{ opacity: 0, y: 30 }}, {{ opacity: 0.8, y: -20, duration: 0.8, stagger: 0.4 }}, {r2(loc("tag1", w("t1b", 8)) - 0.1)});',
                slam("#t1-d-title", loc("tag1", w("t1b", 12)) - 0.05)])
files["tag1"] = comp("tag1", body, js)

# ===================== TAG 2: nachts raus, sie lächeln =====================
(a, ad), (b, bd), (c, cd) = beats("tag2", [SC["tag2"][0], st("t2"), round(w("t2", 7) - 0.12, 2)])
svgB = f'''          <defs><radialGradient id="t2-b-lamp" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffcf8a" stop-opacity="0.45" /><stop offset="1" stop-color="#ffcf8a" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#070a10" />
          <!--@skyline id="t2-b-sk" y="1200" lit="0" seed="8" color="#0e1420" win="#f7c548"-->
          <rect y="1200" width="1080" height="720" fill="#10141c" />
          <rect x="840" y="700" width="16" height="560" fill="#1a1e26" /><path d="M848 700 q-80 0 -100 40" stroke="#1a1e26" stroke-width="14" fill="none" />
          <circle cx="740" cy="760" r="380" fill="url(#t2-b-lamp)" />
          <g id="t2-b-walk"><!--@man id="t2-b-me" x="300" y="1800" s="0.7" pose="walk" shirt="#3a5a4a" pants="#1a1e26" rim="#ffcf8a"--></g>
          {crowd("t2-b-o", [(1330, 0.28, 3, 600, 1040)], "t2-b-c")}'''
svgC = f'''          <rect width="1080" height="1920" fill="#06080c" />
          {OTHER("t2-c-o0", 200, 2100, "1.2", "#4a5a6a", "#2a2018", "short")}
          {OTHER("t2-c-o1", 540, 2050, "1.35", "#5a6070", "#5a3a22", "long")}
          {OTHER("t2-c-o2", 880, 2100, "1.2", "#6a5a5a", "#1e140c", "spiky")}'''
body = "\n".join([card("t2-a", a, ad, 2, "Nachts"),
                  beat("t2-b", b, bd, svgB, title("t2-b-title", '<span class="o">Keiner schläft</span>', top=400, size=120)),
                  beat("t2-c", c, cd, svgC, title("t2-c-title", 'Sie<br /><span class="r">lächeln</span>', top=390, size=130))])
js = "\n".join([card_js("t2-a", a), push("#t2-b-cam", b, bd),
                f'    tl.fromTo("#t2-b-walk", {{ x: -120 }}, {{ x: 120, duration: {r2(bd)}, ease: "none" }}, {r2(b)});',
                slam("#t2-b-title", loc("tag2", w("t2", 5)) - 0.05),
                f'    tl.fromTo("#t2-c-cam", {{ scale: 1.0 }}, {{ scale: 1.15, duration: {r2(cd)}, ease: "power1.in" }}, {r2(c)});',
                f'    tl.fromTo(["#t2-c-o0-head", "#t2-c-o1-head", "#t2-c-o2-head"], {{ rotation: -6, transformOrigin: "50% 90%" }}, {{ rotation: 6, duration: 1.4, repeat: 1, yoyo: true, ease: "sine.inOut", stagger: 0.2 }}, {r2(c)});',
                slam("#t2-c-title", loc("tag2", w("t2", 15)) - 0.05)])
files["tag2"] = comp("tag2", body, js)

# ===================== TAG 3: Zettel in deiner Handschrift =====================
(a, ad), (b, bd), (c, cd) = beats("tag3", [SC["tag3"][0], st("t3"), round(w("t3", 8) - 0.12, 2)])
svgB = '''          <rect width="1080" height="1920" fill="#1e242c" />
          <g fill="#2a3038">''' + "".join(f'<rect x="{x}" y="500" width="200" height="900" />' for x in (40, 840)) + '''</g>
          <g fill="#8d93a1">''' + "".join(f'<rect x="{x}" y="{y}" width="200" height="14" />' for x in (40, 840) for y in (700, 900, 1100, 1300)) + '''</g>
          <rect x="260" y="1200" width="560" height="200" rx="16" fill="#3a4250" /><rect x="280" y="1120" width="200" height="90" rx="10" fill="#14161c" /><text x="380" y="1182" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="44" fill="#7fe0a0">0,00</text>
          <g transform="translate(640 1190) rotate(-8)"><g id="t3-b-note"><rect x="-90" y="-60" width="180" height="120" fill="#f4efe4" /><path d="M-60 -20 h120 M-60 10 h90" stroke="#3a3a4a" stroke-width="6" /></g></g>'''
svgC = '''          <rect width="1080" height="1920" fill="#0e1218" />
          <g transform="translate(540 1000) rotate(-4)"><rect x="-360" y="-300" width="720" height="560" fill="#f4efe4" /><rect x="-360" y="-300" width="720" height="40" fill="#e0d8c4" />
            <text x="0" y="-60" text-anchor="middle" font-family="Playfair Display" font-style="italic" font-weight="600" font-size="96" fill="#1a1e2a">Bleib nicht</text>
            <text x="0" y="70" text-anchor="middle" font-family="Playfair Display" font-style="italic" font-weight="600" font-size="96" fill="#1a1e2a">hier.</text>
            <path id="t3-c-ul" d="M-200 120 q200 30 400 -10" stroke="#8a2a22" stroke-width="8" fill="none" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" /></g>'''
body = "\n".join([card("t3-a", a, ad, 3, "Supermarkt"),
                  beat("t3-b", b, bd, svgB, title("t3-b-title", '<span class="o">Ein Zettel</span>', top=400, size=140)),
                  beat("t3-c", c, cd, svgC, title("t3-c-title", 'Deine<br /><span class="r">Handschrift</span>', top=330, size=110))])
js = "\n".join([card_js("t3-a", a), push("#t3-b-cam", b, bd, 1.0, 1.2), slam("#t3-b-title", loc("tag3", w("t3", 4)) - 0.05),
                f'    tl.fromTo("#t3-b-note", {{ scale: 1, transformOrigin: "50% 50%" }}, {{ scale: 1.12, duration: 0.3, repeat: 3, yoyo: true }}, {r2(loc("tag3", w("t3", 4)))});',
                push("#t3-c-cam", c, cd, 1.0, 1.1), slam("#t3-c-title", loc("tag3", w("t3", 10)) - 0.05),
                f'    tl.fromTo("#t3-c-ul", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.5 }}, {r2(loc("tag3", w("t3", 13)))});'])
files["tag3"] = comp("tag3", body, js)

# ===================== TAG 5: Keller, Schritte über dir =====================
(a, ad), (b, bd) = beats("tag5", [SC["tag5"][0], st("t5")])
steps = "".join(f'<g class="t5-b-s" transform="translate({x} {y})"><ellipse rx="34" ry="14" fill="#2a2f3b" /><rect x="-14" y="-200" width="28" height="190" fill="#3a4250" /></g>' for x, y in [(160, 760), (300, 770), (440, 760), (600, 770), (740, 760), (880, 770), (380, 765), (680, 765)])
svgB = f'''          <rect width="1080" height="1920" fill="#06080b" />
          <rect y="0" width="1080" height="780" fill="#1a1e26" />
          {steps}
          <rect y="780" width="1080" height="60" fill="#3a3028" />
          <g id="t5-b-dust" fill="#8d8478">{"".join(f'<circle class="t5-b-d" cx="{x}" cy="850" r="4" />' for x in range(380, 720, 40))}</g>
          <rect y="1700" width="1080" height="220" fill="#0e1014" />
          <g transform="translate(540 1720)"><g id="t5-b-me"><!--@person id="t5-b-p" x="0" y="0" s="0.8" {ME} mood="shocked"--></g></g>
          <rect id="t5-b-dark" width="1080" height="1920" fill="#000" opacity="0.15" />'''
stop = loc("tag5", w("t5", 15))
body = beat("t5-b", b, bd, svgB, title("t5-b-title", '<span class="r">Über dir</span>', top=900, size=150))
body = "\n".join([card("t5-a", a, ad, 5, "Keller"), body])
js = "\n".join([card_js("t5-a", a), push("#t5-b-cam", b, bd, 1.0, 1.06),
                f'    tl.fromTo(".t5-b-s", {{ opacity: 0, x: -200 }}, {{ opacity: 1, x: 0, duration: 0.6, stagger: 0.15, ease: "power1.out" }}, {r2(loc("tag5", w("t5", 11)) - 0.1)});',
                f'    tl.fromTo(".t5-b-d", {{ y: 0, opacity: 1 }}, {{ y: 500, opacity: 0, duration: 1.4, stagger: 0.08, ease: "power1.in" }}, {r2(stop)});',
                f'    tl.fromTo("#t5-b-me", {{ y: 0 }}, {{ y: 6, duration: 0.08, repeat: 9, yoyo: true }}, {r2(stop)});',
                slam("#t5-b-title", loc("tag5", w("t5", 19)) - 0.05), shake("#t5-b-cam", loc("tag5", w("t5", 19)) + 0.05)])
files["tag5"] = comp("tag5", body, js)

# ===================== TAG 7: Klopfen, deine Stimme =====================
(a, ad), (b, bd), (c, cd) = beats("tag7", [SC["tag7"][0], st("t7"), round(w("t7", 3) - 0.12, 2)])
door = '''<rect x="210" y="520" width="660" height="1120" rx="12" fill="#4a3220" />
          <rect x="260" y="580" width="250" height="420" rx="10" fill="#3a2616" /><rect x="570" y="580" width="250" height="420" rx="10" fill="#3a2616" />
          <rect x="260" y="1060" width="250" height="520" rx="10" fill="#3a2616" /><rect x="570" y="1060" width="250" height="520" rx="10" fill="#3a2616" />
          <g transform="translate(790 1080)"><rect x="-10" y="-60" width="40" height="120" rx="12" fill="#8d93a1" /><rect x="-110" y="-16" width="130" height="34" rx="16" fill="#b8892e" /></g>
          <rect x="210" y="1640" width="660" height="12" fill="#bfe8ff" opacity="0.5" />'''
svgB = f'''          <rect width="1080" height="1920" fill="#0c0a08" />
          <g id="t7-b-door">{door}</g>
          {rings("t7-b-rg", 540, 900, 3, 120, 70)}'''
svgC = f'''          <rect width="1080" height="1920" fill="#0c0a08" />
          {door}
          <g transform="translate(540 1500)"><g id="t7-c-wave" fill="#bfe8ff">{"".join(f'<rect class="t7-c-b" x="{-260 + i * 40}" y="-60" width="22" height="120" rx="11" />' for i in range(14))}</g></g>'''
kn = loc("tag7", w("t7", 1))
body = "\n".join([card("t7-a", a, ad, 7, "Es klopft"),
                  beat("t7-b", b, bd, svgB, title("t7-b-title", '<span class="r">3× Klopfen</span>', top=390, size=140)),
                  beat("t7-c", c, cd, svgC, title("t7-c-title", '„Mach auf.<br /><span class="r">Ich bin\'s.“</span>', top=330, size=110))])
js = "\n".join([card_js("t7-a", a), push("#t7-b-cam", b, bd, 1.0, 1.06),
                f'    tl.fromTo("#t7-b-door", {{ x: 0 }}, {{ x: 10, duration: 0.05, repeat: 1, yoyo: true }}, {r2(kn - 0.05)});',
                f'    tl.to("#t7-b-door", {{ x: 10, duration: 0.05, repeat: 1, yoyo: true }}, {r2(kn + 0.45)});',
                f'    tl.to("#t7-b-door", {{ x: 10, duration: 0.05, repeat: 1, yoyo: true }}, {r2(kn + 0.9)});',
                ring_js("t7-b-rg", kn, 2), slam("#t7-b-title", kn - 0.05),
                f'    tl.fromTo("#t7-c-cam", {{ scale: 1.0 }}, {{ scale: 1.15, duration: {r2(cd)}, ease: "power1.in" }}, {r2(c)});',
                f'    tl.fromTo(".t7-c-b", {{ scaleY: 0.2, transformOrigin: "50% 50%" }}, {{ scaleY: 1, duration: 0.18, repeat: {int(cd / 0.18)}, yoyo: true, stagger: {{ each: 0.05, from: "center" }} }}, {r2(c)});',
                slam("#t7-c-title", loc("tag7", w("t7", 12)) - 0.05)])
files["tag7"] = comp("tag7", body, js)

# ===================== FRAGE =====================
s0, d = SC["frage"]
svg = f'''          <rect width="1080" height="1920" fill="#14100c" />
          <rect x="590" y="520" width="440" height="1180" rx="10" fill="#3a2616" /><rect x="590" y="1700" width="440" height="10" fill="#bfe8ff" opacity="0.5" />
          <rect y="1720" width="1080" height="200" fill="#1a1410" />
          <!--@person id="q-me" x="320" y="1760" s="1.0" {ME} mood="worried"-->'''
extra = "\n".join([title("q-title", 'Würdest du<br /><span class="r">öffnen?</span>', top=210, size=130),
                   '      <div id="q-yes" class="q-choice" style="left: 40px"><span class="chip o">Auf</span></div>',
                   '      <div id="q-no" class="q-choice" style="left: 740px"><span class="chip r">Zu</span></div>',
                   chip("q-com", "In die Kommentare →", top=640, cls="o", size=56)])
css = '    .q-choice { position: absolute; top: 980px; width: 300px; text-align: center; }\n    .q-choice .chip { font-size: 92px; padding: 6px 44px 10px; }'
com = loc("frage", L["cta1"]["start"])
js = "\n".join([push("#q-a-cam", 0, d, 1.0, 1.06),
                f'    tl.fromTo("#q-title", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.2, ease: "power3.out" }}, 0.04);',
                popc("#q-yes", loc("frage", w("frage", 3))), popc("#q-no", loc("frage", w("frage", 4))),
                f'    tl.fromTo("#q-com", {{ opacity: 0, x: -80 }}, {{ opacity: 1, x: 0, duration: 0.25, ease: "power3.out" }}, {r2(com)});'])
files["frage"] = comp("frage", beat("q-a", 0, d, svg, extra), js, css)

# ===================== OUTRO =====================
s0, d = SC["outro"]
css = '''    #root { background: radial-gradient(ellipse 70% 55% at 50% 48%, #3a4250 0%, #1e242e 60%, #101318 100%); }
    #o-share { position: absolute; top: 700px; left: 0; width: 1080px; text-align: center;
      font-family: "Oswald", sans-serif; font-weight: 700; font-size: 70px; letter-spacing: 0.08em; color: var(--ink); text-transform: uppercase;
      text-shadow: 0 5px 0 rgba(0,0,0,.45); }
    #o-share .o { color: var(--orange); }
    #o-series { position: absolute; top: 1580px; left: 0; width: 1080px; text-align: center;
      font-family: "Oswald", sans-serif; font-weight: 700; font-size: 50px; letter-spacing: 0.2em; color: var(--ink); text-transform: uppercase; }
    #o-series .o { color: #bfe8ff; letter-spacing: 0; }'''
body = f'''    <svg class="full" viewBox="0 0 1080 1920">
      <g transform="translate(540 1000)"><g id="o-gear"><circle r="360" fill="#2a323e" /><circle r="320" fill="#3a4250" />
        <ellipse cx="-90" cy="-20" rx="70" ry="80" fill="#dff6ff" /><ellipse cx="90" cy="-20" rx="70" ry="80" fill="#dff6ff" />
        <ellipse cx="-90" cy="-20" rx="100" ry="110" fill="#bfe8ff" opacity="0.25" /><ellipse cx="90" cy="-20" rx="100" ry="110" fill="#bfe8ff" opacity="0.25" /></g></g>
      <path id="o-arrow" d="M880 1010 q60 40 20 110 l-10 -36 m10 36 l-36 -6" fill="none" stroke="#f4a62a" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <div id="o-part" class="title" style="top: 190px; font-size: 140px"><span class="o">Teil 1</span></div>
    <div id="o-q" class="title" style="top: 360px; font-size: 118px"><span class="r" style="color: #ff5a45">Machst du<br />auf?</span></div>
    <div id="o-share">Teilen <span class="o">→ Teil 2</span> ↗</div>
    <div id="o-follow" class="chip-row" style="top: 1050px"><span class="chip o" style="font-size: 64px; border-radius: 40px; padding: 6px 40px 10px">Folge für Teil 2</span></div>
    <div id="o-series"><span class="o">◉</span> Der letzte Mann</div>'''
js = "\n".join([
    '    tl.fromTo("#o-gear", { rotation: -10, scale: 0.85 }, { rotation: 0, scale: 1, duration: 1.2, ease: "power3.out" }, 0);',
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

kn_g = w("t7", 1)
hud = {"start": SC["tag1"][0], "end": SC["frage"][0], "label": "VORRÄTE", "pill": "◉ VERSTECKT",
       "days": [{"t": SC["tag1"][0], "day": 1, "clock": "06:00", "pct": 90},
                {"t": st("t1b"), "day": 1, "clock": "06:12", "pct": 88},
                {"t": SC["tag2"][0], "day": 2, "clock": "02:40", "pct": 70},
                {"t": SC["tag3"][0], "day": 3, "clock": "14:05", "pct": 55},
                {"t": SC["tag5"][0], "day": 5, "clock": "23:10", "pct": 20},
                {"t": SC["tag7"][0], "day": 7, "clock": "03:33", "pct": 6}],
       "alert": {"t": round(kn_g, 2)}}
json.dump(hud, open(os.path.join(P, "hud.json"), "w"), ensure_ascii=False, indent=1)

g = lambda n: SC[n][0]
sfx = [["sfx-ring", "impact-bass-2", 0.2, 0.2], ["sfx-w1", "whoosh-short", st("hook2"), 0.25], ["sfx-nm", "impact-bass-1", w("hook2", 9), 0.3], ["sfx-gl0", "glitch-3", w("hook2", 9) + 0.03, 0.18],
       ["sfx-w2", "whoosh", g("fact"), 0.26], ["sfx-iso", "impact-bass-2", w("fact", 1), 0.2], ["sfx-w2b", "whoosh-short", st("fact2"), 0.2], ["sfx-kt", "impact-bass-1", w("fact2", 4), 0.22],
       ["sfx-w3", "whoosh", g("tag1"), 0.3], ["sfx-w4", "whoosh-short", st("t1"), 0.24], ["sfx-tsd", "impact-bass-2", w("t1", 4), 0.22],
       ["sfx-w5", "whoosh-short", w("t1", 8) - 0.12, 0.24], ["sfx-fen", "impact-bass-1", w("t1", 15), 0.3], ["sfx-w6", "whoosh", st("t1b"), 0.24], ["sfx-fl", "glitch-1", w("t1b", 11), 0.12],
       ["sfx-w7", "whoosh", g("tag2"), 0.3], ["sfx-w8", "whoosh-short", st("t2"), 0.22], ["sfx-ks", "impact-bass-2", w("t2", 5), 0.2], ["sfx-w9", "whoosh-short", w("t2", 7) - 0.12, 0.24], ["sfx-lae", "impact-bass-1", w("t2", 15), 0.3],
       ["sfx-w10", "whoosh", g("tag3"), 0.3], ["sfx-w11", "whoosh-short", st("t3"), 0.22], ["sfx-zt", "pop", w("t3", 4), 0.6], ["sfx-w12", "whoosh-short", w("t3", 8) - 0.12, 0.24], ["sfx-hs", "impact-bass-1", w("t3", 10), 0.3],
       ["sfx-w13", "whoosh", g("tag5"), 0.3], ["sfx-w14", "whoosh-short", st("t5"), 0.22], ["sfx-sch", "click-soft", w("t5", 11), 1.0], ["sfx-st", "impact-bass-1", w("t5", 19), 0.35], ["sfx-gl", "glitch-3", w("t5", 19) + 0.05, 0.2],
       ["sfx-w15", "whoosh", g("tag7"), 0.3], ["sfx-k1", "impact-bass-2", kn_g, 0.35], ["sfx-k2", "impact-bass-2", kn_g + 0.5, 0.35], ["sfx-k3", "impact-bass-2", kn_g + 0.95, 0.35],
       ["sfx-w16", "whoosh-short", w("t7", 3) - 0.12, 0.24], ["sfx-ib", "riser", w("t7", 15) - 0.4, 0.12], ["sfx-ib2", "impact-bass-1", w("t7", 15), 0.35],
       ["sfx-w17", "whoosh", g("frage"), 0.3], ["sfx-q1", "pop", w("frage", 3), 0.7], ["sfx-q2", "pop", w("frage", 4), 0.7],
       ["sfx-w18", "whoosh-cinematic", g("outro"), 0.22]]
sfx = [[a_, b_, round(t, 2), v] for a_, b_, t, v in sfx]
json.dump({"total": TOTAL, "hud": [SC["tag1"][0], round(SC["frage"][0] - SC["tag1"][0], 2)],
           "scenes": [[n, SC[n][0], SC[n][1]] for n, _ in order], "sfx": sfx}, open(os.path.join(P, "scenes.json"), "w"), indent=1)
print("Szenen:", ", ".join(f"{n} {SC[n][0]}+{SC[n][1]}" for n, _ in order), "| Länge", TOTAL)
