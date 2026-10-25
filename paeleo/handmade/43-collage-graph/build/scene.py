"""SCION 43 · stages 2-4 · WORLD GRAMMAR + RULE ENGINE + COMPOSITOR.

The scene is a typed entity graph. Each frame the scene-event contract (the score) decides which rewrite rules fire;
the rules REPLACE / MERGE / SPLIT / ENTER / EXIT typed nodes; each node is a found fragment placed by its visual anchors
(two-point similarity: fragment anchor pair -> world anchor pair). Nothing is tweened between drawings: a node is either
held, re-anchored by a constraint (feet stay where they were planted), or replaced by another fragment.

World: metres along the porch (x, the score's axis; threshold 0, door opening -0.55..0.55 in my facade view), height v.
Screen: X = 340 + 180 x ; Y = ground_y(depth) - 180 * s * v.  Time: the score's 24 fps; the dog's graph is solved on twos.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
CACHE = os.path.join(HERE, 'cache')
FR = os.path.join(CACHE, 'frags')
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
FRAMES = SCORE['frames']
LIB = {f['id']: f for f in json.load(open(os.path.join(CACHE, 'frags.json')))['fragments']}
W, H = 1280, 720
PXM = 195.0
X0 = 300.0
WALL_BASE = 505
G_MID, G_SILL = 588, 520
DOOR_L, DOOR_R, DOOR_TOP_M = -0.55, 0.55, 2.0
HOUSE_R = 1.78  # where the house wall ends (m)
STEPS = 4.9


def PX(x): return X0 + PXM * x


_IMG = {}


def img(fid):
    if fid not in _IMG: _IMG[fid] = Image.open(os.path.join(FR, fid + '.png')).convert('RGBA')
    return _IMG[fid]


def sstep(a, b, x):
    t = np.clip((np.asarray(x, dtype=float) - a) / (b - a), 0, 1); t = t * t * (3 - 2 * t)
    return float(t) if t.ndim == 0 else t


# ------------------------------------------------------------------ placement: two-point similarity (+ optional mirror)
def place(canvas, fid, a1, a2, P1, P2, mirror=False, alpha=1.0, layer_log=None, node=None):
    """Map fragment anchors a1,a2 (fragment px) onto screen points P1,P2. mirror flips the fragment first."""
    im = img(fid)
    w, h = im.size
    if mirror:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
        a1 = (w - 1 - a1[0], a1[1]); a2 = (w - 1 - a2[0], a2[1])
    za1, za2 = complex(*a1), complex(*a2)
    zP1, zP2 = complex(*P1), complex(*P2)
    if abs(za2 - za1) < 1e-6: return None
    A = (zP2 - zP1) / (za2 - za1)
    if abs(A) < 1e-3: return None
    B = zP1 - A * za1
    # forward: X = Re(A) x - Im(A) y + Re(B) ; Y = Im(A) x + Re(A) y + Im(B)
    M = np.array([[A.real, -A.imag, B.real], [A.imag, A.real, B.imag], [0, 0, 1]])
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]]).T
    cc = M @ corners
    x0, y0 = int(math.floor(cc[0].min())) - 1, int(math.floor(cc[1].min())) - 1
    x1, y1 = int(math.ceil(cc[0].max())) + 1, int(math.ceil(cc[1].max())) + 1
    if x1 < 0 or y1 < 0 or x0 > canvas.width or y0 > canvas.height: return M
    T = np.array([[1, 0, x0], [0, 1, y0], [0, 0, 1]])
    Mi = np.linalg.inv(M @ np.eye(3)) @ T
    out = im.transform((x1 - x0, y1 - y0), Image.AFFINE, data=tuple(Mi[:2].reshape(-1)), resample=Image.BICUBIC)
    if alpha < 1:
        a = out.getchannel('A').point(lambda v: int(v * alpha)); out.putalpha(a)
    canvas.alpha_composite(out, (x0, y0)) if x0 >= 0 and y0 >= 0 else _paste_neg(canvas, out, x0, y0)
    if layer_log is not None and node is not None:
        layer_log.append(dict(node=node, frag=fid, mirror=bool(mirror), M=[round(v, 3) for v in M[:2].reshape(-1)]))
    return M


def place3(canvas, fid, a, P, alpha=1.0, layer_log=None, node=None):
    """general affine: fragment points a[0..2] -> screen points P[0..2] (used for the door leaf's swing)"""
    im = img(fid); w, h = im.size
    A = np.array([[a[k][0], a[k][1], 1] for k in range(3)], float)
    M2 = np.linalg.solve(A, np.array(P, float)).T  # 2x3
    M = np.vstack([M2, [0, 0, 1]])
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]]).T
    cc = M @ corners
    x0, y0 = int(math.floor(cc[0].min())) - 1, int(math.floor(cc[1].min())) - 1
    x1, y1 = int(math.ceil(cc[0].max())) + 1, int(math.ceil(cc[1].max())) + 1
    T = np.array([[1, 0, x0], [0, 1, y0], [0, 0, 1]])
    Mi = np.linalg.inv(M) @ T
    out = im.transform((x1 - x0, y1 - y0), Image.AFFINE, data=tuple(Mi[:2].reshape(-1)), resample=Image.BICUBIC)
    canvas.alpha_composite(out, (x0, y0)) if x0 >= 0 and y0 >= 0 else _paste_neg(canvas, out, x0, y0)
    if layer_log is not None: layer_log.append(dict(node=node, frag=fid, M=[round(v, 3) for v in M[:2].reshape(-1)]))
    return M


