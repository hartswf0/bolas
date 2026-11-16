"""teuf-teuf ANIMATOR motion fixture (whole film, 0-44 s, 24 fps, integrated at 240 Hz).

World = layout A: 1280x720, ground y 566, stone FRONT edge x0 = 330 px at 0 m, 100 px/m.
The plan's exposure.json (mechanic-historian unit) did not exist when this unit ran, so this
module carries the motion laws of plan s5 itself and writes its own exposure sheet
(sources/teuf-teuf/animator/exposure_animator.json). Every secondary spring is driven only
by an event in EVENTS (SCION #41).

Load: one stone mask (STONE, 180 x 126 px) in all trials. The layout's default 250 px stone
put the pusher's body off the left edge of frame A at 0 m (stone rear at x 80), so the
load was shortened to 1.8 m; ghosts are regenerated from this outline.
"""
import math
import numpy as np

FPS = 24
DT = 1 / 240
DUR = 44.0
GROUND = 566.0
X0, PXM = 330.0, 100.0
SL = 180.0                     # stone length (px)
LIP = 12.0
R_LOG = 18.0
R_WHEEL = 34.0
RUNNER_H = 10.0
PLAT_L, PLAT_T = 250.0, 12.0
PLAT_OFF = 35.0                # platform starts 35 px behind the stone rear
WHEEL_REL = (48.0, 202.0)      # wheel hubs along the platform
EVENTS = []


def ev(t, kind, what):
    EVENTS.append({"t": round(float(t), 3), "kind": kind, "event": what})


def sstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def gcurve(u):
    """0..1 with zero speed at both ends (cycloid ease)"""
    u = min(1.0, max(0.0, u))
    return u - math.sin(2 * math.pi * u) / (2 * math.pi)


# ------------------------------------------------------------------ stone ---
def make_stone():
    rng = np.random.default_rng(1956)
    pts = []
    cx, cy, rx, ry = SL / 2, -63.0, SL / 2 + 1.5, 64.0
    for t in np.linspace(0, 2 * math.pi, 90, endpoint=False):
        c, s_ = math.cos(t), math.sin(t)
        r = (abs(c) ** 2.3 + abs(s_) ** 2.3) ** (-1 / 2.3)
        r *= 1 + 0.04 * math.sin(3 * t + 1) + 0.03 * math.sin(7 * t + 0.4) + rng.normal(0, 0.008)
        x = cx + rx * r * c
        y = cy + ry * r * s_ * (1.08 if s_ < 0 else 1.0)
        pts.append((x, min(y, 0.0)))
    return pts


STONE = make_stone()
STONE_H = -min(p[1] for p in STONE)


# ------------------------------------------------------------------- drag ---
SLIPS = [4.85 + 0.75 * k for k in range(9)]
SLIP_DUR = 0.16
DRAG_STEP = 120.0 / 9


def drag_front(t):
    return X0 + DRAG_STEP * sum(sstep((t - tk) / SLIP_DUR) for tk in SLIPS)


