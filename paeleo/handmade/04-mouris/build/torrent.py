"""SCION-04 · the torrent engine.

A layer is a mould (an anti-aliased coverage mask), a guide (the colour each place of the mould should read as), a pool
(the subject of the pictures allowed to fill it), an anchor (the grid travels with the thing it builds) and a rate (the
probability per frame that a picture is replaced by another). The mould is filled by a quadtree of archive tiles:
64x48 where the mould is whole and calm, down to 8x6 at edges and shading boundaries. Each placed tile keeps its source
shot and frame, and plays its own shot forward at 12 fps while it is held, so a held picture still lives.
"""
import json, os
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = [(64, 48), (32, 24), (16, 12), (8, 6)]


class Library:
    def __init__(self):
        L = json.load(open(os.path.join(HERE, 'cache/library.json')))
        Z = np.load(os.path.join(HERE, 'cache/library.npz'))
        self.T = {w: Z[f't{w}'] for (w, h) in LEVELS}
        self.shots = L['shots']; self.info = L['tiles']
        self.mean = np.array([t['mean'] for t in self.info], np.float32)
        self.lum = np.array([t['lum'] for t in self.info], np.float32)
        cat_shots = {}
        for s in self.shots:
            key = s['category'] + ('*' if 'kit/' in s['dir'] else '')
            cat_shots.setdefault(s['category'], []).append(s['shot'])
        self.pool_shots = {}
        for p, cats in L['pools'].items():
            ids = []
            for c in cats:
                if c == 'dog-archive': ids += [s['shot'] for s in self.shots if 'kit/archive-dog' in s['dir']]
                elif c == 'door-archive': ids += [s['shot'] for s in self.shots if 'kit/archive-door' in s['dir']]
                else: ids += [s['shot'] for s in self.shots if s['category'] == c and 'kit/' not in s['dir']]
            self.pool_shots[p] = ids
        self.pool_shots['eye'] = [s['shot'] for s in self.shots if s['category'] == 'eye']
        self.pool_shots['hand'] = [s['shot'] for s in self.shots if s['category'] == 'hand']
        self.pool_shots['face'] = [s['shot'] for s in self.shots if s['category'] in ('face', 'eye', 'hat')]
        self.pool_shots['moon'] = [s['shot'] for s in self.shots if s['category'] in ('light-bulb',)]
        self.pool_shots['dogonly'] = [s['shot'] for s in self.shots if 'kit/archive-dog' in s['dir']]
        self.pool_shots['every'] = [s['shot'] for s in self.shots]
        self.usage = {}   # shot -> placements

    def index(self, shot, frame, kind):
        return self.shots[shot]['first_tile'] + 2 * frame + kind

    def choose(self, pool, target, kind, rng, k=5, avoid=None):
        shots = self.pool_shots[pool]
        cand_s = rng.choice(shots, k)
        if avoid is not None and len(shots) > 1:
            cand_s = np.array([s if s != avoid else rng.choice(shots) for s in cand_s])
        cand_f = np.array([rng.integers(self.shots[s]['n']) for s in cand_s])
        idx = np.array([self.index(s, f, kind) for s, f in zip(cand_s, cand_f)])
        tl = float(target @ np.array([.299, .587, .114]))
        sc = np.abs(self.lum[idx] - tl) + 0.08 * np.abs(self.mean[idx] - target).sum(1) + rng.random(k) * 0.22
        j = int(np.argmin(sc))
        s = int(cand_s[j]); self.usage[s] = self.usage.get(s, 0) + 1
        return [s, int(cand_f[j]), kind, 1 if rng.random() < .5 else -1]


class Layer:
    """persistent state of one mould's tiles"""
    def __init__(self, name, pool, kind=0, maxlevel=0, contrast=0.85, keep=0.0, split_std=0.05, minlevel=3):
        self.name, self.pool, self.kind, self.maxlevel, self.contrast, self.keep = name, pool, kind, maxlevel, contrast, keep
        self.split_std, self.minlevel = split_std, minlevel
        self.cells = {}     # (level, r, c) -> [shot, frame, kind, dir, target(3), born]
        self.replaced = 0; self.placed = 0


