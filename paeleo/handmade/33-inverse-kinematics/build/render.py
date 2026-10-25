"""SCION 33 · render: the solved rig drawn as what it is — tapered bones (capsules) with their joints, lit by the dusk
and by the door's light, depth-sorted, clipped at the wall plane, with the door's light cast on the boards each frame and
the bodies' shadows cut out of it. Also measures the dog from the render (its silhouette mask) for trace.json.
usage: python3 render.py [first last] [--only i,j,k] -> build/cache/frames/%04d.png, build/cache/measure/%04d.json"""
import os, sys, json, math, pickle
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from geom import *

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
OUT = os.path.join(CACHE, 'frames'); MEAS = os.path.join(CACHE, 'measure')
os.makedirs(OUT, exist_ok=True); os.makedirs(MEAS, exist_ok=True)
SS = 2
SETS = {}
for _nm in CAMS:
    _fl = np.load(os.path.join(CACHE, 'floor_%s.npz' % _nm))
    SETS[_nm] = dict(cam=Camera(name=_nm), camS=Camera(w=W * SS, h=H * SS, name=_nm), half=Camera(w=W // 2, h=H // 2, name=_nm),
                     BG=np.asarray(Image.open(os.path.join(CACHE, 'bg_%s.png' % _nm)).convert('RGB'), float),
                     INTERIOR=Image.open(os.path.join(CACHE, 'interior_%s.png' % _nm)).convert('RGB'),
                     OPEN_M=Image.open(os.path.join(CACHE, 'opening_mask_%s.png' % _nm)).convert('L'),
                     FX=_fl['fx'][::2, ::2], FZ=_fl['fz'][::2, ::2], FON=_fl['on'][::2, ::2])


def set_camera(nm):
    g = globals()
    for k, v in SETS[nm].items(): g[k] = v
    g['CAMNAME'] = nm


set_camera('A')
UP = np.array([0, 1.0, 0])
WARM = np.array([255, 178, 108.0])

POSE = pickle.load(open(os.path.join(CACHE, 'pose.pkl'), 'rb'))
FRAMES = POSE['frames']


# ---------------------------------------------------------------- light from the door
def panel_edge(theta):
    th = math.radians(theta)
    return np.array([HINGE[0] - math.sin(th) * DOOR_W, HINGE[2] - math.cos(th) * DOOR_W])


def lit_test(px, py, pz, theta):
    """vectorised: is the segment from point p to the ceiling light unobstructed (through the opening, past the door)?"""
    L = CEIL
    ok = np.ones_like(px, bool)
    for xw in (WALL_OUT, WALL_IN):
        s = (px - xw) / (px - L[0])
        z = pz + s * (L[2] - pz); y = py + s * (L[1] - py)
        ok &= (px > xw) & (z > DOOR_Z[0]) & (z < DOOR_Z[1]) & (y < DOOR_H)
    # door panel (vertical segment Hinge -> Edge in XZ, height DOOR_H)
    hx, hz = HINGE[0], HINGE[2]; ex, ez = panel_edge(theta)
    dx, dz = L[0] - px, L[2] - pz
    qx, qz = ex - hx, ez - hz
    den = dx * qz - dz * qx
    den = np.where(np.abs(den) < 1e-9, 1e-9, den)
    s = ((hx - px) * qz - (hz - pz) * qx) / den
    u = ((hx - px) * dz - (hz - pz) * dx) / den
    yy = py + s * (L[1] - py)
    blocked = (s > 0) & (s < 1) & (u > 0) & (u < 1) & (yy < DOOR_H)
    return ok & ~blocked


def light_at(p, theta):
    """scalar light amount at a 3D point (for tinting the bodies)."""
    p = np.asarray(p, float)
    if p[0] < WALL_IN:  # inside the room: lit by the room
        return 0.42
    vis = lit_test(np.array([p[0]]), np.array([p[1]]), np.array([p[2]]), theta)[0]
    if not vis: return 0.0
    d = np.linalg.norm(p - CEIL)
    return float(min(1.0, 1.7 / d ** 1.25))


# ---------------------------------------------------------------- bodies as capsules
def C(a, b, ra, rb, col, part, side=0, joint=None):
    return dict(a=np.asarray(a, float), b=np.asarray(b, float), ra=ra, rb=rb, col=col, part=part, side=side, joint=joint)


def dog_capsules(d):
    caps = []
    Pv, Ch, Fc = d['Pv'], d['Ch'], d['Fc']
    Fp = norm(Ch - Pv); Fp[1] = 0; Fp = norm(Fp)
    br = d['breath']
    body = (78, 62, 58); saddle = (46, 38, 42); tan = (118, 90, 68); dark = (40, 32, 34)
    def L(u): return Pv * (1 - u) + Ch * u
    rump = Pv + UP * 0.025 - Fp * 0.05
    loin = L(0.34) + UP * 0.045
    waist = L(0.55) + UP * 0.01
    ribs = L(0.80) - UP * 0.03
    chest = Ch - UP * 0.035 + Fc * 0.03
    brisket = Ch - UP * 0.09 + Fc * 0.10
    waist = waist + UP * 0.025
    caps += [C(rump, loin, 0.112, 0.098, body, 'torso'), C(loin, waist, 0.098, 0.105, body, 'torso'),
             C(waist, ribs, 0.105, 0.158 + br, body, 'torso'), C(ribs, chest, 0.158 + br, 0.150 + br, body, 'torso'),
             C(chest, brisket, 0.13, 0.10, tan, 'torso')]
    # the saddle: darker over the back
    caps += [C(rump + UP * 0.05, ribs + UP * 0.08, 0.075, 0.09, saddle, 'saddle'), C(ribs + UP * 0.08, d['withers'], 0.09, 0.07, saddle, 'saddle')]
    # neck and ruff
    caps += [C(d['NB'] - Fc * 0.03, d['Hc'] - d['Mdir'] * 0.02, 0.092, 0.064, body, 'neck')]
    # head: skull, muzzle, nose; ears as thin tapered capsules (pricked .. flat)
    Hc, M, Sh = d['Hc'], d['Mdir'], d['Sh']
    caps += [C(Hc - M * 0.015, Hc + M * 0.012, 0.080, 0.078, body, 'skull')]
    m0 = Hc + M * 0.04 - UP * 0.014; m1 = Hc + M * 0.160 - UP * 0.030
    caps += [C(m0, m1, 0.054, 0.031, tan, 'muzzle'), C(m1, m1 + M * 0.014, 0.022, 0.02, (20, 16, 18), 'nose')]
    ear_a = 0.25 + 1.15 * (1 - d['ear'])
    Hup = norm(UP - M * (M @ UP));
    for sgn in (-1, 1):
        base = Hc + Hup * 0.052 + Sh * (0.04 * sgn) - M * 0.02
        tip = base + (Hup * math.cos(ear_a) - M * math.sin(ear_a)) * 0.085 + Sh * (0.012 * sgn)
        caps.append(C(base, tip, 0.036, 0.007, saddle, 'ear', side=sgn))
    # eyes (drawn as joints of the face)
    for sgn in (-1, 1):
        caps.append(C(Hc + M * 0.055 + Hup * 0.022 + Sh * (0.036 * sgn), Hc + M * 0.058 + Hup * 0.022 + Sh * (0.036 * sgn), 0.009, 0.009, (24, 18, 16), 'eye', side=sgn))
    # legs
    for Lg, g in d['legs'].items():
        s = 1 if Lg[0] == 'R' else -1
        fore = Lg[1] == 'F'
        a, m, w, p = g['anchor'], g['mid'], g['wrist'], g['paw']
        if fore:
            caps += [C(a + UP * 0.03, m, 0.062, 0.042, body, 'upper', s, joint='elbow'), C(m, w, 0.034, 0.025, tan, 'lower', s, joint='wrist'),
                     C(w, p, 0.024, 0.026, tan, 'pastern', s)]
        else:
            caps += [C(a + UP * 0.02 - Fp * 0.01, m, 0.074, 0.046, body, 'thigh', s, joint='stifle'), C(m, w, 0.042, 0.026, tan, 'shank', s, joint='hock'),
                     C(w, p, 0.022, 0.024, tan, 'pastern', s)]
        fwd_p = Fc if fore else Fp
        caps.append(C(p - fwd_p * 0.01, p + fwd_p * 0.045, 0.03, 0.026, tan, 'paw', s))
    # tail: bushy, darker
    tl = d['tail']
    for k in range(len(tl) - 1):
        r0 = 0.037 - 0.0026 * k; r1 = 0.037 - 0.0026 * (k + 1)
        caps.append(C(tl[k], tl[k + 1], r0, r1, saddle if k > 1 else body, 'tail'))
    return caps


def person_capsules(p):
    caps = []
    coat = (62, 68, 92); trou = (40, 44, 62); skin = (150, 114, 98); hair = (30, 26, 30); shoe = (26, 24, 28)
    pel, ch, nk, hd = p['pelvis'], p['chest'], p['neck'], p['head']
    caps += [C(pel, ch, 0.15, 0.17, coat, 'p.torso'), C(nk, hd - (hd - nk) * 0.3, 0.05, 0.05, skin, 'p.neck'),
             C(hd, hd + UP * 0.01, 0.105, 0.105, skin, 'p.head'), C(hd + p['gaze'] * 0.08 - UP * 0.01, hd + p['gaze'] * 0.115 - UP * 0.015, 0.03, 0.022, skin, 'p.nose'), C(hd + UP * 0.035 - p['gaze'] * 0.03, hd + UP * 0.04 - p['gaze'] * 0.035, 0.094, 0.092, hair, 'p.hair')]
    for nm, side in (('legR', 1), ('legL', -1)):
        g = p[nm]
        caps += [C(g['root'], g['mid'], 0.085, 0.065, trou, 'p.thigh', side, joint='knee'), C(g['mid'], g['end'], 0.06, 0.045, trou, 'p.shin', side),
                 C(g['end'], g['tip'], 0.045, 0.04, shoe, 'p.foot', side)]
    for nm, side in (('armR', 1), ('armL', -1)):
        g = p[nm]
        caps += [C(g['root'], g['mid'], 0.056, 0.048, coat, 'p.upper', side, joint='elbow'), C(g['mid'], g['end'], 0.045, 0.036, coat, 'p.fore', side),
                 C(g['end'], g['tip'], 0.036, 0.03, skin, 'p.hand', side)]
    return caps


def split_at_wall(cap):
    """clip a capsule at the house's outer wall plane: inside parts are only seen through the opening."""
    a, b = cap['a'], cap['b']
    ia, ib = a[0] < WALL_OUT, b[0] < WALL_OUT
    if ia == ib:
        return [(cap, ia)]
    s = (WALL_OUT - a[0]) / (b[0] - a[0])
    m = a + (b - a) * s; rm = cap['ra'] + (cap['rb'] - cap['ra']) * s
    c1 = dict(cap, b=m, rb=rm); c2 = dict(cap, a=m, ra=rm)
    return [(c1, ia), (c2, ib)]


def shade(col, lit, k=1.0, cool=0.0):
    c = np.array(col, float) * k
    c = c * (1 - cool) + np.array([60, 70, 110.0]) * cool * (c.mean() / 80)
    c = c + lit * (WARM * 0.5 - c * 0.2)
    return tuple(int(max(0, min(255, v))) for v in c)


def draw_capsule(dr, pa, pb, ra, rb, fill):
    ax, ay = pa; bx, by = pb
    dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy)
    if L < 1e-6:
        r = max(ra, rb); dr.ellipse([ax - r, ay - r, ax + r, ay + r], fill=fill); return
    nx, ny = -dy / L, dx / L
    # tangent offset accounting for unequal radii
    sa = (ra - rb) / L
    ca = math.sqrt(max(0.0, 1 - sa * sa))
    ux, uy = dx / L, dy / L
    o1 = (nx * ca + ux * sa, ny * ca + uy * sa); o2 = (-nx * ca + ux * sa, -ny * ca + uy * sa)
    pts = [(ax + o1[0] * ra, ay + o1[1] * ra), (bx + o1[0] * rb, by + o1[1] * rb), (bx + o2[0] * rb, by + o2[1] * rb), (ax + o2[0] * ra, ay + o2[1] * ra)]
    dr.polygon(pts, fill=fill)
    dr.ellipse([ax - ra, ay - ra, ax + ra, ay + ra], fill=fill)
    dr.ellipse([bx - rb, by - rb, bx + rb, by + rb], fill=fill)


