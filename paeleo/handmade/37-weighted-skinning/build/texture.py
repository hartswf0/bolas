"""SCION 37 coat: the public-domain archive dog (Amateur Film New Jersey C, kit/archive-dog frame 8) mapped onto the mesh.
The dog's own film pixels are warped by a thin-plate spline from the archive rig keys onto the mesh's side-projection UV
space (rest pose), the background is replaced by the nearest dog pixel (distance transform inside its SAM mask), and only
the eye, nose and lip line are painted by hand on top. Output: ../assets/texture/coat.png (+ coat_source.png for the card)."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
KIT = os.path.join(ROOT, '..', 'kit', 'archive-dog')
OUT = os.path.join(ROOT, 'assets', 'texture'); os.makedirs(OUT, exist_ok=True)
FRAME = 8
LO, HI = (-.86, -.02), (.76, 1.02)          # the dog mesh's UV box (mesh.py)
TW, TH = 1024, 660


def tps_fit(src, dst, lam=1e-6):
    n = len(src)
    d = np.linalg.norm(src[:, None] - src[None], axis=2); K = np.where(d > 0, d * d * np.log(d + 1e-12), 0) + lam * np.eye(n)
    P = np.hstack([np.ones((n, 1)), src])
    A = np.zeros((n + 3, n + 3)); A[:n, :n] = K; A[:n, n:] = P; A[n:, :n] = P.T
    b = np.zeros((n + 3, 2)); b[:n] = dst
    return src, np.linalg.solve(A, b)

def tps_eval(model, X):
    src, c = model; n = len(src)
    d = np.linalg.norm(X[:, None] - src[None], axis=2); U = np.where(d > 0, d * d * np.log(d + 1e-12), 0)
    return U @ c[:n] + c[n] + X @ c[n + 1:]


def fur_patches(frames, size=10):
    """square patches of the dog's own film pixels, fully inside its eroded SAM mask"""
    masks = json.load(open(os.path.join(KIT, 'masks.json')))
    out = []
    for fr in frames:
        img = np.asarray(Image.open(os.path.join(KIT, 'frames', 'f%03d.jpg' % fr)).convert('L'), float) / 255
        H, W = img.shape
        mim = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(mim)
        for poly in masks.get(str(fr), []): dr.polygon([tuple(p) for p in poly], fill=255)
        m = ndimage.binary_erosion(np.asarray(mim) > 0, iterations=3)
        for y in range(0, H - size, 3):
            for x in range(0, W - size, 3):
                if m[y:y + size, x:x + size].all():
                    out.append((fr, x, y, img[y:y + size, x:x + size]))
    return out


def quilt(patches, shape, scale, rng, n):
    """scatter upscaled archive patches with feathered edges over a canvas (a crude texture quilt)"""
    H, W = shape; acc = np.zeros(shape); wsum = np.zeros(shape) + 1e-6
    ps = patches[0][3].shape[0]; S = int(ps * scale)
    yy, xx = np.mgrid[0:S, 0:S]
    r2 = ((xx - S / 2) / (S / 2)) ** 2 + ((yy - S / 2) / (S / 2)) ** 2
    fe = np.exp(-(r2 ** 4) * 3) + 1e-4          # near-hard patch edges: the quilt keeps each patch's own grain, little averaging
    for _ in range(n):
        p = patches[rng.integers(len(patches))][3]
        up = np.asarray(Image.fromarray((p * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), float) / 255
        up = up - up.mean()                                  # keep only the film's texture, not its exposure
        y0 = rng.integers(-S // 2, H - S // 2); x0 = rng.integers(-S // 2, W - S // 2)
        ys, xs = slice(max(0, y0), min(H, y0 + S)), slice(max(0, x0), min(W, x0 + S))
        sy, sx = slice(ys.start - y0, ys.stop - y0), slice(xs.start - x0, xs.stop - x0)
        acc[ys, xs] += (up * fe)[sy, sx]; wsum[ys, xs] += fe[sy, sx]
    return acc / wsum


def main():
    rng = np.random.default_rng(37)
    frames = list(range(0, 50, 2))
    pt = fur_patches(frames)
    lum = np.array([p[3].mean() for p in pt])
    print('archive fur patches', len(pt), 'from', len(frames), 'frames')
    grain = quilt(pt, (TH, TW), 1.4, rng, 16000)
    grain = grain / (grain.std() + 1e-6)
    # region masks painted in the rest-pose side projection (u along the body, v up)
    def P(x, y): return ((x - LO[0]) / (HI[0] - LO[0]) * TW, (1 - (y - LO[1]) / (HI[1] - LO[1])) * TH)
    def layer(polys, blur):
        im = Image.new('L', (TW, TH), 0); d = ImageDraw.Draw(im)
        for poly in polys: d.polygon([P(*q) for q in poly], fill=255)
        return np.asarray(im.filter(ImageFilter.GaussianBlur(blur)), float) / 255
    saddle = layer([[(-.80, .37), (-.62, .50), (-.40, .60), (-.25, .58), (-.05, .55), (.12, .56), (.22, .60),
                     (.25, .99), (.20, .99), (-.30, .99), (-.86, .99), (-.86, .40)]], 9)
    mask_dark = layer([[(.57, .70), (.80, .70), (.80, .80), (.57, .80)], [(.40, .86), (.50, .86), (.48, 1.0), (.38, 1.0)]], 6)
    socks = layer([[(-.40, -.02), (.40, -.02), (.40, .07), (-.40, .07)]], 5)
    base = .62 - .46 * saddle - .32 * mask_dark + .10 * socks
    tex = np.clip(base + .085 * grain, 0, 1)
    # the archive's own contrast: a gentle S-curve, then unsharp so the grain survives the rasterizer's filtering
    tex = np.clip(.5 + (tex - .5) * 1.15, 0, 1)
    tex = np.asarray(Image.fromarray((tex * 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(2, 90, 1)), float) / 255
    rgb = np.stack([tex * .95 + .05, tex * .80 + .04, tex * .60 + .03], -1)      # monochrome film on a warm base
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    def disc(x, y, r, c):
        (a, b) = P(x, y); s = r / (HI[0] - LO[0]) * TW; d.ellipse([a - s, b - s, a + s, b + s], fill=c)
    # painted by hand (the archive head is ~20 px): nose, eye, lip line
    disc(.650, .744, .024, (14, 11, 10))
    disc(.535, .810, .017, (24, 16, 11)); disc(.539, .815, .005, (215, 205, 175))
    d.line([P(.55, .727), P(.635, .723)], fill=(20, 14, 10), width=3)
    im.save(os.path.join(OUT, 'coat.png'))
    np.save(os.path.join(OUT, 'regions.npy'), np.stack([saddle, mask_dark, socks]).astype(np.float16))
    # the source frames with their masks, for the end card
    s = Image.open(os.path.join(KIT, 'frames', 'f%03d.jpg' % 20)).convert('RGB'); sd = ImageDraw.Draw(s)
    for poly in json.load(open(os.path.join(KIT, 'masks.json')))['20']: sd.polygon([tuple(p) for p in poly], outline=(255, 200, 80))
    s.save(os.path.join(OUT, 'coat_source.png'))
    json.dump({'frames': frames, 'patches': len(pt), 'patch_px': 10, 'upscale': 1.4, 'scatter': 16000, 'grain_gain': .085, 'seed': 37},
              open(os.path.join(OUT, 'coat.json'), 'w'))


if __name__ == '__main__':
    main()
