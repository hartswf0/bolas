"""Cutout surgeon: cut every card from the found frames, engrave it, record its pivots.
Writes build/cache/<card>.png (+ <card>_back.png for the dog) and build/cache/cards.json."""
import json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from common import *

cards = {}


def save(name, im, pivots, meta):
    im.save(os.path.join(CACHE, name + '.png'))
    cards[name] = {'size': im.size, 'pivots': pivots, **meta}


def mk_card(name, rgb, alpha, box, scale, pivots_src, meta, **kw):
    """crop to box, engrave, convert source-pixel pivots to card pixels."""
    e, pad = engrave(rgb.crop(box), alpha.crop(box), scale, **kw)
    piv = {k: [(v[0] - box[0]) * scale + pad, (v[1] - box[1]) * scale + pad] for k, v in pivots_src.items()}
    save(name, e, piv, meta)
    return e, piv


def fill_rows(m):
    """scissor cleanup: open away thin slivers, then fill each row between its outer edges"""
    im = Image.fromarray((m * 255).astype(np.uint8))
    im = im.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
    im = im.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    a = np.asarray(im) > 127
    out = np.zeros_like(a)
    for y in range(a.shape[0]):
        xs = np.nonzero(a[y])[0]
        if len(xs):
            out[y, xs[0]:xs[-1] + 1] = True
    return out


def A(mask_bool):
    return Image.fromarray((mask_bool * 255).astype(np.uint8))


# ------------------------------------------------------------------ the dog (Amateur Film New Jersey C, f008)
DOG_S = 1.45
DOGKW = dict(wash=(206, 170, 112), wash_mix=0.25, margin=1.5, gamma=0.55, spacing=4.8, cross=0.68)
dmeta = {'source': 'dog', 'frame': 8, 'op': 'SAM mask cut, split on pivot joints, engraved from luminance'}
im = load('dog', 8)
m = np.asarray(mask_of('dog', 8, polys_filter=lambda i, p: len(p) > 20), np.float32) / 255 > 0.5
H0, W0 = m.shape
head_poly = [(55, 50), (138, 50), (138, 102), (116, 150), (55, 150)]
hp = np.asarray(poly_mask((W0, H0), head_poly)) > 0
yy, xx = np.mgrid[0:H0, 0:W0]
head = m & hp
inner = np.asarray(poly_mask((W0, H0), [(55, 50), (126, 50), (126, 96), (106, 142), (55, 142)])) > 0
body = m & (yy < 166) & ~inner
fl = m & (xx >= 122) & (xx < 156) & (yy >= 146)
hn = m & (xx >= 176) & (xx < 204) & (yy >= 140)
hf = m & (xx >= 202) & (xx < 228) & (yy >= 140)
mk_card('dog_head', im, A(head), (55, 55, 145, 152), DOG_S, {'neck': (121, 124), 'nose': (82, 80), 'eye': (101, 92)}, dmeta, **DOGKW)
mk_card('dog_body', im, A(body), (95, 85, 232, 172), DOG_S, {'centre': (165, 135), 'neck': (121, 124), 'shoulder': (138, 152),
        'hip_n': (190, 148), 'hip_f': (213, 148), 'rump': (222, 116), 'belly': (165, 162)}, dmeta, **DOGKW)
mk_card('dog_fore', im, A(fl), (118, 140, 160, 208), DOG_S, {'top': (138, 152), 'paw': (140, 201)}, dmeta, **DOGKW)
mk_card('dog_hind_n', im, A(hn), (172, 136, 208, 208), DOG_S, {'top': (190, 148), 'paw': (187, 202)}, dmeta, **DOGKW)
mk_card('dog_hind_f', im, A(hf), (198, 136, 232, 208), DOG_S, {'top': (213, 148), 'paw': (214, 202)}, dmeta, **DOGKW)
# tail: no tail is visible in f008, so the surgeon cuts one from the dog's own back fur with a drawn scissor line
tail_poly = [(0, 6), (10, 1), (26, 3), (44, 9), (58, 18), (52, 22), (38, 17), (22, 13), (8, 14), (0, 12)]
fur = im.crop((150, 100, 214, 128))
tm = poly_mask(fur.size, tail_poly)
mk_card('dog_tail', fur, tm, (0, 0, 64, 28), DOG_S, {'base': (3, 9), 'tip': (56, 20)},
        {'source': 'dog', 'frame': 8, 'op': 'fur crop from the back (150,100)-(214,128) under a drawn tail-shaped scissor line, engraved'}, **DOGKW)

