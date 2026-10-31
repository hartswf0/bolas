"""SCION 40 · the TRACKING RECOVERY AGENT. Reads only the capture plate's pixels (cache/plate/*.jpg, plate_clean.jpg)
and the puppet database (the plate-style card scans and their fiducial ids, data/cards.json) and recovers:
  1. camera calibration: the four corner fiducials of the layout sheet -> homography plate -> stage;
  2. hand mattes: background difference against the clean plate + a chroma model of skin learned from the take;
  3. per-piece rigid transforms (X, Y, theta) and which card is down: fiducial decode for identity and (re)acquisition,
     then Lucas-Kanade (inverse-free Gauss-Newton, rigid + gain/bias, coarse-to-fine, hand pixels and outliers
     down-weighted) on the card's own printed texture for the precise pose;
  4. a timestamped event stream (hand on/off, card swaps, moves) from the recovered data.
It never reads perform.json, except with --eval, after tracking, to measure its error.
Writes data/tracked.json, data/events.jsonl, data/calibration.json, cache/matte/%04d.png (stage-space hand matte, 1/4 res)."""
import json, math, os, sys, time
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

CARDS = json.load(open(os.path.join(DATA, 'cards.json')))
SHEET = json.load(open(os.path.join(DATA, 'sheet.json')))
ID2CARD = {m['id']: n for n, m in CARDS.items()}
FAMILY = {'dog.body': 'b_', 'dog.head': 'h_', 'person': 'p_', 'door': 'd_', 'light': 'light'}


def fam_of(name):
    for k, v in FAMILY.items():
        if name.startswith(v):
            return k


def gray(im):
    a = np.asarray(im, np.float32)
    return a[..., :3].mean(-1) if a.ndim == 3 else a


def bilinear(img, x, y):
    h, w = img.shape
    x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32)
    fx = x - x0; fy = y - y0
    a = img[y0, x0]; b = img[y0, x0 + 1]; c = img[y0 + 1, x0]; d = img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


# ------------------------------------------------------------------ fiducials
def label(mask):
    """connected components (4-neighbour) by union-find over runs; returns list of (ys, xs) arrays"""
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    parent = [0]

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    runs_prev = []
    nxt = 1
    for y in range(h):
        row = mask[y]
        if not row.any():
            runs_prev = []
            continue
        d = np.diff(np.r_[0, row.astype(np.int8), 0])
        starts = np.where(d == 1)[0]; ends = np.where(d == -1)[0]
        runs = []
        for s, e in zip(starts, ends):
            l = None
            for (ps, pe, pl) in runs_prev:
                if ps < e and s < pe:
                    if l is None:
                        l = find(pl)
                    else:
                        a, b = find(pl), l
                        if a != b:
                            parent[max(a, b)] = min(a, b)
                            l = min(a, b)
            if l is None:
                l = nxt; parent.append(nxt); nxt += 1
            lab[y, s:e] = l
            runs.append((s, e, l))
        runs_prev = runs
    roots = np.array([find(k) for k in range(nxt)], np.int32)
    lab = roots[lab]
    out = []
    ys, xs = np.nonzero(lab)
    if len(ys) == 0:
        return out
    ls = lab[ys, xs]
    order = np.argsort(ls, kind='stable')
    ls, ys, xs = ls[order], ys[order], xs[order]
    cuts = np.where(np.diff(ls))[0] + 1
    for a, b in zip(np.r_[0, cuts], np.r_[cuts, len(ls)]):
        out.append((ys[a:b], xs[a:b]))
    return out


