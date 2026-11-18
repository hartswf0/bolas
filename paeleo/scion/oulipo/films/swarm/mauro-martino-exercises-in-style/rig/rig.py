"""U3 RIG: articulated silhouette puppets (SCION #2 Reiniger), cord / coat-tail dynamics
(SCION #41 Secondary Dynamics) and the frozen exposure sheet for "Exercises in Style"
(Mauro Martino), SCION controlled variation.

HANDMADE. Every part is a hand-placed closed Catmull-Rom outline (coat tails, hands with
thumbs, profiles with nose and chin, the felt hat with a braid of cut notches); no capsules.

API (pure, deterministic; the renderer draws NO random numbers):
    pose(seed, t)                      -> Pose dict (world + screen state of every puppet at clip t)
    draw_side(layer, pose, fill, group=None)  -> RGBA image: puppets printed in side elevation
    draw_plan(layer, pose, fill, group=None)  -> RGBA image: plan projections (hat discs, shoulders, feet)
    side_mask(pose, group=None, ids=None)     -> float32 HxW coverage (pre-print outline; for IoU)
    plan_mask(pose, ...)                      -> same for the plan
    feet(pose)                                -> [(x, y)] street feet for stage.shadow_slivers
fill = an RGB tuple (solid ink), an HxWx3 float array (photographic texture, screen px), or a dict
{puppet_id: one of those, "default": ...}. The outline never depends on fill (treatment delta C3).

Groups (side layer order, matching stage.py): "window" (seated passengers + the man once inside;
clipped to the rear pane) -> after bus_body;  "platform" (man, jostler, conductor; "inside" parts
clipped at the bulkhead) -> before bus_front;  "street" (runners) -> after bus_front.

Time base: 24 fps frames; puppets are DRAWINGS on twos: drawing d = floor(12 t). The bus layer slide
dx(t) is per frame (smooth); platform puppets ride it. The cord/coat-tail are integrated at 24 Hz
(semi-implicit Euler) in the bus frame and sampled on twos (state at frame 2d).

RNG: rng(seed, element_id) streams only, for UNPROTECTED elements: runner count / kinds / x / z /
phase / stride, standing idles, and which seated passenger vacates. Protected puppets (man, jostler,
conductor) read no RNG, so their masks are identical across seeds.

Run:  python3 -I rig.py   -> anchors.json, exposure.json, cord-energy.json, shove-strip.png, tests
"""
import json, math, hashlib, functools, sys, importlib.util
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
SLUG = "mauro-martino-exercises-in-style"
WS = ROOT / "films/swarm" / SLUG
RIGDIR = WS / "rig"
MEDIA = ROOT / "films/sources" / SLUG / "rig"
RIG_REV = "rig-1"

W, H, SS = 960, 540, 3
FPS, CLIP = 24, 7.0
NF = int(round(FPS * CLIP))            # 168 frames
ND = NF // 2                           # 84 drawings
INK = (34, 33, 31)
SEEDS = (417, 418)


# ------------------------------------------------------------------ stage geometry (U2, read-only)
@functools.lru_cache(None)
def stage():
    if "stage" in sys.modules and hasattr(sys.modules["stage"], "anchors_world"):
        return sys.modules["stage"]
    spec = importlib.util.spec_from_file_location("stage", WS / "stage/stage.py")
    m = importlib.util.module_from_spec(spec); sys.modules["stage"] = m; spec.loader.exec_module(m)
    return m


@functools.lru_cache(None)
def geo():
    S = stage(); an = S.anchors_world()
    return dict(an=an, floor=an["platform_floor_y"], step=an["step_y"], stx=an["stanchion"]["x"],
                plat0=an["platform_x"][0], plat1=an["platform_x"][1], win=an["rear_window"],
                bell=an["bell_cord"], rest=S.BUS_REST_X)


def bus_dx(t):
    S = stage(); return S.bus_x(t) - S.BUS_REST_X


def rng(seed, *key):
    h = hashlib.sha1(repr(("rig", int(seed)) + key).encode()).digest()
    return np.random.RandomState(int.from_bytes(h[:4], "little"))


def drawing(t):
    return max(0, min(ND - 1, int(math.floor(t * 12 + 1e-9))))


# ------------------------------------------------------------------ H4 · hand-drawn part outlines
def smooth_closed(pts, n=7):
    """Catmull-Rom through hand-placed points: fluid closed outlines. A point given twice is a cusp."""
    P = np.array(pts, np.float64); out = []; m = len(P)
    for i in range(m):
        p0, p1, p2, p3 = P[(i - 1) % m], P[i], P[(i + 1) % m], P[(i + 2) % m]
        for k in range(n):
            u = k / n; u2, u3 = u * u, u * u * u
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3))
    return np.array(out)


# puppet space: +x = the way the puppet faces, y down, units ~ screen px at scale 1.
SHAPES = {
    # --- the long-necked man: narrow coat, long tapered neck, soft felt hat
    "m_torso": [(-8, -45), (-3, -48.5), (4, -48), (8.5, -44), (9.5, -31), (8, -14), (8.6, 2), (10, 22), (3, 25), (-7, 25), (-10, 21), (-9, 2), (-10.5, -20), (-10.5, -37)],
    "m_tail": [(0, -2), (-2.5, 9), (-6.5, 23), (-4.5, 27), (-0.5, 25), (3, 11), (4, -1)],
    "m_neck": [(-3.4, 3), (-2.4, -12), (-1.7, -32), (-0.3, -34.5), (1.9, -33), (2.5, -13), (4.4, 3)],
    "m_head": [(-6, 0.5), (-8, -5.5), (-7.6, -12.5), (-3, -16.5), (3, -16.8), (6, -14), (6.8, -10.5), (10.6, -7.2), (7.2, -5.6), (7.4, -3.6), (8.6, -2.6), (6.6, 0.2), (7.2, 1.8), (4, 3.4), (-0.5, 2.4)],
    # soft felt: drooping front brim, dented crown (the band notches are cut separately)
    "m_hat": [(-12.8, 1.6), (-8.2, 0.4), (-8.0, -4.2), (-6.6, -8.4), (-3.2, -10.6), (-0.2, -9.0), (2.6, -10.8), (6.4, -9.0), (7.8, -4.6), (8.0, 0.0), (11.8, 1.0), (14.2, 3.0), (12.6, 3.6), (7.0, 2.6), (-8, 2.6), (-12, 3.0)],
    # --- arms and legs (shared). Hands are replacement drawings carried on the forearm.
    "uarm": [(-4.2, -1.5), (-3.8, 11), (-3.2, 24), (0, 25.5), (3.2, 24), (3.9, 11), (4.4, -2)],
    "farm_fist": [(-3, 0), (-2.6, 17), (-3.4, 22), (-2.6, 28), (0, 30.2), (2.8, 28.4), (3.2, 24), (5.8, 22.8), (6.4, 20.6), (3.4, 19.4), (2.8, 17), (3, 0)],
    "farm_open": [(-3, 0), (-2.6, 17), (-4.2, 19), (-5.6, 27.6), (-3.8, 28.2), (-2.8, 22), (-2.4, 31), (-0.8, 31.2), (-0.4, 22.4), (0.8, 31.6), (2.4, 31.4), (1.4, 22.4), (3.2, 29.6), (4.6, 28.8), (3.2, 20.4), (7.2, 22.6), (7.6, 21), (3.4, 16.8), (3, 0)],
    "farm_flat": [(-3, 0), (-2.6, 17), (-3.0, 20), (-2.6, 31.5), (-0.6, 33), (1.6, 32), (2.2, 22.5), (5.8, 21), (6.0, 19.2), (3.0, 17.2), (3, 0)],
    "farm_grip": [(-3, 0), (-2.6, 17), (-3.6, 21), (-3.2, 27), (0.4, 29.6), (4.6, 27.6), (5.0, 24.4), (2.2, 25.2), (2.6, 21.6), (6.4, 21.4), (6.4, 19.4), (3, 17), (3, 0)],
    "thigh": [(-5.8, -1.5), (-5.4, 14), (-4.0, 31.5), (0, 33), (4.0, 31.5), (5.4, 14), (5.9, -2)],
    "shin": [(-3.8, -1), (-3.1, 25), (-3.9, 30.5), (-2.4, 33.6), (11.6, 33.6), (13.4, 31.6), (9.6, 29.2), (3.4, 27.4), (3.8, -1)],
    "shin_b": [(-3.4, -1), (-2.6, 25), (-3.2, 30), (-1.8, 33.4), (10.6, 33.4), (11.6, 31.8), (8.8, 30.2), (4.6, 29.6), (2.6, 26.8), (3.4, -1)],   # heeled boot
    # --- the jostler: broad back, bowler
    "j_torso": [(-15, -40), (-9, -47.5), (4, -47), (11, -41), (12.5, -26), (10.5, -8), (11, 4), (13, 22), (2, 24), (-14, 22), (-14, 4), (-16.8, -14), (-18, -30)],
    "j_neck": [(-4.8, 2), (-4.2, -6.5), (4.2, -6.5), (5.2, 2)],
    "j_head": [(-7, 0), (-8.8, -7), (-7, -14), (-2, -17), (4, -16), (7, -12), (8, -8), (10.6, -6), (8, -4.2), (8.4, -1.4), (5, 1.8), (0, 2.6)],
    "bowler": [(-10.8, 1.6), (-7.6, 0.4), (-7.9, -6), (-5.2, -10.8), (0, -11.8), (5.2, -10.8), (7.9, -6), (7.6, 0.4), (10.8, 1.6), (9.8, 3.1), (-9.8, 3.1)],
    # --- runner A: man, coat flaring, cloth cap
    "a_torso": [(-10, -45), (-4, -48), (6, -47), (11, -42), (12, -28), (10, -10), (11, 4), (-11, 4), (-12, -22)],
    "a_tail": [(-1, -2), (-6, 12), (-11, 26), (-5, 28.5), (2, 25), (7, 13), (9, -2)],
    "a_head": [(-6.5, 0), (-8, -6), (-7, -13), (-2.5, -16.5), (3.5, -16), (6.5, -12), (7.5, -8.5), (10, -6), (7.4, -4.6), (7.6, -2), (5, 1.4), (0, 2.2)],
    "cap": [(-8, 1), (-8.4, -6), (-3, -10.4), (4, -10), (8.4, -5.4), (8.8, -0.8), (15.4, 0.6), (14.2, 2.6), (-7.5, 2.8)],
    "neck_s": [(-3.6, 2.5), (-3, -7.5), (3, -7.5), (4.2, 2.5)],
    # --- runner B: woman, long skirt, cloche
    "b_torso": [(-8, -44), (-3, -47), (5, -46), (9, -41), (9.5, -28), (7, -12), (8, 0), (-8, 0), (-9.5, -20), (-9.5, -36)],
    "b_skirt": [(-8, -2), (8, -2), (12, 16), (17, 35), (4, 37.5), (-13, 36), (-10.5, 16)],
    "b_head": [(-6, 0), (-7.4, -6), (-6.6, -12.6), (-2.4, -16), (3.2, -15.6), (6, -11.8), (6.8, -8.6), (8.8, -6.4), (6.8, -5), (7, -2.4), (4.6, 1.2), (0, 2.0)],
    "cloche": [(-9.6, 2.2), (-8.8, -6), (-5, -10.8), (2, -11.2), (7, -8.2), (9.2, -2), (11, 3.2), (-9, 4.2)],
    # --- runner C: young man, short jacket, straw boater
    "c_torso": [(-9, -44), (-3, -47), (5, -46.5), (10, -41.5), (10.5, -28), (9, -10), (10, 5), (2, 7), (-10, 5), (-10, -20)],
    "boater": [(-11.5, 1.6), (-7.2, 0.8), (-7.2, -6.4), (-7.0, -7.2), (7.0, -7.2), (7.2, -6.4), (7.2, 0.8), (11.5, 1.6), (11, 3.0), (-11, 3.0)],
    # --- runner D: man, long overcoat to the knee, bowler (shares bowler)
    "d_torso": [(-11, -45), (-5, -48), (6, -47.5), (11.5, -42), (12.5, -27), (10.5, -9), (11.5, 4), (-12, 4), (-13, -22)],
    "d_tail": [(-8, -2), (-12, 16), (-17, 37), (-7, 40), (5, 38), (9.5, 18), (10.5, -2)],
    # --- runner E: woman, coat to the knee, wide-brimmed hat
    "e_skirt": [(-8.5, -2), (8.5, -2), (11.5, 14), (14.5, 28), (2, 30.5), (-12.5, 29), (-11, 14)],
    "brim": [(-15, 2.2), (-8.4, 0.2), (-7.4, -7), (-2, -10.4), (4.2, -9.8), (7.4, -5.2), (8.2, 0), (15.8, 2.6), (14, 4.4), (-13.4, 4.0)],
    # --- conductor: tunic, kepi, satchel
    "k_torso": [(-10, -45), (-4, -48), (5.5, -47.5), (10.5, -42), (11.5, -27), (10, -8), (11, 6), (-11, 6), (-12, -22)],
    "kepi": [(-7.4, 1.2), (-7.8, -9.2), (-2, -10.4), (6.8, -9.6), (7.2, 0.6), (13.6, 1.8), (12.6, 3.2), (-7.2, 3.2)],
    "satchel": [(-6, -1), (6, -1), (6.6, 6), (4, 11), (-4, 11), (-6.6, 6)],
}
SCALE = {"m_head": 1.25, "m_hat": 1.3, "j_head": 1.15, "bowler": 1.15, "a_head": 1.15, "cap": 1.15, "b_head": 1.15,
         "cloche": 1.15, "boater": 1.15, "brim": 1.15, "kepi": 1.15}
