"""Plate supervisor: builds clean plates from the archive sources with motion tracks, median stacking and keys.
Writes build/cache/plates/*.jpg (RGB) and *_a.jpg (matte), and plates.json (provenance + measured stats)."""
import json, os
import numpy as np
from PIL import Image
from comp import load, poly_matte, noise_level, BezierMask

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'sources'); OUT = os.path.join(HERE, 'cache', 'plates')
os.makedirs(OUT, exist_ok=True)
info = {}


def save(name, rgb, a=None, **meta):
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, name + '.jpg'), quality=95)
    if a is not None:
        Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, name + '_a.jpg'), quality=95)
    meta['noise'] = round(noise_level(rgb), 5)
    info[name] = meta


def shift(img, dx, dy):
    """Stabilise by the camera motion track: integer roll + edge clamp (sub-pixel ignored, 384x288 source)."""
    return np.roll(np.roll(img, -int(round(dy)), 0), -int(round(dx)), 1)


# --- 1. stone plate: tracked median of the home-movie yard, dog held out by its SAM masks -------------------
cam = json.load(open(os.path.join(SRC, 'dog', 'camera.json')))
masks = json.load(open(os.path.join(SRC, 'dog', 'masks.json')))
stack, wts = [], []
for i in range(0, 22):
    f = load(os.path.join(SRC, 'dog', 'f%03d.jpg' % i))
    m = poly_matte(masks[str(i)], (384, 288)) if masks.get(str(i)) else np.zeros((288, 384), np.float32)
    stack.append(shift(f, *cam[i])); wts.append(shift(1 - np.clip(m * 2, 0, 1), *cam[i]))
stack = np.array(stack); wts = np.array(wts)
stack[wts < .5] = np.nan
med = np.nanmedian(stack, axis=0)
med = np.where(np.isnan(med), np.array(stack[0]), med)
med = np.nan_to_num(med, nan=0.4)
save('yard_clean', med, op='tracked median of dog f000-f021 (camera.json track inverted), dog held out by SAM masks',
     source='dog f000-f021')
# the stone pillar (right of the path) and the sunlit path, cut from the clean plate
save('stone', med[40:250, 322:380], op='crop of yard_clean: the stone pillar', source='dog f000-f021')
save('path', med[160:288, 20:230], op='crop of yard_clean: the sunlit path (porch floor texture)', source='dog f000-f021')

# --- 2. door plates: the leaf (SAM mask), the wall, and the person by difference key ------------------------
dcam = json.load(open(os.path.join(SRC, 'door', 'camera.json')))
dmask = json.load(open(os.path.join(SRC, 'door', 'masks.json')))
f31 = load(os.path.join(SRC, 'door', 'f031.jpg'))
leaf = np.array(dmask['31'][0], float)
s = leaf.sum(1); d = leaf[:, 0] - leaf[:, 1]
quad = [leaf[s.argmin()], leaf[d.argmax()], leaf[s.argmax()], leaf[d.argmin()]]  # tl, tr, br, bl
save('door_leaf', f31, poly_matte([dmask['31'][0]], (384, 288), feather=.7), quad=[list(map(float, q)) for q in quad],
     op='SAM mask of door f031, corner quad from the mask extremes', source='door f031')
save('wall', f31[20:230, 300:376], op='crop of door f031 right wall (switch masked by grade)', source='door f031')
save('room', f31, op='door f031 whole frame as the far wall of the lit room (coats on hooks, closed inner door)', source='door f031')
save('floorwood', f31[272:288, 60:380], op='crop: wooden floor strip under the door', source='door f031')

# the person: hand roto (bezier) on f000, back view; she will be graded to a backlit silhouette
WOMAN = [(262,17),(283,22),(290,40),(288,70),(296,86),(318,96),(325,120),(325,185),(318,192),(312,240),(305,262),(282,268),
         (272,288),(215,288),(212,265),(212,215),(205,190),(197,175),(196,125),(205,100),(226,90),(240,78),(236,55),(240,30)]
