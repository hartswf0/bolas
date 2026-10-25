"""SCION-27 · reproducibility tester: measure the dog from its own render. python3 build/measure.py
Reads the DogMatte pass (build/cache/matte/*.png: the same <Dog> component as the film, same camera and wall clipping,
body green, skull blue, muzzle red) and writes ../trace.json: per scene frame the dog's screen position, which way its
muzzle points, its height, whether its head is below the line of its back, and a state read from those measurements
(not copied from the score). Choice onsets are the first frame of each measured change, walked back to where the
movement that makes it begins."""
import glob, json, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(FOLDER, '..', 'score', 'threshold-score.json')))
files = sorted(glob.glob(os.path.join(HERE, 'cache/matte/*.png')))
assert len(files) == 768, len(files)
rows = []
for i, fn in enumerate(files):
    a = np.asarray(Image.open(fn).convert('RGB')).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    G = (g > 110) & (g > r + 40) & (g > b + 40); B = (b > 110) & (b > r + 40) & (b > g + 40); Rm = (r > 110) & (r > g + 40) & (r > b + 40)
    allm = G | B | Rm
    ys, xs = np.nonzero(allm)
    def c(m):
        yy, xx = np.nonzero(m); return (float(xx.mean()), float(yy.mean()), int(len(xx))) if len(xx) else (None, None, 0)
    gx, gy, gn = c(G); bx, by, bn = c(B); rx, ry, rn = c(Rm)
    gys = np.nonzero(G)[0]
    rows.append(dict(x=float(xs.mean()), y=float(ys.mean()), top=int(ys.min()), bottom=int(ys.max()), h=int(ys.max() - ys.min()),
                     skull=(bx, by), muzzle=(rx, ry), rn=rn, bn=bn, back_top=int(np.percentile(gys, 2)) if len(gys) else None,
                     head_top=int(np.nonzero(B | Rm)[0].min()) if (bn + rn) else None))

n = len(rows)
x = np.array([r['x'] for r in rows]); h = np.array([r['h'] for r in rows], float)
# muzzle direction on screen (angle of skull→muzzle), facing: +1 muzzle toward the door (screen left), −1 away
ang = np.zeros(n); facing = np.zeros(n, int); last = 1
for i, r in enumerate(rows):
    (bx, by), (rx, ry) = r['skull'], r['muzzle']
    if bx is not None and rx is not None and r['rn'] > 15:
        dx, dy = rx - bx, ry - by; ang[i] = np.degrees(np.arctan2(dy, dx))
        if abs(dx) > 1.0: last = 1 if dx < 0 else -1
    else:
        ang[i] = ang[i - 1] if i else 180
    facing[i] = last
k = np.ones(5) / 5
vx = np.convolve(np.gradient(x), k, mode='same')
stand_h = np.median(h[:20])
lying = h < 0.62 * stand_h
head_low = np.array([(r['head_top'] is not None and r['back_top'] is not None and r['head_top'] > r['back_top']) for r in rows])
V0 = 0.6   # px/frame: the dog is travelling
state = []
for i in range(n):
    if facing[i] < 0: s = 'refuse'
    elif lying[i]: s = 'lie_down'
    elif vx[i] < -V0: s = 'approach'
    elif vx[i] > V0 and head_low[i]: s = 'retreat'
    else: s = 'watch'
    state.append(s)

# onsets: walk each change back to where the movement that produces it starts
dang = np.abs(np.diff(np.unwrap(np.radians(ang)), prepend=0)) * 180 / np.pi
dh = np.gradient(h)
def walk_back(i, active):
    j = i
    while j > 0 and active(j - 1): j -= 1
    return j
changes = [i for i in range(1, n) if state[i] != state[i - 1]]
for i in changes:
    a, b = state[i - 1], state[i]
    if b == 'refuse' or (a == 'refuse' and b != 'refuse'):
        j = walk_back(i, lambda q: dang[q] > 2.5 and state[q] == a)
    elif b == 'lie_down':
        j = walk_back(i, lambda q: dh[q] < -0.4 and state[q] == a)
    elif b in ('approach', 'retreat'):
        j = walk_back(i, lambda q: abs(vx[q]) > 0.15 and state[q] == a)
    else:
        j = i
    for q in range(j, i): state[q] = b
# measured posture
post = []
for i, r in enumerate(rows):
    if lying[i]: post.append('lying, head up' if not head_low[i] else 'lying, head down')
    else: post.append('standing, head below back' if head_low[i] else 'standing, head up')

frames = []
for i, r in enumerate(rows):
    S = SCORE['frames'][i]
    frames.append({'i': i, 't': round(i / 24, 4), 'state': state[i], 'score_state': S['dog']['state'], 'x_score': S['dog']['x'],
                   'x_screen': round(r['x'], 2), 'y_screen': round(r['y'], 2), 'facing': int(facing[i]), 'posture': post[i],
                   'muzzle_angle_screen_deg': round(float(ang[i]), 1), 'height_px': int(r['h']),
                   'head_below_back': bool(head_low[i]), 'vx_px_per_frame': round(float(vx[i]), 3)})
onsets = []
for c in SCORE['choices']:
    hit = next((f for f in frames if f['t'] >= c['t'] - 0.5 and f['state'] == c['to']), None)
    onsets.append({'choice': f"{c['from']} → {c['to']}", 'score_t': c['t'], 'measured_t': hit['t'] if hit else None,
                   'dt': round(hit['t'] - c['t'], 3) if hit else None})
# 26.4: the look in, measured as the head rising above the back and the muzzle angle turning, while lying
look = next((f for f in frames if f['t'] >= 26.0 and f['state'] == 'lie_down' and not f['head_below_back']
             and f['height_px'] > frames[int(26.0 * 24)]['height_px'] + 4), None)
onsets.append({'choice': 'hears come in → looks in', 'score_t': 26.4, 'measured_t': look['t'] if look else None,
               'dt': round(look['t'] - 26.4, 3) if look else None, 'rule': 'lying, head top rises > 4 px above its 26.0 s height'})
# approach: is the head below the line of the back for the whole approach?
appr = [f for f in frames if f['score_state'] == 'approach']
head_low_share = sum(f['head_below_back'] for f in appr) / len(appr)
out = {'schema': 'scion27.trace/1', 'measured_from': 'build/cache/matte/*.png (DogMatte composition, 1280x720, same camera)',
       'rules': {'x_screen': 'centroid of all dog pixels', 'facing': '+1 muzzle (red) left of skull (blue) on screen = toward the door; −1 away',
                 'lying': f'dog height < 0.62 × standing height ({stand_h:.0f} px)', 'head_below_back': 'top of head pixels lower than the 2nd-percentile top of body pixels',
                 'state': 'refuse if facing −1; else lie_down if lying; else approach/retreat if |vx| > 0.6 px/frame (retreat also needs head below back); else watch',
                 'onsets': 'each state change walked back while the producing movement is active (muzzle turning > 2.5°/frame, height falling > 0.4 px/frame, |vx| > 0.15 px/frame)'},
       'onsets': onsets, 'approach_head_below_back_share': round(head_low_share, 3), 'frames': frames}
json.dump(out, open(os.path.join(FOLDER, 'trace.json'), 'w'), indent=0)
for o in onsets: print(o)
print('approach head below back share', round(head_low_share, 3), ' standing h', stand_h)
