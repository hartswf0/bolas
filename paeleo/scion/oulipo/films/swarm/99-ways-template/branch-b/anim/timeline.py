"""Pose keys for S0-S8 (rig-animator). Frames are local to each shot, 24 fps. Keys are on twos (every 2 frames) or
longer holds; a key holds until the next key. The last key of every action is {} = the page rest pose exactly.
State fields (see panels.py): clerk.post (source-px root transform delta), clerk.pre (panel-px delta),
clerk.dpose (added joint angles, deg) or clerk.pose (absolute), door.theta (deg; <90 outer face), minute_delta_deg,
visitor_dx (panel px), lamp (deg about the cord top). Balloons drop on ones over 4 frames ending on `land`."""
import math

import numpy as np


def _bp():
    import build_page as bp
    return bp


def _lift(u_up, u_right, u_lean):
    bp = _bp()
    rest = bp.T(bp.P2_RIGHT, -170) @ bp.about(bp.ROOT_, bp.R(-5))          # r1: the page's rest lift (shoulder at the edge)
    L = bp.T(bp.P2_RIGHT * u_right, -170 * u_up) @ bp.about(bp.ROOT_, bp.R(-5 * u_lean))
    return np.round(np.linalg.inv(rest) @ L, 6).tolist()


def _step3(dx, dy, pitch):
    bp = _bp()
    sx, sy, sp = bp.P3_STEP                                                 # r1: standing, before the SERVICE door
    rest = bp.T(sx, sy) @ bp.about(bp.ROOT_, bp.R(sp))
    L = bp.T(sx + dx, sy + dy) @ bp.about(bp.ROOT_, bp.R(sp + pitch))
    return np.round(np.linalg.inv(rest) @ L, 6).tolist()


def _pre(dx, dy):
    return [[1, 0, float(dx)], [0, 1, float(dy)], [0, 0, 1]]


def ease(u):
    return 0.5 - 0.5 * math.cos(math.pi * u)


def K(f, state, label=""):
    return {"f": int(f), "state": state, "label": label}


SHOTS = {}

# ---------------------------------------------------------------- S0: sheet, borders rule in (page-level, see panels.s0_frame)
SHOTS["S0"] = {"panel": "PAGE", "frames": 96, "keys": [K(0, {}, "blank sheet")],
               "note": "32 border strokes (8 panels x top,right,bottom,left), each over 2 poses on twos from f6; "
                       "each panel's art is laid down on the pose its box closes; last stroke closes at f132-? see timing.json",
               "sounds": [{"f": 0, "cue": "paper_handling"}, {"f": 0, "cue": "room_tone", "len_f": 96}]}

# ---------------------------------------------------------------- S1 . P1  E0 reading: head dip (two poses), pencil taps
SHOTS["S1"] = {"panel": "P1", "frames": 120, "keys": [
    K(0, {}, "rest: reading"),
    K(24, {"clerk": {"dpose": {"head": 3.0}}}, "dip 1"),
    K(26, {"clerk": {"dpose": {"head": 6.0}}}, "dip 2 (extreme)"),
    K(36, {"clerk": {"dpose": {"head": 3.0}}}, "return"),
    K(38, {}, "rest"),
    K(60, {"clerk": {"dpose": {"pencil": -5.0}}}, "pencil tap 1"),
    K(62, {}, "rest"),
    K(66, {"clerk": {"dpose": {"pencil": -5.0}}}, "pencil tap 2"),
    K(68, {}, "rest (action end)"),
], "action_end": 68, "sounds": [{"f": 10, "cue": "clock_tick"}, {"f": 34, "cue": "clock_tick"}, {"f": 58, "cue": "clock_tick"},
                                 {"f": 61, "cue": "pencil_tap"}, {"f": 67, "cue": "pencil_tap"}, {"f": 82, "cue": "clock_tick"},
                                 {"f": 106, "cue": "clock_tick"}]}