def read_marker(G, corners):
    """corners: 4 (x, y) in order TL, TR, BR, BL (image). Sample a 6x6 grid; return (id, rot) or (None, None)."""
    Hm = homography([(0, 0), (6, 0), (6, 6), (0, 6)], corners)
    cc = np.array([(c + .5, r + .5) for r in range(6) for c in range(6)], float)
    p = apply_h(Hm, cc) - 0.5
    v = bilinear(G, p[:, 0], p[:, 1]).reshape(6, 6)
    border = np.r_[v[0], v[5], v[1:5, 0], v[1:5, 5]]
    inner = v[1:5, 1:5]
    hi = inner.max()
    thr = (border.mean() + hi) / 2
    if (border > thr).sum() > 2 or hi - border.mean() < 40:
        return None, None
    cells = (inner < thr).astype(np.uint8)
    for rot in range(4):
        ident = fid_decode(np.rot90(cells, -rot))
        if ident is not None:
            return ident, rot
    return None, None


def find_markers(G, x0=0, y0=0, size_range=(18, 48), dark=None):
    """search a grey image window for fiducials. Returns list of dict(id, centre, angle) in G's coordinates + offset."""
    if dark is None:
        bg = np.percentile(G, 70)
        dark = G < min(bg * 0.42, 90)
    out = []
    for ys, xs in label(dark):
        n = len(ys)
        if n < 120 or n > 2600:
            continue
        bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        if not (size_range[0] <= bw <= size_range[1] * 1.45 and size_range[0] <= bh <= size_range[1] * 1.45):
            continue
        s1, s2 = xs + ys, xs - ys
        tl = (xs[s1.argmin()], ys[s1.argmin()]); br = (xs[s1.argmax()], ys[s1.argmax()])
        tr = (xs[s2.argmax()], ys[s2.argmax()]); bl = (xs[s2.argmin()], ys[s2.argmin()])
        corners = [(tl[0], tl[1]), (tr[0] + 1, tr[1]), (br[0] + 1, br[1] + 1), (bl[0], bl[1] + 1)]
        ident, rot = read_marker(G, corners)
        if ident is None:
            continue
        C = np.array(corners, float)
        # the marker's "up" edge after undoing the decode rotation
        C = np.roll(C, -rot, 0)
        cx, cy = C.mean(0)
        ex = C[1] - C[0]
        ang = -math.atan2(ex[1], ex[0])        # counter-clockwise on screen
        out.append(dict(id=ident, centre=(cx + x0, cy + y0), angle=ang, corners=(C + [x0, y0]).tolist()))
    return out


# ------------------------------------------------------------------ calibration
def calibrate(clean_rgb):
    G = gray(clean_rgb)
    found = {}
    h, w = G.shape
    for (sx, sy) in ((0, 0), (w - 260, 0), (w - 260, h - 260), (0, h - 260)):
        win = G[sy:sy + 260, sx:sx + 260]
        for m in find_markers(win, sx, sy, size_range=(26, 48), dark=win < 60):
            if m['id'] in SHEET['corner_ids']:
                found[m['id']] = m
    src, dst = [], []
    half = 3 * SHEET['cell']
    for ident, (X, Y) in zip(SHEET['corner_ids'], SHEET['corners_stage']):
        m = found[ident]
        stage_c = [(X - half, Y - half), (X + half, Y - half), (X + half, Y + half), (X - half, Y + half)]
        src += m['corners']; dst += stage_c
    Hp2s = homography(src, dst)
    err = np.hypot(*(apply_h(Hp2s, src) - np.array(dst)).T)
    return Hp2s, dict(ids=sorted(found), reproj_rms_px=float(np.sqrt((err ** 2).mean())), n_points=len(src))


def rectify(im, Hp2s):
    Hs2p = np.linalg.inv(Hp2s); Hs2p /= Hs2p[2, 2]
    return im.transform((W, H), Image.PERSPECTIVE, tuple(Hs2p.reshape(-1)[:8]), resample=Image.BILINEAR)


