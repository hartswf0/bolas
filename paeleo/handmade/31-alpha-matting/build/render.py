"""SCION 31 · Alpha Matting: the threshold scene, composited from solved mattes.

Every visible piece of the dog, the woman, her hand, the door leaf and its curtain, and the clouds is a premultiplied RGBA
matte solved from rights-recorded archive frames (prep_dog.py, prep_world.py). The house, the porch, the sky gradient,
the tree line, the door light and the haze are computed. Compositing is premultiplied 'over' throughout; light is added
as emission (alpha 0). Dog choreography = substitution of whole matted archive frames chosen by the score:
held frames, the archive dog's own turn (played forward to refuse, backward to look again), and its own head-low walk
(mirrored, frames advanced by distance travelled so the feet account for the travel). The lying dog is a labelled
reconstruction made of pieces of one matted frame (body, forelegs pivoted forward, head substituted).

python3 render.py [--frames a:b] [--stills] [--jobs n]      writes build/cache/frames/s%04d.jpg + build/cache/render_trace.json
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from lib_matte import blur, box, resize_premult, coverage

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, 'cache')
SCORE = json.load(open(os.path.join(HERE, '../../score/threshold-score.json')))
FR = SCORE['frames']
W, H = 1280, 720
PPM, XD = 190., 330.            # pixels per metre, screen x of the threshold (door centre)
GY = 600                        # porch floor line where feet stand
DOOR = (int(XD - 87), 195, int(XD + 87), 586)   # door opening (x0, y0, x1, y1)
DS = 1.55                        # dog source px -> screen px
RNG = np.random.default_rng(31)


def sx(x):
    return XD + x * PPM


def smooth(a, b, t):
    u = np.clip((t - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


# ---------------------------------------------------------------- static world (computed)
def fbm1(n, seed, octaves=6):
    r = np.random.default_rng(seed); out = np.zeros(n)
    for o in range(octaves):
        k = 2 ** o * 3; v = r.standard_normal(k + 2)
        out += np.interp(np.linspace(0, k, n), np.arange(k + 2), v) / (1.6 ** o)
    return out


def static_layers():
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    S = {}
    # facade: clapboards in the last light
    wall = np.zeros((H, W, 3), np.float32) + np.array([.17, .185, .25])
    board = (yy % 22) / 22.
    wall *= (0.86 + 0.14 * board)[..., None]
    wall[(yy % 22) < 1.5] *= .6
    wall *= (1 - .25 * (yy / H))[..., None]
    S['wall'] = wall
    # porch floor: boards parallel to the wall, widening toward the camera
    fl = np.zeros((H, W, 3), np.float32) + np.array([.15, .14, .16])
    d = np.clip((yy - 586) / (700 - 586), 0, 1)
    ph = (d ** .8) * 9
    fl *= (0.85 + 0.15 * (ph % 1))[..., None]
    fl[(ph % 1) < .08] *= .55
    fl *= (0.75 + 0.35 * d)[..., None]
    S['floor'] = fl
    # sky gradient (darkens over the scene: see sky())
    S['yy'] = yy; S['xx'] = xx
    # tree line: foliage edge class, a computed fractional matte (fbm height, leaf noise in the edge band)
    prof = 548 - 12 * fbm1(W, 7) - 5 * fbm1(W, 8, 8)
    noise = blur(RNG.random((H, W)).astype(np.float32), 1, 1)
    edge = (yy - prof[None, :]) / 6.
    S['tree_a'] = np.clip(.5 + edge + (noise - .5) * 2.2, 0, 1) * (yy < 600)
    # door light on the porch floor: from the opening, spreading toward the camera, falling off with distance
    x0, x1 = DOOR[0], DOOR[2]
    t = np.clip((yy - 586) / 140., 0, 1)
    l = x0 - t * 120; r = x1 + t * 260
    inside = np.clip(np.minimum(xx - l, r - xx) / 30., 0, 1) * (yy > 586) * (yy < 700)
    dist = np.hypot((xx - XD) / 1.6, (yy - 586) * 1.4)
    S['spill'] = (inside * np.exp(-dist / 260.)).astype(np.float32)
    # haze beam mask (dusk air in front of the opening)
    beam = np.clip(1 - np.abs(xx - (XD + (yy - 420) * .25)) / (110 + .4 * np.maximum(yy - 300, 0)), 0, 1) * (yy > 250) * (yy < 700)
    S['beam'] = (beam ** 1.5).astype(np.float32)
    # interior: far wall with a lamp
    li = np.zeros((H, W, 3), np.float32)
    lamp = np.exp(-(((xx - (XD - 30)) / 120.) ** 2 + ((yy - 330) / 160.) ** 2))
    li += np.array([.55, .36, .18]) * (0.55 + 0.9 * lamp)[..., None]
    li[yy > 540] *= .7
    S['interior'] = li.astype(np.float32)
    return S


ST = None


def sky(t):
    yy = ST['yy']
    k = t / 38.
    top = np.array([.09, .11, .26]) * (1 - .35 * k)
    hor = np.array([.86, .50, .40]) * (1 - .45 * k)
    u = np.clip(yy / 480., 0, 1)[..., None] ** 1.4
    return (top * (1 - u) + hor * u).astype(np.float32)


# ---------------------------------------------------------------- matte assets
def load_npz(path):
    z = np.load(path)
    return {k: z[k] for k in z.files}


DOG = {}
DEBRIS = {15: [(163, 98, 183, 119)],    # frame 15: a fragment standing on the back (source px)
          14: [(149, 100, 160, 107), (160, 100, 165, 104), (149, 104, 155, 110)]}   # frame 14: a hooked strand above the shoulder (round 3, seen 9.2-10.0 s)


def dog_frame(i, mirror):
    key = (i, mirror)
    if key not in DOG:
        z = load_npz(os.path.join(C, 'dog/f%03d.npz' % i))
        P = z['P'].astype(np.float32); x0, y0, x1, y1 = z['box']
        P = P * main_component(P[..., 3])[..., None]       # matte debris detached from the body is dropped
        for (bx0, by0, bx1, by1) in DEBRIS.get(i, []):      # debris attached to the outline (looked at, cut by hand)
            m = np.zeros(P.shape[:2], np.float32)
            m[max(by0 - y0, 0):max(by1 - y0, 0), max(bx0 - x0, 0):max(bx1 - x0, 0)] = 1
            P = P * (1 - blur(m, 1, 1))[..., None]
        if mirror:
            P = P[:, ::-1].copy(); x0, x1 = 384 - x1, 384 - x0
        DOG[key] = (P, (x0, y0, x1, y1))
    return DOG[key]


def piece_canvas(P, box_, CW=384, CH=288):
    full = np.zeros((CH, CW, 4), np.float32)
    x0, y0, x1, y1 = box_
    full[y0:y1, x0:x1] = P
    return full


def rot_premult(P, ang, cx, cy, dx=0, dy=0):
    """rotate a premultiplied canvas about (cx, cy) then translate (PIL, per channel, bicubic)"""
    out = [np.asarray(Image.fromarray(P[..., c]).rotate(ang, Image.BICUBIC, center=(cx, cy), translate=(dx, dy))) for c in range(4)]
    o = np.stack(out, 2).astype(np.float32)
    o[..., 3] = np.clip(o[..., 3], 0, 1); o[..., :3] = np.clip(o[..., :3], 0, o[..., 3:4])
    return o


def soft_region(shape, fn, feather=3):
    yy, xx = np.mgrid[:shape[0], :shape[1]].astype(np.float32)
    m = fn(xx, yy).astype(np.float32)
    return blur(m, feather, 2)


LIE = {}
NECK = (114, 122)     # head pivot in frame 9 (source px)
ELBOW = (120, 150)    # foreleg pivot


def lie_pieces():
    """Reconstruction (labelled): the archive dog was never filmed lying. Pieces of the matted frame 9 (the dog in
    profile, head up) are re-composed: body above the belly line, both forelegs pivoted forward at the elbow, the hind
    legs folded (compressed) under the haunch, and the head pivoted at the neck or substituted by frame 15's head,
    which is turned away from the camera. Soft complementary masks split one solved alpha, so unmoved pieces sum
    back to the matte."""
    if LIE:
        return LIE
    P, b = dog_frame(9, False)
    A = piece_canvas(P, b)
    shp = A.shape[:2]
    yy, xx = np.mgrid[:shp[0], :shp[1]].astype(np.float32)
    # belly edge (reconstruction): the cut through the fur gets a strand-like fringe, not a straight line
    r = np.random.default_rng(9)
    fringe = np.repeat(r.normal(0, 1, shp[1]), 1)
    fringe = np.convolve(fringe - np.convolve(fringe, np.ones(9) / 9, "same"), np.ones(2) / 2, "same") * .9 + .6 * np.sin(xx[0] * .9)
    belly = 151 + fringe[None, :]
    body_m = np.clip((belly - yy) / 2.5 + .5, 0, 1)
    legs_m = np.clip((yy - (belly - 9)) / 3. + .5, 0, 1)          # legs overlap 9 px up under the body
    head_m = np.clip(1 - np.hypot((xx - 98) / 26., (yy - 98) / 30.), 0, 1) * 4
    head_m = np.clip(head_m, 0, 1) * (yy < 140)
    core = np.clip((1 - np.hypot((xx - 96) / 23., (yy - 96) / 27.)) * 6, 0, 1) * (yy < 140)
    body_m = body_m * (1 - core)
    LIE['body'] = A * body_m[..., None]
    LIE['foreA'] = A * (legs_m * (xx < 113))[..., None]          # the foreleg already reaching forward
    LIE['fore'] = A * (legs_m * (xx >= 113) * (xx < 152))[..., None]   # the upright foreleg
    LIE['hind'] = A * (legs_m * (xx >= 152))[..., None]
    LIE['head'] = A * head_m[..., None]
    # the head seen from behind (frame 5: the dog looks up and away, the back of its skull and ears toward the camera)
    P5, b5 = dog_frame(5, False)
    A5 = piece_canvas(P5, b5)
    hm5 = soft_region(shp, lambda x, y: (x < 142) & (y < 138), 3)   # cut only across the neck: skull and ears keep their own matte edge
    LIE['head_back'] = rot_premult(A5 * hm5[..., None], 0, 0, 0, dx=-22, dy=-12)   # skull and both ears above the shoulder line
    return LIE


def lying_sprite(L, head_up, look, rest, face_right=False, look_back=0.0):
    """compose the lying dog at source scale. L 0..1 lowers the body to the floor and folds the legs; head_up keeps
    the head raised (sphinx); rest lowers the chin toward the paws; look substitutes the head turned away (looking in).
    face_right mirrors the whole matte (the refusal); look_back keeps the head unmirrored, turned back toward the door."""
    p = lie_pieces()
    drop = 47 * L
    def over(dst, src):
        return src + dst * (1 - src[..., 3:4])
    hind = p['hind']
    if L > 0:
        s_ = 1 - .88 * L
        ch = [np.asarray(Image.fromarray(hind[..., c]).transform(hind.shape[1::-1], Image.AFFINE, (1, 0, 0, 0, 1 / s_, 151 - 151 / s_), Image.BICUBIC)) for c in range(4)]
        hind = np.clip(np.stack(ch, 2), 0, 1).astype(np.float32)
    hind = rot_premult(hind, 0, 0, 0, dy=drop)
    hind[204:] = 0                                       # folded under the body: nothing below the floor line, but
                                                         # no fade either, so body + hind still add up to solid across the thigh
    def ground(P, target):
        rows = np.nonzero((P[..., 3] > .4).sum(1) > 1)[0]
        return 0 if len(rows) == 0 else target - (rows.max() + 1)
    fore = rot_premult(p['fore'], -84 * L, 128, 150)
    foreA = rot_premult(p['foreA'], -58 * L, 110, 150)
    body = rot_premult(p['body'], 0, 0, 0, dy=drop)
    gl = 151 + drop + 3                                   # the floor under the lowered belly
    fore = rot_premult(fore, 0, 0, 0, dx=-4 * L, dy=drop if L < 1e-3 else (1 - L) * drop + L * ground(fore, gl))
    foreA = rot_premult(foreA, 0, 0, 0, dx=-2 * L, dy=drop if L < 1e-3 else (1 - L) * drop + L * ground(foreA, gl - 1))
    out = np.zeros_like(body)
    out = over(out, hind); out = over(out, foreA); out = over(out, fore); out = over(out, body)
    ang = 52 * rest - 4 * head_up
    hd = rot_premult(p['head'], ang, NECK[0], NECK[1], dx=-3 * rest, dy=drop + 10 * rest)
    if look > 0:
        hb = rot_premult(p['head_back'], 0, 0, 0, dy=drop)
        hd = hd * (1 - look) + hb * look            # premultiplied dissolve over a few frames at the substitution
    if face_right:
        out = out[:, ::-1].copy()
        hm = hd[:, ::-1]
        if look_back > 0:   # head kept facing the door (left), over the right-facing body
            hb2 = rot_premult(hd, 0, 0, 0, dx=384 - 2 * NECK[0] - 4, dy=-22)   # head lifted clear of the back
            hm = hm * (1 - look_back) + hb2 * look_back
        out = over(out, hm)
    else:
        out = over(out, hd)
    # union alpha: pieces cut from one solid body must stay solid where they meet (no sky through the thigh seam)
    a = out[..., 3]
    inner = blur((a > .5).astype(np.float32), 4, 2) > .999
    k = inner & (a < 1)
    out[k, :3] = out[k, :3] / np.maximum(a[k, None], 1e-4)
    out[k, 3] = 1.0
    return out


GAIT = {}
HEAD_RAISE_DEG = 110.   # raised, the gait head carries the upright frames' head line (nose within ~11 px of frame 13)
GAIT_LS = 0.22          # metres per backing step (each leg pair)
LEGS = {'fore': dict(x0=128, x1=172, ytop=160, paw=(136, 210), phase=.5),
        'hind': dict(x0=178, x1=224, ytop=156, paw=(195, 200), phase=0.)}


def gait_pieces():
    """the crouched, head-low frame 45 (mirrored, facing the door) split into body and two leg pairs; the legs overlap
    6 px up under the body and are drawn beneath it, so unmoved pieces add back to the solved matte"""
    if GAIT:
        return GAIT
    P, b = dog_frame(45, True)
    A = piece_canvas(P, b)
    shp = A.shape[:2]
    yy, xx = np.mgrid[:shp[0], :shp[1]].astype(np.float32)
    body_m = np.ones(shp, np.float32)
    for k, L in LEGS.items():
        inx = soft_region(shp, lambda x, y, L=L: (x >= L['x0']) & (x < L['x1']), 1)
        leg_m = np.clip((yy - L['ytop']) / 2. + .5, 0, 1) * inx
        cut = np.clip((L['ytop'] + 6 - yy) / 2. + .5, 0, 1)
        body_m = body_m * (1 - inx * (1 - cut))
        GAIT[k] = A * leg_m[..., None]
    head_m = soft_region(shp, lambda x, y: x < 142, 2)          # the head with a neck root that overlaps the body
    core = soft_region(shp, lambda x, y: x < 128, 2)            # what the body gives up to it
    GAIT['head'] = A * (body_m * head_m)[..., None]
    GAIT['body'] = A * (body_m * (1 - core))[..., None]
    cx, by = anchor(A)
    GAIT['anchor'] = (cx, by)
    return GAIT


def leg_offset(s_):
    """one leg pair's paw offset from its rest place (in steps) and lift, at gait phase s_ (cycles).
    stance (70 %): the paw is planted while the body moves away; swing (30 %): the paw steps back, lifted"""
    n = math.floor(s_); u = s_ - n
    if u < .7:
        return .35 - u, 0., n, True
    v = (u - .7) / .3
    e = v * v * (3 - 2 * v)
    return -.35 + .7 * e, math.sin(math.pi * v), n, False


def shear_leg(P, ytop, ybot, D, lift):
    """shear a leg piece: its top stays with the body, its paw sits D px away; lift shortens it (premultiplied)"""
    Hh = max(ybot - ytop, 1)
    e = 1 + lift / Hh
    coeffs = (1, -D / Hh, D * ytop / Hh, 0, e, -lift * ytop / Hh)
    ch = [np.asarray(Image.fromarray(P[..., c]).transform(P.shape[1::-1], Image.AFFINE, coeffs, Image.BICUBIC)) for c in range(4)]
    o = np.clip(np.stack(ch, 2), 0, 1).astype(np.float32)
    o[..., :3] = np.minimum(o[..., :3], o[..., 3:4])
    return o


def gait_sprite(x_body, x_start, head_raise=0.):
    """backing away on planted paws: the body follows the score; each leg pair is planted, then steps back"""
    g = gait_pieces()
    out = np.zeros_like(g['body'])
    def over(dst, src):
        return src + dst * (1 - src[..., 3:4])
    info = {}
    step_px = GAIT_LS * PPM / DS          # one step in source pixels
    for k in ('hind', 'fore'):
        L = LEGS[k]
        s_ = (x_body - x_start) / GAIT_LS + L['phase']
        D, lift, n, planted = leg_offset(s_)
        D0, _, _, _ = leg_offset(L['phase'])
        Dpx = (D - D0) * step_px          # zero at the start: the dog starts standing on its own frame
        leg = shear_leg(g[k], L['ytop'], L['paw'][1], Dpx, 5 * lift)
        out = over(out, leg)
        info[k] = dict(paw_src_x=L['paw'][0] + Dpx, plant=int(n), planted=bool(planted))
    out = over(out, g['body'])
    if head_raise > 0:   # the hanging head lifted about the neck, to bridge into and out of the upright frames
        out = over(out, rot_premult(g["head"], -HEAD_RAISE_DEG * head_raise, 136, 150))
    else:
        out = over(out, g['head'])
    out = out * main_component(out[..., 3])[..., None]
    a = out[..., 3]
    inner = blur((a > .5).astype(np.float32), 3, 2) > .999
    k = inner & (a < 1)
    out[k, :3] = out[k, :3] / np.maximum(a[k, None], 1e-4); out[k, 3] = 1.0
    return out, info


FL = {}
FL_PIVOT = (122, 124)    # frame 13: base of the neck at the withers (source px)


def flinch_sprite(theta):
    """round 3 bridge between the upright watching frame 13 and the head-low backing gait: frame 13 split along a soft
    diagonal (from the chest at (95,128) to the withers at (142,100)) into head+neck and body; the head+neck piece pivots
    down by theta degrees about the withers. The body overlaps the cut by 6 px so no gap opens on the back. The body is
    not moved: its paws stay where they stand."""
    if theta in FL:
        return FL[theta]
    P, b = dog_frame(13, False)
    A = piece_canvas(P, b)
    shp = A.shape[:2]
    yy, xx = np.mgrid[:shp[0], :shp[1]].astype(np.float32)
    line = 128 - (xx - 95) * (28. / 47.)                 # y of the cut at column x
    head_m = np.clip((line - yy) / 2. + .5, 0, 1) * soft_region(shp, lambda x, y: x < 146, 2)
    body_m = 1 - np.clip((line - 6 - yy) / 2. + .5, 0, 1) * soft_region(shp, lambda x, y: x < 140, 2)
    head = rot_premult(A * head_m[..., None], theta, FL_PIVOT[0], FL_PIVOT[1])
    body = A * body_m[..., None]
    out = head + body * (1 - head[..., 3:4])
    a = out[..., 3]
    inner = blur((a > .5).astype(np.float32), 3, 2) > .999
    k = inner & (a < 1)
    out[k, :3] = out[k, :3] / np.maximum(a[k, None], 1e-4); out[k, 3] = 1.0
    FL[theta] = out
    return out


def main_component(a, thr=.08, grow=2):
    """mask of the largest connected piece of matte (grown by `grow` px so fur strands touching the body stay);
    label propagation in numpy (no scipy here)"""
    from lib_matte import dilate
    m = dilate(a > thr, grow)
    lab = np.where(m, np.arange(m.size, dtype=np.int64).reshape(m.shape) + 1, 0)
    for _ in range(2000):
        p = np.pad(lab, 1)
        nb = np.maximum.reduce([p[1:-1, 1:-1], p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])
        nb = np.where(m, nb, 0)
        if (nb == lab).all():
            break
        lab = nb
    if lab.max() == 0:
        return np.ones_like(a)
    ids, cnt = np.unique(lab[lab > 0], return_counts=True)
    keep = lab == ids[cnt.argmax()]
    return blur(keep.astype(np.float32), 1, 1)


def bbox_crop(A):
    a = A[..., 3]; ys, xs = np.nonzero(a > .004)
    if len(xs) == 0:
        return A[:1, :1], (0, 0, 1, 1)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    return A[y0:y1, x0:x1], (x0, y0, x1, y1)


# ---------------------------------------------------------------- choreography (the score -> which matte, where)
CH = {c['to'] + ('' if c['to'] != 'watch' else str(k)): c['t'] for k, c in enumerate(SCORE['choices'])}
T_RET, T_W1, T_REF, T_W2, T_APP, T_LIE = [c['t'] for c in SCORE['choices']]
T_COMEIN = 26.4
I_RET, I_W1 = int(math.ceil(T_RET * 24)), int(math.ceil(T_W1 * 24))
FLINCH = [0, 18, 36, 54]  # round 3: frame 13, its head+neck lowered about the withers (deg), held in place, then the gait
RISE = [54, 36, 18]       # the gait raises its head before it stops, then frame 13 lifts its head again (no pop)
GAIT_OFF = (-30., -26.)   # px at the first / last gait frame (measured head points of the bridge drawings, see method.md)
GAIT_EASE = 9.
LIE_L0 = float(os.environ.get('LIE_L0', .45))      # round 3: the lie starts part-lowered (bridges the crouched walk frame)
LIE_LEAD = 24.            # px
LIE_REST0 = float(os.environ.get('LIE_REST0', .9))   # and its head carried forward-low, not curled under
CALL_WINDOWS = [(0.62, 1.38), (1.62, 2.30), (2.95, 3.70)]   # the voice comes first (sound.py places the calls here)
WALK = [43, 44, 45, 48]                 # the archive dog's head-low walk, mirrored to face the door (42, 46, 47: head lost in a tangle, skipped)
STRIDE = 0.068                           # metres travelled per walk frame (≈ the source's own advance per frame)
TURN = [14, 14, 26, 28, 31]              # the turn through the dog's front: 3/4 left, front, 3/4 right (source frames 17-22 were illegible tangles)
TURN_BACK = [26, 26, 14, 14]            # back to the door through the front


def cumdist():
    xs = np.array([f['dog']['x'] for f in FR]); d = np.concatenate([[0], np.cumsum(np.abs(np.diff(xs)))])
    return xs, d


XS, DIST = cumdist()


def watch_boil(t):
    """long watching hold: the archive dog's own small attention shifts (frames 12-13-14), never a frozen still"""
    seq = [13, 13, 14, 13, 13, 14, 13]   # frame 12 dropped: a ragged fragment above its back and a streak at the tail
    k = int(t / 0.9) % len(seq)
    return seq[k]


