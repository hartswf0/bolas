"""SCION 40 · puppet fabricator. Cuts every paper piece twice from one shape definition:
  plate/  the working puppets that lie on the table in the capture: white card, marker-pen line, a fiducial tab.
  skin/   the finished puppets the capture is replayed with: coloured, grained, scissor-cut paper, no tab.
The dog's cards are flat drawings. A small geometric guide (ellipsoids and limbs, posed per card) is used only to
draw each card's silhouette consistently across views; once cut, a card never deforms: it is moved rigidly by the
hand (the recovered transform) and replaced by another card (substitution). Writes cache/cards/{plate,skin}/*.png
and data/cards.json (anchors, tab, neck, measurement points)."""
import json, math, os, sys, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

SS = 3                       # supersampling for cutting
M = PX_PER_M                 # px per metre at card scale

SKIN = {
    'body': (198, 138, 70), 'body_far': (150, 100, 52), 'saddle': (84, 54, 36), 'belly': (230, 210, 172),
    'ear': (74, 46, 32), 'ear_far': (60, 38, 26), 'nose': (24, 20, 18), 'eye': (22, 18, 16), 'muzzle': (232, 214, 178),
    'tail': (186, 128, 64), 'tailtip': (236, 222, 190), 'paw': (232, 214, 178), 'paw_far': (186, 164, 130),
    'skull': (198, 138, 70), 'head_far': (160, 108, 56),
}
LINE = (70, 42, 26)


# ---------------------------------------------------------------- the geometric guide (used only to draw)
def ell_pts(c, r, n=14):
    u = np.linspace(0, np.pi, n)
    v = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False)
    uu, vv = np.meshgrid(u, v)
    p = np.stack([np.sin(uu) * np.cos(vv), np.cos(uu), np.sin(uu) * np.sin(vv)], -1).reshape(-1, 3)
    return np.asarray(c) + p * np.asarray(r)


def cap_pts(a, b, ra, rb=None, n=8):
    rb = ra if rb is None else rb
    out = []
    for t in np.linspace(0, 1, 6):
        out.append(ell_pts(np.asarray(a) * (1 - t) + np.asarray(b) * t, [ra * (1 - t) + rb * t] * 3, n))
    return np.concatenate(out)


def ik2(hip, foot, L1, L2, bend):
    """2-link in the sagittal plane (a, h). bend=+1 joint forward, -1 backward."""
    hip, foot = np.asarray(hip, float), np.asarray(foot, float)
    d = foot - hip
    L = min(np.hypot(*d), L1 + L2 - 1e-4)
    a = (L1 * L1 - L2 * L2 + L * L) / (2 * L)
    h = math.sqrt(max(L1 * L1 - a * a, 0))
    e = d / max(np.hypot(*d), 1e-6)
    perp = np.array([e[1], -e[0]]) * (1 if bend > 0 else -1)
    if perp[0] * bend < 0:
        perp = -perp
    j = hip + e * a + perp * h
    return j


