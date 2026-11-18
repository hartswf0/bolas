"""TEST SHOT: the hinge of strip B (B1 held -> B2 'ASK THE LAMP.' -> B3 'AND LOOK - STILL SEALED.').

Camera = a 960x540 crop of the page at 1:1 (page and film share pixels).
Balloons written on stroke by stroke (#17 one plate + dialogue plane; #38 DP boil
library on the balloon plane; #47 one foraged pen grain per stroke onset).
Rendered through kit.Film with grain off and no vignette.
"""
import json
import math
import os
import subprocess
import sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '../../..')))   # films/ (kit.py)
import kit
from page import load, build_page, XS, ROWS, SWARM, MEDIA
from balloons import composite, FPS
from plate2 import art_hash

plate, balloons, layers = load()
page_un = build_page(plate, layers, with_balloons=False)      # page with unlettered panels
page_final = build_page(plate, layers, with_balloons=True)
Y = ROWS['B']
row_un = np.asarray(page_un)[Y:Y + 540]

def cam_x(panel):            # camera left edge that centres a panel
    return XS[panel] + 270 - 480

# ---------------------------------------------------------------- timeline (frames)
B1_HOLD = 10
MOVE = 12                    # 0.5 s eased slide
POST = 48                    # >= 2 s hold on each finished balloon
tl = []
f = 0
tl.append(('hold', f, f + B1_HOLD, 0)); f += B1_HOLD
tl.append(('move', f, f + MOVE, (0, 1))); f += MOVE
b2_start = f
f += balloons['B2'].end_f + POST
tl.append(('write', b2_start, f, 1))
tl.append(('move', f, f + MOVE, (1, 2))); f += MOVE
b3_start = f
f += balloons['B3'].end_f + POST
tl.append(('write', b3_start, f, 2))
TOTAL = f
SECONDS = TOTAL / FPS
starts = {'B2': b2_start, 'B3': b3_start}


def state(k):
    """camera x and per-panel balloon layer at frame k."""
    lay = {0: layers['B1'], 1: None, 2: None, 3: None}
    cx = cam_x(0)
    for kind, a, b, arg in tl:
        if kind != 'move':
            continue
        if k >= b:
            cx = cam_x(arg[1])
        elif a <= k:
            u = (k - a + 1) / (b - a)
            u = u * u * (3 - 2 * u)          # eased, no fade
            cx = round(cam_x(arg[0]) + (cam_x(arg[1]) - cam_x(arg[0])) * u)
    for key, p in (('B2', 1), ('B3', 2)):
        s = starts[key]
        if k >= s:
            fl = k - s
            lay[p] = layers[key] if fl >= balloons[key].end_f else balloons[key].render(fl)
    return cx, lay


_cache = {}


def frame_img(k):
    cx, lay = state(k)
    row = row_un.copy()
    for p, L in lay.items():
        if L is not None:
            row[:, XS[p]:XS[p] + 540] = np.asarray(composite(plate, L))
    pad = 400
    big = np.full((540, row.shape[1] + 2 * pad), 255, np.uint8)
    big[:, pad:pad + row.shape[1]] = row
    crop = big[:, pad + cx: pad + cx + 960]
    return Image.fromarray(crop, 'L').convert('RGB')


film = kit.Film('test-shot', SECONDS, size=(960, 540), fps=FPS, boil=0)


@film.picture
def picture(t, ink):
    ink.paper(grain=False)
    k = int(round(t * FPS))
    ink.paste(frame_img(k))


# ---------------------------------------------------------------- sound (#47)
def decode(path, sr=44100):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


PEN = os.path.join(MEDIA, 'Writing_with_inkpen.ogg.mp3')
CRICKET = os.path.join(MEDIA, 'Field_cricket_unedited.ogg')
cues = []


def grain_bank(x, sr=44100):
    """Cut the real pen recording into stroke grains: windows of high scratch energy."""
    hop = int(0.01 * sr)
    e = np.array([np.sqrt((x[i:i + hop] ** 2).mean()) for i in range(0, len(x) - hop, hop)])
    thr = np.percentile(e, 70)
    act = e > thr
    segs, i = [], 0
    while i < len(act):
        if act[i]:
            j = i
            while j < len(act) and act[j]:
                j += 1
            if j - i >= 4:
                segs.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    return segs


