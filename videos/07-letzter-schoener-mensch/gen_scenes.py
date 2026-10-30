# Erzeugt alle Szenen (compositions/*.html), hud.json und scenes.json aus assets/timing.json.
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

ME = 'jacket="#e8412f" pants="#2a2f3b" hair="#2a1a10" skin="#f1c7a0" style="spiky" mood="happy"'


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

# ===================== HOOK =====================
(a, ad), (b, bd) = beats("hook", [0.0, st("hook2")])
svgA = f'''          <defs><radialGradient id="h-a-glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#f7c548" stop-opacity="0.55" /><stop offset="1" stop-color="#f4a62a" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#1a1f2b" />
          <g id="h-a-rays" opacity="0.25" fill="#f7c548">{"".join(f'<path d="M540 1180 L{540 + 1400 * __import__("math").cos(k * 0.5236):.0f} {1180 + 1400 * __import__("math").sin(k * 0.5236):.0f} L{540 + 1400 * __import__("math").cos(k * 0.5236 + 0.2):.0f} {1180 + 1400 * __import__("math").sin(k * 0.5236 + 0.2):.0f} Z" />' for k in range(12))}</g>
          <circle cx="540" cy="1150" r="520" fill="url(#h-a-glow)" />
          {rings("h-a-rg", 540, 1180)}
          <rect y="1720" width="1080" height="200" fill="#232a3a" />
          <!--@person id="h-me" x="540" y="1740" s="1.15" {ME}-->
          {sparkles("h-a-sp", [(300, 980, 1.2), (790, 900, 1.5), (250, 1400, 0.9), (840, 1330, 1.1), (700, 760, 0.8)])}'''
pots = [(130, 1760, 0.75, "neutral", ""), (330, 1840, 0.8, "shocked", "cap"), (750, 1840, 0.8, "love", ""), (950, 1760, 0.75, "happy", "tie"), (220, 1420, 0.55, "happy", ""), (860, 1420, 0.55, "neutral", "cap")]
svgB = f'''          <rect width="1080" height="1920" fill="#1b232f" />
          <ellipse cx="540" cy="1100" rx="420" ry="560" fill="#f7c548" opacity="0.08" />
          <rect y="1600" width="1080" height="320" fill="#2c3340" />
          <!--@person id="h-me2" x="540" y="1640" s="1.0" {ME}-->
          {sparkles("h-b-sp", [(380, 1020, 0.8), (700, 980, 1.0)])}
          {"".join(f'<g class="h-b-pot"><!--@potato id="h-b-p{i}" x="{x}" y="{y}" s="{sc}" mood="{m}" acc="{ac}" accent="#3d7bb3"--></g>' for i, (x, y, sc, m, ac) in enumerate(pots))}'''
body = "\n".join([beat("h-a", a, ad, svgA, title("h-a-title", 'Der letzte<br /><span class="r">schöne Mensch</span>', top=330, size=128)),
                  beat("h-b", b, bd, svgB, title("h-b-title", '<span class="o">Kartoffeln</span>', top=420, size=170))])
js = "\n".join([push("#h-a-cam", a, ad, 1.0, 1.06), ring_js("h-a-rg", 0.0, 3),
                f'    tl.fromTo("#h-a-rays", {{ rotation: 0, svgOrigin: "540 1180" }}, {{ rotation: 30, duration: {r2(ad)}, ease: "none" }}, {r2(a)});',
                f'    tl.fromTo(".h-a-sp", {{ scale: 0.4, transformOrigin: "50% 50%" }}, {{ scale: 1.2, duration: 0.35, repeat: 9, yoyo: true, stagger: 0.12 }}, 0);',
                shake("#h-a-cam", loc("hook", w("hook1", 9))),
                f'    tl.fromTo("#h-b-cam", {{ scale: 1.1 }}, {{ scale: 1.0, duration: {r2(bd)}, ease: "power1.out" }}, {r2(b)});',
                f'    tl.fromTo(".h-b-pot", {{ y: 400 }}, {{ y: 0, duration: 0.3, ease: "back.out(1.8)", stagger: 0.12 }}, {r2(b + 0.05)});',
                slam("#h-b-title", loc("hook", w("hook2", 8)) - 0.05), shake("#h-b-cam", loc("hook", w("hook2", 8)) + 0.1)])
files["hook"] = comp("hook", body, js)

# ===================== FAKT =====================
(a, ad), (b, bd) = beats("fact", [SC["fact"][0], st("fact2")])
svgA = '''          <rect width="1080" height="1920" fill="#1a1f2b" />
          <g transform="translate(540 1080)"><g id="f-a-brain">
            <path d="M-260 0 q-40 -200 120 -250 q60 -90 170 -40 q130 -60 200 60 q120 40 90 190 q30 140 -110 170 q-80 80 -200 30 q-140 50 -200 -50 q-110 -20 -70 -110 z" fill="#e88aa0" />
            <g fill="none" stroke="#c45a78" stroke-width="12" stroke-linecap="round"><path d="M-180 -120 q60 -40 110 10 q40 -60 120 -20" /><path d="M-200 40 q80 -30 130 30 q60 -60 150 0 q50 -40 110 0" /><path d="M0 -240 q-20 120 10 330" /></g></g></g>
          <g transform="translate(820 760)"><circle r="120" fill="#f4efe4" /><circle r="100" fill="#fff" stroke="#14161c" stroke-width="8" /><rect x="-20" y="-160" width="40" height="40" rx="6" fill="#f4efe4" />
            <g id="f-a-hand"><path d="M0 0 L0 -80" stroke="#e8412f" stroke-width="10" stroke-linecap="round" /></g><circle r="10" fill="#14161c" /></g>'''
