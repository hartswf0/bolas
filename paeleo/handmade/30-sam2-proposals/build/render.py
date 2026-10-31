"""SCION 30 / SAM 2: render the 32 s threshold scene (and the 3 s cards) from accepted mask proposals.

World: a cut-away section of a house at dusk. Outside (left) the porch, inside (right) a lamp-lit room; the wall
section with the doorway between them. The dog, the door leaf, the person (standing, sitting) and the hand are all
accepted mask proposals over public-domain archive frames, placed whole or as part proposals split at prompt points.
Nothing of the dog is drawn: where no source frame shows a part (folded legs), the part is kept out of view.

python3 render.py                 -> pipes 912 frames (title + scene + end card) to ffmpeg -> cache/picture.mp4, trace.json
python3 render.py --stills t1 t2  -> cache/still_<t>.jpg only (scene time in seconds)"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from common import *
from pieces import cut, to_piece, key, neck_cut, halfplane, head_region, CORR, record

W, H = 1280, 720
FPS = 24
FR = SCORE['frames']
FEET = 602                 # porch floor line under the dog's feet (screen y)
WX0, WX1 = 985, 1020       # wall section (outer face, inner face)
LINTEL = 200
SILL_Y = 574
S = 1.65                   # source px -> stage px for the dog (dog ~ 1 m ~ 185 px)
PXM = 205.0                # stage px per metre along the porch


def X(x):
    """score metres -> screen x of the dog's body centroid (threshold side right)."""
    return 985.0 - PXM * (x - 0.59)


def smooth(a):
    a = min(max(a, 0.0), 1.0)
    return a * a * (3 - 2 * a)


def font(n, size):
    return ImageFont.truetype(os.path.join(REPO, 'tools/paeleo/fonts', n), size)


# ---------------------------------------------------------------- world (computed, rights: ours)
rng = np.random.default_rng(30)


def vgrad(h, c0, c1):
    t = np.linspace(0, 1, h)[:, None]
    return (np.array(c0)[None, :] * (1 - t) + np.array(c1)[None, :] * t)


EDGE = 584                 # top of the porch's front board: the camera stands low in the yard, so the floor surface is
                           # not seen and everything below this line at the doorway's depth is behind the board


