"""SCION-36 · render the 32 s threshold scene, frame for frame on the PAELEO score.

The dog is whole archive frames (Amateur Film New Jersey C), each one auto-triangulated, auto-rigged and skinned
with its precomputed bounded biharmonic weights (rigs.py). Views change only through the archive's own turn
(the in-between frames the found dog actually turned through), never by a dissolve. The person is one archive frame
(Straight Talk) rigged the same way, kept as a contre-jour silhouette. The porch, the door and the dusk are
computed here. Writes build/cache/frames/s%04d.jpg, ../trace.json, build/cache/cues.json.
python3 render.py [first last]   (scene frames, default all 768)"""
import json, os, pickle, sys, math
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skin import lbs, raster, rot, trans, compose, apply, scale_along
from pose import mats, depth

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(OUT, '..', '..', '..'))
CACHE = os.path.join(HERE, 'cache'); FR = os.path.join(CACHE, 'frames'); os.makedirs(FR, exist_ok=True)
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
SF = SCORE['frames']; N = len(SF); FPS = 24
W_, H_ = 1280, 720
RIGS = pickle.load(open(os.path.join(CACHE, 'rigs.pkl'), 'rb'))

# ------------------------------------------------------------------ camera and the porch (metres)
F0, CX0, UC, VC, HC, YH0 = 1250.0, 640.0, 2.2, 6.0, 2.4, 0.0
F, CX, YH = F0, CX0, YH0
ZOOM = None
FOCUS = (0.25, 0.15, 0.25)          # a point by the sill the camera closes in on
FOCUS_TO = (600.0, 470.0)


def zoom_at(t):
    z = min(1, max(0, (t - 21.5) / 3.5)); z = z * z * (3 - 2 * z)
    return z


def set_camera(z):
    """z 0 (the whole porch) .. 1 (closer on the sill): F scales, the focus point slides to FOCUS_TO"""
    global F, CX, YH, SET, OPEN_M, OL, OR, OT, OB, ZOOM
    if ZOOM is not None and abs(z - ZOOM) < 1e-6: return
    Z = 1 + .40 * z
    uf, vf, hf = FOCUS; df = VC - vf
    s0 = np.array([CX0 + F0 * (uf - UC) / df, YH0 + F0 * (HC - hf) / df])
    sp = s0 + (np.array(FOCUS_TO) - s0) * z
    F = F0 * Z; CX = sp[0] - F * (uf - UC) / df; YH = sp[1] - F * (HC - hf) / df
    SET = build_set(); OPEN_M, (OL, OR, OT, OB) = opening_mask(); ZOOM = z


def proj(u, v, h=0.0):
    d = VC - v
    return np.array([CX + F * (u - UC) / d, YH + F * (HC - h) / d])


def softplus(z, k=.35):
    return k * np.log1p(np.exp(z / k))


def path(x):
    """the score's x (metres from the threshold) to a point on the porch floor: straight out of the door first,
    then bending along the porch toward the steps"""
    u = 0.08 + 0.82 * x + 0.15 * softplus(x - 1.5) + 0.10 * min(1.0, max(0.0, 1.5 - x))
    v = -0.12 + 0.57 * x - 0.35 * softplus(x - 1.5)
    return u, v


def ground_xy(x):
    u, v = path(x); return proj(u, v)


DOOR_U = (-0.46, 0.46); DOOR_H = 2.05; LEAF_H = 1.0
DOG_H = 0.62       # shoulder height of the dog, metres


# ------------------------------------------------------------------ static set
rng = np.random.default_rng(36)
yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)


