"""Landmark fitter: automatic fit -> anatomy check -> recorded manual correction, for every head of the angle artwork.

The automatic fitter is a generic portrait rig of the kind photo-head tools apply: it assumes an upright frontal face in the
cut's bounding box (eyes on a line at 42 % height, symmetric; nose at 68 %; chin at the bottom; ear bases at the top
corners), then snaps the eyes and the nose to the darkest local minimum inside a search window. It is run blind on all five
heads. Its output is checked against the dog's anatomy (tests below); every failure is reported and replaced by a hand
landmark with the reason. Outputs: actor/landmarks.json (auto, corrected, errors, verdicts), actor/compat.json (the
compatibility classifier for portrait type and orientation), proof/review_pairs.jpg (auto vs corrected, side by side).
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import spec

P = json.load(open(os.path.join(FOLDER, 'actor', 'parts.json')))
NAMES = ['eye_l', 'eye_r', 'nose', 'ear_l', 'ear_r', 'chin', 'jaw_hinge']

# hand landmarks in SOURCE px of each head's frame (read on 8x gridded crops, proof/annotation_grids.jpg). None = not visible.
MANUAL = {
    'profile': {'eye_l': (89, 84), 'eye_r': None, 'nose': (78, 83), 'ear_l': (101, 84), 'ear_r': None, 'chin': (83, 93), 'jaw_hinge': (95, 99)},
    'low':     {'eye_l': (253, 153), 'eye_r': None, 'nose': (274, 180), 'ear_l': (243, 134), 'ear_r': None, 'chin': (264, 188), 'jaw_hinge': (250, 170)},
    'tq':      {'eye_l': (209, 122), 'eye_r': (220, 123), 'nose': (225, 138), 'ear_l': (199, 112), 'ear_r': (229, 108), 'chin': (220, 146), 'jaw_hinge': (207, 138)},
    'front':   {'eye_l': (214, 122), 'eye_r': (232, 123), 'nose': (228, 140), 'ear_l': (203, 112), 'ear_r': (240, 110), 'chin': (226, 151), 'jaw_hinge': (212, 145)},
    'back':    {'eye_l': None, 'eye_r': None, 'nose': None, 'ear_l': (125, 68), 'ear_r': (140, 66), 'chin': None, 'jaw_hinge': None},
}
WHY = {
    'profile': 'profile, muzzle raised 30 deg: the frontal template puts two eyes and a centred nose on a head that shows one eye; '
               'the dark snap finds the dark ear/neck patch behind the skull and calls it the nose.',
    'low': 'muzzle pointing down: the template chin lands on the white neck ruff, the nose window holds the dark eye.',
    'tq': 'three-quarter: closest to the template; eyes are near but the far eye snaps into the dark cheek and the chin sits on the chest.',
    'front': 'near-frontal: the template is close; ear bases sit too low on these drop ears.',
    'back': 'back of the head: no face is visible. The fitter still places two eyes, a nose and a chin on the fur - a face on the back of a head. '
            'Manual: ears only; the face landmarks are declared absent.',
}


def to_sprite(name, pt):
    if pt is None: return None
    p = P['head_' + name]; x0, y0 = p['box_src'][:2]; k = p['scale_from_source']
    x, y = (pt[0] - x0) * k, (pt[1] - y0) * k
    if p['mirrored']: x = p['size'][0] - x
    return [round(x, 1), round(y, 1)]


def auto_fit(img):
    a = np.array(img)[:, :, 3].astype(float); g = np.array(img.convert('L')).astype(float)
    ys, xs = np.nonzero(a > 128); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max(); w, h = x1 - x0, y1 - y0
    tpl = {'eye_l': (.32, .42), 'eye_r': (.68, .42), 'nose': (.5, .68), 'ear_l': (.15, .2), 'ear_r': (.85, .2), 'chin': (.5, .95), 'jaw_hinge': (.22, .8)}
    gs = np.array(Image.fromarray(g.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))).astype(float)
    gs[a < 128] = 255
    out = {}
    for k, (u, v) in tpl.items():
        px, py = x0 + u * w, y0 + v * h
        if k in ('eye_l', 'eye_r', 'nose'):
            r = int(0.12 * w)
            xa, xb, ya, yb = int(max(0, px - r)), int(min(a.shape[1], px + r)), int(max(0, py - r)), int(min(a.shape[0], py + r))
            win = gs[ya:yb, xa:xb]
            j = np.unravel_index(np.argmin(win), win.shape)
            px, py = xa + j[1], ya + j[0]
        out[k] = [round(float(px), 1), round(float(py), 1)]
    return out, float(np.hypot(w, h))


def anatomy_tests(name, lm, size):
    """what a dog head must satisfy; each test is numeric on the landmarks"""
    fails = []
    e = [lm[k] for k in ('eye_l', 'eye_r') if lm.get(k)]
    n, c = lm.get('nose'), lm.get('chin')
    view = name
    if view in ('profile', 'low'):
        if len(e) == 2 and abs(e[0][0] - e[1][0]) > 0.12 * size:
            fails.append('two eyes spread across a profile head (a profile shows one eye)')
        if n and e and n[0] > min(p[0] for p in e):
            fails.append('nose behind the eye: the muzzle of a left-facing head must lead the eyes')
    if view in ('front', 'tq'):
        if n and e and n[1] < max(p[1] for p in e):
            fails.append('nose above the eye line')
        if c and n and c[1] < n[1]:
            fails.append('chin above the nose')
    if view == 'back' and (n or e):
        fails.append('face landmarks placed on the back of the head (no face is visible)')
    if n and e:
        d = min(np.hypot(n[0] - p[0], n[1] - p[1]) for p in e)
        if d < 0.12 * size:
            fails.append('nose within %.0f px of an eye: a dog muzzle is longer than a human nose' % d)
    return fails


res = {}; compat = []
pairs = []
for name in ['front', 'tq', 'profile', 'low', 'back']:
    img = Image.open(os.path.join(FOLDER, P['head_' + name]['file'])).convert('RGBA')
    auto, size = auto_fit(img)
    man = {k: to_sprite(name, MANUAL[name][k]) for k in NAMES}
    err = {}
    for k in NAMES:
        if man[k] is None: err[k] = 'auto placed a landmark that is not visible'
        else: err[k] = round(float(np.hypot(auto[k][0] - man[k][0], auto[k][1] - man[k][1])), 1)
    num = [v for v in err.values() if isinstance(v, float)]
    mean_err = round(float(np.mean(num)) / size, 3) if num else None
    fails_auto = anatomy_tests(name, auto, size)
    fails_man = anatomy_tests(name, {k: v for k, v in man.items() if v}, size)
    ok_auto = not fails_auto and mean_err is not None and mean_err < 0.12 and all(isinstance(v, float) for v in err.values())
    res[name] = {'sprite': P['head_' + name]['file'], 'source_frame': P['head_' + name]['frame'], 'mirrored': P['head_' + name]['mirrored'],
                 'head_diag_px': round(size, 1), 'auto': auto, 'corrected': man, 'error_px': err, 'mean_error_over_diag': mean_err,
                 'auto_anatomy_failures': fails_auto, 'corrected_anatomy_failures': fails_man,
                 'verdict': 'auto accepted' if ok_auto else 'auto rejected, hand-corrected', 'why': WHY[name],
                 'pivot': P['head_' + name]['anchors']['pivot']}
    compat.append({'head': name, 'frame': P['head_' + name]['frame'], 'portrait_type': 'archive animal, 16 mm b/w, ~40 px head',
                   'orientation': {'front': 'frontal', 'tq': 'three-quarter', 'profile': 'profile, raised', 'low': 'profile-3/4, lowered', 'back': 'back of head'}[name],
                   'auto_rig': 'compatible' if ok_auto else 'incompatible', 'mean_error_over_diag': mean_err, 'n_anatomy_failures': len(fails_auto)})
    # review pair
    W, H = img.size; S = 4
    pane = []
    for lab, lm, col in (('AUTO', auto, (255, 70, 60)), ('CORRECTED', man, (90, 230, 120))):
        bg = Image.new('RGBA', (W, H), (30, 30, 34, 255)); bg.alpha_composite(img)
        bg = bg.resize((W * S // 2, H * S // 2), Image.LANCZOS); d = ImageDraw.Draw(bg)
        for k, v in lm.items():
            if v is None: continue
            x, y = v[0] * S / 2, v[1] * S / 2
            d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=col, width=2); d.text((x + 6, y - 6), k, fill=col)
        d.text((4, 4), '%s  %s' % (name, lab), fill=(255, 255, 255))
        pane.append(bg)
    pairs.append(pane)

json.dump(res, open(os.path.join(FOLDER, 'actor', 'landmarks.json'), 'w'), indent=1)
json.dump({'classifier': 'rule learned from these five inspected heads: the frontal portrait rig is accepted only when the head is '
                         'frontal or three-quarter AND mean landmark error < 0.12 of the head diagonal AND no anatomy test fails; '
                         'profile, lowered and back-of-head cuts are routed to hand annotation.', 'heads': compat},
          open(os.path.join(FOLDER, 'actor', 'compat.json'), 'w'), indent=1)
wmax = max(p[0].width * 2 + 10 for p in pairs); htot = sum(max(p[0].height, p[1].height) + 10 for p in pairs)
sheet = Image.new('RGB', (wmax, htot), (16, 16, 18)); y = 0
for a, b in pairs:
    sheet.paste(a.convert('RGB'), (0, y)); sheet.paste(b.convert('RGB'), (a.width + 10, y)); y += max(a.height, b.height) + 10
os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
sheet.save(os.path.join(FOLDER, 'proof', 'review_pairs.jpg'), quality=88)
for n, r in res.items():
    print(n, r['verdict'], r['mean_error_over_diag'], r['auto_anatomy_failures'])
