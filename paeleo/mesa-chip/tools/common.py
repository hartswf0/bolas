"""Shared for PAE-09 only: the score, sound synthesis, the pixel-mask measurement of the four invariants, stills and the mux.
Nothing here draws: every swarm makes its own knight, its own Uncle Mesa, its own place."""
import json, os, subprocess, wave, math
import numpy as np
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
W, H, FPS = 960, 540, 24
SR = 44100

def score():
    return json.load(open(os.path.join(ROOT, 'score', 'glass-knight-score.json')))

def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def ev(sc, what): return next(e['t'] for e in sc['events'] if e['what'] == what)

def releases(sc, n, order):
    """Which of n pieces each shot frees. order: the swarm's own ordering of its pieces (e.g. shoulder first, then by distance).
    Returns list of (shot_index, t, paint, piece_ids). The fractions are the score's; which pieces, the swarm's."""
    out, k = [], 0
    for i, p in enumerate(sc['pieces']):
        m = n - k if p['fraction'] == 'all that remain' else int(round(p['fraction'] * n))
        out.append((i, p['t'], p['paint'], list(order[k:k + m]))); k += m
    return out

# ---------- sound ----------
def tl(sec): return np.zeros(int(sec * SR), np.float32)
def add(buf, t, x, gain=1.0):
    i = int(t * SR)
    if i >= len(buf): return
    x = x[:len(buf) - i]; buf[i:i + len(x)] += gain * x
def env(n, a=.005, r=.3):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4)); return e.astype(np.float32)
def tone(f, d, a=.005, r=.4, harm=(1,), detune=0.0):
    n = int(d * SR); t = np.arange(n) / SR; x = np.zeros(n, np.float32)
    for k, h in enumerate(harm): x += (h if isinstance(h, float) else 1 / (k + 1)) * np.sin(2 * np.pi * f * (k + 1) * (1 + detune * k) * t)
    return x * env(n, a, r)
def noise(d, rng, r=.1, lp=None):
    n = int(d * SR); x = rng.standard_normal(n).astype(np.float32)
    if lp:  # one-pole low pass
        a = math.exp(-2 * math.pi * lp / SR); y = np.empty_like(x); s = 0.0
        for i in range(n): s = a * s + (1 - a) * x[i]; y[i] = s
        x = y * 4
    return x * env(n, .001, r)
def chime(f, d=1.6, rng=None):
    """glass: inharmonic partials, fast attack, long ring"""
    n = int(d * SR); t = np.arange(n) / SR; x = np.zeros(n, np.float32)
    for k, (m, g, r) in enumerate([(1, 1, .9), (2.76, .5, .5), (5.4, .3, .25), (8.93, .15, .12)]):
        x += g * np.sin(2 * np.pi * f * m * t) * np.exp(-t / r)
    return x * np.minimum(1, t / .002)
def write_wav(path, buf):
    b = buf / max(1e-6, np.abs(buf).max()) * .89
    st = np.stack([b, b], 1) if b.ndim == 1 else b
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())

