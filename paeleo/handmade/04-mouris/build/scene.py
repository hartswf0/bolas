"""SCION-04 · the moulds of the scene: dog, person, door, porch and dusk, in metres, driven by the score.
Nothing here is shown directly: every mould is filled with archive pictures by torrent.py."""
import math
import numpy as np

def lerp(a, b, t): return a + (b - a) * t
def clamp(v, a=0., b=1.): return max(a, min(b, v))
def ease(t): t = clamp(t); return t * t * (3 - 2 * t)
def P(a, b, t): return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))
def add(a, b): return (a[0] + b[0], a[1] + b[1])

def circle(c, r, n=20):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]

def ellipse(c, rx, ry, rot=0., n=24):
    cr, sr = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n; x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((c[0] + x * cr - y * sr, c[1] + x * sr + y * cr))
    return out

def capsule(p, q, r1, r2, n=10):
    dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy) + 1e-9
    a = math.atan2(dy, dx); pts = []
    for i in range(n + 1):
        t = a + math.pi / 2 + math.pi * i / n
        pts.append((p[0] + r1 * math.cos(t), p[1] + r1 * math.sin(t)))
    for i in range(n + 1):
        t = a - math.pi / 2 + math.pi * i / n
        pts.append((q[0] + r2 * math.cos(t), q[1] + r2 * math.sin(t)))
    return pts

def chain(pts, radii):
    return [capsule(pts[i], pts[i + 1], radii[i], radii[i + 1]) for i in range(len(pts) - 1)]

def catmull(pts, sub=8):
    n = len(pts); out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for s in range(sub):
            t = s / sub; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    return out

def rot(v, a): return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


# ---------------------------------------------------------------- the dog's mould (local metres, nose toward -x, y up)
DOG_LABELS = {'far': 1, 'tail': 2, 'body': 3, 'near': 4, 'head': 5, 'ear': 6, 'eye': 7}