svgB = f'''          <rect width="1080" height="1920" fill="#1b232f" />
          <g transform="translate(540 1180)"><g id="f-b-cup"><path d="M-200 -400 h400 q0 260 -160 320 v120 h90 v60 h-260 v-60 h90 v-120 q-160 -60 -160 -320 z" fill="#f7c548" />
            <path d="M-200 -360 q-120 0 -100 110 q20 80 120 90 M200 -360 q120 0 100 110 q-20 80 -120 90" stroke="#f7c548" stroke-width="28" fill="none" />
            <text x="0" y="-200" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="120" fill="#8f5a0f">DU</text></g></g>
          {"".join(f'<rect class="f-b-conf" x="{random.Random(i).uniform(60, 1020):.0f}" y="{random.Random(i + 50).uniform(-200, 300):.0f}" width="24" height="14" fill="{["#e8412f", "#f4a62a", "#f7c548", "#3d7bb3", "#5f8f5c"][i % 5]}" />' for i in range(30))}'''
body = "\n".join([beat("f-a", a, ad, svgA, title("f-a-title", '<span class="o">0,1 Sek.</span>', top=330, size=190)),
                  beat("f-b", b, bd, svgB, chip("f-b-chip", "Jedes Mal", top=330, cls="o", size=72))])
js = "\n".join([push("#f-a-cam", a, ad),
                f'    tl.fromTo("#f-a-brain", {{ scale: 1.0, transformOrigin: "50% 50%" }}, {{ scale: 1.06, duration: 0.3, repeat: 9, yoyo: true, ease: "sine.inOut" }}, {r2(a)});',
                f'    tl.fromTo("#f-a-hand", {{ rotation: 0, svgOrigin: "0 0" }}, {{ rotation: 360, duration: 0.5, repeat: 5, ease: "none" }}, {r2(a)});',
                slam("#f-a-title", loc("fact", w("fact", 5)) - 0.05), shake("#f-a-cam", loc("fact", w("fact", 5)) + 0.1),
                f'    tl.fromTo("#f-b-cup", {{ scale: 0.3, rotation: -10, transformOrigin: "50% 100%" }}, {{ scale: 1, rotation: 0, duration: 0.35, ease: "back.out(2)" }}, {r2(b + 0.05)});',
                f'    tl.fromTo(".f-b-conf", {{ y: 0, rotation: 0 }}, {{ y: 1600, rotation: 300, duration: 2.2, ease: "none", stagger: 0.02 }}, {r2(b)});',
                popc("#f-b-chip", loc("fact", w("fact2", 4)) - 0.1)])
files["fact"] = comp("fact", body, js)

# ===================== TAG 1: Bäcker, Bus, Büro =====================
(a, ad), (b, bd), (c, cd), (d, dd) = beats("tag1", [SC["tag1"][0], st("t1"), round(w("t1", 7) - 0.12, 2), st("t1b")])
svgB = f'''          <rect width="1080" height="1920" fill="#2a2018" />
          <g fill="#3a2c20"><rect x="0" y="520" width="1080" height="40" /><rect x="0" y="760" width="1080" height="40" /></g>
          <g fill="#d89a4a">{"".join(f'<ellipse cx="{80 + i * 120}" cy="{500 - (i % 2) * 6}" rx="50" ry="26" /><ellipse cx="{120 + i * 120}" cy="{740}" rx="44" ry="30" />' for i in range(9))}</g>
          <!--@potato id="t1-b-baker" x="380" y="1500" s="1.2" mood="love" acc="chef"-->
          <rect x="0" y="1460" width="1080" height="460" fill="#6a4a2e" /><rect x="0" y="1460" width="1080" height="30" fill="#8a6a3e" />
          <g transform="translate(720 1380)"><g id="t1-b-bread"><ellipse rx="150" ry="70" fill="#d89a4a" /><g stroke="#a86a2a" stroke-width="10" fill="none" stroke-linecap="round"><path d="M-80 -30 q20 30 0 60" /><path d="M0 -40 q20 40 0 80" /><path d="M80 -30 q20 30 0 60" /></g></g></g>
          <!--@person id="t1-b-me" x="880" y="1460" s="0.75" {ME}-->'''
svgC = f'''          <rect width="1080" height="1920" fill="#1f3a56" />
          <rect x="0" y="560" width="1080" height="500" fill="#9fd0e8" opacity="0.5" />
          <g fill="#1a2c40">{"".join(f'<rect x="{x}" y="560" width="24" height="500" />' for x in (0, 350, 700, 1056))}</g>
          <rect x="0" y="1060" width="1080" height="860" fill="#2a4a6a" />
          <!--@potato id="t1-c-drv" x="280" y="1640" s="1.05" mood="shocked" acc="cap" accent="#1d3a6a"-->
          <g transform="translate(500 1420) scale(0.8)"><circle r="110" fill="none" stroke="#14161c" stroke-width="22" /><path d="M-100 0 h200 M0 0 v100" stroke="#14161c" stroke-width="16" /></g>
          <!--@person id="t1-c-me" x="760" y="1640" s="0.95" {ME}-->
          {sparkles("t1-c-sp", [(900, 900, 0.8), (640, 860, 0.6)])}'''