# ---------------------------------------------------------------- S2 . P2  E1 the rise: anticipation, 4 rise poses, head overlap, slide out
S2 = [K(0, {"clerk": {"post": _lift(0, 0, 0), "pose": {"arm": 0.0, "pencil": 0.0, "head": 0.0}}}, "seated (as photographed)")]
S2 += [K(20, {"clerk": {"post": _lift(-0.07, 0, 0), "pose": {"arm": 0.0, "pencil": 0.0, "head": 2.0}}}, "anticipation dip"),
       K(22, {"clerk": {"post": _lift(-0.10, 0, -0.1), "pose": {"arm": 0.0, "pencil": 0.0, "head": 3.0}}}, "anticipation extreme"),
       K(24, {"clerk": {"post": _lift(0.35, 0, 0.3), "pose": {"arm": -4.0, "pencil": 3.0, "head": 4.0}}}, "rise 1 (head lags)"),
       K(26, {"clerk": {"post": _lift(0.75, 0.02, 0.6), "pose": {"arm": -9.0, "pencil": 7.0, "head": 3.0}}}, "rise 2"),
       K(28, {"clerk": {"post": _lift(1.07, 0.04, 0.9), "pose": {"arm": -14.0, "pencil": 11.0, "head": 0.5}}}, "rise 3 (overshoot)"),
       K(30, {"clerk": {"post": _lift(1.0, 0.05, 1.0), "pose": {"arm": -17.0, "pencil": 13.0, "head": -1.5}}}, "rise 4 (head overlaps past)")]
for i, (ur, uu) in enumerate([(0.18, 0.93), (0.30, 1.0), (0.44, 0.93), (0.56, 1.0), (0.70, 0.93), (0.81, 1.0), (0.93, 0.95)]):
    u = (i + 1) / 8
    head = [-1.0, 1.5, 4.5, 2.0, 4.5, 2.5, 3.5][i]
    S2.append(K(40 + 2 * i, {"clerk": {"post": _lift(uu, ur, 1.0), "pose": {
        "arm": -17.0 + (-34.0 + 17.0) * u,
        "pencil": 13.0 + (24.0 - 13.0) * u, "head": head}}}, f"slide {i + 1}" + (" (step down)" if uu < 1 else "")))
S2.append(K(54, {}, "rest: half out of the panel, empty chair (action end)"))
SHOTS["S2"] = {"panel": "P2", "frames": 120, "keys": S2, "action_end": 54,
               "sounds": [{"f": 22, "cue": "chair_scrape"}, {"f": 40, "cue": "footstep"}, {"f": 44, "cue": "footstep"},
                          {"f": 48, "cue": "footstep"}, {"f": 52, "cue": "footstep"}]}

# ---------------------------------------------------------------- S3 . P3  Gilliam stepping walk: translate on twos, bob +-6 page px, head bob on hinge
S3 = []
N = 20
BOB = 14.0    # source px; x0.423 = 5.9 page px
for i in range(N):
    ph = i % 4                       # 0 contact (down), 1 pass, 2 up, 3 pass
    dx = -1500.0 * (1 - (i + 1) / (N + 1))
    dy = {0: BOB, 1: 0.0, 2: -BOB, 3: 0.0}[ph]
    pitch = {0: 1.5, 1: 0.5, 2: -0.5, 3: 0.5}[ph]
    head = {0: -2.0, 1: 0.0, 2: 2.0, 3: 0.0}[(ph + 3) % 4]      # head lags the torso one pose
    arm = {0: 3.0, 1: 0.0, 2: -3.0, 3: 0.0}[ph]
    S3.append(K(8 + 2 * i, {"clerk": {"post": _step3(dx, dy, pitch), "dpose": {"head": head, "arm": arm}}},
                f"step {i // 4 + 1} " + ["contact", "pass", "up", "pass"][ph]))
S3.insert(0, K(0, {"clerk": {"hidden": True}}, "empty office (he has not entered)"))
S3.append(K(48, {}, "rest: mid-step past the SERVICE door (action end)"))
SHOTS["S3"] = {"panel": "P3", "frames": 120, "keys": S3, "action_end": 48,
               "sounds": [{"f": 8 + 8 * s, "cue": "footstep"} for s in range(5)]}