SM = {k: smooth_closed(v) * SCALE.get(k, 1.0) for k, v in SHAPES.items()}
HATS = 1.3


def _std(torso, head, hat, neck="neck_s", neck_pivot=(1, -46), head_pivot=(0, -6.5), hat_pivot=(0, -14.4),
         tail=None, tail_pivot=(0, 2), tail_z=2, shin="shin", sh=(0, -43), extra=()):
    parts = [("leg_f", "root", (0, 2), "thigh", 0), ("shin_f", "leg_f", (0, 31), shin, 0),
             ("arm_f", "torso", sh, "uarm", 1), ("fore_f", "arm_f", (0, 23), "farm_fist", 1)]
    if tail:
        parts.append(("tail", "torso", tail_pivot, tail, tail_z))
    parts += [("torso", "root", (0, 0), torso, 3), ("neck", "torso", neck_pivot, neck, 3),
              ("head", "neck", head_pivot, head, 4), ("hat", "head", hat_pivot, hat, 5),
              ("leg_n", "root", (0, 2), "thigh", 6 if not tail or tail_z < 3 else 2), ("shin_n", "leg_n", (0, 31), shin, 6 if not tail or tail_z < 3 else 2),
              ("arm_n", "torso", sh, "uarm", 7), ("fore_n", "arm_n", (0, 23), "farm_fist", 7)]
    parts += list(extra)
    return parts


LIM = dict(neck=(-28, 30), head=(-32, 30), fore_n=(-5, 150), fore_f=(-5, 150), shin_n=(-125, 0), shin_f=(-125, 0),
           leg_n=(-60, 95), leg_f=(-60, 95), arm_n=(-80, 175), arm_f=(-80, 175), torso=(-40, 30), tail=(-45, 40))
RIGS = {
    "man": dict(parts=_std("m_torso", "m_head", "m_hat", neck="m_neck", neck_pivot=(2.4, -45), head_pivot=(0, -31.5),
                           hat_pivot=(0, -17.2), tail="m_tail", tail_pivot=(-7.5, 4)), limits=LIM),
    "jostler": dict(parts=_std("j_torso", "j_head", "bowler", neck="j_neck", neck_pivot=(0, -45), head_pivot=(0, -5.5),
                               hat_pivot=(0, -14.5), sh=(-2, -41)), limits=LIM),
    "runA": dict(parts=_std("a_torso", "a_head", "cap", tail="a_tail"), limits=LIM),
    "runB": dict(parts=_std("b_torso", "b_head", "cloche", tail="b_skirt", tail_pivot=(0, 0), tail_z=6.5, shin="shin_b", sh=(0, -42)), limits=LIM),
    "runC": dict(parts=_std("c_torso", "a_head", "boater", hat_pivot=(0, -13.6)), limits=LIM),
    "runD": dict(parts=_std("d_torso", "j_head", "bowler", hat_pivot=(0, -14.5), tail="d_tail"), limits=LIM),
    "runE": dict(parts=_std("b_torso", "b_head", "brim", tail="e_skirt", tail_pivot=(0, 0), tail_z=6.5, shin="shin_b", sh=(0, -42), hat_pivot=(0, -13.6)), limits=LIM),
    "conductor": dict(parts=_std("k_torso", "a_head", "kepi", hat_pivot=(0, -13.2),
                                 extra=[("satchel", "torso", (-9, -6), "satchel", 6.8)]), limits=LIM),
}
RUN_KINDS = ("runA", "runB", "runC", "runD", "runE")
CORD_LOCAL = (-8.2 * HATS, 1.0 * HATS)   # where the loose cord end leaves the band (hat space, back of crown)


def rot(th):
    c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
    return np.array([[c, s_], [-s_, c]])   # +θ swings a hanging limb forward (+x)


def fk(kind, ang, limits_log=None):
    """Forward kinematics in puppet space. Joint angles clamped to limits (logged if asked)."""
    R = RIGS[kind]; out = {"root": (np.zeros(2), 0.0)}
    done = {"root"}; pending = list(R["parts"]); ordered = []
    while pending:
        for p in list(pending):
            if p[1] in done:
                ordered.append(p); done.add(p[0]); pending.remove(p)
    for name, parent, pivot, shape, z in ordered:
        po, pa = out[parent]
        a = float(ang.get(name, 0.0))
        lo, hi = R["limits"].get(name, (-180, 180))
        if limits_log is not None and not (lo <= a <= hi):
            limits_log.append((kind, name, a, lo, hi))
        a = max(lo, min(hi, a))
        out[name] = (po + rot(pa) @ np.array(pivot, float), pa + a)
    return out, ordered


def _xf(P):
    """Puppet-space -> screen transform for a placed puppet P."""
    s, f = P["s"], P["facing"]
    piv, tip = P.get("pivot", (0.0, 0.0)), P.get("tip", 0.0)
    R_ = rot(tip); pv = np.array(piv, float)
    org = np.array([P["x"], P["y"]], float)
    def T(pts):
        q = (R_ @ (np.asarray(pts, float) - pv).T).T + pv
        q = q * s; q[:, 0] *= f
        return q + org
    return T


def parts_world(P, limits_log=None):
    """[(z, part, Nx2 screen polygon)] in draw order, plus pins {joint: (parent_pt, child_pt)} and named points."""
    Tm, ordered = fk(P["kind"], P["ang"], limits_log)
    T = _xf(P); hands = P.get("hands", {}); flip = P.get("head_flip", False)
    polys, pins = [], {}
    for name, parent, pivot, shape, z in sorted(ordered, key=lambda p: p[4]):
        o, a = Tm[name]
        key = hands.get(name, shape)
        loc = SM[key].copy()
        if flip and name in ("head", "hat"):
            loc[:, 0] *= -1
        pts = (rot(a) @ loc.T).T + o
        polys.append((z, name, T(pts)))
        po, pa = Tm[parent]
        par_pt = po + rot(pa) @ np.array(pivot, float)      # pin as seen from the parent
        pins[name] = (T(par_pt[None])[0], T(o[None])[0], parent)
    def pt(part, local):
        o, a = Tm[part]; l = np.array(local, float)
        if flip and part in ("head", "hat"):
            l = l * np.array([-1, 1])
        return T((rot(a) @ l + o)[None])[0]
    return polys, pins, pt


def lowest(P):
    """Lowest foot y of the unplaced puppet (puppet space * s)."""
    Q = dict(P, x=0.0, y=0.0, tip=0.0)
    polys, _, _ = parts_world(Q)
    return max(p[:, 1].max() for z, n, p in polys if n.startswith("shin"))


def foot_x(P, which):
    polys, _, _ = parts_world(P)
    for z, n, p in polys:
        if n == which:
            i = int(np.argmax(p[:, 1])); return float(p[i, 0])


def place_on(P, ground_y, lift=0.0):
    P["y"] = ground_y - lowest(P) - lift
    return P


# ------------------------------------------------------------------ run cycle (6 drawings, long stride)
RUN = [(50, -6), (27, -24), (-6, -16), (-36, -42), (-22, -108), (30, -84)]   # (thigh, shin) of one leg
LIFT = [0.0, 1.0, 3.0, 0.0, 1.0, 3.0]          # pelvis rise in the drive/float drawings (x s)