svgD = f'''          <rect width="1080" height="1920" fill="#202836" />
          <g fill="#2c3646"><rect x="80" y="520" width="380" height="260" rx="10" /><rect x="620" y="520" width="380" height="260" rx="10" /></g>
          <rect y="1560" width="1080" height="360" fill="#2c3340" />
          <rect x="0" y="1440" width="1080" height="40" fill="#6b5a4a" />
          {"".join(f'<g class="t1-d-clap"><!--@potato id="t1-d-p{i}" x="{x}" y="{y}" s="{sc}" mood="love" arms="up" acc="{ac}" accent="{col}"--></g>' for i, (x, y, sc, ac, col) in enumerate([(120, 1500, 0.7, "tie", "#e8412f"), (340, 1460, 0.6, "", ""), (760, 1460, 0.6, "tie", "#3d7bb3"), (970, 1500, 0.7, "", "")]))}
          <!--@person id="t1-d-me" x="560" y="1760" s="0.95" {ME}-->
          <g id="t1-d-bub" opacity="0"><path d="M640 820 h300 q30 0 30 30 v120 q0 30 -30 30 h-200 l-60 50 l10 -50 h-50 q-30 0 -30 -30 v-120 q0 -30 30 -30 z" fill="#f4efe4" />
            <text x="790" y="940" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="76" fill="#14161c">Hallo</text></g>'''
body = "\n".join([card("t1-a", a, ad, 1, "7 Uhr"),
                  beat("t1-b", b, bd, svgB, chip("t1-b-chip", "Gratis", top=430, cls="o", size=96)),
                  beat("t1-c", c, cd, svgC, title("t1-c-title", '<span class="r">Neben ihm</span>', top=400, size=150)),
                  beat("t1-d", d, dd, svgD, title("t1-d-title", '<span class="o">Applaus</span>', top=400, size=150))])
js = "\n".join([card_js("t1-a", a), push("#t1-b-cam", b, bd),
                f'    tl.fromTo("#t1-b-bread", {{ x: -300 }}, {{ x: 0, duration: 0.4, ease: "back.out(1.6)" }}, {r2(b + 0.3)});',
                popc("#t1-b-chip", loc("tag1", w("t1", 6)) - 0.05),
                f'    tl.fromTo("#t1-c-cam", {{ scale: 1.08, y: 0 }}, {{ scale: 1.0, y: 0, duration: {r2(cd)}, ease: "power1.out" }}, {r2(c)});',
                f'    tl.fromTo("#t1-c-cam > svg", {{ y: 0 }}, {{ y: 6, duration: 0.12, repeat: 19, yoyo: true }}, {r2(c + 0.01)});',
                slam("#t1-c-title", loc("tag1", w("t1", 13)) - 0.05),
                push("#t1-d-cam", d, dd), bounce(".t1-d-clap", d + 0.6, 11, 0.06),
                f'    tl.fromTo("#t1-d-bub", {{ opacity: 0, scale: 0.4, transformOrigin: "30% 100%" }}, {{ opacity: 1, scale: 1, duration: 0.2, ease: "back.out(2.5)" }}, {r2(loc("tag1", w("t1b", 10)) - 0.08)});',
                slam("#t1-d-title", loc("tag1", w("t1b", 2)) - 0.05)])
files["tag1"] = comp("tag1", body, js)

# ===================== TAG 2: Selfie, Marken, Zähne =====================
(a, ad), (b, bd), (c, cd), (d, dd) = beats("tag2", [SC["tag2"][0], st("t2"), round(w("t2", 6) - 0.12, 2), round(w("t2", 12) - 0.12, 2)])
head = lambda pid, x, y, s: f'<!--@person id="{pid}" x="{x}" y="{y}" s="{s}" {ME}-->'
svgB = f'''          <rect width="1080" height="1920" fill="#1a1f2b" />
          <rect x="250" y="520" width="580" height="1080" rx="60" fill="#14161c" /><rect x="276" y="560" width="528" height="1000" rx="40" fill="#3d7bb3" />
          {head("t2-b-me", 540, 1560, 1.1)}
          <g transform="translate(540 1500)"><rect x="-200" y="-50" width="400" height="100" rx="50" fill="#14161c" opacity="0.85" />
            <path d="M-150 10 l-26 -26 a14 14 0 0 1 26 -18 a14 14 0 0 1 26 18 z" fill="#e8412f" />
            <text id="t2-b-cnt" x="40" y="22" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="60" fill="#f4efe4">0</text></g>
          {"".join(f'<g transform="translate({x} {y})"><path class="t2-b-h" d="M0 30 l-36 -36 a20 20 0 0 1 36 -26 a20 20 0 0 1 36 26 z" fill="#e8412f" /></g>' for x, y in [(160, 900), (920, 820), (180, 1300), (940, 1220), (880, 1580)])}'''
boards = "".join(f'''<g transform="translate({x} {y})"><rect x="-170" y="-230" width="340" height="420" rx="12" fill="{bg}" /><rect x="-12" y="190" width="24" height="200" fill="#3a4150" />
            <text x="0" y="-160" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="60" fill="#14161c">{nm}</text></g>''' for x, y, bg, nm in [(200, 920, "#f7c548", "GLOW"), (540, 760, "#f4efe4", "LUXE"), (880, 920, "#e88aa0", "FRESH")])
svgC = f'''          <rect width="1080" height="1920" fill="#1b232f" />
          {boards}
          {head("t2-c-me1", 200, 1100, 0.42)}{head("t2-c-me2", 540, 940, 0.42)}{head("t2-c-me3", 880, 1100, 0.42)}
          <rect y="1500" width="1080" height="420" fill="#2c3340" />'''
