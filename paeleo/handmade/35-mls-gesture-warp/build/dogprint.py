"""SCION 35 · the view prints of the dog.

The dog is a two-colour risograph print (orange coat plate, blue key/shade plate) on cream stock, cut out along its
silhouette. It exists as a small set of VIEW PRINTS (profile, three-quarter, rear, lying ...). Each print is drawn
here in code as flat layered shapes (capsule strokes, discs, ear wedges), painted with flat tones and a rim shade,
keyed with a solid outline, then screened into dots IN PRINT SPACE, so that every later warp bends the dot grid.

A 12-point stick guide (metres) is used only to place the shapes and the named anchors consistently across views
(so the same anchor names mean the same body point in every print). Nothing of the guide is ever shown.

Output: build/cache/prints/<name>.npz (per layer: alpha, blue ink, orange ink) + <name>.json (anchors, layers).
"""
import numpy as np, json, os, sys
from PIL import Image, ImageDraw, ImageFilter
from common import screen, CACHE, K_SRC, inks, DOGPAPER

PITCH = np.deg2rad(11.0)
SS = 2  # supersampling for drawing masks

# ---------------------------------------------------------------- the guide (dog local frame: x fwd, y up, z = dog's left)
STAND = dict(
    withers=(0.20, 0.56, 0), back=(0.0, 0.53, 0), croup=(-0.27, 0.54, 0), rump=(-0.39, 0.43, 0),
    chest=(0.33, 0.36, 0), belly=(0.0, 0.29, 0), throat=(0.37, 0.50, 0), poll=(0.41, 0.67, 0),
    tail0=(-0.37, 0.50, 0), tail1=(-0.48, 0.53, 0), tail2=(-0.58, 0.48, 0), tail3=(-0.64, 0.39, 0),
    fl_sh=(0.24, 0.41, 1), fl_el=(0.21, 0.25, 1), fl_wr=(0.23, 0.09, 1), fl_paw=(0.265, 0.018, 1),
    fr_sh=(0.24, 0.41, -1), fr_el=(0.21, 0.25, -1), fr_wr=(0.23, 0.09, -1), fr_paw=(0.265, 0.018, -1),
    hl_hip=(-0.26, 0.43, 1), hl_st=(-0.16, 0.26, 1), hl_hk=(-0.31, 0.11, 1), hl_paw=(-0.275, 0.018, 1),
    hr_hip=(-0.26, 0.43, -1), hr_st=(-0.16, 0.26, -1), hr_hk=(-0.31, 0.11, -1), hr_paw=(-0.275, 0.018, -1),
)
LIE = dict(
    withers=(0.20, 0.37, 0), back=(0.0, 0.32, 0), croup=(-0.27, 0.30, 0), rump=(-0.39, 0.19, 0),
    chest=(0.32, 0.15, 0), belly=(0.0, 0.10, 0), throat=(0.36, 0.33, 0), poll=(0.40, 0.49, 0),
    tail0=(-0.38, 0.25, 0), tail1=(-0.50, 0.15, 0), tail2=(-0.62, 0.07, 0), tail3=(-0.73, 0.035, 0),
    fl_sh=(0.24, 0.24, 1), fl_el=(0.20, 0.05, 1), fl_wr=(0.38, 0.035, 1), fl_paw=(0.47, 0.025, 1),
    fr_sh=(0.24, 0.24, -1), fr_el=(0.20, 0.05, -1), fr_wr=(0.38, 0.035, -1), fr_paw=(0.47, 0.025, -1),
    hl_hip=(-0.25, 0.25, 1), hl_st=(-0.07, 0.10, 1), hl_hk=(-0.36, 0.045, 1), hl_paw=(-0.17, 0.025, 1),
    hr_hip=(-0.25, 0.25, -1), hr_st=(-0.07, 0.10, -1), hr_hk=(-0.36, 0.045, -1), hr_paw=(-0.17, 0.025, -1),
)
LEGZ = {'fl': 0.09, 'fr': 0.09, 'hl': 0.11, 'hr': 0.11}
LIEZ = {'fl': 0.085, 'fr': 0.085, 'hl': 0.15, 'hr': 0.12}
# head local (relative to poll, head forward = +x)
HEAD = dict(skull=(0.045, 0.0, 0), nose=(0.215, -0.085, 0), jaw=(0.13, -0.08, 0),
            eye_l=(0.11, 0.0, 0.04), eye_r=(0.11, 0.0, -0.04),
            ear_lb=(0.0, 0.045, 0.045), ear_lt=(-0.025, 0.165, 0.075), ear_rb=(0.0, 0.045, -0.045), ear_rt=(-0.025, 0.165, -0.075))