# ------------------------------------------------------------- the logs ---
class Log:
    """irregular bark log: 9-14 point outline, radius +-12 %, a branch stub, fixed to the body."""

    def __init__(self, name, R, seed, stub=None):
        self.name, self.R = name, R
        rng = np.random.default_rng(seed)
        n = int(rng.integers(9, 15))
        self.n = n
        ang = np.sort(rng.uniform(0, 2 * math.pi, n) + np.linspace(0, 2 * math.pi, n, endpoint=False)) % (2 * math.pi)
        ang = np.sort(ang)
        rad = 1 + rng.uniform(-0.12, 0.12, n)
        # periodic catmull-rom through the irregular points -> 96-sample radius table
        P = np.c_[rad * np.cos(ang), rad * np.sin(ang)]
        out = []
        for i in range(n):
            p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
            for u in np.linspace(0, 1, 10, endpoint=False):
                u2, u3 = u * u, u * u * u
                out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3))
        out = np.array(out)
        phi = np.arctan2(out[:, 1], out[:, 0]) % (2 * math.pi)
        r = np.hypot(out[:, 0], out[:, 1])
        o = np.argsort(phi)
        self.tab_phi = np.r_[phi[o] - 2 * math.pi, phi[o], phi[o] + 2 * math.pi]
        self.tab_r = np.r_[r[o], r[o], r[o]]
        self.stub = stub                         # body angle of the branch stub
        self.knots = [(rng.uniform(0, 2 * math.pi), rng.uniform(0.3, 0.75)) for _ in range(3)]
        self.bark = [(k * 2 * math.pi / 14 + rng.normal(0, 0.12), rng.uniform(0.02, 0.3), rng.uniform(0.6, 1.0)) for k in range(14)]
        self.mean_r = float(np.mean(self.tab_r[len(o):2 * len(o)])) * R

    def r(self, phi):
        phi = np.mod(np.asarray(phi, np.float64), 2 * math.pi)
        return self.R * np.interp(phi, self.tab_phi, self.tab_r)

    def support(self, theta, direction):
        phis = np.linspace(-0.7, 0.7, 57) + direction
        return float(np.max(self.r(phis - theta) * np.cos(phis - direction)))

    def cy(self, theta):
        return GROUND - self.support(theta, math.pi / 2)

    def top(self, theta):
        return self.cy(theta) - self.support(theta, -math.pi / 2)


LOGS = {"A": Log("A", R_LOG, 21, stub=2.2), "B": Log("B", R_LOG * 1.04, 22),
        "C": Log("C", R_LOG * 0.97, 23), "D": Log("D", R_LOG * 1.03, 24, stub=0.9)}

# rollers trial: stone front law
# editor repair 1: the rollers push is 7.0 s of push like the other trials (3.6 + 3.4 s),
# with the stone waiting on two logs 17.6-19.6 while log D is set down in front
ROLL1 = (14.0, 17.6, 0.0, 150.0)        # t0, t1, from px, to px (relative to X0)
ROLL2 = (19.6, 23.0, 150.0, 300.0)


def roll_front(t):
    if t < ROLL1[0]:
        return X0
    if t <= ROLL2[0]:
        return X0 + ROLL1[2] + (ROLL1[3] - ROLL1[2]) * gcurve((t - ROLL1[0]) / (ROLL1[1] - ROLL1[0]))
    return X0 + ROLL2[2] + (ROLL2[3] - ROLL2[2]) * gcurve((t - ROLL2[0]) / (ROLL2[1] - ROLL2[0]))


# shot 2: the three logs are rolled in under the levered stone
LIFT_T = (13.15, 13.275)               # 3 frames
DROP_T = 13.62
LOG_REL0 = {"A": 84.0, "B": 125.0, "C": 168.0}
LOG_LAY = {"A": X0 + 34.0, "B": X0 + 82.0, "C": X0 + 130.0}     # where the carrier laid them (in front)
D_SET_T = (18.4, 19.3)


