"""SCION 11 · composite the 768 scene frames from the stage, the performance and the puppets.

Writes build/cache/frames/%04d.jpg and build/cache/measure.jsonl (what the render itself shows:
the dog's rendered silhouette and the place its head pixels landed, frame by frame).
Usage: python3 render.py [first last]   (WORKERS env for parallel processes)
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stage
from stage import W, H, DOOR, WALL_Y

CACHE = os.path.join(HERE, 'cache')
FRAMES = os.path.join(CACHE, 'frames')
PERF = json.load(open(os.path.join(HERE, '..', 'data', 'performance.json')))['frames']

_G = {}


def init():
    from rig import DogRig
    import person
    S = np.load(os.path.join(CACHE, 'stage.npz'))
    _G['S'] = {k: S[k] for k in S.files}
    _G['rig'] = DogRig()
    _G['person'] = person
    rm, _ = stage.interior(1.0)
    _G['room'] = rm
    pool, glow = stage.light_pool(1.0)
    _G['pool'], _G['glow'] = pool, glow
    _G['door'] = {}
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / (W * .62), (yy - H / 2) / (H * .62))
    _G['vig'] = np.clip(1.08 - .55 * r ** 2.2, 0, 1)[..., None]


def door(theta):
    key = round(theta, 1)
    if key not in _G['door']:
        if len(_G['door']) > 40:
            _G['door'].clear()
        _G['door'][key] = stage.door_panel(key)
    return _G['door'][key]


WARM = np.array([1.0, .74, .42], np.float32)
DUSK = np.array([.80, .84, 1.0], np.float32)


def frame(fr):
    S = _G['S']
    t = fr['t']
    dusk = 1.0 - 0.10 * t / 32.0          # the light keeps falling
    light = fr['door']['light']
    can = S['back'].copy() * dusk
    # the room, the door card, the wall with its hole, the floor
    x0, y0, x1, y1 = DOOR
    can[y0 - 2:y1 + 8, x0 - 2:x1 + 2] = _G['room'][y0 - 2:y1 + 8, x0 - 2:x1 + 2] * (0.25 + 0.95 * light)
    drgb, dm = door(fr['door']['theta'])
    can = can * (1 - dm[..., None]) + drgb * dm[..., None] * dusk
    wall = S['wall']
    can = can * (1 - wall[..., 3:4]) + wall[..., :3] * wall[..., 3:4] * dusk
    fl = S['floor']
    can = can * (1 - fl[..., 3:4]) + fl[..., :3] * fl[..., 3:4] * dusk
    # light from the doorway: on the boards and the sill, and a glow on the wall card round the frame
    pool = _G['pool'] * max(0, light - .2) / .8
    glow = _G['glow'] * max(0, light - .2) / .8
    can = can * (1 + (pool * 1.25 + glow * .45)[..., None] * WARM[None, None])
    can = can * (1 - .15 * light * 0) + 0
    # the person (paper, one real hand)
    prgb, pa, PG = _G['person'].layer(fr['person'])
    plit = 0.85 * dusk + 0.55 * max(0, light - .2) * np.exp(-((PG['hip'][0] - 320) / 260) ** 2)
    can = can * (1 - pa[..., None]) + prgb * plit * pa[..., None]
    # the dog: the footage bent to the performance
    dg = fr['dog']
    anchor = np.array([dg['sx'], dg['y']], float)
    L = _G['rig'].render(dg['k'], dg['pose'], anchor, dg['scale'], t)
    lx, ly = L['x0'], L['y0']
    h, w = L['a'].shape
    cx0, cy0, cx1, cy1 = max(lx, 0), max(ly, 0), min(lx + w, W), min(ly + h, H)
    A = np.zeros((H, W), np.float32); G = np.zeros((H, W), np.float32); HD = np.zeros((H, W), np.float32)
    A[cy0:cy1, cx0:cx1] = L['a'][cy0 - ly:cy1 - ly, cx0 - lx:cx1 - lx]
    G[cy0:cy1, cx0:cx1] = L['g'][cy0 - ly:cy1 - ly, cx0 - lx:cx1 - lx]
    HD[cy0:cy1, cx0:cx1] = L['head'][cy0 - ly:cy1 - ly, cx0 - lx:cx1 - lx]
    # paper on a table: the cut-out throws a soft shadow, and its feet a contact shadow
    sh = ndimage.gaussian_filter(np.roll(np.roll(A, 7, 0), 5, 1), 4)
    ground = np.zeros((H, W), np.float32)
    yy = np.arange(H)[:, None]; xx = np.arange(W)[None, :]
    lie = dg['pose']['lie']
    span = (95 + 25 * lie) * dg['scale']
    ground = np.exp(-(((xx - dg['sx']) / span) ** 2 + ((yy - dg['y'] - 2) / 7.0) ** 2))
    can = can * (1 - (.30 * sh + .45 * ground)[..., None])
    # light on the dog: dusk everywhere, warm where it is in the doorway's light
    dl = float(max(0, light - .2) / .8 * np.exp(-((dg['sx'] - 330) / 190) ** 2))
    look = dg['pose']['look']
    shade = 1 - .30 * look * HD  # looking in, its head is against the light
    col = (G * shade)[..., None] * (DUSK * (0.86 * dusk) + WARM * 0.55 * dl)
    col = col * 1.04
    can = can * (1 - A[..., None]) + col * A[..., None]
    # foreground cards
    fr_ = S['front']
    can = can * (1 - fr_[..., 3:4]) + fr_[..., :3] * fr_[..., 3:4] * dusk
    # the tabletop camera: vignette, a little sensor grain
    can = can * _G['vig']
    rng = np.random.default_rng(fr['i'])
    can = can + rng.normal(0, .012, (H, W, 1)).astype(np.float32)
    img = (np.clip(can, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(FRAMES, '%04d.jpg' % fr['i']), quality=90)
    # --- measurement, from the rendered layer itself
    m = A > .5
    ys, xs = np.nonzero(m)
    hm = (HD * A) > .35
    ht = np.nonzero((HD * A) > .08)[0]  # head top with the ear tufts: any pixel with a trace of the head
    hy, hx = np.nonzero(hm)
    rec = dict(i=fr['i'], t=t, area=int(m.sum()),
               cx=float(xs.mean()) if len(xs) else None, cy=float(ys.mean()) if len(ys) else None,
               top=int(ys.min()) if len(ys) else None, bottom=int(ys.max()) if len(ys) else None,
               left=int(xs.min()) if len(xs) else None, right=int(xs.max()) if len(xs) else None,
               hx=float(hx.mean()) if len(hx) else None, hy=float(hy.mean()) if len(hy) else None,
               det_min=L['det_min'], det_max=L['det_max'], withers_y=L['withers'][1],
               head_top=int(ht.min()) if len(ht) else None,
               in_door=float(((xs >= DOOR[0]) & (xs <= DOOR[2])).mean()) if len(xs) else 0.0)
    return rec


def run(rng):
    init()
    return [frame(PERF[i]) for i in rng]


if __name__ == '__main__':
    os.makedirs(FRAMES, exist_ok=True)
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    b = int(sys.argv[2]) if len(sys.argv) > 2 else len(PERF) - 1
    idx = list(range(a, b + 1))
    nw = int(os.environ.get('WORKERS', '3'))
    chunks = [idx[j::nw] for j in range(nw)]
    with Pool(nw) as pool:
        res = pool.map(run, chunks)
    recs = sorted([r for c in res for r in c], key=lambda r: r['i'])
    out = os.path.join(CACHE, 'measure.jsonl')
    old = {}
    if os.path.exists(out) and (a, b) != (0, len(PERF) - 1):
        for line in open(out):
            r = json.loads(line); old[r['i']] = r
    for r in recs:
        old[r['i']] = r
    with open(out, 'w') as f:
        for i in sorted(old):
            f.write(json.dumps(old[i]) + '\n')
    print('rendered', len(recs))