def run_angles(k, lean=-12, amp=1.0, arm=1.0, fore=85, bob=1.0):
    a = RUN[k % 6]; b = RUN[(k + 3) % 6]
    th = lambda v: v * amp
    return {"torso": lean, "leg_n": th(a[0]) - lean * 0.3, "shin_n": a[1] * (0.8 + 0.2 * amp),
            "leg_f": th(b[0]) - lean * 0.3, "shin_f": b[1] * (0.8 + 0.2 * amp),
            "arm_n": -a[0] * 0.95 * arm, "fore_n": fore, "arm_f": -b[0] * 0.95 * arm, "fore_f": fore,
            "neck": -lean * 0.4, "head": 4, "tail": -12 - 10 * amp * (1 if k % 3 == 1 else 0.4)}


def stand_angles(lean=0.0):
    return {"torso": lean, "leg_n": 4, "shin_n": -4, "leg_f": -5, "shin_f": -2, "arm_n": -4, "fore_n": 12,
            "arm_f": 6, "fore_f": 14, "neck": 0, "head": 0, "tail": 0}


def sit_angles(lean=0.0):
    return {"torso": lean, "leg_n": 86, "shin_n": -84, "leg_f": 80, "shin_f": -80, "arm_n": 18, "fore_n": 70,
            "arm_f": 14, "fore_f": 66, "neck": 0, "head": 0, "tail": 0}


# ------------------------------------------------------------------ EXPOSURE SHEET · protected puppets
MAN_S, JOS_S, CON_S = 0.80, 0.86, 0.80
MAN_Z, JOS_Z, CON_Z = 222.0, 206.0, 150.0     # world depth on the platform (plan view)
SEAT_A, SEAT_B = 593.0, 551.0                  # rear-pane seats (screen x at rest)


def man_keys(d):
    """Long-necked man (bus frame, x at rest). Returns state without placement y."""
    g = geo()
    a = stand_angles(); a.update(arm_n=8, fore_n=40, arm_f=10, fore_f=30, neck=-3, head=-2, tail=0)
    st = dict(x=684.0, tip=0.0, hands={}, flip=False, where="platform", sit=False, note="waits on the platform, facing in")
    if d < 12:
        pass
    elif d == 12:
        a.update(neck=-6, head=-8); st["note"] = "notices the runner (head down-left)"
    elif d == 13:
        a.update(neck=-8, head=-12, arm_n=14, fore_n=50); st["note"] = "braces: sees the arm coming"
    elif d == 14:                                       # A3 contact (1.167-1.25 covers 1.20)
        a.update(torso=4, neck=-6, head=-8, arm_n=20, fore_n=46, arm_f=14); st.update(tip=3, x=686.0, note="A3 contact: flat hand on the chest")
    elif d == 15:                                       # pushed: head lags forward, arms fly forward
        a.update(torso=4, neck=-12, head=-8, arm_n=46, fore_n=26, arm_f=32, fore_f=24, leg_n=12, shin_n=-18, tail=-14)
        st.update(tip=5, x=696.0, note="driven back: head lags, arms fly up")
        st["hands"] = {"fore_n": "farm_open", "fore_f": "farm_open"}
    elif 16 <= d < 24:                                  # A4 1.333: shoulder meets the stanchion; neck whips back
        whip = {16: 7, 17: 11, 18: 5, 19: 8}.get(d, 7)
        a.update(torso=2, neck=whip, head=whip * 0.5, arm_n=34 - min(d - 16, 4) * 6, fore_n=34, arm_f=20, fore_f=30, leg_n=12, shin_n=-18)
        a["head"] = a["head"] - (18 if d >= 18 else 0)                 # winces: head ducked away
        st.update(tip=6 if d < 19 else 5, x=700.0, flip=False, contact=True,
                  note="A4 stanchion contact; recoil, winces away" if d == 16 else "pinned to the stanchion, head turned away")
        st["hands"] = {"fore_f": "farm_grip"}
    elif 24 <= d < 39:                                  # A5 protest 2.0-3.2: head turns back to the jostler, open hand rises
        u = min(1.0, (d - 24) / 4)
        a.update(torso=2 - 4 * u, neck=6 - 16 * u, head=4 - 12 * u, arm_n=-30 + 96 * u, fore_n=40 + 66 * u,
                 arm_f=-14 + 8 * u, fore_f=30, leg_n=10, shin_n=-14)
        st.update(tip=5 - 3 * u, x=700.0, contact=u < 1, note="A5 protest: turns to the jostler, open hand")
        st["hands"] = {"fore_n": "farm_open" if d >= 26 else "farm_fist", "fore_f": "farm_grip"}
        if d in (28, 29, 31, 32):
            a["fore_n"] += 10; a["arm_n"] += 3; st["note"] = "A5 protest beat"
        if d >= 34:                                     # 2.83-3.2: the hand drops, head stays on the jostler
            v = min(1.0, (d - 34) / 3)
            a.update(arm_n=66 - 60 * v, fore_n=106 - 70 * v)
            st["hands"] = {"fore_n": "farm_open" if v < 0.6 else "farm_fist", "fore_f": "farm_grip"}
    elif 39 <= d < 52:                                  # composes himself, still
        a.update(neck=-10, head=-8, torso=-2, arm_n=6, fore_n=36, arm_f=-6, fore_f=30, leg_n=10, shin_n=-14)
        st.update(x=700.0, tip=2, note="composes himself (held: no source for the cord)")
        st["hands"] = {"fore_f": "farm_grip"}
    elif 52 <= d < 60:                                  # 4.33-5.0: ducks in through the bulkhead (moves left, stooping)
        k = d - 52
        a = run_angles(k, lean=-14, amp=0.45, arm=0.4, fore=50); a.update(neck=18, head=10, tail=-6)
        st.update(x=688.0 - k * 11.5, where="inside", note="ducks in at the bulkhead")
    else:                                               # in the rear pane: walks in stooped, sits (A6 5.50 = d66)
        k = d - 60
        if k < 4:
            a = run_angles(k, lean=-10, amp=0.35, arm=0.3, fore=50); a.update(neck=20, head=10)
            st.update(x=616.0 - k * 5.5, where="window", note="seen in the rear pane, stooped under the roof")
        elif k < 6:
            a = sit_angles(lean=-8 if k == 4 else -4); a["leg_n"] = 40 if k == 4 else 70; a["shin_n"] = -40 if k == 4 else -70
            a["leg_f"] = a["leg_n"] - 6; a["shin_f"] = a["shin_n"]; a.update(neck=14, head=6)
            st.update(x=SEAT_A, where="window", sit=0.5 if k == 4 else 0.8, note="lowers onto the seat")
        else:
            a = sit_angles(lean=0); a.update(neck=4, head=2)
            if d >= 75:
                a.update(torso=5, neck=8, head=4)     # 6.25: the bus pulls away; he sways back
            st.update(x=SEAT_A, where="window", sit=1.0, note="A6 seated" if d == 66 else "seated in the vacated seat")
    st["ang"] = a
    return st


def jostler_keys(d):
    a = None; st = dict(hands={}, mode="platform", note="")
    if d < 12:                                          # runs along the bus toward the platform
        a = run_angles(d + 1, lean=-15, amp=1.05); st.update(mode="street", x=468.0 + d * 11.0, note="runs for the platform")
    elif d == 12:                                       # 1.00 foot on the step
        a = run_angles(0, lean=-18); a.update(leg_n=62, shin_n=-62, leg_f=-26, shin_f=-34, arm_n=40, arm_f=-40)
        st.update(mode="step", x=604.0, note="A2 foot on the step")
    elif d == 13:                                       # anticipation: arm cocked back, weight low
        a = dict(torso=-20, leg_n=44, shin_n=-44, leg_f=-28, shin_f=-26, arm_n=-30, fore_n=96, arm_f=-34, fore_f=60, neck=6, head=6)
        st.update(x=624.0, note="anticipation: arm cocked")
    elif d in (14, 15, 16):                             # contact: the flat hand drives into the man
        ext = {14: 0, 15: 6, 16: 9}[d]
        a = dict(torso=-24 - ext * 0.5, leg_n=34, shin_n=-30, leg_f=-30, shin_f=-14, arm_n=92, fore_n=4, arm_f=-36, fore_f=60, neck=8, head=8)
        st["hands"] = {"fore_n": "farm_flat"}; st.update(x=None, note="A3 shove (contact)" if d == 14 else "drives through")
    elif d < 29:                                        # recoil: arm withdrawn, regains balance
        u = min(1.0, (d - 17) / 3)
        a = dict(torso=-16 + 12 * u, leg_n=24 - 12 * u, shin_n=-20 + 10 * u, leg_f=-24 + 16 * u, shin_f=-10, arm_n=70 - 66 * u,
                 fore_n=20 + 10 * u, arm_f=-20 + 22 * u, fore_f=30, neck=4, head=0)
        st.update(x=640.0 + 2 * u, note="recoil, regains balance")
    elif d < 39:                                        # shrug
        k = d - 29; up = 1.0 if 2 <= k < 8 else 0.4
        a = dict(torso=-4, leg_n=10, shin_n=-8, leg_f=-8, shin_f=-6, arm_n=-16 * up + 6, fore_n=110 * up + 10, arm_f=10, fore_f=100 * up,
                 neck=-10 * up, head=14 * up)
        st["hands"] = {"fore_n": "farm_open" if up == 1 else "farm_fist", "fore_f": "farm_open" if up == 1 else "farm_fist"}
        st.update(x=642.0, note="shrugs")
    else:                                               # rides the platform, looking out
        a = dict(torso=-2, leg_n=8, shin_n=-6, leg_f=-6, shin_f=-4, arm_n=-14, fore_n=40, arm_f=12, fore_f=20, neck=0, head=-4)
        if d >= 75:
            a.update(torso=5, neck=6, head=2)
        st.update(x=642.0, note="rides the platform")
    st["ang"] = a
    return st


def conductor_keys(d):
    """Conductor: emerges from the bulkhead after the man ducks in, rings the bell at A7 6.00 (d72)."""
    a = stand_angles(); a.update(arm_n=-6, fore_n=30, arm_f=4, fore_f=40)
    st = dict(x=None, hands={}, visible=False, pull=0.0, note="inside (not visible)")
    if d >= 60:
        k = d - 60
        if k < 6:
            a = run_angles(k + 2, lean=-4, amp=0.42, arm=0.35, fore=40); st.update(x=612.0 + k * 9.0)
            st["note"] = "steps out of the bulkhead"
        else:
            st.update(x=664.0)
            if d == 70:
                a.update(arm_n=118, fore_n=30, head=-10, neck=-8); st["note"] = "reaches for the bell cord"
            elif d in (71, 72, 73):
                a.update(arm_n=136, fore_n=20, head=-12, neck=-10); st["hands"] = {"fore_n": "farm_grip"}
                st.update(pull=1.0 if d >= 72 else 0.4, note="A7 bell: pulls the cord" if d == 72 else "pulls")
            elif d >= 74:
                a.update(arm_n=150, fore_n=12, head=-4, neck=-2); st["hands"] = {"fore_n": "farm_grip"}
                st["note"] = "holds the canopy rail as the bus pulls away"
            else:
                st["note"] = "on the platform"
        st["visible"] = True
    st["ang"] = a
    return st