f0 = load(os.path.join(SRC, 'door', 'f000.jpg'))
save('woman0', f0, BezierMask(WOMAN, feather=1.0).raster((384, 288)), roto=WOMAN,
     op='hand-drawn bezier roto (24 vertices, feather 1 px) of the woman in door f000', source='door f000')

# stone facade texture: random running-bond blocks resampled from the stone pillar (no mirrored tiling)
rng = np.random.default_rng(28)
st = load(os.path.join(OUT, 'stone.jpg'))
BW, BH = 26, 18
tex = np.zeros((BH * 20, BW * 44, 3), np.float32)
for r in range(20):
    off = (BW // 2) * (r % 2)
    for c in range(-1, 45):
        y = rng.integers(0, st.shape[0] - BH); x = rng.integers(0, st.shape[1] - BW)
        blk = st[y:y + BH, x:x + BW] * rng.uniform(.9, 1.06)
        x0 = c * BW + off
        a, b = max(0, x0), min(tex.shape[1], x0 + BW)
        if b > a: tex[r * BH:(r + 1) * BH, a:b] = blk[:, a - x0:b - x0]
# mortar lines
tex[::BH] *= .7
for r in range(20):
    off = (BW // 2) * (r % 2)
    tex[r * BH:(r + 1) * BH, off::BW] *= .72
save('stonewall', tex, op='running-bond stone wall: 26x20 blocks resampled at random from the stone plate, darkened mortar',
     source='dog f000-f021 (via stone)')

# porch flagstones: 40x40 blocks resampled from the sunlit path, random rotation by 90 deg steps
pt = load(os.path.join(OUT, 'path.jpg'))
FB = 40
flo = np.zeros((FB * 8, FB * 24, 3), np.float32)
for r in range(8):
    for c in range(24):
        y = rng.integers(0, pt.shape[0] - FB); x = rng.integers(0, pt.shape[1] - FB)
        blk = np.rot90(pt[y:y + FB, x:x + FB], rng.integers(0, 4)) * rng.uniform(.88, 1.05)
        flo[r * FB:(r + 1) * FB, c * FB:(c + 1) * FB] = blk
flo[::FB] *= .6; flo[:, ::FB] *= .6
save('flags', flo, op='porch flagstones: 40x40 blocks resampled from the path plate, rotated, joints darkened', source='dog f000-f021 (via path)')

# the hand: luma key inside a bezier garbage matte that leaves the card out (Door to Heaven f010)
fh = load(os.path.join(SRC, 'hand', 'f010.jpg'))
ARM = [(186,96),(192,78),(212,66),(240,62),(282,60),(330,56),(384,40),(384,96),(340,98),(296,100),(262,102),(232,104),(206,110),(192,108)]
y = fh @ np.array([.299, .587, .114], np.float32)
key = np.clip((y - .22) / .12, 0, 1) * BezierMask(ARM, feather=1.2).raster((384, 288))
save('arm', fh, key, roto=ARM, op='luma key (0.22..0.34) x bezier garbage matte excluding the card', source='hand f010')

# the seated person: SAM mask refined by a luma key against the snow (Survival Stresses f020)
fs = load(os.path.join(SRC, 'sleeping-bag', 'f020.jpg'))
sm = json.load(open(os.path.join(SRC, 'sleeping-bag', 'masks.json')))['20']
ys = fs @ np.array([.299, .587, .114], np.float32)
a = poly_matte(sm, (fs.shape[1], fs.shape[0]), feather=1.0) * np.clip((.93 - ys) / .1, 0, 1)
save('seated', fs, a, op='SAM mask x inverse luma key (snow > 0.93 removed)', source='sleeping-bag f020')

json.dump(info, open(os.path.join(OUT, 'plates.json'), 'w'), indent=1)
print(json.dumps({k: v.get('noise') for k, v in info.items()}))
