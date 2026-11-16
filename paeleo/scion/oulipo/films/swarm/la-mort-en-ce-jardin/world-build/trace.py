# trace.py -- WorldState trace for versions L, E and the baseline Bl, 24 fps (U1 world unit).
# World coordinates = the P2 plane at the wide framing (800x540 picture, origin top-left of the picture, y down).
# Writes world-trace.json next to world.json. Asserts the plan's invariants (plank<=1, hands<=2, one holder per object,
# holder changes only at logged events, bag above water) on every frame.
import json, math, sys
OUT = sys.argv[1]
FPS = 24

# ---- fixed geometry (wide framing, P2 coordinates) -----------------------------------------
GEOM = dict(
    N_bank=dict(poly=[(-40, 396), (120, 388), (172, 392), (200, 398), (230, 430), (200, 540), (-40, 540)], top_y_at_plank=392,
                wait_x=dict(A=128, B=96, C=58)),
    F_bank=dict(poly=[(688, 384), (700, 390), (770, 378), (840, 380), (840, 540), (720, 540), (700, 450)], top_y_at_plank=384,
                arrive_x=[716, 748, 780]),
    plank=dict(p0=(170, 392), p1=(690, 384), span_px=520, thickness_px=12, capacity=1,
               deflection="2-segment polyline: kink under the occupant, depth D_max(load)*sin(pi*u); empty: damped spring 2 px*exp(-dt/0.25)*cos(2pi*3*dt) after each step-off",
               D_max_px=dict(A=9.0, B=7.5, C=8.5, C_with_bag=8.5, A_with_bag=9.5, B_with_bag=8.0)),
    liana=dict(anchor_N=(-40, 40), anchor_F=(860, 20), rest_sag_px=88, rest_mid=(410, 118),
               rule="the plank occupant holds it with exactly one hand; under the hand the line is pulled to the hand point (sag follows the hand)"),
    water=dict(level_y_at_t0=416, rise_px_per_s=0.5, rise_cap_px=18,
               note="level(t) = 416 - min(0.5 t, 18) in P2 px, t = version-local seconds; L reaches +18 at 36 s, E +15 at 30 s"),
    plank_foot_N=(176, 400), shoe_arrival=(214, 410),
)
PLANK_TOP0 = lambda u: 392 + (384 - 392) * u


def water_y(t): return GEOM["water"]["level_y_at_t0"] - min(0.5 * t, 18.0)


