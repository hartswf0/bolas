"""Monsieur Ripois / « Rien n'y manquait » -- U3 SHADOW THEATRE (flashback E2, S2a-S2d).

SCION #2 (Reiniger articulated shadow theatre), with #32 FK / 2-bone IK, #41 secondary dynamics
(earring pendulum), #44 multiplane (blinds far plane at 0.3x the set's travel, rail 1.3x),
#45 occlusion (the box swallowed in the torso silhouette).

render_flashback(t) -> PIL.Image 720x540 RGB, t = S2 local seconds in [0, 10.5) (film 9.0-19.5 s,
film frame = local frame + 216).  Everything drawn here is HANDMADE card: jointed puppets cut
as polygons, pinned at joints (pin rivets punched as pinholes of light), posed by FK from an
exposure sheet on twos; only the far plane is FORAGED (window blinds of LoC 2017831564, PD).

Coordinates: screen px, y down; 'plane' x = screen x - m(f) (m = set travel, the camera follows R.).
Angles: degrees, clockwise positive (y-down rotation). Rest pose = limbs hanging straight down.
"""
import math, json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/"
W, H, S = 720, 540, 3
FPS, NF = 24, 252
FLOOR = 478.0
INK = np.array([28, 23, 19], np.float32)                     # #1c1713
FONT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"

# ---------------------------------------------------------------- box spec (shared with U2)
try:
    BOXSPEC = json.load(open(os.path.join(HERE, "box-spec.json")))
except Exception:
    BOXSPEC = {"depth": 0.62, "body_h": 0.30, "lid_h": 0.08, "slot": {"cx": 0.5},
               "lid_states_deg": {"closed": 0, "33": 35, "66": 70, "100": 105}}
BW = 72.0                                   # box width on screen (theatrical scale, see sheet)
BODY_H, LID_H, DEPTH = BOXSPEC["body_h"] * BW, BOXSPEC["lid_h"] * BW, BOXSPEC["depth"] * BW
SLOT_CX = BOXSPEC["slot"]["cx"]
LID_DRAW = [BOXSPEC["lid_states_deg"][k] for k in ("closed", "33", "66", "100")]
RING_D = 0.20 * BW                           # spec 0.11w enlarged x1.8 for silhouette legibility
RING_BAND = 0.045 * BW
PRESENT_SLOT_SCREEN = (370.0, 304.0)         # present insert slot centre (U2 slot_screen_insert), norm_x 0.484

# ---------------------------------------------------------------- small geometry
def R(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s], [s, c]])

def sm(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)

def lerp(a, b, x): return a + (b - a) * x

def taper(L, w0, w1, cap0=None):
    """limb piece hanging down from its pivot: tapered card with a rounded cap at the pivot"""
    pts = [(-w0, 0), (-w1, L), (w1, L), (w0, 0)]
    return pts, (cap0 if cap0 else w0)

def circ(cx, cy, r, n=18):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]

def norm180(a):
    a = (a + 180) % 360 - 180
    return a

# ---------------------------------------------------------------- R. (the visitor), facing LEFT
R_JACKET = [(-6, -118), (-16, -113), (-22, -106), (-25, -97), (-29, -91), (-21, -88), (-27, -83), (-29, -72),
            (-28, -58), (-24, -44), (-22, -32), (-24, -14), (-26, 6), (-27, 22), (-12, 24), (-3, 19), (5, 24),
            (25, 23), (23, 6), (20, -14), (18, -32), (20, -52), (23, -74), (25, -92), (23, -104), (16, -112), (6, -118)]
# replacement torso: turned 3/4, back toward the aunt (used only around the swallow)
R_JACKET34 = [(-4, -118), (-18, -115), (-30, -109), (-38, -98), (-41, -80), (-40, -60), (-37, -40), (-36, -14),
              (-38, 22), (-12, 25), (-2, 20), (8, 25), (42, 22), (43, 0), (44, -30), (46, -60), (46, -86),
              (42, -102), (32, -112), (16, -118)]
R_HEAD = [(7, 4), (8, -10), (11, -18), (16, -28), (17, -40), (14, -50), (8, -57), (2, -61), (-6, -66), (-14, -68),
          (-21, -65), (-25, -59), (-19, -61), (-15, -57), (-15, -49), (-17, -44), (-18, -41), (-25, -34), (-18, -31),
          (-19, -28), (-16, -26.5), (-18, -24.5), (-17, -20), (-13, -16), (-8, -13), (-7, 4)]
R_HAND = [(5, 0), (6, 10), (6, 19), (4, 27), (1, 29), (-2, 26), (-4, 18), (-5, 13), (-9, 17), (-12, 16),
          (-11, 11), (-6, 5), (-5, 0)]
R_FOOT = [(-6, -3), (7, -3), (9, 4), (8, 10), (-4, 10), (-20, 10), (-27, 8), (-28, 4), (-20, 1)]
R_UPPER, R_FORE, R_THIGH, R_SHIN = 62.0, 56.0, 90.0, 86.0
R_SHOULDER = {"profile": {"near": (-4, -104), "far": (6, -104)}, "34": {"near": (-12, -104), "far": (22, -104)}}
R_NECK = (-3, -116)
LIMITS_R = {"torso": (-12, 8), "neck": (-20, 20),
            "n_sh": (-40, 150), "n_el": (0, 150), "n_wr": (-80, 80),
            "f_sh": (-42, -22), "f_el": (55, 100), "f_wr": (-50, 10),
            "hipA": (-30, 35), "hipB": (-30, 35), "kneeA": (-75, 0), "kneeB": (-75, 0),
            "ankA": (-30, 20), "ankB": (-30, 20)}

# ---------------------------------------------------------------- the aunt, seated, facing RIGHT
A_BODICE = [(-16, 4), (18, 4), (16, -20), (14, -40), (20, -60), (24, -76), (20, -90), (10, -98), (-6, -98),
            (-16, -90), (-20, -70), (-14, -44), (-18, -20)]
A_SKIRT = [(-22, 0), (-18, -8), (20, -10), (80, -12), (98, -8), (104, 4), (104, 24), (102, 60), (106, 72),
           (60, 74), (58, 30), (40, 16), (-20, 14)]
A_SHINS = [(86, 70), (100, 70), (99, 86), (102, 88), (116, 90), (118, 94), (86, 94)]
A_HEAD_UP = [(-6, 3), (6, 3), (7, -10), (10, -14), (13, -20), (13, -24), (17, -28), (16, -31), (19, -34), (17, -36),
             (16, -40), (18, -44), (15, -52), (10, -58), (2, -61), (-6, -60), (-12, -55), (-14, -46), (-12, -36),
             (-8, -26), (-6, -12)]
