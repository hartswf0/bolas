"""Render Sh1, Sh2a, Sh2b frame by frame (24 fps, 960x408 picture band, true black).

Layers (back to front, SCION #44 multiplane / #45 occlusion DAG):
  0 blue practicals  (handmade gaussian disc + bar), parallax 0.3x of the camera
  1 bare runner      (GrabCut cutout of the photograph, gelled), world plane 1.0x
  2 rings            (GrabCut cutouts, gelled), world plane 1.0x, always in front of the runner (they pass over it in flight)
Motion: flights posed on twos (eased quadratic arcs, staggered starts, rotation <= 10 deg, slight lift scale);
settle on ones (SCION #41 spring-damper, +-4 deg, outward recoil from the gate contact).
usage: python3 render.py [sh1|sh2a|sh2b|all] [--every N]   (frames: global index f, t = f/24)
"""
import sys, json, math
import cv2, numpy as np
from layout import *
from gel import gel

P = OUT / "pieces"
PIECES = {}
WALL = {"bare_runner": 0.42, "runner_with_rings": 0.42}   # declared: runner arms are thin walls (amber); rings are thick discs (wall 1.3, deep red)
def piece(name):
    if name not in PIECES:
        g = gel(cv2.imread(str(P / f"{name}.png"), -1), gain=1.12, wall=WALL.get(name, 1.3))
        # light scattering inside the translucent material (physical sub-surface spread, masked to the part)
        sc = cv2.GaussianBlur(g[..., :3], (0, 0), 3.5)
        g[..., :3] = g[..., :3] + 0.28 * sc * g[..., 3:4]
        PIECES[name] = g
    return PIECES[name]
SRCGEO = json.load(open(OUT / "geom_src.json"))
BBOX = {k: v["bbox_src"] for k, v in SRCGEO["report"]["pieces"].items()}

