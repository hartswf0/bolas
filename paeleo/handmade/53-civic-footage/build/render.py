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
def door_frame_for(t):
    """ajar = source f027 held (a thin warm gap); opens 6.2 s -> 6.7 s by playing the closing swing backwards f027 -> f022."""
    if t < 6.2:
        return 27, 'HELD f027 (ajar)'
    k = min(5, int((t - 6.2) * 12))
    if k < 5:
        return 27 - k, 'REVERSE f027>f022 (the door opens)'
    return 22, 'HELD f022 (open)'

def door_layer(i):
    im = door.frame(i)
    c = door.camera
    dx = c[i][0] - c[DOOR_REF][0]; dy = c[i][1] - c[DOOR_REF][1]
    box = (106 + dx, 0 + dy, 238 + dx, 288 + dy)
    cr = im.crop(tuple(int(round(v)) for v in box)).resize((int(DOOR_R - DOOR_L), WALL_BASE - DOOR_TOP), Image.BICUBIC)
    a = np.asarray(cr).astype(np.float32) / 255
    L = a @ np.array([0.299, 0.587, 0.114])
    hue = (a[..., 0] - a[..., 2]) / (a[..., 0] + 0.05)
    warm = np.clip((hue - 0.30) / 0.15, 0, 1)
    hh, ww = warm.shape
    warm[int(hh * 0.90):] = 0                      # the brown floor of the hallway is not light
    warm[:, :int(ww * 0.45)] *= 0                  # only the gap beside the door's edge
    warm = np.asarray(Image.fromarray((warm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
    grey = np.repeat(L[..., None], 3, -1) * 0.62       # the door panel sits in dusk
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
        return dict(src=k, mirror=False, fold=None, op='PLAY 1:1 · its own turn away (f015-f044, f021-25 cut)', tag='PLAY 1:1 (its turn)')
    if t < 7.458:
        return dict(src=44, mirror=False, fold=(a['lie'], lie_deg(a), False), op='COMPOSED: FOLD f044 · lies down, back turned', tag='COMPOSED FOLD')
    if t < 7.9:
        u = min(1.0, (t - 7.458) / 0.17)
        return dict(src=44, mirror=False, fold=(a['lie'], 70 + 30 * u, True), op='COMPOSED: FOLD f044 + HEAD MIRRORED at the neck · looks back at the door', tag='COMPOSED HEAD TURN')
    if t < 7.9 + len(TURN_BACK) / 12:
        k = TURN_BACK[min(len(TURN_BACK) - 1, int((t - 7.9) * 12))]
        return dict(src=k, mirror=False, fold=None, op='PLAY · turns to the door (f033>f014)', tag='PLAY (turns back)')
    if t < 14.708:
        seq = list(range(0, 16)) + list(range(14, 0, -1))
        k = seq[int((t - 8.4) * 6) % len(seq)]
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
    lie, hdeg, flip = p['fold']
    kp = POSE[str(k)]
    neck, nose, tail = kp['neck'], kp['nose'], kp['tail']
    if p['mirror']:
        neck, nose, tail = mirror_pt(neck), mirror_pt(nose), mirror_pt(tail)
    feet = max(kp['f1'][1], kp['f2'][1], kp['h1'][1], kp['h2'][1]) + 14
    args = (arr, o, neck, kp['chest'][1] + 8, 152, tail[0], feet, lie)
    full, _ = fold2(*args, hdeg, face, nose[1] + 9, head_flip=flip)
    body, _ = fold2(*args, hdeg, face, nose[1] + 9, no_head=True)
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

MON_W, MON_H = 152, 114
def draw_monitor(img, dr, x, label, src, k, op, active, outline=None, mirror=False):
    y = 12
    fr = src.frame(k).resize((MON_W, int(MON_W * src.frame(k).height / src.frame(k).width)), Image.BILINEAR)
    if not active:
        fr = Image.blend(fr, Image.new('RGB', fr.size, (24, 24, 27)), 0.72)
    img.paste(fr, (x, y))
    if outline and active:
        s = MON_W / src.frame(k).width
        for p in outline:
            if len(p) > 2:
                dr.line([(x + q[0] * s, y + q[1] * s) for q in p] + [(x + p[0][0] * s, y + p[0][1] * s)], fill=AMBER, width=1)
    dr.rectangle([x - 1, y - 1, x + MON_W, y + fr.height], outline=(70, 70, 70))
    title, year, rights = rec_line(src)
    tx = x + MON_W + 8
    dr.text((tx, y - 1), label, font=F_MONO_B, fill=AMBER if active else DIM)
    lines = [title[:24], year + ' · ' + rights.replace('_', ' '), 'clip ' + src.rec.get('clip_id', '')[:8],
             'f%03d  clip+%5.2fs' % (k, src.clip_time(k)), ('film ' + tc(src.source_time(k))) if src.source_time(k) is not None else 'film offset unknown']
    for j, s in enumerate(lines):
        dr.text((tx, y + 15 + j * 13), s, font=F_MONO_S, fill=INK if active else DIM)
    # operation, wrapped
    words = op.split(' '); ln = ''; yy = y + 15 + len(lines) * 13 + 2
    for w_ in words:
        if len(ln) + len(w_) + 1 > 21:
            dr.text((tx, yy), ln, font=F_MONO_S, fill=AMBER if active else DIM); yy += 12; ln = w_
        else:
            ln = (ln + ' ' + w_).strip()
    if ln:
        dr.text((tx, yy), ln, font=F_MONO_S, fill=AMBER if active else DIM)

CHOICES = SCORE['choices']
PROMPTS = SCORE['prompts']
def draw_score(dr, n):
    t = FR[n]['t']
    x0, x1, y = 24, W - 24, 676
    dr.line([(x0, y), (x1, y)], fill=(80, 80, 80), width=1)
    for s in range(0, 33):
        X = x0 + (x1 - x0) * s / 32
        dr.line([(X, y - 3), (X, y + 3)], fill=(70, 70, 70))
    # circumstances, as event tags on the timeline
    tl = SCORE['timeline']
    for c in CHOICES:
        X = x0 + (x1 - x0) * c['t'] / 32
        on = t >= c['t']
        dr.line([(X, y - 12), (X, y + 12)], fill=AMBER if on else (100, 96, 90), width=2)
        dr.text((X + 3, y + 6), c['to'].replace('_', ' '), font=F_MONO_S, fill=AMBER if on else DIM)
    X = x0 + (x1 - x0) * t / 32
    dr.line([(X, y - 18), (X, y + 18)], fill=(240, 236, 228), width=1)
    st = FR[n]['dog']['state'].replace('_', ' ')
    dr.text((x0, y - 30), 'SCORE  %05.2f s  frame %03d   dog: %s   x = %.2f m' % (t, n, st.upper(), FR[n]['dog']['x']), font=F_MONO, fill=INK)
    # the prompt on screen (the operator's circumstance), as a catalogue event tag
    cur = None
    for pt, s in PROMPTS:
        if pt <= t < pt + 2.4:
            cur = s
    if cur:
        dr.text((x0 + 520, y - 34), cur, font=F_SER, fill=(236, 220, 190))
    P = FR[n]['person']
    tags = []
    if P['voice'] != 'none': tags.append('VOICE: ' + P['voice'])
    if P['hand'] != 'none': tags.append('HAND: ' + P['hand'])
    tags.append('PERSON: ' + P['posture'] + ', ' + P['place'])
    tags.append('DOOR: ' + FR[n]['door'])
    dr.text((x0, y + 22), '   '.join(tags), font=F_MONO_S, fill=DIM)

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
    # --- door
    dk, dop = door_frame_for(t)
    dl, warm = door_layer(dk)
    open_amt = float(np.clip((t - 6.2) / 0.5, 0, 1))
    base[DOOR_TOP:WALL_BASE, int(DOOR_L):int(DOOR_L) + dl.shape[1]] = dl
    # door frame jambs (dark), so the flat reads as an opening in the stone wall
    base[DOOR_TOP - 8:DOOR_TOP, int(DOOR_L) - 8:int(DOOR_R) + 8] *= 0.35
    base[DOOR_TOP - 8:WALL_BASE, int(DOOR_L) - 8:int(DOOR_L)] *= 0.35
    base[DOOR_TOP - 8:WALL_BASE, int(DOOR_R):int(DOOR_R) + 8] *= 0.35
    edl['door'] = {'src': 'door', 'f': dk, 'op': dop}
    # --- person
    pm = None
    sit = P['sit']
    if sit < 0.5:
        seq = [3, 4, 5, 6, 5, 4]
        speak = P['voice'] == 'call'
        ck = seq[int(t * (10 if speak else 3)) % len(seq)]
        lay = scale_rgba(coat_cut(ck), S_COAT)
        px = sx(P['x']) - 36 * S_COAT
        py = WALL_BASE + 4 - 199 * S_COAT
        over(base, lay, px, py)
        pm = ('coat', ck, 'CUT (drawn matte) · ' + ('PLAY 10:12 while calling' if speak else 'PING-PONG f003-f006'))
        # the reach: the Door to Heaven arm slides out of the coat toward the porch
        if P['reach'] > 0.02:
            hk = int(t * 12) % 62
            hl = scale_rgba(hand_cut(hk), S_HAND)
            hx = px + 52 * S_COAT - hl.shape[1] * (1 - P['reach'] * 0.95)
            hy = GROUND - 0.98 * K - P['reach'] * 10
            over(base, hl, hx, hy)
            edl['hand'] = {'src': 'hand', 'f': hk, 'op': 'MIRROR · CUT · SLIDE (reach %.2f)' % P['reach']}
    else:
        seq = list(range(0, 50)) + list(range(48, 0, -1))
        sk = seq[int(t * 6) % len(seq)]
        a, o = seated_cut(sk)
        lay = scale_rgba(a, S_SEAT)
        # place by the seated body's head/torso column (mirrored source x ~ 230 -> person x)
        px = sx(P['x']) - (230 - o[0]) * S_SEAT
        py = WALL_BASE + 6 - (226 - o[1]) * S_SEAT
        over(base, lay, px, py)
        pm = ('seated', sk, 'MIRROR · CUT · PING-PONG 1:2 · SUBSTITUTED for the coat at sit 0.5')
        if P['low'] > 0.02 or P['hand'] == 'low':
            hk = int(t * 12) % 62
            hl = scale_rgba(hand_cut(hk), S_HAND)
            hi = Image.fromarray((hl * 255).astype(np.uint8), 'RGBA').rotate(-14, resample=Image.BICUBIC, expand=True)
            hl = np.asarray(hi).astype(np.float32) / 255
            u = min(1.0, P['low'])
            hx = sx(-0.62) - hl.shape[1] * (1 - u) + 10
            hy = GROUND - 0.36 * K
            over(base, hl, hx, hy)
            edl['hand'] = {'src': 'hand', 'f': hk, 'op': 'MIRROR · CUT · ROTATE -14° · SLIDE (low hand)'}
    edl['person'] = {'src': 'dog' if pm[0] == 'coat' else 'seated', 'f': pm[1], 'op': pm[2]}
    # --- dog
    p = dog_pick(n)
    lay, face = dog_layer(p)
    al = lay[..., 3]
    ys, xs = np.nonzero(al > 0.25)
    cx = (al[ys, xs] * xs).sum() / al[ys, xs].sum()
    bottom = ys.max()
    X = sx(f['dog']['x']) - cx
    Y = GROUND - bottom
    # contact shadow (computed): a soft dark ellipse under the body
    sh_w = (xs.max() - xs.min()) * 0.55
    sh = np.exp(-(((XX - (X + cx)) / max(20, sh_w)) ** 2 + ((YY - (GROUND - 2)) / 6) ** 2))
    base *= (1 - 0.45 * sh[..., None])
    res = over(base, lay, X, Y)
    edl['dog'] = {'src': 'dog', 'f': p['src'], 'mirror': p['mirror'], 'fold': p['fold'], 'op': p['op']}
    # measured from the composited alpha
    X0_, Y0_, X1_, Y1_, A = res
    yy, xx = np.nonzero(A > 0.25)
    w_ = A[yy, xx]
    mx = X0_ + (w_ * xx).sum() / w_.sum(); my = Y0_ + (w_ * yy).sum() / w_.sum()
    left = X0_ + xx.min(); right = X0_ + xx.max(); top = Y0_ + yy.min()
    span = xx.max() - xx.min()
    front = (xx < xx.min() + 0.28 * span) if face <= 0 else (xx > xx.max() - 0.28 * span)
    head_h = int(GROUND - (Y0_ + yy[front].min())) if front.any() else 0
    frac_in = float((w_ * ((X0_ + xx) < DOOR_R)).sum() / w_.sum())
    posture = 'lying' if (p['fold'] is not None and p['fold'][0] > 0.5) else 'standing'
    TRACE.append({'i': n, 't': t, 'state': f['dog']['state'], 'x_score': f['dog']['x'],
                  'x_screen': round(float(mx), 1), 'y_screen': round(float(my), 1),
                  'x_measured_m': round(float((mx - X0) / K), 3),
                  'facing': {-1: 'door', 0: 'camera', 1: 'away'}[face], 'posture': posture,
                  'height_px': int(GROUND - top), 'head_height_px': head_h, 'nose_left_px': int(left), 'tail_right_px': int(right),
                  'frac_inside_door_frame': round(frac_in, 3), 'src_frame': p['src'], 'mirror': p['mirror'], 'op': p['op']})
    # --- light
    base[BAND_T:BAND_B] *= light_field(open_amt)[BAND_T:BAND_B]
    # band edge vignette
    vy = np.clip((YY[BAND_T:BAND_B] - BAND_T) / 24, 0, 1) * np.clip((BAND_B - YY[BAND_T:BAND_B]) / 10, 0, 1)
    base[BAND_T:BAND_B] *= (0.55 + 0.45 * vy[..., None])
    img = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(img)
    # --- monitors: the unmodified archive frames in use, with their records
    dpol = dog.polys(p['src'])
    draw_monitor(img, dr, 16, 'DOG', dog, p['src'], p['op'], True, outline=[max(dpol, key=poly_area)] if dpol else None)
    draw_monitor(img, dr, 336, 'DOOR', door, dk, dop, True)
    if pm[0] == 'coat':
        draw_monitor(img, dr, 656, 'PERSON', dog, pm[1], pm[2], True, outline=[COAT_POLY])
    else:
        sp = seated.polys(pm[1])
        draw_monitor(img, dr, 656, 'PERSON', seated, pm[1], pm[2], True, outline=[max(sp, key=poly_area)] if sp else None)
    hk = edl.get('hand', {}).get('f', 0)
    draw_monitor(img, dr, 976, 'HAND', hand, hk, edl['hand']['op'] if 'hand' in edl else 'not on screen', 'hand' in edl,
                 outline=hand.polys(hk) if 'hand' in edl else None)
    # the fiction, marked
    dr.text((14, BAND_T + 6), 'COMPOSED SCENE · archive fragments re-performed · not a recorded event', font=F_MONO_S, fill=(150, 146, 138))
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
    dr.text((96, 372), 'Amateur Film New Jersey C · Home Movies, Internet Archive · undated · public domain', font=F_MONO, fill=c3)
    dr.text((96, 392), 'Every fragment on screen is shown above it as it was recorded, with its clip, frame and operation.', font=F_MONO, fill=c3)
    return img

END_LINES = [
    ('MADE OF', ''),
    ('dog', 'Amateur Film New Jersey C · undated home movie · Home Movies (Internet Archive) · archive.org/details/NewJerseyC'),
    ('', 'clip 2fdacde1 · film 225.56-235.40 s · 50 frames, SAM masks · public domain · re-timed, reversed, mirrored, held;'),
    ('', 'lying down and head pivots COMPOSED by folding the cut-out (not in the footage)'),
    ('person, standing', 'the person in the same home movie (coat and legs) · drawn matte · slid aside'),
    ('door', 'Straight Talk · 1992 · NTIS · archive.org/details/gov.ntis.ava19144vnb1 · clip 271d80c7 · public domain · reversed swing'),
    ('person, seated', 'Survival Stresses · 1961 · archive.org/details/hmdvid-101704143 · clip 1d980180 · public domain · mirrored'),
    ('hand', 'The Door to Heaven · 1941 · archive.org/details/DoortoHe1941 · clip 0870ef3a · public domain · mirrored, card removed'),
    ('walls, path', 'stone pillar and gravel path of the house in the home movie, tiled · sill and light computed'),
    ('sound', 'synthesized with numpy: no recorded voices; the calls are formant tones, not words'),
    ('', 'clips via movingimagearchive.com · these are real people\'s films: shown here re-performed, marked as composed'),
]
def end_card(k):
    img = Image.new('RGB', (W, H), (20, 20, 22)); dr = ImageDraw.Draw(img)
    a = min(1, k / 10) * min(1, (END_N - k) / 12)
    y = 150
    for lab, s in END_LINES:
        if lab == 'MADE OF':
            dr.text((96, y - 50), 'What this is made of', font=font('display9', 34), fill=tuple(int(v * a) for v in (232, 226, 214)))
            continue
        dr.text((96, y), lab, font=F_MONO_B, fill=tuple(int(v * a) for v in AMBER))
        dr.text((262, y), s, font=F_MONO_S, fill=tuple(int(v * a) for v in INK))
        y += 30 if lab else 22
    dr.text((96, 640), 'PAE-02 · SCION 53 · score: paeleo/threshold/machine.js, 768 frames, 24 fps', font=F_MONO_S, fill=tuple(int(v * a) for v in (130, 126, 120)))
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
