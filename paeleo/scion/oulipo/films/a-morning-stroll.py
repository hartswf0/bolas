"""A Morning Stroll (after Grant Orchard, 2011) - SCION assembly, Direction 1 "Rizzuto Stoop" (plan-r1 / score-r1).

A real 1870s rooster (LoC stereograph), GrabCut-cut into 10 pieces and driven by forward kinematics, climbs three
real stoops (Rizzuto 1959, Highsmith south Philadelphia, a Commons sliding-glass entrance) and knocks twice with its
beak: tok . tok, 8 frames apart. The door answers by hand (1959), on a chain (2009) and by listening (2059). Then the
1959 score is replayed as Reiniger black-card silhouette theatre (diagnostic D), with identical event frames.

    python3 films/a-morning-stroll.py                 render assets/films/a-morning-stroll.mp4 (68 s)
    python3 films/a-morning-stroll.py --stills 9 25   PNG stills (films/stills/a-morning-stroll/)
    python3 films/a-morning-stroll.py --report        assertions + ledger + compare sheets, no render

Layer DAG per shot follows films/swarm/a-morning-stroll/plates.json (plate -> hall/interior -> leaf -> cast shadows
-> puppet -> railing holdouts -> jamb/sill holdouts -> vignette -> kit grain). Only the unify grades recorded by
story-plates are applied (plates/<era>/*graded*). No look filters.
"""
import json
import math
import os
import sys
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

FILMS = Path(__file__).resolve().parent
OUL = FILMS.parent
SRC = FILMS / "sources" / "a-morning-stroll"
PL = SRC / "plates"
SW = FILMS / "swarm" / "a-morning-stroll"
PUP = SRC / "puppet"
sys.path.insert(0, str(FILMS))
sys.path.insert(0, str(PUP))
import kit  # noqa: E402
import puppet as P  # noqa: E402
import knockproof as KP  # noqa: E402  (the approved V1-B knock, imported as a module; its main() is not run)


# ---- repair r2: a strike that reads with the sound off (#32). The whole neck and head drive forward ~25-30 canvas px:
# 2-frame anticipation (cock: head back), strike on ones with the body pitching into it, a visible recoil.
P.POSES["strike"] = {"neck": -30, "head": -14}
P.POSES["cock"] = {"neck": 12, "head": 6}
P.POSES["recoil"] = {"neck": 9, "head": 4}
LEAN = {"strike": -14.0, "recoil": 4.0, "cock": 5.0}


def _rebuild_kp():
    tr = KP.build_track()
    for f, p in enumerate(tr):
        for e in (KP.E3, KP.E4):
            d = f - e
            extra = {-3: 3.0, -2: 3.0, -1: -3.0, 0: -6.0, 1: -2.0}.get(d)
            if extra is not None and f < 92:
                p["rot"] += extra                              # body pitches into the blow beyond the module's lean
    KP.TRACK = tr


_rebuild_kp()

# ---- repair r2: colour rooster for 2009 (LoC highsm.61221, Carol M. Highsmith 2019; GrabCut, 10 pieces)
P.RIG["rooster_c"] = json.load(open(PUP / "pieces/rooster_c/rig_c.json"))


def colour_rig():
    r = P.Rig("rooster_c", era=2009)
    for n in r.J:                                              # the photograph's own daylight colour: no tone remap
        r.pieces[n] = np.asarray(Image.open(PUP / f"pieces/rooster_c/piece_{n}.png"), np.float32)
    return r


FLECK_RNG = np.random.RandomState(11)
FLECKS = [(FLECK_RNG.uniform(-1, 1), FLECK_RNG.uniform(-1.6, 0.2), FLECK_RNG.uniform(0.6, 1.4)) for _ in range(9)]


def contact_fx(out, pts, f, k, kind, nick_until=None):
    """HANDMADE contact marks drawn where the beak tip met the door (pts = {E3L: canvas xy, E4L: canvas xy};
    k = canvas px per stage px): on each contact frame chips of paint thrown off over the next 5 frames under
    gravity (wood, painted door) or a glint (glass); a hard dark nick with a lit lip stays where the beak hit
    until the door moves."""
    out = np.ascontiguousarray(out, np.float32)
    for e in (E3L, E4L):
        bx, by = float(pts[e][0]), float(pts[e][1])
        d = f - e
        if kind != "glass" and f >= e and (nick_until is None or f < nick_until):
            cv2.ellipse(out, (int(bx), int(by)), (max(2, int(2.4 * k)), max(1, int(1.5 * k))), 20, 0, 360, (12, 12, 12), -1, cv2.LINE_AA)
            cv2.ellipse(out, (int(bx), int(by - 1.4 * k)), (max(2, int(2.4 * k)), max(1, int(1.0 * k))), 20, 180, 360, (245, 245, 245), 1, cv2.LINE_AA)
        if not 0 <= d <= 5:
            continue
        if kind == "glass":
            if d <= 2:
                L = (16 - 5 * d) * max(k, 0.8)
                for ang in (0, 45, 90, 135):
                    a = math.radians(ang)
                    p0 = (int(bx - L * math.cos(a)), int(by - L * math.sin(a)))
                    p1 = (int(bx + L * math.cos(a)), int(by + L * math.sin(a)))
                    cv2.line(out, p0, p1, (235, 240, 236), 2 if d == 0 else 1, cv2.LINE_AA)
                cv2.circle(out, (int(bx), int(by)), int(2 + 2 * (2 - d)), (250, 252, 250), -1, cv2.LINE_AA)
            continue
        col = (22, 22, 22) if kind == "wood" else (150, 168, 186)
        for i, (vx, vy, sz) in enumerate(FLECKS):
            tt = d + 0.6
            x = bx + (vx * 4.0 + 1.0) * tt * k
            y = by + (vy * 4.0 * tt + 1.1 * tt * tt) * k
            r = max(1, int(round(1.3 * sz * k)))
            c = col if i % 3 else (238, 238, 238)
            a0 = 2.1 * i + 0.9 * tt * (vx + 0.3)
            tri = np.int32([[x + r * 1.6 * math.cos(a0 + q), y + r * 1.6 * math.sin(a0 + q)] for q in (0.0, 2.3, 4.1)])
            cv2.fillPoly(out, [tri], c, cv2.LINE_AA)
    return out

W, H, FPS = 960, 540, 24
SECONDS = 68.0
INK = (20, 20, 20)                 # #141414 card ground
OFFS = {"V1": 3.0, "V2": 19.0, "V3": 35.0, "D": 51.0}
E3L, E4L = 144, 152                # local frames (6.00 s, 6.333 s): 8 frames apart
E6END = 240                        # local 10.0 s
BEAT = json.load(open(SW / "beatmap.json"))


def img(p, mode=None):
    im = Image.open(p)
    if mode:
        im = im.convert(mode)
    return np.asarray(im).astype(np.float32)


def T(x, y):
    return P.T(x, y)


def cam_rect(r0, r1, u):
    """stage -> canvas 3x3 for a crop rect interpolated start -> end (the 1.5 % push)."""
    x0, y0, x1, y1 = [a + (b - a) * u for a, b in zip(r0, r1)]
    k = W / (x1 - x0)
    return np.array([[k, 0, -x0 * k], [0, k, -y0 * k], [0, 0, 1.0]])


def warp(a, M, interp=cv2.INTER_LINEAR, border=cv2.BORDER_CONSTANT):
    return cv2.warpAffine(a, np.asarray(M, np.float64)[:2], (W, H), flags=interp, borderMode=border)


def rgb3(g):
    return np.repeat(g[..., None], 3, 2) if g.ndim == 2 else g


def over(base, rgb, a):
    return rgb * a[..., None] + base * (1 - a[..., None])


def vis_px(a):
    return int((a > 0.5).sum())


def height_frac(a):
    ys = np.nonzero((a > 0.5).any(1))[0]
    return 0.0 if len(ys) == 0 else float((ys.max() - ys.min() + 1) / H)


def beak_in(mask_stage, A, lm):
    b = P.ap(np.linalg.inv(A), lm["beak"])
    x, y = int(round(b[0])), int(round(b[1]))
    ok = 0 <= y < mask_stage.shape[0] and 0 <= x < mask_stage.shape[1] and mask_stage[y, x] > 0.5
    return bool(ok), [round(float(b[0]), 1), round(float(b[1]), 1)]


