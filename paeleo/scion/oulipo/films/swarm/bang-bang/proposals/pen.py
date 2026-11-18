# Handmade pen toolkit for the bang-bang proposals: jittered ink strokes and a stroke-built French hand.
# Everything here draws; nothing is traced from the reference.
import math
import numpy as np, cv2
from PIL import Image

SS = 2  # supersample factor for ink


def paper(w, h, seed, tone=(242, 236, 220)):
    """Cream laid paper: low-frequency mottling, fibre speckle, a soft vignette."""
    r = np.random.default_rng(seed)
    lo = cv2.resize(r.normal(0, 1, (h // 40 + 2, w // 40 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    mid = cv2.resize(r.normal(0, 1, (h // 6 + 2, w // 6 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    fib = cv2.GaussianBlur(r.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.7)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    vig = 1 - 0.05 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    k = (1 + 0.018 * lo + 0.008 * mid + 0.012 * fib) * vig
    a = np.stack([np.full((h, w), c, np.float32) for c in tone], -1) * k[..., None]
    return np.clip(a, 0, 255)


class Ink:
    """A supersampled ink layer (coverage 0..1) composited onto paper at the end."""

    def __init__(self, w, h, seed):
        self.w, self.h = w, h
        self.a = np.zeros((h * SS, w * SS), np.float32)
        self.r = np.random.default_rng(seed)

    def line(self, pts, width=2.0, jit=1.2, press=0.25, step=3.0, dash=None):
        """pts in page px. Resample, wobble with low-freq noise, vary width like a nib."""
        p = np.asarray(pts, np.float32)
        if len(p) < 2:
            return
        seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        L = seg[-1]
        n = max(2, int(L / step))
        t = np.linspace(0, L, n)
        q = np.stack([np.interp(t, seg, p[:, 0]), np.interp(t, seg, p[:, 1])], 1)
        k = max(2, n // 6 + 2)
        nz = self.r.normal(0, jit, (k, 2)).astype(np.float32)
        nz = np.stack([np.interp(np.linspace(0, k - 1, n), np.arange(k), nz[:, i]) for i in range(2)], 1)
        q = q + nz + self.r.normal(0, jit * 0.15, q.shape)
        wv = width * (1 + press * np.sin(np.linspace(0, math.pi, n)) - 0.15 * press + self.r.normal(0, 0.06, n))
        for i in range(n - 1):
            if dash and (int(t[i] / dash) % 2):
                continue
            a = tuple(int(v * SS * 8) for v in q[i]); b = tuple(int(v * SS * 8) for v in q[i + 1])
            cv2.line(self.a, a, b, 1.0, max(1, int(round(wv[i] * SS))), cv2.LINE_AA, shift=3)

    def curve(self, ctrl, **kw):
        """Catmull-Rom through control points."""
        c = np.asarray(ctrl, np.float32)
        c = np.vstack([c[0], c, c[-1]])
        out = []
        for i in range(1, len(c) - 2):
            p0, p1, p2, p3 = c[i - 1], c[i], c[i + 1], c[i + 2]
            for s in np.linspace(0, 1, 12, endpoint=False):
                s2, s3 = s * s, s * s * s
                out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s2 + (-p0 + 3 * p1 - 3 * p2 + p3) * s3))
        out.append(c[-2])
        self.line(out, **kw)

    def ellipse(self, cx, cy, rx, ry, rot=0, a0=0, a1=360, **kw):
        t = np.radians(np.linspace(a0, a1, 48))
        ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        x, y = rx * np.cos(t), ry * np.sin(t)
        self.line(np.stack([cx + x * ca - y * sa, cy + x * sa + y * ca], 1), **kw)

    def dot(self, x, y, r):
        cv2.circle(self.a, (int(x * SS * 8), int(y * SS * 8)), int(r * SS * 8), 1.0, -1, cv2.LINE_AA, shift=3)

    def hatch(self, poly, ang=45, gap=6, width=1.0):
        """Loose pen hatching clipped to a polygon."""
        m = np.zeros((self.h, self.w), np.uint8)
        cv2.fillPoly(m, [np.asarray(poly, np.int32)], 255)
        ys, xs = np.nonzero(m)
        if not len(xs):
            return
        cx, cy = xs.mean(), ys.mean(); R = max(xs.ptp(), ys.ptp())
        d = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))]); nrm = np.array([-d[1], d[0]])
        for o in np.arange(-R, R, gap):
            pts = []
            for s in np.linspace(-R, R, int(2 * R / 2)):
                x, y = cx + d[0] * s + nrm[0] * o, cy + d[1] * s + nrm[1] * o
                ok = 0 <= int(x) < self.w and 0 <= int(y) < self.h and m[int(y), int(x)]
                if ok:
                    pts.append((x, y))
                elif len(pts) > 2:
                    self.line(pts, width=width, jit=0.5, press=0.1); pts = []
                else:
                    pts = []
            if len(pts) > 2:
                self.line(pts, width=width, jit=0.5, press=0.1)

    def coverage(self):
        a = cv2.resize(self.a, (self.w, self.h), interpolation=cv2.INTER_AREA)
        return np.clip(a, 0, 1)


def put_ink(page, cov, ink=(28, 26, 34), bleed=0.6, seed=0):
    r = np.random.default_rng(seed)
    c = cv2.GaussianBlur(cov, (0, 0), bleed) * 0.25 + cov * 0.75
    grain = 1 - 0.18 * np.clip(cv2.GaussianBlur(r.random(cov.shape).astype(np.float32), (0, 0), 0.6), 0, 1)
    c = np.clip(c * grain * 1.08, 0, 1)[..., None]
    return page * (1 - c) + np.asarray(ink, np.float32) * c


