"""SCION 42 · few-shot layered-puppet fit.

From a handful of frames of the kit's public-domain archive dog (Amateur Film New Jersey C), discover a layered puppet:
which parts exist (soft layer masks over one template frame), how each part moves between the example frames
(one affine per part per frame), and where neighbouring parts hinge (pivot points found by least squares).

Model (all numpy, gradients written by hand, Adam):
  template points p_i (stride-2 pixels inside the SAM mask of the template frame), their grey value c_i,
  layer logits z_ik  ->  w_i = softmax(z_i / tau)          (the layer masks)
  per frame f, part k: affine A_fk = [M_fk | t_fk]
  warped point  q_fi = sum_k w_ik (M_fk p_i + t_fk)          (linear blend of layer motions = a 2.5D layered mesh)
Losses per example frame (the 'differentiable renderer' is a point splat compared three ways):
  out   : squared distance-transform of the target SAM mask at q   (no template point may fall outside the dog)
  cover : every target mask pixel's squared distance to its nearest q (the dog must be filled)
  photo : (normalised target grey at q - normalised template grey)^2 (appearance consistency)
  conf  : non-conformal part of each M (parts stay near rigid + uniform scale)
  smooth: graph Laplacian of z over the template grid (layers are spatially coherent)
  ent   : entropy of w (layers become crisp), annealed in.
Discovery runs in three passes:
  1. global: one affine per frame (K=1)
  2. over-segment: K0 patches from spatial k-means of the template, each patch gets its own motion per frame
  3. merge: greedy agglomeration of adjacent patches whose motions agree (least-squares cost of sharing one affine);
     the residual curve over K picks the number of parts; then logits and motions are refined jointly.
Joints: for adjacent parts a,b the pivot p* minimises sum_f |(A_fa - A_fb) [p;1]|^2 (the point both parts carry to the
same place in every frame). Its rms residual says how hinge-like the contact is. The kinematic tree is the minimum
spanning tree of those residuals rooted at the largest part.
Held-out test: masks frozen, only motions fitted, IoU on frames never seen in training, against two controls:
  K=1 (one rigid cut-out) and an authored rig (parts drawn from the kit's hand-placed keypoints).
Writes ../model/puppet.npz, ../data/fit_report.json, ../proof/*.jpg
"""
import json, os, sys, time
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree
from scipy.sparse.csgraph import minimum_spanning_tree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KIT = os.path.abspath(os.path.join(ROOT, '..', 'kit', 'archive-dog'))
os.makedirs(os.path.join(ROOT, 'model'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'proof'), exist_ok=True)
RNG = np.random.default_rng(42)

MASKS = json.load(open(os.path.join(KIT, 'masks.json')))
KEYS = json.load(open(os.path.join(KIT, 'pose_agent_v8.json')))
W, H = 384, 288

TEMPLATE = 8
# few-shot training examples: left profile head up (walking toward the person), and right profile head low (walking to
# the bowl), mirrored so every example faces left.  'm' = mirrored.
TRAIN = [(8, 0), (2, 0), (5, 0), (11, 0), (13, 0), (42, 1), (44, 1)]
HOLDOUT = [(3, 0), (7, 0), (10, 0), (12, 0), (43, 1), (45, 1)]
# expanded view examples (round 2): the dog turning toward the camera and standing front-on.  The learned split may
# adapt to them; the hand-cut control cannot.  Held-out turning frames sit between the training ones.
if os.environ.get('PUPPET_VIEWS', '0') == '1':
    TRAIN = TRAIN + [(15, 0), (17, 0), (19, 0), (28, 0), (31, 0)]
    HOLDOUT = HOLDOUT + [(16, 0), (18, 0), (20, 0), (27, 0), (30, 0), (32, 0)]


def load(i, mirror):
    im = np.asarray(Image.open(os.path.join(KIT, 'frames', 'f%03d.jpg' % i)).convert('L'), np.float32) / 255.
    mk = Image.new('L', (W, H), 0); d = ImageDraw.Draw(mk)
    for poly in MASKS[str(i)]:
        if len(poly) >= 3: d.polygon([tuple(q) for q in poly], fill=255)
    mk = np.asarray(mk) > 127
    # keep the largest connected component (SAM sometimes adds stray bits)
    lab, n = ndimage.label(mk)
    if n > 1:
        sz = ndimage.sum(mk, lab, range(1, n + 1)); mk = lab == (1 + int(np.argmax(sz)))
    if mirror: im, mk = im[:, ::-1].copy(), mk[:, ::-1].copy()
    return im, mk


