"""Cut one clean strike from the foraged Fridingen station bell (decode with ffmpeg only).
Finds strike onsets from the energy envelope, keeps the strike with the longest clean decay
before the next onset, trims to 1.4 s with a 0.25 s fade, levels peak to 0.26 (kit's
Mix.master then gives about -13 dBFS). Writes test-shot/bell_strike.wav (mono 44.1 kHz).
Run: python3 -I bell.py"""
import json
import subprocess
import wave
import numpy as np

MED = "/home/user/bolas/paeleo/scion/oulipo/films/sources/anemic-cinema/test-shot"
RATE = 44100
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", (MED + "/fridingen.ogg" if __import__("os").path.exists(MED + "/fridingen.ogg") else MED + "/fridingen_transcode.mp3"), "-ac", "1", "-ar", str(RATE),
                      "-f", "s16le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
hop = RATE // 100
env = np.array([np.sqrt((x[i:i + hop] ** 2).mean()) for i in range(0, len(x) - hop, hop)])
db = 20 * np.log10(env + 1e-9)
rise = np.diff(db, prepend=db[0])
on = [i for i in range(3, len(db)) if rise[i] > 6 and db[i] > db.max() - 20]
onsets = []
for i in on:
    if not onsets or i - onsets[-1] > 30:
        onsets.append(i)
best, best_len = None, -1
for j, i in enumerate(onsets):
    nxt = onsets[j + 1] if j + 1 < len(onsets) else len(db)
    if nxt - i > best_len:
        best, best_len = i, nxt - i
start = max(0, best * hop - int(0.01 * RATE))
L = min(int(1.4 * RATE), best_len * hop)
seg = x[start:start + L].copy()
fade = int(0.25 * RATE)
seg[-fade:] *= np.linspace(1, 0, fade) ** 2
seg *= 0.26 / np.abs(seg).max()
with wave.open(MED + "/bell_strike.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes((seg * 32767).astype(np.int16).tobytes())
info = {"onsets_s": [o / 100 for o in onsets], "chosen_onset_s": start / RATE, "length_s": L / RATE,
        "clean_gap_to_next_s": best_len / 100}
json.dump(info, open(MED + "/bell_trim.json", "w"), indent=1)
print(info)
