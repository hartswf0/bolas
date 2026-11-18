"""SCION 29 GrabCut cuts of the props: bell (yoke, body, clapper), key, bench, goods-shed door leaf.

python3 -I cut_props.py    (sources decoded by OpenCV only; untrusted data)
Each prop: one grabCut over a scissor envelope with fg/bg scribbles, then split into rig pieces by polygons.
Outputs to sources/la-belle-hortense/forage/cut/<prop>/: piece PNGs (RGBA, trimmed), failure_mask.png,
grabcut_mask.png, qa.png, manifest.json (crop box, offsets, pivots in crop + piece coords, grabcut report).
"""
import os, sys, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gcut import grabcut_piece, rgba, trim

ROOT = '/home/user/bolas/paeleo/scion/oulipo/films'
RAW = ROOT + '/sources/la-belle-hortense/forage/raw/'
CUT = ROOT + '/sources/la-belle-hortense/forage/cut/'


def poly(h, w, p, blur=True):
    m = np.zeros((h, w), np.float32)
    cv2.fillPoly(m, [np.array(p, np.int32)], 1.0)
    return cv2.GaussianBlur(m, (3, 3), 0) if blur else m


def run(name, src, box, env, fg, bg, splits, pivots, dense_thr=None, keep_holes=False, invert_dense=False, colour=True, iters=6, min_part=None):
    out = CUT + name; os.makedirs(out, exist_ok=True)
    im = cv2.imread(RAW + src)
    x0, y0, x1, y1 = box
    crop = im[y0:y1, x0:x1].copy()
    h, w = crop.shape[:2]
    alpha, rep, over = grabcut_piece(crop, env, fg, bg, dense_thr=dense_thr, keep_holes=keep_holes,
                                     invert_dense=invert_dense, iters=iters, min_part=min_part)
    cv2.imwrite(out + '/failure_mask.png', over)
    cv2.imwrite(out + '/grabcut_mask.png', (alpha * 255).astype(np.uint8))
    man = {}
    qa = np.full((h, w * 2 + 10, 3), 90, np.uint8); qa[:, :w] = over
    chk = ((np.indices((h, w)).sum(0) // 12) % 2 * 60 + 100).astype(np.uint8)
    qa[:, w + 10:] = chk[..., None]
    for pname, p in splits.items():
        a = alpha * (poly(h, w, p) if p is not None else 1.0)
        if name == 'visitor' and pname == 'body':
            a = a * (1 - poly(h, w, splits['forearm']))
        arr = rgba(crop if colour else cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255., a)
        t, (ox, oy) = trim(arr)
        cv2.imwrite(f'{out}/{pname}.png', cv2.cvtColor(t, cv2.COLOR_RGBA2BGRA))
        piv = pivots.get(pname, {})
        man[pname] = {'png': f'cut/{name}/{pname}.png', 'offset_in_crop': [ox, oy], 'size': [t.shape[1], t.shape[0]],
                      'pivots_crop': piv, 'pivots_piece': {k: [v[0] - ox, v[1] - oy] for k, v in piv.items()}}
        sub = qa[:, w + 10:]
        sub[:] = (sub * (1 - a[..., None]) + crop * a[..., None]).astype(np.uint8)
    for pname, piv in pivots.items():
        for v in piv.values():
            cv2.circle(qa, (w + 10 + v[0], v[1]), 5, (0, 0, 255), -1)
    cv2.imwrite(out + '/qa.png', qa)
    json.dump({'source_file': 'forage/raw/' + src, 'crop_box': list(box), 'grabcut': rep, 'pieces': man},
              open(out + '/manifest.json', 'w'), indent=1)
    print(name, json.dumps(rep))
    return man


# --- bell: Commons "Bahnhofsglocke HLB 1.jpg" (PD), 960x1280 thumbnail; crop (250,20)-(660,520)
B = (250, 20, 660, 520)
bell_env = [(40, 60), (190, 25), (300, 40), (380, 50), (380, 112), (330, 120), (370, 360), (362, 410), (262, 420),
            (238, 485), (210, 485), (186, 420), (70, 410), (66, 360), (130, 122), (40, 112)]
bell_fg = [('ellipse', (230, 270), (90, 90)), ('ellipse', (235, 95), (40, 18)), ('rect', (80, 70, 360, 92)),
           ('ellipse', (222, 445), (12, 25))]
bell_bg = [('rect', (0, 130, 60, 500)), ('rect', (380, 130, 409, 500)), ('rect', (0, 0, 409, 15)),
           ('rect', (0, 470, 180, 499)), ('rect', (270, 450, 409, 499))]
run('bell', 'commons_Bahnhofsglocke_HLB_1_960px.jpg', B, bell_env, bell_fg, bell_bg,
    {'yoke': [(30, 50), (390, 50), (390, 118), (300, 118), (290, 128), (150, 128), (140, 118), (30, 118)],
     'body': [(130, 112), (330, 112), (380, 360), (372, 412), (60, 412), (60, 360)],
     'clapper': [(186, 400), (262, 400), (262, 490), (186, 490)]},
    {'yoke': {'pivot_axle': [235, 92]}, 'body': {'pivot_axle': [235, 92], 'pivot_clapper': [225, 130]},
     'clapper': {'pivot_clapper': [225, 130], 'clapper_tip': [222, 478]}})

# --- key: Commons Skeletonkey.png (CC0), 960x720, left key; crop (150,40)-(400,660); dark on pale; bow hole kept
run('key', 'skeletonkey.png', (150, 40, 400, 660),
    [(5, 5), (245, 5), (245, 615), (5, 615)],
    [('rect', (100, 60, 150, 380))], [('rect', (0, 0, 40, 300)), ('rect', (210, 0, 249, 300))],
    {'key': None}, {'key': {'pivot_bow_hole': [128, 512], 'tip': [128, 30], 'centre': [130, 320]}},
    dense_thr=0.55, keep_holes=True)

# --- bench: Highsmith, Sacramento park bench (PD), 2400x1601; crop (715,995)-(990,1240); gaps kept
run('bench', 'highsmith_bench_sac_23429.jpg', (715, 995, 990, 1240),
    [(10, 10), (130, 4), (240, 36), (272, 96), (272, 175), (230, 236), (40, 236), (5, 160)],
    [('rect', (40, 30, 110, 90)), ('rect', (110, 100, 250, 115)),
     ('line', [(137, 63), (150, 68), (210, 65), (225, 70), (232, 83), (228, 95)], 5),       # armrest
     ('line', [(247, 105), (233, 120), (235, 143), (238, 173), (247, 190)], 6),             # right front leg
     ('line', [(167, 136), (165, 166), (167, 190), (177, 220), (183, 225)], 7),             # middle leg
     ('line', [(160, 156), (200, 156), (227, 166), (237, 176)], 5),                         # strut
     ('line', [(100, 183), (133, 186), (153, 200), (167, 220)], 6)],                        # rear lower curve,
    [('rect', (200, 0, 274, 30)), ('rect', (0, 236, 274, 244))],
    {'bench': None}, {'bench': {'seat_left': [40, 120], 'seat_right': [240, 125], 'ground_contact': [130, 225]}},
    keep_holes=True, dense_thr='lowsat:0.22:140', iters=8, min_part=150)

# --- door leaf: Bourré goods shed 50866795131 (Daniel Jolivet, CC BY 2.0), 1280x960; crop (436,452)-(566,628)
# the leaf is a plain rectangle of boards: box seed with an inset fg rectangle; hinge on the left jamb
run('door', 'bourre_50866795131.jpg', (436, 452, 566, 628),
    [(4, 6), (126, 6), (126, 172), (4, 172)],
    [('rect', (16, 20, 114, 160))], [('rect', (0, 0, 129, 3)), ('rect', (0, 0, 3, 175)), ('rect', (127, 0, 129, 175))],
    {'leaf': None}, {'leaf': {'hinge_top': [7, 10], 'hinge_bottom': [7, 168], 'keyhole': [108, 100]}})

# --- visitor: LoC 2017750547 (Jack Delano 1941, FSA/OWI, PD), 8a36813v.jpg 1024x710; crop (560,160)-(800,600)
# woman walking away, legs visible below the dress hem; dog and leash excluded (bg seeds); split into
# body (hat + dress), forearm (left, hanging), shinL / shinR hinged at the hem (the dress hides the thighs)
run('visitor', 'loc_8a36813v.jpg', (560, 160, 800, 600),
    [(70, 28), (140, 28), (142, 60), (166, 80), (170, 165), (160, 178), (152, 240), (150, 300), (134, 314),
     (132, 392), (104, 392), (86, 352), (72, 302), (54, 245), (50, 180), (54, 100), (70, 70)],
    [('ellipse', (110, 190), (34, 90)), ('ellipse', (105, 46), (28, 9)), ('line', [(98, 310), (100, 345)], 6),
     ('line', [(120, 312), (118, 370)], 6), ('ellipse', (102, 345), (8, 6)), ('ellipse', (118, 375), (8, 8)),
     ('line', [(62, 190), (64, 232)], 6)],
    [('rect', (150, 238, 200, 336)), ('rect', (0, 0, 60, 60)), ('rect', (150, 0, 239, 60)),
     ('rect', (0, 395, 239, 439)), ('rect', (136, 330, 239, 395)), ('rect', (60, 330, 84, 395))],
    {'body': [(40, 20), (175, 20), (175, 312), (40, 312)],
     'forearm': [(48, 186), (82, 186), (82, 245), (48, 245)],
     'shinL': [(80, 300), (110, 300), (110, 395), (80, 395)],
     'shinR': [(110, 300), (140, 300), (140, 395), (110, 395)]},
    {'body': {'pivot_hipL': [100, 300], 'pivot_hipR': [119, 302], 'pivot_elbowL': [64, 188], 'pivot_neck': [108, 70]},
     'forearm': {'pivot_elbowL': [64, 188], 'hand': [65, 235]},
     'shinL': {'pivot_kneeL': [100, 304], 'heelL': [102, 350]},
     'shinR': {'pivot_kneeR': [119, 306], 'heelR': [118, 382]}},
    colour=False)
