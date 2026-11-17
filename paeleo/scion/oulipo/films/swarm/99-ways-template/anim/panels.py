"""99 Ways to Tell a Story - Template, b1: frame-callable panel animation (rig-animator, U3).

SCION #32 Forward Kinematics + #1 Gilliam cutout, on SCION #29 GrabCut pieces.

The page builder (page/build_page.py, the page-cartoonist's) already lays every piece through a joint graph
(clerk: torso -> collar -> head; torso -> elbow -> forearm -> grip -> pencil; set -> jamb -> door -> hook -> key -> tag;
clock -> arbor -> hands). This module does NOT redraw the panels its own way: it calls the page builder's own panel
functions and, for each frame, overrides only the joint parameters (head/arm/pencil angles, the clerk's root
transform, the door's swing, the minute hand's arbor angle, the visitor's place behind the glass, the lamp's cord
angle, the balloons' drop offset). With every override at its rest value the panel is the page panel, bit for bit,
so every action that ends on its rest key ends on the page art.

    import panels
    rgb = panels.frame("S8", 40)          # float32 HxWx3 (0..255), the panel at page scale (panel px)
    panels.SHOTS["S8"]["panel"], panels.SHOTS["S8"]["frames"]
    page = panels.s0_frame(30)            # S0: the whole page with borders ruling in (2550x3300x3)

Poses are keyed on twos (12 poses/s at 24 fps); balloon drops are the one declared exception (impact objects on
ones, 4 frames with one bounce). Keys live in timing.json (written by build_anim.py from TIMELINE below).
Run python3 -I panels.py --check to verify rest identity.
"""
import copy
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
PAGE_DIR = HERE.parent / "page"
sys.path.insert(0, str(PAGE_DIR))
import build_page as bp  # noqa: E402  (the page-cartoonist's builder; importing it does not build the page)

FPS = 24
_orig = {"lay_clerk": bp.lay_clerk, "lay_door_key": bp.lay_door_key, "balloon": bp.balloon, "view_plate": bp.view_plate}
STATE = {}          # overrides for the panel being rendered
MEAS = []           # FK measurements of the last render


def _deg_lerp(a, b, u):
    return a + (b - a) * u


# ------------------------------------------------------------------ joint overrides (wrappers on the page builder)
def lay_clerk(P, Mw, pose, order=("clerk.torso", "clerk.head", "clerk.forearm", "clerk.pencil"), rec=None):
    st = STATE.get("clerk")
    if st is None:
        Ms = _orig["lay_clerk"](P, Mw, pose, order=order, rec=rec)
    else:
        if st.get("hidden"):
            return bp.clerk_mats(Mw, pose)
        Mw2 = np.asarray(st.get("pre", np.eye(3))) @ Mw @ np.asarray(st.get("post", np.eye(3)))
        if "pose" in st:
            pose2 = dict(st["pose"])
        else:
            pose2 = {k: pose.get(k, 0.0) + st.get("dpose", {}).get(k, 0.0) for k in ("arm", "pencil", "head")}
        Ms = _orig["lay_clerk"](P, Mw2, pose2, order=order, rec=None)
    # FK measurement: each child's pivot as carried by the parent vs by the child itself (page px)
    m = {"panel": P.key}
    for child, par, piv in (("clerk.head", "clerk.torso", bp.COLLAR), ("clerk.forearm", "clerk.torso", bp.ELBOW),
                            ("clerk.pencil", "clerk.forearm", bp.GRIP)):
        a, b = bp.apply(Ms[par], piv), bp.apply(Ms[child], piv)
        m[child + "_pivot_drift_px"] = float(np.hypot(*(a - b)))
    m["collar_px"] = list(map(float, bp.apply(Ms["clerk.head"], bp.COLLAR)))
    m["pencil_tip_px"] = list(map(float, bp.apply(Ms["clerk.pencil"], bp.TIP)))
    m["chin_px"] = list(map(float, bp.apply(Ms["clerk.head"], bp.CHIN)))
    m["tip_to_chin_px"] = float(np.hypot(*(np.subtract(m["pencil_tip_px"], m["chin_px"]))))
    MEAS.append(m)
    return Ms


