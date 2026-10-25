# Stil-Bibel (aus den 3 Referenzvideos abgeleitet)

Referenzen: Serie „Der Bunker“ (@geeko.mind), Teil 10–12. Kontaktbögen: `ref1_contact.jpg` …
`ref3_contact.jpg` (alle 2 s ein Bild), Details: `ref_detail_*.png`, Transkripte: `ref*.transcript.txt`.

## Format

| Eigenschaft | Referenz | Wir rendern |
| --- | --- | --- |
| Seitenverhältnis | 9:16 (576×1024 Download) | **1080×1920**, 30 fps, H.264 + AAC |
| Länge | 78–81 s | nach Auftrag (z. B. 30 s) |
| Schnitt | neues Bild alle **1–3 s**, Szenenwechsel ~alle 4–6 s | gleich |
| Ton | Erzählerstimme + leiser dunkler Klangteppich (≈ −28 dB) + gezielte SFX | Piper „Thorsten“ + Drone + Hyperframes-SFX, Mix ≈ −15 LUFS |

## Erzählstruktur (Formel)

1. **Hook mit Lebenswissen (0–~14 s, bei 30 s: 0–8 s).** „Wenn [Situation], ist das kein [Erwartung]. Es ist [Gefahr].“
   Danach ein echter, überprüfbarer Fakt (Zahl!) – in den Referenzen mit kleiner Quelle („Quelle: CDC“).
   Fakten nie erfinden; lieber vorsichtig formulieren („oft“, „etwa“).
2. **Story/Szenario mit Zeitmarke.** Jeder Abschnitt beginnt mit „Tag X, [Uhrzeit].“ → großer Uhrzeit-/Tag-Titel.
   Kurze Hauptsätze, Präsens, ein Bild pro Satz. Der Fakt aus dem Hook wird in der Story angewendet.
3. **Cliffhanger-Frage an den Zuschauer:** „Würdest du …?“ (Ja/Nein-Chips, wie AUF/ZU in den Referenzen).
4. **CTA:** „Du bekommst den nächsten Teil nur, wenn du dieses Video mit jemandem teilst …“ /
   „Folge mir, damit du Teil N nicht verpasst.“ (bei 30 s nur den Folge-Satz).
5. **Outro-Karte** (letzte 3–14 s): „TEIL N“ orange, Frage rot, großes Rad/Symbol, „TEILEN → TEIL N+1 ↗“,
   Chip „FOLGE FÜR TEIL N+1“ mit Pfeil, Serienname unten mit Symbol und weiter Laufweite.

Sprechtempo der Referenzen ≈ 2,8 Wörter/s. Budget: **30 s ≈ 80–90 Wörter**, 60 s ≈ 170, 80 s ≈ 220.

## Bildsprache

- **Flache 2D-Vektorgrafik**, keine Fotos. Große, einfache Objekte mittig (Wecker, Messgerät, Tür, Luke, Funkgerät).
- **Dunkle, entsättigte Hintergründe** (Navy/Anthrazit `#1a202d`, `#0d1119`), weiches Licht von einer Stelle, Vignette, leichtes Korn, Staubpartikel.
- Figuren: großer runder Kopf, Punktaugen in weißen Augäpfeln, Augenbrauen tragen die Emotion, kleiner Mund, Wangenröte, einfache Körper. → `svg_parts.py person`.
- **Bedrohung/Alarm = Rot**: konzentrische rote Puls-Ringe um das Objekt, roter Overlay-Flash, Kamera-Shake.
- Hände-Nahaufnahmen (Taste drücken, Riegel schieben) als Insert-Shots.
- Durchstreichen mit dickem rotem X (Linien zeichnen sich per `stroke-dashoffset`).
- Langsamer Kamera-Push (Scale 1 → 1,07) in jeder Einstellung; Schnitte hart, gelegentlich Whoosh.

## Farben

| Token | Wert | Einsatz |
| --- | --- | --- |
| `--orange` | `#f4a62a` | Zeit, Tag, positive Keywords, Outro „TEIL N“, Rad |
| `--red` | `#e8412f` | Gefahr-Keywords, X, Ringe, Chips |
| `--yellow` | `#f7c548` | aktives Wort im Untertitel + Unterstrich |
| `--ink` | `#f4efe4` | Weißtext |
| Grau | `#8e939d` | noch nicht gesprochene Untertitel-Wörter |
| 3D-Schatten | `--orange-dark #8f5a0f`, `--red-dark #7d1a10` | `text-shadow: 0 7px 0 …` unter Titeln |

## Typografie

- **Oswald 700, Versalien** für alles (in Hyperframes gebündelt).
- Keyword-Titel: 130–270 px, mit 3D-Schatten + Glow, „Slam“-Animation (Scale 1,8 → 1 + Blur 8 → 0, 0,16 s, `power4.in`).
- Titel im oberen Drittel; **solange das HUD sichtbar ist: `top ≥ 390px`**.

## Untertitel (wichtigstes Wiedererkennungsmerkmal)

- 2–3 Wörter pro Gruppe, eine Gruppe zur Zeit, mittig bei **y ≈ 1365 px**.
- Dunkle Box `rgba(17,19,25,.88)`, Radius 10, **orange Linie oben** (4 px, 72 % Breite).
- Karaoke: kommend grau → **aktiv gelb + Unterstrich** → gesprochen weiß. Keywords (`*wort*` im Skript) werden rot.
- Erzeugt von `scripts/build_captions.py` aus den echten Wort-Timings.

## HUD (oben links, ab Story-Beginn)

- Box `left 52, top 196, 520×142`, Zeile 1: ☀-Icon · `TAG N` (orange) · `|` · Uhrzeit (tickt) · Status-Pille.
- Zeile 2: Messwert-Label · Balken mit roten Markern · Prozentwert. In den Referenzen: CO₂ %; bei uns themenbezogen (z. B. VORRÄTE).
- Wert-/Tageswechsel mit kleinem Scale-Pop, Warnzustand rot blinkend.

## Ton

- Stimme: Piper `thorsten-high`, `--speed 1.05–1.12`. Pausen über `pause` je Zeile.
- Klangteppich: tiefer Drone/Brown-Noise ≈ −26 LUFS (siehe Befehl in SKILL.md), Volume 0.9.
- SFX nur mit sichtbarer Ursache: Whoosh auf Schnitte (abwechseln), Pop auf Chips, Impact auf Keyword-Slams,
  Glitch auf Lichtausfall/Störung, Error-Ton beim Durchstreichen, Riser in die Cliffhanger-Frage.
- Peak eines SFX ≈ 1 Frame nach dem Bild: `data-start = Bildzeit − Peak` (Peaks: whoosh 0,16 s, impact 0,07 s,
  pop 0,12 s, glitch-1 0,82 s, error 0,75 s, riser 3,47 s).