class Frame:
    def __init__(self, i, mirror):
        self.i, self.m = i, mirror
        im, mk = load(i, mirror)
        self.im, self.mask = im, mk
        vals = im[mk]; mu, sd = vals.mean(), vals.std() + 1e-3
        n = (ndimage.gaussian_filter(im, 1.2) - mu) / sd
        self.n = n; self.gy, self.gx = np.gradient(n)
        dt = ndimage.distance_transform_edt(~mk).astype(np.float32)
        self.dt = dt; self.dgy, self.dgx = np.gradient(dt)
        ys, xs = np.nonzero(mk[::2, ::2]); self.tpts = np.stack([xs * 2., ys * 2.], 1)
        ys, xs = np.nonzero(mk); self.cen = np.array([xs.mean(), ys.mean()]); self.area = mk.sum()
        self.tree = cKDTree(self.tpts)


def bil(img, x, y):
    x = np.clip(x, 0, W - 1.001); y = np.clip(y, 0, H - 1.001)
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy
            + img[y0 + 1, x0 + 1] * fx * fy)


class Adam:
    def __init__(self, shape, lr):
        self.m = np.zeros(shape); self.v = np.zeros(shape); self.t = 0; self.lr = lr
    def step(self, x, g, lr=None):
        self.t += 1; b1, b2 = .9, .999
        self.m = b1 * self.m + (1 - b1) * g; self.v = b2 * self.v + (1 - b2) * g * g
        mh = self.m / (1 - b1 ** self.t); vh = self.v / (1 - b2 ** self.t)
        return x - (lr if lr is not None else self.lr) * mh / (np.sqrt(vh) + 1e-8)


class Template:
    def __init__(self, fr, stride=2):
        mk = fr.mask
        ys, xs = np.nonzero(mk[::stride, ::stride]); xs = xs * stride; ys = ys * stride
        self.p = np.stack([xs, ys], 1).astype(np.float64)
        self.N = len(self.p)
        self.c = fr.n[ys, xs]
        self.ph = np.concatenate([self.p, np.ones((self.N, 1))], 1)          # N x 3
        idx = -np.ones(mk.shape, int); idx[ys, xs] = np.arange(self.N)
        e = []
        for dy, dx in ((0, stride), (stride, 0)):
            a = idx[:H - dy, :W - dx]; b = idx[dy:, dx:]
            ok = (a >= 0) & (b >= 0); e.append(np.stack([a[ok], b[ok]], 1))
        self.edges = np.concatenate(e)
        self.cen = self.p.mean(0)


def warp(T, A, w):
    """A: K x 2 x 3, w: N x K -> q: N x 2, per-part positions P: K x N x 2"""
    P = np.einsum('kij,nj->kni', A, T.ph)
    return np.einsum('nk,kni->ni', w, P), P


def frame_loss(T, fr, A, w, lam_photo=6.0, want_grad=True):
    q, P = warp(T, A, w)
    x, y = q[:, 0], q[:, 1]
    d = bil(fr.dt, x, y)
    L_out = np.mean(d ** 2)
    g = np.zeros_like(q)
    g[:, 0] += 2 * d * bil(fr.dgx, x, y) / T.N; g[:, 1] += 2 * d * bil(fr.dgy, x, y) / T.N
    # coverage
    tree = cKDTree(q); dd, nn = tree.query(fr.tpts)
    L_cov = np.mean(dd ** 2)
    diff = q[nn] - fr.tpts
    np.add.at(g, nn, 2 * diff / len(fr.tpts))
    # photometric
    v = bil(fr.n, x, y); r = v - T.c
    L_ph = np.mean(r ** 2)
    g[:, 0] += lam_photo * 2 * r * bil(fr.gx, x, y) / T.N; g[:, 1] += lam_photo * 2 * r * bil(fr.gy, x, y) / T.N
    L = L_out + L_cov + lam_photo * L_ph
    if not want_grad: return L, dict(out=L_out, cov=L_cov, photo=L_ph)
    gA = np.einsum('nk,ni,nj->kij', w, g, T.ph)
    gw = np.einsum('ni,kni->nk', g, P)
    return L, dict(out=L_out, cov=L_cov, photo=L_ph), gA, gw


