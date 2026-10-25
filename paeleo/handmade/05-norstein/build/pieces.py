"""The dog as a Norstein cutout: a library of hand-cut, hand-painted replacement pieces, chosen and hinged per frame.

The library (cut once, kept in build/cache/pieces/):
  body   one piece per view and posture: views L (facing the door), BL (three-quarter, rump to us), B (rear), FL
         (three-quarter, chest to us), F (front); R, BR, FR are the same pieces turned over (a cutout painted on both
         sides). Postures: standing, half and full crouch, three stages of lying down (replacement drawings, not a tween).
  head   one piece per view (the same eight, five drawn) x ears (laid back, half, pricked) x eyes (open, shut).
  limbs  upper, lower and paw pieces for the forelegs; thigh, shin, hock and paw for the hind legs; a near (lit) and a
         far (shadowed) cut of each; three tail pieces; a neck piece; a side paw and a front paw.
Each piece is cut from a drawing taken off the maquette at that view (the maquette is the cutting guide, as a sculpted
reference is for a cutout animator), then cut: its outline is broken by a scissor wobble and short hairs, it is painted
with its own fixed brush texture and the archive dog's coat grain, its cut edge is darkened. Pieces never change shape
between frames: a turn is a change of piece, a step is a hinge.

Per frame (render): the maquette, posed by the controller and the foot solver, is used only as a guide for where the
hinges are; the pieces are chosen (view, posture, ears), hinged on those points, and laid on the dog's glass in depth
order, each casting a soft shadow on the pieces under it.
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
import dog as DOG

LIB = os.path.join(CACHE, 'pieces')
LPPM = 640.0          # library pixels per metre
EL = math.radians(10)  # the library is drawn as the camera sees the dog: from 10 degrees above
VIEWS = {4: 'L', 3: 'BL', 2: 'B', 5: 'FL', 6: 'F'}          # sector k: yaw = k*pi/4 (pi = facing the door)
MIRROR = {0: 4, 1: 3, 7: 5}                                    # R, BR, FR are turned-over L, BL, FL
CROUCH = [0.0, 0.45, 0.9]
LIE = [0.0, 0.33, 0.66, 1.0]
EARS = [0.0, 0.5, 1.0]
RNG_SEED = 505


# ------------------------------------------------------------------------------------------------ drawing the pieces
def oproj(P):
    return np.array([P[0], P[1] * math.cos(EL) + P[2] * math.sin(EL)]), P[2] * math.cos(EL) - P[1] * math.sin(EL)


def cut_ortho(prims, keep):
    """the maquette's primitives (only those `keep` accepts) as flat 2D shapes in metres (u right, v up)."""
    J = np.array([[1, 0, 0], [0, math.cos(EL), math.sin(EL)]])
    out = []
    for pr in prims:
        if not keep(pr):
            continue
        if pr[0] == 'ell':
            _, cen, A, tone, tag = pr
            uv, d = oproj(cen)
            B = J @ A
            poly = DOG.ellipse_poly(uv[0], uv[1], B @ B.T, 40)
            out.append((d, poly, tone, 'p'))
        elif pr[0] == 'cap':
            _, p0, p1, r0, r1, tone, tag = pr
            a, da = oproj(p0)
            b, db = oproj(p1)
            out.append(((da + db) / 2, DOG.capsule_poly(a, b, r0, r1, 10), tone, 'p'))
        elif pr[0] == 'tri':
            _, pts, tone, tag = pr
            q = [oproj(v) for v in pts]
            out.append((sum(x[1] for x in q) / 3 - 0.005, [tuple(x[0]) for x in q], tone, 'p'))
        elif pr[0] == 'eye':
            _, cen, r, op, tag = pr
            uv, d = oproj(cen)
            out.append((d - 0.01, (uv[0], uv[1], r, op), 0.0, 'eye'))
    return out


