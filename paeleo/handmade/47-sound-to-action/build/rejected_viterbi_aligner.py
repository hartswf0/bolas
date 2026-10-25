"""Alignment engineer: synthesize each spoken line with flite (CMU, via ffmpeg's libflite filter, voice 'slt'),
then force-align its known phoneme string to the audio with a small Viterbi aligner written here.

Output: build/cache/voice/<id>.wav (16 kHz mono, trimmed) and build/voice_lines.json:
  {id, text, words:[{w,t0,t1}], phones:[{p,cls,t0,t1}], dur, stress_onset}
Times are seconds from the start of the trimmed line. Nothing here is guessed from text length: every boundary is
chosen by the aligner from the audio's features (energy, voicing, spectral balance).
python3 build/voice.py
"""
import json, os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache', 'voice')
os.makedirs(CACHE, exist_ok=True)
SR = 16000
HOP = 80      # 5 ms
WIN = 320     # 20 ms

LINES = [
    # id, text, kind, words (ARPAbet, stress vowel marked with *)
    ('call1', 'Come here.', 'call', [('come', 'K AH M'), ('here', 'HH *IY R')]),
    ('call2', 'Come on, come here.', 'call', [('come', 'K AH M'), ('on', 'AA N'), ('come', 'K AH M'), ('here', 'HH *IY R')]),
    ('call3', 'Come here!', 'call', [('come', 'K AH M'), ('here', 'HH *IY R')]),
    ('call4', 'Come on!', 'call', [('come', 'K AH M'), ('on', '*AA N')]),
    ('soft1', "It's all right.", 'soft', [("it's", '*IH T S'), ('all', 'AO L'), ('right', 'R AY T')]),
    ('soft2', "It's okay.", 'soft', [("it's", '*IH T S'), ('okay', 'OW K EY')]),
    ('soft3', 'Come in.', 'soft', [('come', 'K AH M'), ('in', '*IH N')]),
]

CLS = {'K': 'stop', 'T': 'stop', 'P': 'stop', 'B': 'stop', 'D': 'stop', 'G': 'stop',
       'M': 'nasal', 'N': 'nasal', 'S': 'fric', 'HH': 'aspir', 'R': 'liquid', 'L': 'liquid'}
MIN_FR = {'stop': 6, 'nasal': 6, 'fric': 8, 'aspir': 6, 'liquid': 6, 'vowel': 10, 'sil': 4}


def synth(text, path):
    tf = path + '.txt'
    open(tf, 'w').write(text)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i',
                    f'flite=textfile={tf}:voice=slt', '-ar', str(SR), '-ac', '1', path], check=True)
    os.remove(tf)
    w = wave.open(path)
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x