# ---------------------------------------------------------------- S4 . P4  E2 halted mid-step; visitor shifts; balloon; head swings in 3 steps
H0 = 12.0
S4 = [K(0, {"clerk": {"hidden": True}, "visitor_dx": -24.0, "balloons": {}}, "window (nobody drawn behind the glass: the asker is off-panel)")]
for i, (dx, dy) in enumerate([(170, 6), (130, 0), (90, -6), (55, 0), (25, 6)]):
    S4.append(K(4 + 2 * i, {"clerk": {"pre": _pre(dx, dy), "dpose": {"head": H0 + (1.5 if i % 2 else 0.0)}}, "visitor_dx": -24.0},
                f"steps in {i + 1}"))
S4 += [K(14, {"clerk": {"pre": _pre(-7, 2), "dpose": {"head": H0 + 4.0}}, "visitor_dx": -24.0}, "HALT (bell): torso overshoots, head overlaps"),
       K(16, {"clerk": {"pre": _pre(0, 0), "dpose": {"head": H0 + 1.5}}, "visitor_dx": -24.0}, "settle"),
       K(18, {"clerk": {"dpose": {"head": H0}}, "visitor_dx": -24.0}, "hold, head still away"),
       K(22, {"clerk": {"dpose": {"head": H0}}, "visitor_dx": -15.0}, "hold 1 (the voice outside)"),
       K(24, {"clerk": {"dpose": {"head": H0}}, "visitor_dx": -6.0}, "hold 2"),
       K(26, {"clerk": {"dpose": {"head": H0}}, "visitor_dx": 0.0}, "hold 3"),
       K(56, {"clerk": {"dpose": {"head": 8.0}}}, "head swing 1"),
       K(58, {"clerk": {"dpose": {"head": 3.5}}}, "head swing 2"),
       K(60, {}, "head swing 3 = rest, facing the window (action end)")]
SHOTS["S4"] = {"panel": "P4", "frames": 120, "keys": S4, "action_end": 60, "balloons": [{"id": "b_what_time", "land": 40}],
               "sounds": [{"f": 4, "cue": "footstep"}, {"f": 10, "cue": "footstep"}, {"f": 14, "cue": "counter_bell"},
                          {"f": 40, "cue": "paper_tap"}]}

# ---------------------------------------------------------------- S5 . P5  E3 eyes up to the clock; minute hand ticks onto the 2; balloon
S5 = [K(0, {"clerk": {"dpose": {"head": 6.0}}, "minute_delta_deg": -6.0}, "head down, clock at 4:09"),
      K(18, {"clerk": {"dpose": {"head": 3.0}}, "minute_delta_deg": -6.0}, "head up 1"),
      K(20, {"minute_delta_deg": -6.0}, "head up 2 = rest (looks up at the clock)"),
      K(36, {"minute_delta_deg": 1.2}, "minute hand jumps onto the 2 (overshoot)"),
      K(38, {}, "settles: 4:10 = rest (action end)")]
SHOTS["S5"] = {"panel": "P5", "frames": 120, "keys": S5, "action_end": 38, "balloons": [{"id": "b_ten_past", "land": 56}],
               "sounds": [{"f": 12, "cue": "clock_tick"}, {"f": 36, "cue": "clock_tick_close"}, {"f": 56, "cue": "paper_tap"},
                          {"f": 84, "cue": "clock_tick"}]}

# ---------------------------------------------------------------- S6 . P6  E3b "Thanks!" and the lamp sways from the door draught
S6 = [K(0, {}, "empty window"), K(26, {"lamp": 2.2}, "lamp sway 1"), K(30, {"lamp": -1.4}, "lamp sway 2"),
      K(34, {"lamp": 0.5}, "lamp settles"), K(38, {}, "rest (action end)")]
SHOTS["S6"] = {"panel": "P6", "frames": 120, "keys": S6, "action_end": 38, "balloons": [{"id": "b_thanks", "land": 16}],
               "sounds": [{"f": 16, "cue": "paper_tap"}, {"f": 20, "cue": "steps_receding", "len_f": 70},
                          {"f": 24, "cue": "platform_distant", "len_f": 96}]}

