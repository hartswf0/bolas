"""The set: painted and airbrushed card, cut prints, and the lamps over the table.
Space: screen x = X_D + K * x_metres (x along the porch, threshold at 0). The facade faces the camera; the porch runs
along it; the doorway is a hole cut in the wall card."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from table import place, pin, T, R, PIECES, img, FOLDER, HERE

W, H = 1280, 720
X_D, K = 290, 210.0            # door centre, px per metre
OPEN_L, OPEN_R = int(X_D - .46 * K), int(X_D + .46 * K)   # 193 .. 387, the score's door opening
TOP = 176                      # lintel underside: 2.0 m above the sill
FLOOR = 596                    # where the wall meets the porch boards
WALL_END = 960
CACHE = os.path.join(HERE, 'cache')
rng = np.random.default_rng(7)


def place_at(canvas, name, left, bottom, **kw):
    p = PIECES[name]; im = img(name)
    place(canvas, name, T(left - p['origin'][0], bottom - (p['origin'][1] + im.height)), **kw)


def xs(x):
    return X_D + K * x


def airbrush(w, h, top, bottom, seed=0, speck=.025, curve=1.0):
    """an airbrushed gradient: smooth ramp plus the spatter of a spray gun"""
    r = np.random.default_rng(seed)
    t = (np.linspace(0, 1, h)[:, None] ** curve) * np.ones((1, w))
    top = np.array(top, np.float32) / 255; bottom = np.array(bottom, np.float32) / 255
    rgb = top * (1 - t[..., None]) + bottom * t[..., None]
    sp = r.random((h, w)).astype(np.float32)
    rgb *= 1 + (sp[..., None] - .5) * speck
    low = np.asarray(Image.fromarray((r.random((h // 40 + 2, w // 40 + 2)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    rgb *= 1 + (low[..., None] - .5) * .05
    return np.clip(rgb, 0, 1)


def to_img(a, alpha=None):
    a8 = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    if alpha is None:
        return Image.fromarray(a8, 'RGB').convert('RGBA')
    return Image.fromarray(np.dstack([a8, (np.clip(alpha, 0, 1) * 255).astype(np.uint8)]), 'RGBA')


def card_rect(w, h, color, seed=0, grain=.06):
    r = np.random.default_rng(seed)
    low = np.asarray(Image.fromarray((r.random((h // 8 + 2, w // 8 + 2)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    rgb = np.array(color, np.float32)[None, None] / 255 * (1 + (low[..., None] - .5) * grain + r.normal(0, .012, (h, w, 1)))
    return rgb


def sky_layer():
    """painted dusk, airbrushed, with the moon card and the tree prints on the horizon"""
    sky = airbrush(W, H, (26, 30, 70), (226, 128, 92), seed=1, curve=1.6)
    S = to_img(sky)
    m = pin  # noqa
    # trees: two prints, darkened to silhouette by the dusk
    place_at(S, 'trees2', 940, 476, tint=(.2, .18, .28), shadow=None)
    place_at(S, 'trees', 1010, 478, tint=(.22, .2, .3), shadow=None)
    d = ImageDraw.Draw(S)
    lawn = airbrush(W - WALL_END, 130, (58, 50, 62), (22, 24, 30), seed=3, curve=.7)
    S.alpha_composite(to_img(lawn), (WALL_END, 470))
    return S


def house_layers():
    """interior (behind the wall), wall card with the doorway cut out, trim, sill, pillar, porch boards."""
    # interior: a warm room, painted card; the lamp print hangs in it
    inner = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    room = airbrush(OPEN_R - OPEN_L + 40, FLOOR - TOP + 30, (150, 96, 52), (220, 160, 92), seed=4, curve=.8)
    inner.alpha_composite(to_img(room), (OPEN_L - 20, TOP - 20))
    d = ImageDraw.Draw(inner)
    d.rectangle((OPEN_L - 20, FLOOR - 48, OPEN_R + 20, FLOOR + 6), fill=(112, 70, 40, 255))     # room floor
    d.line((X_D + 20, TOP - 20, X_D + 20, TOP + 40), fill=(40, 26, 18, 255), width=2)          # the lamp cord
    b = PIECES['bulb']
    bi = img('bulb')
    place(inner, 'bulb', T(X_D + 20 - bi.width / 2 - b['origin'][0], TOP + 40 - b['origin'][1]) @ R(180, (b['origin'][0] + bi.width / 2, b['origin'][1] + bi.height / 2)), shadow=None)
    # wall: painted clapboard card
    wall = card_rect(WALL_END, FLOOR - 120, (78, 92, 96), seed=5, grain=.08)
    for y in range(0, FLOOR - 120, 26):          # clapboard shadow lines, drawn
        wall[y:y + 3] *= .72
        wall[y + 3:y + 5] *= 1.08
    a = np.ones(wall.shape[:2], np.float32)
    a[TOP - 120:FLOOR - 120, OPEN_L:OPEN_R] = 0   # the doorway: a hole cut in the card
    wallI = to_img(wall, a)
    house = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # shadow the wall card casts into the doorway (paper thickness, lamp from upper left)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.alpha_composite(wallI, (0, 120))
    sa = sh.getchannel('A').filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * .45))
    shadow = Image.new('RGBA', (W, H), (8, 6, 10, 0)); shadow.putalpha(sa)
    house.alpha_composite(shadow, (3, 4))
    house.alpha_composite(wallI, (0, 120))
    hd = ImageDraw.Draw(house)
    # roof: slate card above the eave
    roof = card_rect(WALL_END + 40, 92, (40, 40, 52), seed=6)
    for x in range(0, WALL_END + 40, 22):
        roof[:, x:x + 2] *= .7
    roof[44:47] *= .6
    house.alpha_composite(to_img(roof), (0, 30))
    fascia = card_rect(WALL_END + 50, 12, (205, 196, 172), seed=7)
    house.alpha_composite(to_img(fascia), (0, 118))
    # door trim: cream card strips; the sill: a plank
    trim = (214, 204, 178)
    for box in [(OPEN_L - 16, TOP - 22, OPEN_L, FLOOR), (OPEN_R, TOP - 22, OPEN_R + 16, FLOOR), (OPEN_L - 22, TOP - 24, OPEN_R + 22, TOP)]:
        w_, h_ = box[2] - box[0], box[3] - box[1]
        house.alpha_composite(to_img(card_rect(w_, h_, trim, seed=box[0])), (box[0], box[1]))
    sill = card_rect(OPEN_R - OPEN_L + 52, 10, (150, 112, 74), seed=8)
    sill[:2] *= 1.25
    house.alpha_composite(to_img(sill), (OPEN_L - 26, FLOOR - 4))
    # porch boards: brown card strips, wider toward the camera
    porch = np.zeros((H - FLOOR, W, 3), np.float32)
    ys = [0, 9, 20, 33, 49, 68, 91, 124]
    for i in range(len(ys) - 1):
        hh = ys[i + 1] - ys[i]
        porch[ys[i]:ys[i + 1]] = card_rect(W, hh, (104 - 4 * i, 74 - 3 * i, 52 - 2 * i), seed=20 + i, grain=.1)
        porch[ys[i]:ys[i] + 1] *= .45
        r = np.random.default_rng(i)
        for jx in r.integers(0, W, 3):    # board ends
            porch[ys[i]:ys[i + 1], jx:jx + 2] *= .55
    house.alpha_composite(to_img(porch), (0, FLOOR + 6))
    # the stone pier at the corner of the house: a print of the dog's own house
    p = PIECES['pillar']
    place_at(house, 'pillar', WALL_END - 30, FLOOR + 8, shadow=(4, 3, .4), tint=(.62, .6, .62))
    # the window: trim of cream card round the curtained glass print
    wx, wy = 590, 250
    wi = img('window')
    house.alpha_composite(to_img(card_rect(wi.width + 28, wi.height + 30, (214, 204, 178), seed=77)), (wx - 14, wy - 14))
    place_at(house, 'window', wx, wy + wi.height, shadow=(2, 2, .4), tint=(.9, .8, .62))
    house.alpha_composite(to_img(card_rect(wi.width + 44, 12, (190, 180, 156), seed=78)), (wx - 22, wy + wi.height + 12))
    return inner, house


def door_layer(name):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    p = PIECES[name]; im = img(name)
    if name == 'door_edge':
        x = OPEN_L + 2
    else:
        x = OPEN_L - 4
    place_at(L, name, x, FLOOR + 2, shadow=(4, 2, .5))
    return L


def blurred_poly(pts, blur):
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255


AMBIENT = np.array([.70, .74, .94], np.float32)
WARM = np.array([1.30, 1.02, .66], np.float32)
BEAM = blurred_poly([(OPEN_L + 6, FLOOR - 160), (OPEN_R - 6, FLOOR - 160), (OPEN_R + 90, H), (OPEN_L - 70, H)], 22)
BEAM_FLOOR = blurred_poly([(OPEN_L - 10, FLOOR + 2), (OPEN_R + 10, FLOOR + 2), (OPEN_R + 110, H), (OPEN_L - 90, H)], 18)
GLOW = np.asarray(Image.fromarray((blurred_poly([(OPEN_L - 60, TOP - 50), (OPEN_R + 60, TOP - 50), (OPEN_R + 60, FLOOR + 40), (OPEN_L - 60, FLOOR + 40)], 60) * 255).astype(np.uint8))).astype(np.float32) / 255
ROOM = blurred_poly([(OPEN_L, TOP), (OPEN_R, TOP), (OPEN_R, FLOOR), (OPEN_L, FLOOR)], 2)
WINDOW = blurred_poly([(590, 250), (692, 250), (692, 400), (590, 400)], 6)
SLIT = blurred_poly([(OPEN_R - 22, TOP), (OPEN_R, TOP), (OPEN_R + 30, H), (OPEN_R - 30, H)], 10)


def lightmap(open_frac, t):
    """the lamps over the table: a blue dusk flood, dimming a little over the scene; a warm lamp in the room whose
    light falls out through as much of the doorway as the door uncovers."""
    amb = AMBIENT * (1 - .07 * t / 32)
    L = np.ones((H, W, 3), np.float32) * amb
    room = ROOM[..., None]
    L = L * (1 - room) + room * np.array([1.12, 1.0, .86], np.float32)
    beam = (np.maximum(BEAM, BEAM_FLOOR) * open_frac + SLIT * .35 * (1 - open_frac))[..., None]
    L = L + beam * (WARM - amb) * .9 * (1 - room)
    L = L + (GLOW * .18 * open_frac)[..., None] * (WARM - amb) * (1 - room)
    L = L + WINDOW[..., None] * (np.array([1.05, .86, .6], np.float32) - amb) * .8
    return L
