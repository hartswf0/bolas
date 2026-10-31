"""SCION 40 · synthesizes the CAPTURE PLATE: what an overhead camera above the table would have recorded.
There was no camera, table or performer here, so this plate is made, not shot: the layout sheet lies on a wooden
table, slightly rotated and in mild perspective; the working (white card, fiducial-tabbed) puppets lie on it at the
performers' sheet poses (perform.json); archive hands (hands.py) reach in from the table edges and hold the tabs;
everything casts shadows from an overhead lamp; then the camera: warm grade, vignette, blur, sensor noise, JPEG.
Writes cache/plate/%04d.jpg (768), cache/plate_clean.jpg (the empty sheet, recorded before the take),
cache/gt_hand/%04d.png (the true hand matte, half resolution, used ONLY for evaluating the tracker) and data/camera_truth.json."""
import json, math, os, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

CARDS = json.load(open(os.path.join(DATA, 'cards.json')))
HANDS = json.load(open(os.path.join(DATA, 'hands.json')))['frames']
# where the sheet's corners land in the camera image (a slightly rotated, slightly keystoned view)
SHEET_IN_PLATE = [(96, 58), (1196, 40), (1222, 672), (70, 688)]
H_S2P = homography([(0, 0), (W, 0), (W, H), (0, H)], SHEET_IN_PLATE)
H_P2S = np.linalg.inv(H_S2P)
HAND_SCALE = 1.5
_cache = {}


def card(name):
    if name not in _cache:
        _cache[name] = Image.open(os.path.join(CACHE, 'cards', 'plate', name + '.png')).convert('RGBA')
    return _cache[name]


def hand_sprite(f, mirror):
    k = ('h', f, mirror)
    if k not in _cache:
        im = Image.open(os.path.join(CACHE, 'hands', 'f%03d.png' % f)).convert('RGBA')
        m = HANDS[f]
        g, a = list(m['grip']), m['arm_angle']
        if mirror:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            g = [im.size[0] - 1 - g[0], g[1]]
            a = math.pi - a
        _cache[k] = (im, g, a)
    return _cache[k]


def table():
    if 'table' not in _cache:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        n = value_noise(H, W, 40, 3)
        rings = np.sin((yy * 0.9 + xx * 0.08 + n * 40) / 5.0) * .5 + .5
        fine = value_noise(H, W, 3, 4)
        v = 0.75 + 0.12 * rings + 0.1 * fine
        a = np.stack([150 * v, 100 * v, 62 * v], -1)
        _cache['table'] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')
    return _cache['table']


def persp_coeffs(Hm):
    """PIL PERSPECTIVE wants the map output->input: here plate->stage = inverse of Hm (stage->plate)"""
    Hi = np.linalg.inv(Hm)
    Hi = Hi / Hi[2, 2]
    return tuple(Hi.reshape(-1)[:8])


def stage_layer(pieces):
    sheet = Image.open(os.path.join(CACHE, 'set_sheet.png')).convert('RGBA') if 'sheet' not in _cache else _cache['sheet'].copy()
    if 'sheet' not in _cache:
        _cache['sheet'] = sheet.copy()
    img = sheet
    order = ['door', 'person', 'light']
    behind = CARDS[pieces['dog.body']['card']]['head_behind']
    order += ['dog.head', 'dog.body'] if behind else ['dog.body', 'dog.head']
    for pn in order:
        p = pieces[pn]
        m = CARDS[p['card']]
        lay = place(card(p['card']), m['anchor'], p['X'], p['Y'], p['th'])
        a = lay.getchannel('A').filter(ImageFilter.GaussianBlur(2.5)).point(lambda v: int(v * .4))
        sh = Image.new('RGBA', (W, H), (30, 20, 10, 255)); sh.putalpha(a)
        img.alpha_composite(sh.transform((W, H), Image.AFFINE, (1, 0, -2, 0, 1, -3)))
        img.alpha_composite(lay)
    return img


