"""SCION 23 · the person: a second runtime actor (profile, facing the porch), authored directly in 2D.
Its one clip, 'perform', is baked from the score's person channels (place, sit, reach, hand low, voice)."""
import json, math, os
import numpy as np
from common import ACTOR, load_score, FPS
import author as A

BONES = [('root', None), ('pelvis', 'root'), ('neck', 'pelvis'), ('head', 'neck'),
         ('uarm_f', 'pelvis'), ('farm_f', 'uarm_f'), ('hand_f', 'farm_f'),
         ('thigh_f', 'pelvis'), ('shin_f', 'thigh_f'), ('foot_f', 'shin_f'),
         ('thigh_n', 'pelvis'), ('shin_n', 'thigh_n'), ('foot_n', 'shin_n'),
         ('uarm_n', 'pelvis'), ('farm_n', 'uarm_n'), ('hand_n', 'farm_n')]
LENS = dict(pelvis=52, neck=9, uarm=29, farm=26, hand=8, thigh=43, shin=43, foot=21)
ORDER = ['uarm_f', 'farm_f', 'hand_f', 'thigh_f', 'shin_f', 'foot_f', 'pelvis', 'neck', 'head',
         'thigh_n', 'shin_n', 'foot_n', 'uarm_n', 'farm_n', 'hand_n']
ATT = dict(pelvis='p_torso', neck='p_neck', head='p_head', uarm_f='p_uarm_far', farm_f='p_farm_far',
           hand_f='p_hand_far', thigh_f='p_thigh_far', shin_f='p_shin_far', foot_f='p_shoe_far',
           thigh_n='p_thigh_near', shin_n='p_shin_near', foot_n='p_shoe_near', uarm_n='p_uarm_near',
           farm_n='p_farm_near', hand_n='p_hand_near')


def d(a):
    return np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])


def lerp(a, b, t): return a + (b - a) * t


def pose(sit, reach, low, call, walk, nod, t):
    """world joints (cm, root at the feet, facing +x) -> per-bone (start, angle)"""
    lean = 4 + 22 * reach + 12 * low * sit
    P = np.array([0.0, lerp(95, 13, sit)])
    ta = 90 - lean + 6 * sit
    N = P + LENS['pelvis'] * d(ta)
    ha = ta + nod
    Hc = N + LENS['neck'] * d(ha)
    Sh = N - 5 * d(ta)
    # arms (world angles)
    rest = (-95, -88, -84)
    beck = (-38 + 4 * math.sin(t * 9) * call, 38 + 14 * math.sin(t * 9) * call, 55)
    rch = (-14, -10, -6)
    sitarm = (-58, -12, -20)
    offer = (-38, -18, -6)
    def mix(*pairs):
        tot = sum(w for w, _ in pairs)
        return [sum(w * v[i] for w, v in pairs) / tot for i in range(3)]
    wn = [(max(0, 1 - call - reach - sit), rest), (call, beck), (reach, rch), (sit * (1 - low), sitarm),
          (sit * low, offer)]
    an = mix(*[p for p in wn if p[0] > 1e-6])
    af = mix((1 - sit, (-98, -92, -88)), (sit, (-120, -70, -60)))
    # legs
    st_n = (-90 + 9 * math.sin(walk), -90 + 6 * max(0, math.sin(walk)) * 2, 0)
    st_f = (-90 - 9 * math.sin(walk), -90 + 6 * max(0, -math.sin(walk)) * 2, 0)
    si_n, si_f = (38, -51, 0), (32, -45, -5)
    ln = [lerp(a, b, sit) for a, b in zip(st_n, si_n)]
    lf = [lerp(a, b, sit) for a, b in zip(st_f, si_f)]
    out = {'pelvis': (P, ta), 'neck': (N, ha), 'head': (Hc + 11 * d(ha), ha - 90)}
    for side, ang, base in (('n', an, Sh + np.array([2, 0])), ('f', af, Sh - np.array([3, 0]))):
        p = base
        for seg, a in zip(('uarm', 'farm', 'hand'), ang):
            out['%s_%s' % (seg, side)] = (p, a); p = p + LENS[seg] * d(a)
    for side, ang, off in (('n', ln, 3.0), ('f', lf, -5.0)):
        p = P + np.array([off, 0])
        for seg, a in zip(('thigh', 'shin', 'foot'), ang):
            out['%s_%s' % (seg, side)] = (p, a); p = p + LENS[seg] * d(a)
    out['root'] = (np.zeros(2), 0.0)
    return out


