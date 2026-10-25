"""The person: a flat cutout in profile (facing the dog, screen right), jointed at neck, shoulder, elbow, wrist, hip,
knee and ankle, in the manner of a multiplane cutout puppet. Painted dark: seen against the door's light it is a
silhouette with a warm edge. Every pose is a set of joint angles keyed to the score's circumstances (call, reach,
step aside, sit, hand low, soft voice)."""
import math
import numpy as np
from PIL import Image, ImageDraw
from common import *

SS = 3


def pose(t):
    i = min(N - 1, int(round(t * FPS)))
    pr = FR[i]['person']
    # position: in the doorway (on the sill line, z 5.02), then a sidestep out to sit beside the door (z 4.70)
    X = pr['x']
    step = smooth(5.35, 6.05, t)
    Zp = lerp(5.02, 4.70, step)
    sit = pr['sit']
    reach = pr['reach']
    low = pr['low']
    calling = 1.0 if pr['voice'] == 'call' else 0.0
    soft = 1.0 if pr['voice'] == 'soft' else 0.0
    # torso lean (deg from vertical, + = forward towards the dog)
    lean = 4 + 9 * keyed([(0.9, 0), (1.1, 1), (2.2, 1), (2.45, 0), (3.35, 0), (3.55, 1), (4.5, 1), (4.8, 0)], t) + 16 * reach
    lean = lean * (1 - sit) + (8 + 10 * low) * sit
    head_tilt = 6 * calling * (1 + 0.5 * math.sin(t * 9)) - 14 * soft * (1 - sit * 0.3) - 6 * low
    # the near arm: shoulder angle from straight down (+ = forward), elbow bend
    beckon = keyed([(0.95, 0), (1.15, 1), (2.1, 1), (2.35, 0)], t)
    sh = 18 + 60 * beckon + 92 * reach
    el = 30 + 70 * beckon * (0.6 + 0.4 * math.sin(t * 11)) - 25 * reach
    wr = -10 + 40 * beckon
    # hand low: arm forward and down to the boards, palm up
    sh = sh * (1 - low) + 62 * low
    el = el * (1 - low) + 8 * low
    wr = wr * (1 - low) + (-28) * low
    # sit (on the boards, back near the wall, knees up) vs stand
    walk = math.sin((t - 5.35) / 0.7 * 2 * math.pi) * (step * (1 - step) * 4)
    hip_y = lerp(0.93, 0.13, sit)
    thigh = lerp(-4 + 22 * walk, 132, sit)   # thigh angle from straight down (+ = forward)
    knee = lerp(4 + 10 * abs(walk), 116, sit)  # knee bend
    thigh2 = lerp(-4 - 22 * walk, 122, sit)
    knee2 = lerp(4 + 10 * abs(walk), 100, sit)
    hipX = X + 0.10 * sit
    return dict(X=hipX, Y=hip_y, Z=Zp, lean=lean, head=head_tilt, sh=sh, el=el, wr=wr, th1=thigh, kn1=knee,
                th2=thigh2, kn2=knee2, low=low, reach=reach, sit=sit)


def chain(base, angs, lens):
    """2D chain in the person's plane: angles in degrees from straight down, + = towards the dog (+X)."""
    pts = [np.array(base)]
    a = 0.0
    for ang, L in zip(angs, lens):
        a += ang
        r = math.radians(a)
        pts.append(pts[-1] + L * np.array([math.sin(r), -math.cos(r)]))
    return pts, a


