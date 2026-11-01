"""Authored narration by Kokoro-82M (open local TTS; imitates no real person). usage: .tts/bin/python speak.py <lines.json> <voice> <speed>"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from kokoro import KPipeline
J, V, S = sys.argv[1], sys.argv[2], float(sys.argv[3]); P = KPipeline(lang_code=V[0], repo_id="hexgrad/Kokoro-82M"); d = os.path.dirname(J)
for k, t in json.load(open(J)).items():
    a = np.concatenate([np.asarray(x, dtype=np.float32) for _, _, x in P(t, voice=V, speed=S)]); w = os.path.join(d, k + ".wav"); sf.write(w + ".t.wav", a, 24000)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", w + ".t.wav", "-af", "highpass=f=80,loudnorm=I=-19:TP=-2:LRA=7", "-ar", "48000", "-ac", "1", w], check=True); os.remove(w + ".t.wav")
    print(k, len(a) / 24000)
