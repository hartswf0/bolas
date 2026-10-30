"""SCION 37 proof: the weight maps, and linear blend skinning against dual-quaternion skinning on the film's own motion.
Measures, for every scene frame, under LBS and under DQS (same weights, same skeleton, same pose):
  volume   the enclosed volume of the whole skin relative to the bind pose
  neck     mean radius of the neck blend ring (vertices shared by neck1/neck2/head) about the skinned neck axis, vs bind
  hock/stifle/elbow  the same ring measure at the hind and fore leg joints
  det      the smallest determinant of an LBS-blended matrix (1 = rigid, <1 = the candy wrapper)
Writes ../proof/skinning_metrics.json, ../proof/weights_*.png, ../proof/lbs_vs_dqs_*.png and a side-by-side clip."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
import rig, raster

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PROOF = os.path.join(ROOT, 'proof'); os.makedirs(PROOF, exist_ok=True)
CACHE = os.path.join(HERE, 'cache')
PF = dict(np.load(os.path.join(CACHE, 'perform.npz')))
D = np.load(os.path.join(ROOT, 'assets', 'mesh', 'dog.npz'))
V, F, idx, w, Wfull, bones = D['V'], D['F'], D['idx'], D['w'], D['W'], list(D['bones'])
SK = rig.dog_skeleton()
COAT = np.asarray(Image.open(os.path.join(ROOT, 'assets', 'texture', 'coat.png')), float) / 255
FONT = '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf'

def font(s): return ImageFont.truetype(FONT, s)


def pose_mats(i):
    pose = {n: PF['dog_rot'][i, j] for j, n in enumerate(SK.names)}
    G = SK.fk(pose, PF['dog_root'][i]); return G, SK.skin_mats(G)

def volume(P):
    return np.einsum('ij,ij->i', P[F[:, 0]], np.cross(P[F[:, 1]], P[F[:, 2]])).sum() / 6

RINGS = {'neck': (('neck1', 'neck2', 'head'), 'neck1', 'head'), 'hock L': (('stifleL', 'hockL'), 'stifleL', 'hpawL'),
         'stifle L': (('hipL', 'stifleL'), 'hipL', 'hockL'), 'elbow L': (('shoulderL', 'elbowL'), 'shoulderL', 'wristL'),
         'hip L': (('pelvis', 'hipL'), 'hipL', 'stifleL')}

def ring_sel(names):
    js = [bones.index(n) for n in names]
    s = Wfull[:, js]
    # vertices genuinely shared: at least two of the bones carry 20 % or more, and together almost all the weight
    return ((s > .2).sum(1) >= 2) & (s.sum(1) > .85)

RSEL = {k: ring_sel(v[0]) for k, v in RINGS.items()}

def ring_radius(P, G, key):
    _, a, b = RINGS[key]
    pa, pb = G[SK.ix[a], :3, 3], G[SK.ix[b], :3, 3]
    # distance from the chain's polyline a -> mid joint -> b
    names = RINGS[key][0]
    pts = [G[SK.ix[n], :3, 3] for n in names] + [pb]
    Q = P[RSEL[key]]
    dmin = np.full(len(Q), np.inf)
    for p0, p1 in zip(pts[:-1], pts[1:]):
        dmin = np.minimum(dmin, raster_seg(Q, p0, p1))
    return dmin.mean()

def raster_seg(Q, a, b):
    ba = b - a; t = np.clip(((Q - a) @ ba) / max(ba @ ba, 1e-12), 0, 1)
    return np.linalg.norm(Q - (a + t[:, None] * ba), axis=1)


def metrics():
    G0 = SK.fk({}); v0 = volume(V)
    r0 = {k: ring_radius(V, G0, k) for k in RINGS}
    rows = []
    for i in range(len(PF['dog_rot'])):
        G, S = pose_mats(i)
        L = rig.lbs(V, idx, w, S); Q = rig.dqs(V, idx, w, S)
        det = rig.blend_shrink(idx, w, S)
        row = {'i': i, 't': round(i / 24, 3), 'lbs_volume': volume(L) / v0, 'dqs_volume': volume(Q) / v0, 'min_det': float(det.min())}
        for k in RINGS:
            row['lbs_' + k] = ring_radius(L, G, k) / r0[k]; row['dqs_' + k] = ring_radius(Q, G, k) / r0[k]
        rows.append(row)
    summ = {}
    for k in ['volume'] + list(RINGS):
        lb = np.array([r['lbs_' + k] for r in rows]); dq = np.array([r['dqs_' + k] for r in rows])
        j = int(np.argmin(lb))
        summ[k] = {'lbs_min': round(float(lb.min()), 3), 'at_t': rows[j]['t'], 'dqs_at_that_frame': round(float(dq[j]), 3),
                   'dqs_min': round(float(dq.min()), 3), 'dqs_max': round(float(dq.max()), 3)}
    dets = np.array([r['min_det'] for r in rows]); j = int(np.argmin(dets))
    summ['lbs_min_blend_det'] = {'value': round(float(dets.min()), 3), 'at_t': rows[j]['t']}
    json.dump({'about': __doc__, 'summary': summ, 'frames': [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in rows]},
              open(os.path.join(PROOF, 'skinning_metrics.json'), 'w'), indent=0)
    print(json.dumps(summ, indent=1))
    return summ


# ------------------------------------------------------------------ pictures
PAL = np.array([[.90, .30, .25], [.95, .65, .20], [.95, .90, .35], [.45, .80, .35], [.25, .70, .80], [.40, .45, .95],
                [.75, .40, .90], [.90, .45, .65], [.60, .60, .60]])

def bone_colors():
    C = np.zeros((len(bones), 3))
    groups = {'pelvis': 0, 'spine': 1, 'chest': 2, 'neck1': 3, 'neck2': 4, 'head': 5, 'earL': 6, 'earR': 6, 'tail1': 7, 'tail2': 0,
              'tail3': 3}
    for j, b in enumerate(bones):
        if b in groups: C[j] = PAL[groups[b]]
        else:
            base = b[:-1]; order = ['shoulder', 'elbow', 'wrist', 'fpaw', 'hip', 'stifle', 'hock', 'hpaw']
            C[j] = PAL[order.index(base) % 8] * (1. if b.endswith('L') else .8)
    return C

def ornament(R):
    """the printed test ornament, evaluated per pixel on the bind-pose position: rings every 4 cm along the body,
    a dorsal line and a line along each flank"""
    c = np.tile([.86, .80, .70], (len(R), 1))
    ring = ((R[:, 0] * 25) % 1) < .28; c[ring] = [.78, .20, .14]
    dors = (np.abs(R[:, 2]) < .018) & (R[:, 1] > .50); c[dors] = [.12, .26, .78]
    flank = (np.abs(np.abs(R[:, 2]) - .06) < .012) & (R[:, 0] > .28) & (R[:, 1] > .55); c[flank] = [.10, .55, .25]
    return c


def draw(P, cols, cam, bg=(.07, .07, .08), facets=True):
    xy, z = cam.project(P); tri, b, _ = raster.rasterize(xy, z, F, cam.W, cam.H)
    m = tri >= 0
    if isinstance(cols, str):
        cols = None; R = np.einsum('pi,pik->pk', b[m], V[F[tri[m]]])
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    Lt = np.array([.35, .8, .5]); Lt /= np.linalg.norm(Lt)
    sh = (.38 + .62 * np.clip(fn[tri[m]] @ Lt, 0, 1))[:, None]
    c = ornament(R) if cols is None else np.einsum('pi,pik->pk', b[m], cols[F[tri[m]]])
    img = np.tile(np.array(bg, float), (cam.H * cam.W, 1)); img[m] = c * sh
    return img.reshape(cam.H, cam.W, 3), m.reshape(cam.H, cam.W)

def coat_cols():
    u = np.clip(D['UV'][:, 0], 0, 1) * (COAT.shape[1] - 1); v = (1 - np.clip(D['UV'][:, 1], 0, 1)) * (COAT.shape[0] - 1)
    return np.stack([ndimage.map_coordinates(COAT[..., c], [v, u], order=1) for c in range(3)], 1)

def to_im(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def heat(x):
    x = np.clip(x, 0, 1)[:, None]
    return np.clip(np.concatenate([1.6 * x, 1.6 * x - .5, .25 + 1.2 * x - 1.6 * x * x + 0 * x], 1), 0, 1) * .95 + .05

def weight_pictures():
    C = Wfull @ bone_colors()
    cams = [raster.Camera((0, .55, 2.6), (-.02, .48, 0), 1250, 900, 560), raster.Camera((1.3, 1.1, 1.9), (0, .45, 0), 1100, 900, 560)]
    for k, cam in enumerate(cams):
        im, _ = draw(V, C, cam); to_im(im).save(os.path.join(PROOF, 'weights_all_%d.png' % k))
    for b in ('neck2', 'hipL', 'shoulderL', 'stifleL', 'tail1', 'head'):
        im, _ = draw(V, heat(Wfull[:, bones.index(b)]), cams[0]); to_im(im).save(os.path.join(PROOF, 'weights_%s.png' % b))


def close_cam(i, dist=1.9, el=.55, side=1.):
    G, _ = pose_mats(i); c = G[SK.ix['spine'], :3, 3] * .5 + G[SK.ix['neck2'], :3, 3] * .5
    eye = c + np.array([.9 * side, el, dist])
    return raster.Camera(eye, c + [0, -.05, 0], 1100, 640, 480)

def compare(i, tag, cam=None):
    G, S = pose_mats(i); cam = cam or close_cam(i)
    L = rig.lbs(V, idx, w, S); Q = rig.dqs(V, idx, w, S)
    det = rig.blend_shrink(idx, w, S)
    cc = coat_cols()
    a, _ = draw(L, cc, cam); b, _ = draw(Q, cc, cam)
    hmap = heat(np.clip((1 - det) / .6, 0, 1)) * .8 + cc * .2
    c, _ = draw(L, hmap, cam)
    ims = [to_im(x) for x in (a, b, c)]
    for im, lab in zip(ims, ('LBS', 'DQS (in the film)', 'LBS volume loss: 1 - det')):
        ImageDraw.Draw(im).text((14, 10), lab + '   t=%.2fs' % (i / 24), font=font(20), fill=(240, 220, 160))
    out = Image.new('RGB', (cam.W * 3, cam.H)); [out.paste(im, (k * cam.W, 0)) for k, im in enumerate(ims)]
    out.save(os.path.join(PROOF, 'lbs_vs_dqs_%s.png' % tag))
    return ims

def stress():
    """the joint stress test (extreme-pose tester): the neck twists about its own axis to 160 degrees while the head
    turns back, and the left forearm twists 140 degrees; LBS on the left, DQS on the right, in the bind-relative frame"""
    tmp = os.path.join(CACHE, 'stress'); os.makedirs(tmp, exist_ok=True)
    # a printed test ornament on the skin (rings every 3 cm along the body, a dorsal and a ventral line), like the
    # sleeve tattoo of the lineage's hard proof: twisting and collapse become visible as the print winds and pinches
    cc = 'ornament'
    cam = raster.Camera((.50, .86, 1.30), (.40, .70, 0), 1250, 640, 480)
    out = {}
    nfr = 48
    for k in range(nfr):
        u = np.sin(np.pi * k / (nfr - 1)) ** 2
        pose = {'neck2': rig.euler(roll=u * 2.8)}
        G = SK.fk(pose); S = SK.skin_mats(G)
        L = rig.lbs(V, idx, w, S); Q = rig.dqs(V, idx, w, S)
        a, _ = draw(L, cc, cam); b, _ = draw(Q, cc, cam)
        ia, ib = to_im(a), to_im(b)
        G0 = SK.fk({}); rl = ring_radius(L, G, 'neck') / ring_radius(V, G0, 'neck'); rq = ring_radius(Q, G, 'neck') / ring_radius(V, G0, 'neck')
        ImageDraw.Draw(ia).text((14, 10), 'LBS  neck twist %3d deg  ring %.2f' % (np.degrees(u * 2.8), rl), font=font(18), fill=(240, 220, 160))
        ImageDraw.Draw(ib).text((14, 10), 'DQS  neck twist %3d deg  ring %.2f' % (np.degrees(u * 2.8), rq), font=font(18), fill=(240, 220, 160))
        o = Image.new('RGB', (1280, 480)); o.paste(ia, (0, 0)); o.paste(ib, (640, 0)); o.save(os.path.join(tmp, '%04d.jpg' % k), quality=90)
        if k == nfr // 2:
            o.save(os.path.join(PROOF, 'stress_twist_160.png')); out = {'neck_twist_deg': round(float(np.degrees(u * 2.8)), 1),
                                                                      'lbs_neck_ring': round(float(rl), 3), 'dqs_neck_ring': round(float(rq), 3),
                                                                      'lbs_min_det': round(float(rig.blend_shrink(idx, w, S).min()), 3)}
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '16', '-i', os.path.join(tmp, '%04d.jpg'), '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-crf', '26', '-movflags', '+faststart', os.path.join(PROOF, 'stress_test_twist.mp4')], check=True)
    for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
    json.dump(out, open(os.path.join(PROOF, 'stress_twist.json'), 'w'), indent=1); print('stress', out)


def clip():
    """a side-by-side clip of the joint stress passages: the look back (7.3-9.0 s) and the lie-down (23.6-25.2 s)"""
    tmp = os.path.join(CACHE, 'proofclip'); os.makedirs(tmp, exist_ok=True)
    k = 0; cc = coat_cols()
    for i in list(range(170, 216)) + list(range(566, 606)):
        G, S = pose_mats(i)
        cam = close_cam(i, side=1. if i < 400 else -.6)
        L = rig.lbs(V, idx, w, S); Q = rig.dqs(V, idx, w, S)
        a, _ = draw(L, cc, cam); b, _ = draw(Q, cc, cam)
        ia, ib = to_im(a), to_im(b)
        ImageDraw.Draw(ia).text((14, 10), 'linear blend  %.2fs' % (i / 24), font=font(20), fill=(240, 220, 160))
        ImageDraw.Draw(ib).text((14, 10), 'dual quaternion', font=font(20), fill=(240, 220, 160))
        o = Image.new('RGB', (1280, 480)); o.paste(ia, (0, 0)); o.paste(ib, (640, 0)); o.save(os.path.join(tmp, '%04d.jpg' % k), quality=90); k += 1
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-i', os.path.join(tmp, '%04d.jpg'), '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-crf', '26', '-movflags', '+faststart', os.path.join(PROOF, 'lbs_vs_dqs_stress.mp4')], check=True)
    for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))


if __name__ == '__main__':
    what = sys.argv[1:] or ['metrics', 'weights', 'compare', 'stress', 'clip']
    if 'metrics' in what: metrics()
    if 'weights' in what: weight_pictures()
    if 'compare' in what:
        compare(186, 'lookback'); compare(600, 'lying'); compare(150, 'refusal_lie')
    if 'stress' in what: stress()
    if 'clip' in what: clip()