def _door_outer(P, k, x0, y0, theta):
    """Closed side of the swing: the door's OUTER face (the photographed cupboard door, unmirrored) about the same
    fixed jamb, foreshortened by cos(theta), free edge coming toward us (grows with sin(theta)), darkening with angle.
    The hook, tag and key hang on the inner face, so they are not seen."""
    Wm = bp.W2P(k, x0, y0)
    dh, dw = bp.DOOR.shape
    jx, jy = bp.DOOR_BOX[0], bp.DOOR_BOX[1]
    jt, jb = bp.apply(Wm, (jx, jy)), bp.apply(Wm, (jx, jy + dh))
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    ow = max(dw * k * c, 2.0)
    grow = dh * k * 0.0532 * s
    src = np.float32([[0, 0], [dw, 0], [dw, dh], [0, dh]])
    dst = np.float32([jt, [jt[0] + ow, jt[1] - grow], [jb[0] + ow, jb[1] + grow], jb])
    Md = cv2.getPerspectiveTransform(src, dst).astype(np.float64)
    shade = 1.0 - 0.30 * s
    P.piece("cupboard.door", bp.DOOR.copy(), np.full(bp.DOOR.shape, 255, np.uint8), Md, margin=8, shade=shade,
            meta={"piece": "cupboard.door", "face": "outer", "theta": theta})
    MEAS.append({"panel": P.key, "door_theta_deg": theta, "face": "outer", "jamb_top_px": list(map(float, jt)),
                 "jamb_bottom_px": list(map(float, jb)), "scaleX": c, "shade": shade})


def lay_door_key(P, k, x0, y0, swing=0.34, rec=None):
    st = STATE.get("door")
    theta = None if st is None else st.get("theta")
    if theta is not None and theta < 90.0:
        return _door_outer(P, k, x0, y0, theta)
    s = swing if theta is None else -math.cos(math.radians(theta))
    r = {}
    _orig["lay_door_key"](P, k, x0, y0, swing=s, rec=r)
    Wm = bp.W2P(k, x0, y0)
    jt = bp.apply(Wm, (bp.DOOR_BOX[0], bp.DOOR_BOX[1]))
    jb = bp.apply(Wm, (bp.DOOR_BOX[0], bp.DOOR_BOX[1] + bp.DOOR.shape[0]))
    kr = r.get(P.key + ".key", {})
    MEAS.append({"panel": P.key, "door_theta_deg": theta if theta is not None else math.degrees(math.acos(-swing)),
                 "face": "inner", "swing_scaleX": s, "jamb_top_px": list(map(float, jt)), "jamb_bottom_px": list(map(float, jb)),
                 "hook_px": kr.get("hook_px"), "ring_px": kr.get("ring_px"), "key_offset_px": kr.get("offset")})
    if rec is not None:
        rec.update(r)


def balloon(P, name, lines, cap, at, tip, seed, tail_w=0.30, bend=0.10):
    st = STATE.get("balloons", {}).get(name)
    if st is None:
        return _orig["balloon"](P, name, lines, cap, at, tip, seed, tail_w=tail_w, bend=bend)
    if st == "hidden":
        return {"id": name, "hidden": True}
    dx, dy = st
    return _orig["balloon"](P, name, lines, cap, (at[0] + dx, at[1] + dy), (tip[0] + dx, tip[1] + dy), seed,
                            tail_w=tail_w, bend=bend)


# ------------------------------------------------------------------ lamp on its cord (P6): a cut piece of the plate
P6_VIEW_K = 0.577
LAMP = {}


