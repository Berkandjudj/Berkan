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
           style="short", mood="neutral", flip="0", hat="", vest="", arms="down", beard="", **_):
    """Figur, Füße auf (x, y). Höhe ≈ 640*s. mood: neutral|worried|shocked|sad|happy.
    style: short|spiky|long|bald|curly. arms: down|up (jubeln). beard: ""|mustache|full."""
    x, y, s = _f(x, 540), _f(y, 1500), _f(s, 1.0)
    sx = -1 if str(flip) == "1" else 1
    dark = "#0f1218"
    brows = {
        "neutral": "M-50 -556 l30 -4 M20 -560 l30 4",
        "worried": "M-52 -548 l32 -12 M20 -560 l32 12",
        "shocked": "M-50 -566 l30 -8 M20 -574 l30 8",
        "sad": "M-52 -552 l32 -10 M20 -562 l32 10",
        "happy": "M-52 -566 q16 -14 32 -4 M20 -570 q16 -10 32 4",
    }[mood]
    mouth = {
        "neutral": '<path d="M-16 -468 q16 8 32 0" fill="none" stroke="#5a2a1e" stroke-width="7" stroke-linecap="round"/>',
        "worried": '<path d="M-18 -462 q18 -12 36 0" fill="none" stroke="#5a2a1e" stroke-width="7" stroke-linecap="round"/>',
        "shocked": '<ellipse cx="0" cy="-466" rx="14" ry="20" fill="#5a2a1e"/>',
        "sad": '<path d="M-20 -458 q20 -16 40 0" fill="none" stroke="#5a2a1e" stroke-width="7" stroke-linecap="round"/>',
        "happy": '<path d="M-34 -478 q34 44 68 0 z" fill="#5a2a1e"/><path d="M-22 -466 q22 16 44 0" fill="#e88a7a"/>',
    }[mood]
    hair_svg = {
        "short": f'<path d="M-104 -520 q-6 -110 104 -118 q110 8 104 118 q-30 -56 -104 -60 q-74 4 -104 60 z" fill="{hair}"/>',
        "spiky": f'<path d="M-104 -516 l-10 -70 l40 26 l10 -70 l40 50 l24 -76 l26 76 l40 -52 l8 72 l42 -26 l-12 70 q-40 -50 -104 -54 q-64 4 -104 54 z" fill="{hair}"/>',
        "long": f'<path d="M-112 -400 q-30 -250 112 -248 q142 -2 112 248 l-40 0 q10 -110 -10 -150 q-60 -30 -124 -24 q-30 40 -20 174 z" fill="{hair}"/>',
        "bald": f'<path d="M-100 -560 q100 -50 200 0" fill="none" stroke="{hair}" stroke-width="10" opacity="0.5"/>',
        "curly": f'<g fill="{hair}"><path d="M-106 -514 q-8 -118 106 -124 q114 6 106 124 q-30 -50 -106 -56 q-76 6 -106 56 z"/>'
                 + "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>' for cx, cy, r in
                           [(-92, -574, 30), (-60, -612, 32), (-18, -630, 32), (26, -630, 32), (66, -610, 32), (96, -572, 30), (-104, -532, 22), (106, -532, 22)])
                 + '</g>',
    }[style]
    beard_svg = ""
    if beard == "mustache":
        beard_svg = f'<path d="M-46 -486 q22 -20 46 -8 q24 -12 46 8 q-10 18 -46 10 q-36 8 -46 -10 z" fill="{hair}"/>'
    elif beard == "full":
        beard_svg = (f'<path d="M-100 -520 q0 120 100 122 q100 -2 100 -122 q-20 60 -40 66 q-60 -26 -120 0 q-20 -6 -40 -66 z" fill="{hair}"/>'
                     f'<path d="M-46 -486 q22 -20 46 -8 q24 -12 46 8 q-10 18 -46 10 q-36 8 -46 -10 z" fill="{hair}"/>')
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
    aL, aR = (150, -150) if arms == "up" else (0, 0)
    # Äußere Gruppe ohne transform-Attribut: GSAP darf sie bewegen, ohne die Position zu überschreiben.
    return f'''<g id="{id}"><g transform="translate({x} {y}) scale({s * sx} {s})">
  <ellipse cx="0" cy="0" rx="120" ry="18" fill="#000" opacity=".3"/>
  <rect x="-70" y="-200" width="58" height="196" rx="20" fill="{pants}"/>
  <rect x="12" y="-200" width="58" height="196" rx="20" fill="{pants}"/>
  <ellipse cx="-44" cy="-6" rx="46" ry="20" fill="#d9d4c7"/><ellipse cx="44" cy="-6" rx="46" ry="20" fill="#d9d4c7"/>
  <g id="{id}-armL" transform="rotate({aL} -124 -380)"><rect x="-150" y="-392" width="52" height="200" rx="26" fill="{jacket}" transform="rotate(8 -124 -392)"/>
    <circle cx="-138" cy="-186" r="26" fill="{skin}"/></g>
  <g id="{id}-armR" transform="rotate({aR} 124 -380)"><rect x="98" y="-392" width="52" height="200" rx="26" fill="{jacket}" transform="rotate(-8 124 -392)"/>
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
    {beard_svg}
    {hat_svg}
  </g>
</g></g>'''


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