def build_set():
    img = np.zeros((H_, W_, 3), np.float32)
    base_y = proj(0, 0)[1]
    # facade (v = 0): clapboards
    wall = np.array([.17, .18, .21], np.float32)
    img[:] = wall
    for hb in np.arange(0, 3.4, .19):
        y = proj(0, 0, hb)[1]
        band = np.clip(1 - np.abs(yy - y) / 1.6, 0, 1)
        img -= band[..., None] * .05
        img += np.clip(1 - np.abs(yy - y - 3) / 3, 0, 1)[..., None] * .015
    # floor of the porch: boards running out from the facade
    floor = yy > base_y
    d = F * HC / np.maximum(yy - YH, 1)
    v = VC - d
    u = UC + (xx - CX) * d / F
    board = (np.abs(((u + 10) / .14) % 1 - .5) > .46).astype(np.float32)
    grain = ndi.gaussian_filter(rng.standard_normal((H_, W_)).astype(np.float32), (1, 6)) * .03
    fl = .13 + .02 * np.clip(v / 3, 0, 1) - .035 * board + grain
    fl = np.where(u > 5.4, .05 + 0 * fl, fl)   # off the end of the porch, by the steps
    img[floor] = (fl[..., None] * np.array([1.0, .95, .9], np.float32))[floor]
    # window to the right of the door
    wa, wb = proj(1.7, 0, 1.85), proj(2.6, 0, .95)
    win = (xx > wa[0]) & (xx < wb[0]) & (yy > wa[1]) & (yy < wb[1])
    img[win] = np.array([.10, .12, .16]) + (yy[win, None] - wa[1]) / (wb[1] - wa[1]) * .03
    for uu in (1.7, 2.15, 2.6):
        x = proj(uu, 0)[0]; m = win | (np.abs(xx - x) < 3) & (yy > wa[1] - 3) & (yy < wb[1] + 3)
        img[(np.abs(xx - x) < 3) & (yy > wa[1] - 4) & (yy < wb[1] + 4)] = .24
    y = proj(0, 0, 1.4)[1]
    img[(np.abs(yy - y) < 2.5) & (xx > wa[0] - 3) & (xx < wb[0] + 3)] = .24
    # the sill: a worn board across the opening, a little proud of the porch
    a0, a1 = proj(DOOR_U[0] - .06, .10), proj(DOOR_U[1] + .06, .10)
    b0 = proj(DOOR_U[0] - .06, -.06, .035)
    sill = (xx > a0[0]) & (xx < a1[0]) & (yy > b0[1]) & (yy < a0[1])
    img[sill] = np.array([.34, .31, .27]) + (yy[sill, None] - b0[1]) / max(a0[1] - b0[1], 1) * -.08
    edge = (xx > a0[0]) & (xx < a1[0]) & (np.abs(yy - a0[1]) < 1.6)
    img[edge] = .09
    # door casing
    l, r = proj(DOOR_U[0] - .12, 0)[0], proj(DOOR_U[1] + .12, 0)[0]
    top = proj(0, 0, DOOR_H + .12)[1]
    cas = (xx > l) & (xx < r) & (yy > top) & (yy < base_y)
    img[cas] = np.array([.30, .29, .27])
    # porch post at the right
    px = proj(5.4, .15)[0]; ptop = 0
    post = (np.abs(xx - px) < 15) & (yy < proj(5.4, .15)[1])
    img[post] = np.array([.24, .23, .22]) - (np.abs(xx[post] - px) / 15)[:, None] * .08
    return img


def opening_mask():
    l, r = proj(DOOR_U[0], 0)[0], proj(DOOR_U[1], 0)[0]
    top = proj(0, 0, DOOR_H)[1]; bot = proj(0, 0)[1]
    return (xx > l) & (xx < r) & (yy > top) & (yy < bot), (l, r, top, bot)


def interior(lit):
    """the room through the door: floor and back wall; lit 0 (dim) .. 1 (the door open, the lamp full)"""
    d = F * HC / np.maximum(yy - YH, 1)
    v = VC - d
    back = -3.2
    img = np.zeros((H_, W_, 3), np.float32)
    isfloor = v > back
    u = UC + (xx - CX) * d / F
    lamp = np.exp(-(((xx - proj(.25, -2.4, 1.6)[0]) / 120) ** 2 + ((yy - proj(.25, -2.4, 1.6)[1]) / 110) ** 2))
    wallc = np.array([.95, .72, .45], np.float32) * (.55 + .45 * lamp[..., None])
    fl = np.array([.62, .42, .24], np.float32) * (.55 + .25 * ((np.abs(((u + 10) / .2) % 1 - .5) < .47)[..., None]))
    img = np.where(isfloor[..., None], fl * (1 - .35 * np.clip((v - back) / 3, 0, 1)[..., None] * 0), wallc)
    return img * (.32 + .68 * lit)


