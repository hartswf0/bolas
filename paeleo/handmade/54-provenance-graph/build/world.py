"""The set: a section through a thick stone wall at dusk. Inside: a room cut from nothing but recorded sources and drawn
coordinates; outside: a porch, a dusk sky of found cloud and strangers' doodles. Units: metres (x along the porch as in
the score, y up from the porch floor). The plate is drawn at PPM px per metre."""
import json, os
import numpy as np
from lineage import FOLDER, REPO

PPM = 320
XMIN, XMAX, YMIN, YMAX = -3.6, 5.9, -1.1, 3.5
PW, PH = int((XMAX - XMIN) * PPM), int((YMAX - YMIN) * PPM)
WALL_IN, WALL_OUT = -0.46, 0.46        # the doorway is the thickness of the wall: the score's door_opening
LINTEL = 2.08
LAMP = (-1.80, 1.72)
BOWL_X = -2.05
BENCH = (-1.58, -0.96, 0.42)


def P(x, y):
    return [round((x - XMIN) * PPM, 2), round((YMAX - y) * PPM, 2)]


def poly(pts, fill, outline=None, w=1):
    return {'t': 'poly', 'pts': [P(*p) for p in pts], 'fill': fill, 'outline': outline, 'w': w}


def rect(x0, y0, x1, y1, fill, outline=None, w=1):
    a, b = P(x0, y1), P(x1, y0)
    return {'t': 'rect', 'pts': [a, b], 'fill': fill, 'outline': outline, 'w': w}


def line(pts, col, w):
    return {'t': 'line', 'pts': [P(*p) for p in pts], 'outline': col, 'w': w}


def Mplace(src_size, x0, y0, x1, y1, flip=False):
    """matrix placing a whole source image into the world box (x0,y0)-(x1,y1) metres."""
    a, b = P(x0, y1), P(x1, y0)
    sx = (b[0] - a[0]) / src_size[0]; sy = (b[1] - a[1]) / src_size[1]
    if flip:
        return [[-sx, 0, b[0]], [0, sy, a[1]], [0, 0, 1]]
    return [[sx, 0, a[0]], [0, sy, a[1]], [0, 0, 1]]


QD_USED = {'moon': ['5431885159202816'], 'tree': None, 'fence': None}


def quickdraw_pick():
    """copy only the Quick, Draw! drawings this film uses into sources/, with their key_id (CC BY 4.0)."""
    src = '/home/user/hartswf0/quickdraw/'
    want = {'moon': ['02816'], 'tree': ['81152', '83200', '00384', '90816', '47072'], 'fence': ['78272']}
    out = []
    p = os.path.join(FOLDER, 'sources', 'quickdraw-used.ndjson')
    if not os.path.isdir(src) and os.path.exists(p):
        return p                      # rebuild from the copy kept in this folder
    for cat, tails in want.items():
        lines = open(src + cat + '.part').read().splitlines()[:-1]   # last line may be partial
        for l in lines[:400]:
            d = json.loads(l)
            if d.get('recognized') and any(d['key_id'].endswith(t) for t in tails) and not any(o['key_id'] == d['key_id'] for o in out):
                out.append(d)
    with open(p, 'w') as f:
        for d in out:
            f.write(json.dumps(d) + '\n')
    return p


def copy_found(rel_shot, frames):
    import shutil
    base = '/home/user/hartswf0/secondhand-motion/shots/' + rel_shot + '/'
    dst = os.path.join(FOLDER, 'sources', rel_shot); os.makedirs(dst, exist_ok=True)
    out = {}
    have = os.path.isdir(base)          # rebuilds without the found-frames library use the copies kept here
    for f in frames:
        if have:
            shutil.copyfile(base + 'frames/f%03d.jpg' % f, os.path.join(dst, 'f%03d.jpg' % f))
        out[f] = os.path.join(dst, 'f%03d.jpg' % f)
    if have:
        shutil.copyfile(base + 'masks.json', os.path.join(dst, 'masks.json'))
        shutil.copyfile(base + 'clip.json', os.path.join(dst, 'clip.json'))
    return out, os.path.join(dst, 'masks.json')


SKY = {'stops': [[0.0, [14, 14, 36]], [0.42, [40, 36, 80]], [0.63, [110, 78, 112]], [0.70, [178, 118, 104]], [0.72, [72, 52, 78]], [1.0, [12, 11, 22]]]}
STONE_DUSK = {'stops': [[0.0, [16, 15, 26]], [0.5, [50, 46, 62]], [1.0, [104, 98, 112]]]}
STONE_LIT = {'stops': [[0.0, [30, 20, 18]], [0.5, [92, 66, 50]], [1.0, [170, 128, 92]]]}
CLOUD_RAMP = {'stops': [[0.0, [30, 28, 60]], [0.6, [92, 74, 116]], [1.0, [196, 150, 150]]]}
BOWL_RAMP = {'stops': [[0.0, [26, 20, 22]], [0.6, [120, 96, 80]], [1.0, [250, 222, 170]]]}
LANTERN_RAMP = {'stops': [[0.0, [20, 12, 8]], [0.5, [120, 80, 40]], [1.0, [255, 236, 190]]]}