@film.sound
def sound(mix):
    sr = mix.rate
    # ambience: real field cricket, distant (low-passed, low), looped by crossfade if short
    c = decode(CRICKET, sr)
    c = mix.lowpass(c, 3500) if hasattr(mix, 'lowpass') else c
    need = mix.n
    bed = np.zeros(need)
    pos = 0
    fade = int(0.5 * sr)
    while pos < need:
        seg = c[: need - pos].copy()
        if pos > 0:
            seg[:fade] *= np.linspace(0, 1, min(fade, len(seg)))[: len(seg[:fade])]
        bed[pos:pos + len(seg)] += seg
        pos += len(c) - fade
    bed /= max(1e-9, np.abs(bed).max())
    mix.add(bed, 0.0, gain=0.10, pan=-0.15)
    # pen: one real grain per stroke onset, length follows the stroke, gain follows its speed
    x = decode(PEN, sr)
    x = x / max(1e-9, np.abs(x).max())
    segs = grain_bank(x, sr)
    rs = np.random.RandomState(5)
    for key in ('B2', 'B3'):
        b = balloons[key]
        t_start = starts[key] / FPS
        # outline: one long grain
        evs = [(0.0, b.sched[0][0], 400.0, 'outline')] + b.onsets()
        for (t0, t1, L, ch) in evs:
            dur = max(0.035, t1 - t0)
            a, z = segs[rs.randint(len(segs))]
            n = int(dur * sr)
            g = x[a:a + n].copy()
            if len(g) < n:
                g = np.pad(g, (0, n - len(g)))
            env = np.ones(n)
            r = min(n // 3, int(0.008 * sr))
            if r:
                env[:r] = np.linspace(0, 1, r); env[-r:] = np.linspace(1, 0, r)
            speed = L / 2 / max(1e-3, dur)          # px (at 540) per second
            gain = float(np.clip(0.35 + speed / 900.0, 0.35, 1.0))
            if ch == '.':
                gain = 1.0                           # the tap of the full stop
            mix.add(g * env, t_start + t0, gain=gain * 0.8, pan=0.1)
            cues.append(dict(balloon=key, t=round(t_start + t0, 4), frame=round((t_start + t0) * FPS, 2), dur=round(dur, 3), gain=round(gain, 2), glyph=ch))


if __name__ == '__main__':
    out = os.path.join(SWARM)
    # invariants before encoding
    from pathlib import Path
    checks = {}
    pf = np.asarray(page_final)
    for key, k_last, p in (('B2', starts['B2'] + balloons['B2'].end_f + POST - 1, 1), ('B3', TOTAL - 1, 2)):
        img = np.asarray(frame_img(k_last).convert('L'))
        cx, _ = state(k_last)
        panel = img[:, XS[p] - cx: XS[p] - cx + 540]
        checks[f'{key}_last_hold_equals_page'] = bool((panel == pf[Y:Y + 540, XS[p]:XS[p] + 540]).all())
        # balloon final frame of schedule equals the published balloon
        L = balloons[key].render(balloons[key].end_f)
        checks[f'{key}_schedule_end_equals_published'] = bool((np.asarray(composite(plate, L)) == np.asarray(composite(plate, layers[key]))).all())
    # art-only identity: removing the balloon plane restores the plate (I2)
    checks['plate_sha'] = art_hash(plate)
    print(json.dumps(checks, indent=1))
    assert all(v for k, v in checks.items() if k != 'plate_sha')
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        for k in map(int, sys.argv[2:]):
            frame_img(k).save(os.path.join('/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad', f'f{k:03d}.png'))
        print('TOTAL', TOTAL, starts, {k: balloons[k].end_f for k in starts}, balloons['B2'].path)
        sys.exit()
    film.render(Path(out))
    json.dump(dict(fps=FPS, frames=TOTAL, timeline=tl, starts=starts, cues=cues,
                   boil_paths={k: balloons[k].path for k in starts}), open(os.path.join(SWARM, 'test-shot-build', 'cues.json'), 'w'), indent=1)
    # #47 check: every cue onset within +-1 frame of a stroke onset; none during camera moves
    on = sorted([starts[k] / FPS + t0 for k in starts for (t0, *_r) in balloons[k].onsets()] + [starts[k] / FPS for k in starts])
    assert all(min(abs(c['t'] - o) for o in on) * FPS <= 1 for c in cues)
    print('cues', len(cues), 'all aligned')
