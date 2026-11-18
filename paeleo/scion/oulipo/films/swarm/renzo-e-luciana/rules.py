"""Renzo e Luciana · "Pausa delle dodici" — RULE MODELER (U1).

One clock for the whole film. Everything the editor, the performers and the sound
unit time against is computed here from the verification fixture (prompt §7) and
emitted to rules.json (+ rules-frames.json, one state record per frame).

    python3 films/swarm/renzo-e-luciana/rules.py          # writes rules.json, rules-frames.json,
                                                          # slate.png, visibility.png, slate frames, self-test
Importable:
    import sys; sys.path.insert(0, 'films/swarm/renzo-e-luciana'); import rules
    s = rules.state(k)                    # full per-frame state (version, tau, clock, facing, locations, heads, apple, camera, exposure)
    rules.assert_frame(k, minute_deg=None, meet_drawn=None)   # invariants 1, 2, 5 for one frame (raises AssertionError)
    rules.check_all()                     # every frame + global asserts; returns a report dict
    img = rules.slate_frame(u)            # handmade slate, u = seconds into the slate, 0 <= u < 2 (PIL RGB 960x540)

Time base: 24 fps. Film = A [0,35) s + slate [35,37) + B [37,72) s = 1728 frames.
Version-local time tau (s); fixture minute m = tau / 5 (12:00 + m). One fixture minute = 5.000 s = 120 frames.
Intervals are half-open [a,b) in fixture minutes unless marked closed.
Drawing uses films/kit.py only (Ink, font, easing); kit.py is not edited.
"""
from __future__ import annotations

import json
import math
import sys
from fractions import Fraction as Fr
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent                      # .../oulipo/films
sys.path.insert(0, str(FILMS))
import kit                                       # noqa: E402

FPS = 24
SEC_PER_MIN = 5                                  # one fixture minute = 5 s of film
A0, A1 = 0.0, 35.0
S0, S1 = 35.0, 37.0
B0, B1 = 37.0, 72.0
TOTAL = 72.0
NFRAMES = int(TOTAL * FPS)                       # 1728

# ------------------------------------------------------------ the fixture ---
# Intervals in fixture minutes after 12:00.  (a, b, closed_right)
class I:
    def __init__(self, a, b, closed=False):
        self.a, self.b, self.closed = Fr(a), Fr(b), closed

    def has(self, m):
        m = Fr(m)
        return self.a <= m and (m <= self.b if self.closed else m < self.b)

    def empty(self):
        return self.b < self.a or (self.b == self.a and not self.closed)

    def __and__(self, o):
        a = max(self.a, o.a)
        if self.b < o.b:
            b, c = self.b, self.closed
        elif o.b < self.b:
            b, c = o.b, o.closed
        else:
            b, c = self.b, self.closed and o.closed
        return I(a, b, c)

    def __eq__(self, o):
        return (self.empty() and o.empty()) or (self.a, self.b, self.closed) == (o.a, o.b, o.closed)

    def js(self):
        if self.empty():
            return None
        return [float(self.a), float(self.b), "closed" if self.closed else "half-open"]

    def clock(self):
        if self.empty():
            return "empty"
        return f"[{hhmm(self.a)},{hhmm(self.b)}{']' if self.closed else ')'}"


def hhmm(m):
    m = float(m)
    s = int(round(m * 60))
    return f"12:{s // 60:02d}" + (f":{s % 60:02d}" if s % 60 else "")


VERSIONS = ("A", "B")
BREAK = {
    "A": {"renzo": I(0, 3), "luciana": I(0, 4)},
    "B": {"renzo": I(0, 3), "luciana": I(3, 7)},      # the late bell
}
CORNER_ACCESS = I(1, 4)
FACING = [(I(0, 1), "FLOOR"), (I(1, 4), "OFFICE"), (I(4, 7, True), "FLOOR")]   # same in A and B
OFFICE = I(1, 4)


def meeting_window(v):
    """MeetingWindow = break(R) ∩ break(L) ∩ access(corner) ∩ {t : facing(t) = OFFICE}."""
    return BREAK[v]["renzo"] & BREAK[v]["luciana"] & CORNER_ACCESS & OFFICE


MW = {v: meeting_window(v) for v in VERSIONS}
assert MW["A"] == I(1, 3), MW["A"].clock()
assert MW["B"].empty(), MW["B"].clock()
assert (BREAK["B"]["renzo"] & BREAK["B"]["luciana"]).empty()


def facing_at(m):
    for iv, f in FACING:
        if iv.has(m):
            return f
    return "FLOOR"                                    # after 12:07 (never reached inside a version)


# ------------------------------------------------------------ clock math ---
def version_of(t):
    """('A'|'slate'|'B', tau seconds)"""
    if t < S0:
        return "A", t - A0
    if t < B0:
        return "slate", t - S0
    return "B", t - B0


def fixture_minutes(tau):
    return tau / SEC_PER_MIN


def minute_hand_deg(tau):
    """Clockwise from 12, degrees. 6° per fixture minute (12:00 -> 0°, 12:07 -> 42°)."""
    return 6.0 * tau / SEC_PER_MIN


def hour_hand_deg(tau):
    """Clockwise from 12; 0.5° per fixture minute (12 o'clock -> 0°)."""
    return 0.5 * tau / SEC_PER_MIN


def clock_angles(t):
    """Film time -> (minute°, hour°) or None on the slate (no clock drawn)."""
    v, tau = version_of(t)
    if v == "slate":
        return None
    return minute_hand_deg(tau), hour_hand_deg(tau)


def clock_text(tau):
    s = tau / SEC_PER_MIN * 60
    return f"12:{int(s // 60):02d}:{int(s % 60):02d}"


def frame_of(t):
    return int(round(t * FPS))


# ------------------------------------------------------------ blocking ---
# Locations (stage left = clock wall + CAPOREPARTO doorway; stage right = work station, offscreen):
#   off       not on stage (at work / not yet released)
#   entering  walking on
#   open_right / open_left   seated at an open end of the pail pile, in view of the doorway
#   to_corner sliding along behind the pile toward the corner
#   corner    the pail corner (hidden from the clock wall; seen from the doorway only when facing = FLOOR)
#   aisle     walking past the pile / between pile and clock
#   clock     at the time clock (punch)
#   station   gone back to work (offscreen right)
PILE_ZONE = {"to_corner", "corner"}                    # concealment positions (rule trigger zone)
ONSTAGE = {"entering", "open_right", "open_left", "to_corner", "corner", "aisle", "clock"}