def place_strip(canvas, fid, a1, a2, P1, P2, wscale, layer_log=None, node=None):
    """map a1->P1, a2->P2 but keep the fragment's width at wscale screen px per fragment px (an arm is not fattened by reaching)"""
    a1, a2 = np.array(a1, float), np.array(a2, float); P1, P2 = np.array(P1, float), np.array(P2, float)
    da = a2 - a1; na = np.array([-da[1], da[0]]) / (np.linalg.norm(da) + 1e-9)
    dP = P2 - P1; nP = np.array([-dP[1], dP[0]]) / (np.linalg.norm(dP) + 1e-9)
    return place3(canvas, fid, [tuple(a1), tuple(a2), tuple(a1 + na * 10)], [tuple(P1), tuple(P2), tuple(P1 + nP * 10 * wscale)], layer_log=layer_log, node=node)


def _paste_neg(canvas, out, x0, y0):
    cx0, cy0 = max(0, -x0), max(0, -y0)
    out = out.crop((cx0, cy0, out.width, out.height))
    canvas.alpha_composite(out, (max(0, x0), max(0, y0)))


def apply(M, p):
    return (M[0, 0] * p[0] + M[0, 1] * p[1] + M[0, 2], M[1, 0] * p[0] + M[1, 1] * p[1] + M[1, 2])


def anc(fid, k): return tuple(LIB[fid]['anchors'][k])


# ------------------------------------------------------------------ the scene-event contract: score frame -> dog graph state
TURN1 = (3.417, 3.583, 3.75)       # profile-L | f027 | f030 | profile-R   (back shown from 3.75)
TURN2 = (7.917, 8.083, 8.25)       # profile-R (head already round) | f030 | f027 | profile-L
LOOKBACK = 7.458                   # REPLACE head by its mirror: the head comes round to the door first


def dog_state(i):
    """Return the dog's typed graph for score frame i (solved on twos)."""
    i2 = i - (i % 2)
    fr = FRAMES[i2]; d = fr['dog']; a = d['act']; t = fr['t']
    st = d['state']
    g = dict(i=i, i2=i2, t=t, state=st, x=d['x'], rules=[])
    # facing / merge for turns
    if TURN1[0] <= t < TURN1[1]: g['mode'] = 'whole'; g['whole'] = ('whole_f027', False); g['rules'].append('MERGE dog->whole_f027 (turn away, 1/2)')
    elif TURN1[1] <= t < TURN1[2]: g['mode'] = 'whole'; g['whole'] = ('whole_f030', False); g['rules'].append('MERGE dog->whole_f030 (turn away, 2/2)')
    elif TURN2[0] <= t < TURN2[1]: g['mode'] = 'whole'; g['whole'] = ('whole_f030', False); g['rules'].append('MERGE dog->whole_f030 (turn back, 1/2)')
    elif TURN2[1] <= t < TURN2[2]: g['mode'] = 'whole'; g['whole'] = ('whole_f027', True); g['rules'].append('MERGE dog->whole_f027 mirrored (turn back, 2/2)')
    else: g['mode'] = 'graph'
    g['facing'] = -1 if TURN1[2] <= t < TURN2[0] else (+1 if g['mode'] == 'graph' else 0)
    # discrete posture states (substitution, not tween): lie quantised to 4 drawings, crouch to 3
    lie = a['lie']
    if TURN1[2] <= t < 4.30: lie = 0.0  # it stands with its back turned before it lies down
    g['lie'] = round(lie * 3) / 3
    if st == 'lie_down' and g['lie'] < 1 / 3: g['lie'] = 1 / 3  # the choice shows on its first frame: it starts to go down
    g['crouch'] = round(a['crouch'] * 2) / 2 if g['lie'] < 0.3 else 0
    if st == 'retreat': g['crouch'] = max(g['crouch'], 0.5)   # it cowers as it backs away, from the first frame of the choice
    if st == 'watch' and t < 3.417: g['crouch'] = 0.0          # it stops backing and stands to look
    g['tail'] = a['tail']; g['wag'] = a['wag']
    g['moving'] = a['moving']
    # head choice: REPLACE head node by the drawing whose native angle fits the intention
    hv, look, rest = a['head'], a['look'], a['rest']
    sun_head = st in ('approach', 'lie_down')
    if look > 0.2:
        g['head'] = ('head_back_f027', 0.0); g['rules'].append('ENTER head->door light: REPLACE head by head_back_f027 (looks in)')
    elif sun_head:
        if g['lie'] >= 0.99 and rest > 0.5: g['head'] = ('head_low_f048', -14.0)
        elif g['lie'] >= 0.99: g['head'] = ('head_low_f048', 8.0 if hv > 0.5 else -6.0)
        else: g['head'] = ('head_low_f048', -42.0)
    else:
        if g['lie'] >= 0.66 and rest > 0.5: g['head'] = ('head_level_f012', -18.0)
        elif g['lie'] >= 0.66: g['head'] = ('head_level_f012', -4.0)
        elif g['crouch'] >= 0.5: g['head'] = ('head_level_f012', -6.0)
        elif hv >= 0.8 or (st == 'watch' and 2.3 < t < 3.417 and hv >= 0.6): g['head'] = ('head_alert_f006', 40.0)  # stops backing: head up to look
        else: g['head'] = ('head_level_f012', 14.0)
    g['head_mirror'] = (st == 'watch' and LOOKBACK <= t < TURN2[0])  # looks back over its shoulder
    if g['head_mirror']: g['rules'].append('REPLACE head by head_front_f030, mirrored to face the door, on the turned-away body (turns back to look)')
    return g


