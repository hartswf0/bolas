# Editor repair 1: route every hand on the page (slips, headers, labels, margin note, show-through) through the
# handmade joined cursive in cursive.py instead of OpenCV's Hershey Script strokes.  Same call signatures as
# proposals/pen.hand and board-build/board.hand2, so the board unit's code is reused unchanged.
import numpy as np
import cursive as C

FPS = 24
XH = 15.0            # page px of x-height per unit of the old `size`


def pen_hand(ink_layer, text, x, y, size=1.0, width=2, rng=None, line_h=None, maxw=None, upto=None):
    import pen
    rng = rng or np.random.default_rng(1)
    if upto is not None:
        text = text[:int(len(text) * upto)]
    seed = int(rng.integers(0, 1 << 30))
    xh = XH * size
    if xh < 1:
        return x, y
    return C.write(ink_layer.a, pen.SS, text, x, y, xh, max(0.8, width * 0.75), seed, maxw=maxw,
                   line_h=line_h or 3.0 * xh)


def hand2(W, H, text, x, y, size=1.0, width=1.6, seed=0, line_h=None, maxw=None, cps=12.0, t0=0.0):
    """Per-character coverage, written on in order at `cps` from frame t0 (one entry per non-space character)."""
    xh = XH * size
    L, end = C.letters(W, H, text, x, y, xh, max(0.9, width * 0.95), seed, maxw=maxw, line_h=line_h or 3.0 * xh)
    cov = dict(L)
    out = []; tf = t0; step = FPS / cps
    for i, ch in enumerate(text):
        if ch == " ":
            tf += step * 0.6; continue
        c = cov.get(i)
        if c is None:
            c = np.zeros((H, W), np.float32)
        out.append((c, tf, tf + step)); tf += step
    return out, end
