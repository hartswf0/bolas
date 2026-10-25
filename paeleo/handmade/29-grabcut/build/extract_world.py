"""Segmentation operator for the world pieces: box seeds + scribble seeds -> GrabCut (our BK graph cut) -> cleanup.
Every box and scribble is manual contour markup, versioned here (source-frame pixel coordinates).
python3 extract_world.py [name ...]   -> build/cache/world/<name>.npz
"""
import sys, os, json, time
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graphcut import grabcut, cleanup, poly_mask, dilate, erode, box_blur

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
DOG = os.path.join(ROOT, 'paeleo/handmade/kit/archive-dog')
DOOR = os.path.join(ROOT, 'paeleo/handmade/kit/archive-door')
HAND = '/home/user/hartswf0/secondhand-motion/shots/hand-sam'
OUT = os.path.join(HERE, 'cache/world')

# name: (shot dir, frame, box [x0,y0,x1,y1], fg scribbles [polyline...], bg scribbles, use_sam, extra)
PIECES = {
    'woman_stand': (DOOR, 0, [188, 8, 334, 288], [[(262, 40), (262, 250)], [(250, 30), (275, 30)], [(215, 140), (225, 200)]],
                    [[(150, 30), (150, 250)], [(345, 20), (345, 260)], [(190, 20), (215, 8)], [(203, 172), (204, 286)], [(196, 165), (196, 288)]], False, {}),
    'woman_reach': (DOOR, 12, [150, 25, 280, 288], [[(232, 50), (232, 190)], [(215, 210), (215, 280)], [(190, 150), (200, 175)], [(240, 30), (242, 45)]],
                    [[(140, 40), (140, 160)], [(290, 30), (290, 270)], [(175, 30), (175, 120)], [(160, 230), (170, 280)]], False, {}),
    'woman_walk': (DOOR, 16, [160, 40, 240, 288], [[(200, 90), (200, 180)], [(205, 200), (195, 270)], [(178, 30 + 20), (178, 75)]],
                   [[(150, 40), (150, 270)], [(255, 60), (255, 270)], [(170, 260), (172, 285)]], False, {}),
    'door_panel': (DOOR, 28, None, [], [], True, {'er': 6, 'di': 8}),
    'hand': (HAND, 10, None, [], [], True, {'forearm': True, 'keep_near': 3}),
    'pillar': (DOG, 6, [312, 40, 384, 215], [[(350, 70), (350, 200)], [(370, 60), (372, 205)]],
               [[(300, 40), (300, 210)], [(330, 230), (380, 232)]], False, {'open_right': True}),
    'shrub': (DOG, 6, [125, 0, 200, 50], [[(160, 8), (162, 40)], [(150, 20), (172, 22)]],
              [[(118, 5), (118, 48)], [(205, 5), (205, 48)], [(130, 52), (195, 54)]], False, {'open_top': True}),
    'bowl': (DOG, 6, [228, 214, 322, 270], [[(250, 235), (300, 235)], [(260, 250), (290, 250)]],
             [[(222, 214), (222, 270)], [(328, 214), (328, 270)], [(230, 276), (320, 276)]], False, {}),
}


def lines_mask(H, W, polylines, ox, oy, width=5):
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    for pl in polylines:
        d.line([(x - ox, y - oy) for x, y in pl], fill=255, width=width)
    return np.array(im) > 127


def run(name):
    sd, fi, box, fgs, bgs, use_sam, ex = PIECES[name]
    t0 = time.time()
    full = np.array(Image.open(os.path.join(sd, 'frames/f%03d.jpg' % fi)).convert('RGB'))
    Hf, Wf = full.shape[:2]
    if use_sam:
        masks = json.load(open(os.path.join(sd, 'masks.json')))
        sam_full = poly_mask(masks[str(fi)], Hf, Wf)
        ys, xs = np.nonzero(sam_full)
        m = 12 if not ex.get('forearm') else 40
        x0, y0 = max(0, xs.min() - m), max(0, ys.min() - m)
        x1 = Wf if ex.get('forearm') else min(Wf, xs.max() + m)
        y1 = min(Hf, ys.max() + m)
    else:
        x0, y0, x1, y1 = box
        x0 = max(0, x0 - 10); y0 = max(0, y0 - 10); x1 = min(Wf, x1 + 10); y1 = min(Hf, y1 + 10)
        sam_full = np.zeros((Hf, Wf), bool)
        sam_full[box[1]:box[3], box[0]:box[2]] = True
    img = full[y0:y1, x0:x1]; prior = sam_full[y0:y1, x0:x1]
    H, W = prior.shape
    arm = np.zeros_like(prior); card = np.zeros_like(prior)
    if ex.get('forearm'):
        # the SAM mask stops at the wrist: the forearm (bright, running off the right edge) is scribbled fg, and the
        # card the fingers overlap (the adjacent object) is scribbled bg, before any bg seeding by distance
        grey = img.mean(2)
        ys, xs = np.nonzero(prior); xr = xs.max()
        arm[:, xr - 6:] = box_blur(grey, 1)[:, xr - 6:] > 98
        rows = np.arange(H)[:, None]
        arm &= (rows > ys.min() - 30) & (rows < ys.max() + 2)
        card = (grey > 70) & (grey < 128) & ~dilate(prior | arm, 5)
        prior = prior | arm
    seed = np.zeros((H, W), np.int8)
    if use_sam:
        seed[erode(prior, ex.get('er', 4))] = 1
        seed[~dilate(prior, ex.get('di', 8))] = 2
    else:
        seed[~prior] = 2
    if ex.get('forearm'):
        seed[erode(arm, 2)] = 1
        seed[erode(card, 2)] = 2
    seed[lines_mask(H, W, fgs, x0, y0)] = 1
    seed[lines_mask(H, W, bgs, x0, y0)] = 2
    up = 2
    img_u = np.array(Image.fromarray(img).resize((W * up, H * up), Image.BICUBIC))
    pr_u = np.array(Image.fromarray(prior.astype(np.uint8) * 255).resize((W * up, H * up), Image.NEAREST)) > 127
    sd_u = np.array(Image.fromarray(seed).resize((W * up, H * up), Image.NEAREST))
    res = grabcut(img_u, pr_u, sd_u, iters=5, prior_w=(0.25 if use_sam else 0.0) / up)
    a_u, cl = cleanup(res['fg'], res['sm'], keep_near=ex.get('keep_near', 0))
    alpha = a_u.reshape(H, up, W, up).mean((1, 3))
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(os.path.join(OUT, name + '.npz'), alpha=alpha.astype(np.float16), rgb=img, origin=np.array([x0, y0]),
                        fg=alpha > .5, sam=prior, seed=seed)
    info = {'src': os.path.relpath(sd, ROOT) if sd.startswith(ROOT) else sd, 'frame': fi, 'box': [int(x0), int(y0), int(x1), int(y1)],
            'iters': res['log'], 'cleanup': cl, 'secs': round(time.time() - t0, 2)}
    print(name, info['secs'], cl, [l['changed_px'] for l in res['log']], flush=True)
    return info


if __name__ == '__main__':
    names = sys.argv[1:] or list(PIECES)
    logp = os.path.join(OUT, 'log.json')
    os.makedirs(OUT, exist_ok=True)
    log = json.load(open(logp)) if os.path.exists(logp) else {}
    for n in names:
        log[n] = run(n)
    json.dump(log, open(logp, 'w'), indent=1)