def wshadow(rig, x, hd, fy, height, light, A):
    """Watcher cast shadow (#45 ground projection of the OWI silhouette): (x, h) -> (x + h*lx, fy + h*ly)."""
    lx, ly = light
    pose = P.mkpose((x, fy), height / rig.r["height_px"], {"head": -hd})
    Pm = T(0, fy) @ np.array([[1, -lx, 0], [0, -ly, 0], [0, 0, 1]], float) @ T(0, -fy)
    Wd = rig.world(pose)
    al = np.zeros((H, W), np.float32)
    for n in rig.order:
        al = np.maximum(al, warp(rig.pieces[n][..., 3] / 255.0, A @ Pm @ Wd[n]))
    return al


def watcher_x(t, x0, x_stop, x_end, t_stop=3.5, t_go=11.0, t_out=15.0):
    """E1 slide -> E2 stop at 3.5 s (0.4 s ease), head +14 deg on twos, held to 10.0 -> E7 resumes at 11.0."""
    x, hd, _ = P.Watcher.score(t, x0, x_stop)
    if t >= t_go:
        x = x_stop + (x_end - x_stop) * min(1.0, (t - t_go) / (t_out - t_go)) ** 1.15
    return x, hd


ROO59 = P.Rig("rooster", era=1959)
ROO09 = colour_rig()   # r2: the Highsmith colour rooster (2009 daylight) replaces the toned 1870s stand-in
ROO59b = ROO59
ROO_59 = ROO59
ROO_2059 = P.Rig("rooster", era=2059)
WATCH = P.Watcher()


def with_head(ang, f, e3, e4, peck=None):
    name, w = P.head_score(f, e3, e4)
    if name is None and peck is not None:
        name, w = P.peck_score(f, peck)
    lean = LEAN.get(name, 0.0) * w
    a = P.add_head(ang, name, w) if name else dict(ang)
    a["rot"] = a.get("rot", 0.0) + lean
    return a, name