# (tau0, tau1, location) in version-local seconds; contiguous, covering [0,35)
LOC = {
    "A": {
        "renzo": [(0, .4, "off"), (.4, 2.0, "entering"), (2.0, 5.0, "open_right"), (5.0, 6.0, "to_corner"),
                  (6.0, 14.3, "corner"), (14.3, 15.0, "aisle"), (15.0, 15.8, "clock"), (15.8, 35, "station")],
        "luciana": [(0, 1.0, "off"), (1.0, 2.6, "entering"), (2.6, 5.0, "open_left"), (5.0, 7.0, "to_corner"),
                    (7.0, 19.0, "corner"), (19.0, 19.6, "aisle"), (19.6, 20.6, "clock"), (20.6, 35, "station")],
    },
    "B": {
        "renzo": [(0, .4, "off"), (.4, 2.0, "entering"), (2.0, 5.0, "open_right"), (5.0, 6.0, "to_corner"),
                  (6.0, 14.3, "corner"), (14.3, 15.0, "aisle"), (15.0, 15.4, "clock"), (15.4, 16.5, "aisle"),
                  (16.5, 35, "station")],
        "luciana": [(0, 15.0, "off"), (15.0, 15.6, "entering"), (15.6, 16.5, "aisle"), (16.5, 19.2, "corner"),
                    (19.2, 19.8, "aisle"), (19.8, 34.3, "open_left"), (34.3, 35, "clock")],
    },
}

# Head substitutions (drawing substitution, #38 method): (tau, state); each state is held >= 6 frames.
HEADS = {
    "A": {
        "renzo": [(0.4, "walk"), (2.0, "clock"), (3.5, "door"), (4.4, "clock"), (5.0, "door"), (5.6, "her"),
                  (8.0, "forward"), (9.0, "clock"), (10.6, "her"), (12.4, "forward"), (13.5, "clock"),
                  (14.0, "lid"), (14.3, "walk"), (15.0, "clock")],
        "luciana": [(1.0, "walk"), (2.6, "pail"), (4.0, "door"), (5.6, "him"), (10.6, "forward"), (11.5, "him"),
                    (15.0, "pail"), (19.0, "walk"), (19.6, "clock")],
        "foreman": [(0.0, "front_pan_left"), (1.6, "front_pan_centre"), (3.2, "front_pan_right"),
                    (4.4, "front_pan_centre"), (5.0, "back_reading"), (20.0, "front_pan_right"),
                    (22.0, "front_pan_centre"), (24.5, "front_pan_left"), (26.0, "front_pan_centre"),
                    (28.0, "front_pan_right"), (31.0, "front_pan_centre"), (33.5, "front_pan_left")],
    },
    "B": {
        "renzo": [(0.4, "walk"), (2.0, "clock"), (3.5, "door"), (4.4, "clock"), (5.0, "door"), (5.6, "empty_place"),
                  (6.0, "clock"), (8.0, "door"), (10.0, "empty_place"), (11.7, "clock"), (13.0, "door"),
                  (13.6, "empty_place"), (14.0, "forward"), (14.3, "walk"), (15.0, "clock"), (15.4, "her")],
        "luciana": [(15.0, "walk"), (15.6, "him"), (16.5, "pail"), (18.0, "forward"), (18.6, "pail"),
                    (20.0, "door"), (21.0, "forward"), (23.0, "pail"), (34.3, "clock")],
        "foreman": [(0.0, "front_pan_left"), (1.6, "front_pan_centre"), (3.2, "front_pan_right"),
                    (4.4, "front_pan_centre"), (5.0, "back_reading"), (20.0, "front_pan_right"),
                    (20.5, "front_on_luciana")],
    },
}

# Apple: (tau, state, attached_to). States: apple0 whole, apple1..apple3 bitten (apple3 = core).
APPLE = {
    "A": [(0.0, None, "in_L_pail"), (2.8, "apple0", "L_wrist"), (8.5, "apple1", "L_wrist"), (11.0, "apple2", "L_wrist"),
          (13.0, "apple3", "L_wrist"), (13.2, "apple3", "R_hand"), (14.0, "apple3", "R_lid")],
    "B": [(0.0, "apple0", "R_pocket"), (6.5, "apple0", "R_hand"), (14.0, "apple1", "R_hand"), (16.0, "apple1", "L_lid"),
          (17.2, "apple1", "L_wrist"), (18.0, "apple2", "L_wrist")],
}
BITES = {"A": [(8.5, "renzo", "apple0->apple1"), (11.0, "luciana", "apple1->apple2"), (13.0, "renzo", "apple2->apple3 (core)")],
         "B": [(14.0, "renzo", "apple0->apple1 (his one bite, for her)"), (18.0, "luciana", "apple1->apple2")]}
LIDS = {"A": [(2.8, "L_lid", "open"), (13.6, "R_lid", "open"), (18.0, "L_lid", "closed")],
        "B": [(17.0, "L_lid", "open")]}
CARDS = {"A": [(15.0, "renzo", "in"), (20.0, "luciana", "in")],
         "B": [(15.0, "renzo", "in"), (34.5, "luciana", "in")]}

# Camera, same in both versions (equivalent replay): stage = 1296x729, WIDE = whole stage,
# MEDIUM = 1.35x push (960x540 window); centres in stage px (from the approved test shot).
CAM_WIDE = {"zoom": 1.0, "centre": [648.0, 364.5]}
CAM_MEDIUM = {"zoom": 1.35, "centre": [540.0, 290.0],
              "note": "editor may raise zoom (<=1.6) so the couple reaches ~50% frame height, provided the door jamb and clock stay in frame"}
CAMERA = [(0.0, 5.0, "WIDE"), (5.0, 7.0, "PUSH"), (7.0, 14.3, "MEDIUM"), (14.3, 16.3, "PULL"), (16.3, 35.0, "WIDE")]

# Occlusion DAG (#45), back to front. Invariant: this order in every frame.
LAYERS = ["wall_plate", "door_frame", "foreman", "door_leaf", "luciana_body", "luciana_head", "renzo_body", "renzo_head",
          "apple", "luciana_forearm", "pail_pile_occluder", "pail_lids", "lid_props", "clock_hands"]
LAYER_NOTES = {
    "apple": "drawn under Luciana's forearm while on L_wrist (fingers pinch in front); above the occluder when on a lid",
    "B_crossing": "at the B near-miss Luciana passes behind the pail-lid line, Renzo in front of it: order L < occluder < R for tau [15.0,16.5)",
}


def _seg(segs, tau):
    for a, b, x in segs:
        if a <= tau < b:
            return x
    return segs[-1][2]


def _last(keys, tau, default=None):
    out = default
    for k in keys:
        if k[0] <= tau + 1e-9:
            out = k
    return out


