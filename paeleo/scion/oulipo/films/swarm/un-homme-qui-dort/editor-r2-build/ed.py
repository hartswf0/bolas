"""Editor repair-round helpers (r2): monotone print curves, shot writer, stats.
Imports U1's lib (read-only use); writes only under films/sources/un-homme-qui-dort/editor-r2/."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
import kit  # noqa: E402
from lib import *  # noqa: F401,F403,E402

E2 = SRC / "editor-r2"
for sub in ("raw", "rgba", "masks", "failure_masks", "fills", "shots", "json", "diag"):
    (E2 / sub).mkdir(parents=True, exist_ok=True)
BAND = (30, 30, 30)
SHOT_T0 = {"S1": 0.0, "S2": 5.5, "S3": 8.5, "S4": 11.5, "S5": 19.0, "S6": 24.5, "S7": 27.0}
SHOT_N = {"S1": 132, "S2": 72, "S3": 72, "S4": 180, "S5": 132, "S6": 60, "S7": 192}


def pchip(xs, ys):
    """Monotone cubic Hermite (Fritsch-Carlson) through control points; returns f(x) on arrays."""
    xs = np.asarray(xs, np.float64); ys = np.asarray(ys, np.float64)
    assert np.all(np.diff(xs) > 0) and np.all(np.diff(ys) >= 0), "control points not monotone"
    h = np.diff(xs); d = np.diff(ys) / h
    m = np.zeros_like(xs)
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, len(xs) - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        x = np.asarray(x, np.float64)
        xc = np.clip(x, xs[0], xs[-1])
        i = np.clip(np.searchsorted(xs, xc) - 1, 0, len(xs) - 2)
        t = (xc - xs[i]) / h[i]
        h00 = 2 * t ** 3 - 3 * t ** 2 + 1; h10 = t ** 3 - 2 * t ** 2 + t
        h01 = -2 * t ** 3 + 3 * t ** 2; h11 = t ** 3 - t ** 2
        return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]
    return f


def lut(points):
    """8-bit monotone LUT from (in, out) control points (0..255)."""
    xs, ys = zip(*points)
    t = np.clip(np.round(pchip(xs, ys)(np.arange(256))), 0, 255).astype(np.uint8)
    assert np.all(np.diff(t.astype(int)) >= 0), "LUT not monotone"
    return t


def through_kit(g8, fi_pass):
    ink = kit.Ink(fi_pass / FPS, fi_pass, (W, H), boil=0, wobble=0)
    ink.paper(color=BAND, grain=False)
    ink.paste(Image.fromarray(to_rgb(g8), "RGB"))
    return ink.finish()


def write_shot(shot, frames_iter, n=None):
    d = E2 / "shots" / shot
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.png"):
        f.unlink()
    shas = []
    f0 = int(round(SHOT_T0[shot] * FPS))
    prev = None
    for i, g8 in enumerate(frames_iter):
        p = d / f"{shot}_{i:04d}.png"
        if prev is not None and np.array_equal(prev[0], g8):
            os.link(prev[1], p)          # identical frame -> hardlink
        else:
            through_kit(g8, f0 + i).save(p, compress_level=6)
            prev = (g8.copy(), p)
        shas.append(sha1(p))
    assert len(shas) == (n or SHOT_N[shot]), (shot, len(shas))
    return shas, str(d)


import os  # noqa: E402
