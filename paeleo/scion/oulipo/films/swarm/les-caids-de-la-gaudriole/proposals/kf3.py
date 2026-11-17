"""KF3 - PHOTO-ROMAN PLIE: archive hands as a two-panel photo strip, and its fold.

Panel 1: Moving Image Archive, 'Key to Our Horizons' (1952), a hand with a
ruffled cuff on a lock knob. Panel 2: 'Bookkeeping and You' (1947), a hand with
a wristwatch. Both frames from the local cineosis-lab cache (movingimagearchive
.com shots, Prelinger-derived). Only translation and uniform scale are applied
(registration), never warping. Lettering and balloons drawn with pen.py.
The folded third panel = P1[0..f] + P2[f..w]: the watch now owns the hand on the lock.
"""
import os, sys, subprocess, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strip as S
from pen import pen, text_width

OUT = os.path.join(S.HERE, "kf-3.png")
CL = "/home/user/hartswf0/cineosis-lab/lab/clips/"
SH1 = ("7102b861-3ff9-5305-a672-ee93edc49815", 9.3)
SH2 = ("af625567-bdef-5658-afe8-1994714524d9", 4.0)
W, H = 1280, 720
PW, PH = 372, 420          # panel size on screen
SCL = PH / 240.0 * 0.92    # uniform scale of the 320x240 frames
FOLD = 0.5                 # fold at the panel's middle (A in P1, B in P2)
CAP = 13


def frame(sid, t, dy=0, dx=0):
    tmp = os.path.join(S.HERE, "_f.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", CL + sid + ".mp4", "-frames:v", "1", tmp], check=True)
    im = Image.open(tmp).convert("L")
    os.remove(tmp)
    im = im.resize((int(320 * SCL), int(240 * SCL)), Image.LANCZOS)
    # panel crop: centred on the frame, plus a registration shift (translation only)
    cx, cy = im.width / 2 + dx, im.height / 2 + dy
    box = (int(cx - PW / 2), int(cy - PH / 2), int(cx - PW / 2) + PW, int(cy - PH / 2) + PH)
    canvas = Image.new("L", (PW, PH), 10)
    canvas.paste(im, (-box[0], -box[1]))
    return canvas


def balloon_lines(d, ox, lines, seed):
    f = int(PW * FOLD)
    x0, x1, y0, y1 = ox + 10, ox + PW - 10, 14, 14 + 3 * CAP * 1.55 + 18
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, fill=(250, 248, 242))
    S.wobble_line(d, S.rr_pts(x0, y0, x1, y1, 22), w=2.5, seed=seed, ink=(18, 18, 18))
    for i, (l, r) in enumerate(lines):
        y = y0 + 12 + i * CAP * 1.55
        if l is not None:
            pen(d, l, ox + f - 4, y, CAP, ink=(18, 18, 18), width=2.2, seed=seed + 10 + i, anchor="r")
        if r is not None:
            pen(d, r, ox + f + 5, y, CAP, ink=(18, 18, 18), width=2.2, seed=seed + 20 + i, anchor="l")
    return y1


