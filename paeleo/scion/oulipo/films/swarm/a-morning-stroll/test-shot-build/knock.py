"""THE KNOCK: test shot (shot B of V1 1959, local 5.0-11.0 s = clip 0.0-6.0 s). Run from anywhere:
    python3 -I knock.py            -> ../test-shot.mp4 (+ stills/ check frames, knock-ledger.json)
    python3 -I knock.py --stills 0.5 1.0 1.04 ...

Plate  : LoC ppmsca.70651 (Rizzuto, July 1959), graded by prep_plate.py; railing holdout + leaf matte (#29, #45).
Puppet : LoC stereo.1s08734 rooster (1870s), GrabCut-cut into 5 pinned pieces by prep_rooster.py; FK chain (#32).
Clip time c = local time - 5.0.  E3 strike1 = frame 24 (local 6.00), E4 strike2 = frame 32 (local 6.333).
"""
import json
import math
import sys
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

OUL = Path("/home/user/bolas/paeleo/scion/oulipo")
sys.path.insert(0, str(OUL / "films"))
import kit  # noqa: E402

SRC = OUL / "films/sources/a-morning-stroll/test-shot"
SWARM = OUL / "films/swarm/a-morning-stroll"
PJ = json.load(open(SRC / "plate/plate.json"))
RJ = json.load(open(SRC / "rooster/rig.json"))
RX0, RY0, RX1, RY1 = PJ["REGION"]
CX0, CY0, CX1, CY1 = PJ["CROP"]
HINGE_X, LEAF_R = PJ["HINGE_X"], PJ["LEAF_R"]
F = 2                     # canvas pixels per plate pixel
FPS, SECONDS = 24, 6.0
E3, E4 = 24, 32           # contact frames

# ------------------------------------------------------------------ plate layers (canvas space)
def up(a, interp=cv2.INTER_CUBIC):
    return cv2.resize(a, ((RX1 - RX0) * F, (RY1 - RY0) * F), interpolation=interp)


plate = np.asarray(Image.open(SRC / "plate/region.png"), np.float32)
iron0 = np.asarray(Image.open(SRC / "plate/iron.png"), np.float32) / 255
leaf0 = (np.asarray(Image.open(SRC / "plate/leaf.png")) > 0).astype(np.uint8)
# leaf texture with the iron in front removed (inpainted from the leaf itself) for the swinging leaf
hole = cv2.dilate((iron0 > 0.3).astype(np.uint8), np.ones((5, 5), np.uint8))
leaf_tex = cv2.inpaint(plate.astype(np.uint8), hole & cv2.dilate(leaf0, np.ones((9, 9), np.uint8)), 7, cv2.INPAINT_TELEA)
PLATE = up(plate)
IRON = up(iron0, cv2.INTER_LINEAR)
LEAF = up(leaf0.astype(np.float32), cv2.INTER_LINEAR)
LEAFTEX = up(leaf_tex.astype(np.float32))
Hc, Wc = PLATE.shape
yy, xx = np.mgrid[0:Hc, 0:Wc]
PX = xx / F + RX0         # plate coords of every canvas pixel
PY = yy / F + RY0
# hall behind the door: real dark interior; a little daylight spills onto the near floor and jamb
HALL = 9 + 22 * np.clip((PY - 520) / 160, 0, 1) * np.clip(1 - (PX - HINGE_X) / 260, 0, 1)
# jamb / stile holdouts for the bird once it is inside (#45)
HOLD_IN = np.maximum(((PX > LEAF_R) | (PX < HINGE_X)).astype(np.float32), IRON)


def rail_c(x):
    return 684.0 - 1.025 * (x - 1560.0)


RAIL_TOP_OFF = 9 * math.hypot(1, 1.025)


def rail_top(x):
    return rail_c(x) - RAIL_TOP_OFF


def P2C(x, y):
    return ((x - RX0) * F, (y - RY0) * F)