def dog_parts(a, time):
    c, l, hd, e = a['crouch'], a['lie'], a['head'], a['ear']
    tl, wag, rest, look, ph, mv = a['tail'], a['wag'], a['rest'], a['look'], a['walk_phase'], a['moving']
    parts = []   # (label, polygon)
    sy = lerp(0.50 - 0.11 * c, 0.20, l); hy = lerp(0.48 - 0.15 * c, 0.17, l)
    S = (-0.30, sy); H = (0.30, hy); M = ((S[0] + H[0]) / 2, (sy + hy) / 2)
    torso = catmull([add(S, (-0.14, -0.06)), add(S, (-0.02, 0.11)), add(M, (0, 0.085)), add(H, (0.03, 0.095)),
                     add(H, (0.13, 0.0)), add(H, (0.08, -0.13)), add(H, (-0.12, -0.14 + 0.03 * l)), add(M, (0, -0.13 + 0.03 * l)),
                     add(S, (-0.01, -0.19 + 0.04 * l)), add(S, (-0.13, -0.15))])
    # legs: standing joints and lying joints, blended by lie
    def front(off, far):
        sw = 0.13 * math.sin(ph + off) * mv; lift = 0.05 * max(0., math.cos(ph + off)) * mv
        top = add(S, (0.01 + (0.05 if far else 0), -0.11))
        st = [top, (top[0] + 0.5 * sw + 0.01, 0.10 + lift * 0.6), (top[0] + sw - 0.035, 0.026 + lift)]
        ly = [top, (S[0] - 0.12 - (0.03 if far else 0), 0.045), (S[0] - 0.30 - (0.05 if far else 0), 0.03)]
        return [P(st[i], ly[i], l) for i in range(3)], [0.058, 0.042, 0.04]
    def hind(off, far):
        sw = 0.13 * math.sin(ph + off) * mv; lift = 0.05 * max(0., math.cos(ph + off)) * mv
        top = add(H, (0.03 + (0.05 if far else 0), -0.05))
        st = [top, (top[0] + 0.07 + 0.3 * sw, top[1] - 0.17 + 0.06 * c), (top[0] + 0.10 + 0.6 * sw, 0.13 + lift * 0.6), (top[0] + 0.04 + sw, 0.026 + lift)]
        ly = [add(H, (0.0, -0.02)), add(H, (-0.14, -0.08)), add(H, (0.05, -0.13)), add(H, (-0.17 - (0.04 if far else 0), -0.14))]
        ly = [(p[0], max(p[1], 0.03)) for p in ly]
        return [P(st[i], ly[i], l) for i in range(4)], [0.085, 0.05, 0.04, 0.035]
    for (pts, rr), far in ((front(math.pi, True), True), (hind(0., True), True)):
        for poly in chain(pts, rr): parts.append(('far', poly))
        parts.append(('far', ellipse(add(pts[-1], (-0.03, 0)), 0.05, 0.026)))
    # tail
    ang = lerp(math.radians(55), math.radians(-25), clamp(tl / 0.5)) if tl <= 0.5 else lerp(math.radians(-25), math.radians(-118), clamp((tl - 0.5) / 0.85))
    ang = lerp(ang, math.radians(-8), l * 0.8)
    ang += wag * 0.45 * math.sin(2 * math.pi * 3.1 * time)
    root = add(H, (0.11, 0.05)); pts = [root]; rr = [0.05]; seg = 0.064; a_ = ang
    for k in range(5):
        a_ += 0.12 * (1 if tl < 0.9 else -0.5)
        nxt = (pts[-1][0] + seg * math.cos(a_), max(pts[-1][1] + seg * math.sin(a_), 0.02))
        pts.append(nxt); rr.append(0.045 - 0.006 * (k + 1))
    for poly in chain(pts, rr): parts.append(('tail', poly))
    parts.append(('body', torso))
    if l > 0.05:   # the haunch folded on the floor
        parts.append(('body', ellipse(add(H, (-0.02, -0.02)), 0.15 * l + 0.01, 0.12 * l + 0.01)))
    for (pts, rr) in (front(0., False), hind(math.pi, False)):
        for poly in chain(pts, rr): parts.append(('near', poly))
        parts.append(('near', ellipse(add(pts[-1], (-0.03, 0)), 0.05, 0.026)))
    # neck and head
    N0 = add(S, (-0.05, 0.05))
    def headrel(h):   # head carriage: up and alert at 1, below the line of the back at 0.45 (approach), low at 0.15
        if h >= 0.7: return P((-0.22, 0.10), (-0.15, 0.25), (h - 0.7) / 0.3)
        if h >= 0.45: return P((-0.28, -0.07), (-0.22, 0.10), (h - 0.45) / 0.25)
        return P((-0.24, -0.17), (-0.28, -0.07), (h - 0.15) / 0.30)
    hc = add(N0, headrel(min(hd, 1.0)))
    pitch = lerp(-0.55, 0.0, clamp((hd - 0.15) / 0.75))
    rest_c = (S[0] - 0.33, 0.12)
    hc = P(hc, rest_c, rest * l); pitch = lerp(pitch, 0.05, rest * l)
    lk = ease(clamp(look * 1.25))
    # looking in: the head turns away from us, into the doorway: muzzle shortens away, both ears seen from behind
    hc = add(hc, (-0.03 * lk, 0.02 * lk))
    pitch = lerp(pitch, 0.0, lk)
    def H_(v): v = rot(v, -pitch); return (hc[0] + v[0], hc[1] + v[1])   # head-local: -x is forward
    parts.append(('body', capsule(add(N0, (0.04, -0.02)), add(hc, (0.03, -0.01)), 0.11, 0.075)))
    ear_tip = P((0.17, 0.03), (0.03, 0.19), e)
    side = 1 - lk
    # profile ears (fade with the turn) and rear-view ears (both, symmetric)
    if side > 0.05:
        parts.append(('ear', [H_((-0.01, 0.05)), H_((0.085, 0.035)), H_((ear_tip[0], ear_tip[1] * (0.6 + 0.4 * side)))]))
        parts.append(('ear', [H_((-0.02, 0.055)), H_((0.05, 0.06)), H_((ear_tip[0] - 0.03, ear_tip[1] - 0.01))]))
    if lk > 0.05:
        for sx_ in (-1, 1):
            parts.append(('ear', [H_((sx_ * 0.035, 0.05)), H_((sx_ * 0.095, 0.03)), H_((sx_ * 0.085, 0.05 + 0.15 * lk))]))
    parts.append(('head', ellipse(H_((0, 0)), lerp(0.105, 0.095, lk), lerp(0.088, 0.095, lk), -pitch)))
    ml = side
    if ml > 0.08:
        parts.append(('head', capsule(H_((-0.05 * ml, -0.015)), H_((-0.19 * ml, -0.04)), 0.052, 0.036)))
    eye = H_((-0.055, 0.02)) if lk < 0.5 else None; nose = H_((-0.205 * ml, -0.03))
    return parts, dict(eye=eye, nose=nose, S=S, H=H, head=hc, torso=torso)