def look(g, base=0.35):
    return ("look_up", 1.0 if (g // 12) % 2 else base)


def walk_ang(g):
    """walk cycle on twos, 8 frames per stride: hips swing +-16, the lifted leg folds."""
    ph = ((g - g % 2) % 8) / 8.0
    s = math.sin(2 * math.pi * ph)
    a = dict(P.POSES["rest"])
    a.update(hip_L=16 * s, hip_R=-16 * s, shank_L=-30 * max(0, s), shank_R=-30 * max(0, -s),
             foot_L=12 * max(0, s), foot_R=12 * max(0, -s), rot=-2.0, neck=-3 * abs(s), head=2 * abs(s))
    return a


def climb(rig, hops, n_frames, x_of, hold_head=True):
    """hops = [(start_frame, tread_from, tread_to)], treads {x,y,scale}; the hop cycle of the puppet module,
    one tread per 8 frames on twos; holds between hops (settle, then hold with the head looking about)."""
    out = []
    for f in range(n_frames):
        g = f - f % 2
        cur = None
        for (s, a, b) in hops:
            if s <= g < s + 8:
                cur = P.track_climb(rig, [a, b], 0, 8)[g - s]
                break
        if cur is None:
            done = [h for h in hops if g >= h[0] + 8]
            tr = done[-1][2] if done else hops[0][1]
            since = g - (done[-1][0] + 8) if done else 99
            key = "settle" if 0 <= since < 4 else "hold"
            ang = P.angles_of(key)
            if hold_head and key == "hold":
                ang = P.add_head(ang, *look(g))
            cur = P.ground_pose(rig, tr["x"], lambda xx, y=tr["y"]: y, tr["scale"], ang)
            cur["key"], cur["contact"] = key, True
        out.append(cur)
    return P.tail_lag(out, rig)


# =============================================================================================== V1 1959
G59 = json.load(open(PL / "1959/geometry.json"))
PLATE59 = img(PL / "1959/plate_graded.png", "L")
VIG59 = img(PL / "1959/vignette_960x540.png", "L") / 255.0
IRON59A = img(PL / "1959/holdout_A_iron.png")[..., 3] / 255.0          # crop-A coords, offset (300, 1050)
CA59 = G59["crops"]["A"]

# the knock-proof module, re-based on story-plates' single unify grade (one curve for plate and puppet)
_r = KP.RX0, KP.RY0, KP.RX1, KP.RY1
KP.plate = PLATE59[_r[1]:_r[3], _r[0]:_r[2]].copy()
_hole = cv2.dilate((KP.iron0 > 0.3).astype(np.uint8), np.ones((5, 5), np.uint8))
KP.leaf_tex = cv2.inpaint(KP.plate.astype(np.uint8), _hole & cv2.dilate(KP.leaf0, np.ones((9, 9), np.uint8)), 7,
                          cv2.INPAINT_TELEA).astype(np.float32)
KP.CAM_I = (1662.0, 118.0, 2202.0)   # repair r2: insert moved off the black vestibule recess; the black mass is now
                                     # the watcher's cast shadow on the door (below) and, later, the open hall


def _watcher_on_door():
    """#45 / real light logic: the watcher stopped on the sidewalk (E2, held until E7) throws a hard head-and-
    shoulders shadow up the stoop onto the lower-left of the door. Same OWI silhouette and head turn (14 deg) as V1-A,
    projected with the low-left sun: sheared right, slightly elongated. Region coords of the knock plate."""
    Hr, Wr = KP.plate.shape
    pose = P.mkpose((1595.0, 990.0), 760.0 / WATCH.r["height_px"], {"head": -14.0})
    Wd = WATCH.world(pose)
    shear = T(0, 990) @ np.array([[1, -0.24, 0], [0, 1.0, 0], [0, 0, 1]], float) @ T(0, -990)
    al = np.zeros((Hr, Wr), np.float32)
    for n in WATCH.order:
        M = (T(-KP.RX0, -KP.RY0) @ shear @ Wd[n])[:2]
        al = np.maximum(al, cv2.warpAffine(WATCH.pieces[n][..., 3] / 255.0, M, (Wr, Hr), flags=cv2.INTER_LINEAR))
    return cv2.GaussianBlur(al, (0, 0), 0.9)


KP_WSH = _watcher_on_door()
KP.plate = KP.plate * (1 - 0.82 * KP_WSH)
_LEAF_CLEAN = KP.leaf_tex.copy()
_LEAF_SH = KP.leaf_tex * (1 - 0.82 * KP_WSH)
_door_layers0 = KP.door_layers


def _door_layers(th, A):
    """the shadow lies on the door while it is shut and slides off it as the leaf swings into the dark hall."""
    u = min(1.0, math.sin(th) * 4.0)
    KP.leaf_tex = _LEAF_SH * (1 - u) + _LEAF_CLEAN * u
    try:
        return _door_layers0(th, A)
    finally:
        KP.leaf_tex = _LEAF_SH


KP.leaf_tex = _LEAF_SH
KP.door_layers = _door_layers
_vy, _vx = np.mgrid[0:H, 0:W].astype(np.float32)
_vr = np.hypot((_vx - W / 2) / (W / 2), (_vy - H / 2) / (H / 2))
KP.VIG = np.clip(1 - 0.45 * np.clip(_vr - 0.42, 0, None) ** 1.3, 0.10, 1).astype(np.float32)   # r2: gentler lens fall-off (corner/centre ~0.3, whites back above 20 %)


def nose_y(name, x):
    pts = np.array(G59["A"]["tread_nose_polylines"][name], float)
    return float(np.interp(x, pts[:, 0], pts[:, 1]))


def tread59(name, x, h):
    y = nose_y(name, x) - 28 if name != "N1" else 880.0
    return {"x": x, "y": y, "scale": h / ROO59.r["height_px"]}


TR59 = {"N6": tread59("N6", 1290, 262), "N5": tread59("N5", 1345, 250), "N4": tread59("N4", 1400, 240)}
# repair r2: the climb runs up the middle of the stoop, behind the near twisted bars (#45 holdout), and stops on N4
# so the comb stays inside the frame; the bird then holds and looks up the last treads toward the door.
HOPS59 = [(14, TR59["N6"], TR59["N5"]), (52, TR59["N5"], TR59["N4"])]
TRACK59A = climb(ROO59, HOPS59, 120, None)
L59_TREAD = (0.88 * 0.5, 0.47 * 0.5)
L59_WATCH = (0.85 * 1.25, -0.53 * 1.25)


def riser_below(y_master, x):
    for n in ("N2", "N3", "N4", "N5", "N6"):
        ny = nose_y(n, x)
        if ny > y_master + 5:
            return ny
    return None


def v1_wide(fl, shot, silhouette=False):
    """V1 A (fl 0-119) / C (fl 264-359): sidewalk-level wide on the Rizzuto treads."""
    t = fl / FPS
    u = fl / 119.0 if shot == "A" else (fl - 264) / 95.0
    A = cam_rect(CA59["push_start"], CA59["push_end"], u)
    iron = warp(IRON59A, A @ T(300, 1050))
    x, hd = watcher_x(t, -1700, 150, 2900)
    wsh = wshadow(WATCH, x, hd, 2350, 1500, L59_WATCH, A)
    wsh = cv2.GaussianBlur(wsh, (0, 0), 1.0)
    info = {"shot": shot, "watcher_x": round(x, 1), "watcher_head_deg": hd}
    lay = None
    if shot == "A":
        pose = TRACK59A[fl]
        lay = ROO59.render(pose, A, (W, H))
    if silhouette:
        return d_wide(A, iron, wsh, lay, info)
    base = rgb3(warp(PLATE59, A, cv2.INTER_CUBIC, cv2.BORDER_REPLICATE))
    plate = base.copy()
    base = base * (1 - 0.80 * wsh[..., None])                   # the watcher's hard morning shadow
    out = base
    if lay is not None:
        al = lay["alpha"]
        sole = [lay["lm"]["foot_L"], lay["lm"]["foot_R"]]
        gy = max(s[1] for s in sole)
        ry = riser_below(P.ap(np.linalg.inv(A), (0, gy))[1] + 0, TRACK59A[fl]["root"][0])
        risers = [P.ap(A, (0, ry))[1]] if ry else None
        sh = P.cast_shadow(al, gy, L59_TREAD, risers, riser_shift=0.25 * 200 * A[0, 0])
        out = out * (1 - 0.70 * sh[..., None])
        if TRACK59A[fl].get("contact", True):
            out = out * (1 - P.contact_shadow((W, H), [(s[0], s[1] + 1) for s in sole], 13, 3.5, 0.65)[..., None])
        out = over(out, lay["rgb"], al)
        vis = al * (1 - iron)
        info.update(bird_px_total=vis_px(al), bird_px_visible=vis_px(vis), bird_px_behind_iron=int(((al > 0.5) & (iron > 0.5)).sum()),
                    bird_height_frac=round(height_frac(al), 3), key=TRACK59A[fl].get("key"))
    shadowed_plate = plate * (1 - 0.80 * wsh[..., None])
    out = over(out, shadowed_plate, iron)                        # #45: the near lace iron is in front of the bird
    out = out * VIG59[..., None]
    return out, info


def kp_beak(c):
    A = KP.cam_affine(c)
    return P.ap(A, KP.BIRD.landmarks(KP.pose_at(c))["beak"]), A


def v1_knock(fl):
    """V1 B (fl 120-263): the approved knock-proof composite (puppet unit), on the story-plates grade, with the
    r2 strike, the watcher's shadow on the door and the contact marks."""
    c = fl - 120
    g = KP.compose(c).astype(np.float32)
    led = KP.LEDGER["frames"][c]
    A = KP.cam_affine(c)
    pts = {e: P.ap(A, KP.BIRD.landmarks(KP.pose_at(e - 120))["beak"]) for e in (E3L, E4L)}
    g = contact_fx(g, pts, fl, A[0, 0], "wood", nick_until=168)
    info = {"shot": "B", "clip_f": c, "insert": led.get("insert"), "beak_in_leaf": led.get("beak_in_leaf_mask"),
            "beak_stage": led.get("beak_plate"), "bird_px_visible": led.get("bird_px_visible"), "door_deg": led.get("door_deg")}
    return rgb3(g), info


# =============================================================================================== D (silhouette)
PAPER_RNG = np.random.RandomState(7)
_fib = cv2.GaussianBlur(PAPER_RNG.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.2)
_fib2 = cv2.GaussianBlur(PAPER_RNG.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 9)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.hypot((_xx - W * 0.5) / (W * 0.62), (_yy - H * 0.46) / (H * 0.62))
BACKLIT = np.clip(1.0 - 0.55 * _r ** 2, 0.25, 1.0) * (1 + 0.035 * _fib + 0.05 * _fib2)
PAPER_RGB = np.array([252, 236, 204], np.float32)               # warm paper lit from behind
CARD = np.array([16, 14, 13], np.float32)
PIN = np.array([150, 146, 140], np.float32)


def paper():
    return BACKLIT[..., None] * PAPER_RGB[None, None, :]


def card_over(out, a, color=CARD):
    return out * (1 - a[..., None]) + color[None, None, :] * a[..., None]


def split_pins(out, lm, A, r=3.2):
    for k, v in lm.items():
        if k.startswith("pin_") and k not in ("pin_body",):
            cv2.circle(out, (int(round(v[0])), int(round(v[1]))), int(round(r)), PIN.tolist(), -1, cv2.LINE_AA)
            cv2.circle(out, (int(round(v[0])), int(round(v[1]))), max(1, int(round(r * 0.4))), (90, 88, 84), -1, cv2.LINE_AA)
    return out


def stoop_card(A):
    """black-card stoop traced from the 1959 tread-nose lines: each tread's nose and riser shadow as a card strip,
    the stoop's shadow side as one card."""
    m = np.zeros((H, W), np.uint8)
    for n, pts in G59["A"]["tread_nose_polylines"].items():
        pts = np.array(pts, float)
        xs = np.concatenate([[200.0], pts[:, 0], [2350.0]])
        ys = np.concatenate([[pts[0, 1]], pts[:, 1], [pts[-1, 1]]])
        top = [P.ap(A, (x, y - 3)) for x, y in zip(xs, ys)]
        bot = [P.ap(A, (x, y + 10)) for x, y in zip(xs[::-1], ys[::-1])]
        cv2.fillPoly(m, [np.int32(np.round(top + bot))], 1, cv2.LINE_AA)
    side = [P.ap(A, p) for p in G59["A"]["shadow_side_left_edge"]] + [P.ap(A, (2400, 2300)), P.ap(A, (2400, 1000))]
    cv2.fillPoly(m, [np.int32(np.round(side))], 1, cv2.LINE_AA)
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.6)


def d_wide(A, iron, wsh, lay, info):
    out = paper()
    out = out * (1 - 0.42 * wsh[..., None])                       # the watcher: a grey gel shadow on the screen
    out = card_over(out, stoop_card(A))
    if lay is not None:
        out = card_over(out, lay["alpha"])
        out = split_pins(out, lay["lm"], A)
        info.update(bird_px_visible=vis_px(lay["alpha"] * (1 - iron)), bird_height_frac=round(height_frac(lay["alpha"]), 3))
    out = card_over(out, cv2.GaussianBlur((iron > 0.5).astype(np.float32), (0, 0), 0.7))
    return out, info


def _poly(m, pts, A, val=1.0):
    cv2.fillPoly(m, [np.int32(np.round([P.ap(A, q) * 4 for q in pts]))], val, cv2.LINE_AA, shift=2)


def _rect(m, x0, y0, x1, y1, A, val=1.0):
    _poly(m, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], A, val)