def _lamp_piece(g):
    """GrabCut (SCION #29) of the hanging lamp (shade + fitting) from the P6 plate, plus a feathered band along the
    twisted cord; the hole is filled by cv2.inpaint so the trailing sliver of a swing shows plate, not paper."""
    if LAMP:
        return LAMP
    g8 = np.clip(g[..., 0], 0, 255).astype(np.uint8)
    h, w = g8.shape
    img = cv2.cvtColor(g8, cv2.COLOR_GRAY2BGR)
    mask = np.zeros((h, w), np.uint8)
    rect = (200, 318, 200, 180)          # shade + fitting, panel px (found by looking at P6's plate)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        fg = np.where(lab == big, 255, 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    # the cord: locate it row by row as the brightest narrow ridge near x~297 (it is a light twisted flex)
    cord = np.zeros_like(fg)
    xs = []
    for y in range(0, 340, 4):
        row = cv2.GaussianBlur(g8[y:y + 1, 270:330].astype(np.float32), (1, 0), 2) if False else g8[y, 270:330].astype(np.float32)
        xs.append((y, 270 + int(np.argmax(np.convolve(row, np.ones(5) / 5, "same")))))
    ys_, xs_ = np.array([p[0] for p in xs]), np.array([p[1] for p in xs])
    fit = np.polyfit(ys_, xs_, 1)
    top = (float(np.polyval(fit, 0)), 0.0)
    bot = (float(np.polyval(fit, 345)), 345.0)
    cv2.line(cord, (int(top[0]), -5), (int(bot[0]), int(bot[1])), 255, 13, cv2.LINE_AA)
    alpha = np.maximum(fg, cord)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.2)
    hole = cv2.dilate((alpha > 8).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    clean = cv2.inpaint(g8, hole, 9, cv2.INPAINT_TELEA).astype(np.float32)
    LAMP.update(alpha=alpha.astype(np.float32) / 255, clean=clean, pivot=top, fit=fit.tolist(), fg_area=int((fg > 0).sum()),
                components=int(cv2.connectedComponents((alpha > 127).astype(np.uint8))[0] - 1))
    return LAMP


def view_plate(img, k, x0, y0, w, h):
    g = _orig["view_plate"](img, k, x0, y0, w, h)
    ang = STATE.get("lamp")
    if ang is None or abs(ang) < 1e-9 or abs(k - P6_VIEW_K) > 1e-6:
        return g
    L = _lamp_piece(g)
    M = cv2.getRotationMatrix2D(L["pivot"], ang, 1.0)
    src = g[..., 0].astype(np.float32)
    lg = cv2.warpAffine(src, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    la = cv2.warpAffine(L["alpha"], M, (w, h), flags=cv2.INTER_LINEAR)
    out = L["clean"] * (1 - la) + lg * la
    MEAS.append({"panel": "P6", "lamp_deg": ang, "lamp_pivot_px": list(L["pivot"])})
    return np.repeat(out[..., None], 3, 2)


bp.lay_clerk, bp.lay_door_key, bp.balloon, bp.view_plate = lay_clerk, lay_door_key, balloon, view_plate

# small parameter overrides that the page builder reads from its manifest/piece tables at call time
_MIN_SRC = bp.man["pieces"]["clock.minute"]["source_angle_deg"]
_VIS_HEAD = tuple(bp.PC["visitor"]["piv"]["head"])
PANEL_FN = {"P1": bp.P1, "P2": bp.P2, "P3": bp.P3, "P4": bp.P4, "P5": bp.P5, "P6": bp.P6, "P7": bp.P7, "P8": bp.P8}
_CACHE = {}


def render_panel(key, state=None):
    """Render panel `key` with joint overrides `state` (None = rest). Returns float32 HxWx3, page scale."""
    global STATE
    state = state or {}
    ck = (key, json.dumps(state, sort_keys=True, default=lambda o: np.asarray(o).round(5).tolist()))
    if ck in _CACHE:
        return _CACHE[ck][0]
    STATE = state
    MEAS.clear()
    bp.man["pieces"]["clock.minute"]["source_angle_deg"] = _MIN_SRC - state.get("minute_delta_deg", 0.0)
    vs = state.get("visitor_dx", 0.0)
    bp.PC["visitor"]["piv"]["head"] = (_VIS_HEAD[0] - vs / 1.05, _VIS_HEAD[1])
    try:
        P = PANEL_FN[key]()
    finally:
        STATE = {}
        bp.man["pieces"]["clock.minute"]["source_angle_deg"] = _MIN_SRC
        bp.PC["visitor"]["piv"]["head"] = _VIS_HEAD
    out = np.clip(P.c, 0, 255).astype(np.float32)
    x0, y0, x1, y1 = bp.PANELS[key]
    # the hand-ruled border is part of the panel's rest art (page/rest/<P>/..._border.png)
    out = _with_border(key, out)
    _CACHE[ck] = (out, copy.deepcopy(MEAS))
    if len(_CACHE) > 400:
        _CACHE.pop(next(iter(_CACHE)))
    return out


_BORDER = {}


def _border_alpha(key):
    if key not in _BORDER:
        from PIL import Image
        d = PAGE_DIR / "rest" / key
        f = sorted(d.glob("*_border.png"))[-1]
        _BORDER[key] = np.asarray(Image.open(f)).astype(np.float32)[..., 3:4] / 255
    return _BORDER[key]


def _with_border(key, c):
    a = _border_alpha(key)
    return c * (1 - a) + bp.INK[None, None] * a


def measurements(key, state=None):
    render_panel(key, state)
    ck = (key, json.dumps(state or {}, sort_keys=True, default=lambda o: np.asarray(o).round(5).tolist()))
    return _CACHE[ck][1]


# ------------------------------------------------------------------ the rig's transforms used by the timeline
def T(x, y):
    return bp.T(x, y)


def lift_P2(u_up, u_right, u_lean):
    """P2 rise: the page-builder's rest lift is T(980,-170) @ about(root, R(-5)) in source px; post = inv(rest) @ L(u)."""
    rest = bp.T(bp.P2_RIGHT, -170) @ bp.about(bp.ROOT_, bp.R(-5))
    L = bp.T(bp.P2_RIGHT * u_right, -170 * u_up) @ bp.about(bp.ROOT_, bp.R(-5 * u_lean))
    return (np.linalg.inv(rest) @ L).tolist()


def step_P3(dx_src, dy_src, pitch):
    sx, sy, sp = bp.P3_STEP
    rest = bp.T(sx, sy) @ bp.about(bp.ROOT_, bp.R(sp))
    L = bp.T(sx + dx_src, sy + dy_src) @ bp.about(bp.ROOT_, bp.R(sp + pitch))
    return (np.linalg.inv(rest) @ L).tolist()


def pre_page(dx, dy, rot=0.0, about_px=None):
    """A panel-space (page px) transform applied before the clerk's own placement: used for the stepping walk bob."""
    M = bp.T(dx, dy)
    if rot and about_px is not None:
        M = M @ bp.about(about_px, bp.R(rot))
    return M.tolist()


POSE_SOURCE, POSE_ARRIVE, POSE_CHIN = dict(bp.POSE_SOURCE), dict(bp.POSE_ARRIVE), dict(bp.POSE_CHIN)


# ------------------------------------------------------------------ S0: borders rule themselves in
_S0 = {}


def _s0_setup():
    if _S0:
        return _S0
    from PIL import Image
    page = np.asarray(Image.open(bp.PAGE_OUT).convert("RGB")).astype(np.float32)
    ground = bp.sheet().astype(np.float32)
    bm = bp.border_mask((bp.PAGE_H, bp.PAGE_W), [bp.PANELS[k] for k in bp.PANELS], 9, 900)
    strokes = []
    for key in ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]:
        x0, y0, x1, y1 = bp.PANELS[key]
        pad = 16
        # one pen stroke per side, in the order a cartoonist rules a box: top, right, bottom, left
        strokes += [(key, "top", (x0 - pad, y0 - pad, x1 + pad, y0 + pad), "x"),
                    (key, "right", (x1 - pad, y0 - pad, x1 + pad, y1 + pad), "y"),
                    (key, "bottom", (x0 - pad, y1 - pad, x1 + pad, y1 + pad), "-x"),
                    (key, "left", (x0 - pad, y0 - pad, x0 + pad, y1 + pad), "-y")]
    _S0.update(page=page, ground=ground, bm=bm.astype(np.float32) / 255, strokes=strokes)
    return _S0


S0_START, S0_POSE_FRAMES = 6, 2         # first stroke at frame 6, one stroke-half per pose (on twos)


def s0_frame(f):
    """Whole page (page px) at S0 frame f: blank 1934 sheet; the borders are ruled straight-ahead, each side drawn
    over two poses (half, whole; the next stroke starts as one finishes); when a panel's box closes, its photo-paper art is laid down in one substitution."""
    S = _s0_setup()
    n = len(S["strokes"])
    pose = max(0, (f - S0_START) // S0_POSE_FRAMES + 1) if f >= S0_START else 0
    reveal = np.zeros(S["bm"].shape, np.float32)
    canvas = S["ground"].copy()
    done_panels = set()
    for i, (key, side, (x0, y0, x1, y1), ax) in enumerate(S["strokes"]):
        prog = min(1.0, max(0.0, (pose - i) / 2.0))   # stroke i: half at pose i+1, whole at pose i+2
        if prog <= 0:
            break
        x0, y0 = max(0, x0), max(0, y0)
        if ax in ("x", "-x"):
            L = x1 - x0
            a, b = (x0, x0 + int(L * prog)) if ax == "x" else (x1 - int(L * prog), x1)
            reveal[y0:y1, a:b] = 1
        else:
            L = y1 - y0
            a, b = (y0, y0 + int(L * prog)) if ax == "y" else (y1 - int(L * prog), y1)
            reveal[a:b, x0:x1] = 1
        if side == "left" and prog >= 1:
            done_panels.add(key)
    for key in done_panels:
        x0, y0, x1, y1 = bp.PANELS[key]
        canvas[y0:y1, x0:x1] = S["page"][y0:y1, x0:x1]
    if len(done_panels) == 8:
        return S["page"].copy()
    a = (S["bm"] * reveal)[..., None]
    return canvas * (1 - a) + bp.INK[None, None] * a


S0_END_POSE = 32 + 1                       # pose index at which the last stroke is complete
S0_DONE_FRAME = S0_START + (S0_END_POSE - 1) * S0_POSE_FRAMES


# ------------------------------------------------------------------ timeline (keys on twos) -> per-frame state
def _load_timeline():
    from timeline import SHOTS  # noqa
    return SHOTS


sys.path.insert(0, str(HERE))
SHOTS = _load_timeline()


def state_at(shot, f):
    """The pose key in force at frame f (keys are held until the next key: on twos, or longer holds)."""
    keys = SHOTS[shot]["keys"]
    cur = keys[0]
    for k in keys:
        if k["f"] <= f:
            cur = k
        else:
            break
    st = copy.deepcopy(cur["state"])
    # balloons: impact objects on ones (4 frames, one bounce), then held on the page position
    for b in SHOTS[shot].get("balloons", []):
        land = b["land"]
        drop = {land - 3: (0, -150), land - 2: (0, -55), land - 1: (0, 9), land: None}
        if f < land - 3:
            st.setdefault("balloons", {})[b["id"]] = "hidden"
        elif f < land:
            st.setdefault("balloons", {})[b["id"]] = drop[f]
    return st


def frame(shot, f):
    sh = SHOTS[shot]
    if shot == "S0":
        return s0_frame(f)
    return render_panel(sh["panel"], state_at(shot, f))


def rest(key):
    return render_panel(key, None)


if __name__ == "__main__" and "--check" in sys.argv:
    from PIL import Image
    pg = np.asarray(Image.open(bp.PAGE_OUT).convert("RGB")).astype(np.float32)
    for k in bp.PANELS:
        x0, y0, x1, y1 = bp.PANELS[k]
        r = np.clip(np.round(rest(k)), 0, 255)
        print(k, "rest vs page mean abs", round(float(np.abs(r - pg[y0:y1, x0:x1]).mean()), 3))