def embers(id, n="40", seed="1", x0="0", x1="1080", y0="600", y1="1900", color="#ff9a3c", r="5", **_):
    """Glutfunken (Klasse {id}-p) – im Script z. B. nach oben treiben lassen."""
    rnd = random.Random(int(seed))
    out = [f'<g id="{id}">']
    for _ in range(int(n)):
        x, y = rnd.uniform(float(x0), float(x1)), rnd.uniform(float(y0), float(y1))
        rr = rnd.uniform(0.4, 1.0) * float(r)
        out.append(f'<circle class="{id}-p" cx="{x:.0f}" cy="{y:.0f}" r="{rr:.1f}" fill="{color}" opacity="{rnd.uniform(0.35, 0.95):.2f}"/>')
    out.append('</g>')
    return "\n".join(out)


def fog(id, y="1300", color="#9fe0d4", opacity="0.12", seed="2", **_):
    """Weiche Nebelschwaden (braucht im SVG einen Blur-Filter id="{id}-blur", wird mitgeliefert)."""
    rnd = random.Random(int(seed))
    out = [f'<g id="{id}"><defs><filter id="{id}-blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter></defs>',
           f'<g filter="url(#{id}-blur)" opacity="{opacity}" fill="{color}">']
    for k in range(5):
        out.append(f'<ellipse cx="{rnd.uniform(0, 1080):.0f}" cy="{float(y) + rnd.uniform(-120, 120):.0f}" rx="{rnd.uniform(260, 460):.0f}" ry="{rnd.uniform(50, 110):.0f}"/>')
    out.append('</g></g>')
    return "\n".join(out)