def main():
    p1 = frame(*SH1)
    p2 = frame(*SH2, dy=-14, dx=-8)    # registration: the watch-hand's wrist line meets the knob-hand's
    f = int(PW * FOLD)
    p3 = Image.new("L", (PW, PH))
    p3.paste(p1.crop((0, 0, f, PH)), (0, 0))
    p3.paste(p2.crop((f, 0, PW, PH)), (f, 0))
    page = Image.new("RGB", (W, H), (246, 244, 238))
    xs = [34, 34 + PW + 22, W - 34 - PW]
    y0 = 150
    d = ImageDraw.Draw(page)
    for x, p in zip(xs, (p1, p2, p3)):
        g = np.asarray(p, np.float32)
        g = np.clip((g - 18) * 1.12, 0, 255)
        rgb = np.stack([g, g * 0.985, g * 0.95], -1).astype(np.uint8)
        page.paste(Image.fromarray(rgb), (x, y0))
    d = ImageDraw.Draw(page)
    # balloons over the photographs (fumetti): same fragments as the drawn strip
    sub = Image.new("RGB", (W, H)); 
    for k, (x, lines) in enumerate([(xs[0], S.P1_LINES), (xs[1], S.P2_LINES),
                                    (xs[2], [(a[0], b[1]) for a, b in zip(S.P1_LINES, S.P2_LINES)])]):
        lay = Image.new("RGB", (W, H), (0, 0, 0)); m = Image.new("L", (W, H), 0)
        dd = ImageDraw.Draw(page)
        yb = y0 + 0
        f0 = int(PW * FOLD)
        x0, x1, ya, yb2 = x + 12, x + PW - 12, y0 + 12, y0 + 12 + 3 * CAP * 1.55 + 20
        dd.rounded_rectangle([x0, ya, x1, yb2], radius=20, fill=(250, 248, 242))
        S.wobble_line(dd, S.rr_pts(x0, ya, x1, yb2, 20), w=2.6, seed=70 + k, ink=(18, 18, 18))
        tx = x + (70 if k != 1 else 120)
        dd.polygon([(tx - 9, yb2 - 1), (tx + 9, yb2 - 1), (tx + 30, yb2 + 40)], fill=(250, 248, 242))
        S.wobble_line(dd, [(tx - 9, yb2), (tx + 30, yb2 + 40), (tx + 9, yb2)], w=2.6, seed=80 + k, ink=(18, 18, 18))
        for i, (l, r) in enumerate(lines):
            yy = ya + 11 + i * CAP * 1.55
            pen(dd, l, x + f0 - 4, yy, CAP, ink=(18, 18, 18), width=2.3, seed=100 + 10 * k + i, anchor="r")
            pen(dd, r, x + f0 + 5, yy, CAP, ink=(18, 18, 18), width=2.3, seed=200 + 10 * k + i, anchor="l")
    # small balloon in panel 2 and its echo in panel 3 (right half survives the fold)
    for x in (xs[1], xs[2]):
        cx, cy = x + PW - 70, y0 + PH - 70
        cx -= 6
        d.ellipse([cx - 66, cy - 26, cx + 66, cy + 26], fill=(250, 248, 242))
        S.wobble_line(d, [(cx + 66 * math.cos(a / 40 * math.pi * 2), cy + 26 * math.sin(a / 40 * math.pi * 2)) for a in range(41)], w=2.4, seed=5, ink=(18, 18, 18))
        pen(d, "OH? REALLY?", cx, cy - 6, 12, ink=(18, 18, 18), width=2.1, seed=9, anchor="m")
    # panel borders, fold marks, arrow
    for k, x in enumerate(xs):
        S.wobble_line(d, S.rr_pts(x, y0, x + PW, y0 + PH, 3, 2), w=4, seed=30 + k, ink=(14, 14, 14))
    for x, lab in [(xs[0] + f, "A"), (xs[1] + f, "B"), (xs[2] + f, "A|B")]:
        for yy, sg in [(y0 - 16, 1), (y0 + PH + 16, -1)]:
            d.polygon([(x - 7, yy - 7 * sg), (x + 7, yy - 7 * sg), (x, yy + 3 * sg)], fill=(14, 14, 14))
        pen(d, lab, x + 10, y0 - 30, 11, ink=(14, 14, 14), width=1.8, seed=3)
    # dashed fold lines in the margins of the open panels
    for x in (xs[0] + f, xs[1] + f):
        for yy in range(y0 - 8, y0 + PH + 8, 14):
            if yy < y0 or yy > y0 + PH:
                d.line([(x, yy), (x, yy + 6)], fill=(14, 14, 14), width=2)
    ax0, ax1, ay = xs[1] + PW + 14, xs[2] - 14, y0 + PH // 2
    d.polygon([(ax0, ay - 9), (ax1 - 22, ay - 9), (ax1 - 22, ay - 22), (ax1, ay), (ax1 - 22, ay + 22), (ax1 - 22, ay + 9), (ax0, ay + 9)], fill=(14, 14, 14))
    pen(d, "FOLD A ONTO B", 34, 52, 22, ink=(14, 14, 14), width=3.2, seed=11)
    pen(d, "THE SAME TWO FRAMES, HALF OF EACH", 34, 92, 13, ink=(80, 78, 74), width=2, seed=12)
    page.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
