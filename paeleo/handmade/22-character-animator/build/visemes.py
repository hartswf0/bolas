"""SCION 22 · lip sync.  Computes the person's visemes from the voice AUDIO only (it never reads the text or the phone list):
per 10 ms analysis frame: RMS, voicing (normalised autocorrelation), high-band ratio, and three
band-energy features standing in for the first two formants (openness, frontness, centroid); a rule
classifier maps them to Character Animator's viseme names; per video frame the dominant class is chosen and a 2-frame
minimum hold is applied (as Character Animator's lip sync does).  Writes ../puppet/visemes.json and cache/visemes.json."""
import numpy as np, json, os
from common import CACHE, FOLDER, N, FPS

FS = 44100


def bands(seg):
    """pre-emphasised power spectrum of a 40 ms window -> centroid (200-4000 Hz), openness (600-1100 / 200-600 Hz:
    a high first formant means an open jaw) and frontness (1700-3200 Hz share: a high second formant means spread lips)"""
    seg = np.append(seg[0], seg[1:] - 0.97 * seg[:-1])
    sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 4096)) ** 2
    f = np.fft.rfftfreq(4096, 1 / FS)
    b = lambda lo, hi: float(sp[(f >= lo) & (f < hi)].sum()) + 1e-12
    tot = b(200, 4000)
    m = (f >= 200) & (f < 4000)
    return {'centroid': float((sp[m] * f[m]).sum() / tot), 'open': b(600, 1100) / b(200, 600), 'front': b(1700, 3200) / tot,
            'hb': b(3800, 12000) / (b(50, 12000)), 'lb': b(50, 600) / b(50, 12000)}


def analyse(x):
    hop, win = int(0.010 * FS), int(0.040 * FS)
    out = []
    for i0 in range(0, len(x) - win, hop):
        s = x[i0:i0 + win]
        rms = float(np.sqrt(np.mean(s ** 2)) + 1e-12)
        ac = np.correlate(s, s, 'full')[win - 1:]
        lo, hi = int(FS / 400), int(FS / 120)
        voiced = float(ac[lo:hi].max() / (ac[0] + 1e-12))
        fe = bands(s) if rms > 1e-5 else {'centroid': 0, 'open': 0, 'front': 0, 'hb': 0, 'lb': 0}
        out.append(dict(t=(i0 + win / 2) / FS, rms=rms, voiced=voiced, **fe))
    return out


def classify(fr, ref):
    db = 20 * np.log10(fr['rms'] / ref)
    if db < -38:
        return 'Neutral'
    if fr['voiced'] < 0.45:
        return 'S' if fr['hb'] > 0.45 else 'D'
    if db < -8 and fr['centroid'] < 460:
        return 'M'                       # weak voiced murmur with all its energy low: lips closed
    if fr['front'] > 0.12:
        return 'Ee'
    if fr['open'] > 4:
        return 'Oh' if fr['centroid'] < 800 else 'Ah'
    if fr['open'] > 0.6:
        return 'Uh'
    if fr['centroid'] < 560:
        return 'W-Oo' if db > -8 else 'L'
    return 'Ee' if fr['front'] > 0.07 else 'Uh'


def main():
    x = np.load(os.path.join(CACHE, 'voice.npy')).astype(float)
    A = analyse(x)
    ref = max(a['rms'] for a in A)
    # loudness reference per utterance region: the classifier's dB threshold should be relative to each line, not the loudest call
    rms = np.array([a['rms'] for a in A]); ts = np.array([a['t'] for a in A])
    labs = []
    for k, a in enumerate(A):
        near = rms[max(0, k - 120):k + 120]
        labs.append(classify(a, max(near.max(), ref * 0.05)))
    vis = []
    for i in range(N):
        t0, t1 = i / FPS, (i + 1) / FPS
        sel = [l for l, t in zip(labs, ts) if t0 <= t < t1]
        if not sel:
            vis.append('Neutral'); continue
        cnt = {}
        for l in sel:
            cnt[l] = cnt.get(l, 0) + (0.6 if l == 'Neutral' else 1.0)
        vis.append(max(cnt, key=cnt.get))
    # 2-frame minimum hold
    for i in range(1, N - 1):
        if vis[i] != vis[i - 1] and vis[i] != vis[i + 1] and vis[i - 1] == vis[i + 1]:
            vis[i] = vis[i - 1]
    lev = [round(float(20 * np.log10(np.mean(rms[(ts >= i / FPS) & (ts < (i + 1) / FPS)] if np.any((ts >= i / FPS) & (ts < (i + 1) / FPS)) else [1e-9]) / ref + 1e-12)), 1) for i in range(N)]
    res = {'about': 'visemes computed from cache/voice.wav by build/visemes.py (audio analysis only: RMS, voicing, band-energy openness/frontness/centroid)',
           'fps': FPS, 'visemes': vis, 'level_db': lev,
           'segments': []}
    cur = None
    for i, v in enumerate(vis):
        if v != cur:
            res['segments'].append([round(i / FPS, 3), v]); cur = v
    json.dump(res, open(os.path.join(CACHE, 'visemes.json'), 'w'))
    os.makedirs(os.path.join(FOLDER, 'puppet'), exist_ok=True)
    json.dump({k: res[k] for k in ['about', 'fps', 'segments']}, open(os.path.join(FOLDER, 'puppet', 'visemes.json'), 'w'), indent=0)
    print(' '.join(f'{t}:{v}' for t, v in res['segments']))


if __name__ == '__main__':
    main()
