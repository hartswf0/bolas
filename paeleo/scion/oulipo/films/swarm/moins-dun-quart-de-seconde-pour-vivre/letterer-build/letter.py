"""Writer-letterer unit, full build: balloon plane + page lettering.

Handmade only. Balloons are drawn with hand.py's dab-chain brush; letters are
written in hand2.py's loose single-stroke capitals in real pen order. Every
balloon is an RGBA layer, 540x540, transparent outside the balloon. Each has a
frame-exact write-on schedule (outline strokes over 8 frames, then glyph
strokes), a #38-style boil decoded by DP while (and only while) it is being
written, and a final state that is the published PNG byte for byte.

Run:  python3 -I letter.py            (writes media + balloons.json)
"""
import hashlib
import itertools
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw
from hand import brush, catmull, wobble, length, resample
from hand2 import layout

SLUG = 'moins-dun-quart-de-seconde-pour-vivre'
ROOT = '/home/user/bolas/paeleo/scion/oulipo'
SWARM = f'{ROOT}/films/swarm/{SLUG}'
SRC = f'{ROOT}/films/sources/{SLUG}'
MEDIA = f'{SRC}/letterer'
EDIT = f'{SRC}/writer-letterer'
DELIV = f'{SWARM}/deliverables/balloons'

FPS = 24
K = 2                      # render at 1080, reduce once to 540
P = 540
INK_V = 19                 # #131313, inside the #121212-#151515 band (same as the plate)
PAPER_V = 255
OUTLINE_F = 8              # outline strokes over 8 frames
LETTER_RATE = 9.0          # letters per second (alphanumerics), lifts included
WORD_LIFT = 2.0            # frames, pen lift between words and between lines
SMALL_LIFT = 0.4           # frames, pen lift between strokes inside a word
MIN_HOLD_S = 2.0

# panel slot lengths (s) from plan.json shots, used to keep the >=2 s hold
SLOT_S = {'A1': 5.0, 'A2': 5.4, 'A4': 4.4, 'B1': 5.5, 'B2': 3.5, 'B3': 4.5, 'B4': 7.0}
HOLD_REQ_S = {'A4': 2.5, 'B2': 2.0, 'B4': 3.0}

# ------------------------------------------------------------- plate geometry
# Fallback geometry = the approved test-shot plate (plate2.py boxes, 540 px).
# If the plate artist has published plate.json / safe-mask.png, those win.
GEOM = dict(
    eye=(190, 180, 300, 285), flap=(175, 375, 340, 455), lamp=(18, 30, 112, 128),
    snout_tip=(480, 268), ear=(145, 180, 222, 340), head_top=185,
    source='fallback: test-shot plate2.py geometry (plate.json not yet published)')


def load_plate_geom():
    """Read the plate artist's plate.json (frozen) and safe-mask.png; fall back to
    the approved test-shot geometry only if they are missing."""
    global INK_V, PAPER_V
    pj = f'{SWARM}/plate.json'
    mask, plate_sha, plate_path, plate_file_sha = None, None, None, None
    if os.path.exists(pj):
        d = json.load(open(pj))
        pl, fr = d['plate'], d['framing']
        plate_path = os.path.join(ROOT, pl['file'])
        plate_sha, plate_file_sha = pl['sha256_pixels'], pl['sha256_file']
        INK_V = int(pl['ink'][1:3], 16)
        PAPER_V = int(pl['paper'][1:3], 16)
        ex, ey = fr['eye_centre_px']
        GEOM['eye'] = (ex - 50, ey - 50, ex + 50, ey + 48)
        fl = np.array(fr['envelope_flap_px'])
        GEOM['flap'] = (int(fl[:, 0].min()), int(fl[:, 1].min()), int(fl[:, 0].max()) + 1, int(fl[:, 1].max()) + 1)
        GEOM['lamp'] = tuple(fr['lamp_globe_bbox_px'])
        GEOM['snout_tip'] = tuple(fr['snout_tip_px'])
        GEOM['head_top'] = fr['head_top_px']
        GEOM['ear'] = (140, 190, 225, 345)       # read off plate-540.png (ear also excluded in safe-mask)
        GEOM['tail_targets'] = fr['tail_targets_px']
        GEOM['source'] = f'plate.json ({pl["plate_id"]})'
        mp = os.path.join(ROOT, d['safe_mask']['file'])
        m = Image.open(mp).convert('L')
        assert m.size == (P, P)
        mask = np.asarray(m) > 127
        GEOM['mask'] = mp
    else:
        plate_path = f'{SRC}/test-shot/plate-540.png'
    return mask, plate_sha, plate_path, plate_file_sha


