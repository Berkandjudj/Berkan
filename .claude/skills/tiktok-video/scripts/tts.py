#!/usr/bin/env python3
"""Deutsche Offline-Sprachausgabe (Piper/Thorsten via sherpa-onnx) mit Wort-Timings.

Aufruf:
  python3 -I tts.py script.json OUT_DIR [--voice DIR] [--speed 1.0] [--sid N]

script.json:
  {"lines": [
     {"id": "hook", "say": "Tag eins, sieben Uhr.", "show": "Tag 1, 7 Uhr.", "pause": 0.25},
     ...
  ]}
  - say   : was gesprochen wird (Zahlen ausgeschrieben)
  - show  : was im Untertitel steht (gleiche Wortanzahl wie say!). *Wort* = rot hervorgehoben.
  - pause : Stille nach der Zeile in Sekunden (Standard 0.18)

Schreibt OUT_DIR/voice.wav und OUT_DIR/timing.json:
  {"duration": s, "lines": [{"id","start","end","words":[{"text","say","start","end","key"}]}]}
"""
import argparse, json, os, re, subprocess, sys
import numpy as np
import sherpa_onnx

SR_OUT = 44100
DEFAULT_VOICE = os.path.expanduser("~/.cache/tiktok-video/voices/vits-piper-de_DE-thorsten-high")


def load_tts(voice_dir, threads=8):
    onnx = [f for f in os.listdir(voice_dir) if f.endswith(".onnx")][0]
    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=os.path.join(voice_dir, onnx),
                tokens=os.path.join(voice_dir, "tokens.txt"),
                data_dir=os.path.join(voice_dir, "espeak-ng-data"),
                noise_scale=0.6, noise_scale_w=0.7, length_scale=1.0),
            num_threads=threads),
        max_num_sentences=1)
    return sherpa_onnx.OfflineTts(cfg)


def syllables(word):
    w = re.sub(r"[^a-zäöüß0-9]", "", word.lower())
    if re.fullmatch(r"\d+", w):
        return 2 * len(w)
    n = len(re.findall(r"[aeiouyäöü]+", w))
    return max(1, n)


def speech_chunks(audio, sr, min_gap=0.11, thr_db=-38):
    """Findet zusammenhängende Sprachabschnitte (für Pausen an Kommas/Punkten)."""
    hop = int(sr * 0.01)
    frames = len(audio) // hop
    rms = np.array([np.sqrt(np.mean(audio[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(frames)])
    db = 20 * np.log10(rms / (rms.max() + 1e-9))
    voiced = db > thr_db
    chunks, start, gap = [], None, 0
    for i, v in enumerate(voiced):
        if v:
            if start is None:
                start = i
            gap = 0
            end = i
        elif start is not None:
            gap += 1
            if gap * 0.01 >= min_gap:
                chunks.append((start * 0.01, (end + 1) * 0.01)); start = None; gap = 0
    if start is not None:
        chunks.append((start * 0.01, (end + 1) * 0.01))
    return chunks


def time_words(say_words, chunks):
    """Verteilt Wörter auf Sprachabschnitte; Phrasengrenzen = Satzzeichen."""
    phrases, cur = [], []
    for i, w in enumerate(say_words):
        cur.append(i)
        if re.search(r"[,.!?;:…]$", w):
            phrases.append(cur); cur = []
    if cur:
        phrases.append(cur)
    if len(chunks) != len(phrases) or not chunks:
        # Fallback: ganzer stimmhafter Bereich als ein Abschnitt
        phrases = [list(range(len(say_words)))]
        chunks = [(chunks[0][0], chunks[-1][1])] if chunks else [(0.0, 1.0)]
    out = [None] * len(say_words)
    for idx, (a, b) in zip(phrases, chunks):
        weights = [syllables(say_words[i]) + 0.6 for i in idx]
        tot, t = sum(weights), a
        for i, wgt in zip(idx, weights):
            d = (b - a) * wgt / tot
            out[i] = (round(t, 3), round(t + d, 3)); t += d
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("out")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--sid", type=int, default=0)
    ap.add_argument("--lead", type=float, default=0.15, help="Stille am Anfang")
    a = ap.parse_args()
    spec = json.load(open(a.script, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    tts = load_tts(a.voice)
    sr = tts.sample_rate
    pieces = [np.zeros(int(sr * a.lead), dtype=np.float32)]
    t = a.lead
    lines_out = []
    for line in spec["lines"]:
        say = line["say"].split()
        show = line.get("show", line["say"]).split()
        if len(say) != len(show):
            sys.exit(f"Zeile {line['id']}: say ({len(say)}) und show ({len(show)}) brauchen gleich viele Wörter")
        g = tts.generate(line["say"], sid=line.get("sid", a.sid), speed=line.get("speed", a.speed))
        audio = np.array(g.samples, dtype=np.float32)
        ch = speech_chunks(audio, sr)
        # führende/abschließende Stille abschneiden
        s0, s1 = (int(ch[0][0] * sr), int(ch[-1][1] * sr)) if ch else (0, len(audio))
        s0 = max(0, s0 - int(0.02 * sr)); s1 = min(len(audio), s1 + int(0.04 * sr))
        audio = audio[s0:s1]
        ch = [(x - s0 / sr, y - s0 / sr) for x, y in ch]
        wt = time_words(say, ch)
        words = []
        for sw, dw, (ws, we) in zip(say, show, wt):
            key = dw.startswith("*") or dw.rstrip(",.!?;:").endswith("*")
            words.append({"text": dw.replace("*", ""), "say": sw, "key": key,
                          "start": round(t + ws, 3), "end": round(t + we, 3)})
        dur = len(audio) / sr
        lines_out.append({"id": line["id"], "start": round(t, 3), "end": round(t + dur, 3), "words": words})
        pause = line.get("pause", 0.18)
        pieces += [audio, np.zeros(int(sr * pause), dtype=np.float32)]
        t += dur + pause
    full = np.concatenate(pieces)
    raw = os.path.join(a.out, "voice_raw.f32")
    full.astype(np.float32).tofile(raw)
    wav = os.path.join(a.out, "voice.wav")
    # leichte Wärme + Kompression + Lautheit für Social (-16 LUFS, -1.5 dBTP)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", raw,
                    "-af", "highpass=f=70,equalizer=f=180:t=q:w=1:g=2.5,equalizer=f=3500:t=q:w=1.5:g=1.5,"
                           "acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
                           "loudnorm=I=-16:TP=-1.5:LRA=7",
                    "-ar", str(SR_OUT), wav], check=True)
    os.remove(raw)
    json.dump({"duration": round(t, 3), "lines": lines_out}, open(os.path.join(a.out, "timing.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"voice.wav  {t:.2f}s  ({sum(len(l['words']) for l in lines_out)} Wörter)")
    for l in lines_out:
        print(f"  [{l['start']:6.2f}-{l['end']:6.2f}] {l['id']}: {' '.join(w['text'] for w in l['words'])}")


if __name__ == "__main__":
    main()