svgD = f'''          <rect width="1080" height="1920" fill="#20303a" />
          <rect x="0" y="1600" width="1080" height="320" fill="#d9e4ea" opacity="0.2" />
          <!--@person id="t2-d-me" x="540" y="1760" s="1.15" jacket="#e8412f" pants="#2a2f3b" hair="#2a1a10" skin="#f1c7a0" style="spiky" mood="worried"-->
          <g transform="translate(700 1200) rotate(-30)"><rect x="-10" y="-160" width="20" height="200" rx="8" fill="#3d7bb3" /><rect x="-14" y="-200" width="28" height="50" rx="6" fill="#f4efe4" /></g>
          <g id="t2-d-stink" fill="none" stroke="#7fbf5a" stroke-width="12" stroke-linecap="round">
            <path class="t2-d-s" d="M500 1050 q-30 -40 0 -80 q30 -40 0 -80" /><path class="t2-d-s" d="M580 1040 q-30 -40 0 -80 q30 -40 0 -80" /><path class="t2-d-s" d="M420 1070 q-30 -40 0 -80" /></g>'''
body = "\n".join([card("t2-a", a, ad, 2, "9 Uhr"),
                  beat("t2-b", b, bd, svgB, title("t2-b-title", '<span class="r">10 Mio.</span>', top=390, size=150)),
                  beat("t2-c", c, cd, svgC, title("t2-c-title", '<span class="o">3 Marken</span>', top=390, size=140)),
                  beat("t2-d", d, dd, svgD, title("t2-d-title", '<span class="r">Ungeputzt</span>', top=420, size=150))])
cnt0 = loc("tag2", w("t2", 3)) - 0.1
js = "\n".join([card_js("t2-a", a), push("#t2-b-cam", b, bd),
                f'    const t2c = {{ v: 0 }};',
                f'    tl.fromTo(t2c, {{ v: 0 }}, {{ v: 10, duration: 0.8, ease: "power2.out", onUpdate: () => {{ const e = document.getElementById("t2-b-cnt"); if (e) e.textContent = (t2c.v >= 9.95 ? "10" : t2c.v.toFixed(1).replace(".", ",")) + " Mio."; }} }}, {r2(cnt0)});',
                f'    tl.fromTo(".t2-b-h", {{ y: 0, opacity: 1 }}, {{ y: -300, opacity: 0, duration: 1.2, stagger: 0.15, ease: "power1.out" }}, {r2(b + 0.2)});',
                slam("#t2-b-title", cnt0 + 0.05),
                push("#t2-c-cam", c, cd, 1.0, 1.06),
                f'    tl.fromTo(["#t2-c-me1", "#t2-c-me2", "#t2-c-me3"], {{ scale: 0, transformOrigin: "50% 100%" }}, {{ scale: 1, duration: 0.25, ease: "back.out(2)", stagger: 0.15 }}, {r2(c + 0.05)});',
                slam("#t2-c-title", c + 0.1),
                f'    tl.fromTo("#t2-d-cam", {{ scale: 1.1 }}, {{ scale: 1.0, duration: {r2(dd)}, ease: "power1.out" }}, {r2(d)});',
                f'    tl.fromTo(".t2-d-s", {{ y: 20, opacity: 0.3 }}, {{ y: -40, opacity: 1, duration: 0.5, repeat: 3, yoyo: true, stagger: 0.12 }}, {r2(d)});',
                slam("#t2-d-title", loc("tag2", w("t2", 19)) - 0.05)])
files["tag2"] = comp("tag2", body, js)

# ===================== TAG 3: Fans, Müll, Briefkasten =====================
(a, ad), (b, bd), (c, cd), (d, dd) = beats("tag3", [SC["tag3"][0], st("t3"), round(w("t3", 6) - 0.12, 2), round(w("t3", 13) - 0.12, 2)])
rng = random.Random(7)
fans = "".join(f'<g class="t3-b-fan"><!--@potato id="t3-b-f{i}" x="{x:.0f}" y="{y:.0f}" s="{sc:.2f}" mood="{rng.choice(["love", "happy", "love", "shocked"])}" arms="{rng.choice(["up", "wave", "down"])}"--></g>'
               for i, (x, y, sc) in enumerate([(rng.uniform(40, 1040), 1250 + k * 70, 0.32 + k * 0.08) for k in range(7) for _ in range(3)]))
signs = "".join(f'<g transform="translate({x} {y})"><rect x="-6" y="0" width="12" height="160" fill="#6b4a2a" /><rect x="-80" y="-90" width="160" height="100" rx="8" fill="#f4efe4" /><path d="M0 -10 l-30 -30 a17 17 0 0 1 30 -22 a17 17 0 0 1 30 22 z" fill="#e8412f" /></g>' for x, y in [(200, 1300), (540, 1220), (860, 1320)])
svgB = f'''          <rect width="1080" height="1920" fill="#2a3446" />
          <rect x="340" y="560" width="400" height="660" fill="#6a3519" /><circle cx="680" cy="900" r="20" fill="#f4a62a" /><rect x="320" y="540" width="440" height="30" fill="#4a2a14" />
          <rect y="1200" width="1080" height="720" fill="#3a4250" />
          {signs}
          {fans}'''
svgC = f'''          <rect width="1080" height="1920" fill="#1b232f" />
          <rect x="190" y="560" width="700" height="760" rx="10" fill="#9fd0e8" opacity="0.35" />
          <!--@person id="t3-c-me" x="540" y="1620" s="1.0" jacket="#e8412f" pants="#2a2f3b" hair="#2a1a10" skin="#f1c7a0" style="spiky" mood="worried"-->
          <g transform="translate(720 1440)"><path d="M-70 0 q-20 -120 30 -150 l10 -30 h60 l10 30 q50 30 30 150 z" fill="#14161c" /><path d="M-10 -180 l10 -30 l10 30" stroke="#14161c" stroke-width="10" fill="none" /></g>
          <g fill="#1a2030"><rect x="190" y="560" width="700" height="20" /><rect x="530" y="560" width="20" height="760" /><rect x="190" y="930" width="700" height="20" /></g>
          <g>{"".join(f'<circle cx="{x}" cy="{y}" r="34" fill="#c9955a" /><circle cx="{x - 10}" cy="{y - 6}" r="6" fill="#1a1210" /><circle cx="{x + 12}" cy="{y - 6}" r="6" fill="#1a1210" />' for x, y in [(280, 700), (820, 660), (300, 1100), (800, 1150)])}</g>
          <rect y="1620" width="1080" height="300" fill="#2c3340" />'''
