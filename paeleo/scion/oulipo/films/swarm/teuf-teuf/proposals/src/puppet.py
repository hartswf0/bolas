"""Articulated cut-card puppet: FK spine, two-bone IK limbs pinned to contacts."""
import math
from common import limb


def ik2(p0, target, L1, L2, bend=1):
    x0, y0 = p0; tx, ty = target
    dx, dy = tx - x0, ty - y0
    d = min(math.hypot(dx, dy), L1 + L2 - 1e-3)
    a = math.atan2(dy, dx)
    c = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    b = math.acos(max(-1, min(1, c)))
    k = (x0 + L1 * math.cos(a + bend * b), y0 + L1 * math.sin(a + bend * b))
    e = (k[0] + L2 * math.cos(math.atan2(ty - k[1], tx - k[0])),
         k[1] + L2 * math.sin(math.atan2(ty - k[1], tx - k[0])))
    return k, e


def figure(hip, lean_deg, feet, hands, scale=1.0, head_tilt=0.0, knee_bend=(-1, -1), elbow_bend=(1, 1)):
    """returns list of polygons/ellipses and a joint dict.
    lean_deg: torso angle from vertical (+ = leaning right).
    feet, hands: two contact targets each (IK)."""
    s = scale
    T, TH, SH, UA, LA = 92 * s, 60 * s, 60 * s, 46 * s, 44 * s
    a = math.radians(lean_deg)
    neck = (hip[0] + T * math.sin(a), hip[1] - T * math.cos(a))
    sh = (hip[0] + T * 0.88 * math.sin(a), hip[1] - T * 0.88 * math.cos(a))
    parts = []
    parts.append(limb(hip, neck, 15 * s, 12 * s))                       # torso
    # buttock / chest mass
    parts.append(limb(hip, (hip[0] + T * 0.35 * math.sin(a), hip[1] - T * 0.35 * math.cos(a)), 17 * s, 15 * s))
    ha = a + math.radians(head_tilt)
    head = (neck[0] + 17 * s * math.sin(ha), neck[1] - 17 * s * math.cos(ha))
    parts.append(("ellipse", head[0], head[1], 13 * s, 15 * s))
    # hair knot / brow, so the head reads in silhouette
    parts.append(("ellipse", head[0] + 9 * s * math.cos(ha), head[1] + 9 * s * math.sin(ha) - 2 * s, 6 * s, 5 * s))
    joints = {"hip": hip, "neck": neck, "head": head}
    for i, f in enumerate(feet):
        k, e = ik2(hip, f, TH, SH, knee_bend[i])
        parts.append(limb(hip, k, 11 * s, 8 * s)); parts.append(limb(k, e, 8 * s, 5 * s))
        parts.append(limb(e, (e[0] + 15 * s, e[1] + 1), 5 * s, 3.5 * s))   # foot
        joints[f"knee{i}"] = k; joints[f"foot{i}"] = e
    for i, h in enumerate(hands):
        k, e = ik2(sh, h, UA, LA, elbow_bend[i])
        parts.append(limb(sh, k, 7 * s, 5.5 * s)); parts.append(limb(k, e, 5.5 * s, 4 * s))
        parts.append(("ellipse", e[0], e[1], 5.5 * s, 5 * s))
        joints[f"elbow{i}"] = k; joints[f"hand{i}"] = e
    return parts, joints