def conf_pen(A):
    M = A[:, :, :2]
    S = np.einsum('kij,klj->kil', M, M)
    tr = (S[:, 0, 0] + S[:, 1, 1]) / 2
    D = S - tr[:, None, None] * np.eye(2)[None]
    L = np.sum(D ** 2)
    # dL/dM = 4 D M  (D symmetric, traceless)
    gM = 4 * np.einsum('kil,klj->kij', D, M)
    gA = np.zeros_like(A); gA[:, :, :2] = gM
    return L, gA


def softmax(z, tau):
    e = np.exp((z - z.max(1, keepdims=True)) / tau); return e / e.sum(1, keepdims=True)


def fit(T, frames, K, w=None, z=None, A=None, iters=600, learn_w=False, tau=1.0, lam_conf=40., lam_smooth=0.02,
        lam_ent=0.0, ent_ramp=False, log=None, tag='', hinge=None, lam_h=0.0):
    F = len(frames)
    if A is None: raise ValueError
    A = A.copy()
    optA = Adam(A.shape, 1.0)
    lrs = np.zeros(A.shape); lrs[..., :2] = 0.004; lrs[..., 2] = 0.4
    if learn_w: optZ = Adam(z.shape, 0.05)
    hist = []
    for it in range(iters):
        if learn_w: w = softmax(z, tau)
        gA = np.zeros_like(A); gw = np.zeros((T.N, K)); Ltot = 0; parts = {'out': 0, 'cov': 0, 'photo': 0}
        for f, fr in enumerate(frames):
            L, comp, ga, g_w = frame_loss(T, fr, A[f], w)
            Lc, gc = conf_pen(A[f])
            Ltot += L + lam_conf * Lc; gA[f] = ga + lam_conf * gc; gw += g_w
            if hinge is not None and lam_h > 0 and len(hinge[0]):
                ph_, ia, ib = hinge
                diff = np.einsum('nij,nj->ni', A[f][ia] - A[f][ib], ph_)
                n_ = len(ph_)
                Ltot += lam_h * np.sum(diff ** 2) / n_
                gpair = 2 * lam_h / n_ * np.einsum('ni,nj->nij', diff, ph_)
                np.add.at(gA[f], ia, gpair); np.add.at(gA[f], ib, -gpair)
            for k in parts: parts[k] += comp[k] / F
        if learn_w:
            gz = w * (gw - np.sum(w * gw, 1, keepdims=True)) / tau
            e = T.edges; dz = z[e[:, 0]] - z[e[:, 1]]
            Ltot += lam_smooth * np.sum(dz ** 2)
            np.add.at(gz, e[:, 0], 2 * lam_smooth * dz); np.add.at(gz, e[:, 1], -2 * lam_smooth * dz)
            le = lam_ent * (min(1, it / (0.6 * iters)) if ent_ramp else 1)
            if le > 0:
                lw = np.log(w + 1e-9); H_ = -np.sum(w * lw, 1)
                Ltot += le * np.sum(H_) / T.N * 100
                gHw = -(lw + 1)
                gz += le * 100 / T.N * w * (gHw - np.sum(w * gHw, 1, keepdims=True)) / tau
            z = optZ.step(z, gz)
        A = adam_scaled(optA, A, gA, lrs)
        if it % 50 == 0 or it == iters - 1:
            hist.append(dict(it=it, L=float(Ltot / F), **{k: float(v) for k, v in parts.items()}))
            if log: print(tag, hist[-1], flush=True)
    if learn_w: w = softmax(z, tau)
    return A, w, z, hist


def adam_scaled(opt, x, g, lrs):
    opt.t += 1; b1, b2 = .9, .999
    opt.m = b1 * opt.m + (1 - b1) * g; opt.v = b2 * opt.v + (1 - b2) * g * g
    mh = opt.m / (1 - b1 ** opt.t); vh = opt.v / (1 - b2 ** opt.t)
    return x - lrs * mh / (np.sqrt(vh) + 1e-8)


