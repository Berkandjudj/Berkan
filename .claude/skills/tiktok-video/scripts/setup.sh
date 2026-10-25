#!/usr/bin/env bash
# Einmalig pro Session/Container: Werkzeuge für tiktok-video bereitstellen.
# HuggingFace ist in dieser Umgebung gesperrt – Modelle kommen von GitHub-Releases (sherpa-onnx).
set -euo pipefail
C="$HOME/.cache/tiktok-video"
mkdir -p "$C/voices" "$C/asr"
REL=https://github.com/k2-fsa/sherpa-onnx/releases/download

python3 -c "import sherpa_onnx; assert sherpa_onnx.__version__.startswith(\"1.12\")" 2>/dev/null || pip install -q "sherpa-onnx==1.12.40" numpy

# Deutsche Stimme (männlich, Erzähler). Alternative: thorsten_emotional-medium (Sprecher-IDs: neutral=4, whisper=7 …)
if [ ! -d "$C/voices/vits-piper-de_DE-thorsten-high" ]; then
  curl -sSL "$REL/tts-models/vits-piper-de_DE-thorsten-high.tar.bz2" | tar xj -C "$C/voices"
fi

# Whisper small (ONNX) + Silero-VAD – nur nötig, um Referenzvideos zu transkribieren
if [ "${1:-}" = "--asr" ] && [ ! -d "$C/asr/sherpa-onnx-whisper-small" ]; then
  curl -sSL "$REL/asr-models/sherpa-onnx-whisper-small.tar.bz2" | tar xj -C "$C/asr"
  curl -sSL -o "$C/asr/silero_vad.onnx" "$REL/asr-models/silero_vad.onnx"
fi

# Hyperframes-Plugin + Headless-Chrome
HF_CLI=$(ls -d "$HOME"/.claude/plugins/cache/hyperframes/hyperframes/*/skills/hyperframes/scripts/plugin-cli.mjs 2>/dev/null | tail -1 || true)
if [ -z "$HF_CLI" ]; then
  claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes
  HF_CLI=$(ls -d "$HOME"/.claude/plugins/cache/hyperframes/hyperframes/*/skills/hyperframes/scripts/plugin-cli.mjs | tail -1)
fi
node "$HF_CLI" browser ensure >/dev/null
echo "HF_CLI=$HF_CLI"
echo "OK: Stimme in $C/voices, Hyperframes bereit."
