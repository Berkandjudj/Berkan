# LEGENDE – Stilbibel (Lebensgeschichten bekannter Persönlichkeiten)

Referenzen: drei Videos im Stil „zeitreisehaus“ (Pablo Escobar, Napoleon, Kosovo/NATO) –
Kontaktbögen `legende_ref1..3_contact.jpg`, Untertitel-Detail `legende_detail_caption.png`.
Umsetzung im Code: `videos/04-legende-ronaldo/` (Referenz-Implementierung).

## Format
- 9:16, 1080×1920 @ 30 fps, 55–65 s, Deutsch, eine tiefe, ernste Erzählerstimme.
- Kein HUD, keine Outro-Karte „TEIL N“, keine roten Alarm-Ringe.

## Erzählstruktur
1. **Teaser-Hook (0–4 s):** das Paradox ohne Namen. „Der erfolgreichste … wäre beinahe nie … geworden.“
2. **Schwarze Textkarten (3–4 s):** „Denn mit fünfzehn …“ – ein Schlüsselwort rot (Montserrat 800, zentriert, schwarzer Grund).
   Keine Untertitel darüber (`--skip card1,card2`).
3. **„Es ist [Jahr].“** – ab hier chronologisch: Herkunft → Kindheit → Wendepunkt/Krise → Aufstieg → Rekorde.
   Kurze Sätze, je Satz ein neues Bild.
4. **Auflösung am Ende:** Name erst im letzten Satz. „Und der Junge, der …, heißt X.“ Name groß in Gold, Feuerwerk/Glow.
5. Optional Folge-Pille („Folg für mehr Legenden!“).
Fakten nur, wenn sie stimmen – lieber weglassen als erfinden.

## Look
- Painterly-cinematisch, Teal/Orange-Palette, Feuer, Glut (`embers`), Nebel (`fog`), Rim-Light, Vignette.
- Alle 2–4 s ein neues Bild (Beat), jedes mit langsamem Push-in (scale 1 → 1.06) und kleinem Drift.
- Personen in Rückansicht / Silhouette (`player`-Part: Hinterkopf, Trikotnummer, Posen stand/siu/run/arms) –
  keine Gesichter nötig, wirkt filmischer.
- Zahlen und Jahre als große Inserts („12 JAHRE“, „5×“, „2016“, Zähler 0→900 via onUpdate).

## Untertitel
`build_captions.py --style legende --skip card1,card2 --max-words 3`: weiß, Montserrat 800, Großbuchstaben,
kein Kasten, starker Schatten, zentriert bei y≈1210, 2–3 Wörter pro Gruppe.

## Aufbau des Projekts
- `scenes.json`: Szenen (id, start, dur) + SFX-Liste; `build_index.py` erzeugt daraus Hosts und Audio in `index.html`
  und entfernt den HUD-Host des Templates.
- Szenen als Sub-Compositions in `compositions/` mit Beats (`.clip` + eigene Präfixe), Parts per `svg_parts.py`.
- SFX: Whoosh je Szenenwechsel, Herzschlag/Impact auf Schlüsselwörter, Riser + Impact auf den Namen.

## Szenen-Generator (ab Video 06)
`videos/06-legende-escobar/gen_scenes.py` erzeugt alle Szenen + `scenes.json` direkt aus `assets/timing.json`
(Beat-Grenzen und Einblendungen hängen an Wort-Zeitpunkten). Neue Stimme einbauen ohne retime:
`place_voice.py` (natürlich, ohne `--match`) → `python3 gen_scenes.py` → `svg_parts.py .` → `python3 build_index.py`
→ `build_captions.py . --style legende --skip card1,card2`. Für neue Personen dieses Skript als Vorlage kopieren.
Parts dafür: `man` (Mann in Rückansicht, Posen stand/phone/arms/walk), `hippo`, `person` mit `style="curly"` und `beard="mustache|full"`.
