#!/usr/bin/env python3
"""Fremde Sprachaufnahme (z. B. ElevenLabs) ins Video einpassen – ohne Szenen neu zu timen.

Aufruf:
  python3 -I place_voice.py AUFNAHME.mp3 script.json OUT_DIR [--match alte_timing.json] [--max-tempo 1.10]

1. Teilt die Aufnahme an Sprechpausen (Silero-VAD) und transkribiert jeden Abschnitt (Whisper, offline).
2. Gleicht die erkannten Wörter mit den `say`-Wörtern aus script.json ab → Zeilengrenzen in der Aufnahme.
3. Schneidet jede Zeile aus. Mit --match wird sie exakt auf den alten Zeilenstart gesetzt; ist sie länger als
   bis zum nächsten Start Platz ist, wird sie leicht beschleunigt (höchstens --max-tempo), sonst rückt alles nach.
   Ohne --match werden die Zeilen mit ihren natürlichen Pausen hintereinander gesetzt.
4. Schreibt OUT_DIR/voice.wav (−14 LUFS) und OUT_DIR/timing.json im selben Format wie tts.py.
"""
import argparse, difflib, json, os, re, subprocess, sys
import numpy as np
import sherpa_onnx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts import speech_chunks, time_words, stretch  # noqa: E402

SR = 16000
OUT_SR = 44100
ASR = os.path.expanduser("~/.cache/tiktok-video/asr")