GROUP = {'torso': 'dog.body', 'saddle': 'dog.body', 'neck': 'dog.head', 'skull': 'dog.head', 'muzzle': 'dog.head',
         'nose': 'dog.head', 'eye': 'dog.head', 'ear': 'dog.head', 'tail': 'dog.tail',
         'p.torso': 'p.body', 'p.neck': 'p.body', 'p.head': 'p.head', 'p.hair': 'p.head', 'p.nose': 'p.head'}
LATE = {'saddle', 'nose', 'eye'}


def cap_geom(cap, off):
    A = camS.project(cap['a']); B = camS.project(cap['b'])
    if A[2] < 0.1 or B[2] < 0.1: return None
    ra = cap['ra'] * camS.scale(A[2]); rb = cap['rb'] * camS.scale(B[2])
    return (A[0] - off[0], A[1] - off[1]), (B[0] - off[0], B[1] - off[1]), ra, rb


def render_caps(dr, items, theta, off, mask_dr=None, light_dir=None):
    """items: depth-sorted far -> near; each is a list of capsules drawn as one volume (all outlines, then fills by
    depth, then the lit side), so a body reads as one mass while each limb bone keeps its own outline and joint."""
    for grp in items:
        geo = []
        for cap in sorted(grp, key=lambda c: (c['part'] in LATE, -depth_key(c))):
            g = cap_geom(cap, off)
            if g is None: continue
            mid = (cap['a'] + cap['b']) / 2
            lit = light_at(mid, theta)
            k = 0.70 if cap.get('side_far') else 1.0
            geo.append((cap, g, lit, k))
        ow = 1.3 * SS / 2
        for cap, (pa, pb, ra, rb), lit, k in geo:
            if cap['part'] in LATE: continue
            draw_capsule(dr, pa, pb, ra + ow, rb + ow, shade(cap['col'], lit * 0.3, k * 0.45, cool=0.4))
        for cap, (pa, pb, ra, rb), lit, k in geo:
            draw_capsule(dr, pa, pb, ra, rb, shade(cap['col'], lit, k * 0.92, cool=0.25))
        if light_dir is not None:
            for cap, (pa, pb, ra, rb), lit, k in geo:
                if cap['part'] in LATE or ra < 2.5 or rb < 2.0: continue
                lx, ly = light_dir if lit > 0.02 else (-0.25, -0.97)
                sh = 0.36
                draw_capsule(dr, (pa[0] + lx * ra * sh, pa[1] + ly * ra * sh), (pb[0] + lx * rb * sh, pb[1] + ly * rb * sh), ra * 0.52, rb * 0.52,
                             shade(cap['col'], lit * 1.25, k * 1.16, cool=0.05))
        for cap, (pa, pb, ra, rb), lit, k in geo:
            if cap['joint'] and ra > 3:
                jr = max(1.4, rb * 0.55)
                dr.ellipse([pb[0] - jr, pb[1] - jr, pb[0] + jr, pb[1] + jr], outline=shade((176, 156, 124), lit, 0.85 * k), width=max(1, int(SS * 0.75)))