# ------------------------------------------------------------------ puppet (FK, #32)
PIECES = {}
for n in ("leg_far", "tail", "body", "leg_near", "head"):
    a = np.asarray(Image.open(SRC / f"rooster/piece_{n}.png"), np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 0.9)    # pre-filter: pieces are reduced ~0.42x in one warp
    PIECES[n] = a
J = RJ["joints"]
Q = 125.0 / RJ["height_px"]                 # rig px -> plate px (bird ~125 plate px tall = 26% of frame)
BEAK = np.array(RJ["beak_tip"], float)
SOLES = {k: np.array(v, float) for k, v in RJ["soles"].items()}


def rot(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s], [s, c]])


def fk(pose):
    """pose: root (x,y plate) at body pin, ang (rad), and joint angles. Returns {piece: 2x3 rig->plate}."""
    Rb = rot(pose["ang"]) * Q
    pb = np.array(J["body"]["pin"], float)
    root = np.array(pose["root"], float)
    M = {}
    def mat(A, t):
        return np.hstack([A, t.reshape(2, 1)])
    M["body"] = mat(Rb, root - Rb @ pb)
    for n in ("head", "tail", "leg_near", "leg_far"):
        pc = np.array(J[n]["pin"], float)
        A = Rb @ rot(pose.get(n, 0.0))
        pin_w = root + Rb @ (pc - pb)
        M[n] = mat(A, pin_w - A @ pc)
    return M


def apply(Mx, p):
    return Mx[:, :2] @ p + Mx[:, 2]


def plant(x_root, ang, lift=0.0):
    """Find root y and leg angles that put both soles on the rail top (feet planted), legs near vertical."""
    best = None
    for dy in np.arange(-160, -40, 1.0):
        root = (x_root, rail_c(x_root) + dy)
        err = 0
        legs = {}
        for leg in ("leg_near", "leg_far"):
            be = None
            for a in np.radians(np.arange(-40, 41, 2)):
                M = fk({"root": root, "ang": ang, leg: a})[leg]
                s = apply(M, SOLES[leg])
                e = abs(s[1] - rail_top(s[0])) + 0.15 * abs(math.degrees(a + ang))
                if be is None or e < be[0]:
                    be = (e, a)
            legs[leg] = be[1]
            err += be[0]
        if best is None or err < best[0]:
            best = (err, root, legs)
    _, root, legs = best
    return {"root": (root[0], root[1] - lift), "ang": ang, **legs}


# ------------------------------------------------------------------ the performance (frame by frame)
ANG = -0.20                                  # body leans nose-up on the 45-degree rail, facing uphill (right)
X_PERCH = 1868.0                             # hip-centre x on the rail at the door
PERCH = plant(X_PERCH, ANG)
_cache = {}


STRIKE = math.radians(22) + 0.20            # 22 deg forward-down of the neck relative to the level body