def player(id, x=540, y=1600, s=1.0, shirt="#d8262e", sleeve="", shorts="#f4f1ea", socks="#d8262e", number="7",
           numcol="#f4f1ea", skin="#c98d62", hair="#1a1210", pose="stand", rim="#ffb35c", flip="0", boots="#f4f1ea", **_):
    """Fußballer in Rückansicht (Hinterkopf, Nummer sichtbar), Füße auf (x, y), Höhe ≈ 800*s.
    pose: stand | siu (Sprung, Arme nach unten-außen) | run | arms (Arme hoch). rim = Gegenlicht-Kante."""
    x, y, s = _f(x, 540), _f(y, 1600), _f(s, 1.0)
    sx = -1 if str(flip) == "1" else 1
    sleeve = sleeve or shirt
    legs = {
        "stand": ("M-52 -330 l-14 280", "M52 -330 l14 280"),
        "siu": ("M-52 -330 l-56 270", "M52 -330 l56 270"),
        "run": ("M-46 -330 l-80 200 l-50 70", "M46 -330 l50 150 l100 80"),
        "arms": ("M-52 -330 l-14 280", "M52 -330 l14 280"),
    }[pose]
    feet = {"stand": ((-66, -40), (66, -40)), "siu": ((-108, -50), (108, -50)),
            "run": ((-176, -50), (196, -90)), "arms": ((-66, -40), (66, -40))}[pose]
    arms = {
        "stand": ("M-128 -630 q-36 110 -30 230", "M128 -630 q36 110 30 230"),
        "siu": ("M-128 -630 q-100 100 -160 200", "M128 -630 q100 100 160 200"),
        "run": ("M-128 -630 q-80 70 -110 170", "M128 -630 q90 -30 120 -150"),
        "arms": ("M-128 -630 q-80 -120 -110 -250", "M128 -630 q80 -120 110 -250"),
    }[pose]
    hand = {"stand": ((-158, -398), (158, -398)), "siu": ((-288, -428), (288, -428)),
            "run": ((-238, -458), (248, -778)), "arms": ((-238, -880), (238, -880))}[pose]
    return f'''<g id="{id}"><g transform="translate({x} {y}) scale({s * sx} {s})">
  <ellipse cx="0" cy="0" rx="190" ry="28" fill="#000" opacity=".5"/>
  <g stroke-linecap="round" fill="none">
    <path d="{legs[0]}" stroke="{skin}" stroke-width="76"/><path d="{legs[1]}" stroke="{skin}" stroke-width="76"/>
    <path d="{legs[0]}" stroke="{socks}" stroke-width="80" stroke-dasharray="0 150 400"/>
    <path d="{legs[1]}" stroke="{socks}" stroke-width="80" stroke-dasharray="0 150 400"/>
    <path d="{arms[0]}" stroke="{skin}" stroke-width="56"/><path d="{arms[1]}" stroke="{skin}" stroke-width="56"/>
    <path d="{arms[0]}" stroke="{sleeve}" stroke-width="68" stroke-dasharray="85 600"/>
    <path d="{arms[1]}" stroke="{sleeve}" stroke-width="68" stroke-dasharray="85 600"/>
  </g>
  <ellipse cx="{feet[0][0]}" cy="{feet[0][1]}" rx="52" ry="26" fill="{boots}"/><ellipse cx="{feet[1][0]}" cy="{feet[1][1]}" rx="52" ry="26" fill="{boots}"/>
  <circle cx="{hand[0][0]}" cy="{hand[0][1]}" r="30" fill="{skin}"/><circle cx="{hand[1][0]}" cy="{hand[1][1]}" r="30" fill="{skin}"/>
  <path d="M-118 -470 h236 l18 150 q-60 16 -114 0 l-4 -40 l-4 40 q-54 16 -114 0 z" fill="{shorts}"/>
  <path d="M-150 -652 q150 -50 300 0 l-26 196 q-124 22 -248 0 z" fill="{shirt}"/>
  <path d="M-150 -652 q60 -24 90 -28 l-12 222 q-30 -2 -52 -6 z" fill="#000" opacity=".12"/>
  <text data-layout-ignore="true" x="4" y="-512" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="130" fill="#000" opacity=".25">{number}</text>
  <text x="0" y="-518" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="130" fill="{numcol}">{number}</text>
  <path d="M-40 -690 h80 v44 q-40 14 -80 0 z" fill="{skin}"/>
  <ellipse cx="-74" cy="-756" rx="14" ry="24" fill="{skin}"/><ellipse cx="74" cy="-756" rx="14" ry="24" fill="{skin}"/>
  <ellipse cx="0" cy="-770" rx="72" ry="84" fill="{hair}"/>
  <path d="M-72 -760 q0 -96 72 -100 q74 4 74 100 q-20 -54 -74 -60 q-54 6 -72 60 z" fill="#000" opacity=".35"/>
  <path d="M-40 -700 q40 14 80 0" stroke="{hair}" stroke-width="10" fill="none"/>
  <g fill="none" stroke="{rim}" stroke-width="6" stroke-linecap="round" opacity=".55">
    <path d="M60 -836 q22 40 10 100"/><path d="M150 -652 l-26 196"/><path d="M118 -470 l18 150"/>
    <path d="{arms[1]}"/><path d="{legs[1]}"/>
  </g>
</g></g>'''