# replacement profile "looking down at the box": chin tucked, lips parted (a different drawing, not a rotation only)
A_HEAD_DOWN = [(-6, 3), (6, 3), (8, -8), (12, -12), (15, -15), (14, -19), (17, -21), (15, -23.5), (17.5, -25),
               (19, -29), (17, -33), (20, -36), (17, -38), (16, -42), (16, -47), (12, -55), (4, -60), (-5, -60),
               (-12, -55), (-14, -46), (-12, -36), (-8, -26), (-6, -12)]
A_CHIGNON = [(-16, -46, 9.5), (-12, -58, 6.0)]
A_EARLOBE = (1, -30)
A_HAND = [(-4, 0), (4, 0), (6, 7), (11, 11), (13, 15), (10, 16), (5, 13), (5, 19), (4, 26), (2, 27), (1, 21),
          (-1, 27), (-3, 27), (-3, 21), (-5, 25), (-7, 24), (-5, 14)]
A_UPPER, A_FORE = 50.0, 46.0
A_SHOULDER, A_NECK = (2, -90), (4, -98)
LIMITS_A = {"torso": (-6, 16), "neck": (-15, 25), "sh": (-160, 40), "el": (-155, 0), "wr": (-80, 80)}

# ---------------------------------------------------------------- 2-bone IK (#32 FK hierarchy, analytic IK)
def ik2(S, T, L1, L2, bend):
    """returns (dir_upper, dir_fore) screen angles; bend=+1 elbow on clockwise side"""
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = max(1e-3, min(L1 + L2 - 1e-3, math.hypot(dx, dy)))
    base = math.degrees(math.atan2(dy, dx))
    a = math.degrees(math.acos(max(-1, min(1, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)))))
    du = base - bend * a
    e = math.radians(du)
    E = (S[0] + L1 * math.cos(e), S[1] + L1 * math.sin(e))
    df = math.degrees(math.atan2(T[1] - E[1], T[0] - E[0]))
    return du, df

# ---------------------------------------------------------------- exposure sheet (timing on twos)
# local frames (0..251) ; film frame = local + 216
F_DOOR = [(0, "D1 closed"), (6, "D2 ajar"), (12, "D3 open")]
F_WALK0, F_WALK1 = 18, 50                   # 2 cycles x 8 poses on twos = 32 frames, 4 contacts
WALK = [  # (name, legA (hip, knee, ankle), legB, stance)
    ("W1 contact A", (13, -2, 8), (-12, -6, -12), "A"),
    ("W2 down A", (9, -16, 2), (-7, -34, -20), "A"),
    ("W3 pass A", (1, -4, 0), (8, -56, 4), "A"),
    ("W4 up A", (-8, -2, -8), (15, -28, 6), "A"),
    ("W5 contact B", (-12, -6, -12), (13, -2, 8), "B"),
    ("W6 down B", (-7, -34, -20), (9, -16, 2), "B"),
    ("W7 pass B", (8, -56, 4), (1, -4, 0), "B"),
    ("W8 up B", (15, -28, 6), (-8, -2, -8), "B"),
]
STAND = ("ST stand", (3, -2, 0), (-3, -2, 0))
F_OFFER = [(72, "O1 carry"), (82, "O2 lift"), (94, "O3 extend"), (106, "O4 reach (overshoot)"),
           (116, "O5 settle"), (126, "O6 present")]
F_LID = [(132, "L1 lid 0"), (144, "L2 lid 35"), (152, "L3 lid 70"), (160, "L4 lid 105")]
F_SWALLOW = (190, 197)                      # box inside his torso silhouette, on ones
F_HANDOFF = 214
F_SETDOWN = 240

def f2(f):
    """on twos, except the swallow which is shot on ones"""
    if 184 <= f <= 199: return f
    return f - f % 2

# ---- the walk: contact-plane solver (stance ankle pinned, lowest sole on the floor rail)
def _leg_points(root, hip, knee, ank, side):
    """FK of a leg from the pelvis root; returns joint positions and sole points"""
    hp = np.array(root) + np.array([0 if side == "A" else 4, 4])
    k = hp + R(hip) @ np.array([0, R_THIGH])
    a = k + R(hip + knee) @ np.array([0, R_SHIN])
    sole = [a + R(hip + knee + ank) @ np.array(p) for p in R_FOOT]
    return hp, k, a, sole