def dog_pose(i):
    """-> dict(kind, frame, mirror, facing, posture, lie params)"""
    t = i / 24.
    if t < T_RET:
        return dict(kind='frame', f=9, m=False, facing=1, posture='watch')
    if t < T_W1:   # flinch: the head drops through the dog's own frames 14-15-16, then it backs away on planted paws
        k = i - I_RET
        if k < len(FLINCH):
            return dict(kind='flinch', theta=FLINCH[k], xi=I_RET, facing=1, posture='back away')
        k2 = i - (I_RET + len(FLINCH)); k3 = I_W1 - 1 - i
        hr = max(0., 1 - k2 / 7.) if k2 < 7 else (max(0., 1 - k3 / 7.) if k3 < 7 else 0.)
        # round 3: the gait starts and ends GAIT_OFF px from the score (eased over GAIT_EASE frames) so its head meets the
        # bridge drawings; the offset is fed to the leg solver as body travel, so planted paws stay planted while it closes
        e0 = 1 - float(smooth(0, GAIT_EASE, k2)); e1 = 1 - float(smooth(0, GAIT_EASE, k3))
        return dict(kind='gait', facing=1, posture='back away', head_raise=hr, xoff_px=GAIT_OFF[0] * e0 + GAIT_OFF[1] * e1)
    if t < T_REF:  # stops and lifts its head again through 16-15-14 to 13 (no pop)
        k = i - I_W1
        if k < len(RISE):
            return dict(kind='flinch', theta=RISE[k], xi=I_W1 + len(RISE), facing=1, posture='watch')
        return dict(kind='frame', f=13, m=False, facing=1, posture='watch')
    if t < T_W2:   # turns its back: the archive dog's own turn at its own rate, then lies down with its back to them
        k = int((t - T_REF) * 12)
        if k < len(TURN):
            f = TURN[k]
            return dict(kind='frame', f=f, m=False, facing=1 if f in (14, 26) else -1, posture='turn away')
        L = float(smooth(4.3, 5.0, t)); rest = .45 + .55 * float(smooth(5.6, 6.5, t))
        return dict(kind='lie', L=L, head_up=0., look=0., rest=rest, face_right=True, look_back=0.,
                    facing=-1, posture='back turned, lying' if L > .95 else 'back turned')
    if t < T_APP:  # turns back to look: head first, over the shoulder; rises; then the archive turn, backward
        if t < T_W2 + .55:
            L = 1 - float(smooth(T_W2 + .2, T_W2 + .55, t))   # head turns back to the door at once (hard substitution, no dissolve)
            return dict(kind="lie", L=L, head_up=1., look=0., rest=.62, face_right=True, look_back=1.,
                        facing=1, posture='looks back, rising')
        k = int((t - T_W2 - .55) * 12)
        R = TURN_BACK
        if k < len(R):
            f = R[k]
            return dict(kind='frame', f=f, m=False, facing=1, posture='turn back')
        return dict(kind='frame', f=watch_boil(t - T_W2), m=False, facing=1, posture='watch')
    if t < T_LIE:  # comes, head low: mirrored head-low walk, one frame per STRIDE metres travelled
        k0 = int((t - T_APP) * 12)
        if k0 < 2:
            return dict(kind='frame', f=[14, 14][k0], m=False, facing=1, posture='head lowers')
        d = DIST[i] - DIST[int(T_APP * 24)]
        k = int(d / STRIDE) % len(WALK)
        return dict(kind='frame', f=WALK[k], m=True, facing=1, posture='walk head low')
    # lies down across the sill; hears "come in": looks in, then settles
    L = LIE_L0 + (1 - LIE_L0) * float(smooth(T_LIE, T_LIE + .75, t))   # round 3: starts already part-lowered, like the crouched walk frame
    look = float(smooth(T_COMEIN, T_COMEIN + .16, t) * (1 - smooth(28.15, 28.35, t)))
    look = 1.0 if look >= .5 else 0.0      # round 3: a hard substitution (the dissolve left a double head at 26.50 and 28.29 s)
    rest = float(smooth(28.2, 28.9, t))
    head_up = float(L * (1 - rest))
    rest = max(rest, .5 * L, LIE_REST0 * (1 - float(smooth(T_LIE, T_LIE + .5, t))))   # head comes up from the walk's low carriage, then held level
    return dict(kind='lie', L=L, head_up=head_up, look=look, rest=rest, facing=1,
                posture='lie' if L > .95 else 'lying down', looking_in=look > .5)