def build(q):
    """pieces in world (X, Y) on the person's glass at depth q['Z']: [(layer, polygon or capsule, tone)]"""
    hip = np.array([q['X'], q['Y']])
    L = math.radians(q['lean'])
    up = np.array([math.sin(L), math.cos(L)])
    sho = hip + up * 0.54
    neck = hip + up * 0.60
    pieces = []
    # far leg, far arm (darker, behind)
    for k, (th, kn) in enumerate([(q['th2'], q['kn2']), (q['th1'], q['kn1'])]):
        pts, a = chain(hip, [th, -kn], [0.46, 0.45])
        tone = 0.65 if k == 0 else 1.0
        pieces.append((k * 2, ('cap', pts[0], pts[1], 0.085, 0.065), tone, 'coat'))
        pieces.append((k * 2, ('cap', pts[1], pts[2], 0.06, 0.045), tone, 'coat'))
        # the foot: flat on the boards
        f0 = pts[2]
        pieces.append((k * 2, ('poly', [f0 + (-0.04, -0.04), f0 + (0.2, -0.05), f0 + (0.21, 0.0), f0 + (0.03, 0.04)]), tone * 0.8, 'coat'))
    far_arm, _ = chain(sho - up * 0.02, [q['sh'] * 0.4 - 6, 20], [0.3, 0.27])
    pieces.append((1, ('cap', far_arm[0], far_arm[1], 0.055, 0.045), 0.6, 'coat'))
    pieces.append((1, ('cap', far_arm[1], far_arm[2], 0.045, 0.035), 0.6, 'coat'))
    # torso: a coat, wider at the hem
    nrm = np.array([up[1], -up[0]])
    torso = [hip - nrm * 0.17 - up * 0.05, hip + nrm * 0.15 - up * 0.05, sho + nrm * 0.12, sho + nrm * 0.02 + up * 0.05,
             sho - nrm * 0.10 + up * 0.04, sho - nrm * 0.15]
    pieces.append((3, ('poly', torso), 1.0, 'coat'))
    # head
    hr = math.radians(q['lean'] * 0.4 + q['head'])
    hup = np.array([math.sin(hr), math.cos(hr)])
    hc = neck + hup * 0.15 + np.array([0.02, 0])
    pieces.append((3, ('cap', neck - up * 0.02, neck + hup * 0.07, 0.05, 0.045), 0.9, 'skin'))
    pieces.append((3, ('ell', hc, 0.105, 0.125, hr), 0.95, 'skin'))
    hn = np.array([hup[1], -hup[0]])
    pieces.append((3, ('poly', [hc + hn * 0.09 + hup * 0.0, hc + hn * 0.135 - hup * 0.02, hc + hn * 0.09 - hup * 0.05]), 0.95, 'skin'))  # nose
    pieces.append((3, ('ell', hc - hn * 0.03 + hup * 0.05, 0.11, 0.10, hr), 0.55, 'coat'))  # hair
    pieces.append((3, ('ell', hc - hn * 0.085 - hup * 0.03, 0.05, 0.08, hr), 0.55, 'coat'))  # hair at the nape
    # near arm and hand
    arm, a = chain(sho, [q['sh'] + q['lean'] * 0.5, -q['el']], [0.30, 0.27])
    pieces.append((4, ('cap', arm[0], arm[1], 0.058, 0.046), 1.05, 'coat'))
    pieces.append((4, ('cap', arm[1], arm[2], 0.046, 0.034), 1.05, 'coat'))
    w = arm[2]
    ra = math.radians(a + q['wr'])
    hd = np.array([math.sin(ra), -math.cos(ra)])
    hn2 = np.array([hd[1], -hd[0]])
    hand = [w - hn2 * 0.03, w + hd * 0.09 - hn2 * 0.035, w + hd * 0.15 - hn2 * 0.012, w + hd * 0.15 + hn2 * 0.01,
            w + hd * 0.08 + hn2 * 0.035, w + hn2 * 0.03]
    pieces.append((5, ('poly', hand), 1.0, 'skin'))
    thumb = [w + hd * 0.03 + hn2 * 0.02, w + hd * 0.08 + hn2 * 0.065, w + hd * 0.1 + hn2 * 0.05, w + hd * 0.05 + hn2 * 0.015]
    pieces.append((5, ('poly', thumb), 1.0, 'skin'))
    return pieces, hand


def render(t, c):
    q = pose(t)
    pieces, hand = build(q)
    zc = q['Z'] - c[2]

    def P(v):
        return (CX + F * (v[0] - c[0]) / zc, CY - F * (v[1] - c[1]) / zc)

    s = F / zc
    polys = []
    for layer, geo, tone, mat in sorted(pieces, key=lambda r: r[0]):
        if geo[0] == 'cap':
            from dog import capsule_poly
            polys.append((capsule_poly(P(geo[1]), P(geo[2]), geo[3] * s, geo[4] * s), tone, mat))
        elif geo[0] == 'poly':
            polys.append(([P(v) for v in geo[1]], tone, mat))
        else:
            cen, a, b, r = geo[1], geo[2], geo[3], geo[4]
            ts = np.linspace(0, 2 * np.pi, 30, endpoint=False)
            pts = [P(cen + np.array([a * math.cos(u) * math.cos(r) + b * math.sin(u) * math.sin(r),
                                     -a * math.cos(u) * math.sin(r) + b * math.sin(u) * math.cos(r)])) for u in ts]
            polys.append((pts, tone, mat))
    allp = np.array([v for p_, _, _ in polys for v in p_])
    x0, y0 = np.floor(allp.min(0)) - 4
    x1, y1 = np.ceil(allp.max(0)) + 4
    w, h = int(x1 - x0), int(y1 - y0)
    tone_im = Image.new('L', (w * SS, h * SS), 0)
    skin = Image.new('L', (w * SS, h * SS), 0)
    al = Image.new('L', (w * SS, h * SS), 0)
    dt, ds, da = ImageDraw.Draw(tone_im), ImageDraw.Draw(skin), ImageDraw.Draw(al)
    for pts, tone, mat in polys:
        pp = [((u - x0) * SS, (v - y0) * SS) for u, v in pts]
        dt.polygon(pp, fill=int(clamp(tone * 170, 0, 255)))
        ds.polygon(pp, fill=255 if mat == 'skin' else 0)
        da.polygon(pp, fill=255)
    hand_px = np.mean([P(v) for v in hand], 0)
    return int(x0), int(y0), tone_im, skin, al, q, hand_px