def light_pool(open_):
    """warm light thrown on the porch floor through the opening (a lamp inside at 2.5 m)"""
    if open_ <= 0: return np.zeros((H_, W_), np.float32)
    d = F * HC / np.maximum(yy - YH, 1); v = VC - d; u = UC + (xx - CX) * d / F
    Lu, Lv, Lh = -1.2, -1.8, 2.5
    # a floor point (u,v) is lit if the ray to the lamp passes through the opening at v = 0
    t = (0 - v) / (Lv - v + 1e-6)
    uo = u + t * (Lu - u); ho = t * Lh
    inside = (v > 0) & (uo > DOOR_U[0]) & (uo < DOOR_U[1] * (2 * open_ - 1 if open_ < 1 else 1)) & (ho < DOOR_H)
    inside = inside & (yy > proj(0, 0)[1])
    pool = inside.astype(np.float32) / (1 + .18 * (v + .3) ** 2)
    return ndi.gaussian_filter(pool, 4) * min(1, open_ * 1.3)


set_camera(0.0)


# ------------------------------------------------------------------ timeline: the dog
def score_at(i): return SF[min(max(i, 0), N - 1)]


T1 = (3.46, 3.97)     # first turn (away): the archive's own in-betweens
T2 = (7.40, 7.60)     # turn back to look, lying: head first, hips down
SEQ = ['t13', 't16', 't21', 't22', 't24', 't25', 't26', 't30', 't33', 't36', 't40']   # the found turn, frame by frame


def dog_plan(i):
    """which archive view, and the pose numbers, for scene frame i"""
    f = score_at(i); t = i / FPS; a = f['dog']['act']; st = f['dog']['state']
    head = a['head']; crouch = a['crouch']; tail = (a['tail'] - .5) * 1.1
    wag = a['wag'] * .45 * math.sin(t * 2 * math.pi * 2.3)
    mv = a['moving']; ph = a['walk_phase']
    amp = .18 * mv
    swing = [amp * math.sin(ph), amp * math.sin(ph + math.pi)]   # (front, hind): legs that overlap in the found frame swing together, no tearing between them
    p = dict(tail=tail, wag=wag, crouch=crouch, swing=swing)
    if t < T1[0]:
        view = 'W'; p['neck'] = (1.0 - head) * 2.0 - .05
    elif t < T1[1]:
        k = int((t - T1[0]) / (T1[1] - T1[0]) * len(SEQ)); view = SEQ[min(k, len(SEQ) - 1)]
        p.update(neck=0.0 if view in ('t24', 't25', 't26', 't30', 't33', 't36', 't40') else .5, crouch=.45, swing=None, frontal=view in ('t24', 't25', 't26', 't30', 't33', 't36'), tail=.4)
    elif t < T2[0]:
        # the turned back: f010 mirrored standing, then f007 mirrored (the next found frame, with its own tail and
        # folding hind leg) as it lies down, chin toward the boards
        lie = a['lie']
        view = 'r7m' if lie > .5 else 'Wm'
        p['fold'] = lie; p['chin'] = .25 * a['rest']
        p['neck'] = (.85 + .2 * a['rest']) if view == 'r7m' else (1.0 - head) * 1.5
    elif t < T2[1]:
        # turning to look, lying: the head comes up and round (f005, the back of the skull to the camera), through
        # the next found frame (f006) ...
        view = 'r5'
        p.update(neck=.25, fold=1.0, swing=None, tail=.3, crouch=0, tuck=True)
    elif t < 8.3:
        # ... and settles toward the door, muzzle level, hips still down (f007 lying); then it rises (f010)
        rise = min(1, max(0, (t - 7.8) / .45)); rise = rise * rise * (3 - 2 * rise)
        view = 'r7' if rise < .5 else 'W'
        p.update(neck=.75 * (1 - rise) + .1 * rise if view == 'r7' else .1, fold=1 - rise, fold_front=1 - rise,
                 swing=None, crouch=.2 * (1 - rise))
    elif st == 'lie_down':
        lie = a['lie']; look = a['look']; rest = a['rest']
        view = 'r7' if lie > 0 else 'W'
        p['fold'] = lie; p['swing'] = [s * (1 - lie) for s in swing]
        if view == 'W':
            p['neck'] = (1.0 - head) * 2.5 - .05
        else:
            p['neck'] = .85 + .25 * rest; p['chin'] = .06 * rest
        if look > .5:
            # looking in: the archive's own look over the shoulder (f005), held while the score looks in: the head
            # turns away from the camera, up into the lit room, back of the skull and ears to us; body still lying
            view = 'r5'; p['neck'] = .25; p['chin'] = 0.0; p['tuck'] = True
    elif st == 'approach':
        view = 'W'; p['neck'] = (1.0 - head) * 2.5 - .05
    else:
        view = 'W'; p['neck'] = (1.0 - head) * 2.0 - .05
    return view, p