def man(id, x=540, y=1600, s=1.0, shirt="#e9e2d0", pants="#2a2f3b", shoes="#1a1412", skin="#c98d62", hair="#1a1210",
        pose="stand", rim="#ffb35c", flip="0", phone="#2a2a2a", **_):
    """Erwachsener Mann in Rückansicht (lockiges Haar, Hemd, lange Hose), Füße auf (x, y), Höhe ≈ 820*s.
    pose: stand | phone (rechte Hand am Ohr mit Telefon) | arms (Arme hoch) | walk. rim = Gegenlicht-Kante."""
    x, y, s = _f(x, 540), _f(y, 1600), _f(s, 1.0)
    sx = -1 if str(flip) == "1" else 1
    legs = {"stand": ("M-48 -380 l-10 340", "M48 -380 l10 340"), "phone": ("M-48 -380 l-10 340", "M48 -380 l10 340"),
            "arms": ("M-48 -380 l-10 340", "M48 -380 l10 340"), "walk": ("M-44 -380 l-60 330", "M44 -380 l40 330")}[pose]
    feet = {"stand": ((-60, -30), (60, -30)), "phone": ((-60, -30), (60, -30)), "arms": ((-60, -30), (60, -30)),
            "walk": ((-108, -40), (86, -40))}[pose]
    arms = {"stand": ("M-140 -660 q-30 120 -26 250", "M140 -660 q30 120 26 250"),
            "phone": ("M-140 -660 q-30 120 -26 250", "M140 -660 q60 70 -30 30"),
            "arms": ("M-140 -660 q-80 -110 -110 -250", "M140 -660 q80 -110 110 -250"),
            "walk": ("M-140 -660 q-50 110 -70 240", "M140 -660 q40 110 30 240")}[pose]
    hand = {"stand": ((-166, -404), (166, -404)), "phone": ((-166, -404), (110, -632)),
            "arms": ((-250, -914), (250, -914)), "walk": ((-210, -414), (170, -414))}[pose]
    ph = ""
    if pose == "phone":
        ph = (f'<rect x="88" y="-760" width="44" height="120" rx="8" fill="{phone}" transform="rotate(14 110 -700)"/>'
              f'<rect x="112" y="-800" width="8" height="50" fill="{phone}" transform="rotate(14 110 -700)"/>')
    curls = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{hair}"/>' for cx, cy, r in
                    [(-62, -820, 30), (-24, -846, 32), (22, -846, 32), (60, -820, 30), (-70, -778, 26), (70, -778, 26), (0, -812, 34)])
    return f'''<g id="{id}"><g transform="translate({x} {y}) scale({s * sx} {s})">
  <ellipse cx="0" cy="0" rx="170" ry="26" fill="#000" opacity=".5"/>
  <g stroke-linecap="round" fill="none">
    <path d="{legs[0]}" stroke="{pants}" stroke-width="84"/><path d="{legs[1]}" stroke="{pants}" stroke-width="84"/>
    <path d="{arms[0]}" stroke="{skin}" stroke-width="52"/><path d="{arms[1]}" stroke="{skin}" stroke-width="52"/>
    <path d="{arms[0]}" stroke="{shirt}" stroke-width="66" stroke-dasharray="110 600"/>
    <path d="{arms[1]}" stroke="{shirt}" stroke-width="66" stroke-dasharray="110 600"/>
  </g>
  <ellipse cx="{feet[0][0]}" cy="{feet[0][1]}" rx="54" ry="24" fill="{shoes}"/><ellipse cx="{feet[1][0]}" cy="{feet[1][1]}" rx="54" ry="24" fill="{shoes}"/>
  <circle cx="{hand[0][0]}" cy="{hand[0][1]}" r="28" fill="{skin}"/><circle cx="{hand[1][0]}" cy="{hand[1][1]}" r="28" fill="{skin}"/>
  {ph}
  <path d="M-150 -680 q150 -46 300 0 q10 120 -24 230 l-6 70 q-120 22 -240 0 l-6 -70 q-34 -110 -24 -230 z" fill="{shirt}"/>
  <path d="M-150 -680 q60 -24 90 -26 l-14 330 q-30 -2 -52 -6 l-6 -70 q-34 -110 -18 -228 z" fill="#000" opacity=".12"/>
  <path d="M-60 -660 q20 120 6 240 M64 -656 q-16 110 -4 230" stroke="#000" stroke-width="4" opacity=".1" fill="none"/>
  <rect x="-118" y="-392" width="236" height="16" rx="4" fill="#2a1e16"/>
  <path d="M-44 -720 h88 v46 q-44 14 -88 0 z" fill="{skin}"/>
  <ellipse cx="-76" cy="-776" rx="14" ry="24" fill="{skin}"/><ellipse cx="76" cy="-776" rx="14" ry="24" fill="{skin}"/>
  <ellipse cx="0" cy="-790" rx="76" ry="84" fill="{hair}"/>
  {curls}
  <path d="M-76 -780 q0 -96 76 -100 q78 4 78 100 q-20 -54 -78 -60 q-56 6 -76 60 z" fill="#000" opacity=".3"/>
  <g fill="none" stroke="{rim}" stroke-width="6" stroke-linecap="round" opacity=".55">
    <path d="M64 -858 q24 40 12 100"/><path d="M150 -680 l-6 300"/><path d="{legs[1]}"/><path d="{arms[1]}"/>
  </g>
</g></g>'''


