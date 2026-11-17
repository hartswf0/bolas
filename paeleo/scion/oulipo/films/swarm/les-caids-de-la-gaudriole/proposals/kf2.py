"""KF2 - LA TABLE LUMINEUSE: the fold filmed top-down on an animator's light box.

The same printed strip on thin paper, lit from below. When folded, each sheet
point X of the folded panel stacks real layers: for X < A the front facet
(sheet x = X), the tucked facet (sheet x = 2A - X, mirrored) and the lower
facet (sheet x = X + D). Light through n paper layers falls as T**n and the
ink of deeper layers is diffused by the paper above it, so hidden ink shows as
soft onion-skin ghosts: recoverable, never added. Fold A sits on mark B.
"""
import math, os, sys
import numpy as np
import cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strip as S

OUT = os.path.join(S.HERE, "kf-2.png")
W, H = 1280, 720
T = 0.62           # light transmission of one paper layer
INK_T = 0.06       # transmission of a pen/print line


def fibre(w, h):
    p = Image.open(os.path.join(S.SRC, "paper.jpg")).convert("L").resize((w, int(w * 1630 / 1280)))
    a = np.asarray(p.crop((0, 0, w, h)), np.float32)
    a = (a - a.mean()) / (a.std() + 1e-6)
    return np.clip(1 + 0.035 * a, 0.85, 1.15)


def main():
    r = S.build()
    sh = 1 - np.asarray(r["sheet"], np.float32) / 255.0     # ink coverage 0..1
    A, B, D = S.A, S.B, S.D
    Wf = (A - 0) + (S.SW - B)                                  # folded strip width (x 0..A, then B..)
    X = np.arange(Wf)
    # transmission per layer for each folded column
    front = np.zeros((S.SH, Wf), np.float32)
    mid = np.zeros_like(front)
    low = np.zeros_like(front)
    nl = np.ones(Wf, np.float32)
    left = X < A
    front[:, left] = sh[:, X[left]]
    u2 = 2 * A - X[left]
    mid[:, left] = sh[:, u2]                  # mirrored: the tucked facet lies face down
    u3 = X[left] + D
    low[:, left] = sh[:, u3]
    nl[left] = 3
    front[:, ~left] = sh[:, X[~left] + D]
    # the paper above a layer diffuses its ink: blur grows with depth
    mid = cv2.GaussianBlur(mid, (0, 0), 3.5)
    low = cv2.GaussianBlur(low, (0, 0), 7.0)
    trans = (1 - front * (1 - INK_T)) * (1 - mid * (1 - INK_T)) * (1 - low * (1 - INK_T))
    paper_layers = T ** nl[None, :]
    fib = fibre(Wf, S.SH)
    # the stand mixes a top light (reflected, front layer only) with the box light (transmitted)
    KTOP = 0.62
    refl = (1 - front * 0.94) * fib * 0.80
    back = trans * paper_layers / T * fib
    lum = KTOP * refl + (1 - KTOP) * back
    # the strip's outline: the right part of the sheet beyond 2360 + margins already blank paper

    # light box: frosted glass glow under the paper, falloff to the corners
    scale = 0.70
    sw, shh = int(Wf * scale), int(S.SH * scale)
    lum_s = cv2.resize(lum, (sw, shh), interpolation=cv2.INTER_AREA)
    yy, xx = np.mgrid[0:H, 0:W]
    glow = 1.0 - 0.38 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
    base = 265 * glow                                         # bare glass, slightly blown out
    img = base.copy()
    ox, oy = (W - sw) // 2 + 6, (H - shh) // 2 + 8
    # strip sits on the glass
    img[oy:oy + shh, ox:ox + sw] = base[oy:oy + shh, ox:ox + sw] * lum_s * 1.55
    # the light box frame (black) beyond the glass
    frame = np.zeros((H, W), np.float32)
    cv2.rectangle(frame, (18, 14), (W - 19, H - 15), 1.0, -1)
    frame = cv2.GaussianBlur(frame, (0, 0), 3)
    img = img * frame + 14 * (1 - frame)
    # a peg bar along the top edge, as on an animation light box (drawn)
    cv2.rectangle(img, (W // 2 - 190, 22), (W // 2 + 190, 44), 40, -1)
    for px in (W // 2 - 140, W // 2, W // 2 + 140):
        cv2.ellipse(img, (px, 34), (14 if px == W // 2 else 8, 7), 0, 0, 360, 120, -1)
    # warm cast of a tungsten light box; monochrome otherwise
    img = np.clip(img, 0, 255)
    rgb = np.stack([img * 1.0, img * 0.965, img * 0.88], -1)
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