def placement(r, x, view, lie=0.0):
    """source px -> screen px for an archive view standing at score position x: scale by depth, shear along the
    path (the far end of the body goes up the screen), foreshorten along the path"""
    g = ground_xy(x)
    u, v = path(x); d = VC - v
    s = DOG_H * F / d / r['body']['body_h']
    e = .05
    a, b = ground_xy(x - e), ground_xy(x + e)      # toward the door is a (x smaller)
    tan = a - b; tan = tan / (np.linalg.norm(tan) + 1e-9)
    k = tan[1] / tan[0] if abs(tan[0]) > 1e-3 else 0.0
    pu, pv = path(x - e); qu, qv = path(x + e)
    metres = math.hypot(pu - qu, pv - qv)
    fr = np.linalg.norm(a - b) / (metres * F / d)
    fr = min(1.0, .35 + .65 * fr)
    if lie > .5:
        fr = max(fr, .55 + .3 * lie)     # lying: the body keeps most of its length
    k = float(np.clip(k, -.38, .38)) * (1 - .4 * lie)
    if r.get('frontal'):
        k *= .3; fr = 1.0
    an = r['body']['anchor'].copy()
    if lie > .5:
        # lying: anchor on the middle of the body, so every lying view sits across the same spot of the sill
        an[0] = r['body']['cx']
    A = np.array([[s * fr, 0], [s * fr * k, s]])
    return np.hstack([A, (g - A @ an)[:, None]]), s


