"""SCION 35 · the person: two view prints (standing, sitting), profile facing the porch, printed like the dog
(blue clothes plate, orange skin plate, solid key line), no face drawn (no identifiable person)."""
import numpy as np, json, os
from PIL import Image
from common import screen, CACHE, K_SRC
from dogprint import Canvas, stamp_capsule, to_arr, shade, blur

STAND = dict(head=(0.03, 1.57), head_f=(0.13, 1.56), head_t=(0.0, 1.69), neck=(0.0, 1.44), sh=(0.0, 1.38),
             chest=(0.12, 1.25), back=(-0.12, 1.27), belly=(0.12, 0.98), seat=(-0.12, 0.98), pelvis=(0.0, 0.95), hip=(0.0, 0.92),
             kn_n=(0.03, 0.50), an_n=(0.0, 0.08), ft_n=(0.17, 0.02), kn_f=(0.0, 0.50), an_f=(-0.03, 0.08), ft_f=(0.13, 0.02),
             el_n=(0.03, 1.12), ha_n=(0.05, 0.86), el_f=(-0.02, 1.12), ha_f=(0.0, 0.86))
SIT = dict(head=(0.10, 1.11), head_f=(0.20, 1.09), head_t=(0.07, 1.23), neck=(0.07, 0.98), sh=(0.05, 0.93),
           chest=(0.17, 0.80), back=(-0.09, 0.82), belly=(0.15, 0.55), seat=(-0.10, 0.52), pelvis=(0.0, 0.50), hip=(0.02, 0.47),
           kn_n=(0.40, 0.53), an_n=(0.36, 0.08), ft_n=(0.50, 0.02), kn_f=(0.37, 0.51), an_f=(0.31, 0.08), ft_f=(0.45, 0.02),
           el_n=(0.22, 0.70), ha_n=(0.38, 0.60), el_f=(0.19, 0.70), ha_f=(0.35, 0.59))
FAMILY = {'arm_f': 'similarity', 'leg_f': 'similarity', 'torso': 'affine', 'head': 'rigid', 'leg_n': 'similarity', 'arm_n': 'similarity'}
ANCH = {'arm_f': ['sh', 'el_f', 'ha_f'], 'arm_n': ['sh', 'el_n', 'ha_n'],
        'leg_f': ['hip', 'kn_f', 'an_f', 'ft_f'], 'leg_n': ['hip', 'kn_n', 'an_n', 'ft_n'],
        'torso': ['neck', 'sh', 'chest', 'back', 'belly', 'seat', 'pelvis'], 'head': ['head', 'head_f', 'head_t', 'neck']}
ORDER = ['arm_f', 'leg_f', 'torso', 'head', 'leg_n', 'arm_n']


def make(name, G):
    pts = {k: np.array([v[0] * K_SRC, -v[1] * K_SRC]) for k, v in G.items()}
    xs = [p[0] for p in pts.values()]; ys = [p[1] for p in pts.values()]
    m = 0.22 * K_SRC
    x0, x1, y0, y1 = min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m
    cv = Canvas(int(x1 - x0), int(y1 - y0), -x0, -y0)
    L = {}
    r = lambda v: v * K_SRC
    im, dr = cv.new(); stamp_capsule(dr, cv, [pts['ha_f'], pts['el_f'], pts['sh']], [r(.045), r(.045), r(.055)]); L['arm_f'] = to_arr(im)
    im, dr = cv.new(); stamp_capsule(dr, cv, [pts['ft_f'], pts['an_f'], pts['kn_f'], pts['hip']], [r(.04), r(.05), r(.065), r(.085)]); L['leg_f'] = to_arr(im)
    im, dr = cv.new()
    stamp_capsule(dr, cv, [pts['sh'], (pts['chest'] + pts['back']) / 2, pts['pelvis']], [r(.15), r(.16), r(.17)])
    stamp_capsule(dr, cv, [pts['neck'], pts['sh']], [r(.06), r(.07)])
    L['torso'] = to_arr(im)
    im, dr = cv.new()
    hc = pts['head']
    stamp_capsule(dr, cv, [hc, hc], [r(.108)] * 2)
    stamp_capsule(dr, cv, [hc, pts['head_f'] * 0.5 + hc * 0.5], [r(.1), r(.085)])
    L['head'] = to_arr(im)
    im, dr = cv.new(); stamp_capsule(dr, cv, [pts['ft_n'], pts['an_n'], pts['kn_n'], pts['hip']], [r(.042), r(.052), r(.068), r(.09)]); L['leg_n'] = to_arr(im)
    im, dr = cv.new(); stamp_capsule(dr, cv, [pts['ha_n'], pts['el_n'], pts['sh']], [r(.047), r(.047), r(.058)]); L['arm_n'] = to_arr(im)
    h, w = cv.h, cv.w
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    res = {}
    for k in ORDER:
        a = L[k]
        far = 0.2 if k.endswith('_f') else 0.0
        bl, og = shade(a, far, 0.1)
        bl = np.clip(bl + 0.66, 0, 1)                # dark clothes
        if k == 'head':
            # hair cap over the back and top of the head, skin plate on the face side; no features
            c = pts['head'] + (cv.ox, cv.oy); f = pts['head_f'] + (cv.ox, cv.oy)
            dirv = (f - c) / np.linalg.norm(f - c)
            proj = (xx - c[0]) * dirv[0] + (yy - c[1]) * dirv[1]
            face = np.clip(proj / (0.03 * K_SRC) + 0.3, 0, 1) * np.clip((yy - (c[1] - 0.03 * K_SRC)) / 8, 0, 1)
            bl = bl * (1 - 0.7 * face); og = np.maximum(og, 0.4 * face)
        if k.startswith('arm'):
            hpt = pts['ha_' + k[-1]] + (cv.ox, cv.oy)
            dh = np.sqrt((xx - hpt[0]) ** 2 + (yy - hpt[1]) ** 2)
            hand = np.clip(1 - dh / (0.06 * K_SRC), 0, 1) ** 0.5
            bl = bl * (1 - 0.75 * hand); og = np.maximum(og, 0.6 * hand)
        key = np.clip((a - np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(__import__('PIL.ImageFilter').ImageFilter.MinFilter(5)), np.float32) / 255) * 1.6, 0, 1)
        bl = np.maximum(bl, key)
        ib = screen(bl * (a > 0.01), 14.0, 15.0); io = screen(og * (a > 0.01), 14.0, 75.0, ox=3, oy=-2)
        res[k] = (a, ib, io)
    root = np.array([0.0, 0.0])
    meta = dict(name=name, size=[w, h], root=[float(root[0] + cv.ox), float(root[1] + cv.oy)],
                anchors={k: [float(p[0] + cv.ox), float(p[1] + cv.oy)] for k, p in pts.items()},
                order=ORDER, family=FAMILY, falloff={k: 1.4 for k in ORDER}, layer_anchors=ANCH)
    return meta, res


if __name__ == '__main__':
    os.makedirs(os.path.join(CACHE, 'prints'), exist_ok=True)
    for nm, G in (('PERSON_stand', STAND), ('PERSON_sit', SIT)):
        meta, res = make(nm, G)
        np.savez_compressed(os.path.join(CACHE, 'prints', nm + '.npz'),
                            **{k + '__' + n: v.astype(np.float16) for k, vals in res.items() for n, v in zip(('a', 'ib', 'io'), vals)})
        json.dump(meta, open(os.path.join(CACHE, 'prints', nm + '.json'), 'w'), indent=0)
        print(nm, meta['size'])
