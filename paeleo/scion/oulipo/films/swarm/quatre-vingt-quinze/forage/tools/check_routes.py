"""Simulate the plan.md section 7 sound timetable from the cues alone, to check A2: across E (15-18 s) carries
no bell tail; down E (44-47 s) does. Writes route_mix_preview.wav (64 s) and route_check.json.
Usage: python3 check_routes.py <forager-sound dir> [offset_s]  (offset = cue t0 after cell start; default 0.5)"""
import json, sys, wave
import numpy as np
D = sys.argv[1]; OFF = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
R = 44100
def rd(p):
    w = wave.open(f"{D}/{p}"); return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768.0
cues = {c: rd(f"cue_{c}.wav") for c in "ABCDEFGHI"}
across, down = "ABCDEFGHI", "ADGBEHCFI"
sched = [(3 + 3 * i, c) for i, c in enumerate(across)] + [(32 + 3 * i, c) for i, c in enumerate(down)]
n = 64 * R
mix = np.zeros((n, 2)); bell = np.zeros((n, 2))
for t, c in sched:
    i = int((t + OFF) * R); s = cues[c][: n - i]
    mix[i:i + len(s)] += s
    if c == "B": bell[i:i + len(s)] += s
room = rd("room.wav")[:n]; mix[: len(room)] += room
def db(x): return round(float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)), 1)
res = {"offset_s": OFF, "across_E_15_18_bell_rms_dbfs": db(bell[15 * R:18 * R]),
       "down_E_44_47_bell_rms_dbfs": db(bell[44 * R:47 * R]),
       "down_E_44.5_45.5_bell_rms_dbfs": db(bell[int(44.5 * R):int(45.5 * R)]),
       "down_bell_last_audible_s": round(float(np.where(np.abs(bell).max(1) > 10 ** (-60 / 20))[0][-1] / R), 2),
       "across_bell_last_audible_s": round(float(np.where(np.abs(bell[: 30 * R]).max(1) > 10 ** (-60 / 20))[0][-1] / R), 2),
       "peak_dbfs": db(np.abs(mix).max()), "sched": sched}
res["A2_sound_ok"] = res["across_E_15_18_bell_rms_dbfs"] < -90 and res["down_E_44.5_45.5_bell_rms_dbfs"] > -45
mx = np.clip(mix, -1, 1)
w = wave.open(f"{D}/route_mix_preview.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(R)
w.writeframes((mx * 32767).astype("<i2").tobytes()); w.close()
json.dump(res, open(f"{D}/route_check.json", "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "sched"}, indent=1))
