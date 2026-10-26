"""SCION 03 Ernst · cutting the plate: tone + line systems -> ink on paper, with the door's warm light as a hand tint."""
import numpy as np
import burin
import plate

WARM = np.array([246, 214, 150], float) / 255
DUSK = np.array([196, 200, 214], float) / 255
H, W = plate.H, plate.W


def cut_plate(Lr, floor_light, air_light, dusk):
    """Lr: a plate.Layer (static + door).  Returns ink coverage and the paper tint."""
    dark = Lr.dark.copy()
    lit = np.clip(floor_light * Lr.lit, 0, 1)
    dark = np.clip(dark + dusk * 0.18 * (1 - lit) - 0.62 * lit - 0.25 * air_light, 0, 1)
    u = Lr.u
    v = Lr.v
    has_v = ~np.isnan(v)
    v0 = np.where(has_v, v, 0.0)
    c1 = burin.cut(u, dark)
    d2 = np.clip((dark - 0.62) / 0.38, 0, 1) * 0.8
    c2 = burin.cut(v0, d2, lo=0.0) * has_v
    cov = 1 - (1 - c1) * (1 - c2)
    cov = np.maximum(cov, Lr.ink * (1 - 0.5 * lit))
    return cov, np.clip(0.7 * lit + air_light, 0, 0.8)


def paper_tint(warm, dusk):
    base = burin.PAPER[None, None] * (1 - 0.22 * dusk) + DUSK[None, None] * 0.22 * dusk
    w = warm[..., None]
    return base * (1 - w) + (WARM[None, None] * 1.04) * w


def finish(rgb, page_border=True):
    """the page: a paper margin and a ruled plate border."""
    x0, y0, x1, y1 = plate.PLATE
    out = rgb.copy()
    page = burin.PAPER * 0.985
    m = np.ones((H, W), bool); m[y0:y1, x0:x1] = False
    out[m] = page
    ink = burin.INK
    for (a, b, c, d) in ((x0 - 3, y0 - 3, x1 + 3, y0 - 1), (x0 - 3, y1 + 1, x1 + 3, y1 + 3), (x0 - 3, y0 - 3, x0 - 1, y1 + 3), (x1 + 1, y0 - 3, x1 + 3, y1 + 3)):
        out[b:d, a:c] = ink
    return out
