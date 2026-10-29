"""SCION-10 · render the 32 s scene: the set, the door and its light, the person, and the dog (the one hide, warped by MLS
from this frame's handles), depth-composited; spoken words as captions. Writes cache/frames/s_%04d.jpg and, measured from
each rendered frame's own buffers, cache/raw/%04d.json (where the dog's visible pixels are, where its head is, how high).

python3 render.py [first last]   (default all 768 frames, 3 worker processes)"""
import json, os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from multiprocessing import Pool

H_ = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H_)
import cam, dog, scene, person

R = os.path.normpath(os.path.join(H_, '..', '..', '..', '..'))
SCORE = json.load(open(os.path.join(H_, '..', '..', 'score', 'threshold-score.json')))
FR = SCORE['frames']
CACHE = os.path.join(H_, 'cache'); FRAMES = os.path.join(CACHE, 'frames'); RAW = os.path.join(CACHE, 'raw')
FONT_IT = os.path.join(R, 'tools/paeleo/fonts/f27.woff2')
FAMILY = os.environ.get('MLS_FAMILY', 'affine')

# what is said, when (from the score's voice timeline); captions are the person's words, never the dog's state
WORDS = [(1.0, 2.3, 'Come here.', 'call'), (3.4, 4.6, 'Come here!', 'call'), (7.4, 9.4, "It's all right.", 'soft'),
         (10.4, 11.6, "It's all right.", 'soft'), (26.4, 27.4, 'Come in.', 'soft')]


def ss(a, b, t):
    x = np.clip((t - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)


def door(t):
    ang = 0.10 + (1.75 - 0.10) * ss(6.2, 7.0, t)
    power = 1.3 + 3.4 * ss(6.2, 7.2, t)
    return ang, power


_W = {}


def init():
    _W['sets'] = {}; _W['bgd'] = {}
    for shot in ('wide', 'close'):
        cam.use(shot); S = scene.Set(); _W['sets'][shot] = S
        _W['bgd'][shot] = np.repeat(np.repeat(np.where(np.isinf(S.t), 1e9, S.t), 2, 0), 2, 1)
    _W['hide'] = dog.Hide(sample=1.0)
    _W['poses'] = json.load(open(os.path.join(CACHE, 'poses.json')))['frames']
    _W['font'] = ImageFont.truetype(FONT_IT, 30); _W['font_c'] = ImageFont.truetype(FONT_IT, 36)


def shade(S, P, N, rgb, ang, power):
    sky = (0.50 + 0.50 * np.clip(N[:, 2], 0, 1))[:, None] * scene.SKY_COL * 0.80 + np.clip(N @ scene.MOON, 0, 1)[:, None] * scene.MOON_COL * 0.75
    lamp = S.lamp_term(P, N, ang, power, nsamp=2)
    return rgb * (sky + lamp[:, None] * scene.LAMP_COL)


def shade_dog(S, P, N, rgb, ang, power):
    """the hide keeps its colour at dusk: the sky and moon light it by intensity with only a slight cool cast,
    the lamp through the door lights it warm."""
    sky = (0.50 + 0.50 * np.clip(N[:, 2], 0, 1)) * 0.36 + np.clip(N @ scene.MOON, 0, 1) * 0.40
    lamp = S.lamp_term(P, N, ang, power, nsamp=2)
    return rgb * (sky[:, None] * np.array([0.90, 0.95, 1.08]) + lamp[:, None] * scene.LAMP_COL) + 0.015


def splat_depth(xy, depth, rgba, lab, bgd2, ss=2):
    """nearest-last splat with a depth test against the set (walls, jambs, the sill) at 2x; returns layer and label map."""
    W, H = cam.W, cam.H
    x0, y0 = np.floor(xy.min(0)).astype(int) - 2; x1, y1 = np.ceil(xy.max(0)).astype(int) + 3
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W), min(y1, H)
    w, h = (x1 - x0) * ss, (y1 - y0) * ss
    px = (xy[:, 0] - x0) * ss; py = (xy[:, 1] - y0) * ss
    ix = np.floor(px).astype(np.int64); iy = np.floor(py).astype(np.int64)
    rank = np.empty(len(depth), np.int64); rank[np.argsort(-depth, kind='stable')] = np.arange(len(depth))
    idxs, rks, srcs = [], [], []
    for dx in range(2):
        for dy in range(2):
            jx, jy = ix + dx, iy + dy
            ok = (jx >= 0) & (jx < w) & (jy >= 0) & (jy < h)
            idxs.append((jy * w + jx)[ok]); rks.append(rank[ok]); srcs.append(np.nonzero(ok)[0])
    idx = np.concatenate(idxs); rk = np.concatenate(rks); src = np.concatenate(srcs)
    o = np.lexsort((rk, idx)); idx, src = idx[o], src[o]
    last = np.r_[idx[1:] != idx[:-1], True]
    idx, src = idx[last], src[last]
    gy, gx = idx // w, idx % w
    bgd = bgd2[gy + y0 * ss, gx + x0 * ss]
    vis = depth[src] < bgd + 0.01
    idx, src = idx[vis], src[vis]
    canvas = np.zeros((h * w, 4)); labm = np.zeros(h * w, np.int16)
    c = rgba[src]
    canvas[idx, :3] = c[:, :3] * c[:, 3:4]; canvas[idx, 3] = c[:, 3]
    labm[idx] = lab[src]
    canvas = canvas.reshape(h // ss, ss, w // ss, ss, 4).mean((1, 3))
    return (x0, y0, x1, y1), canvas, labm.reshape(h, w), src


def floor_mask(xy, shape=(cam.H, cam.W), blur=3.0, scale=0.5):
    from scipy import ndimage as ndi
    hh, ww = int(shape[0] * scale), int(shape[1] * scale)
    m = np.zeros((hh, ww))
    ix = (xy[:, 0] * scale).astype(int); iy = (xy[:, 1] * scale).astype(int)
    ok = (ix >= 0) & (ix < ww) & (iy >= 0) & (iy < hh)
    m[iy[ok], ix[ok]] = 1
    m = ndi.gaussian_filter(m, blur)
    m = np.clip(m * 2.2, 0, 1)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((shape[1], shape[0]), Image.BILINEAR), float) / 255