def head_angle(f):
    """Head piece about the neck pin; + = forward-down (towards the leaf). Strikes on ones, holds on twos."""
    table = {20: -0.16, 21: -0.16, 22: 0.12, 23: 0.12, 24: STRIKE, 25: 0.30, 26: 0.10,
             27: -0.10, 28: -0.10, 29: -0.10, 30: 0.14, 31: 0.14, 32: STRIKE, 33: 0.30, 34: 0.10}
    if f in table:
        return table[f]
    if f < 16:
        return 0.0
    if f < 20:
        return -0.07                          # looks up at the door
    if f < 48:
        return 0.0
    if f < 84:
        return -0.10 if (f // 12) % 2 else -0.05   # waits, small head moves on twos while the door swings
    return 0.0


def pose_at(f):
    if f in _cache:
        return _cache[f]
    g = f - (f % 2)                           # on twos, except the strike frames below
    if E3 - 4 <= f <= E4 + 3:
        g = f
    if g < 16:                                # walk-in: two hops up the handrail, 8 frames each
        hop, k = divmod(g, 8)
        x0 = X_PERCH - 2 * 34 + hop * 34
        ph = k / 8.0
        if k < 2:                             # crouch
            p = plant(x0, ANG, lift=-3)
        elif k < 6:                           # air: arc along the rail, legs tucked back
            u = (k - 1) / 5.0
            x = x0 + 34 * u
            p = plant(x, ANG - 0.06, lift=16 * math.sin(math.pi * u))
            p["leg_near"], p["leg_far"] = 0.35, 0.25
        else:                                 # land
            p = plant(x0 + 34, ANG + 0.04, lift=-2 if k == 6 else 0)
        _ = ph
    elif g < 86:                              # at the door: knock, wait
        p = dict(PERCH)
        if g in (E3, E3 + 1, E4, E4 + 1):    # reaction: body braces back 1 px on contact
            p["root"] = (PERCH["root"][0] - 1.2, PERCH["root"][1])
            p["ang"] = ANG - 0.02
    elif g < 92:                              # crouch before the jump
        p = plant(X_PERCH, ANG + 0.05, lift=-4)
    else:                                     # the jump into the hall: forward, up, then down behind the stile
        u = min(1.0, (g - 92) / 26.0)         # frames 92..118 (clip 3.83..4.92)
        x = X_PERCH + 150 * u
        y = PERCH["root"][1] - 40 * math.sin(math.pi * min(u, 0.5)) + 380 * max(0, u - 0.3) ** 1.6
        p = {"root": (x, y), "ang": ANG + 0.5 * u, "leg_near": 0.5, "leg_far": 0.4, "head": -0.1}
    p.setdefault("head", 0.0)
    if g < 92:
        p["head"] = head_angle(g)
    p["tail"] = 0.06 * math.sin(f / 3.0) if g < 92 else -0.2   # tail: lagged secondary motion
    _cache[f] = p
    return p


def inside(f):
    return f >= 100                           # crosses the threshold plane at the jump's apex (feet above rail)


def depth_scale(f):
    if f < 92:
        return 1.0, 1.0
    u = min(1.0, (f - 92) / 26.0)
    return 1.0 - 0.12 * u, 1.0 - 0.7 * max(0.0, u - 0.25) / 0.75   # smaller and darker: out of the daylight


# ------------------------------------------------------------------ door (hinged leaf, inward, #45)
def door_theta(t):
    if t < 1.75:
        return 0.0
    if t < 2.0:
        return math.radians(1.5) * (t - 1.75) / 0.25            # latch gives
    u = kit.smooth(kit.clamp((t - 2.0) / 1.5))
    return math.radians(1.5 + 76.5 * u)


CAM = np.array([1235.0, 1513.0])            # principal point of the full scan (plate coords)
Z0 = 1500.0                                  # door distance in plate-pixel units


def leaf_quad(th):
    """Image of the leaf rotated th inward about the hinge (perspective)."""
    wl = LEAF_R - HINGE_X
    k = Z0 / (Z0 + wl * math.sin(th))
    top, bot_h, bot_e = RY0 - 40.0, 650.0 - 0.2 * (HINGE_X - 1950), 650.0 - 0.2 * (LEAF_R - 1950)
    xe = CAM[0] + (HINGE_X + wl * math.cos(th) - CAM[0]) * k
    te = CAM[1] + (top - CAM[1]) * k
    be = CAM[1] + (bot_e - CAM[1]) * k
    return np.float32([[HINGE_X, top], [LEAF_R, top], [LEAF_R, bot_e], [HINGE_X, bot_h]]), \
        np.float32([[HINGE_X, top], [xe, te], [xe, be], [HINGE_X, bot_h]])


def door_layer(th):
    src, dst = leaf_quad(th)
    s = np.float32([P2C(*p) for p in src])
    d = np.float32([P2C(*p) for p in dst])
    M = cv2.getPerspectiveTransform(s, d)
    tex = cv2.warpPerspective(LEAFTEX, M, (Wc, Hc), flags=cv2.INTER_LINEAR)
    al = cv2.warpPerspective(LEAF, M, (Wc, Hc), flags=cv2.INTER_LINEAR)
    tex = tex * (1 - 0.55 * math.sin(th))   # turning away from the daylight
    # the leaf's edge (thickness) catches the light as it turns
    edge = np.zeros((Hc, Wc), np.float32)
    if th > 0.05:
        x_e = d[1][0]
        w_e = max(1.0, 9 * F * math.sin(th) * 0.5)
        edge = np.clip(1 - np.abs(xx - (x_e + w_e / 2)) / w_e, 0, 1) * ((yy > d[1][1]) & (yy < d[2][1]))
    return tex, al, edge


# ------------------------------------------------------------------ bird render
def bird_layer(f):
    p = pose_at(f)
    M = fk(p)
    sc, lum = depth_scale(f)
    rgb = np.zeros((Hc, Wc), np.float32)
    al = np.zeros((Hc, Wc), np.float32)
    head_al = np.zeros((Hc, Wc), np.float32)
    C = np.array([[F, 0, -RX0 * F], [0, F, -RY0 * F], [0, 0, 1]], float)
    root = np.array(p["root"])
    S = np.array([[sc, 0, root[0] * (1 - sc)], [0, sc, root[1] * (1 - sc)], [0, 0, 1]])
    for n in ("leg_far", "tail", "body", "leg_near", "head"):
        A = np.vstack([M[n], [0, 0, 1]])
        T = (C @ S @ A)[:2]
        pc = cv2.warpAffine(PIECES[n], T, (Wc, Hc), flags=cv2.INTER_LINEAR)
        a = pc[..., 3] / 255
        rgb = pc[..., 0] * a + rgb * (1 - a)
        al = a + al * (1 - a)
        if n == "head":
            head_al = a
    beak = apply(M["head"], BEAK)
    beak = root + sc * (beak - root)
    return rgb * lum, al, head_al, beak, M


# head distance from the leaf (plate px): rest 7, contact 0 -> cast-shadow offset along the light
def head_gap(f):
    a = head_angle(f) if f < 92 else 0.0
    return max(0.0, 7.0 * (1 - a / STRIKE))


LIGHT = np.array([0.75, 0.45])               # shadow direction per unit gap (light from upper left, front)

# lens vignette (optical fall-off of the 1959 camera), applied once in canvas space
_r = np.hypot((PX - (CX0 + CX1) / 2) / ((CX1 - CX0) / 2), (PY - (CY0 + CY1) / 2) / ((CY1 - CY0) / 2))
VIG = np.clip(1 - 0.55 * np.clip(_r - 0.38, 0, None) ** 1.35, 0.12, 1)
LEDGER = {"frames": {}}


def compose(f):
    t = f / FPS
    th = door_theta(t)
    base = PLATE.copy()
    if th > 0:
        tex, al, edge = door_layer(th)
        base = np.where(LEAF > 0.5, HALL, base)
        base = tex * al + base * (1 - al)
        base = np.maximum(base, edge * 205 * al)
        base = base * (1 - IRON) + PLATE * IRON           # the railing stays in front of door and hall
    rgb, al, head_al, beak, M = bird_layer(f)
    vis_px = 0
    if not inside(f):
        # cast shadow on the door: body 10 px from the leaf, head gap varies (contact => shadow meets beak)
        sh = np.zeros((Hc, Wc), np.float32)
        for a_, gap in ((al - head_al, 10.0), (head_al, head_gap(f))):
            dx, dy = LIGHT * gap * F
            sh = np.maximum(sh, cv2.warpAffine(a_, np.float32([[1, 0, dx], [0, 1, dy]]), (Wc, Hc)))
        sh = cv2.GaussianBlur(sh, (0, 0), 1.1)
        sh *= (1 - IRON) * (PY < rail_top(PX) + 2)       # falls on the door, not on the iron in front
        base = base * (1 - 0.62 * sh)
        # contact shadow on the rail under the feet
        if f < 92:
            for leg in ("leg_near", "leg_far"):
                s = apply(M[leg], SOLES[leg])
                cx, cy = P2C(s[0] - 2, rail_top(s[0] - 2) + 3)
                g = np.exp(-(((xx - cx) / (9 * F)) ** 2 + ((yy - cy) / (2.2 * F)) ** 2))
                base = base * (1 - 0.6 * g)
        out = rgb * al + base * (1 - al)
        vis_px = int((al > 0.5).sum())
    else:
        comp = rgb * al + base * (1 - al)
        out = comp * (1 - HOLD_IN) + base * HOLD_IN
        vis_px = int(((al * (1 - HOLD_IN)) > 0.5).sum())
    out = out * VIG
    # 1.5 % push over the shot, centred on the knock
    z = 1 + 0.015 * t / SECONDS
    cx, cy = 1905.0, 300.0
    w = (CX1 - CX0) / z
    h = w * 9 / 16
    x0 = cx - (cx - CX0) / z
    y0 = cy - (cy - CY0) / z
    a0, b0 = P2C(x0, y0)
    Mz = np.float32([[960 / (w * F), 0, -a0 * 960 / (w * F)], [0, 540 / (h * F), -b0 * 540 / (h * F)]])
    fr = cv2.warpAffine(out.astype(np.float32), Mz, (960, 540), flags=cv2.INTER_AREA)
    # ledger: beak in leaf mask on contact frames; visibility after entry
    bi = (int(round(beak[0])) - RX0, int(round(beak[1])) - RY0)
    in_leaf = bool(leaf0[bi[1], bi[0]]) and iron0[bi[1], bi[0]] < 0.5 if 0 <= bi[0] < leaf0.shape[1] else False
    LEDGER["frames"][f] = {"beak_plate": [round(float(beak[0]), 1), round(float(beak[1]), 1)],
                           "beak_on_leaf": bool(in_leaf), "bird_px_visible": vis_px, "door_deg": round(math.degrees(th), 1),
                           "head_rad": round(pose_at(f)["head"], 3), "inside": inside(f)}
    return np.clip(fr, 0, 255).astype(np.uint8), M


def bone_report():
    """#32 invariant: pivot-to-pivot distances are constant over all frames."""
    pairs = [("body", n) for n in ("head", "tail", "leg_near", "leg_far")]
    rep = {}
    for _, n in pairs:
        d = []
        for f in range(int(SECONDS * FPS)):
            M = fk(pose_at(f))
            sc, _l = depth_scale(f)
            a = apply(M["body"], np.array(J["body"]["pin"], float))
            b = apply(M[n], np.array(J[n]["pin"], float))
            d.append(np.hypot(*(b - a)))   # rig-space FK; the depth scale is a uniform camera-space scale
        rep[n] = round(float(np.ptp(d)), 4)
    return rep


# ------------------------------------------------------------------ sound
def load_mono(path, rate=44100):
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
        return x, w.getframerate()


def pitch(x, semis):
    r = 2 ** (semis / 12)
    n = int(len(x) / r)
    return np.interp(np.arange(n) * r, np.arange(len(x)), x)


def sound(mix):
    rate = mix.rate
    knock, _ = load_mono(SRC / "knock_m.wav")
    on = int(1.337 * rate)
    seg = knock[on - 40: on + int(0.16 * rate)].copy()
    seg *= np.linspace(1, 0, len(seg)) ** 2
    seg = seg - np.convolve(seg, np.ones(40) / 40, "same")          # thin it: a beak, not a knuckle
    seg /= np.abs(seg).max()
    lead = 40
    s1, s2 = pitch(seg, 5), pitch(seg, 8)                             # strike 2 is +3 semitones above strike 1
    mix.add(s1, E3 / FPS - lead / rate / 2 ** (5 / 12), gain=0.55, pan=0.15)
    mix.add(s2, E4 / FPS - lead / rate / 2 ** (8 / 12), gain=0.55, pan=0.15)
    # bed: the optical-track room of a 1941 street film (a pause between lines), looped with crossfades
    amb, _ = load_mono(SRC / "amb_ee12b007.wav")
    bed = amb[int(2.6 * rate): int(4.4 * rate)]
    n = len(bed)
    fade = int(0.3 * rate)
    w = np.ones(n)
    w[:fade] = np.linspace(0, 1, fade)
    w[-fade:] = np.linspace(1, 0, fade)
    at = 0.0
    while at < SECONDS:
        mix.add(bed * w, at, gain=1.6)
        at += (n - fade) / rate
    # handmade: latch, hinge creak, wing flutter, landing inside
    mix.click(1.75, gain=0.25, bright=2500, seconds=0.025)
    mix.click(1.80, gain=0.18, bright=1500, seconds=0.04)
    tt = mix.t(1.4)
    rate_hz = 38 + 26 * np.sin(np.linspace(0, 2.6, len(tt))) + 6 * mix.rs.randn(len(tt)).cumsum() / 200
    ph = np.cumsum(rate_hz / rate)
    puls = np.exp(-((ph % 1.0) * 14))
    creak = mix.band(puls * (0.6 + 0.4 * mix.rs.rand(len(tt))), 500, 2400)
    creak *= np.sin(np.linspace(0, np.pi, len(tt))) ** 0.7
    mix.add(creak / (np.abs(creak).max() + 1e-9), 2.0, gain=0.12, pan=-0.2)
    fl = mix.band(mix.noise(0.45), 300, 3200) * (0.5 + 0.5 * np.sign(np.sin(np.linspace(0, 2 * np.pi * 9, int(0.45 * rate)))))
    fl *= np.hanning(len(fl))
    mix.add(fl / (np.abs(fl).max() + 1e-9), 3.85, gain=0.10, pan=0.3)
    mix.thud(4.75, freq=90, gain=0.10, seconds=0.25, pan=0.35)
    mix.reverb(0.12, 0.6)


# ------------------------------------------------------------------ run
def main():
    args = sys.argv[1:]
    film = kit.Film("test-shot", seconds=SECONDS, boil=0)

    def picture(t, ink):
        f = int(round(t * FPS))
        fr, _ = compose(f)
        ink.paste(Image.fromarray(fr).convert("RGB"))
    film.picture(picture)
    film.sound(sound)
    film.poster_at = E3 / FPS
    if args and args[0] == "--stills":
        out = SWARM / "test-shot-build/stills"
        out.mkdir(exist_ok=True)
        for t in [float(a) for a in args[1:]]:
            film.frame(int(round(t * FPS))).save(out / f"{t:05.2f}.png")
        print("stills ->", out, json.dumps({k: v for k, v in LEDGER["frames"].items()}))
        return
    film.render(out_dir=SWARM)
    LEDGER["bones_ptp_px"] = bone_report()
    LEDGER["events"] = {"E3_strike1": {"frame": E3, "clip_s": E3 / FPS, "local_s": 5 + E3 / FPS},
                        "E4_strike2": {"frame": E4, "clip_s": E4 / FPS, "local_s": 5 + E4 / FPS},
                        "E5_open": {"clip_s": [2.0, 3.5], "local_s": [7.0, 8.5]},
                        "E6_enter": {"clip_s": [3.83, 5.0], "local_s": [8.83, 10.0]}}
    json.dump(LEDGER, open(SWARM / "test-shot-build/knock-ledger.json", "w"), indent=1)
    print("bones", LEDGER["bones_ptp_px"])


if __name__ == "__main__":
    main()