def hippo(id, x=540, y=1500, s=1.0, color="#6d6f80", belly="#8d8a99", flip="0", **_):
    """Nilpferd in Seitenansicht, Füße auf (x, y), Länge ≈ 560*s, Kopf rechts (flip=1: links)."""
    x, y, s = _f(x, 540), _f(y, 1500), _f(s, 1.0)
    sx = -1 if str(flip) == "1" else 1
    return f'''<g id="{id}"><g transform="translate({x} {y}) scale({s * sx} {s})">
  <ellipse cx="0" cy="0" rx="260" ry="22" fill="#000" opacity=".35"/>
  <g fill="{color}">
    <rect x="-200" y="-110" width="70" height="110" rx="26"/><rect x="-90" y="-110" width="70" height="110" rx="26"/>
    <rect x="60" y="-110" width="70" height="110" rx="26"/><rect x="150" y="-110" width="66" height="110" rx="26"/>
    <ellipse cx="-10" cy="-200" rx="250" ry="140"/>
    <path d="M150 -300 q70 -40 130 -10 q50 26 50 90 q0 60 -60 70 q-60 6 -120 -30 z"/>
    <circle cx="190" cy="-316" r="22"/><circle cx="236" cy="-318" r="20"/>
  </g>
  <ellipse cx="-20" cy="-120" rx="200" ry="46" fill="{belly}" opacity=".5"/>
  <ellipse cx="300" cy="-224" rx="10" ry="7" fill="#2a2630"/><ellipse cx="272" cy="-232" rx="9" ry="6" fill="#2a2630"/>
  <circle cx="220" cy="-276" r="12" fill="#fff"/><circle cx="224" cy="-276" r="6" fill="#141218"/>
  <path d="M250 -168 q40 0 70 -30" stroke="#2a2630" stroke-width="6" fill="none" stroke-linecap="round"/>
  <circle cx="-240" cy="-200" r="10" fill="{color}"/>
</g></g>'''