def render(fr, clean=False):
    i = fr['i']
    img = table().copy()
    st = _cache['sheet'].copy() if (clean and 'sheet' in _cache) else (Image.open(os.path.join(CACHE, 'set_sheet.png')).convert('RGBA') if clean else stage_layer(fr['pieces']))
    warped = st.transform((W, H), Image.PERSPECTIVE, persp_coeffs(H_S2P), resample=Image.BICUBIC)
    msk = Image.new('L', (W, H), 0)
    ImageDraw.Draw(msk).polygon(SHEET_IN_PLATE, fill=255)
    # the sheet's own shadow on the table
    sh = Image.new('RGBA', (W, H), (20, 12, 6, 255)); sh.putalpha(msk.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * .5)))
    img.alpha_composite(sh.transform((W, H), Image.AFFINE, (1, 0, -4, 0, 1, -6)))
    warped.putalpha(msk)
    img.alpha_composite(warped)
    hand_m = Image.new('L', (W, H), 0)
    if not clean:
        for h in fr['hands']:
            spr, g, a = hand_sprite((i // 2 + ord(h['hand']) * 7) % 62, h['mirror'])
            gx, gy = apply_h(H_S2P, [h['grip']])[0]
            phi = h['ang']
            # presence: the hand slides in along its own arm
            off = (1 - h['presence']) * 720
            tx, ty = gx + math.cos(phi) * off, gy + math.sin(phi) * off
            d = phi - a
            c, s = math.cos(d), math.sin(d)
            k = 1 / HAND_SCALE
            co = (c * k, s * k, g[0] - k * (c * tx + s * ty), -s * k, c * k, g[1] - k * (-s * tx + c * ty))
            lay = spr.transform((W, H), Image.AFFINE, co, resample=Image.BICUBIC)
            A = lay.getchannel('A')
            hs = Image.new('RGBA', (W, H), (16, 10, 6, 255)); hs.putalpha(A.filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * .42)))
            img.alpha_composite(hs.transform((W, H), Image.AFFINE, (1, 0, -16, 0, 1, -20)))
            img.alpha_composite(lay)
            hand_m = Image.fromarray(np.maximum(np.asarray(hand_m), np.asarray(A)))
    # the camera
    a = np.asarray(img.convert('RGB'), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    lamp = 1.08 - 0.32 * (((xx - 560) / 900.) ** 2 + ((yy - 300) / 600.) ** 2)
    a = a * lamp[..., None] * np.array([1.04, 0.98, 0.88])
    rng = np.random.default_rng(1000 + i)
    a += rng.normal(0, 3.0, a.shape)
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    return out, hand_m


def work(fr):
    out, hm = render(fr)
    out.save(os.path.join(CACHE, 'plate', '%04d.jpg' % fr['i']), quality=88)
    hm.resize((W // 2, H // 2)).point(lambda v: 255 if v > 127 else 0).convert('1').save(os.path.join(CACHE, 'gt_hand', '%04d.png' % fr['i']))
    return fr['i']


def main():
    os_makedirs(os.path.join(CACHE, 'plate'), os.path.join(CACHE, 'gt_hand'))
    P = json.load(open(os.path.join(CACHE, 'perform.json')))['frames']
    clean, _ = render(dict(i=9999, pieces={}, hands=[]), clean=True)
    clean.save(os.path.join(CACHE, 'plate_clean.jpg'), quality=92)
    only = [int(a) for a in sys.argv[1:]]
    todo = [P[i] for i in only] if only else P
    with Pool(3) as pool:
        for k, _ in enumerate(pool.imap_unordered(work, todo, chunksize=8)):
            if k % 100 == 0:
                print('plate', k, flush=True)
    json.dump(dict(about='TRUTH of the synthesized camera, for evaluation only; the tracker calibrates from the corner fiducials',
                   sheet_in_plate=SHEET_IN_PLATE, H_stage_to_plate=H_S2P.tolist()), open(os.path.join(DATA, 'camera_truth.json'), 'w'), indent=1)
    print('plate done', len(todo))


if __name__ == '__main__':
    main()