def sstep(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


# crossings: (who, t_on, t_off, load)  -- plan section 6
VERSIONS = {
 "L": dict(dur=36.0, shoe_t0=14.0, crossings=[("A", 7.0, 12.0, "A"), ("C", 24.6, 29.6, "C_with_bag"), ("B", 30.0, 35.0, "B")],
           events=[(18.4, "handoff", "bag", "B", "C"), (19.6, "retrieve", "shoe", "water", "B")],
           order_before="1 A · 2 B (sac) · 3 C", order_after="1 A · 2 C (sac) · 3 B", ledger_strike=(21.5, 23.5)),
 "E": dict(dur=30.0, shoe_t0=7.0, crossings=[("B", 15.0, 19.5, "B"), ("A", 19.8, 24.4, "A_with_bag"), ("C", 24.8, 29.4, "C")],
           events=[(11.4, "handoff", "bag", "B", "A"), (12.6, "retrieve", "shoe", "water", "B")],
           order_before="1 A · 2 B (sac) · 3 C", order_after="1 B (chaussure) · 2 A (sac) · 3 C", ledger_strike=(12.9, 15.0)),
 "Bl": dict(dur=26.0, shoe_t0=None, crossings=[("A", 7.0, 12.0, "A"), ("B", 12.6, 17.6, "B_with_bag"), ("C", 18.2, 23.2, "C")],
           events=[], order_before="1 A · 2 B (sac) · 3 C", order_after=None, ledger_strike=None),
}
# N-bank stations (x keyframes, eased between keys) -- staging from plan section 6
STATIONS = {
 "L": dict(A=[(0, 128)], B=[(0, 96), (16.8, 96), (17.8, 196), (20.4, 196), (22.4, 120)], C=[(0, 58), (17.6, 58), (18.3, 150)]),
 "E": dict(A=[(0, 128), (5.8, 128), (7.0, 168), (11.6, 168), (13.4, 128)], B=[(0, 96), (9.8, 96), (10.8, 196), (13.0, 196), (14.0, 150)], C=[(0, 58)]),
 "Bl": dict(A=[(0, 128)], B=[(0, 96)], C=[(0, 58)]),
}


def station(vk, who, t):
    ks = STATIONS[vk][who]
    if t <= ks[0][0]: return ks[0][1]
    for (t0, x0), (t1, x1) in zip(ks, ks[1:]):
        if t <= t1: return x0 + (x1 - x0) * sstep((t - t0) / max(t1 - t0, 1e-6))
    return ks[-1][1]


SHOE_DRIFT = dict(id="SHOE-DRIFT-1", frames=150, enter=(830, 404), arrive=(214, 410), arrive_dt=3.6,
                  bob_px=3, bob_period_s=0.9, path="Catmull-Rom through (830,404) (640,398) (430,406) (214,410), eased in time; holds at the plank foot after arrive_dt")


def shoe_xy(dt):
    pts = [(830, 404), (640, 398), (430, 406), (214, 410)]
    u = sstep(min(dt / SHOE_DRIFT["arrive_dt"], 1.0)) * 3
    i = min(int(u), 2); f = u - i
    p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, 3)]
    cr = lambda a, b, c, d: 0.5 * (2 * b + (-a + c) * f + (2 * a - 5 * b + 4 * c - d) * f * f + (-a + 3 * b - 3 * c + d) * f ** 3)
    x = cr(p0[0], p1[0], p2[0], p3[0]); y = cr(p0[1], p1[1], p2[1], p3[1])
    return round(x, 1), round(y + 3 * math.sin(2 * math.pi * dt / 0.9), 1)