def railing_card(A):
    """HANDMADE black-card railing for the theatre (r2): the handrail as one strip along the measured rail line,
    square balusters every 34 px and a cut scroll ring between each pair: cut shapes, not the photo's matte."""
    m = np.zeros((H, W), np.float32)
    rc = KP.rail_c
    _poly(m, [(1450, rc(1450) - 9), (2320, rc(2320) - 9), (2320, rc(2320) + 9), (1450, rc(1450) + 9)], A)
    for i, x in enumerate(np.arange(1566.0, 2320.0, 34.0)):
        _rect(m, x - 3.5, rc(x) + 6, x + 3.5, 760, A)
        if i % 2 == 0:
            cx, cy = x + 17, rc(x + 17) + 70
            c = P.ap(A, (cx, cy))
            r = 13 * A[0, 0]
            cv2.circle(m, (int(c[0] * 4), int(c[1] * 4)), int(r * 4), 1.0, max(1, int(4 * 3.2 * A[0, 0])), cv2.LINE_AA, shift=2)
            cv2.circle(m, (int(c[0] * 4), int((c[1] + 2.2 * r) * 4)), int(r * 0.7 * 4), 1.0, max(1, int(4 * 3.0 * A[0, 0])), cv2.LINE_AA, shift=2)
    return np.clip(m, 0, 1)


def door_card_geo(A):
    """HANDMADE door: one black card over the leaf with its four panel mouldings cut as thin slots (light through)."""
    d = np.zeros((H, W), np.float32)
    _rect(d, KP.HINGE_X, KP.RY0 - 60, KP.LEAF_R, 700, A)
    for (x0, y0, x1, y1) in ((1782, 20, 1958, 262), (1782, 300, 1958, 690)):
        for inset, wdt in ((0, 6), (16, 3.5)):
            a0, b0, a1, b1 = x0 + inset, y0 + inset, x1 - inset, y1 - inset
            sl = np.zeros((H, W), np.float32)
            _rect(sl, a0, b0, a1, b1, A)
            _rect(sl, a0 + wdt, b0 + wdt, a1 - wdt, b1 - wdt, A, 0.0)
            d = d * (1 - 0.92 * sl)
    kn = P.ap(A, (1958, 318))                                     # the knob: a pin-head disc
    cv2.circle(d, (int(kn[0]), int(kn[1])), max(2, int(7 * A[0, 0])), 1.0, -1, cv2.LINE_AA)
    return d


def d_knock(fl):
    """D B: the knock-proof score replayed as silhouette theatre - same camera, same FK track, same door angle.
    r2: every set piece is a cut card (door with slot mouldings, vestibule and jamb boards, railing strip with
    balusters and scroll rings); the watcher is a grey gel shadow; nothing is thresholded from the photograph."""
    c = fl - 120
    t = c / FPS
    A = KP.cam_affine(c)
    th = KP.door_theta(t)
    leafm = KP.warp_plate(KP.leaf0.astype(np.float32), A, cv2.INTER_LINEAR)
    rail = railing_card(A)
    board = np.zeros((H, W), np.float32)
    _rect(board, 1380, KP.RY0 - 80, KP.HINGE_X - 6, 760, A)          # the vestibule: a board
    _rect(board, KP.LEAF_R, KP.RY0 - 80, KP.LEAF_R + 16, 760, A)      # the latch jamb: a strip
    hold_in = np.maximum(np.maximum(board, rail), 1 - leafm)        # once inside, seen only through the doorway
    out = paper()
    wsh = KP.warp_plate(KP_WSH, A, cv2.INTER_LINEAR)
    out = out * (1 - 0.42 * wsh[..., None])                          # the watcher: grey gel, as in the wides
    door_card = door_card_geo(A)
    if th > 0:
        src, dst = KP.leaf_quads(th)
        s_ = np.float32([P.ap(A, p) for p in src])
        d_ = np.float32([P.ap(A, p) for p in dst])
        Hm = cv2.getPerspectiveTransform(s_, d_)
        swung = cv2.warpPerspective(door_card, Hm, (W, H))
        out = out * (1 + 0.12 * leafm[..., None])                  # the opened doorway: the lamp behind the screen
        out = card_over(out, swung * 0.58)
    else:
        out = card_over(out, door_card * 0.58)                     # the door is tissue over card: a grey the bird reads on
    out = card_over(out, board * 0.97)
    pose = KP.pose_at(c)
    lay = KP.BIRD.render(pose, A, (W, H))
    al = lay["alpha"]
    if KP.TRACK[c]["inside"]:
        al = al * (1 - hold_in)
    out = card_over(out, al)
    if not KP.TRACK[c]["inside"]:
        out = split_pins(out, lay["lm"], A, r=3.2 * A[0, 0] / 1.7)
    out = card_over(out, rail)
    pts = {e: P.ap(A, KP.BIRD.landmarks(KP.pose_at(e - 120))["beak"]) for e in (E3L, E4L)}
    out = contact_fx(out, pts, fl, A[0, 0], "wood", nick_until=168)
    led = KP.LEDGER["frames"].get(c)
    if led is None:
        KP.compose(c)
        led = KP.LEDGER["frames"][c]
    info = {"shot": "B", "clip_f": c, "beak_in_leaf": led["beak_in_leaf_mask"], "beak_stage": led["beak_plate"],
            "bird_px_visible": vis_px(al * (1 - rail)) if KP.TRACK[c]["inside"] else led["bird_px_visible"]}
    return out, info


# =============================================================================================== V2 2009
G09 = json.load(open(PL / "2009/geometry.json"))
PRE09 = img(PL / "2009/preview_graded.png", "RGB")                     # A/C stage: 1024-px service JPEG coords
REG09 = img(PL / "2009/region_graded.png", "RGB")                      # B stage: master region / 3
LEAF09 = img(PL / "2009/piece_leaf.png")
HALL09 = img(PL / "2009/hall.png")
JAMBR09 = img(PL / "2009/holdout_jamb_right.png")[..., 3] / 255.0
JAMBL09 = img(PL / "2009/holdout_jamb_left.png")[..., 3] / 255.0
IRON09 = img(PL / "2009/holdout_iron.png")[..., 3] / 255.0
S_RP = 3 * 1024 / 13925.0
R2P = np.array([[S_RP, 0, 7300 * 1024 / 13925.0], [0, S_RP, 1500 * 1024 / 13925.0], [0, 0, 1.0]])   # region -> preview
CA09 = G09["crops"]["A"]
RB09_0, RB09_1 = (400.0, 1006.2, 933.0, 1306.0), (404.0, 1008.4, 929.0, 1303.8)    # r2: B reframed onto the latch edge, brick and iron (saturation from the scene, not a boost)
QUAD09 = [(145.0, 330.0), (485.0, 330.0), (485.0, 1245.0), (145.0, 1245.0)]
CAM09, Z09 = (466.0, 1000.0), 1500.0
CHAIN_Y = 842.0                    # chain height on the leaf (handmade object, placed just above the knob)
L09 = (-0.42, 0.22)                # bird cast shadow: plate light from upper right (shadows fall down-left)
LINK_F = img(PL / "handmade/chain_link_face.png")
LINK_E = img(PL / "handmade/chain_link_edge.png")


def p2r(y):
    return (y - 1500 * 1024 / 13925.0) / S_RP


def v2_tread(y_pre, x_pre=592.0, h_pre=38.0):
    return {"x": x_pre, "y": y_pre, "scale": h_pre / 608.0}


TR09 = [v2_tread(560, 586, 40), v2_tread(533, 588, 39.5), v2_tread(508, 589, 39), v2_tread(473, 590, 38.5),
        v2_tread(441, 591, 38), v2_tread(412, 592, 37.5), v2_tread(395, 593, 37.5)]
HOPS09 = [(6 + 14 * i, TR09[i], TR09[i + 1]) for i in range(6)]
TRACK09A = climb(ROO09, HOPS09, 120, None)


def door_hinged(stage_img, leaf_a, hall_rgb, quad, th, cam, z0, A, shade=0.35):
    """#45 door layer: plate, hall where the leaf has swung away, the leaf as a homography about its hinge."""
    base = warp(stage_img, A, cv2.INTER_CUBIC, cv2.BORDER_REPLICATE)
    la = warp(leaf_a, A)
    if th <= 0:
        return base, la, la, None
    dst = P.hinge_quad(quad, "left", th, cam, z0)
    s = np.float32([P.ap(A, p) for p in quad])
    d = np.float32([P.ap(A, p) for p in dst])
    Hm = cv2.getPerspectiveTransform(s, d)
    tex = cv2.warpPerspective(base, Hm, (W, H)) * (1 - shade * math.sin(th))
    sw = cv2.warpPerspective(la, Hm, (W, H))
    hall = warp(hall_rgb, A)
    out = over(base, hall, la)
    out = over(out, tex, sw)
    return out, la, sw, d


