#!/usr/bin/env python3
"""Wiederverwendbare Flat-Vector-Bausteine im Referenz-Look (Cartoon, dunkle Szenen).

In einer Szenendatei einen Platzhalter schreiben, z. B.
  <!--@person id="t1-p1" x="300" y="1500" s="1" jacket="#2f6f8f" hair="#5a3a22" style="spiky" mood="worried"-->
  <!--@shelf id="f-shelf" x="140" y="560" w="800" h="900" fill="1"-->
  <!--@skyline id="t5-city" y="1150" lit="1" seed="3"-->
und dann ausführen:  python3 -I svg_parts.py PROJEKT_DIR
Der Platzhalter bleibt stehen, das erzeugte SVG landet direkt dahinter bis <!--/@-->.
Erneutes Ausführen ersetzt den Block (idempotent). Alle Teile sind deterministisch (seed).
"""
import glob, os, random, re, sys

SKIN = ["#f1c7a0", "#e0ac7e", "#c98d62", "#8d5a3b"]


def _f(v, d):
    return float(v) if v is not None else d


def person(id, x=540, y=1500, s=1.0, jacket="#2f6f8f", pants="#2a2f3b", hair="#5a3a22", skin="#f1c7a0",
           style="short", mood="neutral", flip="0", hat="", vest="", **_):
    """Figur, Füße auf (x, y). Höhe ≈ 640*s. mood: neutral|worried|shocked|sad. style: short|spiky|long|bald."""
    x, y, s = _f(x, 540), _f(y, 1500), _f(s, 1.0)
    sx = -1 if str(flip) == "1" else 1
    dark = "#0f1218"
    brows = {
        "neutral": "M-50 -556 l30 -4 M20 -560 l30 4",
        "worried": "M-52 -548 l32 -12 M20 -560 l32 12",
        "shocked": "M-50 -566 l30 -8 M20 -574 l30 8",
        "sad": "M-52 -552 l32 -10 M20 -562 l32 10",
    }[mood]
    mouth = {
        "neutral": '<path d="M-16 -468 q16 8 32 0" fill="none" stroke="#5a2a1e" stroke-width="7" stroke-linecap="round"/>',
        "worried": '<path d="M-18 -462 q18 -12 36 0" fill="none" stroke="#5a2a1e" stroke-width="7" stroke-linecap="round"/>',
        "shocked": '<ellipse cx="0" cy="-466" rx="14" ry="20" fill="#5a2a1e"/>',
        "sad": '<path d="M-20 -458 q20 -16 40 0" fill="none" stroke="#5a2a1e" stroke-width="7" stroke-linecap="round"/>',
    }[mood]
    hair_svg = {
        "short": f'<path d="M-104 -520 q-6 -110 104 -118 q110 8 104 118 q-30 -56 -104 -60 q-74 4 -104 60 z" fill="{hair}"/>',
        "spiky": f'<path d="M-104 -516 l-10 -70 l40 26 l10 -70 l40 50 l24 -76 l26 76 l40 -52 l8 72 l42 -26 l-12 70 q-40 -50 -104 -54 q-64 4 -104 54 z" fill="{hair}"/>',
        "long": f'<path d="M-112 -400 q-30 -250 112 -248 q142 -2 112 248 l-40 0 q10 -110 -10 -150 q-60 -30 -124 -24 q-30 40 -20 174 z" fill="{hair}"/>',
        "bald": f'<path d="M-100 -560 q100 -50 200 0" fill="none" stroke="{hair}" stroke-width="10" opacity="0.5"/>',
    }[style]
    hat_svg = ""
    if hat:
        hat_svg = (f'<path d="M-112 -566 q0 -110 112 -112 q112 2 112 112 z" fill="{hat}" stroke="{dark}" stroke-opacity=".35" stroke-width="6"/>'
                   f'<rect x="-132" y="-574" width="264" height="22" rx="11" fill="{hat}"/>'
                   f'<rect x="-10" y="-676" width="20" height="104" rx="8" fill="#000" opacity=".15"/>')
    vest_svg = ""
    if vest:
        vest_svg = (f'<path d="M-96 -392 h52 l44 210 l44 -210 h52 v210 h-192 z" fill="{vest}" opacity=".95"/>'
                    '<rect x="-104" y="-300" width="208" height="16" fill="#e9e6da" opacity=".9"/>'
                    '<rect x="-104" y="-250" width="208" height="16" fill="#e9e6da" opacity=".9"/>')
    return f'''<g id="{id}" transform="translate({x} {y}) scale({s * sx} {s})">
  <ellipse cx="0" cy="0" rx="120" ry="18" fill="#000" opacity=".3"/>
  <rect x="-70" y="-200" width="58" height="196" rx="20" fill="{pants}"/>
  <rect x="12" y="-200" width="58" height="196" rx="20" fill="{pants}"/>
  <ellipse cx="-44" cy="-6" rx="46" ry="20" fill="#d9d4c7"/><ellipse cx="44" cy="-6" rx="46" ry="20" fill="#d9d4c7"/>
  <g id="{id}-armL"><rect x="-150" y="-392" width="52" height="200" rx="26" fill="{jacket}" transform="rotate(8 -124 -392)"/>
    <circle cx="-138" cy="-186" r="26" fill="{skin}"/></g>
  <g id="{id}-armR"><rect x="98" y="-392" width="52" height="200" rx="26" fill="{jacket}" transform="rotate(-8 124 -392)"/>
    <circle cx="138" cy="-186" r="26" fill="{skin}"/></g>
  <path d="M-110 -340 q0 -66 60 -66 h100 q60 0 60 66 v150 h-220 z" fill="{jacket}"/>
  <path d="M-30 -406 l30 60 l30 -60 z" fill="#e9e6da"/>
  {vest_svg}
  <rect x="-24" y="-436" width="48" height="40" fill="{skin}"/>
  <g id="{id}-head">
    {hair_svg if style == "long" else ""}
    <circle cx="0" cy="-520" r="102" fill="{skin}"/>
    <circle cx="-102" cy="-512" r="18" fill="{skin}"/><circle cx="102" cy="-512" r="18" fill="{skin}"/>
    {hair_svg if style != "long" else ""}
    <ellipse cx="-36" cy="-522" rx="17" ry="19" fill="#fff"/><ellipse cx="36" cy="-522" rx="17" ry="19" fill="#fff"/>
    <circle id="{id}-eyeL" cx="-34" cy="-520" r="9" fill="{dark}"/><circle id="{id}-eyeR" cx="34" cy="-520" r="9" fill="{dark}"/>
    <path d="{brows}" stroke="{hair if style != 'bald' else '#6b5a4a'}" stroke-width="9" stroke-linecap="round" fill="none"/>
    <circle cx="-62" cy="-482" r="14" fill="#e88a7a" opacity=".35"/><circle cx="62" cy="-482" r="14" fill="#e88a7a" opacity=".35"/>
    {mouth}
    {hat_svg}
  </g>
</g>'''