def features(x):
    n = 1 + max(0, (len(x) - WIN) // HOP)
    win = np.hanning(WIN)
    fr = np.stack([x[i * HOP:i * HOP + WIN] * win for i in range(n)])
    spec = np.abs(np.fft.rfft(fr, 512, axis=1)) ** 2 + 1e-10
    f = np.fft.rfftfreq(512, 1 / SR)
    tot = spec.sum(1)
    e = 10 * np.log10(tot)
    e = e - e.max()
    hi = spec[:, f > 3000].sum(1) / tot
    lo = spec[:, f < 400].sum(1) / tot
    # voicing: normalized autocorrelation peak in 80-400 Hz pitch range
    v = np.zeros(n)
    for i in range(n):
        s = fr[i] - fr[i].mean()
        a = np.correlate(s, s, 'full')[WIN - 1:]
        if a[0] > 1e-8:
            v[i] = a[40:200].max() / a[0]
    return e, hi, lo, v, spec


def emis(cls, e, hi, lo, v):
    """log-score of each frame for a phone class; hand-set, monotone in the obvious cues."""
    if cls == 'sil':
        return -0.35 * np.maximum(0, e + 42)
    if cls == 'vowel':
        return -0.12 * np.maximum(0, -e - 6) + 2.5 * (v - 0.5) - 6 * hi - 1.5 * lo
    if cls == 'nasal':
        return -0.15 * np.abs(e + 14) + 2.0 * (v - 0.5) + 3.0 * lo - 8 * hi
    if cls == 'liquid':
        return -0.15 * np.abs(e + 9) + 2.0 * (v - 0.5) - 4 * hi + 0.5 * lo
    if cls == 'stop':  # closure (quiet) or burst (noisy, short)
        return np.maximum(-0.12 * np.maximum(0, e + 30), -0.2 * np.abs(e + 18) + 4 * hi - 1.5) - 1.0 * v
    if cls == 'fric':
        return 6 * hi - 2.5 * v - 0.08 * np.abs(e + 18)
    if cls == 'aspir':
        return 3 * hi - 2.0 * v - 0.1 * np.abs(e + 16)
    raise ValueError(cls)


def align(e, hi, lo, v, phones):
    """phones: list of (p, cls). Left-to-right HMM, each phone = MIN_FR chain + self loop; silences at both ends."""
    seq = [('sil', 'sil')] + phones + [('sil', 'sil')]
    states = []  # (phone index, is_loop)
    for k, (p, c) in enumerate(seq):
        m = MIN_FR[c] if c != 'sil' else 1
        for j in range(m):
            states.append((k, j == m - 1))
    S, T = len(states), len(e)
    E = np.stack([emis(c, e, hi, lo, v) for _, c in seq])  # phones x T
    NEG = -1e9
    D = np.full((T, S), NEG); B = np.zeros((T, S), dtype=int)
    D[0, 0] = E[0, 0]
    for t in range(1, T):
        for s in range(S):
            k, loop = states[s]
            best, arg = D[t - 1, s - 1] if s > 0 else NEG, s - 1
            if loop and D[t - 1, s] > best:
                best, arg = D[t - 1, s], s
            D[t, s] = best + E[k, t]; B[t, s] = arg
    s = S - 1; path = [s]
    for t in range(T - 1, 0, -1):
        s = B[t, s]; path.append(s)
    path = path[::-1]
    lab = [states[s][0] for s in path]
    out = []
    for k, (p, c) in enumerate(seq):
        idx = [t for t, l in enumerate(lab) if l == k]
        out.append((p, c, idx[0] * HOP / SR, (idx[-1] + 1) * HOP / SR))
    return out


def main():
    res = []
    for lid, text, kind, words in LINES:
        path = os.path.join(CACHE, lid + '_raw.wav')
        x = synth(text, path)
        # trim to 30 ms before first and after last frame above -45 dB
        e0, *_ = features(x)
        on = np.where(e0 > -45)[0]
        a = max(0, on[0] * HOP - 480); b = min(len(x), on[-1] * HOP + WIN + 480)
        x = x[a:b]
        e, hi, lo, v, spec = features(x)
        phones, wmap, stress_k = [], [], None
        for wi, (w, ph) in enumerate(words):
            for p in ph.split():
                st = p.startswith('*'); p = p.lstrip('*')
                c = CLS.get(p, 'vowel')
                if st: stress_k = len(phones)
                phones.append((p, c)); wmap.append(wi)
        al = align(e, hi, lo, v, phones)[1:-1]
        ph_out = [{'p': p, 'cls': c, 't0': round(t0, 3), 't1': round(t1, 3)} for p, c, t0, t1 in al]
        w_out = []
        for wi, (w, _) in enumerate(words):
            ps = [ph_out[k] for k in range(len(ph_out)) if wmap[k] == wi]
            w_out.append({'w': w, 't0': ps[0]['t0'], 't1': ps[-1]['t1']})
        np.save(os.path.join(CACHE, lid + '_feat.npy'), np.stack([e, hi, lo, v]))
        np.save(os.path.join(CACHE, lid + '_spec.npy'), spec.astype(np.float32))
        out = os.path.join(CACHE, lid + '.wav')
        with wave.open(out, 'w') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
        os.remove(path)
        res.append({'id': lid, 'text': text, 'kind': kind, 'dur': round(len(x) / SR, 3), 'words': w_out, 'phones': ph_out,
                    'stress_onset': ph_out[stress_k]['t0'], 'synth': 'flite (CMU Flite via ffmpeg libflite), voice slt'})
        print(lid, text, ' '.join(f"{p['p']}:{p['t0']:.2f}-{p['t1']:.2f}" for p in ph_out))
    json.dump(res, open(os.path.join(HERE, 'voice_lines.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
