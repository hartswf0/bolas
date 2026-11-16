# Performance unit (U2) for la-mort-en-ce-jardin: FK rig, pose keys, world/possession trace.
#   python3 -I rig.py          -> writes rig.json, poses.json, trace-{L,E,baseline}.json, events.json
# SCION #32 Forward Kinematics: typed joint graph, local transforms composed parent->child, invariant bone lengths,
#   props parented to hand bones.  #48 state machine: plank occupancy / hands / possession law, every frame.
#   #41 secondary dynamics: plank spring (deflection follows the occupant, decays when empty) and hair strands
#   (spring-damper chains driven by the head; simulated in puppets.py).
# World units = wide-shot picture pixels (800x540 picture, puppet scale s = 1). Close shots are camera reframings of
# this world (zoom Z about a world point); the world never jumps between shots (plan section 5.6).
import math, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FPS, POSE_RATE = 24, 12

# ------------------------------------------------------------------ joint graph (SCION #32)
BONES = {  # name: (parent, length in world px at s = 1)
    "spine": ("root", 92), "neck": ("spine", 16), "head": ("neck", 22),
    "upper_f": ("spine", 44), "fore_f": ("upper_f", 42), "hand_f": ("fore_f", 14),
    "upper_n": ("spine", 44), "fore_n": ("upper_n", 42), "hand_n": ("fore_n", 14),
    "thigh_f": ("root", 58), "shin_f": ("thigh_f", 56), "foot_f": ("shin_f", 22),
    "thigh_n": ("root", 58), "shin_n": ("thigh_n", 56), "foot_n": ("shin_n", 22),
}
ORDER = list(BONES)
HAND_OF = {"L": "hand_f", "R": "hand_n"}   # figures face the far bank (right): far hand = left hand, near = right
PROP_ATTACH = {"bag": {"bone_end": True, "offset": [0, -4], "note": "strap hangs from the hand-bone end"},
               "shoe": {"bone_frac": 0.7, "note": "heel in the palm, rotates with the hand bone"},
               "pencil": {"bone_frac": 1.0}}


def fk(root, absd, s=1.0):
    """root (x, y) = hip; absd = absolute bone angles (deg, screen coords: 0 = +x, 90 = down).
    Local transform = abs(child) - abs(parent); composed parent->child.  Returns {bone: (p0, p1, abs_angle)}."""
    W = {"root": (tuple(root), tuple(root), 0.0)}
    for b in ORDER:
        par, L = BONES[b]
        p0 = W[par][1] if par != "root" else tuple(root)
        a = W[par][2] + (absd[b] - (absd[par] if par != "root" else 0.0)) if par != "root" else absd[b]
        W[b] = (p0, (p0[0] + L * s * math.cos(math.radians(a)), p0[1] + L * s * math.sin(math.radians(a))), a)
    return W


def bone_error(J, s=1.0):
    """max |length - L*s| and max child-pivot-to-parent-end gap, per joint."""
    per = {}
    for b, (par, L) in BONES.items():
        (x0, y0), (x1, y1), _ = J[b]
        e = abs(math.hypot(x1 - x0, y1 - y0) - L * s)
        if par != "root": e = max(e, math.dist(J[b][0], J[par][1]))
        else: e = max(e, math.dist(J[b][0], J["root"][1]))
        per[b] = e
    return per


def pose(torso, head, arm_f, arm_n, leg_f, leg_n):
    return dict(spine=torso, neck=torso + (head - torso) * 0.5, head=head,
                upper_f=arm_f[0], fore_f=arm_f[1], hand_f=arm_f[2], upper_n=arm_n[0], fore_n=arm_n[1], hand_n=arm_n[2],
                thigh_f=leg_f[0], shin_f=leg_f[1], foot_f=leg_f[2], thigh_n=leg_n[0], shin_n=leg_n[1], foot_n=leg_n[2])