# ------------------------------------------------------------- the lines
# (lines, centre (540 px), cap size, tail aim point, seed, emphasised words)
SPECS = {
    'A1': (["IF I OPEN IT,", "I'LL KNOW."], (322, 88), 21, (432, 242), 301, {'KNOW'}),
    'A2': (["IF I DON'T,", "I CAN STILL", "HOPE."], (300, 98), 21, (432, 242), 302, {'HOPE'}),
    'A4': (["HOPE IT IS,", "THEN."], (372, 84), 20, (432, 242), 304, set()),
    'B1': (["ME? I'VE BEEN", "ON THIS BENCH", "SINCE NINE."], (300, 100), 21, (432, 242), 311, {'ME'}),
    'B2': (["ASK THE LAMP."], (376, 84), 22, (432, 242), 312, {'LAMP'}),
    'B3': (["AND LOOK -", "STILL SEALED."], (330, 92), 21, (432, 242), 323, {'SEALED'}),
    'B4': (["WHY WOULD I", "OPEN SOMEONE", "ELSE'S?"], (300, 100), 21, (432, 242), 314, {"ELSE'S"}),
}
PEN_HOLD = {'B4': ("OPEN SOMEONE", 10)}   # 10-frame pen hold after 'SOMEONE'

# branches: alternates kept, never merged
BRANCH_SPECS = {
    'branch-a': {
        'A1': (["IT'S HER", "WRITING."], (330, 86), 21, (432, 242), 401, {'HER'}),
        'A2': (["SHE ONLY WRITES", "TO SAY", "GOODBYE."], (300, 98), 21, (432, 242), 402, {'GOODBYE'}),
        'A4': (["NICE NIGHT."], (392, 82), 21, (432, 242), 404, set()),
    },
    'branch-b': {
        'B4': (["WHO SAID", "ANYTHING ABOUT", "A LETTER?"], (300, 100), 21, (432, 242), 414, {'LETTER'}),
    },
}


# ------------------------------------------------------------- balloon geometry
def balloon_contour(cx, cy, rw, rh, rng, n=11, expo=2.4):
    """Irregular, flattened hand balloon (superellipse-ish), as a closed polyline."""
    ctrl = []
    a0 = rng.uniform(0, 2 * math.pi)
    for i in range(n):
        a = a0 + 2 * math.pi * i / n + rng.normal(0, 0.06)
        c, s = math.cos(a), math.sin(a)
        r = (abs(c) ** expo + abs(s) ** expo) ** (-1 / expo)
        k = rng.uniform(0.95, 1.05)
        ctrl.append((cx + rw * r * k * c, cy + rh * r * k * s))
    pts = catmull(ctrl, 16, closed=True)
    pts = wobble(pts, 1.4 * K, rng, 4)            # ragged, bitten hand edge
    return [tuple(map(float, p)) for p in pts]


def split_for_tail(contour, cx, cy, aim, base_half=9.0 * K, stub=24.0 * K):
    """Open the contour where the stub tail leaves it. Returns (open contour
    starting just after the tail base and ending just before it, tail stroke
    (base_a -> tip -> base_b), tip)."""
    C = np.array(contour)
    d = np.array(aim) - np.array((cx, cy))
    ang = math.atan2(d[1], d[0])
    angs = np.arctan2(C[:, 1] - cy, C[:, 0] - cx)
    # exit point: the contour point nearest the aim (the snout), biased to the aim's side
    dist = np.linalg.norm(C - np.array(aim), axis=1) + 0.25 * np.abs(np.angle(np.exp(1j * (angs - ang)))) * 40 * K
    i = int(np.argmin(dist))
    n = len(C)
    # walk along the contour by arc length to find base points either side
    def walk(i, step, dist):
        acc, j = 0.0, i
        while acc < dist:
            k = (j + step) % n
            acc += float(np.linalg.norm(C[k] - C[j]))
            j = k
        return j
    ia, ib = walk(i, -1, base_half), walk(i, 1, base_half)
    base_mid = (C[ia] + C[ib]) / 2
    u = np.array(aim) - base_mid
    u = u / (np.linalg.norm(u) + 1e-9)
    tip = base_mid + u * stub
    # open contour from ib around to ia
    idx = [(ib + k) % n for k in range(((ia - ib) % n) + 1)]
    open_c = [tuple(C[k]) for k in idx]
    # tail: slightly bowed sides
    perp = np.array((-u[1], u[0]))
    mA = (C[ia] + tip) / 2 + perp * 1.2 * K
    mB = (C[ib] + tip) / 2 + perp * 1.2 * K
    tail = [tuple(C[ia]), tuple(mA), tuple(tip), tuple(mB), tuple(C[ib])]
    tail = [tuple(map(float, p)) for p in catmull(tail, 5)]
    return open_c, tail, tuple(map(float, tip))


