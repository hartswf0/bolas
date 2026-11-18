"""TEST SHOT: start of cut B (plan 0:36.25-0:43.25 + its lead-in), 10.0 s, 240 f @ 24.

f0-23   notebook, on twos: card 05 finishes its slide into slot 1, sets down
        (spring overshoot, shadow shrinks); red pencil strikes the ink '5'
        (4 f) and writes '1' stroke by stroke (8 f).
f24-41  rostrum push into slot 1 until the frame equals asset 05 W0.
f42-161 B1 event 1: asset 05, src 0..59 at speed 0.5 (each frame twice).
f162-209 B1 event 2: asset 04, src 0..47.
f210-239 B1 event 3: asset 02, src 24..53 (first 30 of its 72 f).
Run: python3 -I shot.py   (renders with films/kit.py, unedited)
"""
import sys, math, json, hashlib, random, wave
from pathlib import Path
sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kit
from rig import *

MEDIA = Path('/home/user/bolas/paeleo/scion/oulipo/films/sources/la-machine-a-tuer-le-temps/test-shot')
FPS = 24; N = 240
T_PUSH0, T_PUSH1, T_05, T_04, T_02 = 24, 41, 42, 162, 210

# ---------------------------------------------------------------- scene data
TABLE = build_table()
# cut-A state at this moment of S5: 01 lifted away (parked at the bottom gutter,
# out of frame), slots 2,3,4 still hold 02,03,04 with their A numbers.
REST = {2: '02', 3: '03', 4: '04'}
CARDS = {k: build_card(k, str(s), seed=40 + s) for s, k in REST.items()}
CARD05, NUM05 = build_card('05', '5', seed=45)
BASE = TABLE.copy()
for s, k in REST.items():
    cx, cy = SLOT_C[s]
    # rest state: nearly flat contact shadow (<= 3 px)
    sh = Image.new('L', (CW + 40, CH + 40), 0)
    ImageDraw.Draw(sh).rectangle([20 + 1, 20 + 2, 20 + CW + 1, 20 + CH + 2], fill=60)
    sh = sh.filter(ImageFilter.GaussianBlur(1.5))
    BASE.paste(Image.new('RGB', sh.size, (40, 32, 24)), (cx - 20, cy - 20), sh)
    BASE.paste(CARDS[k][0].convert('RGB'), (cx, cy))

# event stream (SCION 40): frame-indexed, consumed by the sound below
EVENTS = [dict(f=-10, ev='lift', card='05', from_slot=5),
          dict(f=-10, ev='travel', card='05', to_slot=1),
          dict(f=6, ev='setdown', card='05', slot=1),
          dict(f=10, ev='strike', card='05', mark='5', frames=4),
          dict(f=14, ev='write', card='05', mark='1', frames=8, tool='red pencil'),
          dict(f=24, ev='push', target='05 W0', frames=18),
          dict(f=42, ev='cut', asset='05', src=[0, 59], speed=0.5),
          dict(f=162, ev='cut', asset='04', src=[0, 47], speed=1),
          dict(f=210, ev='cut', asset='02', src=[24, 53], speed=1)]


def sstep(u):
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)


