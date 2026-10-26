"""Fig. 2, the person: drawn for this plate (no source), in the same engraved line, except the hand, which is engraved after
a frame of *Door to Heaven* (hand-sam f000, public domain; the card it holds in the source is cropped away and recorded).
Local px = screen px; feet at (0, 0), facing right (+x)."""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from eng import engrave, screen, poly_mask, blur, contour, dilate, erode
from cutout import blit, rot, add, sub
PL = os.path.join(HERE, 'cache', 'plates')
HAND_SRC = os.path.join(HERE, '..', 'sources', 'hand-door-to-heaven')
SS = 2

def ell(cx, cy, rx, ry, n=36, a0=0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(a0, a1, n)]

PARTS = {
 'skirt': {'pivot': (0, -140), 'tone': 0.62, 'angle': 4, 'poly': [(-23, -150), (21, -150), (25, -104), (28, -64), (-28, -64), (-27, -104)]},
 'lower': {'pivot': (0, -70), 'tone': 0.62, 'angle': 4, 'poly': [(-24, -78), (24, -78), (32, -14), (-28, -14)],
           'extra': [[(6, -16), (12, -16), (12, -6), (30, -4), (31, 0), (6, 0)], [(-10, -16), (-4, -16), (-4, -6), (12, -4), (12, 0), (-10, 0)]]},
 'torso': {'pivot': (0, -140), 'tone': 0.66, 'angle': 6, 'poly': [(-15, -264), (9, -264), (18, -248), (21, -218), (15, -182), (22, -128), (-24, -128), (-19, -182), (-23, -222), (-21, -252)]},
 'head':  {'pivot': (0, -262), 'tone': 0.12, 'angle': 80,
           'poly': [(-6, -261), (7, -261), (7, -270)] + ell(3, -287, 15, 19, 30, math.radians(80), math.radians(370)) + [(-6, -270)],
           'hair': ell(-2, -295, 15, 12, 30) + [], 'bun': ell(-15, -291, 8, 8, 24),
           'face': [(14, -296), (19, -288), (22, -283), (18, -281), (17, -275), (14, -272)]},
 'uarm':  {'pivot': (1, -252), 'tone': 0.72, 'angle': 4, 'poly': [(-7, -258), (9, -258), (8, -198), (-5, -198)]},
 'farm':  {'pivot': (1, -200), 'tone': 0.72, 'angle': 4, 'poly': [(-6, -203), (8, -203), (6, -156), (-4, -156)]},
}