class Balloon:
    def __init__(self, key, spec, pen_hold=None):
        self.key = key
        lines, (cx, cy), size, aim, seed, emph = spec
        self.lines, self.seed, self.emph = lines, seed, sorted(emph)
        self.cap = size
        S = size * K
        glyphs, (tw, th) = layout(lines, S, seed, emph=emph)
        rng = np.random.default_rng(seed + 7)
        rw = tw / 2 + S * 1.3
        rh = th / 2 + S * 1.1
        CX, CY = cx * K, cy * K
        contour = balloon_contour(CX, CY, rw, rh, rng)
        aimK = (aim[0] * K, aim[1] * K)
        self.contour = contour
        self.open_c, self.tail, tip = split_for_tail(contour, CX, CY, aimK)
        self.tip = (tip[0] / K, tip[1] / K)
        self.centre = (CX, CY)
        cc = np.array(contour)
        bx, by = (cc[:, 0].min() + cc[:, 0].max()) / 2, (cc[:, 1].min() + cc[:, 1].max()) / 2
        ox, oy = bx - tw / 2, by - th / 2      # centre the writing in the drawn balloon
        self.glyphs = []
        for g in glyphs:
            g = dict(g)
            g['strokes'] = [[(x + ox, y + oy) for x, y in s] for s in g['strokes']]
            self.glyphs.append(g)
        self.pen_hold_spec = pen_hold
        self.stroke_w = 3.8 * K
        self.outline_w = 5.2 * K
        self._schedule()
        self.variants = [self._variant(v) for v in range(3)]
        self.path = self._decode()

    # ------------------------------------------------------------ schedule
    def _schedule(self):
        letters = sum(1 for g in self.glyphs if g['ch'].isalnum())
        D = round(letters * FPS / LETTER_RATE)
        slot = SLOT_S.get(self.key)
        if slot:
            hold = HOLD_REQ_S.get(self.key, MIN_HOLD_S)
            ph = self.pen_hold_spec[1] if self.pen_hold_spec else 0
            D = min(D, int(slot * FPS) - OUTLINE_F - ph - int(round(hold * FPS)))
        self.write_frames = D
        # gaps between consecutive glyph strokes
        items = []          # (glyph index, stroke index)
        for gi, g in enumerate(self.glyphs):
            for si in range(len(g['strokes'])):
                items.append((gi, si))
        gaps = []
        hold_after = None
        for (ga, sa), (gb, sb) in zip(items, items[1:]):
            A, B = self.glyphs[ga], self.glyphs[gb]
            if A['line'] != B['line']:
                if self.pen_hold_spec and self.lines[A['line']] == self.pen_hold_spec[0]:
                    gaps.append(('penhold', float(self.pen_hold_spec[1])))
                else:
                    gaps.append(('line', WORD_LIFT))
            elif A['word'] != B['word']:
                gaps.append(('word', WORD_LIFT))
            else:
                gaps.append(('small', SMALL_LIFT))
        fixed = sum(v for k, v in gaps if k != 'penhold')
        ink_total = D - fixed
        lens = [max(1.0, length(self.glyphs[g]['strokes'][s])) for g, s in items]
        wts = [L ** 0.75 for L in lens]
        assert ink_total > 0.5 * len(items), (self.key, D, fixed, len(items))
        t = float(OUTLINE_F)
        sched = []
        for n, ((gi, si), w) in enumerate(zip(items, wts)):
            d = ink_total * w / sum(wts)
            sched.append(dict(g=gi, s=si, t0=t, t1=t + d))
            t += d
            if n < len(gaps):
                kind, v = gaps[n]
                if kind == 'penhold':
                    self.pen_hold = (t, t + v)
                t += v
        if not self.pen_hold_spec:
            self.pen_hold = None
        self.sched = sched
        self.items = items
        self.end_t = t
        self.end_f = int(math.ceil(t - 1e-6)) - 1          # first frame showing the finished balloon
        # outline: stroke 1 contour 0 -> 4.5, 2-frame lift, tail stub 6.5 -> 8.0
        self.outline_sched = [dict(kind='outline', t0=0.0, t1=4.5), dict(kind='tail', t0=6.5, t1=8.0)]

    # ------------------------------------------------------------ boil variants
    def _variant(self, v):
        if v == 0:
            return self.open_c, self.tail, self.glyphs
        rng = np.random.default_rng(1000 * v + self.seed)
        oc = wobble(self.open_c, 1.2 * K, rng, 5)
        oc[0], oc[-1] = self.open_c[0], self.open_c[-1]
        tl = list(self.tail)
        gl = []
        for g in self.glyphs:
            dx, dy = rng.normal(0, 0.45 * K, 2)
            g2 = dict(g)
            g2['strokes'] = [[(x + dx, y + dy) for x, y in s] for s in g['strokes']]
            gl.append(g2)
        return oc, tl, gl

    def _decode(self):
        """#38 DP over boil drawings per writing frame: min hold 2 frames,
        flicker cost, frozen during the pen hold, last frame = v0 (canonical)."""
        n = self.end_f + 1
        frozen = set()
        if self.pen_hold:
            a, b = self.pen_hold
            frozen = set(range(int(math.ceil(a)), int(math.floor(b))))
        INF = 1e9

        def unary(f, v):
            if f >= self.end_f:
                return 0.0 if v == 0 else INF
            return 0.0 if v else 0.4
        best = {(0, v, 1): unary(0, v) for v in range(3)}
        back = {}
        for f in range(1, n):
            nb = {}
            for (ff, v, h), c in best.items():
                for w in range(3):
                    if w != v and (h < 2 or f in frozen):
                        continue
                    if w == v:
                        nh, tc = min(h + 1, 3), (0.6 if (h >= 2 and f not in frozen) else 0.0)
                    else:
                        nh, tc = 1, 0.1
                    cost = c + tc + unary(f, w)
                    key = (f, w, nh)
                    if cost < nb.get(key, INF):
                        nb[key] = cost
                        back[key] = (ff, v, h)
            best = nb
        k = min(best, key=lambda q: best[q])
        path = []
        while True:
            path.append(k[1])
            if k[0] == 0:
                break
            k = back[k]
        path = path[::-1]
        assert len(path) == n and path[-1] == 0
        runs = [len(list(g)) for _, g in itertools.groupby(path)]
        assert min(runs[:-1] or [2]) >= 2, runs
        return path

    # ------------------------------------------------------------ render
    def _draw(self, t, v):
        oc, tl, gl = self.variants[v]
        W = P * K
        C = Image.new('L', (W, W), PAPER_V)
        A = Image.new('L', (W, W), 0)
        dc, da = ImageDraw.Draw(C), ImageDraw.Draw(A)
        # outline stroke 1: contour, the white fill fans in behind the pen
        o = self.outline_sched[0]
        u = min(1.0, max(0.0, (t - o['t0']) / (o['t1'] - o['t0'])))
        if u > 0:
            m = max(2, int(round(len(oc) * u)))
            poly = list(oc[:m]) if u < 1 else list(oc)   # white laid along the pen path, closed by the chord
            if len(poly) >= 3:
                dc.polygon(poly, fill=PAPER_V)
                da.polygon(poly, fill=255)
            for img, col in ((dc, INK_V), (da, 255)):
                rng = np.random.default_rng(self.seed + 17)
                brush(img, oc, self.outline_w, rng, col=col, taper=(0.04, 0.06), press=0.32, upto=u)
        o = self.outline_sched[1]
        u = min(1.0, max(0.0, (t - o['t0']) / (o['t1'] - o['t0'])))
        if u > 0:
            m = max(2, int(round(len(tl) * u)))
            poly = list(tl[:m]) if u < 1 else list(tl)
            if len(poly) >= 3:
                dc.polygon(poly, fill=PAPER_V)
                da.polygon(poly, fill=255)
            for img, col in ((dc, INK_V), (da, 255)):
                rng = np.random.default_rng(self.seed + 19)
                brush(img, tl, self.outline_w * 0.8, rng, col=col, taper=(0.0, 0.0), press=0.2, upto=u)
        for n, sc in enumerate(self.sched):
            if t <= sc['t0']:
                break
            u = min(1.0, (t - sc['t0']) / max(1e-6, sc['t1'] - sc['t0']))
            u = u * u * (3 - 2 * u)
            g = gl[sc['g']]
            s = g['strokes'][sc['s']]
            rng = np.random.default_rng(31 * n + self.seed)
            brush(dc, s, self.stroke_w * g['widths'][sc['s']], rng, col=INK_V,
                  taper=(0.12, 0.22), press=0.2, upto=u)
        return C, A

    def _reduce(self, C, A):
        c = np.asarray(C, np.float64)
        a = np.asarray(A, np.float64) / 255.0
        pm = Image.fromarray((c * a).astype(np.float32), 'F').resize((P, P), Image.LANCZOS)
        aa = Image.fromarray(a.astype(np.float32), 'F').resize((P, P), Image.LANCZOS)
        pm = np.asarray(pm, np.float64)
        aa = np.clip(np.asarray(aa, np.float64), 0, 1)
        col = np.where(aa > 1e-4, pm / np.maximum(aa, 1e-4), PAPER_V)
        col = np.clip(np.round(col), INK_V, PAPER_V).astype(np.uint8)
        al = np.clip(np.round(aa * 255), 0, 255).astype(np.uint8)
        al[al < 3] = 0
        rgba = np.dstack([col, col, col, al])
        rgba[al == 0, :3] = 0
        return rgba

    def final(self):
        if not hasattr(self, '_final'):
            self._final = self._reduce(*self._draw(self.end_t + 1, 0))
        return self._final

    def frame(self, f):
        """RGBA uint8 (540x540x4) at frame f from panel start; frame f shows the
        state at t = f+1 frames. f >= end_f returns the published PNG array."""
        if f >= self.end_f:
            return self.final()
        if f < 0:
            return np.zeros((P, P, 4), np.uint8)
        return self._reduce(*self._draw(f + 1.0, self.path[f]))

    # ------------------------------------------------------------ ledger
    def ledger(self):
        def pts(s):
            return [[round(x / K, 1), round(y / K, 1)] for x, y in s]

        def fr(t0, t1):
            return dict(t0_f=round(t0, 3), t1_f=round(t1, 3), on_frame=int(math.floor(t0)),
                        done_frame=int(math.ceil(t1)) - 1)
        strokes = [dict(idx=0, kind='outline', path=pts(self.open_c), **fr(0.0, 4.5), width_px=5.2),
                   dict(idx=1, kind='tail-stub', path=pts(self.tail), **fr(6.5, 8.0), width_px=4.2)]
        for n, sc in enumerate(self.sched):
            g = self.glyphs[sc['g']]
            s = g['strokes'][sc['s']]
            strokes.append(dict(idx=n + 2, kind='glyph', ch=g['ch'], glyph_index=sc['g'],
                                stroke_in_glyph=sc['s'], line=g['line'], word=g['word'],
                                path=pts(s), length_px=round(length(s) / K, 1),
                                width_px=round(3.8 * g['widths'][sc['s']], 2), **fr(sc['t0'], sc['t1'])))
        return strokes


