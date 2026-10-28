"""SCION-10 · proof strips: crops of the rendered scene around the dog through the passages the critics look at (the turn
away, the turn back, the approach, the lie-down, the look-in), and the weight-exponent comparison (same handles, alpha
1.0 / 1.3 / 1.6 / 2.0) that set ALPHA. Writes ../proof/*_strip.jpg."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
P = os.path.join(H, '..', 'proof'); FR = os.path.join(H, 'cache', 'frames')
RAW = os.path.join(H, 'cache', 'raw')


def crop_strip(idx, name, w=320, h=220, cols=6):
    ims = []
    for i in idx:
        r = json.load(open(os.path.join(RAW, f'{i:04d}.json')))
        cx, cy = r['x_screen'], r['y_screen'] - 20
        im = Image.open(os.path.join(FR, f's_{i:04d}.jpg'))
        x0 = int(np.clip(cx - w / 2, 0, 1280 - w)); y0 = int(np.clip(cy - h / 2, 0, 720 - h))
        c = im.crop((x0, y0, x0 + w, y0 + h)); ImageDraw.Draw(c).text((6, 4), f'{i / 24:.2f} s', fill=(255, 255, 255))
        ims.append(c)
    rows = (len(ims) + cols - 1) // cols
    S = Image.new('RGB', (w * cols, h * rows))
    for k, c in enumerate(ims): S.paste(c, ((k % cols) * w, (k // cols) * h))
    S.save(os.path.join(P, name), quality=88)


def alpha_strip():
    import dog, cam
    hide = dog.Hide(sample=1.0)
    poses = json.load(open(os.path.join(H, 'cache', 'poses.json')))['frames']
    ims = []
    for i in (30, 600):
        Q = np.array(poses[i]['Q'])
        for a in (1.0, 1.3, 1.6, 2.0):
            pts, N, _ = hide.warp(Q, 'affine', alpha=a)
            N = np.where(((N @ cam.F) > 0)[:, None], -N, N)
            l = np.array([-0.3, -0.5, 0.8]); l /= np.linalg.norm(l)
            rgba = np.c_[hide.rgb * (np.clip(N @ l, 0, 1) * 0.6 + 0.45)[:, None], hide.a]
            keep = (cam.SCALE, cam.ORIGIN.copy(), cam.W, cam.H)
            cam.SCALE = 260; cam.ORIGIN = np.zeros(2)
            c, _ = cam.project(np.array([[poses[i]['pose']['cx'], poses[i]['pose']['cy'], 0.3]]))
            cam.ORIGIN = np.array([160.0, 120.0]) - c[0]; cam.W, cam.H = 320, 240
            img = np.ones((240, 320, 3)) * 0.45
            xy, d = cam.project(pts); cam.over(img, cam.splat(xy, d, rgba))
            cam.SCALE, cam.ORIGIN, cam.W, cam.H = keep
            im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
            ImageDraw.Draw(im).text((6, 4), f'frame {i}  alpha {a}', fill=(255, 255, 255))
            ims.append(im)
    S = Image.new('RGB', (320 * 4, 240 * 2))
    for k, c in enumerate(ims): S.paste(c, ((k % 4) * 320, (k // 4) * 240))
    S.save(os.path.join(P, 'alpha_strip.jpg'), quality=88)


if __name__ == '__main__':
    os.makedirs(P, exist_ok=True)
    crop_strip(range(78, 114, 3), 'turn_away_strip.jpg')
    crop_strip(range(174, 222, 4), 'turn_back_strip.jpg')
    crop_strip(range(350, 570, 18), 'approach_strip.jpg')
    crop_strip(range(560, 620, 5), 'lie_down_strip.jpg')
    crop_strip(range(620, 716, 8), 'look_in_strip.jpg')
    alpha_strip()