# ------------------------------------------------------------------ gait: feet are planted and stay planted
D_CYCLE, STANCE, LIFT = 0.72, 0.62, 0.075
DOGK = 1.25  # a big shepherd: local graph metres -> world metres
PHASE = dict(hind_n=0.0, fore_n=0.25, hind_f=0.5, fore_f=0.75)
NEUT = dict(fore_n=0.25, fore_f=0.19, hind_n=-0.20, hind_f=-0.26)


def travel(i):
    """distance walked along the facing direction up to score frame i (forward positive), and current facing."""
    return _TRAVEL[i]


def _build_travel():
    out = []; d = 0.0
    for k, f in enumerate(FRAMES):
        if k: dx = f['dog']['x'] - FRAMES[k - 1]['dog']['x']
        else: dx = 0
        t = f['t']
        face = -1 if TURN1[2] <= t < TURN2[0] else 1
        d += -face * dx  # facing left (+1) and x decreasing = forward
        out.append(d)
    return out


_TRAVEL = _build_travel()


def foot_rel(leg, d, moving, K=1.0):
    """foot position relative to the body, in LOCAL metres; the stride is solved in WORLD metres so a planted foot
    stays where it landed while the body travels d (K = local->world scale)"""
    p = (d / D_CYCLE + PHASE[leg]) % 1.0
    half = STANCE * D_CYCLE / 2
    if p < STANCE:
        return NEUT[leg] + (half - (p / STANCE) * 2 * half) / K, 0.0, 'stance'
    q = (p - STANCE) / (1 - STANCE)
    return NEUT[leg] + (-half + q * 2 * half) / K, LIFT * math.sin(math.pi * q) * min(1, moving * 1.5), 'swing'


# ------------------------------------------------------------------ the dog graph -> placed fragments
SHADE = dict(torso='torso_f006', chest='chest_f006', haunch='haunch_f006', fore_n='fore_b_f012', fore_f='fore_a_f012',
             hind_n='hind_a_f012', hind_f='hind_a_f012', hind_swing='hind_b_f012', fore_swing='fore_a_f012')
SUN = dict(torso='torso_f045', chest='chest_f045', haunch='haunch_f045', fore_n='fore_a_f045', fore_f='fore_b_f045',
           hind_n='hind_a_f045', hind_f='hind_a_f045', hind_swing='hind_b_f045', fore_swing='fore_b_f045')


def dog_depth(x, t):
    """my staging: it walks the middle of the porch, and comes in to the sill at the end of its approach"""
    if t < 14.7: k = 0.0
    else: k = sstep(1.75, 0.70, x)
    gy = G_MID + (G_SILL - G_MID) * k
    s = 1.0 - 0.07 * k
    return gy, s, k


def light_amount(t):
    return 0.10 + 0.90 * sstep(6.2, 6.9, t)


def node_material(g, node, ux_world, light_on):
    """REPLACE node.material shade->sun: the head by the decision to come; the rest by entering the door's light (x <= 0.62)."""
    if g['state'] not in ('approach', 'lie_down'): return 'shade'
    if node == 'head': return 'sun'
    if node in ('tail',): return 'shade'
    return 'sun' if (light_on > 0.5 and ux_world <= 0.62) else 'shade'