def dog_parts(pose):
    """3D parts in dog-local metres: a forward, h up, s toward the dog's right side.
    pose: dict(kind=stand|walk|crouch|settle|lie, phase, crouch, tail)"""
    kind = pose.get('kind', 'stand')
    cr = pose.get('crouch', 0.0)
    tail = pose.get('tail', 0.5)
    parts = []
    if kind in ('stand', 'walk'):
        ch, hh = 0.42 - 0.10 * cr, 0.42 - 0.12 * cr
    elif kind == 'settle':          # hips down, front up: going down / rising
        ch, hh = 0.33, 0.20
    else:                           # lie
        ch, hh = 0.17, 0.15
    pitch_drop = hh - ch
    parts.append(('belly', 'body', ell_pts((0.0, (ch + hh) / 2 - 0.01, 0), (0.27, 0.13, 0.14)), 0))
    parts.append(('chest', 'body', ell_pts((0.2, ch, 0), (0.19, 0.165, 0.16)), 0))
    parts.append(('hip', 'body', ell_pts((-0.21, hh + 0.01, 0), (0.18, 0.15, 0.155)), 0))
    parts.append(('saddle', 'saddle', ell_pts((-0.02, (ch + hh) / 2 + 0.085, 0), (0.25, 0.075, 0.15)), 0.001))
    neck_a = (0.27, ch + 0.06, 0)
    if kind == 'lie':
        neck_b = (0.34, ch + 0.16, 0)
    elif kind == 'settle':
        neck_b = (0.36, ch + 0.20, 0)
    else:
        low = pose.get('low', 0.0)
        neck_b = (0.37 + 0.05 * low, ch + 0.20 - 0.04 * cr - 0.17 * low, 0)
    parts.append(('neck', 'body', cap_pts(neck_a, neck_b, 0.085, 0.07), 0.0005))
    # tail: base on the rump, a chain bending down as it tucks
    base = np.array([-0.37, hh + 0.08, 0.0])
    ang0 = math.radians(40 - 75 * tail)          # high 40 deg up, tucked ~ -60
    if kind == 'lie':
        ang0 = math.radians(-35)
    pts, p, ang = [], base, ang0
    for k in range(5):
        q = p + 0.065 * np.array([-math.cos(ang), math.sin(ang), 0])
        pts.append((p, q))
        p = q
        ang -= math.radians(18 if kind != 'lie' else 6)
    for k, (a, b) in enumerate(pts):
        parts.append(('tail%d' % k, 'tail' if k < 4 else 'tailtip', cap_pts(a, b, 0.032 - 0.004 * k), -0.002))
    # legs
    legs = {'LF': (0.21, -1), 'RF': (0.21, 1), 'LH': (-0.22, -1), 'RH': (-0.22, 1)}
    S = 0.5
    ph = pose.get('phase', 0.0)
    offs = {'LF': 0.0, 'RH': 0.0, 'RF': 0.5, 'LH': 0.5}
    for name, (la, side) in legs.items():
        sz = 0.1 * side
        front = name.endswith('F')
        if kind in ('stand', 'walk', 'crouch'):
            hip = (la + (0.03 if front else -0.01), (ch if front else hh) - 0.05)
            fa, lift = la + (0.02 if front else -0.03), 0.0
            if kind == 'walk':
                u = (ph + offs[name]) % 1.0
                if u < 0.5:
                    fa += S / 4 - u * S
                else:
                    w = (u - 0.5) / 0.5
                    fa += -S / 4 + w * S / 2
                    lift = 0.07 * math.sin(math.pi * w)
            foot = (fa, 0.035 + lift)
            if front:
                j = ik2(hip, foot, 0.17, 0.185 - 0.05 * cr, -1)
                segs = [(hip, j, 0.06, 0.04), (j, foot, 0.04, 0.033)]
            else:
                j = ik2(hip, foot, 0.25 - 0.06 * cr, 0.15, -1)
                segs = [(hip, j, 0.08, 0.042), (j, foot, 0.04, 0.033)]
        elif kind == 'settle':
            if front:
                hip = (la + 0.03, ch - 0.05)
                foot = (la + 0.05, 0.035)
                j = ik2(hip, foot, 0.16, 0.18, -1)
                segs = [(hip, j, 0.06, 0.04), (j, foot, 0.04, 0.033)]
            else:
                hip = (la, hh)
                knee = (la + 0.14, hh - 0.02)
                foot = (la + 0.02, 0.03)
                segs = [(hip, knee, 0.1, 0.06), (knee, foot, 0.045, 0.033)]
        else:  # lie: forelegs along the ground, hind folded with the paw forward
            if front:
                elbow = (la - 0.02, 0.06)
                foot = (la + 0.27 + (0.03 if side > 0 else 0), 0.035)
                segs = [((la, ch - 0.02), elbow, 0.06, 0.045), (elbow, foot, 0.042, 0.034)]
            else:
                knee = (la + 0.12, 0.09)
                foot = (la + 0.18, 0.03)
                segs = [((la, hh), knee, 0.115, 0.07), ((la - 0.12, 0.05), foot, 0.04, 0.032)]
        role = 'body'
        for k, (a, b, ra, rb) in enumerate(segs):
            parts.append(('%s%d' % (name, k), role, cap_pts((a[0], a[1], sz), (b[0], b[1], sz), ra, rb), 0.0))
        parts.append(('%spaw' % name, 'paw', ell_pts((foot[0] + 0.03, foot[1] - 0.005, sz), (0.05, 0.03, 0.035)), 0.0))
    neck_top = np.array(neck_b)
    return parts, neck_top


