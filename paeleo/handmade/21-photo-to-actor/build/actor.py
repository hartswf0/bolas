"""The actor: photo-textured parts on a body template, expression controls on the photographed heads, angle artwork by
sprite replacement. Draws one pose into a local RGBA canvas.

Coordinates. TEMPLATE space = source pixels of the profile frame f009 (the dog faces screen-left, forward = -x, y down).
The canvas maps template -> screen by K (1.2 screen px per template px) about the body centre C0. A right-facing dog is the
same pose drawn and then mirrored about the body centre (the photographs are mirrored as sprites; nothing is redrawn).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter, ImageChops, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import spec

K = 1.2                       # screen px per template px (1 m = 150 template px = 180 screen px)
CW, CH = 560, 400             # local canvas
C0 = np.array([(spec.JOINTS['S'][0] + spec.JOINTS['H'][0]) / 2, (spec.JOINTS['S'][1] + spec.JOINTS['H'][1]) / 2])
CC = np.array([CW / 2, 250.0])  # canvas point of the body centre
GROUND_C = CC[1] + (spec.GROUND_Y - C0[1]) * K   # canvas y of the ground

P = json.load(open(os.path.join(FOLDER, 'actor', 'parts.json')))
LM = json.load(open(os.path.join(FOLDER, 'actor', 'landmarks.json')))
IMG = {k: Image.open(os.path.join(FOLDER, v['file'])).convert('RGBA') for k, v in P.items()}


def t2c(p):
    return CC + (np.asarray(p, float) - C0) * K


def src2tmpl(part, pt):
    """sprite px -> source px (only for parts cut from f009, where source px == template px)"""
    x0, y0 = P[part]['box_src'][:2]; k = P[part]['scale_from_source']
    return np.array([pt[0] / k + x0, pt[1] / k + y0])


def place(canvas, img, sa, sb, da, db, perp=None, flip=False, shade=1.0):
    """map sprite segment sa->sb onto canvas segment da->db (canvas px). perp: scale across the axis (default = along)."""
    sa, sb, da, db = (np.asarray(v, float) for v in (sa, sb, da, db))
    u = sb - sa; Ls = np.hypot(*u); u /= Ls; v = np.array([-u[1], u[0]])
    U = db - da; Ld = np.hypot(*U); U /= max(Ld, 1e-6); V = np.array([-U[1], U[0]]) * (-1 if flip else 1)
    spar = Ld / Ls; sperp = spar if perp is None else perp
    A = spar * np.outer(U, u) + sperp * np.outer(V, v)
    t = da - A @ sa
    Ai = np.linalg.inv(A); c = -Ai @ t
    if shade != 1.0:
        r, g, b, a = img.split(); img = Image.merge('RGBA', [x.point(lambda q: int(q * shade)) for x in (r, g, b)] + [a])
    out = img.transform((CW, CH), Image.AFFINE, (Ai[0, 0], Ai[0, 1], c[0], Ai[1, 0], Ai[1, 1], c[1]), resample=Image.BILINEAR)
    canvas.alpha_composite(out)


def place_rot(canvas, img, pivot_s, ang, scale, at, flip=False):
    """put sprite point pivot_s at canvas point `at`, rotated by ang (rad), uniform scale"""
    sa = np.asarray(pivot_s, float); sb = sa + np.array([20.0, 0])
    da = np.asarray(at, float); db = da + 20 * scale * np.array([math.cos(ang), math.sin(ang)])
    place(canvas, img, sa, sb, da, db, flip=flip)


# ------------------------------------------------------------------------------------------- expression controls
class Head:
    """one photographed head (angle artwork) split into base + ear patches + jaw patch + brow patch, by its landmarks"""

    def __init__(self, name):
        self.name = name
        self.img = IMG['head_' + name]
        L = LM[name][LM[name].get('used', 'corrected')]; self.L = L   # the factory uses the automatic fit where it passed
        self.pivot = np.array(LM[name]['pivot'], float)
        W, H = self.img.size
        a = np.array(self.img)[:, :, 3].astype(float) / 255
        rgb = np.array(self.img)[:, :, :3].astype(float)
        # blurred fur fill (alpha-normalised) for what a moved patch uncovers
        blur = lambda arr, r: np.array(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(float)
        aw = blur(a * 255, 7) / 255 + 1e-3
        fill = np.stack([blur(rgb[:, :, c] * a, 7) / 255 / aw * 255 for c in range(3)], -1)
        yy, xx = np.mgrid[0:H, 0:W]
        diag = math.hypot(W, H)
        self.patches = []
        holes = np.zeros((H, W))
        for ek in (() if name == 'back' else ('ear_l', 'ear_r')):   # the assembled rear view keeps its ears whole (round 3)
            e = L.get(ek)
            if not e: continue
            r = 0.2 * diag
            m = np.clip(1.3 - np.hypot(xx - e[0], yy - (e[1] - 0.08 * diag)) / r, 0, 1) * a
            # only above / behind the ear base
            m *= np.clip((e[1] + 0.03 * diag - yy) / (0.05 * diag) + 0.5, 0, 1)
            self.patches.append(('ear', np.array(e), m))
            holes = np.maximum(holes, m)
        jh, nose, chin = L.get('jaw_hinge'), L.get('nose'), L.get('chin')
        if jh and nose and chin:
            jh, nose, chin = (np.array(v) for v in (jh, nose, chin))
            d = nose - jh; n = np.array([-d[1], d[0]])
            if np.dot(chin - jh, n) < 0: n = -n
            side = ((xx - jh[0]) * n[0] + (yy - jh[1]) * n[1]) / (np.hypot(*n) + 1e-6)
            r = np.hypot(*(chin - jh)) * 1.25 + 4
            m = np.clip(side / 3.0 + 0.2, 0, 1) * np.clip(1.2 - np.hypot(xx - (jh[0] + chin[0]) / 2, yy - (jh[1] + chin[1]) / 2) / r, 0, 1) * a
            self.patches.append(('jaw', jh, m))
            holes = np.maximum(holes, m)
        eyes = [np.array(L[k]) for k in ('eye_l', 'eye_r') if L.get(k)]
        for e in eyes:
            r = 0.08 * diag
            m = np.clip(1.3 - np.hypot(xx - e[0], yy - (e[1] - 0.06 * diag)) / r, 0, 1) * a * 0.9
            self.patches.append(('brow', e, m))
        holes = np.clip(holes, 0, 1)[:, :, None]
        base_rgb = rgb * (1 - holes) + fill * holes
        core = np.array(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(9))).astype(float) / 255
        base_a = np.maximum(core, a * (1 - holes[:, :, 0] * 0.85))
        self.base = Image.fromarray(np.dstack([base_rgb, base_a * 255]).clip(0, 255).astype(np.uint8), 'RGBA')
        self.patch_imgs = []
        for kind, piv, m in self.patches:
            self.patch_imgs.append((kind, piv, Image.fromarray(np.dstack([rgb, m * 255]).clip(0, 255).astype(np.uint8), 'RGBA')))
        self.area = float(a.sum())

    def compose(self, ear=0.6, mouth=0.0, brow=0.0):
        """ear: 0 flat .. 1 pricked ; mouth: 0 shut .. 1 open ; brow: -1 down .. 1 raised (worried)"""
        out = self.base.copy()
        W, H = out.size
        for kind, piv, im in self.patch_imgs:
            if kind == 'ear':
                ang = (0.65 - ear) * 38          # flattening swings the ear back and down (+ = clockwise in screen)
                if piv[0] > W * 0.55 and self.name in ('front', 'tq', 'back'): ang = -ang
                rot = im.rotate(-ang, resample=Image.BILINEAR, center=tuple(piv), translate=(0, (0.6 - ear) * 3))
                out.alpha_composite(rot)
            elif kind == 'jaw':
                ang = mouth * 13
                sgn = -1 if self.name in ('profile', 'low') else 1
                rot = im.rotate(sgn * ang, resample=Image.BILINEAR, center=tuple(piv), translate=(0, mouth * 2))
                out.alpha_composite(rot)
            elif kind == 'brow':
                out.alpha_composite(im.transform(im.size, Image.AFFINE, (1, 0, 0, 0, 1, brow * 2.2), resample=Image.BILINEAR))
        return out


HEADS = {n: Head(n) for n in ('profile', 'low', 'tq', 'front', 'back')}
# normalise head sizes by photographed area (each frame's camera distance differs); the profile head is the reference
for n, h in HEADS.items():
    h.norm = math.sqrt(HEADS['profile'].area / h.area)
HEADS['profile'].norm *= 1.0


def muzzle_angle(head):
    L = head.L
    if L.get('nose'):
        d = np.array(L['nose']) - head.pivot
        return math.atan2(d[1], d[0])
    return None


# ------------------------------------------------------------------------------------------- body template
J = {k: np.array(v, float) for k, v in spec.JOINTS.items()}


def seg_place(canvas, part, a_t, b_t, A_c, B_c, shade=1.0, perp=K * 0.5 / 1.0):
    """leg/neck/tail strip whose anchors are given in template px; sprite anchors from parts.json"""
    an = P[part]['anchors']
    place(canvas, IMG[part], an['a'], an['b'], A_c, B_c, perp=perp, shade=shade)


def ik(root, target, l1, l2, bend):
    d = target - root; D = float(np.hypot(*d))
    D = min(max(D, abs(l1 - l2) + 1.0), l1 + l2 - 0.3)
    base = math.atan2(d[1], d[0])
    al = math.acos(max(-1, min(1, (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D))))
    cands = [root + l1 * np.array([math.cos(base + s * al), math.sin(base + s * al)]) for s in (1, -1)]
    knee = max(cands, key=lambda k: bend * k[0])
    foot = root + D * np.array([math.cos(base), math.sin(base)])
    return knee, foot


def lerp(a, b, t): return a + (b - a) * t


def draw(pose):
    """pose: dict (see perform.py). returns (RGBA canvas, info) ; canvas in screen px, body centre at CC, ground at GROUND_C."""
    cv = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    view = pose.get('view', 'rig')
    info = {}
    if view != 'rig':
        b = 'body_' + view
        im = IMG[b]; an = P[b]['anchors']
        h_s = an['foot_mid'][1] - an['top'][1]
        target_h = pose.get('sprite_h', 118) * K
        s = target_h / h_s
        foot = np.array([CC[0] + pose.get('sprite_dx', 0), GROUND_C + 2])
        place(cv, im, an['foot_mid'], np.array(an['foot_mid']) + [20, 0], foot, foot + [20 * s, 0])
        info['head_c'] = foot + np.array([-0.25 * target_h, -0.8 * target_h])
        return cv, info

    lie, crouch = pose['lie'], pose['crouch']
    bob = pose.get('bob', 0.0)
    dS = 41 * lie + 9 * crouch * (1 - lie) + bob
    dH = 43 * lie + 17 * crouch * (1 - lie) + bob
    S2, H2 = J['S'] + [0, dS], J['H'] + [0, dH]
    # torso similarity S->S2, H->H2 (template), then to canvas
    def tor(p):
        # rotate/translate p rigidly with the torso
        u = J['H'] - J['S']; U = H2 - S2
        a = math.atan2(U[1], U[0]) - math.atan2(u[1], u[0])
        c, s_ = math.cos(a), math.sin(a)
        q = np.asarray(p, float) - J['S']
        return S2 + np.array([c * q[0] - s_ * q[1], s_ * q[0] + c * q[1]])
    Sc, Hc = t2c(S2), t2c(H2)
    shade_far = 0.72
    legs = {}
    for ln, Lg in spec.LEGS.items():
        p0, p1, p2 = (np.array(v, float) for v in Lg['pts'])
        l1, l2 = np.hypot(*(p1 - p0)), np.hypot(*(p2 - p1))
        root = tor(p0)
        tgt = pose['feet'][ln]                     # template target for the paw (x, y)
        knee, foot = ik(root, np.array(tgt, float), l1, l2, Lg['bend'])
        legs[ln] = (root, knee, foot)
    # far legs, tail, torso, neck, near legs, head
    for ln in ('fore_far', 'hind_far'):
        r, k_, f = legs[ln]
        seg_place(cv, ln + '_0', None, None, t2c(r), t2c(k_), shade=shade_far, perp=K * 0.5)
        seg_place(cv, ln + '_1', None, None, t2c(k_), t2c(f), shade=shade_far, perp=K * 0.5)
    # tail
    Tr = tor(J['T'])
    ta = math.radians(pose['tail_ang'])
    tl = np.hypot(*(np.array(spec.TAIL['b']) - spec.TAIL['a']))
    seg_place(cv, 'tail', None, None, t2c(Tr), t2c(Tr + tl * np.array([math.cos(ta), math.sin(ta)])), perp=K * 0.5)
    an = P['torso']['anchors']
    place(cv, IMG['torso'], an['S'], an['H'], Sc, Hc)
    # neck + head
    Nn = tor(J['N'])
    nl = np.hypot(*(J['P'] - J['N'])) * pose.get('neck_len', 1.0)
    na = math.radians(pose['neck_ang'])
    Pp = Nn + nl * np.array([math.cos(na), math.sin(na)])
    seg_place(cv, 'neck', None, None, t2c(Nn), t2c(Pp), perp=K * 0.5)
    for ln in ('hind_near', 'fore_near'):
        r, k_, f = legs[ln]
        seg_place(cv, ln + '_0', None, None, t2c(r), t2c(k_), perp=K * 0.5)
        seg_place(cv, ln + '_1', None, None, t2c(k_), t2c(f), perp=K * 0.5)
    hv = pose['head_view']; H_ = HEADS[hv]
    himg = H_.compose(pose.get('ear', 0.6), pose.get('mouth', 0), pose.get('brow', 0))
    if pose.get('head_tone', 1.0) != 1.0:      # backlit: the head turned into the lit room darkens
        r_, g_, b_, a_ = himg.split(); k_ = pose['head_tone']
        himg = Image.merge('RGBA', [c.point(lambda q: int(q * k_)) for c in (r_, g_, b_)] + [a_])
    scale = 0.5 * K * H_.norm * pose.get('head_scale', 1.0)     # sprite px -> canvas px
    flip = pose.get('head_flip', False)
    at = t2c(Pp) + np.asarray(pose.get('head_off', (0, 0))) * K
    if hv in ('profile', 'low'):
        own = muzzle_angle(H_)
        want = math.radians(pose['muzzle_ang'])
        if flip:
            want = math.pi - want
            own = math.pi - own
        rot = want - own
        sx = pose.get('head_sx', 1.0)
        sa = H_.pivot; sb = sa + np.array([20.0, 0])
        da = at; db = da + 20 * scale * np.array([math.cos(rot), math.sin(rot)])
        if flip:
            himg = himg.transpose(Image.FLIP_LEFT_RIGHT)
            sa = np.array([himg.width - H_.pivot[0], H_.pivot[1]]); sb = sa + np.array([20.0, 0])
            # mirrored sprite: its muzzle angle is pi - own; rotation so that it lands on want
        place(cv, himg, sa, sb, da, db, perp=scale * sx if sx != 1.0 else None)
    else:
        tilt = math.radians(pose.get('head_tilt', 0))
        sa = H_.pivot
        if flip:
            himg = himg.transpose(Image.FLIP_LEFT_RIGHT); sa = np.array([himg.width - H_.pivot[0], H_.pivot[1]])
        hsx = pose.get('head_sx', 1.0)
        sb = np.asarray(sa, float) + np.array([20.0, 0])
        db = at + 20 * scale * hsx * np.array([math.cos(tilt), math.sin(tilt)])
        place(cv, himg, sa, sb, at, db, perp=scale)
    info.update({'head_c': t2c(Pp), 'S': Sc, 'H': Hc, 'feet': {k: t2c(v[2]) for k, v in legs.items()}})
    return cv, info