def draw_dog(canvas, i, log=None):
    g = dog_state(i)
    t, x = g['t'], g['x']
    gy, s, k = dog_depth(x, t)
    K = DOGK * s  # local metres -> world metres
    sc = PXM * K
    f = g['facing'] if g['facing'] != 0 else 1
    info = dict(g=g, gy=gy, s=s, nodes=[])
    L = light_amount(t)

    def W2S(u, v, ff=None):  # local (u forward, v up) -> screen
        ff = f if ff is None else ff
        return (PX(x) - ff * u * sc, gy - v * sc)

    if g['mode'] == 'whole':
        fid, mir = g['whole']
        hgt = 0.80
        P1 = (PX(x), gy); P2 = (PX(x), gy - hgt * sc)
        M = place(canvas, fid, anc(fid, 'ground'), anc(fid, 'top'), P1, P2, mirror=mir, layer_log=log, node='dog.whole')
        hx = apply(M, anc(fid, 'head'))[0] if not mir else None
        info['head_screen'] = None
        info['nose'] = info['neck'] = None
        info['facing_measured'] = 0
        return info

    lie, cr = g['lie'], g['crouch']
    # anchors of the body graph (metres, local)
    Sv = 0.47 - 0.10 * cr - 0.32 * lie
    Hv = 0.48 - 0.15 * cr - 0.34 * lie
    S = (0.24 + 0.03 * lie, Sv); Hh = (-0.24, Hv); Mm = (0.0, (Sv + Hv) / 2 + 0.03 - 0.02 * lie)
    N = (0.33 + 0.02 * lie, Sv + 0.12 - 0.06 * lie)
    T = (-0.31, Hv + 0.07)
    d = travel(g['i2'])
    # the legs: stance feet planted (constraint), swing feet substituted by a bent fragment
    legs = {}
    for leg in ('hind_f', 'fore_f', 'hind_n', 'fore_n'):
        top = S if leg.startswith('fore') else Hh
        if lie >= 0.99:
            fu = top[0] + (0.29 if leg.startswith('fore') else 0.22) + (0.0 if leg.endswith('n') else -0.05)
            foot = (fu, 0.035); phase = 'down'
        else:
            ru, lift, phase = foot_rel(leg, d, g['moving'], K)
            if lie > 0.1:  # settling: feet gather forward as it goes down
                ru = ru * (1 - lie) + (top[0] + (0.30 if leg.startswith('fore') else 0.18)) * lie
                lift = 0
            foot = (ru, lift)
        legs[leg] = (top, foot, phase)
    mats = {}
    for node, ux in (('head', N[0] + 0.15), ('chest', S[0]), ('haunch', Hh[0]), ('fore_n', legs['fore_n'][1][0]), ('fore_f', legs['fore_f'][1][0]),
                     ('hind_n', legs['hind_n'][1][0]), ('hind_f', legs['hind_f'][1][0]), ('tail', T[0])):
        mats[node] = node_material(g, node, x - f * ux, L)
    info['materials'] = mats
    SETS = dict(shade=SHADE, sun=SUN)

    def put_leg(leg):
        top, foot, phase = legs[leg]
        st = SETS[mats[leg]]
        fid = st[leg]
        if phase == 'swing': fid = st['hind_swing'] if leg.startswith('hind') else st['fore_swing']
        tp = (top[0] + (0.02 if leg.endswith('f') else 0.0), top[1] + 0.03)
        place(canvas, fid, anc(fid, 'top'), anc(fid, 'foot'), W2S(*tp), W2S(*foot), mirror=(f < 0), layer_log=log, node='dog.' + leg)
        if phase != 'swing' and lie < 0.1:
            info.setdefault('planted', []).append(round(x - f * foot[0] * K, 4))

    # far side first
    put_leg('hind_f'); put_leg('fore_f')
    # tail (pivot at base: the only rotating node), angle by score tail + wag
    ta = (30 - 72 * min(1.35, g['tail']) / 1.35) if lie < 0.99 else -8
    ta += 22 * g['wag'] * math.sin(2 * math.pi * 2.6 * t)
    tl = 0.30
    tip = (T[0] - tl * math.cos(math.radians(ta)), T[1] + tl * math.sin(math.radians(ta)))
    if lie >= 0.99: tip = (tip[0], max(0.03, tip[1]))
    place(canvas, 'tail_f006', anc('tail_f006', 'base'), anc('tail_f006', 'tip'), W2S(*T), W2S(*tip), mirror=(f < 0), layer_log=log, node='dog.tail')
    if mats['haunch'] == mats['chest']:
        tf = SETS[mats['chest']]['torso']
        place(canvas, tf, anc(tf, 'H'), anc(tf, 'S'), W2S(*Hh), W2S(*S), mirror=(f < 0), layer_log=log, node='dog.torso')
        put_leg('hind_n')
    else:
        # SPLIT torso at the light's edge: haunch (shade) and chest (sun) are two nodes with a visible seam
        info['split'] = True
        hf = SETS[mats['haunch']]['haunch']
        place(canvas, hf, anc(hf, 'H'), anc(hf, 'S'), W2S(*Hh), W2S(*S), mirror=(f < 0), layer_log=log, node='dog.haunch')
        put_leg('hind_n')
        cf = SETS[mats['chest']]['chest']
        place(canvas, cf, anc(cf, 'H'), anc(cf, 'S'), W2S(*Hh), W2S(*S), mirror=(f < 0), layer_log=log, node='dog.chest')
    put_leg('fore_n')
    # head: neck anchor on N, nose direction from the chosen drawing's angle
    hid, ang = g['head']
    hf_ = 1 if not g['head_mirror'] else -1  # mirrored head looks the other way
    hl = 0.30
    if hid == 'head_back_f027':
        # the neck runs from inside the chest up into the doorway; the found head seen from the room's light
        Nn = (N[0] - 0.08, N[1] - 0.05)
        crown = (Nn[0] + 0.02, Nn[1] + 0.33)
        M = place(canvas, hid, anc(hid, 'neck'), anc(hid, 'crown'), W2S(*Nn), W2S(*crown), mirror=(f > 0), layer_log=log, node='dog.head')  # any trace of muzzle points into the room
        info['nose'] = None; info['neck'] = W2S(*Nn); info['head_kind'] = 'away'
        info['facing_measured'] = f
    elif g['head_mirror']:
        # turning to look: the found frontal head (f030), mirrored so its muzzle points to the door, leads the body
        hid = 'head_front_f030'
        Nn = (N[0] - 0.02, N[1] - 0.02)
        crown = (Nn[0] + 0.03, Nn[1] + 0.30)
        mir = f < 0  # f030's muzzle points right; on a body facing away it is mirrored to point at the door
        M = place(canvas, hid, anc(hid, 'neck'), anc(hid, 'crown'), W2S(*Nn), W2S(*crown), mirror=mir, layer_log=log, node='dog.head')
        w = img(hid).width; a_mz = anc(hid, 'muzzle')
        info['nose'] = apply(M, (w - 1 - a_mz[0], a_mz[1]) if mir else a_mz)
        info['neck'] = W2S(*Nn); info['head_kind'] = hid
        info['facing_measured'] = 1 if info['nose'][0] < info['neck'][0] else -1
    else:
        nose = (N[0] + hf_ * hl * math.cos(math.radians(ang)), N[1] + hl * math.sin(math.radians(ang)))
        if lie >= 0.99 or (g['lie'] >= 0.66):
            nose = (nose[0], max(0.04, nose[1]))
        mirror_head = (f < 0) ^ (hf_ < 0)
        place(canvas, hid, anc(hid, 'neck'), anc(hid, 'nose'), W2S(*N), W2S(*nose), mirror=mirror_head, layer_log=log, node='dog.head')
        info['nose'] = W2S(*nose); info['neck'] = W2S(*N); info['head_kind'] = hid
        info['facing_measured'] = 1 if info['nose'][0] < info['neck'][0] else -1
    info['withers'] = W2S(*S)
    info['back_v'] = max(Sv, Hv)
    return info


