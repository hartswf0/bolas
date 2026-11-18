"""U3 sound: decode the foraged recordings (ffmpeg only) and cut the grain bank.

Inputs (foraged, untrusted; decoded with ffmpeg, never executed):
  sound/raw/ or test-shot/ : Writing_with_inkpen.ogg.mp3 (PD, pdsounds.org via Commons)
                             night ambience (Grillenzirpen Moedling, CC BY-SA 4.0; fallback Field cricket, CC BY-SA 3.0)
Outputs in films/sources/<slug>/sound/:
  pen-44k.wav, ambience-44k.wav   decoded mono float -> 16-bit wav
  grains/g00..gNN.wav             real scratch grains, cut at detected stroke onsets
  taps/t00..wav                   real pen-down transients (sharpest onsets in the pen recording)
  bank.json                       grain/tap table with source offsets
"""
import json, os, subprocess, sys, wave
import numpy as np

SR = 44100
ROOT = '/home/user/bolas/paeleo/scion/oulipo/films/sources/moins-dun-quart-de-seconde-pour-vivre'
OUT = os.path.join(ROOT, 'sound')
PEN = os.path.join(OUT, 'raw', 'Writing_with_inkpen.ogg.mp3')   # copy of the test-shot download
AMB_CANDIDATES = [os.path.join(OUT, 'raw', 'grillenzirpen_moedling.ogg.mp3'),
                  os.path.join(OUT, 'raw', 'night_original_format.wav'),
                  os.path.join(ROOT, 'test-shot', 'Field_cricket_unedited.ogg')]


def decode(path, sr=SR):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def band(x, lo, hi, sr=SR):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    w = np.ones_like(f)
    if lo > 0:
        w *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)   # 4th-order-ish high-pass, no ringing edge
    if hi:
        w *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * w, len(x))


def write_wav(path, x, sr=SR):
    y = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((y * 32767).astype('<i2').tobytes())


def envelope(x, hop):
    n = len(x) // hop
    return np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-20)


def cut_bank(x):
    """Grains: contiguous runs of scratch energy (5 ms hop) above a floor; onset trimmed to the first
    hop over threshold, so a grain's sample 0 IS the pen touching down."""
    hop = int(0.005 * SR)
    e = envelope(x, hop)
    floor = np.percentile(e, 30)
    thr = floor * 2.8
    act = e > thr
    # close tiny gaps (<=15 ms) inside a scratch
    for i in range(1, len(act) - 3):
        if not act[i] and act[i - 1] and act[i + 1:i + 4].any():
            act[i] = True
    grains, i = [], 0
    while i < len(act):
        if act[i]:
            j = i
            while j < len(act) and act[j]:
                j += 1
            dur = (j - i) * hop / SR
            if dur >= 0.04:
                seg_e = e[i:j]
                grains.append(dict(a=i * hop, z=j * hop, dur=round(dur, 3), peak_db=round(float(20 * np.log10(seg_e.max())), 1),
                                   rms_db=round(float(20 * np.log10(np.sqrt((seg_e ** 2).mean()))), 1)))
            i = j
        else:
            i += 1
    # taps: sharpest onsets (energy jump over 1 hop), short
    jump = np.r_[0, np.diff(np.log(e))]
    idx = np.argsort(-jump)
    taps, used = [], []
    for k in idx:
        if len(taps) >= 6:
            break
        if e[k] < thr or any(abs(k - u) < 40 for u in used):
            continue
        used.append(k)
        taps.append(dict(a=int(k * hop - hop), jump_db=round(float(jump[k] * 8.686), 1)))
    return grains, taps, dict(floor_db=round(float(20 * np.log10(floor)), 1), thr_db=round(float(20 * np.log10(thr)), 1))


def chorus_only(x, hop_s=0.5, drop_db=20.0, min_keep_s=2.5, xf_s=1.0):
    hop = int(hop_s * SR)
    e = 20 * np.log10(envelope(x, hop))
    ok = e > np.median(e) - drop_db
    spans, i = [], 0
    while i < len(ok):
        if ok[i]:
            j = i
            while j < len(ok) and ok[j]:
                j += 1
            if (j - i) * hop_s >= min_keep_s:
                spans.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    xf = int(xf_s * SR)
    w = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2
    out = x[spans[0][0]:spans[0][1]].copy()
    for a, z in spans[1:]:
        seg = x[a:z].copy()
        out[-xf:] *= np.sqrt(w[::-1]); seg[:xf] *= np.sqrt(w)
        out = np.concatenate([out[:-xf], out[-xf:] + seg[:xf], seg[xf:]])
    return out, [[round(a / SR, 2), round(z / SR, 2)] for a, z in spans]


def main():
    os.makedirs(os.path.join(OUT, 'grains'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'taps'), exist_ok=True)
    pen = decode(PEN)
    pen = band(pen, 350, 14000)          # remove desk/handling rumble below the scratch band; nothing added
    pen /= np.abs(pen).max()
    write_wav(os.path.join(OUT, 'pen-44k.wav'), pen * 0.9)
    grains, taps, lv = cut_bank(pen)
    for k, g in enumerate(grains):
        write_wav(os.path.join(OUT, 'grains', f'g{k:02d}.wav'), pen[g['a']:g['z']])
        g['file'] = f'grains/g{k:02d}.wav'
    tl = int(0.09 * SR)
    for k, t in enumerate(taps):
        s = pen[max(0, t['a']):t['a'] + tl].copy()
        s *= np.exp(-np.arange(len(s)) / (0.018 * SR))      # pen-lift tap: the real transient, shortened
        write_wav(os.path.join(OUT, 'taps', f't{k:02d}.wav'), s / max(1e-9, np.abs(s).max()) * 0.9)
        t['file'] = f'taps/t{k:02d}.wav'
    amb_src = next(p for p in AMB_CANDIDATES if os.path.exists(p) and os.path.getsize(p) > 10000)
    amb = decode(amb_src)
    amb = band(amb, 150, 12000)
    amb, kept = chorus_only(amb)
    amb /= np.abs(amb).max()
    write_wav(os.path.join(OUT, 'ambience-44k.wav'), amb * 0.9)
    bank = dict(sr=SR, pen_source=PEN, pen_len_s=round(len(pen) / SR, 3), pen_filter='high-pass 350 Hz / low-pass 14 kHz (rumble removal only)',
                levels=lv, grains=grains, taps=taps, ambience_source=amb_src, ambience_len_s=round(len(amb) / SR, 3),
                ambience_kept_spans_s=kept,
                ambience_edit='the chorus falls almost silent for 3-5 s three times in the recording; those deep gaps are cut and the kept spans joined with 1 s equal-power crossfades, so the bed never drops out (A3 must be heard as night, not as a dropout)',
                ambience_filter='high-pass 150 Hz / low-pass 12 kHz (distance: pen is close, crickets far)')
    json.dump(bank, open(os.path.join(OUT, 'bank.json'), 'w'), indent=1)
    print(len(grains), 'grains', 'durs', sorted(g['dur'] for g in grains)[:5], '...', sorted(g['dur'] for g in grains)[-5:], len(taps), 'taps', lv, 'amb', amb_src)


if __name__ == '__main__':
    main()
