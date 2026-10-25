"""SCION 07 · proof images, made from the encoded film where possible (what a viewer gets), else from the key set.
stills/still_*.jpg (from film.mp4), proof/keys.png (the key drawing set), proof/before_after.png (a naive mirror blend vs
the drawn-view path through a turn), proof/morph_refusal.png, proof/morph_turnback.png, proof/morph_door_light.png
(frames extracted from film.mp4), proof/measures.json."""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
from draw import Canvas, SS
from dog import compose, to_screen
from paint import paint

ROOT = os.path.dirname(HERE)
FILM = os.path.join(ROOT, 'film.mp4')
FONT = ImageFont.truetype(os.path.join(ROOT, '..', '..', '..', 'tools/paeleo/fonts/f14.woff2'), 15)
WASH = (216, 198, 166)


def film_frame(t_scene, out=None):
    t = 3.0 + t_scene + 0.5 / 24
    p = out or os.path.join(HERE, 'cache', 'ff.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '%.4f' % t, '-i', FILM, '-frames:v', '1', p], check=True)
    return Image.open(p).convert('RGB')


def strip(times, box, path, cols=6, title=''):
    w, h = box[2] - box[0], box[3] - box[1]
    rows = (len(times) + cols - 1) // cols
    W = Image.new('RGB', (w * cols, h * rows + 26), (245, 242, 235))
    d = ImageDraw.Draw(W); d.text((6, 5), title, font=FONT, fill=(30, 30, 30))
    for i, t in enumerate(times):
        im = film_frame(t).crop(box)
        ImageDraw.Draw(im).text((5, 4), '%.2f s (frame %d)' % (t, round(t * 24)), font=FONT, fill=(255, 255, 255))
        W.paste(im, ((i % cols) * w, 26 + (i // cols) * h))
    W.save(path)


def keysheet(path):
    cells = [('stand', 'profile', (-0.55, 0.73, 0, 1), 'stand (watch)'), ('crouch', 'profile', (-0.56, 0.53, 0.18, 1), 'crouch (retreat)'),
             ('stand', 'profile', (-0.60, 0.40, 0.30, 1), 'stand, head low (approach)'), ('lie', 'profile', (-0.50, 0.47, 0, 1), 'lie'),
             ('rear34L', 'rear34', (-0.33, 0.68, 0, .95), 'rear 3/4'), ('rearA', 'rearH', (0, 0.70, 0, .95), 'rear (substitution point)'),
             ('front34L', 'front34', (-0.40, 0.71, 0, 1), 'front 3/4'), ('frontA', 'frontH', (0, 0.72, 0, 1), 'front (substitution point)'),
             ('curl_R', 'profile_R', (0.45, 0.12, -0.3, .97), 'curl (refusal, closed)'), ('lie_R', 'profile', (0.40, 0.50, 0, 1), 'lie, looking back'),
             ('lie', 'rear34', (-0.47, 0.56, -0.18, 1), 'lie, looking in'), ('lie', 'profile', (-0.565, 0.13, 0.12, 1), 'lie, chin down (stays)')]
    W, H = 1280, 760
    im = Image.new('RGB', (W * SS, H * SS), (236, 230, 216)); cv = Canvas(im)
    S = 175
    for i, (b, h, pl, lab) in enumerate(cells):
        ox = 165 + (i % 4) * 315; oy = 205 + (i // 4) * 245
        st, m = compose({b: 1}, {h: 1}, pl, ear=0.9, tv=0.5)
        paint(cv, to_screen(st, ox, oy, S, 0), WASH, S, fwd=m['fwd'])
    out = im.reduce(SS); d = ImageDraw.Draw(out)
    for i, (b, h, pl, lab) in enumerate(cells):
        d.text((25 + (i % 4) * 315, 215 + (i // 4) * 245), lab, font=FONT, fill=(40, 36, 40))
    d.text((25, 8), 'SCION 07 key contour set (dog). Body keys x head keys; point i of a stroke corresponds across every key.', font=FONT, fill=(30, 30, 30))
    out.save(path)


def before_after(path):
    """top: the flat answer, a straight blend of a key and its mirror. bottom: the drawn-view path the film uses."""
    S = 175
    rows = [('naive: stand -> its mirror (linear blend of corresponding points)',
             [({'stand': 1 - u, 'stand_R': u}, {'profile': 1 - u, 'profile_R': u}, (-0.55 + 1.1 * u, 0.73, 0, 1)) for u in (0, .25, .5, .75, 1)]),
            ('film: stand -> rear 3/4 -> rear | substitution | rear 3/4 -> stand facing away',
             [({'stand': 1}, {'profile': 1}, (-0.55, 0.73, 0, 1)), ({'rear34L': 1}, {'rear34': 1}, (-0.33, 0.68, 0, .95)),
              ({'rearA': 1}, {'rearH': 1}, (0, 0.70, 0, .95)), ({'rear34R': 1}, {'rear34_R': 1}, (0.33, 0.64, 0, .95)),
              ({'stand_R': 1}, {'profile_R': 1}, (0.55, 0.73, 0, 1))]),
            ('naive: the head looking away -> looking back (mirror blend): the head goes edge-on, a stick',
             [({'lie_R': 1}, {'profile_R': 1 - u, 'profile': u}, (0.56 - .16 * u, 0.28 + .22 * u, -.05 * (1 - u), 1)) for u in (0, .25, .5, .75, 1)]),
            ('film: profile -> 3/4 front -> front | substitution | -> 3/4 front -> profile looking back',
             [({'lie_R': 1}, {'profile_R': 1}, (0.56, 0.27, -0.05, 1)), ({'lie_R': 1}, {'front34_R': 1}, (0.56, 0.27, -0.05, 1)),
              ({'lie_R': 1}, {'frontH': 1}, (0.54, 0.35, 0, 1)), ({'lie_R': 1}, {'front34': 1}, (0.50, 0.42, 0, 1)),
              ({'lie_R': 1}, {'profile': 1}, (0.40, 0.50, 0, 1))])]
    W, H = 1280, 4 * 190 + 10
    im = Image.new('RGB', (W * SS, H * SS), (236, 230, 216)); cv = Canvas(im)
    for r, (lab, cells) in enumerate(rows):
        for c, (bw, hw, pl) in enumerate(cells):
            st, m = compose(bw, hw, pl, ear=0.9, tv=0.5)
            paint(cv, to_screen(st, 128 + c * 256, 175 + r * 190, S, 0), WASH, S, fwd=m['fwd'])
    out = im.reduce(SS); d = ImageDraw.Draw(out)
    for r, (lab, cells) in enumerate(rows):
        d.text((10, 6 + r * 190), lab, font=FONT, fill=(150, 20, 20) if lab.startswith('naive') else (20, 70, 30))
    out.save(path)


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'stills'), exist_ok=True); os.makedirs(os.path.join(ROOT, 'proof'), exist_ok=True)
    for t in (3.6, 9.0, 19.0, 28.0):
        film_frame(t).save(os.path.join(ROOT, 'stills', 'still_%04.1fs.jpg' % t), quality=92)
    keysheet(os.path.join(ROOT, 'proof', 'keys.png'))
    before_after(os.path.join(ROOT, 'proof', 'before_after.png'))
    strip([3.42 + i * 2 / 24 for i in range(12)], (930, 360, 1280, 600), os.path.join(ROOT, 'proof', 'morph_refusal.png'),
          title='the refusal (score 3.417): every second frame from film.mp4')
    strip([7.38 + i / 24 for i in range(18)] + [7.38 + 18 / 24 + i * 2 / 24 for i in range(6)], (930, 360, 1280, 600),
          os.path.join(ROOT, 'proof', 'morph_turnback.png'), title='turning back to look (score 7.458): frames from film.mp4')
    strip([6.1 + i * 0.1 for i in range(12)], (0, 120, 640, 660), os.path.join(ROOT, 'proof', 'morph_door_light.png'), cols=6,
          title='the door opens and its outline is laid down as light (6.2-7.2 s): frames from film.mp4')
    strip([23.6 + i * 0.25 for i in range(6)] + [26.3 + i * 0.3 for i in range(6)] + [28.2 + i * 0.4 for i in range(6)],
          (150, 380, 700, 640), os.path.join(ROOT, 'proof', 'morph_sill.png'), title='lying across the sill, looking in, staying: frames from film.mp4')
    tr = json.load(open(os.path.join(ROOT, 'trace.json')))['frames']
    ap = [f for f in tr if f['state'] == 'approach']
    ld = [f for f in tr if f['t'] >= 24.5]
    lv = json.load(open(os.path.join(HERE, 'cache', 'levels.json')))
    meas = {'approach_head_top_below_withers_px': {'min': min(f['head_below_back_px'] for f in ap[7:]), 'max': max(f['head_below_back_px'] for f in ap),
                                                    'first_frame_below': next(f['t'] for f in ap if f['head_below_back_px'] > 0),
                                                    'note': 'positive = head top lower on screen than the withers; first 7 frames of the approach are the head going down'},
            'lying_px_inside_door_frame': min(f['front_px_inside_frame'] for f in ld), 'lying_px_outside_door_frame': min(f['rear_px_outside_frame'] for f in ld),
            'refusal_back_turned_share': json.load(open(os.path.join(ROOT, 'invariants.json')))['I4_refusal']['share_turned'] if os.path.exists(os.path.join(ROOT, 'invariants.json')) else None,
            'sound_levels_dbfs_rms': lv,
            'film_bytes': os.path.getsize(FILM)}
    json.dump(meas, open(os.path.join(ROOT, 'proof', 'measures.json'), 'w'), indent=1)
    print(json.dumps(meas, indent=1))