def load(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def norm(w):
    w = w.lower().replace("ß", "ss")
    return re.sub(r"[^a-z0-9äöü]", "", w)


NUM = {"1": "eins", "2": "zwei", "3": "drei", "4": "vier", "5": "fünf", "6": "sechs", "7": "sieben",
       "8": "acht", "9": "neun", "10": "zehn", "11": "elf", "12": "zwölf"}


def segments(audio16):
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = os.path.join(ASR, "silero_vad.onnx")
    cfg.silero_vad.min_silence_duration = 0.16
    cfg.silero_vad.min_speech_duration = 0.1
    cfg.silero_vad.max_speech_duration = 12
    cfg.sample_rate = SR
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=180)
    ws, out = cfg.silero_vad.window_size, []
    for i in range(0, len(audio16), ws):
        vad.accept_waveform(audio16[i:i + ws])
        while not vad.empty():
            out.append((vad.front.start / SR, (vad.front.start + len(vad.front.samples)) / SR)); vad.pop()
    vad.flush()
    while not vad.empty():
        out.append((vad.front.start / SR, (vad.front.start + len(vad.front.samples)) / SR)); vad.pop()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio"); ap.add_argument("script"); ap.add_argument("out")
    ap.add_argument("--match")
    ap.add_argument("--max-tempo", type=float, default=1.10)
    ap.add_argument("--lead", type=float, default=0.15)
    a = ap.parse_args()
    spec = json.load(open(a.script, encoding="utf-8"))
    old = {l["id"]: l for l in json.load(open(a.match, encoding="utf-8"))["lines"]} if a.match else {}

    a16 = load(a.audio, SR)
    full = load(a.audio, OUT_SR)
    segs = segments(a16)
    M = os.path.join(ASR, "sherpa-onnx-whisper-small")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=f"{M}/small-encoder.int8.onnx", decoder=f"{M}/small-decoder.int8.onnx",
        tokens=f"{M}/small-tokens.txt", language="de", task="transcribe", num_threads=8)
    # erkannte Wörter mit grober Zeit (gleichmäßig im Abschnitt verteilt, nach Zeichenlänge)
    hyp = []  # (norm_word, t_start, t_end)
    for s, e in segs:
        st = rec.create_stream(); st.accept_waveform(SR, a16[int(s * SR):int(e * SR)]); rec.decode_stream(st)
        words = [w for w in st.result.text.split() if norm(w)]
        tot = sum(len(norm(w)) + 1 for w in words) or 1
        t = s
        for w in words:
            d = (e - s) * (len(norm(w)) + 1) / tot
            hyp.append((NUM.get(norm(w), norm(w)), t, t + d)); t += d

    # Skriptwörter
    ref, owner = [], []  # norm word, line index
    for li, line in enumerate(spec["lines"]):
        for w in line["say"].split():
            ref.append(NUM.get(norm(w), norm(w))); owner.append(li)
    sm = difflib.SequenceMatcher(a=ref, b=[h[0] for h in hyp], autojunk=False)
    ref_t = [None] * len(ref)
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            ref_t[i + k] = (hyp[j + k][1], hyp[j + k][2])
    matched = sum(1 for x in ref_t if x)
    print(f"Abgleich: {matched}/{len(ref)} Skriptwörter in der Aufnahme gefunden")
    # Lücken monoton interpolieren
    known = [i for i, x in enumerate(ref_t) if x]
    if not known:
        sys.exit("Keine Übereinstimmung – passt die Aufnahme zum Skript?")
    for i in range(len(ref)):
        if ref_t[i] is None:
            p = max([k for k in known if k < i], default=None); n_ = min([k for k in known if k > i], default=None)
            if p is None:
                ref_t[i] = (ref_t[n_][0], ref_t[n_][0])
            elif n_ is None:
                ref_t[i] = (ref_t[p][1], ref_t[p][1])
            else:
                f = (i - p) / (n_ - p)
                tt = ref_t[p][1] + f * (ref_t[n_][0] - ref_t[p][1])
                ref_t[i] = (tt, tt)

    # Zeilengrenzen: an der nächsten echten Pause (VAD-Lücke) zwischen letztem und erstem Wort
    gaps = [(segs[i][1], segs[i + 1][0]) for i in range(len(segs) - 1)]
    nlines = len(spec["lines"])
    first = [owner.index(li) for li in range(nlines)]
    last = [len(owner) - 1 - owner[::-1].index(li) for li in range(nlines)]
    cuts = []  # (start, end) je Zeile in der Aufnahme
    for li in range(nlines):
        cuts.append([ref_t[first[li]][0], ref_t[last[li]][1]])
    for li in range(nlines - 1):
        boundary = (cuts[li][1] + cuts[li + 1][0]) / 2
        near = [g for g in gaps if abs((g[0] + g[1]) / 2 - boundary) < 0.9]
        if near:
            g = min(near, key=lambda g: abs((g[0] + g[1]) / 2 - boundary))
            cuts[li][1], cuts[li + 1][0] = g[0], g[1]
        else:
            cuts[li][1] = cuts[li + 1][0] = boundary
    cuts[0][0] = segs[0][0]
    cuts[-1][1] = segs[-1][1]

    placed, lines_out, t, report = [], [], a.lead, []
    for li, line in enumerate(spec["lines"]):
        s0 = max(0, int((cuts[li][0] - 0.03) * OUT_SR)); s1 = int((cuts[li][1] + 0.06) * OUT_SR)
        clip = full[s0:s1].copy()
        fade = int(0.01 * OUT_SR)
        clip[:fade] *= np.linspace(0, 1, fade); clip[-fade:] *= np.linspace(1, 0, fade)
        nat_gap = (cuts[li][0] - cuts[li - 1][1]) if li else 0
        if line["id"] in old:
            start = max(t, old[line["id"]]["start"])
            nxt = [old[l["id"]]["start"] for l in spec["lines"][li + 1:] if l["id"] in old]
            room = (nxt[0] - 0.08 - start) if nxt else 1e9
            tempo = min(a.max_tempo, (len(clip) / OUT_SR) / room) if room > 0 else a.max_tempo
            if tempo > 1.003:
                clip = stretch(clip, OUT_SR, tempo)
            report.append((line["id"], round(max(tempo, 1.0), 3)))
        else:
            start = t + (nat_gap if li else 0)
        placed.append((int(start * OUT_SR), clip))
        say, show = line["say"].split(), line.get("show", line["say"]).split()
        wt = time_words(say, speech_chunks(clip, OUT_SR))
        words = []
        for sw, dw, (ws, we) in zip(say, show, wt):
            key = dw.startswith("*") or dw.rstrip(",.!?;:").endswith("*")
            words.append({"text": dw.replace("*", ""), "say": sw, "key": key,
                          "start": round(start + ws, 3), "end": round(start + we, 3)})
        dur = len(clip) / OUT_SR
        lines_out.append({"id": line["id"], "start": round(start, 3), "end": round(start + dur, 3), "words": words})
        t = start + dur
    total = t + 0.3
    mix = np.zeros(int(total * OUT_SR) + 1, dtype=np.float32)
    for s, x in placed:
        mix[s:s + len(x)] += x[:len(mix) - s]
    os.makedirs(a.out, exist_ok=True)
    raw = os.path.join(a.out, "voice_raw.f32"); mix.tofile(raw)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(OUT_SR), "-ac", "1", "-i", raw,
                    "-af", "highpass=f=60,loudnorm=I=-14:TP=-1.2:LRA=9", "-ar", str(OUT_SR),
                    os.path.join(a.out, "voice.wav")], check=True)
    os.remove(raw)
    json.dump({"duration": round(total, 3), "lines": lines_out}, open(os.path.join(a.out, "timing.json"), "w"),
              ensure_ascii=False, indent=1)
    if report:
        print("Beschleunigung je Zeile:", [r for r in report if r[1] > 1.0] or "keine")
    late = [(l["id"], round(l["start"] - old[l["id"]]["start"], 2)) for l in lines_out
            if l["id"] in old and l["start"] - old[l["id"]]["start"] > 0.05]
    if late:
        print("Zeilen später als vorher (Szenen ggf. nachziehen):", late)
    print(f"voice.wav {total:.2f}s")
    for l in lines_out:
        print(f"  [{l['start']:6.2f}-{l['end']:6.2f}] {l['id']}")


if __name__ == "__main__":
    main()
