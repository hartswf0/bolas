"""SCION-GRABCUT core: the native formal language, as code.

Typed primitives (kept first-class, never flattened to unexplained pixels):
  Unary   : U_fg[y,x], U_bg[y,x]  cost (nats, scaled to int) of labelling a pixel foreground / background
  Pairwise: W_r[y,x], W_d[y,x]    cost of cutting between (y,x)-(y,x+1) and (y,x)-(y+1,x)  (contrast-sensitive)
  Seeds   : seed[y,x] in {0 unknown, 1 hard fg (scribble/inside box core), 2 hard bg (outside box)}
  Cut     : boolean fg[y,x], the min s-t cut of the 4-connected grid graph (Boykov-Kolmogorov max-flow, below)
  Alpha   : float alpha[y,x] in [0,1] after cleanup (island removal, hole fill, border matting)
Coordinates are source-frame pixels (x right, y down) of the original 384x288 archive frame; every piece keeps its
crop origin so it can be mapped back to the original frame (the original-coordinate transform).

No cv2/scipy: max-flow is a pure-Python BK implementation over flat lists; everything else is numpy.
"""
import numpy as np
from collections import deque

BIG = 10 ** 7


def maxflow_grid(src, snk, wr, wd):
    """Min s-t cut on an HxW 4-connected grid.
    src, snk: int arrays HxW (terminal capacities); wr: HxW cost to the right neighbour (last column ignored);
    wd: HxW cost to the lower neighbour (last row ignored). Returns (bool HxW source-side mask, flow)."""
    H, W = src.shape
    N = H * W
    off = (1, -1, W, -W)
    wr = wr.copy(); wd = wd.copy()
    wr[:, -1] = 0; wd[-1, :] = 0
    # residual capacity from p in direction d (0:+x 1:-x 2:+y 3:-y); edges are symmetric (n-links)
    c0 = wr.ravel().astype(np.int64)
    c1 = np.zeros((H, W), np.int64); c1[:, 1:] = wr[:, :-1]
    c2 = wd.ravel().astype(np.int64)
    c3 = np.zeros((H, W), np.int64); c3[1:, :] = wd[:-1, :]
    cap = [c0.tolist(), c1.ravel().tolist(), c2.tolist(), c3.ravel().tolist()]
    tr_np = (src.astype(np.int64) - snk.astype(np.int64)).ravel()
    flow = int(np.minimum(src, snk).sum())
    tr = tr_np.tolist()
    tree = [0] * N          # 0 free, 1 S, 2 T
    parent = [-2] * N       # -1 terminal root, -2 none/orphan, d>=0 direction to parent
    active = deque()
    for p in np.nonzero(tr_np > 0)[0].tolist():
        tree[p] = 1; parent[p] = -1; active.append(p)
    for p in np.nonzero(tr_np < 0)[0].tolist():
        tree[p] = 2; parent[p] = -1; active.append(p)
    orphans = []
    while True:
        # ---- growth
        found = None
        while active:
            p = active[0]
            t = tree[p]
            if t == 0:
                active.popleft(); continue
            for d in range(4):
                if t == 1:
                    c = cap[d][p]
                    if c <= 0: continue
                    q = p + off[d]
                else:
                    q = p + off[d]
                    if q < 0 or q >= N: continue
                    c = cap[d ^ 1][q]
                    if c <= 0: continue
                tq = tree[q]
                if tq == 0:
                    tree[q] = t; parent[q] = d ^ 1; active.append(q)
                elif tq != t:
                    found = (p, q, d, t); break
            if found: break
            active.popleft()
        if not found:
            break
        p, q, d, t = found
        if t == 1:
            s_node, t_node, ed = p, q, d
        else:
            s_node, t_node, ed = q, p, d ^ 1
        # ---- bottleneck
        c = cap[ed][s_node]
        x = s_node
        while parent[x] != -1:
            d2 = parent[x]; y = x + off[d2]
            v = cap[d2 ^ 1][y]
            if v < c: c = v
            x = y
        if tr[x] < c: c = tr[x]
        x = t_node
        while parent[x] != -1:
            d2 = parent[x]
            v = cap[d2][x]
            if v < c: c = v
            x = x + off[d2]
        if -tr[x] < c: c = -tr[x]
        # ---- augment
        cap[ed][s_node] -= c; cap[ed ^ 1][t_node] += c
        x = s_node
        while parent[x] != -1:
            d2 = parent[x]; y = x + off[d2]
            cap[d2 ^ 1][y] -= c; cap[d2][x] += c
            if cap[d2 ^ 1][y] == 0:
                parent[x] = -2; orphans.append(x)
            x = y
        tr[x] -= c
        if tr[x] == 0:
            parent[x] = -2; orphans.append(x)
        x = t_node
        while parent[x] != -1 and parent[x] != -2:
            d2 = parent[x]; y = x + off[d2]
            cap[d2][x] -= c; cap[d2 ^ 1][y] += c
            if cap[d2][x] == 0:
                parent[x] = -2; orphans.append(x)
            x = y
        if parent[x] == -1:
            tr[x] += c
            if tr[x] == 0:
                parent[x] = -2; orphans.append(x)
        flow += c
        # ---- adoption
        while orphans:
            p = orphans.pop()
            t = tree[p]
            if parent[p] != -2:
                continue
            adopted = False
            for d in range(4):
                q = p + off[d]
                if q < 0 or q >= N or tree[q] != t: continue
                c = cap[d ^ 1][q] if t == 1 else cap[d][p]
                if c <= 0: continue
                x = q
                while parent[x] >= 0:
                    x = x + off[parent[x]]
                if parent[x] == -1:
                    parent[p] = d; adopted = True; break
            if adopted:
                continue
            for d in range(4):
                q = p + off[d]
                if q < 0 or q >= N or tree[q] != t: continue
                c = cap[d ^ 1][q] if t == 1 else cap[d][p]
                if c > 0:
                    active.append(q)
                pq = parent[q]
                if pq >= 0 and q + off[pq] == p:
                    parent[q] = -2; orphans.append(q)
            tree[p] = 0
            parent[p] = -2
    seg = np.array(tree, np.int8).reshape(H, W) == 1
    return seg, flow