def structure(lit):
    """the drawn architecture, as coordinates. lit: the room and the doorway reveal take the lamp's colour."""
    S = []
    room = [88, 60, 44, 255] if lit else [34, 32, 46, 255]
    room_floor = [70, 46, 34, 255] if lit else [26, 24, 34, 255]
    reveal = [26, 22, 30, 255]
    wood = [52, 38, 36, 255]; wood_hi = [92, 68, 56, 255]; dark = [12, 11, 18, 255]
    # room: back wall, ceiling, floor
    S.append(rect(XMIN, 0, WALL_IN, 2.72, room))
    S.append(rect(XMIN, 2.72, WALL_IN, 2.86, [24, 20, 26, 255]))
    S.append(rect(XMIN, -0.18, WALL_IN, 0, room_floor))
    for xb in np.arange(XMIN, WALL_IN, 0.32):
        S.append(line([(xb, -0.18), (xb, 0)], [18, 14, 18, 255], 2))
    # wainscot line and a picture rail, so the room reads as a room
    S.append(line([(XMIN, 0.9), (WALL_IN, 0.9)], [24, 20, 26, 160] if not lit else [70, 46, 34, 255], 3))
    # the doorway reveal: the far jamb of the thick wall, seen through the cut
    S.append(rect(WALL_IN, 0, WALL_OUT, LINTEL, reveal))
    # the door frame: two cased posts and the head, so the doorway reads as a frame you can be half inside
    S.append(rect(WALL_IN - 0.05, 0.04, WALL_IN + 0.03, LINTEL, wood)); S.append(line([(WALL_IN + 0.03, 0.04), (WALL_IN + 0.03, LINTEL)], wood_hi, 2))
    S.append(rect(WALL_OUT - 0.03, 0.04, WALL_OUT + 0.06, LINTEL, wood)); S.append(line([(WALL_OUT - 0.03, 0.04), (WALL_OUT - 0.03, LINTEL)], wood_hi, 2))
    # lintel beam
    S.append(rect(WALL_IN - 0.04, LINTEL, WALL_OUT + 0.06, LINTEL + 0.16, wood))
    S.append(line([(WALL_IN - 0.04, LINTEL), (WALL_OUT + 0.06, LINTEL)], wood_hi, 3))
    # sill: a worn stone threshold proud of the floor
    S.append(poly([(WALL_IN - 0.03, 0), (WALL_OUT + 0.10, 0), (WALL_OUT + 0.10, 0.045), (WALL_IN - 0.03, 0.06)], [88, 80, 88, 255] if not lit else [150, 120, 98, 255]))
    # porch deck
    S.append(rect(WALL_OUT, -0.20, 4.92, 0, [34, 28, 36, 255]))
    for xb in np.arange(WALL_OUT + 0.25, 4.9, 0.38):
        S.append(line([(xb, -0.20), (xb, -0.02)], [18, 14, 20, 255], 2))
    S.append(line([(WALL_OUT, 0), (4.92, 0)], [70, 60, 70, 255], 3))
    # steps down to the yard
    S.append(rect(4.92, -0.42, 5.24, -0.22, [30, 26, 34, 255])); S.append(line([(4.92, -0.22), (5.24, -0.22)], [64, 56, 66, 255], 3))
    S.append(rect(5.24, -0.64, 5.56, -0.44, [28, 24, 32, 255])); S.append(line([(5.24, -0.44), (5.56, -0.44)], [60, 52, 62, 255], 3))
    S.append(rect(4.92, -1.2, XMAX, -0.66, [14, 14, 22, 255]))
    S.append(rect(WALL_OUT, -1.2, 4.92, -0.20, [16, 14, 22, 255]))
    for xb in np.arange(WALL_OUT + 0.1, 4.9, 0.22):     # lattice under the porch
        S.append(line([(xb, -0.22), (xb + 0.22, -1.0)], [30, 26, 36, 255], 2))
        S.append(line([(xb + 0.22, -0.22), (xb, -1.0)], [30, 26, 36, 255], 2))
    # porch roof and its post
    S.append(poly([(WALL_OUT, 2.86), (4.85, 2.50), (4.85, 2.36), (WALL_OUT, 2.70)], wood))
    S.append(line([(WALL_OUT, 2.70), (4.85, 2.36)], wood_hi, 3))
    S.append(rect(4.56, 0, 4.70, 2.42, [40, 32, 36, 255]))
    S.append(line([(4.56, 0), (4.56, 2.42)], [70, 58, 62, 255], 2))
    # house roof over the room, off the top of the frame
    S.append(poly([(XMIN, 3.05), (WALL_OUT + 0.25, 3.05), (WALL_OUT + 0.25, 3.6), (XMIN, 3.6)], [18, 16, 24, 255]))
    # bench beside the door, inside
    b0, b1, bh = BENCH
    S.append(rect(b0, bh - 0.06, b1, bh, [60, 40, 32, 255] if lit else [30, 26, 34, 255]))
    S.append(rect(b0 + 0.04, 0, b0 + 0.09, bh - 0.06, [44, 30, 26, 255] if lit else [24, 22, 30, 255]))
    S.append(rect(b1 - 0.09, 0, b1 - 0.04, bh - 0.06, [44, 30, 26, 255] if lit else [24, 22, 30, 255]))
    # lamp cord
    S.append(line([(LAMP[0], 2.72), (LAMP[0], LAMP[1] + 0.2)], [10, 8, 10, 255], 2))
    return S