def head_parts(ears=1.0, mouth=0.0):
    """head in head-local metres; origin = the pivot at the top of the neck. a forward (muzzle), h up, s right."""
    P = []
    P.append(('skull', 'skull', ell_pts((0.07, 0.05, 0), (0.095, 0.088, 0.085)), 0))
    P.append(('cheek', 'skull', ell_pts((0.11, 0.02, 0), (0.07, 0.06, 0.07)), 0))
    P.append(('muzzle', 'muzzle', cap_pts((0.13, 0.015, 0), (0.24, -0.005, 0), 0.05, 0.036), 0.0))
    P.append(('nose', 'nose', ell_pts((0.262, 0.005, 0), (0.024, 0.022, 0.026)), 0.0))
    P.append(('jaw', 'muzzle', cap_pts((0.12, -0.03, 0), (0.21, -0.035 - 0.03 * mouth, 0), 0.032, 0.022), 0.0))
    for side in (-1, 1):
        s = 0.052 * side
        P.append(('eye%d' % side, 'eye', ell_pts((0.155, 0.065, s * 1.02), (0.015, 0.015, 0.012)), 0))
        # ear: a thin flap; ears=1 pricked up, 0 flat back
        base = np.array([0.03, 0.12, 0.045 * side])
        tip = base + np.array([-0.025 - 0.11 * (1 - ears), 0.085 * ears + 0.025, 0.03 * side])
        w = np.array([0.045, 0, 0.05 * side])
        tri = []
        for t in np.linspace(0, 1, 7):
            for q in np.linspace(-1, 1, 5):
                tri.append(base * (1 - t) + tip * t + w * q * (1 - t) + np.array([0, 0, 0.006]) * q)
        P.append(('ear%d' % side, 'ear', np.array(tri), 0.0))
    return P


def project(parts, yaw_deg, origin_px, scale=M):
    """orthographic camera; yaw 0 = facing left, 90 = facing away (rear to camera), 180 = right, 270 = toward camera."""
    ps = math.radians(yaw_deg)
    f = np.array([-math.cos(ps), 0, math.sin(ps)])
    up = np.array([0, 1, 0])
    r = np.array([-math.sin(ps), 0, -math.cos(ps)])
    out = []
    for name, role, pts, bias in parts:
        wpts = pts[:, :1] * f + pts[:, 1:2] * up + pts[:, 2:3] * r
        xy = np.stack([origin_px[0] + wpts[:, 0] * scale, origin_px[1] - wpts[:, 1] * scale], 1)
        depth = wpts[:, 2].mean() - bias
        out.append((name, role, hull(xy), depth, wpts[:, 2].mean()))
    out.sort(key=lambda o: -o[3])
    return out


def proj_pt(p, yaw_deg, origin_px, scale=M):
    ps = math.radians(yaw_deg)
    f = np.array([-math.cos(ps), 0, math.sin(ps)]); r = np.array([-math.sin(ps), 0, -math.cos(ps)])
    w = p[0] * f + np.array([0, p[1], 0]) + p[2] * r
    return (origin_px[0] + w[0] * scale, origin_px[1] - w[1] * scale), w[2]