def draw_chain(out, p_jamb, p_leaf, th, k):
    """HANDMADE 2009 door chain: 6 shaded steel links along the puppet module's catenary (slack -> taut at 25 deg)."""
    pts = P.chain_links(p_jamb, p_leaf, th, sag_px=14.0 * k)
    lay = np.zeros((H, W, 4), np.float32)
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0) * 2.0
        sp = LINK_F if i % 2 == 0 else LINK_E
        sc = max(0.08, L / 50.0)
        ang = math.degrees(math.atan2(-(y1 - y0), x1 - x0))
        M = cv2.getRotationMatrix2D((36.0, 36.0), ang, sc)
        M[:, 2] += [(x0 + x1) / 2 - 36.0, (y0 + y1) / 2 - 36.0]
        s = cv2.warpAffine(sp, M, (W, H), flags=cv2.INTER_LINEAR)
        a = s[..., 3:4] / 255.0
        lay[..., :3] = s[..., :3] * a + lay[..., :3] * (1 - a)
        lay[..., 3:4] = a + lay[..., 3:4] * (1 - a)
    return over(out, lay[..., :3] * 0.9, lay[..., 3])


def v2_wide(fl, shot):
    t = fl / FPS
    u = fl / 119.0 if shot == "A" else (fl - 264) / 95.0
    A = cam_rect(CA09["push_start"], CA09["push_end"], u)
    th = 0.0 if shot == "A" else math.radians(25.0)
    quad = [tuple(P.ap(R2P, q)) for q in QUAD09]
    leaf_a = cv2.warpAffine(LEAF09[..., 3] / 255.0, R2P[:2], (1024, 575))
    hall = cv2.warpAffine(HALL09[..., :3], R2P[:2], (1024, 575))
    out, la, sw, d = door_hinged(PRE09, leaf_a, hall, quad, th, tuple(P.ap(R2P, CAM09)), Z09 * S_RP, A)
    plate = warp(PRE09, A, cv2.INTER_CUBIC, cv2.BORDER_REPLICATE)
    x, hd = watcher_x(t, 1010, 948, 1160)
    wsh = cv2.GaussianBlur(wshadow(WATCH, x, -hd, 562, 165, (-0.95, 0.10), A), (0, 0), 1.2)
    out = out * (1 - 0.5 * wsh[..., None])
    info = {"shot": shot, "door_deg": round(math.degrees(th), 1), "watcher_x": round(x, 1)}
    iron = warp(IRON09, A @ R2P)
    if shot == "A":
        pose = TRACK09A[fl]
        lay = ROO09.render(pose, A, (W, H))
        al = lay["alpha"]
        sole = [lay["lm"]["foot_L"], lay["lm"]["foot_R"]]
        gy = max(s[1] for s in sole)
        sh = P.cast_shadow(al, gy, L09)
        out = out * (1 - 0.45 * sh[..., None])
        if TRACK09A[fl].get("contact", True):
            out = out * (1 - P.contact_shadow((W, H), [(s[0], s[1] + 1) for s in sole], 7, 2.0, 0.55)[..., None])
        out = over(out, lay["rgb"], al)
        info.update(bird_px_visible=vis_px(al * (1 - iron)), bird_height_frac=round(height_frac(al), 3))
    out = over(out, plate * (1 - 0.5 * wsh[..., None]), iron)
    return out, info


