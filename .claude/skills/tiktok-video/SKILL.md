---
name: tiktok-video
description: Erstellt Berkans TikTok-Videos (immer auf DEUTSCH) komplett im Code mit HyperFrames, 9:16. Zwei Formate per Codewort – SZENARIO = „Was wäre wenn …“/Überlebens-Story im Stil „Der Bunker“ (flache Vektor-Illustrationen, Karaoke-Untertitel, HUD, rote Ringe, Outro „TEIL N“); LEGENDE = Lebensgeschichte einer bekannten Persönlichkeit im Stil „zeitreisehaus“ (cinematische Bilder, weiße Großbuchstaben-Untertitel, Name erst am Ende). Verwenden bei jeder Anfrage nach einem neuen Video („Die Geschichte von X – LEGENDE“, „… – SZENARIO“), einem neuen Teil oder Änderungen an einem Video in videos/.
---

# TikTok-Video (Deutsch, HyperFrames)

Jedes Video: **Deutsch**, 1080×1920 @ 30 fps, gebaut als HyperFrames-Projekt unter `videos/<nr>-<slug>/`.
Der Look ist verbindlich – er steht in `references/style.md` (vorher lesen) und ist in
`videos/01-keiner-arbeitet/` vollständig umgesetzt (Referenz-Implementierung: bei Zweifeln dort nachsehen).
Für HyperFrames-Regeln gilt zusätzlich der Plugin-Skill `/hyperframes:hyperframes`.

`HF` = `node ~/.claude/plugins/cache/hyperframes/hyperframes/*/skills/hyperframes/scripts/plugin-cli.mjs`
(Plugin-Launcher, nie `npx hyperframes` direkt). `SK` = `.claude/skills/tiktok-video`.

## Codewörter – welches Format?

| Codewort | Format | Stil-Referenz | Beispiel-Projekt |
|---|---|---|---|
| **SZENARIO** | Was-wäre-wenn / Überleben, „Tag X, Uhrzeit“, Cliffhanger, Outro „TEIL N“ | `references/style.md` | `videos/03-apokalypse/` |
| **LEGENDE** | Lebensgeschichte einer bekannten Person, Teaser → schwarze Karten → „Es ist [Jahr].“ → Name am Ende | `references/legende.md` | `videos/04-legende-ronaldo/` |

Beispiel: „Die Geschichte von Cristiano Ronaldo – LEGENDE“. Ohne Codewort: nach Thema entscheiden
(Person → LEGENDE, Gedankenexperiment → SZENARIO). Schritte 1–6 gelten für beide; LEGENDE-Abweichungen:
kein HUD (`build_index.py` entfernt den Host), Untertitel mit `--style legende --skip <Kartenzeilen>`,
Szenen/SFX in `scenes.json`.

## 0. Setup (einmal pro Container)

```bash
bash $SK/scripts/setup.sh          # sherpa-onnx 1.12.40, Stimme Thorsten, Hyperframes-Plugin, Chrome
bash $SK/scripts/setup.sh --asr    # zusätzlich Whisper, wenn transkribiert werden soll
```
HuggingFace und CDNs (jsdelivr, unpkg) sind in dieser Umgebung gesperrt; GitHub, npm und PyPI gehen.
Darum: Modelle von GitHub-Releases (sherpa-onnx), GSAP lokal aus `assets/lib/gsap.min.js`.

## 1. Skript (script.json)

Struktur nach `references/style.md` → „Erzählstruktur“: Hook mit echtem Fakt → „Tag X, Uhrzeit.“-Abschnitte
→ „Würdest du …?“ → „Folge mir, damit du Teil N+1 nicht verpasst.“ Wortbudget ≈ 2,8 Wörter/s
(30 s ≈ 85 Wörter). Fakten nur, wenn sie stimmen; sonst vorsichtig formulieren.

```json
{ "id": "tag1_mark", "say": "Tag eins, sieben Uhr.", "show": "Tag 1, 7 Uhr.", "pause": 0.22 }
```
- `say` = gesprochen (Zahlen ausschreiben), `show` = Untertitel, **gleiche Wortanzahl**. `*Wort*` = rotes Keyword.
- Tages-Marker als eigene Zeile mit Pause **und Komma**: `say: "Tag, vier."`, sonst wird „Tag vier“ zu „K4“ verschluckt.
- Bekannte Aussprache-Fixes für Piper: „Chaos“ → `say: "Kaos"`. Neue Fälle hier ergänzen.

## 2. Stimme + Timings