def build_world():
    """-> (background dusk, background lit, foreground RGBA dusk, foreground RGBA lit); all computed, nothing found."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.zeros((H, W, 3), np.float32)
    sky = vgrad(H, (14, 20, 42), (104, 86, 100))
    img[:] = sky[:, None, :]
    # distant tree line: low-frequency ridge with fine noise (computed)
    xs = np.arange(W)
    n = rng.normal(0, 1, W + 40)
    fine = np.convolve(n, np.ones(9) / 9, 'same')[20:W + 20] * 10
    ridge = 470 + 14 * np.sin(xs / 97.) + 9 * np.sin(xs / 41. + 1.3) + fine
    tree = yy > ridge[None, :]
    img[tree] = img[tree] * .22 + np.array([20, 22, 32]) * .78
    # porch rail on the far side and its balusters
    rail = (yy >= 492) & (yy < 497) & (xx > 104) & (xx < WX0)
    img[rail] = np.array([30, 28, 36])
    bal = ((xx % 46) < 3) & (yy >= 497) & (yy < EDGE) & (xx > 104) & (xx < WX0)
    img[bal] = img[bal] * .4 + np.array([28, 26, 34]) * .6
    # porch roof eave and the corner post at the steps
    img[yy < 34] = np.array([16, 14, 20])
    post = (xx >= 96) & (xx < 112)
    img[post] = np.array([26, 24, 30])
    # ---- room interior (right of the wall section)
    room = np.zeros_like(img)
    room[:] = vgrad(H, (92, 64, 40), (140, 96, 56))[:, None, :]
    lamp = np.exp(-(((xx - 1190) / 130.) ** 2 + ((yy - 230) / 160.) ** 2))
    room += lamp[..., None] * np.array([96, 74, 38])
    room[yy < 70] = np.array([40, 28, 20])                     # ceiling cut
    skirt = (yy >= 566) & (yy < EDGE)
    room[skirt] = np.array([66, 44, 28])
    inside = xx >= WX1
    dark_room = room * np.array([.16, .15, .18]) + np.exp(-(((xx - 1190) / 90.) ** 2 + ((yy - 230) / 110.) ** 2))[..., None] * np.array([40, 28, 14])
    dusk = img.copy(); lit = img.copy()
    dusk[inside] = dark_room[inside]; lit[inside] = room[inside]
    # wall section above the doorway and the far jamb seen through the gap
    wall = (xx >= WX0) & (xx < WX1) & (yy < LINTEL)
    face = np.array([38, 32, 34]) + rng.normal(0, 2, (H, W, 1))
    dusk[wall] = face[wall]; lit[wall] = face[wall]
    gap = (xx >= WX0) & (xx < WX1) & (yy >= LINTEL)
    dusk[gap] = np.array([22, 16, 14]); lit[gap] = np.array([96, 66, 40])
    eave = (yy < 34) & (xx >= WX0 - 30)
    dusk[eave] = np.array([12, 10, 14]); lit[eave] = np.array([12, 10, 14])
    # the light that comes out: a warm wash in the porch air, strongest at the doorway
    air = np.clip(1 - (WX0 - xx) / 640., 0, 1) ** 1.8 * np.exp(-((yy - 470) / 210.) ** 2) * (xx < WX0)
    lit = lit + air[..., None] * np.array([120, 80, 36]) * .55
    # ---- foreground: the porch front board and lattice skirting; the cut face of the house floor
    fg = np.zeros((H, W, 4), np.float32)
    board = (yy >= EDGE) & (yy < EDGE + 20)
    fg[board] = [46, 40, 44, 255]
    fg[(yy >= EDGE) & (yy < EDGE + 2)] = [84, 74, 74, 255]
    lat = yy >= EDGE + 20
    u = (xx + yy) % 34; v = (xx - yy) % 34
    slat = (u < 5) | (v < 5)
    fg[lat] = [14, 12, 16, 255]
    fg[lat & slat] = [40, 36, 40, 255]
    house = (xx >= WX0) & (yy >= EDGE)
    fg[house] = [30, 24, 24, 255]
    fg[house & (yy < EDGE + 2)] = [70, 56, 50, 255]
    # steps down at the far left
    for k in range(3):
        stp = (xx < 96 - k * 30) & (yy >= EDGE + 34 * (k + 1)) & (yy < EDGE + 34 * (k + 1) + 16)
        fg[stp] = [50, 44, 48, 255]
    fg[..., :3] += rng.normal(0, 2, (H, W, 1))
    fg_lit = fg.copy()
    glow = np.clip(1 - (WX0 - xx) / 520., 0, 1) ** 1.5 * (yy >= EDGE) * (yy < EDGE + 20) * (xx < WX0)
    fg_lit[..., :3] += glow[..., None] * np.array([120, 80, 40])
    return np.clip(dusk, 0, 255), np.clip(lit, 0, 255), np.clip(fg, 0, 255), np.clip(fg_lit, 0, 255)


def sill_layer():
    """the sill board in front, drawn over the dog's legs region at the threshold (computed)"""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((WX0 - 10, SILL_Y, WX1 + 10, EDGE + 1), fill=(70, 54, 44, 255))
    d.line([(WX0 - 10, SILL_Y), (WX1 + 10, SILL_Y)], fill=(130, 100, 66, 255), width=2)
    return im


# ---------------------------------------------------------------- non-dog proposals
def door_leaf():
    """door leaf: Straight Talk f31, SAM proposal door#5 (closed door, face-on), graded to dusk-warm"""
    pim, info = cut('door', 31, False, scale=1.0, tone=None)
    a = np.asarray(pim, dtype=np.float32) / 255.
    g = a[..., :3] @ np.array([.299, .587, .114])
    rgb = np.stack([g * 150 + 30, g * 118 + 24, g * 84 + 18], -1)
    out = np.dstack([rgb, a[..., 3] * 255]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA').resize((170, SILL_Y - LINTEL), Image.LANCZOS)


def person_stand():
    """person#1: our box+colour proposal on Straight Talk f2, used as a backlit silhouette; the lower legs are not in
    the source frame, so the silhouette fades into the dark of the doorway floor instead of being completed."""
    mi = Image.open(os.path.join(CACHE, 'person_f002.png')).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    m = np.asarray(mi, dtype=np.float32) / 255.      # closing (dilate 5, erode 5) fills the pale hair clip
    ys, xs = np.nonzero(m > .5)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = m.shape
    fade = np.clip((h - np.arange(h)) / (h * .22), 0, 1)[:, None]
    a = m * fade
    rgb = np.zeros((h, w, 3)); rgb[:] = (16, 13, 16)
    im = Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), 'RGBA')
    sc = 330. / h
    return im.resize((int(w * sc), int(h * sc)), Image.LANCZOS)