# ------------------------------------------------------------------ the person (a graph too: coat, head, hand, voice)
def person_state(i):
    p = FRAMES[i]['person']
    return p


def draw_person(canvas, i, log=None):
    """the person graph: coat (or SPLIT coat: torso + thighs + shins), sleeve + found forearm/hand, found face + hair cut from the coat"""
    fr = FRAMES[i]; p = fr['person']; t = fr['t']
    px = p['x']; sit = round(p['sit'] * 3) / 3
    depth = sstep(-0.28, -1.0, px)  # doorway (sill) -> against the wall beside the door
    gy = 512 + 14 * depth
    sc = PXM
    X = PX(px)
    walking = 5.4 < t < 6.4 and sit < 0.99
    bob = 4 * abs(math.sin(math.pi * (t - 5.4) * 2.2)) if walking else 0
    def P(dx, h): return (X + dx * sc, gy - h * sc - bob)
    if sit < 0.2:
        place(canvas, 'coat_f000', anc('coat_f000', 'feet'), anc('coat_f000', 'top'), P(0.01, 0), P(0, 1.46), layer_log=log, node='person.body')
        sh = P(0.05, 1.36); neck = P(0.03, 1.45)
    else:
        hip_h = 0.85 * (1 - sit) + 0.10 * sit
        hip = P(0, hip_h)
        knee = P(0.42 * sit, hip_h + 0.30 * sit - 0.42 * (1 - sit))
        foot = P(0.42 * sit + 0.12, 0.02)
        place_strip(canvas, 'coat_lo', anc('coat_lo', 'hip'), anc('coat_lo', 'feet'), knee, foot, 0.95, layer_log=log, node='person.shin')
        place_strip(canvas, 'coat_lo', anc('coat_lo', 'hip'), anc('coat_lo', 'feet'), hip, knee, 1.05, layer_log=log, node='person.thigh')
        place(canvas, 'coat_up', anc('coat_up', 'hip'), anc('coat_up', 'top'), hip, P(-0.03, hip_h + 0.62), layer_log=log, node='person.torso')
        sh = P(0.03, hip_h + 0.54); neck = P(0.0, hip_h + 0.62)
    calling = p['voice'] == 'call'
    tilt = 10 if calling else (5 if p['voice'] == 'soft' else (6 if sit > 0.5 else 0))
    hh = 0.30 * sc
    crown = (neck[0] + hh * math.sin(math.radians(tilt)) - 6, neck[1] - hh * math.cos(math.radians(tilt)))
    # hair/back of the head: the coat cut round, behind the found face
    cx_, cy_ = (neck[0] * 0.45 + crown[0] * 0.55) - 0.06 * sc, (neck[1] * 0.45 + crown[1] * 0.55)
    place(canvas, 'hair_coat', anc('hair_coat', 'c'), anc('hair_coat', 'top'), (cx_, cy_), (cx_, cy_ - 0.12 * sc), layer_log=log, node='person.hair')
    M = place(canvas, 'head_miner_f000', anc('head_miner_f000', 'neck'), anc('head_miner_f000', 'crown'), neck, crown, layer_log=log, node='person.head')
    mouth = apply(M, anc('head_miner_f000', 'mouth'))
    # arm: sleeve (upper arm) + the found forearm and hand; hangs / reaches for the dog / is offered low
    reach, low = p['reach'], p['low']
    if low > 0.05:
        a1, a2 = math.radians(20 + 40 * low), math.radians(30 + 50 * low)
    else:
        a1, a2 = math.radians(8 + 72 * reach), math.radians(12 + 80 * reach)
    elbow = (sh[0] + 0.30 * sc * math.sin(a1), sh[1] + 0.30 * sc * math.cos(a1))
    tip = (elbow[0] + 0.38 * sc * math.sin(a2), elbow[1] + 0.38 * sc * math.cos(a2))
    if low > 0.05:  # the hand comes down to the floor, low and open, in front of the knees
        tip = (tip[0], min(gy - 0.16 * sc, tip[1] + 0.25 * sc * low))
    place_strip(canvas, 'sleeve_coat', anc('sleeve_coat', 'top'), anc('sleeve_coat', 'bottom'), sh, elbow, 0.95, layer_log=log, node='person.sleeve')
    place_strip(canvas, 'hand_f000', anc('hand_f000', 'arm'), anc('hand_f000', 'tip'), elbow, tip, 0.40, layer_log=log, node='person.hand')
    return dict(mouth=mouth, tip=tip, X=X, gy=gy)