def frame(i):
    hide, poses = _W['hide'], _W['poses']
    f = FR[i]; t = f['t']; ps = poses[i]
    shot = cam.shot_at(t); cam.use(shot); S = _W['sets'][shot]
    ang, power = door(t)
    Q = np.array(ps['Q'])
    pts, N, _ = hide.warp(Q, FAMILY)
    # make normals face the camera side we see (a sheet has two sides)
    flip = (N @ cam.F) > 0
    Nv = np.where(flip[:, None], -N, N)
    drgb = shade_dog(S, pts, Nv, hide.rgb, ang, power)
    dog_xy = np.array([ps['pose']['cx'], ps['pose']['cy']])
    parts, pinfo = person.pose(t, f, dog_xy)
    pp, pn, pc = scene.person_points(parts, dens=int(32000 * (cam.SCALE / 200.0) ** 2))
    flipp = (pn @ cam.F) > 0
    pn = np.where(flipp[:, None], -pn, pn)
    prgb = shade(S, pp, pn, pc, ang, power)
    allP = np.r_[pts, pp]
    rgba = np.r_[np.c_[drgb, hide.a], np.c_[prgb, np.ones(len(pp))]]
    lab = np.r_[hide.lab.astype(np.int16), np.full(len(pp), 20, np.int16)]
    # shadows: from the lamp through the doorway onto the floor, and the soft contact darkness under bodies
    L = scene.LAMP
    lowz = allP[:, 2] < L[2] - 0.05
    Pl = allP[lowz]
    s = L[2] / (L[2] - Pl[:, 2])
    sh = L + (Pl - L) * s[:, None]; sh[:, 2] = 0
    shx, _ = cam.project(sh[sh[:, 0] > -0.2])
    shadow = floor_mask(shx[::3], blur=2.5)
    under = allP.copy(); under[:, 2] = 0
    ux, _ = cam.project(under[::4])
    ao = floor_mask(ux, blur=6.0) * 0.8
    img = S.compose(ang, power, shadow=shadow, ao=ao)
    lay = S.leaf_layer(ang, power)
    bgd2 = _W['bgd'][shot]
    if lay is not None:
        m, out = lay; img[m] = out[m, :3]
    xy, d = cam.project(allP)
    box, canvas, labm, _ = splat_depth(xy, d, rgba, lab, bgd2)
    x0, y0, x1, y1 = box
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - canvas[..., 3:4]) + canvas[..., :3]
    # grade: gentle tone curve, a little grain, a soft vignette
    rg = np.random.default_rng(i)
    yy, xx = np.mgrid[0:cam.H, 0:cam.W]
    vig = 1 - 0.28 * (((xx - 640) / 760) ** 2 + ((yy - 360) / 520) ** 2)
    img = np.clip(img * vig[..., None], 0, 1) ** (1 / 1.25)
    img = np.clip(img + rg.normal(0, 0.012, (cam.H, cam.W, 1)), 0, 1)
    im = Image.fromarray((img * 255).astype(np.uint8))
    for a, b, txt, kind in WORDS:
        if a <= t < b + 0.3:
            fade = min(1, (t - a) / 0.15, (b + 0.3 - t) / 0.3)
            dr = ImageDraw.Draw(im, 'RGBA')
            font = _W['font'] if shot == 'wide' else _W['font_c']
            col = (238, 228, 210, int(255 * fade)) if kind == 'call' else (215, 205, 190, int(200 * fade))
            tw = dr.textlength(txt, font=font)
            ph = cam.project(np.array([pinfo['head'] + np.array([0, 0, 0.25])]))[0][0]
            x = int(np.clip(ph[0] - tw / 2, 20, 1260 - tw)); y = int(np.clip(ph[1] - 40, 12, 700))
            dr.text((x, y), txt, font=font, fill=col)
    os.makedirs(FRAMES, exist_ok=True)
    im.save(os.path.join(FRAMES, f's_{i:04d}.jpg'), quality=92)
    # ---- measurements from this frame's own render buffers -----------------------------------------------------------
    dl = (labm > 0) & (labm < 20)
    yy2, xx2 = np.nonzero(dl)
    # the visible dog pixels (2x canvas -> screen px)
    sx = (xx2 / 2 + x0); sy = (yy2 / 2 + y0)
    headpix = (labm == 3)
    hy2, hx2 = np.nonzero(headpix)
    lab_d = hide.lab
    trunk = lab_d == 1; head = lab_d == 3
    raw = {'i': i, 't': t,
           'dog_px': int(dl.sum()), 'x_screen': float(sx.mean()) if len(sx) else None, 'y_screen': float(sy.mean()) if len(sy) else None,
           'head_px': int(headpix.sum()),
           'head_screen': [float(hx2.mean() / 2 + x0), float(hy2.mean() / 2 + y0)] if len(hx2) else None,
           'trunk_world': pts[trunk].mean(0).round(4).tolist(), 'head_world': pts[head].mean(0).round(4).tolist(),
           'nose_world': Q[dog.NAMES.index('nose')].round(4).tolist(), 'skull_world': Q[dog.NAMES.index('skull')].round(4).tolist(),
           'back_z': float(np.percentile(pts[trunk][:, 2], 95)), 'head_top_z': float(np.percentile(pts[head][:, 2], 95)),
           'paw_z': [float(Q[dog.NAMES.index(n)][2]) for n in ('fpaw_L', 'fpaw_R', 'hpaw_L', 'hpaw_R')],
           'min_x_world': float(pts[:, 0].min()), 'max_x_world': float(pts[:, 0].max()),
           'person_base': pinfo['base'].round(3).tolist(), 'person_sit': float(pinfo['sit']),
           'door_angle': float(ang), 'lamp_power': float(power), 'shot': shot, 'cam_scale': float(cam.SCALE), 'cam_origin': cam.ORIGIN.round(2).tolist()}
    os.makedirs(RAW, exist_ok=True)
    json.dump(raw, open(os.path.join(RAW, f'{i:04d}.json'), 'w'))
    return i


def main():
    a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, len(FR) - 1)
    idx = list(range(a, b + 1))
    if os.environ.get('MLS_SKIP_DONE'):
        idx = [i for i in idx if not (os.path.exists(os.path.join(RAW, f'{i:04d}.json')) and os.path.exists(os.path.join(FRAMES, f's_{i:04d}.jpg')))]
    t0 = time.time()
    procs = int(os.environ.get('MLS_PROCS', '3'))
    if procs <= 1:
        init(); [frame(i) for i in idx]
    else:
        with Pool(procs, initializer=init) as pool:
            for k, _ in enumerate(pool.imap_unordered(frame, idx, chunksize=4)):
                if k % 48 == 0: print(k, 'frames', round(time.time() - t0, 1), 's', flush=True)
    print('rendered', len(idx), 'in', round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main()