# ------------------------------------------------------------------ helpers (numpy only)
def shift(a, dy, dx, fill=0):
    out = np.full_like(a, fill)
    H, W = a.shape[:2]
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    out[yd, xd] = a[ys, xs]
    return out


def dilate(m, r=1):
    m = m.copy()
    for _ in range(r):
        m = m | shift(m, 1, 0) | shift(m, -1, 0) | shift(m, 0, 1) | shift(m, 0, -1)
    return m


def erode(m, r=1):
    return ~dilate(~m, r)


def dist_steps(m, cap=40):
    """city-block distance (in steps, capped) from pixels outside m to m."""
    d = np.full(m.shape, cap, np.int32)
    cur = m.copy(); d[cur] = 0
    for k in range(1, cap):
        nxt = dilate(cur, 1)
        d[nxt & ~cur] = k
        cur = nxt
    return d


def box_blur(a, r=1):
    a = a.astype(np.float32)
    out = np.zeros_like(a); n = 0
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out += np.roll(np.roll(a, dy, 0), dx, 1)
            n += 1
    return out / n


def poly_mask(polys, H, W):
    from PIL import Image, ImageDraw
    im = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(im)
    for poly in polys:
        if len(poly) >= 3:
            dr.polygon([tuple(p) for p in poly], fill=255)
    return np.array(im) > 127


def components(m):
    """4-connected labelling (pure python BFS on the mask's pixels). returns labels, sizes"""
    H, W = m.shape
    lab = np.zeros((H, W), np.int32)
    flat = m.ravel().tolist(); L = [0] * (H * W)
    sizes = [0]
    cur = 0
    for s in range(H * W):
        if not flat[s] or L[s]: continue
        cur += 1; L[s] = cur; n = 0
        st = [s]
        while st:
            p = st.pop(); n += 1
            y, x = divmod(p, W)
            if x + 1 < W and flat[p + 1] and not L[p + 1]: L[p + 1] = cur; st.append(p + 1)
            if x > 0 and flat[p - 1] and not L[p - 1]: L[p - 1] = cur; st.append(p - 1)
            if y + 1 < H and flat[p + W] and not L[p + W]: L[p + W] = cur; st.append(p + W)
            if y > 0 and flat[p - W] and not L[p - W]: L[p - W] = cur; st.append(p - W)
        sizes.append(n)
    return np.array(L, np.int32).reshape(H, W), sizes


# ------------------------------------------------------------------ the operator
def features(img):
    """quantised feature index per pixel. Grey archive film: intensity x local texture (grain vs fur), after a
    3x3 restoration blur so halftone/grain is not read as body texture. Colour footage: RGB cube."""
    img = img.astype(np.float32)
    grey = img.mean(2)
    colourful = np.abs(img - grey[..., None]).mean() > 6
    sm = box_blur(grey, 1)
    var = box_blur((grey - sm) ** 2, 2) ** .5
    if colourful:
        q = np.clip((box_blur(img[..., 0], 1) / 32).astype(int), 0, 7) * 64 + \
            np.clip((box_blur(img[..., 1], 1) / 32).astype(int), 0, 7) * 8 + \
            np.clip((box_blur(img[..., 2], 1) / 32).astype(int), 0, 7)
        return q, 512, sm
    qi = np.clip((sm / 16).astype(int), 0, 15)
    qv = np.clip((var / 6).astype(int), 0, 3)
    return qi * 4 + qv, 64, sm