def hand_piece(frame=20, silhouette=False):
    """hand#1: SAM hand proposal on Door to Heaven f20, + forearm grown from the same box (correction: add)"""
    im = src_frame('hand', frame)
    v = np.asarray(im.convert('L'), dtype=np.float32) / 255.
    a = raster(src_masks('hand')[str(frame)], im.size)
    arm = np.zeros_like(a); arm[62:116, 270:384] = (v[62:116, 270:384] > .42)
    arm = largest_component(arm > .5).astype(np.float32)
    a = np.clip(a + arm, 0, 1)
    record(piece='hand', src='hand', frame=frame, op='add', what='forearm grown from box (270,62)-(384,116), luminance > 0.42, largest component',
           why='the SAM prompt "a hand." stops at the wrist; the offered hand needs its forearm, which the frame does show')
    ys, xs = np.nonzero(a > .05)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    rgb = np.asarray(im, dtype=np.float32)[y0:y1, x0:x1]
    if silhouette:
        rgb = np.zeros_like(rgb); rgb[:] = (16, 13, 16)
    else:
        g = rgb @ np.array([.299, .587, .114]) / 255.
        rgb = np.stack([g * 235 + 20, g * 170 + 14, g * 110 + 8], -1)
    return Image.fromarray(np.dstack([rgb, a[y0:y1, x0:x1] * 255]).astype(np.uint8), 'RGBA')


def sitter_piece(frame=36):
    """sitter#1: SAM proposal on Survival Stresses f36 (a hooded person sitting hunched in a sleeping bag, facing left),
    graded to lamp light; correction stroke removes the empty bag spread right of x=272 so the figure fits the room"""
    im = src_frame('sitter', frame)
    cutr = [(272, 0), (384, 0), (384, 256), (272, 256)]
    a = raster(src_masks('sitter')[str(frame)], im.size, sub=[cutr])
    record(piece='sitter', src='sitter', frame=frame, op='sub', polygon=cutr, why='empty sleeping-bag spread; the room is narrow')
    ys, xs = np.nonzero(a > .05)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    rgb = np.asarray(im, dtype=np.float32)[y0:y1, x0:x1] / 255.
    g = rgb @ np.array([.299, .587, .114])
    rgb = np.clip(rgb * np.array([1.05, .86, .66]) * 1.3 * 255, 0, 255)     # colour kept, lamp-warmed
    pim = Image.fromarray(np.dstack([rgb, a[y0:y1, x0:x1] * 255]).astype(np.uint8), 'RGBA')
    sc = 225. / pim.size[1]
    return pim.resize((int(pim.size[0] * sc), int(pim.size[1] * sc)), Image.LANCZOS)


# ---------------------------------------------------------------- the dog: choreography over proposals
# u<n> = Amateur Film New Jersey C frame n as shot; m<n> = the same proposal mirrored (recorded).
# Door is at the right, so a dog facing right (+1) faces the door.
FACING = {}
for f in range(3, 14): FACING[(f, 1)] = 1          # mirrored side views, head up
for f in range(14, 18): FACING[(f, 1)] = 1         # mirrored side views, head lowering
for f in range(0, 18): FACING[(f, 0)] = -1         # as shot: facing left (away from the door)
for f in range(18, 27): FACING[(f, 0)] = -1        # turning toward camera, head still left
for f in range(27, 38): FACING[(f, 0)] = 0         # facing the camera
for f in range(38, 49): FACING[(f, 0)] = 1         # as shot: facing right (the door)

