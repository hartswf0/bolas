"""SCION 07 · correspondence mapper + interpolation engineer.

blend(): an in-between is the weighted sum of CORRESPONDING points of key drawings (same stroke name, same point index).
compose(): places the head key on the body key (the neck points are bound to the head: a point correspondence across
groups), applies the acting fields (ears, tail, wag, breath) and the foot interventions (planted paws), and returns strokes
in body-local metres."""
import math, copy, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
K = json.load(open(os.path.join(os.path.dirname(HERE), 'keys', 'dog_keys.json')))
BODY, HEAD = K['body'], K['head']
LEGS = ('RF', 'LF', 'RH', 'LH')


def _lerp_pts(A, B, t):
    return [[a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t] for a, b in zip(A, B)]


def tail_of(key, tv):
    mid = key['tail']['pts']
    if '_tail_hi' not in key:
        return mid
    if tv <= 0.5:
        return _lerp_pts(key['_tail_hi'], mid, max(tv, 0) / 0.5)
    return _lerp_pts(mid, key['_tail_tuck'], min((tv - 0.5) / 0.85, 1.0))


def blend(weights, table, tv=0.5):
    """weights: {keyname: w}. Returns a key whose every point is sum(w_i * point_i)."""
    tot = sum(weights.values())
    items = [(table[n], w / tot) for n, w in weights.items() if w > 1e-6]
    base = copy.deepcopy(items[0][0])
    for name, s in base.items():
        if name.startswith('_'):
            if isinstance(s, (int, float)):
                base[name] = sum(k[name] * w for k, w in items)
            continue
        pts = [[0.0, 0.0] for _ in s['pts']]
        for k, w in items:
            src = tail_of(k, tv) if name == 'tail' else k[name]['pts']
            for i, p in enumerate(src):
                pts[i][0] += p[0] * w; pts[i][1] += p[1] * w
        s['pts'] = pts
        for a in ('a', 'k', 'z'):
            s[a] = sum(k[name][a] * w for k, w in items)
        if 'w' in s:
            s['w'] = [sum(k[name]['w'][i] * w for k, w in items) for i in range(len(s['w']))]
    return base


def rot(p, c, th):
    x, y = p[0] - c[0], p[1] - c[1]
    return [c[0] + x * math.cos(th) - y * math.sin(th), c[1] + x * math.sin(th) + y * math.cos(th)]


def place_head(hk, cx, cy, ang, sc):
    out = {}
    for n, s in hk.items():
        if n.startswith('_'):
            out[n] = s; continue
        s2 = dict(s)
        s2['pts'] = [[cx + sc * (p[0] * math.cos(ang) - p[1] * math.sin(ang)), cy + sc * (p[0] * math.sin(ang) + p[1] * math.cos(ang))]
                     for p in s['pts']]
        out[n] = s2
    return out