def coverage_grids(mask, guide, ax, ay):
    """mask HxW float (0..1), guide HxWx3 float; grid origin at (ax, ay) in screen px.
    Returns per level: coverage, mean colour, lum std, and the integer offsets of the padded canvas."""
    H, W = mask.shape
    px = (-ax) % 64; py = (-ay) % 48
    Hp = ((H + py + 47) // 48) * 48; Wp = ((W + px + 63) // 64) * 64
    M = np.zeros((Hp, Wp), np.float32); M[py:py + H, px:px + W] = mask
    G = np.zeros((Hp, Wp, 3), np.float32); G[py:py + H, px:px + W] = guide
    lum = G @ np.array([.299, .587, .114], np.float32)
    w, h = LEVELS[-1]; R, C = Hp // h, Wp // w
    def bs(X): return X.reshape(R, h, C, w, *X.shape[2:]).sum((1, 3))
    S0 = bs(M); SG = bs(G * M[..., None]); SL = bs(lum * M); SL2 = bs(lum * lum * M)
    lv = []
    for k in range(4):
        lv.append((S0, SG, SL, SL2))
        if k < 3:
            def up(X): r, c = X.shape[0] // 2, X.shape[1] // 2; return X.reshape(r, 2, c, 2, *X.shape[2:]).sum((1, 3))
            S0, SG, SL, SL2 = up(S0), up(SG), up(SL), up(SL2)
    out = []
    for k, (w, h) in enumerate(LEVELS):
        S0, SG, SL, SL2 = lv[3 - k]
        cov = S0 / (w * h); ws = S0 + 1e-6
        col = SG / ws[..., None]; l1 = SL / ws; std = np.sqrt(np.maximum(SL2 / ws - l1 * l1, 0))
        out.append((cov, col, std))
    # absolute cell index offset relative to the anchor
    m_x = (px + ax) // 64; m_y = (py + ay) // 48
    return out, px, py, m_x, m_y, Hp, Wp


def render_layer(lib, layer, mask, guide, ax, ay, rate, rng, frame_no, canvas, override=None, advance=2, bbox=None):
    """Fill `mask` with tiles of layer.pool, composite onto canvas (HxWx3 float 0..1). Returns stats.
    override: optional function (level, cx, cy) -> (pool or None, extra_rate) for shock-waves of other pictures.
    """
    H, W = mask.shape
    if bbox is None:
        ys, xs = np.nonzero(mask > 0.01)
        if len(xs) == 0: return dict(cells=0, replaced=0)
        bbox = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - 2); y0 = max(0, y0 - 2); x1 = min(W, x1 + 2); y1 = min(H, y1 + 2)
    sub = mask[y0:y1, x0:x1]; gsub = guide[y0:y1, x0:x1]
    grids, px, py, m_x, m_y, Hp, Wp = coverage_grids(sub, gsub, ax - x0, ay - y0)
    taken = None
    tiles_out = []
    for L in range(layer.maxlevel, 4):
        cov, col, std = grids[L]
        w, h = LEVELS[L]
        if taken is None: taken = np.zeros_like(cov, bool)
        else: taken = np.repeat(np.repeat(taken, 2, 0), 2, 1)[:cov.shape[0], :cov.shape[1]]
        if L < 3:
            use = (cov > 0.999) & (std < layer.split_std) & ~taken
        else:
            use = (cov > 0.003) & ~taken
        taken = taken | use
        rr, cc = np.nonzero(use)
        f = 64 // w
        for r, c in zip(rr, cc):
            tiles_out.append((L, r, c, col[r, c]))
    # paint
    region = np.zeros((Hp, Wp, 3), np.float32)
    replaced = 0
    seen = set()
    k = layer.contrast
    for (L, r, c, target) in tiles_out:
        w, h = LEVELS[L]; f = 64 // w
        key = (L, r - m_y * f, c - m_x * f)
        seen.add(key)
        cy = y0 - py + r * h + h / 2; cx = x0 - px + c * w + w / 2
        pool = layer.pool; extra = 0.0
        if override is not None:
            o = override(L, cx, cy)
            if o is not None: pool, extra = o
        st = layer.cells.get(key)
        rep = st is None or rng.random() < rate + extra or (st[6] != pool) or np.abs(st[4] - target).max() > 0.22
        if rep:
            ch = lib.choose(pool, target, layer.kind, rng, avoid=None if st is None else st[0])
            st = ch + [target.copy(), frame_no, pool]
            layer.cells[key] = st; replaced += 1
        else:
            st[4] = st[4] * 0.8 + target * 0.2
            if advance and (frame_no - st[5]) % advance == 0:   # the held picture plays its own shot forward
                n = lib.shots[st[0]]['n']; nf = st[1] + st[3]
                if nf < 0 or nf >= n: st[3] = -st[3]; nf = st[1] + st[3]
                st[1] = int(min(max(nf, 0), n - 1))
        t = lib.T[w][lib.index(st[0], st[1], st[2])].astype(np.float32) / 255.
        tm = lib.mean[lib.index(st[0], st[1], st[2])]
        tgt = st[4] if not rep else target
        out = (t - tm) * k + tgt
        if layer.keep: out = out * (1 - layer.keep) + t * layer.keep
        region[r * h:(r + 1) * h, c * w:(c + 1) * w] = out
    # drop the state of cells that left the mould
    if len(layer.cells) > 4 * len(seen) + 200:
        layer.cells = {k_: v for k_, v in layer.cells.items() if k_ in seen}
    reg = np.clip(region[py:py + (y1 - y0), px:px + (x1 - x0)], 0, 1)
    a = sub[..., None]
    canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1] * (1 - a) + reg * a
    layer.replaced += replaced; layer.placed += replaced
    return dict(cells=len(tiles_out), replaced=replaced)