def _man_P(d, dx=0.0):
    g = geo(); k = man_keys(d)
    P = dict(id="man", kind="man", protected=True, s=MAN_S, facing=-1, ang=k["ang"], hands=k["hands"], head_flip=k["flip"],
             x=k["x"] + dx, tip=0.0, z=MAN_Z, group="window" if k["where"] == "window" else "platform",
             clip="window" if k["where"] == "window" else ("inside" if k["where"] == "inside" else None),
             note=k["note"], seated=bool(k["sit"]))
    if k["where"] == "window":
        win = g["win"]
        sill = win["y1"]
        if k["sit"]:
            P["y"] = sill + 30.0 + (1 - float(k["sit"])) * 12.0
        else:
            P["y"] = g["floor"] - 0.0
            place_on(P, g["floor"] + 2.0)
        P["plan_visible"] = False
    else:
        place_on(P, g["floor"])
        low = lowest(P) / MAN_S
        P["pivot"] = (0.0, low); P["tip"] = k["tip"]      # tips back about the heels
        # contact plane: the stanchion stops his back (never interpenetrates it)
        polys, _, _ = parts_world(P)
        back = max(p[:, 0].max() for z, n, p in polys if n in ("torso", "tail"))
        lim_x = geo()["stx"] + dx - 0.3
        if k.get("contact") or back > lim_x:
            P["x"] += lim_x - back
            P["contact"] = True
        P["plan_visible"] = k["where"] == "platform" or (P["x"] - dx) > g["plat0"]
    return P


def _hand_tip(P, part="fore_n"):
    polys, pins, pt = parts_world(P)
    for z, n, p in polys:
        if n == part:
            return p
    return None


def _jostler_P(d, dx=0.0):
    g = geo(); k = jostler_keys(d)
    P = dict(id="jostler", kind="jostler", protected=True, s=JOS_S, facing=1, ang=k["ang"], hands=k["hands"], z=JOS_Z,
             group="platform", clip=None, note=k["note"], plan_visible=True)
    if k["mode"] == "street":
        P["x"] = k["x"] + dx * 0 ; P["z"] = 262.0
        place_on(P, stage().side_ground_y(262.0), lift=LIFT[(d + 1) % 6] * JOS_S)
        P["on_bus"] = False
        P["plan_visible"] = True
        return P
    P["on_bus"] = True
    gy = g["step"] if k["mode"] == "step" else g["floor"]
    if k["x"] is None:                                   # contact constraint: palm on the man's chest
        M = _man_P(d, 0.0)
        mp = _hand_tip(M, "torso")
        chest = mp[:, 0].min() + 1.0                     # man faces -x: his chest is his min-x edge
        P["x"] = 0.0; place_on(P, gy)
        hp = _hand_tip(P, "fore_n")
        P["x"] = chest - hp[:, 0].max() + 0.6
    else:
        P["x"] = k["x"]
    P["x"] += dx
    place_on(P, gy)
    if k["mode"] == "step":
        P["z"] = 236.0
    return P


def _conductor_P(d, dx=0.0):
    g = geo(); k = conductor_keys(d)
    if not k["visible"]:
        return None, 0.0
    P = dict(id="conductor", kind="conductor", protected=True, s=CON_S, facing=1, ang=k["ang"], hands=k["hands"], z=CON_Z,
             group="platform", clip="inside", x=k["x"] + dx, note=k["note"], plan_visible=True)
    place_on(P, g["floor"])
    return P, k["pull"]


# ------------------------------------------------------------------ seeded (unprotected) elements
@functools.lru_cache(None)
def runners_spec(seed):
    """Crowd of 6-8 runners: count, kinds, depth, arrival x, timing, stride, phase from rng(seed, 'runner', i)."""
    rc = rng(seed, "runners")
    n = 6 + int(rc.randint(0, 3))
    kinds_r = rng(seed, "runner-kinds")
    order = list(kinds_r.permutation(len(RUN_KINDS)))
    out = []
    for i in range(n):
        r = rng(seed, "runner", i)
        z = float(r.uniform(*stage().WORLD["runner_z"]))
        gy = stage().side_ground_y(z)
        s = float(r.uniform(0.94, 1.08) * (gy / 440.0))
        out.append(dict(i=i, kind=RUN_KINDS[order[i % len(order)]], z=z, gy=gy, s=s,
                        stop_x=float(552 - i * 50 + r.uniform(-16, 16)),
                        t_arr=float(1.0 + 0.09 * i + r.uniform(-0.04, 0.05)) if i < 3 else float(1.15 + 0.16 * i + r.uniform(-0.06, 0.1)),
                        amp=float(r.uniform(0.88, 1.18)), lean=float(r.uniform(-18, -9)), arm=float(r.uniform(0.75, 1.15)),
                        fore=float(r.uniform(60, 100)), phase=int(r.randint(0, 6)), idle=int(r.randint(0, 1000)),
                        chase=bool(r.rand() < 0.45) and i < 3, hold_hat=bool(r.rand() < 0.25)))
    return out


@functools.lru_cache(None)
def _runner_track(seed, i):
    """Per-drawing (x, angles, lift, mode) for runner i, with the contact foot locked on the ground."""
    R = runners_spec(seed)[i]
    d_arr = int(round(R["t_arr"] * 12))
    rows = [None] * ND
    # run segment: march forward from x=0 with foot locking, then shift so the arrival drawing hits stop_x
    xs = [0.0]; prev_foot = None
    for d in range(0, d_arr + 1):
        k = d + R["phase"]
        ang = run_angles(k, R["lean"], R["amp"], R["arm"], R["fore"])
        if R["hold_hat"]:
            ang.update(arm_n=150, fore_n=110)
        P = dict(kind=R["kind"], ang=ang, s=R["s"], facing=1, x=0.0, y=0.0)
        place_on(P, R["gy"])
        fn, ff = foot_x(P, "shin_n"), foot_x(P, "shin_f")
        polys, _, _ = parts_world(P)
        lown = max(p[:, 1].max() for z, n, p in polys if n == "shin_n")
        lowf = max(p[:, 1].max() for z, n, p in polys if n == "shin_f")
        cont = ("n", fn) if lown >= lowf else ("f", ff)
        if d == 0:
            x = 0.0
        elif prev_foot and prev_foot[0] == cont[0]:
            x = xs[-1] + (prev_foot[1] - cont[1])           # planted foot stays put
            x = max(x, xs[-1] + 4.0 * R["s"])
        else:
            x = xs[-1] + 26.0 * R["s"] * R["amp"]           # flight / foot change: carried forward
        if d > 0:
            xs.append(x)
        prev_foot = (cont[0], cont[1] + 0.0)
        prev_foot = (cont[0], cont[1])
        rows[d] = dict(x=x, ang=ang, lift=LIFT[k % 6] * R["s"], mode="run")
    shift = R["stop_x"] - rows[d_arr]["x"]
    for d in range(d_arr + 1):
        rows[d]["x"] += shift
    # brake (2 drawings), then idle holds with seeded weight shifts; optional chase after the bus
    ri = rng(seed, "runner-idle", i)
    x_end = R["stop_x"]
    idle_pose = None; hold_left = 0
    for d in range(d_arr + 1, ND):
        k = d - d_arr
        if k == 1:
            ang = run_angles(0, lean=4, amp=0.9); ang.update(arm_n=-30, arm_f=40, neck=-6, head=-4)
            rows[d] = dict(x=x_end + 14 * R["s"], ang=ang, lift=0.0, mode="brake"); continue
        if k == 2:
            ang = stand_angles(lean=2); ang.update(leg_n=18, shin_n=-10, leg_f=-14, arm_n=10, fore_n=40)
            rows[d] = dict(x=x_end + 18 * R["s"], ang=ang, lift=0.0, mode="brake"); continue
        if R["chase"] and d >= 76:
            kk = d - 76 + R["phase"]
            ang = run_angles(kk, R["lean"], R["amp"] * 0.9, R["arm"], R["fore"])
            rows[d] = dict(x=x_end + 18 * R["s"] - (d - 75) * 24 * R["s"], ang=ang, lift=LIFT[kk % 6] * R["s"], mode="chase", facing=-1)
            continue
        if hold_left <= 0 or idle_pose is None:
            v = ri.randint(0, 4)
            ang = stand_angles(lean=float(ri.uniform(-4, 4)))
            if v == 0:
                ang.update(arm_n=60, fore_n=100, neck=-10, head=-8)            # points at the platform
            elif v == 1:
                ang.update(arm_n=-10, fore_n=120, arm_f=-20, fore_f=120)       # hands on hips
            elif v == 2:
                ang.update(leg_n=20, shin_n=-12, arm_n=150, fore_n=100)        # hand on hat
            else:
                ang.update(neck=-14, head=-10)                                  # cranes toward the window
            if R["kind"] in ("runB", "runE"):
                ang["tail"] = 2
            idle_pose = ang; hold_left = int(ri.randint(6, 14))                # snapped holds
        hold_left -= 1
        rows[d] = dict(x=x_end + 18 * R["s"], ang=dict(idle_pose), lift=0.0, mode="stand")
    return rows


@functools.lru_cache(None)
def vacate_choice(seed):
    return "A" if rng(seed, "vacate").rand() < 0.5 else "B"


