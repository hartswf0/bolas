"""Rollers beat, film time 15.0-21.0 s: the motion fixture for the test shot.

World space: layout A (1280x720), ground y = 566, 100 px/m.
Stone: rigid irregular card, 250 px long; rolls on logs with no slip, so every
log under it translates at v/2 and turns at (v/2)/R. A log whose centre passes
the flat of the stone's underside at the rear (xb + 12) is no longer carried:
the rear lip squeezes it out backwards (kick), it rolls on its bark, comes to
rest on its flat facet and rocks (spring, secondary motion) before settling.

All integration at 240 Hz; sampled at 24 fps.
"""
import math
import json
import numpy as np

GROUND = 566.0
DT = 1 / 240
T0, T1 = 15.0, 21.0
STONE_W = 250.0
LIP = 12.0

# stone back-edge x(t): 80 px/s (0.8 m/s) until 16.45, decelerating to a stop at 16.75
V0, T_DEC, T_STOP = 80.0, 16.6, 16.95
XB_162 = 230.0                       # front edge = xb + 250 = 480 px = 1.5 m at 16.2 s


def stone_xb(t):
    if t <= T_DEC:
        return XB_162 + V0 * (t - 16.2)
    a = V0 / (T_STOP - T_DEC)
    tt = min(t, T_STOP) - T_DEC
    return XB_162 + V0 * (T_DEC - 16.2) + V0 * tt - 0.5 * a * tt * tt


def stone_v(t):
    if t <= T_DEC:
        return V0
    if t >= T_STOP:
        return 0.0
    return V0 * (1 - (t - T_DEC) / (T_STOP - T_DEC))


class Log:
    def __init__(self, name, R, seed, flat=None):
        self.name = name
        self.R = R
        rng = np.random.default_rng(seed)
        # irregular bark outline radius as a function of body angle (rotates with the log)
        self.k = [(rng.uniform(0.03, 0.06), rng.integers(2, 4), rng.uniform(0, 6.28)),
                  (rng.uniform(0.02, 0.04), rng.integers(5, 8), rng.uniform(0, 6.28))]
        self.jit = rng.normal(0, 0.018, 64)
        self.flat = flat                  # body angle of a flattened facet (where it comes to rest)

    def r(self, phi):
        """radius at body angle phi (array ok)"""
        phi = np.asarray(phi, dtype=np.float64)
        v = 1.0 + sum(a * np.sin(n * phi + p) for a, n, p in self.k)
        u = (phi % (2 * math.pi)) / (2 * math.pi) * 64
        v = v + np.interp(u, np.arange(65), np.r_[self.jit, self.jit[0]]) * 0.5
        if self.flat is not None:
            d = np.angle(np.exp(1j * (phi - self.flat)))
            v = np.minimum(v, (0.86 / np.maximum(np.cos(np.clip(d, -1.2, 1.2)), 0.3)))
        return self.R * v

    def support(self, theta, direction):
        """max extent of the rotated outline along screen angle `direction`"""
        phis = np.linspace(-0.6, 0.6, 61) + direction
        return float(np.max(self.r(phis - theta) * np.cos(phis - direction)))

    def cy(self, theta):
        return GROUND - self.support(theta, math.pi / 2)    # lowest point touches the ground

    def top(self, x, theta):
        return self.cy(theta) - self.support(theta, -math.pi / 2)


def spring_bounce(t, amp, f=3.2, zeta=0.42):
    """one-sided rocking (it rests against its facet): |damped sine|"""
    if t < 0:
        return 0.0
    w = 2 * math.pi * f
    wd = w * math.sqrt(1 - zeta * zeta)
    return amp * math.exp(-zeta * w * t) * abs(math.sin(wd * t))


def run():
    R = 24.0
    logs = {"A": Log("A", R, 11, flat=0.71), "B": Log("B", R * 1.04, 12), "C": Log("C", R * 0.97, 13),
            "D": Log("D", R * 1.02, 14)}
    rel0 = {"A": 73.3, "B": 163.0, "C": 236.0}
    xb0 = stone_xb(T0)
    state = {n: {"x": xb0 + rel0[n], "th": 0.0, "carried": True} for n in rel0}
    # initial angles chosen so the bark knots and end marks start in readable places
    state["A"]["th"] = 0.4; state["B"]["th"] = 2.1; state["C"]["th"] = -1.0
    events = []
    frames = []
    a_free = None
    t = T0
    fps_step = round((1 / 24) / DT)
    n = int(round((T1 - T0) / DT))
    kick_v = -300.0
    a_stop_t = None
    a_rest = None
    for i in range(n + 1):
        t = T0 + i * DT
        xb = stone_xb(t); v = stone_v(t)
        for name, s in state.items():
            L = logs[name]
            if s["carried"]:
                s["x"] += v / 2 * DT
                s["th"] += (v / 2) / L.R * DT
                if s["x"] < xb + LIP:
                    s["carried"] = False
                    a_free = t
                    s["v"] = kick_v
                    events.append({"t": round(t, 3), "event": f"log {name} squeezed out behind the stone", "kind": "release"})
            else:
                if s["v"] != 0.0:
                    dv = 900.0 * DT                     # rolling resistance of bark on grit
                    nv = s["v"] + dv if s["v"] < 0 else 0.0
                    if nv >= 0:
                        nv = 0.0
                        a_stop_t = t
                        events.append({"t": round(t, 3), "event": f"log {name} stops on its facet (tok)", "kind": "stop"})
                    s["x"] += s["v"] * DT
                    s["th"] += s["v"] / L.R * DT
                    s["v"] = nv
        if i % fps_step == 0:
            fr = {"t": round(t, 4), "xb": xb, "v": v, "logs": {}}
            for name, s in state.items():
                fr["logs"][name] = {"x": s["x"], "th": s["th"], "carried": s["carried"]}
            frames.append(fr)
    # stone stop event
    events.append({"t": T_STOP, "event": "stone stops, waiting on logs B and C", "kind": "stone-stop"})
    events.sort(key=lambda e: e["t"])
    return logs, frames, events, a_stop_t


if __name__ == "__main__":
    logs, frames, events, ts = run()
    print(len(frames), events)
    f = frames[-1]
    print("final xb", f["xb"], {k: (round(v["x"], 1), round(v["th"], 2)) for k, v in f["logs"].items()})
