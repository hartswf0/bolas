"""Measure the meter in the rendered mix: per-onset rise (dB) in a band, caesura gap level, spectral-flux onset error."""
import sys, json, wave
import numpy as np
wav, cues = sys.argv[1], json.load(open(sys.argv[2]))["verse"]
with wave.open(wav) as w:
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768; sr = w.getframerate()
def lev(y, a, b):
    s = y[int(a * sr):int(b * sr)]; return 10 * np.log10(np.mean(s ** 2) + 1e-12)
out = {}
for band in ((200, 400), (500, 2000), (2500, 6000)):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / sr); X[(f < band[0]) | (f > band[1])] = 0
    y = np.fft.irfft(X, len(x))
    # spectral-flux style onset: envelope derivative peak within +-60 ms
    env = np.sqrt(np.convolve(y ** 2, np.ones(int(0.01 * sr)) / int(0.01 * sr), "same"))
    de = np.diff(env, prepend=0)
    res = {}
    for L, ons in cues.items():
        rises, errs = [], []
        for t in ons:
            rises.append(round(lev(y, t, t + 0.06) - lev(y, t - 0.07, t - 0.01), 1))
            a, b = int((t - 0.06) * sr), int((t + 0.06) * sr)
            errs.append(round((a + int(np.argmax(de[a:b]))) / sr - t, 3))
        gap = lev(y, ons[5] + 0.17, ons[6] - 0.05); hemi = lev(y, ons[0], ons[5] + 0.12)
        res[L] = dict(rise_db=rises, min_rise=min(rises), onset_err_s=errs, max_abs_err=max(abs(e) for e in errs),
                      gap_below_hemistich_db=round(hemi - gap, 1))
    out[f"{band[0]}-{band[1]}Hz"] = res
print(json.dumps(out, indent=1))