def place(canvas, g, origin_world, cam, rot_deg=0.0, scale=1.0, pivot_local=None):
    """composite premultiplied RGBA g, whose local (0,0) sits at origin_world, under camera cam (over operator)"""
    c, z = cam
    h, w = g.shape[:2]
    if pivot_local is None: pivot_local = (w / 2, h / 2)
    px, py = pivot_local
    pw = np.array(origin_world) + np.array([px, py])          # pivot in world
    fx, fy = to_film(pw, cam)
    k = z * scale; th = math.radians(rot_deg)
    ca, sa = k * math.cos(th), k * math.sin(th)
    M = np.array([[ca, -sa, fx - ca * px + sa * py], [sa, ca, fy - sa * px - ca * py]], np.float32)
    lay = cv2.warpAffine(g, M, (BW, BH), flags=cv2.INTER_CUBIC if k > 1.0 else cv2.INTER_AREA if k < 0.8 else cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    lay = np.clip(lay, 0, None); lay[..., 3] = np.clip(lay[..., 3], 0, 1)
    canvas *= (1 - lay[..., 3:4]); canvas += lay[..., :3]
    return lay[..., 3]

yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
def practicals(cam):
    """two defocused blue practical lights on their own plane at 0.3x parallax (handmade)"""
    c, z = cam
    dx = -0.3 * (c[0] - CAM_SH2A[0][0]) * z * 0.25; dy = -0.3 * (c[1]) * z * 0.25
    disc = np.exp(-(((xx - (128 + dx)) ** 2 + (yy - (78 + dy)) ** 2) / (2 * 54 ** 2)) ** 2.2)
    bar = np.exp(-((np.clip(np.abs(xx - (700 + dx)) - 160, 0, None) / 34) ** 2 + ((yy - (34 + dy)) / 16) ** 2) ** 1.6)
    c1 = np.array([0.025, 0.14, 0.36], np.float32); c2 = np.array([0.05, 0.15, 0.36], np.float32)
    return 0.78 * disc[..., None] * c1 + 0.72 * bar[..., None] * c2

def smoother(x):
    x = min(max(x, 0.0), 1.0); return x * x * x * (x * (6 * x - 15) + 10)

ZETA, FREQ = 0.35, 3.2
def settle(tau, amp):
    if tau < 0: return 0.0
    w = 2 * math.pi * FREQ; wd = w * math.sqrt(1 - ZETA ** 2)
    return amp / 0.62 * math.exp(-ZETA * w * tau) * math.sin(wd * tau)   # peak ~ amp

def ring_pose(r, t):
    """returns (centre_world, rot_deg, scale)"""
    j = r["flight"]; t0, t1 = FLIGHT[j]
    rest, home, u = r["rest_world"], r["home_world"], r["u"]
    if t < t0:
        rot = 0.0; ctr = rest.copy(); sc = 1.0
        if r["loose_id"] == 1 and t < 2.0:    # Sh1: this ring was just set down at 0.6 s (click on the soundtrack)
            rot = settle(t - 0.6, 2.0); sc = 1.0 + 0.05 * (1 - smoother(t / 0.6)); ctr = ctr + np.array([0, -6.0]) * (1 - smoother(t / 0.6))
        return ctr, rot, sc
    if t < t1:
        tp = math.floor(t * FPS / 2) * 2 / FPS              # posed on twos
        s = smoother((tp - t0) / (t1 - t0))
        chord = home - rest; L = np.linalg.norm(chord)
        up = np.array([0.0, -1.0])
        ctrl = (rest + home) / 2 + up * LIFT[j] * L
        p = (1 - s) ** 2 * rest + 2 * (1 - s) * s * ctrl + s ** 2 * home
        return p, ROT[j] * math.sin(math.pi * s), 1.0 + 0.10 * math.sin(math.pi * s)
    tau = t - t1                                             # settle on ones
    sgn = 1 if j % 2 else -1
    rot = settle(tau, 4.0 * sgn)
    rec = abs(settle(tau, 2.5))                              # outward recoil from the gate (never penetrates)
    return home + u * rec, rot, 1.0

def frame(f):
    t = f / FPS
    cam = camera(t)
    img = practicals(cam).astype(np.float32)
    if t >= T_SH2A:
        bb = BBOX["bare_runner"]
        place(img, piece("bare_runner"), np.array(bb[:2], float) - HUB, cam)
    order = sorted(RINGS, key=lambda r: -r["flight"])     # earlier ring drawn last only matters on overlap; flights rarely overlap
    for r in order:
        e = r["ellipse_src"]; bb = BBOX[r["piece"]]
        pv = (e["cx"] - bb[0], e["cy"] - bb[1])
        ctr, rot, sc = ring_pose(r, t)
        place(img, piece(r["piece"]), ctr - np.array(pv), cam, rot, sc, pivot_local=pv)
    # mild halation of the amber cores (one physical bloom, same in every shot)
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    hot = img * np.clip((lum - 0.45) / 0.3, 0, 1)[..., None]
    img = img + 0.22 * cv2.GaussianBlur(hot, (0, 0), 5) + 0.10 * cv2.GaussianBlur(hot, (0, 0), 16)
    return rolloff(img)

def rolloff(img):
    # shared warm-highlight roll-off (the plan's one unifying grade step): no whites, cores top out near lum 205
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    k = 0.66; tgt = np.where(lum > k, k + 0.15 * np.tanh((lum - k) / 0.15), lum)
    return np.clip(img * (tgt / np.maximum(lum, 1e-4))[..., None], 0, 1)

SHOTS = {"sh1": (0, 206), "sh2a": (207, 312), "sh2b": (313, 422)}
if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    every = int(sys.argv[sys.argv.index("--every") + 1]) if "--every" in sys.argv else 1
    for name, (a, b) in SHOTS.items():
        if which not in ("all", name): continue
        d = OUT / name; d.mkdir(exist_ok=True)
        for f in range(a, b + 1, every):
            im = (frame(f) * 255 + 0.5).astype(np.uint8)
            cv2.imwrite(str(d / f"f{f:04d}.png"), cv2.cvtColor(im, cv2.COLOR_RGB2BGR))
        print(name, a, b)