def init_global(T, fr):
    s = np.sqrt(fr.area / max(1, T.N * 4))
    A = np.array([[s, 0, 0], [0, s, 0]], float)
    A[:, 2] = fr.cen - s * T.cen
    return A


def kmeans(X, K, iters=50):
    C = X[RNG.choice(len(X), K, replace=False)]
    for _ in range(iters):
        lab = np.argmin(((X[:, None] - C[None]) ** 2).sum(-1), 1)
        for k in range(K):
            if np.any(lab == k): C[k] = X[lab == k].mean(0)
    return lab, C


def ls_affine(ph, q):
    X, *_ = np.linalg.lstsq(ph, q, rcond=None)      # 3 x 2
    return X.T, np.sum((ph @ X - q) ** 2)


def adjacency(T, lab, K):
    Adj = np.zeros((K, K), int)
    a, b = lab[T.edges[:, 0]], lab[T.edges[:, 1]]
    m = a != b
    np.add.at(Adj, (a[m], b[m]), 1); np.add.at(Adj, (b[m], a[m]), 1)
    return Adj


def splat_mask(T_full_p, A, w_full, shape=(H, W)):
    # 2x2 sub-points per template pixel so a stretched layer leaves no splat holes
    T_full_p = (T_full_p[:, None, :] + np.array([[-.25, -.25], [.25, -.25], [-.25, .25], [.25, .25]])[None]).reshape(-1, 2)
    w_full = np.repeat(w_full, 4, axis=0)
    ph = np.concatenate([T_full_p, np.ones((len(T_full_p), 1))], 1)
    P = np.einsum('kij,nj->kni', A, ph); q = np.einsum('nk,kni->ni', w_full, P)
    m = np.zeros(shape, bool)
    xi = np.round(q[:, 0]).astype(int); yi = np.round(q[:, 1]).astype(int)
    ok = (xi >= 0) & (xi < shape[1]) & (yi >= 0) & (yi < shape[0])
    m[yi[ok], xi[ok]] = True
    m = ndimage.binary_closing(m, iterations=1)
    return m, q


BETA = float(os.environ.get('PUPPET_BETA', 4.0))
LAM_H = float(os.environ.get('PUPPET_LAMH', 0.05))


