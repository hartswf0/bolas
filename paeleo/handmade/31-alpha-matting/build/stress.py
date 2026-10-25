"""Stress fixture (the SCION hard-proof material kept as a regression clip): matted dog frames turning (the archive
turn, frames 13-22 and back) and rotating in-plane, over light, dark and moving checker backgrounds; written to
proof/stress_composite.mp4, plus one RGBA PNG per edge class in proof/rgba/ and an edge log in proof/edge_log.json."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, HERE := os.path.dirname(os.path.abspath(__file__)))
from lib_matte import resize_premult, premult_ok, blur
C = os.path.join(HERE, 'cache'); P0 = os.path.join(HERE, '../proof'); os.makedirs(P0 + '/rgba', exist_ok=True)
od = os.path.join(C, 'stress'); os.makedirs(od, exist_ok=True)


def dogP(i):
    z = np.load(os.path.join(C, 'dog/f%03d.npz' % i)); return z['P'].astype(np.float32)


seq = list(range(13, 23)) + list(range(22, 12, -1))
W, H = 960, 320
log = []
for k in range(96):
    P = dogP(seq[(k // 2) % len(seq)])
    P = resize_premult(P, int(P.shape[1] * 1.4), int(P.shape[0] * 1.4))
    ang = 25 * np.sin(k / 96 * 2 * np.pi)
    ch = [np.asarray(Image.fromarray(np.pad(P[..., c], 40)).rotate(ang, Image.BICUBIC)) for c in range(4)]
    R = np.stack(ch, 2); R[..., 3] = np.clip(R[..., 3], 0, 1); R[..., :3] = np.clip(R[..., :3], 0, R[..., 3:4])
    h, w = R.shape[:2]
    yy, xx = np.mgrid[:H, :W // 3]
    bgs = [np.ones((H, W // 3, 3)) * [.93, .9, .85], np.ones((H, W // 3, 3)) * [.05, .06, .12],
           ((((yy + k * 3) // 16 + (xx + k * 2) // 16) % 2)[..., None] * [.95, .25, .6] + .05)]
    tiles = []
    for bg in bgs:
        bg = bg.astype(np.float32).copy(); y0, x0 = (H - h) // 2, (W // 3 - w) // 2
        sub = bg[max(y0, 0):max(y0, 0) + h, max(x0, 0):max(x0, 0) + w]
        Rs = R[:sub.shape[0], :sub.shape[1]]
        bg[max(y0, 0):max(y0, 0) + h, max(x0, 0):max(x0, 0) + w] = Rs[..., :3] + sub * (1 - Rs[..., 3:4])
        tiles.append(bg)
    im = np.concatenate(tiles, 1)
    Image.fromarray((np.clip(im, 0, 1) * 255).astype(np.uint8)).save(os.path.join(od, 'k%03d.png' % k))
    # edge log: in the fractional band, the composite's deviation from (F over bg) is zero by construction if premult is
    # correct; we log the premult invariant and the band mean luminance of F vs the interior (halo = brighter rim)
    a = R[..., 3]; band = (a > .05) & (a < .6); core = a > .98
    F = R[..., :3] / np.maximum(a, 1e-4)[..., None]
    log.append(dict(k=k, src=seq[(k // 2) % len(seq)], rot_deg=round(float(ang), 2), premult_ok=premult_ok(R),
                    band_F_lum=round(float(F[band].mean()), 4), core_F_lum=round(float(F[core].mean()), 4)))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(od, 'k%03d.png'), '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p', '-crf', '24', '-movflags', '+faststart', os.path.join(P0, 'stress_composite.mp4')], check=True)
rimmed = [l for l in log if l['band_F_lum'] > l['core_F_lum'] + .08]
json.dump(dict(about='edge acceptance log: per stress frame, premultiplication invariant and rim-vs-core foreground luminance '
                     '(a rim brighter than the core by > 0.08 would be a bright halo carried from the sunlit gravel)',
               frames=log, n_premult_fail=sum(not l['premult_ok'] for l in log), n_bright_rim=len(rimmed)),
          open(os.path.join(P0, 'edge_log.json'), 'w'), indent=0)
# RGBA variants, one per edge class
def png(P, name):
    a = P[..., 3:4]; F = P[..., :3] / np.maximum(a, 1e-4)
    Image.fromarray((np.clip(np.concatenate([F, a], 2), 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(P0, 'rgba', name))
png(dogP(9), 'dog_f009_fur.png'); png(dogP(45), 'dog_f045_fur.png')
png(np.load(os.path.join(C, 'woman.npz'))['P'].astype(np.float32), 'woman_hair_fabric.png')
png(np.load(os.path.join(C, 'hand.npz'))['P'].astype(np.float32), 'hand_skin.png')
png(np.load(os.path.join(C, 'cloud/c10.npz'))['P'].astype(np.float32), 'cloud_smoke.png')
print('stress ok', len(log), 'premult fails', sum(not l['premult_ok'] for l in log), 'bright rims', len(rimmed))