# ---------- measurement from pixel masks ----------
class Meter:
    """Each frame the swarm hands over its label mask (uint8, H x W, any scale) and its rendered RGB. Labels: 1 Uncle Mesa,
    2 the knight standing, 3 the canyon window's glass, 4 the knight's sword, 5 Uncle Mesa's gun, 6 the knight's face (visor),
    10 + i a piece freed by shot i. Everything in report() is measured from those pixels, not from the swarm's pose variables."""
    def __init__(self, sc): self.sc = sc; self.rows = []
    def frame(self, f, lab, rgb, skip=False):
        """skip=True: a frame that is not the master geography (an insert or a re-telling); recorded, never measured"""
        t = f / FPS; r = {'t': round(t, 4), 'f': f}
        if skip: r['skip'] = True; self.rows.append(r); return
        hl, wl = lab.shape; st = max(1, rgb.shape[0] // hl); small = rgb[::st, ::st][:hl, :wl].astype(np.float32)   # the same pixels the label was taken from (a resize samples one pixel off)
        def box(m):
            ys, xs = np.nonzero(m)
            if len(xs) < 3: return None
            return dict(cx=float(xs.mean() / wl), cy=float(ys.mean() / hl), top=float(ys.min() / hl), bot=float(ys.max() / hl), h=float((ys.max() - ys.min() + 1) / hl), n=int(len(xs)))
        r['mesa'] = box((lab == 1) | (lab == 5)); r['knight'] = box((lab == 2) | (lab == 4) | (lab == 6))
        r['sword'] = box(lab == 4); r['gun'] = box(lab == 5); r['face'] = box(lab == 6); w = box(lab == 3)
        if w is not None:
            ys, xs = np.nonzero(lab == 3); r['window'] = [float(xs.min() / wl), float(ys.min() / hl), float(xs.max() / wl), float(ys.max() / hl)]
        else: r['window'] = None
        pieces = []
        for i, p in enumerate(self.sc['pieces']):
            m = lab == 10 + i; n = int(m.sum())
            if n == 0: pieces.append(dict(n=0)); continue
            # the colour is held if the pixel's hue and saturation are the paint's, whatever light is on it (brightness normalized)
            c = np.array(hexrgb(p['paint']), np.float32); c /= c.max(); px = small[m]; mx = px.max(1, keepdims=True)
            d = np.abs(px / np.maximum(1, mx) - c).sum(1)
            pieces.append(dict(n=n, colour_ok=float(((d < .45) & (mx[:, 0] > 40)).mean())))
        r['pieces'] = pieces; self.rows.append(r)
    def report(self):
        sc, R = self.sc, [r for r in self.rows if not r.get('skip')]
        win = next((r['window'] for r in R if r['window']), None)
        kn = lambda r: r['knight']
        inside = lambda r: win[0] - .005 <= kn(r)['cx'] <= win[2] + .005 and win[1] - .005 <= kn(r)['cy'] <= win[3] + .005
        sh = ev(sc, 'shatter')
        pre = [r for r in R if r['t'] < 4.5 and kn(r)]; post = [r for r in R if 5.5 < r['t'] < sh and kn(r)]
        i2_pre = float(np.mean([inside(r) for r in pre])) if pre else 0.0
        i2_post = float(np.mean([not inside(r) for r in post])) if post else 0.0
        i2_nowhere = all(r['t'] >= 4.5 or not kn(r) or inside(r) for r in R)
        I2 = dict(ok=i2_pre > .97 and i2_post > .97 and i2_nowhere, window=win, inside_before_4_5=i2_pre, outside_after_5_5=i2_post, never_elsewhere_before=i2_nowhere)
        I3 = []
        for i, p in enumerate(sc['pieces']):
            after = [r for r in R if r['t'] >= p['t'] + .6]
            present = float(np.mean([r['pieces'][i]['n'] > 0 for r in after])) if after else 0
            col = [r['pieces'][i].get('colour_ok', 0) for r in after if r['pieces'][i]['n']]
            before = any(r['pieces'][i]['n'] > 0 for r in R if r['t'] < p['t'] - .05)
            cm = float(np.mean(col)) if col else 0.0
            I3.append(dict(shot=i + 1, t=p['t'], paint=p['paint'], present_to_end=present, colour_match=cm, last_frame_pixels=R[-1]['pieces'][i]['n'], not_before=not before, ok=present > .98 and cm > .6 and not before))
        def first(pred, t0, lo=.6):
            for r in R:
                if r['t'] >= t0 - lo and pred(r): return r['t']
            return None
        mh = float(np.median([r['mesa']['h'] for r in R if r['mesa'] and 7 < r['t'] < 9]))
        base_face = float(np.median([r['face']['cx'] - r['knight']['cx'] for r in R if r['face'] and r['knight'] and 1 < r['t'] < 2.5]))
        gunrel = lambda r: (r['gun']['cy'] - r['mesa']['top']) / max(1e-6, r['mesa']['h'])
        g0 = float(np.median([gunrel(r) for r in R if r['gun'] and r['mesa'] and 3.5 < r['t'] < 6]))
        found = {
            'turns_head': first(lambda r: r['face'] and r['knight'] and (r['face']['cx'] - r['knight']['cx']) < base_face - .003, 3.0),
            'steps_out': first(lambda r: kn(r) and not inside(r), 4.5),
            'draws': first(lambda r: r['t'] > 5 and r['sword'] is not None, 6.0),
            'raises_gun': first(lambda r: r['gun'] and r['mesa'] and gunrel(r) < g0 - .1, 6.5),
            'knocked_down': first(lambda r: r['mesa'] and r['mesa']['h'] < .62 * mh, 12.2),
            'gets_up': first(lambda r: r['t'] > 13 and r['mesa'] and r['mesa']['h'] > .85 * mh, 14.0),
            'shatter': first(lambda r: r['t'] > 19 and not kn(r), 19.5),
            'sits': first(lambda r: r['t'] > 21 and r['mesa'] and r['mesa']['h'] < .8 * mh, 22.0),
        }
        for i, p in enumerate(sc['pieces'][:5]): found[f'hit_{i + 1}'] = first(lambda r, i=i: r['pieces'][i]['n'] > 0, p['t'])
        I1 = []
        for e in sc['events']:
            ft = found.get(e['what'])
            I1.append(dict(t=e['t'], what=e['what'], found_at=ft, dt=None if ft is None else round(ft - e['t'], 3), ok=ft is not None and abs(ft - e['t']) <= .25))
        rows = [(r, sc['frames'][r['f']]) for r in R if r['mesa'] and kn(r) and 5.5 < r['t'] < sh]
        a = np.array([abs(r['knight']['cx'] - r['mesa']['cx']) for r, _ in rows]); b = np.array([fr['distance'] for _, fr in rows])
        na = (a - a.min()) / max(1e-6, np.ptp(a)); nb = (b - b.min()) / max(1e-6, np.ptp(b)); err = np.abs(na - nb)
        I4 = dict(ok=float((err <= .15).mean()) > .9, within_15pct=float((err <= .15).mean()), r=float(np.corrcoef(a, b)[0, 1]), frames=len(rows))
        return dict(measured_frames=len(R), skipped_frames=len(self.rows) - len(R), I1=dict(ok=all(x['ok'] for x in I1), events=I1), I2=I2, I3=dict(ok=all(x['ok'] for x in I3), pieces=I3), I4=I4)

# ---------- film ----------
class Film:
    def __init__(self, path): self.path = path; self.p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', path + '.v.mp4'], stdin=subprocess.PIPE)
    def put(self, rgb): self.p.stdin.write(np.ascontiguousarray(rgb, np.uint8).tobytes())
    def close(self, wav):
        self.p.stdin.close(); self.p.wait()
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', self.path + '.v.mp4', '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', self.path], check=True)
        os.remove(self.path + '.v.mp4')

STILL_T = [2.0, 3.2, 5.0, 6.8, 9.9, 12.5, 14.2, 16.4, 18.4, 20.0, 22.8]
def contact(stills_dir, out, cols=4):
    fs = sorted(f for f in os.listdir(stills_dir) if f.startswith('still_'))
    ims = [Image.open(os.path.join(stills_dir, f)).resize((320, 180)) for f in fs]
    rows = (len(ims) + cols - 1) // cols; sheet = Image.new('RGB', (cols * 320, rows * 180))
    for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 320, (i // cols) * 180))
    sheet.save(out, quality=88)