def camera_at(tau):
    for a, b, s in CAMERA:
        if a <= tau < b:
            if s in ("WIDE", "MEDIUM"):
                c = CAM_WIDE if s == "WIDE" else CAM_MEDIUM
                return {"state": s, "zoom": c["zoom"], "centre": list(c["centre"]), "u": None}
            u = kit.smooth((tau - a) / (b - a))
            f, g = (CAM_WIDE, CAM_MEDIUM) if s == "PUSH" else (CAM_MEDIUM, CAM_WIDE)
            return {"state": s, "u": round(u, 4),
                    "zoom": round(kit.lerp(f["zoom"], g["zoom"], u), 4),
                    "centre": [round(kit.lerp(f["centre"][i], g["centre"][i], u), 2) for i in (0, 1)]}
    return {"state": "WIDE", "zoom": 1.0, "centre": list(CAM_WIDE["centre"]), "u": None}


def location(v, who, tau):
    return _seg(LOC[v][who], tau)


def meet(v, tau):
    """The central operation's typed preconditions. True only while the shared encounter may be drawn."""
    m = fixture_minutes(tau)
    return (BREAK[v]["renzo"].has(m) and BREAK[v]["luciana"].has(m) and CORNER_ACCESS.has(m)
            and facing_at(m) == "OFFICE" and location(v, "renzo", tau) == "corner"
            and location(v, "luciana", tau) == "corner")


def exposure(v, tau):
    """Who sees whom, and what persists."""
    m = fixture_minutes(tau)
    f = facing_at(m)
    loc = {w: location(v, w, tau) for w in ("renzo", "luciana")}
    on = {w for w in loc if loc[w] in ONSTAGE}
    fsees = sorted(on) if f == "FLOOR" else []
    ap = _last(APPLE[v], tau)
    props = []
    if v == "A" and tau >= 14.0:
        props.append("apple core (3 bites) in Renzo's pail lid")
    if v == "B" and 16.0 <= tau < 17.2:
        props.append("apple with Renzo's one bite on Luciana's pail lid")
    if v == "B" and tau >= 18.0:
        props.append("two-bite apple (one his, one hers) in Luciana's hand")
    state = "clear"
    if f == "FLOOR" and props:
        state = "foreman sees the core in the lid; it reads as litter (unread evidence)" if v == "A" else \
                "foreman sees Luciana with Renzo's token (legal, alone, carried to the end)"
    if f == "FLOOR" and len(PILE_ZONE & set(loc.values())) and len(on) == 2 and \
            all(loc[w] in PILE_ZONE for w in loc):
        state = "VIOLATION"
    return {
        "foreman_facing": f,
        "foreman_sees": fsees,
        "renzo_sees_luciana": len(on) == 2,
        "luciana_sees_renzo": len(on) == 2,
        "couple_sees_foreman_facing": True,           # the doorway is in plain view of the pile
        "hidden_from_foreman": sorted(w for w in on if f == "OFFICE"),
        "apple": {"state": ap[1], "at": ap[2]},
        "carried_forward": props,
        "exposure_state": state,
    }


# Knowledge (invariant 3): what each actor believes about the schedule.
def beliefs(v, tau):
    if v == "A":
        return {"renzo": "L's break is [12:00,12:04)", "luciana": "R's break is [12:00,12:03)"}
    if tau < 15.0:
        return {"renzo": "expects L at 12:00 as usual (does not know of the late bell)",
                "luciana": "held at her station; her bell has not rung"}
    return {"renzo": "learns at the late bell (12:03) that her break was moved; his own has ended",
            "luciana": "released at 12:03; finds his token on her lid"}


# ------------------------------------------------------------ state ---
def state(k):
    t = k / FPS
    v, tau = version_of(t)
    if v == "slate":
        return {"frame": k, "t": round(t, 4), "version": "slate", "u": round(tau, 4)}
    m = fixture_minutes(tau)
    heads = {w: _last(HEADS[v][w], tau, (0, "off"))[1] for w in ("renzo", "luciana", "foreman")}
    loc = {w: location(v, w, tau) for w in ("renzo", "luciana")}
    for w in loc:
        if loc[w] in ("off", "station"):
            heads[w] = None
    return {
        "frame": k, "t": round(t, 4), "version": v, "tau": round(tau, 4), "fixture": clock_text(tau),
        "minute_deg": round(minute_hand_deg(tau), 4), "hour_deg": round(hour_hand_deg(tau), 4),
        "on_break": {w: BREAK[v][w].has(m) for w in ("renzo", "luciana")},
        "corner_access": CORNER_ACCESS.has(m),
        "location": loc, "heads": heads, "meet": meet(v, tau),
        "in_meeting_window": MW[v].has(m),
        "camera": camera_at(tau),
        "lids": {lid: s for (_, lid, s) in sorted([x for x in LIDS[v] if x[0] <= tau + 1e-9])},
        "cards_in": [w for (tt, w, _) in CARDS[v] if tt <= tau + 1e-9],
        "exposure": exposure(v, tau),
        "beliefs": beliefs(v, tau),
    }


# ------------------------------------------------------------ asserts (importable) ---
def assert_one_clock(k, measured_minute_deg=None, tol=0.5):
    """Invariant 1: minute hand = 6°·tau/5. Pass the angle the renderer actually drew to check it."""
    t = k / FPS
    a = clock_angles(t)
    if a is None:
        return True
    v, tau = version_of(t)
    assert abs(a[0] - 6.0 * tau / 5.0) < 1e-9
    if measured_minute_deg is not None:
        d = (measured_minute_deg - a[0] + 180) % 360 - 180
        assert abs(d) <= tol, f"frame {k}: minute hand {measured_minute_deg:.2f}° vs rule {a[0]:.2f}°"
    return True


def assert_rule(k):
    """Invariant 2: never both actors in the pail zone while the foreman faces FLOOR."""
    v, tau = version_of(k / FPS)
    if v == "slate":
        return True
    f = facing_at(fixture_minutes(tau))
    both = all(location(v, w, tau) in PILE_ZONE for w in ("renzo", "luciana"))
    assert not (both and f == "FLOOR"), f"frame {k}: co-presence in corner while foreman faces FLOOR"
    return True


def assert_meeting(k, meet_drawn=None):
    """Invariant 5: the shared encounter only inside the computed MeetingWindow.
    meet_drawn: what the renderer drew (True/False); None checks the model only."""
    v, tau = version_of(k / FPS)
    if v == "slate":
        assert not meet_drawn, f"frame {k}: meet drawn on the slate"
        return True
    mm = meet(v, tau)
    if mm:
        assert MW[v].has(fixture_minutes(tau)), f"frame {k}: meet outside MeetingWindow"
    if meet_drawn is not None:
        assert bool(meet_drawn) == mm, f"frame {k}: renderer meet={meet_drawn}, rules meet={mm}"
    return True


def assert_layer_order(order):
    """#45: the renderer's actual back-to-front list of layer names must respect LAYERS order."""
    idx = [LAYERS.index(x) for x in order if x in LAYERS]
    assert idx == sorted(idx), f"layer order broken: {order}"
    return True