# ---------------------------------------------------------------- cutting paper
def cut(size, polys, style, seed, tab=None, grain_seed=0):
    """polys: list of (role, polygon px, far:boolean). style 'skin' or 'plate'. returns RGBA PIL image."""
    w, h = size
    big = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    torso = [p for p in polys if len(p) > 3 and p[3] == 'torso']
    torso_done = False
    for k, item in enumerate(polys):
        role, poly, far = item[:3]
        grp = item[3] if len(item) > 3 else None
        if len(poly) < 3:
            continue
        if grp == 'torso':
            if torso_done:
                continue
            torso_done = True
            # one sheet: all torso shapes cut as a single silhouette, outlined only on its outer edge
            m = Image.new('L', big.size, 0)
            dm = ImageDraw.Draw(m)
            for j, t in enumerate(torso):
                dm.polygon([tuple(p) for p in jitter_poly(t[1], 0.7, seed * 131 + 900 + j, step=4.0) * SS], fill=255)
            if style == 'skin':
                col, lc, lw = SKIN['body'], LINE, 1.3
            else:
                col, lc, lw = (238, 236, 228), (28, 28, 30), 1.8
            edge = m.filter(ImageFilter.MaxFilter(2 * int(lw * SS / 2) + 1))
            big.paste(Image.new('RGBA', big.size, lc + (255,)), (0, 0), edge)
            big.paste(Image.new('RGBA', big.size, col + (255,)), (0, 0), m.filter(ImageFilter.MinFilter(int(lw * SS) | 1)))
            continue
        jp = jitter_poly(poly, 0.7, seed * 131 + k, step=4.0) * SS
        pts = [tuple(p) for p in jp]
        if style == 'skin':
            col = SKIN.get(role + '_far' if far and role + '_far' in SKIN else role, SKIN['body'])
            if far and role + '_far' not in SKIN:
                col = tuple(int(c * .78) for c in col)
            d.polygon(pts, fill=col + (255,))
            d.line(pts + [pts[0]], fill=LINE + (255,), width=int(1.3 * SS))
        else:
            fills = {'saddle': (196, 196, 190), 'nose': (40, 40, 40), 'eye': (30, 30, 30), 'ear': (205, 205, 200)}
            col = fills.get(role, (238, 236, 228))
            if far:
                col = tuple(int(c * .88) for c in col)
            d.polygon(pts, fill=col + (255,))
            d.line(pts + [pts[0]], fill=(28, 28, 30, 255), width=int(1.8 * SS))
    if tab is not None:
        draw_tab(d, tab, style)
    im = big.resize((w, h), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    g = grain(h, w, 11 + grain_seed)
    amt = 0.07 if style == 'skin' else 0.035
    a[..., :3] *= (1 + amt * g)[..., None]
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    if tab is not None and style == 'plate':
        out = paste_marker(out, tab)
    return out


def draw_tab(d, tab, style):
    if style != 'plate':
        return
    (mx, my), (bx, by), ident = tab['marker'], tab['base'], tab['id']
    s = SS
    half = MARK / 2 + 4
    d.rectangle([(mx - half) * s, (my - half) * s, (mx + half) * s, (my + half) * s], fill=(244, 243, 236, 255), outline=(60, 60, 60, 255), width=s)
    # the bridge: a strip of card from the marker down to the drawing
    x0 = min(mx, bx) - 5; x1 = max(mx, bx) + 5
    d.polygon([((mx - 6) * s, (my + half - 1) * s), ((mx + 6) * s, (my + half - 1) * s), ((bx + 6) * s, by * s), ((bx - 6) * s, by * s)], fill=(244, 243, 236, 255), outline=(60, 60, 60, 255))


def paste_marker(img, tab):
    mx, my = tab['marker']
    fi = fid_image(tab['id'])
    a = np.asarray(img).copy()
    y0, x0 = int(round(my - MARK / 2)), int(round(mx - MARK / 2))
    a[y0:y0 + MARK, x0:x0 + MARK, :3] = fi[..., None]
    a[y0:y0 + MARK, x0:x0 + MARK, 3] = 255
    return Image.fromarray(a, 'RGBA')


# ---------------------------------------------------------------- the card list
def dog_body_specs():
    S = []
    for k in range(8):
        S.append(('b_walk_%d' % k, 0, dict(kind='walk', phase=k / 8, crouch=0.08, tail=0.3, low=1.0)))
    for k in range(8):
        S.append(('b_step_%d' % k, 0, dict(kind='walk', phase=k / 8, crouch=0.15, tail=0.6)))
    for k in range(8):
        S.append(('b_back_%d' % k, 0, dict(kind='walk', phase=k / 8, crouch=0.85, tail=1.3)))
    S += [
        ('b_stand_L', 0, dict(kind='stand', crouch=0.1, tail=0.5)),
        ('b_crouch_L', 0, dict(kind='stand', crouch=0.85, tail=1.3)),
        ('b_turn45', 45, dict(kind='stand', crouch=0.35, tail=0.9)),
        ('b_turn90', 90, dict(kind='stand', crouch=0.45, tail=1.1)),
        ('b_turn135', 135, dict(kind='stand', crouch=0.5, tail=1.15)),
        ('b_stand_R', 180, dict(kind='stand', crouch=0.5, tail=1.15)),
        ('b_settle_R', 180, dict(kind='settle', tail=1.15)),
        ('b_lie_R', 180, dict(kind='lie', tail=1.15)),
        ('b_turn225', 225, dict(kind='stand', crouch=0.2, tail=0.6)),
        ('b_turn270', 270, dict(kind='stand', crouch=0.15, tail=0.5)),
        ('b_turn315', 315, dict(kind='stand', crouch=0.1, tail=0.5)),
        ('b_settle_L', 0, dict(kind='settle', tail=0.3)),
        ('b_lie_L', 0, dict(kind='lie', tail=0.3)),
    ]
    return S


HEADS = [  # name, yaw, ears, mouth
    ('h_L', 0, 1.0, 0), ('h_L_low', 0, 0.35, 0), ('h_L_flat', 0, 0.05, 0),
    ('h_45', 45, 0.6, 0), ('h_90', 90, 0.5, 0), ('h_135', 135, 0.2, 0), ('h_R', 180, 0.1, 0),
    ('h_225', 225, 0.8, 0), ('h_270', 270, 0.9, 0), ('h_315', 315, 1.0, 0),
    ('h_in', 40, 1.0, 0),          # looking in: back of the head toward us, muzzle going into the room
]

BODY_SIZE, BODY_ANCHOR = (380, 340), (190, 300)
HEAD_SIZE, HEAD_ANCHOR = (170, 170), (85, 100)
BODY_TAB = (190, 92)          # marker centre, same for every body card so a swap keeps the tab in place
HEAD_TAB = (85, 22)
HS = 1.22                     # head cards are cut a little large: they carry the acting


def build_dog(style, ids, meta, outdir):
    for name, yaw, pose in dog_body_specs():
        parts, neck = dog_parts(pose)
        pr = project(parts, yaw, BODY_ANCHOR)
        cen = np.array([0, 0, 0.0])
        polys = []
        for (pn, role, poly, depth, zc) in pr:
            tor = pn in ('belly', 'chest', 'hip', 'neck')
            far = zc > 0.02 and not tor and pn != 'saddle'
            polys.append((role, poly, far, 'torso' if tor else None))
        (nx, ny), nz = proj_pt(neck, yaw, BODY_ANCHOR)
        top = min(p[:, 1].min() for (_, _, p, _, _) in pr)
        tab = dict(marker=BODY_TAB, base=(BODY_TAB[0], top + 6), id=ids[name])
        im = cut(BODY_SIZE, polys, style, seed=zlib.crc32(name.encode()) % 9973, tab=tab, grain_seed=len(name))
        im.save(os.path.join(outdir, name + '.png'))
        tail_tip = pr and [p for (pn, _, p, _, _) in pr if pn == 'tail4'][0].mean(0)
        meta[name] = dict(kind='dog_body', size=BODY_SIZE, anchor=BODY_ANCHOR, neck=[nx, ny], yaw=yaw, pose=pose,
                          head_behind=bool(30 < yaw % 360 < 150), id=ids[name], tab=dict(marker=BODY_TAB, grip=[BODY_TAB[0] + 21, BODY_TAB[1] + 4]),
                          tail_tip=[float(tail_tip[0]), float(tail_tip[1])])
    for name, yaw, ears, mouth in HEADS:
        parts = head_parts(ears, mouth)
        pr = project(parts, yaw, HEAD_ANCHOR, scale=M * HS)
        polys = []
        for (pn, role, poly, depth, zc) in pr:
            far = zc > 0.03 and pn.startswith(('ear', 'eye'))
            polys.append((role, poly, far, 'torso' if pn in ('skull', 'cheek') else None))
        top = min(p[:, 1].min() for (_, _, p, _, _) in pr)
        tab = dict(marker=HEAD_TAB, base=(HEAD_TAB[0], top + 5), id=ids[name])
        im = cut(HEAD_SIZE, polys, style, seed=zlib.crc32(name.encode()) % 9973, tab=tab, grain_seed=3)
        im.save(os.path.join(outdir, name + '.png'))
        (mx, my), mz = proj_pt(np.array([0.27, 0.0, 0]), yaw, HEAD_ANCHOR, M * HS)
        (sx, sy), sz = proj_pt(np.array([-0.02, 0.06, 0]), yaw, HEAD_ANCHOR, M * HS)
        meta[name] = dict(kind='dog_head', size=HEAD_SIZE, anchor=HEAD_ANCHOR, yaw=yaw, id=ids[name], muzzle=[mx, my], skull=[sx, sy],
                          muzzle_hidden=bool(mz > 0.05), tab=dict(marker=HEAD_TAB, grip=[HEAD_TAB[0] - 21, HEAD_TAB[1] + 2]))


# ---------------------------------------------------------------- the person (profile facing right, toward the door)
PERSON_SIZE, PERSON_ANCHOR = (300, 470), (130, 450)
PERSON_TAB = (170, 26)
PSKIN = {'skin': (214, 168, 132), 'hair': (52, 40, 36), 'shirt': (92, 112, 140), 'trouser': (58, 58, 72), 'shoe': (36, 30, 28), 'cuff': (200, 196, 182), 'far': (70, 86, 110)}


def capsule_poly(a, b, ra, rb, n=10):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = max(np.hypot(*d), 1e-6)
    e = d / L
    nrm = np.array([-e[1], e[0]])
    P = []
    for k in range(n + 1):
        t = math.pi / 2 + math.pi * k / n
        P.append(a + (e * math.cos(t) + nrm * math.sin(t)) * ra)
    for k in range(n + 1):
        t = -math.pi / 2 + math.pi * k / n
        P.append(b + (e * math.cos(t) + nrm * math.sin(t)) * rb)
    return np.array(P)


def person_pose(name):
    """joint positions in card px (y down), facing right. Returns dict of segments."""
    ax, ay = PERSON_ANCHOR
    J = {}
    if name.startswith('p_sit'):
        hipy = ay - 34
        J['hip'] = (ax - 10, hipy); J['sh'] = (ax - 2, hipy - 142); J['head'] = (ax + 8, hipy - 178)
        J['knee_n'] = (ax + 68, hipy - 62); J['foot_n'] = (ax + 104, ay - 6)
        J['knee_f'] = (ax + 62, hipy - 56); J['foot_f'] = (ax + 96, ay - 8)
        if name == 'p_sit_low':
            J['elb_n'] = (ax + 46, hipy - 70); J['hand_n'] = (ax + 120, hipy - 28)
        else:
            J['elb_n'] = (ax + 30, hipy - 80); J['hand_n'] = (ax + 66, hipy - 64)
        J['elb_f'] = (ax + 24, hipy - 78); J['hand_f'] = (ax + 60, hipy - 66)
    elif name == 'p_down':
        hipy = ay - 120
        J['hip'] = (ax - 20, hipy); J['sh'] = (ax + 12, hipy - 136); J['head'] = (ax + 30, hipy - 170)
        J['knee_n'] = (ax + 50, hipy + 10); J['foot_n'] = (ax + 30, ay - 6)
        J['knee_f'] = (ax + 40, hipy + 14); J['foot_f'] = (ax + 10, ay - 6)
        J['elb_n'] = (ax + 40, hipy - 64); J['hand_n'] = (ax + 66, hipy - 20)
        J['elb_f'] = (ax + 30, hipy - 66); J['hand_f'] = (ax + 54, hipy - 24)
    else:
        lean = {'p_stand': 0, 'p_call': 8, 'p_reach': 24, 'p_step': 4}[name]
        hipy = ay - 180
        J['hip'] = (ax, hipy); J['sh'] = (ax + lean, hipy - 142); J['head'] = (ax + lean * 1.3 + 6, hipy - 180)
        if name == 'p_step':
            J['knee_n'] = (ax - 22, hipy + 88); J['foot_n'] = (ax - 44, ay - 6)
            J['knee_f'] = (ax + 20, hipy + 90); J['foot_f'] = (ax + 28, ay - 6)
        else:
            J['knee_n'] = (ax + 6, hipy + 90); J['foot_n'] = (ax + 4, ay - 6)
            J['knee_f'] = (ax - 4, hipy + 90); J['foot_f'] = (ax - 8, ay - 6)
        if name == 'p_reach':
            J['elb_n'] = (ax + lean + 62, hipy - 84); J['hand_n'] = (ax + lean + 128, hipy - 50)
        elif name == 'p_call':
            J['elb_n'] = (ax + lean + 30, hipy - 70); J['hand_n'] = (ax + lean + 50, hipy - 118)
        else:
            J['elb_n'] = (ax + lean + 10, hipy - 70); J['hand_n'] = (ax + lean + 12, hipy - 2)
        J['elb_f'] = (ax + lean - 8, hipy - 70); J['hand_f'] = (ax + lean - 4, hipy - 4)
    return J


def build_person(style, ids, meta, outdir):
    for name in ('p_stand', 'p_call', 'p_reach', 'p_step', 'p_down', 'p_sit', 'p_sit_low'):
        J = person_pose(name)
        polys = []
        far = []
        far.append(('far', capsule_poly(J['hip'], J['knee_f'], 17, 14)))
        far.append(('far', capsule_poly(J['knee_f'], J['foot_f'], 14, 11)))
        far.append(('shoe', capsule_poly(J['foot_f'], (J['foot_f'][0] + 22, J['foot_f'][1]), 9, 8)))
        far.append(('far', capsule_poly(J['sh'], J['elb_f'], 13, 11)))
        far.append(('far', capsule_poly(J['elb_f'], J['hand_f'], 11, 9)))
        near = []
        near.append(('trouser', capsule_poly(J['hip'], J['knee_n'], 19, 15)))
        near.append(('trouser', capsule_poly(J['knee_n'], J['foot_n'], 15, 12)))
        near.append(('shoe', capsule_poly(J['foot_n'], (J['foot_n'][0] + 24, J['foot_n'][1]), 10, 8)))
        torso = capsule_poly(J['sh'], J['hip'], 32, 28)
        near.append(('shirt', torso))
        hx, hy = J['head']
        near.append(('skin', capsule_poly((J['sh'][0] + 2, J['sh'][1] - 4), (hx - 4, hy + 18), 10, 10)))
        head = [(hx + 26 * math.cos(t) * (1.0 if math.cos(t) < 0 else 0.92), hy + 30 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 28, endpoint=False)]
        head.insert(0, (hx + 27, hy + 4)); head.insert(1, (hx + 30, hy + 8)); head.insert(2, (hx + 26, hy + 12))   # nose
        near.append(('skin', np.array(head)))
        hair = [(hx + 26 * math.cos(t), hy + 30 * math.sin(t)) for t in np.linspace(math.pi * .95, math.pi * 2.08, 20)]
        hair += [(hx - 10, hy + 10), (hx - 22, hy + 22)]
        near.append(('hair', np.array(hair)))
        near.append(('shirt', capsule_poly(J['sh'], J['elb_n'], 13, 11)))
        near.append(('skin', capsule_poly(J['elb_n'], J['hand_n'], 10, 8)))
        near.append(('skin', capsule_poly(J['hand_n'], (J['hand_n'][0] + (J['hand_n'][0] - J['elb_n'][0]) * .22, J['hand_n'][1] + (J['hand_n'][1] - J['elb_n'][1]) * .22), 10, 7)))
        allp = [(r, p, r == 'far') for r, p in far] + [(r, p, False) for r, p in near]
        top = min(p[:, 1].min() for _, p, _ in allp)
        tab = dict(marker=PERSON_TAB, base=(PERSON_TAB[0] + 10, top + 30), id=ids[name])
        big = Image.new('RGBA', (PERSON_SIZE[0] * SS, PERSON_SIZE[1] * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        for k, (role, poly, isfar) in enumerate(allp):
            pts = [tuple(p) for p in jitter_poly(poly, 0.8, k + len(name) * 17, 4.0) * SS]
            if style == 'skin':
                col = PSKIN[role]
                d.polygon(pts, fill=col + (255,)); d.line(pts + [pts[0]], fill=(40, 30, 28, 255), width=int(1.3 * SS))
            else:
                col = {'hair': (60, 60, 60), 'far': (214, 214, 206), 'shoe': (70, 70, 70)}.get(role, (238, 236, 228))
                d.polygon(pts, fill=col + (255,)); d.line(pts + [pts[0]], fill=(28, 28, 30, 255), width=int(1.8 * SS))
        if style == 'skin':  # eye and a mouth line
            d.ellipse([(hx + 12) * SS, (hy - 4) * SS, (hx + 16) * SS, hy * SS], fill=(30, 24, 22, 255))
            if name == 'p_call' or name == 'p_reach':
                d.ellipse([(hx + 17) * SS, (hy + 14) * SS, (hx + 24) * SS, (hy + 21) * SS], fill=(70, 30, 30, 255))
            else:
                d.line([(hx + 17) * SS, (hy + 18) * SS, (hx + 23) * SS, (hy + 17) * SS], fill=(90, 50, 44, 255), width=SS)
        draw_tab(d, tab, style)
        im = big.resize(PERSON_SIZE, Image.LANCZOS)
        a = np.asarray(im, np.float32)
        a[..., :3] *= (1 + (0.07 if style == 'skin' else 0.03) * grain(PERSON_SIZE[1], PERSON_SIZE[0], 21))[..., None]
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
        if style == 'plate':
            im = paste_marker(im, tab)
        im.save(os.path.join(outdir, name + '.png'))
        meta[name] = dict(kind='person', size=PERSON_SIZE, anchor=PERSON_ANCHOR, id=ids[name], hand=list(J['hand_n']), head=list(J['head']),
                          tab=dict(marker=list(tab['marker']), grip=[tab['marker'][0] - 21, tab['marker'][1] + 2]))


# ---------------------------------------------------------------- door leaf and light
DOOR_SIZE, DOOR_ANCHOR = (220, 440), (150, 420)       # anchor = the hinge at the inner jamb, floor


def build_door(style, ids, meta, outdir):
    for name, wpx in (('d_ajar', 12), ('d_mid', 26), ('d_open', 46)):
        ax, ay = DOOR_ANCHOR
        top, bot = ay - (GROUND - LINTEL) + 6, ay
        sk = wpx * 0.22            # the free edge drops/rises in oblique projection
        poly = np.array([(ax, top), (ax - wpx, top + sk), (ax - wpx, bot - sk * .2), (ax, bot)])
        polys = [('door', poly, False)]
        big = Image.new('RGBA', (DOOR_SIZE[0] * SS, DOOR_SIZE[1] * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        pts = [tuple(p) for p in jitter_poly(poly, 0.6, len(name), 4.0) * SS]
        if style == 'skin':
            d.polygon(pts, fill=(64, 82, 70, 255)); d.line(pts + [pts[0]], fill=(30, 36, 30, 255), width=2 * SS)
            for fr in (0.12, 0.55):   # two panels
                y0 = top + (bot - top) * fr; y1 = y0 + (bot - top) * 0.36
                p = [(ax - wpx * .18, y0 + sk * .18 + 6), (ax - wpx * .82, y0 + sk * .82 + 6), (ax - wpx * .82, y1 + sk * .82 - 6), (ax - wpx * .18, y1 + sk * .18 - 6)]
                d.polygon([(x * SS, y * SS) for x, y in p], outline=(36, 48, 40, 255), width=SS)
            kx, ky = ax - wpx * .86, (top + bot) / 2 + sk * .86
            d.ellipse([(kx - 3) * SS, (ky - 3) * SS, (kx + 3) * SS, (ky + 3) * SS], fill=(200, 170, 90, 255))
        else:
            d.polygon(pts, fill=(226, 226, 218, 255)); d.line(pts + [pts[0]], fill=(28, 28, 30, 255), width=2 * SS)
        tab = dict(marker=(ax + 42, 26), base=(ax - 8, top + 4), id=ids[name])
        draw_tab(d, tab, style)
        im = big.resize(DOOR_SIZE, Image.LANCZOS)
        if style == 'plate':
            im = paste_marker(im, tab)
        im.save(os.path.join(outdir, name + '.png'))
        meta[name] = dict(kind='door', size=DOOR_SIZE, anchor=DOOR_ANCHOR, id=ids[name], width=wpx, tab=dict(marker=list(tab['marker']), grip=[ax + 42 + 21, 28]))
    # light: a piece of yellow tissue. anchor = the end that sits in the doorway
    LS, LA = (340, 120), (14, 60)
    big = Image.new('RGBA', (LS[0] * SS, LS[1] * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    poly = np.array([(LA[0], LA[1] - 10), (LS[0] - 20, LA[1] - 26), (LS[0] - 6, LA[1] + 48), (LA[0], LA[1] + 18)])
    pts = [tuple(p) for p in jitter_poly(poly, 1.0, 5, 4.0) * SS]
    if style == 'skin':
        d.polygon(pts, fill=(255, 214, 120, 255))
    else:
        d.polygon(pts, fill=(250, 226, 120, 255)); d.line(pts + [pts[0]], fill=(150, 120, 40, 255), width=SS)
    tab = dict(marker=(LA[0] + 30, LA[1] - 34), base=(LA[0] + 30, LA[1] - 14), id=ids['light'])
    draw_tab(d, tab, style)
    im = big.resize(LS, Image.LANCZOS)
    if style == 'skin':
        im = im.filter(ImageFilter.GaussianBlur(3))
    else:
        im = paste_marker(im, tab)
    im.save(os.path.join(outdir, 'light.png'))
    meta['light'] = dict(kind='light', size=LS, anchor=LA, id=ids['light'], tab=dict(marker=list(tab['marker']), grip=[LA[0] + 80, LA[1] + 6]))


def all_names():
    n = [s[0] for s in dog_body_specs()] + [h[0] for h in HEADS]
    n += ['p_stand', 'p_call', 'p_reach', 'p_step', 'p_down', 'p_sit', 'p_sit_low', 'd_ajar', 'd_mid', 'd_open', 'light']
    return n


def main():
    names = all_names()
    ids = {n: k + 1 for k, n in enumerate(names)}
    assert len(ids) < 128
    meta = {}
    for style in ('plate', 'skin'):
        od = os.path.join(CACHE, 'cards', style)
        os_makedirs(od)
        m = {}
        build_dog(style, ids, m, od)
        build_person(style, ids, m, od)
        build_door(style, ids, m, od)
        meta = m
    os_makedirs(DATA)
    json.dump(meta, open(os.path.join(DATA, 'cards.json'), 'w'), indent=1, default=float)
    print('cards', len(meta))


if __name__ == '__main__':
    main()
