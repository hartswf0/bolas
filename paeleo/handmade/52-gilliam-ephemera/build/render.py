"""The rostrum camera: shoots each exposure of the x-sheet onto n film frames (grain changes every film frame, the
lamp flickers a little per exposure), and measures the dog from the shot layer for the trace.
Writes cache/frames/s%03d.jpg (768 scene frames) and ../trace.json."""
import json, math, os, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world
from world import W, H, sky_layer, house_layers, door_layer, lightmap, place_at, OPEN_L, OPEN_R, X_D, K
from puppets import draw_dog, draw_person, dog_points
from table import place, T, pin

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(FOLDER)))
OUT = os.path.join(HERE, 'cache', 'frames')
XS = json.load(open(os.path.join(FOLDER, 'xsheet.json')))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
G = {}


def init():
    G['sky'] = sky_layer()
    G['inner'], G['house'] = house_layers()
    G['doors'] = {}


def jitter(k, piece_scale=1.0):
    r = np.random.default_rng(1000 + k)
    return r.normal(0, .35 * piece_scale, 2)


def shoot(e):
    k = e['k']
    sky = G['sky'].copy()
    place(sky, 'moon', T(1120, 70 + e.get('moon_dy', 0)), shadow=(1, 2, .25))
    place_at(sky, 'cloud', 900 + e['cloud_dx'] + 200, 250, tint=(.8, .75, .9), shadow=None, alpha=.85)
    if e.get('hand_x') is not None:      # the giant hand comes in over the table edge and lowers the moon
        tp = pin('giant_hand', 'tip')
        place(sky, 'giant_hand', T(e['hand_x'], 112 + e.get('moon_dy', 0)) @ T(-tp[0], -tp[1]), shadow=(6, 8, .45), tint=(.78, .78, .92))
    lit = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    lit.alpha_composite(G['inner'])
    if e['door'] not in G['doors']:
        G['doors'][e['door']] = door_layer(e['door'])
    lit.alpha_composite(G['doors'][e['door']])
    lit.alpha_composite(G['house'])
    pp = dict(e['person'])
    if k > 0 and XS['exposures'][k - 1]['person'] != e['person']:     # a touched card is never put back exactly
        j = jitter(k); pp['X'] += j[0]; pp['nod'] = pp['nod'] + j[1]
    draw_person(lit, pp)
    dog = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    rec = []
    dp = dict(e['dog'])
    if k > 0 and XS['exposures'][k - 1]['dog'] != e['dog'] and 'head' in dp:
        j = jitter(k + 500); dp['head'] += j[0] * 1.2; dp['tail'] = dp.get('tail', 0) + j[1] * 2
    draw_dog(dog, dp, rec=rec)
    # measure the dog from what was shot
    A = np.asarray(dog.getchannel('A')).astype(np.float32) / 255
    ys, xs_ = np.nonzero(A > .5)
    meas = None
    if len(xs_):
        wts = A[ys, xs_]
        cx = float((xs_ * wts).sum() / wts.sum()); cy = float((ys * wts).sum() / wts.sum())
        bbox = [int(xs_.min()), int(ys.min()), int(xs_.max()), int(ys.max())]
        hx = None; head_top = None; withers = None
        for name, x0, y0, al in rec:
            if name in ('dog_head', 'dog_backhead', 'dog_lookback', 'dog_head_low'):
                a = np.asarray(al).astype(np.float32); yy, xx = np.nonzero(a > 128)
                hx = float(xx.mean() + x0); hy = float(yy.mean() + y0); head_top = int(yy.min() + y0)
            if name == 'dog_front':
                a = np.asarray(al).astype(np.float32); hh = a.shape[0]
                top = a[: int(hh * .45)]; yy, xx = np.nonzero(top > 128)
                hx = float(xx.mean() + x0); hy = float(yy.mean() + y0)
        tor = [r for r in rec if r[0] == 'dog_torso']
        if tor:
            _, x0, y0, al = tor[0]; a = np.asarray(al).astype(np.float32); yy, xx = np.nonzero(a > 128)
            bx = float(xx.mean() + x0)
            # the line of the back: the top edge of the torso card over its middle third
            mid = a[:, a.shape[1] // 3: 2 * a.shape[1] // 3] > 128
            rows = np.nonzero(mid.any(axis=1))[0]
            back_y = float(rows.min() + y0) if len(rows) else None
            if 'card' not in dp:   # the withers: top of the torso card in the column of the shoulder pin
                sx = int(dog_points(dp)['shoulder'][0]) - x0
                col = (a[:, max(0, sx - 4):sx + 5] > 128).any(axis=1)
                withers = int(np.nonzero(col)[0].min() + y0)
        else:
            bx = cx; back_y = None
        if 'card' in dp:
            facing = 1 if hx < cx else -1      # turning card: where its head is
        else:
            pts_ = dog_points(dp)
            facing = 1 if pts_['head'][0] < pts_['neck'][0] - 1 else -1  # the head card's muzzle pin left of the neck pin: +1 toward the door
        body_facing = dp.get('face', 1)
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
        inside = float(((A[:, OPEN_L:OPEN_R] > .5).sum()) / max(1, (A > .5).sum()))
        meas = {'x_screen': round(cx, 2), 'y_screen': round(cy, 2), 'bbox': bbox, 'facing': facing, 'body_facing': body_facing, 'head_xy': [round(hx, 1), round(hy, 1)],
                'aspect_h_w': round(h / max(1, w), 3), 'share_inside_door_frame_px': round(inside, 3),
                'back_line_y': back_y, 'head_top_y': head_top, 'withers_y': withers,
                'muzzle_y': round(dog_points(dp)['head'][1], 1) if 'card' not in dp else None, 'head_piece': next((r[0] for r in rec if r[0] in ('dog_head', 'dog_backhead', 'dog_front', 'dog_lookback', 'dog_head_low')), None)}
        if 'card' not in dp:
            pts = dog_points(dp)
            meas['feet'] = {kk: [round(v[0], 2), round(v[1], 2)] for kk, v in pts.items() if kk.startswith('dog_')}
    lit.alpha_composite(dog)
    a = np.asarray(lit).astype(np.float32) / 255
    L = lightmap(e['open'], e['t'])
    rgb = np.clip(a[..., :3] * L, 0, 1); al = a[..., 3:]
    s = np.asarray(sky.convert('RGB')).astype(np.float32) / 255
    img = s * (1 - al) + rgb * al
    r = np.random.default_rng(k)
    img *= 1 + r.normal(0, .008)                 # lamp flicker per exposure
    # vignette of the rostrum lamps
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - .22 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
    img *= vig[..., None]
    for f in range(e['f0'], e['f0'] + e['n']):
        rr = np.random.default_rng(10000 + f)
        g = rr.normal(0, .022, (H // 2, W // 2)).astype(np.float32)
        g = np.repeat(np.repeat(g, 2, 0), 2, 1)
        fr = np.clip(img + g[..., None] * (.5 + .5 * img), 0, 1)
        Image.fromarray((fr * 255).astype(np.uint8)).save(os.path.join(OUT, 's%03d.jpg' % f), quality=90)
    return e['k'], meas


def main():
    os.makedirs(OUT, exist_ok=True)
    ex = XS['exposures']
    only = None
    if len(sys.argv) > 1:
        only = set(int(v) for v in sys.argv[1].split(','))
        ex = [e for e in ex if any(e['f0'] <= f < e['f0'] + e['n'] for f in only)]
    with Pool(3, initializer=init) as p:
        res = dict(p.map(shoot, ex, chunksize=4))
    if only:
        return
    sc = {f['i']: f for f in SCORE['frames']}
    frames = []
    for e in XS['exposures']:
        m = res[e['k']]
        for f in range(e['f0'], e['f0'] + e['n']):
            s = sc[f]['dog']
            posture = 'lying' if m['aspect_h_w'] < .55 else ('crouched' if e['dog'].get('drop', 0) >= 4 and s['act']['lie'] < .5 else 'standing')
            frames.append({'i': f, 't': round(f / 24, 4), 'state': e['state'], 'x_score': s['x'], 'x_screen': m['x_screen'],
                           'y_screen': m['y_screen'], 'facing': m['facing'], 'body_facing': m['body_facing'], 'posture': posture, 'exposure': e['k'],
                           'exposure_first_frame': e['f0'], 'card': e['dog_label'], 'head_piece': m['head_piece'],
                           'head_xy': m['head_xy'], 'back_line_y': m['back_line_y'], 'head_top_y': m['head_top_y'],
                           'withers_y': m['withers_y'], 'muzzle_y': m['muzzle_y'], 'bbox': m['bbox'], 'aspect_h_w': m['aspect_h_w'],
                           'share_inside_door_frame_px': m['share_inside_door_frame_px'], 'feet': m.get('feet')})
    json.dump({'about': 'measured from the rendered dog layer of each exposure (alpha centroid, bbox, muzzle pin of the head card vs '
                        'the neck pin for facing: +1 = head toward the door). state = the score state the x-sheet '
                        'acts on that frame. No camera moves: x_screen is in fixed screen pixels, x_metres = (x_screen-290)/210.',
               'frames': frames}, open(os.path.join(FOLDER, 'trace.json'), 'w'))
    print('frames', len(frames))


if __name__ == '__main__':
    main()
