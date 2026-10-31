"""SCION 40 · the replay compositor: puts the finished (skin) paper pieces on the finished set at given poses.
Called by render.py with RECOVERED poses (tracked.json). Returns the picture and the dog's own layers (alpha of body
and head, rendered alone) so the trace can be measured from what was drawn."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

CARDS = json.load(open(os.path.join(DATA, 'cards.json')))
_cache = {}


def card(name, style='skin'):
    k = (style, name)
    if k not in _cache:
        _cache[k] = Image.open(os.path.join(CACHE, 'cards', style, name + '.png')).convert('RGBA')
    return _cache[k]


def setimg(name):
    if name not in _cache:
        _cache[name] = Image.open(os.path.join(CACHE, name)).convert('RGBA')
    return _cache[name]


def layer(p, style='skin'):
    m = CARDS[p['card']]
    return place(card(p['card'], style), m['anchor'], p['X'], p['Y'], p['th'])


def drop_shadow(img, lay, dx=3, dy=4, blur=3, op=0.38):
    a = lay.getchannel('A').filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * op))
    sh = Image.new('RGBA', img.size, (14, 10, 8, 255))
    sh.putalpha(a)
    img.alpha_composite(sh, (0, 0)) if (dx, dy) == (0, 0) else img.alpha_composite(sh.transform(img.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy)))


def light_u(pieces):
    return float(np.clip((pieces['light']['X'] - 8) / (WALL[0] - 8), 0, 1))


def compose(pieces):
    u = light_u(pieces)
    img = Image.blend(setimg('set_dark.png'), setimg('set_lit.png'), u) if 0 < u < 1 else setimg('set_lit.png' if u >= 1 else 'set_dark.png').copy()
    # the door leaf swings into the room
    dl = layer(pieces['door'])
    drop_shadow(img, dl, 2, 3, 2, .3)
    img.alpha_composite(dl)
    # the person
    pl = layer(pieces['person'])
    drop_shadow(img, pl, 3, 3, 3, .35)
    img.alpha_composite(pl)
    # light spill onto the porch: the tissue, only where it lies outside the wall
    if u > 0:
        ll = layer(pieces['light'])
        a = np.asarray(ll.getchannel('A'), np.float32)
        a[:, :WALL[1]] = 0
        a[:GROUND - 260] = 0
        a *= 0.55 * u
        base = np.asarray(img, np.float32)
        col = np.array([255, 206, 120], np.float32)
        scr = 255 - (255 - base[..., :3]) * (255 - col) / 255
        k = (a / 255)[..., None]
        base[..., :3] = base[..., :3] * (1 - k) + scr * k
        img = Image.fromarray(base.astype(np.uint8), 'RGBA')
        # the beam in the air through the door: a soft wedge
        beam = Image.new('L', (W, H), 0)
        ex = WALL[1] + (pieces['light']['X'] - 8) / (WALL[0] - 8) * 260
        ImageDraw.Draw(beam).polygon([(WALL[1], LINTEL + 10), (WALL[1], GROUND), (ex + 60, GROUND + 6), (ex - 40, GROUND - 40)], fill=int(70 * u))
        beam = beam.filter(ImageFilter.GaussianBlur(18))
        bl = Image.new('RGBA', (W, H), (255, 214, 140, 255)); bl.putalpha(beam)
        img.alpha_composite(bl)
    # the dog: body and head cards, its shadow on the floor
    bl_ = layer(pieces['dog.body'])
    hl_ = layer(pieces['dog.head'])
    dog_a = ImageChops.lighter(bl_.getchannel('A'), hl_.getchannel('A'))
    A = np.asarray(dog_a)
    cols = np.where(A.max(0) > 128)[0]
    if len(cols):
        x0, x1 = cols.min(), cols.max()
        sh = Image.new('L', (W, H), 0)
        rows = np.where(A.max(1) > 128)[0]
        ybot = min(rows.max(), GROUND + 6)
        ImageDraw.Draw(sh).ellipse([x0 + 6, ybot - 7, x1 - 6, ybot + 7], fill=150)
        sh = sh.filter(ImageFilter.GaussianBlur(5))
        s = Image.new('RGBA', (W, H), (16, 10, 8, 255)); s.putalpha(sh)
        img.alpha_composite(s)
    drop_shadow(img, Image.merge('RGBA', (dog_a, dog_a, dog_a, dog_a)), 3, 3, 3, .3)
    behind = CARDS[pieces['dog.body']['card']]['head_behind']
    order = [hl_, bl_] if behind else [bl_, hl_]
    dog = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for L in order:
        dog.alpha_composite(L)
    # warm light on the dog where the spill reaches it
    if u > 0:
        d = np.asarray(dog, np.float32)
        xx = np.arange(W)[None, :]
        warm = np.clip(1 - (xx - WALL[1]) / 320.0, 0, 1) * u * 0.35
        warm = np.broadcast_to(warm, (H, W))
        d[..., 0] *= 1 + warm * 0.25; d[..., 1] *= 1 + warm * 0.12
        dog = Image.fromarray(np.clip(d, 0, 255).astype(np.uint8), 'RGBA')
    img.alpha_composite(dog)
    return img.convert('RGB'), bl_.getchannel('A'), hl_.getchannel('A')
