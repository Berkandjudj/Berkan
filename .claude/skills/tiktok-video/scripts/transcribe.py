#!/usr/bin/env python3
"""Transkribiert ein Video/Audio auf Deutsch (Whisper small via sherpa-onnx, offline).
Aufruf: python3 -I transcribe.py DATEI [~/.cache/tiktok-video/asr/sherpa-onnx-whisper-small]"""
import os, sys, subprocess, numpy as np, sherpa_onnx
M=sys.argv[2] if len(sys.argv)>2 else os.path.expanduser("~/.cache/tiktok-video/asr/sherpa-onnx-whisper-small")
def load(path):
    raw=subprocess.run(["ffmpeg","-v","error","-i",path,"-ac","1","-ar","16000","-f","f32le","-"],capture_output=True).stdout
    return np.frombuffer(raw,dtype=np.float32)
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/small-encoder.int8.onnx",decoder=f"{M}/small-decoder.int8.onnx",tokens=f"{M}/small-tokens.txt",language="de",task="transcribe",num_threads=8)
cfg=sherpa_onnx.VadModelConfig(); cfg.silero_vad.model=os.path.join(os.path.dirname(M.rstrip("/")),"silero_vad.onnx"); cfg.silero_vad.min_silence_duration=0.25; cfg.silero_vad.max_speech_duration=20; cfg.sample_rate=16000
vad=sherpa_onnx.VoiceActivityDetector(cfg,buffer_size_in_seconds=120)
a=load(sys.argv[1]); ws=cfg.silero_vad.window_size
segs=[]
for i in range(0,len(a),ws):
    vad.accept_waveform(a[i:i+ws])
    while not vad.empty(): segs.append((vad.front.start, np.array(vad.front.samples))); vad.pop()
vad.flush()
while not vad.empty(): segs.append((vad.front.start, np.array(vad.front.samples))); vad.pop()
for st,s in segs:
    stream=rec.create_stream(); stream.accept_waveform(16000,s); rec.decode_stream(stream)
    print(f"[{st/16000:6.2f}-{(st+len(s))/16000:6.2f}] {stream.result.text.strip()}")