def make_plates():
    meta = {}
    for n, P in PARTS.items():
        polys = [P['poly']] + P.get('extra', [])
        if n == 'head': polys += [P['hair'], P['bun']]
        xs = [p[0] for Q in polys for p in Q]; ys = [p[1] for Q in polys for p in Q]
        org = (math.floor(min(xs)) - 4, math.floor(min(ys)) - 4)
        w, h = int((max(xs) - org[0] + 4) * SS), int((max(ys) - org[1] + 4) * SS)
        m = poly_mask((h, w), polys, SS, org)
        tone = np.full((h, w), P['tone'], np.float32)
        if n == 'head':
            hair = poly_mask((h, w), [P['hair'], P['bun']], SS, org)
            face = poly_mask((h, w), [P['poly']], SS, org) * (1 - hair)
            tone = np.where(hair > 0.5, 0.86, 0.10).astype(np.float32)
            # cheek shading toward the back of the head
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            tone = np.where(hair > 0.5, tone, np.clip(0.06 + 0.25 * np.clip((org[0] + xx / SS - 0) / -12, 0, 1), 0, 1))
        else:
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            lx = org[0] + xx / SS
            tone = np.clip(tone + 0.18 * np.clip(-lx / 25, -1, 1), 0, 1)   # light from the right (the porch), shade behind
            if n in ('skirt', 'lower', 'torso'):
                tone = np.clip(tone + 0.16 * np.sin(lx / 6.5 + 0.9) * (0.5 + 0.5 * np.sin(lx / 13.0)), 0, 1)  # folds of the coat
        ink = engrave(tone * m, 90 + P['angle'] if n != 'head' else 90, 2.6 * SS, 0.5, 0.7)
        ink = np.maximum(ink, contour(m, 1.6 * SS))
        if n == 'head':
            im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
            T = lambda p: ((p[0] - org[0]) * SS, (p[1] - org[1]) * SS)
            d.line([T(p) for p in P['face']], fill=255, width=int(1.4 * SS))
            ex, ey = T((11, -290)); d.ellipse([ex - 2.2, ey - 1.6, ex + 2.2, ey + 1.6], fill=255)
            d.line([T((12, -279)), T((17, -279))], fill=255, width=int(1.0 * SS))
            ink = np.maximum(ink, np.asarray(im, np.float32) / 255.)
        save(n, ink * (m > 0), m)
        meta[n] = {'org': org, 'pivot': P['pivot']}
    # the hand, engraved after the scan
    M = json.load(open(os.path.join(HAND_SRC, 'masks_f000.json')))
    src = Image.open(os.path.join(HAND_SRC, 'f000.jpg')).convert('L')
    polys = M['0']
    hs = 0.25           # screen px per scan px: the hand is about 0.19 m long
    xs = [p[0] for Q in polys for p in Q]; ys = [p[1] for Q in polys for p in Q]
    box = (min(xs) - 3, min(ys) - 3, max(xs) + 3, max(ys) + 3)
    sc = hs * SS * 2   # engrave at double size, then shrink
    w, h = int((box[2] - box[0]) * sc), int((box[3] - box[1]) * sc)
    m = poly_mask((h, w), polys, sc, box[:2])
    g = np.asarray(src.crop(box).resize((w, h), Image.BICUBIC), np.float32) / 255.
    v = g[m > 0.5]; lo, hi_ = np.percentile(v, 3), np.percentile(v, 97)
    tone = np.clip(1 - (g - lo) / (hi_ - lo), 0, 1) * 0.75 + 0.08
    ink = np.maximum(engrave(tone * m, 80, 2.4 * SS * 2, 0.8, 0.6), contour(m, 1.4 * SS * 2)) * (m > 0)
    im_i = Image.fromarray((ink * 255).astype(np.uint8)).resize((w // 2, h // 2), Image.LANCZOS)
    im_m = Image.fromarray((m * 255).astype(np.uint8)).resize((w // 2, h // 2), Image.LANCZOS)
    z = Image.new('L', im_i.size, 0)
    Image.merge('RGBA', (im_i, z, z, im_m)).save(os.path.join(PL, 'person_hand.png'))
    # the wrist is the right end of the scan hand (arm entered from the right), fingers to the left
    wrist = (max(xs) - 2, (min(ys) + max(ys)) / 2 - 6)
    meta['hand'] = {'org_scan': box[:2], 'scale': hs, 'wrist_scan': wrist, 'tip_scan': (min(xs), ys[xs.index(min(xs))])}
    json.dump(meta, open(os.path.join(PL, 'person.json'), 'w'), indent=0)

def save(n, ink, cov):
    a = Image.fromarray(np.clip(ink * 255, 0, 255).astype(np.uint8)); c = Image.fromarray(np.clip(cov * 255, 0, 255).astype(np.uint8))
    a = a.resize((a.width // SS, a.height // SS), Image.LANCZOS); c = c.resize((c.width // SS, c.height // SS), Image.LANCZOS)
    z = Image.new('L', a.size, 0)
    Image.merge('RGBA', (a, z, z, c)).save(os.path.join(PL, 'person_%s.png' % n))

_P = {}
def _load():
    if not _P:
        _P['meta'] = json.load(open(os.path.join(PL, 'person.json')))
        for n in list(PARTS) + ['hand']:
            _P[n] = Image.open(os.path.join(PL, 'person_%s.png' % n))
    return _P

def draw(ink, cov, pose, O):
    """pose: lean, thigh, shin, head, uarm, farm (radians; positive = clockwise on screen), pelvis (dx, dy) from O,
    hand_turn (extra rotation of the hand). O = screen point of the feet when standing."""
    P = _load(); M = P['meta']
    pel = add((0, -140), pose.get('pelvis', (0, 0)))
    hip = (0, -140)
    def piece(n, pr, pn, a):
        org = M[n]['org']
        blit(ink, cov, P[n], org, 1.0, pr, pn, a, O)
    # lower (knee down) hangs from the knee at the end of the thigh
    knee = add(pel, rot((0, 70), pose['thigh']))
    piece('lower', (0, -70), knee, pose['shin'])
    piece('skirt', hip, pel, pose['thigh'])
    piece('torso', hip, pel, pose['lean'])
    neck = add(pel, rot(sub((0, -262), hip), pose['lean']))
    piece('head', (0, -262), neck, pose['lean'] + pose['head'])
    sh = add(pel, rot(sub((1, -252), hip), pose['lean']))
    ua = pose['lean'] + pose['uarm']
    piece('uarm', (1, -252), sh, ua)
    el = add(sh, rot((0, 52), ua))
    fa = ua + pose['farm']
    piece('farm', (1, -200), el, fa)
    wr = add(el, rot((0, 46), fa))
    # hand: scan coordinates; the scan hand points left (fingers at -x). Map wrist → wr and fingers along the forearm direction.
    H = M['hand']; s = H['scale']
    v_scan = sub(H['tip_scan'], H['wrist_scan']); a_scan = math.atan2(v_scan[1], v_scan[0])
    a_arm = fa + math.pi / 2       # forearm direction (rest points down = +90 deg)
    # mirror the scan hand (reversed impression) so its thumb side faces the viewer as the arm reaches right
    a = a_arm - (math.pi - a_scan) + pose.get('hand_turn', 0)
    org = H['org_scan']
    # blit with f = -1 mirrors about the local x; express in local units of scan px with g = s
    pr = H['wrist_scan']
    blit(ink, cov, P['hand'], org, 1.0 / s * s * (1 / s) * s, pr, (0, 0), 0, (0, 0), 1, 1) if False else None
    _hand(ink, cov, P['hand'], H, wr, a_arm, O, pose.get('hand_turn', 0))
    return {'hand': (O[0] + wr[0], O[1] + wr[1]), 'head': (O[0] + neck[0], O[1] + neck[1] - 25)}

def _hand(ink, cov, im, H, wr, a_arm, O, turn):
    s = H['scale']
    v = sub(H['tip_scan'], H['wrist_scan']); a_scan = math.atan2(v[1], -v[0])   # angle of wrist→tip after mirroring x
    a = a_arm - a_scan + turn
    # local unit = scan px; plate px per scan px = s (plate was saved at scale s)
    blit(ink, cov, im, H['org_scan'], s, H['wrist_scan'], (0, 0), a, (O[0] + wr[0], O[1] + wr[1]), g=s, f=-1) if False else \
        _blit_mirror(ink, cov, im, H, a, (O[0] + wr[0], O[1] + wr[1]))

def _blit_mirror(ink, cov, im, H, a, Q):
    """mirror the scan in x, then rotate by a about the wrist and place the wrist at Q (screen)."""
    s = H['scale']; org = H['org_scan']; wrs = H['wrist_scan']
    # local coordinates of a scan point p after mirroring about the wrist: m(p) = (-(p.x - wr.x), p.y - wr.y)
    # screen = Q + s * R(a) m(p). Use blit with f=-1 applied before rotation: emulate by flipping the plate image.
    flipped = im.transpose(Image.FLIP_LEFT_RIGHT)
    w = im.width
    # flipped pixel u' = w - u ; local point p' = (-(org.x + u / s), org.y + v / s) → origin of flipped plate in mirrored coords:
    org_m = (-(org[0] + w / s), org[1])
    blit(ink, cov, flipped, org_m, s, (-wrs[0], wrs[1]), (0, 0), a, Q, g=s, f=1)

POSES = {
 'stand': dict(lean=0.0, thigh=0.0, shin=0.0, head=0.0, uarm=0.05, farm=-0.05),
 'call':  dict(lean=0.10, thigh=0.0, shin=0.0, head=-0.10, uarm=-0.55, farm=-1.25),   # beckoning, forearm raised
 'reach': dict(lean=0.42, thigh=-0.10, shin=0.10, head=-0.05, uarm=-1.30, farm=-0.15),  # bending forward, arm out
 'sit':   dict(lean=0.06, thigh=-1.52, shin=0.04, head=0.18, uarm=-0.35, farm=-0.35, pelvis=(0, 56)),
 'low':   dict(lean=0.30, thigh=-1.52, shin=0.04, head=0.28, uarm=-0.75, farm=-0.55, pelvis=(0, 56)),  # hand offered low, toward the porch
}

if __name__ == '__main__':
    make_plates(); print('person ok')