def draw_voice(canvas, i, mouth, dog_xy, log=None):
    """ENTER voice: the telephone film's sound arcs, re-timed (its own frames cycle at 12 fps), become the person's voice.
    A call sends wide arcs travelling out to the dog; the soft voice makes small arcs that hardly leave the mouth."""
    fr = FRAMES[i]; v = fr['person']['voice']; t = fr['t']
    if v == 'none': return None
    on = max(tt for tt, ev in SCORE['timeline'] if 'voice' in ev and tt <= t + 1e-6)
    age = t - on
    ids = sorted(k for k in LIB if k.startswith('arcs_'))
    dx, dy = dog_xy[0] - mouth[0], dog_xy[1] - mouth[1]
    dist = math.hypot(dx, dy); ux, uy = dx / dist, dy / dist
    a0 = anc(ids[0], 'mouth')
    if v == 'call':
        n, speed, period = 4, 900.0, 0.22
        for k in range(n):
            r = (age - k * period) * speed  # radius of this wavefront (px)
            if r <= 30 or r > dist + 80: continue
            fid = ids[int((age * 12) + k) % len(ids)]
            scale = r / 170.0
            alpha = 0.95 * (1 - 0.55 * r / dist) * (1 - sstep(1.0, 1.3, age))
            place(canvas, fid, a0, (a0[0] + 100, a0[1]), mouth, (mouth[0] + ux * 100 * scale, mouth[1] + uy * 100 * scale), alpha=max(0, alpha), layer_log=log, node='voice.arcs')
    else:
        for k in range(2):
            r = 40 + ((age * 60 + k * 30) % 60)
            fid = ids[int(age * 12 + k) % len(ids)]
            place(canvas, fid, a0, (a0[0] + 100, a0[1]), mouth, (mouth[0] + ux * 100 * r / 170, mouth[1] + uy * 100 * r / 170), alpha=0.55 * (1 - (r - 40) / 70), layer_log=log, node='voice.arcs')
    return v