def _passengers(seed, d, dx):
    """Two seated passengers in the rear pane; seed picks who vacates (3.6-4.6). Seat A is always
    free by 4.6 so the protected man always takes seat A at 5.50 (if B vacates, P1 slides A -> B)."""
    g = geo(); sill = g["win"]["y1"]
    who = vacate_choice(seed)
    out = []
    for pid, kind, seat, s in (("p1", "runD", SEAT_A, 0.76), ("p2", "runE", SEAT_B, 0.74)):
        a = sit_angles(); x = seat; y = sill + 22.0; facing = -1; vis = True; note = "seated"
        leaving = (pid == "p1" and who == "A") or (pid == "p2" and who == "B")
        if leaving and d >= 43:
            k = d - 43
            if k < 3:
                a = sit_angles(lean=-10 * (k + 1)); a.update(leg_n=86 - 20 * k, shin_n=-84 + 20 * k, neck=-6, head=-4)
                y = sill + 22.0 - 8 * (k + 1); note = "rises"
            else:
                kk = k - 3
                a = run_angles(kk, lean=-6, amp=0.35, arm=0.3, fore=40); y = None
                x = seat - 4 - kk * 8.0; note = "leaves the window"
                vis = x > g["win"]["x0"] - 30
        if pid == "p1" and who == "B" and d >= 52:
            k = min(d - 52, 3)
            x = SEAT_A + (SEAT_B - SEAT_A) * (k / 3); a = sit_angles(lean=-6 if k < 3 else 0); note = "slides along the bench"
            if k == 3:
                note = "seated (moved up)"
        if not vis:
            continue
        P = dict(id=pid, kind=kind, protected=False, s=s, facing=facing, ang=a, hands={}, x=x + dx, z=150.0,
                 group="window", clip="window", note=note, plan_visible=False)
        if y is None:
            place_on(P, g["floor"] + 2.0)
        else:
            P["y"] = y
        out.append(P)
    return out


# ------------------------------------------------------------------ secondary dynamics (#41)
class Chain:
    """3-link damped pendulum: the loose cord end. Semi-implicit Euler at 24 Hz with 6 substeps,
    distance projection, and a collision boundary (cannot whip above 75 deg from hanging)."""
    G = 980.0

    def __init__(self, anchor, n=3, seg=6.5):
        self.seg = seg; self.n = n
        self.p = np.array([anchor + np.array([0.0, seg * (i + 1)]) for i in range(n)], float)
        self.v = np.zeros_like(self.p); self.prev = np.array(anchor, float)

    def step(self, anchor, dt, c=7.5, sub=6):
        h = dt / sub; anchor = np.asarray(anchor, float)
        for k in range(sub):
            a_k = self.prev + (anchor - self.prev) * (k + 1) / sub
            self.v += (np.array([0, self.G]) - c * self.v) * h          # v <- v + a h  (semi-implicit)
            old = self.p.copy(); self.p = self.p + self.v * h          # x <- x + v h
            for _ in range(3):
                prev = a_k
                for i in range(self.n):
                    dv = self.p[i] - prev; L_ = np.linalg.norm(dv) + 1e-9
                    self.p[i] = prev + dv / L_ * self.seg; prev = self.p[i]
            prev = a_k
            for i in range(self.n):
                dv = self.p[i] - prev; ang = math.atan2(dv[0], dv[1]); lim = math.radians(75)
                if abs(ang) > lim:
                    ang = math.copysign(lim, ang); self.p[i] = prev + self.seg * np.array([math.sin(ang), math.cos(ang)])
                prev = self.p[i]
            self.v = (self.p - old) / h
        self.anchor_v = (anchor - self.prev) / dt
        self.prev = anchor.copy()

    def energy(self, anchor):
        """Energy in the anchor's frame: kinetic (relative velocity) + potential above hanging rest."""
        rel_v = self.v - getattr(self, "anchor_v", np.zeros(2))
        ke = 0.5 * (rel_v ** 2).sum()
        rest_y = anchor[1] + self.seg * np.arange(1, self.n + 1)
        pe = self.G * (rest_y - self.p[:, 1]).clip(0).sum()
        return float(ke + pe)


class Spring1:
    """1-link angular spring (coat tail) driven by the pelvis acceleration (bus frame)."""
    def __init__(self):
        self.a = 0.0; self.w = 0.0; self.px = None; self.vx = 0.0

    def step(self, x, dt, k=320.0, c=16.0, gain=0.0016):
        vx = 0.0 if self.px is None else (x - self.px) / dt
        acc = (vx - self.vx) / dt; self.px = x; self.vx = vx
        self.w += (-k * self.a - c * self.w - gain * acc) * dt
        self.a += self.w * dt
        return math.degrees(self.a)


def _cord_anchor(P):
    _, _, pt = parts_world(P)
    return pt("hat", CORD_LOCAL)


@functools.lru_cache(None)
def simulate():
    """Run the cord + coat tail through the clip once, in the bus frame (dx = 0). The man is
    protected: no RNG, so the result is seed-independent. Head anchor is the drawn (on-twos) pose,
    passed through a critically damped felt-hat compliance (w0 = 34 rad/s) before driving the chain."""
    dt = 1.0 / FPS
    chain = None; tail = Spring1(); rows = []
    filt = None; fv = np.zeros(2); w0 = 34.0
    for f in range(NF):
        d = f // 2
        M = _man_P(d, 0.0)
        head = _cord_anchor(M)
        if filt is None:
            filt = head.copy()
        for _ in range(6):
            acc = w0 * w0 * (head - filt) - 2 * w0 * fv
            fv = fv + acc * dt / 6; filt = filt + fv * dt / 6
        if chain is None:
            chain = Chain(filt)
            for _ in range(48):
                chain.step(filt, dt)
        chain.step(filt, dt)
        ta = tail.step(M["x"], dt)
        rel = chain.p - filt
        ang = math.degrees(math.atan2(rel[-1][0], rel[-1][1]))
        rows.append(dict(f=f, t=f / FPS, d=d, anchor=head.tolist(), filt=filt.tolist(), cord=(chain.p + (head - filt)).tolist(),
                         energy=chain.energy(filt), end_angle=ang, tail=ta, where=M["group"]))
    return rows


# ------------------------------------------------------------------ POSE
def pose(seed, t):
    """Full pose at clip time t. Puppets snap on twos; the bus slide dx is per frame."""
    seed = int(seed); f = max(0, min(NF - 1, int(round(t * FPS)))); d = drawing(t)
    dx = bus_dx(t)
    sim = simulate()[min(NF - 1, 2 * d)]                    # dynamics sampled on twos
    M = _man_P(d, dx)
    M["ang"] = dict(M["ang"]); M["ang"]["tail"] = M["ang"].get("tail", 0.0) + sim["tail"]
    cord = None
    if M["group"] == "platform" or M["clip"] in ("inside", "window"):
        cord = (np.array(sim["cord"]) + np.array([dx, 0.0])).tolist()
    J = _jostler_P(d, dx)
    C, pull = _conductor_P(d, dx)
    pups = []
    for P in _passengers(seed, d, dx):
        pups.append(P)
    pups.append(M)
    if C is not None:
        pups.append(C)
    pups.append(J)
    # runners (street), far to near
    spec = runners_spec(seed)
    rs = []
    for R in spec:
        row = _runner_track(seed, R["i"])[d]
        ang = dict(row["ang"])
        P = dict(id="runner%d" % R["i"], kind=R["kind"], protected=False, s=R["s"], facing=row.get("facing", 1), ang=ang,
                 hands={"fore_n": "farm_open"} if row["mode"] == "brake" else {}, x=row["x"], z=R["z"], group="street",
                 clip=None, note=row["mode"], plan_visible=True)
        place_on(P, R["gy"], lift=row["lift"])
        P["ground"] = R["gy"]
        rs.append(P)
    rs.sort(key=lambda P: P["z"])
    pups += rs
    return dict(seed=seed, t=float(t), frame=f, drawing=d, dx=dx, puppets=pups, cord=cord,
                cord_visible=M["group"] == "platform" or M["clip"] == "window", bell_pull=pull,
                man_where=M["group"], vacate=vacate_choice(seed), rig_rev=RIG_REV)


def feet(P_or_pose):
    """Street feet (x, ground y) of the runners and jostler (for stage.shadow_slivers)."""
    out = []
    for P in P_or_pose["puppets"]:
        if P["group"] == "street" or (P["id"] == "jostler" and not P.get("on_bus", True)):
            polys, _, _ = parts_world(P)
            for z, n, p in polys:
                if n.startswith("shin"):
                    i = int(np.argmax(p[:, 1]))
                    gy = P.get("ground", p[i, 1])
                    if p[i, 1] > gy - 6:
                        out.append((float(p[i, 0]), float(gy)))
    return out


# ------------------------------------------------------------------ SIDE drawing
def _clip_rect(P, pose_):
    g = geo(); dx = pose_["dx"]
    if P.get("clip") == "window":
        w = g["win"]; return (w["x0"] + dx, w["y0"], w["x1"] + dx, w["y1"])
    if P.get("clip") == "inside":
        return (g["plat0"] + dx + 3.0, 0, W, H)
    return None