def _walk_roots():
    seq = []
    for i in range((F_WALK1 - F_WALK0) // 2):
        seq.append(WALK[i % 8])
    seq.append(("ST stand",) + STAND[1:] + ("A",))
    roots = []
    x = 655.0
    pin = None
    prev_stance = None
    for i, (name, A, B, st) in enumerate(seq):
        # height: lowest sole point on the floor
        def height(rootx):
            pts = _leg_points((rootx, 0), *A, "A")[3] + _leg_points((rootx, 0), *B, "B")[3]
            return FLOOR - max(p[1] for p in pts)
        if pin is None:
            y = height(x); _, _, aA, _ = _leg_points((x, y), *A, "A"); pin = ("A", aA[0])
        old = prev_stance if (prev_stance and prev_stance != st) else st
        leg = A if old == "A" else B
        _, _, a0, _ = _leg_points((0, 0), *leg, old)
        x = pin[1] - a0[0]
        y = height(x)
        if old != st or pin[0] != st:
            _, _, an, _ = _leg_points((x, y), *(A if st == "A" else B), st)
            pin = (st, an[0])
        roots.append((name, (x, y), A, B, st))
        prev_stance = st
    return roots
WALK_ROOTS = _walk_roots()
ROOT_END = WALK_ROOTS[-1][1]

# layout derived from where the walk ends (the set is built around him)
BOX_OFFER = (ROOT_END[0] - 92.0, ROOT_END[1] - 6.0)        # box bottom-centre (plane) when presented
AUNT_ROOT = (BOX_OFFER[0] - 104.0, 392.0)                    # her hip on the seat (plane)
LAP_Y = AUNT_ROOT[1] - 10.0
BOX_LAP = (AUNT_ROOT[0] + 66.0, LAP_Y)
M_END = PRESENT_SLOT_SCREEN[0] - BOX_OFFER[0]                # ring lands on the present slot's screen x

def m_of(f):
    """set travel (camera follows R. leftwards): main plane offset in px"""
    return M_END * sm((f2(f) - 14) / 60.0)

def walk_state(f):
    if f < F_WALK0:
        name, root, A, B, st = WALK_ROOTS[0]
        return "ST in doorway", (root[0] + 4, root[1]), STAND[1], STAND[2]
    i = min(len(WALK_ROOTS) - 1, (f - F_WALK0) // 2)
    name, root, A, B, st = WALK_ROOTS[i]
    return name, root, A, B

def key_interp(keys, f):
    """keys: list of (frame, value(s)); smoothstep between keys"""
    if f <= keys[0][0]: return keys[0][1]
    for (fa, va), (fb, vb) in zip(keys, keys[1:]):
        if f <= fb:
            x = sm((f - fa) / float(fb - fa))
            if isinstance(va, tuple): return tuple(lerp(a, b, x) for a, b in zip(va, vb))
            return lerp(va, vb, x)
    return keys[-1][1]

def chest_point(root):                                         # where the box hides (inside torso34)
    return (root[0] + 2.0, root[1] - 46.0)

def box_track(f, root):
    """box bottom-centre (plane coords), holder, lid angle; on twos (ones in the swallow)"""
    g = f2(f)
    carry = (root[0] - 44.0, root[1] - 40.0)
    if g < 72:
        return carry, "him", 0.0
    if g < 132:
        k = [(72, carry), (82, (carry[0] - 10, carry[1] - 16)), (94, (BOX_OFFER[0] + 22, BOX_OFFER[1] - 8)),
             (106, (BOX_OFFER[0] - 5, BOX_OFFER[1] - 3)), (116, (BOX_OFFER[0] + 2, BOX_OFFER[1] + 1)),
             (126, BOX_OFFER)]
        return key_interp(k, g), "him", 0.0
    if g < 184:
        lid = LID_DRAW[0]
        for i, (fa, nm) in enumerate(F_LID):
            if g >= fa: lid = LID_DRAW[i]
        return BOX_OFFER, "him", float(lid)
    C = chest_point(root)
    if g < 198:
        pos = key_interp([(184, BOX_OFFER), (190, C)], g)
        lid = LID_DRAW[3] if g < 190 else LID_DRAW[3] * (1 - sm((g - 190) / 7.0))
        return pos, "him", float(lid)
    PH = (AUNT_ROOT[0] + 92.0, AUNT_ROOT[1] - 64.0)
    if g < F_HANDOFF:
        return key_interp([(198, C), (204, (C[0] - 40, C[1] + 6)), (F_HANDOFF, PH)], g), "him", 0.0
    if g < F_SETDOWN:
        x = (g - F_HANDOFF) / float(F_SETDOWN - F_HANDOFF)
        e = x * x * (0.6 + 0.4 * x)                               # ease-in: the weight accelerates onto the lap
        return (lerp(PH[0], BOX_LAP[0], sm(x)), lerp(PH[1], BOX_LAP[1], e)), "her", 0.0
    return BOX_LAP, "her", 0.0

# ---------------------------------------------------------------- poses
def pose_R(f):
    g = f2(f)
    wname, root, A, B = walk_state(g)
    P = {"walk": wname, "root": root, "legA": A, "legB": B}
    sw = 0.0
    if F_WALK0 <= g < F_WALK1:
        sw = 1.0
    P["torso34"] = 188 <= g <= 199
    lean = -3.0 * sw
    lean = lean + key_interp([(72, 0.0), (94, -4.0), (106, -7.0), (126, -5.0), (184, -5.0), (190, 2.0),
                              (198, 2.0), (212, -6.0), (226, -2.0)], g) if g >= 72 else lean
    P["torso"] = lean
    P["neck"] = key_interp([(0, 0.0), (60, 0.0), (72, -4.0), (106, -12.0), (140, -10.0), (184, -10.0),
                            (190, 4.0), (198, 4.0), (212, -8.0), (240, -6.0)], g)
    # far arm behind the back: only the elbow moves, +6 deg during the swallow (the hidden hand meets the box)
    fsh = -36.0 + 6.0 * sm((g - 190) / 7.0) * (1 - sm((g - 200) / 8.0))
    P["f_sh"], P["f_el"], P["f_wr"] = fsh, 72.0 + 14.0 * sm((g - 190) / 7.0) * (1 - sm((g - 200) / 8.0)), -22.0
    return P

def pose_A(f):
    g = f2(f)
    P = {}
    P["torso"] = key_interp([(0, 0.0), (104, 0.0), (124, 8.0), (180, 8.0), (188, 2.0), (204, 4.0), (214, 10.0),
                             (240, 6.0), (252, 6.0)], g)
    P["head"] = "down" if (128 <= g < 206 or g >= 222) else "up"
    P["neck"] = key_interp([(0, 0.0), (120, 4.0), (128, 10.0), (180, 12.0), (206, 2.0), (222, 12.0), (240, 16.0)], g)
    return P

# ---------------------------------------------------------------- rig evaluation (FK)
class Rig:
    def __init__(self):
        self.pieces = []    # (name, world polygon, layer)
        self.joints = {}    # name -> (world point, parent piece, child piece)
        self.angles = {}
    def add(self, name, M, t, pts):
        self.pieces.append((name, [tuple(t + M @ np.array(p, float)) for p in pts]))
    def joint(self, name, pt, parent, child):
        self.joints[name] = (tuple(pt), parent, child)

def build_R(f, box_pos):
    P = pose_R(f)
    rg = Rig(); rg.angles = {}
    root = np.array(P["root"], float)
    tor = P["torso"]; rg.angles["torso"] = tor
    Mt = R(tor)
    jk = "34" if P["torso34"] else "profile"
    jacket = R_JACKET34 if P["torso34"] else R_JACKET
    # legs (children of the pelvis root, not of the torso)
    for side, leg in (("B", P["legB"]), ("A", P["legA"])):
        hip, knee, ank = leg
        hp, k, a, sole = _leg_points(root, hip, knee, ank, side)
        th, th_c = taper(R_THIGH, 12, 9)
        rg.add("thigh" + side, R(hip), hp, th + circ(0, 0, 12)[:0]); rg.pieces.append(("thighcap" + side, circ(hp[0], hp[1], 12)))
        rg.add("shin" + side, R(hip + knee), k, [(-9, 0), (-6.5, 80), (-8, R_SHIN), (8, R_SHIN), (6.5, 80), (9, 0)])
        rg.pieces.append(("kneecap" + side, circ(k[0], k[1], 9)))
        rg.add("foot" + side, R(hip + knee + ank), a, R_FOOT)
        rg.joint("hip" + side, hp, "torso", "thigh" + side); rg.joint("knee" + side, k, "thigh" + side, "shin" + side)
        rg.joint("ankle" + side, a, "shin" + side, "foot" + side)
        rg.angles["hip" + side], rg.angles["knee" + side], rg.angles["ank" + side] = hip, knee, ank
    rg.add("torso", Mt, root, jacket)
    # far arm (behind the back) -- drawn BEHIND the torso; its hand must stay inside the torso silhouette
    sb = root + Mt @ np.array(R_SHOULDER[jk]["far"], float)
    du = 90 + tor + P["f_sh"]; df = du + P["f_el"]; dh = df + P["f_wr"]
    elb = sb + np.array([math.cos(math.radians(du)), math.sin(math.radians(du))]) * R_UPPER
    wr = elb + np.array([math.cos(math.radians(df)), math.sin(math.radians(df))]) * R_FORE
    rg.add("f_upper", R(du - 90), sb, taper(R_UPPER, 8, 6.5)[0]); rg.pieces.append(("f_elbowcap", circ(elb[0], elb[1], 6.5)))
    rg.add("f_fore", R(df - 90), elb, taper(R_FORE, 6.5, 4.8)[0])
    rg.add("far_hand", R(dh - 90), wr, [(x * 0.9, y * 0.75) for x, y in R_HAND])
    rg.joint("f_shoulder", sb, "torso", "f_upper"); rg.joint("f_elbow", elb, "f_upper", "f_fore"); rg.joint("f_wrist", wr, "f_fore", "far_hand")
    rg.angles.update(f_sh=P["f_sh"], f_el=P["f_el"], f_wr=P["f_wr"])
    # head
    nk = root + Mt @ np.array(R_NECK, float)
    rg.add("head", R(tor + P["neck"]), nk, R_HEAD); rg.joint("neck", nk, "torso", "head"); rg.angles["neck"] = P["neck"]
    # near arm: IK to the box grip (hand under the box, thumb against its front), or a hanging rest
    sn = root + Mt @ np.array(R_SHOULDER[jk]["near"], float)
    holder = box_pos[1]
    if holder == "him":
        bp = box_pos[0]
        T = (bp[0] + 0.30 * BW, bp[1] + 4.0)
        hand_dir = 180.0
    else:
        g = f2(f)
        x = sm((g - F_HANDOFF) / 14.0)
        PH = (AUNT_ROOT[0] + 92.0 + 0.30 * BW, AUNT_ROOT[1] - 60.0)
        rest = (root[0] - 14.0, root[1] + 8.0)
        T = (lerp(PH[0], rest[0], x), lerp(PH[1], rest[1], x)); hand_dir = lerp(180.0, 100.0, x)
    du, df = ik2(sn, T, R_UPPER, R_FORE, bend=-1)
    s_rel = norm180(du - 90 - tor); e_rel = norm180(df - du)
    if e_rel < 0:                                            # pick the elbow-down solution
        du, df = ik2(sn, T, R_UPPER, R_FORE, bend=+1); s_rel = norm180(du - 90 - tor); e_rel = norm180(df - du)
    w_rel = max(LIMITS_R["n_wr"][0], min(LIMITS_R["n_wr"][1], norm180(hand_dir - df)))
    el = sn + np.array([math.cos(math.radians(du)), math.sin(math.radians(du))]) * R_UPPER
    wrn = el + np.array([math.cos(math.radians(df)), math.sin(math.radians(df))]) * R_FORE
    rg.add("n_upper", R(du - 90), sn, taper(R_UPPER, 9.5, 7)[0]); rg.pieces.append(("n_shouldercap", circ(sn[0], sn[1], 9.5)))
    rg.pieces.append(("n_elbowcap", circ(el[0], el[1], 7)))
    rg.add("n_fore", R(df - 90), el, [(-7, 0), (-5, 50), (-6, R_FORE), (6, R_FORE), (5, 50), (7, 0)])
    # hand: rest drawing has fingers down, thumb forward; for the grip rotate so fingers point along hand_dir
    rg.add("near_hand", R(df + w_rel - 90), wrn, R_HAND)
    rg.joint("n_shoulder", sn, "torso", "n_upper"); rg.joint("n_elbow", el, "n_upper", "n_fore"); rg.joint("n_wrist", wrn, "n_fore", "near_hand")
    rg.angles.update(n_sh=s_rel, n_el=e_rel, n_wr=w_rel)
    rg.info = {"root": tuple(root), "elbow_far": tuple(elb), "far_wrist": tuple(wr), "near_target": T,
               "near_reach_err": float(np.hypot(*(wrn - np.array(T)))), "torso_drawing": "34" if P["torso34"] else "profile",
               "walk": P["walk"]}
    return rg

def build_A(f, box_pos, ear_angle):
    P = pose_A(f)
    rg = Rig()
    root = np.array(AUNT_ROOT, float)
    tor = P["torso"]; Mt = R(tor)
    rg.add("skirt", np.eye(2), root, A_SKIRT); rg.add("shins", np.eye(2), root, A_SHINS)
    rg.add("torso", Mt, root, A_BODICE)
    rg.joint("waist", root, "skirt", "torso")
    nk = root + Mt @ np.array(A_NECK, float)
    head = A_HEAD_DOWN if P["head"] == "down" else A_HEAD_UP
    Mh = R(tor + P["neck"])
    rg.add("head", Mh, nk, head)
    for cx, cy, r in A_CHIGNON:
        c = nk + Mh @ np.array([cx, cy]); rg.pieces.append(("chignon", circ(c[0], c[1], r, 22)))
    rg.joint("neck", nk, "torso", "head")
    ear = nk + Mh @ np.array(A_EARLOBE, float)
    # near arm: IK to the task point (lid edge / box underside / lap)
    sh = root + Mt @ np.array(A_SHOULDER, float)
    g = f2(f)
    rest = (root[0] + 54.0, root[1] - 14.0)                         # palm resting on the lap, by the knee
    bp, holder, lid = box_pos
    lid_front = (bp[0] - 0.40 * BW, bp[1] - BODY_H - DEPTH * math.sin(math.radians(lid)) - 2)
    if g < 104:
        T = rest; hd = 60.0
    elif g < 126:
        T = key_interp([(104, rest), (116, (bp[0] - 60, bp[1] - 60)), (126, lid_front)], g); hd = lerp(60, -10, sm((g - 104) / 22.))
    elif g < 180:
        T = lid_front; hd = -10.0
    elif g < 200:
        T = key_interp([(180, lid_front), (190, rest)], g); hd = 60.0
    elif g < F_HANDOFF:
        under = (bp[0] - 0.20 * BW, bp[1] + 3)
        PH_under = (AUNT_ROOT[0] + 92.0 - 0.20 * BW, AUNT_ROOT[1] - 61.0)
        T = key_interp([(200, rest), (F_HANDOFF, PH_under)], g); hd = -20.0
    elif g < F_SETDOWN:
        T = (bp[0] - 0.20 * BW, bp[1] + 3); hd = -20.0
    else:
        top = (bp[0] - 0.05 * BW, bp[1] - BODY_H - LID_H - 1)        # her palm settles on the closed lid
        T = key_interp([(F_SETDOWN, (bp[0] - 0.20 * BW, bp[1] + 3)), (F_SETDOWN + 4, (bp[0] - 0.42 * BW, bp[1] - 8)),
                        (F_SETDOWN + 8, top)], g); hd = key_interp([(F_SETDOWN, -20.0), (F_SETDOWN + 8, 10.0)], g)
    du, df = ik2(sh, T, A_UPPER, A_FORE, bend=+1)
    s_rel = norm180(du - 90 - tor); e_rel = norm180(df - du)
    if e_rel > 0:
        du, df = ik2(sh, T, A_UPPER, A_FORE, bend=-1); s_rel = norm180(du - 90 - tor); e_rel = norm180(df - du)
    w_rel = max(LIMITS_A["wr"][0], min(LIMITS_A["wr"][1], norm180(hd - df)))
    el = sh + np.array([math.cos(math.radians(du)), math.sin(math.radians(du))]) * A_UPPER
    wr = el + np.array([math.cos(math.radians(df)), math.sin(math.radians(df))]) * A_FORE
    rg.add("upper", R(du - 90), sh, taper(A_UPPER, 7, 5.5)[0]); rg.pieces.append(("shouldercap", circ(sh[0], sh[1], 7)))
    rg.pieces.append(("elbowcap", circ(el[0], el[1], 5.5)))
    rg.add("fore", R(df - 90), el, taper(A_FORE, 5.5, 3.8)[0])
    rg.add("hand", R(df + w_rel - 90), wr, A_HAND)
    rg.joint("shoulder", sh, "torso", "upper"); rg.joint("elbow", el, "upper", "fore"); rg.joint("wrist", wr, "fore", "hand")
    rg.angles = {"torso": tor, "neck": P["neck"], "sh": s_rel, "el": e_rel, "wr": w_rel}
    # drop earring: pendulum hung at the ear lobe (state integrated in EARRING below)
    L = 11.0
    drop = ear + L * np.array([math.sin(ear_angle), math.cos(ear_angle)])
    rg.pieces.append(("earwire", [tuple(ear + R(math.degrees(-ear_angle)) @ np.array(p)) for p in [(-0.8, 0), (0.8, 0), (0.8, L), (-0.8, L)]]))
    rg.pieces.append(("earring", [tuple(drop + R(math.degrees(-ear_angle)) @ np.array(p)) for p in
                                  [(0, -1), (2.2, 1.5), (3.4, 4.5), (2.4, 7.2), (0, 8.2), (-2.4, 7.2), (-3.4, 4.5), (-2.2, 1.5)]]))
    rg.joint("earlobe", ear, "head", "earwire")
    rg.info = {"ear": tuple(ear), "drop": tuple(drop), "head_drawing": P["head"], "reach_err": float(np.hypot(*(wr - np.array(T))))}
    rg.punch_drop = drop + R(math.degrees(-ear_angle)) @ np.array([0, 4.6])
    return rg

# ---------------------------------------------------------------- secondary dynamics: the drop earring (#41)
def _ear_anchor_continuous(f):
    """ear lobe position from the un-stepped (continuous) pose, used only to drive the pendulum"""
    P = pose_A(f)  # pose_A is stepped; build a continuous version by evaluating on ones
    tor = key_interp([(0, 0.0), (104, 0.0), (124, 8.0), (180, 8.0), (188, 2.0), (204, 4.0), (214, 10.0), (240, 6.0)], f)
    neck = key_interp([(0, 0.0), (120, 4.0), (128, 10.0), (180, 12.0), (206, 2.0), (222, 12.0), (240, 16.0)], f)
    root = np.array(AUNT_ROOT, float)
    nk = root + R(tor) @ np.array(A_NECK, float)
    return nk + R(tor + neck) @ np.array(A_EARLOBE, float)

def _simulate_earring():
    g = 9.81 * (360 / 1.75)            # px/s^2 at this puppet scale (R. 360 px = 1.75 m)
    L, c = 11.0, 2.2
    sub = 8; dt = 1.0 / FPS / sub
    th, om = 0.0, 0.0
    out = []
    pos = [_ear_anchor_continuous(max(0, f - 1)) for f in range(-1, NF + 2)]
    pos = [_ear_anchor_continuous(f) for f in range(-2, NF + 2)]
    for f in range(NF):
        p0, p1, p2 = pos[f + 1], pos[f + 2], pos[f + 3]
        acc = (p2 - 2 * p1 + p0) * FPS * FPS
        for _ in range(sub):
            # L th'' = -g sin th - ax cos th + ay sin th   (y down)
            al = (-g * math.sin(th) - acc[0] * math.cos(th) + acc[1] * math.sin(th)) / L - c * om
            om += al * dt; th += om * dt
        out.append(th)
    return out
EARRING = _simulate_earring()

# ---------------------------------------------------------------- stage (handmade card set pieces)
def stage_pieces(f):
    """returns list of (name, polygon, plane) in PLANE coords (before travel); plane in {'set','rail'}"""
    ps = []
    ax = AUNT_ROOT[0]
    # wing chair (facing right), plane coords relative to her hip
    def C(pts): return [(ax + x, y) for x, y in pts]
    ps.append(("chair_back", C([(-60, 392), (-66, 330), (-68, 262), (-64, 216), (-52, 199), (-34, 197), (-22, 207),
                                (-20, 262), (-22, 330), (-20, 392)])))
    ps.append(("chair_wing", C([(-28, 212), (-4, 210), (14, 222), (18, 244), (8, 262), (-14, 270), (-24, 262)])))
    ps.append(("chair_arm", C([(-32, 342), (80, 336), (92, 330), (100, 338), (96, 352), (82, 356), (-32, 360)])))
    ps.append(("chair_seat", C([(-66, 392), (104, 392), (108, 408), (100, 420), (-62, 420)])))
    ps.append(("chair_legF", C([(90, 418), (100, 418), (96, 440), (102, 470), (106, 478), (92, 478), (92, 460), (88, 440)])))
    ps.append(("chair_legB", C([(-60, 418), (-50, 418), (-52, 450), (-58, 478), (-66, 478), (-60, 450)])))
    # lace antimacassar over the chair back: scalloped lower edge (holes punched separately)
    lace = [(-70, 194), (-50, 186), (-30, 190), (-18, 200)]
    for k in range(7):
        x0 = -18 - k * 7.5
        lace += [(x0 - 1.5, 238 - 2), (x0 - 3.75, 244), (x0 - 6, 238 - 2)]
    lace += [(-72, 236)]
    ps.append(("lace", C(lace)))
    # standard lamp, left of the chair
    lx = ax - 128
    ps.append(("lamp_shade", [(lx - 26, 190), (lx + 26, 190), (lx + 17, 150), (lx - 17, 150)]))
    ps.append(("lamp_finial", circ(lx, 146, 4)))
    ps.append(("lamp_pole", [(lx - 2.5, 190), (lx + 2.5, 190), (lx + 2.5, 470), (lx - 2.5, 470)]))
    ps.append(("lamp_base", [(lx - 22, 478), (lx + 22, 478), (lx + 8, 466), (lx - 8, 466)]))
    # door frame + door (3 drawings), at the right
    dx0 = 600.0
    ps.append(("door_jambL", [(dx0, 100), (dx0 + 10, 100), (dx0 + 10, 478), (dx0, 478)]))
    ps.append(("door_jambR", [(dx0 + 74, 100), (dx0 + 84, 100), (dx0 + 84, 478), (dx0 + 74, 478)]))
    ps.append(("door_lintel", [(dx0 - 8, 92), (dx0 + 92, 92), (dx0 + 92, 104), (dx0 - 8, 104)]))
    g = f2(f)
    dw = 64.0 if g < 6 else (30.0 if g < 12 else 7.0)
    ps.append(("door_panel", [(dx0 + 74 - dw, 106), (dx0 + 74, 106), (dx0 + 74, 476), (dx0 + 74 - dw, 476)]))
    return ps, dx0, dw

def stage_holes(f, dx0, dw):
    """punched light: lace holes, lamp slot, door mouldings (plane coords)"""
    holes = []
    ax = AUNT_ROOT[0]
    for r_ in range(3):
        for k in range(6):
            cx = ax - 66 + k * 8 + (4 if r_ % 2 else 0); cy = 202 + r_ * 9
            if cx < ax - 20: holes.append(("lace_hole", circ(cx, cy, 2.0, 10)))
    for k in range(7):
        holes.append(("lace_scallop", circ(ax - 21.75 - k * 7.5, 238, 1.3, 8)))
    lx = ax - 128
    holes.append(("lamp_slot", [(lx - 19, 168), (lx + 19, 168), (lx + 19, 173), (lx - 19, 173)]))
    if dw > 20:
        x0, x1 = dx0 + 74 - dw + dw * 0.18, dx0 + 74 - dw * 0.18
        for (y0, y1) in ((140, 260), (300, 440)):
            holes.append(("door_moulding", [(x0, y0), (x1, y0), (x1, y0 + 1.6), (x0, y0 + 1.6)]))
            holes.append(("door_moulding", [(x0, y1), (x1, y1), (x1, y1 + 1.6), (x0, y1 + 1.6)]))
            holes.append(("door_moulding", [(x0, y0), (x0 + 1.6, y0), (x0 + 1.6, y1), (x0, y1)]))
            holes.append(("door_moulding", [(x1 - 1.6, y0), (x1, y0), (x1, y1), (x1 - 1.6, y1)]))
    return holes

def rail_pieces():
    """scalloped floor rail: foreground card along the bottom (plane 'rail', travels 1.3x)"""
    top = FLOOR
    pts = [(-300, 540), (-300, top)]
    x = -300.0
    while x < 1300:
        pts += [(x + 6, top - 4), (x + 12, top)]
        x += 12
    pts += [(1300, 540)]
    holes = [circ(-300 + 12 * k + 6, top + 9, 2.2, 10) for k in range(134)]
    return pts, holes

def box_polys(pos, lid):
    """front elevation of the silver box from box-spec (w, body 0.30w, lid 0.08w hinged at the back).
    returns (solid polys, punched polys, ring centre or None)"""
    x0 = pos[0] - BW / 2; yb = pos[1]; yt = yb - BODY_H
    solid, punched = [], []
    solid.append([(x0, yt), (x0 + BW, yt), (x0 + BW, yb - 3), (x0, yb - 3)])
    for fx in (x0 + 5, x0 + BW - 5):                                         # ball feet
        solid.append(circ(fx, yb - 2.5, 3.0, 12))
    a = math.radians(lid)
    ring = None
    if lid < 1:
        solid.append([(x0 - 1.5, yt - LID_H), (x0 + BW + 1.5, yt - LID_H), (x0 + BW + 1.5, yt + 0.5), (x0 - 1.5, yt + 0.5)])
        solid.append([(pos[0] - 5, yt - LID_H - 2.5), (pos[0] + 5, yt - LID_H - 2.5), (pos[0] + 3, yt - LID_H), (pos[0] - 3, yt - LID_H)])
        punched.append([(x0 + 2, yt - 0.6), (x0 + BW - 2, yt - 0.6), (x0 + BW - 2, yt + 0.6), (x0 + 2, yt + 0.6)])  # lid seam
    else:
        top = yt - DEPTH * math.sin(a) - LID_H * max(0.25, math.cos(a))
        solid.append([(x0 + 1, top), (x0 + BW - 1, top), (x0 + BW - 1, yt + 0.5), (x0 + 1, yt + 0.5)])
        punched.append([(x0 + 4, yt - 1.6), (x0 + BW - 4, yt - 1.6), (x0 + BW - 4, yt - 0.4), (x0 + 4, yt - 0.4)])  # velvet lip
        if lid >= 60:
            rc = (x0 + SLOT_CX * BW, yt - RING_D * 0.30)
            ring = rc
    return solid, punched, ring

def ring_polys(rc):
    """the ring standing in the slot, half sunk: a punched light annulus + stone (drawn above the body top)"""
    ro, ri = RING_D / 2, RING_D / 2 - RING_BAND
    outer = circ(rc[0], rc[1], ro, 28); inner = circ(rc[0], rc[1], ri, 24)
    stone = [(rc[0], rc[1] - ro - 5.5), (rc[0] + 3.2, rc[1] - ro - 1.5), (rc[0], rc[1] - ro + 1.2), (rc[0] - 3.2, rc[1] - ro - 1.5)]
    return outer, inner, stone

# ---------------------------------------------------------------- the backlit paper screen
def _make_paper(seed=1954):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - 330) / 520) ** 2 + ((yy - 230) / 380) ** 2)
    lum = 214.0 - 34.0 * np.clip(r, 0, 1.3) ** 1.6                          # backlight hot spot -> ~180 at the edges
    mott = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 18) * 22
    mott += cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 4) * 3
    # fibres: short curved strokes of denser/thinner pulp, a real random process laid like rag paper
    fib = np.zeros((H * 2, W * 2), np.float32)
    for _ in range(2600):
        x, y = rng.uniform(0, W * 2), rng.uniform(0, H * 2)
        ang = rng.uniform(0, math.pi); L = rng.uniform(8, 40); bend = rng.normal(0, 0.04)
        pts = []
        for k in range(8):
            ang += bend
            pts.append((x, y)); x += math.cos(ang) * L / 8; y += math.sin(ang) * L / 8
        cv2.polylines(fib, [np.array(pts, np.int32)], False, float(rng.choice([-1, 1]) * rng.uniform(0.4, 1.0)), 1, cv2.LINE_AA)
    fib = cv2.resize(cv2.GaussianBlur(fib, (0, 0), 0.8), (W, H), interpolation=cv2.INTER_AREA) * 7
    Lm = lum + mott + fib
    warm = np.array([1.05, 1.00, 0.95], np.float32)                         # +5 % warm: his account
    return Lm[..., None] * warm[None, None]