def pose_key(i):
    p = dog_pose(i)
    return (p['kind'], p.get('f'), p.get('m')) if p['kind'] == 'frame' else None


def x_drawn(i):
    """substitution: a drawing (matted frame) is placed where the score has the dog when that drawing appears and
    stays there while it is held, so nothing slides under a held frame; the next drawing carries the travel"""
    p = dog_pose(i)
    if 'xi' in p:            # a bridge drawing held where the dog stood when the bridge began
        return FR[p['xi']]['dog']['x']
    k = pose_key(i)
    if k is None:
        return FR[i]['dog']['x']
    j = i
    while j > 0 and pose_key(j - 1) == k:
        j -= 1
    return FR[j]['dog']['x']


def dog_sprite(i):
    p = dog_pose(i)
    if p['kind'] == 'frame':
        P, b = dog_frame(p['f'], p['m'])
    elif p['kind'] == 'flinch':
        A = flinch_sprite(p['theta'])
        P, b = A, (0, 0, A.shape[1], A.shape[0])       # uncropped, frame 13's own anchor: the body and paws do not move
        p['anchor'] = anchor(piece_canvas(*dog_frame(13, False)))
    elif p['kind'] == 'gait':
        i0 = I_RET + len(FLINCH)
        A, info = gait_sprite(FR[i]['dog']['x'] + p['xoff_px'] / PPM, FR[i0]['dog']['x'] + dog_pose(i0)['xoff_px'] / PPM, p.get('head_raise', 0.))
        p['legs'] = info
        P, b = A, (0, 0, A.shape[1], A.shape[0])        # uncropped: the body keeps one fixed anchor
        p['anchor'] = gait_pieces()['anchor']
    else:
        A = lying_sprite(p['L'], p['head_up'], p['look'], p['rest'], p.get('face_right', False), p.get('look_back', 0.))
        A = A * main_component(A[..., 3])[..., None]          # drop matte debris detached from the body
        P, b = bbox_crop(A)
    return p, P, b