def sim_rollers():
    """returns per-frame dict for 13.0..25.0 and fills EVENTS."""
    frames = {}
    xb0 = X0 - SL
    st = {}
    for n in "ABC":
        st[n] = {"x": LOG_LAY[n], "th": {"A": 0.4, "B": 2.1, "C": -1.0}[n], "state": "laid", "v": 0.0, "stop": None}
    st["D"] = {"x": None, "th": 0.6, "state": "held", "v": 0.0, "stop": None}
    n_steps = int(round((25.0 - 13.0) / DT))
    rolled_in = set()
    for i in range(n_steps + 1):
        t = 13.0 + i * DT
        F = roll_front(t)
        xb = F - SL
        v = (roll_front(t + DT) - F) / DT
        for n in "ABC":
            s = st[n]
            if s["state"] == "laid":
                # 13.2-13.55: rolled leftward under the lifted stone (no slip)
                u0, u1 = 13.2 + 0.06 * "ABC".index(n), 13.55
                tgt = xb0 + LOG_REL0[n]
                if t >= u0:
                    nx = LOG_LAY[n] + (tgt - LOG_LAY[n]) * sstep((t - u0) / (u1 - u0))
                    s["th"] += (nx - s["x"]) / LOGS[n].R
                    s["x"] = nx
                if t >= u1 and n not in rolled_in:
                    rolled_in.add(n)
                    ev(t, "log-in", f"log {n} rolled in under the lifted stone (knock)")
                if t >= DROP_T:
                    s["state"] = "carried"
            elif s["state"] == "carried":
                s["x"] += v / 2 * DT
                s["th"] += (v / 2) / LOGS[n].R * DT
                if s["x"] < xb + LIP:
                    s["state"] = "free"
                    s["v"] = -260.0 if n == "A" else -190.0
                    ev(t, "release", f"log {n} squeezed out behind the stone")
            elif s["state"] == "free":
                if s["v"] != 0.0:
                    nv = s["v"] + 520.0 * DT
                    s["x"] += s["v"] * DT
                    s["th"] += s["v"] / LOGS[n].R * DT
                    if nv >= 0:
                        nv = 0.0
                        s["stop"] = t
                        ev(t, "log-stop", f"log {n} stops behind the stone (tok)")
                    s["v"] = nv
        # D: carried by the carrier until set down, then waits; carried once the stone reaches it
        sD = st["D"]
        if sD["state"] == "held" and t >= D_SET_T[1]:
            sD["state"] = "ground"
            sD["x"] = D_X
            ev(t, "log-set", "log D set down in front of the stone (wood on stone)")
        elif sD["state"] == "ground" and sD["x"] - xb <= SL - 6:
            sD["state"] = "carried"
            ev(t, "log-under", "the stone rolls onto log D")
        elif sD["state"] == "carried":
            sD["x"] += v / 2 * DT
            sD["th"] += (v / 2) / LOGS["D"].R * DT
        k = round((t - 13.0) * FPS, 6)
        if abs(k - round(k)) < 1e-6:
            frames[int(round(k))] = {"t": round(t, 4), "F": F, "v": v,
                                     "logs": {n: dict(x=s["x"], th=s["th"], state=s["state"], stop=s["stop"]) for n, s in st.items()}}
    return frames


D_X = X0 + ROLL1[3] + 10.0                  # set down just ahead of the waiting stone's front


# --------------------------------------------------------- wheel and axle ---
W_T0, W_T1 = 26.0, 33.0
W_ACC, W_DEC = 0.8, 1.4
W_V = 800.0 / (7.0 - W_ACC / 2 - W_DEC / 2)


def wheel_d(tau):
    """metres*100 travelled in the 7 s push: accelerate, cruise, decelerate to 8.0 m"""
    tau = min(max(tau, 0.0), 7.0)
    a1 = W_V / W_ACC
    a2 = W_V / W_DEC
    if tau < W_ACC:
        return 0.5 * a1 * tau * tau
    d1 = 0.5 * W_V * W_ACC
    if tau < 7.0 - W_DEC:
        return d1 + W_V * (tau - W_ACC)
    tt = tau - (7.0 - W_DEC)
    return d1 + W_V * (7.0 - W_DEC - W_ACC) + W_V * tt - 0.5 * a2 * tt * tt


def wheel_front(t):
    return X0 + wheel_d(t - W_T0)


# ------------------------------------------------- counter-check (no axle) ---
C_T0 = 35.0
PIN_T = (34.45, 34.7)
DROP_DUR = 0.30                # repair 2: the platform's rear falls 2R in 0.30 s (gravity), not 2 frames
KICK_V, ROLL_DEC = -260.0, 260.0   # repair 2: the falling platform edge kicks the rear wheel out behind,
                                   # clear of the pusher's legs (it rolls ~130 px and lies behind him)


