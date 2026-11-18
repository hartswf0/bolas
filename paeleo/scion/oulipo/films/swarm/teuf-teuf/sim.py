"""teuf-teuf: the mechanism fixture for the whole film (mechanic-historian unit).

One load, one push, one wall. This file integrates every moving part at 240 Hz
(dt = 1/240) and samples it at 24 fps into exposure.json, the exposure sheet
the animator renders from and the sound unit times its events against.

World space = layout A: 1280x720, ground y = 566, load front edge x0 = 330 px at 0 m,
100 px/m (8 m reaches x = 1130). y grows downward.

Trials (film time, s):
  drag      push 4.5-11.5   stick-slip, 9 lurches, 1.2 m
  rollers   push 14.0-23.0  three logs under the load travel at v/2; the rear one is squeezed
                            out behind and left; the load waits on two logs (tau 2.2-4.8) while
                            the carrier fetches a fourth and sets it down in front; 3.0 m
  wheel     push 26.0-33.0  wheels on axles in bearings, ease to 8.0 m (stride <= 0.75 m)
  counter   push 35.4-37.0  same cart, axle hold-down pin pulled: wheels free at v/2, rear wheel
                            drops out, platform grinds, ~0.9 m
The push clock tau runs 0-7.0 in every trial. In the rollers trial the shot list (plan 5)
stretches it over 9 s of film (TAU_MAP_ROLLERS); free bodies (a log rolling out, a wheel
falling) always integrate in film time.

Run:  python3 sim.py            -> exposure.json, mechanism.json (asserts), prints a summary
Reads nothing but this file. Writes nothing outside films/swarm/teuf-teuf/.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

# ------------------------------------------------------------------ layout ---
W, H = 1280, 720
FPS = 24
DT = 1 / 240
SUB = 10                        # substeps per frame
DUR = 44.0
NFR = int(DUR * FPS)            # frames 0..NFR-1
GROUND = 566.0
X0 = 330.0                      # load front edge at 0 m
PXM = 100.0
G_PX = 9.81 * PXM               # gravity in px/s^2

# ------------------------------------------------------------------- load ---
STONE_FRONT = 250.0             # local x of the front edge (rear edge = local 0); = layout_wall
HAND_Y = 451.0                  # world y of the upper hand on the load, identical in every trial
HAND_DY = 20.0                  # lower hand 20 px below
RUNNER_H = 14.0                 # sledge runner under the stone (drag)
LIP = 12.0                      # a roller whose centre is < LIP inside the rear edge is squeezed out
CAPTURE = STONE_FRONT - 14.0    # a log on the ground becomes carried when its centre is this far in
LOG_R = 24.0
WHEEL_R = 36.0                  # 0.72 m diameter at 100 px/m (the staged load is not to scale)
AXLE_Y = GROUND - WHEEL_R       # 530
PLAT_BOT = AXLE_Y - 7.0         # 523: platform underside rests on the axle journals
PLAT_TOP = PLAT_BOT - 12.0      # 511: stone bottom on the cart
PLAT_REAR, PLAT_FRONT = 10.0, STONE_FRONT + 14.0     # platform extent, stone-local x (stone overhangs the rear by 10)
WHEEL_REL = {"rear": 28.0, "front": 214.0}           # wheel centres, stone-local x (wheel trial)
STRIDE_MAX = 75.0               # px: one foot's displacement per step <= 0.75 m

# film-time map of the shot list (plan 5)
T_DRAG = (4.5, 11.5)
T_RESET = {"rollers": 12.75, "wheel": 25.0, "counter": 34.0}     # declared cuts (scratch wipe / dissolve)
T_CAM_B = (16.2, 18.8)                                           # oblique close-up x2.2, same instants
TAU_MAP_ROLLERS = [(14.0, 0.0), (16.95, 2.2), (21.0, 4.8), (23.0, 7.0)]
T_WHEEL = (26.0, 33.0)
T_PIN = 34.6
T_COUNTER0 = 35.3
COUNTER_WINDOW = 1.6
T_SIT = (38.6, 39.6)
GHOST_T = {"1.2": 11.7, "3.0": 23.3, "8.0": 33.3}
END_LINE_T = 42.0


def S(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    return a + (b - a) * u


def profile(t, t0, T, dist, ta, td):
    """distance and speed along a push with smoothstep velocity ramps (accel ta, decel td)."""
    V = dist / (T - ta / 2 - td / 2)
    u = t - t0
    if u <= 0:
        return 0.0, 0.0
    if u >= T:
        return dist, 0.0
    if u < ta:
        r = u / ta
        return V * ta * (r ** 3 - r ** 4 / 2), V * S(r)
    xa = V * ta / 2
    if u < T - td:
        return xa + V * (u - ta), V
    r = (T - u) / td
    return dist - V * td * (r ** 3 - r ** 4 / 2), V * S(r)


def tau_rollers(t):
    for (a, ta), (b, tb) in zip(TAU_MAP_ROLLERS, TAU_MAP_ROLLERS[1:]):
        if t <= b:
            return ta + (tb - ta) * max(0.0, (t - a)) / (b - a)
    return 7.0


# ------------------------------------------------------------- the stone ---
def make_stone():
    """the boulder's cut-card outline (local: rear at x 0, bottom at y 0, up is -y);
    identical to the approved test shot and to layout_wall.stone_outline()."""
    rng = np.random.default_rng(1956)
    pts = []
    cx, cy, rx, ry = 125.0, -76.0, 127.0, 80.0
    for t in np.linspace(0, 2 * math.pi, 90, endpoint=False):
        c, s_ = math.cos(t), math.sin(t)
        e = 2.4
        r = (abs(c) ** e + abs(s_) ** e) ** (-1 / e)
        r *= 1 + 0.035 * math.sin(3 * t + 1) + 0.025 * math.sin(7 * t + 0.4) + rng.normal(0, 0.008)
        pts.append((cx + rx * r * c, min(cy + ry * r * s_, 0.0)))
    return pts


STONE = make_stone()
STONE_HASH = hashlib.sha1(np.round(np.array(STONE), 6).tobytes()).hexdigest()


def stone_back_x(yl):
    best = None
    for i in range(len(STONE)):
        (x0, y0), (x1, y1) = STONE[i], STONE[(i + 1) % len(STONE)]
        if (y0 - yl) * (y1 - yl) <= 0 and y0 != y1:
            x = x0 + (x1 - x0) * (yl - y0) / (y1 - y0)
            best = x if best is None else min(best, x)
    return best


def affine(xb, bottom, ang=0.0, pivot=None):
    """stone-local -> world. Rotation `ang` (rad, + = clockwise on screen, nose down) about
    `pivot` (world). Returns [a, b, c, d, e, f]: X = a x + b y + c, Y = d x + e y + f."""
    c_, s_ = math.cos(ang), math.sin(ang)
    if pivot is None:
        pivot = (xb + 125.0, bottom)
    px, py = pivot
    # translate local->world, then rotate about pivot
    a, b, d, e = c_, -s_, s_, c_
    c = px + c_ * (xb - px) - s_ * (bottom - py)
    f = py + s_ * (xb - px) + c_ * (bottom - py)
    return [a, b, c, d, e, f]


def apply(A, x, y):
    return (A[0] * x + A[1] * y + A[2], A[3] * x + A[4] * y + A[5])


# --------------------------------------------------------------- the logs ---
class Log:
    """irregular bark outline radius as a function of body angle (rotates with the log);
    same seeds and law as the approved test shot."""

    def __init__(self, name, R, seed, flat=None):
        self.name, self.R = name, R
        rng = np.random.default_rng(seed)
        self.k = [(rng.uniform(0.03, 0.06), rng.integers(2, 4), rng.uniform(0, 6.28)),
                  (rng.uniform(0.02, 0.04), rng.integers(5, 8), rng.uniform(0, 6.28))]
        self.jit = rng.normal(0, 0.018, 64)
        self.flat = flat

    def r(self, phi):
        phi = np.asarray(phi, dtype=np.float64)
        v = 1.0 + sum(a * np.sin(n * phi + p) for a, n, p in self.k)
        u = (phi % (2 * math.pi)) / (2 * math.pi) * 64
        v = v + np.interp(u, np.arange(65), np.r_[self.jit, self.jit[0]]) * 0.5
        if self.flat is not None:
            d = np.angle(np.exp(1j * (phi - self.flat)))
            v = np.minimum(v, (0.86 / np.maximum(np.cos(np.clip(d, -1.2, 1.2)), 0.3)))
        return self.R * v

    def support(self, theta, direction):
        phis = np.linspace(-0.6, 0.6, 61) + direction
        return float(np.max(self.r(phis - theta) * np.cos(phis - direction)))

    def cy(self, theta):
        return GROUND - self.support(theta, math.pi / 2)

    def top(self, theta):
        return self.cy(theta) - self.support(theta, -math.pi / 2)


LOGS = {"A": Log("A", LOG_R, 11, flat=0.71), "B": Log("B", LOG_R * 1.04, 12),
        "C": Log("C", LOG_R * 0.97, 13), "D": Log("D", LOG_R * 1.02, 14)}
PILE = {"A": 372.0, "B": 425.0, "C": 478.0}        # where the carrier has laid them, ahead of the stone
LAND = {"A": 13.15, "B": 13.35, "C": 13.55}         # each log shoved in under the levered stone
REL0 = {"B": 170.0, "C": 236.0}                     # A's is solved so that it is squeezed out at T_A_REL
T_A_REL = 16.25
A_TH0 = [0.0]                                        # solved in main() so A rests flat facet down
A_RR = 1000.0                                        # rolling resistance of bark on grit, px/s^2
D_REST0 = 700.0                                      # the spare log lies ahead of the work


# ----------------------------------------------------------- drag (stick-slip) ---
def drag_sim():
    """a mass on a sledge runner, driven through the pusher's body (a spring) whose far end
    advances at Vd. Static/kinetic friction gives stick-slip. Vd is bisected so the stone is
    at 1.2 m when the push window closes, with exactly nine slips."""
    w = 2 * math.pi / 0.32              # a slip lasts about half a period, ~0.16 s
    k = w * w
    es = 0.12                           # static friction as spring extension (m); ek solved below
    ek = 0.07

    def run(Vd, record=False):
        nonlocal ek
        x = v = 0.0
        tau = 0.0
        slips, sticking = [], True
        rec = []
        n = int(round(7.0 / DT))
        for i in range(n + 1):
            tau = i * DT
            xd = Vd * tau
            e = xd - x
            if sticking:
                if e * k > es * k:
                    sticking = False
                    slips.append([tau, None, x])
            if not sticking:
                a = k * e - ek * k
                v += a * DT
                x += v * DT
                if v <= 0:
                    v = 0.0
                    sticking = True
                    slips[-1][1] = tau
            if record:
                rec.append((tau, x, v, xd - x))
        return x, slips, rec

    # nine equal lurches of 1.2/9 m; the driver speed puts the ninth slip near tau 6.6 so a tenth
    # would fall after the window closes. Bisect the kinetic level ek for the 1.2 m total.
    d = 1.2 / 9
    Vd = (es + 8 * d) / 6.6
    lo, hi = es - 0.07, es - 0.035
    for _ in range(60):
        ek = (lo + hi) / 2
        x, slips, _ = run(Vd)
        if x > 1.2:
            lo = ek
        else:
            hi = ek
    ek = (lo + hi) / 2
    x, slips, rec = run(Vd, record=True)
    assert len(slips) == 9 and slips[-1][1] is not None, slips
    return Vd, slips, rec, dict(omega=w, es=es, ek=ek)


VD, SLIPS, DRAG_REC, DRAG_PAR = drag_sim()
DRAG_ARR = np.array(DRAG_REC)


def drag_state(t):
    """(x_m, v_m_s, strain_m) of the stone during the drag trial."""
    tau = t - T_DRAG[0]
    if tau <= 0:
        return 0.0, 0.0, 0.0
    if tau >= 7.0:
        x = DRAG_ARR[-1, 1]
        return float(x), 0.0, 0.0
    i = min(len(DRAG_ARR) - 1, int(round(tau / DT)))
    return float(DRAG_ARR[i, 1]), float(DRAG_ARR[i, 2]), float(DRAG_ARR[i, 3])


# --------------------------------------------------------- roller profile ---
R1 = (14.0, 2.95, 150.0, 0.4, 0.35)          # t0, T, dist(px), ta, td: tau 0-2.2 -> 1.5 m
R3 = (21.0, 2.0, 150.0, 0.4, 0.4)            # tau 4.8-7.0 -> +1.5 m
WP = (T_WHEEL[0], 7.0, 800.0, 1.0, 3.0)      # 8.0 m, peak 1.6 m/s


def rollers_front(t):
    x1, v1 = profile(t, *R1)
    x3, v3 = profile(t, *R3)
    return X0 + x1 + x3, v1 + v3


# -------------------------------------------------------- spring (sec. #41) ---
class Spring:
    """semi-implicit Euler spring-damper; moves only after an impulse from a sim event."""

    def __init__(self, name, f, zeta, unit):
        self.name, self.f, self.zeta, self.unit = name, f, zeta, unit
        self.w = 2 * math.pi * f
        self.x = self.v = 0.0
        self.impulses = []
        self.trace = []

    def kick(self, t, amp, cause):
        # velocity impulse sized so the first peak is about `amp`
        wd = self.w * math.sqrt(1 - self.zeta ** 2)
        tp = math.atan2(math.sqrt(1 - self.zeta ** 2), self.zeta) / wd
        peak = math.exp(-self.zeta * self.w * tp) * math.sin(wd * tp) / wd
        self.v += amp / peak
        self.impulses.append({"t": round(t, 4), "amp": amp, "cause": cause})

    def step(self, t):
        self.v += (-self.w ** 2 * self.x - 2 * self.zeta * self.w * self.v) * DT
        self.x += self.v * DT
        self.trace.append((t, self.x, 0.5 * (self.v ** 2 + (self.w * self.x) ** 2)))


SPRINGS = {
    "stone_rock_deg": Spring("stone_rock_deg", 2.2, 0.45, "deg, + = nose down, about the underside middle"),
    "P_head_nod_deg": Spring("P_head_nod_deg", 2.4, 0.42, "deg added to the pusher's head angle"),
    "C_head_nod_deg": Spring("C_head_nod_deg", 2.6, 0.45, "deg added to the carrier's head angle"),
    "rope_sag_px": Spring("rope_sag_px", 2.6, 0.5, "px of extra sag at the rope's middle (static sag 3 px)"),
    "logA_rock_rad": Spring("logA_rock_rad", 3.0, 0.40, "rad, one-sided rock on its flat facet: draw |x|"),
    "logD_sway_deg": Spring("logD_sway_deg", 2.6, 0.5, "deg of the carried log D in the carrier's hands"),
    "platform_bounce_deg": Spring("platform_bounce_deg", 4.0, 0.5, "deg added to the dropped platform's tilt"),
}


# ------------------------------------------------------------------ gait ---
class Gait:
    """planted-foot locks for one figure (#33). Each foot has a nominal place in the stance
    (lead = centre + d*half, trail = centre - d*half). A planted foot never moves. Walking: when
    the trailing foot falls `slack` behind its nominal it swings to the lead nominal plus an
    anticipation of the body's travel during the swing; the step is capped at STRIDE_MAX and kept
    out of `avoid` zones (lying logs, a fallen wheel). Never both feet in the air. Forced re-plants
    (drag slips) and settling steps move the worst-placed foot to its own nominal."""

    def __init__(self, name, x0s, lift=11.0):
        self.name = name
        self.f = [x0s[0], x0s[1]]
        self.swing = [None, None]       # (t0, x0, x1, dur, lift, kind)
        self.plants = []                # (t_lift, t_plant, foot, from, to, kind)
        self.lift = lift
        self.forced = []
        self.y = [0.0, 0.0]

    def teleport(self, xs):
        self.f = list(xs)
        self.swing = [None, None]

    def start(self, i, t, x1, dur, lift=None, kind="step"):
        self.swing[i] = (t, self.f[i], x1, dur, self.lift if lift is None else lift, kind)

    def update(self, t, centre, half, d, speed, avoid, locked=False, explicit=None, slack=10.0):
        out = []
        sd = max(0.15, min(0.32, 0.32 - 0.11 * speed / PXM))
        if explicit is not None:
            for i in range(2):
                ex = explicit[i]
                if ex and ex[0] <= t < ex[1] and self.swing[i] is None and abs(ex[2] - self.f[i]) > 1:
                    self.start(i, ex[0], ex[2], ex[1] - ex[0], lift=8.0, kind="sit")
        idle = self.swing[0] is None and self.swing[1] is None
        if idle and not locked and explicit is None:
            lead_n, trail_n = centre + d * half, centre - d * half
            lead = 0 if (self.f[0] - self.f[1]) * d >= 0 else 1
            trail = 1 - lead
            force = any(abs(ft - t) < DT / 2 for ft in self.forced)
            err_trail = (trail_n - self.f[trail]) * d
            if err_trail > slack and speed > 1.0:
                target = lead_n + d * (slack / 2 + 0.5 * speed * sd)
                if abs(target - self.f[trail]) > STRIDE_MAX:
                    target = self.f[trail] + d * STRIDE_MAX
                target = self._avoid(target, self.f[trail], d, avoid)
                if abs(target - self.f[trail]) > 2.0:
                    self.start(trail, t, target, sd)
            elif force or speed <= 1.0:
                errs = [abs(lead_n - self.f[lead]), abs(trail_n - self.f[trail])]
                j = int(np.argmax(errs))
                i = lead if j == 0 else trail
                nom = lead_n if j == 0 else trail_n
                if (force and errs[j] > 2.0) or errs[j] > 22.0:
                    target = nom
                    if abs(target - self.f[i]) > STRIDE_MAX:
                        target = self.f[i] + math.copysign(STRIDE_MAX, target - self.f[i])
                    target = self._avoid(target, self.f[i], 1 if target > self.f[i] else -1, avoid)
                    self.start(i, t, target, 0.22, lift=7.0, kind="replant")
        for i in range(2):
            sw = self.swing[i]
            if sw is None:
                self.y[i] = 0.0
                continue
            ts, x0, x1, dur, lift, kind = sw
            u = (t - ts) / dur
            if u >= 1:
                self.f[i] = x1
                self.swing[i] = None
                self.plants.append((round(ts, 4), round(t, 4), i, round(x0, 2), round(x1, 2), kind))
                out.append(i)
                self.y[i] = 0.0
            else:
                self.y[i] = lift * math.sin(math.pi * u)
        return out

    def pos(self, i, t):
        sw = self.swing[i]
        if sw is None:
            return self.f[i], GROUND, True
        ts, x0, x1, dur, lift, kind = sw
        u = min(1.0, (t - ts) / dur)
        return x0 + (x1 - x0) * S(u), GROUND - self.y[i], False

    @staticmethod
    def _avoid(target, cur, d, avoid):
        for (a, b) in avoid:
            if a <= target <= b:
                far = b + 2 if d > 0 else a - 2
                near = a - 2 if d > 0 else b + 2
                if abs(far - cur) <= STRIDE_MAX:
                    return far
                return near if (near - cur) * d > 0 else cur
        return target


# ------------------------------------------------------------- the run ---
def solve():
    """integrate everything once at 240 Hz; returns per-frame records and the event list."""
    events = []

    def ev(t, kind, what, **kw):
        e = {"t": round(t, 3), "kind": kind, "event": what}
        e.update(kw)
        events.append(e)

    # ---- drag events
    for n, (a, b, x) in enumerate(SLIPS):
        ev(T_DRAG[0] + a, "slip", f"drag slip {n + 1}: the stone lurches", n=n + 1,
           end=round(T_DRAG[0] + b, 3), x_m=round(x, 4))
        if n >= 1:
            prev_end = T_DRAG[0] + SLIPS[n - 1][1]
            ev(prev_end, "stick", f"drag stick {n + 1} begins (stone holds)", n=n + 1)
    ev(T_DRAG[0], "push-start", "drag push window opens")
    ev(T_DRAG[1], "stop", f"drag push window closes; stone rests at {DRAG_ARR[-1, 1]:.3f} m (thud)")
    for m, tg in GHOST_T.items():
        ev(tg, "ghost", f"white scratched ghost of the stone appears at {m} m")

    # ---- the rollers: solve A's start so that it is squeezed out at T_A_REL
    xa_rel, _ = profile(T_A_REL, *R1)
    rel0 = dict(REL0)
    rel0["A"] = LIP + xa_rel / 2 + 0.01
    th0 = {"A": A_TH0[0], "B": 2.1, "C": -1.0, "D": 0.6}
    return events, rel0, th0, ev


# The roller pass needs the carrier's carry of log D (hold, set down) and the pusher's
# stance (for where A comes to rest), so the figures are solved first for the parts that do
# not depend on A, then the rollers, then the whole thing frame by frame.

# ---------------------------------------------------------------- figures ---
P_HIP_DX = -134.0       # pusher hip relative to his upper hand while pushing
P_SC, C_SC = 1.2, 1.15  # puppet scales (animator's Puppet class: thigh 63s, shin 61s, arms 48s+46s)
LEG = {"P": (63 + 61) * P_SC, "C": (63 + 61) * C_SC}
ARM = {"P": (48 + 46) * P_SC, "C": (48 + 46) * C_SC}
TORSO = {"P": (50 + 46 * 0.82) * P_SC, "C": (50 + 46 * 0.82) * C_SC}

# carrier keys for the log-D carry (film time): pick-up and set-down
T_D_PICK, T_D_LIFT, T_D_WALK1, T_D_CROUCH, T_D_SET, T_D_LET = 16.95, 17.35, 19.15, 19.15, 19.70, 20.05
C_FACE_OFF = 74.0       # held log centre is 74 px in front of the carrier's hip


def track(keys, t):
    """smooth keyframe track [(t, value), ...]"""
    if t <= keys[0][0]:
        return keys[0][1]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t <= b:
            return lerp(va, vb, S((t - a) / (b - a)))
    return keys[-1][1]


def loadstate(t):
    """the load at film time t: mechanism, front x, affine, speed, extras."""
    if t < T_RESET["rollers"]:
        x, v, strain = drag_state(t)
        front = X0 + x * PXM
        bottom = GROUND - RUNNER_H
        return dict(mech="drag", front=front, v=v * PXM, strain=strain * PXM, bottom=bottom, ang=0.0, pivot=None,
                    tau=max(0.0, min(7.0, t - T_DRAG[0])) if t >= T_DRAG[0] else None)
    if t < T_RESET["wheel"]:
        front, v = rollers_front(t)
        return dict(mech="rollers", front=front, v=v, strain=0.0, bottom=None, ang=0.0, pivot=None,
                    tau=tau_rollers(t) if t >= 14.0 else None)
    if t < T_RESET["counter"]:
        x, v = profile(t, *WP)
        return dict(mech="wheel", front=X0 + x, v=v, strain=0.0, bottom=PLAT_TOP, ang=0.0, pivot=None,
                    tau=max(0.0, min(7.0, t - T_WHEEL[0])) if t >= T_WHEEL[0] else None)
    c = counter(t)
    return dict(mech="counter", front=X0 + c["x"], v=c["v"], strain=0.0, bottom=PLAT_TOP, ang=c["ang"],
                pivot=c["pivot"], tau=max(0.0, min(COUNTER_WINDOW, t - T_COUNTER0)) if t >= T_COUNTER0 else None)


# ---------------------------------------------------------- counter-check ---
def counter_sim():
    """the wheel trial's cart and push with the axle hold-down beam removed. The wheels are
    loose under the platform: no-slip at both contacts puts them at v/2. The load follows the
    wheel trial's motion law (same input) until the rear wheel leaves the platform's rear end;
    then the rear end falls (rigid rotation about the front wheel's contact), the platform
    grinds on the ground and kinetic friction stops it."""
    recs = []
    t = T_RESET["counter"]
    x = v = 0.0
    wx = {k: X0 - STONE_FRONT + r for k, r in WHEEL_REL.items()}
    wth = {k: 0.0 for k in wx}
    wstate = {k: "loose" for k in wx}
    wv = {"rear": 0.0, "front": 0.0}
    phase = "rolling"
    ang = angv = 0.0
    events = []
    mu_dec = None
    pivot = None
    while t < DUR + 1e-9:
        if phase == "rolling":
            xn, vn = profile(t, T_COUNTER0, *WP[1:])
            dx = xn - x
            x, v = xn, vn
            for k in wx:
                if wstate[k] == "loose":
                    wx[k] += dx / 2
                    wth[k] += (dx / 2) / WHEEL_R
            xb = X0 - STONE_FRONT + x
            if wx["rear"] - (xb + PLAT_REAR) < -4.0:
                wstate["rear"] = "free"
                wv["rear"] = v / 2
                phase = "falling"
                d = wx["front"] - (xb + PLAT_REAR)
                pivot_rel = wx["front"] - xb
                events.append((t, "wheel-drop", "the loose rear wheel runs out from under the platform's rear end"))
                alpha = 1.5 * G_PX / d
                ang_g = math.atan2(GROUND - PLAT_BOT, d)
                mu_dec = None
        elif phase in ("falling", "grind"):
            # the push stops being useful once the rear end sags: the load decelerates at
            # 2 m/s^2 while the rear end falls, then kinetic friction of the platform's rear end
            # on the ground (solved so that the load stops at ~0.95 m)
            dec = 200.0 if phase == "falling" else mu_dec
            vn = max(0.0, v - dec * DT)
            dx = vn * DT
            x += dx
            v = vn
            xb = X0 - STONE_FRONT + x
            wx["front"] += dx / 2
            wth["front"] += (dx / 2) / WHEEL_R
            if phase == "falling":
                angv += alpha * DT
                ang += angv * DT
                if ang >= ang_g:
                    ang = ang_g
                    angv = 0.0
                    phase = "grind"
                    remain = 0.95 * PXM - x
                    mu_dec = v * v / (2 * max(remain, 5.0))
                    events.append((t, "platform-drop", "the platform's rear end hits the ground (thud), grind begins"))
            if phase == "grind" and v <= 0.0:
                phase = "stopped"
                events.append((t, "stop", f"the wheel-less load grinds to a stop at {x / PXM:.3f} m"))
            pivot = (wx["front"], PLAT_BOT)
        if wstate["rear"] == "free":
            if wv["rear"] > 0:
                nv = max(0.0, wv["rear"] - 450.0 * DT)
                wx["rear"] += wv["rear"] * DT
                wth["rear"] += wv["rear"] * DT / WHEEL_R
                wv["rear"] = nv
                if nv == 0.0:
                    wstate["rear"] = "rest"
                    events.append((t, "wheel-stop", "the fallen rear wheel stops"))
        k = t * FPS
        if abs(k - round(k)) < 1e-6:
            recs.append(dict(t=round(t, 4), x=x, v=v, ang=ang, pivot=pivot,
                             wx=dict(wx), wth=dict(wth), wstate=dict(wstate), phase=phase))
        t = round(t + DT, 10)
    return recs, events


COUNTER_RECS, COUNTER_EVENTS = counter_sim()
_C_IDX = {round(r["t"] * FPS): r for r in COUNTER_RECS}


def counter(t):
    k = int(round(t * FPS))
    r = _C_IDX.get(k)
    if r is None:
        r = min(COUNTER_RECS, key=lambda q: abs(q["t"] - t))
    ang = r["ang"]
    return {"x": r["x"], "v": r["v"], "ang": ang, "pivot": r["pivot"], "r": r}


# =================================================================== build ---
def build():
    events, rel0, th0, ev = solve()

    # ---------- figures: hip / pose tracks -------------------------------------
    def stone_affine(t, L):
        mech = L["mech"]
        xb = L["front"] - STONE_FRONT
        if mech == "rollers":
            bottom = L["bottom"]
        else:
            bottom = L["bottom"]
        return affine(xb, bottom, math.radians(L.get("ang_deg_total", 0.0)), L.get("pivot_total"))

    # pusher's hands: on the stone's rear face at HAND_Y and HAND_Y + HAND_DY (untilted)
    def p_hands_local(bottom):
        out = []
        for dy in (0.0, HAND_DY):
            yl = (HAND_Y + dy) - bottom
            out.append((stone_back_x(yl) + 1.5, yl))
        return out

    # ---------- pass 2: everything, frame by frame at 240 Hz ------------------
    # prepare the roller run with A's target decided from the pusher's stance just before
    # A is squeezed out: A must come to rest between the pusher's feet, well behind the stone
    # (test-shot review: "let the left-behind log come to rest clearly further behind").
    P_g = Gait("P", (-254 + 25, -254 - 25))
    C_g = Gait("C", (554 + 24, 554 - 24))
    frames = []
    footfalls = []

    # roller state integrated alongside
    st = {}
    for n in "ABC":
        st[n] = {"x": PILE[n], "th": th0[n], "state": "absent", "v": 0.0}
    st["D"] = {"x": D_REST0, "th": th0["D"], "state": "absent", "v": 0.0}
    a_target = None
    c_prev = None
    prev_front_r = X0
    a_rel_t = None
    a_stop_t = None
    d_set_x = None

    sp = SPRINGS
    slip_starts = [T_DRAG[0] + a for a, b, x in SLIPS]
    slip_ends = [T_DRAG[0] + b for a, b, x in SLIPS]
    P_g.forced = [e + 0.02 for e in slip_ends]
    C_g.forced = [e + 0.06 for e in slip_ends]
    stop_rollers1 = None
    roll_events = []
    carried_D = False
    prev_bottom = None
    p_lift_req = None
    sit_explicit_P = None
    sit_explicit_C = None
    A_hit_P = None
    lever = lambda t: S((t - 13.0) / 0.125) * (1 - S((t - 13.6) / 0.10))
    settle_kicked = False
    d_pick_x = None

    n_steps = int(round(DUR / DT))
    for i in range(n_steps):
        t = round(i * DT, 10)
        L = loadstate(t)
        mech = L["mech"]
        front = L["front"]
        xb = front - STONE_FRONT

        # ---- springs: impulses from events
        for a in slip_starts:
            if abs(t - a) < DT / 2:
                sp["stone_rock_deg"].kick(t, 1.5, "drag slip")
                sp["P_head_nod_deg"].kick(t, 6.0, "drag slip")
                sp["C_head_nod_deg"].kick(t, -5.0, "drag slip (rope goes slack)")
                sp["rope_sag_px"].kick(t, 9.0, "drag slip (rope goes slack)")
        if abs(t - T_DRAG[1]) < DT / 2:
            sp["P_head_nod_deg"].kick(t, 4.0, "drag stop")

        # ---- the rollers (state machine; free bodies in film time)
        dfront = 0.0
        if mech == "rollers":
            dfront = front - prev_front_r
            prev_front_r = front
        if T_RESET["rollers"] - 1e-9 <= t:
            for n, s in st.items():
                Lg = LOGS[n]
                if s["state"] == "absent":
                    s["state"] = "pile" if n != "D" else "rest"
                if n in LAND and s["state"] == "pile" and t >= LAND[n] - 0.18:
                    s["state"] = "shoved"
                    s["x0"] = s["x"]
                if s["state"] == "shoved":
                    u = S((t - (LAND[n] - 0.18)) / 0.18)
                    nx = lerp(s["x0"], (X0 - STONE_FRONT) + rel0[n], u)
                    s["th"] += (nx - s["x"]) / Lg.R
                    s["x"] = nx
                    if t >= LAND[n] - 1e-9:
                        s["state"] = "carried"
                        ev(t, "log-land", f"log {n} shoved in under the levered stone (knock)", log=n)
                elif s["state"] == "carried" and mech == "rollers":
                    s["x"] += dfront / 2
                    s["th"] += (dfront / 2) / Lg.R
                    if s["x"] - xb < LIP and dfront > 0:
                        s["state"] = "free"
                        a_rel_t = t
                        # A comes to rest between the pusher's planted feet, clear of both
                        rear = min(P_g.f)
                        frontf = max(P_g.f)
                        a_target = rear + 20.0 + 4.0 + Lg.R
                        s["v"] = -math.sqrt(2 * A_RR * max(s["x"] - a_target, 1.0))
                        if a_target + Lg.R + 6 > frontf:
                            p_lift_req = (n, frontf)
                        ev(t, "release", f"log {n} squeezed out behind the stone's rear lip; kicked back at "
                                         f"{-s['v'] / PXM:.2f} m/s", log=n)
                        sp["stone_rock_deg"].kick(t, -0.9, "rear log squeezed out")
                        sp["P_head_nod_deg"].kick(t, -4.0, "rear log squeezed out")
                elif s["state"] == "free":
                    nv = s["v"] + A_RR * DT
                    if nv >= 0:
                        s["v"] = 0.0
                        s["state"] = "rest"
                        a_stop_t = t
                        ev(t, "log-stop", f"log {n} stops on its bark, flat facet down (tok)", log=n,
                           x=round(s["x"], 2), behind_rear_edge_px=round(xb - s["x"], 1))
                        sp["logA_rock_rad"].kick(t, 0.16, "log A stops")
                    else:
                        s["x"] += s["v"] * DT
                        s["th"] += s["v"] * DT / Lg.R
                        s["v"] = nv
                elif n == "D":
                    if s["state"] == "rest" and t >= T_D_PICK - 1e-9 and t < T_D_SET:
                        s["state"] = "held"
                        d_pick_x = s["x"]
                        ev(t, "pickup", "the carrier lifts log D (hands pinned to it)", log="D")
                    if s["state"] == "held":
                        # path: lift, carry left, set down at d_set_x
                        if d_set_x is None:
                            d_set_x = round(X0 + 150.0 + 30.0, 2)       # 30 px ahead of the waiting stone's front
                        u_lift = S((t - T_D_PICK) / (T_D_LIFT - T_D_PICK))
                        u_walk = S((t - T_D_LIFT) / (T_D_WALK1 - T_D_LIFT))
                        u_set = S((t - T_D_CROUCH) / (T_D_SET - T_D_CROUCH))
                        s["x"] = lerp(d_pick_x, d_set_x, u_walk)
                        s["lift"] = 80.0 * u_lift * (1 - u_set)
                        if t >= T_D_SET - 1e-9:
                            s["state"] = "ground"
                            s["lift"] = 0.0
                            s["x"] = d_set_x
                            ev(t, "log-set", "the carrier sets log D down in front of the stone (wood on stone)",
                               log="D", x=d_set_x, ahead_of_front_px=round(d_set_x - front, 1))
                    elif s["state"] == "ground" and mech == "rollers":
                        if s["x"] - xb <= CAPTURE and dfront > 0:
                            s["state"] = "carried"
                            ev(t, "capture", "the stone's nose rides up onto log D", log="D")
                if mech != "rollers" and s["state"] in ("carried", "ground", "held", "pile", "shoved") and t >= T_RESET["wheel"]:
                    s["state"] = "cleared"          # the reset clears B, C, D with the stone; A stays
            if mech == "rollers" and stop_rollers1 is None and t >= 16.95 - 1e-9:
                stop_rollers1 = t
                ev(t, "stop", "the stone stops at 1.5 m on logs B and C and waits (tau 2.2)")
                sp["stone_rock_deg"].kick(t, 0.7, "stone stops on its rollers")
                sp["P_head_nod_deg"].kick(t, 6.0, "stone stops")

        # stone bottom
        if mech == "rollers":
            if t < 13.6:
                lv = lever(t)
                bottom = GROUND - 56.0 * lv
            else:
                tops = [LOGS[n].top(s["th"]) for n, s in st.items() if s["state"] == "carried"]
                support = min(tops) if tops else GROUND
                if t < 13.70:
                    bottom = lerp(GROUND - 56.0, support, S((t - 13.6) / 0.10))
                else:
                    bottom = support
            if not settle_kicked and t >= 13.70 - 1e-9:
                settle_kicked = True
                ev(t, "settle", "the stone settles onto its three logs (tilt spring)")
                sp["stone_rock_deg"].kick(t, -1.2, "stone settles onto logs")
            if 13.0 - 1e-9 <= t < 13.0 + DT / 2:
                ev(t, "lever", "the stone is levered up (3 frames)")
            L["bottom"] = bottom
        if mech == "wheel" and abs(t - T_WHEEL[1]) < DT / 2:
            sp["stone_rock_deg"].kick(t, 0.6, "cart stops")
            sp["P_head_nod_deg"].kick(t, 5.0, "cart stops")
        if mech == "rollers" and abs(t - 23.0) < DT / 2:
            sp["stone_rock_deg"].kick(t, 0.6, "stone stops at 3.0 m")
            sp["P_head_nod_deg"].kick(t, 5.0, "stone stops")
        for (te, kind, what) in COUNTER_EVENTS:
            if abs(t - te) < DT / 2 and kind == "platform-drop":
                sp["platform_bounce_deg"].kick(t, -1.4, "platform hits the ground")
                sp["P_head_nod_deg"].kick(t, 7.0, "platform hits the ground")

        # total load transform
        rock = sp["stone_rock_deg"].x
        if mech == "counter":
            ang = L["ang"] + math.radians(sp["platform_bounce_deg"].x if L["ang"] > 0 else 0.0)
            pivot = L["pivot"]
            A_ = affine(xb, PLAT_TOP, -ang, (pivot[0], PLAT_TOP) if pivot else None) if ang else affine(xb, PLAT_TOP)
        else:
            A_ = affine(xb, L["bottom"], math.radians(rock))

        # ---------- the pusher (P)
        hands_l = p_hands_local(L["bottom"] if mech != "counter" else PLAT_TOP)
        hands_w = [apply(A_, *h) for h in hands_l]
        pin_world = None
        if mech == "counter":
            pin_world = apply(A_, PLAT_REAR + 6.0, PLAT_BOT - PLAT_TOP - 3.0)
        p = {}
        strain = L.get("strain", 0.0)
        hand_x0 = hands_w[0][0]
        push_hip = hand_x0 + P_HIP_DX + 0.6 * max(0.0, strain - 6.0)
        p_mode = "push"
        if t < 3.4:
            p_mode = "walk-in"
            hip_x = lerp(-250.0, push_hip, S(t / 3.4))
        elif t < 4.2:
            p_mode = "lean-in"
            hip_x = push_hip
        elif t >= 38.3:
            p_mode = "sit"
            hip_x = push_hip
        else:
            hip_x = push_hip
        # rest poses: hip y and lean (keys)
        p_hip_y = track([(0, 425), (3.4, 425), (4.2, 462)], t)
        p_lean = track([(0, 8), (3.4, 8), (4.2, 40)], t)
        p_hip_y += (hands_w[0][1] - HAND_Y) * 0.9 if t >= 4.2 else 0.0
        if 34.0 <= t < 35.4:
            # crouch for the pin
            c_ = S((t - 34.25) / 0.35) * (1 - S((t - 35.0) / 0.4))
            p_hip_y = lerp(462, 495, c_)
            p_lean = lerp(40, 52, c_)
        p_facing = 1
        hands_P = [{"x": hands_w[0][0], "y": hands_w[0][1], "pin": "stone"},
                   {"x": hands_w[1][0], "y": hands_w[1][1], "pin": "stone"}]
        if t < 4.2:
            u = S((t - 3.7) / 0.5)
            free = [(hip_x + 18, p_hip_y - 6), (hip_x + 8, p_hip_y + 2)]
            hands_P = [{"x": lerp(free[j][0], hands_w[j][0], u), "y": lerp(free[j][1], hands_w[j][1], u),
                        "pin": "stone" if u >= 1 else "free"} for j in range(2)]
        if mech == "counter" and 34.25 <= t < 35.25:
            # upper hand goes to the hold-down pin, pulls it up 30 px, drops it, returns to the stone
            u_to = S((t - 34.25) / 0.35)
            u_up = S((t - T_PIN) / 0.3)
            u_back = S((t - 34.95) / 0.3)
            px_, py_ = pin_world
            tgt = (px_, py_ - 30 * u_up)
            hx = lerp(lerp(hands_w[0][0], tgt[0], u_to), hands_w[0][0], u_back)
            hy = lerp(lerp(hands_w[0][1], tgt[1], u_to), hands_w[0][1], u_back)
            hands_P[0] = {"x": hx, "y": hy, "pin": "pin" if (u_to >= 1 and u_back <= 0) else ("free" if u_back < 1 else "stone")}
        if abs(t - T_PIN) < DT / 2:
            ev(t, "pin-pull", "the pusher pulls the axle hold-down pin; the beam lifts away (click)")
        # sit on the forgotten log (shot 6)
        aX = st["A"]["x"]
        if t >= 38.3:
            u_rel = S((t - 38.3) / 0.3)
            u_sit = S((t - T_SIT[0]) / (T_SIT[1] - T_SIT[0]))
            free = [(hip_x + 30, p_hip_y - 30), (hip_x + 20, p_hip_y - 10)]
            seat = (aX - 2.0, LOGS["A"].top(st["A"]["th"]) - 8.0)
            hip_x = lerp(push_hip, seat[0], u_sit)
            p_hip_y = lerp(p_hip_y, seat[1], u_sit)
            p_lean = lerp(40, -6, u_sit)
            knee = [(hip_x + 40, p_hip_y - 6), (hip_x + 30, p_hip_y + 2)]
            hands_P = [{"x": lerp(hands_w[j][0], knee[j][0], u_rel if u_sit <= 0 else 1.0) if u_sit <= 0 else lerp(free[j][0], knee[j][0], u_sit),
                        "y": lerp(hands_w[j][1], free[j][1], u_rel) if u_sit <= 0 else lerp(free[j][1], knee[j][1], u_sit),
                        "pin": "free"} for j in range(2)]
            if A_hit_P is None and u_sit >= 1:
                A_hit_P = t
                ev(t, "sit", "the pusher sits on the forgotten log A; it rocks once (tok)", log="A")
                sp["logA_rock_rad"].kick(t, 0.10, "pusher sits on log A")

        # pusher feet (gait); stance relative to the hip in the push pose
        p_centre = (hip_x - 62.0 + 20.0 * min(1.0, abs(L["v"]) / 160.0)) if p_mode != "walk-in" else hip_x - 4.0
        p_half = 25.0
        avoid = []
        if st["A"]["state"] == "rest":
            avoid.append((st["A"]["x"] - LOGS["A"].R - 6, st["A"]["x"] + LOGS["A"].R + 6))
        if mech == "counter":
            r = counter(t)["r"]
            if r["wstate"]["rear"] != "loose":
                avoid.append((r["wx"]["rear"] - WHEEL_R - 4, r["wx"]["rear"] + WHEEL_R + 4))
        for T_r, nm in ((T_RESET["rollers"], "rollers"), (T_RESET["wheel"], "wheel"), (T_RESET["counter"], "counter")):
            if abs(t - T_r) < DT / 2:
                P_g.teleport((p_centre + 25, p_centre - 25))
                ev(t, "cut", f"declared reset cut to the {nm} trial: the load returns to x0 = 0 m", trial=nm)
        # A rolls under the pusher's lead foot: the foot lifts high as the log arrives and
        # re-plants ahead of it (contact changes the next pose, #33)
        if p_lift_req and st["A"]["state"] == "free":
            fi = int(np.argmax(P_g.f))
            toe = P_g.f[fi] + 20.0
            if st["A"]["x"] - LOGS["A"].R < toe + 30 and P_g.swing[fi] is None and P_g.swing[1 - fi] is None:
                dest = a_target + LOGS["A"].R + 8
                P_g.start(fi, t, dest, 0.40, lift=58.0, kind="lift-over-log")
                ev(t, "foot-lift", "the log rolls under the pusher's lead foot; he lifts it and re-plants ahead of the log")
                p_lift_req = None
        explicitP = None
        if t >= T_SIT[0]:
            fr = st["A"]["x"]
            explicitP = [(T_SIT[0], T_SIT[0] + 0.3, fr + 58.0), (T_SIT[0] + 0.4, T_SIT[0] + 0.7, fr + 82.0)]
        speedP = abs(L["v"]) if p_mode != "walk-in" else 60.0
        dP = 1
        lockedP = (mech == "rollers" and 13.0 <= t < 14.0) or (t >= 38.3 and explicitP is None) or \
                  (st["A"]["state"] == "free")
        planted = P_g.update(t, p_centre, p_half, dP, speedP, avoid, locked=lockedP, explicit=explicitP)
        for fi in planted:
            footfalls.append({"t": round(t, 3), "who": "P", "foot": fi, "x": round(P_g.f[fi], 2)})

        # ---------- the carrier (C)
        c_mode = "stand"
        c_face = -1
        c_hip_y, c_lean = 440.0, 6.0
        handsC = None
        if t < T_RESET["rollers"]:
            hip_rope = front + 25.0 + 205.0 + 0.5 * max(0.0, strain - 6.0)
            c_hip = 560.0 if t < 4.5 else hip_rope
            c_face = -1 if t < 3.0 else 1
            c_lean = track([(0, 6), (3.0, 6), (4.2, 32), (11.5, 32), (11.9, 8)], t)
            c_hip_y = track([(0, 440), (3.0, 440), (4.2, 448), (11.5, 448), (11.9, 440)], t)
            c_mode = "haul" if 3.3 <= t < 11.9 else "stand"
        elif t < T_RESET["wheel"]:
            # rollers: shove (13.0-13.6), walk to the spare log, carry it, set it down, step clear
            ckeys = [(12.75, 520.0), (14.2, 520.0), (15.9, d_pick_hip := D_REST0 + C_FACE_OFF)]
            if t < T_D_PICK:
                c_hip = track(ckeys, t)
            elif st["D"]["state"] in ("held",) or t < T_D_LET:
                c_hip = st["D"]["x"] + C_FACE_OFF
            else:
                c_hip = track([(T_D_LET, (d_set_x or 510) + C_FACE_OFF), (20.6, (d_set_x or 510) + C_FACE_OFF), (22.0, 770.0)], t)
            c_face = -1 if (t < 14.0 or 16.0 <= t < 20.5 or t >= 21.8) else 1
            crouch = 0.0
            if t < 14.0:
                crouch = 1.0 - S((t - 13.6) / 0.5)
            elif t < T_D_LIFT:
                crouch = S((t - 16.45) / 0.5) * (1 - S((t - T_D_PICK) / 0.4))
            elif t < T_D_LET + 0.5:
                crouch = S((t - T_D_CROUCH) / (T_D_SET - T_D_CROUCH)) * (1 - S((t - T_D_LET) / 0.45))
            c_hip_y = lerp(436.0, 505.0, crouch)
            c_lean = lerp(14.0, 55.0, crouch)
            if 16.95 <= t < T_D_LET:
                c_lean = max(c_lean, 22.0)
            c_mode = "shove" if t < 13.7 else ("carry" if st["D"]["state"] == "held" else "walk")
        elif t < T_RESET["counter"]:
            # wheel: walks alongside with empty hands, cannot keep up, looks at his hands
            xw, vw = profile(t, 26.0, 4.0, 340.0, 0.6, 0.8)
            c_hip = 470.0 + xw
            c_face = 1
            c_hip_y, c_lean = 438.0, 10.0
            c_mode = "walk"
        else:
            c_hip = 600.0
            c_face = -1
            c_hip_y, c_lean = 440.0, 6.0
            c_mode = "watch"
            if t >= T_SIT[0]:
                u = S((t - T_SIT[0]) / (T_SIT[1] - T_SIT[0]))
                c_hip_y = lerp(440.0, 540.0, u)
                c_lean = lerp(6.0, -8.0, u)
                c_mode = "sit"
        # carrier hands
        sh = (c_hip + c_face * TORSO["C"] * math.sin(math.radians(c_lean)),
              c_hip_y - TORSO["C"] * math.cos(math.radians(c_lean)))
        if c_mode == "haul":
            u = S((t - 3.3) / 0.6) * (1 - S((t - 11.5) / 0.4))
            handsC = [{"x": sh[0] + 10 * u + 12, "y": sh[1] + 14, "pin": "rope" if u > 0.99 else "free"},
                      {"x": sh[0] + 22 * u + 14, "y": sh[1] + 26, "pin": "rope" if u > 0.99 else "free"}]
        elif mech == "rollers" and 12.75 <= t < 13.6:
            # each shove: hands on the log being shoved from its arrival side
            nx = [n for n in "ABC" if st[n]["state"] in ("pile", "shoved")]
            if nx:
                n = nx[0]
                s = st[n]
                lx = max(s["x"], PILE[n] - 40.0) + LOGS[n].R * 0.6
                pin = f"log {n}" if s["x"] >= PILE[n] - 40.0 else "free (follow-through)"
                cyn = LOGS[n].cy(s["th"])
                handsC = [{"x": lx, "y": cyn - LOGS[n].R * 0.7, "pin": pin},
                          {"x": lx + 6, "y": cyn - LOGS[n].R * 0.3, "pin": pin}]
        elif st["D"]["state"] == "held" or (mech == "rollers" and T_D_SET <= t < T_D_LET):
            dx_, dy_ = st["D"]["x"], LOGS["D"].cy(st["D"]["th"]) - st["D"].get("lift", 0.0)
            rD = LOGS["D"].R
            handsC = [{"x": dx_ + rD * 0.55, "y": dy_ - rD * 0.86, "pin": "log D"},
                      {"x": dx_ - rD * 0.15, "y": dy_ - rD * 1.0, "pin": "log D"}]
        elif mech == "rollers" and 16.45 <= t < T_D_PICK:
            u = S((t - 16.45) / 0.5)
            dx_, dy_ = st["D"]["x"], LOGS["D"].cy(st["D"]["th"])
            rD = LOGS["D"].R
            tgt = [(dx_ + rD * 0.55, dy_ - rD * 0.86), (dx_ - rD * 0.15, dy_ - rD * 1.0)]
            rest = [(sh[0] + c_face * 20, sh[1] + 70), (sh[0] + c_face * 10, sh[1] + 80)]
            handsC = [{"x": lerp(rest[j][0], tgt[j][0], u), "y": lerp(rest[j][1], tgt[j][1], u), "pin": "free"}
                      for j in range(2)]
        elif mech == "wheel" and 30.2 <= t < 31.6:
            u = S((t - 30.2) / 0.4) * (1 - S((t - 31.2) / 0.4))
            rest = [(sh[0] + 8, sh[1] + 82), (sh[0] + 2, sh[1] + 86)]
            look = [(sh[0] + 48, sh[1] + 24), (sh[0] + 40, sh[1] + 34)]
            handsC = [{"x": lerp(rest[j][0], look[j][0], u), "y": lerp(rest[j][1], look[j][1], u), "pin": "free"}
                      for j in range(2)]
            c_mode = "looks-at-hands"
        if handsC is None:
            if c_mode == "sit":
                handsC = [{"x": c_hip + c_face * 40, "y": c_hip_y - 4, "pin": "free"},
                          {"x": c_hip + c_face * 30, "y": c_hip_y + 4, "pin": "free"}]
            else:
                handsC = [{"x": sh[0] + c_face * 8, "y": sh[1] + 84, "pin": "free"},
                          {"x": sh[0] + c_face * 2, "y": sh[1] + 88, "pin": "free"}]
        # carrier feet
        c_centre = c_hip - c_face * 6.0
        c_half = 24.0
        c_vel = 0.0 if c_prev is None or any(abs(t - T_r) < DT / 2 for T_r in T_RESET.values()) else (c_hip - c_prev) / DT
        c_prev = c_hip
        c_speed = abs(c_vel)
        c_dir = (1 if c_vel > 0 else -1) if c_speed > 1.0 else c_face
        if mech == "drag":
            c_centre = c_hip - 30.0
        avoidC = list(avoid)
        if st["D"]["state"] in ("rest", "ground"):
            avoidC.append((st["D"]["x"] - LOGS["D"].R - 6, st["D"]["x"] + LOGS["D"].R + 6))
        for T_r in T_RESET.values():
            if abs(t - T_r) < DT / 2:
                C_g.teleport((c_centre + 24, c_centre - 24))
        explicitC = None
        if t >= T_SIT[0] and mech == "counter":
            explicitC = [(T_SIT[0], T_SIT[0] + 0.3, c_hip - 70.0), (T_SIT[0] + 0.4, T_SIT[0] + 0.7, c_hip - 95.0)]
        lockedC = (mech == "rollers" and 12.75 <= t < 13.7) or (T_D_CROUCH <= t < T_D_LET + 0.3) or (16.4 <= t < T_D_LIFT)
        plC = C_g.update(t, c_centre, c_half, c_dir, c_speed, avoidC, locked=lockedC, explicit=explicitC)
        for fi in plC:
            footfalls.append({"t": round(t, 3), "who": "C", "foot": fi, "x": round(C_g.f[fi], 2)})
            if st["D"]["state"] == "held":
                sp["logD_sway_deg"].kick(t, 2.4 * (1 if fi == 0 else -1), "carrier foot plant while carrying D")

        # ---- springs step
        for s_ in sp.values():
            s_.step(t)

        # ---- sample the frame
        k = t * FPS
        if abs(k - round(k)) < 1e-6:
            k = int(round(k))
            cam = "B" if T_CAM_B[0] <= t < T_CAM_B[1] else "A"
            # logs
            logs_out = {}
            for n, s in st.items():
                if s["state"] in ("absent", "cleared"):
                    logs_out[n] = {"state": s["state"]}
                    continue
                Lg = LOGS[n]
                th = s["th"]
                cy = Lg.cy(th) - s.get("lift", 0.0)
                rock = 0.0
                if n == "A" and s["state"] == "rest":
                    rock = abs(sp["logA_rock_rad"].x)
                if n == "D" and s["state"] == "held":
                    th = th + math.radians(sp["logD_sway_deg"].x)
                logs_out[n] = {"x": round(s["x"] + rock * Lg.R, 2), "cy": round(cy, 2), "theta": round(th + rock, 4),
                               "R": round(Lg.R, 2), "state": s["state"]}
            # cart
            cart = None
            if mech in ("wheel", "counter"):
                if mech == "wheel":
                    xw, _ = profile(t, *WP)
                    wxs = {kk: X0 - STONE_FRONT + r + xw for kk, r in WHEEL_REL.items()}
                    wth = {kk: xw / WHEEL_R for kk in WHEEL_REL}
                    wst = {kk: "axle" for kk in WHEEL_REL}
                    beam = "on"
                else:
                    r = counter(t)["r"]
                    wxs, wth, wst = r["wx"], r["wth"], r["wstate"]
                    beam = "on" if t < T_PIN else ("lifting" if t < T_PIN + 0.4 else "off")
                cart = {"platform_local": [PLAT_REAR, PLAT_BOT - PLAT_TOP, PLAT_FRONT, 0.0],
                        "wheels": {kk: {"x": round(wxs[kk], 2), "cy": AXLE_Y, "theta": round(wth[kk], 4),
                                        "R": WHEEL_R, "state": wst[kk]} for kk in wxs},
                        "axle_beam": beam,
                        "pin": [round(pin_world[0], 2), round(pin_world[1], 2)] if pin_world else None}
            rope = None
            if mech == "drag" and 3.3 <= t < 11.9:
                rope = {"nose": [round(front + 25.0, 2), GROUND - 10.0],
                        "shoulder": [round(sh[0], 2), round(sh[1], 2)] if c_mode == "haul" else None,
                        "hands": [round(handsC[0]["x"], 2), round(handsC[0]["y"], 2)],
                        "sag_px": round(3.0 + max(0.0, sp["rope_sag_px"].x), 2)}

            def feet_of(g):
                out = []
                for fi in range(2):
                    x_, y_, pl = g.pos(fi, t)
                    out.append({"x": round(x_, 2), "y": round(y_, 2), "planted": pl})
                return out
            p_head = {"ang": round(-30.0 + sp["P_head_nod_deg"].x if p_mode != "walk-in" else -5.0, 2),
                      "face": -1 if 17.30 <= t < 18.40 else 1}
            if t >= 38.3:
                p_head = {"ang": round(-8.0 + sp["P_head_nod_deg"].x, 2), "face": 1}
            c_head = {"ang": round((-18.0 if c_mode == "haul" else -8.0) + sp["C_head_nod_deg"].x
                                   - (25.0 if c_mode == "looks-at-hands" else 0.0), 2), "face": c_face}
            frames.append({
                "k": k, "t": round(t, 4), "cam": cam, "mech": mech,
                "tau": None if L["tau"] is None else round(L["tau"], 4),
                "load": {"x_m": round((front - X0) / PXM, 4), "front": round(front, 2), "xb": round(xb, 2),
                         "bottom": round(L["bottom"] if mech != "counter" else PLAT_TOP, 2),
                         "angle_deg": round(-math.degrees(L["ang"]) + (sp["platform_bounce_deg"].x if mech == "counter" and L["ang"] > 0 else 0.0)
                                            if mech == "counter" else sp["stone_rock_deg"].x, 3),
                         "affine": [round(a, 5) for a in A_], "v_px_s": round(L["v"], 2),
                         "on": {"drag": "runner", "rollers": "logs", "wheel": "cart", "counter": "cart"}[mech]},
                "logs": logs_out,
                "cart": cart,
                "rope": rope,
                "P": {"mode": p_mode, "hip": [round(hip_x, 2), round(p_hip_y, 2)], "lean": round(p_lean, 2),
                      "facing": p_facing, "head": p_head, "feet": feet_of(P_g),
                      "hands": [{"x": round(h["x"], 2), "y": round(h["y"], 2), "pin": h["pin"]} for h in hands_P]},
                "C": {"mode": c_mode, "hip": [round(c_hip, 2), round(c_hip_y, 2)], "lean": round(c_lean, 2),
                      "facing": c_face, "head": c_head, "feet": feet_of(C_g),
                      "hands": [{"x": round(h["x"], 2), "y": round(h["y"], 2), "pin": h["pin"]} for h in handsC]},
                "springs": {n_: round(s_.x, 4) for n_, s_ in sp.items()},
            })
    # counter events + wheel trial events
    for (te, kind, what) in COUNTER_EVENTS:
        ev(te, kind, what)
    ev(T_COUNTER0, "push-start", "counter-check push (the wheel trial's input, tau 0-1.6)")
    ev(T_WHEEL[0], "push-start", "wheel trial push window opens")
    ev(T_WHEEL[1], "stop", "the cart stops at 8.0 m (push window closes)")
    ev(14.0, "push-start", "rollers push window opens (tau 0)")
    ev(21.0, "push-start", "rollers push resumes (tau 4.8)")
    ev(23.0, "stop", "the stone stops at 3.0 m (rollers push window closes; soft thud)")
    ev(END_LINE_T, "end-line", "end source line scratches in")
    for m_, lab in ((3.0, "pass-3m"),):
        # wheel trial crossing of the 3 m ghost
        for kk in range(int(T_WHEEL[0] * 240), int(T_WHEEL[1] * 240)):
            tt = kk / 240
            if X0 + profile(tt, *WP)[0] >= X0 + m_ * PXM:
                ev(tt, lab, "the cart passes the 3 m roller ghost")
                break
    # carry window = the load waits
    ev(T_D_PICK, "carry-start", "carry window opens (tau 2.2): the load waits on two logs")
    ev(21.0, "carry-end", "carry window closes (tau 4.8)")
    events.sort(key=lambda e: e["t"])
    return frames, events, footfalls, P_g, C_g, rel0


# ================================================================= asserts ---
def checks(frames, events, footfalls, P_g, C_g):
    res = {}
    fr = {f["k"]: f for f in frames}

    def at(t):
        return fr[int(round(t * FPS))]

    # ---------- invariant 1: same challenge
    hand_heights = {}
    for name, t in (("drag", 4.6), ("rollers", 15.0), ("wheel", 26.5), ("counter", 35.6)):
        f = at(t)
        A_ = f["load"]["affine"]
        # untilted hand height: hand local y + bottom
        hand_heights[name] = {"hand_y_world_untilted": HAND_Y, "bottom": f["load"]["bottom"],
                              "hand_local_y": round(HAND_Y - f["load"]["bottom"], 2),
                              "on_face": f["load"]["bottom"] - HAND_Y < 150}
    windows = {"drag": 7.0, "rollers": 7.0, "wheel": 7.0, "counter": "tau 0-1.6 of the wheel trial's input"}
    x0s = {name: at(t)["load"]["front"] for name, t in (("drag", 4.5), ("rollers", 14.0), ("wheel", 26.0), ("counter", T_COUNTER0))}
    ends = {"drag": at(11.5)["load"]["x_m"], "rollers": at(23.0)["load"]["x_m"], "wheel": at(33.0)["load"]["x_m"],
            "counter": at(37.9)["load"]["x_m"]}
    # mask identity: every load transform is rigid (det 1, orthonormal), the outline is one object
    max_det = max(abs(f["load"]["affine"][0] * f["load"]["affine"][4] - f["load"]["affine"][1] * f["load"]["affine"][3] - 1)
                  for f in frames)
    nslips = len([e for e in events if e["kind"] == "slip"])
    inv1 = {
        "stone_outline_sha1": STONE_HASH,
        "load_transform_rigid_max_det_err": max_det,
        "load_front_at_push_start_px": x0s,
        "hand_height": hand_heights,
        "push_window_tau_s": windows,
        "frame": [W, H], "ground_y": GROUND, "px_per_m": PXM, "x0": X0,
        "final_displacement_m": ends,
        "drag_slips": nslips,
    }
    pass1 = (max_det < 1e-4 and all(abs(v - X0) < 1e-6 for v in x0s.values())
             and abs(ends["drag"] - 1.2) <= 0.05 and abs(ends["rollers"] - 3.0) <= 0.05
             and abs(ends["wheel"] - 8.0) <= 0.1 and ends["counter"] <= 1.2 and nslips == 9
             and all(h["on_face"] for h in hand_heights.values()))
    res["invariant_1_same_challenge"] = {"pass": bool(pass1), **inv1}

    # ---------- invariant 2: contact carried through motion
    max_slide = {"P": 0.0, "C": 0.0}
    for who in ("P", "C"):
        for a, b in zip(frames, frames[1:]):
            for fi in range(2):
                fa, fb = a[who]["feet"][fi], b[who]["feet"][fi]
                if fa["planted"] and fb["planted"] and b["k"] not in CUT_FRAMES:
                    max_slide[who] = max(max_slide[who], abs(fb["x"] - fa["x"]) + abs(fb["y"] - fa["y"]))
    # hands on stone face: recompute the face point from the affine
    max_hand = 0.0
    for f in frames:
        for h in f["P"]["hands"]:
            if h["pin"] == "stone":
                A_ = f["load"]["affine"]
                # invert: local = R^T (world - c)
                X, Y = h["x"] - A_[2], h["y"] - A_[5]
                xl = A_[0] * X + A_[3] * Y
                yl = A_[1] * X + A_[4] * Y
                bx = stone_back_x(yl)
                if bx is not None:
                    max_hand = max(max_hand, abs(xl - (bx + 1.5)))
    # roller and wheel slip, tangency
    max_roll_slip = 0.0
    max_tangent = 0.0
    for a, b in zip(frames, frames[1:]):
        if b["k"] in CUT_FRAMES:
            continue
        for n, lb in b["logs"].items():
            la = a["logs"].get(n, {})
            if "x" in lb and "x" in la and lb["state"] in ("carried", "free", "rest", "shoved") and la["state"] in ("carried", "free", "rest", "shoved"):
                if n == "A" and lb["state"] == "rest":
                    continue        # rocking on its facet: rotation about the contact, accounted by the spring
                max_roll_slip = max(max_roll_slip, abs((lb["theta"] - la["theta"]) * lb["R"] - (lb["x"] - la["x"])))
            if "x" in lb and lb["state"] not in ("held",):
                Lg = LOGS[n]
                max_tangent = max(max_tangent, abs(Lg.cy(lb["theta"]) + Lg.support(lb["theta"], math.pi / 2) - GROUND)
                                  if lb["state"] != "rest" else 0.0)
        if a["cart"] and b["cart"]:
            for kk, wb in b["cart"]["wheels"].items():
                wa = a["cart"]["wheels"][kk]
                if wb["state"] in ("axle", "loose", "free"):
                    max_roll_slip = max(max_roll_slip, abs((wb["theta"] - wa["theta"]) * WHEEL_R - (wb["x"] - wa["x"])))
    # stone not inside its carried logs
    max_pen = 0.0
    for f in frames:
        if f["mech"] == "rollers" and f["t"] >= 13.7:
            for n, l in f["logs"].items():
                if l.get("state") == "carried":
                    top = LOGS[n].top(l["theta"])
                    max_pen = max(max_pen, f["load"]["bottom"] - top)
    inv2 = {"max_planted_foot_slide_px": max_slide, "max_hand_to_stone_face_px": round(max_hand, 4),
            "max_roll_slip_px_per_frame": round(max_roll_slip, 4), "max_ground_tangency_error_px": round(max_tangent, 4),
            "max_stone_into_log_px": round(max_pen, 4)}
    pass2 = max(max_slide.values()) <= 1.0 and max_hand <= 2.0 and max_roll_slip <= 0.5 and max_tangent <= 1.0 and max_pen <= 1.0
    res["invariant_2_contact"] = {"pass": bool(pass2), **inv2}

    # ---------- invariant 3: continuity
    max_jump = 0.0
    worst = None
    for a, b in zip(frames, frames[1:]):
        if b["k"] in CUT_FRAMES:
            continue
        dx = abs(b["load"]["front"] - a["load"]["front"])
        allow = max(abs(a["load"]["v_px_s"]), abs(b["load"]["v_px_s"])) / FPS + 1.0
        if dx - allow > max_jump:
            max_jump = dx - allow
            worst = b["t"]
    cam_b = [f for f in frames if f["cam"] == "B"]
    inv3 = {"max_excess_jump_px": round(max_jump, 4), "worst_t": worst,
            "declared_cuts_frames": sorted(CUT_FRAMES),
            "declared_cuts_t": sorted(k / FPS for k in CUT_FRAMES),
            "wide_and_closeup_share_state": "one sim state per instant; cam B frames (%.2f-%.2f s) carry the same load record"
                                            % (cam_b[0]["t"], cam_b[-1]["t"])}
    res["invariant_3_continuity"] = {"pass": bool(max_jump <= 0.0), **inv3}

    # ---------- extra: secondary motion (#41)
    sec = {}
    ok7 = True
    for n, s_ in SPRINGS.items():
        tr = np.array(s_.trace)
        first = s_.impulses[0]["t"] if s_.impulses else None
        before = float(np.max(np.abs(tr[tr[:, 0] < first - 1e-3, 1]))) if first else float(np.max(np.abs(tr[:, 1])))
        decays = []
        imps = [i["t"] for i in s_.impulses]
        for j, ti in enumerate(imps):
            nxt = imps[j + 1] if j + 1 < len(imps) else 1e9
            if nxt - ti < 0.6:
                continue
            seg = tr[(tr[:, 0] >= ti) & (tr[:, 0] < ti + 0.6)]
            Emax = float(seg[:, 2].max())
            Eend = float(seg[-1, 2])
            decays.append(Eend / Emax if Emax > 0 else 0.0)
        sec[n] = {"impulses": len(imps), "first_impulse_t": first, "max_before_first_impulse": before,
                  "worst_energy_ratio_after_0.6s": round(max(decays), 6) if decays else None,
                  "isolated_impulses_checked": len(decays)}
        if before > 1e-12 or (decays and max(decays) > 0.01):
            ok7 = False
    res["invariant_7_secondary"] = {"pass": ok7, **sec}

    # ---------- extra: rollers read and gait limits
    a_stop = next(e for e in events if e["kind"] == "log-stop")
    rel = next(e for e in events if e["kind"] == "release")
    waits = [f["load"]["front"] for f in frames if f["mech"] == "rollers" and f["tau"] is not None and 2.2 <= f["tau"] <= 4.8]
    strides = [abs(p[4] - p[3]) for p in P_g.plants + C_g.plants if p[5] != "sit"]
    wheel_plants = [p for p in P_g.plants if T_WHEEL[0] <= p[1] <= T_WHEEL[1]]
    cad = []
    for a_, b_ in ((26.0, 27.0), (27.0, 28.0), (28.0, 29.0), (29.0, 30.0), (30.0, 31.0), (31.0, 32.0), (32.0, 33.0)):
        n_ = len([p for p in wheel_plants if a_ <= p[1] < b_])
        cad.append((a_, n_ / (b_ - a_)))
    res["rollers_and_gait"] = {
        "load_waits_tau_2.2_4.8_front_range_px": [round(min(waits), 3), round(max(waits), 3)],
        "log_A_release_t": rel["t"], "log_A_stop_t": a_stop["t"], "log_A_rest_behind_rear_edge_px": a_stop.get("behind_rear_edge_px"),
        "max_step_px": round(max(strides), 2), "steps": len(strides),
        "pusher_footfalls_per_s_by_second_26_to_33": [c for _, c in cad],
        "pass": bool(max(waits) - min(waits) < 1e-6 and max(strides) <= STRIDE_MAX + 1e-3),
    }
    return res


CUT_FRAMES = {int(round(T_RESET[k] * FPS)) for k in T_RESET}


def reach_report(frames):
    """how far each IK target lies beyond the animator's limb lengths (info for the animator)."""
    worst = {"P_leg": 0.0, "P_arm": 0.0, "C_leg": 0.0, "C_arm": 0.0}
    offscreen = []
    for f in frames:
        for who in ("P", "C"):
            hip = f[who]["hip"]
            lean = math.radians(f[who]["lean"])
            fa = f[who]["facing"]
            sh = (hip[0] + fa * TORSO[who] * math.sin(lean), hip[1] - TORSO[who] * math.cos(lean))
            for ft in f[who]["feet"]:
                worst[f"{who}_leg"] = max(worst[f"{who}_leg"], math.hypot(ft["x"] - hip[0], ft["y"] - hip[1]) - LEG[who])
            for h in f[who]["hands"]:
                worst[f"{who}_arm"] = max(worst[f"{who}_arm"], math.hypot(h["x"] - sh[0], h["y"] - sh[1]) - ARM[who])
        if f["P"]["hip"][0] < 60:
            offscreen.append(f["t"])
    return {k: round(v, 2) for k, v in worst.items()}, offscreen


def main():
    frames, events, footfalls, P_g, C_g, rel0 = build()
    # solve log A's initial angle so that it comes to rest with its flat facet on the ground:
    # the facet (body angle 0.71) faces down when theta = pi/2 - 0.71 (mod 2 pi)
    stop = next(e for e in events if e["kind"] == "log-stop")
    th_end = next(f["logs"]["A"]["theta"] for f in frames if f["t"] >= stop["t"] + 0.5)
    A_TH0[0] = (math.pi / 2 - 0.71 - th_end) % (2 * math.pi)
    for s_ in SPRINGS.values():
        s_.x = s_.v = 0.0
        s_.impulses, s_.trace = [], []
    frames, events, footfalls, P_g, C_g, rel0 = build()
    res = checks(frames, events, footfalls, P_g, C_g)
    reach, offscreen = reach_report(frames)
    cuts = [{"t": T_RESET[k], "kind": "reset", "to": k} for k in T_RESET] + \
           [{"t": T_CAM_B[0], "kind": "camera", "to": "B (x2.2 oblique close-up)"},
            {"t": T_CAM_B[1], "kind": "camera", "to": "A (wide)"}]
    exposure = {
        "about": "teuf-teuf exposure sheet: one record per frame at 24 fps, produced by sim.py (240 Hz substeps). "
                 "World px, y down. load.affine maps stone-local (x from the rear edge, y up negative from the "
                 "underside) to world: X = a x + b y + c, Y = d x + e y + f. Logs: centre (x, cy), body angle theta "
                 "(rad, + clockwise on screen), state. Feet/hands are IK targets with plant/pin state.",
        "constants": {"fps": FPS, "substep": DT, "frame": [W, H], "ground_y": GROUND, "x0": X0, "px_per_m": PXM,
                      "stone_front_local": STONE_FRONT, "hand_y": HAND_Y, "hand_dy": HAND_DY, "runner_h": RUNNER_H,
                      "log_R": {n: L.R for n, L in LOGS.items()}, "log_seeds": {"A": 11, "B": 12, "C": 13, "D": 14},
                      "log_A_flat_body_angle": 0.71, "wheel_R": WHEEL_R, "axle_y": AXLE_Y, "platform_bottom": PLAT_BOT,
                      "platform_top": PLAT_TOP, "platform_local_x": [PLAT_REAR, PLAT_FRONT], "wheel_rel": WHEEL_REL,
                      "stride_max_px": STRIDE_MAX, "pusher_hip_dx_from_hand": P_HIP_DX,
                      "rope_nose_local": [STONE_FRONT + 25.0, "y = ground - 10"],
                      "tau_map_rollers": TAU_MAP_ROLLERS, "close_up": {"cam": "B", "t": list(T_CAM_B), "scale": 2.2},
                      "ghost_t": GHOST_T, "end_line_t": END_LINE_T,
                      "stone_outline_sha1": STONE_HASH,
                      "drag_stick_slip": {"driver_speed_m_s": round(VD, 6), **{k: round(v, 4) for k, v in DRAG_PAR.items()}}},
        "cuts": cuts,
        "events": events,
        "footfalls": footfalls,
        "foot_plants": {"P": [dict(zip(("t_lift", "t_plant", "foot", "from", "to", "kind"), p)) for p in P_g.plants],
                        "C": [dict(zip(("t_lift", "t_plant", "foot", "from", "to", "kind"), p)) for p in C_g.plants]},
        "springs": {n: {"f_hz": s.f, "zeta": s.zeta, "unit": s.unit, "impulses": s.impulses} for n, s in SPRINGS.items()},
        "frames": frames,
    }
    exposure["caption_cues"] = caption_cues(events)
    (HERE / "exposure.json").write_text(json.dumps(exposure, separators=(",", ":")))
    write_mechanism(res, reach, offscreen, events)
    return frames, events, res, reach, offscreen, rel0


CAPTIONS = [  # (cause kind, selector, planned onset from plan 5, text)
    ("stick", 4, 7.3, "« La pierre avance d'un pas, puis elle réfléchit. »"),
    ("log-stop", "A", 17.2, "« Et moi ? » dit le rouleau qu'on laisse derrière."),
    ("pass-3m", None, 28.8, "« La roue tourne sur place ; c'est tout le reste qui voyage. »"),
    ("platform-drop", None, 36.6, "« Sans essieu, la roue n'est qu'un rouleau qui se croit quelqu'un. »"),
]


def caption_cues(events):
    out = []
    for kind, sel, onset, text in CAPTIONS:
        e = next(e for e in events if e["kind"] == kind and (sel is None or e.get("n") == sel or e.get("log") == sel))
        lag = round(onset - e["t"], 3)
        out.append({"cause_t": e["t"], "cause": e["event"], "window": [round(e["t"] + 0.2, 3), round(e["t"] + 0.6, 3)],
                    "planned_onset": onset, "lag_s": lag, "ok": 0.2 <= lag <= 0.6, "text": text})
    return out


def write_mechanism(res, reach, offscreen, events):
    ev = {e["kind"]: e for e in events}
    stops = [e for e in events if e["kind"] == "stop"]
    cues = caption_cues(events)
    mech = {
        "about": "teuf-teuf parts and contact schema (plan 3, Olog), the [substitute] operation, asserts for "
                 "invariants 1-3 (+7) with results, foraged-item evidence and handmade records. Written by sim.py.",
        "revision": {"sim": "films/swarm/teuf-teuf/sim.py", "exposure": "films/swarm/teuf-teuf/exposure.json",
                     "register": "films/swarm/teuf-teuf/register.json", "credits": "films/credits/teuf-teuf.json",
                     "date": "2026-11-16"},
        "input_force": {"kind": "Push", "N": "constant (same in every trial)", "height_world_y": HAND_Y,
                        "second_hand_y": HAND_Y + HAND_DY, "window_tau_s": 7.0,
                        "note": "hands pinned to the stone's rear face at the same world height in every trial; "
                                "the push clock tau runs 0-7 s in drag, rollers and wheel; the counter-check replays "
                                "the wheel trial's input for tau 0-1.6"},
        "load": {"outline_sha1": STONE_HASH, "width_px": STONE_FRONT, "same_mask_every_trial": True,
                 "front_at_0m_px": X0},
        "mechanisms": [
            {"name": "drag", "period": {"kind": "Unsourced", "note": "shown as a demonstration, no date on screen"},
             "film_t": [T_DRAG[0], T_DRAG[1]],
             "parts": ["stone", "sledge runner (handmade)", "rope (handmade)"],
             "contacts": [
                 {"a": "runner", "b": "ground", "kind": "slide", "law": "stick-slip: static/kinetic friction, body as spring",
                  "params": {"driver_m_s": round(VD, 5), **{k: round(v, 5) for k, v in DRAG_PAR.items()}}},
                 {"a": "pusher hands", "b": "stone rear face", "kind": "grip"},
                 {"a": "carrier hands", "b": "rope (over shoulder) to runner nose", "kind": "grip"},
                 {"a": "feet", "b": "ground", "kind": "plant", "law": "rear foot re-plants after every slip"}],
             "supported_action": {"displacement_m": res["invariant_1_same_challenge"]["final_displacement_m"]["drag"],
                                  "in_s": 7.0},
             "failure_mode": {"event": "stick-slip", "slips": [e["t"] for e in events if e["kind"] == "slip"],
                              "note": "nine lurches of 0.133 m; the stone thinks it over between them"}},
            {"name": "rollers", "period": {"kind": "Unsourced", "note": "no date; roller-to-wheel lineage is contested (register R5)"},
             "film_t": [14.0, 23.0], "tau_map": TAU_MAP_ROLLERS,
             "parts": ["stone", "log A", "log B", "log C", "log D (spare, set down in front)"],
             "contacts": [
                 {"a": "stone", "b": "log", "kind": "roll", "law": "no slip: log centre at v/2, rotation (v/2)/R"},
                 {"a": "log", "b": "ground", "kind": "roll", "law": "lowest outline point tangent to the ground"},
                 {"a": "carrier hands", "b": "log D", "kind": "grip"},
                 {"a": "pusher hands", "b": "stone rear face", "kind": "grip"},
                 {"a": "feet", "b": "ground", "kind": "plant"}],
             "supported_action": {"displacement_m": res["invariant_1_same_challenge"]["final_displacement_m"]["rollers"],
                                  "in_tau_s": 7.0},
             "failure_mode": {"event": "logs drift back at v/2 and fall out behind; the load waits while a log is carried",
                              "log_A_release_t": ev["release"]["t"], "log_A_stop_t": ev["log-stop"]["t"],
                              "log_A_rest_behind_rear_edge_px": ev["log-stop"].get("behind_rear_edge_px"),
                              "load_waits_tau": [2.2, 4.8], "load_waits_film_t": [16.95, 21.0],
                              "carry": {"pickup": ev["pickup"]["t"], "set_down": ev["log-set"]["t"],
                                        "capture_by_stone": ev["capture"]["t"]}}},
            {"name": "wheel and axle", "period": {"kind": "SourcedClaim", "register": "R3",
                                                 "note": "Copper Age / Baden culture (Commons categories of the wheel photograph); "
                                                         "no number shown on screen"},
             "film_t": [T_WHEEL[0], T_WHEEL[1]],
             "parts": ["stone", "plank platform (handmade)", "rear axle + wheel", "front axle + wheel",
                       "axle hold-down beam and pin (handmade)",
                       "wheel image: GrabCut cutout of the Ljubljana Marshes wheel photograph (foraged)"],
             "contacts": [
                 {"a": "platform", "b": "axle journals", "kind": "axle",
                  "law": "axle turns in a bearing notch under the platform, held by the hold-down beam; the wheel is "
                         "fixed to its axle (square hole, as in the Ljubljana wheel)"},
                 {"a": "wheel", "b": "ground", "kind": "roll", "law": "no slip: theta = dx/R, wheel stays under the load"},
                 {"a": "pusher hands", "b": "stone rear face", "kind": "grip"},
                 {"a": "feet", "b": "ground", "kind": "plant", "law": "step <= 0.75 m, so cadence must rise"}],
             "supported_action": {"displacement_m": res["invariant_1_same_challenge"]["final_displacement_m"]["wheel"],
                                  "in_s": 7.0, "peak_speed_m_s": 1.6, "pass_3m_t": ev["pass-3m"]["t"]},
             "failure_mode": {"event": "none in the window; the pusher's walking becomes the limit",
                              "pusher_footfalls_per_s_by_second": res["rollers_and_gait"]["pusher_footfalls_per_s_by_second_26_to_33"]}},
            {"name": "counter-check: wheels without the axle contact", "film_t": [T_RESET["counter"], 38.0],
             "substitution": "remove contact kind 'axle' only (pin pulled, beam lifts away); same cart, same push input",
             "contacts": [
                 {"a": "platform", "b": "wheel", "kind": "roll", "law": "loose: wheel centre at v/2 under the platform"},
                 {"a": "wheel", "b": "ground", "kind": "roll"},
                 {"a": "platform rear end", "b": "ground", "kind": "slide", "law": "after the drop: kinetic friction"}],
             "supported_action": {"displacement_m": res["invariant_1_same_challenge"]["final_displacement_m"]["counter"]},
             "failure_mode": {"pin_pull_t": T_PIN, "wheel_drop_t": ev["wheel-drop"]["t"],
                              "platform_drop_t": ev["platform-drop"]["t"], "stop_t": stops[-1]["t"]}},
        ],
        "substitute": {
            "operation": "Mechanism x Load -> Mechanism' x Load (moving_parts and contacts swapped; load, input force, frame, window kept)",
            "preconditions": {"a_load_mask_identical": res["invariant_1_same_challenge"]["stone_outline_sha1"],
                              "b_push_height_and_window": res["invariant_1_same_challenge"]["hand_height"],
                              "c_frame_ground_scale": [W, H, GROUND, PXM, X0],
                              "d_new_contact_kind": ["slide", "roll", "axle"]},
            "consequences": {"displacement_m": res["invariant_1_same_challenge"]["final_displacement_m"],
                             "labour": ["strain (drag)", "carrying (rollers)", "walking to keep up (wheel)"],
                             "contact_sound": ["scrape", "tok", "rumble"]},
            "counterexample": "wheels without the axle contact behave as rollers: rear wheel drops out, load stops at "
                              f"{res['invariant_1_same_challenge']['final_displacement_m']['counter']} m",
        },
        "asserts": res,
        "caption_cues": cues,
        "ik_reach_excess_px": {"value": reach,
                               "note": "max distance by which a foot/hand target exceeds the test-shot puppet's limb "
                                       "lengths (Puppet: thigh 63s, shin 61s, arms 48s+46s; P s=1.2, C s=1.15). The large "
                                       "C value is the shove follow-through (13.04 s) and seated leg extensions; the "
                                       "animator's ik2 clamps, so residuals there are expected and reported in animation.json"},
        "layout_warning": {
            "pusher_hip_x_below_60px_intervals_s": [[0.0, 10.46], [12.75, 16.13], [25.0, 27.21], [34.0, 43.96]],
            "n_frames": len(offscreen),
            "why": "with x0 = 330 and the approved 250 px stone, the rear face is at x 80 at 0 m; the pusher's hip is "
                   "134 px behind his hands (40 deg lean), so at 0 m his hip sits at x ~ -54 and his rear foot near "
                   "-140. During the whole drag (0-1.2 m) and the first second of every later trial he is half "
                   "cropped at frame left. kf-1 had the same issue less badly (smaller figures).",
            "options": ["accept the crop (the reference frieze crops animals at the edges)",
                        "the director moves x0 to ~430 (8 m then reaches 1230; ticks and ghosts move with it)",
                        "narrow the stone to ~180 px (breaks the approved test-shot stone)"],
        },
        "deviations_from_plan": [
            "Rollers push clock: tau 2.2 falls at 16.95 s (not 16.2) so that, as in the approved test shot, log A is "
            "squeezed out inside the close-up (release 16.25, stop 16.84, caption 17.2 = +0.36 s). tau 0-2.2 -> 14.0-16.95, "
            "tau 2.2-4.8 -> 16.95-21.0 (the wait), tau 4.8-7.0 -> 21.0-23.0.",
            "Resets are declared cuts at 12.75 (scratch wipe 12.5-12.75), 25.0 (wipe 24.75-25.0) and 34.0 (dissolve "
            "34.0-34.25); camera cuts at 16.2 and 18.8. Load x is continuous everywhere else.",
            "Only the pusher walks in (0-3.4 s); the carrier stands at the rope from the start (walking in from either "
            "edge would need > 2 m/s with a 0.75 m step).",
            "Log D is a fourth, spare log lying at x 700 from the rollers reset; the carrier walks to it, faces left, "
            "carries it back and sets it 30 px ahead of the waiting stone (19.70), steps clear by 22.0.",
            "Log A comes to rest 191 px behind the stone's rear edge (review fix), between the pusher's feet: it rolls "
            "under his lead foot, which lifts 58 px and re-plants ahead of the log (contact-driven, #33). This spot "
            "also keeps A clear of the cart's rear wheel at 0 m (4 px gap) and of the fallen wheel in shot 6.",
            "Counter-check caption is caused by the platform hitting the ground (36.30 -> 36.6, +0.30 s); the pin pull "
            "(34.6) is its own beat (click). Wheel drop 36.07, stop 36.83 at 0.95 m.",
            "In profile the cart shows two wheels, each on its own axle in bearings under the platform; the 'axle' "
            "contact is held by one hold-down beam with a pin at the platform's rear end, which the pusher pulls.",
            "Shot 6: the pusher sits on the forgotten log A (39.6); that contact is the impulse for its one last rock "
            "and tok (#41: no motion without a sim event).",
        ],
        "evidence_foraged": EVIDENCE,
        "handmade": HANDMADE,
        "absences": ABSENCES,
    }
    (HERE / "mechanism.json").write_text(json.dumps(mech, indent=1, ensure_ascii=False, default=str))
    return mech


EVIDENCE = [
    {"id": "F1", "title": "File:Cueva de las manos - detalle.jpg", "author": "Suzko", "license": "CC BY-SA 3.0",
     "license_url": "https://creativecommons.org/licenses/by-sa/3.0",
     "source_url": "https://commons.wikimedia.org/wiki/File:Cueva_de_las_manos_-_detalle.jpg",
     "file_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Cueva_de_las_manos_-_detalle.jpg/960px-Cueva_de_las_manos_-_detalle.jpg",
     "local_path": "films/sources/teuf-teuf/hands_cueva.jpg (960x720 thumbnail of the 1280x960 original)",
     "what_it_shows": "Detail of a rock wall at Cueva de las Manos, Río Pinturas (Santa Cruz, Argentina; Monumento "
                      "Histórico Nacional ID 876): negative hand stencils, animal figures (guanacos) and symbols. "
                      "Photographed 2005-01-07 (EXIF), Wiki Loves Monuments 2012.",
     "verified_date_or_place": "Commons API extmetadata re-read 2026-11-16: LicenseShortName 'CC BY-SA 3.0', License "
                               "'cc-by-sa-3.0', Artist 'Suzko', Credit 'Own work', Copyrighted True; wikitext {{self|cc-by-sa-3.0}}. "
                               "Saved: films/sources/teuf-teuf/mechanic/extmeta.json",
     "used_as": "the wall in every shot: real rock re-toned to the reference's cream wash, its real stencils as pale hands "
                "in dark blown halos, its guanaco silhouettes kept"},
    {"id": "F2", "title": "File:Ljubljana Marshes Wheel with axle (oldest wooden wheel yet discovered).jpg",
     "author": "Petar Milošević", "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0",
     "source_url": "https://commons.wikimedia.org/wiki/File:Ljubljana_Marshes_Wheel_with_axle_(oldest_wooden_wheel_yet_discovered).jpg",
     "file_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Ljubljana_Marshes_Wheel_with_axle_%28oldest_wooden_wheel_yet_discovered%29.jpg/1280px-Ljubljana_Marshes_Wheel_with_axle_%28oldest_wooden_wheel_yet_discovered%29.jpg",
     "local_path": "films/sources/teuf-teuf/wheel_ljubljana.jpg (1280x980 thumbnail of the 4504x3448 original)",
     "what_it_shows": "The Ljubljana Marshes wooden wheel with its axle as displayed (photographed 2020-02-08); Commons "
                      "categories: Ljubljana Marshes Wheel, Cartwheels, Baden culture, Copper Age in Europe.",
     "verified_date_or_place": "Commons API extmetadata re-read 2026-11-16: LicenseShortName 'CC BY-SA 4.0', License "
                               "'cc-by-sa-4.0', Artist 'Petar Milošević', Credit 'Own work'; wikitext {{self|cc-by-sa-4.0}}. "
                               "Saved: films/sources/teuf-teuf/mechanic/extmeta.json",
     "used_as": "the two cart wheels in the wheel trial and counter-check: a cv2.grabCut cutout of the real wheel, toned "
                "to charcoal, its square axle hole kept (the animator makes the cutout)"},
]

HANDMADE = [
    {"what": "the mechanism fixture: stick-slip drag, roller sim, wheel ease, axle-less counter-check, gait planner, springs",
     "where": "films/swarm/teuf-teuf/sim.py -> exposure.json"},
    {"what": "stone outline (cut card, seed 1956), log outlines (seeds 11-14, A with a flat facet), cart platform, axles, "
             "hold-down beam and pin, sledge runner, rope geometry",
     "where": "sim.py (geometry and positions); drawn by the animator"},
    {"what": "diagnostic sheets of the exposure (not for the film)",
     "where": "films/sources/teuf-teuf/mechanic/exposure-check.jpg, load-x-chart.png"},
]

ABSENCES = [
    "Ljubljana wheel date and dimensions: the Commons category page (Category:Ljubljana Marshes Wheel, which carries "
    "the Wikidata infobox) could not be read: the Commons API answered 'too many requests' three times on 2026-11-16 "
    "and I stopped retrying. The file page itself gives no date or size, only the categories Copper Age in Europe / "
    "Baden culture. The numeric age (~5,150 years) therefore stays 'uncertain' in register.json and must not appear "
    "on screen.",
    "No new searches or downloads were needed for this unit (sounds belong to commentary-sound). "
    "drag_djehutihotep.jpg and roll_nineveh_c.jpg remain in sources/ but are not used by direction 1 and are not credited.",
]

if __name__ == "__main__":
    frames, events, res, reach, offscreen, rel0 = main()
    for e in events:
        if e["kind"] not in ("stick",):
            print(f'{e["t"]:7.3f}  {e["kind"]:13s} {e["event"]}')
    print(json.dumps(res, indent=1, default=str)[:6000])
    print("reach excess", reach, "pusher hip x<60 frames:", len(offscreen))
    (Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/teuf-teuf/mechanic/checks.json")).write_text(json.dumps({"checks": res, "reach": reach, "offscreen_t": offscreen[:5] + offscreen[-5:],
                                                  "n_offscreen": len(offscreen), "rel0": rel0}, indent=1, default=str))