def anchor(P):
    a = P[..., 3]
    cols = a.sum(0); cx = float((cols * np.arange(a.shape[1])).sum() / max(cols.sum(), 1e-6))
    rows = np.nonzero((a > .3).sum(1) > 2)[0]
    by = float(rows.max() + 1) if len(rows) else a.shape[0]
    return cx, by


# ---------------------------------------------------------------- compositing helpers
def derim_edge(S, D, band_r=5, core_r=8):
    """edge colour match against the actual backdrop (round 3): inside a band_r px band at the silhouette edge, a fur
    pixel may not be lighter than the brighter of (a) the solid fur core beside it and (b) the backdrop behind it.
    Where the backdrop is dark (the lower doorway at dusk) the edge falls to the core's value, so no pale line is drawn
    round the head; against bright light the cap is the light itself and nothing changes. Premultiplied in, out."""
    a = S[..., 3]
    F = S[..., :3] / np.maximum(a[..., None], 1e-4)
    L = F.mean(2)
    solid = (a > .97).astype(np.float32)
    core = (blur(solid, band_r, 2) > .999).astype(np.float32)
    den = blur(core, core_r, 2)
    Lc = blur(L * core, core_r, 2) / np.maximum(den, 1e-4)
    Lc = np.where(den > .01, Lc, L)
    Lb = blur(D.mean(2), 3, 2)
    cap = np.maximum(Lc, Lb)
    band = (a > .004) & (core < .5)
    k = np.where(band & (L > cap), cap / np.maximum(L, 1e-4), 1.0).astype(np.float32)
    out = S.copy()
    out[..., :3] = S[..., :3] * k[..., None]
    return out