TORSO_STAND = [((0.21, 0.43), 0.155), ((0.05, 0.42), 0.13), ((-0.12, 0.42), 0.125), ((-0.26, 0.44), 0.13)]
TORSO_LIE = [((0.21, 0.24), 0.15), ((0.05, 0.215), 0.135), ((-0.12, 0.205), 0.135), ((-0.25, 0.19), 0.15)]

LAYER_FAMILY = {'head': 'rigid', 'ear_l': 'rigid', 'ear_r': 'rigid', 'neck': 'similarity', 'torso': 'affine', 'tail': 'similarity',
                'leg_fl': 'similarity', 'leg_fr': 'similarity', 'leg_hl': 'similarity', 'leg_hr': 'similarity'}
LAYER_FALLOFF = {'head': 1.0, 'ear_l': 1.0, 'ear_r': 1.0, 'neck': 1.4, 'torso': 1.2, 'tail': 1.6,
                 'leg_fl': 1.8, 'leg_fr': 1.8, 'leg_hl': 1.8, 'leg_hr': 1.8}
LAYER_ANCHORS = {
    'head': ['skull', 'nose', 'jaw', 'eye_l', 'eye_r', 'poll', 'ear_lb', 'ear_rb'],
    'ear_l': ['ear_lb', 'ear_lt', 'skull'], 'ear_r': ['ear_rb', 'ear_rt', 'skull'],
    'neck': ['withers', 'chest', 'poll', 'skull'],
    'torso': ['withers', 'back', 'croup', 'rump', 'chest', 'belly', 'tail0'],
    'tail': ['rump', 'tail0', 'tail1', 'tail2', 'tail3'],
}
for L in ('fl', 'fr'):
    LAYER_ANCHORS['leg_' + L] = [L + '_sh', L + '_el', L + '_wr', L + '_paw', 'withers', 'chest']
for L in ('hl', 'hr'):
    LAYER_ANCHORS['leg_' + L] = [L + '_hip', L + '_st', L + '_hk', L + '_paw', 'croup', 'rump']


def guide(posture='stand', head_yaw=0.0, head_pitch=0.0, neck_pitch=0.0):
    """3D points of the guide in the dog frame. head_yaw/pitch in degrees, relative to the body."""
    lie = {'stand': 0.0, 'lie': 1.0}.get(posture, posture)
    P = {}
    for k in STAND:
        x0, y0, s = STAND[k]; x1, y1, _ = LIE[k]
        z = 0.0
        if s:
            z = s * (LEGZ[k[:2]] * (1 - lie) + LIEZ[k[:2]] * lie)
        P[k] = np.array([x0 * (1 - lie) + x1 * lie, y0 * (1 - lie) + y1 * lie, z])
    # neck follows a share of the head yaw (the poll swings round the withers)
    hy = np.deg2rad(head_yaw); hp = np.deg2rad(head_pitch)
    w = P['withers']
    rel = P['poll'] - w
    npt = np.deg2rad(neck_pitch)            # positive: the neck goes down (the poll swings forward-down round the withers)
    rot_p = lambda r, a: np.array([r[0] * np.cos(a) + r[1] * np.sin(a), -r[0] * np.sin(a) + r[1] * np.cos(a), r[2]])
    rel = rot_p(rel, npt)
    P['throat'] = w + rot_p(P['throat'] - w, npt * 0.5)
    hp = hp - npt
    ny = hy * 0.45
    rel = np.array([rel[0] * np.cos(ny) - rel[2] * np.sin(ny), rel[1], rel[0] * np.sin(ny) + rel[2] * np.cos(ny)])
    P['poll'] = w + rel
    for k, (x, y, z) in HEAD.items():
        v = np.array([x, y, z])
        # pitch (about z), then yaw (about y)
        v = np.array([v[0] * np.cos(hp) - v[1] * np.sin(hp), v[0] * np.sin(hp) + v[1] * np.cos(hp), v[2]])
        v = np.array([v[0] * np.cos(hy) - v[2] * np.sin(hy), v[1], v[0] * np.sin(hy) + v[2] * np.cos(hy)])
        P[k] = P['poll'] + v
    return P