def dog_layer(i, canvas, light):
    f = score_at(i); x = f['dog']['x']
    view, p = dog_plan(i)
    r = RIGS[view]
    Ms = mats(r, **p)
    Vd = lbs(r['V'], r['W'], Ms)
    P, s = placement(r, x, view, p.get('fold', 0.0) or 0.0)
    Vs = apply(P, Vd)
    # grade the archive texture for dusk and for the door light at the dog's place
    tex = r['tex'].copy()
    gx, gy = ground_xy(x)
    lw = float(light[int(min(max(gy, 0), H_ - 1)), int(min(max(gx, 0), W_ - 1))])
    lw = max(lw, float(light[int(min(max(gy - 6, 0), H_ - 1)), int(min(max(gx - 30, 0), W_ - 1))]))
    m3 = tex[..., 3:4] > .5
    mu = float(tex[..., :3][m3[..., 0]].mean())
    tex[..., :3] = np.clip(mu * .85 + (tex[..., :3] - mu) * 1.6, 0, 1)    # the found grey, pressed for dusk
    amb = np.array([.70, .72, .80], np.float32); warm = np.array([.85, .62, .36], np.float32)
    tex[..., :3] = tex[..., :3] * (amb + warm * lw * .45)
    # contact shadow: the body sits on it
    pts = Vs
    gyl = gy
    xs = pts[:, 0]
    lo, hi = np.percentile(xs, 4), np.percentile(xs, 96)
    cxs = (lo + hi) / 2; rx = (hi - lo) / 2 * 1.02 + 6
    ry = max(6, .09 * rx)
    # the ground line follows the shear: shadow centre at the ground under the body centre
    tilt = (P[1, 0] / P[0, 0]) if P[0, 0] else 0
    sh = np.exp(-(((xx - cxs) / rx) ** 2 + ((yy - (gyl + tilt * (xx - gx)) - 2) / ry) ** 2) * 1.6)
    canvas *= (1 - .55 * sh[..., None])
    fold = p.get('fold', 0.0) or 0.0
    clip = None
    if fold > .2:
        # lying: nothing of the dog goes below the boards it lies on
        slope = P[1, 0] / P[0, 0] if P[0, 0] else 0.0
        clip = np.clip((gy + slope * (xx - gx) + 5 - yy) / 3, 0, 1).astype(np.float32)
    px, py, al = raster(canvas, None, Vs, r['V'], r['T'], tex, depth(r, fold), clip=clip)
    # measurements from the render
    names = r['names']
    hd = Vs[np.argmax(r['W'][:, names.index('head')])]
    tl = Vs[np.argmax(r['W'][:, names.index('tailtip')])] if 'tailtip' in names else Vs[np.argmax(r['W'][:, names.index('back' if 'back' in names else names[1])])]
    bk = Vs[r['W'][:, names.index('back' if 'back' in names else names[1])] > .5]
    cov = al > .5
    legs = [j for j, k in enumerate(names) if k.startswith('leg')]
    pinned = np.concatenate([r['sets'][names[j]] for j in legs]) if legs else np.arange(len(Vs))
    feet = Vs[pinned][np.argsort(Vs[pinned][:, 1])[-max(4, len(pinned) // 6):]]
    contact = feet.mean(0)
    xs_grid = np.linspace(-.5, 5.5, 1201)
    gp = np.array([ground_xy(xg) for xg in xs_grid])
    xw = float(xs_grid[np.argmin(np.abs(gp[:, 0] - contact[0]))])
    meas = dict(x_world_measured=xw, contact=[float(contact[0]), float(contact[1])], zoom=ZOOM,view=view, frame=r['fi'], x_screen=float(px[cov].mean()) if cov.any() else float(gx),
                y_screen=float(py[cov].mean()) if cov.any() else float(gy), area=float(al.sum()), ground=[float(gx), float(gy)],
                head=[float(hd[0]), float(hd[1])], tail=[float(tl[0]), float(tl[1])],
                back_y=float(bk[:, 1].mean()) if len(bk) else None, top=float(py[cov].min()) if cov.any() else None,
                scale=float(s), facing=-1 if hd[0] < tl[0] else 1, pose={k: (v if not isinstance(v, list) else None) for k, v in p.items()})
    return meas


# ------------------------------------------------------------------ the person
def person_plan(i):
    f = score_at(i); pe = f['person']; t = i / FPS
    # place: doorway (score -0.28) -> beside (score -1.25): across the opening to the left, inside
    xs = pe['x']; k = min(1, max(0, (xs - (-0.28)) / (-1.25 + .28)))
    u = .0 - .54 * k; v = -.28 - .05 * k
    sit = pe['sit']
    reach = pe['reach']; low = pe['low']; mouth = pe['mouth']
    voice = pe['voice']
    return dict(u=u, v=v, sit=sit, reach=reach, low=low, voice=voice, t=t, mouth=mouth)


def person_layer(i, canvas, lit, leaf_open):
    q = person_plan(i); r = RIGS['P']
    names = r['names']; H = r['H']
    sit = q['sit']
    # standing: the head top at 1.66 m; the frame's lower edge (mid thigh) at 0.70 m, below the closed lower leaf
    # sitting: on the floor, the same cut at 0.04 m
    top_h = 1.66 - .92 * sit
    d = VC - q['v']
    srcH = r['bottom'] - r['top']
    s = (.96 * F / d) / srcH
    head_screen = proj(q['u'], q['v'], top_h)
    # handle transforms in source px
    sh = np.array(H['chest']['a'])
    lean = -.10 * q['reach'] - .14 * q['low'] + .03 * math.sin(q['t'] * 7) * (q['voice'] == 'call')
    Mc = rot(lean, sh)
    arm_a = np.array(H['arm']['a'])
    arm = -1.05 * q['reach'] - 1.25 * q['low']
    Ma = compose(Mc, rot(arm, arm_a))
    nod = (.06 * math.sin(q['t'] * 9) if q['voice'] == 'call' else 0) + (.10 if q['voice'] == 'soft' else 0)
    Mh = compose(Mc, rot(nod, np.array(H['head']['at'])))
    Mhip = np.hstack([np.eye(2), np.zeros((2, 1))])
    Ms = np.stack([{'head': Mh, 'chest': Mc, 'hips': Mhip, 'arm': Ma}[k] for k in names])
    Vd = lbs(r['V'], r['W'], Ms)
    A = np.array([[s, 0], [0, s]]); src_top = np.array([r['cx'], r['top']])
    P = np.hstack([A, (head_screen - A @ src_top)[:, None]])
    Vs = apply(P, Vd)
    tex = r['tex'].copy()
    # contre-jour: the room's light is behind her
    tex[..., :3] = tex[..., :3] * .20 + np.array([.03, .025, .02], np.float32)
    # behind the closed lower leaf she is hidden below its top edge (until the leaf opens)
    clip = np.ones((H_, W_), np.float32)     # the lower leaf, drawn after her, hides what it covers
    # her legs are out of the frame: the lower edge fades into the floor's shadow
    bottom_y = apply(P, np.array([[r['cx'], r['bottom']]]))[0, 1]
    fade = np.clip((bottom_y - yy) / 18, 0, 1)
    clip = clip * fade
    # and she is only ever seen through the opening
    clip = clip * OPEN_M
    raster(canvas, None, Vs, r['V'], r['T'], tex, None, clip=clip)
    return dict(head=[float(head_screen[0]), float(head_screen[1])], sit=sit, reach=q['reach'], low=q['low'])


# ------------------------------------------------------------------ the door
def door_state(t):
    o = min(1, max(0, (t - 6.2) / .7)); o = o * o * (3 - 2 * o)
    return o


def draw_leaf(canvas, o):
    """the lower leaf of a half door, hinged on the right jamb, swinging in"""
    th = o * math.radians(105)
    hu = DOOR_U[1]; L = DOOR_U[1] - DOOR_U[0]
    eu, ev = hu - L * math.cos(th), -L * math.sin(th)
    P = [proj(hu, 0, 0), proj(eu, ev, 0), proj(eu, ev, LEAF_H), proj(hu, 0, LEAF_H)]
    from PIL import ImageDraw
    m = Image.new('L', (W_, H_), 0); ImageDraw.Draw(m).polygon([tuple(p) for p in P], fill=255)
    m = np.asarray(m, np.float32) / 255
    if o > 0: m = m * OPEN_M          # swung in: seen only through the opening
    shade = .20 + .06 * math.cos(th)
    col = np.array([shade, shade * .93, shade * .85], np.float32)
    # panel lines
    pan = np.zeros((H_, W_), np.float32)
    canvas[:] = canvas * (1 - m[..., None]) + col * m[..., None] * (1 - .25 * pan[..., None])
    # the top rail catches the room light
    e1, e2 = proj(hu, 0, LEAF_H), proj(eu, ev, LEAF_H)
    return m


def compose_frame(i):
    t = i / FPS; f = score_at(i)
    set_camera(zoom_at(t))
    o = door_state(t)
    lit = .30 + .70 * o
    img = SET.copy()
    inner = interior(lit)
    img[OPEN_M] = inner[OPEN_M]
    pool = light_pool(o)
    floor = yy > OB
    warm = np.array([1.0, .72, .42], np.float32)
    img *= 1 + (pool[..., None] * warm * 2.2) * floor[..., None]
    # light also leaks from the upper half before the door opens: a thin wash
    pre = light_pool(1.0) * .10 * (1 - o)
    img *= 1 + (pre[..., None] * warm * 2.2) * floor[..., None]
    pm = person_layer(i, img, lit, o)
    draw_leaf(img, o)
    light = pool + pre
    dm = dog_layer(i, img, light)
    return img, dm, pm, o


def film_look(img, i):
    r = np.random.default_rng(1000 + i)
    g = r.standard_normal((H_ // 2, W_ // 2)).astype(np.float32)
    g = np.kron(g, np.ones((2, 2), np.float32))
    lum = img.mean(2, keepdims=True)
    img = img * .55 + lum * .45                      # mostly monochrome, the door light keeps its warmth
    img = img + g[..., None] * .028
    vig = 1 - .38 * (((xx - W_ / 2) / (W_ * .62)) ** 2 + ((yy - H_ / 2) / (H_ * .62)) ** 2)
    flick = 1 + .018 * math.sin(i * 2.1) + .01 * r.standard_normal()
    img = img * vig[..., None] * flick
    img = np.clip(img * 1.12, 0, 1) ** .92
    return img


def main():
    a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, N)
    meas = []
    for i in range(a, b):
        img, dm, pm, o = compose_frame(i)
        img = film_look(img, i)
        Image.fromarray((img * 255).astype(np.uint8)).save(os.path.join(FR, 's%04d.jpg' % i), quality=92)
        meas.append({'i': i, 'dog': dm, 'person': pm, 'door_open': o})
        if i % 48 == 0: print('frame', i, dm['view'], flush=True)
    json.dump(meas, open(os.path.join(CACHE, 'meas_%04d_%04d.json' % (a, b)), 'w'))


if __name__ == '__main__':
    main()