PRODUCT_COLORS = ["#e8412f", "#f4a62a", "#5f8f5c", "#3d7bb3", "#f4efe4", "#c96b9a", "#f7c548", "#6b4330"]


def shelf(id, x=140, y=560, w=800, h=900, fill="1", seed="1", **_):
    """Supermarktregal mit 4 Böden. fill=1 voll (Produkte haben Klasse {id}-item), fill=0 leer mit Preisschildern."""
    x, y, w, h = _f(x, 140), _f(y, 560), _f(w, 800), _f(h, 900)
    rnd = random.Random(int(seed))
    rows = 4
    rh = h / rows
    out = [f'<g id="{id}">',
           f'<rect x="{x - 24}" y="{y - 30}" width="{w + 48}" height="{h + 60}" rx="14" fill="#3a4150"/>',
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#242a36"/>']
    for r in range(rows):
        by = y + (r + 1) * rh
        if str(fill) == "1":
            cx = x + 14
            while cx < x + w - 60:
                kind = rnd.choice(["box", "can", "bottle", "box"])
                col = rnd.choice(PRODUCT_COLORS)
                if kind == "box":
                    pw, ph = rnd.randint(70, 100), rnd.randint(110, int(rh) - 40)
                    out.append(f'<g class="{id}-item"><rect x="{cx}" y="{by - 18 - ph}" width="{pw}" height="{ph}" rx="6" fill="{col}"/>'
                               f'<rect x="{cx + 10}" y="{by - 18 - ph * 0.7}" width="{pw - 20}" height="{ph * 0.25}" rx="4" fill="#fff" opacity=".55"/></g>')
                elif kind == "can":
                    pw, ph = 62, rnd.randint(80, 110)
                    out.append(f'<g class="{id}-item"><rect x="{cx}" y="{by - 18 - ph}" width="{pw}" height="{ph}" rx="10" fill="{col}"/>'
                               f'<rect x="{cx}" y="{by - 18 - ph * 0.6}" width="{pw}" height="{ph * 0.3}" fill="#f4efe4" opacity=".8"/></g>')
                else:
                    pw, ph = 50, rnd.randint(150, int(rh) - 30)
                    out.append(f'<g class="{id}-item"><path d="M{cx + 16} {by - 18 - ph} h18 v30 q16 14 16 40 v{ph - 70} q0 10 -10 10 h-30 q-10 0 -10 -10 v{-(ph - 70)} q0 -26 16 -40 z" fill="{col}"/>'
                               f'<rect x="{cx + 4}" y="{by - 18 - ph * 0.5}" width="42" height="{ph * 0.22}" fill="#fff" opacity=".6"/></g>')
                cx += pw + rnd.randint(8, 18)
        else:
            for k in range(3):
                tx = x + 60 + k * (w - 160) / 2
                out.append(f'<rect x="{tx}" y="{by - 14}" width="80" height="36" rx="4" fill="#f7c548"/>'
                           f'<rect x="{tx + 10}" y="{by - 2}" width="44" height="8" fill="#6b4a12"/>')
        out.append(f'<rect x="{x - 10}" y="{by - 18}" width="{w + 20}" height="26" rx="6" fill="#8d93a1"/>')
        out.append(f'<rect x="{x - 10}" y="{by + 2}" width="{w + 20}" height="8" fill="#000" opacity=".25"/>')
    out.append('</g>')
    return "\n".join(out)


def skyline(id, y=1150, lit="1", seed="3", color="#0d0b10", win="#f7c548", **_):
    """Häuserkette über die ganze Breite, Fenster mit Klasse {id}-win."""
    y = _f(y, 1150)
    rnd = random.Random(int(seed))
    out = [f'<g id="{id}">']
    bx = -20
    wins = []
    while bx < 1100:
        bw = rnd.randint(110, 190)
        bh = rnd.randint(260, 620)
        top = y + 600 - bh
        out.append(f'<rect x="{bx}" y="{top}" width="{bw}" height="{1920 - top}" fill="{color}"/>')
        for wy in range(int(top) + 40, int(y) + 560, 70):
            for wx in range(bx + 22, bx + bw - 30, 46):
                if rnd.random() < 0.55:
                    wins.append(f'<rect x="{wx}" y="{wy}" width="22" height="30" fill="{win}"/>')
        bx += bw + rnd.randint(-10, 6)
    out.append(f'<g class="{id}-win" opacity="{1 if str(lit) == "1" else 0}">' + "".join(wins) + '</g>')
    out.append('</g>')
    return "\n".join(out)


PARTS = {"person": person, "shelf": shelf, "skyline": skyline}
PAT = re.compile(r'(<!--@(\w+)((?:\s+[\w-]+="[^"]*")*)\s*-->)(\n<g .*?<!--/@-->)?', re.S)


def expand(text):
    def rep(m):
        name, attrs = m.group(2), dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(3)))
        return m.group(1) + "\n" + PARTS[name](**attrs) + "<!--/@-->"
    return PAT.sub(rep, text)


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "."
    for f in sorted(glob.glob(os.path.join(proj, "compositions", "*.html"))):
        src = open(f, encoding="utf-8").read()
        out = expand(src)
        if out != src:
            open(f, "w", encoding="utf-8").write(out)
            print("erweitert:", f)