def _make_blinds():
    """far plane: window blinds of the Vachon lounge print (LoC 2017831564), thresholded and softened"""
    v0 = np.array(Image.open(SRC + "8d04830.jpg").convert("L")).astype(np.float32)
    win = v0[40:440, 862:985]
    win = cv2.resize(win, (150, 480))
    th = (win < np.percentile(win, 45)).astype(np.float32)                   # slats / dark gaps
    soft = cv2.GaussianBlur(th, (0, 0), 3.0)
    e = np.minimum.reduce([np.linspace(0, 1, 150)[None, :].repeat(480, 0), np.linspace(1, 0, 150)[None, :].repeat(480, 0),
                           np.linspace(0, 1, 480)[:, None].repeat(150, 1), np.linspace(1, 0, 480)[:, None].repeat(150, 1)]) * 6
    return soft * np.clip(e, 0, 1) * 0.20

PAPER = None
BLINDS = None
def _assets():
    global PAPER, BLINDS
    if PAPER is None:
        PAPER = _make_paper(); BLINDS = _make_blinds()
    return PAPER, BLINDS

# ---------------------------------------------------------------- drawing
def _poly(d, pts, dx, fill):
    d.polygon([((x + dx) * S, y * S) for x, y in pts], fill=fill)

def scene(f):
    """all geometry of frame f in SCREEN coords; returns dict of layers"""
    m = m_of(f)
    wname, root, A, B = walk_state(f2(f))
    bpos = box_track(f, root)
    rR = build_R(f, bpos)
    rA = build_A(f, bpos, EARRING[f2(f) if f < NF else NF - 1])
    st, dx0, dw = stage_pieces(f)
    holes = stage_holes(f, dx0, dw)
    solid_box, punched_box, ring = box_polys(*bpos[:1], bpos[2]) if False else box_polys(bpos[0], bpos[2])
    return dict(m=m, R=rR, A=rA, stage=st, holes=holes, box=solid_box, box_punch=punched_box, ring=ring,
                box_pos=bpos, door_w=dw)