```bash
python3 -I $SK/scripts/tts.py script.json assets --speed 1.0                 # Stil human (Standard) → voice.wav + timing.json
python3 -I $SK/scripts/transcribe.py assets/voice.wav              # Gegenprobe: alles richtig ausgesprochen?
```
Stile: **`human` (Standard, von Berkan gewünscht)**: Satz für Satz mit leicht schwankendem Tempo, Atemzüge in Pausen,
schonende Kette ohne Tonhöhenverschiebung. `power`: tiefer/druckvoller, klingt aber synthetischer. `neutral`: ruhig.
Stimme eines fertigen Videos austauschen, ohne Szenen neu zu timen: `--match assets/timing.json` (alte Timings) –
Zeilenanfänge bleiben exakt, zu lange Zeilen werden leicht beschleunigt, nie verlangsamt. Danach Untertitel neu bauen.
Noch menschlicher geht nur mit Cloud-TTS (Gemini/Google sind hier erreichbar) – dafür braucht es einen API-Schlüssel von Berkan.
Länge an das Ziel anpassen über `--speed` (1.0–1.15), Pausen oder Textkürzung. 60 s ≈ 170 Wörter bei `--speed 1.0`.
Whisper lässt kurze Einleitungen („Tag 2.“) gern aus – dann den Ausschnitt einzeln prüfen, bevor man die Stimme verdächtigt. Zielt das Video auf 30 s,
endet die Stimme bei ~28,5 s; der Rest gehört der Outro-Karte.

### Beste Stimme: Gemini (AI Studio) – Berkans bevorzugter Weg

Berkan erzeugt die Stimme selbst auf aistudio.google.com → „Generate speech“ (tiefe Männerstimme, z. B. Charon/Fenrir)
und schickt die WAV in den Chat. Vorlage für ihn: nur den reinen Sprechtext, Stilwunsch ins separate Stil-Feld –
sonst wird die Anweisung mitgesprochen (dann `--skip <Sekunden>`). Einbauen, Szenen bleiben synchron:
```bash
python3 -I $SK/scripts/transcribe.py upload.wav                        # Inhalt prüfen, Anweisungs-Vorspann finden
python3 -I $SK/scripts/place_voice.py upload.wav script.json out --match assets/timing.json --skip 0 --max-gap 0.2
```
**Spricht Gemini deutlich langsamer als der Platzhalter** (Zeilen kämen > 0,3 s zu spät), nicht quetschen, sondern
die Szenen auf die Stimme umtimen (natürliches Tempo, Pausen gekürzt):
```bash
python3 -I $SK/scripts/place_voice.py upload.wav script.json nat --max-gap 0.15 --max-line-gap 0.26
cp assets/timing.json alt_timing.json
python3 -I $SK/scripts/retime.py . alt_timing.json nat/timing.json --tail <Outro-Länge>
cp nat/voice.wav nat/timing.json assets/ && build_hud.py && build_captions.py   # dann voice-Dauer in index.html
```
Ohne bestehendes Video (`--match` weglassen) werden die Zeilen mit natürlichen Pausen gesetzt; dann Szenen nach
`timing.json` bauen. ElevenLabs ist angebunden, lieferte aber dauerhaft 429 (Kontolimit) – nicht erneut probieren,
ohne dass Berkan sein Konto geprüft hat.

## 3. Projekt anlegen

```bash
bash $SK/scripts/new_video.sh 02-<slug>
```
Kopiert Gerüst, lokales GSAP, SFX, `index.html` (gemeinsame Klassen `.title .r/.o`, `.chip`, `.ring`, `.cam`,
Grain, Vignette, Szenen-Hosts, Audio) und die Szenen `hud.html`, `frage.html`, `outro.html` als Vorlage.
Szenen-Hosts, HUD-Texte/Zeiten, Outro-Texte und SFX-Zeiten in `index.html` an das neue Skript anpassen.
Klangteppich erzeugen (bei 60 s: `d=61` und Fade-out `st=57.5`):
```bash
ffmpeg -y -f lavfi -i "anoisesrc=color=brown:amplitude=0.6:seed=7:d=31" -f lavfi -i "sine=f=55:d=31" -f lavfi -i "sine=f=82.4:d=31" -f lavfi -i "sine=f=110.3:d=31" -filter_complex "[0]lowpass=f=320,highpass=f=35,volume=0.5[n];[1]volume=0.35,tremolo=f=0.13:d=0.5[a];[2]volume=0.22,tremolo=f=0.21:d=0.6[b];[3]volume=0.08,tremolo=f=0.31:d=0.7[c];[n][a][b][c]amix=inputs=4:normalize=0,afade=t=in:d=1.2,afade=t=out:st=28.5:d=2.5,loudnorm=I=-26:TP=-6,aformat=channel_layouts=stereo" -ar 44100 assets/ambience.wav
```

## 4. Szenenplan

Aus `timing.json` die Wortzeiten lesen und pro Satz ein Bild planen (neues Bild alle 1–3 s).
Eine Szene (= Sub-Komposition) pro Abschnitt, darin 2–3 Beats als `.clip`-Divs. Bewährte Beat-Typen:

