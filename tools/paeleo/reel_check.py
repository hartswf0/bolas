"""Check the reel's sound against the critics' conditions. python3 tools/paeleo/reel_check.py FILM REEL_JSON
- every cut (and the end card) rises at least 12 dB within 30 ms over the 100 ms before it;
- the bed (140-260 Hz, measured with a windowed FFT of each 100 ms) is at least 20 dB lower in the 100 ms before each cut than at that lens's middle."""
import json, subprocess, sys
import numpy as np
SR = 44100
x = np.frombuffer(subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', sys.argv[1], '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, dtype=np.float32).astype(float)
R = json.load(open(sys.argv[2])); cuts = [c['at'] for c in R['cuts']] + [R['dur'] - R['tail']]
rms = lambda a, b: 20 * np.log10(np.sqrt(np.mean(x[int(a * SR):int(b * SR)] ** 2)) + 1e-9)
def band(a, b):
    seg = x[int(a * SR):int(b * SR)] * np.hanning(int(b * SR) - int(a * SR)); F = np.abs(np.fft.rfft(seg)); f = np.fft.rfftfreq(len(seg), 1 / SR)
    return 20 * np.log10(np.sqrt(np.sum(F[(f >= 140) & (f <= 260)] ** 2)) + 1e-9)
on = [rms(t, t + .03) - rms(t - .1, t) for t in cuts]
bed = [band(t - .85, t - .75) - band(t - .1, t) for t in cuts[1:]]
print(f'onsets: min {min(on):.1f} dB, under 12: {sum(v < 12 for v in on)} of {len(on)}')
print(f'bed before cuts: min drop {min(bed):.1f} dB, under 20: {sum(v < 20 for v in bed)} of {len(bed)}')