WATCH = [(38, 0), (39, 0), (38, 0), (39, 0)]
WALK = [43, 44, 45]                     # as shot; f42 removed (garbled head, critic round 1); wrap 45->43 IoU 0.63
STEP_M = 0.066
LIE_BELLY = {4: 160}
LEGS = {4: [(0, 160), (384, 160), (384, 288), (0, 288)]}          # correction stroke: legs (no source frame shows them folded)
TAIL6 = [(211, 146), (254, 146), (254, 184), (211, 184)]         # tail part box on frame 19 (as shot), mirrored on use
TAIL6_ROOT = (214, 150)                  # source y of the belly line (correction stroke: everything below is legs)                          # source world travel per source frame (camera pan 8.75 px / 130 px per m)
REFUSE_TURN = [(38, 0), (36, 0), (33, 0), (30, 0), (28, 0), (26, 0), (26, 0), (5, 0), (5, 0), (3, 0), (3, 0), (2, 0)]
REFUSE_HOLD = [(2, 0), (1, 0), (0, 0), (1, 0)]
# head leads: the refusal body (f1) holds while head proposals that point at the door (f33, then f36) take its neck point
LOOK_BACK = [(1, 0, 33), (1, 0, 33), (1, 0, 36), (1, 0, 36), (1, 0, 36), (1, 0, 36), (36, 0), (36, 0), (38, 0), (38, 0), (39, 0), (39, 0)]
CRINGE = [(39, 0), (40, 0), (41, 0), (43, 0)]
RISE = [(43, 0), (41, 0), (40, 0), (39, 0)]
HEAD_DOWN = [(39, 0), (40, 0), (41, 0), (43, 0)]
ARRIVE = [(44, 0), (43, 0), (41, 0), (40, 0), (40, 0), (4, 1)]

CH = [c['t'] for c in SCORE['choices']]
I_RETREAT, I_WATCH1, I_REFUSE, I_WATCH2, I_APPROACH, I_LIE = [round(t * FPS) for t in CH]
I_LOOK = round(26.4 * FPS)


def dist_since(i0, i):
    return sum(abs(FR[k]['dog']['x'] - FR[k - 1]['dog']['x']) for k in range(i0 + 1, i + 1))


def walk_frame(i, i0, reverse=False, end_on=None, total=None):
    d = dist_since(i0, i)
    n = d / STEP_M
    if end_on is not None and total is not None:
        # stretch the stride slightly so the last step lands on the lying proposal
        steps = total / STEP_M
        want = math.floor(steps / len(WALK)) * len(WALK) + WALK.index(end_on)
        n = n * want / steps if steps else n
    k = int(n) % len(WALK)
    seq = WALK[::-1] if reverse else WALK
    return seq[k]