# ------------------------------------------------------------------ the world (built once), the door, the light
def build_world():
    """house wall from the home movie's stone pillar, porch from its path, dusk from a cloud time-lapse."""
    wall = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    stones = ['stone_f044', 'stone_f046', 'stone_f048', 'stone_f049']
    rng = np.random.RandomState(43)
    xr = int(PX(HOUSE_R))
    for yy in range(-40, WALL_BASE, 150):
        for xx in range(-30, xr, 120):
            s = Image.open(os.path.join(FR, stones[rng.randint(4)] + '.png')).convert('L')
            s = s.resize((int(s.width * 1.45), int(s.height * 1.45)), Image.BICUBIC).rotate(rng.uniform(-3, 3), expand=True, fillcolor=0)
            s = s.point(lambda v: int(v * 0.55 + 38))
            a = Image.new('L', s.size, 0); ImageDraw.Draw(a).rectangle((4, 4, s.width - 5, s.height - 5), fill=255)
            piece = Image.merge('RGBA', [s, s, s, a])
            wall.alpha_composite(piece, (xx + rng.randint(-8, 8), yy + rng.randint(-8, 8)))
    # trim to the house: right edge, base
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rectangle((0, 0, xr, WALL_BASE), fill=255)
    wall.putalpha(Image.fromarray(np.minimum(np.array(wall.getchannel('A')), np.array(m))))
    # the doorway hole
    hole = Image.new('L', (W, H), 255)
    ImageDraw.Draw(hole).rectangle((PX(DOOR_L), WALL_BASE - DOOR_TOP_M * PXM, PX(DOOR_R), WALL_BASE), fill=0)
    wall.putalpha(Image.fromarray(np.minimum(np.array(wall.getchannel('A')), np.array(hole))))
    # porch floor from the path
    fl = Image.open(os.path.join(FR, 'floor_f020.png')).convert('L')
    floor = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    strip = fl.resize((W // 3 + 2, 150), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: int(v * 0.5 + 30))
    for xx in (0, W // 3, 2 * W // 3):
        floor.paste(Image.merge('RGBA', [strip, strip, strip, Image.new('L', strip.size, 255)]), (xx, WALL_BASE))
    if PX(STEPS) + 14 < W: ImageDraw.Draw(floor).rectangle((PX(STEPS) + 14, 0, W, H), fill=(0, 0, 0, 0))
    # the lawn beyond the porch end (the home movie's ground, dark)
    lawn = fl.resize((W, 230), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2)).point(lambda v: int(v * 0.3 + 12))
    lawnl = Image.merge('RGBA', [lawn, lawn, lawn, Image.new('L', lawn.size, 255)])
    if PX(STEPS) + 14 < W: floor.alpha_composite(lawnl.crop((int(PX(STEPS)) + 14, 0, W, 230)), (int(PX(STEPS)) + 14, WALL_BASE - 15))
    # steps at the porch end: two stone slabs cut from the pillar
    st = Image.open(os.path.join(FR, 'stone_f048.png')).convert('L')
    for k in range(3 if PX(STEPS) + 14 < W else 0):
        sl = st.resize((90, 40)); a = Image.new('L', sl.size, 255)
        floor.alpha_composite(Image.merge('RGBA', [sl, sl, sl, a]), (int(PX(STEPS)) + 14 + k * 16, WALL_BASE + 70 + k * 40))
    # front fascia (dark)
    ImageDraw.Draw(floor).rectangle((0, 655, min(W, int(PX(STEPS)) + 14), H), fill=(28, 26, 24, 255))
    # hedge beyond the porch
    hd = Image.open(os.path.join(FR, 'hedge_f000.png')).convert('L')
    hedge = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hs = hd.resize((W - xr + 40, 120), Image.BICUBIC)
    hv = np.asarray(hs).astype(float)
    ha = np.clip((200 - hv) * 3, 0, 255).astype(np.uint8)  # dark shrubs keyed against the bright sky of the home movie
    ha[60:] = 255
    hedge.paste(Image.merge('RGBA', [hs, hs, hs, Image.fromarray(ha)]), (xr - 20, WALL_BASE - 115))
    # door frame: jambs and lintel from the Straight Talk frame, sill from its floor
    jamb = Image.open(os.path.join(FR, 'jamb_f030.png')).convert('RGB')
    frame = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    jh = int(DOOR_TOP_M * PXM) + 20
    jj = jamb.resize((18, jh)).convert('RGBA')
    frame.alpha_composite(jj, (int(PX(DOOR_L)) - 18, WALL_BASE - jh + 4))
    frame.alpha_composite(jj, (int(PX(DOOR_R)), WALL_BASE - jh + 4))
    lin = jamb.resize((18, int((DOOR_R - DOOR_L) * PXM) + 36)).rotate(90, expand=True).convert('RGBA')
    frame.alpha_composite(lin, (int(PX(DOOR_L)) - 18, WALL_BASE - jh - 14))
    sill = Image.open(os.path.join(FR, 'sill_f030.png')).convert('RGB').resize((int((DOOR_R - DOOR_L) * PXM) + 36, 14)).convert('RGBA')
    frame.alpha_composite(sill, (int(PX(DOOR_L)) - 18, WALL_BASE - 4))
    # porch post + eave beam (dark wood = the home movie's coat cut as timber)
    post = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    coat = Image.open(os.path.join(FR, 'coat_f000.png')).convert('RGBA')
    beam = coat.crop((6, 20, 56, 60)).resize((W, 34)).convert('RGBA'); beam.putalpha(255)
    post.alpha_composite(beam, (0, 0))
    pst = coat.crop((10, 10, 50, 180)).resize((24, WALL_BASE + 10)); pst.putalpha(255)
    post.alpha_composite(pst, (int(PX(HOUSE_R)) + 4, 20))
    return dict(wall=wall, floor=floor, hedge=hedge, frame=frame, post=post)


_SKY = {}


def sky(t):
    k = int(t * 1.2) % 31 * 2
    if k not in _SKY:
        c = np.asarray(Image.open(os.path.join(FR, 'sky_f%03d.png' % k)).resize((W, 540), Image.BICUBIC)).astype(float) / 255
        _SKY[k] = c
    c = _SKY[k]
    yy = np.linspace(0, 1, 540)[:, None]
    top = np.array([0.10, 0.12, 0.26]); hor = np.array([0.78, 0.48, 0.36])
    base = top[None, None, :] * (1 - yy[..., None] ** 1.6) + hor[None, None, :] * (yy[..., None] ** 1.6)
    cl = np.clip((c - 0.55) * 2.2, 0, 1)[..., None]
    rose = np.array([0.62, 0.44, 0.50])
    out = base * (1 - cl * 0.8) + rose * cl * 0.8 * (0.6 + 0.4 * yy[..., None])
    dark = 1 - 0.18 * (t / 32)
    full = np.zeros((H, W, 3)); full[:540] = out * dark; full[540:] = out[-1] * dark
    return full


def draw_door(canvas, t, log=None):
    """REPLACE door.leaf by the found swing (Straight Talk, closing played backward); ENTER the room (a lit bulb)."""
    op = sstep(6.2, 6.75, t)
    seq = ['leaf_f030', 'leaf_f028', 'leaf_f026', 'leaf_f024', 'leaf_f022', 'leaf_f020']
    k = int(round(op * (len(seq) - 1)))
    if t < 6.2: k = 1  # ajar
    fid = seq[k]
    wfrac = [0.93, 0.86, 0.7, 0.55, 0.42, 0.3][k]
    # room first (seen through the opening)
    room = img('room_bulb_f%03d' % (12 + 4 * (int(t * 3) % 4)))
    x0, x1 = int(PX(DOOR_L)), int(PX(DOOR_R)); y0 = int(WALL_BASE - DOOR_TOP_M * PXM)
    r = room.resize((x1 - x0, WALL_BASE - y0), Image.BICUBIC)
    canvas.alpha_composite(r, (x0, y0))
    # leaf: hinge on the left jamb; its found width scaled by the swing
    lf = LIB[fid]['anchors']
    lw = (x1 - x0) * wfrac
    a = [(lf['left'][0], lf['top'][1]), (lf['left'][0], lf['ground'][1]), (lf['right'][0], lf['top'][1])]
    place3(canvas, fid, a, [(x0, y0), (x0, WALL_BASE), (x0 + lw, y0 + 8 * (1 - wfrac))], layer_log=log, node='door.leaf')
    return dict(leaf=fid, open=op, wfrac=wfrac)


_LM = []


def light_map(t):
    """the door's light: inside the opening, a column in front of it, and a spill on the porch floor"""
    L = light_amount(t)
    if _LM: return _LM[0] * L
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    xl, xr = PX(DOOR_L), PX(DOOR_R)
    ytop = WALL_BASE - DOOR_TOP_M * PXM
    spread = np.clip(yy - WALL_BASE, 0, None) * 0.45
    inx = sstep(-45, 25, xx - (xl - spread)) * sstep(-45, 25, (xr + spread) - xx)
    col = inx * sstep(ytop - 20, ytop + 20, yy) * (1 - sstep(660, 700, yy))
    _LM.append(col.astype(np.float32))
    return _LM[0] * L


def grade(rgb, Lm, t):
    """dusk everywhere outside; warm where the door's light reaches"""
    lum = rgb.mean(axis=2, keepdims=True)
    rgbn = rgb * 0.7 + lum * 0.3
    dusk = rgbn * np.array([0.40, 0.47, 0.70]) * (1 - 0.15 * t / 32)
    warm = rgbn * np.array([1.18, 0.92, 0.62]) * 1.05
    Lm = Lm[..., None]
    return dusk * (1 - Lm) + warm * Lm


# ------------------------------------------------------------------ prompts (typed slips, optional, my way)
FONT = {}


def font(name, size):
    k = (name, size)
    if k not in FONT: FONT[k] = ImageFont.truetype(os.path.join(CACHE, 'fonts', name), size)
    return FONT[k]


def prompt_at(t):
    cur = None
    for tt, txt in SCORE['prompts']:
        if tt <= t: cur = (tt, txt)
    if cur and t - cur[0] < 2.6: return cur[1]
    return None


def draw_prompt(im, t):
    txt = prompt_at(t)
    if not txt: return
    d = ImageDraw.Draw(im)
    f = font('mono.ttf', 19)
    w = d.textlength(txt, font=f)
    x, y = 36, 40
    d.polygon([(x - 12, y - 9), (x + w + 14, y - 11), (x + w + 10, y + 30), (x - 10, y + 32)], fill=(222, 214, 194))
    d.text((x, y), txt, font=f, fill=(40, 34, 30))


# ------------------------------------------------------------------ one frame
WORLD = None


def render(i, want_layers=False):
    global WORLD
    if WORLD is None: WORLD = build_world()
    t = FRAMES[i]['t']
    log = []
    can = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    can.alpha_composite(WORLD['hedge'])
    door = draw_door(can, t, log)
    can.alpha_composite(WORLD['wall'])
    can.alpha_composite(WORLD['frame'])
    can.alpha_composite(WORLD['floor'])
    can.alpha_composite(WORLD['post'])
    pinfo = draw_person(can, i, log)
    doglayer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dinfo = draw_dog(doglayer, i, log)
    # contact shadow under the dog
    da = np.asarray(doglayer.getchannel('A')).astype(float) / 255
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ys, xs = np.nonzero(da > 0.5)
    if len(xs):
        ImageDraw.Draw(sh).ellipse((xs.min() + 6, dinfo['gy'] - 9, xs.max() - 6, dinfo['gy'] + 7), fill=(0, 0, 0, 120))
        sh = sh.filter(ImageFilter.GaussianBlur(5))
        can.alpha_composite(sh)
    rim = doglayer.getchannel('A').filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(0.6))
    paper = Image.new('RGBA', (W, H), (226, 218, 198, 255)); paper.putalpha(rim)
    can.alpha_composite(paper)
    can.alpha_composite(doglayer)
    dog_xy = (xs.mean(), ys.mean()) if len(xs) else (PX(3), 520)
    fx = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_voice(fx, i, pinfo['mouth'], dog_xy, log)
    rgba = np.asarray(can).astype(float) / 255
    Lm = light_map(t)
    # the room itself glows (its own light), brighter once open
    lit = grade(rgba[..., :3], Lm, t)
    sk = sky(t)
    a = rgba[..., 3:4]
    out = lit * a + sk * (1 - a)
    # light spill on the porch floor (additive warm), and a glow at the opening
    out = np.clip(out, 0, 1)
    im = Image.fromarray((out * 255).astype(np.uint8), 'RGB').convert('RGBA')
    fa = np.asarray(fx).astype(float) / 255  # sound marks are luminous: drawn after the grade, tinted pale
    if fa[..., 3].max() > 0:
        tint = Image.new('RGBA', (W, H), (236, 226, 200, 0)); tint.putalpha(Image.fromarray((fa[..., 3] * 255).astype(np.uint8)))
        im.alpha_composite(tint)
    im = im.convert('RGB')
    draw_prompt(im, t)
    if len(xs):
        dinfo['meas'] = dict(cx=float(xs.mean()), cy=float(ys.mean()), x0=int(xs.min()), x1=int(xs.max()), y0=int(ys.min()), y1=int(ys.max()))
    meta = dict(dog=dinfo, person=pinfo, door=door, log=log, dog_alpha=da if want_layers else None)
    return im, meta


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, '../proof'), exist_ok=True)
    for i in map(int, sys.argv[1:]):
        im, meta = render(i)
        im.save(os.path.join(HERE, '../proof/f%03d.jpg' % i), quality=90)
        print(i, meta['dog']['g']['state'], meta['dog']['g']['rules'])