def project(P, psi_deg):
    """dog frame -> print px (x right, y down) + depth (toward camera). psi: body yaw, 180 = facing screen-left."""
    ps = np.deg2rad(psi_deg)
    out = {}
    for k, v in P.items():
        X = v[0] * np.cos(ps) - v[2] * np.sin(ps)
        Z = v[0] * np.sin(ps) + v[2] * np.cos(ps)
        sx = K_SRC * X
        sy = -K_SRC * (v[1] * np.cos(PITCH)) + K_SRC * Z * np.sin(PITCH)
        out[k] = (sx, sy, Z)
    return out


def proj_pt(v, psi_deg):
    return project({'_': np.asarray(v, float)}, psi_deg)['_']


# ---------------------------------------------------------------- drawing
class Canvas:
    def __init__(self, w, h, ox, oy):
        self.w, self.h, self.ox, self.oy = w, h, ox, oy

    def new(self):
        im = Image.new('L', (self.w * SS, self.h * SS), 0)
        return im, ImageDraw.Draw(im)

    def P(self, xy):
        return ((xy[0] + self.ox) * SS, (xy[1] + self.oy) * SS)


def stamp_capsule(dr, cv, pts, radii, fill=255, step=1.5):
    for i in range(len(pts) - 1):
        a = np.array(pts[i][:2]); b = np.array(pts[i + 1][:2])
        n = max(2, int(np.linalg.norm(b - a) / step) + 1)
        for t in np.linspace(0, 1, n):
            c = a + (b - a) * t
            r = (radii[i] + (radii[i + 1] - radii[i]) * t) * SS
            x, y = cv.P(c)
            dr.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def to_arr(im):
    return np.asarray(im.resize((im.width // SS, im.height // SS), Image.LANCZOS), np.float32) / 255


def blur(a, r):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


def erode(a, px):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MinFilter(px)), np.float32) / 255


def shade(mask, far=0.0, base_o=0.55, under=None):
    """flat riso painting of one layer: orange coat + blue rim/shade + solid key line."""
    b = blur(mask, 9)
    gy, gx = np.gradient(b)
    n = np.sqrt(gx * gx + gy * gy) + 1e-6
    lit = (-gx * -0.55 + -gy * -0.83) / n          # normal (pointing out = -grad) . light (up-left)
    rim = np.clip((0.88 - b) / 0.38, 0, 1)
    blue = 0.1 + 0.42 * rim * (0.55 - 0.45 * lit) + far
    org = np.full_like(mask, base_o)
    org = org - 0.18 * rim * np.clip(lit, 0, 1)    # lit edges lighter
    if under is not None:
        blue = blue + 0.22 * under
        org = org - 0.2 * under
    key = np.clip((mask - erode(mask, 7)) * 1.6, 0, 1)
    blue = np.maximum(blue, key)
    return np.clip(blue, 0, 1), np.clip(org, 0, 1)


def make_print(name, psi, posture='stand', head_yaw=0.0, head_pitch=0.0, note=''):
    P = guide(posture, head_yaw, head_pitch)
    pr = project(P, psi)
    torso_spec = TORSO_STAND if posture == 'stand' else TORSO_LIE
    tz = lambda xy: np.array([xy[0], xy[1], 0.0])
    # extents
    xs = [v[0] for v in pr.values()]; ys = [v[1] for v in pr.values()]
    m = 0.2 * K_SRC
    x0, x1, y0, y1 = min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m
    cv = Canvas(int(x1 - x0), int(y1 - y0), -x0, -y0)
    layers = {}
    depth = {}

    def Q(k):
        return pr[k]

    # torso
    im, dr = cv.new()
    tp = [proj_pt(tz(c), psi) for c, r in torso_spec]
    stamp_capsule(dr, cv, tp, [r * K_SRC for c, r in torso_spec])
    # croup/withers top line bumps
    for kk, rr in (('withers', 0.07), ('croup', 0.075)):
        c = proj_pt(P[kk] - np.array([0, 0.06, 0]), psi)
        stamp_capsule(dr, cv, [c, c], [rr * K_SRC, rr * K_SRC])
    layers['torso'] = to_arr(im); depth['torso'] = 0.0
    # neck
    im, dr = cv.new()
    nb = P['withers'] * 0.5 + P['chest'] * 0.5 + np.array([-0.02, 0.0, 0])
    stamp_capsule(dr, cv, [proj_pt(nb, psi), proj_pt(P['poll'] * 0.6 + nb * 0.4, psi), proj_pt(P['poll'] + (P['skull'] - P['poll']) * 0.3, psi)],
                  [0.105 * K_SRC, 0.08 * K_SRC, 0.066 * K_SRC])
    layers['neck'] = to_arr(im); depth['neck'] = float(proj_pt(P['poll'] * 0.5 + nb * 0.5, psi)[2])
    # head: skull + muzzle (+ cheek)
    im, dr = cv.new()
    stamp_capsule(dr, cv, [Q('skull'), Q('skull')], [0.078 * K_SRC] * 2)
    mz0 = P['skull'] + (P['nose'] - P['skull']) * 0.35 + (P['jaw'] - P['nose']) * 0.15
    stamp_capsule(dr, cv, [proj_pt(mz0, psi), proj_pt(P['nose'] + (P['skull'] - P['nose']) * 0.06, psi)], [0.056 * K_SRC, 0.033 * K_SRC])
    layers['head'] = to_arr(im); depth['head'] = float(Q('skull')[2]) + 0.02
    # ears (wedges)
    for side in ('l', 'r'):
        im, dr = cv.new()
        b = P['ear_%sb' % side]; t = P['ear_%st' % side]
        fwd = (P['nose'] - P['skull']); fwd = fwd / np.linalg.norm(fwd)
        b1 = proj_pt(b + fwd * 0.035, psi); b2 = proj_pt(b - fwd * 0.03, psi); tt = proj_pt(t, psi)
        dr.polygon([cv.P(b1), cv.P(tt), cv.P(b2)], fill=255)
        stamp_capsule(dr, cv, [((b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2), tt], [0.022 * K_SRC, 0.008 * K_SRC])
        layers['ear_' + side] = to_arr(im)
        depth['ear_' + side] = float(tt[2]) + (0.01 if np.sign(tt[2] - Q('skull')[2]) > 0 else -0.03)
    # legs
    for L in ('fl', 'fr', 'hl', 'hr'):
        im, dr = cv.new()
        if L[0] == 'f':
            ks = [L + '_sh', L + '_el', L + '_wr', L + '_paw']
            rr = [0.068, 0.045, 0.031, 0.034]
        else:
            ks = [L + '_hip', L + '_st', L + '_hk', L + '_paw']
            rr = [0.09, 0.06, 0.03, 0.034]
        pts = [Q(k) for k in ks]
        stamp_capsule(dr, cv, pts, [r * K_SRC for r in rr])
        # toes: a short pad forward of the paw
        toe = P[ks[-1]] + np.array([0.045, 0, 0])
        stamp_capsule(dr, cv, [Q(ks[-1]), proj_pt(toe, psi)], [0.034 * K_SRC, 0.027 * K_SRC])
        layers['leg_' + L] = to_arr(im)
        depth['leg_' + L] = float(np.mean([p[2] for p in pts]))
    # tail
    im, dr = cv.new()
    stamp_capsule(dr, cv, [Q('tail0'), Q('tail1'), Q('tail2'), Q('tail3')], [0.036 * K_SRC, 0.03 * K_SRC, 0.022 * K_SRC, 0.012 * K_SRC])
    layers['tail'] = to_arr(im); depth['tail'] = float(np.mean([Q(k)[2] for k in ('tail1', 'tail2', 'tail3')])) + 0.03

    order = sorted(layers, key=lambda k: depth[k])
    # ---- painting
    h, w = cv.h, cv.w
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = {}
    near_side_z = max(Q('fl_sh')[2], Q('fr_sh')[2])
    for k in order:
        a = layers[k]
        far = 0.0
        if k.startswith('leg_') or k.startswith('ear_'):
            pz = depth[k]
            others = [depth[j] for j in layers if j[:4] == k[:4] and j != k]
            if others and pz < max(others) - 0.02:
                far = 0.22
        base_o = {'torso': 0.54, 'neck': 0.52, 'head': 0.52, 'tail': 0.56, 'ear_l': 0.72, 'ear_r': 0.72}.get(k, 0.5)
        # underside: lower part of the torso / neck lighter coat + bluer shade
        under = None
        if k in ('torso', 'neck'):
            cy = (Q('back')[1] + Q('belly')[1]) / 2 + cv.oy
            under = np.clip((yy - cy) / (0.12 * K_SRC), 0, 1) * a
        bl, og = shade(a, far, base_o, under)
        if k == 'torso':
            # saddle: a darker blanket over the back (a marking, it also shows how the coat plate is strained)
            c = np.array(Q('back')[:2]) + (cv.ox, cv.oy)
            cr = np.array(Q('croup')[:2]) + (cv.ox, cv.oy)
            sad = np.zeros_like(a)
            for t in np.linspace(0, 1, 9):
                p = c * (1 - t) + cr * t + np.array([0, 0.035 * K_SRC])
                sad = np.maximum(sad, np.clip(1 - ((xx - p[0]) ** 2 + (yy - p[1]) ** 2) / (0.1 * K_SRC) ** 2, 0, 1))
            bl = np.clip(bl + 0.45 * np.clip(sad * 1.6, 0, 1) * a, 0, 1)
        if k.startswith('leg_'):
            # socks: lighter lower legs
            pk = [n for n in LAYER_ANCHORS[k] if n.endswith('_wr') or n.endswith('_hk')][0]
            ylow = Q(pk)[1] + cv.oy
            sock = np.clip((yy - ylow) / (0.05 * K_SRC), 0, 1)
            og = og * (1 - 0.55 * sock)
        if k == 'head':
            # muzzle lighter, nose and eyes solid key
            nz = np.array(Q('nose')[:2]) + (cv.ox, cv.oy)
            sk = np.array(Q('skull')[:2]) + (cv.ox, cv.oy)
            dm = np.sqrt((xx - nz[0]) ** 2 + (yy - nz[1]) ** 2)
            og = og - 0.22 * np.clip(1 - dm / (0.1 * K_SRC), 0, 1)
            fwd3 = P['nose'] - P['skull']
            view_toward = proj_pt(P['skull'] + fwd3, psi)[2] - Q('skull')[2]
            if view_toward > -0.17:  # nose visible unless the head points straight away
                r = 0.024 * K_SRC
                bl = np.maximum(bl, np.clip((r - dm) / 2 + .5, 0, 1))
            for e in ('eye_l', 'eye_r'):
                side = 1 if e == 'eye_l' else -1
                # eye visible when its side faces the camera
                outward = P[e] + np.array([0, 0, 0.05 * side]) * 0
                n3 = P[e] - P['skull']; n3 = n3 / np.linalg.norm(n3)
                nz3 = proj_pt(P['skull'] + n3, psi)[2] - Q('skull')[2]
                if nz3 > -0.2:
                    ep = np.array(Q(e)[:2]) + (cv.ox, cv.oy)
                    de = np.sqrt((xx - ep[0]) ** 2 + (yy - ep[1]) ** 2)
                    r = 0.0145 * K_SRC
                    bl = np.maximum(bl, np.clip((r - de) / 1.5 + .5, 0, 1))
                    hl = np.clip((0.0045 * K_SRC - np.sqrt((xx - ep[0] + 2.5) ** 2 + (yy - ep[1] + 2.5) ** 2)) / 1.2 + .5, 0, 1)
                    bl = bl * (1 - hl); og = og * (1 - hl)
            # mouth line in profile-ish views
            if abs(np.sin(np.deg2rad(psi + head_yaw))) < 0.75:
                j = np.array(Q('jaw')[:2]) + (cv.ox, cv.oy)
                for t in np.linspace(0, 1, 30):
                    p = j * (1 - t) + nz * t + np.array([0, 0.012 * K_SRC]) * (t * (1 - t))
                    d = np.sqrt((xx - p[0]) ** 2 + (yy - p[1]) ** 2)
                    bl = np.maximum(bl, np.clip((2.2 - d) / 1.2, 0, 1) * 0.9)
            bl = bl * a + 0 * a
        if k.startswith('ear_'):
            og = np.clip(og + 0.1, 0, 1)
        out[k] = (a, bl * (a > 0.01), og * (a > 0.01))
    # screen the plates in print space (orange 75 deg, blue 15 deg, cell 14 print px = 7 film px), riso misregistration
    res = {}
    for k in order:
        a, bl, og = out[k]
        ib = screen(bl, 18.0, 15.0)
        io = screen(og, 18.0, 75.0, ox=3.0, oy=-2.0)
        res[k] = (a, ib, io, bl, og)
    root = proj_pt(np.array([0.0, 0.0, 0.0]), psi)
    anchors = {k: [float(v[0] + cv.ox), float(v[1] + cv.oy)] for k, v in pr.items()}
    meta = dict(name=name, psi=psi, posture=posture, head_yaw=head_yaw, head_pitch=head_pitch, note=note,
                size=[w, h], root=[float(root[0] + cv.ox), float(root[1] + cv.oy)], anchors=anchors,
                anchor_depth={k: float(v[2]) for k, v in pr.items()},
                order=order, family={k: LAYER_FAMILY[k] for k in order}, falloff={k: LAYER_FALLOFF[k] for k in order},
                layer_anchors={k: LAYER_ANCHORS[k] for k in order})
    return meta, res


PRINTS = [
    # name, body yaw (180 = facing the door, screen-left), posture, head yaw rel. body, head pitch, note
    ('P_prof', 180, 'stand', 0, 0, 'profile, facing the door'),
    ('R0_t', 202.5, 'stand', 0, 0, 'turning away, a quarter of the way'),
    ('R1_r34', 225, 'stand', 0, 0, 'rear three-quarter, turning away'),
    ('R1b_t', 247.5, 'stand', 0, 0, 'turning away, almost rear'),
    ('R2_rear', 270, 'stand', 0, 0, 'rear view: back to the viewer'),
    ('R2b_t', 292.5, 'stand', 0, 0, 'rear, coming round to the far profile'),
    ('R3_r34', 315, 'stand', 0, 0, 'rear three-quarter, other side'),
    ('R3b_t', 337.5, 'stand', 0, -4, 'almost in profile, back to the door'),
    ('P_right', 360, 'stand', 0, -8, 'profile, back turned to the door'),
    ('L_right', 360, 'lie', 0, -5, 'lying, back to the door'),
    ('LB_look', 360, 'lie', -160, 6, 'lying, back to the door, head turned over the shoulder to the door'),
    ('SB_look', 360, 'stand', -150, 4, 'getting up, body still away, head on the door'),
    ('RT3', 315, 'stand', -118, 2, 'rear three-quarter, head held on the door'),
    ('RT2', 270, 'stand', -82, 0, 'rear view, head in profile toward the door'),
    ('RT1', 225, 'stand', -40, 0, 'rear three-quarter, almost round'),
    ('L_prof', 180, 'lie', 0, 0, 'lying across the sill, head up'),
    ('L_in', 180, 'lie', 84, 0, 'lying, head turned in through the door: back of the head to the viewer'),
]


def contact_sheet(metas, results, path):
    from common import PAPER
    tiles = []
    for meta, res in zip(metas, results):
        w, h = meta['size']
        acc = np.ones((h, w, 3), np.float32) * PAPER * 0.85
        for k in meta['order']:
            a, ib, io, _, _ = res[k]
            col = inks(DOGPAPER, ib, io)
            acc = acc * (1 - a[..., None]) + col * a[..., None]
        im = Image.fromarray((acc * 255).astype(np.uint8))
        im.thumbnail((360, 280))
        tile = Image.new('RGB', (380, 310), (230, 224, 210))
        tile.paste(im, ((380 - im.width) // 2, 5))
        ImageDraw.Draw(tile).text((8, 292), meta['name'] + ' · ' + meta['note'][:44], fill=(30, 40, 90))
        tiles.append(tile)
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (380 * cols, 310 * rows), (230, 224, 210))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 380, (i // cols) * 310))
    sheet.save(path, quality=88)


if __name__ == '__main__':
    os.makedirs(os.path.join(CACHE, 'prints'), exist_ok=True)
    metas, results = [], []
    only = sys.argv[1:]
    for spec in PRINTS:
        if only and spec[0] not in only:
            continue
        meta, res = make_print(*spec)
        np.savez_compressed(os.path.join(CACHE, 'prints', meta['name'] + '.npz'),
                            **{k + '__' + n: v.astype(np.float16) for k, vals in res.items() for n, v in zip(('a', 'ib', 'io', 'tb', 'to'), vals)})
        json.dump(meta, open(os.path.join(CACHE, 'prints', meta['name'] + '.json'), 'w'), indent=0)
        metas.append(meta); results.append(res)
        print(meta['name'], meta['size'], meta['order'])
    from common import ROOT
    contact_sheet(metas, results, os.path.join(ROOT, 'proof', 'view_prints.jpg'))