def outline(canvas, mask, width=5, color=(0.04, 0.03, 0.06), alpha=0.85, shadow=None):
    """dark rim around a figure so it detaches from the boiling ground"""
    ys, xs = np.nonzero(mask > 0.01)
    if len(xs) == 0: return
    Hh, Ww = mask.shape; p = width
    x0, y0, x1, y1 = max(0, xs.min() - p), max(0, ys.min() - p), min(Ww, xs.max() + p + 1), min(Hh, ys.max() + p + 1)
    sub = mask[y0:y1, x0:x1]
    m = Image.fromarray((np.clip(sub, 0, 1) * 255).astype(np.uint8))
    d = np.asarray(m.filter(ImageFilter.MaxFilter(width)), np.float32) / 255.
    ring = np.clip(d - sub, 0, 1)[..., None] * alpha
    canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1] * (1 - ring) + np.array(color, np.float32) * ring


def render_single(lib, layer, mask, target, rate, rng, frame_no, canvas, advance=2):
    """one found picture cut to the whole mould (a face for a head, a hand for a hand, an eye for an eye)"""
    ys, xs = np.nonzero(mask > 0.01)
    if len(xs) == 0: return dict(cells=0, replaced=0)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    st = layer.cells.get(0); rep = st is None or rng.random() < rate
    target = np.asarray(target, np.float32)
    if rep:
        st = lib.choose(layer.pool, target, layer.kind, rng, avoid=None if st is None else st[0]) + [target, frame_no, layer.pool]
        layer.cells[0] = st; layer.placed += 1
    elif advance and (frame_no - st[5]) % advance == 0:
        n = lib.shots[st[0]]['n']; nf = st[1] + st[3]
        if nf < 0 or nf >= n: st[3] = -st[3]; nf = st[1] + st[3]
        st[1] = int(min(max(nf, 0), n - 1))
    idx = lib.index(st[0], st[1], st[2])
    im = Image.fromarray(lib.T[64][idx]).resize((int(x1 - x0), int(y1 - y0)), Image.BILINEAR)
    tt = np.asarray(im, np.float32) / 255.
    out = (tt - lib.mean[idx]) * layer.contrast + target
    if layer.keep: out = out * (1 - layer.keep) + tt * layer.keep
    a = mask[y0:y1, x0:x1, None]
    canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1] * (1 - a) + np.clip(out, 0, 1) * a
    return dict(cells=1, replaced=int(rep))