def assert_frame(k, minute_deg=None, meet_drawn=None):
    assert_one_clock(k, minute_deg)
    assert_rule(k)
    assert_meeting(k, meet_drawn)
    return True


def _hold_frames(keys, end=35.0):
    out = []
    for i, kk in enumerate(keys):
        nxt = keys[i + 1][0] if i + 1 < len(keys) else end
        out.append((kk[1], frame_of(nxt) - frame_of(kk[0])))
    return out


def check_all():
    rep = {"frames": NFRAMES, "per_frame": "pass"}
    meet_frames = {"A": [], "B": []}
    cross = 0
    for k in range(NFRAMES):
        assert_frame(k)
        v, tau = version_of(k / FPS)
        if v in VERSIONS and meet(v, tau):
            meet_frames[v].append(k)
        if v == "B":
            locs = [location(v, w, tau) for w in ("renzo", "luciana")]
            if all(l in ONSTAGE for l in locs):
                cross += 1
    assert meet_frames["B"] == [], "B must contain no meeting"
    a0, a1 = meet_frames["A"][0], meet_frames["A"][-1]
    assert a0 >= frame_of(5.0) and a1 < frame_of(15.0)
    assert cross <= int(1.5 * FPS), f"B co-presence {cross} frames > 36"
    for v in VERSIONS:                                  # substitutions held >= 6 frames
        for w, keys in HEADS[v].items():
            for s, n in _hold_frames(keys):
                assert n >= 6, f"{v} {w} head {s} held {n} frames"
    for v in VERSIONS:                                  # bites happen in hand, not on a lid
        for tb, who, _ in BITES[v]:
            assert location(v, who, tb) in ("corner",), f"{v} bite at {tb} not in the corner"
    for v in VERSIONS:                                  # each bite of A inside the meeting
        if v == "A":
            for tb, _, _ in BITES[v]:
                assert meet("A", tb)
    # defining frames
    s10, s47 = state(frame_of(10.0)), state(frame_of(47.0))
    assert s10["meet"] and s10["exposure"]["foreman_facing"] == "OFFICE" and s10["fixture"] == "12:02:00"
    assert s47["location"]["renzo"] == "corner" and s47["location"]["luciana"] == "off" and s47["fixture"] == "12:02:00"
    assert state(frame_of(57.5))["heads"]["foreman"] == "front_on_luciana"
    assert "two-bite" in " ".join(state(frame_of(60.0))["exposure"]["carried_forward"])
    assert "core" in " ".join(state(frame_of(30.0))["exposure"]["carried_forward"])
    rep.update({"meet_frames_A": [a0, a1], "meet_seconds_A": [a0 / FPS, (a1 + 1) / FPS],
                "meet_frames_B": 0, "B_copresence_frames": cross,
                "clock_checks": {f"t={t}": clock_text(version_of(t)[1]) for t in (0, 10, 34.99, 37, 47, 71.99)}})
    return rep


# ------------------------------------------------------------ cues ---
def cues():
    """Full cue list in film seconds and frames. kind: bell, punch, turn, bite, sub, cam, steps, sfx, slate, prop."""
    C = []

    def add(t, kind, what, dur=None, **kw):
        c = {"t": round(t, 4), "frame": frame_of(t), "kind": kind, "what": what}
        if dur is not None:
            c["dur"] = round(dur, 4)
            c["end_frame"] = frame_of(t + dur)
        c["fixture"] = clock_text(version_of(t)[1]) if version_of(t)[0] != "slate" else None
        c.update(kw)
        C.append(c)

    for v, off in (("A", A0), ("B", B0)):
        add(off, "version", f"version {v} begins (12:00:00), camera WIDE")
        if v == "A":
            add(off, "bell", "work bell: both breaks begin (one ring ~2 s)", 2.0, sound="work_bell")
        else:
            add(off, "bell", "work bell: Renzo's break only (single ring)", 1.2, sound="work_bell")
        add(off + .4, "steps", "foreman pacing in the doorway (FLOOR)", 4.6, sound="footsteps_foreman", pan=-.6)
        add(off + .4, "steps", "Renzo walks on from the right", 1.6, sound="footsteps", pan=.6)
        add(off + 35 * 0 + 0, "sfx", "room tone bed (whole version)", 35.0, sound="room_tone")
        add(off, "sfx", "clock tick bed" + (" (rises 12:01-12:03)" if v == "B" else ""), 35.0, sound="clock_tick")
        if v == "A":
            add(off + 1.0, "steps", "Luciana walks on from the left", 1.6, sound="footsteps", pan=-.3)
        for tt, lid, s in LIDS[v]:
            add(off + tt, "prop", f"{lid} {s}", sound="lid_tin")
        add(off + 5.0, "turn", "FOREMAN TURNS to OFFICE: substitution front -> back photograph (12:01)", sound="paper_rustle", pan=-.6)
        add(off + 12.0, "sfx", "foreman turns a time sheet", sound="paper_rustle", pan=-.6)
        add(off + 5.0, "cam", "camera WIDE -> MEDIUM (push 1.35x)", 2.0)
        add(off + 14.3, "cam", "camera MEDIUM -> WIDE (pull back)", 2.0)
        if v == "B":
            add(off + 6.5, "prop", "Renzo takes the apple out of his pocket (does not eat)")
        for tb, who, what in BITES[v]:
            add(off + tb, "bite", f"{who} bites: {what}", sound="bite_crunch", tol_frames=1)
        if v == "A":
            add(off + 13.2, "prop", "Luciana gives Renzo the core")
            add(off + 14.0, "prop", "Renzo sets the core in his pail lid (persists to 12:07)", sound="tap_small")
        add(off + 14.3, "steps", "Renzo rises and walks to the clock", .7, sound="footsteps")
        if v == "A":
            add(off + 15.0, "punch", "Renzo punches in (12:03, end of his break); his card drops a slot", sound="timeclock_punch", tol_frames=1)
            add(off + 19.0, "steps", "Luciana walks from the corner to the clock", .6, sound="footsteps", pan=-.4)
            add(off + 20.0, "punch", "Luciana punches in (12:04, end of her break)", sound="timeclock_punch", tol_frames=1)
        else:
            add(off + 15.0, "bell", "LATE BELL (higher): Luciana's break begins 12:03", 1.6, sound="late_bell", tol_frames=1)
            add(off + 15.0, "punch", "Renzo punches in (12:03), same frame as the late bell", sound="timeclock_punch", tol_frames=1)
            add(off + 15.0, "steps", "Luciana walks on from the left (NEAR-MISS begins)", 1.5, sound="footsteps", pan=-.5)
            add(off + 15.4, "steps", "Renzo walks back past the pile to his station", 1.1, sound="footsteps", pan=.3)
            add(off + 16.0, "prop", "Renzo sets the once-bitten apple on Luciana's pail lid (wood tap)", sound="tap_small")
            add(off + 16.5, "sfx", "NEAR-MISS ends: Renzo off right, Luciana in the corner")
            add(off + 17.2, "prop", "Luciana picks up the apple")
            add(off + 19.2, "steps", "Luciana moves to the open left end", .6, sound="footsteps", pan=-.3)
            add(off + 34.5, "punch", "Luciana punches in (end of her late break, 12:06:54)", sound="timeclock_punch", tol_frames=1)
        add(off + 20.0, "turn", "FOREMAN TURNS back to FLOOR: substitution back -> front photograph (12:04)", sound="footsteps_foreman", pan=-.6)
        add(off + 20.0, "steps", "foreman pacing resumes, fading", 15.0, sound="footsteps_foreman", pan=-.6)
        if v == "B":
            add(off + 20.5, "sub", "foreman's gaze settles on Luciana (head substitution held to 12:07)")
        for w in ("renzo", "luciana", "foreman"):
            for tt, s in HEADS[v][w]:
                add(off + tt, "sub", f"{w} head -> {s}", who=w, state=s)
        add(off + 35.0 - 1 / FPS, "version", f"version {v} last frame (clock 12:06:57.5 ≈ 12:07)")
    add(S0, "slate", "SLATE: handmade typed card + light box; whoosh as the card is set down", 2.0, sound="whoosh")
    add(S0 + .25, "slate", "Luciana's strip slides 3 minutes right (12:00-12:04 -> 12:03-12:07)", 1.5, sound="card_slide")
    C.sort(key=lambda c: (c["t"], c["kind"]))
    return C