def dog_plan(i):
    """-> dict(f, m, state, posture, look, drop) : which proposal the dog is at frame i, and why"""
    fr = FR[i]['dog']; act = fr['act']
    if i < I_RETREAT:
        f, m = WATCH[(i // 7) % 4]; return dict(f=f, m=m, state='watch', posture='stand')
    if i < I_WATCH1:
        j = i - I_RETREAT
        if j < 2 * len(CRINGE):
            f, m = CRINGE[j // 2]; return dict(f=f, m=m, state='retreat', posture='crouch')
        return dict(f=walk_frame(i, I_RETREAT + 2 * len(CRINGE), reverse=True), m=0, state='retreat', posture='crouch-backing')
    if i < I_REFUSE:
        j = i - I_WATCH1
        if j < 2 * len(RISE):
            f, m = RISE[j // 2]; return dict(f=f, m=m, state='watch', posture='stand')
        f, m = WATCH[((i - I_WATCH1) // 7) % 4]; return dict(f=f, m=m, state='watch', posture='stand')
    if i < I_WATCH2:
        j = i - I_REFUSE
        if j < len(REFUSE_TURN):
            f, m = REFUSE_TURN[j]; return dict(f=f, m=m, state='refuse', posture='turning-away')
        f, m = REFUSE_HOLD[((j - len(REFUSE_TURN)) // 12) % 4]; return dict(f=f, m=m, state='refuse', posture='back-turned')
    if i < I_APPROACH:
        j = i - I_WATCH2
        if j < len(LOOK_BACK):
            e = LOOK_BACK[j]
            if len(e) == 3:
                return dict(f=e[0], m=e[1], hswap=e[2], state='watch', posture='head-turns-back')
            return dict(f=e[0], m=e[1], state='watch', posture='turning-back')
        f, m = WATCH[((j - len(LOOK_BACK)) // 8) % 4]; return dict(f=f, m=m, state='watch', posture='stand')
    if i < I_LIE:
        j = i - I_APPROACH
        if j < 2 * len(HEAD_DOWN):
            f, m = HEAD_DOWN[j // 2]; return dict(f=f, m=m, state='approach', posture='head-low')
        i0 = I_APPROACH + 2 * len(HEAD_DOWN)
        if i >= I_LIE - 2 * len(ARRIVE):
            f, m = ARRIVE[(i - (I_LIE - 2 * len(ARRIVE))) // 2]; return dict(f=f, m=m, state='approach', posture='arriving')
        tot = dist_since(i0, I_LIE - 2 * len(ARRIVE))
        return dict(f=walk_frame(i, i0, end_on=44, total=tot), m=0, state='approach', posture='walk-head-low')
    return dict(f=4, m=1, state='lie_down', posture='lying', drop=act['lie'], look=act['look'], rest=act['rest'], head=act['head'])


# dog piece geometry, cached per proposal
_geo = {}


def dog_piece(f, m, legs=True, part=None):
    """whole-dog proposal (or its head/body part split at the neck prompt) as an RGBA piece + centroid/feet anchors"""
    keep = None
    if part == 'head':
        keep = [neck_cut(f, 'head', back=5)]
    elif part == 'body':
        keep = [neck_cut(f, 'body')]
    pim, info = cut('dog', f, bool(m), keep=keep, scale=S)
    k = (f, m, part)
    if k not in _geo:
        full, finfo = cut('dog', f, bool(m), scale=S)
        a = np.asarray(full)[..., 3].astype(np.float32) / 255.
        ys, xs = np.nonzero(a > .5)
        cx = float((a.sum(0) * np.arange(a.shape[1])).sum() / a.sum())
        _geo[k] = dict(cx=cx, bottom=float(ys.max()), finfo=finfo)
    return pim, info, _geo[k]


def place_dog(i, plan):
    """compose the dog layer (RGBA, full frame) for frame i, plus its shadow; returns (layer, shadow_alpha, meta)"""
    x = FR[i]['dog']['x']
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    f, m = plan['f'], plan['m']
    full, info, g = dog_piece(f, m)
    ox = X(x) - g['cx']
    oy = FEET - g['bottom']
    pieces_used = [dict(src='dog', frame=f, mirror=bool(m), part='whole')]
    if plan['state'] == 'lie_down':
        drop = plan.get('drop', 0)
        # legs: no source frame shows this dog's legs folded, so they are not made: the body is lowered onto the floor and
        # everything below the floor line is kept out of view (in the sill's and its own shadow)
        dy = drop * (g['bottom'] - (LIE_BELLY[f] - info['origin'][1]) * S + (EDGE + 3 - FEET))
        look = plan.get('look', 0); rest = plan.get('rest', 0); hd = plan.get('head', .7)
        # lying is assembled: the m4 body proposal (level back, legs kept out of view below the belly stroke), a tail proposal
        # from f19 (a tail held clear of the body, lying back along the floor once mirrored), and head proposals substituted at the neck prompt:
        #   u40 head (level, muzzle forward) / u44 (lower) / u47 (lowest, nose down) -- each a real head of this dog
        t = i / FPS
        hm = False
        if look > .1:
            hf, hm = 1, True        # f1 head, mirrored: the back of the head and ears toward the viewer, muzzle away into the room
        elif rest > .3:
            hf = 47
        elif t >= 25.9:
            hf = 47 if t >= 26.1 else 44
        else:
            hf = 40
        body, binfo = cut('dog', f, bool(m), keep=[neck_cut(f, 'body')], scale=S, feather=2.0)
        hk, hdisk = head_region(hf)
        head, hinfo = cut('dog', hf, hm, keep=hk, keep2=hdisk, scale=S, feather=2.0)
        tail, tinfo = cut('dog', 19, True, keep=[TAIL6], scale=S)
        fneck = to_piece(info, key(f, 'neck')); bneck = to_piece(binfo, key(f, 'neck'))
        bx = ox + fneck[0] - bneck[0]; by = oy + fneck[1] - bneck[1] + dy
        btail = to_piece(binfo, key(f, 'tail')); ttail = to_piece(tinfo, TAIL6_ROOT)
        if drop < .92:
            # still going down: the whole m4 proposal (legs and all) sinks behind the porch board; nothing is cut
            layer.alpha_composite(full, (int(round(ox)), int(round(oy + dy))))
            hf = 4
        else:
            layer.alpha_composite(tail, (int(round(bx + btail[0] - ttail[0])), int(round(by + btail[1] - ttail[1]))))
            layer.alpha_composite(body, (int(round(bx)), int(round(by))))
            hneck = to_piece(hinfo, key(hf, 'neck'))
            sink = 9 * S if hf == 1 else 0                 # f1's neck is raised; set its head 9 source px lower on the lying body
            layer.alpha_composite(head, (int(round(bx + bneck[0] - hneck[0])), int(round(by + bneck[1] - hneck[1] + sink))))
        pieces_used = ([dict(src='dog', frame=f, mirror=bool(m), part='whole', legs='sinking behind the porch board')] if drop < .92 else
                       [dict(src='dog', frame=f, mirror=bool(m), part='body', legs='behind the porch board (no frame shows them folded)'),
                        dict(src='dog', frame=19, mirror=True, part='tail'), dict(src='dog', frame=hf, mirror=hm, part='head')])
        # floor clip: below the floor line nothing of the dog is shown (legs refused), soft 6 px edge
        arr = np.asarray(layer).copy()
        ramp = np.clip((EDGE + 4 - np.arange(H)) / 3., 0, 1)
        arr[..., 3] = (arr[..., 3] * ramp[:, None]).astype(np.uint8)
        layer = Image.fromarray(arr, 'RGBA')
    elif plan.get('hswap'):
        hf = plan['hswap']
        _, own = head_region(f, r_scale=1.35)          # the body's own raised head is removed with it (correction stroke)
        body, binfo = cut('dog', f, bool(m), keep=[neck_cut(f, 'body')], sub=[own], scale=S, feather=2.0)
        hk, hdisk = head_region(hf)
        head, hinfo = cut('dog', hf, False, keep=hk, keep2=hdisk, scale=S, feather=2.0)
        fneck = to_piece(info, key(f, 'neck')); bneck = to_piece(binfo, key(f, 'neck'))
        bx = ox + fneck[0] - bneck[0]; by = oy + fneck[1] - bneck[1]
        layer.alpha_composite(body, (int(round(bx)), int(round(by))))
        hneck = to_piece(hinfo, key(hf, 'neck'))
        lift = 14 * S                                   # head set 14 source px above the neck prompt: f1's neck is raised
        layer.alpha_composite(head, (int(round(bx + bneck[0] - hneck[0])), int(round(by + bneck[1] - hneck[1] - lift))))
        pieces_used = [dict(src='dog', frame=f, mirror=bool(m), part='body'), dict(src='dog', frame=hf, mirror=False, part='head')]
    else:
        layer.alpha_composite(full, (int(round(ox)), int(round(oy))))
    return layer, pieces_used


def light_factor(t):
    if t < 6.2:
        return 0.06
    return 0.06 + 0.94 * smooth((t - 6.2) / 0.9)


def door_angle(t):
    return 12 + 66 * smooth((t - 6.2) / 0.9) if t >= 6.2 else 12.0


# ---------------------------------------------------------------- frame composition
class Scene:
    def __init__(self):
        self.dusk, self.lit, self.fg, self.fg_lit = build_world()
        self.leaf = door_leaf()
        self.stand = person_stand()
        self.arm = hand_piece(20, silhouette=True)
        self.hand = hand_piece(30, silhouette=False)
        self.sit = sitter_piece(36)
        self.sill = sill_layer()
        self.noise = [rng.normal(0, 1, (H, W, 1)).astype(np.float32) for _ in range(6)]
        yy, xx = np.mgrid[0:H, 0:W]
        self.vign = (1 - .38 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 1.6)) ** 2)).clip(.45, 1)[..., None].astype(np.float32)

    def person_layers(self, t, base):
        P = None
        for k in range(len(FR)):
            pass
        fr = FR[min(int(round(t * FPS)), len(FR) - 1)]['person']
        # standing in the doorway until 5.4, steps aside 5.4-5.9, sits from 5.9
        if t < 5.9:
            sx = 1003 + (0 if t < 5.4 else 150 * smooth((t - 5.4) / .5))
            st = self.stand
            px = int(sx - st.size[0] / 2); py = int(FEET - st.size[1] + 8 + (0 if t < 5.4 else 30 * smooth((t - 5.4) / .5)))
            # reach: the call-again arm, 3.4-4.6 (extends 3.40-3.70, withdraws 4.35-4.60)
            if 3.4 <= t < 4.6:
                e = smooth((t - 3.4) / .3) * (1 - smooth((t - 4.35) / .25))
                arm = self.arm
                aw = int(arm.size[0] * (.55 + .85 * e)); ah = int(arm.size[1] * 1.15)
                a2 = arm.resize((aw, ah), Image.LANCZOS).rotate(-18 * e, resample=Image.BICUBIC, expand=True)
                base.alpha_composite(a2, (int(sx - a2.size[0] + 22), int(py + 118)))
            base.alpha_composite(st, (px, py))
        else:
            sp = self.sit
            base.alpha_composite(sp, (1078, int(EDGE - sp.size[1] + 20)))   # sits beside the door, clear of the dog's line into the room
        # the low hand, offered from 6.8
        if t >= 6.8:
            e = smooth((t - 6.8) / .6)
            hd = self.hand
            hw = int(hd.size[0] * .95); hh = int(hd.size[1] * .95)
            h2 = hd.resize((hw, hh), Image.LANCZOS)
            back = 70 * smooth((t - 21.5) / 2.0) + 90 * smooth((t - 24.8) / 1.0)
            hx = int(1205 - hw + 60 * (1 - e) + back); hy = int(EDGE - hh + 10)
            base.alpha_composite(h2, (hx, hy))

    def door_layer(self, t, base):
        th = math.radians(door_angle(t))
        w = max(6, int(170 * math.sin(th)))
        leaf = self.leaf.resize((w, self.leaf.size[1]), Image.LANCZOS)
        # shade by angle: a leaf turned away from the lamp is darker
        arr = np.asarray(leaf).astype(np.float32)
        arr[..., :3] *= (.45 + .55 * math.sin(th))
        leaf = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')
        base.alpha_composite(leaf, (WX1, LINTEL))

    def frame(self, i):
        t = i / FPS
        L = light_factor(t)
        bg = self.dusk * (1 - L) + self.lit * L
        base = Image.fromarray(bg.astype(np.uint8)).convert('RGBA')
        self.door_layer(t, base)
        self.person_layers(t, base)
        plan = dog_plan(i)
        dog, used = place_dog(i, plan)
        da = np.asarray(dog).astype(np.float32)
        alpha = da[..., 3] / 255.
        # light on the dog: cool dusk everywhere, warm from the doorway when the door is open (stronger nearer the door)
        xx = np.arange(W)[None, :]
        warm = (L * np.clip(1 - (WX0 - xx) / 560., 0, 1) ** 1.3)[..., None]
        if plan['state'] == 'lie_down':
            warm = np.maximum(warm, (L * plan.get('drop', 0) * np.clip((xx - 880) / 140., 0, 1))[..., None])
        rgb = da[..., :3]
        cool = rgb * np.array([.78, .84, 1.0]) * .92
        hot = rgb * np.array([1.16, .98, .76])
        da[..., :3] = cool * (1 - warm) + hot * warm
        # the dog's underside sits in its own shadow (the doorway light comes from the side and above the board)
        ys, xs = np.nonzero(alpha > .3)
        if len(xs):
            y0, y1 = ys.min(), min(ys.max(), EDGE)
            hgt = max(y1 - y0, 1)
            yr = np.clip((np.arange(H) - (y1 - .42 * hgt)) / (.42 * hgt), 0, 1)[:, None, None]
            da[..., :3] *= (1 - .55 * yr * yr)
        base.alpha_composite(self.sill)
        base.alpha_composite(Image.fromarray(da.clip(0, 255).astype(np.uint8), 'RGBA'))
        fg = self.fg * (1 - L) + self.fg_lit * L
        base.alpha_composite(Image.fromarray(fg.astype(np.uint8), 'RGBA'))
        out = np.asarray(base.convert('RGB')).astype(np.float32)
        out = out * self.vign + self.noise[i % 6] * 3.2
        meas = measure(alpha)
        return Image.fromarray(out.clip(0, 255).astype(np.uint8)), plan, used, meas, alpha


def measure(alpha):
    ys, xs = np.nonzero(alpha > .5)
    if len(xs) == 0:
        return None
    w = alpha[alpha > .5]
    return dict(cx=round(float((xs * w).sum() / w.sum()), 2), cy=round(float((ys * w).sum() / w.sum()), 2),
                x0=int(xs.min()), x1=int(xs.max()), y0=int(ys.min()), y1=int(ys.max()), area=int(len(xs)))


def main():
    args = sys.argv[1:]
    sc = Scene()
    if args and args[0] == '--stills':
        for a in args[1:]:
            t = float(a); img, plan, used, meas, _ = sc.frame(int(round(t * FPS)))
            img.save(os.path.join(CACHE, 'still_%05.2f.jpg' % t), quality=90)
            print(t, plan, meas)
        return
    raise SystemExit('use make.sh (film.py) for the full render')


if __name__ == '__main__':
    main()