# ------------------------------------------------------------------ templates and Lucas-Kanade
class Template:
    def __init__(self, name):
        m = CARDS[name]
        im = Image.open(os.path.join(CACHE, 'cards', 'plate', name + '.png')).convert('RGBA')
        self.name, self.anchor = name, m['anchor']
        self.levels = []
        for lv in (2, 1, 0):
            s = 2 ** lv
            imL = im.resize((im.size[0] // s, im.size[1] // s), Image.BOX) if s > 1 else im
            a = np.asarray(imL, np.float32)
            A = a[..., 3]
            g = blur5(gray(a))
            inner = np.asarray(Image.fromarray((A > 250).astype(np.uint8) * 255).filter(ImageFilter.MinFilter(3))) > 0
            ys, xs = np.nonzero(inner)
            step = 2 if lv == 0 else 1
            sel = (ys % step == 0) & (xs % step == 0)
            ys, xs = ys[sel], xs[sel]
            u = (xs + .5) * s - self.anchor[0]
            v = (ys + .5) * s - self.anchor[1]
            self.levels.append(dict(s=s, u=u, v=v, T=g[ys, xs]))
        tm = m['tab']['marker']
        self.marker = (tm[0] - self.anchor[0], tm[1] - self.anchor[1])


def blur5(g):
    k = np.array([1, 4, 6, 4, 1], np.float32) / 16
    p = np.pad(g, 2, mode='edge')
    h = sum(k[j] * p[:, j:j + g.shape[1]] for j in range(5))
    return sum(k[j] * h[j:j + g.shape[0], :] for j in range(5))


def pyramid(G):
    P = [G]
    for _ in range(2):
        g = P[-1]
        h2, w2 = g.shape[0] // 2 * 2, g.shape[1] // 2 * 2
        P.append(g[:h2, :w2].reshape(h2 // 2, 2, w2 // 2, 2).mean((1, 3)))
    out = []
    for lv, g in enumerate(P):
        gb = blur5(g)
        gx = np.zeros_like(gb); gy = np.zeros_like(gb)
        gx[:, 1:-1] = (gb[:, 2:] - gb[:, :-2]) / 2; gy[1:-1] = (gb[2:] - gb[:-2]) / 2
        out.append((gb, gx, gy))
    return out


def lk(pyr, mattes, tpl, pose, iters=(10, 8, 6), rot=True):
    X, Y, th = pose
    a_, b_ = 1.0, 0.0
    info = {}
    for li, L in enumerate(tpl.levels):
        s = L['s']; lv = int(round(math.log2(s)))
        I, Ix, Iy = pyr[lv]
        hm = mattes[lv]
        u, v, T = L['u'], L['v'], L['T']
        for it in range(iters[li]):
            c, sn = math.cos(th), math.sin(th)
            x = (X + c * u + sn * v) / s - .5
            y = (Y - sn * u + c * v) / s - .5
            Iw = bilinear(I, x, y); gx = bilinear(Ix, x, y); gy = bilinear(Iy, x, y)
            occ = bilinear(hm, x, y)
            e = Iw - (a_ * T + b_)
            # robust weights: Tukey on the residual, zero on the hand matte
            sig = 1.4826 * np.median(np.abs(e - np.median(e))) + 4
            r = e / (4.685 * sig)
            w = np.where(np.abs(r) < 1, (1 - r * r) ** 2, 0) * (occ < 0.5)
            dxdt = (-sn * u + c * v) / s; dydt = (-c * u - sn * v) / s
            J = np.stack([gx / s, gy / s, gx * dxdt + gy * dydt, -T, -np.ones_like(T)], 1)
            Jw = J * w[:, None]
            A = J.T @ Jw + np.diag([1e-3, 1e-3, 10.0, 1e-2, 1e-2]) * (w.sum() + 1) * 1e-4
            if not rot:
                A[2, :] = 0; A[:, 2] = 0; A[2, 2] = 1.0
            g = Jw.T @ e
            if not rot:
                g[2] = 0
            try:
                d = -np.linalg.solve(A, g)
            except np.linalg.LinAlgError:
                break
            X += d[0]; Y += d[1]; th += float(np.clip(d[2], -0.15, 0.15)); a_ = float(np.clip(a_ + d[3], 0.6, 1.3)); b_ = float(np.clip(b_ + d[4], -60, 60))
            if abs(d[0]) < 0.02 and abs(d[1]) < 0.02 and abs(d[2]) < 2e-4:
                break
        info = dict(resid=float(np.sqrt((w * e * e).sum() / max(w.sum(), 1))), support=float(w.mean()), gain=float(a_))
    return (X, Y, th), info


def decode_at(G, tpl, pose, r=42, near=18.0, fam=None):
    """find and read a marker of this piece's family near where the pose says its tab is (a small window search)"""
    X, Y, th = pose
    c, s = math.cos(th), math.sin(th)
    mu, mv = tpl.marker
    cx, cy = X + c * mu + s * mv, Y - s * mu + c * mv
    x0, y0 = int(max(0, cx - r)), int(max(0, cy - r))
    win = G[y0:int(min(H, cy + r)), x0:int(min(W, cx + r))]
    if win.shape[0] < 20 or win.shape[1] < 20:
        return None
    best, bd = None, near
    fam = fam or fam_of(tpl.name)
    for m in find_markers(win, x0, y0, size_range=(20, 40)):
        nm = ID2CARD.get(m['id'])
        if not nm or fam_of(nm) != fam:
            continue
        d = math.hypot(m['centre'][0] - cx, m['centre'][1] - cy)
        if d < bd:
            best, bd = m, d
    return best


# ------------------------------------------------------------------ hand matte
class HandModel:
    """skin chroma: a 2D Gaussian in (log R/G, log B/G), learned from foreground pixels the pieces cannot explain"""
    def __init__(self):
        self.samples = []
        self.mu = None

    def feats(self, rgb):
        a = rgb + 6.0
        return np.stack([np.log(a[..., 0] / a[..., 1]), np.log(a[..., 2] / a[..., 1])], -1)

    def learn(self, rgb, fg, explained):
        sel = fg & ~explained
        f = self.feats(rgb)[sel]
        if len(f) > 200:
            self.samples.append(f[::7])

    def fit(self):
        f = np.concatenate(self.samples)
        # trim: keep the dominant cluster (the hands), drop shadow fringes and paper edges
        mu = np.median(f, 0)
        for _ in range(4):
            C = np.cov((f - mu).T) + np.eye(2) * 1e-5
            dmah = np.einsum('ni,ij,nj->n', f - mu, np.linalg.inv(C), f - mu)
            keep = f[dmah < 4]
            mu = keep.mean(0)
        self.mu, self.Ci = mu, np.linalg.inv(np.cov((keep - mu).T) + np.eye(2) * 1e-5)
        return dict(mu=mu.tolist(), n=int(len(f)))

    def matte(self, rgb, fg):
        f = self.feats(rgb) - self.mu
        d = np.einsum('hwi,ij,hwj->hw', f, self.Ci, f)
        m = (d < 9) & fg
        im = Image.fromarray(m.astype(np.uint8) * 255)
        im = im.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.MinFilter(5))
        return np.asarray(im) > 0


def foreground(rgb, bg):
    d = np.abs(rgb - bg).sum(-1)
    lum_r = (rgb.sum(-1) + 10) / (bg.sum(-1) + 10)
    ch = np.abs(np.log((rgb[..., 0] + 6) / (rgb[..., 1] + 6)) - np.log((bg[..., 0] + 6) / (bg[..., 1] + 6)))
    shadow = (lum_r < 0.95) & (lum_r > 0.35) & (ch < 0.06)
    return (d > 45) & ~shadow


def piece_mask(tpls, poses, dil=7):
    m = Image.new('L', (W, H), 0)
    for pn, tp in tpls.items():
        X, Y, th = poses[pn]
        card = Image.open(os.path.join(CACHE, 'cards', 'plate', tp.name + '.png')).getchannel('A') if not hasattr(tp, 'alpha') else tp.alpha
        tp.alpha = card
        lay = place(Image.merge('RGBA', (card, card, card, card)), tp.anchor, X, Y, th).getchannel('A')
        m = Image.fromarray(np.maximum(np.asarray(m), np.asarray(lay)))
    return np.asarray(m.filter(ImageFilter.MaxFilter(dil)) if dil else m) > 128


# ------------------------------------------------------------------ main loop
def main():
    t0 = time.time()
    plate_dir = os.path.join(CACHE, 'plate')
    clean = Image.open(os.path.join(CACHE, 'plate_clean.jpg')).convert('RGB')
    Hp2s, cal = calibrate(clean)
    print('calibration', cal, flush=True)
    json.dump(dict(H_plate_to_stage=Hp2s.tolist(), **cal), open(os.path.join(DATA, 'calibration.json'), 'w'), indent=1)
    bg = np.asarray(rectify(clean, Hp2s), np.float32)
    os_makedirs(os.path.join(CACHE, 'matte'))
    # --- acquisition on the first frame: every fiducial on the sheet
    f0 = rectify(Image.open(os.path.join(plate_dir, '0000.jpg')).convert('RGB'), Hp2s)
    G0 = gray(f0)
    poses, tpls, cards_now = {}, {}, {}
    for m in find_markers(G0):
        name = ID2CARD.get(m['id'])
        fam = fam_of(name) if name else None
        if fam is None or fam in poses:
            continue
        tp = Template(name)
        th = m['angle']
        c, s = math.cos(th), math.sin(th)
        mu, mv = tp.marker
        X = m['centre'][0] - (c * mu + s * mv)
        Y = m['centre'][1] - (-s * mu + c * mv)
        poses[fam], tpls[fam], cards_now[fam] = (X, Y, th), tp, name
    print('acquired', {k: cards_now[k] for k in cards_now}, flush=True)
    model = HandModel()
    # learn the skin model from a pass over the take (pixels in the foreground the pieces cannot explain)
    for i in range(0, N, 24):
        rgb = np.asarray(rectify(Image.open(os.path.join(plate_dir, '%04d.jpg' % i)).convert('RGB'), Hp2s), np.float32)
        fg = foreground(rgb, bg)
        model.learn(rgb, fg, piece_mask(tpls, poses, 25) | ~fg)
    hm_info = model.fit()
    print('skin model', hm_info, flush=True)
    out, prev = [], dict(poses)
    vel = {k: (0, 0, 0) for k in poses}
    tcache = {}
    for i in range(N):
        im = rectify(Image.open(os.path.join(plate_dir, '%04d.jpg' % i)).convert('RGB'), Hp2s)
        rgb = np.asarray(im, np.float32)
        G = gray(rgb)
        fg = foreground(rgb, bg)
        hand = model.matte(rgb, fg)
        hm_img = Image.fromarray(hand.astype(np.uint8) * 255)
        hm_img.resize((W // 4, H // 4), Image.BOX).save(os.path.join(CACHE, 'matte', '%04d.png' % i))
        mattes = [hand.astype(np.float32)]
        for _ in range(2):
            g = mattes[-1]
            h2, w2 = g.shape[0] // 2 * 2, g.shape[1] // 2 * 2
            mattes.append(g[:h2, :w2].reshape(h2 // 2, 2, w2 // 2, 2).mean((1, 3)))
        pyr = pyramid(G)
        rec = {}
        for fam in ('door', 'light', 'person', 'dog.body', 'dog.head'):
            if fam not in poses:
                continue
            X, Y, th = poses[fam]
            vx, vy, vt = vel[fam]
            pred = (X + 0.5 * vx, Y + 0.5 * vy, th + 0.5 * vt)
            # identity first: find and read the marker near where the prediction puts the tab
            m = decode_at(pyr[0][0], tpls[fam], pred)
            ident = m['id'] if m else None
            how = 'flow'
            if m is None:
                m = decode_at(pyr[0][0], tpls[fam], pred, r=130, near=60)
                how = 'reacquire' if m else 'flow-occluded'
                ident = m['id'] if m else None
            if m is not None:
                nm = ID2CARD[m['id']]
                if nm != cards_now[fam]:
                    cards_now[fam] = nm
                    how = 'swap'
                tp2 = tcache.get(nm) or Template(nm)
                tcache[nm] = tp2
                c, s_ = math.cos(m['angle']), math.sin(m['angle'])
                mxp = m['centre'][0] - (c * tp2.marker[0] + s_ * tp2.marker[1])
                myp = m['centre'][1] - (-s_ * tp2.marker[0] + c * tp2.marker[1])
                # the marker fixes the translation (and the angle, if the prediction is far off)
                th0 = pred[2] if abs(m['angle'] - pred[2]) < 0.08 else m['angle']
                c, s_ = math.cos(th0), math.sin(th0)
                pred = (m['centre'][0] - (c * tp2.marker[0] + s_ * tp2.marker[1]), m['centre'][1] - (-s_ * tp2.marker[0] + c * tp2.marker[1]), th0)
            nm = cards_now[fam]
            if nm not in tcache:
                tcache[nm] = Template(nm)
            tpls[fam] = tcache[nm]
            pose, info = lk(pyr, mattes, tpls[fam], pred, rot=(fam == 'dog.head'))
            # a flow step that runs away (support collapsed) is not trusted: hold the prediction
            if info['support'] < 0.15 or abs(pose[0] - pred[0]) > 40 or abs(pose[1] - pred[1]) > 40:
                pose, how = pred, how + '-held'
            vel[fam] = tuple(np.array(pose) - np.array(poses[fam]))
            vel[fam] = (float(np.clip(vel[fam][0], -20, 20)), float(np.clip(vel[fam][1], -20, 20)), float(np.clip(vel[fam][2], -.2, .2)))
            if how == 'swap':
                vel[fam] = (0.0, 0.0, 0.0)
            poses[fam] = pose
            # hand contact: matte coverage of a disc around the tab's grip point
            gp = to_stage(CARDS[nm]['tab']['grip'], CARDS[nm]['anchor'], *pose)
            gx, gy = int(gp[0]), int(gp[1])
            disc = hand[max(0, gy - 24):gy + 24, max(0, gx - 24):gx + 24]
            rec[fam] = dict(card=nm, X=round(pose[0], 2), Y=round(pose[1], 2), th=round(pose[2], 4), how=how,
                            resid=round(info['resid'], 2), support=round(info['support'], 3), marker=ident is not None,
                            held=bool(disc.size and disc.mean() > 0.2))
        out.append(dict(i=i, t=round(i / FPS, 4), pieces=rec, hand_px=int(hand.sum())))
        if i % 48 == 0:
            print('track', i, '%.1fs' % (time.time() - t0), {k: (v['card'], v['how']) for k, v in rec.items()}, flush=True)
    json.dump(dict(about=__doc__, calibration=cal, skin_model=hm_info, frames=out), open(os.path.join(DATA, 'tracked.json'), 'w'))
    events(out)
    print('tracked', len(out), '%.1fs' % (time.time() - t0))


def events(fr):
    ev = []
    last = {}
    still = {}
    for f in fr:
        for fam, p in f['pieces'].items():
            L = last.get(fam)
            if L is None:
                ev.append(dict(t=f['t'], i=f['i'], piece=fam, ev='acquired', card=p['card']))
            else:
                if p['card'] != L['card']:
                    ev.append(dict(t=f['t'], i=f['i'], piece=fam, ev='swap', frm=L['card'], to=p['card']))
                if p['held'] != L['held']:
                    ev.append(dict(t=f['t'], i=f['i'], piece=fam, ev='hand_on' if p['held'] else 'hand_off'))
                mv = math.hypot(p['X'] - L['X'], p['Y'] - L['Y']) > 3 or abs(p['th'] - L['th']) > 0.03
                st = still.get(fam, True)
                if mv and st:
                    ev.append(dict(t=f['t'], i=f['i'], piece=fam, ev='move', dx=round(p['X'] - L['X'], 1), dth=round(p['th'] - L['th'], 3)))
                still[fam] = not mv
            last[fam] = p
    with open(os.path.join(DATA, 'events.jsonl'), 'w') as fh:
        for e in ev:
            fh.write(json.dumps(e) + '\n')
    print('events', len(ev))


def evaluate():
    T = json.load(open(os.path.join(DATA, 'tracked.json')))['frames']
    P = json.load(open(os.path.join(CACHE, 'perform.json')))['frames']
    cal = json.load(open(os.path.join(DATA, 'calibration.json')))
    truth = json.load(open(os.path.join(DATA, 'camera_truth.json')))
    Ht = np.linalg.inv(np.array(truth['H_stage_to_plate']))
    Hc = np.array(cal['H_plate_to_stage'])
    grid = np.array([(x, y) for x in range(0, W + 1, 160) for y in range(0, H + 1, 120)], float)
    pp = apply_h(np.linalg.inv(Ht), grid)
    cal_err = np.hypot(*(apply_h(Hc, pp) - grid).T)
    res = dict(calibration_err_px=dict(mean=float(cal_err.mean()), max=float(cal_err.max())))
    per = {}
    for fam in ('dog.body', 'dog.head', 'person', 'door', 'light'):
        e, ea, idok, n = [], [], 0, 0
        for t, p in zip(T, P):
            if fam not in t['pieces']:
                continue
            a, b = t['pieces'][fam], p['pieces'][fam]
            n += 1
            idok += a['card'] == b['card']
            if a['card'] == b['card']:
                e.append(math.hypot(a['X'] - b['X'], a['Y'] - b['Y'])); ea.append(abs(a['th'] - b['th']))
        e = np.array(e); ea = np.degrees(np.array(ea))
        per[fam] = dict(frames=n, card_id_correct=round(idok / max(n, 1), 4), pos_err_px_mean=round(float(e.mean()), 3), pos_err_px_p95=round(float(np.percentile(e, 95)), 3),
                        pos_err_px_max=round(float(e.max()), 3), angle_err_deg_mean=round(float(ea.mean()), 3), angle_err_deg_max=round(float(ea.max()), 3))
    res['pieces'] = per
    # hand matte IoU in plate space (half resolution)
    Hs2p = np.linalg.inv(Hc); Hs2p /= Hs2p[2, 2]
    inv = np.linalg.inv(Hs2p); inv /= inv[2, 2]
    ious = []
    for i in range(0, N, 4):
        gt = np.asarray(Image.open(os.path.join(CACHE, 'gt_hand', '%04d.png' % i)).convert('L')) > 0
        m = Image.open(os.path.join(CACHE, 'matte', '%04d.png' % i)).resize((W, H), Image.BILINEAR)
        mp = m.transform((W, H), Image.PERSPECTIVE, tuple(inv.reshape(-1)[:8]), resample=Image.BILINEAR).resize((W // 2, H // 2))
        mp = np.asarray(mp) > 127
        # the matte lives on the sheet: compare only there
        if gt.sum() + mp.sum() < 50:
            continue
        ious.append((gt & mp).sum() / max((gt | mp).sum(), 1))
    res['hand_matte_iou'] = dict(frames=len(ious), mean=round(float(np.mean(ious)), 3), p10=round(float(np.percentile(ious, 10)), 3))
    json.dump(res, open(os.path.join(DATA, 'tracking_error.json'), 'w'), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    if '--eval' in sys.argv:
        evaluate()
    elif '--events' in sys.argv:
        events(json.load(open(os.path.join(DATA, 'tracked.json')))['frames'])
    else:
        main()
