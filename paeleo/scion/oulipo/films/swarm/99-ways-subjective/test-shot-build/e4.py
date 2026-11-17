"""E4, the defining beat of 99-ways-subjective, PAPER HANDS direction.

Test shot = film 0:28.0-0:38.0 (local t = film t - 28; all plan timings kept exactly):
  local 0.0-1.0  hold on the stair, P3's question card still hanging at the top of the window
  local 1.0-4.0  head turn: the panorama strip (stair, banister, newel post, floor) is pulled up-right
  local 2.5-5.0  the cuffed left forearm rises from below the bottom edge (pinned at the elbow)
  local 4.5-6.0  the right hand reaches, pinches the cuff (2-bone IK, contact) and pulls it back
  local 6.25/6.5 the wrist turns through replacement drawings D1 edge-on -> D2 3/4 -> D3 face
  local 6.5-7.0  the tracing-paper dial inlay lights, 1:15; the watch tick starts
  local 8.5      own-voice card 'Quarter past one!' arrives from below the bottom edge on a damped spring

SCIONs: #2 Reiniger (pinned pieces, joint limits, replacement profiles, exposure sheet),
#33 IK (world-space pinch target on the cuff, 2-bone fingers, contact interval, world responds after contact),
#45 occlusion (DAG: hands behind screen < screen < set pieces < cards/rods < board mat; cuff is the holdout over the watch).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lightbox as lb
from lightbox import facet, dense_poly, ellipse_pts, capsule_pts, hull, xf, Card

FPS = 24
DUR = 10.0
O = np.array([70.0, 910.0])            # P4 origin on the page
PW, PH = 1530, 820                     # P4 size
CROP = (53, 880, 1564, 880)            # film camera: page rect around P4 (16:9)
DEG = math.pi / 180


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def on_twos(t):
    return math.floor(t * FPS / 2) * 2 / FPS


# ------------------------------------------------------------------ the set ---
class Strip:
    """Panorama strip (cut card) behind the window: stair, banister, newel post, floorboards.
    Defined in strip coords = P4-local coords at the start of the turn."""

    def __init__(self):
        self.pieces = []
        s = 500
        # stair body: steps descending from upper right to the newel post
        prof = [(1900, 1700), (720, 1700)]
        for i in range(8):
            x = 720 + 140 * i; y = 700 - 120 * i
            prof += [(x, y), (x + 140, y)]
        prof += [(1900, 700 - 120 * 8)]
        self.pieces.append(facet(dense_poly(prof), s)); s += 1
        rail = lambda x: 300 - 0.857 * (x - 700)
        for i in range(8):                                   # balusters
            bx = 790 + 140 * i; yt = 700 - 120 * i
            self.pieces.append(facet(dense_poly([(bx - 8, yt + 4), (bx - 8, rail(bx)), (bx + 8, rail(bx)), (bx + 8, yt + 4)]), s)); s += 1
        # handrail
        a = math.atan2(-0.857, 1)
        self.pieces.append(facet(capsule_pts((690, rail(690)), (1950, rail(1950)), 17, 17), s)); s += 1
        # newel post: turned profile from the floor to a ball finial
        post = []
        ys = np.linspace(1700, 260, 60)
        for y in ys:
            w = 38 + (16 if 260 < y < 290 else 0) + (10 if 330 < y < 350 else 0) + (6 if 520 < y < 540 else 0)
            post.append((680 + w, y))
        post += [(680 + 30, 240)]
        post += [(680 - x + 680, y) for (x, y) in reversed(post)]
        self.pieces.append(facet(dense_poly(post), s)); s += 1
        self.pieces.append(facet(dense_poly([(640, 262), (720, 262), (708, 236), (652, 236)]), s)); s += 1
        self.pieces.append(facet(ellipse_pts(680, 228, 16, 12), s)); s += 1
        # floorboard seams: thin black slits in perspective across the hall floor
        for k in range(4):
            y0 = 1010 + 300 * k; y1 = 890 + 210 * k
            self.pieces.append(facet(dense_poly([(-1100, y0 - 3), (700, y1 - 2), (700, y1 + 3), (-1100, y0 + 4)]), s, 8, 12, 0.4)); s += 1

    def offset(self, t):
        """head turn: constant velocity from 1.0 to 4.0 with a 2-frame ease at each end"""
        e = 2 / FPS; a, b = 1.0, 4.0
        T = b - a; vmax = 1 / (T - e)
        if t <= a: u = 0
        elif t < a + e: u = 0.5 * vmax * (t - a) ** 2 / e
        elif t < b - e: u = 0.5 * vmax * e + vmax * (t - a - e)
        elif t < b: u = 1 - 0.5 * vmax * (b - t) ** 2 / e
        else: u = 1
        return np.array([820.0, -700.0]) * u

    def draw(self, R, m, t):
        off = self.offset(t) + O
        for p in self.pieces:
            R.fill(m, p + off)


# ------------------------------------------------------------- left arm rig ---
ARM_L = 1012.0
X_WATCH = 935.0
CUFF0, CUFF1 = 1060.0, 790.0
T_CONTACT = 5.0
T_CUFF = T_CONTACT + 2 / FPS            # world responds 2 frames after contact
ROLLS = {'D1': 80.0, 'D2': 42.0, 'D3': 8.0}


def proj(x, y, z, phi):
    return (x, y * math.cos(phi) - z * math.sin(phi))


def wrist_W(x):  # half width / half thickness of the bare forearm
    f = clamp((x - 640) / (ARM_L - 640))
    return 150 - 56 * f, 100 - 38 * f


def forearm_drawing(phi_deg, seed):
    """replacement drawing of the bare distal forearm + strap + watch, arm frame (x from elbow)."""
    phi = phi_deg * DEG
    top, bot = [], []
    for x in np.linspace(640, ARM_L + 10, 30):
        W, T = wrist_W(min(x, ARM_L))
        e = math.hypot(W * math.cos(phi), T * math.sin(phi))
        top.append((x, -e)); bot.append((x, e))
    fore = facet(dense_poly(top + bot[::-1]), seed)
    W, T = wrist_W(X_WATCH)
    zc = T + 2
    # strap: band slightly proud of the wrist
    st = []
    for x in (X_WATCH - 52, X_WATCH + 52):
        W2, T2 = wrist_W(x)
        st.append((x, math.hypot((W2 + 4) * math.cos(phi), (T2 + 4) * math.sin(phi))))
    strap = facet(dense_poly([(st[0][0], -st[0][1]), (st[1][0], -st[1][1]), (st[1][0], st[1][1]), (st[0][0], st[0][1])]), seed + 1)
    # case: hull of both rims + lugs at 12 and 6 (12 points to -y, across the wrist; crown at 3 toward the hand)
    pts = []
    for h in (0, 22):
        for th in np.linspace(0, 2 * np.pi, 40, endpoint=False):
            pts.append(proj(X_WATCH + 92 * math.cos(th), 92 * math.sin(th), zc + h, phi))
    for sgn in (-1, 1):
        for dx in (-30, 30):
            for dy in (88, 104):
                for h in (0, 14):
                    pts.append(proj(X_WATCH + dx, sgn * dy, zc + h, phi))
    case = facet(hull(pts), seed + 2, 6, 9, 0.4)
    c0 = proj(X_WATCH + 100, 0, zc + 11, phi); c1 = proj(X_WATCH + 118, 0, zc + 11, phi)
    crown = facet(capsule_pts(c0, c1, 11, 11), seed + 3, 6, 8, 0.3)
    out = {'fore': fore, 'strap': strap, 'case': case, 'crown': crown, 'inlay': None, 'marks': [], 'centre': proj(X_WATCH, 0, zc + 23, phi)}
    if math.cos(phi) > 0.4:                               # the dial faces the eye only after the turn
        zt = zc + 22
        inl = [proj(X_WATCH + 76 * math.cos(th), 76 * math.sin(th), zt, phi) for th in np.linspace(0, 2 * np.pi, 90, endpoint=False)]
        out['inlay'] = facet(np.array(inl), seed + 4, 6, 9, 0.25)
        TW = 16 * DEG   # the watch sits turned a little on its strap, as worn
        U = lambda a, r: proj(X_WATCH + r * math.sin(a + TW), -r * math.cos(a + TW), zt + 1, phi)   # clock angle a from 12
        marks = []
        for k in range(12):
            a = k * 30 * DEG
            if k % 3 == 0:
                w = 9 if k else 0
                if k == 0:   # 12: a bold double slot
                    for dd in (-2.6 * DEG, 2.6 * DEG):
                        marks.append(capsule_pts(U(dd * 2.2, 74), U(dd * 2.2, 50), 4, 4, 6))
                else:
                    marks.append(capsule_pts(U(a, 72), U(a, 54), 5, 5, 6))
            else:
                c = U(a, 66); marks.append(ellipse_pts(c[0], c[1], 3.5, 3.5 * max(math.cos(phi), .3), n=10))
        hour = (1 + 15 / 60) * 30 * DEG      # 1:15
        minute = 15 * 6 * DEG
        marks.append(capsule_pts(U(hour + math.pi, 10), U(hour, 42), 7, 4.5, 8))
        marks.append(capsule_pts(U(minute + math.pi, 12), U(minute, 64), 5, 3, 8))
        out['marks'] = [facet(m, seed + 10 + i, 3, 5, 0.15) for i, m in enumerate(marks)]
    return out


def lefthand_drawing(phi_deg, seed):
    """replacement drawing of the relaxed left hand (palm down at phi=0), hand frame at the wrist pin.
    One 3-D hand model, rolled and projected: D1, D2, D3 are the same hand turned."""
    phi = phi_deg * DEG
    pieces, pins = [], []
    box = []
    for x, hw, hz in ((0, 86, 30), (60, 100, 34), (150, 108, 32), (192, 100, 26)):
        for a in np.linspace(0, 2 * np.pi, 16, endpoint=False):
            box.append(proj(x, hw * math.cos(a), hz * math.sin(a), phi))
    pieces.append(facet(hull(box), seed))
    fingers = [(84, 8, 96, 80, 22, 18), (28, 2, 106, 88, 23, 19), (-28, -4, 100, 82, 22, 18), (-82, -11, 80, 66, 19, 15)]
    for i, (y0, spr, l1, l2, r0, r1) in enumerate(fingers):
        p1, p2 = 18 + 4 * i, 52 + 6 * i
        p1, p2 = p1 * DEG, p2 * DEG
        s = spr * DEG
        root = np.array([188, y0, 6.0])
        d1 = np.array([math.cos(p1) * math.cos(s), math.cos(p1) * math.sin(s), -math.sin(p1)])
        d2 = np.array([math.cos(p2) * math.cos(s), math.cos(p2) * math.sin(s), -math.sin(p2)])
        j = root + d1 * l1; tip = j + d2 * l2
        P = [proj(*v, phi) for v in (root, j, tip)]
        pieces.append(facet(capsule_pts(P[0], P[1], r0, r0 - 2), seed + 10 + i))
        pieces.append(facet(capsule_pts(P[1], P[2], r0 - 3, r1), seed + 20 + i))
        pins.append(P[0]); pins.append(P[1])
    th = [np.array(v, float) for v in ((30, 96, -22), (96, 142, -30), (152, 170, -24), (200, 182, -16))]
    rr = [29, 26, 23, 20]
    T = [proj(*v, phi) for v in th]
    for k in range(3):
        pieces.append(facet(capsule_pts(T[k], T[k + 1], rr[k], rr[k + 1]), seed + 30 + k))
        pins.append(T[k + 1])
    return pieces, pins


class LeftArm:
    def __init__(self):
        self.fd = {k: forearm_drawing(v, 100 + i * 50) for i, (k, v) in enumerate(ROLLS.items())}
        self.hd = {k: lefthand_drawing(v, 400 + i * 50) for i, (k, v) in enumerate(ROLLS.items())}
        # sleeve: one long faceted piece, cut (holdout) under the cuff
        top = [(x, -(186 - 22 * (x + 400) / 1500)) for x in np.linspace(-600, 1100, 40)]
        bot = [(x, (186 - 22 * (x + 400) / 1500)) for x in np.linspace(-600, 1100, 40)]
        self.sleeve = facet(dense_poly(top + bot[::-1]), 700)
        # cuff (local origin at its distal edge): band with rounded distal corners, placket step, punched button
        c = [(-135, -176), (-12, -176), (0, -150), (2, 150), (-10, 174), (-135, 174)]
        self.cuff = facet(dense_poly(c), 701)
        self.placket = facet(dense_poly([(-70, -186), (-4, -184), (-2, -150), (-70, -150)]), 702)
        self.button = ellipse_pts(-48, -118, 11, 11, n=16)
        self.folds = [facet(ellipse_pts(-185, 178, 40, 14), 703), facet(ellipse_pts(-215, -182, 46, 13), 704),
                      facet(ellipse_pts(-300, 186, 44, 12), 705)]

    def pose(self, t):
        u = ease((t - 2.5) / 2.3)
        u = 1 - (1 - clamp((t - 2.5) / 2.3)) ** 3 if t < 4.8 else 1.0   # rise: fast out of the bottom, slowing
        E0, E1 = np.array([-260.0, 1180.0]), np.array([-330.0, 700.0])
        a0, a1 = -4 * DEG, -20 * DEG
        settle = 0.0
        if 4.2 < t < 5.4:                                    # weight: a small overshoot and settle
            settle = -2.2 * DEG * math.sin(math.pi * (t - 4.2) / 1.2) * math.exp(-(t - 4.2) * 1.5)
        E = E0 + (E1 - E0) * u
        ang = a0 + (a1 - a0) * u + settle
        # pull reaction: the arm resists slightly while the cuff is pulled
        if T_CUFF < t < 6.0:
            ang += 0.6 * DEG * math.sin(math.pi * (t - T_CUFF) / (6.0 - T_CUFF))
        # roll drawing (replacement profile, swapped on frame boundaries only)
        k = int(round(t * FPS))
        if k < int(6.25 * FPS): dr = 'D1'
        elif k < int(6.5 * FPS): dr = 'D2'
        else: dr = 'D3'
        flex = 6 * DEG
        if 6.0 <= t < 6.25: flex = (6 - 9 * math.sin(math.pi * (t - 6.0) / 0.25)) * DEG   # anticipation dip before the turn
        if t >= 6.5: flex = 10 * DEG
        # cuff slide (responds after contact)
        p = ease((t - T_CUFF) / (5.85 - T_CUFF)) if t >= T_CUFF else 0.0
        xc = CUFF0 + (CUFF1 - CUFF0) * p
        lift = clamp(1 - (t - 4.6) / 0.5) if t >= 2.5 else 1.0
        if 6.0 <= t < 6.9: lift = max(lift, 0.35 * math.sin(math.pi * (t - 6.0) / 0.9))
        return dict(E=E, ang=ang, dr=dr, flex=flex, xc=xc, pull=p, lift=lift)

    def frame_pts(self, P):
        E, a = P['E'], P['ang']
        return lambda pts: xf(pts, a, E)

    def pinch_target(self, P):
        d = np.array([math.cos(P['ang']), math.sin(P['ang'])]); rn = np.array([-d[1], d[0]])
        return P['E'] + d * (P['xc'] - 35) + rn * 166

    def draw(self, R, P):
        """returns D (dark), inlay mask, pins, log info. All coordinates P4-local + O."""
        A = lambda pts: xf(pts, P['ang'], P['E']) + O
        fd = self.fd[P['dr']]; hp, hpins = self.hd[P['dr']]
        D = R.blank(); inl = R.blank()
        R.fill(D, A(fd['fore'])); R.fill(D, A(fd['strap'])); R.fill(D, A(fd['case'])); R.fill(D, A(fd['crown']))
        d = np.array([math.cos(P['ang']), math.sin(P['ang'])])
        wrist = P['E'] + d * ARM_L                                # forearm's distal pin
        ha = P['ang'] + P['flex']
        hand_origin = xf(np.array([[0.0, 0.0]]), ha, wrist)[0]    # hand piece's pivot
        for pc in hp:
            R.fill(D, xf(pc, ha, wrist) + O)
        level = 0.0
        if fd['inlay'] is not None:
            a = R.fill(inl, A(fd['inlay']))
            D *= (1 - inl)
            for mk in fd['marks']:
                b = R.fill(D, A(mk)); inl *= (1 - b)
        # sleeve + cuff (the holdout over the watch)
        cover = R.blank()
        xc = P['xc']
        sl = R.blank(); R.fill(sl, A(self.sleeve))
        cutpoly = np.array([[xc - 90, -400], [xc + 2000, -400], [xc + 2000, 400], [xc - 90, 400]])
        cut = R.blank(); R.fill(cut, A(cutpoly)); sl *= (1 - cut)
        cover = np.maximum(cover, sl)
        cuffT = lambda pts: A(np.asarray(pts) + [xc, 0])
        R.fill(cover, cuffT(self.cuff)); R.fill(cover, cuffT(self.placket))
        for i, th in enumerate((0.3, 0.6, 0.85)):
            if P['pull'] >= th:
                R.fill(cover, cuffT(self.folds[i]))
        R.fill(cover, cuffT(self.button), 0.0)                    # punched buttonhole: light through it
        D = np.maximum(D * (1 - cover), cover)
        inl *= (1 - cover)
        # pins: wrist pin + finger pins (visible where not under the cuff), watch centre pin
        pins = []
        def vis(pt):
            x, y = int(pt[0] - R.x0), int(pt[1] - R.y0)
            if 0 <= x < R.w and 0 <= y < R.h:
                return float(1 - cover[y, x] * (1 - 0)) if cover[y, x] > 0.5 and False else float(cover[y, x] < 0.5)
            return 0.0
        wp = wrist + O
        pins.append((wp, 5, vis(wp)))
        if P['dr'] == 'D3':
            for pp in hpins[0:8:2]:
                g = xf(np.array([pp]), ha, wrist)[0] + O
                pins.append((g, 4, vis(g)))
        if fd['inlay'] is not None:
            g = A(np.array([fd['centre']]))[0]
            pins.append((g, 5, vis(g)))
        info = dict(pin_residual=float(np.linalg.norm(hand_origin - wrist)), wrist_flex_deg=P['flex'] / DEG,
                    flex_ok=bool(-25 <= P['flex'] / DEG <= 35))
        return D, inl, pins, info


# ------------------------------------------------------------ right hand rig ---
def ik2(root, target, l1, l2, bend):
    v = target - root; d = np.linalg.norm(v)
    dc = clamp(d, abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    base = math.atan2(v[1], v[0])
    c = clamp((l1 * l1 + dc * dc - l2 * l2) / (2 * l1 * dc), -1, 1)
    a1 = base - bend * math.acos(c)
    j = root + l1 * np.array([math.cos(a1), math.sin(a1)])
    a2 = math.atan2(target[1] - j[1], target[0] - j[0])
    end = j + l2 * np.array([math.cos(a2), math.sin(a2)])
    return j, end, a1, a2


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


class RightHand:
    PINCH = np.array([288.0, -92.0])
    IDX_ROOT = np.array([178.0, -76.0]); IDX_L = (96.0, 82.0)
    TH_CMC = np.array([30.0, -92.0]); TH_MCP = np.array([100.0, -140.0]); TH_L = (105.0, 95.0)
    LIMITS = {'idx_mcp': (-35, 90), 'idx_pip': (0, 110), 'th_mcp': (-70, 45), 'th_ip': (-10, 85)}

    def __init__(self):
        s = 900
        self.palm = facet(dense_poly([(0, -92), (60, -112), (176, -104), (192, -60), (194, 40), (182, 96), (60, 104), (0, 88)]), s)
        self.curled = []
        for i, (y, l, r) in enumerate(((-20, 64, 20), (34, 58, 19), (86, 46, 16))):
            j = (184 + l, y + 6)
            self.curled.append(facet(capsule_pts((184, y), j, r, r - 1), s + 10 + i))
            self.curled.append(facet(capsule_pts(j, (j[0] + 16, j[1] + 7), r - 2, r - 3), s + 20 + i))
        self.th_meta = facet(capsule_pts(self.TH_CMC, self.TH_MCP, 28, 25), s + 30)
        # rigid finger segment pieces (local: from pivot along +x)
        self.idx1 = facet(capsule_pts((0, 0), (self.IDX_L[0], 0), 21, 19), s + 40)
        self.idx2 = facet(capsule_pts((0, 0), (self.IDX_L[1], 0), 18, 15), s + 41)
        self.th1 = facet(capsule_pts((0, 0), (self.TH_L[0], 0), 24, 21), s + 42)
        self.th2 = facet(capsule_pts((0, 0), (self.TH_L[1], 0), 20, 17), s + 43)
        self.fore = facet(capsule_pts((0, 0), (-1000, 0), 92, 130), s + 50)
        self.sleeve = facet(dense_poly([(-300, -168), (-1400, -180), (-1400, 180), (-300, 168)]), s + 51)
        self.cuff = facet(dense_poly([(-290, -160), (-410, -164), (-410, 164), (-290, 160)]), s + 52)

    def pose(self, t, target):
        """target: world pinch point on the cuff (moves with the cuff)."""
        if t < 4.5:
            return None
        h = (-112 + (-118 + 112) * ease((t - 4.5) / 0.5)) * DEG
        if t > T_CONTACT:
            h += (-10 * ease((t - T_CONTACT) / 0.9)) * DEG
        R = np.array([[math.cos(h), -math.sin(h)], [math.sin(h), math.cos(h)]])
        wrist = target - R @ self.PINCH
        e = ease((t - 4.5) / 0.42)
        wrist = wrist + np.array([240.0, 560.0]) * (1 - e) ** 1.5
        close = ease((t - 4.80) / (T_CONTACT - 4.80))
        idx_loc = self.PINCH * close + np.array([306.0, -38.0]) * (1 - close)
        th_loc = (self.PINCH + [-4, -12]) * close + np.array([252.0, -168.0]) * (1 - close)
        if t >= T_CONTACT:      # contact interval: tips locked to the world target
            idx_w = target; th_w = target + R @ np.array([-4.0, -12.0])
        else:
            idx_w = wrist + R @ idx_loc; th_w = wrist + R @ th_loc
        lift = clamp(1 - (t - 4.5) / 0.5) * 0.8 + 0.15
        return dict(h=h, R=R, wrist=wrist, idx_w=idx_w, th_w=th_w, lift=lift, contact=t >= T_CONTACT)

    def draw(self, R_, P, target):
        D = R_.blank()
        if P is None:
            return D, [], {}
        h, Rm, W = P['h'], P['R'], P['wrist']
        L = lambda pts: (np.asarray(pts) @ Rm.T) + W + O
        R_.fill(D, L(self.sleeve)); R_.fill(D, L(self.cuff)); R_.fill(D, L(self.fore))
        R_.fill(D, L(self.palm))
        for c in self.curled: R_.fill(D, L(c))
        R_.fill(D, L(self.th_meta))
        ir = W + Rm @ self.IDX_ROOT
        j, end, a1, a2 = ik2(ir, P['idx_w'], *self.IDX_L, bend=-1)
        R_.fill(D, xf(self.idx1, a1, ir) + O); R_.fill(D, xf(self.idx2, a2, j) + O)
        tr = W + Rm @ self.TH_MCP
        tj, tend, b1, b2 = ik2(tr, P['th_w'], *self.TH_L, bend=1)
        R_.fill(D, xf(self.th1, b1, tr) + O); R_.fill(D, xf(self.th2, b2, tj) + O)
        meta_a = math.atan2(*(self.TH_MCP - self.TH_CMC)[::-1]) + h
        ang = {'idx_mcp': wrap(a1 - h) / DEG, 'idx_pip': wrap(a2 - a1) / DEG * -1,
               'th_mcp': wrap(b1 - meta_a) / DEG, 'th_ip': wrap(b2 - b1) / DEG}
        ok = {k: bool(self.LIMITS[k][0] - 0.01 <= v <= self.LIMITS[k][1] + 0.01) for k, v in ang.items()}
        pins = [(W + O, 5, 1.0), (ir + O, 4, 1.0), (j + O, 4, 1.0), (tr + O, 4, 1.0), (tj + O, 4, 1.0)]
        info = dict(idx_residual=float(np.linalg.norm(end - P['idx_w'])), th_residual=float(np.linalg.norm(tend - P['th_w'])),
                    idx_to_target=float(np.linalg.norm(end - target)), contact=bool(P['contact']), joint_deg=ang, limits_ok=ok)
        return D, pins, info


# ---------------------------------------------------------------- cards ---
Q_CARD = Card('What time\nis it?', 50, tail_vec=(-400, -250), seed=31, rod_vec=(0, -1))
A_CARD = Card('Quarter\npast one!', 52, tail_vec=(60, 700), seed=37, rod_vec=(0, 1))
Q_C0 = np.array([330.0, 178.0])
A_C1 = np.array([1235.0, 170.0])


def q_card_pos(t, strip):
    tt = on_twos(t)
    sway = 5 * math.exp(-1.2 * tt) * math.sin(2 * math.pi * 1.1 * tt)
    return Q_C0 + strip.offset(t) + np.array([sway, 0])


def a_card_pos(t):
    if t < 8.2:
        return None
    tau = t - 8.2
    y = 830 * math.exp(-3.6 * tau) * math.cos(5.2 * tau)
    if tau > 1.2:
        tau2 = on_twos(t) - 8.2
        y = 830 * math.exp(-3.6 * tau2) * math.cos(5.2 * tau2)
    return A_C1 + np.array([0, y])


# ---------------------------------------------------------------- frame ---
class Shot:
    def __init__(self, page):
        self.page = page
        self.strip = Strip()
        self.left = LeftArm()
        self.right = RightHand()
        self.log = []

    def render(self, t, rect=CROP, page_mode=False):
        R = lb.Raster(*rect)
        x0, y0, w, h = rect
        paper = self.page[y0:y0 + h, x0:x0 + w].copy()
        board = np.ones((h, w), np.float32)
        for k, (a, b, c, d) in lb.PANELS.items():
            bx0, by0, bx1, by1 = max(a - x0, 0), max(b - y0, 0), min(c - x0, w), min(d - y0, h)
            if bx1 > bx0 and by1 > by0:
                board[by0:by1, bx0:bx1] = 0
        setd = R.blank(); self.strip.draw(R, setd, t)
        PL = self.left.pose(t)
        DL, inl, pinsL, infoL = self.left.draw(R, PL)
        tgt = self.left.pinch_target(PL)
        PR = self.right.pose(t, tgt)
        DR, pinsR, infoR = self.right.draw(R, PR, tgt)
        inl *= (1 - DR)
        # inlay light: D2 dim (oblique), D3 rising to full on twos
        level = 0.0
        if PL['dr'] == 'D2': level = 0.55
        if PL['dr'] == 'D3': level = 0.72 + 0.28 * ease((on_twos(t) - 6.5) / 0.5)
        lift_l, lift_r = PL['lift'], (PR['lift'] if PR else 0)
        groups = [(DL, 1.6 + 2.6 * lift_l, (4 + 6 * lift_l, 3 + 5 * lift_l), 0.42),
                  (DR, 1.6 + 2.6 * lift_r, (4 + 6 * lift_r, 3 + 5 * lift_r), 0.42)]
        cards = []
        qp = q_card_pos(t, self.strip)
        if qp[1] > -400 and not page_mode:
            dk, vl, ik = R.blank(), R.blank(), R.blank()
            Q_CARD.draw(R, dk, vl, ik, qp + O); cards.append((dk, vl, ik))
        ap = a_card_pos(t)
        if ap is not None:
            dk, vl, ik = R.blank(), R.blank(), R.blank()
            A_CARD.draw(R, dk, vl, ik, ap + O); cards.append((dk, vl, ik))
        pins = pinsL + pinsR
        # pins under the right hand are hidden
        pins2 = []
        for i, (c, r, v) in enumerate(pins):
            x, y = int(c[0] - x0), int(c[1] - y0)
            if i < len(pinsL) and 0 <= x < w and 0 <= y < h and DR[y, x] > 0.5:
                v = 0.0
            pins2.append((c, r, v))
        rgb = lb.composite(R, paper, groups, setd, cards, board, inlay=(inl, level, 1.6 + 2.6 * lift_l * 0.5), pins=pins2)
        # per-frame visibility / puppet log
        dial_area = float(inl.sum())
        self.log.append(dict(t=round(t, 4), frame=int(round(t * FPS)), drawing=PL['dr'], dial_area_px=round(dial_area, 1),
                             dial_level=round(level, 3), cuff_x=round(PL['xc'], 2), **infoL,
                             right=infoR, strip_offset=[round(v, 2) for v in self.strip.offset(t)],
                             layer_order=['lamp', 'hand.L(behind screen)', 'hand.R(behind screen)', 'paper', 'set.strip', 'cards+rods', 'board']))
        return np.clip(rgb, 0, 255).astype(np.uint8)