# neck: a strip of the dog's own chest fur, stretched when the head leans in to look
nk_im = im.crop((112, 104, 152, 136))
mk_card('dog_neck', nk_im, Image.new('L', nk_im.size, 255), (0, 0, 40, 32), DOG_S, {'c': (20, 16)},
        {'source': 'dog', 'frame': 8, 'op': 'chest-fur crop (112,104)-(152,136), engraved; stretched as an accordion neck'}, **DOGKW)

# eye: an engraver's highlight, drawn on the head card (the photo's head is a dark mass)
hc = Image.open(os.path.join(CACHE, 'dog_head.png'))
d = ImageDraw.Draw(hc)
ex, ey = cards['dog_head']['pivots']['eye']
d.ellipse([ex - 4.5, ey - 3.2, ex + 4.5, ey + 3.2], fill=(240, 232, 205, 255), outline=(20, 14, 16, 255))
d.ellipse([ex - 3.2, ey - 2.4, ex + 1.0, ey + 2.4], fill=(18, 12, 14, 255))
nx, ny = cards['dog_head']['pivots']['nose']
d.ellipse([nx - 4, ny - 3, nx + 4, ny + 4], fill=(18, 12, 14, 255))
hc.save(os.path.join(CACHE, 'dog_head.png'))

# the reverse of every dog card: bare white card; the body's back carries a rubber stamp
for n in ['dog_head', 'dog_body', 'dog_fore', 'dog_hind_n', 'dog_hind_f', 'dog_tail']:
    fr = Image.open(os.path.join(CACHE, n + '.png'))
    bk = card_back(fr, seed=hash(n) % 1000)
    if n == 'dog_body':
        st = Image.new('RGBA', bk.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        from PIL import ImageFont
        f = ImageFont.truetype(os.path.join(HERE, 'fonts', 'BigShoulders-900.ttf'), 44); f.set_variation_by_axes([900])
        cx, cy = bk.size[0] * 0.5, bk.size[1] * 0.46
        sd.rounded_rectangle([cx - 46, cy - 27, cx + 46, cy + 27], 6, outline=(176, 30, 34, 230), width=4)
        sd.text((cx, cy + 1), 'NO', font=f, fill=(176, 30, 34, 235), anchor='mm')
        st = st.rotate(-12, center=(cx, cy), resample=Image.BICUBIC)
        # stamp ink only where there is card, and a little patchy
        sa = np.asarray(st, np.float32)
        rng = np.random.default_rng(3)
        patch = np.clip(0.55 + rng.random(sa.shape[:2]) * 0.6, 0, 1)
        sa[..., 3] *= patch * (np.asarray(bk)[..., 3] / 255.0)
        # mirror the stamp so it reads correctly once the card is turned over (placed with sx < 0)
        st = ImageOps.mirror(Image.fromarray(sa.astype(np.uint8), 'RGBA'))
        bk.alpha_composite(st)
    bk.save(os.path.join(CACHE, n + '_back.png'))
    cards[n + '_back'] = {**cards[n], 'op': 'reverse of the card: blank card, ink ghost, stamp (body)'}

# the door-head substitution card (the door from Straight Talk f031, shrunk to a head)
dim = load('door', 31)
dmask = mask_of('door', 31)
mk_card('door_head', dim, dmask, (98, 0, 222, 280), 0.42, {'hinge': (100, 150), 'knob': (210, 150)},
        {'source': 'door', 'frame': 31, 'op': 'SAM mask cut, engraved, used as a substitution object for the dog head'},
        wash=(232, 226, 208), wash_mix=0.2, margin=1.2, gamma=0.8, spacing=3.4, cross=0.75, contrast=(0.02, 0.99))

# ------------------------------------------------------------------ the house door (Straight Talk f031)
door_w, door_h = 2 * 0.46 * K, 2.05 * K
sxs, sys_ = door_w / 124.0, door_h / 280.0
dc = dim.crop((98, 0, 222, 262)).resize((int(door_w), int(door_h)), Image.BICUBIC)
dm = dmask.crop((98, 0, 222, 262)).resize((int(door_w), int(door_h)), Image.BILINEAR)
dm = Image.new('L', dm.size, 255)  # the door is a full rectangle card
e, pad = engrave(dc, dm, 1.0, wash=(226, 218, 196), wash_mix=0.25, margin=0, gamma=0.75, spacing=4.4, cross=0.72,
                 contrast=(0.02, 0.99), outline=2.5, angle=80)
dd = ImageDraw.Draw(e)
kx, ky = pad + door_w - 22, pad + door_h * 0.53
dd.ellipse([kx - 7, ky - 7, kx + 7, ky + 7], fill=(196, 160, 70, 255), outline=(30, 20, 20, 255), width=2)
save('door', e, {'hinge_top': [pad, pad], 'hinge_bot': [pad, pad + door_h]},
     {'source': 'door', 'frame': 31, 'op': 'crop of the closed door, stretched to the opening, engraved; swings on its hinge as a card'})

# interior seen through the doorway (Straight Talk f000: the coat wall), unlit and lit
it = load('door', 0).crop((0, 0, 100, 288))
for nm, wash, lift, mix in [('interior_dark', (70, 78, 120), 0.0, 0.1), ('interior_lit', (255, 206, 120), 0.32, 0.25)]:
    ic = it.resize((int(door_w), int(door_h)), Image.BICUBIC)
    e, pad = engrave(ic, Image.new('L', ic.size, 255), 1.0, wash=wash, wash_mix=mix, outline=0, margin=0, gamma=0.8,
                     spacing=4.0, cross=0.6, lift=lift, angle=-30)
    save(nm, e, {'tl': [pad, pad]}, {'source': 'door', 'frame': 0, 'op': 'crop (0,0)-(100,288), engraved, tinted ' + nm})

# ------------------------------------------------------------------ the person (Straight Talk f000 + f012)
pim = load('door', 0)
a = np.asarray(pim, np.float32) / 255
dmk = np.asarray(mask_of('door', 0), np.float32) / 255
mx, mn = a.max(2), a.min(2)
sat = (mx - mn) / (mx + 1e-3)
wom = ((sat > 0.18) | (mx < 0.42)) & (dmk < 0.5)
wom[:, :185] = False; wom[:, 335:] = False; wom[272:, :] = False
wom = fill_rows(wom)
P_S = 0.74
pmeta = {'source': 'door', 'frame': 0, 'op': 'colour/darkness cut against the white wall and the SAM door mask, rows filled, engraved'}
PKW = dict(wash=(226, 150, 170), wash_mix=0.55, margin=1.5, gamma=0.7, spacing=3.6, cross=0.7, angle=20)
yy, xx = np.mgrid[0:wom.shape[0], 0:wom.shape[1]]
mk_card('p_head', pim, A(wom & (yy < 80)), (225, 8, 305, 82), P_S, {'neck': (262, 78), 'top': (262, 14)}, pmeta, **PKW)
mk_card('p_torso', pim, A(wom & (yy >= 72)), (190, 70, 332, 274), P_S,
        {'neck': (262, 78), 'hip': (262, 262), 'shoulder_r': (318, 100), 'shoulder_l': (205, 100)}, pmeta, **PKW)
# legs: two trouser shapes drawn by the scissors, filled with the jeans from f012
jeans = load('door', 12).crop((185, 200, 235, 288)).resize((40, 150), Image.BICUBIC)
leg_poly = [(4, 0), (36, 0), (35, 140), (40, 150), (6, 150), (8, 140)]
lm = poly_mask(jeans.size, leg_poly)
mk_card('p_leg', jeans, lm, (0, 0, 40, 150), 0.92, {'hip': (20, 4), 'foot': (22, 146)},
        {'source': 'door', 'frame': 12, 'op': 'jeans crop (185,200)-(235,288) under a drawn trouser scissor line, engraved'},
        wash=(90, 104, 160), wash_mix=0.3, margin=1.2, gamma=0.45, spacing=3.4, cross=0.7, angle=75)
# a sleeve segment for the telescoping arm (her right sleeve, f000)
sl = pim.crop((298, 100, 326, 170)).rotate(90, expand=True)  # now horizontal, 70x28
mk_card('p_sleeve', sl, Image.new('L', sl.size, 255), (0, 0, sl.size[0], sl.size[1]), 0.8, {'l': (0, 14), 'r': (70, 14)},
        {'source': 'door', 'frame': 0, 'op': 'sleeve crop (298,100)-(326,170), rotated, engraved; repeated as telescoping arm'},
        wash=(150, 40, 60), wash_mix=0.5, margin=1.0, gamma=0.8, spacing=3.4, cross=0.7, angle=10)

# ------------------------------------------------------------------ faces (We Learn About the Telephone I)
for f, nm in [(6, 'face_loud'), (18, 'face_soft'), (12, 'face_half')]:
    fim = load('face', f)
    mk_ = mask_of('face', f, polys_filter=lambda i, p: len(p) > 20)
    ma = np.asarray(mk_) > 127
    ys, xs = np.nonzero(ma)
    box = (0, 0, int(min(200, xs.max() + 4)), 288)
    em = Image.new('L', fim.size, 0); ImageDraw.Draw(em).ellipse([-70, 10, 150, 275], fill=255)
    ma = fill_rows(ma) & (np.asarray(em) > 127)
    mk_card(nm, fim, A(ma), box, 0.42, {'neck': (40, 280), 'mouth': (100, 150)},
            {'source': 'face', 'frame': f, 'op': 'SAM mask cut of the cartoon profile, engraved; substitution head'},
            wash=(244, 196, 180), wash_mix=0.35, margin=1.5, gamma=0.55, spacing=3.6, cross=0.7, contrast=(0.01, 0.99))

fc = Image.open(os.path.join(CACHE, 'face_loud.png')); d = ImageDraw.Draw(fc)
ex, ey = 58, 26   # the eye sits forward, by the nose, and looks out to the right: at the dog
d.ellipse([ex - 9, ey - 6, ex + 9, ey + 6], fill=(244, 238, 220, 255), outline=(20, 14, 16, 255), width=2)
d.ellipse([ex + 1, ey - 5, ex + 8, ey + 4], fill=(18, 12, 14, 255))
d.line([(ex - 10, ey - 11), (ex + 9, ey - 8)], fill=(20, 14, 16, 255), width=3)   # a frown: the command
fc.save(os.path.join(CACHE, 'face_loud.png'))

# ------------------------------------------------------------------ the reaching hand (The Door to Heaven f010)
him = load('hand', 10)
ha = np.asarray(him, np.float32) / 255
hl = ha @ np.array([0.299, 0.587, 0.114])
hm = np.asarray(mask_of('hand', 10), np.float32) / 255 > 0.5
yy, xx = np.mgrid[0:hl.shape[0], 0:hl.shape[1]]
arm = (hl > 0.58) & (yy < 118) & (yy > 30) & (xx > 225)
hand = fill_rows(hm | arm)
hand[:, :180] = False
hbox = (180, 30, 384, 120)
hcard_im = ImageOps.mirror(him.crop(hbox)); hcard_m = ImageOps.mirror(A(hand).crop(hbox))
mk_card('hand_reach', hcard_im, hcard_m, (0, 0, 204, 90), 0.95, {'wrist': (204 - 190, 52), 'tip': (204 - 12, 40)},
        {'source': 'hand', 'frame': 10, 'op': 'SAM hand mask + forearm by luminance, mirrored, engraved'},
        wash=(240, 206, 178), wash_mix=0.2, margin=1.8, gamma=0.45, spacing=3.6, cross=0.8, contrast=(0.02, 0.995))

# ------------------------------------------------------------------ the low hand and the butterfly (Insect Zoo f000)
bim = load('butterfly', 60)
ba = np.asarray(bim, np.float32) / 255
bl = ba @ np.array([0.299, 0.587, 0.114])
bm = np.asarray(mask_of('butterfly', 60), np.float32) / 255 > 0.5
yy, xx = np.mgrid[0:bl.shape[0], 0:bl.shape[1]]
hm_ = A((bl > 0.16) & (xx > 70) & (yy > 95) & ~bm).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
handm = np.asarray(hm_.filter(ImageFilter.GaussianBlur(1.5))) > 127
handm &= ~bm
bbox = (70, 100, 384, 288)
mk_card('hand_low', bim, A(handm), bbox, 0.40, {'wrist': (330, 280), 'tip': (110, 128)},
        {'source': 'butterfly', 'frame': 60, 'op': 'luminance cut of the hand on black, minus the butterfly mask, engraved'},
        wash=(244, 210, 182), wash_mix=0.2, margin=1.8, gamma=0.5, spacing=3.6, cross=0.8, contrast=(0.02, 0.995))
ys, xs = np.nonzero(bm)
bb = (int(xs.min()) - 2, int(ys.min()) - 2, int(xs.max()) + 3, int(ys.max()) + 3)
mk_card('butterfly', bim, A(bm), bb, 0.85, {'body': (bb[0] + 8, bb[3] - 4)},
        {'source': 'butterfly', 'frame': 60, 'op': 'SAM mask cut, engraved and hand-coloured, flaps by card scaling; the soft voice'},
        wash=(250, 150, 40), wash_mix=0.35, margin=1.5, gamma=0.5, spacing=2.8, cross=0.85, contrast=(0.0, 1.0), lift=0.15)

# ------------------------------------------------------------------ the lantern (Anthracite ... f030)
lim = load('lantern', 30)
lm = mask_of('lantern', 30, polys_filter=lambda i, p: len(p) > 30)
la = np.asarray(lm) > 127
ys, xs = np.nonzero(la[:200])
lb = (int(xs.min()) - 2, int(ys.min()) - 2, int(xs.max()) + 3, 160)
mk_card('lantern', lim, lm, lb, 0.5, {'hook': ((lb[0] + lb[2]) / 2, lb[1] + 2)},
        {'source': 'lantern', 'frame': 30, 'op': 'SAM mask cut (cage only), engraved'},
        wash=(150, 150, 160), wash_mix=0.3, margin=1.5, gamma=0.8, spacing=3.0, cross=0.7)

# ------------------------------------------------------------------ the stone wall (dog film f000, the pillar)
st = load('dog', 0).crop((325, 45, 382, 195)).resize((114, 300), Image.BICUBIC)
tile = Image.new('RGB', (int(1.25 * K + 330), FLOOR + 10))
tw, th = st.size
rng = np.random.default_rng(7)
for ty in range(0, tile.size[1], th - 10):
    for tx in range(-int(rng.integers(0, tw)), tile.size[0], tw - 6):
        t = st if rng.random() < 0.5 else ImageOps.mirror(st)
        tile.paste(t, (tx, ty))
tile = tile.resize((tile.size[0] // 2 * 2, tile.size[1]), Image.BICUBIC)
e, pad = engrave(tile, Image.new('L', tile.size, 255), 1.0, wash=(150, 140, 172), wash_mix=0.1, outline=0, margin=0,
                 gamma=0.6, spacing=5.0, cross=0.78, angle=-12, lift=0.12)
save('wall', e, {'tl': [pad, pad]}, {'source': 'dog', 'frame': 0, 'op': 'stone pillar crop (306,60)-(380,200) tiled and mirrored into a wall, engraved'})

# ------------------------------------------------------------------ hedge: the cloud's outline, brought down to earth
cm = np.asarray(mask_of('cloud', 0), np.float32) / 255 > 0.5
cim = load('cloud', 0)
hb = (0, 60, 384, 170)
hedge_rgb = Image.fromarray((255 - np.asarray(cim)).astype(np.uint8))
mk_card('hedge', hedge_rgb, A(cm), hb, 2.2, {'tl': (0, 60)},
        {'source': 'cloud', 'frame': 0, 'op': 'the SAM cloud outline reused as a hedge silhouette, tones inverted, engraved dark'},
        wash=(54, 46, 72), wash_mix=0.0, margin=0, gamma=1.0, spacing=3.2, cross=0.4, outline=1.5)

# ------------------------------------------------------------------ clouds (Top Of The Cloud, time lapse), engraved as dusk
for f in range(0, 62, 6):
    cim = load('cloud', f)
    big = cim.resize((1280 - 0, int(216 * 1280 / 384)), Image.BICUBIC).crop((0, 60, 1280, 470))
    e, pad = engrave(big, Image.new('L', big.size, 255), 0.5, wash=(240, 170, 150), wash_mix=0.0, outline=0, margin=0,
                     gamma=1.4, spacing=4.8, cross=0.75, angle=-8, warp=2.5)
    e = e.resize((1280, 410), Image.BICUBIC)
    save('cloud_%02d' % f, e, {}, {'source': 'cloud', 'frame': f, 'op': 'time-lapse frame, engraved as dusk sky'})

json.dump(cards, open(os.path.join(CACHE, 'cards.json'), 'w'), indent=1)
print('cards:', len(cards))