def card05_state(f):
    """(x, y, h) of card 05 at drawing time f (on twos). Translation only."""
    fq = 2 * (f // 2)
    x5, y5 = SLOT_C[5]; x1, y1 = SLOT_C[1]
    TD = 6; T0 = -10
    if fq < TD:
        u = (fq - T0) / (TD - T0)
        e = 1 - (1 - u) ** 2.2                     # decelerating hand
        x = x5 + (x1 - x5) * e
        y = y5 + (y1 - y5) * e - 16 * math.sin(math.pi * u)
        r = random.Random(fq)
        x += r.uniform(-1.5, 1.5); y += r.uniform(-1.2, 1.2)   # hand irregularity
    else:
        t = fq - TD                                 # damped spring, SCION 41
        x = x1 - 3.0 * math.exp(-0.32 * t) * math.sin(0.62 * t + 0.35) / 0.95
        y = y1 + 0.8 * math.exp(-0.4 * t) * math.sin(0.62 * t)
        if t >= 14:
            x, y = x1, y1                           # energy fully decayed
    h = 1 - sstep((fq - 2) / 6)                     # lift height 1 -> 0 over f2..f8
    return x, y, h


STRIKE = None; ONE = None


def red_marks(card_rgba, f):
    fq = 2 * (f // 2)
    img = card_rgba.convert('RGB')
    nx, ny = NUM05
    fs = min(1, max(0, (fq - 9) / 4))
    if fs > 0:
        r = random.Random(77)
        pts = [(nx - 8, ny + 52), (nx + 14, ny + 30), (nx + 46, ny - 2)]
        pts = [(x + r.uniform(-1.5, 1.5), y + r.uniform(-1.5, 1.5)) for x, y in pts]
        m, off = draw_path([catmull(pts)], fs, 3.6, 11, pencil=True)
        ink_on(img, m, off, RED_CORE)
    fw = min(1, max(0, (fq - 13) / 8))
    if fw > 0:
        g = glyph_path('1', nx + 58, ny - 6, 52, seed=913)
        m, off = draw_path(g, fw, 3.8, 12, pencil=True)
        ink_on(img, m, off, RED_CORE)
    return img.convert('RGBA')


def print_table_rect(k, cx, cy):
    x0, y0, x1, y1 = print_rect_local(k)
    return (cx + x0, cy + y0, cx + x1, cy + y1)


def w0_table_rect(cx, cy):
    p = POOL['05']; c = p['crop']; R = print_table_rect('05', cx, cy)
    sx = (R[2] - R[0]) / (c[2] - c[0]); sy = (R[3] - R[1]) / (c[3] - c[1])
    W = p['W0']
    return (R[0] + (W[0] - c[0]) * sx, R[1] + (W[1] - c[1]) * sy, R[0] + (W[2] - c[0]) * sx, R[1] + (W[3] - c[1]) * sy)


V0 = (40.0, 76.0, 1360.0, 76.0 + 1320 * 9 / 16)
V1 = w0_table_rect(*SLOT_C[1])


def view(f):
    jit = 0.0
    if f < T_PUSH0:
        u = 0.0
    else:
        u = (f - T_PUSH0) / (T_PUSH1 - T_PUSH0)
        u = 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
    w0, w1 = V0[2] - V0[0], V1[2] - V1[0]
    w = w0 * (w1 / w0) ** u
    c0 = ((V0[0] + V0[2]) / 2, (V0[1] + V0[3]) / 2); c1 = ((V1[0] + V1[2]) / 2, (V1[1] + V1[3]) / 2)
    # keep the target print still in frame while zooming: interpolate in the
    # zoom-normalised domain so the push lands straight on the print
    k = (w0 - w) / (w0 - w1) if w0 != w1 else 1
    cx = c0[0] + (c1[0] - c0[0]) * k; cy = c0[1] + (c1[1] - c0[1]) * k
    h = w * 9 / 16
    # stop-motion table jitter, per drawing, +-0.6 output px, gone by push end
    d = (2 * (f // 2)) // 2
    r = random.Random(1000 + d); amp = 0.6 * (1 - u) * (w / OW)
    jx, jy = r.uniform(-amp, amp), r.uniform(-amp, amp)
    if f >= T_PUSH1:
        return V1
    return (cx - w / 2 + jx, cy - h / 2 + jy, cx + w / 2 + jx, cy + h / 2 + jy)


def put_print(out, k, R, V):
    """Re-sample the toned print from source at the current camera scale."""
    im, s = toned(k); c = POOL[k]['crop']
    S = OW / (V[2] - V[0])
    o = [(R[0] - V[0]) * S, (R[1] - V[1]) * S, (R[2] - V[0]) * S, (R[3] - V[1]) * S]
    ox0, oy0 = max(0, math.ceil(o[0])), max(0, math.ceil(o[1]))
    ox1, oy1 = min(OW, math.floor(o[2])), min(OH, math.floor(o[3]))
    if ox1 <= ox0 or oy1 <= oy0:
        return
    fx = im.width / (o[2] - o[0]); fy = im.height / (o[3] - o[1])
    box = ((ox0 - o[0]) * fx, (oy0 - o[1]) * fy, (ox1 - o[0]) * fx, (oy1 - o[1]) * fy)
    out.paste(im.transform((ox1 - ox0, oy1 - oy0), Image.EXTENT, box, Image.BICUBIC), (ox0, oy0))


def notebook_frame(f):
    V = view(f)
    if f == T_PUSH1:      # last push frame lands exactly on asset 05 frame 0
        return asset_frame('05', 0), V
    out = BASE.transform((OW, OH), Image.EXTENT, V, Image.BICUBIC)
    for s, k in REST.items():
        put_print(out, k, print_table_rect(k, *SLOT_C[s]), V)
    # moving layer: card 05 + its lift shadow
    x, y, h = card05_state(f)
    M = 80
    patch = Image.new('RGBA', (CW + 2 * M, CH + 2 * M), (0, 0, 0, 0))
    sh = Image.new('L', patch.size, 0)
    offx, offy = 1 + 12 * h, 2 + 16 * h
    ImageDraw.Draw(sh).rectangle([M + offx, M + offy, M + offx + CW, M + offy + CH], fill=int(60 + 55 * h))
    sh = sh.filter(ImageFilter.GaussianBlur(1.5 + 11 * h))
    patch.paste(Image.new('RGBA', patch.size, (40, 32, 24, 255)), (0, 0), sh)
    card = red_marks(CARD05, f)
    patch.alpha_composite(card, (M, M))
    px0, py0 = x - M, y - M
    lay = patch.transform((OW, OH), Image.EXTENT, (V[0] - px0, V[1] - py0, V[2] - px0, V[3] - py0), Image.BICUBIC)
    out = out.convert('RGBA'); out.alpha_composite(lay); out = out.convert('RGB')
    put_print(out, '05', print_table_rect('05', x, y), V)
    return out, V


def segment(f):
    if f <= T_PUSH1:
        return ('notebook', None, None)
    if f < T_04:
        return ('cut', '05', (f - T_05) // 2)
    if f < T_02:
        return ('cut', '04', f - T_04)
    return ('cut', '02', 24 + f - T_02)


LEDGER = {}


def picture(t, ink):
    f = int(round(t * FPS))
    ink._grain = False                    # no kit grain on prints or notebook
    seg, k, src = segment(f)
    if seg == 'notebook':
        img, V = notebook_frame(f)
        x, y, h = card05_state(f)
        LEDGER[f] = dict(frame=f, segment='notebook', card05=[round(x, 3), round(y, 3)], lift=round(h, 3),
                         view=[round(v, 3) for v in V])
    else:
        img = asset_frame(k, src)
        LEDGER[f] = dict(frame=f, segment='cut', asset_id=k, src_frame=src,
                         md5=hashlib.md5(img.tobytes()).hexdigest())
    ink.paste(img, (0, 0))


# ------------------------------------------------------------------ sound ---
def load_wav(path, rate=44100):
    with wave.open(str(path)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(1)
    return a


def sound(mix):
    sec = lambda fr: fr / FPS
    r = mix.rate
    bed_path = MEDIA / 'aud' / 'bed.wav'
    # T0 room (handmade): low air + 50 Hz hum, very quiet, throughout
    mix.room(0, 10.0, gain=0.010)
    # station bed T1 (foraged if present): rises on the push, ducked -9 dB in B
    n = int(10.0 * r)
    if bed_path.exists():                 # FORAGED (see ledger)
        bed = np.resize(load_wav(bed_path), n)
    else:                                 # HANDMADE fallback: concourse murmur + rumble
        sub = kit.Mix(10.0, seed=5)
        sub.murmur(0, 10.0, gain=0.5, pitch=115)
        sub.add(sub.lowpass(sub.noise(10.0, 'brown'), 180), 0, gain=0.6)
        sub.reverb(0.35, 1.4)
        bed = (sub.L + sub.R) / 2; bed = bed / (np.abs(bed).max() + 1e-9)
    if True:
        t = np.arange(n) / r
        env = np.interp(t, [0, sec(T_PUSH0), sec(T_PUSH1), sec(T_05) + 0.3, 6.4, 6.75, 10.0],
                        [0.05, 0.08, 0.30, 0.106, 0.106, 0.106, 0.106])
        # during the stare the bed thins further toward the declared silence
        env *= np.interp(t, [0, 3.8, 4.2, 6.3, 6.6, 10], [1, 1, 0.45, 0.45, 1, 1])
        mix.add(bed * env, 0, gain=1.0)
    # wall clock tick (handmade click) : steady, then slows over the stare and stops
    ticks = [0.12, 1.12, 2.12, 3.25, 4.0]
    for i, tk in enumerate(ticks):
        mix.click(tk, gain=0.16 * (0.8 if i >= 3 else 1), bright=5200, seconds=0.025)
        mix.click(tk + 0.012, gain=0.05, bright=1600, seconds=0.04)
    # declared silence of the tick: 4.0 .. 6.5 s (inside the 05 hold)
    # T2 foley, handmade from the event stream
    # slide hiss of the card on the page until set-down
    n = int(sec(6) * r) + 1
    hiss = mix.band(mix.noise(n / r + 0.05), 900, 6000)[:n] * np.linspace(0.6, 1, n)
    mix.add(hiss, 0, gain=0.035)
    mix.click(sec(6), gain=0.28, bright=2600, seconds=0.05)        # card sets down
    mix.thud(sec(6), freq=140, gain=0.08, seconds=0.12)
    for ev, f0, nf in (('strike', 10, 4), ('write', 14, 8)):        # pencil on paper
        dur = nf / FPS
        x = mix.band(mix.noise(dur + 0.05), 1800, 9000)[:int(dur * r)]
        e = np.abs(np.sin(np.linspace(0, math.pi * (1 if ev == 'strike' else 3), len(x)))) ** 0.6
        e *= 0.6 + 0.4 * (mix.rs.random(len(x)) > 0.3)
        mix.add(x * e, sec(f0), gain=0.06)
    # pre-lapped door latch, 6 f before the 05 -> 04 cut (handmade)
    tl = sec(T_04 - 6)
    mix.click(tl, gain=0.30, bright=3500, seconds=0.03)
    mix.click(tl + 0.06, gain=0.22, bright=2200, seconds=0.05)
    mix.thud(tl + 0.06, freq=95, gain=0.22, seconds=0.3)


film = kit.Film('test-shot', seconds=10.0, size=(OW, OH), fps=FPS, boil=0, wobble=0)
film.picture(picture)
film.sound(sound)
film.poster_at = 0.6

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--frames':
        out = MEDIA / 'frames'; out.mkdir(exist_ok=True)
        for f in [int(x) for x in sys.argv[2:]]:
            film.frame(f).save(out / f'{f:03d}.png')
        print('frames ->', out)
    else:
        film.render(out_dir=MEDIA)
        json.dump(dict(shot='test-shot', fps=FPS, frames=N, events=EVENTS,
                       ledger=[LEDGER[k] for k in sorted(LEDGER)]),
                  open(MEDIA / 'test-shot-ledger-frames.json', 'w'), indent=1)