svgD = f'''          <rect width="1080" height="1920" fill="#2a3446" />
          <rect y="1560" width="1080" height="360" fill="#3a4250" />
          <rect x="520" y="1160" width="40" height="420" fill="#4a5262" />
          <g transform="translate(540 1000)"><path d="M-260 -200 h360 q160 0 160 160 v240 h-520 z" fill="#3d7bb3" /><path d="M100 -200 q160 0 160 160 v240 h-160 z" fill="#2f6a9a" />
            <rect x="-210" y="-60" width="260" height="50" rx="12" fill="#14161c" />
            <g id="t3-d-pot"><circle cx="-80" cy="-36" r="46" fill="#c9955a" /><path d="M-104 -40 q10 8 20 0 M-70 -40 q10 8 20 0" stroke="#1a1210" stroke-width="6" fill="none" /></g>
            <rect x="-210" y="-14" width="260" height="20" fill="#3d7bb3" /></g>
          <g id="t3-d-z" font-family="Oswald" font-weight="700" fill="#f4efe4"><text class="t3-d-zz" x="560" y="860" font-size="64">Z</text><text class="t3-d-zz" x="620" y="800" font-size="80">Z</text><text class="t3-d-zz" x="700" y="730" font-size="96">Z</text></g>'''
body = "\n".join([card("t3-a", a, ad, 3, "11 Uhr"),
                  beat("t3-b", b, bd, svgB, title("t3-b-title", '<span class="r">200 Fans</span>', top=390, size=150)),
                  beat("t3-c", c, cd, svgC, chip("t3-c-chip", "Keine Chance", top=400, cls="r", size=56)),
                  beat("t3-d", d, dd, svgD, title("t3-d-title", '<span class="o">Briefkasten</span>', top=400, size=140))])
js = "\n".join([card_js("t3-a", a), push("#t3-b-cam", b, bd),
                f'    tl.fromTo(".t3-b-fan", {{ y: 300, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.25, ease: "back.out(1.6)", stagger: 0.04 }}, {r2(b + 0.05)});',
                bounce(".t3-b-fan > g", b + 1.2, 5, 0.03),
                slam("#t3-b-title", loc("tag3", w("t3", 4)) - 0.05), shake("#t3-b-cam", loc("tag3", w("t3", 4)) + 0.1),
                push("#t3-c-cam", c, cd), popc("#t3-c-chip", loc("tag3", w("t3", 11)) - 0.1),
                push("#t3-d-cam", d, dd, 1.0, 1.1),
                f'    tl.fromTo("#t3-d-pot", {{ y: 0 }}, {{ y: -6, duration: 0.6, repeat: 3, yoyo: true, ease: "sine.inOut" }}, {r2(d)});',
                f'    tl.fromTo(".t3-d-zz", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.3, stagger: 0.3 }}, {r2(d + 0.2)});',
                slam("#t3-d-title", loc("tag3", w("t3", 17)) - 0.05)])
files["tag3"] = comp("tag3", body, js)

# ===================== TAG 5: Nationalschatz, Fahrrad, zu gefährlich =====================
(a, ad), (b, bd), (c, cd), (d, dd) = beats("tag5", [SC["tag5"][0], st("t5"), round(w("t5", 6) - 0.12, 2), round(w("t5", 13) - 0.12, 2)])
svgB = f'''          <defs><radialGradient id="t5-b-spot" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#f7c548" stop-opacity="0.5" /><stop offset="1" stop-color="#f7c548" stop-opacity="0" /></radialGradient></defs>
          <rect width="1080" height="1920" fill="#2a1f2a" />
          <g fill="#3a2a3a">{"".join(f'<rect x="{x}" y="0" width="60" height="1920" />' for x in (60, 960))}</g>
          <circle cx="540" cy="1150" r="520" fill="url(#t5-b-spot)" />
          <rect x="300" y="1640" width="480" height="280" fill="#e9e2d0" /><rect x="280" y="1620" width="520" height="40" fill="#f4efe4" />
          <!--@person id="t5-b-me" x="540" y="1630" s="0.95" {ME}-->
          <rect x="300" y="760" width="480" height="880" fill="#bfe6f4" opacity="0.22" stroke="#e9f6ff" stroke-width="6" />
          <g transform="translate(540 1040)"><path d="M-90 0 l-20 -90 l60 50 l50 -80 l50 80 l60 -50 l-20 90 z" fill="#f7c548" /></g>
          <g stroke="#b5442e" stroke-width="14" fill="none"><path d="M60 1700 q120 60 220 0" /><path d="M800 1700 q120 60 220 0" /></g>
          <g fill="#f7c548"><circle cx="60" cy="1700" r="18" /><circle cx="280" cy="1700" r="18" /><circle cx="800" cy="1700" r="18" /><circle cx="1020" cy="1700" r="18" /></g>
          <!--@potato id="t5-b-guard" x="160" y="1900" s="0.8" mood="cool" acc="police"-->
          <!--@potato id="t5-b-pres" x="900" y="1900" s="0.8" mood="love" acc="tie" accent="#e8412f"-->'''
