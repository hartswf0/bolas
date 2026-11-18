"""World layout, constraint graph (SCION #8) and cameras for Sh1/Sh2a/Sh2b.

World plane = the table plane of the photograph in source pixels, origin at the bare runner's hub.
Constraint graph:
  point hub (fixed) -- arm_k: line hub->tip_k (rigid, measured)  [attached-to runner]
  gate_k = tip_k                                                    [point on arm_k]
  ring_k.centre = gate_k + d_k * u_k, d_k = ring outer support radius along -u_k   [contact: rim touches gate]
  ring rest (Sh1) = the photograph's own loose-ring layout, translated by T_SCATTER  [equality: relative layout kept]
Moving a measured tip moves the gate, the homed ring centre, the flight end and the mould layout together.
"""
import json, math
from pathlib import Path
import numpy as np

OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/cutout-puppetry-camera-unit-a-sh1-sh2a-sh2b-sh5-heap-")
G = json.load(open(OUT / "geom_src.json"))["geo"]
BW, BH, FPS = 960, 408, 24
HUB = np.array(G["bare_runner"]["hub_src"])
SPRUE_ANGLE = 250            # the short thick post with the open mouth (seen in perspective) is the sprue, not an arm
ARM_ORDER = [181, 297, 9, 105]   # arm for ring R1..R4: R1 left arm (homes in the wide), R2-R4 the right side (homed in the close)
T_SCATTER = np.array([-482.0, -270.0])

arms_all = G["bare_runner"]["arms_all"]
def _arm(a):
    return min(arms_all, key=lambda r: abs(((r["angle_deg"] - a + 180) % 360) - 180))
ARMS = [_arm(a) for a in ARM_ORDER]
SPRUE = _arm(SPRUE_ANGLE)

def ell_support(e, phi):
    """distance from ellipse centre to its boundary in direction phi (radians, image coords)"""
    a, b = e["major"] / 2, e["minor"] / 2
    psi = phi - math.radians(e["angle"] + 90)  # cv2.fitEllipse angle refers to the first axis; major lies ~ angle+90 for these fits
    return a * b / math.hypot(b * math.cos(psi), a * math.sin(psi))

# loose ring k (photo order) -> flight index: rightmost-nearest ring first
LOOSE = G["loose_rings"]
order = sorted(range(4), key=lambda k: -LOOSE[k]["ellipse_src"]["cx"] - 0.3 * LOOSE[k]["ellipse_src"]["cy"])
RINGS = []
for j, k in enumerate(order):
    e = LOOSE[k]["ellipse_src"]
    arm = ARMS[j]
    tip = np.array(arm["tip_src"]) - HUB
    u = tip / np.linalg.norm(tip)
    d = ell_support(e, math.atan2(-u[1], -u[0])) - 2.0   # rim overlaps the gate stub by 2 px (the gate is fused to the rim)
    home = tip + d * u
    rest = np.array([e["cx"], e["cy"]]) - HUB + T_SCATTER
    RINGS.append(dict(flight=j + 1, loose_id=k, piece=f"ring{k}", ellipse_src=e, arm_angle=ARM_ORDER[j],
                      gate_world=tip, u=u, home_world=home, rest_world=rest, support=d))

# timing (s). R1 home at frame 312 (t = 13.000 s), the last frame of Sh2a; the cut C1 at 13.02 s lies between frames 312 and 313.
T_SH1, T_SH2A, T_SH2B, T_END = 0.0, 8.60, 13.02, 17.60
FLIGHT = {1: (10.30, 13.000), 2: (11.10, 14.000), 3: (11.80, 14.700), 4: (12.50, 15.300)}
ROT = {1: 8.0, 2: -6.0, 3: 9.0, 4: -7.0}       # max in-flight rotation, deg (<= 10)
LIFT = {1: 0.38, 2: 0.30, 3: 0.34, 4: 0.26}    # arc height as a fraction of chord

# cameras: centre (world), zoom (film px per world px)
def ease(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

CAM_SH1 = ((-560.0, 20.0), 1.00, (-548.0, 14.0), 1.025)      # slight drift over Sh1
CAM_SH2A = (-300.0, 10.0), 0.62
CAM_SH2B_A = (120.0, -5.0), 1.12                               # close on the right arm pair
CAM_HOLD = (9.0, 26.0), 0.75                                  # the complete shot, from 15.8 s
def camera(t):
    if t < T_SH2A:
        (c0, z0, c1, z1) = CAM_SH1; x = (t - T_SH1) / (T_SH2A - T_SH1)
        return np.array(c0) + (np.array(c1) - np.array(c0)) * x, z0 + (z1 - z0) * x
    if t < T_SH2B:
        return np.array(CAM_SH2A[0]), CAM_SH2A[1]
    x = ease((t - T_SH2B) / (15.80 - T_SH2B))
    return np.array(CAM_SH2B_A[0]) + (np.array(CAM_HOLD[0]) - np.array(CAM_SH2B_A[0])) * x, CAM_SH2B_A[1] + (CAM_HOLD[1] - CAM_SH2B_A[1]) * x

def to_film(p, cam):
    c, z = cam
    return [float((p[0] - c[0]) * z + BW / 2), float((p[1] - c[1]) * z + BH / 2)]