def silhouette(f, sc=None, scale=S):
    """the ink coverage alpha (0..1) at W x H, the light-punch mask and the glow mask"""
    sc = sc or scene(f)
    m = sc["m"]
    img = Image.new("L", (W * S, H * S), 0); d = ImageDraw.Draw(img)
    # set plane (stage), then the aunt, R. (far arm behind torso: order in pieces), the box
    for name, pts in sc["stage"]:
        _poly(d, pts, m, 255)
    for name, pts in sc["holes"]:
        _poly(d, pts, m, 0)
    # R. is drawn only once he is in the doorway (behind the panel in D1)
    showR = f2(f) >= 6
    if showR:
        for name, pts in sc["R"].pieces:
            _poly(d, pts, m, 255)
    for name, pts in sc["A"].pieces:
        _poly(d, pts, m, 255)
    # the door panel is in front of him while he steps through
    if f2(f) < 18:
        for name, pts in sc["stage"]:
            if name == "door_panel": _poly(d, pts, m, 255)
        for name, pts in sc["holes"]:
            if name == "door_moulding": _poly(d, pts, m, 0)
    for pts in sc["box"]:
        _poly(d, pts, m, 255)
    for pts in sc["box_punch"]:
        _poly(d, pts, m, 0)
    glow = Image.new("L", (W * S, H * S), 0); dg = ImageDraw.Draw(glow)
    if sc["ring"] is not None and not (F_SWALLOW[0] <= f <= F_SWALLOW[1]):
        outer, inner, stone = ring_polys(sc["ring"])
        yt = sc["box_pos"][0][1] - BODY_H
        clip = Image.new("L", (W * S, H * S), 0); dc = ImageDraw.Draw(clip)
        _poly(dc, outer, m, 255); _poly(dc, inner, m, 0); _poly(dc, stone, m, 255)
        dc.rectangle([0, int((yt - 0.8) * S), W * S, H * S], fill=0)          # lower half sunk behind the front wall
        img = Image.composite(Image.new("L", img.size, 0), img, clip)
        glow = clip
    # her pearl drop: a punched pinhole in the earring (light through the bead)
    pd = sc["A"].punch_drop
    _poly(d if False else ImageDraw.Draw(img), circ(pd[0], pd[1], 0.9, 8), m, 0)
    # pin rivets: tiny punched holes at the visible joints
    dd = ImageDraw.Draw(img)
    for rig, names in ((sc["R"], ("n_shoulder", "n_elbow", "f_shoulder", "hipA", "kneeA")), (sc["A"], ("shoulder", "elbow"))):
        if rig is sc["R"] and not showR: continue
        for n in names:
            p = rig.joints[n][0]
            _poly(dd, circ(p[0], p[1], 0.85, 8), m, 0)
    # foreground rail travels 1.3x
    rail, rholes = rail_pieces()
    _poly(dd, rail, 1.3 * m, 255)
    for h in rholes: _poly(dd, h, 1.3 * m, 0)
    a = np.asarray(img.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255.0
    gl = np.asarray(glow.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255.0
    return np.clip(a, 0, 1), gl, sc

_LABEL = None
def _label():
    global _LABEL
    if _LABEL is None:
        fnt = ImageFont.truetype(FONT, 18)
        im = Image.new("L", (W, 40), 0); d = ImageDraw.Draw(im)
        txt = "« — selon lui — »"
        tw = d.textlength(txt, font=fnt)
        d.text(((W - tw) / 2, 10), txt, font=fnt, fill=255)
        _LABEL = np.asarray(im).astype(np.float32) / 255.0 * 0.80
    return _LABEL

def render_flashback(t, label=True, grain=True):
    """S2 local time t (s) in [0, 10.5) -> 720x540 RGB PIL image"""
    f = int(round(t * FPS)); f = max(0, min(NF - 1, f))
    paper, blinds = _assets()
    a, gl, sc = silhouette(f)
    m = sc["m"]
    img = paper.copy()
    # far plane: the blinds, behind the screen, travel 0.3x the set (multiplane depth)
    bx = int(round(470 + 0.3 * m)); by = 40
    x0, x1 = max(0, bx), min(W, bx + blinds.shape[1])
    if x1 > x0:
        img[by:by + blinds.shape[0], x0:x1] *= (1 - blinds[:, x0 - bx:x1 - bx])[..., None]
    # the doorway: light from the hall is brighter than the room (open door)
    # silhouettes: card pressed to the screen; tiny edge diffusion only
    a2 = cv2.GaussianBlur(a, (0, 0), 0.45)
    img = img * (1 - a2[..., None]) + INK[None, None] * a2[..., None]
    # punched ring: light through the hole blooms a little (glint)
    if gl.max() > 0:
        bloom = cv2.GaussianBlur(gl, (0, 0), 2.2) * 0.55 + gl * 0.25
        img = img + bloom[..., None] * np.array([40, 36, 28], np.float32)[None, None]
    if label:
        lab = _label(); col = np.array([58, 46, 36], np.float32)
        reg = img[14:54]
        img[14:54] = reg * (1 - lab[..., None]) + col * lab[..., None]
    if grain:
        rng = np.random.default_rng(1000 + f2(f))
        gr = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.6) * 3.2
        img = img + gr[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")

# ---------------------------------------------------------------- assertions + exposure sheet
def _mask(polys, dx, inv=None):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for p in polys: d.polygon([(x + dx, y) for x, y in p], fill=255)
    if inv:
        for p in inv: d.polygon([(x + dx, y) for x, y in p], fill=0)
    return np.asarray(im) > 127

def _inside(mask, p, dx):
    x, y = int(round(p[0] + dx)), int(round(p[1]))
    if not (0 <= x < W and 0 <= y < H): return None            # off-screen: not testable
    return bool(mask[max(0, y - 1):y + 2, max(0, x - 1):x + 2].any())

def check_frame(f):
    sc = scene(f); m = sc["m"]
    res = {"frame": f, "film_frame": f + 216}
    rR, rA = sc["R"], sc["A"]
    def piece_mask(rig, name_prefix):
        return _mask([p for n, p in rig.pieces if n == name_prefix], m)
    det = []
    for rig, who in ((rR, "R"), (rA, "aunt")):
        if who == "R" and f2(f) < 6: continue
        for jn, (pt, par, ch) in rig.joints.items():
            pm, cm = piece_mask(rig, par), piece_mask(rig, ch)
            ip, ic = _inside(pm, pt, m), _inside(cm, pt, m)
            if ip is False or ic is False: det.append(f"{who}.{jn}")
        # whole-puppet connectivity: one card assembly, no detached piece
        um = _mask([p for n, p in rig.pieces], m)
        if who == "aunt": um = um | _mask([p for n, p in sc["stage"] if n.startswith("chair")], m)
        ncomp = cv2.connectedComponents(um.astype(np.uint8))[0] - 1
        res[f"{who}_components"] = int(ncomp)
        if ncomp > 1: det.append(f"{who}.components={ncomp}")
    res["detached"] = det
    lim = []
    for k, v in rR.angles.items():
        lo, hi = LIMITS_R.get(k, (-999, 999))
        if not (lo - 1e-6 <= v <= hi + 1e-6): lim.append(f"R.{k}={v:.1f} not in [{lo},{hi}]")
    for k, v in rA.angles.items():
        lo, hi = LIMITS_A.get(k, (-999, 999))
        if not (lo - 1e-6 <= v <= hi + 1e-6): lim.append(f"aunt.{k}={v:.1f} not in [{lo},{hi}]")
    res["limit_violations"] = lim
    tm = piece_mask(rR, "torso"); fh = piece_mask(rR, "far_hand")
    res["far_hand_px_outside_torso"] = int((fh & ~tm).sum())
    bm = _mask(sc["box"], m)
    res["box_px_outside_torso"] = int((bm & ~tm).sum())
    res["box_holder"] = sc["box_pos"][1]; res["lid_deg"] = round(sc["box_pos"][2], 1)
    res["ring_visible"] = sc["ring"] is not None and not (F_SWALLOW[0] <= f <= F_SWALLOW[1])
    if sc["ring"] is not None:
        res["ring_screen"] = [round(sc["ring"][0] + m, 1), round(sc["ring"][1], 1)]
        x0 = sc["box_pos"][0][0] - BW / 2
        res["ring_norm_x_in_box"] = round((sc["ring"][0] - x0) / BW, 3)
    res["angles_R"] = {k: round(v, 2) for k, v in rR.angles.items()}
    res["angles_aunt"] = {k: round(v, 2) for k, v in rA.angles.items()}
    res["earring_deg"] = round(math.degrees(EARRING[f2(f)]), 2)
    res["walk_drawing"] = rR.info["walk"]; res["torso_drawing"] = rR.info["torso_drawing"]
    res["head_aunt"] = rA.info["head_drawing"]; res["door_w"] = sc["door_w"]
    res["near_reach_err_px"] = round(rR.info["near_reach_err"], 2); res["aunt_reach_err_px"] = round(rA.info["reach_err"], 2)
    res["set_travel_px"] = round(m, 2); res["far_plane_px"] = round(0.3 * m, 2); res["rail_px"] = round(1.3 * m, 2)
    res["elbow_far"] = [round(rR.info["elbow_far"][0] + m, 1), round(rR.info["elbow_far"][1], 1)]
    return res

def drawing_names(f):
    g = f2(f); out = []
    for fa, nm in F_DOOR[::-1]:
        if g >= fa: out.append(nm); break
    if F_WALK0 <= g < F_WALK1: out.append(WALK[((g - F_WALK0) // 2) % 8][0])
    for fa, nm in F_OFFER[::-1]:
        if fa <= g < 132 and g >= fa: out.append(nm); break
    for fa, nm in F_LID[::-1]:
        if fa <= g < 184: out.append(nm); break
    if F_SWALLOW[0] <= f <= F_SWALLOW[1]: out.append("SW%d swallow (on ones)" % (f - F_SWALLOW[0] + 1))
    if 198 <= g < F_HANDOFF: out.append("H1 hand-off (box re-emerges closed)")
    if F_HANDOFF <= g < F_SETDOWN: out.append("H2 her palm lowers the box")
    if g >= F_SETDOWN: out.append("H3 box set down on her lap")
    return out