def track09b():
    tr = []
    x0, y0, sc = 436.0, 1283.0, 108.0 / 608.0       # r2: closer to the latch edge, scaled to the tighter B
    gr = lambda xx: y0  # noqa: E731
    for c in range(144):
        g = c - c % 2
        if E3L - 120 - 4 <= c <= E4L - 120 + 4:
            g = c
        f = g + 120
        if g < 84:
            ang = P.angles_of("hold" if g >= 4 else "settle")
            if g < 18:
                ang = P.add_head(ang, "look_up", 0.6 if (g // 6) % 2 else 0.2)
            ang, name = with_head(ang, f, E3L, E4L)
            if name is None and g >= 40:
                ang = P.add_head(ang, *look(g, 0.5))
            p = P.ground_pose(ROO09, x0, gr, sc, ang)
            if f in (E3L, E4L):
                p["root"] = (p["root"][0] - 1.0, p["root"][1] + 0.4)
            p["key"] = name or "hold"
        else:                                                  # E6: walk right into the chained gap, past the jamb
            u = (g - 84) / 34.0
            x = x0 + 230 * min(1.0, u) ** 1.1
            p = P.ground_pose(ROO09, x, gr, sc * (1 - 0.06 * min(1, u)), walk_ang(g))
            p["key"] = "walk_in"
        tr.append(p)
    return P.tail_lag(tr, ROO09)


TRACK09B = track09b()


def v2_knock(fl):
    c = fl - 120
    t = fl / FPS
    A = cam_rect(RB09_0, RB09_1, c / 143.0)
    th = P.chain_theta(t)
    out, la, sw, d = door_hinged(REG09, LEAF09[..., 3] / 255.0, HALL09[..., :3], QUAD09, th, CAM09, Z09, A)
    k = A[0, 0]
    jambR = warp(JAMBR09, A)
    pose = TRACK09B[c]
    lum = 1.0 - 0.4 * np.clip((pose["root"][0] - 400) / 140, 0, 1)
    lay = ROO09.render(pose, A, (W, H), lum=float(lum))
    al = lay["alpha"]
    sole = [lay["lm"]["foot_L"], lay["lm"]["foot_R"]]
    gy = max(s[1] for s in sole)
    sh = P.cast_shadow(al, gy, L09) * (1 - la * (th > 0.05))
    out = out * (1 - 0.45 * sh[..., None])
    out = out * (1 - P.contact_shadow((W, H), [(s[0], s[1] + 1) for s in sole], 16, 4, 0.55)[..., None])
    vis = al
    if c >= 84:                                                # inside the doorway: only the gap shows the bird
        xe = d[1][0] if d is not None else W
        xx = np.arange(W, dtype=np.float32)[None, :]
        revealed = np.clip(la - sw, 0, 1)
        front = (xx < xe).astype(np.float32)
        vis = al * np.maximum(front, revealed) * (1 - jambR)
    out = over(out, lay["rgb"], vis)
    if th > 0.01 and d is not None:                            # the chain across the gap
        fy = (CHAIN_Y - 330) / (1245 - 330)
        p_leaf = (d[1][0] + (d[2][0] - d[1][0]) * fy, d[1][1] + (d[2][1] - d[1][1]) * fy)
        p_jamb = tuple(P.ap(A, (489.0, CHAIN_Y - 6)))
        out = draw_chain(out, p_jamb, p_leaf, th, k)
    pts = {e: P.ap(A, ROO09.landmarks(TRACK09B[e - 120])["beak"]) for e in (E3L, E4L)}
    out = contact_fx(out, pts, fl, k, "paint", nick_until=167)
    bi, bst = beak_in(LEAF09[..., 3] / 255.0, A, lay["lm"])
    return out, {"shot": "B", "door_deg": round(math.degrees(th), 2), "beak_in_leaf": bi, "beak_stage": bst,
                 "bird_px_visible": vis_px(vis), "bird_height_frac": round(height_frac(al), 3)}


# =============================================================================================== V3 2059
G59x = json.load(open(PL / "2059/geometry.json"))
PL59 = img(PL / "2059/plate_graded.png", "RGB")
def _interior():
    """the view through the doorway once the glass has gone: the plate's own through-glass view with the leaf frame
    members (stiles, rails) inpainted away and the glass sheen taken off (x0.66). HANDMADE from the foraged plate."""
    p = np.clip(img(PL / "2059/plate_graded.png", "RGB"), 0, 255).astype(np.uint8)
    m = np.zeros(p.shape[:2], np.uint8)
    for x0, x1 in ((690, 709), (919, 941), (1156, 1175)):
        m[180:712, x0:x1] = 1
    for y0, y1 in ((182, 204), (680, 704)):
        m[y0:y1, 690:1175] = 1
    out = cv2.inpaint(p, m, 9, cv2.INPAINT_TELEA).astype(np.float32)
    return out * 0.66


INT59 = _interior()
LL59 = img(PL / "2059/piece_leaf_left.png")
LR59 = img(PL / "2059/piece_leaf_right.png")
POSTL = img(PL / "2059/piece_post_left.png")
POSTR = img(PL / "2059/piece_post_right.png")
PILLAR = img(PL / "2059/piece_pillar.png")
THRESH = img(PL / "2059/piece_threshold.png")
BAR = img(PL / "handmade/sensor_bar_off.png")
DOT_ON = img(PL / "handmade/sensor_dot_on.png")
DOT_RF = img(PL / "handmade/sensor_dot_refuse.png")
DOTC = json.load(open(PL / "handmade/handmade.json"))["sensor_2059"]["dot_centres"]
CA20 = G59x["crops"]["A"]
RB20_0, RB20_1 = (400.0, 180.0, 1440.0, 765.0), (407.8, 184.4, 1432.2, 760.6)
TRAVEL = G59x["slide_rails"]["travel_px"]
X1_T = 4.6
FSM, FSM_EVENTS = P.DoorFSM([(X1_T, True), (E3L / FPS, True), (E4L / FPS, True)], t_close=10.2).trace(15.0)
LEAF_MASK20 = np.maximum(LL59[..., 3], LR59[..., 3]) / 255.0
L20_BIRD = (0.10, -0.32)
L20_WATCH = (0.30, -0.95)


def sensor_layer(dots, state):
    """HANDMADE 7-dot strip: brushed bar, lit dots composited at the sprite positions."""
    s = BAR.copy()
    for i, on in enumerate(dots):
        if on <= 0:
            continue
        sp = DOT_RF if state == "refuse" else DOT_ON
        cx, cy = DOTC[i]
        x0, y0 = int(cx - 32), int(cy - 32)
        sub = np.zeros_like(s)
        xa, ya = max(0, x0), max(0, y0)
        xb, yb = min(s.shape[1], x0 + 64), min(s.shape[0], y0 + 64)
        sub[ya:yb, xa:xb] = sp[ya - y0:yb - y0, xa - x0:xb - x0]
        a = sub[..., 3:4] / 255.0 * on
        s[..., :3] = sub[..., :3] * a + s[..., :3] * (1 - a)
        s[..., 3:4] = np.maximum(s[..., 3:4], sub[..., 3:4] * on)
    return s


def strip_on(out, A, fr):
    m = A @ T(930 - 140, 205 - 11.5) @ P.S(0.5)
    s = warp(sensor_layer(fr["dots"], fr["state"]), m)
    return over(out, s[..., :3], s[..., 3] / 255.0)


def track20a():
    tr = []
    for f in range(120):
        g = f - f % 2
        if X1_T * FPS - 4 <= f <= X1_T * FPS + 5:
            g = f
        if g < 100:
            u = g / 100.0
            x = 300 + 480 * u
            y = 850 - 105 * u
            sc = (0.335 - 0.035 * u)
            ang = walk_ang(g)
            ang = P.add_head(ang, "look_up", 0.3)
            p = P.ground_pose(ROO_2059, x, lambda xx, y=y: y, sc, ang)
            p["key"] = "walk"
        else:
            ang = P.angles_of("hold")
            ang, name = with_head(ang, f, -999, -999, peck=int(round(X1_T * FPS)))
            p = P.ground_pose(ROO_2059, 780, lambda xx: 745.0, 0.30, ang)
            p["key"] = name or "hold"
        tr.append(p)
    return P.tail_lag(tr, ROO_2059)


def track20b():
    tr = []
    for c in range(144):
        g = c - c % 2
        f = c + 120
        if E3L - 4 <= f <= E4L + 4:
            g = c
        inside = False
        if g < 12:                                         # one step closer: the peck had come a tread too early
            u = g / 12.0
            p = P.ground_pose(ROO_2059, 780 + 22 * u, lambda xx: 745.0, 0.30, walk_ang(g))
            p["key"] = "step"
        elif g < 84:
            ang = P.angles_of("settle" if g < 16 else "hold")
            ang, name = with_head(ang, f, E3L, E4L)
            if name is None and g >= 44:
                ang = P.add_head(ang, *look(g, 0.5))
            p = P.ground_pose(ROO_2059, 802, lambda xx: 745.0, 0.30, ang)
            if f in (E3L, E4L):
                p["root"] = (p["root"][0] - 1.0, p["root"][1] + 0.4)
            p["key"] = name or "hold"
        elif g < 92:                                       # hop over the threshold rail
            k = (g - 84) // 2
            key = P.HOP_KEYS[k]
            u = {"crouch": 0.0, "push": 0.08, "air": 0.55, "land": 1.0}[key]
            x = 802 + 60 * u
            y = 745 + (700 - 745) * u
            lift = 30.0 if key == "air" else 0.0
            p = P.ground_pose(ROO_2059, x, lambda xx, y=y: y, 0.30 - 0.03 * u, P.angles_of(key), lift=lift)
            p["key"] = key
            inside = u > 0.5
        else:                                              # walk on into the interior, behind the glass and the pillar
            u = min(1.0, (g - 92) / 26.0)
            x = 862 + (1196 - 862) * u
            y = 700 - 14 * u
            p = P.ground_pose(ROO_2059, x, lambda xx, y=y: y, 0.27 - 0.165 * u, walk_ang(g))
            p["key"] = "walk_in"
            inside = True
        p["inside"] = inside
        tr.append(p)
    return P.tail_lag(tr, ROO_2059)


TRACK20A, TRACK20B = track20a(), track20b()


def v3_frame(fl, shot):
    t = fl / FPS
    fr = FSM[min(fl, len(FSM) - 1)]
    if shot == "B":
        A = cam_rect(RB20_0, RB20_1, (fl - 120) / 143.0)
    else:
        # 2059 wides are locked off (no push): the reference's static camera, and the terrazzo plate resampled
        # every frame would cost ~2.5 MB of the 6 MB budget in codec noise
        A = cam_rect(CA20["push_start"], CA20["push_end"], 0.5)
    slide = fr["slide"]
    base = warp(PL59, A, cv2.INTER_CUBIC, cv2.BORDER_REPLICATE)
    leafm = warp(LEAF_MASK20, A)
    interior = warp(INT59, A, cv2.INTER_LINEAR, cv2.BORDER_REPLICATE)
    out = over(base, interior, leafm * (1.0 if slide > 0 else 0.0))
    info = {"shot": shot, "state": fr["state"], "dots": fr["dots"], "slide": slide}
    bird = None
    track = TRACK20A if shot == "A" else TRACK20B if shot == "B" else None
    if track is not None:
        c = fl if shot == "A" else fl - 120
        pose = track[c]
        inside = pose.get("inside", False)
        lum = 1.0 - 0.3 * (1.0 if inside else 0.0) * min(1.0, (pose["root"][0] - 862) / 200 + 0.4)
        bird = ROO_2059.render(pose, A, (W, H), lum=float(lum))
        bird["inside"] = inside
    # watcher: AK17's very long low-sun shadow raking up the forecourt onto the glass
    if shot != "B":
        x, hd = watcher_x(t, -900, 520, 2150)
        wsh = cv2.GaussianBlur(wshadow(WATCH, x, hd, 1000, 700, L20_WATCH, A), (0, 0), 1.8)
        info.update(watcher_x=round(x, 1), watcher_shadow_height_frac=round(height_frac(wsh), 3))
    else:
        wsh = np.zeros((H, W), np.float32)
    out = out * (1 - 0.55 * wsh[..., None])
    if bird is not None and bird["inside"]:
        out = over(out, bird["rgb"], bird["alpha"])
    # the two leaves slide on their rails (the door's own answer, no hand)
    if slide > 0 or (bird is not None and bird["inside"]):
        dx = TRAVEL * slide
        for piece, sgn in ((LL59, -1), (LR59, 1)):
            M = A @ T(sgn * dx, 0)
            pc = warp(piece, M)
            a = pc[..., 3] / 255.0
            if bird is not None and bird["inside"]:            # glass: the bird behind reads at 45 %
                ba = bird["alpha"] * a
                mixc = pc[..., :3] * (1 - 0.45 * ba[..., None]) + bird["rgb"] * 0.45 * ba[..., None]
                out = over(out, mixc, a)
            else:
                out = over(out, pc[..., :3], a)
    th = warp(THRESH, A)
    out = over(out, th[..., :3], th[..., 3] / 255.0)
    if bird is not None and not bird["inside"]:
        al = bird["alpha"]
        sole = [bird["lm"]["foot_L"], bird["lm"]["foot_R"]]
        gy = max(s[1] for s in sole)
        out = out * (1 - 0.35 * P.cast_shadow(al, gy, L20_BIRD)[..., None])
        out = out * (1 - P.contact_shadow((W, H), [(s[0], s[1] + 1) for s in sole], 11 * A[0, 0] / 0.63 * 0.6, 3, 0.6)[..., None])
        out = over(out, bird["rgb"], al)
    hold = np.zeros((H, W), np.float32)
    for piece in (POSTL, POSTR, PILLAR):
        pc = warp(piece, A)
        a = pc[..., 3] / 255.0
        out = over(out, pc[..., :3] * (1 - 0.55 * wsh[..., None]), a)
        hold = np.maximum(hold, a)
    out = strip_on(out, A, fr)
    if shot == "B":
        pts = {e: P.ap(A, ROO_2059.landmarks(TRACK20B[e - 120])["beak"]) for e in (E3L, E4L)}
        out = contact_fx(out, pts, fl, A[0, 0], "glass")
    if bird is not None:
        al = bird["alpha"]
        if bird["inside"]:
            v = al * (1 - hold)
            info["bird_px_visible"] = vis_px(v)
            info["bird_px_visible_full"] = vis_px(v * (1 - leafm * (slide < 0.5)))
        else:
            info["bird_px_visible"] = vis_px(al * (1 - hold))
        info["bird_height_frac"] = round(height_frac(al), 3)
        bi, bst = beak_in(LEAF_MASK20, A, bird["lm"])
        info.update(beak_in_leaf=bi, beak_stage=bst, inside=bird["inside"])
    return out, info


# =============================================================================================== cards and timeline
def card_frame(ink, t, big, small=None, a0=0.0, a1=1.0, size=46):
    ink.fill(INK)
    al = min(1.0, (t - a0) / 0.25, (a1 - t) / 0.35) if a1 > a0 else 1.0
    al = max(0.0, al)
    ink.text((W / 2, H / 2 - (16 if small else 0)), big, "sans", size, (238, 238, 238), anchor="mm", alpha=int(255 * al))
    if small:
        ink.text((W / 2, H / 2 + 34), small, "sans", 17, (150, 150, 150), anchor="mm", alpha=int(255 * al))


def version_frame(v, fl):
    if v == "V1":
        if fl < 120:
            return v1_wide(fl, "A")
        if fl < 264:
            return v1_knock(fl)
        return v1_wide(fl, "C")
    if v == "D":
        if fl < 120:
            return v1_wide(fl, "A", silhouette=True)
        if fl < 264:
            return d_knock(fl)
        return v1_wide(fl, "C", silhouette=True)
    if v == "V2":
        if fl < 120:
            return v2_wide(fl, "A")
        if fl < 264:
            return v2_knock(fl)
        return v2_wide(fl, "C")
    return v3_frame(fl, "A" if fl < 120 else "B" if fl < 264 else "C")


def which(k):
    for v, o in OFFS.items():
        f0 = int(round(o * FPS))
        if f0 <= k < f0 + 360:
            return v, k - f0
    return None, None


def picture(t, ink):
    k = int(round(t * FPS))
    v0, _ = which(k)
    ink._grain = v0 == "D"   # r2: the 1959 silver print carries its own grain; kit grain only on the paper theatre
    if k < 48:
        card_frame(ink, t, "A MORNING STROLL", "after Grant Orchard (2011)", 0.15, 2.0)
        return
    if k >= 1584:
        card_frame(ink, t, "", None, 66.0, 68.2)
        al = max(0.0, min(1.0, (t - 66.0) / 0.25, (68.2 - t) / 0.35))
        lines = [("Foraged: Library of Congress (Rizzuto 1959, Highsmith 2019, 1870s stereograph, Bubley 1943),", 17, 205),
                 ("Wikimedia Commons, Prelinger Archives via movingimagearchive.com.", 17, 205),
                 ("Sliding door photograph: Plennert, CC BY-SA 4.0. This film is CC BY-SA 4.0.", 17, 205),
                 ("Handmade: the cuts and joints, shadows, chain, sensor strip, chips, silhouette cards.", 15, 150)]
        for i, (tx, sz, g) in enumerate(lines):
            ink.text((W / 2, H / 2 - 48 + 30 * i), tx, "sans", sz, (g, g, g), anchor="mm", alpha=int(255 * al))
        return
    v, fl = which(k)
    if v is None:
        lab = {48: ("1959", None), 432: ("2009", "plate photographed 2019, standing in"), 816: ("2059", "plate photographed 2022; staged"),
               1200: ("1959", "diagnostic: silhouette")}
        f0 = max(x for x in lab if x <= k)
        big, small = lab[f0]
        card_frame(ink, t, big, small, f0 / FPS, f0 / FPS + 1.0)
        return
    out, _ = version_frame(v, fl)
    ink.paste(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB"))


# =============================================================================================== sound (sound unit stems)
def load_st(p):
    with wave.open(str(p)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
        return x.reshape(-1, 2) if w.getnchannels() == 2 else np.stack([x, x], 1)


STEMS = SRC / "sound" / "stems"


def add_st(mix, st, at, gain=1.0):
    mix.add(st[:, 0], at, gain / 1.414, pan=-1.0)
    mix.add(st[:, 1], at, gain / 1.414, pan=1.0)


def faded(st, a, b, fin=0.3, fout=0.4, rate=44100):
    seg = st[int(a * rate):int(b * rate)].copy()
    n = len(seg)
    w = np.ones(n)
    w[:int(fin * rate)] = np.linspace(0, 1, int(fin * rate))
    w[n - int(fout * rate):] = np.linspace(1, 0, int(fout * rate))
    return seg * w[:, None]


def sound(mix):
    v = {n: load_st(STEMS / f"{n}.wav") for n in ("v1", "v2", "v3")}
    add_st(mix, load_st(STEMS / "title_tail.wav"), 0.0, 0.9)
    add_st(mix, faded(v["v1"], 13.9, 15.0, 0.35, 0.15), 1.95, 0.8)    # card 1959: the 1959 bed leads in
    add_st(mix, v["v1"], 3.0)
    add_st(mix, faded(v["v2"], 13.9, 15.0, 0.3, 0.1), 18.0, 0.8)
    add_st(mix, v["v2"], 19.0)
    add_st(mix, faded(v["v3"], 13.9, 15.0, 0.3, 0.1), 34.0, 0.8)
    add_st(mix, v["v3"], 35.0)
    add_st(mix, faded(v["v1"], 13.9, 15.0, 0.3, 0.1), 50.0, 0.6)
    add_st(mix, v["v1"], 51.0)                                       # D reuses the identical 1959 stem
    add_st(mix, faded(v["v1"], 12.5, 14.5, 0.1, 1.6), 66.0, 0.6)


# =============================================================================================== ledger, checks, compare
REFS = OUL / "assets" / "references"


def stats(a):
    a = np.asarray(a, np.float32)
    L = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    hsv = cv2.cvtColor(np.clip(a, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
    h, w = L.shape
    cs = max(1, int(min(h, w) * 0.12))
    corners = np.mean([L[:cs, :cs].mean(), L[:cs, -cs:].mean(), L[-cs:, :cs].mean(), L[-cs:, -cs:].mean()])
    centre = L[h // 3: 2 * h // 3, w // 3: 2 * w // 3].mean()
    q = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).quantize(6, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[:18]
    cnt = sorted(q.getcolors(), reverse=True)
    palette = ["#%02x%02x%02x" % tuple(pal[3 * i:3 * i + 3]) for _, i in cnt]
    dark = (L < 40).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(dark, connectivity=8)
    big = float(st[1:, cv2.CC_STAT_AREA].max() / L.size) if n > 1 else 0.0
    return {"lt40": round(float((L < 40).mean() * 100), 1), "gt200": round(float((L > 200).mean() * 100), 1),
            "median": round(float(np.median(L)), 1), "p5_p95": [int(np.percentile(L, 5)), int(np.percentile(L, 95))],
            "corner_centre": round(float(corners / max(centre, 1e-6)), 2),
            "R_minus_B": round(float((a[..., 0] - a[..., 2]).mean()), 1),
            "abs_R_minus_B": round(float(np.abs(a[..., 0] - a[..., 2]).mean()), 1),
            "sat": round(float(hsv[..., 1].mean() / 255), 3), "largest_black_mass": round(big * 100, 1), "palette": palette}


def compare_sheet(frame_img, ref_name, title, fs, rs, out_path):
    from PIL import ImageDraw
    ref = Image.open(REFS / ref_name).convert("RGB")
    ref = ref.resize((960, int(960 * ref.size[1] / ref.size[0])))
    sheet = Image.new("RGB", (1940, 760), (20, 20, 20))
    sheet.paste(frame_img, (10, 50))
    sheet.paste(ref.crop((0, 0, 960, min(540, ref.size[1]))), (970, 50))
    d = ImageDraw.Draw(sheet)
    f1 = kit.font("sans", 22)
    f2 = kit.font("mono", 14)
    d.text((10, 14), title, fill=(235, 235, 235), font=f1)
    d.text((970, 14), f"reference: {ref_name} (compared only; never copied)", fill=(235, 235, 235), font=f1)
    for x0, s in ((10, fs), (970, rs)):
        y = 600
        for i, c in enumerate(s["palette"]):
            d.rectangle([x0 + i * 82, y, x0 + i * 82 + 74, y + 34], fill=c, outline=(90, 90, 90))
            d.text((x0 + i * 82, y + 38), c, fill=(200, 200, 200), font=f2)
        d.text((x0, y + 66), f"<40 {s['lt40']}%  >200 {s['gt200']}%  median {s['median']}  p5/p95 {s['p5_p95']}  "
               f"corner/centre {s['corner_centre']}", fill=(220, 220, 220), font=f2)
        d.text((x0, y + 86), f"mean R-B {s['R_minus_B']}  |R-B| {s['abs_R_minus_B']}  sat {s['sat']}  "
               f"largest <40 mass {s['largest_black_mass']}%", fill=(220, 220, 220), font=f2)
    sheet.save(out_path, quality=88)


def report(film):
    led = {"film": "a-morning-stroll", "revision": "score-r1 / plan-r1", "fps": FPS, "seconds": SECONDS,
           "versions": {}, "assertions": {}}
    gl = lambda v, f: int(round(OFFS[v] * FPS)) + f  # noqa: E731
    for v in ("V1", "V2", "V3", "D"):
        bv = BEAT["versions"][v]
        man = {"era": bv["era"], "genre_tone": bv["genre_tone"], "render_technique": bv["render_technique"],
               "door_mechanism": bv["door_mechanism"], "plate": bv["plate"], "offset_s": OFFS[v],
               "events": {e: dict(bv["events"][e]) for e in bv["events"]}, "shots": bv["shots"], "checks": {}}
        if v == "V3":
            man["counterexample"] = bv["counterexample"]
            man["door_fsm_events"] = FSM_EVENTS
        for name, fl in (("E3", E3L), ("E4", E4L)):
            out, info = version_frame(v, fl)
            assert gl(v, fl) == bv["events"][name]["global_frame"], (v, name)
            assert info["beak_in_leaf"], f"{v} {name}: beak tip not inside the door-leaf mask {info}"
            man["checks"][name] = {"global_frame": gl(v, fl), "global_s": round(gl(v, fl) / FPS, 3),
                                   "beak_in_leaf_mask": info["beak_in_leaf"], "beak_stage_px": info.get("beak_stage"),
                                   "label": "measured"}
        assert gl(v, E4L) - gl(v, E3L) == 8
        out, info = version_frame(v, E6END)
        assert info["bird_px_visible"] == 0, f"{v}: bird visible past the jamb at E6 end: {info}"
        seq = []
        for fl in range(204, 241, 4):
            seq.append(version_frame(v, fl)[1]["bird_px_visible"])
        man["checks"]["E6_end"] = {"global_frame": gl(v, E6END), "bird_px_visible": 0,
                                   "visible_px_f204_to_f240_step4": seq, "label": "measured on the composite"}
        man["checks"]["strike_poses_E3_window"] = {
            "keys_f138_f156": [(TRACK09B[f - 120]["key"] if v == "V2" else TRACK20B[f - 120]["key"] if v == "V3"
                                else KP.TRACK[f - 120].get("key")) for f in range(138, 157)],
            "label": "pose keys per frame (>=3 distinct joint configurations within 1 s of E3)"}
        if v == "V1":
            man["checks"]["V1A_bird_px_behind_iron_f0_f119_step8"] = [
                {"f": f, **{k_: version_frame("V1", f)[1].get(k_) for k_ in ("bird_px_total", "bird_px_behind_iron", "bird_height_frac")}}
                for f in range(0, 120, 8)]
        if v in ("V1", "V2", "V3"):
            fa = 60
            man["checks"]["shot_A_f60"] = version_frame(v, fa)[1]
        if v == "V3":
            ox = BEAT["versions"]["V3"]["counterexample"]["local_frame"]
            o, ix = version_frame("V3", ox)
            o2, ix2 = version_frame("V3", ox + 3)
            man["checks"]["X1"] = {"peck_frame": ix, "plus3": ix2, "door_slide_at_X1": ix["slide"],
                                   "label": "measured: one dot, refused, door shut"}
            man["checks"]["V3A_watcher_shadow_height_frac_f96"] = version_frame("V3", 96)[1]["watcher_shadow_height_frac"]
        led["versions"][v] = man
    for e in ("E1", "E2", "E3", "E4", "E5", "E6", "E7"):
        loc = [led["versions"][v]["events"][e]["global_frame"] for v in ("V1", "V2", "V3", "D")]
        loc0 = [x - int(round(OFFS[v] * FPS)) if isinstance(x, int) else [y - int(round(OFFS[v] * FPS)) for y in x]
                for x, v in zip(loc, ("V1", "V2", "V3", "D"))]
        assert all(l == loc0[0] for l in loc0), e
    led["assertions"] = {"E3_E4_global_frames": {v: [gl(v, E3L), gl(v, E4L)] for v in OFFS},
                         "E3_E4_global_s": {v: [round(gl(v, E3L) / FPS, 3), round(gl(v, E4L) / FPS, 3)] for v in OFFS},
                         "all_versions_share_local_event_frames": True, "beak_in_leaf_on_E3_E4": True,
                         "zero_bird_px_past_jamb_at_E6_end": True}
    comps = {}
    for v, ts, ref, name in (("V1", 9.0, "orchard3.webp", "compare-1959.jpg"), ("V2", 25.0, "orchardAK08.webp", "compare-2009.jpg"),
                             ("V3", 41.0, "orchardAK17.webp", "compare-2059.jpg")):
        fimg = film.frame(int(round(ts * FPS)))
        fs = stats(np.asarray(fimg))
        rs = stats(np.asarray(Image.open(REFS / ref).convert("RGB")))
        compare_sheet(fimg, ref, f"film {ts:.1f} s ({v})", fs, rs, SW / name)
        comps[name] = {"film_frame_s": ts, "film": fs, "reference": ref, "reference_stats": rs}
    for v, ts in (("V3A", 39.0), ("V1A", 5.5), ("V2A", 22.0)):
        comps[f"extra_{v}_{ts}"] = stats(np.asarray(film.frame(int(round(ts * FPS)))))
    led["compare"] = comps
    json.dump(led, open(SW / "ledger.json", "w"), indent=1, default=lambda o: o if not isinstance(o, np.generic) else o.item())
    print(json.dumps(led["assertions"], indent=1))
    for k, c in comps.items():
        print(k, c.get("film", c))
    return led


film = kit.Film("a-morning-stroll", seconds=SECONDS, boil=0)
film.picture(picture)
film.sound(sound)
film.poster_at = 9.0

if __name__ == "__main__":
    if "--report" in sys.argv:
        report(film)
    else:
        film.render()