# ------------------------------------------------------------ beats ---
def beats():
    rows = [
        ("A", 0.0, 0.4, "Bell. Clock 12:00. Foreman in the doorway facing FLOOR."),
        ("A", 0.4, 5.0, "R enters right, sits at the open right end, head to the clock. L enters, sits apart at the open left end, opens her pail: apple0. Two co-workers, not a couple."),
        ("A", 5.0, 7.0, "Foreman turns to OFFICE (back photograph). L slides along behind the pile to the corner; R tips toward her on his hip pin. Push to MEDIUM."),
        ("A", 7.0, 14.3, "MEETING (inside MeetingWindow [12:01,12:03)). She feeds, he guards: bite R 8.5, defining frame 10.0 (head to clock, apple at his mouth), bite L 11.0, bite R 13.0, core into his lid 14.0."),
        ("A", 14.3, 16.3, "R rises, walks to the clock, punches at 15.0 (12:03). Pull back to WIDE."),
        ("A", 16.3, 20.0, "L alone in the corner wipes her hand, closes her pail (18.0), walks to the clock, punches at 20.0 (12:04)."),
        ("A", 20.0, 35.0, "Foreman turns back to FLOOR; his gaze passes over the core in the lid without stopping (26.0). Empty pails to 12:07."),
        ("slate", 35.0, 37.0, "Handmade slate: 'B · la campanella suona in ritardo'; L's strip slides; the light column through all three slots closes."),
        ("B", 37.0, 42.0, "Same WIDE frame. Single bell (R only). R enters and sits in the open. L absent."),
        ("B", 42.0, 51.3, "Foreman turns to OFFICE (identical frames to A 5.0). R alone in the corner, apple out but uneaten; head clock -> door -> empty place, tightening. Counterpart frame 47.0. Bite for her at 51.0."),
        ("B", 51.3, 53.5, "R walks to the clock, punches at 52.0 as the LATE BELL rings. NEAR-MISS: L enters left, they pass at the pile (<= 1.5 s, she behind the lid line, he in front); he sets the bitten apple on her lid (53.0) and goes."),
        ("B", 53.5, 57.0, "L alone in the corner picks up the apple (54.2), takes bite 2 (55.0), moves to the open left end (56.2-56.8)."),
        ("B", 57.0, 72.0, "Foreman turns back to FLOOR and his gaze settles on L (57.5, held). She eats the two-bite apple in full view, legal and alone. Punches in at 71.5. End."),
    ]
    out = []
    for v, a, b, txt in rows:
        mid = (a + b) / 2
        st = state(frame_of(mid)) if v != "slate" else None
        out.append({"version": v, "t": [a, b], "frames": [frame_of(a), frame_of(b) - 1],
                    "fixture": None if st is None else [clock_text(version_of(a)[1]), clock_text(version_of(b - 1e-6)[1])],
                    "action": txt,
                    "exposure_at_mid": None if st is None else st["exposure"],
                    "camera_at_mid": None if st is None else st["camera"]["state"]})
    return out


# ------------------------------------------------------------ handmade slate ---
SLATE_TONES = {"desk": 40, "frame": 77, "glass": 228, "strip": 86, "strip_edge": 54, "card": 206, "ink": 30, "tab": 196}
X0, PX_MIN = 268, 80                     # strip coordinate: x = X0 + 80 px per fixture minute
ROWS = [("Renzo", 214), ("Luciana", 276), ("angolo", 338)]   # strip top y; each 62 px tall
STRIP_H = 62
_slate_cache = {}