def place(canvas, P, x, y, wrap=0.0, wrap_col=None, derim=False):
    """premultiplied over at integer offset; optional light wrap (the background bleeds light into fractional edges)"""
    h, w = P.shape[:2]
    X0, Y0 = int(round(x)), int(round(y))
    cx0, cy0 = max(X0, 0), max(Y0, 0); cx1, cy1 = min(X0 + w, W), min(Y0 + h, H)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    S = P[cy0 - Y0:cy1 - Y0, cx0 - X0:cx1 - X0]
    D = canvas[cy0:cy1, cx0:cx1]
    a = S[..., 3:4]
    if derim:
        S = derim_edge(S, D)
    if wrap > 0:
        bgb = blur(D.copy(), 1, 1) if wrap_col is None else wrap_col[cy0:cy1, cx0:cx1]   # only light actually behind the edge
        inner = blur(S[..., 3], 3, 2)[..., None]
        edge = np.clip(a * (1 - inner) * 3.0, 0, 1)
        k = np.clip(edge * wrap, 0, .6)
        # energy-conserving wrap: a share of the edge's own colour is replaced by the light behind it, never added,
        # so an edge can never be brighter than the brighter of fur and background
        canvas[cy0:cy1, cx0:cx1] = S[..., :3] * (1 - k) + bgb * k * a + D * (1 - a)
    else:
        canvas[cy0:cy1, cx0:cx1] = S[..., :3] + D * (1 - a)


def scale_premult(P, s):
    h, w = P.shape[:2]
    return resize_premult(P, max(1, int(round(w * s))), max(1, int(round(h * s))))


def grade_dusk(P, warm, dark=.48, grain=.018, seed=0):
    """relight a greyscale (archive) matte for dusk: cool, dimmer; warm door light by amount `warm`.
    Grain is renewed per frame inside the alpha only (print grain stays alive on held frames)."""
    a = P[..., 3:4]
    F = P[..., :3] / np.maximum(a, 1e-4)
    g = F.mean(2, keepdims=True)
    # edge colour match (decontamination at playback scale): a fractional edge pixel may not be lighter than the solid
    # fur beside it, so no pale outline is carried from the sunlit source
    solid = (a[..., 0] > .95).astype(np.float32)
    den = blur(solid, 4, 2)
    gi = blur(g[..., 0] * solid, 4, 2) / np.maximum(den, 1e-4)
    band = (a[..., 0] < .95) & (den > .02)
    g0 = g[..., 0]
    g0[band] = np.minimum(g0[band], gi[band])
    g = g0[..., None]
    r = np.random.default_rng(seed)
    g = np.clip(g + r.normal(0, grain, g.shape).astype(np.float32) * (0.5 + g), 0, 1)
    cool = np.array([.62, .66, .86], np.float32) * dark
    hot = np.array([1.25, .86, .50], np.float32)
    col = g ** 1.15 * (cool + warm * hot)
    return np.concatenate([np.clip(col, 0, 1) * a, a], 2).astype(np.float32)