def sim_counter():
    frames = {}
    xb = X0 - SL
    pl0 = xb - PLAT_OFF
    wx = [pl0 + WHEEL_REL[0], pl0 + WHEEL_REL[1]]
    wth = [0.0, 0.0]
    wst = ["axle", "axle"]
    wv = [0.0, 0.0]
    F = X0
    v = 0.0
    tilt_drop_t = None
    grind = False
    n_steps = int(round((44.0 - 34.0) / DT))
    for i in range(n_steps + 1):
        t = 34.0 + i * DT
        if t >= PIN_T[1] and wst[0] == "axle":
            wst = ["free", "free"]
            ev(t, "pin-pull", "axle pins pulled, forks drop: the wheels are loose under the platform")
        # push: same law as the wheel trial (same input), until the platform grinds
        if not grind:
            F_new = X0 + wheel_d(t - C_T0)
        else:
            # grinding: friction stops it within ~0.35 s
            v = max(0.0, v - 380.0 * DT)      # repair 2: grinds to rest just after the rear lands (0.30 s fall)
            F_new = F + v * DT
        v = (F_new - F) / DT if not grind else v
        F = F_new
        xb = F - SL
        pl = xb - PLAT_OFF
        for j in range(2):
            if wst[j] == "free":
                wx[j] += v / 2 * DT
                wth[j] += (v / 2) / R_WHEEL * DT
                if wx[j] < pl + LIP + 4 and j == 0:
                    wst[j] = "out"
                    wv[j] = KICK_V
                    tilt_drop_t = t
                    grind = True
                    ev(t, "wheel-drop", "rear wheel rolls out behind; the platform's rear drops to the ground (thud, grind)")
            elif wst[j] == "out":
                if wv[j] < 0:
                    wx[j] += wv[j] * DT
                    wth[j] += wv[j] / R_WHEEL * DT
                    wv[j] = min(0.0, wv[j] + ROLL_DEC * DT)
                    if wv[j] == 0.0:
                        ev(t, "loose-wheel-stop", "the loose wheel stops behind")
        if tilt_drop_t is not None and t >= tilt_drop_t + DROP_DUR and not any(e["kind"] == "platform-lands" for e in EVENTS):
            ev(t, "platform-lands", "the platform's rear end lands on the ground (thud)")
        if grind and v == 0.0 and not any(e["kind"] == "stop-counter" for e in EVENTS):
            ev(t, "stop-counter", f"platform grinds to a stop at {(F - X0) / PXM:.2f} m")
        k = round((t - 34.0) * FPS, 6)
        if abs(k - round(k)) < 1e-6:
            frames[int(round(k))] = {"t": round(t, 4), "F": F, "v": v, "wx": list(wx), "wth": list(wth),
                                     "wst": list(wst), "drop_t": tilt_drop_t}
    return frames


# ------------------------------------------------------------- springs ---
class Spring:
    """1-D spring-damper, semi-implicit Euler at 240 Hz, excited only by impulses (sim events)."""

    def __init__(self, f, zeta, impulses):
        self.w = 2 * math.pi * f
        self.z = zeta
        self.imp = sorted(impulses)          # (t, velocity kick)
        n = int(DUR / DT) + 2
        x = np.zeros(n); vv = 0.0; xx = 0.0
        j = 0
        for i in range(n):
            t = i * DT
            while j < len(self.imp) and self.imp[j][0] <= t:
                vv += self.imp[j][1]
                j += 1
            a = -self.w * self.w * xx - 2 * self.z * self.w * vv
            vv += a * DT
            xx += vv * DT
            x[i] = xx
        self.x = x

    def __call__(self, t):
        i = t / DT
        i0 = int(min(max(i, 0), len(self.x) - 2))
        return float(self.x[i0] + (self.x[i0 + 1] - self.x[i0]) * (i - i0))

    def decay_times(self, thr=0.01):
        """time from each impulse until energy < thr * its peak (before the next impulse)"""
        out = []
        for k, (t0, _) in enumerate(self.imp):
            t1 = self.imp[k + 1][0] if k + 1 < len(self.imp) else DUR
            i0, i1 = int(t0 / DT), int(t1 / DT)
            seg = self.x[i0:i1]
            if len(seg) < 3:
                continue
            vel = np.gradient(seg, DT)
            E = 0.5 * vel ** 2 + 0.5 * (self.w ** 2) * seg ** 2
            pk = E.max()
            if pk <= 0:
                continue
            ip = int(np.argmax(E))
            below = np.where(E[ip:] < thr * pk)[0]
            # first time after which it stays below
            idx = None
            for b in below:
                if np.all(E[ip + b:] < thr * pk):
                    idx = b
                    break
            out.append(round((ip + idx) * DT, 3) if idx is not None else None)
        return out


