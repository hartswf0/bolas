"""SCION 23 · paint the dog's texture atlas (and the person's) in code.

Each region is painted once, in gouache, for the view it serves: the torso for body views 0/45/90/135 deg, the head
for head views 0/45/90/135/180, leg segments, neck, tail and ears in near (lit) and far (shadowed) versions.
Torso and head shapes come from ellipsoid volumes laid out on the turnaround sheet (a guide for the silhouette and
the light, ray cast once here); the paint (bands, cool/warm shift, strokes, wash, grain, outline) is 2D.
Output: actor/dog.png + actor/dog.atlas (libgdx/Spine text atlas) + actor/dog.atlas.json (where each region sits).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ACTOR, CACHE
import paint as P
import turnaround as T

PPM = 640          # paint resolution (px per metre); the atlas keeps half of it
SS = 2
rng = np.random.default_rng(23)

TAN = np.array([0.80, 0.55, 0.30]); SADDLE = np.array([0.25, 0.175, 0.13]); CREAM = np.array([0.93, 0.83, 0.63])
MASKC = np.array([0.30, 0.205, 0.15]); NOSE = np.array([0.07, 0.055, 0.055]); EYE = np.array([0.13, 0.075, 0.04])
FAR = np.array([0.70, 0.67, 0.80])


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def ell(c, r, axes, cid, rot=None):
    return dict(c=c, r=r, ax=axes, id=cid)


def paint_plane(ells_dog, phi, albedo_fn, bounds, angle=0.0, flow=None, seed=0, round_px=9, dome_px=40, ray_w=0.35):
    """ray cast ellipsoids given in a local frame posed at view phi; bounds (x0,x1,y0,y1) metres in the plane"""
    fw, lf = T.view_axes(phi)
    A = np.array([fw, [0, 1, 0], lf])
    ells = []
    for e in ells_dog:
        R = np.asarray(e.get('R', np.eye(3)))
        ax = R @ A
        ells.append(dict(c=T.to_world(np.asarray(e['c']), phi), r=e['r'], ax=ax, id=e['id']))
    x0, x1, y0, y1 = bounds
    w = int((x1 - x0) * PPM); h = int((y1 - y0) * PPM)
    X = x0 + (np.arange(w) + 0.5) / PPM; Y = y1 - (np.arange(h) + 0.5) / PPM
    X, Y = np.meshgrid(X, Y)
    mask, ncam, hit, idx = P.raycast(ells, X, Y)
    # hit point and normal back in the local (dog) frame
    hl = hit @ A.T
    nw = ncam[..., 0:1] * P.EX + ncam[..., 1:2] * P.EY - ncam[..., 2:3] * P.EV
    nl = nw @ A.T
    alb = albedo_fn(hl, nl, idx, ncam)
    # one smooth body, not a pile of volumes: round the silhouette, then take the light from a soft height field
    m8 = Image.fromarray((mask * 255).astype(np.uint8))
    ms = np.asarray(m8.filter(ImageFilter.GaussianBlur(round_px)), np.float32) / 255 > 0.5
    ms = ms | (mask & (idx >= 3))
    hf = np.asarray(Image.fromarray((ms * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(dome_px)),
                    np.float32) / 255
    gy, gx = np.gradient(hf)
    n2 = np.dstack([-gx * dome_px * 1.6, gy * dome_px * 1.6, np.ones_like(hf)])
    n2 /= np.linalg.norm(n2, axis=2, keepdims=True)
    nn = np.where(mask[..., None], ray_w * ncam + (1 - ray_w) * n2, n2)
    nn /= np.linalg.norm(nn, axis=2, keepdims=True)
    # fill albedo into the rounded creases from the neighbours
    am = mask.astype(np.float32)
    num = np.dstack([np.asarray(Image.fromarray(((alb[..., c] * am) * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(6)), np.float32) / 255 for c in range(3)])
    den = np.asarray(Image.fromarray((am * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    alb = np.where(mask[..., None], alb, num / np.maximum(den[..., None], 1e-3))
    col = P.shade(nn, alb)
    col = np.where((idx == 4)[..., None] & ((ncam @ P.LIGHT) > 0.9)[..., None], 0.9, col)
    mask = ms
    alpha = mask.astype(np.float32)
    col, alpha = P.finish(col, alpha, np.random.default_rng(seed), angle=angle, flow=flow, outline=4,
                          stroke_len=(14, 34), stroke_w=(3, 6), amount=0.26, density=3.0)
    col[~mask] = 0
    return col, alpha, (x0, y1)


def torso_albedo(hl, nl, idx, ncam):
    nu = nl[..., 1]
    x = hl[..., 0]
    nz = P.value_noise(nu.shape[0], nu.shape[1], 9, rng) - 0.5
    sad = sstep(0.18, 0.42, nu + 0.18 * nz) * sstep(-0.47, -0.36, x) * (1 - sstep(0.12, 0.24, x + 0.05 * nz))
    belly = sstep(-0.12, -0.42, nu + 0.15 * nz)
    bib = sstep(0.27, 0.36, x + 0.03 * nz) * (1 - sstep(0.15, 0.5, nu))
    cr = np.clip(belly + bib, 0, 1)
    a = TAN * (1 - cr[..., None]) + CREAM * cr[..., None]
    a = a * (1 - sad[..., None]) + SADDLE * sad[..., None]
    return a


def head_albedo(hl, nl, idx, ncam):
    nu = nl[..., 1]; x = hl[..., 0]
    nz = P.value_noise(nu.shape[0], nu.shape[1], 6, rng) - 0.5
    a = np.zeros(hl.shape) + TAN
    jaw = sstep(-0.05, -0.4, nu + 0.2 * nz) * sstep(0.05, 0.12, x)
    a = a * (1 - jaw[..., None]) + CREAM * jaw[..., None]
    top = sstep(0.25, 0.65, nu + 0.2 * nz)
    mask_m = top * sstep(0.10, 0.16, x)                                 # dark bridge of the muzzle
    a = a * (1 - mask_m[..., None]) + MASKC * mask_m[..., None]
    back = sstep(0.0, -0.06, x + 0.03 * nz) * sstep(0.0, 0.5, nu + 0.4)  # darker nape
    a = a * (1 - 0.6 * back[..., None]) + SADDLE * 0.6 * back[..., None]
    a = np.where((idx == 3)[..., None], NOSE, a)
    a = np.where((idx == 4)[..., None], EYE, a)
    return a


def torso_ells():
    J, _, _ = T.pose3d({})
    return [dict(c=(0.10, 0.475, 0), r=(0.235, 0.165, 0.135), id=0),
            dict(c=(0.255, 0.435, 0), r=(0.105, 0.14, 0.115), id=0),
            dict(c=(-0.08, 0.49, 0), r=(0.19, 0.118, 0.106), id=0),
            dict(c=(-0.245, 0.48, 0), r=(0.14, 0.135, 0.125), id=0),
            dict(c=(-0.22, 0.43, 0.045), r=(0.14, 0.14, 0.09), id=0),
            dict(c=(-0.22, 0.43, -0.045), r=(0.14, 0.14, 0.09), id=0),
            dict(c=(0.21, 0.55, 0.0), r=(0.10, 0.07, 0.11), id=0)]


def rz(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])


def head_ells(k=1.2):
    E = _head_ells()
    for e in E:
        e['c'] = tuple(k * v for v in e['c']); e['r'] = tuple(k * v for v in e['r'])
    return E


def _head_ells():
    return [dict(c=(0.06, 0.012, 0), r=(0.088, 0.076, 0.073), id=1),
            dict(c=(0.168, -0.024, 0), r=(0.098, 0.052, 0.05), id=2, R=rz(-6)),
            dict(c=(0.10, -0.03, 0), r=(0.08, 0.058, 0.066), id=2),
            dict(c=(0.255, -0.02, 0), r=(0.021, 0.018, 0.022), id=3),
            dict(c=(0.128, 0.022, 0.041), r=(0.013, 0.012, 0.010), id=4),
            dict(c=(0.128, 0.022, -0.041), r=(0.013, 0.012, 0.010), id=4)]


def crop(col, alpha, origin, pad=8):
    ys, xs = np.nonzero(alpha > 0.01)
    y0, y1 = max(0, ys.min() - pad), min(alpha.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(alpha.shape[1], xs.max() + pad + 1)
    ox, oy = origin
    return col[y0:y1, x0:x1], alpha[y0:y1, x0:x1], (ox + x0 / PPM, oy - y0 / PPM)


def paint_capsule(L, r0, r1, base, far, light_angle, bulge=0.0, tip=None, back_stripe=None, seed=0, stroke_angle=0.0,
                  side_outline=True, stripe_side=-1, soft_end=False, flat=0.0):
    (X, Y), alpha, ncam, (x0, y1, w, h) = P.capsule_field(L, r0, r1, PPM, pad=10, bulge=bulge)
    alb = np.zeros(alpha.shape + (3,)) + base
    if tip is not None:
        tcol, tfrom = tip
        tw = sstep(tfrom * L, L + r1 * 0.5, X)
        alb = alb * (1 - tw[..., None]) + np.asarray(tcol) * tw[..., None]
    if back_stripe is not None:
        sw = sstep(0.05, 0.7, stripe_side * Y / max(r0, r1))
        alb = alb * (1 - sw[..., None]) + np.asarray(back_stripe) * sw[..., None]
    col = P.shade(ncam, alb, light=P.light_for(light_angle), up_axis=P.vec_for(light_angle, (0, 1, 0)))
    if flat: col = col * (1 - flat) + alb * 0.86 * flat   # flatter: painted, not turned on a lathe
    if far: col = col * FAR
    ow = None
    if side_outline:   # outline the long sides only: the round ends tuck under the neighbouring part
        ow = np.clip(1 - np.maximum(sstep(0.0, -0.6 * r0, X), sstep(L, L + 0.6 * r1, X)), 0, 1)
    col, alpha = P.finish(col, alpha, np.random.default_rng(seed), angle=stroke_angle, outline=4,
                          stroke_len=(8, 20), stroke_w=(2, 4), amount=0.2, density=3.0, outline_w=ow)
    if soft_end:   # the distal end melts into the next segment: no dowel seam at the knee or hock
        alpha = alpha * (1 - sstep(L - 0.1 * r1, L + 0.95 * r1, X))
    return col, alpha, (x0, y1)


def paint_ear(kind, seed):
    L = 0.115
    bw = 0.041 if kind != 'back' else 0.052
    w = int((L + 0.04) * PPM); h = int((2 * bw + 0.04) * PPM)
    x0, y1 = -0.02, bw + 0.02
    X = x0 + (np.arange(w) + 0.5) / PPM; Y = y1 - (np.arange(h) + 0.5) / PPM
    X, Y = np.meshgrid(X, Y)
    t = np.clip(X / L, 0, 1)
    half = bw * (1 - t) ** 0.85 * (1 + 0.25 * np.sin(np.pi * t))
    inside = (X > -0.012) & (X < L) & (np.abs(Y + (0.004 if kind != 'back' else 0)) < half + 0.012 * (X < 0))
    alpha = inside.astype(np.float32)
    v = np.clip(Y / np.maximum(half, 1e-4), -1, 1)
    ncam = np.stack([np.zeros_like(v) + 0.1, v * 0.6, np.sqrt(np.clip(1 - 0.36 * v * v, 0, 1))], -1)
    if kind == 'back':
        alb = np.zeros(alpha.shape + (3,)) + SADDLE * 1.15
        rimw = sstep(0.6, 0.95, np.abs(v))
        alb = alb * (1 - rimw[..., None]) + TAN * 0.8 * rimw[..., None]
    else:
        alb = np.zeros(alpha.shape + (3,)) + TAN * 0.9
        inner = sstep(0.1, -0.3, v) * sstep(0.05, 0.25, t) * (1 - sstep(0.8, 0.95, t))
        alb = alb * (1 - inner[..., None]) + np.array([0.86, 0.66, 0.55]) * inner[..., None]
        tipd = sstep(0.55, 0.9, t)
        alb = alb * (1 - 0.7 * tipd[..., None]) + SADDLE * 0.7 * tipd[..., None]
    col = P.shade(ncam, alb, light=P.light_for(90))
    if kind == 'side_far': col = col * FAR
    col, alpha = P.finish(col, alpha, np.random.default_rng(seed), angle=0, outline=4, stroke_len=(6, 14),
                          stroke_w=(2, 3), amount=0.18)
    return col, alpha, (x0, y1)


def main():
    regions = {}

    def put(name, col, alpha, origin, kind, ref=None):
        c2, a2 = P.downsample(col, alpha, SS)
        regions[name] = dict(img=P.to_image(c2, a2), origin=origin, kind=kind, ref=ref)

    for phi in (0, 45, 90, 135):
        col, al, org = paint_plane(torso_ells(), phi, torso_albedo, (-0.62, 0.62, 0.05, 0.85), angle=0.0,
                                   seed=100 + phi)
        col, al, org = crop(col, al, org)
        put('torso_%d' % phi, col, al, org, 'plane', 'root')
        print('torso', phi, al.shape)
    for psi in (0, 45, 68, 90, 112, 135, 180):
        col, al, org = paint_plane(head_ells(), psi, head_albedo, (-0.38, 0.38, -0.2, 0.24), seed=200 + psi,
                                   round_px=5, dome_px=22, ray_w=0.5)
        col, al, org = crop(col, al, org)
        put('head_%d' % psi, col, al, org, 'plane', 'head')
        print('head', psi, al.shape)
    LEG = dict(up_f=(0.18, 0.064, 0.031, TAN, None), lo_f=(0.19, 0.031, 0.021, TAN, None),
               paw_f=(0.075, 0.027, 0.031, CREAM * 0.92, None), th_h=(0.20, 0.09, 0.04, TAN, None),
               sh_h=(0.21, 0.041, 0.022, TAN, None), mt_h=(0.12, 0.023, 0.019, TAN * 0.95 + CREAM * 0.05, None),
               paw_h=(0.07, 0.026, 0.03, CREAM * 0.92, None))
    k = 0
    for nm, (L, r0, r1, base, _) in LEG.items():
        for nf in ('near', 'far'):
            col, al, org = paint_capsule(L, r0, r1, base, nf == 'far', -90, seed=300 + k, stroke_angle=0,
                                         soft_end=not nm.startswith('paw'), flat=0.45)
            put('%s_%s' % (nm, nf), col, al, org, 'axis')
            k += 1
    for nm, sgn in (('neck_dL', -1), ('neck_dR', 1)):   # dorsal stripe on the -y (facing left) or +y side
        col, al, org = paint_capsule(0.19, 0.082, 0.06, TAN, False, 120 if sgn < 0 else 60, seed=400,
                                     side_outline=True, back_stripe=SADDLE * 1.1, stripe_side=sgn)
        put(nm, col, al, org, 'axis')
    col, al, org = paint_capsule(0.38, 0.042, 0.026, TAN * 0.95, False, -40, bulge=0.75, tip=(SADDLE, 0.72),
                                 seed=401)
    put('tail', col, al, org, 'axis')
    for kind in ('side_near', 'side_far', 'back'):
        col, al, org = paint_ear(kind, 500 + len(kind))
        put('ear_' + kind, col, al, org, 'axis')
    import person_atlas
    for name, (col, al, org, kind) in person_atlas.paint_all(PPM).items():
        put(name, col, al, org, kind)
    pack(regions)


def pack(regions):
    """shelf-pack all regions into one page; write the libgdx text atlas and a JSON with each region's frame"""
    items = sorted(regions.items(), key=lambda kv: -kv[1]['img'].size[1])
    W = 2048; x = y = 2; shelf = 0; pos = {}
    for name, r in items:
        w, h = r['img'].size
        if x + w + 2 > W: x = 2; y += shelf + 2; shelf = 0
        pos[name] = (x, y); x += w + 2; shelf = max(shelf, h)
    Hh = y + shelf + 2
    page = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    meta = {'page': 'actors.png', 'size': [W, Hh], 'ppm_atlas': PPM // SS, 'units': 'skeleton cm; 1 atlas px = %.4f cm' % (100 / (PPM // SS)), 'regions': {}}
    lines = ['', 'actors.png', 'size: %d,%d' % (W, Hh), 'format: RGBA8888', 'filter: Linear,Linear', 'repeat: none']
    for name, r in regions.items():
        px, py = pos[name]; w, h = r['img'].size
        page.paste(r['img'], (px, py))
        ox, oy = r['origin']
        meta['regions'][name] = dict(xy=[px, py], size=[w, h], kind=r['kind'], ref=r['ref'],
                                     origin_m=[round(ox, 5), round(oy, 5)])
        lines += [name, '  rotate: false', '  xy: %d, %d' % (px, py), '  size: %d, %d' % (w, h),
                  '  orig: %d, %d' % (w, h), '  offset: 0, 0', '  index: -1']
    os.makedirs(ACTOR, exist_ok=True)
    page.save(os.path.join(ACTOR, 'actors.png'), optimize=True)
    open(os.path.join(ACTOR, 'actors.atlas'), 'w').write('\n'.join(lines) + '\n')
    json.dump(meta, open(os.path.join(ACTOR, 'actors.atlas.json'), 'w'), indent=1)
    print('atlas', W, Hh, len(regions), 'regions')


if __name__ == '__main__':
    main()
