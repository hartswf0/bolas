"""SCION 23 · render the 768 scene frames: the painted set through the camera, the door on its swing and the light it
lets out, the person and the dog as the runtime posed them (draw.py), contact shadow, dusk and lamp light on the
actors, the spoken words. Writes cache/frames/####.jpg and, per frame, measurements of the dog taken from the
rendered pixels (cache/meas/####.json)."""
import json, math, os, pickle, sys
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import set as SET
from draw import Cam, draw_actor
from fonts import font

FR = None; PLATES = {}; DOOR = None
HEAD_SLOTS = {'head', 'earL', 'earR'}
LINES = [(0.88, 2.25, 'Come here.', 'call'), (3.30, 4.55, 'Come here! Come on.', 'call'),
         (7.30, 8.70, 'It’s all right.', 'soft'), (10.40, 11.55, 'It’s all right.', 'soft'),
         (26.25, 27.35, 'Come in.', 'soft')]


def init():
    global FR, DOOR
    FR = pickle.load(open(os.path.join(CACHE, 'perform.pkl'), 'rb'))
    DOOR = np.load(os.path.join(CACHE, 'door.npy'))


def plate_for(theta):
    key = round(theta, 2)
    if key in PLATES: return PLATES[key]
    if len(PLATES) > 2: PLATES.clear()
    base = np.asarray(Image.open(os.path.join(CACHE, 'plate.png')), np.float32) / 255
    SET.warp_quad(base, DOOR, SET.door_quad(theta), 0.82)
    sp = SET.spill_mask(theta)
    base = base + sp[..., None] * np.array([0.62, 0.42, 0.18], np.float32)
    PLATES[key] = np.clip(base, 0, 1)
    return PLATES[key]