# ---------------------------------------------------------------- person
WOMAN = None
HAND = None


def poly_layer(polys, col, alpha=1.0):
    cov = coverage(polys, W, H, ss=3)
    return cov, col


def person(canvas, i, t, light):
    global WOMAN, HAND
    if WOMAN is None:
        z = load_npz(os.path.join(C, 'woman.npz')); WOMAN = z['P'].astype(np.float32)
        z = load_npz(os.path.join(C, 'hand.npz')); HAND = z['P'].astype(np.float32)[:, ::-1].copy()   # fingers to the right
    pr = FR[i]['person']
    s = 0.70
    px = sx(pr['x'])
    sit = pr['sit']
    calling = 1.0 if any(a0 <= t < a1 for a0, a1 in CALL_WINDOWS) else 0.0
    lean = calling * (0.6 + 0.4 * math.sin(t * 9)) if calling else 0
    # torso: matte (Straight Talk), cropped at the hip as she sits
    crop_y = int(WOMAN.shape[0] - sit * 70)
    Wm = WOMAN[:crop_y].copy()
    fade = np.clip((crop_y - np.arange(crop_y)) / 8., 0, 1)[:, None]
    Wm *= fade[..., None]
    Wd = grade_dusk(scale_premult(Wm, s), warm=.06 * light, dark=.13, grain=.02, seed=i * 7 + 1)
    hip_stand = GY - 10 - 117
    hip_sit = GY - 22
    hip = hip_stand * (1 - sit) + hip_sit * sit
    wh = Wd.shape[0]
    bottom_src = crop_y * s
    top = hip - bottom_src + (WOMAN.shape[0] * s - (WOMAN.shape[0] * s)) - 0
    top = hip - (WOMAN.shape[0] - sit * 70) * s
    left = px - Wd.shape[1] / 2 + lean * 5
    # legs (reconstruction, drawn): standing pair, scissoring as she steps aside, folding as she sits
    walk = (pr['x'] < -0.3) and sit < .95 and pr['x'] > -1.24
    ph = math.sin(t * 9) if walk else 0
    hx = px + 2
    st_l = [(hx - 27, hip - 6), (hx - 1, hip - 6), (hx - 4 + 8 * ph, GY - 4), (hx - 22 + 8 * ph, GY - 4)]
    st_r = [(hx + 1, hip - 6), (hx + 27, hip - 6), (hx + 22 - 8 * ph, GY - 4), (hx + 4 - 8 * ph, GY - 4)]
    knee = (hx + 58, GY - 66)
    si_l = [(hx - 24, hip_sit - 12), (hx + 4, hip_sit - 20), (knee[0] + 6, knee[1] - 4), (knee[0] + 14, GY - 2), (knee[0] - 4, GY - 2), (knee[0] - 8, knee[1] + 14), (hx - 22, hip_sit + 16)]
    si_r = si_l
    def lerp(A, B, u):
        n = max(len(A), len(B))
        A = A + [A[-1]] * (n - len(A)); B = B + [B[-1]] * (n - len(B))
        return [(a[0] * (1 - u) + b[0] * u, a[1] * (1 - u) + b[1] * u) for a, b in zip(A, B)]
    legs = [lerp(st_l, si_l, sit), lerp(st_r, si_r, sit)]
    cov = coverage(legs, W, H, ss=3)
    cov = blur(cov, 1, 1)
    legcol = np.array([.035, .04, .06], np.float32) + light * np.array([.05, .03, .015])
    canvas[:] = canvas * (1 - cov[..., None]) + legcol * cov[..., None]
    # hand + forearm (Door to Heaven): reaching at shoulder height, or offered low from the seat
    reach, low = pr['reach'], pr['low']
    hand_amt = max(reach, low)
    if hand_amt > 0.02:
        Hs = grade_dusk(scale_premult(HAND, 0.56), warm=.25 * light, dark=.26, grain=.02, seed=i * 7 + 2)
        sh_y = top + 48 * s / .7
        if low > reach:
            ang = -16; ox = px + 30 + 60 * low; oy = GY - 40 - 20 * (1 - low)
        else:
            ang = -10; ox = px + 10 + 74 * reach; oy = sh_y + 6
        Hr = rot_premult(np.pad(Hs, [(60, 60), (60, 60), (0, 0)]), ang, Hs.shape[1] / 2 + 60, Hs.shape[0] / 2 + 60)
        Hr, _ = bbox_crop(Hr)
        Hr *= min(1, hand_amt * 3)
        place(canvas, Hr, ox - 30, oy - Hr.shape[0] / 2, wrap=.5)
    place(canvas, Wd, left, top, wrap=.9)
    return dict(px=px, top=top)


# ---------------------------------------------------------------- door leaf (Straight Talk, rectified) and its curtain
LEAF = None


def door_leaf(canvas, t, interior):
    global LEAF
    if LEAF is None:
        z = load_npz(os.path.join(C, 'door_leaf.npz')); LEAF = (z['P'].astype(np.float32), z['lace'].astype(np.float32), z['win'])
    P, lace, win = LEAF
    th = math.radians(16 + 92 * float(smooth(6.2, 7.0, t)))
    x0, y0, x1, y1 = DOOR
    w = (x1 - x0) * math.cos(th)
    if w < 2:
        return 1.0
    # graded leaf: the room side of a white door at dusk; the curtained window backlit by the lamp
    g = P[..., :3].mean(2, keepdims=True)
    col = g * np.array([.40, .42, .52], np.float32) * (0.65 + 0.35 * math.cos(th))
    lamp = np.array([1.0, .70, .38], np.float32)
    l3 = lace[..., None]
    winmask = (lace > 0)[..., None]
    glow = lamp * (1 - .85 * l3) * .75 + l3 * np.array([.22, .17, .14])   # backlit sheer: light through the gaps, cloth glows dim
    col = np.where(winmask, glow, col)
    leaf = np.concatenate([col, np.ones_like(g)], 2).astype(np.float32)
    # perspective: far edge recedes into the room
    sh = math.sin(th)
    dst = [(x0, y0), (x0, y1), (x0 + w, y1 - 10 * sh), (x0 + w, y0 + 16 * sh)]
    # inverse quad: PIL wants for each output corner the source corner; build the leaf onto the canvas via QUAD
    bw, bh = int(math.ceil(w)) + 2, y1 - y0
    # map output (local) coords to leaf coords with a simple column scale + per-column vertical compression
    xs = np.arange(bw, dtype=np.float32)
    u = np.clip(xs / max(w, 1), 0, 1)
    top = 16 * sh * u; bot = bh - 10 * sh * u
    yy = np.arange(bh, dtype=np.float32)[:, None]
    v = (yy - top[None, :]) / (bot - top)[None, :]
    inside = (v >= 0) & (v <= 1) & (xs[None, :] <= w)
    lx = np.clip((u * (P.shape[1] - 1)).astype(int), 0, P.shape[1] - 1)[None, :].repeat(bh, 0)
    ly = np.clip((v * (P.shape[0] - 1)).astype(int), 0, P.shape[0] - 1)
    S = leaf[ly, lx] * inside[..., None]
    place(canvas, S, x0, y0)
    return 1.0 - w / (x1 - x0)    # how open the doorway is