| Beat | Inhalt |
| --- | --- |
| Hook-Objekt | großes Objekt mittig + rote Puls-Ringe + Shake, Zweizeilen-Titel oben (weiß/rot) – **Frame 0 ist das Thumbnail** |
| Durchstreichen | Objekt/Wort + dickes rotes X (`stroke-dashoffset`), Error-SFX |
| Fakt | Illustration + großer oranger Zahlen-Titel, der auf dem Wort „slammt“ + kleiner Chip |
| Zeitkarte | große Uhrzeit/„TAG N“ in Orange + dunkler Chip „TAG N“ mit roter Unterkante |
| Story-Bild | Figuren (`person`) in Umgebung, Keyword-Titel + roter Chip |
| Ausfall | Lichter flackern (Fenster-Klasse `*-win`), dann dunkel, Impact + Glitch |
| Frage | Figur mittig, „WÜRDEST DU …“ weiß/rot, Chips JA (orange) / NEIN (rot) |
| Outro | „TEIL N“, rote Frage, großes Rad, TEILEN → TEIL N+1, Chip „FOLGE FÜR TEIL N+1“, Serienname |

Wiederverwendbare Grafik per Platzhalter in den Szenen, dann `python3 -I $SK/scripts/svg_parts.py .`:
`<!--@person id="x-p1" x="700" y="1330" s="0.9" jacket="#3d7bb3" hair="#2a1d16" style="short|spiky|long|bald" mood="neutral|worried|shocked|sad" hat="" vest="" flip="1"-->`,
`<!--@shelf id="x-shelf" x="150" y="560" w="780" h="920" fill="1|0"-->`, `<!--@skyline id="x-city" y="760" lit="1" seed="3"-->`.
Neue Bausteine (Tür, Luke, Funkgerät …) als Funktion in `svg_parts.py` ergänzen, damit sie in späteren Videos gleich aussehen.

## 5. HUD + Untertitel

`hud.json` schreiben (Format im Kopf von `scripts/build_hud.py`: Start/Ende, Tage mit Uhrzeit und Prozent, optionaler Alarm),
dann `python3 -I $SK/scripts/build_hud.py .` → `compositions/hud.html`; Host-Zeiten in `index.html` wie ausgegeben setzen.


```bash
python3 -I $SK/scripts/build_captions.py . --max-chars 20     # → compositions/captions.html
```
Nach jeder neuen Stimme neu erzeugen. Nicht von Hand editieren.

## 6. Prüfen, ansehen, rendern

```bash
$HF check                                   # 0 Fehler; Warnungen abwägen
$HF snapshot --at 0.05,2.9,4.8,...          # PNGs/Kontaktbogen LESEN – jede Szene mindestens einmal
$HF render --quality delivery --output renders/<name>.mp4
```
Danach verifizieren: `ffprobe` (1080×1920, 30 fps, Länge = Root-`data-duration`), Lautheit
(`ffmpeg -i out.mp4 -af ebur128 -f null -` → ≈ −16…−14 LUFS), Kontaktbogen aus dem MP4 ansehen,
`transcribe.py` auf das MP4. Das fertige MP4 dem Nutzer schicken.

## Fallstricke (alle schon passiert)

- GSAP vom CDN lädt nicht → Szenen frieren im Endzustand ein. Immer `assets/lib/gsap.min.js`.
- `<audio>` ohne `data-duration` gilt bis Videoende → Spur-Überlappungs-Warnungen. Dauer setzen, überlappende SFX auf eigene Spuren.
- Gradients (`<defs>`) nicht aus einem anderen Beat referenzieren – jeder Beat-SVG bekommt eigene IDs.
- Kein `stagger: { from: "random" }` (nicht deterministisch) – `"end"`, `"edges"`, `"center"` nehmen.
- Zwei `fromTo` auf dasselbe Ziel → das zweite als `tl.to(...)` schreiben.
- Puls-Ringe, die später erscheinen: `fromTo({opacity:0})` → kurz einblenden → `to(...)`, sonst sind sie vorher schon sichtbar.
- Drehpunkte in verschachtelten SVG-Gruppen mit `transformOrigin: "50% 92%"` statt `svgOrigin`.
- **GSAP überschreibt das `transform`-Attribut** einer SVG-Gruppe, die es bewegt → Objekt springt an den Bildrand oder verschwindet.
  Immer verschachteln: `<g transform="translate(…)"><g id="x-obj">…</g></g>` und nur die innere Gruppe animieren (`person` macht das schon).
- Titel nicht unter das HUD legen (`top ≥ 390px`), Text nicht in die Untertitel-Zone 1300–1430 px.
- sherpa-onnx 2.x hat kein espeak-Frontend mehr → Version 1.12.40 verwenden.
- IDs eindeutig mit Szenen-Präfix (`h-`, `f-`, `t1-` …), jede Szene registriert `window.__timelines["<id>"]`.