# ---------------------------------------------------------------- S7 . P7  E4 arrives; door swings on its fixed jamb in 7 foreshortened poses
S7 = [K(0, {"clerk": {"hidden": True}, "door": {"theta": 0.0}}, "cupboard shut")]
for i, (dx, dy) in enumerate([(300, 7), (240, 0), (180, -7), (125, 0), (75, 7), (35, 0), (10, -3)]):
    S7.append(K(6 + 2 * i, {"clerk": {"pre": _pre(dx, dy), "dpose": {"head": [1.5, 0, -1.5, 0, 1.5, 0, -0.5][i]}},
                            "door": {"theta": 0.0}}, f"arrives, step {i + 1}"))
S7.append(K(20, {"door": {"theta": 0.0}}, "at the cupboard (clerk at rest), door shut"))
for f, th, lab in [(40, 4.0, "latch gives"), (42, 30.0, "swing 1 scaleX .87"), (44, 55.0, "swing 2 scaleX .57"),
                   (46, 75.0, "swing 3 scaleX .26"), (48, 88.0, "swing 4 edge-on .03"), (50, 100.0, "swing 5 inner face .17, key shows"),
                   (52, 113.0, "swing 6 overshoot .39")]:
    S7.append(K(f, {"door": {"theta": th}}, lab))
S7.append(K(54, {}, "door at rest (swing .34), key on its hook (action end)"))
SHOTS["S7"] = {"panel": "P7", "frames": 120, "keys": S7, "action_end": 54,
               "sounds": [{"f": 6, "cue": "footstep"}, {"f": 14, "cue": "footstep"}, {"f": 40, "cue": "door_latch"},
                          {"f": 42, "cue": "door_creak", "len_f": 12}]}

# ---------------------------------------------------------------- S8 . P8  E5 defining beat
A0 = {"arm": -34.0, "pencil": 24.0}
def _bpose():
    return _bp().POSE_CHIN
_H8 = _bp().H8          # r1: rest head angle, tipped up and turned away from the key (he faces right, the key is left)
S8 = [K(0, {"clerk": {"pose": dict(A0, head=_H8 + 13.0)}}, "head down, arm low")]
S8 += [K(10, {"clerk": {"pose": dict(A0, head=_H8 + 8.5)}}, "head tilt 1"),
       K(14, {"clerk": {"pose": dict(A0, head=_H8 + 4.0)}}, "head tilt 2"),
       K(18, {"clerk": {"pose": dict(A0, head=_H8)}}, "head tilt 3 (up and away from the key)"),
       K(26, {"clerk": {"pose": {"arm": -36.0, "pencil": 19.0, "head": _H8}}}, "arm anticipation (dips)")]
_CH = None
for i, u in enumerate([0.30, 0.68, 0.93, 1.03]):
    S8.append(K(28 + 2 * i, {"clerk": {"pose_u": u}}, f"arm rise {i + 1}" + (" (overshoot)" if u > 1 else "")))
S8 += [K(36, {}, "pencil at the chin = rest; HOLD"),
       K(58, {"clerk": {"dpose": {"pencil": 5.0, "arm": 1.0}}}, "scratch 1"), K(60, {}, "rest"),
       K(62, {"clerk": {"dpose": {"pencil": 5.0, "arm": 1.0}}}, "scratch 2"), K(64, {}, "rest (action end); key never moves")]
SHOTS["S8"] = {"panel": "P8", "frames": 168, "keys": S8, "action_end": 64, "balloons": [{"id": "b_forgot", "land": 84}],
               "holds": {"read_hold": [84, 120], "final_hold_2s": [120, 168]},
               "sounds": [{"f": 84, "cue": "paper_tap"}, {"f": 140, "cue": "clock_tick"}]}


def resolve():
    """Turn pose_u keys (fraction of the arm rise from A0 to the page's chin pose) into absolute poses."""
    ch = _bpose()
    for k in SHOTS["S8"]["keys"]:
        c = k["state"].get("clerk", {})
        if "pose_u" in c:
            u = c.pop("pose_u")
            c["pose"] = {"arm": A0["arm"] + (ch["arm"] - A0["arm"]) * u, "pencil": A0["pencil"] + (ch["pencil"] - A0["pencil"]) * u,
                         "head": ch["head"]}


resolve()
