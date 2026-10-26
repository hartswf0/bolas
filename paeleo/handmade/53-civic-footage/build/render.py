"""SCION 53 · civic footage performer · the threshold re-performed by a dog from a home movie.

Renders 912 frames (3 s title, 768 scene frames aligned 1:1 with the score, 3 s source card) as raw RGB to stdout
(pipe to ffmpeg) or, with --still T, one scene frame as JPEG. Writes ../trace.json and ../build/edl.json
(the transform ledger: for every scene frame, which archive frame each fragment shows and the operation).

Run:  python3 render.py | ffmpeg -f rawvideo -pix_fmt rgb24 -s 1280x720 -r 24 -i - ...
"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib import *

W, H, FPS = 1280, 720, 24
TITLE_N = END_N = 72
SCORE = load_json(SRC, 'threshold-score.json')
FR = SCORE['frames']
N = len(FR)  # 768

# ---- the stage: world metres -> screen px (side view, threshold at x = 0, porch to the right) ----
K = 185.0           # px per metre
X0 = 372.0          # screen x of the threshold
def sx(x): return X0 + K * x
BAND_T, BAND_B = 150, 612      # the composed scene occupies this band; above it the source monitors, below it the score
WALL_BASE = 556                # where the house wall meets the porch floor (back plane)
GROUND = 580                   # where the dog's feet touch (front plane)
DOOR_L, DOOR_R = sx(-0.46), sx(0.46)
DOOR_TOP = WALL_BASE - int(2.03 * K)
HOUSE_END = sx(1.05)           # corner of the house; beyond it the yard at dusk

dog = Source('dog'); door = Source('door'); hand = Source('hand'); seated = Source('seated')
POSE = load_json(dog.dir, 'pose_agent_v8.json')
S_DOG = 1.60        # archive dog: ~116 px/m in the source -> 185 px/m
S_COAT = 1.62       # the person in the same home movie, same camera, same scale as the dog
S_SEAT = 0.92       # Survival Stresses: seated figure ~170 px tall in source = ~1.0 m
S_HAND = 0.55       # Door to Heaven: forearm and hand
S_DOOR = (DOOR_R - DOOR_L) / 132.0

# ===================== static plates (all cut from the archive frames, then darkened for dusk) =====================
def build_plates():
    bg = np.zeros((H, W, 3), np.float32)
    bg[:] = np.array([24, 24, 27]) / 255
    # sky / yard beyond the house: the home movie's own background (frame 0, top strip: shrubs, lawn), blurred and nearly dark
    yard = to_grey(dog.frame(0)).crop((70, 0, 300, 70)).resize((W, BAND_B - BAND_T), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    yard = np.asarray(yard).astype(np.float32) / 255
    grad = np.linspace(1.0, 0.45, BAND_B - BAND_T)[:, None, None]
    sky = np.array([0.30, 0.31, 0.35])[None, None, :] * grad
    scene = sky * 0.8 + yard * 0.16 * grad
    # fieldstone wall of the house: blocks cut from the stone pillar of the same house (dog frames 3, 9, 14), laid like stones
    rng = np.random.default_rng(53)
    wall_h = WALL_BASE - BAND_T
    blocks = []
    for fk in (3, 9, 14):
        st = np.asarray(to_grey(dog.frame(fk)).crop((314, 46, 376, 282))).astype(np.float32) / 255
        blocks.append(st)
    wall = np.zeros((wall_h, int(HOUSE_END), 3), np.float32)
    bh, bw = 58, 50
    yrow = 0
    while yrow < wall_h:
        xoff = -int(rng.integers(0, bw))
        x = xoff
        while x < wall.shape[1]:
            b = blocks[int(rng.integers(0, 3))]
            sy_ = int(rng.integers(0, b.shape[0] - bh // 1.6 - 1)); sx_ = int(rng.integers(0, b.shape[1] - bw // 1.6 - 1))
            piece = Image.fromarray((b[sy_:sy_ + int(bh / 1.6), sx_:sx_ + int(bw / 1.6)] * 255).astype(np.uint8)).resize((bw, bh), Image.BICUBIC)
            pa = np.asarray(piece).astype(np.float32) / 255
            x0, x1 = max(0, x), min(wall.shape[1], x + bw); y1 = min(wall_h, yrow + bh)
            if x1 > x0:
                wall[yrow:y1, x0:x1] = pa[:y1 - yrow, x0 - x:x1 - x] * (0.85 + 0.3 * rng.random())
                wall[yrow:y1, x0:min(x0 + 2, x1)] *= 0.55   # mortar joints
            x += bw
        wall[yrow:min(wall_h, yrow + 2)] *= 0.55
        yrow += bh
    scene_wall = wall * 0.55
    scene[0:wall_h, 0:int(HOUSE_END)] = scene_wall
    # corner shadow of the house
    xs = np.arange(int(HOUSE_END) - 18, int(HOUSE_END))
    scene[0:wall_h, xs] *= np.linspace(1, 0.6, len(xs))[None, :, None]
    # porch floor: the gravel path of the same home movie (frame 30, lower strip), tiled, seen from slightly above
    gr = to_grey(dog.frame(30)).crop((0, 236, 380, 288))
    ga = np.asarray(gr.resize((int(380 * 1.6), int(52 * 1.6)), Image.BICUBIC)).astype(np.float32) / 255
    fl_h = BAND_B - WALL_BASE
    gt = np.concatenate([ga, ga[:, ::-1]], 1)
    gt = np.concatenate([gt] * 3, 1)[:fl_h, :W]
    scene[WALL_BASE - BAND_T:, :] = gt * 0.55
    # the sill: a slab in front of the doorway (drawn: a plain lighter stone, the only drawn surface)
    s0, s1 = int(DOOR_L) - 6, int(DOOR_R) + 6
    scene[WALL_BASE - BAND_T:WALL_BASE - BAND_T + 14, s0:s1] = scene[WALL_BASE - BAND_T:WALL_BASE - BAND_T + 14, s0:s1] * 0.5 + 0.30
    scene[WALL_BASE - BAND_T + 14:WALL_BASE - BAND_T + 16, s0:s1] *= 0.55
    # wall base shadow line
    scene[WALL_BASE - BAND_T - 2:WALL_BASE - BAND_T + 1, :int(HOUSE_END)] *= 0.5
    # porch edge / steps at x = 4.9
    pe = int(sx(4.9))
    if pe < W:
        scene[WALL_BASE - BAND_T:, pe:] *= 0.45
    bg[BAND_T:BAND_B] = scene
    return bg

# ===================== the door: Straight Talk (1992), re-timed =====================
DOOR_REF = 31
DOOR_CROP_W = 132
def door_frame_for(t, P):
    """Straight Talk, mirrored so the woman in it faces the porch. Returns (frame, crop x0 in the mirrored frame, op, tag).
    0-5.42 s  the woman stands in the half-open door, hand on the knob: f010-f013 ping-pong (faster while she calls)
    5.42-6.0  she steps aside: f013>f019 played as recorded, the crop re-framed from her to the door
    6.0-6.2   the door swings toward shut: f023, f024 (ajar)
    6.2-6.4   the door opens: f024>f022 played backward; held f022 (open), its warm hallway lifted as light"""
    if t < 5.417:
        seq = [10, 11, 12, 13, 12, 11]
        k = seq[int(t * (8 if P['voice'] == 'call' else 3)) % len(seq)]
        return k, 98, 'MIRROR · PING-PONG f010-f013 · the woman in the door', 'MIRROR · PING-PONG'
    if t < 6.0:
        u = (t - 5.417) / 0.583
        return min(19, 13 + int((t - 5.417) * 12)), 98 + 47 * u, 'MIRROR · PLAY 1:1 f013>f019 · she steps aside · REFRAMED', 'PLAY · steps aside'
    if t < 6.2:
        return (23 if t < 6.1 else 24), 145, 'MIRROR · f023-f024 · the door swings to (ajar)', 'MIRROR · ajar'
    k = max(22, 24 - int((t - 6.2) * 12))
    if k > 22:
        return k, 145, 'MIRROR · REVERSE f024>f022 · the door opens', 'REVERSE · opens'
    return 22, 145, 'MIRROR · HELD f022 (open)', 'HELD · open'

def door_layer(i, x0, open_amt):
    im = door.frame(i).transpose(Image.FLIP_LEFT_RIGHT)
    c = door.camera
    dx = -(c[i][0] - c[DOOR_REF][0]); dy = c[i][1] - c[DOOR_REF][1]
    y0 = min(16.0, max(0.0, 8 + dy))                 # stay inside the frame: no black edge
    box = (x0 + dx, y0, x0 + DOOR_CROP_W + dx, y0 + 272)
    cr = im.crop(tuple(int(round(v)) for v in box)).resize((int(DOOR_R - DOOR_L), WALL_BASE - DOOR_TOP), Image.BICUBIC)
    a = np.asarray(cr).astype(np.float32) / 255
    L = a @ np.array([0.299, 0.587, 0.114])
    grey = np.repeat(L[..., None], 3, -1) * 0.74          # the doorway at dusk
    if open_amt <= 0:
        return grey, None
    hue = (a[..., 0] - a[..., 2]) / (a[..., 0] + 0.05)
    warm = np.clip((hue - 0.30) / 0.15, 0, 1)
    hh, ww = warm.shape
    warm[int(hh * 0.90):] = 0                      # the brown floor of the hallway is not light
    warm[:, int(ww * 0.55):] *= 0                  # only the gap beside the door's edge (mirrored: left)
    warm = np.asarray(Image.fromarray((warm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
    warm *= open_amt
    lit = a / np.maximum(L, 0.12)[..., None] * 0.80     # the gap's own warm colour, exposure lifted: the light inside
    out = grey * (1 - warm[..., None]) + np.clip(lit, 0, 1) * warm[..., None]
    return out, warm

# ===================== the person =====================
COAT_POLY = [(0, 0), (72, 0), (70, 45), (62, 62), (56, 80), (55, 150), (58, 175), (63, 186), (60, 197), (30, 199), (20, 193), (14, 160), (4, 152), (0, 152)]
def coat_cut(i):
    c = dog.camera
    dx = c[i][0] - c[4][0]; dy = c[i][1] - c[4][1]
    m = Image.new('L', (384, 288), 0)
    ImageDraw.Draw(m).polygon([(x + dx, y + dy) for x, y in COAT_POLY], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.6))
    g = np.asarray(to_grey(dog.frame(i))).astype(np.float32) / 255
    a = np.dstack([np.clip(g * 1.25, 0, 1), np.asarray(m).astype(np.float32) / 255])[0:205, 0:80].copy()
    # the footage ends at the top and left frame edges: let those edges fade instead of pretending there is more coat
    a[:, :10, 3] *= np.linspace(0.2, 1, 10)[None, :]
    a[:70, :, 3] *= np.linspace(0, 1, 70)[:, None]
    return a

def seated_cut(i):
    a, o = cutout(seated, i, mirror=True, feather=1.4)
    return a, o

HAND_REF = 0
def hand_cut(i):
    g = np.asarray(to_grey(hand.frame(i))).astype(np.float32)[..., 0] / 255
    hm = np.asarray(hand.mask(i, feather=0)).astype(np.float32) > 0
    ys, xs = np.nonzero(hm)
    x1 = xs.max(); band = ys[xs > x1 - 15]
    arm = g > 0.37
    arm[:, :x1 - 12] = False; arm[:max(0, band.min() - 12), :] = False; arm[band.max() + 14:, :] = False
    m = Image.fromarray((np.maximum(hm, arm) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
    a = np.dstack([np.repeat(g[..., None], 3, -1), np.asarray(m).astype(np.float32) / 255])
    a = a[:, ::-1]                                    # mirrored: the arm now comes from the left, toward the porch
    ys, xs = np.nonzero(a[..., 3] > 0.05)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
    a[:, :30, 3] *= np.linspace(0, 1, 30)[None, :]   # the forearm leaves the archive frame: fade the cut end
    return a

# ===================== the dog's performance: which archive frame, which operation =====================
TURN = [15, 16, 17, 18, 19, 20, 26, 28, 30, 33, 36, 38, 40, 42, 44]    # the dog's own turn away from the person in the home movie
FACE = {}
for f in range(0, 21): FACE[f] = -1      # source native: facing left (toward the person)
for f in range(21, 40): FACE[f] = 0      # frontal
for f in range(40, 50): FACE[f] = 1      # facing right

def lerp(a, b, u): return a + (b - a) * u

TURN_BACK = [33, 30, 28, 26, 15, 14]   # frontal, then facing the door; f016-f020 are motion-blurred doubles (critic round 1)

def lie_deg(a):
    """head angle of the lying composite: 40 deg puts the chin on the floor; 'look' lifts it to point into the doorway."""
    return 40 + 25 * min(1.0, max(0.0, a['head'] - 0.2)) + 30 * a.get('look', 0) - 4 * a.get('rest', 0)

def dog_pick(n):
    """score frame n -> dict(src, mirror, fold(lie, head_deg, flip) or None, op (ledger), tag (screen))"""
    f = FR[n]; t = f['t']; d = f['dog']; a = d['act']; x = d['x']
    if t < 1.0:
        k = int(t * 12) % 12
        return dict(src=k, mirror=False, fold=None, op='PLAY 1:1 · f%03d' % k, tag='PLAY 1:1')
    if t < 2.333:
        k = 48 - int(max(0, x - 3.0) / 0.055) % 7   # f042-f048: the side-on walk (f040-41 are still turning)
        return dict(src=k, mirror=True, fold=None, op='MIRROR + REVERSE · walks backward', tag='MIRROR+REVERSE')
    if t < 3.417:
        seq = list(range(4, 13)) + list(range(11, 4, -1))
        k = seq[int((t - 2.333) * 8) % len(seq)]
        return dict(src=k, mirror=False, fold=None, op='PING-PONG 2:3 · f004-f012', tag='PING-PONG 2:3')
    if t < 3.417 + len(TURN) / 12:
        k = TURN[min(len(TURN) - 1, int((t - 3.417) * 12))]
        return dict(src=k, mirror=False, fold=None, op='PLAY 1:1 · its own turn away (f015-f044, f021-25 cut)', tag='PLAY 1:1 · turn')
    if t < 7.458:
        return dict(src=44, mirror=False, fold=(a['lie'], lie_deg(a), False), op='COMPOSED: FOLD f044 · lies down, back turned', tag='COMPOSED FOLD')
    if t < 8.4:
        # comes round at once, in the footage's own frames: frontal f033, f028, then f015/f014 facing the door;
        # while the score's lie value is still high the legs stay folded (COMPOSED squash), rising by 8.0 s
        seq = [33, 28]
        i_ = int((t - 7.458) * 12)
        k = seq[i_] if i_ < 2 else [15, 14][int((t - 7.625) * 3) % 2]
        lie = a['lie']
        return dict(src=k, mirror=False, fold=('squash', lie) if lie > 0.02 else None,
                    op='PLAY f033>f028>f015 · comes round to the door' + (' · legs folded %.2f (COMPOSED)' % lie if lie > 0.02 else ''),
                    tag='PLAY · comes round')
    if t < 14.708:
        seq = list(range(0, 16)) + list(range(14, 0, -1))
        k = seq[(int((t - 8.4) * 6) + 17) % len(seq)]
        return dict(src=k, mirror=False, fold=None, op='PING-PONG 1:2 · f000-f015 · waits', tag='PING-PONG 1:2')
    if t < 23.792:
        k = 42 + int(max(0, 4.0 - x) / 0.055) % 7
        return dict(src=k, mirror=True, fold=None, op='MIRROR · stepped by distance', tag='MIRROR (walk)')
    return dict(src=44, mirror=True, fold=(a['lie'], lie_deg(a), False), op='COMPOSED: FOLD f044 (mirror) · across the sill', tag='COMPOSED FOLD')

_FOLD_ANCHOR = {}
def dog_layer(p):
    """returns (drawn layer, body-only layer used to anchor and measure, facing)."""
    k = p['src']
    arr, o = cutout(dog, k, mirror=p['mirror'], feather=0.9, erode=1)
    face = FACE[k] * (-1 if p['mirror'] else 1)
    if p['fold'] is None:
        lay = scale_rgba(arr, S_DOG)
        return lay, lay, face
    if p['fold'][0] == 'squash':
        lie = p['fold'][1]
        ys_, xs_ = np.nonzero(arr[..., 3] > 0.3)
        fy = ys_.max() + 1; top = ys_.min()
        by = int(top + 0.55 * (fy - top))
        new_leg = max(1, int(round((fy - by) * (1 - 0.85 * lie))))
        drop = (fy - by) - new_leg
        out = np.zeros_like(arr)
        out[drop:by + drop] = arr[:by]
        legs = resample_rows(arr, by, fy, new_leg); legs[..., :3] *= (1 - 0.4 * lie)
        out[by + drop:by + drop + new_leg] = legs
        lay = scale_rgba(out, S_DOG)
        return lay, lay, face
    lie, hdeg, flip = p['fold']
    kp = POSE[str(k)]
    neck, nose, tail = kp['neck'], kp['nose'], kp['tail']
    if p['mirror']:
        neck, nose, tail = mirror_pt(neck), mirror_pt(nose), mirror_pt(tail)
    feet = max(kp['f1'][1], kp['f2'][1], kp['h1'][1], kp['h2'][1]) + 14
    args = (arr, o, neck, kp['chest'][1] + 8, 152, tail[0], feet, lie)
    body, d = fold2(*args, hdeg, face, nose[1] + 9, no_head=True)
    if flip == 'swap8':
        # head substitution: the real head of f008, where the dog looks up and left at the person, set on the folded body's neck
        h8, o8 = cutout(dog, 8, feather=0.9, erode=1)
        k8 = POSE['8']
        xs8 = np.arange(h8.shape[1])[None, :] + o8[0]; ys8 = np.arange(h8.shape[0])[:, None] + o8[1]
        keep = np.clip((k8['neck'][0] + 14 - xs8) / 9.0, 0, 1) * np.clip((k8['neck'][1] + 28 - ys8) / 9.0, 0, 1)
        h8 = h8.copy(); h8[..., 3] *= keep
        h8 = rotate_rgba(h8, hdeg, (k8['neck'][0] - o8[0], k8['neck'][1] - o8[1]))
        full = body.copy()
        tx = int(round((neck[0] - o[0]) - (k8['neck'][0] - o8[0]) - 6))
        ty = int(round((neck[1] - o[1] + d) - (k8['neck'][1] - o8[1]) - 4))
        Hh, Wh = full.shape[:2]
        canvas = np.zeros((Hh + 120, Wh + 120, 4), np.float32); canvas[60:60 + Hh, 60:60 + Wh] = full
        bodyc = np.zeros_like(canvas); bodyc[60:60 + Hh, 60:60 + Wh] = body
        y0, x0 = ty + 60, tx + 60
        hs = h8[max(0, -y0):, max(0, -x0):]; y0 = max(0, y0); x0 = max(0, x0)
        hh_, ww_ = min(hs.shape[0], canvas.shape[0] - y0), min(hs.shape[1], canvas.shape[1] - x0)
        hs = hs[:hh_, :ww_]
        reg = canvas[y0:y0 + hh_, x0:x0 + ww_]
        ah = hs[..., 3:4]
        col = hs[..., :3] * ah + reg[..., :3] * reg[..., 3:4] * (1 - ah)
        al = ah + reg[..., 3:4] * (1 - ah)
        reg[..., :3] = np.where(al > 1e-4, col / np.maximum(al, 1e-4), 0); reg[..., 3:4] = al
        canvas[y0:y0 + hh_, x0:x0 + ww_] = reg
        return scale_rgba(canvas, S_DOG), scale_rgba(bodyc, S_DOG), face
    full, _ = fold2(*args, hdeg, face, nose[1] + 9, head_flip=flip)
    return scale_rgba(full, S_DOG), scale_rgba(body, S_DOG), face

# ===================== lighting: dusk, and the light that comes out of the door =====================
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
def light_field(open_amt):
    amb = np.array([0.70, 0.74, 0.86], np.float32)
    if open_amt <= 0:
        return np.broadcast_to(amb, (H, W, 3))
    cx = (DOOR_L + DOOR_R) / 2 + 30
    # a fan of light on the porch floor and on whatever stands in front of the doorway
    dyf = np.clip((YY - (WALL_BASE - 60)) / 60, 0, 1)
    width = 120 + (YY - WALL_BASE).clip(0) * 2.2
    fx = np.exp(-((XX - cx) / width) ** 2 * 1.6)
    ramp = np.clip((XX - (DOOR_L - 30)) / 40, 0, 1)
    spill = fx * dyf * ramp
    glow = np.exp(-(((XX - cx) / 210) ** 2 + ((YY - (WALL_BASE - 140)) / 260) ** 2))
    warm = np.array([1.00, 0.70, 0.36], np.float32)
    f = amb[None, None, :] + (spill[..., None] * 1.5 + glow[..., None] * 0.30) * warm * open_amt
    return f

# ===================== typography: monitors, catalogue slips, the score strip =====================
F_MONO = font('mono', 11); F_MONO_S = font('mono', 10); F_MONO_B = font('mono6', 11)
F_DISP = font('display', 15); F_SER = font('serifi', 17); F_SER_S = font('serif', 13)
INK = (214, 208, 196); DIM = (120, 118, 112); AMBER = (232, 176, 92)

def rec_line(src):
    r = src.rec
    return r.get('source_title', '?'), (r.get('source_year') or 'undated'), r.get('rights_statement', 'unknown')

MON_W, MON_H = 128, 96
F_HUD = font('mono', 16); F_HUD_B = font('mono6', 16); F_PROMPT = font('serifi', 22)
def draw_monitor(img, dr, x, label, src, k, tag, active, outline=None):
    y = 10
    fr0 = src.frame(k)
    fr = fr0.resize((MON_W, int(MON_W * fr0.height / fr0.width)), Image.BILINEAR)
    if not active:
        fr = Image.blend(fr, Image.new('RGB', fr.size, (24, 24, 27)), 0.72)
    img.paste(fr, (x, y))
    if outline and active:
        s = MON_W / fr0.width
        for p_ in outline:
            if len(p_) > 2:
                dr.line([(x + q[0] * s, y + q[1] * s) for q in p_] + [(x + p_[0][0] * s, y + p_[0][1] * s)], fill=AMBER, width=1)
    dr.rectangle([x - 1, y - 1, x + MON_W, y + fr.height], outline=(70, 70, 70))
    title, year, rights = rec_line(src)
    tx = x + MON_W + 8
    st = src.source_time(k)
    lines = [(label, AMBER if active else DIM, F_HUD_B), (title[:18], INK, F_HUD),
             ((year + ' · ' + ('PD' if rights == 'public_domain' else rights))[:18], INK, F_HUD),
             (('f%03d +%.2fs' % (k, src.clip_time(k)))[:18], INK, F_HUD),
             (tc(st) if st is not None else 'film tc unknown', INK, F_HUD),
             (tag[:18], AMBER, F_HUD)]
    for j, (s_, col, fnt) in enumerate(lines):
        dr.text((tx, y - 2 + j * 19), s_, font=fnt, fill=col if active else DIM)

CHOICES = SCORE['choices']
PROMPTS = SCORE['prompts']
def draw_score(dr, n):
    """the score strip: time, the prompt, the circumstances, and an unlabelled timeline (choices read from the picture)."""
    t = FR[n]['t']
    x0, x1, y = 24, W - 24, 700
    dr.line([(x0, y), (x1, y)], fill=(80, 80, 80), width=1)
    for s in range(0, 33):
        X = x0 + (x1 - x0) * s / 32
        dr.line([(X, y - 3), (X, y + 3)], fill=(70, 70, 70))
    for c in CHOICES:
        X = x0 + (x1 - x0) * c['t'] / 32
        dr.line([(X, y - 7), (X, y + 7)], fill=(150, 140, 120) if t >= c['t'] else (90, 88, 84), width=2)
    X = x0 + (x1 - x0) * t / 32
    dr.line([(X, y - 12), (X, y + 12)], fill=(240, 236, 228), width=2)
    dr.text((x0, 622), 'score %05.2f s · frame %03d' % (t, n), font=F_HUD, fill=INK)
    cur = None
    for pt, s in PROMPTS:
        if pt <= t < pt + 2.4:
            cur = s
    if cur:
        dr.text((380, 618), cur, font=F_PROMPT, fill=(236, 220, 190))
    P = FR[n]['person']
    tags = []
    if P['voice'] != 'none': tags.append('voice: ' + P['voice'])
    if P['hand'] != 'none': tags.append('hand: ' + P['hand'])
    tags.append('person: ' + P['posture'] + ', ' + P['place'])
    tags.append('door: ' + FR[n]['door'])
    dr.text((x0, 654), '   '.join(tags), font=F_HUD, fill=(150, 146, 138))

# ===================== the scene frame =====================
PLATES = None
EDL = []
TRACE = []

def scene_frame(n):
    global PLATES
    if PLATES is None:
        PLATES = build_plates()
    f = FR[n]; t = f['t']; P = f['person']
    base = PLATES.copy()
    edl = {'i': n, 't': t}
    # --- door (and, until she steps aside, the person in it)
    open_amt = float(np.clip((t - 6.2) / 0.5, 0, 1))
    dk, dx0, dop, dtag = door_frame_for(t, P)
    dl, warm = door_layer(dk, dx0, open_amt)
    base[DOOR_TOP:WALL_BASE, int(DOOR_L):int(DOOR_L) + dl.shape[1]] = dl
    base[DOOR_TOP - 8:DOOR_TOP, int(DOOR_L) - 8:int(DOOR_R) + 8] *= 0.35
    base[DOOR_TOP - 8:WALL_BASE, int(DOOR_L) - 8:int(DOOR_L)] *= 0.35
    base[DOOR_TOP - 8:WALL_BASE, int(DOOR_R):int(DOOR_R) + 8] *= 0.35
    edl['door'] = {'src': 'door', 'f': dk, 'crop_x0_mirrored': round(dx0, 1), 'op': dop}
    sc = (DOOR_R - DOOR_L) / DOOR_CROP_W
    if t < 5.417:
        pm = ('door', dk, dop, dtag)
        if P['reach'] > 0.02:
            hk = int(t * 12) % 62
            hl = scale_rgba(hand_cut(hk), S_HAND)
            hx = DOOR_L + 112 * sc - hl.shape[1] * (1 - P['reach'] * 0.95)
            hy = DOOR_TOP + 168 * (WALL_BASE - DOOR_TOP) / 288 - P['reach'] * 8
            over(base, hl, hx, hy)
            edl['hand'] = {'src': 'hand', 'f': hk, 'op': 'MIRROR · CUT · SLIDE from her hand (reach %.2f)' % P['reach'], 'tag': 'MIRROR · SLIDE'}
    elif P['sit'] < 0.5:
        pm = ('door', dk, dop, dtag)
    else:
        seq = list(range(0, 50)) + list(range(48, 0, -1))
        sk = seq[int(t * 6) % len(seq)]
        a_, o = seated_cut(sk)
        lay = scale_rgba(a_, S_SEAT)
        px = sx(P['x']) - (230 - o[0]) * S_SEAT
        py = WALL_BASE + 6 - (226 - o[1]) * S_SEAT
        over(base, lay, px, py)
        pm = ('seated', sk, 'MIRROR · CUT · PING-PONG 1:2 · SUBSTITUTED at sit 0.5', 'MIRROR · PING-PONG')
        if P['low'] > 0.02 or P['hand'] == 'low':
            hk = int(t * 12) % 62
            hl = scale_rgba(hand_cut(hk), S_HAND)
            hi = Image.fromarray((hl * 255).astype(np.uint8), 'RGBA').rotate(-14, resample=Image.BICUBIC, expand=True)
            hl = np.asarray(hi).astype(np.float32) / 255
            u = min(1.0, P['low'])
            hx = sx(-0.62) - hl.shape[1] * (1 - u) + 10
            hy = GROUND - 0.36 * K
            over(base, hl, hx, hy)
            edl['hand'] = {'src': 'hand', 'f': hk, 'op': 'MIRROR · CUT · ROTATE -14° · SLIDE (low hand)', 'tag': 'MIRROR · SLIDE'}
    edl['person'] = {'src': pm[0], 'f': pm[1], 'op': pm[2]}
    # --- dog: anchored and measured by its body (the head piece, when composed, may move; the body does not)
    p = dog_pick(n)
    lay, body, face = dog_layer(p)
    ab = body[..., 3]
    ys, xs = np.nonzero(ab > 0.25)
    cx = (ab[ys, xs] * xs).sum() / ab[ys, xs].sum()
    bottom = ys.max()
    X = sx(f['dog']['x']) - cx
    Y = GROUND - bottom
    sh_w = (xs.max() - xs.min()) * 0.55
    sh = np.exp(-(((XX - (X + cx)) / max(20, sh_w)) ** 2 + ((YY - (GROUND - 2)) / 6) ** 2))
    base *= (1 - 0.45 * sh[..., None])
    res = over(base, lay, X, Y)
    edl['dog'] = {'src': 'dog', 'f': p['src'], 'mirror': p['mirror'], 'fold': p['fold'], 'op': p['op']}
    X0_, Y0_, X1_, Y1_, A = res
    Bd = body[Y0_ - int(round(Y)):Y1_ - int(round(Y)), X0_ - int(round(X)):X1_ - int(round(X)), 3]
    by_, bx_ = np.nonzero(Bd > 0.25); bw = Bd[by_, bx_]
    mx = X0_ + (bw * bx_).sum() / bw.sum(); my = Y0_ + (bw * by_).sum() / bw.sum()
    bxa, bxb = bx_.min(), bx_.max()
    # back line: least-squares fit to the top edge of the body over its middle 60 %
    cols = np.arange(int(bxa + 0.2 * (bxb - bxa)), int(bxa + 0.8 * (bxb - bxa)) + 1)
    tops = [(c_, np.nonzero(Bd[:, c_] > 0.5)[0].min()) for c_ in cols if (Bd[:, c_] > 0.5).any()]
    if len(tops) > 5:
        tx_, ty_ = np.array(tops, float).T
        back_deg = float(abs(np.degrees(np.arctan(np.polyfit(tx_, ty_, 1)[0]))))
    else:
        back_deg = float('nan')
    yy, xx = np.nonzero(A > 0.25)
    w_ = A[yy, xx]
    left = X0_ + xx.min(); right = X0_ + xx.max(); top = Y0_ + yy.min()
    span = xx.max() - xx.min()
    front = (xx < xx.min() + 0.28 * span) if face <= 0 else (xx > xx.max() - 0.28 * span)
    head_h = int(GROUND - (Y0_ + yy[front].min())) if front.any() else 0
    frac_in = float((w_ * ((X0_ + xx) < DOOR_R)).sum() / w_.sum())
    frac_len = float(np.clip((DOOR_R - left) / max(1, right - left), 0, 1))
    posture = 'lying' if (p['fold'] is not None and p['fold'][0] != 'squash' and p['fold'][0] > 0.5) or (p['fold'] is not None and p['fold'][0] == 'squash' and p['fold'][1] > 0.5) else 'standing'
    hface = None
    if p['fold'] is not None and len(p['fold']) > 2 and p['fold'][2] == 'swap8':
        hface = 'door'
    TRACE.append({'i': n, 't': t, 'state': f['dog']['state'], 'x_score': f['dog']['x'],
                  'x_screen': round(float(mx), 1), 'y_screen': round(float(my), 1),
                  'x_measured_m': round(float((mx - X0) / K), 3),
                  'facing': {-1: 'door', 0: 'camera', 1: 'away'}[face], 'head_facing': hface or {-1: 'door', 0: 'camera', 1: 'away'}[face],
                  'posture': posture, 'back_line_deg': round(back_deg, 1), 'height_px': int(GROUND - top), 'head_height_px': head_h,
                  'nose_left_px': int(left), 'tail_right_px': int(right),
                  'frac_inside_door_frame': round(frac_in, 3), 'frac_length_inside_jamb': round(frac_len, 3),
                  'src_frame': p['src'], 'mirror': p['mirror'], 'op': p['op']})
    # --- light
    base[BAND_T:BAND_B] *= light_field(open_amt)[BAND_T:BAND_B]
    # band edge vignette
    vy = np.clip((YY[BAND_T:BAND_B] - BAND_T) / 24, 0, 1) * np.clip((BAND_B - YY[BAND_T:BAND_B]) / 10, 0, 1)
    base[BAND_T:BAND_B] *= (0.55 + 0.45 * vy[..., None])
    img = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(img)
    # --- monitors: the unmodified archive frames in use, with their records
    dpol = dog.polys(p['src'])
    draw_monitor(img, dr, 12, 'DOG', dog, p['src'], p['tag'], True, outline=[max(dpol, key=poly_area)] if dpol else None)
    draw_monitor(img, dr, 332, 'DOOR', door, dk, dtag, True)
    if pm[0] == 'door':
        draw_monitor(img, dr, 652, 'PERSON', door, pm[1], pm[3], True)
    else:
        sp = seated.polys(pm[1])
        draw_monitor(img, dr, 652, 'PERSON', seated, pm[1], pm[3], True, outline=[max(sp, key=poly_area)] if sp else None)
    hk = edl.get('hand', {}).get('f', 0)
    draw_monitor(img, dr, 972, 'HAND', hand, hk, edl['hand']['tag'] if 'hand' in edl else 'not on screen', 'hand' in edl,
                 outline=hand.polys(hk) if 'hand' in edl else None)
    dr.text((14, BAND_T + 6), 'COMPOSED SCENE · not a recorded event', font=F_HUD, fill=(156, 152, 144))
    draw_score(dr, n)
    EDL.append(edl)
    return img

# ===================== cards =====================
def title_card(k):
    img = Image.new('RGB', (W, H), (20, 20, 22)); dr = ImageDraw.Draw(img)
    a = min(1, k / 12) * min(1, (TITLE_N - k) / 10)
    c = tuple(int(v * a) for v in (232, 226, 214)); c2 = tuple(int(v * a) for v in AMBER); c3 = tuple(int(v * a) for v in (150, 146, 138))
    dr.text((96, 250), 'PAE-02 · SCION 53 · Atlanta Moving Image — Civic Footage Performer', font=font('display9', 40), fill=c)
    dr.text((96, 316), 'The threshold, re-performed by a dog from a home movie.', font=font('serifi', 26), fill=c2)
    dr.text((96, 376), 'Amateur Film New Jersey C · Home Movies, Internet Archive · undated · public domain', font=F_HUD, fill=c3)
    dr.text((96, 400), 'Every fragment on screen is shown above it as recorded, with its clip, frame and operation.', font=F_HUD, fill=c3)
    return img

END_LINES = [
    ('MADE OF', ''),
    ('dog', 'Amateur Film New Jersey C · undated home movie · Home Movies, Internet Archive'),
    ('', 'archive.org/details/NewJerseyC · clip 2fdacde1 · public domain · SAM-masked frames'),
    ('', 're-timed, reversed, mirrored, held; lying, head turned back and head lifts'),
    ('', 'COMPOSED from f044 by folding the cut-out (not in the footage)'),
    ('door, person', 'Straight Talk · 1992 · NTIS · archive.org/details/gov.ntis.ava19144vnb1'),
    ('', 'clip 271d80c7 · public domain · mirrored · the woman in the door, her step aside,'),
    ('', 'the door swinging to and, run backward, opening'),
    ('person, seated', 'Survival Stresses · 1961 · archive.org/details/hmdvid-101704143 · mirrored'),
    ('hand', 'The Door to Heaven · 1941 · archive.org/details/DoortoHe1941 · card left out'),
    ('walls, path', 'stone pillar and gravel path of the house in the home movie · sill, light computed'),
    ('sound', 'synthesized with numpy · the calls are formant tones, not words'),
    ('', "real people's films, re-performed and marked as composed"),
]
def end_card(k):
    img = Image.new('RGB', (W, H), (20, 20, 22)); dr = ImageDraw.Draw(img)
    a = min(1, k / 10) * min(1, (END_N - k) / 12)
    y = 120
    for lab, s in END_LINES:
        if lab == 'MADE OF':
            dr.text((80, y - 62), 'What this is made of', font=font('display9', 38), fill=tuple(int(v * a) for v in (232, 226, 214)))
            continue
        if lab:
            y += 10
        dr.text((80, y), lab, font=F_HUD_B, fill=tuple(int(v * a) for v in AMBER))
        dr.text((262, y), s, font=F_HUD, fill=tuple(int(v * a) for v in INK))
        y += 24
    dr.text((80, 672), 'PAE-02 · SCION 53 · score: paeleo/threshold/machine.js, 768 frames, 24 fps', font=F_HUD, fill=tuple(int(v * a) for v in (130, 126, 120)))
    return img

def main():
    if len(sys.argv) > 2 and sys.argv[1] == '--still':
        for s in sys.argv[2:]:
            t = float(s); n = int(round(t * 24))
            scene_frame(n).save(os.path.join(os.environ.get('OUT', '.'), 'still_%05.2f.jpg' % t), quality=92)
        return
    out = sys.stdout.buffer
    for k in range(TITLE_N):
        out.write(title_card(k).tobytes())
    for n in range(N):
        out.write(scene_frame(n).tobytes())
        if n % 96 == 0:
            print('frame', n, file=sys.stderr)
    for k in range(END_N):
        out.write(end_card(k).tobytes())
    with open(os.path.join(ROOT, 'trace.json'), 'w') as fh:
        json.dump({'about': 'Measured from the render: x_screen/y_screen are the alpha-weighted centroid of the composited dog layer; '
                   'x_measured_m maps it back through x = (x_screen - %.0f) / %.0f. facing comes from the archive frame and the mirror flag '
                   '(structural, not measured from pixels). posture is lying when the fold composite has lie > 0.5. frac_inside_door_frame is the share '
                   'of dog alpha left of the door frame\'s outer edge (x = 0.46 m). head_height_px is the highest alpha point in the front 28%% of the body (the head end), above the ground line.' % (X0, K),
                   'scene_offset_frames': TITLE_N, 'fps': 24, 'frames': TRACE}, fh)
    with open(os.path.join(HERE, 'edl.json'), 'w') as fh:
        json.dump(EDL, fh)

if __name__ == '__main__':
    main()