def pairwise(sm, gamma=50.0):
    dr = np.zeros_like(sm); dd = np.zeros_like(sm)
    dr[:, :-1] = (sm[:, 1:] - sm[:, :-1]) ** 2
    dd[:-1, :] = (sm[1:, :] - sm[:-1, :]) ** 2
    beta = 1.0 / (2 * max(1e-3, (dr.mean() + dd.mean()) / 2))
    return gamma * np.exp(-beta * dr), gamma * np.exp(-beta * dd)


def grabcut(img, prior, seed, iters=3, prior_w=0.15, gamma=50.0, scale=40, extra=None, extra_bins=1):
    """img HxWx3 uint8; prior bool HxW (the SAM mask: one input among our own); seed int8 HxW (1 fg, 2 bg).
    Returns dict(fg, unary_margin, iters_log)."""
    q, nb, sm = features(img)
    if extra is not None:   # e.g. quantised |frame - clean plate|: the dog is what is not the porch
        q = q * extra_bins + extra; nb = nb * extra_bins
    wr, wd = pairwise(sm, gamma)
    din = dist_steps(~prior, 30)   # distance inside prior to its edge
    dout = dist_steps(prior, 30)   # distance outside prior
    fg = prior.copy()
    log = []
    for it in range(iters):
        hf = np.bincount(q[fg & (seed != 2)].ravel(), minlength=nb).astype(np.float64) + 1
        hb = np.bincount(q[~fg & (seed != 1)].ravel(), minlength=nb).astype(np.float64) + 1
        pf = hf / hf.sum(); pb = hb / hb.sum()
        Uf = -np.log(pf[q]) + prior_w * dout      # cost of being fg grows outside the prior
        Ub = -np.log(pb[q]) + prior_w * din       # cost of being bg grows inside the prior
        src = np.round(Ub * scale).astype(np.int64)   # source = fg: cutting the source link means labelling bg
        snk = np.round(Uf * scale).astype(np.int64)
        src[seed == 1] = BIG; snk[seed == 1] = 0
        snk[seed == 2] = BIG; src[seed == 2] = 0
        new, flow = maxflow_grid(src, snk, np.round(wr * scale).astype(np.int64), np.round(wd * scale).astype(np.int64))
        changed = int((new != fg).sum())
        fg = new
        log.append({'iter': it, 'flow': int(flow), 'fg_px': int(fg.sum()), 'changed_px': changed})
        if changed < 20:
            break
    margin = (Ub - Uf)
    return {'fg': fg, 'margin': margin, 'log': log, 'sm': sm}


def cleanup(fg, img_sm, min_hole=80, keep_near=0):
    """alpha cleanup: keep the main body (no background islands), fill small holes, border-matte the edge."""
    lab, sizes = components(fg)
    if len(sizes) > 1:
        main = int(np.argmax(sizes[1:])) + 1
        body = lab == main
        if keep_near:
            near = dilate(body, keep_near)
            for k in range(1, len(sizes)):
                if k != main and sizes[k] > 30 and (near & (lab == k)).any():
                    body |= lab == k
    else:
        body = fg.copy()
    islands = fg & ~body
    hl, hs = components(~body)
    holes = np.zeros_like(body)
    for k in range(1, len(hs)):
        if hs[k] < min_hole:
            m = hl == k
            # a hole is interior only if it does not touch the border
            if not (m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any()):
                holes |= m
    body |= holes
    # contour smoothing (round 2): a 2-pass box filter of the binary body, re-thresholded, rounds polygon corners
    # and staircases without moving straight runs of true edge by more than ~1 px
    sm_body = box_blur(box_blur(body.astype(np.float32), 1), 1) > 0.5
    body = sm_body | (body & erode(body, 2))
    # border matting: alpha from local fg/bg means across a 2px band, fallback to a distance ramp
    inner = erode(body, 2); outer = ~dilate(body, 2)
    band = ~inner & ~outer
    s = img_sm
    def local_mean(mask):
        num = box_blur(np.where(mask, s, 0), 3); den = box_blur(mask.astype(np.float32), 3)
        return num / np.maximum(den, 1e-3), den
    mf, df = local_mean(inner); mb, db = local_mean(outer)
    a = np.where(body, 1.0, 0.0).astype(np.float32)
    contrast = np.abs(mf - mb)
    est = np.clip((s - mb) / np.where(np.abs(mf - mb) < 1e-3, 1e-3, mf - mb), 0, 1)
    ramp = box_blur(body.astype(np.float32), 1)
    use = band & (contrast > 25) & (df > .05) & (db > .05)
    a[band] = ramp[band]
    a[use] = 0.5 * est[use] + 0.5 * ramp[use]
    a[inner] = 1.0; a[outer] = 0.0
    return a, {'islands_px': int(islands.sum()), 'holes_filled_px': int(holes.sum()), 'matted_px': int(use.sum())}


def contour(m):
    return m & ~erode(m, 1)
