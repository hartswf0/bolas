"""SCION 42 · the person: an authored layered puppet (hand-set joints, forward kinematics), drawn as a coat silhouette.
It is the 'rig-only' structure the dog is compared against: nothing about it was learned.
"""
import numpy as np
from PIL import Image, ImageDraw
import world as Wo

SS = 2  # supersample


def rot(v, a):
    c, s = np.cos(a), np.sin(a); return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


def pose_points(sit, reach, low, lean, step):
    """metres, origin at the feet line under the hip, +x toward the porch (right), +y up"""
    P = {}
    hip_h = 0.93 * (1 - sit) + 0.47 * sit
    hip = np.array([0.0, hip_h])
    # torso leans forward when calling/reaching, back a little when seated
    ta = -(0.10 * lean + 0.22 * reach) + 0.05 * sit - 0.10 * low * sit
    sh = hip + rot(np.array([0, 0.55]), ta)
    head = sh + rot(np.array([0.03, 0.2]), ta * 1.3)
    # legs: standing straight, stepping swings them; seated: thigh forward, shin down
    sw = 0.35 * np.sin(step)
    th_a = (1 - sit) * (np.pi + sw * (1 - sit)) + sit * (np.pi / 2 + 0.05)   # angle from +x
    knee = hip + 0.46 * np.array([np.cos(th_a), np.sin(th_a)]) * np.array([1, 1])
    knee = hip + 0.46 * np.array([np.sin(-sw) * (1 - sit) + sit * 1.0, -np.cos(sw) * (1 - sit) + sit * 0.05])
    foot = np.array([knee[0] + 0.02 * sit - 0.1 * np.sin(sw) * (1 - sit), 0.02])
    knee2 = hip + 0.46 * np.array([np.sin(sw) * (1 - sit) + sit * 0.92, -np.cos(sw) * (1 - sit) + sit * 0.04])
    foot2 = np.array([knee2[0] - 0.04 * sit + 0.1 * np.sin(sw) * (1 - sit), 0.02])
    # arm: hanging, reaching (forward, slightly down), or offered low (forward and down, from the seat)
    a_rest = -np.pi / 2 + 0.08
    a_reach = -0.12
    a_low = -0.75
    ua = a_rest * (1 - reach) * (1 - low) + a_reach * reach + a_low * low * (1 - reach)
    el = sh + 0.31 * np.array([np.cos(ua), np.sin(ua)])
    fa = ua + (0.25 * (1 - reach) * (1 - low)) + 0.35 * low * (1 - reach)
    hand = el + 0.30 * np.array([np.cos(fa), np.sin(fa)])
    P.update(hip=hip, sh=sh, head=head, knee=knee, foot=foot, knee2=knee2, foot2=foot2, el=el, hand=hand, ta=ta)
    return P


def draw(img, x_world, sit, reach, low, lean, step, lit):
    """draw onto a PIL RGB image in place"""
    P = pose_points(sit, reach, low, lean, step)
    ox = Wo.X(x_world)
    def S(p): return ((ox + p[0] * Wo.S) * SS, (Wo.FLOOR - p[1] * Wo.S) * SS)
    x0 = int(ox - 1.2 * Wo.S); y0 = int(Wo.FLOOR - 2.1 * Wo.S)
    w, h = int(2.4 * Wo.S), int(2.2 * Wo.S)
    lay = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    def L(p): q = S(p); return (q[0] - x0 * SS, q[1] - y0 * SS)
    col = (16, 13, 16, 255)
    rim = (int(70 + 150 * lit), int(48 + 90 * lit), int(30 + 40 * lit), 255)
    def cap(a, b, r, c):
        a, b = L(a), L(b); rr = r * Wo.S * SS
        d.line([a, b], fill=c, width=int(2 * rr))
        for q in (a, b): d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=c)
    for pass_, c, grow in ((0, rim, 0.012), (1, col, 0.0)):
        off = np.array([0.012, 0.004]) if pass_ == 0 else np.array([0, 0])
        cap(P['hip'] + off, P['knee2'] + off, 0.07 + grow, c); cap(P['knee2'] + off, P['foot2'] + off, 0.055 + grow, c)
        cap(P['hip'] + off, P['knee'] + off, 0.07 + grow, c); cap(P['knee'] + off, P['foot'] + off, 0.055 + grow, c)
        # coat: from shoulders flaring to below the knees (follows the thigh when seated)
        sh, hip = P['sh'] + off, P['hip'] + off
        kn = (P['knee'] + P['knee2']) / 2 + off
        hem = hip + (kn - hip) * 1.25 + np.array([0, -0.05])
        coat = [sh + [-0.14, 0.02], sh + [0.13, 0.0], hip + [0.16, 0], hem + [0.1, -0.02 - 0.05 * (1 - sit)],
                hem + [-0.12, -0.02 - 0.05 * (1 - sit)], hip + [-0.17, 0]]
        d.polygon([L(p) for p in coat], fill=c)
        cap(P['sh'] + off, P['head'] + off + [-0.01, -0.12], 0.05 + grow, c)
        hq = L(P['head'] + off); rr = (0.105 + grow) * Wo.S * SS
        d.ellipse([hq[0] - rr * 0.92, hq[1] - rr, hq[0] + rr * 0.92, hq[1] + rr], fill=c)
        cap(P['sh'] + off, P['el'] + off, 0.05 + grow, c); cap(P['el'] + off, P['hand'] + off, 0.042 + grow, c)
        hq = L(P['hand'] + off); rr = (0.05 + grow) * Wo.S * SS
        d.ellipse([hq[0] - rr, hq[1] - rr * 0.8, hq[0] + rr, hq[1] + rr * 0.8], fill=c)
    lay = lay.resize((w, h), Image.LANCZOS)
    img.paste(lay, (x0, y0), lay)
    return {k: (Wo.X(x_world) + v[0] * Wo.S, Wo.FLOOR - v[1] * Wo.S) for k, v in P.items() if k != 'ta'}


def stool(img):
    d = ImageDraw.Draw(img)
    x = Wo.X(-1.25)
    top = Wo.FLOOR - 0.45 * Wo.S
    d.rectangle([x - 0.22 * Wo.S, top, x + 0.22 * Wo.S, top + 10], fill=(52, 36, 26))
    for dx in (-0.18, 0.15):
        d.line([(x + dx * Wo.S, top + 8), (x + dx * Wo.S * 1.1, Wo.FLOOR)], fill=(40, 28, 20), width=7)