def arm_to(hip, torso, target, bend=1, hand=None, s=1.0):
    """authoring helper only (2-bone analytic reach); the frames themselves are pure FK of the keyed angles."""
    sh = (hip[0] + 92 * s * math.cos(math.radians(torso)), hip[1] + 92 * s * math.sin(math.radians(torso)))
    l1, l2 = 44 * s, 42 * s
    dx, dy = target[0] - sh[0], target[1] - sh[1]
    D = math.hypot(dx, dy); d = min(max(D, abs(l1 - l2) + 1), (l1 + l2) * 0.999)
    base = math.degrees(math.atan2(dy, dx))
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    a1 = math.degrees(math.acos(max(-1, min(1, c))))
    if bend == "down":
        up = max([base - a1, base + a1], key=lambda q: sh[1] + l1 * math.sin(math.radians(q)))
    else:
        up = base - bend * a1
    e = (sh[0] + l1 * math.cos(math.radians(up)), sh[1] + l1 * math.sin(math.radians(up)))
    tx, ty = sh[0] + dx * d / max(D, 1e-6), sh[1] + dy * d / max(D, 1e-6)
    fo = math.degrees(math.atan2(ty - e[1], tx - e[0]))
    return (up, fo, fo if hand is None else hand)


STAND = ((94, 92, 0), (86, 90, 0))
CROUCH = ((-22, 98, 0), (-10, 104, 0))
SEIZA = ((10, 186, 182), (18, 190, 182))
HIP_ABOVE = {"stand": 114 * 0.995 + 6, "crouch": 40, "seiza": 16}
LEGS = {"stand": STAND, "crouch": CROUCH, "seiza": SEIZA}