# ---------------------------------------------------------------- clouds and haze
CLOUD = {}


def cloud(k):
    if k not in CLOUD:
        if len(CLOUD) > 6:
            CLOUD.clear()
        CLOUD[k] = np.load(os.path.join(C, 'cloud/c%02d.npz' % k))['P'].astype(np.float32)
    return CLOUD[k]


def cloud_layer(t):
    u = t * 1.85
    k0 = int(u) % 62; k1 = (k0 + 1) % 62; f = u - int(u)
    P = cloud(k0) * (1 - f) + cloud(k1) * f       # premultiplied interpolation between solved frames
    P = resize_premult(P, 900, 506)
    a = P[..., 3:4]
    Fc = P[..., :3] / np.maximum(a, 1e-4)
    g = Fc.mean(2, keepdims=True)
    k = t / 38.
    lit = np.array([1.0, .62, .52]) * (1 - .4 * k); shade = np.array([.30, .26, .42]) * (1 - .3 * k)
    col = shade + (lit - shade) * np.clip((g - .45) / .5, 0, 1)
    yy = np.arange(506)[:, None, None]
    fade = np.clip((420 - yy) / 160., 0, 1) * .7
    a2 = a * fade
    return np.concatenate([col * a2, a2], 2).astype(np.float32)


# ---------------------------------------------------------------- one frame
def dog_layer(i):
    pose, P, b = dog_sprite(i)
    # dog placement: alpha centroid -> score x, lowest solid row -> floor line (a gait sprite keeps its body's anchor)
    Ps = scale_premult(P, DS)
    if 'anchor' in pose:
        cx, by = pose['anchor'][0] * DS, pose['anchor'][1] * DS
    else:
        cx, by = anchor(Ps)
    xd = x_drawn(i)
    if pose['kind'] == 'lie' and not pose.get('face_right'):     # set further in as it lies down (round 3: its own ramp,
        r_in = float(smooth(T_LIE, T_LIE + .75, i / 24.))         # starting LIE_LEAD px back so it meets the walk frame)
        inward = 48 * r_in - LIE_LEAD * (1 - r_in)
    else:
        inward = 0.
    left = sx(xd) - cx - inward + pose.get('xoff_px', 0.)
    top = GY + 4 - by
    if pose['kind'] == 'gait':
        for k, v in pose['legs'].items():
            v['paw_screen_x'] = round(int(round(left)) + v['paw_src_x'] * DS, 2)
    return pose, Ps, left, top, xd


def mix_layers(Pa, la, ta, Pb, lb, tb, w):
    """premultiplied dissolve of two placed sprites in their union box"""
    la, ta, lb, tb = int(round(la)), int(round(ta)), int(round(lb)), int(round(tb))
    x0, y0 = min(la, lb), min(ta, tb)
    x1, y1 = max(la + Pa.shape[1], lb + Pb.shape[1]), max(ta + Pa.shape[0], tb + Pb.shape[0])
    M = np.zeros((y1 - y0, x1 - x0, 4), np.float32)
    M[ta - y0:ta - y0 + Pa.shape[0], la - x0:la - x0 + Pa.shape[1]] += (1 - w) * Pa
    M[tb - y0:tb - y0 + Pb.shape[0], lb - x0:lb - x0 + Pb.shape[1]] += w * Pb
    return M, x0, y0


DISSOLVES = []   # (first frame, frames): premultiplied dissolves, unused; pops are bridged by intermediate drawings instead