svgC = f'''          <rect width="1080" height="1920" fill="#1b232f" />
          <rect y="1500" width="1080" height="420" fill="#2c3340" />
          <g transform="translate(540 1200)" fill="none" stroke="#f4efe4" stroke-width="18" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="-220" cy="100" r="150" /><circle cx="220" cy="100" r="150" />
            <path d="M-220 100 L-60 -100 L160 -100 L220 100 M-60 -100 L0 100 L160 -100 M0 100 L-220 100 M-80 -150 h60 M160 -100 l-20 -70 h70" /></g>
          <g fill="none" stroke="#e8412f" stroke-width="44" stroke-linecap="round"><path id="t5-c-x1" d="M220 820 L860 1480" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" /><path id="t5-c-x2" d="M860 820 L220 1480" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" /></g>'''
svgD = f'''          <rect width="1080" height="1920" fill="#202836" />
          <rect y="1620" width="1080" height="300" fill="#2c3340" />
          <!--@person id="t5-d-me" x="540" y="1680" s="1.0" jacket="#e8412f" pants="#2a2f3b" hair="#2a1a10" skin="#f1c7a0" style="spiky" mood="worried"-->
          <g fill="#e9f6ff" opacity="0.35" stroke="#e9f6ff" stroke-width="4">{"".join(f'<circle cx="{x}" cy="{y}" r="26" />' for x in range(420, 671, 50) for y in range(1300, 1620, 50))}</g>
          <path d="M432 1006 q108 -110 216 0 z" fill="#f7c548" /><rect x="420" y="996" width="240" height="20" rx="8" fill="#e0a92a" />
          <!--@potato id="t5-d-g1" x="190" y="1720" s="0.95" mood="cool"-->
          <!--@potato id="t5-d-g2" x="890" y="1720" s="0.95" mood="cool" flip="1"-->'''
body = "\n".join([card("t5-a", a, ad, 5, "15 Uhr"),
                  beat("t5-b", b, bd, svgB, title("t5-b-title", '<span class="o">Nationalschatz</span>', top=400, size=120)),
                  beat("t5-c", c, cd, svgC, title("t5-c-title", '<span class="r">Verboten</span>', top=400, size=150)),
                  beat("t5-d", d, dd, svgD, title("t5-d-title", 'Zu<br /><span class="r">gefährlich</span>', top=390, size=120))])
xt = loc("tag5", w("t5", 11)) - 0.1
js = "\n".join([card_js("t5-a", a), push("#t5-b-cam", b, bd), slam("#t5-b-title", loc("tag5", w("t5", 5)) - 0.05),
                push("#t5-c-cam", c, cd),
                f'    tl.fromTo("#t5-c-x1", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.18, ease: "power2.in" }}, {r2(xt)});',
                f'    tl.fromTo("#t5-c-x2", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.18, ease: "power2.in" }}, {r2(xt + 0.18)});',
                slam("#t5-c-title", xt + 0.2), shake("#t5-c-cam", xt + 0.36),
                push("#t5-d-cam", d, dd), slam("#t5-d-title", loc("tag5", w("t5", 14)) - 0.05),
                f'    tl.fromTo(["#t5-d-g1", "#t5-d-g2"], {{ x: 0 }}, {{ x: 10, duration: 0.3, repeat: 5, yoyo: true }}, {r2(d)});'])
files["tag5"] = comp("tag5", body, js)

# ===================== TAG 7: Pickel, Panik =====================
(a, ad), (b, bd), (c, cd) = beats("tag7", [SC["tag7"][0], st("t7"), round(w("t7", 11) - 0.12, 2)])
pk = loc("tag7", w("t7", 6))
svgB = f'''          <rect width="1080" height="1920" fill="#1a2430" />
          <ellipse cx="540" cy="980" rx="470" ry="640" fill="#c7ccd6" /><ellipse cx="540" cy="980" rx="440" ry="610" fill="#9fc4d8" />
          <ellipse cx="420" cy="620" rx="80" ry="200" fill="#e9f6ff" opacity="0.25" transform="rotate(-20 420 620)" />
          <!--@person id="t7-b-me" x="540" y="2190" s="2.4" jacket="#e8412f" pants="#2a2f3b" hair="#2a1a10" skin="#f1c7a0" style="spiky" mood="neutral"-->
          <!--@person id="t7-b-me2" x="540" y="2190" s="2.4" jacket="#e8412f" pants="#2a2f3b" hair="#2a1a10" skin="#f1c7a0" style="spiky" mood="shocked"-->
          {rings("t7-b-rg", 540, 1004, 3, 60, 50)}
          <g transform="translate(540 1004)"><g id="t7-b-pk"><circle r="26" fill="#e8412f" /><circle cx="-8" cy="-8" r="8" fill="#ffb0a0" /></g></g>'''
pan = "".join(f'<g class="t7-c-run"><!--@potato id="t7-c-p{i}" x="{x}" y="{y}" s="{sc}" mood="shocked" arms="up" flip="{fl}"--></g>' for i, (x, y, sc, fl) in enumerate([(130, 1860, 0.7, 0), (380, 1800, 0.6, 1), (720, 1840, 0.65, 0), (960, 1800, 0.6, 1)]))
svgC = f'''          <rect width="1080" height="1920" fill="#2a1414" />
          <rect x="120" y="560" width="840" height="560" rx="20" fill="#14161c" /><rect x="150" y="590" width="780" height="500" fill="#3a2020" />
          {head("t7-c-me", 540, 1290, 0.8)}
          <g transform="translate(540 894)"><circle r="13" fill="#e8412f" /></g>
          <rect x="150" y="960" width="780" height="130" fill="#e8412f" />
          <text x="540" y="1046" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="74" fill="#fff">EILMELDUNG: PICKEL</text>
          <rect y="1440" width="1080" height="480" fill="#3a2020" />
          {pan}'''