def depth_key(cap):
    return float(((cap['a'] + cap['b']) / 2 - cam.pos) @ cam.fwd)


def characters(fr, theta):
    """-> list of (group of capsules, inside_house)"""
    d = fr['dog']; p = fr['person']
    dc = dog_capsules(d); pc = person_capsules(p)
    camv = cam.pos
    for c in dc:
        c['dog'] = True
        c['side_far'] = (c['side'] != 0) and ((camv - d['Ch']) @ d['S'] * c['side'] < 0)
    for c in pc:
        c['dog'] = False
        c['side_far'] = (c['side'] != 0) and ((camv - p['pelvis']) @ np.array([0, 0, 1.0]) * c['side'] < 0)
    groups = {}
    order = []
    n = 0
    for c in dc + pc:
        if c['part'] == 'eye' and c['side_far']: continue
        for piece, inside in split_at_wall(c):
            gid = (GROUP.get(c['part'], 'solo%d' % n), inside)
            n += 1
            if gid not in groups: groups[gid] = []; order.append(gid)
            groups[gid].append(piece)
    return [(groups[g], g[1]) for g in order]


def group_depth(grp):
    return float(np.mean([depth_key(c) for c in grp]))


def floor_light(theta, shadow_polys):
    """per-pixel door light on the porch boards (half resolution), with the bodies' cast shadows removed."""
    lit = lit_test(FX, np.zeros_like(FX), FZ, theta) & FON
    d2 = (FX - CEIL[0]) ** 2 + CEIL[1] ** 2 + (FZ - CEIL[2]) ** 2
    inten = 3.0 * (CEIL[1] / np.sqrt(d2)) / d2 ** 0.62
    m = Image.fromarray((lit * 255).astype(np.uint8))
    dr = ImageDraw.Draw(m)
    for poly in shadow_polys:
        dr.polygon(poly, fill=0)
    m = m.filter(ImageFilter.GaussianBlur(1.6))
    a = np.asarray(m, float) / 255 * np.clip(inten, 0, 1.2)
    a = np.asarray(Image.fromarray((np.clip(a, 0, 1.5) / 1.5 * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), float) / 255 * 1.5
    return a


def cast_shadow_polys(caps):
    """project each capsule from the ceiling light onto the boards (half-resolution screen polygons)."""
    out = []
    for c in caps:
        segs = []
        for P_ in (c['a'], c['b']):
            P_ = np.asarray(P_, float)
            if P_[0] < WALL_OUT or P_[1] >= CEIL[1] - 0.05: segs = None; break
            s = P_[1] / (CEIL[1] - P_[1])
            g = P_ + (P_ - CEIL) * s; g[1] = 0.0
            segs.append(g)
        if not segs: continue
        ga, gb = segs
        r = max(c['ra'], c['rb']) * 1.3
        dirv = gb - ga; dirv[1] = 0
        n = np.array([-dirv[2], 0, dirv[0]]); n = norm(n) * r if np.linalg.norm(n) > 1e-6 else np.array([r, 0, 0])
        quad = [ga + n, gb + n, gb - n, ga - n]
        q = half.project(np.array(quad))
        out.append([(float(x), float(y)) for x, y, _ in q])
    return out


def contact_shadow(img_arr, fr):
    """soft occlusion on the boards under the dog's body and paws, and under the person (multiplicative)."""
    m = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(m)
    d = fr['dog']
    def blob(p, rx, rz, a):
        pts = []
        for k in range(16):
            ang = 2 * math.pi * k / 16
            pts.append(p + np.array([math.cos(ang) * rx, 0, math.sin(ang) * rz]))
        q = cam.project(np.array(pts)); dr.polygon([(x, y) for x, y, _ in q], fill=a)
    body_c = (d['Pv'] + d['Ch']) / 2; body_c = np.array([body_c[0], 0.0, body_c[2]])
    hgt = (d['Pv'][1] + d['Ch'][1]) / 2
    blob(body_c, 0.40, 0.16, int(120 if hgt < 0.25 else 70))
    for Lg, g in d['legs'].items():
        if g['paw'][0] < WALL_OUT: continue
        a = 150 if g['planted'] else 60
        blob(np.array([g['paw'][0], 0, g['paw'][2]]), 0.05, 0.035, a)
    p = fr['person']
    for f in (p['rfoot'], p['lfoot']):
        if f[0] > WALL_OUT: blob(np.array([f[0] + 0.06, 0, f[2]]), 0.14, 0.06, 120)
    if p['seated'] > 0.5:
        blob(np.array([p['pelvis'][0], 0, p['pelvis'][2]]), 0.22, 0.20, 140)
    m = m.filter(ImageFilter.GaussianBlur(5))
    a = np.asarray(m, float)[..., None] / 255
    return img_arr * (1 - 0.55 * a)


def render(i):
    set_camera(cam_name(i))
    fr = FRAMES[i]
    theta = fr['door']
    caps = characters(fr, theta)
    img = BG.copy()
    # door light on the boards, minus cast shadows
    allcaps = [c for grp, inside in caps if not inside for c in grp]
    L = floor_light(theta, cast_shadow_polys(allcaps))
    img = img + L[..., None] * (WARM[None, None] * 0.85 - img * 0.25)
    img = contact_shadow(img, fr)
    frame = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    # the room through the opening: interior, far reveal, inner sill, door panel, bodies inside
    inside = INTERIOR.copy()
    di = ImageDraw.Draw(inside)
    def ppoly(dr, pts, fill, c=cam):
        q = c.project(np.array(pts, float)); dr.polygon([(x, y) for x, y, _ in q], fill=fill)
    open_k = min(1.0, max(0.0, (theta - 11) / 60))
    ppoly(di, [[WALL_OUT, 0, DOOR_Z[0]], [WALL_IN, 0, DOOR_Z[0]], [WALL_IN, DOOR_H, DOOR_Z[0]], [WALL_OUT, DOOR_H, DOOR_Z[0]]], shade((70, 68, 92), 0.12 + 0.22 * open_k))
    ppoly(di, [[WALL_IN - 0.02, 0.0, DOOR_Z[0]], [WALL_OUT, 0.0, DOOR_Z[0]], [WALL_OUT, 0.03, DOOR_Z[1]], [WALL_IN - 0.02, 0.03, DOOR_Z[1]]], shade((110, 96, 90), 0.5 + 0.3 * open_k))
    th = math.radians(theta)
    E0 = HINGE + np.array([-math.sin(th) * DOOR_W, 0, -math.cos(th) * DOOR_W])
    panel = [HINGE + [0, 0.01, 0], E0 + [0, 0.01, 0], E0 + [0, DOOR_H - 0.01, 0], HINGE + [0, DOOR_H - 0.01, 0]]
    # which face we see: outer face (dark, back-lit) while ajar; the room-lit face once it swings past the view line
    n_out = np.array([math.cos(th), 0, -math.sin(th)])
    pc = (HINGE + E0) / 2 + UP * 1.0
    outer = (cam.pos - pc) @ n_out > 0
    ppoly(di, panel, (34, 30, 40) if outer else (150, 104, 70))
    # panels in the door (four recessed fields)
    for (s0, s1, y0, y1) in [(0.12, 0.45, 0.15, 0.95), (0.55, 0.88, 0.15, 0.95), (0.12, 0.45, 1.1, 1.9), (0.55, 0.88, 1.1, 1.9)]:
        pts = [HINGE + np.array([-math.sin(th) * DOOR_W * s, y, -math.cos(th) * DOOR_W * s]) for s, y in ((s0, y0), (s1, y0), (s1, y1), (s0, y1))]
        ppoly(di, pts, (28, 24, 34) if outer else (128, 88, 60))
    # the brass knob near the edge
    kn = cam.project(HINGE + np.array([-math.sin(th) * DOOR_W * 0.92, 0.95, -math.cos(th) * DOOR_W * 0.92]))
    di.ellipse([kn[0] - 3, kn[1] - 3, kn[0] + 3, kn[1] + 3], fill=(150, 120, 70))
    # interior-side bodies
    ins = sorted([g for g, inside_ in caps if inside_], key=lambda g: -group_depth(g))
    out = sorted([g for g, inside_ in caps if not inside_], key=lambda g: -group_depth(g))
    dmask = Image.new('L', (W * SS, H * SS), 0); dm = ImageDraw.Draw(dmask)
    door_scr = cam.project(np.array([0.0, 1.4, 0.0]))
    def ldir(p0):
        v = np.array([door_scr[0] - p0[0], door_scr[1] - p0[1]]); n = np.linalg.norm(v)
        return (v / n) if n > 1 else (-1, 0)
    if ins:
        layer = inside.resize((W * SS, H * SS), Image.BILINEAR)
        dl = ImageDraw.Draw(layer)
        render_caps(dl, ins, theta, (0, 0), None, light_dir=(0.6, -0.8))
        for c in [c for g in ins for c in g]:
            if c.get('dog'):
                A = camS.project(c['a']); B = camS.project(c['b'])
                draw_capsule(dm, A[:2], B[:2], c['ra'] * camS.scale(A[2]), c['rb'] * camS.scale(B[2]), 255)
        inside = layer.resize((W, H), Image.LANCZOS)
    frame.paste(inside, (0, 0), OPEN_M)
    # outside bodies, drawn in a crop at 2x
    if out:
        flat = [c for g in out for c in g]
        pts = np.array([camS.project(c['a'])[:2] for c in flat] + [camS.project(c['b'])[:2] for c in flat])
        x0 = int(max(0, pts[:, 0].min() - 120)); y0 = int(max(0, pts[:, 1].min() - 120))
        x1 = int(min(W * SS, pts[:, 0].max() + 120)); y1 = int(min(H * SS, pts[:, 1].max() + 120))
        x0 -= x0 % 2; y0 -= y0 % 2; x1 -= x1 % 2; y1 -= y1 % 2
        crop = frame.crop((x0 // 2, y0 // 2, x1 // 2, y1 // 2)).resize((x1 - x0, y1 - y0), Image.BICUBIC)
        dc = ImageDraw.Draw(crop)
        # door-ward light direction in screen space for the lit side
        cen = pts.mean(0)
        render_caps(dc, out, theta, (x0, y0), None, light_dir=tuple(ldir(cen / SS)))
        # mask for the dog (measurement) — draw into the full-size mask
        for c in flat:
            if c.get('dog'):
                A = camS.project(c['a']); B = camS.project(c['b'])
                draw_capsule(dm, A[:2], B[:2], c['ra'] * camS.scale(A[2]), c['rb'] * camS.scale(B[2]), 255)
        small = crop.resize(((x1 - x0) // 2, (y1 - y0) // 2), Image.LANCZOS)
        frame.paste(small, (x0 // 2, y0 // 2))
    # film: a little grain and a soft vignette (seeded per frame)
    arr = np.asarray(frame, float)
    rng = np.random.default_rng(1000 + i)
    arr += rng.normal(0, 2.2, (H, W, 1))
    arr *= VIG[..., None]
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, '%04d.png' % i), compress_level=1)
    # measurement from the render
    dmask = np.asarray(dmask.resize((W, H), Image.BILINEAR)) > 100
    ys, xs = np.nonzero(dmask)
    d = fr['dog']
    hs = cam.project(d['Hc']); ms = cam.project(d['Hc'] + d['Mdir'] * 0.15)
    meas = dict(i=i, area=int(len(xs)), cam=CAMNAME)
    if len(xs):
        meas.update(cx=float(xs.mean()), cy=float(ys.mean()), x0=int(xs.min()), x1=int(xs.max()), y0=int(ys.min()), y1=int(ys.max()))
    meas.update(head_x=float(hs[0]), head_y=float(hs[1]), muzzle_x=float(ms[0]), muzzle_y=float(ms[1]))
    bl = cam.project(d['withers'] + UP * 0.035)
    meas.update(back_y=float(bl[1]))
    json.dump(meas, open(os.path.join(MEAS, '%04d.json' % i), 'w'))
    return i


yy, xx = np.mgrid[0:H, 0:W]
VIG = 1 - 0.28 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.4
VIG = np.clip(VIG, 0.55, 1)

if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--only':
        idx = [int(v) for v in args[1].split(',')]
    elif len(args) >= 2:
        idx = list(range(int(args[0]), int(args[1])))
    else:
        idx = list(range(N))
    workers = int(os.environ.get('WORKERS', '1'))
    if workers > 1:
        from multiprocessing import Pool
        with Pool(workers) as pool:
            for _ in pool.imap_unordered(render, idx, chunksize=4): pass
    else:
        for i in idx: render(i)
    print('rendered', len(idx))
