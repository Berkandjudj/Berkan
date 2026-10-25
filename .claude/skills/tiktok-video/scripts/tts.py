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
import argparse, json, os, re, subprocess, sys, zlib
import numpy as np
import sherpa_onnx

SR_OUT = 44100

# Klang-Presets. "power": ~4 % tiefer (Tempo kompensiert → Timings bleiben gleich), mehr Körper und
# Präsenz, harte Kompression + leichte Sättigung, lauter. Mehr noise = lebendigere Betonung.
STYLES = {
    "neutral": {"noise": 0.6, "noise_w": 0.7, "chain":
        "highpass=f=70,equalizer=f=180:t=q:w=1:g=2.5,equalizer=f=3500:t=q:w=1.5:g=1.5,"
        "acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-16:TP=-1.5:LRA=7"},
    # "human": Piper-Standardwerte für Betonung, Satz für Satz, Atemzüge, schonende Kette ohne Tonhöhen-
    # verschiebung (die klingt synthetisch), etwas Wärme, De-Esser, kurzer kleiner Raum, -14 LUFS.
    "human": {"noise": 0.667, "noise_w": 0.8, "per_sentence": True, "breaths": True, "chain":
        "highpass=f=70,equalizer=f=150:t=q:w=1:g=2.5,equalizer=f=420:t=q:w=1.2:g=-2,"
        "equalizer=f=3200:t=q:w=1.4:g=2,deesser=i=0.35,"
        "acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=2,"
        "aecho=0.88:0.6:17|29:0.09|0.05,"
        "loudnorm=I=-14:TP=-1.2:LRA=8"},
    "power": {"noise": 0.72, "noise_w": 0.9, "chain":
        "asetrate={sr96},aresample={sr},atempo=1.0416667,"
        "highpass=f=60,equalizer=f=130:t=q:w=1:g=4,equalizer=f=320:t=q:w=1.2:g=-2,"
        "equalizer=f=2800:t=q:w=1.2:g=4,equalizer=f=6500:t=q:w=1.5:g=-1.5,"
        "acompressor=threshold=-26dB:ratio=5:attack=2:release=60:makeup=4,"
        "asoftclip=type=tanh:threshold=0.9,"
        "loudnorm=I=-14:TP=-1.2:LRA=5"},
}
DEFAULT_VOICE = os.path.expanduser("~/.cache/tiktok-video/voices/vits-piper-de_DE-thorsten-high")


def load_tts(voice_dir, threads=8, noise=0.6, noise_w=0.7):
    onnx = [f for f in os.listdir(voice_dir) if f.endswith(".onnx")][0]
    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=os.path.join(voice_dir, onnx),
                tokens=os.path.join(voice_dir, "tokens.txt"),
                data_dir=os.path.join(voice_dir, "espeak-ng-data"),
                noise_scale=noise, noise_scale_w=noise_w, length_scale=1.0),
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


def synth(tts, text, sid, speed, sr):
    """Erzeugt Audio, schneidet Stille vorn/hinten ab."""
    g = tts.generate(text, sid=sid, speed=speed)
    audio = np.array(g.samples, dtype=np.float32)
    ch = speech_chunks(audio, sr)
    s0, s1 = (int(ch[0][0] * sr), int(ch[-1][1] * sr)) if ch else (0, len(audio))
    s0 = max(0, s0 - int(0.02 * sr)); s1 = min(len(audio), s1 + int(0.04 * sr))
    return audio[s0:s1]


def stretch(audio, sr, tempo):
    """Zeitdehnung ohne Tonhöhenänderung (rubberband, sonst atempo). tempo > 1 = schneller."""
    raw = audio.astype(np.float32).tobytes()
    for flt in (f"rubberband=tempo={tempo:.5f}:formant=preserved", f"atempo={tempo:.5f}"):
        r = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                            "-af", flt, "-f", "f32le", "-"], input=raw, capture_output=True)
        if r.returncode == 0 and r.stdout:
            return np.frombuffer(r.stdout, dtype=np.float32).copy()
    return audio


def breath(sr, dur, seed, rms):
    """Leiser, natürlicher Einatmer: bandbegrenztes Rauschen mit weicher Hüllkurve."""
    n = int(sr * dur)
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / sr)
    spec *= np.exp(-((np.log(np.maximum(f, 1)) - np.log(1100)) ** 2) / (2 * 0.55 ** 2))
    x = np.fft.irfft(spec, n)
    tt = np.linspace(0, 1, n)
    env = np.sin(np.pi * tt ** 0.7) ** 1.6
    x = x * env
    return (x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * rms).astype(np.float32)


def crc(*parts):
    return zlib.crc32("|".join(map(str, parts)).encode())