def background(t, z, cx, cy):
    pl = plate_for(SET.door_angle(t))
    x0, x1 = (cx - W / 2 / z) * 2, (cx + W / 2 / z) * 2
    y0, y1 = (cy - H / 2 / z) * 2, (cy + H / 2 / z) * 2
    im = Image.fromarray((pl * 255).astype(np.uint8)).transform((W, H), Image.EXTENT, (x0, y0, x1, y1), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255


def actor_light(t, z, cx, cy):
    """per-pixel light on the actors: dusk outside (dimming over the scene), the lamp inside, the doorway's warm
    light on the porch once the door opens"""
    xs = (np.arange(W) + 0.5 - W / 2) / z + cx
    xm = (xs - X0) / K
    op = (SET.door_angle(t) - 24) / 72.0
    dusk = 1.0 - 0.12 * t / 32
    amb = np.array([0.80, 0.80, 0.96]) * dusk
    inside = 1 - np.clip((xm - (WALL_IN - 0.05)) / 0.12, 0, 1)
    warm = np.exp(-np.clip(xm - WALL_OUT, 0, None) / 1.3) * (0.25 + 0.75 * op)
    lamp = np.array([1.08, 0.94, 0.74])
    L = amb[None, :] * (1 - inside[:, None]) + lamp[None, :] * inside[:, None]
    L = L + (1 - inside[:, None]) * warm[:, None] * np.array([0.42, 0.26, 0.08])[None, :]
    return L[None, :, :].astype(np.float32)


def shadow(canvas, geo, cam, strength):
    pts = [g['pts'] for g in geo if g['type'] == 'mesh' and g['slot'] == 'torso']
    if not pts: return
    p = pts[0]
    xa, xb = p[:, 0].min(), p[:, 0].max()
    c = cam(np.array([[(xa + xb) / 2, 0.0]]))[0]
    rx = (xb - xa) / 2 * 1.15 * cam.A[0, 0]; ry = 9 * cam.A[0, 0]
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    x0, x1 = int(max(0, c[0] - rx * 1.6)), int(min(W, c[0] + rx * 1.6))
    y0, y1 = int(max(0, c[1] - ry * 3)), int(min(H, c[1] + ry * 3))
    if x0 >= x1 or y0 >= y1: return
    sub = ((xs[y0:y1, x0:x1] - c[0]) / rx) ** 2 + ((ys[y0:y1, x0:x1] - c[1]) / ry) ** 2
    a = np.clip(1.0 - sub, 0, 1) ** 1.5 * strength
    canvas[y0:y1, x0:x1] *= (1 - a[..., None] * np.array([0.75, 0.75, 0.6]))


def subtitle(img, t):
    for a, b, txt, kind in LINES:
        if a <= t <= b:
            al = min(1, (t - a) / 0.15, (b - t) / 0.2)
            f = font('literata_italic', 30 if kind == 'call' else 26)
            d = ImageDraw.Draw(img, 'RGBA')
            w = d.textlength(txt, font=f)
            col = (250, 238, 214) if kind == 'call' else (236, 222, 200)
            d.text(((W - w) / 2 + 2, 662 + 2), txt, font=f, fill=(0, 0, 0, int(140 * al)))
            d.text(((W - w) / 2, 662), txt, font=f, fill=col + (int(255 * al),))


def render(i):
    f = FR[i]; t = f['t']
    z, cx, cy = camera(t)
    cam = Cam(z, cx, cy)
    bg = background(t, z, cx, cy)
    lit = actor_light(t, z, cx, cy)
    # person
    pc = np.zeros((H, W, 4), np.float32)
    pmask = np.zeros((H, W), np.float32)
    draw_actor(pc, f['person'], cam, mask=pmask)
    pc[..., :3] *= lit
    bg = bg * (1 - pc[..., 3:4]) + pc[..., :3]
    # dog
    lying = 'lie' in str(f['alphas'].get(0, ('',))[0]) or 'settle' in str(f['alphas'].get(0, ('',))[0])
    shadow(bg, f['dog'], cam, 0.42 if lying else 0.32)
    dc = np.zeros((H, W, 4), np.float32)
    dmask = np.zeros((H, W), np.float32); hmask = np.zeros((H, W), np.float32)
    draw_actor(dc, f['dog'], cam, mask=dmask, mask_slots=HEAD_SLOTS, head_mask=hmask)
    dc[..., :3] *= lit
    out = bg * (1 - dc[..., 3:4]) + dc[..., :3]
    # vignette, grain
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.22 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.2
    out = out * v[..., None]
    rng = np.random.default_rng(i)
    out = out * (1 + 0.035 * (rng.random((H, W, 1)) - 0.5))
    img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    subtitle(img, t)
    img.save(os.path.join(CACHE, 'frames', '%04d.jpg' % (i + 1)), quality=92)
    # measurements from the rendered layers
    m = {'i': i, 't': round(t, 4), 'zoom': z, 'cx': cx, 'cy': cy}
    for name, mk in (('dog', dmask), ('head', hmask)):
        s = mk.sum()
        if s > 1:
            ys_, xs_ = np.nonzero(mk > 0.5)
            m[name] = dict(area=float(s), cx=float((mk * xx).sum() / s), cy=float((mk * yy).sum() / s),
                           x0=int(xs_.min()), x1=int(xs_.max()), y0=int(ys_.min()), y1=int(ys_.max()))
    m['overlap_person_px'] = int(((dmask > 0.5) & (pmask > 0.5)).sum())
    json.dump(m, open(os.path.join(CACHE, 'meas', '%04d.json' % (i + 1)), 'w'))
    return i


def main():
    os.makedirs(os.path.join(CACHE, 'frames'), exist_ok=True)
    os.makedirs(os.path.join(CACHE, 'meas'), exist_ok=True)
    idx = list(range(N))
    if len(sys.argv) > 1:
        idx = [int(round(float(s) * FPS)) for s in sys.argv[1].split(',')]
    workers = int(os.environ.get('WORKERS', '3'))
    if workers <= 1 or len(idx) < 4:
        init()
        for i in idx: render(i)
    else:
        with Pool(workers, initializer=init) as p:
            for k, _ in enumerate(p.imap_unordered(render, idx, chunksize=4)):
                if k % 96 == 0: print('frame', k, flush=True)
    print('rendered', len(idx))


if __name__ == '__main__':
    main()