def noise_field(h, w, scale, seed):
    r = np.random.default_rng(seed)
    sh = max(2, int(h / scale)), max(2, int(w / scale))
    f = Image.fromarray((r.random(sh) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(f, np.float32) / 255


COAT = None


def coat_grain(h, w):
    global COAT
    if COAT is None:
        COAT = np.load(os.path.join(CACHE, 'coat_tex.npy'))
    reps = (h // COAT.shape[0] + 1, w // COAT.shape[1] + 1)
    return np.tile(COAT, reps)[:h, :w]


def paint(shapes, seed, kind, axis_deg=0.0, hair=True):
    """cut and paint one piece from its 2D shapes. Returns (tone L image, alpha L image, origin offset in px)."""
    pts = np.array([q for d, g, t, k in shapes if k == 'p' for q in g])
    m = 0.03
    u0, v0 = pts.min(0) - m
    u1, v1 = pts.max(0) + m
    S = 2  # paint at 2x, keep at 1x
    w, h = int((u1 - u0) * LPPM * S), int((v1 - v0) * LPPM * S)

    def P(u, v):
        return ((u - u0) * LPPM * S, (v1 - v) * LPPM * S)
    tone = Image.new('L', (w, h), 0)
    al = Image.new('L', (w, h), 0)
    dt, da = ImageDraw.Draw(tone), ImageDraw.Draw(al)
    zs = [d for d, g, t, k in shapes if k == 'p']
    zmin = min(zs)
    eyes = []
    for d, g, t, k in sorted(shapes, key=lambda r: -r[0]):
        if k == 'p':
            tn = t * (1 - 0.35 * clamp(d - zmin, 0, 0.35))
            poly = [P(*q) for q in g]
            dt.polygon(poly, fill=int(clamp(tn * 160, 0, 255)))
            da.polygon(poly, fill=255)
        else:
            eyes.append((d, g))
    dhead = max(zs)  # an eye shows only on the near side of the skull
    eyes = [(d, g) for d, g in eyes if d < np.median(zs) - 0.015]
    A = np.asarray(al, np.float32) / 255
    T = np.asarray(tone.filter(ImageFilter.GaussianBlur(2.5 * S)), np.float32)  # painted, not shaded: soft inner forms
    # the scissor cut: the outline wobbles a little (low frequency) and, on coat pieces, breaks into short hairs
    Ab = np.asarray(Image.fromarray((A * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6 * S)), np.float32) / 255
    wob = noise_field(h, w, 26 * S, seed) - 0.5
    thr = 0.5 + 0.30 * wob
    if hair:
        hf = np.asarray(Image.fromarray((np.random.default_rng(seed + 1).random((h, w)) * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(0.7 * S)), np.float32) / 255
        thr = thr + (hf - 0.5) * 0.9
    Ac = np.clip((Ab - thr) / 0.06 + 0.5, 0, 1)
    # the brush: short strokes along the piece's grain, fixed to the piece
    br = Image.new('L', (w, h), 128)
    db = ImageDraw.Draw(br)
    r = np.random.default_rng(seed + 2)
    ax = math.radians(axis_deg)
    for _ in range(int(w * h / (60 * S * S))):
        x, y = r.uniform(0, w), r.uniform(0, h)
        L = r.uniform(6, 16) * S
        a = ax + r.normal(0, 0.35)
        db.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=int(r.uniform(70, 190)), width=max(1, int(1.2 * S)))
    brush = np.asarray(br.filter(ImageFilter.GaussianBlur(0.8 * S)), np.float32) / 255
    grain = coat_grain(h, w)
    grain = np.asarray(Image.fromarray(((grain + 1) * 127).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5 * S)), np.float32) / 127 - 1
    tex = 0.80 + 0.32 * brush + 0.05 * grain
    # the cut edge is darker (the paper's edge and the paint pooled at it)
    inner = np.asarray(Image.fromarray((Ac * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2 * S)), np.float32) / 255
    rim = np.clip((1 - inner) * 2.2, 0, 1) * Ac
    Tn = T / np.maximum(A, 1e-3) * tex * (1 - 0.45 * rim)  # the cut edge: a visible seam
    Tn = np.where(Ac > 0, Tn, 0)
    tone_im = Image.fromarray(np.clip(Tn, 0, 255).astype(np.uint8))
    al_im = Image.fromarray((Ac * 255).astype(np.uint8))
    d2 = ImageDraw.Draw(tone_im)
    for d, (u, v, rr, op) in eyes:  # eyes: painted on the piece
        cx, cy = P(u, v)
        R = rr * LPPM * S
        if op > 0.5:
            d2.ellipse([cx - R, cy - R * 0.85, cx + R, cy + R * 0.85], fill=16)
            g = R * 0.42
            d2.ellipse([cx - g * 1.3, cy - R * 0.45 - g, cx - g * 1.3 + 2 * g, cy - R * 0.45 + g], fill=235)
        else:
            d2.line([(cx - R, cy), (cx + R, cy + R * 0.2)], fill=24, width=max(1, int(0.6 * R)))
    tone_im = tone_im.resize((w // S, h // S), Image.LANCZOS)
    al_im = al_im.resize((w // S, h // S), Image.LANCZOS)
    return tone_im, al_im, (u0, v1)


def to_px(uv, origin):
    return ((uv[0] - origin[0]) * LPPM, (origin[1] - uv[1]) * LPPM)


def guide_params(psi, crouch=0.0, lie=0.0, ear=1.0, eye=1.0, alpha=20.0):
    p = dict(i=0, t=0.0, state='watch', x=0.0, z=0.0, psi=psi, bend=0.0, head_rel=0.0, alpha=alpha, lie=lie, crouch=crouch,
             ear=ear, tail=0.5, wag=0.0, wag_phase=0.0, rest=0.0, look=0.0, breath=0.0, eye=eye, moving=0.0)
    feet = {}
    for leg in DOG.LEGS:
        m, f, l = DOG.mount_world(p, leg)
        feet[leg] = (np.array([m[0], 0.0, m[2]]), 0.0, False)
    p['feet'] = feet
    return p


def save(name, tone, al, meta):
    Image.merge('LA', (tone, al)).save(os.path.join(LIB, name + '.png'))
    json.dump(meta, open(os.path.join(LIB, name + '.json'), 'w'))


def body_piece(k, cq, lq):
    name = 'body_%s_c%.2f_l%.2f' % (VIEWS[k], cq, lq)
    if os.path.exists(os.path.join(LIB, name + '.png')):
        return name
    p = guide_params(k * math.pi / 4, cq, lq)
    prims = DOG.build(p)
    shapes = cut_ortho(prims, lambda pr: pr[-1] == 'torso')
    tone, al, origin = paint(shapes, RNG_SEED + 10 * k + int(cq * 7) + int(lq * 31), 'body', axis_deg=0 if k in (4, 6) else 90)
    meta = dict(anchor=to_px(oproj(np.zeros(3))[0], origin), size=tone.size)
    save(name, tone, al, meta)
    return name


def back_head_piece(name, eq):
    """the back of the head, cut by hand (not taken off the maquette, where the ears would be edge-on): the round of the
    skull, the cheeks showing either side, both ears standing (or laid back), a darker nape."""
    sk = [(math.cos(a) * 0.078 * (1.0 + 0.12 * max(0, -math.sin(a))), 0.075 + math.sin(a) * 0.07) for a in np.linspace(0, 2 * math.pi, 40)]
    shapes = [(0.0, sk, 1.0, 'p')]
    for sgn in (1, -1):
        base0, base1 = (sgn * 0.022, 0.125), (sgn * 0.074, 0.105)
        tip = (sgn * lerp(0.13, 0.07, eq), lerp(0.11, 0.215, eq))
        shapes.append((-0.01, [base0, tip, base1], 0.9, 'p'))
    shapes.append((-0.02, [(-0.03, 0.0), (0.03, 0.0), (0.02, 0.05), (-0.02, 0.05)], 0.8, 'p'))  # the nape, darker
    tone, al, origin = paint(shapes, RNG_SEED + 777 + int(eq * 5), 'head', axis_deg=90)
    meta = dict(anchor=to_px((0.0, 0.0), origin), nose=to_px((0.0, 0.075), origin), size=tone.size, beta0=-5.0)
    save(name, tone, al, meta)
    return name


def head_piece(k, eq, eye):
    name = 'head_%s_e%.1f_%s' % (VIEWS[k], eq, 'open' if eye else 'shut')
    if os.path.exists(os.path.join(LIB, name + '.png')):
        return name
    if k == 2:
        return back_head_piece(name, eq)
    p = guide_params(k * math.pi / 4, ear=eq, eye=1.0 if eye else 0.0, alpha=20.0)
    prims = DOG.build(p)
    g = p['_g']
    attach = g['head'] - g['dh'] * 0.07
    shapes = cut_ortho(prims, lambda pr: pr[-1] == 'head')
    if k in (2, 3):  # turned away (lost profile): the cheek and the ear, no eye
        shapes = [sh for sh in shapes if sh[3] != 'eye']
    tone, al, origin = paint(shapes, RNG_SEED + 100 + 7 * k + int(eq * 3), 'head', axis_deg=0)
    nose = next(pr for pr in prims if pr[0] == 'ell' and pr[-1] == 'head' and pr[3] == 0.25)[1]
    meta = dict(anchor=to_px(oproj(attach)[0], origin), nose=to_px(oproj(nose)[0], origin), size=tone.size,
                beta0=math.degrees(g['beta']))
    save(name, tone, al, meta)
    return name


def strip_piece(name, L, r0, r1, seed, tone=1.0, hair=True):
    """a limb, neck or tail piece: drawn hanging from its hinge (anchor at the top), length L metres."""
    if os.path.exists(os.path.join(LIB, name + '.png')):
        return name
    shapes = [(0.0, DOG.capsule_poly((0.0, 0.0), (0.0, -L), r0, r1, 10), tone, 'p')]
    t, a, origin = paint(shapes, seed, 'limb', axis_deg=90, hair=hair)
    save(name, t, a, dict(anchor=to_px((0.0, 0.0), origin), end=to_px((0.0, -L), origin), size=t.size, L=L))
    return name


def paw_piece(name, front, seed):
    if os.path.exists(os.path.join(LIB, name + '.png')):
        return name
    if front:  # seen from the front or behind: a rounded paw with two toe notches
        poly = [(math.cos(a) * 0.034, 0.012 + math.sin(a) * 0.024) for a in np.linspace(0, 2 * math.pi, 30)]
    else:      # from the side, toes to the left
        poly = [(-0.05, 0.004), (-0.045, 0.02), (-0.02, 0.034), (0.02, 0.036), (0.034, 0.02), (0.03, 0.0), (-0.04, -0.004)]
    t, a, origin = paint([(0.0, poly, 1.0, 'p')], seed, 'paw', hair=False)
    save(name, t, a, dict(anchor=to_px((0.0, 0.0), origin), size=t.size))
    return name


LIMBS = dict(  # name: (length, r0, r1)
    f_upper=(DOG.UPPER_F, 0.052, 0.034), f_lower=(DOG.LOWER_F, 0.031, 0.024),
    h_thigh=(DOG.THIGH, 0.075, 0.042), h_shin=(DOG.SHIN, 0.04, 0.026), h_meta=(DOG.META, 0.025, 0.022),
    tail_a=(0.10, 0.03, 0.022), tail_b=(0.10, 0.022, 0.014), tail_c=(0.10, 0.014, 0.008),
    neck=(0.2, 0.08, 0.05))


def build_limbs():
    os.makedirs(LIB, exist_ok=True)
    for k, (n, (L, r0, r1)) in enumerate(LIMBS.items()):
        strip_piece(n, L, r0, r1, RNG_SEED + 300 + k)
    paw_piece('paw_side', False, RNG_SEED + 400)
    paw_piece('paw_front', True, RNG_SEED + 401)


def quant(v, levels):
    return min(levels, key=lambda q: abs(q - v))


def sector(yaw, X, Zw, c):
    """the view sector of a heading, as seen from the camera (the ray to the dog is not straight ahead)."""
    phi = math.atan2(Zw - c[2], X - c[0])
    rel = yaw - 0.35 * (phi - math.pi / 2)  # mostly the dog's own heading: profile holds unless it truly turns
    return int(round(rel / (math.pi / 4))) % 8


def choose(p, c):
    """which replacement pieces this frame uses (and the quantized posture the guide is posed in)."""
    cq = quant(p['crouch'], CROUCH)
    lq = quant(p['lie'], LIE)
    kb = sector(p['psi'] + 0.5 * p['bend'], p['x'], p['z'], c)
    psi_h = p['psi'] + p['bend'] + p['head_rel']
    kh = sector(psi_h, p['x'], p['z'], c)
    if lq > 0 or cq > 0.5:  # lying and deep crouch are drawn in profile only (the dog is never seen lying end-on)
        kb = 4 if math.cos(p['psi']) < 0 else 0
        cq = cq if lq == 0 else 0.0
    if cq > 0 and kb not in (4, 0):
        cq = 0.45 if cq > 0 else 0.0
    eq = quant(p['ear'], EARS)
    eye = p['eye'] > 0.5
    return dict(cq=cq, lq=lq, kb=kb, kh=kh, eq=eq, eye=eye)


def ensure(ch):
    kb = MIRROR.get(ch['kb'], ch['kb'])
    kh = MIRROR.get(ch['kh'], ch['kh'])
    return body_piece(kb, ch['cq'], ch['lq']), head_piece(kh, ch['eq'], ch['eye'])


# ------------------------------------------------------------------------------------------------ hinging per frame
_cache = {}


def load(name):
    if name not in _cache:
        im = Image.open(os.path.join(LIB, name + '.png'))
        t, a = im.split()
        _cache[name] = (t, a, json.load(open(os.path.join(LIB, name + '.json'))))
    return _cache[name]


class Canvas:
    def __init__(self, x0, y0, w, h, ss):
        self.x0, self.y0, self.ss = x0, y0, ss
        self.W, self.H = w * ss, h * ss
        self.tone = np.zeros((self.H, self.W), np.float32)
        self.al = np.zeros((self.H, self.W), np.float32)
        self.passes = {}

    def c(self, xy):
        return ((xy[0] - self.x0) * self.ss, (xy[1] - self.y0) * self.ss)

    def lay(self, name, target, angle, sx, sy, mirror=False, tone_k=1.0, pass_name=None, shadow=True):
        """lay a piece: its anchor on `target` (screen px), turned by `angle` (radians, clockwise on screen), scaled sx
        across and sy along its length (library px -> screen px), turned over if `mirror`."""
        t, a, meta = load(name)
        ax, ay = meta['anchor']
        if mirror:
            ax = meta['size'][0] - ax
            t, a = t.transpose(Image.FLIP_LEFT_RIGHT), a.transpose(Image.FLIP_LEFT_RIGHT)
        tx, ty = self.c(target)
        ca, sa = math.cos(angle), math.sin(angle)
        k = self.ss
        # output (canvas) -> piece: undo the translation, the rotation and the scale
        a11, a12 = ca / (sx * k), sa / (sx * k)
        a21, a22 = -sa / (sy * k), ca / (sy * k)
        data = (a11, a12, ax - a11 * tx - a12 * ty, a21, a22, ay - a21 * tx - a22 * ty)
        T = np.asarray(t.transform((self.W, self.H), Image.AFFINE, data, Image.BILINEAR), np.float32) * tone_k
        A = np.asarray(a.transform((self.W, self.H), Image.AFFINE, data, Image.BILINEAR), np.float32) / 255
        if shadow and self.al.any():  # the piece casts a soft shadow on the pieces under it
            sh = Image.fromarray((A * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5 * k))
            sh = np.roll(np.roll(np.asarray(sh, np.float32) / 255, int(2 * k), 0), int(1 * k), 1)
            self.tone *= 1 - 0.42 * sh * self.al
        self.tone = self.tone * (1 - A) + T * A
        # the cut edge of a piece catches the light where it lies over another piece: a thin pale seam
        sh = int(round(1.5 * k))
        edge = np.clip(A - np.roll(np.roll(A, sh, 0), sh, 1), 0, 1) * self.al
        self.tone = self.tone + 70.0 * edge * A
        self.al = A + self.al * (1 - A)
        if pass_name:
            self.passes[pass_name] = np.maximum(self.passes.get(pass_name, 0), A)
        return meta, (ax, ay), (tx, ty), (a11, a12, a21, a22)


def render(p, c):
    """the dog for one frame, laid from the piece library. Returns what dog.render returned, plus the nose point."""
    ch = choose(p, c)
    bname, hname = ensure(ch)
    q = dict(p)
    q['crouch'], q['lie'] = (ch['cq'] if ch['lq'] == 0 else 0.0), ch['lq']
    # the guide is posed at the chosen pieces' own angles, so the hinges sit where the drawn pieces have them
    off = 0.35 * (math.atan2(p['z'] - c[2], p['x'] - c[0]) - math.pi / 2)

    def near(a, ref):
        return a + 2 * math.pi * round((ref - a) / (2 * math.pi))
    psi_q = near(ch['kb'] * math.pi / 4 + off, p['psi'])
    head_abs = p['psi'] + p['bend'] + p['head_rel']
    head_q = near(ch['kh'] * math.pi / 4 + off, head_abs)
    q['psi'], q['bend'], q['head_rel'] = psi_q, 0.0, head_q - psi_q
    prims = DOG.build(q)
    g = q['_g']
    zc = p['z'] - c[2]
    s = F / zc / LPPM  # library px -> screen px
    P = lambda v: project(v, c)[:2]
    pts = [P(pr[1]) for pr in prims if pr[0] in ('ell', 'cap')]
    pts = np.array(pts)
    x0, y0 = np.floor(pts.min(0) - 0.35 * F / zc)
    x1, y1 = np.ceil(pts.max(0) + 0.35 * F / zc)
    cv = Canvas(int(x0), int(y0), int(x1 - x0), int(y1 - y0), 2)

    def depth(v):
        return project(v, c)[2]
    items = []
    # body
    mirror_b = ch['kb'] in MIRROR
    items.append((depth(g['root'] + np.array([0, 0.3, 0])), 'body'))
    # legs: segments from the guide
    legs = {}
    for pr in prims:
        if pr[0] == 'cap' and pr[-1].startswith('leg_'):
            legs.setdefault(pr[-1][4:], []).append((pr[1], pr[2]))
    paws = {pr[-1][4:]: pr[1] for pr in prims if pr[0] == 'ell' and pr[-1].startswith('leg_')}
    for leg, segs in legs.items():
        items.append((np.mean([depth(a) for a, b in segs]), 'leg', leg, segs, paws[leg]))
    tail = [(pr[1], pr[2]) for pr in prims if pr[0] == 'cap' and pr[-1] == 'tail']
    items.append((depth(tail[0][0]) + 0.01, 'tail', tail))
    items.append((depth(g['root'] + np.array([0, 0.3, 0])) + 0.02, 'neck'))  # behind the body piece: the shoulder covers its root
    items.append((depth(g['head']) - 0.02, 'head'))
    items.sort(key=lambda r: -r[0])
    fwd_screen = P(g['root'] + g['ff'] * 0.3)[0] - P(g['root'])[0]
    nose_px = None
    for it in items:
        kind = it[1]
        if kind == 'body':
            cv.lay(bname, P(g['root']), 0.0, s, s, mirror_b, pass_name='torso', shadow=False)
        elif kind == 'leg':
            leg, segs, paw = it[2], it[3], it[4]
            front = DOG.LEGS[leg]['front']
            far = DOG.far_side_tone(p, 'leg_' + leg, c) < 1
            names = ['f_upper', 'f_lower'] if front else ['h_thigh', 'h_shin', 'h_meta']
            for nm, (a3, b3) in zip(names, segs):
                a2, b2 = np.array(P(a3)), np.array(P(b3))
                d = b2 - a2
                Lpx = np.linalg.norm(d) + 1e-6
                ang = math.atan2(d[1], d[0]) - math.pi / 2  # pieces hang down (+y); turn to the bone
                L = LIMBS[nm][0]
                cv.lay(nm, a2, ang, s, Lpx / (L * LPPM), tone_k=0.84 if far else 0.92)
            side = abs(fwd_screen) > 0.35 * 0.3 * F / zc
            pname = 'paw_side' if side else 'paw_front'
            cv.lay(pname, P(paw - np.array([0, 0.02, 0])), 0.0, s, s, mirror=(fwd_screen > 0), tone_k=0.72 if far else 1.0)
        elif kind == 'tail':
            segs = it[2]
            for nm, (a3, b3) in zip(['tail_a', 'tail_b', 'tail_c'], [(segs[0][0], segs[1][1]), (segs[2][0], segs[3][1]), (segs[4][0], segs[5][1])]):
                a2, b2 = np.array(P(a3)), np.array(P(b3))
                d = b2 - a2
                ang = math.atan2(d[1], d[0]) - math.pi / 2
                cv.lay(nm, a2, ang, s, (np.linalg.norm(d) + 1e-6) / (0.10 * LPPM), tone_k=0.95)
        elif kind == 'neck':
            a2, b2 = np.array(P(g['nb'] - g['ff'] * 0.02)), np.array(P(g['head']))
            d = b2 - a2
            ang = math.atan2(d[1], d[0]) - math.pi / 2
            cv.lay('neck', a2, ang, s, max(0.5 * s, (np.linalg.norm(d) + 1e-6) / (0.2 * LPPM)))
        elif kind == 'head':
            attach = g['head'] - g['dh'] * 0.07
            meta = load(hname)[2]
            kh = ch['kh']
            view_yaw = kh * math.pi / 4
            sgn = -math.cos(view_yaw)
            ang = math.radians(math.degrees(g['beta']) - meta['beta0']) * sgn
            mirror_h = kh in MIRROR
            m, anc, tgt, A = cv.lay(hname, P(attach), ang, s, s, mirror_h, pass_name='head')
            nx, ny = meta['nose']
            if mirror_h:
                nx = meta['size'][0] - nx
            # forward-map the nose point through the same placement
            dx, dy = nx - anc[0], ny - anc[1]
            ca, sa = math.cos(ang), math.sin(ang)
            px_ = tgt[0] + (ca * dx * s - sa * dy * s) * cv.ss
            py_ = tgt[1] + (sa * dx * s + ca * dy * s) * cv.ss
            nose_px = (px_ / cv.ss + cv.x0, py_ / cv.ss + cv.y0)
    tone = Image.fromarray(np.clip(cv.tone, 0, 255).astype(np.uint8))
    alpha = Image.fromarray((np.clip(cv.al, 0, 1) * 255).astype(np.uint8))
    w, h = cv.W // 2, cv.H // 2
    torso = Image.fromarray((cv.passes.get('torso', np.zeros((cv.H, cv.W))) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    headm = Image.fromarray((cv.passes.get('head', np.zeros((cv.H, cv.W))) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    head_anchor = P(g['head'] - g['dh'] * 0.07)
    return cv.x0, cv.y0, tone, alpha, torso, headm, dict(choice=ch, body=bname, head=hname, nose_px=nose_px, head_anchor_px=head_anchor)


def build_library(P, cams):
    """cut every piece the film will use (called once, before the frames)."""
    os.makedirs(LIB, exist_ok=True)
    build_limbs()
    used = set()
    for p, c in zip(P, cams):
        ch = choose(p, c)
        used.add(ensure(ch))
    return sorted({n for pair in used for n in pair})