def compose(bw, hw, place, ear=0.9, tv=0.5, wag=0.0, t=0.0, breath=0.0, paws=None, lifts=None):
    """bw/hw: body/head key weights. place: (cx, cy, ang, sc) of the head in body-local metres.
    paws: {leg: [x, y]} body-local planted paw positions overriding the key (foot intervention). Returns stroke list."""
    b = blend(bw, BODY, tv)
    h = blend(hw, HEAD)
    cx, cy, ang, sc = place
    H = place_head(h, cx, cy, ang, sc)
    gaze = h['_gaze']
    s = 1.0 if gaze <= 0.05 else -1.0
    # neck binding: body points 0 (neck top) and 11 (throat) are bound to the back of the skull and the throat
    att = b['_neck_attach']
    nt = place_head({'p': {'pts': [[0.10 * s, 0.035], [0.0, -0.075]]}}, cx, cy, ang, sc)['p']['pts']
    bp = b['body']['pts']
    bp[0] = [bp[0][0] + (nt[0][0] - bp[0][0]) * att, bp[0][1] + (nt[0][1] - bp[0][1]) * att]
    bp[11] = [bp[11][0] + (nt[1][0] - bp[11][0]) * att, bp[11][1] + (nt[1][1] - bp[11][1]) * att]
    # breath: the barrel swells
    if breath:
        for i in (1, 2, 3, 7, 8, 9):
            bp[i][1] += breath * (0.012 if i < 4 else -0.008)
    # ears: rotate about the base by how flat they are (score act 'ear': 1 pricked .. 0 flat)
    for en in ('earR', 'earL'):
        e = H[en]['pts']
        base = [(e[0][0] + e[3][0]) / 2, (e[0][1] + e[3][1]) / 2]
        flat = 1.0 - max(min(ear, 1.0), 0.0)
        wp = max(0.0, min(1.0, (abs(gaze) - 0.35) / 0.55))   # how much of a profile this head is
        sb = 1.0 if gaze < 0 else -1.0                         # profile: flatten toward the back of the head
        so = 1.0 if base[0] > cx else -1.0                     # from behind / in front: droop outward
        th = -flat * (wp * sb * math.radians(58) + (1 - wp) * so * math.radians(34))
        sc_e = 1.0 - 0.3 * flat
        H[en]['pts'] = [rot([base[0] + (p[0] - base[0]) * sc_e, base[1] + (p[1] - base[1]) * sc_e], base, th) for p in e]
    # tail wag: a travelling bend from the root
    tp = b['tail']['pts']
    if wag > 0.005:
        root = tp[0]
        ph = math.sin(2 * math.pi * 2.1 * t)
        for i in range(1, len(tp)):
            th = wag * 0.55 * ph * (i / (len(tp) - 1)) ** 1.1
            tp[i] = rot(tp[i], root, th)
    # foot interventions: re-pose each leg drawing to reach its planted paw (similarity on the drawn leg)
    if paws:
        for L in LEGS:
            if L not in paws:
                continue
            cl = b[L]['pts']
            top, paw = cl[0], cl[-1]
            new = paws[L]
            v0 = (paw[0] - top[0], paw[1] - top[1]); v1 = (new[0] - top[0], new[1] - top[1])
            l0 = math.hypot(*v0) or 1e-6; l1 = math.hypot(*v1)
            a0 = math.atan2(v0[1], v0[0]); a1 = math.atan2(v1[1], v1[0])
            da = a1 - a0; k = l1 / l0
            out = []
            lift = (lifts or {}).get(L, 0.0)
            for j, p in enumerate(cl):
                x, y = p[0] - top[0], p[1] - top[1]
                # along/perp in the key's frame, then bend the joints a little more as the paw lifts (a step)
                al = (x * v0[0] + y * v0[1]) / l0; pe = (-x * v0[1] + y * v0[0]) / l0
                if 0 < j < len(cl) - 1:
                    pe *= 1.0 + 0.7 * lift
                    pe += 0.025 * lift * (1 if L[1] == 'H' else -1) * (1 if b['_fwd'] <= 0 else -1)
                if k < 1:
                    pe *= 1 + min(1 - k, 0.3) * 1.2   # a compressed leg bends rather than shrinks
                al *= k
                ux, uy = math.cos(a1), math.sin(a1)
                out.append([top[0] + al * ux - pe * uy, top[1] + al * uy + pe * ux])
            out[-1] = list(new)
            b[L]['pts'] = out
    strokes = []
    for n, st in b.items():
        if n.startswith('_'):
            continue
        strokes.append(dict(st, name=n))
    for n, st in H.items():
        if n.startswith('_'):
            continue
        strokes.append(dict(st, name=n))
    meta = {'fwd': b['_fwd'], 'gaze': gaze}
    return strokes, meta


def to_screen(strokes, ox, oy, S, x_anchor):
    out = []
    for s in strokes:
        s2 = dict(s)
        s2['P'] = [(ox + (x_anchor + p[0]) * S, oy - p[1] * S) for p in s['pts']]
        if 'w' in s:
            s2['W'] = [w * S for w in s['w']]
        out.append(s2)
    return out
