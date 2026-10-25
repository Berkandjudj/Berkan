#!/usr/bin/env bash
# Legt ein neues Video-Projekt an:  new_video.sh <nr>-<slug>   (z. B. 02-ohne-internet)
# Ergebnis: /home/user/Berkan/videos/<name>/ mit Hyperframes-Gerüst, lokalem GSAP, SFX,
# Root-index.html (gemeinsame Styles, HUD/Captions/Outro-Hosts, Ton) und Beispiel-Szenen.
set -euo pipefail
NAME="${1:?Name fehlt, z. B. 02-ohne-internet}"
SK="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$SK/../../.." && pwd)"
DIR="$REPO/videos/$NAME"
HF_CLI=$(ls -d "$HOME"/.claude/plugins/cache/hyperframes/hyperframes/*/skills/hyperframes/scripts/plugin-cli.mjs | tail -1)
[ -e "$DIR" ] && { echo "existiert schon: $DIR"; exit 1; }
mkdir -p "$REPO/videos"
(cd "$REPO" && node "$HF_CLI" init "videos/$NAME" >/dev/null)
cp "$SK/template/index.html" "$DIR/index.html"
mkdir -p "$DIR/compositions" "$DIR/assets"
cp "$SK/template/compositions/"*.html "$DIR/compositions/"
cp -r "$SK/template/assets/lib" "$SK/template/assets/sfx" "$DIR/assets/"
cp "$SK/template/script.example.json" "$DIR/script.json"
echo "Projekt: $DIR"
echo "Nächste Schritte: script.json schreiben → tts.py → build_captions.py → Szenen bauen (siehe SKILL.md)"