def _fibre(w, h, seed, amp):
    rs = np.random.RandomState(seed)
    n = rs.normal(0, 1, (h, w)).astype(np.float32)
    a = np.array(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.7)), np.float32) - 128
    s = rs.normal(0, 1, (h // 3 + 1, w)).astype(np.float32)
    s = np.repeat(s, 3, 0)[:h]                            # short horizontal fibres (card stock)
    s = np.array(Image.fromarray(((s * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(2)), np.float32) - 128
    return (a * .6 + s * .4) / 40 * amp


def _grey(ink_img):
    return np.asarray(ink_img.convert("L"), np.float32)


def _slate_static():
    if "static" in _slate_cache:
        return _slate_cache["static"]
    T = SLATE_TONES
    ink = kit.Ink(0, 0, boil=0, wobble=.6, seed=3)
    g = (T["desk"],) * 3
    ink.paper(g, grain=False)
    # light box: dark plastic frame, glowing glass
    ink.rect(118, 176, 842, 470, fill=(T["frame"],) * 3, color=(T["strip_edge"],) * 3, width=2, rough=True)
    ink.rect(250, 190, 830, 456, fill=(T["glass"],) * 3, color=(170,) * 3, width=1.5, rough=False)
    # typed ruler card on the glass (12:00 ... 12:07)
    for m in range(8):
        x = X0 + PX_MIN * m
        ink.line([(x, 404), (x, 416)], color=(T["ink"],) * 3, width=1.6, rough=True, amount=.4)
        ink.text((x - (4 if m == 7 else 0), 420), f"12:0{m}", "mono", 13, (T["ink"],) * 3, anchor="ra" if m == 7 else "ma")
    for name, y in ROWS:                                    # typed paper labels on the box frame
        ink.rect(130, y + 16, 240, y + 44, fill=(T["tab"],) * 3, color=(120,) * 3, width=1, rough=True)
        ink.text((185, y + 30), name, "mono", 15, (T["ink"],) * 3, anchor="mm")
    base = _grey(ink.img) + _fibre(960, 540, 5, 5.0)
    # glass glow (the box is lit from inside): slightly brighter centre
    yy, xx = np.mgrid[0:540, 0:960]
    glass = (xx >= 250) & (xx < 830) & (yy >= 190) & (yy < 456)
    base[glass] += 8 * np.exp(-(((xx[glass] - 540) / 330.0) ** 2 + ((yy[glass] - 320) / 160.0) ** 2))
    # typed card (rotated), drawn once
    card = kit.Ink(0, 0, size=(560, 92), boil=0, wobble=.5, seed=9)
    card.paper((T["card"],) * 3, grain=False)
    rs = np.random.RandomState(4)
    s = "B · la campanella suona in ritardo"
    x = 22
    f = kit.font("mono", 25)
    for ch in s:                                            # typed: per-key strike weight and baseline wobble
        a = int(255 * (0.78 + 0.22 * rs.rand()))
        card.d.text((x, 30 + rs.normal(0, .5)), ch, font=f, fill=(T["ink"],) * 3 + (a,))
        x += f.getlength(ch)
    card.line([(18, 74), (540, 74)], color=(150,) * 3, width=1, rough=True, amount=.5)
    card.text((22, 76), "pausa delle dodici · versione B", "mono", 11, (95,) * 3)
    cg = _grey(card.img) + _fibre(560, 92, 7, 4.0)
    cimg = Image.fromarray(cg.clip(0, 255).astype(np.uint8)).convert("L")
    alpha = Image.new("L", (560, 92), 255)
    rot = -1.1
    cimg = cimg.rotate(rot, resample=Image.BICUBIC, expand=True, fillcolor=0)
    alpha = alpha.rotate(rot, resample=Image.BICUBIC, expand=True, fillcolor=0)
    _slate_cache["static"] = (base, cimg, alpha)
    return _slate_cache["static"]


def _strip_alpha(slot_min, shift_px, y):
    """Opaque card strip covering the glass row except its cut slot [a,b) minutes."""
    a = np.zeros((540, 960), np.float32)
    a[y:y + STRIP_H, 0:960] = 1.0
    x0 = int(round(X0 + PX_MIN * slot_min[0] + shift_px))
    x1 = int(round(X0 + PX_MIN * slot_min[1] + shift_px))
    a[y + 6:y + STRIP_H - 6, max(x0, 0):max(x1, 0)] = 0.0   # the slot (scissor cut, 6 px card margin)
    return a, (x0, x1)


def slate_frame(u):
    """Handmade slate, u in [0, 2) seconds. Strips: R [12:00,12:03), corner [12:01,12:04) fixed;
    L slides from A [12:00,12:04) to B [12:03,12:07) on u in [0.25, 1.75] (eased)."""
    T = SLATE_TONES
    base, cimg, calpha = _slate_static()
    img = base.copy()
    slide = kit.smooth((u - .25) / 1.5) * 3 * PX_MIN
    # a light hand sets the card down at the start: tiny settle over the first 0.2 s
    settle = 4.0 * (1 - kit.smooth(u / .2))
    yy, xx = np.mgrid[0:540, 0:960]
    glass = (xx >= 250) & (xx < 830) & (yy >= 190) & (yy < 456)
    lightmask = glass.astype(np.float32)
    strips = [((0, 3), 0.0, ROWS[0][1]), ((0, 4), slide, ROWS[1][1]), ((1, 4), 0.0, ROWS[2][1])]
    cover = np.zeros_like(img)
    for i, (slot, sh, y) in enumerate(strips):
        a, _ = _strip_alpha(slot, sh, y)
        a[:, :118] = 0; a[:, 842:] = 0                        # strips trimmed to the box
        a[:, :250] *= (xx[:, :250] >= 245)
        # card stock with its own fibre; darker cut edge
        tone = T["strip"] + 6 * (i - 1)
        edge = np.array(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES), np.float32) / 255
        layer = np.full_like(img, tone) + _strip_fibre(i)
        layer = layer * (1 - edge * .45)
        img = img * (1 - a) + layer * a
        cover = np.maximum(cover, a)
    # light through the slots blooms a little onto the card edges (lit from inside the box)
    lit = lightmask * (1 - cover)
    bloom = np.array(Image.fromarray((lit * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
    img = img + 14 * bloom * cover
    # column of light through all three slots: where the three slot gaps coincide
    col = _common_light(slide)
    # the typed card, with a soft drop shadow (key light upper left -> shadow down right)
    cx, cy = 200, int(54 + settle)
    ca = np.asarray(calpha, np.float32) / 255
    cg = np.asarray(cimg, np.float32)
    h, w = ca.shape
    sh = np.zeros_like(img)
    sh[cy + 7:cy + 7 + h, cx + 9:cx + 9 + w] = ca
    sh = np.array(Image.fromarray((sh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    img = img * (1 - .45 * sh)
    region = img[cy:cy + h, cx:cx + w]
    img[cy:cy + h, cx:cx + w] = region * (1 - ca) + cg * ca
    g = np.clip(img, 0, 255).astype(np.uint8)
    out = Image.fromarray(np.stack([g] * 3, -1))
    out.info["light_column_minutes"] = col
    return out


_sf = {}


def _strip_fibre(i):
    if i not in _sf:
        _sf[i] = _fibre(960, 540, 20 + i, 4.0)
    return _sf[i]


def _common_light(slide_px):
    """Minutes (in the A frame of reference) where light passes all three strips."""
    sh = slide_px / PX_MIN
    iv = I(0, 3) & I(Fr(0) + Fr(sh).limit_denominator(1000), Fr(4) + Fr(sh).limit_denominator(1000)) & I(1, 4)
    return iv.js()


# ------------------------------------------------------------ visibility graph ---
def visibility_png(path):
    Wd, Hd = 1600, 980
    ink = kit.Ink(0, 0, size=(Wd, Hd), boil=0, wobble=.5, seed=1)
    ink.paper(kit.PAGE, grain=False)
    INK, MUT, RULE, ACC = kit.INK, kit.MUTED, kit.RULE, kit.ACCENT
    L, R = 250, 1540
    xm = lambda m: L + (R - L) * m / 7.0
    ink.text((40, 26), "Renzo e Luciana · pausa delle dodici — schedule and visibility (rules.json)", "serif", 34, INK)
    ink.text((40, 70), "One clock: 1 fixture minute = 5 s = 120 frames. Version A film t = 0-35 s, slate 35-37, B 37-72 s (t = 37 + tau).",
             "mono", 15, MUT)
    loc_tone = {"off": None, "station": None, "entering": (150, 150, 150), "open_right": (120, 120, 120),
                "open_left": (120, 120, 120), "to_corner": (80, 80, 80), "corner": (40, 40, 40),
                "aisle": (170, 170, 170), "clock": (200, 200, 200)}
    for p, v in enumerate(VERSIONS):
        top = 120 + p * 420
        ink.text((40, top), f"Version {v}" + (" · orario originale" if v == "A" else " · campanella in ritardo"), "serif", 28, INK)
        ink.text((40, top + 34), f"MeetingWindow = {MW[v].clock()}", "mono", 15, ACC if v == "A" else MUT)
        y0 = top + 64
        rows = [("Renzo break", BREAK[v]["renzo"]), ("Luciana break", BREAK[v]["luciana"]),
                ("corner access", CORNER_ACCESS)]
        y = y0
        for name, iv in rows:
            ink.text((L - 14, y + 11), name, "mono", 14, INK, anchor="rm")
            ink.rect(xm(0), y, xm(7), y + 22, fill=(236, 230, 220), color=RULE, width=1, rough=False)
            if not iv.empty():
                ink.rect(xm(float(iv.a)), y, xm(float(iv.b)), y + 22, fill=(110, 104, 96), color=INK, width=1.2, rough=False)
            y += 30
        ink.text((L - 14, y + 11), "foreman faces", "mono", 14, INK, anchor="rm")
        for iv, f in FACING:
            a, b = float(iv.a), float(iv.b)
            ink.rect(xm(a), y, xm(b), y + 22, fill=(60, 56, 52) if f == "FLOOR" else (236, 230, 220), color=INK, width=1.2, rough=False)
            ink.text(((xm(a) + xm(b)) / 2, y + 11), f + (" (sees the pile)" if f == "FLOOR" else " (back turned)"), "mono", 12,
                     (240, 236, 228) if f == "FLOOR" else INK, anchor="mm")
        y += 30
        ink.text((L - 14, y + 11), "MeetingWindow", "mono", 14, ACC, anchor="rm")
        ink.rect(xm(0), y, xm(7), y + 22, fill=(236, 230, 220), color=RULE, width=1, rough=False)
        if not MW[v].empty():
            ink.rect(xm(float(MW[v].a)), y, xm(float(MW[v].b)), y + 22, fill=ACC, color=ACC, width=1, rough=False)
            ink.text(((xm(float(MW[v].a)) + xm(float(MW[v].b))) / 2, y + 11), "meet() allowed", "mono", 12, (250, 245, 240), anchor="mm")
        else:
            ink.text((xm(3.5), y + 11), "empty: break(R) and break(L) do not overlap", "mono", 12, MUT, anchor="mm")
        y += 40
        for who in ("renzo", "luciana"):
            ink.text((L - 14, y + 9), f"{who} where", "mono", 14, INK, anchor="rm")
            for a, b, l in LOC[v][who]:
                tone = loc_tone[l]
                if tone is None:
                    ink.line([(xm(a / 5), y + 9), (xm(b / 5), y + 9)], color=RULE, width=1, rough=False)
                    continue
                ink.rect(xm(a / 5), y + 2, xm(b / 5), y + 16, fill=tone, color=INK, width=.8, rough=False)
                if (b - a) >= 1.6:
                    ink.text(((xm(a / 5) + xm(b / 5)) / 2, y + 9), l, "mono", 11, (250, 248, 240) if sum(tone) < 400 else INK, anchor="mm")
            y += 24
        # exposure / sight lines and events
        ink.text((L - 14, y + 9), "foreman sees", "mono", 14, INK, anchor="rm")
        k0 = frame_of(A0 if v == "A" else B0)
        prev = None
        lastx = None
        for kk in range(k0, k0 + 840, 6):
            s = state(kk)
            fs = ",".join(n[0].upper() for n in s["exposure"]["foreman_sees"]) or "-"
            cf = s["exposure"]["exposure_state"]
            lab = fs + ("" if cf == "clear" else (" + core in lid (unread)" if v == "A" else " + L holding R's token, gaze held"))
            if lab != prev:
                xx_ = xm(s["tau"] / 5)
                if lastx is not None and xx_ - lastx < 220:
                    xx_ = lastx + 220
                lastx = xx_
                ink.text((xx_, y + 9), lab, "mono", 11, ACC if cf != "clear" else INK, anchor="lm")
                prev = lab
        y += 24
        ev = [c for c in cues() if c["kind"] in ("bell", "punch", "turn", "bite") and
              ((v == "A" and c["t"] < 35) or (v == "B" and c["t"] >= 37))]
        ink.text((L - 14, y + 9), "cues", "mono", 14, INK, anchor="rm")
        sym = {"bell": "BELL", "punch": "punch", "turn": "TURN", "bite": "bite"}
        placed = []
        for c in ev:
            tau = c["t"] - (0 if v == "A" else 37)
            x = xm(tau / 5)
            n = 0
            while any(abs(x - px) < 95 and pn == n for px, pn in placed):
                n += 1
            placed.append((x, n))
            ink.line([(x, y0 - 6), (x, y + 6 + 14 * n)], color=ACC if c["kind"] in ("bell", "turn") else MUT, width=1, rough=False)
            ink.text((x + 3, y + 8 + 14 * n), f"{sym[c['kind']]} {c['t']:g}s", "mono", 11, INK, anchor="lm")
        # axis
        ya = y + 52
        for m in range(8):
            ink.line([(xm(m), ya - 4), (xm(m), ya + 4)], color=INK, width=1, rough=False)
            ink.text((xm(m), ya + 8), f"12:0{m}", "mono", 12, INK, anchor="ma")
            ink.text((xm(m), ya + 24), f"t {m * 5 + (0 if v == 'A' else 37)} s", "mono", 11, MUT, anchor="ma")
        ink.line([(xm(0), ya), (xm(7), ya)], color=INK, width=1, rough=False)
    ink.text((40, Hd - 34), "Rule (asserted per frame): never both in {to_corner, corner} while the foreman faces FLOOR.  "
             "Carried forward: A core in R's lid from t 14; B two-bite apple seen by foreman from t 57.", "mono", 13, MUT)
    ink.img.convert("RGB").save(path)


# ------------------------------------------------------------ emit ---
def build():
    rep = check_all()
    out = {
        "slug": "renzo-e-luciana", "unit": "rule-modeler (U1)", "base": "plan.md §3-5 (authoritative), test-shot r2 approved",
        "time_base": {"fps": FPS, "sec_per_fixture_minute": SEC_PER_MIN, "frames_per_fixture_minute": SEC_PER_MIN * FPS,
                      "total_s": TOTAL, "total_frames": NFRAMES,
                      "segments": [{"name": "A", "t": [A0, A1], "frames": [0, frame_of(A1) - 1], "tau": "t"},
                                   {"name": "slate", "t": [S0, S1], "frames": [frame_of(S0), frame_of(S1) - 1], "u": "t - 35"},
                                   {"name": "B", "t": [B0, B1], "frames": [frame_of(B0), NFRAMES - 1], "tau": "t - 37"}],
                      "fixture_clock": "c(tau) = 12:00 + tau/5 min (tau = version-local seconds)"},
        "actors": {
            "renzo": {"role": "operaio", "commitment": "Luciana", "break": {v: BREAK[v]["renzo"].js() for v in VERSIONS},
                      "break_clock": {v: BREAK[v]["renzo"].clock() for v in VERSIONS}},
            "luciana": {"role": "operaia", "commitment": "Renzo", "break": {v: BREAK[v]["luciana"].js() for v in VERSIONS},
                        "break_clock": {v: BREAK[v]["luciana"].clock() for v in VERSIONS}},
            "foreman": {"role": "observer (InstitutionalRule)", "facing": [{"interval": iv.js(), "clock": iv.clock(), "facing": f} for iv, f in FACING]},
        },
        "institutional_rule": {"observer": "foreman", "trigger": "facing = FLOOR and both actors in {to_corner, corner}",
                               "scope": "factory floor visible from the CAPOREPARTO doorway",
                               "visible_consequence": "the foreman's turn and gaze; a card pulled from the rack (never triggered)"},
        "corner_access": {"interval": CORNER_ACCESS.js(), "clock": CORNER_ACCESS.clock()},
        "meeting_window": {v: {"interval": MW[v].js(), "clock": MW[v].clock(),
                               "formula": "break(R) ∩ break(L) ∩ access(corner) ∩ facing=OFFICE"} for v in VERSIONS},
        "meeting_frames": {"A": rep["meet_frames_A"], "A_seconds": rep["meet_seconds_A"], "B": None},
        "locations": {v: {w: [{"tau": [a, b], "t": [a + (0 if v == "A" else 37), b + (0 if v == "A" else 37)], "loc": l}
                              for a, b, l in LOC[v][w]] for w in LOC[v]} for v in VERSIONS},
        "pile_zone": sorted(PILE_ZONE),
        "heads": {v: {w: [{"tau": tt, "t": tt + (0 if v == "A" else 37), "frame": frame_of(tt + (0 if v == "A" else 37)), "state": s}
                          for tt, s in HEADS[v][w]] for w in HEADS[v]} for v in VERSIONS},
        "apple": {v: [{"tau": tt, "t": tt + (0 if v == "A" else 37), "frame": frame_of(tt + (0 if v == "A" else 37)), "state": s, "attached_to": at}
                      for tt, s, at in APPLE[v]] for v in VERSIONS},
        "bites": {v: [{"tau": tt, "t": tt + (0 if v == "A" else 37), "frame": frame_of(tt + (0 if v == "A" else 37)), "who": w, "substitution": s}
                      for tt, w, s in BITES[v]] for v in VERSIONS},
        "camera": {"stage_px": [1296, 729], "WIDE": CAM_WIDE, "MEDIUM": CAM_MEDIUM,
                   "states": {v: [{"tau": [a, b], "t": [a + (0 if v == "A" else 37), b + (0 if v == "A" else 37)], "state": s} for a, b, s in CAMERA] for v in VERSIONS},
                   "rule": "same tau-schedule in A and B (equivalent replay); door jamb and clock stay in frame at MEDIUM"},
        "clock_function": {"minute_deg": "6 * tau / 5 (clockwise from 12)", "hour_deg": "0.5 * tau / 5",
                           "python": "rules.clock_angles(t) -> (minute_deg, hour_deg) or None on the slate",
                           "checks": rep["clock_checks"]},
        "layers_back_to_front": LAYERS, "layer_notes": LAYER_NOTES,
        "exposure_beats": beats(),
        "carried_forward": {"A": {"from_t": 14.0, "prop": "apple core (3 bites) in Renzo's pail lid", "seen_by_foreman_from_t": 20.0,
                                  "reading": "unread evidence: his gaze passes over the lid at t 26 without stopping"},
                            "B": {"from_t": 55.0, "prop": "two-bite apple (one his, one hers) in Luciana's hand",
                                  "seen_by_foreman_from_t": 57.0, "reading": "observer sees L with R's token; gaze held on her to the end"}},
        "knowledge": {"A": beliefs("A", 0), "B_before_12:03": beliefs("B", 0), "B_from_12:03": beliefs("B", 16)},
        "replay": {"equivalent": ["camera schedule", "foreman frames and facing on every tau", "R's blocking on tau [0,14.3)",
                                  "clock"],
                   "diverge": ["from 12:00: Luciana absent in B", "12:03: late bell + crossing", "after 12:04: gaze held on L (B) vs pan (A)"]},
        "cues": cues(),
        "asserts": {"module": "films/swarm/renzo-e-luciana/rules.py",
                    "functions": ["assert_frame(k, minute_deg=None, meet_drawn=None)", "assert_one_clock(k, measured_minute_deg, tol=0.5)",
                                  "assert_rule(k)", "assert_meeting(k, meet_drawn)", "assert_layer_order(order)", "check_all()"],
                    "self_test": rep},
        "slate": {"file": "films/swarm/renzo-e-luciana/slate.png", "callable": "rules.slate_frame(u), 0 <= u < 2",
                  "frames_dir": "films/sources/renzo-e-luciana/rule-modeler/slate/", "t": [S0, S1],
                  "strips": {"renzo": [0, 3], "luciana_from": [0, 4], "luciana_to": [3, 7], "corner": [1, 4]},
                  "slide": "u 0.25 -> 1.75 s, eased, +3 minutes (240 px)",
                  "light_column": {"u=0": _common_light(0), "u=2": _common_light(3 * PX_MIN)},
                  "made_of": "HANDMADE with kit.Ink: typed card (IBM Plex Mono, per-key strike weight), three card strips with scissor-cut slots on a light box, typed ruler and paper labels; card-fibre texture; drop shadow from upper left"},
        "frames_file": "films/swarm/renzo-e-luciana/rules-frames.json",
    }
    (HERE / "rules.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    frames = [state(k) for k in range(NFRAMES)]
    (HERE / "rules-frames.json").write_text(json.dumps(frames, separators=(",", ":"), ensure_ascii=False))
    slate_frame(1.999).save(HERE / "slate.png")
    sd = FILMS / "sources" / "renzo-e-luciana" / "rule-modeler" / "slate"
    sd.mkdir(parents=True, exist_ok=True)
    for i in range(int((S1 - S0) * FPS)):
        slate_frame(i / FPS).save(sd / f"slate_{frame_of(S0) + i:04d}.png")
    visibility_png(HERE / "visibility.png")
    return rep


if __name__ == "__main__":
    print(json.dumps(build(), indent=1))