def smoothstep(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def key(t, root, absd, gaze=0.0, brow=0.0, mouth=0.0, tag=""):
    return dict(t=round(t, 4), root=[round(root[0], 2), round(root[1], 2)], a={b: round(absd[b], 2) for b in ORDER},
                gaze=gaze, brow=brow, mouth=mouth, tag=tag)


def sample(keys, t):
    """poses on twos: t floored to 1/12 s; root and angles eased (smoothstep) between keys; angles whole degrees."""
    tq = math.floor(t * POSE_RATE + 1e-6) / POSE_RATE
    if tq <= keys[0]["t"]: k0 = k1 = keys[0]; u = 0.0
    elif tq >= keys[-1]["t"]: k0 = k1 = keys[-1]; u = 0.0
    else:
        lo, hi = 0, len(keys) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if keys[m]["t"] <= tq: lo = m
            else: hi = m
        k0, k1 = keys[lo], keys[hi]
        u = (tq - k0["t"]) / (k1["t"] - k0["t"])
        if not (k0.get("linear") and k1.get("linear")): u = smoothstep(u)
    root = (k0["root"][0] + (k1["root"][0] - k0["root"][0]) * u, k0["root"][1] + (k1["root"][1] - k0["root"][1]) * u)
    ab = {}
    for b in ORDER:
        d = (k1["a"][b] - k0["a"][b] + 180) % 360 - 180
        ab[b] = int(round(k0["a"][b] + d * u))
    ex = {q: k0[q] + (k1[q] - k0[q]) * u for q in ("gaze", "brow", "mouth")}
    return (round(root[0], 1), round(root[1], 1)), ab, ex


# ------------------------------------------------------------------ the world (wide-shot coordinates)
N_GROUND, F_GROUND = 392, 384
PLANK_N, PLANK_F = (190.0, 392.0), (690.0, 384.0)
PLANK_DEFL_MAX = 9.0
VERSIONS = {"L": dict(T=36.0, shoe_t0=14.0), "E": dict(T=30.0, shoe_t0=7.0), "baseline": dict(T=36.0, shoe_t0=None)}


def water_y(v, t):
    """water rises 18 px over each version (smaller y = higher water). Tuned so the last crosser's clearance at the
    plank centre is 4 px (L, B) and 6 px (E, C), as in plan section 4."""
    if v == "E": return 421.0 - 18.0 * min(t, 27.1) / 27.1
    return 419.0 - 18.0 * min(t, 32.5) / 32.5


def liana_y(x):
    q = (x + 40) / 900.0
    return 70 + (60 - 70) * q + 40 * math.sin(math.pi * min(max(q, 0), 1))


def plank_top(x, occ_x=None, defl=0.0):
    u = (x - PLANK_N[0]) / (PLANK_F[0] - PLANK_N[0])
    base = PLANK_N[1] + (PLANK_F[1] - PLANK_N[1]) * u
    if occ_x is None or defl == 0: return base
    uo = (occ_x - PLANK_N[0]) / (PLANK_F[0] - PLANK_N[0])
    w = u / uo if u <= uo else (1 - u) / max(1 - uo, 1e-6)          # bends as a 2-segment polyline at the occupant
    return base + defl * min(max(w, 0), 1)


def on_plank_span(x): return PLANK_N[0] + 4 < x < PLANK_F[0] - 4


# ------------------------------------------------------------------ pose builders
def standing(t, x, ground, torso=-90, head=-92, arm_f=(100, 94, 94), arm_n=(80, 86, 86), **ex):
    return key(t, (x, ground - HIP_ABOVE["stand"]), pose(torso, head, arm_f, arm_n, *STAND), **ex)


def walk_keys(t0, t1, x0, x1, who, v, cargo, ground_fn, stride=58.0):
    """walk with weight on (and off) the deflecting plank. Keys on twos (12/s). Far (left) hand rides the liana while
    the walk is on the plank span; the near (right) hand carries cargo: 'bag_high' | 'shoe_chest' | None.
    Hip height solved so the lower boot sole rests on the surface under it: weight = hip drop at double support."""
    keys = []
    n = max(2, int(round((t1 - t0) * POSE_RATE)))
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        u = smoothstep(i / n) * 0.25 + (i / n) * 0.75            # gentle start/stop, mostly constant pace
        x = x0 + (x1 - x0) * u
        phase = ((x - x0) / stride) % 1.0
        sw = math.sin(phase * 2 * math.pi)
        th_f, th_n = 90 - 24 * sw, 90 + 24 * sw
        kb_f = 26 * max(0, math.cos(phase * 2 * math.pi)); kb_n = 26 * max(0, -math.cos(phase * 2 * math.pi))
        legs = ((th_f, th_f + kb_f, 6 * max(0, sw)), (th_n, th_n + kb_n, 6 * max(0, -sw)))
        torso = -84 - 3 * abs(sw)                                   # leans into the step
        hip0 = (x, 0.0)
        on = on_plank_span(x)
        # near arm (right hand): cargo
        if cargo == "bag_high":
            arm_n = arm_to(hip0, torso, (x + 30, -150), bend=-1, hand=-80)
        elif cargo == "shoe_chest":
            arm_n = arm_to(hip0, torso, (x + 26, -58), bend="down", hand=-50)
        else:
            arm_n = (80 + 18 * sw, 70 + 18 * sw, 70 + 18 * sw)
        tmp = pose(torso, -78, (100, 94, 94), arm_n, *legs)
        J0 = fk(hip0, tmp)
        foot_y = max(J0["shin_f"][1][1], J0["shin_n"][1][1]) + 5     # boot sole below the ankle
        foot_x = J0["shin_f"][1][0] if J0["shin_f"][1][1] > J0["shin_n"][1][1] else J0["shin_n"][1][0]
        gy = ground_fn(t, foot_x)
        root = (x, gy - foot_y)
        if on or cargo is not None and (PLANK_N[0] - 30 < x < PLANK_F[0] + 30):
            shx = root[0] + 92 * math.cos(math.radians(torso)); shy = root[1] + 92 * math.sin(math.radians(torso))
            tx = shx + 34
            arm_f = arm_to(root, torso, (tx, liana_y(tx) + 4), bend=1, hand=-96)
        else:
            arm_f = (100 - 18 * sw, 94 - 18 * sw, 94 - 18 * sw)
        tmp = pose(torso, -76 + 2 * sw, arm_f, arm_n, *legs)
        k = key(t, root, tmp, tag=f"walk {who}")
        k["linear"] = True
        keys.append(k)
    return keys


def retrieval_keys(T0, hip_x=172.0, ground=N_GROUND):
    """the shared kneel-reach-grasp-rise sequence (identical keys, relative to the hand-off time T0) for L-S5 and E-S4.
    B faces the plank foot; her far (left) hand gives the bag back to the receiver; her near (right) hand takes the
    heel of the floating shoe; she rises with it held at her chest, well below and in front of her face; her free
    hand rises toward the liana."""
    R = []
    def k(dt, hip, torso, head, far_t, near_t, legs, bf=-1, bn=1, hn=None, hf=None, **ex):
        absd = pose(torso, head, arm_to(hip, torso, far_t, bf, hf), arm_to(hip, torso, near_t, bn, hn), *LEGS[legs])
        R.append(key(T0 + dt, hip, absd, tag=f"retrieve {dt:+.2f}", **ex))
    G = ground
    k(-0.40, (hip_x, G - 40), -72, -56, (160, G - 50), (206, G - 52), "crouch", bf=1, gaze=0.6, brow=0.5)   # sees it
    k(0.00, (hip_x - 6, G - 38), -84, -70, (128, G - 74), (204, G - 54), "crouch", gaze=0.3, brow=0.8,
      mouth=0.4)                                                                                         # pushes the bag back
    k(0.40, (hip_x + 2, G - 32), -62, -44, (196, G - 46), (214, G - 30), "crouch", gaze=1.0, brow=0.6)    # far hand empty; lowers
    k(0.85, (hip_x + 6, G - HIP_ABOVE["seiza"]), -38, -20, (214, G - 26), (220, G - 4), "seiza", gaze=1.0, brow=0.4)  # knees, reach
    k(1.20, (hip_x + 8, G - HIP_ABOVE["seiza"]), -30, -12, (214, G - 26), (228, G + 6), "seiza", hn=24, gaze=1.0,
      brow=0.9, mouth=0.25)                                                                              # grasp: hand over the satin
    k(1.70, (hip_x + 6, G - HIP_ABOVE["seiza"]), -60, -44, (206, G - 70), (232, G - 66), "seiza", gaze=0.8, brow=0.6)  # rises with it
    k(2.20, (hip_x + 4, G - HIP_ABOVE["seiza"]), -84, -74, (208, G - 182), (210, G - 60), "seiza", bf=1, bn="down",
      hn=-40, hf=-96, gaze=0.9, brow=0.2, mouth=0.0)                                                     # at her chest; other hand up
    k(2.60, (hip_x + 4, G - HIP_ABOVE["seiza"]), -86, -78, (208, G - 186), (210, G - 62), "seiza", bf=1, bn="down",
      hn=-40, hf=-96, gaze=0.5, brow=-0.2)
    return R


def receive_keys(T0, hip_x=112.0, ground=N_GROUND, who="C"):
    """the receiver (C in L, A in E) crouched behind her: hands out, takes the bag at T0, pulls it to his chest,
    rises and holds it high (dry)."""
    G = ground; R = []
    def k(dt, hip, torso, head, far_t, near_t, legs, **ex):
        absd = pose(torso, head, arm_to(hip, torso, far_t, -1), arm_to(hip, torso, near_t, -1), *LEGS[legs])
        R.append(key(T0 + dt, hip, absd, tag=f"receive {who} {dt:+.2f}", **ex))
    k(-0.60, (hip_x - 6, G - 40), -84, -84, (140, G - 130), (150, G - 120), "crouch", gaze=0.2)
    k(-0.20, (hip_x, G - 40), -78, -72, (124, G - 72), (130, G - 70), "crouch", gaze=0.4, brow=0.5)
    k(0.00, (hip_x + 2, G - 40), -76, -68, (126, G - 74), (132, G - 72), "crouch", gaze=0.4, brow=0.6, mouth=0.3)
    k(0.50, (hip_x - 8, G - 40), -86, -84, (118, G - 108), (128, G - 100), "crouch", gaze=0.6, brow=0.7)
    hs = (hip_x - 6, G - HIP_ABOVE["stand"])
    absd = pose(-90, -88, arm_to(hs, -90, (hip_x + 10, G - 268), -1, -90), arm_to(hs, -90, (hip_x + 24, G - 262), -1, -90), *STAND)
    R.append(key(T0 + 2.6, hs, absd, tag=f"receive {who} bag high", gaze=0.3, brow=0.8))
    return R


def crouch_write_keys(t0, t1, x, ground=N_GROUND):
    """A crouched at the bank card pencilling the ledger (S2); the near hand moves along the line."""
    R = []
    n = int((t1 - t0) * POSE_RATE / 2)
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        px = x + 30 + 50 * (i / n) + 4 * math.sin(i * 1.7)
        hip = (x, ground - 40)
        absd = pose(-58, -30, arm_to(hip, -58, (x + 28, ground - 18), -1), arm_to(hip, -58, (px, ground - 6), 1, 20), *CROUCH)
        R.append(key(t, hip, absd, tag="write ledger", gaze=1.0))
    return R


def head_turn_keys(base, times_angles):
    """head turns toward the shoe as it drifts in, in 12 fps steps (abs head angle)."""
    out = []
    for t, ha, g in times_angles:
        k = json.loads(json.dumps(base)); k["t"] = t
        k["a"]["head"] = ha; k["a"]["neck"] = (k["a"]["spine"] + ha) / 2; k["gaze"] = g
        k["tag"] = "head turn"; out.append(k)
    return out


# ------------------------------------------------------------------ the three performances (plan section 6)
def ground_N_or_plank(v, occ):
    def g(t, x):
        if x <= PLANK_N[0]: return N_GROUND
        if x >= PLANK_F[0]: return F_GROUND
        return plank_top(x, occ(t), PLANK_DEFL_MAX if occ(t) is not None else 0)
    return g


def build(v):
    T = VERSIONS[v]["T"]
    P = {"A": [], "B": [], "C": []}
    grips = {"A": [], "B": [], "C": []}        # (t, hand, item) changes of grip
    ev = []
    cross = []                                  # (who, t_on, t_off, x0, x1) along the plank, for the deflection
    # crossing schedule (local times)
    if v == "L":
        sched = [("A", 6.0, 12.5, None), ("C", 24.0, 29.6, "bag_high"), ("B", 30.0, 35.0, "shoe_chest")]
    elif v == "E":
        sched = [("B", 15.0, 19.5, "shoe_chest"), ("A", 19.8, 24.4, "bag_high"), ("C", 24.8, 29.4, None)]
    else:
        sched = [("A", 6.0, 12.5, None), ("B", 13.0, 19.5, "bag_high"), ("C", 20.0, 26.5, None)]

    def occ_x(t):
        for who, a, b, _ in sched:
            if a <= t <= b:
                u = smoothstep((t - a) / (b - a)) * 0.25 + ((t - a) / (b - a)) * 0.75
                return 176 + (712 - 176) * u
        return None
    gfn = ground_N_or_plank(v, occ_x)
    F_SPOTS = iter([780, 748, 716])
    walks = {}
    for who, a, b, cargo in sched:
        walks[who] = (a, b, cargo, next(F_SPOTS))
    # ---- per-person timelines
    hfun = lambda x: N_GROUND if x < PLANK_F[0] else F_GROUND

    def walk_bank(who, t0, t1, x0, x1, cargo=None):
        return walk_keys(t0, t1, x0, x1, who, v, cargo, lambda t, x: hfun(x))

    def crossing(who):
        a, b, cargo, fx = walks[who]
        K = walk_keys(a, b, 176, 712, who, v, cargo, gfn)
        K += walk_bank(who, b + 1 / 12, b + 0.9, 712, fx, cargo)
        return K, fx

    shoe_t0 = VERSIONS[v]["shoe_t0"]
    if v in ("L", "baseline"):
        # A: S1 standing, S2 writes the ledger, S3 crosses
        P["A"] += [standing(0.0, 150, N_GROUND)] + crouch_write_keys(3.0, 5.6, 150) + [standing(5.75, 160, N_GROUND)]
        K, fxA = crossing("A"); P["A"] += K
        P["A"].append(standing(b_end(K) + 0.5, fxA, F_GROUND, arm_n=(-150, -110, -100)))
        grips["A"] += [(6.0, "L", "liana"), (12.5 + 0.05, "L", "free")]
        ev += [dict(t=6.0, event="grip", who="A", hand="L", obj="liana"), dict(t=12.55, event="release", who="A", hand="L", obj="liana")]
    if v == "L":
        T0 = 18.4
        # B: bag in her LEFT (far) hand from the start
        P["B"] += [standing(0.0, 110, N_GROUND, arm_f=(96, 92, 92))]
        P["B"] += walk_bank("B", 8.0, 9.5, 110, 172)
        base = standing(9.6, 172, N_GROUND, arm_f=(96, 92, 92))
        P["B"].append(base)
        P["B"] += head_turn_keys(base, [(14.25, -84, 0.0), (14.5, -70, 0.4), (15.5, -66, 0.5), (16.2, -60, 0.6), (17.0, -58, 0.7)])
        P["B"] += retrieval_keys(T0)
        P["B"].append(standing(T0 + 3.4, 176, N_GROUND, arm_n=arm_to((176, 272), -90, (200, 330), "down", -40),
                               arm_f=(100, 94, 94), gaze=0.6))
        P["B"].append(standing(29.9, 176, N_GROUND, arm_n=arm_to((176, 272), -90, (200, 330), "down", -40), arm_f=(100, 94, 94)))
        K, fxB = crossing("B"); P["B"] += K
        # C
        P["C"] += [standing(0.0, 64, N_GROUND, arm_f=(96, 92, 92))]
        P["C"] += walk_bank("C", 9.0, 10.2, 64, 106)
        P["C"].append(standing(10.3, 106, N_GROUND))
        P["C"] += head_turn_keys(P["C"][-1], [(15.5, -70, 0.3), (16.0, -80, 0.0)])   # « Laisse-la. »
        P["C"] += walk_bank("C", 16.6, 17.2, 106, 112)
        P["C"] += receive_keys(T0, 112, who="C")
        P["C"] += walk_bank("C", 23.0, 23.9, 106, 176, "bag_high")
        K, fxC = crossing("C"); P["C"] += K
        P["A"].append(standing(26.5, 780, F_GROUND, arm_n=(-150, -110, -100)))
        # grips and possession
        grips["B"] += [(0.0, "L", "bag"), (T0, "L", "free"), (T0 + 1.2, "R", "shoe"), (30.0, "L", "liana"), (35.05, "L", "free")]
        grips["C"] += [(T0, "R", "bag"), (24.0, "L", "liana"), (29.65, "L", "free")]
        ev += [dict(t=T0, event="handoff", obj="bag", frm="B", to="C", hands=["B.L", "C.R"]),
               dict(t=T0 + 1.2, event="retrieve", obj="shoe", frm="water", to="B", hands=["B.R"]),
               dict(t=24.0, event="grip", who="C", hand="L", obj="liana"), dict(t=29.65, event="release", who="C", hand="L", obj="liana"),
               dict(t=30.0, event="grip", who="B", hand="L", obj="liana"), dict(t=35.05, event="release", who="B", hand="L", obj="liana")]
    if v == "E":
        T0 = 11.4
        P["A"] += [standing(0.0, 150, N_GROUND)] + crouch_write_keys(3.0, 5.6, 150) + [standing(5.75, 160, N_GROUND)]
        P["A"] += walk_bank("A", 6.0, 6.6, 160, 176)
        base = standing(6.7, 176, N_GROUND)
        P["A"].append(base)
        P["A"] += head_turn_keys(base, [(7.25, -84, 0.0), (7.5, -72, 0.4), (8.4, -66, 0.6)])
        P["A"] += walk_bank("A", 9.0, 10.0, 176, 112)                 # steps back from the edge as she comes forward
        P["A"] += receive_keys(T0, 112, who="A")
        P["A"].append(standing(19.0, 106, N_GROUND, arm_f=arm_to((106, 272), -90, (116, 124), -1, -90),
                               arm_n=arm_to((106, 272), -90, (130, 130), -1, -90)))
        P["A"] += walk_bank("A", 19.1, 19.75, 106, 176, "bag_high")
        K, fxA = crossing("A"); P["A"] += K
        P["B"] += [standing(0.0, 110, N_GROUND, arm_f=(96, 92, 92))]
        P["B"].append(standing(7.2, 110, N_GROUND, arm_f=(96, 92, 92)))
        P["B"] += head_turn_keys(P["B"][-1], [(7.5, -70, 0.5)])
        P["B"] += walk_bank("B", 9.0, 10.4, 110, 172)
        P["B"] += retrieval_keys(T0)
        P["B"].append(standing(T0 + 3.0, 176, N_GROUND, arm_n=arm_to((176, 272), -90, (200, 330), "down", -40)))
        P["B"] += walk_bank("B", 14.5, 14.95, 176, 176.01, "shoe_chest")
        K, fxB = crossing("B"); P["B"] += K
        P["C"] += [standing(0.0, 64, N_GROUND, arm_f=(96, 92, 92))]
        P["C"].append(standing(24.0, 64, N_GROUND))
        P["C"] += walk_bank("C", 24.1, 24.75, 64, 176)
        K, fxC = crossing("C"); P["C"] += K
        grips["B"] += [(0.0, "L", "bag"), (T0, "L", "free"), (T0 + 1.2, "R", "shoe"), (15.0, "L", "liana"), (19.55, "L", "free")]
        grips["A"] += [(T0, "R", "bag"), (19.8, "L", "liana"), (24.45, "L", "free")]
        grips["C"] += [(24.8, "L", "liana"), (29.45, "L", "free")]
        ev += [dict(t=T0, event="handoff", obj="bag", frm="B", to="A", hands=["B.L", "A.R"]),
               dict(t=T0 + 1.2, event="retrieve", obj="shoe", frm="water", to="B", hands=["B.R"])]
        for who, a, b, _ in sched:
            ev += [dict(t=a, event="grip", who=who, hand="L", obj="liana"), dict(t=round(b + 0.05, 2), event="release", who=who, hand="L", obj="liana")]
    if v == "baseline":
        P["B"] += [standing(0.0, 110, N_GROUND, arm_f=(96, 92, 92))]
        P["B"] += walk_bank("B", 8.0, 9.5, 110, 172)
        P["B"].append(standing(12.4, 172, N_GROUND, arm_f=(96, 92, 92)))
        hs = (172, N_GROUND - HIP_ABOVE["stand"])
        P["B"].append(standing(12.8, 172, N_GROUND, arm_f=(100, 94, 94), arm_n=arm_to(hs, -90, (200, 130), -1, -80)))   # swaps the bag to her right hand
        K, fxB = crossing("B"); P["B"] += K
        P["C"] += [standing(0.0, 64, N_GROUND)] + walk_bank("C", 9.0, 10.2, 64, 106) + [standing(10.3, 106, N_GROUND), standing(19.2, 106, N_GROUND)]
        P["C"] += walk_bank("C", 19.3, 19.95, 106, 176)
        K, fxC = crossing("C"); P["C"] += K
        grips["B"] += [(0.0, "L", "bag"), (12.75, "R", "bag"), (12.75, "L", "free"), (13.0, "L", "liana"), (19.55, "L", "free")]
        grips["C"] += [(20.0, "L", "liana"), (26.55, "L", "free")]
        ev += [dict(t=12.75, event="hand_swap", who="B", obj="bag", frm="L", to="R"),
               dict(t=13.0, event="grip", who="B", hand="L", obj="liana"), dict(t=19.55, event="release", who="B", hand="L", obj="liana"),
               dict(t=20.0, event="grip", who="C", hand="L", obj="liana"), dict(t=26.55, event="release", who="C", hand="L", obj="liana")]
    for who in P:
        P[who].sort(key=lambda k: k["t"])
        # drop exact duplicate times (later builder wins)
        out = []
        for k in P[who]:
            if out and abs(out[-1]["t"] - k["t"]) < 1e-6: out[-1] = k
            else: out.append(k)
        P[who] = out
    ev.sort(key=lambda e: e["t"])
    return dict(version=v, T=T, keys=P, grips=grips, events=ev, schedule=sched, occ_fn=occ_x)


def b_end(K): return K[-1]["t"]


# ------------------------------------------------------------------ the shoe's drift (approximation of U3's SHOE-DRIFT-1)
def shoe_world(v, t, rest):
    """until grasped: drifts from upstream (frame right) to the plank foot in 3.6 s, then bobs at rest."""
    t0 = VERSIONS[v]["shoe_t0"]
    if t0 is None or t < t0: return None
    u = smoothstep((t - t0) / 3.6)
    x = 860 + (rest[0] - 860) * u
    y = water_y(v, t) - 4 + 2.5 * math.sin(2 * math.pi * (t - t0) / 0.9)
    return (round(x, 2), round(y, 2))


def holders_at(G, t):
    """current grips {who: {L, R}} at time t from the grip-change list (last change at or before t wins)."""
    out = {}
    for who, ch in G.items():
        h = {"L": "free", "R": "free"}
        for (tt, hand, item) in sorted(ch, key=lambda c: c[0]):
            if tt <= t + 1e-9: h[hand] = item
        out[who] = h
    return out


def trace(B):
    """every frame at 24 fps: pose, FK joints (hands, ankles), plank occupancy, grips, holders, water, clearance."""
    v, T = B["version"], B["T"]
    frames = []
    shoe_rest = None
    if v != "baseline":
        T0 = [e for e in B["events"] if e["event"] == "retrieve"][0]["t"]
        r, ab, _ = sample(B["keys"]["B"], T0)
        J = fk(r, ab)
        p0, p1, _ = J["hand_n"]; shoe_rest = (p0[0] + (p1[0] - p0[0]) * .7, p0[1] + (p1[1] - p0[1]) * .7)
    nF = int(round(T * FPS))
    for i in range(nF):
        t = i / FPS
        G = holders_at(B["grips"], t)
        st = dict(i=i, t=round(t, 4), water_y=round(water_y(v, t), 2), people={})
        occ = []
        for who in ("A", "B", "C"):
            r, ab, ex = sample(B["keys"][who], t)
            J = fk(r, ab)
            ank = [J["shin_f"][1], J["shin_n"][1]]
            hands = {"L": J["hand_f"][1], "R": J["hand_n"][1]}
            on = on_plank_span(r[0]) or any(on_plank_span(a[0]) and a[1] > N_GROUND - 40 for a in ank)
            bank = "P" if on else ("N" if r[0] < PLANK_N[0] else "F")
            if on: occ.append(who)
            st["people"][who] = dict(root=list(r), a=ab, bank=bank, grips=G[who],
                                     hands={h: [round(p[0], 2), round(p[1], 2)] for h, p in hands.items()},
                                     ankles=[[round(a[0], 2), round(a[1], 2)] for a in ank], expr={k: round(x, 3) for k, x in ex.items()})
        st["plank_occupant"] = occ
        ox = B["occ_fn"](t)
        st["plank_deflection_px"] = PLANK_DEFL_MAX if ox is not None else 0.0
        if ox is not None:
            st["clearance_px"] = round(st["water_y"] - plank_top(ox, ox, PLANK_DEFL_MAX), 2)
        # holders
        for obj in ("bag", "shoe"):
            hs = [(w, h) for w, p in st["people"].items() for h, it in p["grips"].items() if it == obj]
            if hs: st[obj] = [f"{w}.{h}" for w, h in hs]
            elif obj == "shoe":
                sp = shoe_world(v, t, shoe_rest) if shoe_rest else None
                st[obj] = ["water"] if sp else []
                if sp: st["shoe_pos"] = list(sp)
            else: st[obj] = []
        # bag bottom (hangs ~70 px below the hand point when carried low, held high on crossing)
        if st["bag"] and st["bag"][0] != "water":
            w, h = st["bag"][0].split(".")
            hp = st["people"][w]["hands"][h]
            st["bag_bottom_y"] = round(hp[1] + 70 * 0.95, 2)
        frames.append(st)
    return frames


def main():
    rig = dict(
        scion="#32 Forward Kinematics", units="world px (wide-shot picture px at puppet scale s=1)",
        angle_convention="absolute bone angles in degrees, screen coordinates (0 = +x, 90 = down); local = abs(child) - abs(parent)",
        joint_graph={b: dict(parent=p, length=L) for b, (p, L) in BONES.items()},
        order=ORDER, hands=HAND_OF, prop_attachment=PROP_ATTACH,
        head_card_scale=1.22, pose_rate=POSE_RATE, fps=FPS, quantisation="time floor to 1/12 s, angles rounded to whole degrees",
        invariants=["bone length |L - L0*s| < 0.5 px every frame", "child pivot on parent end < 0.5 px (no head/neck detachment)",
                    "props drawn from the holder's hand bone only"],
        world=dict(N_ground=N_GROUND, F_ground=F_GROUND, plank=[PLANK_N, PLANK_F], plank_capacity=1, plank_deflection_max_px=PLANK_DEFL_MAX,
                   liana="y(x) = 70 - 10q + 40 sin(pi q), q = (x+40)/900", water="see water_y() in rig.py"))
    json.dump(rig, open(HERE / "rig.json", "w"), indent=1)
    allp, allev = {}, {}
    for v in VERSIONS:
        B = build(v)
        fr = trace(B)
        allp[v] = dict(keys=B["keys"], schedule=[list(s) for s in B["schedule"]])
        allev[v] = B["events"]
        json.dump(dict(version=v, fps=FPS, events=B["events"], frames=fr), open(HERE / f"trace-{v}.json", "w"), separators=(",", ":"))
        print(v, len(fr), "frames;", len(B["events"]), "events")
    json.dump(allp, open(HERE / "poses.json", "w"), separators=(",", ":"))
    json.dump(allev, open(HERE / "events.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
