"""Sound for a re-rendered FALL cut, rebuilt the way that evening's assemble.py did it: foley from the cut's own event list and the
porch TV's sound (silent while time is stopped). No credits. python3 sound.py N -> cutN_av.mp4"""
import sys, json, subprocess, wave, numpy as np
N = sys.argv[1]; sys.argv = ['x']
sys.path.insert(0, '/home/claude/lab/kit'); sys.path.insert(0, '/home/claude/rerender'); sys.path.insert(1, '/home/claude/lab/fall')
import importlib, sound2 as SD; F = importlib.import_module(f'cut{N}')
D = '/home/claude/lab/fall/'; O = '/home/claude/rerender/'; SR = 48000
ev = [tuple(x) for x in json.load(open(O + f'events{N}.json'))]
SD.build(F.DUR, ev, O + f'fx{N}.wav', norm=1.5)
w = wave.open(O + f'fx{N}.wav'); fx = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767; w.close()
def audio(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32767
tv = SD.bp(audio(D + 'plates/cataloochee.mp4'), 350, 3200); tv /= np.abs(tv).max() + 1e-9
out = fx.copy()
def lay(src, s0, s1, c0, g):
    i0, i1 = int(s0 * SR), int(s1 * SR); a = int(c0 * SR); seg = src[a:a + (i1 - i0)]
    if len(seg) == 0: return
    n = len(seg); fade = np.ones(n); k = min(n // 2, int(.04 * SR)); fade[:k] = np.linspace(0, 1, k); fade[-k:] = np.linspace(1, 0, k)
    out[i0:i0 + n] += seg * fade * g
lay(tv, 8.0, F.T_FREEZE - .1, F.TV_START + F.world(8.0), .35)
lay(tv, F.T_RELEASE + .6, F.T_RELEASE + 6.0, F.TV_START + F.world(F.T_RELEASE + .6), .3)
for k in range(3): lay(tv, F.T_RELEASE + 6.0 + k * 6.5, min(F.DUR - 4.5, F.T_RELEASE + 6.0 + (k + 1) * 6.5), 41.3, .22)
out = np.tanh(out * 1.1) * .95
w = wave.open(O + f'cut{N}.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', O + f'cut{N}.mp4', '-i', O + f'cut{N}.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '96k', '-shortest', '-movflags', '+faststart', O + f'cut{N}_av.mp4'], check=True)
print('ok', N)