# ------------------------------------------------------------------ the hand (Hershey script strokes, re-set word by word)
ACC = {"é": ("e", "acute"), "è": ("e", "grave"), "ê": ("e", "circ"), "à": ("a", "grave"), "â": ("a", "circ"),
       "ç": ("c", "ced"), "ô": ("o", "circ"), "î": ("i", "circ"), "ù": ("u", "grave"), "û": ("u", "circ"),
       "’": ("'", None), "«": ("<", None), "»": (">", None), "…": ("...", None)}
FONT = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX


def _word_img(word, scale, thick):
    base = "".join(ACC.get(ch, (ch, None))[0] for ch in word)
    (tw, th), bl = cv2.getTextSize(base, FONT, scale, thick)
    W, H = tw + 40, th + bl + 60
    m = np.zeros((H, W), np.uint8)
    org = (20, th + 30)
    cv2.putText(m, base, org, FONT, scale, 255, thick, cv2.LINE_AA)
    # accents: find the x of each accented glyph from the width of its prefix
    pre = ""
    for ch in word:
        b, acc = ACC.get(ch, (ch, None))
        if acc:
            x0 = cv2.getTextSize(pre, FONT, scale, thick)[0][0] if pre else 0
            gw = cv2.getTextSize(b, FONT, scale, thick)[0][0]
            cx = org[0] + x0 + gw * 0.55; top = org[1] - th * 0.52
            s = scale * 9
            if acc == "acute":
                cv2.line(m, (int(cx - s * .3), int(top)), (int(cx + s * .5), int(top - s * .9)), 255, thick, cv2.LINE_AA)
            elif acc == "grave":
                cv2.line(m, (int(cx + s * .3), int(top)), (int(cx - s * .5), int(top - s * .9)), 255, thick, cv2.LINE_AA)
            elif acc == "circ":
                cv2.polylines(m, [np.int32([(cx - s * .5, top), (cx, top - s * .8), (cx + s * .5, top)])], False, 255, thick, cv2.LINE_AA)
            elif acc == "ced":
                cv2.ellipse(m, (int(cx - s * .1), int(org[1] + s * .5)), (int(s * .35), int(s * .45)), 0, -90, 120, 255, thick, cv2.LINE_AA)
        pre += b
    return m, org[1], tw


def hand(ink_layer, text, x, y, size=1.0, width=2, rng=None, line_h=None, maxw=None, upto=None):
    """Write `text` on an Ink layer (page px) starting at x,y baseline.  Each word gets its own slant, size and
    baseline drift, as a pen does.  `upto` (0..1) writes on only the first fraction of characters (the
    write-on used for cue sync); returns (x_end, y_end) of the pen."""
    rng = rng or np.random.default_rng(1)
    scale = 1.25 * size * SS
    thick = 1
    line_h = line_h or 46 * size
    words = text.split(" ")
    total = sum(len(w) + 1 for w in words); budget = total * (upto if upto is not None else 1.0)
    cx, cy = x, y; used = 0
    for wd in words:
        if wd == "":
            cx += 10 * size; continue
        if wd == "\n":
            cx, cy = x, cy + line_h; continue
        if used >= budget:
            break
        part = wd[:max(0, int(budget - used))]; used += len(wd) + 1
        if not part:
            break
        m, base, tw = _word_img(part, scale * rng.uniform(0.95, 1.05), thick)
        ang = rng.normal(0, 1.6)
        M = cv2.getRotationMatrix2D((m.shape[1] / 2, base), ang, 1.0)
        M[0, 1] += math.tan(math.radians(rng.normal(-4, 2)))  # forward slant
        M[0, 2] -= math.tan(math.radians(-4)) * base
        m = cv2.warpAffine(m, M, (m.shape[1] + 20, m.shape[0]), flags=cv2.INTER_LINEAR)
        # the hand is not a typeface: a smooth displacement per word, ~1.5 page px, so no two letters repeat
        H0, W0 = m.shape
        k = (max(2, H0 // 14), max(2, W0 // 14))
        dx = cv2.resize(rng.normal(0, 0.55 * SS, k).astype(np.float32), (W0, H0), interpolation=cv2.INTER_CUBIC)
        dy2 = cv2.resize(rng.normal(0, 0.55 * SS, k).astype(np.float32), (W0, H0), interpolation=cv2.INTER_CUBIC)
        gx, gy = np.meshgrid(np.arange(W0, dtype=np.float32), np.arange(H0, dtype=np.float32))
        m = cv2.remap(m, gx + dx, gy + dy2, cv2.INTER_LINEAR)
        # felt-tip nib: a small slanted ellipse, so verticals and diagonals differ a little in weight
        nb = max(2, int(round(width * SS)))
        ker = np.zeros((nb + 2, nb + 2), np.uint8)
        cv2.ellipse(ker, ((nb + 1) // 2, (nb + 1) // 2), (max(1, nb // 2), max(1, int(nb * 0.35))), 35, 0, 360, 1, -1)
        m = cv2.dilate(m, ker)
        wpx = tw / SS
        if maxw and cx + wpx > x + maxw:
            cx, cy = x, cy + line_h
        dy = rng.normal(0, 1.5)
        X0, Y0 = int((cx - 20 / SS) * SS), int((cy + dy) * SS - base)
        H, W = m.shape
        A = ink_layer.a
        x0, y0 = max(0, X0), max(0, Y0); x1, y1 = min(A.shape[1], X0 + W), min(A.shape[0], Y0 + H)
        if x1 > x0 and y1 > y0:
            sub = m[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0].astype(np.float32) / 255
            A[y0:y1, x0:x1] = np.maximum(A[y0:y1, x0:x1], sub)
        cx += wpx + 14 * size * rng.uniform(0.8, 1.3)
    return cx, cy
