"""SCION 51 · shared geometry: camera, porch/door/room, the steady dog (a body of spheres in my own construction, a stable
silhouette whose surface carries the substituted images) and the person.
World: metres. x along the facade (door centre 0), y up, z out of the house (facade outer face z=0, inner face z=-0.15).
Score mapping: the dog's body centre stands at world z = x_score - 0.34 on the line x = 0 (straight at the door)."""
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(OUT, '../../..'))
SCORE = json.load(open(os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')))
FPS = 24
W, H = 1280, 720
SS = 2                      # supersampling for the render
Z_OFF = -0.34               # world z = x_score + Z_OFF
DOOR_HW, DOOR_H, WALL_T = 0.46, 2.05, 0.15

# ---------------------------------------------------------------- camera (static)
CAM = np.array([3.9, 1.5, 5.9])
LOOK = np.array([-0.25, 0.75, 1.9])
FOCAL = 1300.0              # px at 1x


def cam_basis():
    w = LOOK - CAM; w = w / np.linalg.norm(w)
    u = np.cross(w, [0, 1, 0]); u = u / np.linalg.norm(u)
    v = np.cross(u, w)
    return u, v, w


U, V, Wd = cam_basis()

# camera keys: wide while the dog refuses and waits; a slow push toward the door over the approach
CAM_KEYS = [(0.0, (3.9, 1.5, 5.9), (-0.25, 0.75, 1.9), 1300.0),
            (15.2, (3.9, 1.5, 5.9), (-0.25, 0.75, 1.9), 1300.0),
            (23.6, (2.5, 1.25, 2.9), (-0.15, 0.35, 0.1), 1250.0)]


def cam_at(t):
    ks = CAM_KEYS
    if t <= ks[0][0]:
        k = ks[0]; return np.array(k[1]), np.array(k[2]), k[3]
    for a, b in zip(ks, ks[1:]):
        if t <= b[0]:
            u = smooth(a[0], b[0], t)
            return lerp(np.array(a[1]), np.array(b[1]), u), lerp(np.array(a[2]), np.array(b[2]), u), lerp(a[3], b[3], u)
    k = ks[-1]; return np.array(k[1]), np.array(k[2]), k[3]


def set_camera(t):
    global CAM, LOOK, FOCAL, U, V, Wd
    CAM, LOOK, FOCAL = cam_at(t)
    U, V, Wd = cam_basis()
    return (round(float(CAM[0]), 4), round(float(CAM[1]), 4), round(float(CAM[2]), 4), round(float(LOOK[0]), 4), round(float(LOOK[1]), 4), round(float(LOOK[2]), 4), round(float(FOCAL), 2))


def project(p, ss=1):
    q = np.asarray(p, float) - CAM
    d = q @ Wd
    return np.stack([(W / 2 + FOCAL * (q @ U) / d) * ss, (H / 2 - FOCAL * (q @ V) / d) * ss, d], -1)


def rays(ss=SS):
    ys, xs = np.mgrid[0:H * ss, 0:W * ss].astype(np.float32)
    px = (xs + .5) / ss - W / 2; py = H / 2 - (ys + .5) / ss
    d = U[None, None] * px[..., None] / FOCAL + V[None, None] * py[..., None] / FOCAL + Wd[None, None]
    return (d / np.linalg.norm(d, axis=-1, keepdims=True)).astype(np.float32)


def smooth(a, b, t):
    t = np.clip((t - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- spheres
class Body:
    def __init__(self):
        self.c = []; self.r = []; self.part = []; self.R = []

    def add(self, c, r, part, R):
        self.c.append(np.asarray(c, float)); self.r.append(float(r)); self.part.append(part); self.R.append(R)

    def chain(self, a, b, r0, r1, n, part, R, end=True):
        for k in range(n):
            t = k / (n - 1 if end else n)
            self.add(lerp(np.asarray(a, float), np.asarray(b, float), t), lerp(r0, r1, t), part, R)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def align(a, b):
    """minimal rotation taking unit vector a to unit vector b"""
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b)
    if c < -0.999:
        return -np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def ik2(root, target, l1, l2, bend):
    """two-bone IK in the local x-y plane (z carried linearly). bend=+1 joint toward +x, -1 toward -x"""
    d = target - root; L = np.linalg.norm(d[:2]); L = min(max(L, 1e-4), l1 + l2 - 1e-4)
    a = math.atan2(d[1], d[0])
    cosb = (l1 * l1 + L * L - l2 * l2) / (2 * l1 * L); cosb = max(-1, min(1, cosb))
    b = math.acos(cosb)
    # choose sign so the joint sits toward the bend side
    cand = [a + b, a - b]
    js = [root[:2] + l1 * np.array([math.cos(x), math.sin(x)]) for x in cand]
    j = max(js, key=lambda p: bend * (p[0] - (root[0] + target[0]) / 2))
    jz = root[2] + (target[2] - root[2]) * 0.5
    return np.array([j[0], j[1], jz])


# ---------------------------------------------------------------- the dog
def dog_local(P):
    """Build the dog in its own local frame (x forward, y up, z left) from pose dict P. Returns Body with part-local R."""
    B = Body(); I = np.eye(3)
    lie, cr = P['lie'], P['crouch']
    hh = lerp(0.47 - 0.10 * cr, 0.19, lie); sh = lerp(0.50 - 0.06 * cr, 0.21, lie)
    Hp = np.array([-0.28, hh, 0.]); Sp = np.array([0.22, sh, 0.])
    # torso
    prof_r = [0.112, 0.118, 0.12, 0.122, 0.128, 0.138, 0.146, 0.15]
    prof_y = [0.0, -0.004, -0.008, -0.014, -0.024, -0.036, -0.046, -0.05]
    for k in range(15):
        t = k / 14; c = lerp(Hp, Sp, t) + [0, float(np.interp(t * 7, range(8), prof_y)), 0]
        B.add(c, float(np.interp(t * 7, range(8), prof_r)), 'torso', I)
    B.add(Sp + [-0.03, -0.085, 0], 0.115, 'torso', I)
    B.add(Sp + [0.05, -0.03, 0], 0.12, 'torso', I)
    # neck and head
    hy = P['head_yaw']
    th = math.radians(P['neck'])
    Ry = rot_y(hy)
    Nb = Sp + np.array([0.07, 0.05, 0])
    nd = Ry @ np.array([math.cos(th), math.sin(th), 0])
    nlen = P.get('neck_len', 0.21)
    Rn = Ry @ rot_z(th - math.radians(40))
    for k in range(7):
        B.add(Nb + nd * nlen * k / 6, lerp(0.092, 0.078, k / 6), 'neck', Rn)
    Hc = Nb + nd * nlen + Ry @ np.array([0.0, 0.03, 0])
    phi = math.radians(P['muzzle'])
    Rh = Ry @ rot_z(phi)
    md = Rh @ np.array([1, 0, 0]); up = Rh @ np.array([0, 1, 0]); side = Rh @ np.array([0, 0, 1])
    B.add(Hc, 0.088, 'head', Rh)
    B.add(Hc - md * 0.03 + up * 0.01, 0.082, 'head', Rh)
    for k in range(4):
        B.add(Hc + md * (0.06 + 0.035 * k) - up * (0.025 + 0.004 * k), lerp(0.058, 0.04, k / 3), 'muzzle', Rh)
    B.add(Hc + md * 0.19 - up * 0.032, 0.027, 'nose', Rh)
    for s in (1, -1):
        B.add(Hc + md * 0.055 + side * s * 0.045 + up * 0.03, 0.021, 'eye', Rh)
    # ears: pricked (ear=1) up and a bit forward; flat (0) laid back
    e = P['ear']
    for s in (1, -1):
        base = Hc + side * s * 0.05 + up * 0.055 - md * 0.02
        ed = lerp(-md * 0.85 + up * 0.25 + side * s * 0.3, up * 0.95 + md * 0.15 + side * s * 0.15, e)
        ed = ed / np.linalg.norm(ed)
        for k in range(7):
            B.add(base + ed * 0.016 * k, lerp(0.04, 0.012, k / 6), 'ear', Rh)
    # tail
    ta = math.radians(48 - 100 * P['tail']); wag = P['wag'] * math.radians(32) * math.sin(P['t'] * 11)
    tb = Hp + np.array([-0.11, 0.03, 0])
    Rt = rot_y(wag)
    prev = tb
    for k in range(14):
        a = ta - 0.06 * k * (1 if P['tail'] < 0.9 else -1)
        dvec = Rt @ np.array([-math.cos(a), math.sin(a), 0])
        if P['tail'] > 1.0:  # tucked: drops, then curls forward under the belly between the hind legs
            a2 = math.radians(-70) - 0.16 * k
            dvec = Rt @ np.array([-math.cos(a2), math.sin(a2), 0])
        c = prev + dvec * 0.025; prev = c
        B.add(c, lerp(0.042, 0.016, k / 13), 'tail', I)
    # legs
    for front in (True, False):
        for s in (1, -1):
            root = (Sp + [0.0, -0.04, s * 0.075]) if front else (Hp + [0.02, -0.03, s * 0.08])
            l1, l2 = (0.25, 0.25) if front else (0.27, 0.26)
            foot = P['feet'][('F' if front else 'H') + ('L' if s > 0 else 'R')]
            foot = np.array(foot, float)
            jt = ik2(root, foot, l1, l2, -1 if front else 1)
            if not front and lie > 0:   # lying: the thigh lies flat along the flank, knee forward, hock back on the floor
                kl = smooth(0.2, 0.95, lie)
                jt = lerp(jt, np.array([Hp[0] + 0.21, 0.10, s * 0.14]), kl)
            R1 = align(np.array([0, -1., 0]), jt - root); R2 = align(np.array([0, -1., 0]), foot - jt)
            B.chain(root, jt, 0.06 if front else 0.07, 0.045, 12, 'leg', R1, end=False)
            B.chain(jt, foot, 0.043, 0.031, 12, 'leg', R2, end=False)
            fwd = np.array([1., 0, 0])
            B.add(foot + [0.02, 0.005, 0], 0.037, 'paw', I)
            B.add(foot + fwd * 0.045 + [0, -0.002, 0], 0.03, 'paw', I)
    return B


def feet_for(P, walk):
    """foot targets in local frame. walk = signed distance travelled forward (m). Trot: diagonal pairs."""
    lie = P['lie']; cr = P['crouch']
    stride = 0.55; ph = 2 * math.pi * walk / stride
    feet = {}
    for key, x0, z0, off in (('FL', 0.25, 0.085, 0), ('HR', -0.27, -0.085, 0), ('FR', 0.25, -0.085, math.pi), ('HL', -0.27, 0.085, math.pi)):
        p = (ph + off) % (2 * math.pi)
        amp = P['moving']
        if p < math.pi:      # stance: foot slides back in the body frame, still on the ground in the world
            dx = 0.1375 - 0.275 * (p / math.pi); dy = 0
        else:
            q = (p - math.pi) / math.pi
            dx = -0.1375 + 0.275 * q; dy = 0.07 * math.sin(math.pi * q)
        stand = np.array([x0 + dx * amp, 0.035 + dy * amp, z0])
        if key[0] == 'F':
            lyp = np.array([0.52, 0.035, z0 * 0.9])
        else:
            lyp = np.array([-0.31, 0.04, z0 * 1.75])
        feet[key] = lerp(stand, lyp, smooth(0.15, 0.95, lie)) if lie > 0 else stand
        if cr > 0 and lie < 0.5:
            feet[key][0] += (-0.03 if key[0] == 'H' else 0.04) * cr
    return feet


def dog_world(P):
    B = dog_local(P)
    a = P['yaw']
    h = np.array([math.sin(a), 0, -math.cos(a)]); left = np.cross(h, [0, 1, 0])
    # local x->h, y->up, z->left ; build matrix with columns
    Rw = np.stack([h, [0, 1, 0], left], 1)
    pos = np.array([0.0, 0.0, P['z']])
    C = np.array([pos + Rw @ c for c in B.c])
    Rs = [Rw @ R for R in B.R]
    return C, np.array(B.r), B.part, Rs, Rw


# ---------------------------------------------------------------- the person
def person_world(Q):
    """A plain body of spheres; its coat and hand carry substituted images (person, hands classes)."""
    B = Body(); I = np.eye(3)
    sit = Q['sit']; lean = Q['lean']; reach = Q['reach']; low = Q['low']
    # local: x forward, y up, z left
    pel_h = lerp(0.95, 0.20, sit)
    pel = np.array([lerp(0, -0.05, sit), pel_h, 0])
    tdir = np.array([math.sin(lean), math.cos(lean), 0])
    tdir = lerp(tdir, np.array([-0.25, 0.97, 0]), sit * 0.6); tdir /= np.linalg.norm(tdir)
    neck = pel + tdir * 0.58
    for k in range(12):
        B.add(pel + tdir * 0.58 * k / 11, lerp(0.17, 0.15, k / 11), 'pcoat', I)
    B.add(pel + tdir * 0.12 + [0.02, 0, 0], 0.19, 'pcoat', I)
    hd = neck + tdir * 0.19 + np.array([0.03 + 0.06 * Q['bow'], -0.05 * Q['bow'], 0])
    B.add(neck + tdir * 0.06, 0.06, 'skin', I)
    B.add(hd, 0.11, 'phead', I)
    B.add(hd + [-0.03, 0.03, 0], 0.105, 'phead', I)
    # legs
    for s in (1, -1):
        hip = pel + [0, -0.03, s * 0.1]
        if sit > 0.01:
            knee_s = hip + [0.42, 0.28, s * 0.03]; foot_s = hip + [0.62, -0.17, s * 0.06]
        else:
            knee_s = foot_s = None
        ph = Q['walk'] * 2 * math.pi / 1.3 + (0 if s > 0 else math.pi)
        sw = 0.22 * math.sin(ph) * Q['moving']
        knee_w = hip + [sw * 0.5 + 0.03, -0.45, 0]; foot_w = hip + [sw, -0.90 + 0.06 * max(0, math.cos(ph)) * Q['moving'], 0]
        if sit > 0.01:
            knee = lerp(knee_w, knee_s, sit); foot = lerp(foot_w, foot_s, sit)
        else:
            knee, foot = knee_w, foot_w
        B.chain(hip, knee, 0.09, 0.075, 8, 'pleg', I)
        B.chain(knee, foot, 0.07, 0.055, 8, 'pleg', I)
        B.add(foot + [0.07, -0.02, 0], 0.055, 'pshoe', I)
    # arms: s=+1 left (far), s=-1 right (the reaching / offering arm)
    for s in (1, -1):
        sh = neck + [0, -0.05, s * 0.19]
        if s == -1:
            hand_rest = sh + [0.05, -0.55, -0.03]
            hand_reach = sh + [0.58, -0.25, 0.05]
            hand_low = pel + [0.62, -0.08 if sit > 0.5 else -0.5, -0.05]
            hand_beck = sh + [0.35, 0.08, -0.02]
            hand = hand_rest
            hand = lerp(hand, hand_beck, Q['beckon'])
            hand = lerp(hand, hand_reach, reach)
            hand = lerp(hand, hand_low, low)
        else:
            hand = sh + [0.02 + 0.15 * sit, -0.52 + 0.2 * sit, 0.05]
        el = lerp(sh, hand, 0.5) + [-0.04, -0.05, 0]
        B.chain(sh, el, 0.07, 0.06, 7, 'pcoat', I)
        B.chain(el, hand, 0.055, 0.045, 7, 'pcoat', I)
        B.add(hand + [0.03, 0, 0], 0.05, 'hand' if s == -1 else 'skin', I)
        if s == -1:
            B.add(hand + [0.08, -0.005, 0], 0.04, 'hand', I)
    b = Q['yaw']
    h = np.array([math.sin(b), 0, math.cos(b)]); left = np.cross(h, [0, 1, 0]) * -1
    Rw = np.stack([h, [0, 1, 0], left], 1)
    pos = np.array([Q['x'], 0, Q['z']])
    C = np.array([pos + Rw @ c for c in B.c])
    return C, np.array(B.r), B.part, [Rw for _ in B.c], Rw, pos + Rw @ hd