class Grid:
    """the template points live on a stride-2 grid; smoothing and blurring happen there"""
    def __init__(self, T):
        self.ix = (T.p[:, 0] // 2).astype(int); self.iy = (T.p[:, 1] // 2).astype(int)
        self.shape = (H // 2 + 1, W // 2 + 1)
        m = np.zeros(self.shape, np.float32); m[self.iy, self.ix] = 1; self.m = m
    def smooth(self, v, s):
        im = np.zeros(self.shape, np.float32); im[self.iy, self.ix] = v
        a = ndimage.gaussian_filter(im, s); b = ndimage.gaussian_filter(self.m, s)
        return (a / np.maximum(b, 1e-6))[self.iy, self.ix]
    def blur_onehot(self, lab, K, s):
        w = np.stack([self.smooth((lab == k).astype(np.float32), s) for k in range(K)], 1)
        return w / w.sum(1, keepdims=True)


def boundary_pairs(T, lab):
    e = T.edges; a, b = lab[e[:, 0]], lab[e[:, 1]]; m = a != b
    mid = (T.ph[e[m, 0]] + T.ph[e[m, 1]]) / 2
    return mid, a[m], b[m]


def res_by(curve, K): return next(c['residual_px2_per_point_frame'] for c in curve if c['K'] == K)


def iou(a, b): return float((a & b).sum() / max(1, (a | b).sum()))


def main():
    t0 = time.time()
    frames = [Frame(i, m) for i, m in TRAIN]
    hold = [Frame(i, m) for i, m in HOLDOUT]
    tf = frames[0]
    T = Template(tf, 2)
    print('template points', T.N, 'train frames', len(frames))
    F = len(frames)
    report = {'template_frame': TEMPLATE, 'train': TRAIN, 'holdout': HOLDOUT, 'N_points': T.N}

    # ---- pass 1: global affine per frame
    A1 = np.stack([init_global(T, fr)[None] for fr in frames])
    w1 = np.ones((T.N, 1))
    A1, _, _, h1 = fit(T, frames, 1, w=w1, A=A1, iters=400, lam_conf=10., log=True, tag='global')
    report['pass1_global'] = h1[-1]

    # ---- pass 2: over-segmentation into K0 patches, each patch moves on its own
    K0 = 18
    lab0, C0 = kmeans(T.p, K0)
    d2 = ((T.p[:, None] - C0[None]) ** 2).sum(-1)
    w0 = softmax(-d2 / 30.0, 1.0)  # soft patch weights (spatial), fixed in this pass
    A0 = np.repeat(A1, K0, axis=1)
    A0, _, _, h0 = fit(T, frames, K0, w=w0, A=A0, iters=700, lam_conf=20., log=True, tag='patches')
    report['pass2_patches'] = {'K0': K0, **h0[-1]}
    q0 = np.stack([warp(T, A0[f], w0)[0] for f in range(F)])          # F x N x 2: the dense motion field

    # ---- pass 3: greedy merge of adjacent patches by least-squares motion agreement
    groups = {k: [k] for k in range(K0)}
    lab = lab0.copy()
    def gcost(members):
        idx = np.isin(lab0, members)
        return sum(ls_affine(T.ph[idx], q0[f, idx])[1] for f in range(F))
    cost = {k: gcost([k]) for k in groups}
    curve = [{'K': K0, 'residual_px2_per_point_frame': sum(cost.values()) / (T.N * F)}]
    merges = []
    while len(groups) > 1:
        Adj = adjacency(T, lab, lab.max() + 1)
        best = None
        for a in groups:
            for b in groups:
                if a < b and Adj[a, b] > 0:
                    c = gcost(groups[a] + groups[b]) - cost[a] - cost[b]
                    if best is None or c < best[0]: best = (c, a, b)
        c, a, b = best
        groups[a] = groups[a] + groups.pop(b); cost[a] = gcost(groups[a]); cost.pop(b)
        lab[lab == b] = a
        tot = sum(cost.values()) / (T.N * F)
        curve.append({'K': len(groups), 'residual_px2_per_point_frame': tot, 'merge_cost': c / (T.N * F)})
        merges.append((int(a), int(b)))
        if True:
            snap = {g: list(m) for g, m in groups.items()}
            curve[-1]['groups'] = snap
    report['merge_curve'] = [{k: v for k, v in c.items() if k != 'groups'} for c in curve]
    # proof: the merge hierarchy as label maps
    pal = (np.array([[230, 90, 60], [70, 160, 230], [240, 200, 60], [120, 210, 110], [200, 110, 220], [60, 200, 200],
                     [250, 150, 180], [150, 120, 60], [255, 255, 255], [100, 100, 250], [180, 250, 160], [250, 120, 40],
                     [90, 60, 160], [200, 200, 200], [40, 120, 60], [160, 40, 80], [120, 120, 120], [250, 220, 160]]))
    show = [18, 12, 10, 8, 7, 6, 5, 4, 3, 2]
    tiles = []
    for Kshow in show:
        g = next(c for c in curve if c['K'] == Kshow)['groups'] if Kshow != K0 else {k: [k] for k in range(K0)}
        im = (np.stack([tf.im] * 3, -1) * 120).astype(np.uint8)
        for j, (gk, mem) in enumerate(sorted(g.items())):
            sel = np.isin(lab0, mem)
            pts = T.p[sel].astype(int)
            for dy in (0, 1):
                for dx in (0, 1):
                    im[pts[:, 1] + dy, pts[:, 0] + dx] = pal[j % len(pal)]
        t = Image.fromarray(im).crop((40, 40, 280, 230)).resize((360, 285))
        ImageDraw.Draw(t).text((6, 4), 'K=%d  resid %.1f px^2' % (Kshow, res_by(curve, Kshow)), fill=(255, 255, 255))
        tiles.append(t)
    sheet = Image.new('RGB', (360 * 5, 285 * 2))
    for j, t in enumerate(tiles): sheet.paste(t, ((j % 5) * 360, (j // 5) * 285))
    sheet.save(os.path.join(ROOT, 'proof', 'merge_hierarchy.jpg'), quality=88)
    # choose K: the smallest K whose residual is within 2x of the K0 residual + 0.5 px^2 (elbow rule, printed)
    res = {c['K']: c['residual_px2_per_point_frame'] for c in curve}
    base = res[K0]
    Ks = sorted(res)
    Kc = next(k for k in Ks if res[k] <= 1.8 * base + 0.6)
    # model selection by held-out IoU (sweep.sh fits K in {3..12}; frames never seen in training decide)
    sw = {}
    for fn in os.listdir(os.path.join(HERE, 'cache')) if os.path.isdir(os.path.join(HERE, 'cache')) else []:
        if fn.startswith('sweep_K') and fn.endswith('.json'):
            r = json.load(open(os.path.join(HERE, 'cache', fn)))
            sw[r['K_chosen']] = r['heldout_summary']['learned']['mean_iou']
    if sw and not os.environ.get('PUPPET_SWEEP'):
        best = max(sw.values())
        Kc = min(k for k, v in sw.items() if v >= best - 0.01)
        report['K_rule'] = 'smallest K whose held-out IoU is within 0.01 of the best K in the sweep'
        report['K_sweep_heldout_iou'] = {int(k): round(v, 4) for k, v in sorted(sw.items())}
    Kc = int(os.environ.get('PUPPET_K', Kc))
    print('residual by K', {k: round(res[k], 2) for k in Ks}, 'chosen K', Kc)
    report['K_rule'] = 'smallest K with residual <= 1.8 x residual(K0) + 0.6 px^2'
    report['K_chosen'] = Kc
    snap = next(c['groups'] for c in curve if c['K'] == Kc)
    labK = np.zeros(T.N, int)
    for j, (g, mem) in enumerate(sorted(snap.items())):
        labK[np.isin(lab0, mem)] = j
    # ---- pass 4: EM over crisp layers.  M-step: motions with layers fixed (+ hinge consistency at the layer borders);
    # E-step: every template point joins the layer whose motion explains it best over all frames (costs smoothed on
    # the template grid, a Potts-like prior), then the layer weights are the one-hot labels blurred by 1.5 grid cells
    # (soft seams, crisp layers).
    G = Grid(T)
    lab = labK.copy()
    AK = np.zeros((F, Kc, 2, 3))
    for f in range(F):
        for k in range(Kc):
            idx = lab == k; AK[f, k] = ls_affine(T.ph[idx], q0[f, idx])[0]
    em_log = []
    for rnd in range(6):
        Kc = lab.max() + 1
        wK = G.blur_onehot(lab, Kc, 1.2)
        hinge = boundary_pairs(T, lab)
        AK, _, _, hK = fit(T, frames, Kc, w=wK, A=AK, iters=300, lam_conf=20., hinge=hinge, lam_h=LAM_H, log=False)
        # E-step
        cost = np.zeros((T.N, Kc))
        for f, fr in enumerate(frames):
            Pk = np.einsum('kij,nj->kni', AK[f], T.ph)
            for k in range(Kc):
                x, y = Pk[k, :, 0], Pk[k, :, 1]
                cost[:, k] += bil(fr.dt, x, y) ** 2 + 6.0 * (bil(fr.n, x, y) - T.c) ** 2
        cs = np.stack([G.smooth(cost[:, k], 1.0) for k in range(Kc)], 1) / F
        # ICM with a Potts prior: a point may only take a label one of its grid neighbours already has, and pays BETA
        # for every neighbour that disagrees.  Parts can grow, shrink and vanish, but not scatter.
        new = lab.copy(); e = T.edges
        for _ in range(8):
            cnt = np.zeros((T.N, Kc))
            np.add.at(cnt, (e[:, 0], new[e[:, 1]]), 1); np.add.at(cnt, (e[:, 1], new[e[:, 0]]), 1)
            deg = cnt.sum(1, keepdims=True)
            E = cs + BETA * (deg - cnt)
            E[cnt == 0] = np.inf; E[np.arange(T.N), new] = (cs + BETA * (deg - cnt))[np.arange(T.N), new]
            new = np.argmin(E, 1)
        changed = int(np.sum(new != lab))
        # layers that lost (almost) all their points are dropped: the data did not need them
        keep = [k for k in range(Kc) if np.sum(new == k) >= 8]
        remap = -np.ones(Kc, int); remap[keep] = np.arange(len(keep))
        if len(keep) < Kc:
            cs2 = cs[:, keep]; mm = remap[new]; bad = mm < 0; mm[bad] = np.argmin(cs2[bad], 1); new = mm
        AK = AK[:, keep]
        lab = new
        em_log.append(dict(round=rnd, K=len(keep), changed_points=changed, **hK[-1]))
        print('EM', em_log[-1], flush=True)
        if changed < 10: break
    Kc = lab.max() + 1
    wK = G.blur_onehot(lab, Kc, 1.2)
    hinge = boundary_pairs(T, lab)
    AK, _, _, hK = fit(T, frames, Kc, w=wK, A=AK, iters=500, lam_conf=20., hinge=hinge, lam_h=LAM_H, log=True, tag='final')
    z = np.log(wK + 1e-6)
    report['pass4_em'] = em_log
    report['pass4_layers'] = hK[-1]
    report['K_final'] = int(Kc)
    labF = lab
    sizes = np.bincount(labF, minlength=Kc)

    # ---- joints: on the shared border of two adjacent layers, the point both motions carry to the same place in every
    # frame (least rms disagreement).  The unconstrained least-squares pivot is kept as a diagnostic.
    Adj = adjacency(T, labF, Kc)
    joints = {}
    Wgt = np.zeros((Kc, Kc))
    for a in range(Kc):
        for b in range(a + 1, Kc):
            if Adj[a, b] < 3: continue
            D = AK[:, a] - AK[:, b]                       # F x 2 x 3
            Mx = D[:, :, :2].reshape(-1, 2); bx = -D[:, :, 2].reshape(-1)
            p, *_ = np.linalg.lstsq(Mx, bx, rcond=None)
            ea = T.edges[(labF[T.edges[:, 0]] == a) & (labF[T.edges[:, 1]] == b) | (labF[T.edges[:, 0]] == b) & (labF[T.edges[:, 1]] == a)]
            bpts = (T.p[ea[:, 0]] + T.p[ea[:, 1]]) / 2
            bh = np.concatenate([bpts, np.ones((len(bpts), 1))], 1)
            dis = np.sqrt(np.mean(np.sum(np.einsum('fij,nj->fni', D, bh) ** 2, -1), 0))
            j = int(np.argmin(dis))
            joints[(a, b)] = dict(pivot=bpts[j].tolist(), pivot_used=bpts[j].tolist(), rms_px=float(dis[j]),
                                  border_rms_px_mean=float(dis.mean()), contact=int(Adj[a, b]),
                                  free_ls_pivot=p.tolist(), free_pivot_dist_px=float(np.min(np.linalg.norm(bpts - p, axis=1))))
            Wgt[a, b] = Wgt[b, a] = float(dis[j]) + 0.01
    mst = minimum_spanning_tree(Wgt).toarray()
    root = int(np.argmax(sizes))
    edges = [(i, j) for i in range(Kc) for j in range(Kc) if mst[i, j] > 0]
    parent = -np.ones(Kc, int); seen = {root}; frontier = [root]
    while frontier:
        u = frontier.pop()
        for i, j in edges:
            for a, b in ((i, j), (j, i)):
                if a == u and b not in seen: parent[b] = a; seen.add(b); frontier.append(b)

    # ---- held-out: masks frozen, motions fitted
    def heldout_fit(wfix, Kh, tag):
        out = []
        Tfull_p = np.stack(np.nonzero(tf.mask)[::-1], 1).astype(float)
        wfull = wfix_full(wfix)
        for fr in hold:
            A = np.repeat(init_global(T, fr)[None], 1, 0)
            A, _, _, _ = fit(T, [fr], 1, w=np.ones((T.N, 1)), A=A[None], iters=250, lam_conf=10.)
            A = np.repeat(A, Kh, axis=1)
            A, _, _, hh = fit(T, [fr], Kh, w=wfix, A=A, iters=400, lam_conf=20.)
            m, _ = splat_mask(Tfull_p, A[0], wfull)
            L, comp = frame_loss(T, fr, A[0], wfix, want_grad=False)
            out.append(dict(frame=fr.i, mirrored=fr.m, iou=iou(m, fr.mask), photo=float(comp['photo']), out=float(comp['out']), cov=float(comp['cov'])))
        return out

    # dense weights for every template pixel by nearest template point
    tree_T = cKDTree(T.p)
    def wfix_full(wfix):
        Tfull_p = np.stack(np.nonzero(tf.mask)[::-1], 1).astype(float)
        _, nn = tree_T.query(Tfull_p, k=4)
        return wfix[nn].mean(1)

    # training IoU for the learned model
    Tfull_p = np.stack(np.nonzero(tf.mask)[::-1], 1).astype(float)
    train_iou = [dict(frame=fr.i, mirrored=fr.m, iou=iou(splat_mask(Tfull_p, AK[f], wfix_full(wK))[0], fr.mask)) for f, fr in enumerate(frames)]

    # control 1: one rigid layer
    w_rigid = np.ones((T.N, 1))
    # control 2: authored rig from the kit's hand-placed keypoints on the template frame
    kp = {k: np.array(v, float) for k, v in KEYS[str(TEMPLATE)].items() if not k.startswith('_')}
    hip = kp['chest'] + 0.78 * (kp['tail'] - kp['chest']) + np.array([0, 15.])
    segs = {'head': (kp['nose'], kp['neck']), 'neck': (kp['neck'], kp['chest']), 'trunk': (kp['chest'], hip),
            'tail': (hip, kp['tail']), 'fore1': (kp['chest'], kp['f1']), 'fore2': (kp['chest'] + [10, 0], kp['f2']),
            'hind1': (hip, kp['h1']), 'hind2': (hip, kp['h2'])}
    def segd(P, a, b):
        ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
    names = list(segs)
    Dm = np.stack([segd(T.p, *segs[n]) for n in names], 1)
    lab_auth = np.argmin(Dm, 1)
    w_auth = softmax(-Dm ** 2 / 20., 1.0)
    held = {
        'learned': heldout_fit(wK, Kc, 'learned'),
        'rigid_K1': heldout_fit(w_rigid, 1, 'rigid'),
        'authored_rig': heldout_fit(w_auth, len(names), 'authored'),
    }
    summ = {k: dict(mean_iou=float(np.mean([r['iou'] for r in v])), mean_photo=float(np.mean([r['photo'] for r in v])),
                    mean_out_px2=float(np.mean([r['out'] for r in v]))) for k, v in held.items()}
    print('held-out', json.dumps(summ, indent=1))
    report.update(train_iou=train_iou, heldout=held, heldout_summary=summ,
                  parts=[dict(k=k, n_points=int(sizes[k]), parent=int(parent[k]),
                              centroid=T.p[labF == k].mean(0).tolist() if sizes[k] else None) for k in range(Kc)],
                  root=root, joints=[dict(a=a, b=b, **v) for (a, b), v in joints.items()],
                  tree_edges=[(int(parent[k]), k) for k in range(Kc) if parent[k] >= 0],
                  authored_parts=names, seconds=round(time.time() - t0, 1))
    # uncertainty: per-point disagreement of the soft masks (1 - max w) and per-point photometric residual over frames
    ph_res = np.zeros(T.N)
    for f, fr in enumerate(frames):
        q, _ = warp(T, AK[f], wK); ph_res += (bil(fr.n, q[:, 0], q[:, 1]) - T.c) ** 2 / F
    sweep = os.environ.get('PUPPET_SWEEP')
    if sweep:
        json.dump(report, open(os.path.join(ROOT, 'build', 'cache', 'sweep_K%d%s.json' % (Kc, os.environ.get('PUPPET_TAG', ''))), 'w'), indent=1)
        return
    np.savez_compressed(os.path.join(ROOT, 'model', 'puppet.npz'), p=T.p, c=T.c, z=z, w=wK, lab=labF, A=AK, train=np.array(TRAIN),
                        template_frame=TEMPLATE, parent=parent, root=root, lab0=lab0, A0=A0, w_auth=w_auth, lab_auth=lab_auth,
                        mask_uncert=1 - wK.max(1), photo_resid=ph_res,
                        joint_keys=np.array(list(joints.keys())), joint_pivots=np.array([v['pivot_used'] for v in joints.values()]),
                        joint_rms=np.array([v['rms_px'] for v in joints.values()]))
    json.dump(report, open(os.path.join(ROOT, 'data', 'fit_report.json'), 'w'), indent=1)
    print('done', round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main()
