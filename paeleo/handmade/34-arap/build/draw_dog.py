"""The dog, engraved. Drawn here (no found pixels): a shepherd-type dog whose proportions follow the archive dog's
rig keys (kit/archive-dog/pose_agent_v8.json, profile frames 0-12: body ~1.7x its chest height, neck ~0.3 body).

Drawings (mm, y up, ground y = 0, body centre x = 0, facing LEFT = toward the door):
  P_body  profile: torso, neck, four legs, tail          (one mesh)
  P_head  profile head with ears, eye, nose, collar tag   (one mesh, rides the neck)
  F_body  front three-quarter view, head turned toward the left (substitution key for the turn back)
  B_body  rear three-quarter view, head away (substitution key for the turn away)
Each drawing writes: <name>.png (RGBA texture, 1 px = 1 mm), <name>.json (origin, part layers, named points, features).
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DRAW
from engrave import Drawing, catmull, to_pil, INK, PAPER


def save(name, d, rgba, label, layers, extra=None):
    to_pil(rgba).save(os.path.join(DRAW, name + '.png'))
    Image.fromarray((label + 1).astype(np.uint8)).save(os.path.join(DRAW, name + '_label.png'))
    meta = dict(name=name, w=d.w, h=d.h, ox=d.ox, oy=d.oy, parts=[dict(name=p['name'], layer=p['layer']) for p in d.parts],
                points={k: list(map(float, v)) for k, v in d.points.items()},
                features=[dict(name=n, c=list(map(float, c)), r=float(r)) for n, c, r in d.features])
    if extra:
        meta.update(extra)
    json.dump(meta, open(os.path.join(DRAW, name + '.json'), 'w'), indent=1)


def dot(d, rgb, alpha, c, r, col, rim=None):
    m = d.ellipse_mask(c, r, r)
    rgb[m] = col
    alpha[m] = 1


# ------------------------------------------------------------------ profile body
def leg_chain(top, knee, ankle, paw, toe):
    return [top, knee, ankle, paw, toe]


def P_body():
    d = Drawing(1240, 900, 640, 860)
    torso = catmull([(-300, 300), (-350, 400), (-345, 500), (-300, 575), (-215, 605), (-100, 580), (30, 565), (160, 575),
                     (270, 552), (330, 490), (335, 420), (300, 360), (235, 335), (120, 345), (0, 330), (-140, 300),
                     (-235, 285)], 10)
    neck = catmull([(-300, 560), (-250, 610), (-300, 680), (-350, 735), (-405, 745), (-440, 690), (-425, 600),
                    (-380, 500), (-345, 430)], 10)
    tail_chain = [(305, 515), (370, 500), (425, 450), (460, 380), (468, 300), (455, 235)]
    tail_r = [44, 46, 44, 38, 30, 18]
    # legs: shoulder/hip, elbow/stifle, wrist/hock, paw heel, toe
    FN = [(-255, 420), (-262, 275), (-262, 95), (-262, 30), (-318, 20)]
    FF = [(-150, 400), (-150, 265), (-148, 95), (-148, 30), (-202, 20)]
    HN = [(215, 440), (182, 255), (268, 125), (258, 30), (205, 20)]
    HF = [(95, 430), (60, 255), (140, 125), (130, 30), (78, 20)]
    FR = [64, 50, 34, 30, 24]
    HR = [74, 56, 35, 30, 24]
    d.add('far_hind', d.capsules_mask(HF, HR), 0, ('axis', HF, HR), tone=0.22, spacing=12)
    d.add('far_fore', d.capsules_mask(FF, FR), 0, ('axis', FF, FR), tone=0.22, spacing=12)
    d.add('tail', d.capsules_mask(tail_chain, tail_r), 1, ('axis', tail_chain, tail_r), tone=0.12, spacing=12)
    d.add('torso', d.poly_mask(torso), 2, ('dir', -0.04), tone=0.0, spacing=14)
    d.add('neck', d.poly_mask(neck), 2, ('dir', 1.05), tone=-0.04, spacing=13)
    d.add('near_hind', d.capsules_mask(HN, HR), 3, ('axis', HN, HR), tone=0.0, spacing=12)
    d.add('near_fore', d.capsules_mask(FN, FR), 3, ('axis', FN, FR), tone=-0.05, spacing=12)
    d.add('near_thigh', d.poly_mask(catmull([(150, 470), (250, 500), (300, 440), (275, 330), (225, 240), (170, 235),
                                              (150, 300), (135, 400)], 8)), 3, ('axis', HN, [150, 110, 60, 40, 30]), tone=0.0, spacing=12)
    d.add('near_shoulder', d.poly_mask(catmull([(-300, 520), (-215, 545), (-205, 450), (-225, 330), (-270, 300),
                                                 (-305, 360), (-315, 450)], 8)), 3, ('axis', FN, [110, 80, 40, 30, 30]), tone=-0.05, spacing=12)
    # saddle: a darker cape over the back (shepherd marking): drawn as a tone change inside the torso
    saddle = d.poly_mask(catmull([(-220, 600), (-100, 590), (60, 570), (200, 575), (300, 530), (250, 470), (100, 470),
                                  (-60, 480), (-200, 520)], 8))
    d.parts[3]['mask_saddle'] = saddle
    pts = dict(withers=(-215, 590), hip=(215, 470), croup=(250, 540), chest=(-300, 330), belly=(0, 335),
               neck_top=(-395, 715), neck_base=(-300, 560), throat=(-430, 640),
               tail_root=(305, 515), tail_mid=(460, 380), tail_tip=(455, 240))
    for nm, ch in (('FN', FN), ('FF', FF), ('HN', HN), ('HF', HF)):
        pts[nm + '_top'], pts[nm + '_knee'], pts[nm + '_ankle'], pts[nm + '_heel'], pts[nm + '_toe'] = ch
    d.points = {k: np.array(v, float) for k, v in pts.items()}

    def saddle_mark(dd, rgb, alpha):
        # re-ink the saddle with tighter cross lines
        m = saddle & dd.parts[3]['mask']
        X, Y = dd.X, dd.Y
        phi = X * 0.35 + Y * 0.94
        s = 9.0
        dl = np.abs((phi / s) % 1 - 0.5) * s
        ink = 1 - np.clip((s / 2 - dl) - 1.6, 0, 1)
        cur = rgb[m]
        rgb[m] = cur * (1 - ink[m][:, None] * 0.75) + INK * ink[m][:, None] * 0.75
    rgba, label, layers = d.render(marks=[saddle_mark])
    save('P_body', d, rgba, label, layers)
    return d


# ------------------------------------------------------------------ profile head (rides the neck)
def P_head():
    d = Drawing(420, 360, 260, 300)   # origin at the head joint (atlas): x,y relative to it
    skull = catmull([(-30, -40), (40, -10), (55, 40), (20, 85), (-40, 95), (-100, 80), (-150, 62), (-195, 48), (-215, 30),
                     (-212, 8), (-190, -6), (-140, -18), (-80, -40)], 10)
    ear_far = [(-35, 70), (-5, 165), (20, 66)]
    ear_near = [(-10, 66), (40, 170), (52, 52)]
    d.add('ear_far', d.poly_mask(catmull(ear_far, 6)), 0, ('dir', 1.3), tone=0.3, spacing=10)
    d.add('skull', d.poly_mask(skull), 1, ('dir', -0.15), tone=-0.02, spacing=11)
    d.add('ear_near', d.poly_mask(catmull(ear_near, 6)), 2, ('dir', 1.2), tone=0.12, spacing=10)
    d.points = {k: np.array(v, float) for k, v in dict(
        joint=(0, 0), occiput=(30, 60), nose=(-212, 22), eye=(-95, 50), ear_near_tip=(40, 165), ear_far_tip=(-5, 160),
        ear_near_base=(20, 60), jaw=(-120, -15), brow=(-60, 80)).items()}
    d.features = [('eye', (-95, 50), 22), ('nose', (-205, 22), 22)]

    def face(dd, rgb, alpha):
        def fill(mask, col):
            rgb[mask] = col
        # eye: dark almond, light catch
        fill(dd.ellipse_mask((-95, 50), 15, 10, 0.25), INK)
        fill(dd.ellipse_mask((-98, 53), 4, 3), PAPER)
        # nose
        fill(dd.ellipse_mask((-206, 24), 17, 13, -0.2), INK)
        fill(dd.ellipse_mask((-210, 30), 4, 3), PAPER * 0.8)
        # mouth line
        X, Y = dd.X, dd.Y
        t = np.clip((X + 205) / 140, 0, 1)
        yline = 0 - 8 * np.sin(t * np.pi) + 2
        m = (X > -205) & (X < -70) & (np.abs(Y - yline) < 2.4)
        fill(m, INK)
        # dark muzzle mask (shepherd): extra ink density at the muzzle
        mm = dd.ellipse_mask((-170, 22), 55, 32, -0.1) & dd.parts[1]['mask']
        rgb[mm] = rgb[mm] * 0.55 + INK * 0.45
    rgba, label, layers = d.render(marks=[face])
    save('P_head', d, rgba, label, layers)
    return d


if __name__ == '__main__' and len(sys.argv) == 1:
    P_body(); P_head()
    # preview: compose head on body at the neck top
    b = Image.open(os.path.join(DRAW, 'P_body.png')); h = Image.open(os.path.join(DRAW, 'P_head.png'))
    bj = json.load(open(os.path.join(DRAW, 'P_body.json'))); hj = json.load(open(os.path.join(DRAW, 'P_head.json')))
    can = Image.new('RGBA', (b.size[0] + 200, b.size[1] + 100), (60, 70, 90, 255))
    can.alpha_composite(b, (200, 100))
    nt = bj['points']['neck_top']
    px = 200 + bj['ox'] + nt[0] - hj['ox']; py = 100 + bj['oy'] - nt[1] - hj['oy']
    can.alpha_composite(h, (int(px), int(py)))
    can.convert('RGB').save(os.path.join(os.path.dirname(DRAW), '..', 'build', 'cache', 'preview_P.jpg'))


# ------------------------------------------------------------------ rear view (the turned back)
def R0_body():
    d = Drawing(720, 760, 360, 720)
    # far forelegs, seen between the hind legs
    for sx in (-1, 1):
        ch = [(sx * 55, 330), (sx * 52, 170), (sx * 50, 30)]
        d.add('fore_' + ('l' if sx < 0 else 'r'), d.capsules_mask(ch, [30, 22, 20]), 0, ('axis', ch, [30, 22, 20]), tone=0.35, spacing=12)
    # the back receding to the shoulders (behind the haunches)
    back = catmull([(-125, 470), (-130, 545), (-95, 600), (0, 615), (95, 600), (130, 545), (125, 470)], 10)
    d.add('back', d.poly_mask(back), 1, ('dir', 0.0), tone=0.12, spacing=13)
    belly = catmull([(-110, 470), (-95, 330), (0, 300), (95, 330), (110, 470)], 8)
    d.add('belly', d.poly_mask(belly), 1, ('dir', 1.57), tone=0.3, spacing=13)
    for sx in (-1, 1):
        nm = 'l' if sx < 0 else 'r'
        haunch = catmull([(sx * 10, 560), (sx * 95, 545), (sx * 150, 470), (sx * 145, 360), (sx * 110, 280),
                          (sx * 60, 300), (sx * 20, 380)], 10)
        d.add('haunch_' + nm, d.poly_mask(haunch), 2, ('dir', 1.57 - sx * 0.45), tone=0.0, spacing=13)
        ch = [(sx * 100, 330), (sx * 95, 220), (sx * 88, 125), (sx * 86, 30)]
        rr = [52, 42, 30, 27]
        d.add('hind_' + nm, d.capsules_mask(ch, rr), 2, ('axis', ch, rr), tone=0.05, spacing=12)
    tail = [(0, 545), (0, 470), (-4, 390), (-8, 300)]
    tr = [36, 46, 44, 26]
    d.add('tail', d.capsules_mask(tail, tr), 3, ('axis', tail, tr), tone=0.2, spacing=11)
    d.points = {k: np.array(v, float) for k, v in dict(
        withers=(0, 600), hip=(0, 470), tail_root=(0, 545), tail_mid=(-4, 390), tail_tip=(-8, 300),
        neck_top=(0, 615), pl=(-86, 25), pr=(86, 25), fl=(-50, 25), fr=(50, 25)).items()}
    rgba, label, layers = d.render()
    save('R0_body', d, rgba, label, layers)


def R0_head():
    # the back of the head and the backs of the ears; the joint at (0, 0)
    d = Drawing(320, 300, 160, 230)
    d.add('ear_l', d.poly_mask(catmull([(-70, 50), (-62, 165), (-20, 70)], 6)), 0, ('dir', 1.45), tone=0.25, spacing=10)
    d.add('ear_r', d.poly_mask(catmull([(70, 50), (62, 165), (20, 70)], 6)), 0, ('dir', 1.7), tone=0.25, spacing=10)
    d.add('skull', d.poly_mask(catmull([(-80, 0), (-78, 55), (-40, 95), (40, 95), (78, 55), (80, 0), (0, -30)], 10)), 1,
          ('dir', 0.15), tone=0.1, spacing=11)
    d.points = {k: np.array(v, float) for k, v in dict(joint=(0, 0), ear_l_tip=(-62, 160), ear_r_tip=(62, 160)).items()}
    rgba, label, layers = d.render()
    save('R0_head', d, rgba, label, layers)


# ------------------------------------------------------------------ front three-quarter view (the turn back)
def F0_body():
    d = Drawing(720, 780, 360, 740)
    for sx in (-1, 1):   # hind legs, far behind, outside the forelegs
        ch = [(sx * 120, 300), (sx * 125, 150), (sx * 118, 30)]
        d.add('hind_' + ('l' if sx < 0 else 'r'), d.capsules_mask(ch, [40, 26, 22]), 0, ('axis', ch, [40, 26, 22]), tone=0.4, spacing=12)
    barrel = catmull([(-150, 330), (-160, 470), (-120, 560), (0, 585), (120, 560), (160, 470), (150, 330), (0, 290)], 10)
    d.add('barrel', d.poly_mask(barrel), 1, ('dir', 1.57), tone=0.25, spacing=13)
    chest = catmull([(-125, 330), (-140, 470), (-110, 590), (-60, 640), (60, 640), (110, 590), (140, 470), (125, 330),
                     (60, 280), (0, 265), (-60, 280)], 10)
    d.add('chest', d.poly_mask(chest), 2, ('dir', 1.57), tone=-0.05, spacing=13)
    for sx in (-1, 1):
        nm = 'l' if sx < 0 else 'r'
        ch = [(sx * 82, 380), (sx * 78, 250), (sx * 74, 100), (sx * 74, 35)]
        rr = [46, 36, 28, 26]
        d.add('fore_' + nm, d.capsules_mask(ch, rr), 3, ('axis', ch, rr), tone=0.0, spacing=12)
        d.add('paw_' + nm, d.ellipse_mask((sx * 76, 24), 36, 22), 3, ('dir', 0.0), tone=0.05, spacing=10)
    d.points = {k: np.array(v, float) for k, v in dict(
        neck_top=(0, 640), chest=(0, 420), pl=(-76, 25), pr=(76, 25), hl=(-118, 25), hr=(118, 25)).items()}
    rgba, label, layers = d.render()
    save('F0_body', d, rgba, label, layers)


def F0_head():
    # a head seen from the front, turned a quarter toward the LEFT (the door when the dog faces the camera)
    d = Drawing(380, 360, 200, 230)
    d.add('ear_r', d.poly_mask(catmull([(25, 70), (78, 175), (88, 55)], 6)), 0, ('dir', 1.7), tone=0.3, spacing=10)
    skull = catmull([(-70, 0), (-75, 50), (-45, 95), (20, 105), (70, 75), (80, 20), (55, -40), (0, -55), (-45, -40)], 10)
    d.add('skull', d.poly_mask(skull), 1, ('dir', 0.25), tone=0.0, spacing=11)
    d.add('ear_l', d.poly_mask(catmull([(-62, 60), (-82, 170), (-18, 85)], 6)), 2, ('dir', 1.4), tone=0.15, spacing=10)
    muzzle = catmull([(-30, 10), (-95, 0), (-130, -20), (-125, -48), (-80, -62), (-20, -50), (0, -15)], 8)
    d.add('muzzle', d.poly_mask(muzzle), 3, ('dir', 0.1), tone=0.05, spacing=10)
    d.points = {k: np.array(v, float) for k, v in dict(joint=(0, -20), nose=(-122, -30), ear_l_tip=(-80, 165),
                                                        ear_r_tip=(78, 168)).items()}
    d.features = [('eye_l', (-62, 32), 16), ('eye_r', (18, 40), 16), ('nose', (-118, -28), 20)]

    def face(dd, rgb, alpha):
        for c, rx, ry in (((-62, 32), 13, 9), ((18, 40), 11, 8)):
            rgb[dd.ellipse_mask(c, rx, ry, 0.15)] = INK
            rgb[dd.ellipse_mask((c[0] - 3, c[1] + 3), 3.5, 3)] = PAPER
        rgb[dd.ellipse_mask((-120, -28), 20, 14, -0.15)] = INK
        rgb[dd.ellipse_mask((-124, -22), 5, 3)] = PAPER * 0.8
        m = dd.ellipse_mask((-80, -30), 55, 30, -0.1) & dd.parts[3]['mask']
        rgb[m] = rgb[m] * 0.55 + INK * 0.45
        X, Y = dd.X, dd.Y
        mm = (X > -118) & (X < -40) & (np.abs(Y - (-50 + 0.12 * (X + 118))) < 2.2)
        rgb[mm] = INK
    rgba, label, layers = d.render(marks=[face])
    save('F0_head', d, rgba, label, layers)


def preview_views():
    out = Image.new('RGBA', (1500, 700), (60, 70, 90, 255))
    x = 10
    for b, hname, hoff in (('R0_body', 'R0_head', (0, 600)), ('F0_body', 'F0_head', (-10, 660))):
        bi = Image.open(os.path.join(DRAW, b + '.png')); bj = json.load(open(os.path.join(DRAW, b + '.json')))
        hi = Image.open(os.path.join(DRAW, hname + '.png')); hj = json.load(open(os.path.join(DRAW, hname + '.json')))
        bi = bi.resize((bi.size[0] * 2 // 3, bi.size[1] * 2 // 3)); hi = hi.resize((hi.size[0] * 2 // 3, hi.size[1] * 2 // 3))
        jx = (bj['ox'] + hoff[0] - hj['ox']) * 2 / 3; jy = (bj['oy'] - hoff[1] - hj['oy']) * 2 / 3
        if b.startswith('R0'):
            out.alpha_composite(hi, (int(x + jx), int(150 + jy))); out.alpha_composite(bi, (x, 150))
        else:
            out.alpha_composite(bi, (x, 150)); out.alpha_composite(hi, (int(x + jx), int(150 + jy)))
        x += 520
    out.convert('RGB').save(os.path.join(os.path.dirname(DRAW), '..', 'build', 'cache', 'preview_views.jpg'))


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'views':
    R0_body(); R0_head(); F0_body(); F0_head(); preview_views()