body = "\n".join([card("t7-a", a, ad, 7, "7 Uhr"),
                  beat("t7-b", b, bd, svgB, chip("t7-b-chip", "Pickel!", top=400, cls="r", size=90)),
                  beat("t7-c", c, cd, svgC, title("t7-c-title", '<span class="r">Panik</span>', top=390, size=170))])
js = "\n".join([card_js("t7-a", a), push("#t7-b-cam", b, bd, 1.0, 1.1),
                f'    tl.fromTo("#t7-b-me2", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.1 }}, {r2(pk + 0.1)});',
                f'    tl.fromTo("#t7-b-pk", {{ scale: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, duration: 0.18, ease: "back.out(3)" }}, {r2(pk - 0.06)});',
                f'    tl.fromTo(".t7-b-rg-c", {{ scale: 0.4, opacity: 0, transformOrigin: "50% 50%" }}, {{ scale: 1.4, opacity: 0.9, duration: 0.6, repeat: 3, stagger: 0.15, ease: "none" }}, {r2(pk)});',
                popc("#t7-b-chip", pk + 0.02), shake("#t7-b-cam", pk + 0.1),
                f'    tl.fromTo("#t7-c-cam", {{ scale: 1.1 }}, {{ scale: 1.0, duration: {r2(cd)}, ease: "power1.out" }}, {r2(c)});',
                f'    tl.fromTo(".t7-c-run", {{ x: -40 }}, {{ x: 40, duration: 0.2, repeat: 9, yoyo: true, stagger: 0.05 }}, {r2(c)});',
                bounce(".t7-c-run", c, 9, 0.05),
                slam("#t7-c-title", loc("tag7", w("t7", 16)) - 0.05), shake("#t7-c-cam", loc("tag7", w("t7", 16)) + 0.1)])
files["tag7"] = comp("tag7", body, js)

# ===================== FRAGE =====================
s0, d = SC["frage"]
svg = f'''          <rect width="1080" height="1920" fill="#1a1f2b" />
          <circle cx="540" cy="1250" r="440" fill="#f7c548" opacity="0.1" />
          <rect y="1720" width="1080" height="200" fill="#232a3a" />
          <!--@person id="q-me" x="540" y="1760" s="1.0" {ME}-->
          {sparkles("q-sp", [(320, 1100, 1.0), (760, 1040, 1.2)])}'''
extra = "\n".join([title("q-title", 'Wärst du gern<br /><span class="r">schön?</span>', top=210, size=130),
                   '      <div id="q-yes" class="q-choice" style="left: 40px"><span class="chip o">Ja</span></div>',
                   '      <div id="q-no" class="q-choice" style="left: 740px"><span class="chip r">Nein</span></div>',
                   chip("q-com", "In die Kommentare →", top=640, cls="o", size=56)])
css = '    .q-choice { position: absolute; top: 980px; width: 300px; text-align: center; }\n    .q-choice .chip { font-size: 92px; padding: 6px 44px 10px; }'
com = loc("frage", L["cta1"]["start"])
js = "\n".join([push("#q-a-cam", 0, d, 1.0, 1.06),
                f'    tl.fromTo("#q-title", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.2, ease: "power3.out" }}, 0.04);',
                popc("#q-yes", loc("frage", w("frage", 4))), popc("#q-no", loc("frage", w("frage", 5))),
                f'    tl.fromTo("#q-com", {{ opacity: 0, x: -80 }}, {{ opacity: 1, x: 0, duration: 0.25, ease: "power3.out" }}, {r2(com)});',
                f'    tl.to("#q-com", {{ x: 18, duration: 0.2, repeat: 3, yoyo: true, ease: "sine.inOut" }}, {r2(com + 0.3)});',
                f'    tl.fromTo(".q-sp", {{ scale: 0.4, transformOrigin: "50% 50%" }}, {{ scale: 1.2, duration: 0.35, repeat: 7, yoyo: true, stagger: 0.15 }}, 0);'])
files["frage"] = comp("frage", beat("q-a", 0, d, svg, extra), js, css)

# ===================== OUTRO =====================
s0, d = SC["outro"]
css = '''    #root { background: radial-gradient(ellipse 70% 55% at 50% 48%, #6a6d74 0%, #3a3c42 60%, #232428 100%); }
    #o-share { position: absolute; top: 700px; left: 0; width: 1080px; text-align: center;
      font-family: "Oswald", sans-serif; font-weight: 700; font-size: 70px; letter-spacing: 0.08em; color: var(--ink); text-transform: uppercase;
      text-shadow: 0 5px 0 rgba(0,0,0,.45); }
    #o-share .o { color: var(--orange); }
    #o-series { position: absolute; top: 1580px; left: 0; width: 1080px; text-align: center;
      font-family: "Oswald", sans-serif; font-weight: 700; font-size: 50px; letter-spacing: 0.2em; color: var(--ink); text-transform: uppercase; }
    #o-series .o { color: var(--orange); letter-spacing: 0; }'''
