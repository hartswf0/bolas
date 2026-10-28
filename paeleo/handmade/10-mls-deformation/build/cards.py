"""SCION-10 · the title card (3 s: the flat hide lifting into the standing dog, handle by handle, under MLS) and the end card
(3 s: what it is made of; the hide with its handle set; the same handles under affine, similarity and rigid MLS).
Writes cache/frames/t_%04d.jpg (72) and cache/frames/e_%04d.jpg (72); also ../proof/handles_on_hide.jpg, ../proof/variants_strip.jpg."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import cam, dog

R = os.path.normpath(os.path.join(H, '..', '..', '..', '..'))
FR = os.path.join(H, 'cache', 'frames'); PROOF = os.path.join(H, '..', 'proof')
os.makedirs(FR, exist_ok=True); os.makedirs(PROOF, exist_ok=True)
F_DISP = os.path.join(R, 'tools/paeleo/fonts/f8.woff2'); F_MONO = os.path.join(R, 'tools/paeleo/fonts/f14.woff2')
F_SER = os.path.join(R, 'tools/paeleo/fonts/f34.woff2'); F_IT = os.path.join(R, 'tools/paeleo/fonts/f27.woff2')
BG = (14, 16, 24); INK = (232, 224, 210); DIM = (150, 150, 160); RED = (226, 92, 70); AMBER = (240, 180, 90)


def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight is not None:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f


def render_dog(Q, scale, center, size, family='affine', light=(-0.3, -0.5, 0.8), hide=None):
    hide = hide or dog.Hide(sample=1.0)
    pts, N, _ = hide.warp(Q, family)
    flip = (N @ cam.F) > 0; N = np.where(flip[:, None], -N, N)
    l = np.array(light, float); l /= np.linalg.norm(l)
    lam = np.clip(N @ l, 0, 1) * 0.65 + 0.42
    rgba = np.c_[hide.rgb * lam[:, None], hide.a]
    keep = (cam.SCALE, cam.ORIGIN.copy())
    cam.SCALE = scale; cam.ORIGIN = np.array([0.0, 0.0])
    c, _ = cam.project(np.array([center]))
    cam.ORIGIN = np.array([size[0] / 2, size[1] / 2]) - c[0]
    xy, d = cam.project(pts)
    qxy, _ = cam.project(Q)
    W0, H0 = cam.W, cam.H
    cam.W, cam.H = size
    lay = cam.splat(xy, d, rgba)
    cam.W, cam.H = W0, H0
    cam.SCALE, cam.ORIGIN = keep
    return lay, qxy


def standing_pose():
    P = json.load(open(os.path.join(H, 'cache', 'poses.json')))['frames']
    return np.array(P[300]['Q']), P[300]['pose']


def flat_targets():
    """the handles where they sit on the flat hide (z = 0), placed in the same world frame as the standing pose."""
    Q, p = standing_pose()
    th = p['th']; f = np.array([np.cos(th), np.sin(th)]); l = np.array([-f[1], f[0]])
    C = np.array([p['cx'], p['cy']])
    S = dog.P_SRC
    return np.c_[C + S[:, :1] * f + S[:, 1:2] * l, np.zeros(len(S))]


def title():
    Qs, p = standing_pose(); Qf = flat_targets()
    hide = dog.Hide(sample=1.0)
    ft = font(F_DISP, 46, 800); fs = font(F_SER, 26); fm = font(F_MONO, 17)
    center = np.r_[p['cx'], p['cy'], 0.25]
    for k in range(72):
        t = k / 71
        e = np.clip((t - 0.2) / 0.6, 0, 1); e = e * e * (3 - 2 * e)
        Q = Qf + (Qs - Qf) * e
        img = Image.new('RGB', (1280, 720), BG)
        lay, qxy = render_dog(Q, 330, center, (1280, 470), hide=hide)
        if lay is not None:
            (x0, y0, x1, y1), c = lay
            a = np.asarray(img, float) / 255
            sub = a[250 + y0:250 + y1, x0:x1]
            sub[:] = sub * (1 - c[..., 3:4]) + np.clip(c[..., :3], 0, 1)
            img = Image.fromarray((a * 255).astype(np.uint8))
        dr = ImageDraw.Draw(img)
        for (x, y) in qxy[:len(dog.POINT_NAMES)]:
            r = 2.5
            dr.ellipse([x - r, 250 + y - r, x + r, 250 + y + r], fill=RED)
        fade = min(1, k / 10)
        col = tuple(int(c * fade) for c in INK)
        dr.text((70, 60), 'PAE-02 · SCION 10 · Schaefer, McPhail & Warren — MLS Deformation', font=ft, fill=col)
        dr.text((72, 130), 'The threshold. One painted hide, lifted into a dog by Moving Least Squares from its handles.', font=fs, fill=tuple(int(c * fade) for c in DIM))
        dr.text((72, 680), 'handles (red) move; the image between them is the MLS solution', font=fm, fill=tuple(int(c * fade * 0.8) for c in DIM))
        img.save(os.path.join(FR, f't_{k:04d}.jpg'), quality=92)


def hide_with_handles(width):
    im = Image.open(os.path.join(H, '..', 'assets', 'dog_hide.png')).convert('RGBA')
    bg = Image.new('RGBA', im.size, (40, 44, 56, 255)); bg.alpha_composite(im)
    dr = ImageDraw.Draw(bg)
    px = dog.source_points_px()
    idx = {n: i for i, n in enumerate(dog.POINT_NAMES)}
    for a, b in dog.SEGMENTS:
        dr.line([tuple(px[idx[a]]), tuple(px[idx[b]])], fill=AMBER, width=3)
    for n, (x, y) in zip(dog.POINT_NAMES, px[:len(dog.POINT_NAMES)]):
        g = dog.HANDLES[n]['group']
        col = (120, 200, 255) if g in ('head', 'ear') else RED
        dr.ellipse([x - 6, y - 6, x + 6, y + 6], fill=col, outline=(255, 255, 255))
    s = width / bg.width
    return bg.convert('RGB').resize((width, int(bg.height * s)), Image.LANCZOS)


def variants(width=380, height=300):
    """same handles, the walking pose of frame 300, in the film's camera: affine / similarity / rigid (x, y by the family; height z by affine)."""
    P = json.load(open(os.path.join(H, 'cache', 'poses.json')))['frames']
    hide = dog.Hide(sample=1.0)
    out = []
    keep = (cam.F.copy(), cam.R.copy(), cam.UP.copy())
    # a plan camera: look straight down
    for fam in ('affine', 'similarity', 'rigid'):
        Q = np.array(P[300]['Q'])
        lay, qxy = render_dog(Q, width / 1.7, np.r_[P[300]['pose']['cx'] - 0.05, P[300]['pose']['cy'], 0.3], (width, height), family=fam, hide=hide)
        img = Image.new('RGB', (width, height), (40, 44, 56))
        if lay is not None:
            (x0, y0, x1, y1), c = lay
            a = np.asarray(img, float) / 255
            sub = a[y0:y1, x0:x1]; sub[:] = sub * (1 - c[..., 3:4]) + np.clip(c[..., :3], 0, 1)
            img = Image.fromarray((a * 255).astype(np.uint8))
        dr = ImageDraw.Draw(img)
        for (x, y) in qxy[:len(dog.POINT_NAMES)]:
            dr.ellipse([x - 2, y - 2, x + 2, y + 2], fill=RED)
        dr.text((8, 6), fam, font=font(F_MONO, 16), fill=INK)
        out.append(img)
    cam.F[:], cam.R[:], cam.UP[:] = keep
    return out


