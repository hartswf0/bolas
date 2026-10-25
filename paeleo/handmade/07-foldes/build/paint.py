"""SCION 07 · paints screen-space contour strokes (dog or person) with ink and wash, in draw order (z)."""
import math
from draw import cr, limb_outline, INK

LINE = 2.1


def _foot(paw, w, fwd, S):
    r = max(w * 0.62, 0.028 * S)
    cx, cy = paw[0] + fwd * 0.03 * S, paw[1] - r * 0.55
    rx, ry = r * (1.0 + 0.55 * abs(fwd)), r * 0.62
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in [math.pi * (i / 12) for i in range(13)]]


def paint(cv, strokes, wash, S, fwd=0.0, ink=INK, washes=None, line=LINE, seed=0.0, light=None):
    """washes: optional {stroke name: colour}. light: optional fn(x,y)->0..1 that warms the wash (the door light)."""
    lval = 0.0
    if light is not None:
        body = next((s for s in strokes if s['name'] in ('body', 'coat')), strokes[0])
        P = body['P']
        lval = light(sum(q[0] for q in P) / len(P), max(q[1] for q in P))
    for s in sorted(strokes, key=lambda s: s['z']):
        a = s['a']
        if a < 0.02:
            continue
        col = (washes or {}).get(s['name'], wash)
        if washes is None and s['name'] in ('RF', 'LF', 'RH', 'LH', 'earL', 'earR') and s['k'] < 0.95:
            col = tuple(int(c * (0.86 + 0.14 * (s['k'] - 0.5) / 0.45)) for c in col)   # the far side is in shade
        if lval > 0:
            col = tuple(int(c + (w - c) * lval) for c, w in zip(col, (250, 214, 150)))
        fa = max(0.0, min(1.0, (a - 0.25) / 0.4))
        k = s['k']
        sd = seed + sum(ord(c) * (j + 1) for j, c in enumerate(s['name'])) % 97
        if s['type'] == 'closed':
            poly = cr(s['P'], True, 7)
            if s.get('fill', True) and fa > 0:
                cv.fill(poly, col, fa)
            cv.line(poly, line * k, ink, a, sd, taper=(1, 1))
        elif s['type'] == 'open':
            poly = cr(s['P'], False, 6)
            if len(poly) >= 2 and math.hypot(poly[-1][0] - poly[0][0], poly[-1][1] - poly[0][1]) < 0.5:
                cv.dot(poly[0][0], poly[0][1], line * k * 0.55, ink, a)
            else:
                cv.line(poly, line * k, ink, a, sd)
        elif s['type'] == 'limb':
            C, W, L, R = limb_outline(s['P'], s['W'], fwd, S)
            is_leg = s['name'] in ('RF', 'LF', 'RH', 'LH')
            if is_leg:
                foot = _foot(C[-1], W[-1], fwd, S)
                # foot arc from the left side's end around to the right side's end
                fl = foot if (L[-1][0] - R[-1][0]) * (foot[0][0] - foot[-1][0]) >= 0 else foot[::-1]
                outline = L + fl + R[::-1]
            else:
                tip = C[-1]
                outline = L + [tip] + R[::-1]
            if fa > 0:
                cv.fill(outline, col, fa)
            n0 = max(1, int(len(L) * (0.22 if is_leg else 0.18)))   # the top of a limb melts into the body: no line there
            if is_leg:
                cv.lines([L[n0:] + fl + R[::-1][:len(R) - n0]], line * k, ink, a, sd, taper=(0.2, 0.2))
            else:
                cv.lines([L[n0:] + [tip] + R[::-1][:len(R) - n0]], line * k, ink, a, sd, taper=(0.2, 0.2))