def composite(art_l, rgba):
    """Reference composite (L art 540 + RGBA balloon): integer, exact."""
    a = rgba[..., 3].astype(np.int32)
    c = rgba[..., 0].astype(np.int32)
    p = np.asarray(art_l, np.int32)
    out = (p * (255 - a) + c * a + 127) // 255
    return Image.fromarray(out.astype(np.uint8), 'L')


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def coverage(alpha, box):
    x0, y0, x1, y1 = [int(v) for v in box]
    return float((alpha[y0:y1, x0:x1] > 0).mean())


def check_place(b, mask):
    al = b.final()[..., 3]
    rep = dict(eye=coverage(al, GEOM['eye']), flap=coverage(al, GEOM['flap']),
               lamp=coverage(al, GEOM['lamp']))
    ex0, ey0, ex1, ey1 = GEOM['ear']
    tail = np.array(b.tail) / K
    rep['tail_crosses_ear'] = bool(((tail[:, 0] >= ex0) & (tail[:, 0] <= ex1) &
                                    (tail[:, 1] >= ey0) & (tail[:, 1] <= ey1)).any())
    rep['tail_tip'] = [round(v, 1) for v in b.tip]
    rep['tip_above_head_px'] = round(GEOM['head_top'] - b.tip[1], 1)
    ys, xs = np.nonzero(al)
    rep['bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    rep['within_panel_border'] = bool(xs.min() >= 12 and ys.min() >= 12 and xs.max() <= P - 13)
    if mask is not None:
        rep['outside_safe_mask_px'] = int(((al > 0) & ~mask).sum())
    rep['ok'] = (rep['eye'] == 0 and rep['flap'] == 0 and rep['lamp'] == 0 and not rep['tail_crosses_ear']
                 and rep['within_panel_border'] and rep.get('outside_safe_mask_px', 0) == 0)
    return rep


# ------------------------------------------------------------- page lettering
PAGE_ITEMS = {
    # key: (text, x, y(top), cap size, seed, stroke px, anchor)
    'header': ("ONE PLATE, TWO STRIPS", 106, 76, 54, 3, 6.0, 'left', {'TWO'}),
    'header-right': ("AFTER MENU & TRONDHEIM, 1991", 2374, 102, 26, 4, 3.6, 'right', set()),
    'label-A': ("A — TO WAIT", 106, 220, 36, 5, 4.4, 'left', {'A'}),
    'label-B': ("B — THE ALIBI", 106, 920, 36, 6, 4.4, 'left', {'B'}),
    'footer': (None, 106, 1630, 24, 8, 3.4, 'left', set()),
}


def page_item(key, text, x, y, size, seed, w, anchor, emph):
    glyphs, (tw, th) = layout([text], size * K, seed, emph=emph, loose=0.8)
    pad = int(size * 0.6) * K
    Wd, Ht = int(tw) + 2 * pad, int(th) + 2 * pad
    C = Image.new('L', (Wd, Ht), PAPER_V)
    A = Image.new('L', (Wd, Ht), 0)
    dc, da = ImageDraw.Draw(C), ImageDraw.Draw(A)
    strokes = []
    n = 0
    letters = sum(1 for g in glyphs if g['ch'].isalnum())
    tot = sum(max(1.0, length(s)) ** 0.75 for g in glyphs for s in g['strokes'])
    D = letters * FPS / LETTER_RATE
    t = 0.0
    for gi, g in enumerate(glyphs):
        for si, s in enumerate(g['strokes']):
            s2 = [(px + pad, py + pad) for px, py in s]
            for img, col in ((dc, INK_V), (da, 255)):
                rng = np.random.default_rng(seed * 97 + n)
                brush(img, s2, w * K * g['widths'][si], rng, col=col, taper=(0.12, 0.22), press=0.2)
            d = 0.75 * D * max(1.0, length(s)) ** 0.75 / tot
            strokes.append(dict(idx=n, ch=g['ch'], path=[[round(px / K, 1), round(py / K, 1)] for px, py in s2],
                                t0_f=round(t, 3), t1_f=round(t + d, 3)))
            t += d + (0.25 * D / max(1, sum(len(gg['strokes']) for gg in glyphs)))
            n += 1
    c = np.asarray(C.resize((Wd // K, Ht // K), Image.LANCZOS), np.float64)
    a = np.asarray(A.resize((Wd // K, Ht // K), Image.LANCZOS), np.float64)
    c = np.clip(np.round(c), INK_V, PAPER_V).astype(np.uint8)
    a = np.clip(np.round(a), 0, 255).astype(np.uint8)
    a[a < 3] = 0
    rgba = np.dstack([c, c, c, a])
    rgba[a == 0, :3] = 0
    wpx = Wd // K
    px = x - pad // K if anchor == 'left' else x - wpx + pad // K
    return rgba, (int(px), int(y - pad // K)), strokes, t


# ------------------------------------------------------------- outputs
def main():
    mask, plate_sha, plate_path, plate_file_sha = load_plate_geom()
    for d in (MEDIA, EDIT, DELIV, f'{MEDIA}/branch-a', f'{MEDIA}/branch-b'):
        os.makedirs(d, exist_ok=True)
    plate = Image.open(plate_path).convert('L') if plate_path else Image.new('L', (P, P), INK_V)
    if plate_sha is None and plate_path:
        plate_sha = sha(plate_path)

    out = dict(slug=SLUG, unit='writer-letterer', generated='2026-11-17',
               code=[f'{HERE}/letter.py', f'{HERE}/hand2.py', f'{HERE}/hand.py'],
               plate_used_for_checks=dict(path=plate_path, sha256_pixels=plate_sha, sha256_file=plate_file_sha, ink_value=INK_V, paper_value=PAPER_V, geometry_source=GEOM['source'],
                                          safe_mask=GEOM.get('mask')),
               geometry=dict((k, v) for k, v in GEOM.items() if k not in ('source', 'mask')),
               conventions=dict(
                   fps=FPS, panel_px=P, render='drawn at 1080 px (2x), reduced once to 540 px (Lanczos, premultiplied)',
                   frame_time='frame f (from panel start) shows the state at t=f+1 frames; stroke visible from on_frame, complete at done_frame',
                   outline='stroke 0 contour t 0-4.5 f, 2-frame pen lift, stroke 1 tail stub t 6.5-8.0 f: outline complete at frame 7, letters start at t=8',
                   pen_rate=f'{LETTER_RATE} letters/s (alphanumerics), punctuation and lifts inside that budget; capped so the required post-balloon hold fits the plan.json panel slot',
                   lifts=f'{WORD_LIFT:.0f}-frame pen lift between words and between lines; {SMALL_LIFT} frame between strokes inside a word (see amendments.md: a literal 2-frame lift between every stroke cannot meet 9 glyphs/s)',
                   boil='#38 DP over 3 hand variants (v0 canonical + 2 redraws), min hold 2 frames, flicker cost, frozen through the B4 pen hold; only while writing; frame >= end_frame is exactly the PNG',
                   composite='out = (art*(255-a) + c*a + 127)//255 on L; colour channels R=G=B; balloon ink and paper values taken from plate.json (see plate_used_for_checks)',
                   placement_rule='never cover eye, flap, lamp globe; tails short stubs aimed at the snout; no tail crosses the ear box'),
               panels={}, beats=[], branches={}, page_lettering={}, foraged=[], handmade=[], absences=[])

    def build(key, spec, folder, label):
        b = Balloon(key, spec, PEN_HOLD.get(key) if label == 'main' else None)
        rgba = b.final()
        pth = f'{folder}/{key}.png'
        Image.fromarray(rgba, 'RGBA').save(pth, optimize=False)
        # proof: last scheduled frame equals the PNG exactly
        re = np.asarray(Image.open(pth))
        last = b.frame(b.end_f)
        assert np.array_equal(re, last), key
        # proof: one frame before the end is not yet final (the pen is still writing)
        pre = b._reduce(*b._draw(b.end_f, 0))
        rep = check_place(b, mask)
        hold_f = int(SLOT_S[key] * FPS) - (b.end_f + 1) if key in SLOT_S else None
        rec = dict(strings=b.lines, text=' / '.join(b.lines), file=pth, sha256=sha(pth),
                   size=[P, P], mode='RGBA', centre=list(spec[1]), cap_px=spec[2], tail_aim=list(spec[3]),
                   tail_tip=rep['tail_tip'], seed=spec[4], emphasis=b.emph, bbox=rep['bbox'],
                   placement=rep, end_frame=b.end_f, write_frames=b.write_frames,
                   letters=sum(1 for g in b.glyphs if g['ch'].isalnum()),
                   effective_letter_rate=round(sum(1 for g in b.glyphs if g['ch'].isalnum()) / (b.write_frames / FPS), 2),
                   pen_hold=(dict(after='SOMEONE', t0_f=round(b.pen_hold[0], 3), t1_f=round(b.pen_hold[1], 3),
                                  frames=PEN_HOLD[key][1], on_frame=int(math.ceil(b.pen_hold[0])),
                                  off_frame=int(math.floor(b.pen_hold[1])) - 1) if b.pen_hold else None),
                   slot_s=SLOT_S.get(key), hold_after_write_frames=hold_f,
                   hold_after_write_s=(round(hold_f / FPS, 3) if hold_f is not None else None),
                   boil_path=''.join(str(v) for v in b.path),
                   final_equals_png=True, penultimate_differs=bool(not np.array_equal(pre, last)),
                   strokes=b.ledger())
        return b, rec

    balloons = {}
    for key, spec in SPECS.items():
        b, rec = build(key, spec, MEDIA, 'main')
        balloons[key] = b
        out['panels'][key] = rec
        print(key, 'end_f', b.end_f, 'hold', rec['hold_after_write_s'], 'rate', rec['effective_letter_rate'],
              'ok', rec['placement']['ok'], rec['placement']['bbox'])
    out['panels']['A3'] = dict(silence=True, strings=[], file=None, duration_s=4.4,
                               sound='ambience only: no scratch, no tap, no music',
                               note='declared Silence beat; no balloon layer; black above the head stays empty; lamp fully visible')

    for br, specs in BRANCH_SPECS.items():
        out['branches'][br] = {}
        for key, spec in specs.items():
            b, rec = build(key, spec, f'{MEDIA}/{br}', 'branch')
            rec.pop('strokes')
            rec['status'] = 'alternate, not merged; same plate, same placement rules'
            out['branches'][br][key] = rec

    # page lettering
    foot = "THE ART LAYER IS IDENTICAL IN ALL EIGHT PANELS · SHA256 " + (plate_sha or '?' * 12)[:12].upper()
    for key, (text, x, y, size, seed, w, anchor, emph) in PAGE_ITEMS.items():
        text = text or foot
        rgba, pos, strokes, dur = page_item(key, text, x, y, size, seed, w, anchor, emph)
        pth = f'{MEDIA}/page-{key}.png'
        Image.fromarray(rgba, 'RGBA').save(pth)
        out['page_lettering'][key] = dict(text=text, file=pth, sha256=sha(pth), page_xy=list(pos),
                                          size=list(rgba.shape[1::-1]), cap_px=size, stroke_px=w,
                                          natural_write_frames=round(dur, 2),
                                          note=('footer carries the sha256 prefix of the plate used for this run; re-run letter.py once plate.json is final'
                                                if key == 'footer' else 'S1 writes header and labels in ~0.8 s: scale t0_f/t1_f by 19/natural_write_frames'),
                                          strokes=strokes)

    # beats (DialogueBeat ledger)
    out['beats'] = BEATS
    out['writers_room'] = WRITERS_ROOM
    out['handmade'] = [
        dict(item='balloon layers A1 A2 A4 B1 B2 B3 B4 (RGBA 540x540)', made_how='brush outline (hand.py dab chains) + loose single-stroke pen capitals (hand2.py) in pen order', where=MEDIA),
        dict(item='branch balloons branch-a A1 A2 A4, branch-b B4', made_how='same hand and brush', where=f'{MEDIA}/branch-a, {MEDIA}/branch-b'),
        dict(item='page header, header-right, strip labels, footer (RGBA at page scale)', made_how='same pen hand, larger', where=MEDIA),
        dict(item='editor previews: lettered strips over the current plate, write-on contact sheet, B-strip write-on test clip', made_how='composited from the layers above over the plate (art untouched)', where=EDIT)]
    out['foraged'] = []
    out['absences'] = ['No foraged material is used by this unit (lettering and balloons are handmade); nothing was downloaded.']

    # previews for the editor (art never written: we only read the plate)
    previews(balloons, plate, out)
    for k in list(out['panels']):
        if out['panels'][k].get('file'):
            import shutil
            shutil.copy(out['panels'][k]['file'], f'{DELIV}/{k}.png')
            shutil.copy(out['panels'][k]['file'], f'{EDIT}/{k}.png')
    for k, v in out['page_lettering'].items():
        import shutil
        shutil.copy(v['file'], f'{EDIT}/page-{k}.png')
    json.dump(out, open(f'{SWARM}/balloons.json', 'w'), indent=1, ensure_ascii=False)
    slim = json.loads(json.dumps(out))
    for k, v in slim['panels'].items():
        if v.get('file'):
            v['file'] = f'{DELIV}/{k}.png'
    json.dump(slim, open(f'{DELIV}/balloons.json', 'w'), indent=1, ensure_ascii=False)
    print('wrote', f'{SWARM}/balloons.json')


def previews(balloons, plate, out):
    order = {'A': ['A1', 'A2', None, 'A4'], 'B': ['B1', 'B2', 'B3', 'B4']}
    for row, keys in order.items():
        strip = Image.new('L', (4 * P + 3 * 36, P), PAPER_V)
        for i, k in enumerate(keys):
            pan = composite(plate, balloons[k].final()) if k else plate.copy()
            strip.paste(pan, (i * (P + 36), 0))
        strip.save(f'{EDIT}/preview-strip-{row}.png')
    # write-on contact sheet for B4 (pen hold visible) and B1
    for key in ('B1', 'B4'):
        b = balloons[key]
        fs = list(range(0, b.end_f + 1, max(1, (b.end_f + 1) // 11)))[:11] + [b.end_f]
        if b.pen_hold:
            fs[5] = int(math.ceil(b.pen_hold[0])) + 4
            fs = sorted(set(fs))
        sheet = Image.new('L', (len(fs) * 272, 272 + 30), PAPER_V)
        for i, f in enumerate(fs):
            fr = composite(plate, b.frame(f)).crop((0, 0, P, P)).resize((270, 270), Image.LANCZOS)
            sheet.paste(fr, (i * 272, 0))
        sheet.save(f'{EDIT}/contact-writeon-{key}.png')
    # B-strip write-on test clip (1:1 panel, balloons written over the plate), for the editor to look at
    import subprocess
    tmp = f'{EDIT}/_frames'
    os.makedirs(tmp, exist_ok=True)
    for fn in os.listdir(tmp):
        os.remove(os.path.join(tmp, fn))
    n = 0
    for key in ('B1', 'B2', 'B3', 'B4'):
        b = balloons[key]
        L = int(SLOT_S[key] * FPS)
        for f in range(L):
            composite(plate, b.frame(f)).save(f'{tmp}/{n:05d}.png')
            n += 1
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{tmp}/%05d.png',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', f'{EDIT}/preview-B-writeon.mp4'], check=True)
    for fn in os.listdir(tmp):
        os.remove(os.path.join(tmp, fn))
    os.rmdir(tmp)


BEATS = [
    dict(panel='A1', kind='DialogueBeat', speaker='creature', addressee='itself (thinking aloud)',
         line="IF I OPEN IT, / I'LL KNOW.", intention='name the stakes: opening the envelope ends uncertainty',
         transition='listener learns the envelope matters and that knowing is feared, not wanted'),
    dict(panel='A2', kind='DialogueBeat', speaker='creature', addressee='itself',
         line="IF I DON'T, / I CAN STILL / HOPE.", intention='argue for the other branch: not opening keeps hope alive',
         transition='the sideways eye now reads as longing over the letter; the reader expects a choice'),
    dict(panel='A3', kind='Silence', speaker='creature', addressee='itself', line=None, duration_s=4.4,
         intention='withhold; decide without saying',
         transition='nothing is said and nothing moves: the reader supplies the decision; the silence is the choice being made'),
    dict(panel='A4', kind='DialogueBeat', speaker='creature', addressee='itself',
         line='HOPE IT IS, / THEN.', intention='settle, deflated: choose not knowing',
         transition='the unchanged half-lidded eye now reads as resignation; the letter will stay shut'),
    dict(panel='B1', kind='DialogueBeat', speaker='creature', addressee='unseen questioner (off panel)',
         line="ME? I'VE BEEN / ON THIS BENCH / SINCE NINE.", intention='deflect an accusation with a time alibi',
         transition='reader infers an off-panel accuser and a crime; the same pose becomes a witness stand'),
    dict(panel='B2', kind='DialogueBeat', speaker='creature', addressee='unseen questioner',
         line='ASK THE LAMP.', intention='cite the picture itself as witness (the lamp, uncovered top-left)',
         transition='reader looks at the lamp; the drawing is now evidence, and the joke is that a lamp cannot testify'),
    dict(panel='B3', kind='DialogueBeat', speaker='creature', addressee='unseen questioner',
         line='AND LOOK - / STILL SEALED.', intention='offer the sealed flap as proof of innocence',
         transition='reader checks the flap (uncovered) and half-accepts the alibi'),
    dict(panel='B4', kind='DialogueBeat', speaker='creature', addressee='unseen questioner',
         line="WHY WOULD I / OPEN SOMEONE / ELSE'S?", intention='protest innocence once too often',
         pen_hold='10 frames after SOMEONE',
         transition="volunteers that the envelope is not its own: the alibi collapses; the identical sideways eye now reads as guilt (not 'continue': the meaning of the eye flips)"),
]

WRITERS_ROOM = {
    'A': {
        'arc-1 (chosen)': ["IF I OPEN IT, / I'LL KNOW.", "IF I DON'T, / I CAN STILL / HOPE.", '(silent)', 'HOPE IT IS, / THEN.'],
        'arc-2 (branch-a, kept, lettered)': ["IT'S HER / WRITING.", 'SHE ONLY WRITES / TO SAY / GOODBYE.', '(silent)', 'NICE NIGHT.'],
        'judgement': 'arc-1 keeps the reference shape (dilemma, dilemma, silence, deflating short line) and makes the silence the decision itself. arc-2 is stronger as story (a reason to fear the letter) but its last line changes the subject rather than resolving the dilemma, and it gives the envelope a sender, which would pre-empt strip B\'s "someone else\'s". Kept as branch-a.',
    },
    'B': {
        'arc-1 (chosen; B1-B3 locked)': ["ME? I'VE BEEN / ON THIS BENCH / SINCE NINE.", 'ASK THE LAMP.', 'AND LOOK - / STILL SEALED.', "WHY WOULD I / OPEN SOMEONE / ELSE'S?"],
        'arc-2 (branch-b, kept, B4 lettered)': ["ME? I'VE BEEN / ON THIS BENCH / SINCE NINE.", 'ASK THE LAMP.', 'AND LOOK - / STILL SEALED.', 'WHO SAID / ANYTHING ABOUT / A LETTER?'],
        'arc-3 (drafted, not lettered)': ['WHAT BAG?', 'I ONLY FOUND / THIS.', 'ON THE BENCH. / HONEST.', 'ASK THE LAMP.'],
        'judgement': "arc-1's B4 turns the alibi into a confession through ownership: the reader re-reads the eye as guilt. branch-b B4 (over-denial) is funny but the accuser never mentioned a letter only if we assume so; it is less sure to flip the eye. arc-3 spends the lamp too late and loses the hinge.",
    },
}

def load_balloons():
    """Editor entry point: {key: Balloon} with plate ink/paper loaded.
    b.frame(f) -> RGBA uint8 for frame f from panel start; b.end_f; b.final()."""
    load_plate_geom()
    return {k: Balloon(k, spec, PEN_HOLD.get(k)) for k, spec in SPECS.items()}


if __name__ == '__main__':
    main()