def render(i):
    global ST
    if ST is None:
        ST = static_layers()
    t = i / 24.
    can = np.zeros((H, W, 3), np.float32)
    # sky, clouds (smoke edge class), tree line (foliage edge class)
    can[:] = sky(t)
    place(can, cloud_layer(t), 520 - t * 3, 20)
    ta = ST['tree_a'][..., None]
    can[:] = can * (1 - ta) + np.array([.035, .045, .065]) * ta
    # porch floor, then facade
    fl = ST['floor']
    can[586:] = fl[586:]
    wx1 = 610
    can[:586, :wx1] = ST['wall'][:586, :wx1]
    can[:586, wx1 - 14:wx1] = np.array([.24, .25, .32])          # corner board
    # door opening: interior seen through it
    x0, y0, x1, y1 = DOOR
    can[y0:y1, x0:x1] = ST['interior'][y0:y1, x0:x1]
    opened = door_leaf(can, t, None)
    light = max(.05, opened)                                     # the sliver when ajar, the full door once open
    # casing
    for (a0, b0, a1, b1) in [(x0 - 14, y0 - 14, x0, y1), (x1, y0 - 14, x1 + 14, y1), (x0 - 14, y0 - 14, x1 + 14, y0)]:
        can[b0:b1, a0:a1] = np.array([.30, .30, .36]) * (1 + .5 * light * np.array([1, .8, .55]))
    # sill: a board across the opening, toward the porch
    can[584:596, x0 - 18:x1 + 18] = np.array([.26, .23, .24]) + light * np.array([.25, .17, .08])
    can[594:597, x0 - 18:x1 + 18] *= .6
    # porch steps at the porch end
    xe = int(sx(SCORE['places']['porch_end']))
    can[586:, xe:] = np.array([.05, .055, .075])
    can[640:, xe + 20:] = np.array([.09, .085, .10])
    # door light on the floor (emission) minus the dog's shadow, computed after the dog sprite is known
    pose, Ps, left, top, xd = dog_layer(i)
    for i0, n in DISSOLVES:                # premultiplied dissolve across a substitution that would pop
        if i0 <= i < i0 + n:
            _, Po, lo, to, _ = dog_layer(i0 - 1)
            w = (i - i0 + 1) / (n + 1.)
            Ps, left, top = mix_layers(Po, lo, to, Ps, left, top, w)
            pose = dict(pose, dissolve=round(w, 3))
    dist = abs(xd)
    warm = light * math.exp(-dist / 1.6) * .22 + .03
    Pd = grade_dusk(Ps, warm, dark=.44 - .12 * light * math.exp(-dist / 1.2), seed=i * 7 + 3)
    wrapk = .3 + .9 * light * math.exp(-dist / 1.5)
    if pose['kind'] == 'lie' and pose.get('L', 0) > .95:
        k = 1 + .012 * math.sin(t * 2 * math.pi / 1.7)
        Pd = resize_premult(Pd, Pd.shape[1], max(1, int(Pd.shape[0] * k)))
        top -= Pd.shape[0] - Ps.shape[0]
    # shadow on the floor: the dog's own fractional alpha, projected away from the door light
    sh = np.zeros((H, W), np.float32)
    a = Pd[..., 3]
    hs = max(2, int(a.shape[0] * .22))
    proj = np.asarray(Image.fromarray(a[::-1]).resize((a.shape[1], hs), Image.BILINEAR))
    ox, oy = int(left), int(GY + 1)
    for r in range(hs):                      # shear toward the right (away from the door)
        sh_x = ox + int(r * 1.8 * light)
        yy = oy + r - 2
        if 0 <= yy < H:
            xs0, xs1 = max(sh_x, 0), min(sh_x + a.shape[1], W)
            if xs1 > xs0:
                sh[yy, xs0:xs1] = np.maximum(sh[yy, xs0:xs1], proj[r, xs0 - sh_x:xs1 - sh_x])
    sh = blur(sh, 2, 2)
    # contact darkening (always), door light spill (when open), with the shadow cut out of it
    can *= (1 - .55 * sh[..., None] * (ST['yy'][..., None] > 586))
    spill = ST['spill'] * (1 - .9 * sh)
    can += (light * 1.15 * spill)[..., None] * np.array([1.0, .66, .32], np.float32)
    # person
    pinfo = person(can, i, t, light)
    # dog (light wrap from what is behind it)
    # contact shadow: the dog's own alpha, pressed onto the boards just under it (the lit sill does not shine through the fur)
    X0, Y0 = int(round(left)), int(round(top))
    ca = np.zeros((H, W), np.float32)
    hh, ww = Pd.shape[:2]
    y0c, x0c = max(Y0 + 4, 0), max(X0, 0); y1c, x1c = min(Y0 + 4 + hh, H), min(X0 + ww, W)
    if y1c > y0c and x1c > x0c:
        ca[y0c:y1c, x0c:x1c] = Pd[y0c - Y0 - 4:y1c - Y0 - 4, x0c - X0:x1c - X0, 3]
    ca = blur(ca, 3, 2) * (ST['yy'] > 580)
    can *= (1 - .8 * ca[..., None])
    # light wrap only from what is behind the dog in depth (the wall, the doorway, the sky), never from the floor
    wc = blur(can.copy(), 1, 1); wc[584:] = 0
    if not os.environ.get('NODOG'):      # NODOG: verification plate, the same frame (shadows included) without the dog itself
        place(can, Pd, left, top, wrap=wrapk, wrap_col=wc, derim=True)
    # dusk air: haze in the door's beam, density from the solved cloud matte (smoke), drifting slowly
    hz = cloud(int(t * 0.7) % 62)[..., 3]
    hz = np.asarray(Image.fromarray(hz).resize((W, H), Image.BILINEAR))
    hz = np.roll(hz, int(t * 6), 1)
    beam = ST['beam'] * (.35 + .65 * hz) * light * .16
    can += beam[..., None] * np.array([1.0, .72, .42], np.float32)
    # overall print grain + gentle vignette
    yy, xx = ST['yy'], ST['xx']
    vig = 1 - .28 * (((xx - 640) / 900.) ** 2 + ((yy - 380) / 600.) ** 2)
    can *= vig[..., None]
    can += np.random.default_rng(i).normal(0, .012, (H, W, 1)).astype(np.float32)
    img = (np.clip(can, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8)
    if os.environ.get('NODOG'):
        return img, pose, {}
    # measured from what was drawn: dog alpha centroid and footprint on screen
    ah = Pd[..., 3]
    cols = ah.sum(0); rows = ah.sum(1)
    mx = left + float((cols * np.arange(len(cols))).sum() / max(cols.sum(), 1e-6))
    my = top + float((rows * np.arange(len(rows))).sum() / max(rows.sum(), 1e-6))
    ys, xs = np.nonzero(ah > .5)
    # the head's lead point: the outermost solid column on the side the dog faces, and its mean row
    cs = np.nonzero((ah > .5).sum(0) > 0)[0]
    if len(cs):
        c = cs.min() if pose.get('facing', 1) == 1 else cs.max()
        rr = np.nonzero(ah[:, c] > .5)[0]
        nose = (round(left + c, 1), round(top + float(rr.mean()), 1))
    else:
        nose = (None, None)
    # head point: centroid of the solid matte in the 45 px nearest the side it faces, above the floor contact rows
    hx, hy = None, None
    if len(cs):
        sol = (ah > .5); sol[max(0, int(GY - 14 - top)):] = False
        cs2 = np.nonzero(sol.sum(0) > 0)[0]
        if len(cs2):
            band = (np.arange(sol.shape[1]) <= cs2.min() + 45) if pose.get('facing', 1) == 1 else (np.arange(sol.shape[1]) >= cs2.max() - 45)
            yy_, xx_ = np.nonzero(sol & band[None, :])
            hx, hy = round(left + float(xx_.mean()), 1), round(top + float(yy_.mean()), 1)
    meas = dict(head_x=hx, head_y=hy, nose_x=nose[0], nose_y=nose[1], x_screen=round(mx, 2), y_screen=round(my, 2), dog_left=round(left + xs.min(), 1), dog_right=round(left + xs.max(), 1),
                dog_top=round(top + ys.min(), 1), dog_bottom=round(top + ys.max(), 1), door_open=round(opened, 3))
    return img, pose, meas


def main():
    args = sys.argv[1:]
    a, b = 0, 768
    for k, v in enumerate(args):
        if v == '--frames':
            a, b = [int(x) for x in args[k + 1].split(':')]
    od = os.path.join(C, 'frames'); os.makedirs(od, exist_ok=True)
    tr = {}
    for i in range(a, b):
        img, pose, meas = render(i)
        Image.fromarray(img).save(os.path.join(od, 's%04d.jpg' % i), quality=93)
        p = {k: v for k, v in pose.items() if k in ('kind', 'f', 'm', 'facing', 'posture', 'L', 'look', 'rest', 'looking_in', 'legs', 'dissolve', 'theta', 'head_raise')}
        tr[i] = dict(pose=p, **meas)
    json.dump(tr, open(os.path.join(C, 'trace_part_%04d_%04d.json' % (a, b)), 'w'))
    print('rendered', a, b)


if __name__ == '__main__':
    main()