def render_line(tts, line, say, sid, speed, sr, st):
    if not st.get("per_sentence"):
        return synth(tts, line["say"], sid, speed, sr)
    # Satz für Satz, mit leicht schwankendem Tempo und natürlichen Satzpausen
    sents, cur = [], []
    for w in say:
        cur.append(w)
        if re.search(r"[.!?]$", w):
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    parts = []
    for k, sw in enumerate(sents):
        jitter = ((crc(line["id"], k) % 7) - 3) * 0.012
        parts.append(synth(tts, " ".join(sw), sid, speed * (1 + jitter), sr))
        if k < len(sents) - 1:
            parts.append(np.zeros(int(sr * (0.16 + (crc(line["id"], k, "g") % 5) * 0.025)), dtype=np.float32))
    return np.concatenate(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("out")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--sid", type=int, default=0)
    ap.add_argument("--lead", type=float, default=0.15, help="Stille am Anfang")
    ap.add_argument("--style", choices=sorted(STYLES), default="human",
                    help="human = natürlichster Erzähler (Standard), neutral = ruhig, power = tiefer/druckvoller")
    ap.add_argument("--match", help="alte timing.json: jede Zeile wird exakt auf deren Start/Ende gedehnt, "
                                    "damit fertige Szenen synchron bleiben")
    a = ap.parse_args()
    spec = json.load(open(a.script, encoding="utf-8"))
    old = {l["id"]: l for l in json.load(open(a.match, encoding="utf-8"))["lines"]} if a.match else {}
    os.makedirs(a.out, exist_ok=True)
    st = STYLES[a.style]
    tts = load_tts(a.voice, noise=st["noise"], noise_w=st["noise_w"])
    sr = tts.sample_rate
    placed = []          # (startsample, audio)
    t = a.lead           # Ende des bisher gesetzten Audios
    lines_out = []
    stretches = []
    for li, line in enumerate(spec["lines"]):
        say = line["say"].split()
        show = line.get("show", line["say"]).split()
        if len(say) != len(show):
            sys.exit(f"Zeile {line['id']}: say ({len(say)}) und show ({len(show)}) brauchen gleich viele Wörter")
        sid, speed = line.get("sid", a.sid), line.get("speed", a.speed)
        audio = render_line(tts, line, say, sid, speed, sr, st)
        if line["id"] in old:
            o = old[line["id"]]
            # Zeilenanfang bleibt exakt; das Ende darf etwas in die folgende Pause ragen
            nxt = [old[l["id"]]["start"] for l in spec["lines"][li + 1:] if l["id"] in old]
            end = min(o["end"] + 0.18, nxt[0] - 0.1) if nxt else o["end"] + 0.18
            target = max(o["end"], end) - o["start"]
            # Nie verlangsamen (klingt unnatürlich). Zu lang → erst Modell-Tempo (max +15 %), dann Rest dehnen (max +10 %).
            f = (len(audio) / sr) / target
            if f > 1.01:
                speed *= min(1.15, f)
                audio = render_line(tts, line, say, sid, speed, sr, st)
            tempo = min(1.10, (len(audio) / sr) / target)
            stretches.append((line["id"], round(speed, 3), round(max(tempo, 1.0), 3)))
            audio = stretch(audio, sr, tempo) if tempo > 1.003 else audio
            start = max(t, o["start"])
        else:
            start = t
        # Atemzug in längeren Pausen vor einer neuen Zeile
        if st.get("breaths") and li > 0 and start - t >= 0.2:
            b = breath(sr, min(0.3, start - t - 0.05), crc(line["id"], "breath"),
                       float(np.sqrt(np.mean(audio ** 2))) * 0.11)
            placed.append((int((start - 0.05) * sr) - len(b), b))
        placed.append((int(start * sr), audio))
        ch = speech_chunks(audio, sr)
        wt = time_words(say, ch)
        words = []
        for sw, dw, (ws, we) in zip(say, show, wt):
            key = dw.startswith("*") or dw.rstrip(",.!?;:").endswith("*")
            words.append({"text": dw.replace("*", ""), "say": sw, "key": key,
                          "start": round(start + ws, 3), "end": round(start + we, 3)})
        dur = len(audio) / sr
        lines_out.append({"id": line["id"], "start": round(start, 3), "end": round(start + dur, 3), "words": words})
        t = start + dur + (0 if line["id"] in old else line.get("pause", 0.18))
    total = max(t, max((s + len(x)) / sr for s, x in placed) + 0.3)
    full = np.zeros(int(total * sr) + 1, dtype=np.float32)
    for s0, x in placed:
        s0 = max(0, s0)
        full[s0:s0 + len(x)] += x[:len(full) - s0]
    raw = os.path.join(a.out, "voice_raw.f32")
    full.tofile(raw)
    wav = os.path.join(a.out, "voice.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", raw,
                    "-af", st["chain"].format(sr=sr, sr96=int(sr * 0.96)),
                    "-ar", str(SR_OUT), wav], check=True)
    os.remove(raw)
    json.dump({"duration": round(total, 3), "lines": lines_out}, open(os.path.join(a.out, "timing.json"), "w"),
              ensure_ascii=False, indent=1)
    if stretches:
        print("Anpassung (Zeile, Modell-Tempo, Rest-Dehnung):", stretches)
    print(f"voice.wav  {total:.2f}s  ({sum(len(l['words']) for l in lines_out)} Wörter, Stil {a.style})")
    for l in lines_out:
        print(f"  [{l['start']:6.2f}-{l['end']:6.2f}] {l['id']}: {' '.join(w['text'] for w in l['words'])}")


if __name__ == "__main__":
    main()