def wall_section():
    """the cut stone of the wall, above the lintel and below the floor: the poché is filled with found stone."""
    return [poly([(WALL_IN, LINTEL + 0.16), (WALL_OUT, LINTEL + 0.16), (WALL_OUT, 3.05), (WALL_IN, 3.05)], [255, 255, 255, 255]),
            poly([(XMIN, -0.18), (WALL_OUT, -0.18), (WALL_OUT, -1.2), (XMIN, -1.2)], [255, 255, 255, 255])]


def land():
    pts = [(WALL_OUT, 0.18)]
    xs = np.linspace(WALL_OUT, XMAX, 24)
    for i, x in enumerate(xs):
        pts.append((x, 0.2 + 0.06 * np.sin(i * 1.7) + 0.04 * np.sin(i * 0.6)))
    pts += [(XMAX, -1.2), (WALL_OUT, -1.2)]
    return [poly(pts, [18, 17, 30, 255])]


def build_world(G):
    import ops as O
    plates = {}
    sky = G.op('vgradient', [G.drawn('ramp sky', SKY, 'dusk sky stops')], {'size': [PW, PH]}, label='dusk sky gradient')
    # cloud from 'Top Of The Cloud - Time Lapse' (public domain), recoloured to dusk, luminance as its matte
    cf, _ = copy_found('cloud-sam', [20])
    cloud = G.source(cf[20], 'CEP391:3a3663e4-7a6e-5277-8cf5-12e94237350c:f020', 'Top Of The Cloud - Time Lapse (Wide Screen 16:9)', 'https://archive.org/details/CEP391', 'public_domain')
    cloudc = G.op('crop', [cloud], {'box': [0, 60, 384, 250]})
    cloudr = G.op('recolor', [cloudc, G.drawn('ramp cloud', CLOUD_RAMP, 'cloud at dusk')], {'gain': 1.3, 'lift': -0.05})
    clouda = G.op('luma_alpha', [cloudr], {'lo': 0.28, 'hi': 0.7, 'opacity': 0.55})
    # Quick, Draw! moon, trees, fence (CC BY 4.0)
    qp = quickdraw_pick()
    qd = G.source(qp, 'quickdraw:selection', 'Quick, Draw! drawings (Google Creative Lab and contributors)', 'https://quickdraw.withgoogle.com/data', 'CC-BY-4.0',
                  kind='strokes', credit='Quick, Draw! by Google Creative Lab, CC BY 4.0; drawings by anonymous players, identified by key_id')
    drawings = G.get(qd)
    def qd_node(key, size, width, color):
        return G.op('qd_strokes', [qd], {'key_id': key, 'size': size, 'width': width, 'color': color}, label='Quick, Draw! ' + key)
    G.register('qd_strokes', 1, lambda dr, key_id, size, width, color: O.op_strokes(next(d for d in dr if d['key_id'] == key_id), size, width, color),
               'render one Quick, Draw! drawing (by key_id) as chalk strokes')
    moon = next(d for d in drawings if d['word'] == 'moon')
    trees = [d for d in drawings if d['word'] == 'tree']
    fence = next(d for d in drawings if d['word'] == 'fence')
    n_moon = qd_node(moon['key_id'], [150, 150], 4, [236, 226, 196])
    n_trees = [qd_node(t['key_id'], [260, 300], 3.2, [96, 88, 124]) for t in trees]
    n_fence = qd_node(fence['key_id'], [420, 140], 3, [70, 64, 92])
    glow = G.op('radial', [], {'size': [300, 300], 'color': [230, 210, 180, 60], 'falloff': 2.2})
    land_n = G.op('draw', [G.drawn('far land', {'shapes': land()}, 'the yard and fields beyond the porch')], {'size': [PW, PH]})
    # stone: the pillar of the house in the home movie (dog clip f000), cut, recoloured, tiled into the wall section
    f0 = G.source('paeleo/handmade/kit/archive-dog/frames/f000.jpg', 'NJC:2fdacde1-8a23-58e1-b905-5407385bd039:f000', 'Amateur Film New Jersey C (Home Movies, Internet Archive)', 'https://archive.org/details/NewJerseyC', 'public_domain')
    stone = G.op('crop', [f0], {'box': [326, 30, 382, 200]}, label='stone of the pillar in the home movie')
    stone2 = G.op('scale', [stone], {'k': 1.6})
    sec = G.op('draw', [G.drawn('wall section matte', {'shapes': wall_section()}, 'where the wall is cut')], {'size': [PW, PH]})
    struct = {}
    for lit in (False, True):
        tag = 'lit' if lit else 'dusk'
        st = G.op('recolor', [stone2, G.drawn('ramp stone ' + tag, STONE_LIT if lit else STONE_DUSK, 'stone colour')], {'gain': 1.2, 'lift': 0})
        tiled = G.op('tile_bond', [st], {'size': [PW, PH]})
        poche = G.op('mask_with', [tiled, sec], {}, label='wall section in found stone (' + tag + ')')
        struct[tag] = (G.op('draw', [G.drawn('architecture ' + tag, {'shapes': structure(lit)}, 'room, doorway reveal, lintel, sill, porch, steps, roof, bench')], {'size': [PW, PH]}), poche)
    # bowl: the pan at the dog's feet in the home movie, cut with a drawn line, set inside on the floor
    G.register('draw_alpha', 1, lambda pd, size: O.poly_alpha(tuple(size), pd['polys'], 4, 0.6), 'rasterise a drawn polygon as a matte')
    bowl_raw = G.op('crop', [f0], {'box': [236, 218, 316, 270]})
    bowl_cut = G.op('cutout', [bowl_raw, G.op('draw_alpha', [G.drawn('bowl cut', {'polys': [[[6, 14], [18, 6], [44, 3], [70, 7], [78, 16], [74, 36], [62, 47], [40, 50], [18, 46], [7, 34]]]}, 'the pan, cut by hand')], {'size': [80, 52]})], {})
    bowl = {t: G.op('recolor', [bowl_cut, G.drawn('ramp bowl ' + t, BOWL_RAMP if t == 'lit' else STONE_DUSK, 'bowl')], {'gain': 1.1, 'lift': 0}) for t in ('dusk', 'lit')}
    shade = {t: G.op('room_shade', [], {'size': [PW, PH], 'box_px': P(XMIN, 2.72) + P(WALL_IN - 0.05, -0.18), 'lamp_px': P(LAMP[0], LAMP[1] - 0.2),
                                        'radius_px': 3.0 * PPM, 'strength': 0.78 if t == 'lit' else 0.55}) for t in ('dusk', 'lit')}
    for tag in ('dusk', 'lit'):
        parents = [sky, clouda, glow, n_moon, land_n] + n_trees + [n_fence, struct[tag][0], struct[tag][1], bowl[tag], shade[tag]]
        ix = {n: parents.index(n) for n in parents}
        I = np.eye(3).tolist()
        pl = [[ix[sky], I, 1.0],
              [ix[clouda], Mplace((384, 190), 0.6, 1.55, 5.9, 3.1), 1.0],
              [ix[glow], Mplace((300, 300), 3.05, 2.25, 4.15, 3.35), 1.0],
              [ix[n_moon], Mplace((150, 150), 3.38, 2.55, 3.82, 2.99), 1.0]]
        tree_spots = [(1.2, 0.95), (2.35, 1.25), (3.55, 1.05), (4.4, 1.4), (5.45, 1.15)]
        for nt, (tx, th) in zip(n_trees, tree_spots):
            pl.append([ix[nt], Mplace((260, 300), tx - th * 0.45, 0.16, tx + th * 0.45, 0.16 + th * 1.04), 1.0])
        pl.append([ix[land_n], I, 1.0])
        pl.append([ix[n_fence], Mplace((420, 140), 0.9, 0.12, 2.9, 0.62), 0.8])
        pl.append([ix[n_fence], Mplace((420, 140), 3.0, 0.12, 5.0, 0.62), 0.8])
        pl.append([ix[struct[tag][0]], I, 1.0])
        pl.append([ix[struct[tag][1]], I, 1.0])
        pl.append([ix[shade[tag]], I, 1.0])
        pl.append([ix[bowl[tag]], Mplace((80, 52), BOWL_X - 0.24, -0.01, BOWL_X + 0.24, 0.30), 1.0])
        plates[tag] = G.op('composite', parents, {'size': [PW, PH], 'placements': pl, 'bg': [0, 0, 0, 255]}, label='set plate (' + tag + ')')
    return plates