# ---------------------------------------------------------------- the person's mould (local metres, faces +x)
def person_parts(p, walk):
    s, r, lw = ease(p['sit']), p['reach'], p['low']
    hip = P((0, 0.95), (-0.05, 0.14), s)
    lean = 0.06 * r + 0.07 * lw
    sh = add(P((0.03, 1.45), (0.06, 0.68), s), (lean, -0.03 * r))
    neck = add(sh, (0.015, 0.07))
    head = add(sh, (0.04 + 0.02 * r, 0.21))
    parts = []
    # legs: standing (with steps) and sitting
    for k, side in enumerate((-1, 1)):
        sw = 0.18 * math.sin(walk + k * math.pi) * (1 - s)
        st = [hip, (0.02 + sw * 0.5, 0.50), (sw, 0.07), (sw + 0.17, 0.03)]
        si = [hip, (0.33 + 0.03 * k, 0.46 - 0.02 * k), (0.56 + 0.04 * k, 0.07), (0.71 + 0.04 * k, 0.03)]
        pts = [P(st[i], si[i], s) for i in range(4)]
        lab = 'far' if k == 0 else 'cloth'
        for poly in chain(pts, [0.085, 0.065, 0.05, 0.04]): parts.append((lab, poly))
    parts.append(('cloth', capsule(hip, sh, 0.15, 0.14)))
    # arms: far arm rests; near arm reaches (standing) or is offered low (sitting)
    rest_st = [sh, add(sh, (0.03, -0.27)), add(sh, (0.07, -0.52))]
    rest_si = [sh, (0.24, 0.42), (0.36, 0.50)]
    reach = [sh, add(sh, (0.27, -0.12)), add(sh, (0.58, -0.30))]
    low = [sh, (0.45, 0.34), (0.86, 0.18)]
    far = [P(rest_st[i], rest_si[i], s) for i in range(3)]
    near = [P(P(P(rest_st[i], rest_si[i], s), reach[i], r), low[i], lw) for i in range(3)]
    for poly in chain(far, [0.06, 0.05, 0.045]): parts.insert(0, ('far', poly))
    parts.append(('skin', ellipse(head, 0.105, 0.125)))
    parts.append(('cloth', capsule(add(sh, (0, -0.02)), neck, 0.08, 0.055)))
    parts.append(('cloth', capsule(near[0], near[1], 0.065, 0.05)))
    parts.append(('hand', capsule(P(near[1], near[2], 0.35), near[2], 0.042, 0.04)))   # bare forearm: built from hands
    hand_rot = lerp(-1.2, -0.45, r) if lw < 0.5 else 0.0
    parts.append(('hand', ellipse(add(near[2], (0.06, 0.0)), 0.11, 0.06, hand_rot)))
    parts.append(('hand', capsule(near[2], add(near[2], (0.17, 0.02 - 0.02 * r)), 0.035, 0.025)))
    return parts, dict(head=head, mouth=add(head, (0.09, -0.04)), hand=near[2])