body = f'''    <svg class="full" viewBox="0 0 1080 1920">
      <g transform="translate(540 1000)"><g id="o-gear"><circle r="360" fill="#4b4e55" /><circle r="320" fill="#5b5f67" />
        <path d="M0 -200 L46 -64 L190 -62 L74 24 L118 162 L0 78 L-118 162 L-74 24 L-190 -62 L-46 -64 Z" fill="#f7c548" />
        <g fill="#9aa0a8"><circle cx="0" cy="-340" r="9" /><circle cx="0" cy="340" r="9" /><circle cx="-340" cy="0" r="9" /><circle cx="340" cy="0" r="9" /></g></g></g>
      <path id="o-arrow" d="M880 1010 q60 40 20 110 l-10 -36 m10 36 l-36 -6" fill="none" stroke="#f4a62a" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <div id="o-part" class="title" style="top: 190px; font-size: 140px"><span class="o">Teil 1</span></div>
    <div id="o-q" class="title" style="top: 360px; font-size: 118px"><span class="r" style="color: #ff5a45">Wärst du<br />gern schön?</span></div>
    <div id="o-share">Teilen <span class="o">→ Teil 2</span> ↗</div>
    <div id="o-follow" class="chip-row" style="top: 1050px"><span class="chip o" style="font-size: 64px; border-radius: 40px; padding: 6px 40px 10px">Folge für Teil 2</span></div>
    <div id="o-series"><span class="o">✦</span> Der letzte schöne Mensch</div>'''
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

# ---- hud.json ----
pk_g = w("t7", 6)
hud = {"start": SC["tag1"][0], "end": SC["frage"][0], "label": "EGO", "pill": "✦ SCHÖN",
       "days": [{"t": SC["tag1"][0], "day": 1, "clock": "07:00", "pct": 92},
                {"t": st("t1b"), "day": 1, "clock": "08:30", "pct": 100},
                {"t": SC["tag2"][0], "day": 2, "clock": "09:14", "pct": 100},
                {"t": SC["tag3"][0], "day": 3, "clock": "11:02", "pct": 100},
                {"t": SC["tag5"][0], "day": 5, "clock": "15:40", "pct": 100},
                {"t": SC["tag7"][0], "day": 7, "clock": "07:31", "pct": 100},
                {"t": round(pk_g, 2), "day": 7, "clock": "07:32", "pct": 3}],
       "alert": {"t": round(pk_g, 2)}}
json.dump(hud, open(os.path.join(P, "hud.json"), "w"), indent=1)

# ---- scenes.json ----
g = lambda n: SC[n][0]
sfx = [["sfx-ring", "pop", w("hook1", 9), 0.5], ["sfx-w0", "whoosh", g("fact") - 0.0, 0.3],
       ["sfx-w1", "whoosh-short", st("hook2"), 0.25], ["sfx-kart", "impact-bass-1", w("hook2", 8), 0.3],
       ["sfx-01", "impact-bass-2", w("fact", 5), 0.22], ["sfx-cup", "pop", L["fact2"]["start"], 0.8],
       ["sfx-w2", "whoosh", g("tag1"), 0.3], ["sfx-w3", "whoosh-short", st("t1"), 0.24], ["sfx-gr", "pop", w("t1", 6), 0.8],
       ["sfx-w4", "whoosh-short", w("t1", 7) - 0.12, 0.24], ["sfx-neben", "impact-bass-1", w("t1", 13), 0.22],
       ["sfx-w5", "whoosh", st("t1b"), 0.26], ["sfx-hallo", "pop", w("t1b", 10), 0.8],
       ["sfx-w6", "whoosh", g("tag2"), 0.3], ["sfx-likes", "riser", w("t2", 3), 0.12], ["sfx-mio", "impact-bass-2", w("t2", 3) + 0.05, 0.2],
       ["sfx-w7", "whoosh-short", w("t2", 6) - 0.12, 0.24], ["sfx-w8", "whoosh-short", w("t2", 12) - 0.12, 0.24], ["sfx-zahn", "error", w("t2", 19), 0.35],
       ["sfx-w9", "whoosh", g("tag3"), 0.3], ["sfx-fans", "impact-bass-1", w("t3", 4), 0.25], ["sfx-w10", "whoosh-short", w("t3", 6) - 0.12, 0.24],
       ["sfx-w11", "whoosh-short", w("t3", 13) - 0.12, 0.24], ["sfx-bk", "pop", w("t3", 17), 0.8],
       ["sfx-w12", "whoosh", g("tag5"), 0.3], ["sfx-schatz", "impact-bass-2", w("t5", 5), 0.22],
       ["sfx-w13", "whoosh-short", w("t5", 6) - 0.12, 0.24], ["sfx-x", "error", w("t5", 11), 0.4], ["sfx-w14", "whoosh-short", w("t5", 13) - 0.12, 0.24],
       ["sfx-w15", "whoosh", g("tag7"), 0.3], ["sfx-pickel", "error", w("t7", 6), 0.45], ["sfx-pk2", "impact-bass-1", w("t7", 6), 0.3],
       ["sfx-gl", "glitch-3", w("t7", 6) + 0.05, 0.2], ["sfx-w16", "whoosh-short", w("t7", 11) - 0.12, 0.26], ["sfx-panik", "impact-bass-1", w("t7", 16), 0.28],
       ["sfx-w17", "whoosh", g("frage"), 0.3], ["sfx-ja", "pop", w("frage", 4), 0.7], ["sfx-nein", "pop", w("frage", 5), 0.7],
       ["sfx-w18", "whoosh-cinematic", g("outro"), 0.22]]
sfx = [[a_, b_, round(t, 2), v] for a_, b_, t, v in sfx]
json.dump({"total": TOTAL, "hud": [SC["tag1"][0], round(SC["frage"][0] - SC["tag1"][0], 2)],
           "scenes": [[n, SC[n][0], SC[n][1]] for n, _ in order], "sfx": sfx}, open(os.path.join(P, "scenes.json"), "w"), indent=1)
print("Szenen:", ", ".join(f"{n} {SC[n][0]}+{SC[n][1]}" for n, _ in order), "| Länge", TOTAL)