def locals_of(W):
    L = {}
    for name, parent in BONES:
        P0, a = W[name]
        if parent is None:
            L[name] = dict(x=0.0, y=0.0, rotation=0.0, scaleX=1.0); continue
        Pp, ap = W[parent]
        v = P0 - Pp; c, s = math.cos(math.radians(-ap)), math.sin(math.radians(-ap))
        L[name] = dict(x=round(v[0] * c - v[1] * s, 3), y=round(v[0] * s + v[1] * c, 3),
                       rotation=round(((a - ap) + 180) % 360 - 180, 3), scaleX=1.0)
    return L


def author():
    W0 = pose(0, 0, 0, 0, 0, 0, 0)
    L0 = locals_of(W0)
    bones = [dict(name=n, parent=p, length=LENS.get(n.split('_')[0], 0), transform='noScale', **L0[n]) for n, p in BONES]
    skin = {}
    for sl in ORDER:
        an = ATT[sl]
        skin[sl] = {an: A.region_att(an, inherit_scale=False)}
    sk = dict(skeleton=dict(name='person', units='cm', yUp=True, images='actors.png', atlas='actors.atlas'),
              bones=bones, slots=[dict(name=s, bone=s, attachment=ATT[s]) for s in ORDER], ik=[],
              skins=[dict(name='default', attachments=skin)])
    json.dump(sk, open(os.path.join(ACTOR, 'person.skel.json'), 'w'), indent=1)
    sc = load_score()
    fr = sc['frames']
    tl = dict(bones={}, slots={}, drawOrder=[dict(time=0, order=ORDER)], ik={}, events=[], duration=32.0, loop=False,
              track='body', note='baked every 2 frames from the score person channels')
    xs = []
    walk = 0.0
    for i in range(0, len(fr), 2):
        f = fr[i]; p = f['person']; t = f['t']
        if i >= 2:
            walk += abs(p['x'] - fr[i - 2]['person']['x']) * 9.0
        call = 1.0 if p['voice'] == 'call' and p['reach'] < 0.3 else 0.0
        talking = p['voice'] in ('call', 'soft')
        nod = (2.5 * math.sin(t * 7) if talking else 0) - 8 * p['low'] * p['sit']
        W = pose(p['sit'], p['reach'], p['low'], call, walk, nod, t)
        L = locals_of(W)
        for n, _ in BONES:
            b = tl['bones'].setdefault(n, dict(rotate=[], translate=[], scale=[]))
            b['rotate'].append(dict(time=round(t, 4), value=L[n]['rotation']))
            b['translate'].append(dict(time=round(t, 4), x=L[n]['x'], y=L[n]['y']))
    # smooth the call-arm switch: average neighbouring keys
    for n, b in tl['bones'].items():
        r = b['rotate']
        vals = [k['value'] for k in r]
        sm = [vals[0]] + [(vals[j - 1] + 2 * vals[j] + vals[j + 1]) / 4 for j in range(1, len(vals) - 1)] + [vals[-1]]
        for k, v in zip(r, sm): k['value'] = round(v, 3)
    json.dump(dict(about='SCION 23 person clip, baked from the score', animations={'perform': tl}),
              open(os.path.join(ACTOR, 'person.clips.json'), 'w'))
    print('person', len(bones), 'bones')