def build(vk):
    V = VERSIONS[vk]; n = int(round(V["dur"] * FPS))
    frames = []; spring_from = []
    holders = dict(bag="B", shoe=("water" if V["shoe_t0"] is not None else None))
    hands = dict(A=["free", "free"], B=["bag", "free"], C=["free", "free"])
    arrived = []; last = None; ev_i = 0; min_clear = {}
    for c in V["crossings"]: spring_from.append(c[2])
    log = []
    for f in range(n + 1):
        t = round(f / FPS, 4)
        while ev_i < len(V["events"]) and V["events"][ev_i][0] <= t + 1e-9:
            et, kind, obj, frm, to = V["events"][ev_i]
            assert holders[obj] == frm, (vk, t, obj)
            # hand bookkeeping: bag goes into a free hand of `to`, shoe into the freed hand of B
            if frm in hands:
                hands[frm][hands[frm].index(obj)] = "free"
            k = hands[to].index("free"); hands[to][k] = obj
            holders[obj] = to
            gap = abs(station(vk, frm, et) - station(vk, to, et)) if frm in hands else abs(station(vk, to, et) - shoe_xy(et - V["shoe_t0"])[0])
            log.append(dict(t=et, event=kind, obj=obj, frm=frm, to=to, body_gap_px=round(gap, 1))); ev_i += 1
        pos = {}; occ = []
        wl = water_y(t)
        for who, t_on, t_off, load in V["crossings"]:
            if t < t_on:
                x = station(vk, who, t)
                # the next crosser walks to the plank head during the 1.2 s before stepping on
                if t > t_on - 1.2:
                    x0 = station(vk, who, t_on - 1.2); x = x0 + (170 - x0) * sstep((t - (t_on - 1.2)) / 1.2)
                pos[who] = dict(x=round(x, 1), y=GEOM["N_bank"]["top_y_at_plank"], on="N")
            elif t <= t_off:
                u = (t - t_on) / (t_off - t_on); u = 0.04 * u + 0.96 * sstep(u) if False else u * 0.8 + 0.2 * sstep(u)
                D = GEOM["plank"]["D_max_px"][load]
                defl = D * math.sin(math.pi * u)
                y = PLANK_TOP0(u) + defl
                x = 170 + 520 * u
                pos[who] = dict(x=round(x, 1), y=round(y, 2), on="P", u=round(u, 4), deflection_px=round(defl, 2))
                occ.append(who)
                clear = wl - y
                min_clear[who] = min(min_clear.get(who, 99), clear)
                # hands: exactly one on the liana
                hs = hands[who]
                if "liana" not in hs: hs[hs.index("free")] = "liana"
            else:
                if who not in arrived: arrived.append(who)
                k = arrived.index(who)
                xa = GEOM["F_bank"]["arrive_x"][k]
                x = 690 + (xa - 690) * sstep((t - t_off) / 0.8)
                pos[who] = dict(x=round(x, 1), y=GEOM["F_bank"]["top_y_at_plank"], on="F")
                hs = hands[who]
                if "liana" in hs: hs[hs.index("liana")] = "free"
        # empty plank spring after the most recent step-off
        offs = [c[2] for c in V["crossings"] if c[2] <= t]
        sp = 0.0
        if not occ and offs:
            dt = t - max(offs); sp = 2.0 * math.exp(-dt / 0.25) * math.cos(2 * math.pi * 3 * dt)
        # invariants
        assert len(occ) <= 1, (vk, t, occ)
        for p, hs in hands.items():
            assert len(hs) == 2
            if p in occ: assert hs.count("liana") == 1, (vk, t, p, hs)
        assert sum(1 for p in hands for h in hands[p] if h == "bag") == (0 if holders["bag"] in ("ground_N", "ground_F") else 1)
        bag_y = pos[holders["bag"]]["y"] - 40 if holders["bag"] in pos else None
        assert bag_y is None or bag_y < wl
        sh = None
        if V["shoe_t0"] is not None and t >= V["shoe_t0"]:
            if holders["shoe"] == "water": sh = shoe_xy(t - V["shoe_t0"])
        fr = dict(f=f, t=t, water_y=round(wl, 2), water_rise_px=round(416 - wl, 2), plank_occupant=(occ[0] if occ else None),
                  plank_spring_px=round(sp, 2), bag=holders["bag"],
                  shoe=(holders["shoe"] if V["shoe_t0"] is not None and t >= V["shoe_t0"] else ("absent" if V["shoe_t0"] is None else "not_yet")),
                  hands={p: list(h) for p, h in hands.items()}, pos=pos)
        if sh: fr["shoe_xy"] = sh
        if occ: fr["clearance_px"] = round(wl - pos[occ[0]]["y"], 2)
        frames.append(fr)
    order = [c[0] for c in V["crossings"]]
    lastc = order[-1]
    summ = dict(version=vk, duration_s=V["dur"], fps=FPS, frames=len(frames), shoe_first_appearance_s=V["shoe_t0"],
                crossings=[dict(who=c[0], t_on=c[1], t_off=c[2], load=c[3], min_clearance_px=round(min_clear[c[0]], 2)) for c in V["crossings"]],
                order=order, bag_carrier=next(c[0] for c in V["crossings"] if "bag" in c[3] or (c[0] == "B" and vk == "Bl")) if vk == "Bl" else
                ("C" if vk == "L" else "A"), last_crosser=lastc, last_crosser_min_clearance_px=round(min_clear[lastc], 2),
                water_rise_end_px=round(416 - water_y(V["dur"]), 2), events=log,
                ledger=dict(before=V["order_before"], after=V["order_after"], strike_rewrite_window_s=V["ledger_strike"]))
    return summ, frames


res = {}
for vk in ("L", "E", "Bl"):
    s, fr = build(vk); res[vk] = dict(summary=s, frames=fr)
    print(json.dumps(s, ensure_ascii=False))
assert res["L"]["summary"]["last_crosser"] != res["E"]["summary"]["last_crosser"]
json.dump(dict(geometry=GEOM, stations=STATIONS, shoe_drift=SHOE_DRIFT, versions=res,
               coords="P2 plane, wide framing, picture px (800x540), y down; film t = L local + 2.0, E local + 39.5"),
          open(OUT, "w"), ensure_ascii=False)