def endcard():
    img = Image.new('RGB', (1280, 720), BG); dr = ImageDraw.Draw(img)
    ft = font(F_DISP, 40, 800); fs = font(F_SER, 19); fm = font(F_MONO, 14)
    dr.text((60, 34), 'What the dog is made of', font=ft, fill=INK)
    lines = ['One image: a dog\'s coat painted flat in numpy (back, both flanks, legs, head, tail).',
             'Every frame it is warped by Moving Least Squares (Schaefer, McPhail & Warren 2006) from',
             f'{len(dog.POINT_NAMES)} point handles and {len(dog.SEGMENTS)} line-segment handles. Affine MLS lifts the sheet into a',
             'body (flanks down, legs to the boards); the head is a rigid cluster of handles. No skeleton,',
             'no cut pieces, no frame swaps. Set, light and person: ray-cast and drawn in code. Sound synthesized.']
    for k, s in enumerate(lines):
        dr.text((62, 92 + k * 27), s, font=fs, fill=DIM if k else INK)
    hw = hide_with_handles(560)
    img.paste(hw, (60, 250))
    dr.text((62, 250 + hw.height + 8), 'the hide and its handle set: red points, amber segments, blue = protected head', font=fm, fill=DIM)
    vs = variants(200, 170)
    for k, v in enumerate(vs):
        img.paste(v.resize((200, 170)), (660 + k * 205, 260))
    dr.text((660, 440), 'one pose, the same handles, three MLS families (height by affine)', font=fm, fill=DIM)
    dr.text((660, 462), 'similarity thins the legs to threads; rigid swells and wrinkles them;', font=fm, fill=DIM)
    dr.text((660, 480), 'the film uses affine (2D -> 3D), with the head held rigid by its handles', font=fm, fill=DIM)
    dr.text((62, 680), 'PAE-02 · SCION 10 · MLS Deformation · trace, invariants and method in the folder', font=fm, fill=(110, 110, 120))
    for k in range(72):
        f = min(1, k / 8, (71 - k) / 10 + 0.3)
        a = (np.asarray(img, float) * f + np.array(BG) * (1 - f)).astype(np.uint8)
        Image.fromarray(a).save(os.path.join(FR, f'e_{k:04d}.jpg'), quality=92)
    img.save(os.path.join(PROOF, 'endcard.jpg'), quality=90)
    hide_with_handles(1100).save(os.path.join(PROOF, 'handles_on_hide.jpg'), quality=90)
    vs = variants(420, 340)
    S = Image.new('RGB', (420 * 3, 340)); [S.paste(v, (k * 420, 0)) for k, v in enumerate(vs)]
    S.save(os.path.join(PROOF, 'variants_strip.jpg'), quality=90)


if __name__ == '__main__':
    title(); endcard()