ROLL = sim_rollers()
COUNTER = sim_counter()
EV_T = lambda kind: [e["t"] for e in EVENTS if e["kind"] == kind]

# event list additions that are not integrator outputs
for k, tk in enumerate(SLIPS):
    ev(tk + SLIP_DUR, "slip", f"drag stick-slip lurch {k + 1}/9")
ev(11.5, "drag-stop", "push window ends: stone at 1.20 m")
# repair 1: explicit stick-holds (stick 1 = the stone holding at the push start) and push windows
ev(4.5, "stick", "stick 1/10 begins: push starts, the stone holds")
for k, tk in enumerate(SLIPS):
    ev(tk + SLIP_DUR, "stick", f"stick {k + 2}/10 begins: the stone holds after lurch {k + 1}")
for nm, a_, b_ in (("drag", 4.5, 11.5), ("rollers-1", ROLL1[0], ROLL1[1]), ("rollers-2", ROLL2[0], ROLL2[1]),
                   ("wheel", W_T0, W_T1)):
    ev(a_, "push-on", f"push on ({nm})")
    ev(b_, "push-off", f"push off ({nm})")
ev(C_T0, "push-on", "push on (counter-check, the wheel trial's input replayed)")
ev(LIFT_T[1], "lift", "stone levered up (3 frames)")
ev(DROP_T, "settle", "stone drops onto three logs")
ev(ROLL1[1], "stone-stop", "stone stops, waits on two logs")
ev(ROLL2[1], "stone-stop-2", "stone stops at 3.00 m")
_t3 = W_T0 + (300.0 - 0.5 * W_V * W_ACC) / W_V + W_ACC
ev(_t3, "pass-3m", "cart passes the 3 m roller ghost")
ev(W_T1, "wheel-stop", "cart reaches 8.0 m")
ev(41.0, "callback", "the loose wheel rocks once (tok)")
EVENTS.sort(key=lambda e: e["t"])

A_STOP = [e["t"] for e in EVENTS if e["kind"] == "log-stop"]
REL_T = [e["t"] for e in EVENTS if e["kind"] == "release"]
DROP_W = [e["t"] for e in EVENTS if e["kind"] == "wheel-drop"]

# spring channels (impulse = velocity kick in units/s)
SP = {
    "stone_rock": Spring(2.2, 0.45, [(t, 0.32) for t in [s + SLIP_DUR for s in SLIPS]] +
                         [(REL_T[0], -0.10), (ROLL1[1], 0.06), (ROLL2[1], 0.05)]),     # radians
    "stone_bounce": Spring(4.0, 0.5, [(DROP_T, 70.0)]),                                  # px
    "stone_settle_tilt": Spring(2.6, 0.42, [(DROP_T, -0.30), (LIFT_T[1], 0.25)]),
    "nod": Spring(2.4, 0.42, [(s + SLIP_DUR, 60.0) for s in SLIPS] + [(ROLL1[1], 45.0), (REL_T[0], -30.0)]),   # degrees
    "rope": Spring(1.8, 0.35, [(s, 90.0) for s in SLIPS]),                              # px sag kick
    "logA_end": Spring(3.0, 0.40, [(A_STOP[0], 1.6)]),                                   # rad: end-mark overshoot
    "logB_end": Spring(3.2, 0.42, [(A_STOP[1], 1.1)] if len(A_STOP) > 1 else []),
    "logD_set": Spring(4.0, 0.45, [(D_SET_T[1], 0.9)]),
    "plat_drop": Spring(2.8, 0.40, [(DROP_W[0] + DROP_DUR, 1.4)] if DROP_W else []),          # rad overshoot of tilt
    "callback": Spring(2.6, 0.38, [(41.0, 0.9)]),
}