def potato(id, x=540, y=1600, s=1.0, color="#c9955a", shade="#a8743e", mood="happy", acc="", arms="down", flip="0", accent="#3d7bb3", **_):
    """Kartoffel-Mensch (lustige Nebenfigur), Füße auf (x, y), Höhe ≈ 470*s.
    mood: happy|neutral|shocked|love|sleep|cool. acc: ""|chef|cap|tie|police|apron (accent = Farbe von Cap/Krawatte).
    arms: down|up|wave. Armgruppen: {id}-armL / {id}-armR (zum Winken/Klatschen animierbar)."""
    x, y, s = _f(x, 540), _f(y, 1600), _f(s, 1.0)
    sx = -1 if str(flip) == "1" else 1
    eyes = {
        "happy": '<ellipse cx="-42" cy="-300" rx="22" ry="26" fill="#fff"/><ellipse cx="42" cy="-300" rx="22" ry="26" fill="#fff"/><circle cx="-38" cy="-296" r="11" fill="#1a1210"/><circle cx="46" cy="-296" r="11" fill="#1a1210"/>',
        "neutral": '<ellipse cx="-42" cy="-300" rx="20" ry="22" fill="#fff"/><ellipse cx="42" cy="-300" rx="20" ry="22" fill="#fff"/><circle cx="-42" cy="-298" r="10" fill="#1a1210"/><circle cx="42" cy="-298" r="10" fill="#1a1210"/>',
        "shocked": '<circle cx="-44" cy="-304" r="30" fill="#fff"/><circle cx="44" cy="-304" r="30" fill="#fff"/><circle cx="-44" cy="-304" r="9" fill="#1a1210"/><circle cx="44" cy="-304" r="9" fill="#1a1210"/>',
        "love": '<path d="M-42 -284 l-26 -26 a14 14 0 0 1 26 -18 a14 14 0 0 1 26 18 z" fill="#e8412f"/><path d="M42 -284 l-26 -26 a14 14 0 0 1 26 -18 a14 14 0 0 1 26 18 z" fill="#e8412f"/>',
        "sleep": '<path d="M-64 -298 q22 16 44 0 M20 -298 q22 16 44 0" stroke="#1a1210" stroke-width="8" fill="none" stroke-linecap="round"/>',
        "cool": '<path d="M-84 -318 h168 v14 l-14 36 h-48 l-14 -30 h-8 l-14 30 h-48 l-14 -36 z" fill="#14161c"/>',
    }[mood]
    mouth = {
        "happy": '<path d="M-36 -236 q36 40 72 0 z" fill="#5a2a1e"/>',
        "neutral": '<path d="M-22 -232 q22 8 44 0" stroke="#5a2a1e" stroke-width="7" fill="none" stroke-linecap="round"/>',
        "shocked": '<ellipse cx="0" cy="-222" rx="22" ry="30" fill="#5a2a1e"/>',
        "love": '<path d="M-36 -236 q36 40 72 0 z" fill="#5a2a1e"/>',
        "sleep": '<ellipse cx="0" cy="-230" rx="12" ry="9" fill="#5a2a1e"/>',
        "cool": '<path d="M-26 -232 q26 14 52 -4" stroke="#5a2a1e" stroke-width="7" fill="none" stroke-linecap="round"/>',
    }[mood]
    arm = {"down": ("M-118 -190 q-40 50 -50 110", "M118 -190 q40 50 50 110"),
           "up": ("M-118 -200 q-60 -60 -70 -170", "M118 -200 q60 -60 70 -170"),
           "wave": ("M-118 -190 q-40 50 -50 110", "M118 -200 q60 -60 70 -170")}[arms]
    hand = {"down": ((-168, -80), (168, -80)), "up": ((-188, -370), (188, -370)), "wave": ((-168, -80), (188, -370))}[arms]
    acc_svg = {
        "": "",
        "chef": '<path d="M-70 -400 q-60 -10 -40 -70 q20 -50 70 -20 q20 -60 80 -20 q60 -10 50 60 q30 40 -30 50 z" fill="#f4f1ea"/><rect x="-72" y="-414" width="144" height="34" rx="8" fill="#e9e6da"/>',
        "cap": f'<path d="M-96 -372 q0 -78 96 -80 q96 2 96 80 z" fill="{accent}"/><path d="M40 -376 h110 q10 0 0 16 h-120 z" fill="{accent}"/>',
        "police": f'<path d="M-96 -372 q0 -70 96 -72 q96 2 96 72 z" fill="#1d3a6a"/><rect x="-104" y="-384" width="208" height="22" rx="6" fill="#14161c"/><circle cx="0" cy="-412" r="16" fill="#f7c548"/>',
        "tie": f'<path d="M-14 -190 h28 l-6 20 l16 110 l-24 26 l-24 -26 l16 -110 z" fill="{accent}"/>',
        "apron": '<path d="M-80 -170 h160 l14 150 q-94 22 -188 0 z" fill="#f4f1ea"/>',
    }[acc]
    return f'''<g id="{id}"><g transform="translate({x} {y}) scale({s * sx} {s})">
  <ellipse cx="0" cy="0" rx="130" ry="20" fill="#000" opacity=".3"/>
  <g stroke="#5a3a22" stroke-width="18" stroke-linecap="round"><path d="M-40 -60 v52"/><path d="M40 -60 v52"/></g>
  <ellipse cx="-48" cy="-8" rx="34" ry="16" fill="#3a2a1c"/><ellipse cx="48" cy="-8" rx="34" ry="16" fill="#3a2a1c"/>
  <g id="{id}-armL"><path d="{arm[0]}" stroke="{color}" stroke-width="22" fill="none" stroke-linecap="round"/><circle cx="{hand[0][0]}" cy="{hand[0][1]}" r="20" fill="{color}"/></g>
  <g id="{id}-armR"><path d="{arm[1]}" stroke="{color}" stroke-width="22" fill="none" stroke-linecap="round"/><circle cx="{hand[1][0]}" cy="{hand[1][1]}" r="20" fill="{color}"/></g>
  <path d="M6 -420 q112 -4 124 130 q12 120 -40 210 q-56 46 -150 18 q-80 -30 -70 -170 q4 -184 136 -188 z" fill="{color}"/>
  <path d="M-110 -250 q-8 140 70 168 q60 18 120 -2 q-104 14 -150 -60 q-30 -50 -40 -106 z" fill="{shade}" opacity=".7"/>
  <g fill="{shade}"><ellipse cx="70" cy="-360" rx="10" ry="7"/><ellipse cx="-70" cy="-150" rx="9" ry="6"/><ellipse cx="86" cy="-140" rx="8" ry="6"/><ellipse cx="-20" cy="-390" rx="7" ry="5"/></g>
  {acc_svg if acc in ("tie", "apron") else ""}
  {eyes}
  {mouth}
  <circle cx="-74" cy="-252" r="14" fill="#e88a7a" opacity=".4"/><circle cx="74" cy="-252" r="14" fill="#e88a7a" opacity=".4"/>
  {acc_svg if acc not in ("tie", "apron") else ""}
</g></g>'''


PARTS = {"person": person, "shelf": shelf, "skyline": skyline, "embers": embers, "fog": fog, "player": player, "man": man, "hippo": hippo, "potato": potato}
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