def _puppet_mask(P, pose_, cut_braid=True, crop=None):
    """Binary-ish outline mask at SS (full frame, or the bbox `crop` in screen px)."""
    ox, oy = (crop[0], crop[1]) if crop else (0, 0)
    cw, ch = ((crop[2] - crop[0]), (crop[3] - crop[1])) if crop else (W, H)
    im = Image.new("L", (cw * SS, ch * SS), 0); dr = _OffsetDraw(ImageDraw.Draw(im), ox * SS, oy * SS)
    polys, pins, pt = parts_world(P)
    for z, n, p in polys:
        dr.polygon([tuple(q * SS) for q in p], fill=255)
    if P["id"] == "man" and cut_braid:                 # plaited-cord band: a braid of diamonds cut through the crown
        for k in range(6):
            cx = (-6.0 + k * 2.45) * HATS; yb = -2.2 * HATS; e = 1.05 * HATS
            q = [pt("hat", (cx, yb - e)), pt("hat", (cx + e * 0.9, yb)), pt("hat", (cx, yb + e)), pt("hat", (cx - e * 0.9, yb))]
            dr.polygon([tuple(v * SS) for v in q], fill=0)
        if pose_.get("cord") is not None and pose_.get("cord_visible"):
            a0 = pt("hat", CORD_LOCAL)
            pts = [a0] + [np.array(c) for c in pose_["cord"]]
            for i in range(len(pts) - 1):
                wdt = (1.9 - 0.35 * i) * SS
                dr.line([tuple(pts[i] * SS), tuple(pts[i + 1] * SS)], fill=255, width=max(2, int(round(wdt))))
                dr.ellipse([(pts[i + 1][0] - 0.9) * SS, (pts[i + 1][1] - 0.9) * SS, (pts[i + 1][0] + 0.9) * SS, (pts[i + 1][1] + 0.9) * SS], fill=255)
            e_ = pts[-1]                                  # frayed knot at the cord end
            dr.polygon([((e_[0] - 1.6) * SS, (e_[1] - 0.6) * SS), ((e_[0] + 1.6) * SS, (e_[1] - 0.6) * SS), ((e_[0] + 0.8) * SS, (e_[1] + 3.2) * SS), ((e_[0] - 0.8) * SS, (e_[1] + 3.2) * SS)], fill=255)
    m = np.asarray(im, np.float32) / 255.0
    r = _clip_rect(P, pose_)
    if r is not None:
        x0, y0, x1, y1 = [int(round((v - o) * SS)) for v, o in zip(r, (ox, oy, ox, oy))]
        c = np.zeros_like(m); c[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = 1.0
        m *= c
    return m


class _OffsetDraw:
    """ImageDraw proxy that subtracts a crop offset (SS px) from every coordinate."""
    def __init__(self, d, ox, oy):
        self.d, self.ox, self.oy = d, ox, oy
    def _p(self, pts):
        out = []
        for q in pts:
            out.append((q[0] - self.ox, q[1] - self.oy))
        return out
    def polygon(self, pts, **k):
        self.d.polygon(self._p(pts), **k)
    def line(self, pts, **k):
        self.d.line(self._p(pts), **k)
    def ellipse(self, box, **k):
        x0, y0, x1, y1 = box
        self.d.ellipse([x0 - self.ox, y0 - self.oy, x1 - self.ox, y1 - self.oy], **k)


def _group_ok(P, group):
    return group is None or P["group"] == group or (isinstance(group, (tuple, list, set)) and P["group"] in group)


def side_mask(pose_, group=None, ids=None):
    """Outline coverage (0..1, HxW screen px) of the selected puppets in side elevation. It depends
    only on the pose, never on fill or treatment (use it for outline IoU / protected-mask identity)."""
    acc = np.zeros((H, W), np.float32)
    for P in pose_["puppets"]:
        if _group_ok(P, group) and (ids is None or P["id"] in ids):
            bb = _bbox(P, pose_)
            if bb is None:
                continue
            x0, y0, x1, y1 = bb
            m = cv2.resize(_puppet_mask(P, pose_, crop=bb), (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
            acc[y0:y1, x0:x1] = np.maximum(acc[y0:y1, x0:x1], m)
    return acc


@functools.lru_cache(None)
def _grain(seed):
    """Paper-fixed grain that governs ink transfer at the edges (static per seed, never per frame)."""
    r = rng(seed, "puppet-print")
    def sn(sy, sx):
        n = r.rand(H // sy + 3, W // sx + 3).astype(np.float32)
        n = cv2.resize(n, ((W // sx + 3) * sx, (H // sy + 3) * sy), interpolation=cv2.INTER_CUBIC)
        return n[sy:sy + H, sx:sx + W]
    return np.clip(0.55 * sn(2, 6) + 0.45 * r.rand(H, W).astype(np.float32), 0, 1)


def print_puppets(mask_ss, seed):
    """Charcoal-soft relief print of a puppet mask: area downsample, 0.9 px feather, ink-starved edge
    bite from the paper grain, sparse starving in the solids. Returns alpha HxW float."""
    a = cv2.resize(mask_ss, (W, H), interpolation=cv2.INTER_AREA)
    a = cv2.GaussianBlur(a, (0, 0), 0.9)
    gr = _grain(seed)
    edge = np.clip(4 * a * (1 - a), 0, 1)
    a = np.clip(a - 0.30 * edge * (gr - 0.35), 0, 1)
    a = a * (1 - 0.07 * (gr > 0.82))
    return a


def _fill_for(fill, pid):
    if isinstance(fill, dict):
        return fill.get(pid, fill.get("default", INK))
    return INK if fill is None else fill


HALO = (211, 203, 188)   # shade paper: the cleared rim a cutter leaves where a figure crosses a dark block


def _bbox(P, pose_, pad=10):
    polys, _, _ = parts_world(P)
    a = np.concatenate([q for z, n, q in polys])
    if P["id"] == "man" and pose_.get("cord") is not None:
        a = np.concatenate([a, np.array(pose_["cord"])])
    x0, y0 = np.floor(a.min(0) - pad); x1, y1 = np.ceil(a.max(0) + pad)
    x0, y0 = max(0, int(x0)), max(0, int(y0)); x1, y1 = min(W, int(x1)), min(H, int(y1))
    return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None


def _puppet_alpha(P, pose_, seed):
    """Printed alpha of one puppet in its own bbox: (alpha HxW crop, bbox)."""
    bb = _bbox(P, pose_)
    if bb is None:
        return None, None
    x0, y0, x1, y1 = bb
    m = _puppet_mask(P, pose_, crop=bb)
    a = cv2.resize(m, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    a = cv2.GaussianBlur(a, (0, 0), 0.9)
    gr = _grain(seed)[y0:y1, x0:x1]
    edge = np.clip(4 * a * (1 - a), 0, 1)
    a = np.clip(a - 0.30 * edge * (gr - 0.35), 0, 1)
    a = a * (1 - 0.07 * (gr > 0.82))
    return a, bb


def draw_side(layer, pose_or_seed=None, fill=None, group=None, t=None, treatment=None, stage=None, seed=None, halo=True):
    """Print the puppets of `group` (None = all) onto `layer` (PIL RGBA, 960x540), one puppet at a
    time back to front, each with a 1.5 px cleared rim (halo) so overlaps never merge into blobs.
    fill: RGB tuple, HxWx3 array (screen px) or {puppet_id: fill, "default": fill}. Returns the image.
    Also accepts stage.py's sheet call draw_side(img, seed, t, treatment=..., stage=...)."""
    if isinstance(pose_or_seed, (int, np.integer)):
        tt = t if t is not None else (fill if isinstance(fill, (int, float)) else 1.20)
        P_ = pose(int(pose_or_seed), tt)
        fill = INK if treatment in (None, "cut-paper") else _bourse_fill()
        out = draw_side(layer, P_, fill, group="window")
        out = draw_side(out, P_, fill, group="platform")
        return draw_side(out, P_, fill, group="street")
    pose_ = pose_or_seed
    sd = pose_["seed"] if seed is None else seed
    base = np.asarray(layer.convert("RGBA"), np.float32).copy()
    hcol = np.array(HALO, np.float32)
    for P in pose_["puppets"]:
        if not _group_ok(P, group):
            continue
        a, bb = _puppet_alpha(P, pose_, sd)
        if a is None:
            continue
        x0, y0, x1, y1 = bb
        reg = base[y0:y1, x0:x1]
        if halo and P.get("clip") != "window":
            ha = cv2.GaussianBlur(cv2.dilate(a, np.ones((3, 3), np.uint8), iterations=1), (0, 0), 0.6)[..., None]
            ha = np.clip(ha * 1.4, 0, 1) * 0.92
            reg[..., :3] = reg[..., :3] * (1 - ha) + hcol * ha
        fl = _fill_for(fill, P["id"])
        col = fl[y0:y1, x0:x1, :3].astype(np.float32) if isinstance(fl, np.ndarray) else np.array(fl[:3], np.float32)[None, None]
        a3 = a[..., None]
        reg[..., :3] = reg[..., :3] * (1 - a3) + col * a3
        reg[..., 3:] = np.maximum(reg[..., 3:], a3 * 255)
        base[y0:y1, x0:x1] = reg
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGBA")


@functools.lru_cache(None)
def _bourse_fill():
    S = stage()
    g = S._gray(S.BOURSE).astype(np.float32)[560:760, 300:1100]
    g = np.tile(cv2.resize(g, (g.shape[1], g.shape[0])), (4, 2))[:H, :W]
    g = 34 + (g - g.min()) / (np.ptp(g) + 1e-6) * 120
    return np.repeat(g[..., None], 3, 2)


# ------------------------------------------------------------------ PLAN projection
PLAN_SIZE = {   # (hat radius, shoulder half-width (z), shoulder half-depth (x)) in world px (~72.5 px/m)
    "man": (11.5, 17.0, 7.0), "jostler": (10.0, 21.0, 9.0), "conductor": (9.5, 17.0, 7.5),
    "runA": (9.0, 17.0, 7.5), "runB": (9.0, 15.0, 7.0), "runC": (10.0, 16.5, 7.0), "runD": (9.5, 18.0, 8.0), "runE": (12.0, 15.0, 7.0),
}


def plan_parts(P, pose_):
    """Plan forms (screen px): hat disc (+ cord ring for the man), shoulder ellipse, arms, feet.
    x comes from the same side pose (FK); depth from world z; nothing drawn from any RNG."""
    S = stage()
    if not P.get("plan_visible", True):
        return []
    polys, pins, pt = parts_world(P)
    get = {n: p for z, n, p in polys}
    s = P["s"]; z = P["z"]; py = S.plan_xy(0, z)[1]
    hr, sw, sd = PLAN_SIZE.get(P["kind"], (9.5, 16.0, 7.0))
    sh_x = float(np.mean(get["torso"][:, 0]))
    head_x = float(np.mean(get["head"][:, 0]))
    out = []
    def ell(cx, cy, rx, ry, n=28, rot_=0.0):
        th = np.linspace(0, 2 * np.pi, n, endpoint=False)
        return np.stack([cx + rx * np.cos(th), cy + ry * np.sin(th)], 1)
    # feet: toes follow the FK foot x, the two feet sit either side of the body line
    for nm, dz in (("shin_f", -5.5), ("shin_n", 5.5)):
        p = get[nm]; i = int(np.argmax(p[:, 1])); fx = float(p[i, 0]); toe = float(p[:, 0].max() if P["facing"] > 0 else p[:, 0].min())
        cx = (fx + toe) / 2
        out.append(("foot", ell(cx, py + dz, max(4.5, abs(toe - fx) / 2 + 2.5), 2.6)))
    # arms: horizontal reach of each hand from the shoulder (the shove reads as an arm crossing)
    for nm, dz in (("fore_f", -sw * 0.8), ("fore_n", sw * 0.8)):
        p = get[nm]; hx = float(p[:, 0].max() if P["facing"] > 0 else p[:, 0].min())
        x0, x1 = sorted((sh_x, hx))
        if x1 - x0 > 6:
            out.append(("arm", np.array([(x0, py + dz - 2.6), (x1, py + dz - 1.6), (x1 + 0.0, py + dz + 1.6), (x0, py + dz + 2.6)])))
    out.append(("shoulders", ell(sh_x, py, sd + abs(P["ang"].get("torso", 0)) * 0.15, sw)))
    out.append(("hat", ell(head_x, py, hr, hr * 0.96, n=36)))
    if P["id"] == "man":
        out.append(("ring", (head_x, py, hr)))
    return out


def plan_mask(pose_, group=None, ids=None, ss=False, parts=None):
    im = Image.new("L", (W * SS, H * SS), 0); dr = ImageDraw.Draw(im)
    for P in pose_["puppets"]:
        if not (_group_ok(P, group) and (ids is None or P["id"] in ids)):
            continue
        for nm, geo_ in plan_parts(P, pose_):
            if parts is not None and nm not in parts:
                continue
            if nm == "ring":
                cx, cy, r_ = geo_
                for k in range(14):                            # notched cord ring cut into the crown
                    th = 2 * np.pi * k / 14; rr = r_ * 0.66
                    x, y = cx + rr * np.cos(th), cy + rr * np.sin(th)
                    e = 1.15
                    dr.polygon([((x - e) * SS, y * SS), (x * SS, (y - e) * SS), ((x + e) * SS, y * SS), (x * SS, (y + e) * SS)], fill=0)
                # loose cord end: a short tail from the back of the ring, swung by the chain's x offset
                if pose_.get("cord") is not None:
                    c = np.array(pose_["cord"]); a0 = c[0]
                    sw_ = float(c[-1][0] - a0[0])
                    bx = cx + r_ * 0.95 * (1 if P["facing"] < 0 else -1)
                    tail = [(bx, cy - 1.2), (bx + 4 * (1 if P["facing"] < 0 else -1) + sw_ * 0.9, cy + 1.2 + 1.5), (bx, cy + 1.2)]
                    dr.polygon([(x * SS, y * SS) for x, y in tail], fill=255)
                continue
            dr.polygon([tuple(q * SS) for q in geo_], fill=255)
    m = np.asarray(im, np.float32) / 255.0
    return m if ss else cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA)


def draw_plan(layer, pose_, fill=None, group=None):
    """Print the plan forms onto `layer`. Same fill contract as draw_side."""
    base = np.asarray(layer.convert("RGBA"), np.float32).copy()
    m = plan_mask(pose_, group=group, ss=True)
    a = print_puppets(m, pose_["seed"])[..., None]
    fl = _fill_for(fill, "default")
    col = fl[..., :3].astype(np.float32) if isinstance(fl, np.ndarray) else np.array(fl[:3], np.float32)[None, None]
    base[..., :3] = base[..., :3] * (1 - a) + col * a
    base[..., 3:] = np.maximum(base[..., 3:], a * 255)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGBA")


# ------------------------------------------------------------------ compositing helpers (editor may reuse)
def side_frame(seed, t, treatment="cut-paper", fill=None):
    """Reference composite of stage + rig in the documented layer order (cut-paper fill = ink)."""
    S = stage(); P = pose(seed, t); dx = P["dx"]; tr = treatment
    L_ = [S.backdrop(seed, tr), S.crowd(seed, tr), S.bus_shadow(seed, dx), S.shift(S.bus_body(seed, tr), dx)]
    travel = S.bus_x(0) - S.bus_x(min(t, 0.90 - 1 / 12))
    for name in ("front", "rear"):
        tile, (cx, cy) = S.wheel(seed, name, S.wheel_angle_for(travel), tr)
        L_.append((tile, (cx + dx - tile.size[0] / 2, cy - tile.size[1] / 2)))
    img = S.compose(L_)
    fill = INK if fill is None else fill
    img = draw_side(img, P, fill, group="window")
    img = draw_side(img, P, fill, group="platform")
    img.alpha_composite(S.shift(S.bus_front(seed, tr), dx))
    img.alpha_composite(S.shift(S.bell_tassel(seed, P["bell_pull"], tr), dx))
    img.alpha_composite(S.shadow_slivers(seed, "runners", feet(P), 150))
    return draw_side(img, P, fill, group="street"), P


def plan_frame(seed, t, fill=None):
    S = stage(); P = pose(seed, t)
    img = S.plan_stage(seed, t)
    return draw_plan(img, P, INK if fill is None else fill), P


# ------------------------------------------------------------------ anchors, manifest, exposure, tests
PROTECTED = ("man", "jostler", "conductor")


def baseline_manifest():
    return dict(scene="platform-bus encounter", camera="street-side", treatment="cut-paper", seeds=list(SEEDS),
                duration=CLIP, fps=FPS, drawings_per_second=12, size=[W, H],
                generator_rev="kit.py procedural animatic / stage-2 / " + RIG_REV,
                destination="MADELEINE – BASTILLE")


def manifest_sha1(m):
    return hashlib.sha1(json.dumps(m, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def cord_report():
    rows = simulate()
    E = np.array([r["energy"] for r in rows]); ang = np.array([r["end_angle"] for r in rows])
    imp_d = 14
    pre = ang[2 * imp_d]                                   # displayed (on twos) value at the impulse drawing
    disp = [ang[2 * d] for d in range(ND)]
    first = next((d for d in range(imp_d, ND) if abs(disp[d] - pre) > 1.0), None)
    win = slice(2 * imp_d, int(4.33 * FPS))
    peak = float(E[win].max()); peak_f = int(np.argmax(E[win]) + 2 * imp_d)
    f32 = int(round(3.2 * FPS))
    after = E[f32:int(4.33 * FPS)] / peak
    pre_still = float(np.abs(np.diff(ang[:2 * imp_d])).max())
    return dict(
        model="3-link damped chain, semi-implicit Euler, 24 Hz x 6 substeps, damping c=7.5/s, g=980 px/s^2, seg 6.5 px; "
              "driver: drawn head (on twos) through a critically damped felt-hat compliance w0=34 rad/s; bus frame (braking "
              "excluded: declared simplification so the shove is the cord's only cause); sampled on twos (state at frame 2d)",
        impulse_drawing=imp_d, impulse_t=imp_d / 12, first_moving_drawing=first,
        lag_drawings=None if first is None else first - imp_d,
        peak_energy=peak, peak_frame=peak_f, peak_t=peak_f / FPS,
        energy_ratio_at_3_2=float(E[f32] / peak), max_ratio_3_2_to_4_33=float(after.max()),
        max_end_angle_change_before_impulse_deg=pre_still,
        pass_starts_after_impulse=first is not None and first - imp_d >= 1,
        pass_decay_below_2pct_by_3_2=bool(after.max() < 0.02),
        frames=[dict(f=r["f"], t=round(r["t"], 4), d=r["d"], energy=round(r["energy"], 3), ratio=round(r["energy"] / peak, 5),
                     end_angle_deg=round(r["end_angle"], 2), coat_tail_deg=round(r["tail"], 2), man=r["where"]) for r in rows])


def anchors_doc(cr):
    lag = cr["first_moving_drawing"]
    A = [
        dict(id="A0", action="destination legible", role="bus", prop="carved board MADELEINE – BASTILLE", cue="throughout", t=0.0, t_end=CLIP, protected=True),
        dict(id="A1", action="bus slides to its stop; wheels stop turning", role="bus", prop="rotating cut wheels", cue="brake squeal ends", t=0.90, protected=True),
        dict(id="A2", action="runners arrive at the rear platform (crowd of 6-8; count/x/phase seeded)", role="runners + jostler", prop="rear step", cue="footfalls", t=1.00, t_end=1.10, protected=True,
             note="arrival window protected; which runners, how many and where are unprotected (rng(seed,'runner',i))"),
        dict(id="A3", action="shove: the jostler's flat hand drives into the long-necked man's chest", role="jostler -> man", prop="flat hand (thumb out)", cue="thud", t=1.20, protected=True),
        dict(id="A4", action="stanchion contact: his back meets the brass stanchion, neck whips back", role="man", prop="stanchion", cue="click on brass", t=4 / 3, protected=True),
        dict(id="A4c", action="cord swing: loose cord end swings out and decays", role="man (secondary)", prop="plaited-cord hat, 3-link chain", cue="none (visual)",
             t=round(lag / 12, 4) if lag is not None else None, t_end=3.2, protected=True,
             measured=dict(first_moving_drawing=lag, energy_ratio_at_3_2=round(cr["energy_ratio_at_3_2"], 5))),
        dict(id="A5", action="protest: head turns back to the jostler, open hand rises; jostler shrugs", role="man, jostler", prop="open hand", cue="none", t=2.0, t_end=3.2, protected=True),
        dict(id="A5v", action="seat vacated: one seated passenger rises and leaves the rear pane (which one is seeded; seat A always ends free)", role="passengers p1/p2", prop="rear-pane bench", cue="none", t=3.6, t_end=4.6, protected=False),
        dict(id="A5d", action="duck-in: the man stoops through the bulkhead", role="man", prop="bulkhead", cue="none", t=52 / 12, t_end=5.0, protected=True),
        dict(id="A6", action="seat taken: the man sits in seat A, seen in the rear pane", role="man", prop="rear-pane seat A", cue="none", t=5.50, protected=True),
        dict(id="A6w", action="seat seen through the window", role="man", prop="rear pane", cue="none", t=5.0, t_end=CLIP, protected=True, overhead="predicted lost (under the roof)"),
        dict(id="A7", action="bell: conductor's hand pulls the cord", role="conductor", prop="bell cord tassel (stage.bell_tassel pull)", cue="bell", t=6.00, protected=True),
        dict(id="A8", action="bus pulls away", role="bus", prop="wheels turn again", cue="engine", t=6.20, t_end=CLIP, protected=True),
        dict(id="A-neck", action="long neck legible", role="man", prop="m_neck part (28 units, tapered)", cue="none", t=0.0, t_end=CLIP, protected=True, overhead="predicted lost (0 neck pixels in plan)"),
        dict(id="A-hat", action="cord hat legible", role="man", prop="soft felt hat, braid of 6 cut notches + loose cord end", cue="none", t=0.0, t_end=CLIP, protected=True,
             overhead="reads as a notched ring + short cord tail"),
    ]
    for a in A:
        a["drawing"] = drawing(a["t"]) if a.get("t") is not None else None
        a["frame"] = int(round(a["t"] * FPS)) if a.get("t") is not None else None
    m = baseline_manifest()
    return dict(
        schema="EventAnchor {id, action, role, prop, cue, t} (+ t_end, drawing, frame, protected)",
        time_base=dict(fps=FPS, drawings="on twos: drawing d = floor(12 t), frames 2d and 2d+1", clip_seconds=CLIP, frames=NF, drawings_n=ND),
        anchors=A, protected_set=[a["id"] for a in A if a["protected"]], protected_puppets=list(PROTECTED),
        unprotected=["runner count (6-8), kinds, x, depth, phase, stride, idle holds, chase", "which seated passenger vacates (p1 or p2)",
                     "print grain (per seed, never per frame)"],
        rng="rng(seed, element_id...) = sha1(('rig', seed) + key) -> RandomState; drawn only for unprotected elements; never by any renderer/projector",
        baseline_manifest=m, baseline_manifest_sha1=manifest_sha1(m),
        manifest_canonical_form="json.dumps(m, sort_keys=True, separators=(',', ':'), ensure_ascii=False), sha1 of UTF-8",
        stage_geometry_used=geo()["an"],
        evidence=[
            dict(id="H-rig-parts", kind="handmade", what_it_shows="hand-placed closed Catmull-Rom part outlines for 8 puppet kinds (man, jostler, conductor, 5 runner/passenger kinds): coat tails, skirts, hands with thumbs (fist/open/flat/grip replacements), profiles with nose and chin, felt hat with 6 cut braid notches, cord end",
                 made_with="rig/rig.py SHAPES + smooth_closed", local_path=str((RIGDIR / "rig.py").relative_to(ROOT)), license="made for this work", used_as="all side-view puppets"),
            dict(id="H-rig-plan", kind="handmade", what_it_shows="plan forms: hat discs, notched cord ring + cord tail, shoulder ellipses, arm bars, feet", made_with="rig.plan_parts", local_path=str((RIGDIR / "rig.py").relative_to(ROOT)), license="made for this work", used_as="overhead condition"),
            dict(id="H-rig-dyn", kind="handmade", what_it_shows="3-link cord chain + coat-tail spring simulation", made_with="rig.Chain, rig.Spring1", local_path=str((RIGDIR / "cord-energy.json").relative_to(ROOT)), license="made for this work", used_as="secondary motion, I7 evidence"),
            dict(id="F-bourse-fill (compat only)", kind="foraged (not new)", title="Greve des autobus - Place de la Bourse (Peyriras, 1933)", license="Public domain (Commons tag; see stage/stage-evidence.json)",
                 source_url="see stage/stage-evidence.json", local_path="films/sources/mauro-martino-exercises-in-style/commons/bourse1933.jpg", verified_date_or_place="re-verified by U2 stage unit 2026-11-17 (Commons extmetadata)",
                 used_as="only in draw_side's stage-sheet compatibility call for photographic-plate fill; the editor supplies the real fill"),
        ],
        absences=["This unit foraged nothing new: the rig is wholly handmade. No sound was foraged here (U1/editor own the bed and bell)."], rig_module=str((RIGDIR / "rig.py").relative_to(ROOT)),
        rig_py_sha1=hashlib.sha1((RIGDIR / "rig.py").read_bytes()).hexdigest(),
        stage_py_sha1=hashlib.sha1((WS / "stage/stage.py").read_bytes()).hexdigest(),
    )


def _r(v, n=2):
    return round(float(v), n)


def exposure_doc():
    def ent(P):
        return dict(id=P["id"], kind=P["kind"], x=_r(P["x"]), y=_r(P["y"]), s=_r(P["s"], 3), facing=P["facing"],
                    tip=_r(P.get("tip", 0)), ang={k: _r(v, 1) for k, v in P["ang"].items()}, hands=P.get("hands", {}),
                    head_flip=bool(P.get("head_flip", False)), group=P["group"], clip=P.get("clip"), z=_r(P["z"], 1), note=P.get("note", ""))
    prot, seeded = [], {str(s): [] for s in SEEDS}
    for d in range(ND):
        t = d / 12
        Pz = pose(SEEDS[0], t)
        prot.append(dict(d=d, t=_r(t, 4), frames=[2 * d, 2 * d + 1], bell_pull=Pz["bell_pull"],
                         puppets=[ent(P) for P in Pz["puppets"] if P["id"] in PROTECTED]))
        for s in SEEDS:
            Ps = pose(s, t)
            seeded[str(s)].append(dict(d=d, puppets=[ent(P) for P in Ps["puppets"] if P["id"] not in PROTECTED]))
    return dict(
        note="Exposure sheet, 7.0 s clip, on twos (84 drawings). x is the screen x at the drawing's first frame; platform puppets "
             "ride the bus layer slide dx(t) which is per frame (pose() adds it), so their x here includes dx(2d/24). "
             "Angles in degrees (+ swings a hanging limb toward the facing direction). Run cycle: 6 drawings, long stride, "
             "contact foot locked to the ground.",
        run_cycle=dict(drawings=6, thigh_shin=RUN, lift=LIFT), protected=prot, seeded=seeded,
        runners={str(s): runners_spec(s) for s in SEEDS}, vacate={str(s): vacate_choice(s) for s in SEEDS})


def rig_tests():
    lim_log = []; gaps = []; inside_fail = []
    for s in SEEDS:
        for d in range(ND):
            for P in pose(s, d / 12)["puppets"]:
                polys, pins, pt = parts_world(P, lim_log)
                get = {n: p for z, n, p in polys}
                for name, (pp, cp, parent) in pins.items():
                    gaps.append(float(np.linalg.norm(pp - cp)))
                    if parent == "root":
                        continue
                    for nm in (name, parent):
                        if nm in get and cv2.pointPolygonTest(get[nm].astype(np.float32).reshape(-1, 1, 2), (float(cp[0]), float(cp[1])), False) < 0:
                            inside_fail.append((s, d, P["id"], name, nm))
    # protected-mask identity across seeds, every frame (C4)
    diff_max = 0.0
    for f in range(0, NF):
        t = f / FPS
        a = side_mask(pose(SEEDS[0], t), ids=PROTECTED); b = side_mask(pose(SEEDS[1], t), ids=PROTECTED)
        diff_max = max(diff_max, float(np.abs(a - b).max()))
    # twos: frames 2d and 2d+1 carry the same drawing (only the bus slide dx may differ)
    twos_ok = True
    for d in range(ND):
        p0, p1 = pose(SEEDS[0], 2 * d / FPS), pose(SEEDS[0], (2 * d + 1) / FPS)
        for A_, B_ in zip(p0["puppets"], p1["puppets"]):
            if A_["ang"] != B_["ang"] or (A_["group"] == "street" and A_["x"] != B_["x"]):
                twos_ok = False
    h1 = hashlib.sha1(repr(pose(417, 1.2)["puppets"]).encode()).hexdigest()
    h2 = hashlib.sha1(repr(pose(417, 1.2)["puppets"]).encode()).hexdigest()
    spec = {str(s): len(runners_spec(s)) for s in SEEDS}
    return dict(pin_gap_max_px=max(gaps), pin_gap_pass=max(gaps) < 0.5, pins_checked=len(gaps),
                pivot_inside_both_parts_failures=len(inside_fail), pivot_inside_examples=inside_fail[:12],
                angle_limit_violations_before_clamp=len(lim_log), limit_examples=[list(map(str, x)) for x in lim_log[:12]],
                protected_mask_max_abs_diff_417_vs_418_all_frames=diff_max, protected_identical=diff_max == 0.0,
                on_twos=twos_ok, deterministic_pose_hash=h1 == h2, runner_counts=spec,
                vacate={str(s): vacate_choice(s) for s in SEEDS})


def neck_plan_pixels(seed=417, t=1.20):
    P = pose(seed, t)
    side = side_mask(P, ids=("man",))
    man = [q for q in P["puppets"] if q["id"] == "man"][0]
    neck_only = dict(man); polys, _, _ = parts_world(man)
    nk = [p for z, n, p in polys if n == "neck"][0]
    im = Image.new("L", (W, H), 0); ImageDraw.Draw(im).polygon([tuple(q) for q in nk], fill=255)
    side_neck = int((np.asarray(im) > 127).sum())
    # plan: the neck has no plan form (vertical part under the hat disc) -> 0 pixels by construction
    return dict(side_neck_px=side_neck, plan_neck_px=0, plan_parts=[n for n, _ in plan_parts(man, P)])


def shove_strip(seed=417, d0=12, n=12):
    tiles_s, tiles_p = [], []
    from PIL import ImageFont
    for d in range(d0, d0 + n):
        t = d / 12 + 1e-6
        im, P = side_frame(seed, t)
        tiles_s.append(im.convert("RGB").crop((560, 168, 760, 418)).resize((300, 375), Image.LANCZOS))
        pm, _ = plan_frame(seed, t)
        tiles_p.append(pm.convert("RGB").crop((560, 210, 760, 340)).resize((300, 195), Image.LANCZOS))
    Wt = 300 * 6
    out = Image.new("RGB", (Wt, 2 * (375 + 195) + 60), (238, 230, 214))
    dr = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype(str(ROOT / "assets/fonts/IBMPlexMono-Regular.ttf"), 15)
    except Exception:
        font = ImageFont.load_default()
    for i in range(n):
        r, c = divmod(i, 6)
        x = c * 300; y = r * (375 + 195 + 30) + 30
        out.paste(tiles_s[i], (x, y)); out.paste(tiles_p[i], (x, y + 375))
        d = d0 + i
        dr.rectangle([x + 4, y - 24, x + 160, y - 4], fill=(34, 33, 31))
        dr.text((x + 8, y - 23), "d%02d  t %.3f" % (d, d / 12), fill=(238, 230, 214), font=font)
    return out


def preview(seed=417, out=None, treatment="cut-paper"):
    import subprocess, tempfile
    out = out or MEDIA / ("rig-preview-%04d.mp4" % seed)
    with tempfile.TemporaryDirectory() as td:
        for f in range(NF):
            im, _ = side_frame(seed, f / FPS, treatment)
            im.convert("RGB").save(f"{td}/f{f:04d}.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{td}/f%04d.png",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(out)], check=True)
    return out


def main(argv):
    MEDIA.mkdir(parents=True, exist_ok=True)
    if "--preview" in argv:
        for s in SEEDS:
            print(preview(s))
        return
    cr = cord_report()
    (RIGDIR / "cord-energy.json").write_text(json.dumps(cr, indent=1))
    doc = anchors_doc(cr)
    T = rig_tests(); T["neck"] = neck_plan_pixels(); T["cord"] = {k: v for k, v in cr.items() if k != "frames"}
    doc["tests"] = T
    (RIGDIR / "anchors.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    (RIGDIR / "exposure.json").write_text(json.dumps(exposure_doc(), ensure_ascii=False, separators=(",", ":")))
    strip = shove_strip(); strip.save(RIGDIR / "shove-strip.png"); strip.save(MEDIA / "shove-strip.png")
    for t in (0.5, 1.2, 1.333, 2.6, 4.0, 5.0, 5.5, 6.0, 6.8):
        for s in SEEDS:
            side_frame(s, t)[0].convert("RGB").save(MEDIA / ("still_%04d_%.2f.png" % (s, t)))
        plan_frame(417, t)[0].convert("RGB").save(MEDIA / ("plan_0417_%.2f.png" % t))
    print(json.dumps({k: v for k, v in T.items() if k != "cord"}, indent=1)); print(json.dumps(T["cord"], indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
