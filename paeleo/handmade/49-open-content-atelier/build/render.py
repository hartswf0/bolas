"""Open-Content Atelier, PAE-02: render the 32 s threshold scene from cut CC0 museum parts, following the score.
Reads build/cache/parts/ (from parts.py) and paeleo/handmade/score/threshold-score.json.
Writes build/cache/frames/f_0000.jpg … f_0767.jpg (1280x720) and build/cache/measure.json (per-frame measurements
taken from the rendered dog layer: body-layer centroid, head pivots, mask top, etc.).
Usage: python3 render.py [first last]   (renders a frame range; default all)

Stage (a museum period-room cutaway): the house is cut in section. World x in metres along the porch (score units):
threshold x=0, room x < -0.30, wall/door frame -0.30..+0.30 under a lintel at 2.1 m, threshold stone out to the sill 0.56,
porch boards beyond. Screen: X = 330 + 200 x, feet line Y = 650, then a camera (static, then a push-in from 21 s)."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PD = os.path.join(HERE, 'cache', 'parts'); FD = os.path.join(HERE, 'cache', 'frames'); os.makedirs(FD, exist_ok=True)
SCORE = json.load(open(os.path.join(HERE, '..', '..', 'score', 'threshold-score.json')))
FR = SCORE['frames']; FPS = 24; N = len(FR)
W, H = 1280, 720
S, X0, FEET = 185.0, 340.0, 650.0
WALL_IN, WALL_OUT, SILL, LINTEL = 0.02, 0.46, 0.56, 2.10
META = json.load(open(os.path.join(PD, 'parts.json')))

# ---------------------------------------------------------------- helpers: affine algebra
def T(x, y): return np.array([[1, 0, x], [0, 1, y], [0, 0, 1.]])
def R(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg)); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.]])
def Sc(sx, sy=None): return np.array([[sx, 0, 0], [0, sx if sy is None else sy, 0], [0, 0, 1.]])
def ap(M, p): v = M @ np.array([p[0], p[1], 1.]); return (v[0], v[1])
def ease(u): u = min(max(u, 0.), 1.); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u


class Part:
    """A cut piece: RGBA, pre-scaled by `pre` (so later transforms are mostly downscales); pivots in source px."""
    def __init__(self, name, pre, tint=None):
        m = META[name]; self.name = name
        rgb = Image.open(os.path.join(PD, name + '.jpg')).convert('RGB')
        a = Image.open(os.path.join(PD, name + '_a.jpg')).convert('L')
        if tint is not None:
            arr = np.asarray(rgb).astype(float) * np.array(tint)[None, None]; rgb = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        im = rgb.copy(); im.putalpha(a)
        w, h = im.size; self.pre = pre
        self.im = im.resize((max(1, round(w * pre)), max(1, round(h * pre))), Image.LANCZOS)
        self.ox, self.oy = m['bbox_in_source'][0], m['bbox_in_source'][1]
        self.piv = {k: (v[0] + self.ox, v[1] + self.oy) for k, v in m.get('pivots', {}).items()}
    def src_to_img(self):  # source px -> pre-scaled image px
        return Sc(self.pre) @ T(-self.ox, -self.oy)


def draw(canvas, part, M, alpha=1.0, mult=None):
    """Composite `part` onto RGBA `canvas` with M: source px -> canvas px (3x3)."""
    A = M @ np.linalg.inv(part.src_to_img())          # image px -> canvas px
    w, h = part.im.size
    cs = np.array([ap(A, p) for p in [(0, 0), (w, 0), (0, h), (w, h)]])
    x0, y0 = np.floor(cs.min(0)).astype(int); x1, y1 = np.ceil(cs.max(0)).astype(int) + 1
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, canvas.size[0]), min(y1, canvas.size[1])
    if x1 <= x0 or y1 <= y0: return
    Ai = np.linalg.inv(T(-x0, -y0) @ A)
    out = part.im.transform((x1 - x0, y1 - y0), Image.AFFINE, data=tuple(Ai[:2].reshape(-1)), resample=Image.BICUBIC)
    if mult is not None or alpha < 1:
        arr = np.asarray(out).astype(float)
        if mult is not None: arr[..., :3] *= np.array(mult)[None, None]
        arr[..., 3] *= alpha; out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    canvas.alpha_composite(out, (x0, y0))


# ---------------------------------------------------------------- the score, smoothed
def sc(i, key, default=0.0):
    a = FR[min(max(i, 0), N - 1)]['dog']['act']; return a.get(key, default)
def scx(i): return FR[min(max(i, 0), N - 1)]['dog']['x']
def per(i, key): return FR[min(max(i, 0), N - 1)]['person'][key]


def door_angle(t):  # degrees open (0 closed): ajar until 6.2 s, swings open by 6.9 s
    return lerp(24, 84, ease((t - 6.2) / 0.7))
def openness(t): return (math.sin(math.radians(door_angle(t))) - 0.25) / (math.sin(math.radians(84)) - 0.25) * 0.8 + 0.2


def camera(t):
    u = ease((t - 21.0) / 3.3)
    z = lerp(1.0, 1.32, u); cx = lerp(640, 330, u); cy = lerp(360, 455, u)
    return T(640, 360) @ Sc(z) @ T(-cx, -cy), z


def wx(x): return X0 + S * x


# ---------------------------------------------------------------- dog choreography (built on the score, plus atelier choices)
T_TURN_A = (3.45, 3.95)     # refusal turn: back shown by 3.95 s
T_LOOKBACK = 7.4583         # head leads: the look-back head arrives on the score's choice frame
T_RISE = 7.80               # Juno -> standing puppet substitution while rising
T_TURN_B = (7.95, 8.45)     # body comes round after the head


def dog_turn(t):
    if t < T_TURN_A[0]: return 1.0
    if t < T_TURN_A[1]: return math.cos(math.pi * ease((t - T_TURN_A[0]) / (T_TURN_A[1] - T_TURN_A[0])))
    if t < T_TURN_B[0]: return -1.0
    if t < T_TURN_B[1]: return -math.cos(math.pi * ease((t - T_TURN_B[0]) / (T_TURN_B[1] - T_TURN_B[0])))
    return 1.0


def dog_lie(i, t):
    if 4.0 <= t < 7.46: return min(1., (t - 4.0) / 0.7)                    # refusal: lies down, back to the door
    if 7.46 <= t < 8.2: return max(0., 1 - (t - 7.62) / 0.45)
    if t >= 23.62: return min(1., (t - 23.62) / 0.6)                        # the sill: 15 frames down
    return 0.0


# precompute walking distance (forward = toward the door when facing it) for the gait phase
XS = np.array([scx(i) for i in range(N)])
DIST = np.concatenate([[0], np.cumsum(-(XS[1:] - XS[:-1]))])   # metres travelled toward the door (negative = backing)
SPEED = np.abs(np.gradient(XS)) * FPS


class Dog:
    """One dog: every pose is the Woodcock Shooting pointer's own cuts, hinged differently (no other print's dog)."""
    def __init__(self):
        self.k_w = S * 1.05 / 398
        pw = self.k_w * 1.4
        self.head = Part('w_head', pw); self.torso = Part('w_torso', pw); self.tail = Part('w_tail', pw)
        self.fore = Part('w_fore', pw); self.fore_far = Part('w_fore', pw, tint=(.62, .6, .6))
        self.thigh = Part('w_thigh', pw); self.shank = Part('w_shank', pw)
        self.thigh_far = Part('w_thigh', pw, tint=(.62, .6, .6)); self.shank_far = Part('w_shank', pw, tint=(.62, .6, .6))
        self.back = Part('w_back', pw); self.nape = Part('w_nape', pw)
        self.C_W = (792, 886)
        self.HIP = (885, 808)

    # ---- gait: foot target (local Woodcock px) for a leg with phase offset
    def foot(self, i, offset, u_neutral, t, liftmax):
        Ls = 0.28 * S / self.k_w; duty = .62; A = duty * Ls
        ph = DIST[i] / 0.28 + offset; u = ph - math.floor(ph)
        mv = min(1.0, SPEED[i] / 0.12)
        if u < duty: off = A / 2 - u / duty * A; lift = 0
        else:
            v = (u - duty) / (1 - duty); off = -A / 2 + ease(v) * A; lift = liftmax * math.sin(math.pi * v) * mv
        return (u_neutral - off, 886 - lift)

    def leg(self, part, top_local, foot0, top_src, F, Mt_local_to_screen):
        L0 = math.dist(top_src, foot0)
        P = top_local
        a0 = math.atan2(foot0[1] - top_src[1], foot0[0] - top_src[0])
        a1 = math.atan2(F[1] - P[1], F[0] - P[0])
        s = max(0.82, min(1.12, math.dist(P, F) / L0))
        ax = np.array([math.cos(a1), math.sin(a1)])
        Sm = np.eye(3); Sm[:2, :2] += (s - 1) * np.outer(ax, ax)
        M = T(*P) @ Sm @ R(math.degrees(a1 - a0)) @ T(-top_src[0], -top_src[1])
        return Mt_local_to_screen @ M

    def render(self, i, t, cam):
        """Returns (body_layer, head_layer, info)."""
        body = Image.new('RGBA', (W, H), (0, 0, 0, 0)); headL = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        x = scx(i); turn = dog_turn(t); lie = dog_lie(i, t)
        crouch = sc(i, 'crouch'); headp = sc(i, 'head'); tail = sc(i, 'tail'); wag = sc(i, 'wag'); rest = sc(i, 'rest')
        look = sc(i, 'look')
        info = {'x_score': x, 'turn': turn, 'lie': lie, 'model': 'woodcock'}
        f = 1 if turn >= 0 else -1
        Xc = wx(x)
        hs = 0.85 + 0.15 * abs(turn)           # never more than 15 % horizontal squash
        pl = ease(lie)                                 # folding toward lying (haunches lead)
        approach = 14.7 <= t < 23.6
        drop = 10 * crouch * (1 - pl) + 54 * pl
        haunch = 9 * math.sin(math.pi * pl) if lie < 0.999 else 0.0   # the rear goes down first
        pitch = ((6 if approach else 0) - 3 * crouch * (0 if approach else 1)) * (1 - pl) - haunch
        bob = 1.5 * math.sin(2 * math.pi * DIST[i] / 0.17) * min(1, SPEED[i] / .12)
        Mw0 = T(Xc, FEET) @ Sc(f * hs * self.k_w, self.k_w) @ T(-self.C_W[0], -self.C_W[1]); Mw = cam @ Mw0
        Mt = T(0, drop + bob) @ T(792, 800) @ R(-pitch) @ T(-792, -800)
        sh = self.torso.piv['shoulder']; hip = self.HIP
        legs = []
        for far, off, un in ((True, .5, 945), (True, .75, 668), (False, 0., 945), (False, .25, 668)):
            hindleg = un > 800
            F = self.foot(i, off, un + (8 if far else 0), t, 26 if hindleg else 20)
            top = hip if hindleg else sh
            P = ap(Mt, top)
            if not hindleg:
                if pl > 0:   # forelegs reach forward along the floor (sphinx)
                    L0 = 80; dv = max(0., min(L0, 886 - P[1]))
                    fold = (P[0] - math.sqrt(max(L0 ** 2 - dv ** 2, 0)) - (6 if far else 0), 886)
                    F = (lerp(F[0], fold[0], pl), lerp(F[1], fold[1], pl))
                part = self.fore_far if far else self.fore
                legs.append((far, [(part, self.leg(part, P, (652, 884), (690, 812), F, Mw))]))
            else:
                th_, sk_ = (self.thigh_far, self.shank_far) if far else (self.thigh, self.shank)
                A_, B_ = 102.0, 52.0
                d = max(abs(A_ - B_) + 1, min(A_ + B_ - 1, math.dist(P, F)))
                base = math.atan2(F[1] - P[1], F[0] - P[0])
                al = math.acos(max(-1, min(1, (A_ ** 2 + d ** 2 - B_ ** 2) / (2 * A_ * d))))
                c1 = base - al; c2 = base + al
                Hc1 = (P[0] + A_ * math.cos(c1), P[1] + A_ * math.sin(c1)); Hc2 = (P[0] + A_ * math.cos(c2), P[1] + A_ * math.sin(c2))
                Hk = Hc1 if Hc1[0] > Hc2[0] else Hc2
                a_th = math.atan2(Hk[1] - P[1], Hk[0] - P[0]); a_sk = math.atan2(F[1] - Hk[1], F[0] - Hk[0])
                if pl > 0:   # folded: thigh forward along the belly, shank back along the floor
                    tth = math.radians(172 - (8 if far else 0)); hk2 = (P[0] + A_ * math.cos(tth), P[1] + A_ * math.sin(tth))
                    tsk = math.atan2(886 - hk2[1], math.sqrt(max(B_ ** 2 - (886 - hk2[1]) ** 2, 1)))
                    def blend(a1, a2, u):   # linear in angle: the leg swings down through the floor side, never over the back
                        a1 = (a1 + math.pi) % (2 * math.pi) - math.pi; return a1 + (a2 - a1) * u
                    a_th = blend(a_th, tth, pl); Hk = (P[0] + A_ * math.cos(a_th), P[1] + A_ * math.sin(a_th))
                    a_sk = blend(a_sk, tsk, pl)
                # keep the leg on or above the floor while it folds
                if Hk[1] > 880:
                    dy = 880 - P[1]; cx_ = math.cos(a_th); a_th = math.atan2(dy, math.copysign(math.sqrt(max(A_ ** 2 - dy ** 2, 1)), cx_ if abs(cx_) > 1e-3 else -1))
                    Hk = (P[0] + A_ * math.cos(a_th), P[1] + A_ * math.sin(a_th))
                if Hk[1] + B_ * math.sin(a_sk) > 888:
                    dy = 888 - Hk[1]; cx_ = math.cos(a_sk); a_sk = math.atan2(dy, math.copysign(math.sqrt(max(B_ ** 2 - dy ** 2, 1)), cx_ if abs(cx_) > 1e-3 else 1))
                a_th0 = math.atan2(838 - 800, 990 - 895); a_sk0 = math.atan2(888 - 838, 1006 - 990)
                M1 = Mw @ T(*P) @ R(math.degrees(a_th - a_th0)) @ T(-895, -800)
                M2 = Mw @ T(*Hk) @ R(math.degrees(a_sk - a_sk0)) @ T(-990, -838)
                legs.append((far, [(th_, M1), (sk_, M2)]))
                if not far:
                    info['hind_paw'] = ap(M2, (1006, 888)); info['hind_target'] = ap(Mw, F); info['hind_reach_ok'] = abs(math.dist(P, F) - d) < 0.5
        for far, pcs in legs:
            if far:
                for part, M in pcs: draw(body, part, M)
        draw(body, self.torso, Mw @ Mt)
        # tail: lowered to lie along the floor when the dog lies
        rt = self.tail.piv['root']
        ta = (tail - 0.5) * 48 + wag * 16 * math.sin(2 * math.pi * 2.6 * t)
        ta = lerp(ta, 34 + wag * 6 * math.sin(2 * math.pi * 2.6 * t), pl)
        draw(body, self.tail, Mw @ Mt @ T(*rt) @ R(ta) @ T(-rt[0], -rt[1]))
        for far, pcs in legs:
            if not far:
                for part, M in pcs: draw(body, part, M)
        # head (always the same pointer's head)
        nk = self.torso.piv['neck']
        ha = -40 + 60 * headp
        if approach: ha -= 4
        drop_head = (12 if approach else 0) + 8 * crouch * (1 - pl)
        rs = ease(rest) * pl
        ha = lerp(ha, -34, rs); drop_head += 22 * rs; fwd = -14 * rs          # chin down toward the paws
        # head turn: hx = +1 head along the body, -1 head looking back over the shoulder
        hx = hs
        if T_LOOKBACK - 0.0833 <= t < T_TURN_B[1] and f < 0:
            u = min(1., (t - (T_LOOKBACK - 0.0833)) / 0.1667)
            c = math.cos(math.pi * u); hx = (1 if u < 0.5 else -1) * max(abs(c), 0.35) * hs
        elif t >= T_TURN_B[1] or turn >= 0: hx = hs
        # looking in: the head turns away from us into the room (profile narrows, then the back of the head)
        # looking in: the head turns away from us into the room: profile narrows (3 in-betweens), then the back of the head
        # widens (3 in-betweens); the reverse from 28.04 s
        if pl > 0.5 and 26.42 <= t < 28.29:
            u = min(1., (t - 26.42) / 0.25) if t < 28.04 else max(0., 1 - (t - 28.04) / 0.25)
        else:
            u = 0.0
        view = 'profile'
        local_mirror = 1 if hx > 0 else -1
        base_local = T(nk[0] + fwd - 20 * min(1., 2 * u), nk[1] + drop_head)
        if u > 0 or local_mirror < 0:
            # the neck: nape fur of the same dog, joining a turned head to the torso (shadow side when looking in)
            nm = lerp(.95, .5, min(1., 2 * u)) if u > 0 else .95
            Mn = Mw @ Mt @ (base_local if u > 0 else T(nk[0], nk[1] + drop_head)) @ T(-10 if u > 0 else -4, 4) @ Sc(0.95, 1.0) @ T(-690, -768)
            draw(headL, self.nape, Mn, mult=(nm, nm * .97, nm * .95))
        if u > 0.5:
            view = 'back'
            sbx = lerp(0.3, 1.0, (u - 0.5) / 0.5) * 0.8
            Mb = Mw @ Mt @ base_local @ T(-30, -14) @ Sc(sbx, 0.8) @ T(-self.back.piv['nose'][0], -self.back.piv['nose'][1])
            draw(headL, self.back, Mb); hp = (self.back, Mb)
        else:
            nx = lerp(1.0, 0.25, u / 0.5)
            dm = lerp(1.0, 0.7, u / 0.5)
            Mh = Mw @ Mt @ base_local @ Sc(local_mirror * abs(hx / hs) * nx, 1) @ R(ha * (1 - u)) @ T(-nk[0], -nk[1])
            draw(headL, self.head, Mh, mult=(dm, dm * .97, dm * .95)); hp = (self.head, Mh)
        nose = ap(hp[1], hp[0].piv['nose']); neck = ap(hp[1], hp[0].piv['neck'])
        if view == 'profile' and abs(nose[0] - neck[0]) < 1: nose = (neck[0] - local_mirror * f, nose[1])
        back = ap(Mw @ Mt, self.torso.piv['back'])
        moving = SPEED[i] > 0.05
        posture = 'lie' if pl > 0.5 else ('turning' if abs(turn) < 0.95 else ('walk' if moving else ('crouch' if crouch > .5 else 'stand')))
        info.update(nose=nose, neck=neck, back=back, body_dir=f, posture=posture, head_view=view)
        return body, headL, info


class Person:
    def __init__(self):
        self.k = 0.504 * S / 200; p = self.k * 1.4
        self.up = Part('m_upper', p, tint=(.42, .42, .45)); self.th = Part('m_thigh', p, tint=(.42, .42, .45))
        self.sh = Part('m_shin', p, tint=(.42, .42, .45)); self.arm = Part('b_arm', 0.59 * 1.4, tint=(.45, .45, .48))
        self.bench = Part('bench', 0.52 * 1.4, tint=(.85, .8, .75))

    def render(self, canvas, i, t, cam):
        px = per(i, 'x')
        px = lerp(-1.25, -0.08, (px + 1.25) / 0.97)   # score doorway -0.28 -> just inside our thinner door frame; beside stays -1.25
        sit = ease(min(per(i, 'sit') / 0.9, 1)); reach = per(i, 'reach'); low = per(i, 'low'); mouth = per(i, 'mouth')
        # bench beside the door (always there; the person backs onto it)
        bx = wx(-1.25) + 2
        Mb = cam @ T(bx, FEET) @ Sc(0.42 * S / 200, 0.22 * S / 200) @ T(-235, -1100)
        draw(canvas, self.bench, Mb, mult=(.75, .7, .65))
        Mp = cam @ T(wx(px), FEET) @ Sc(self.k) @ T(-600, -1192)
        th = -88 * sit
        moving = 5.4 < t < 6.3
        swing = 9 * math.sin(2 * math.pi * (t - 5.4) / 0.45) * (1 - sit) if moving else 0
        knee_v = 1062
        hip = (595 - 55 * sit, knee_v - 117 * math.cos(math.radians(th)) if sit > 0 else 945)
        knee = ap(T(*hip) @ R(th + swing), (0, 117))
        lean = 4 * mouth + 6 * low * sit
        Mup = Mp @ T(hip[0], hip[1]) @ R(lean) @ T(-595, -945)
        draw(canvas, self.sh, Mp @ T(knee[0], knee[1]) @ R(-swing * 0.6) @ T(-600, -1062))
        draw(canvas, self.th, Mp @ T(hip[0], hip[1]) @ R(th + swing) @ T(-595, -945))
        draw(canvas, self.up, Mup)
        # the arm (Edouart's pointing boy, mirrored): reach = straight at the dog; low = offered low, open
        ang = None
        if reach > 0.02: ang = lerp(75, -6, ease(reach))
        if low > 0.02: ang = lerp(75, 38, ease(low))
        if ang is not None and ang < 72:
            shp = ap(Mup, (625, 650))
            z = cam[0, 0]
            Ma = T(*shp) @ R(ang) @ Sc(-0.59 * z * 0.85 * S / 200, 0.59 * z * 0.85 * S / 200) @ T(-890, -725)
            draw(canvas, self.arm, Ma)
        return {'x': px, 'sit': sit}


class Stage:
    """Static plates rendered once per lighting state at world scale (screen coords at zoom 1, margin for the push-in)."""
    def __init__(self):
        self.M = 300  # margin px on each side
        self.w, self.h = W + 2 * self.M, H + 2 * self.M
        pl = lambda n: Image.open(os.path.join(PD, n + '.jpg')).convert('RGB')
        room, dusk, floor, jamb = pl('room'), pl('dusk'), pl('floor'), pl('jamb'); self.reveal = pl('reveal')
        self.door = Part('door', 0.238 * 1.4 * S / 200)
        self.A = self.build(room, dusk, floor, jamb, 0.0); self.B = self.build(room, dusk, floor, jamb, 1.0)

    def sx(self, x): return wx(x) + self.M
    def sy(self, y): return y + self.M

    def build(self, room, dusk, floor, jamb, lit):
        c = np.zeros((self.h, self.w, 3), float)
        def put(img, x0, y0, x1, y1, mult):
            x0, y0, x1, y1 = map(int, (x0, y0, x1, y1)); x0c, y0c = max(x0, 0), max(y0, 0); x1c, y1c = min(x1, self.w), min(y1, self.h)
            im = np.asarray(img.resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(float)
            c[y0c:y1c, x0c:x1c] = im[y0c - y0:y1c - y0, x0c - x0:x1c - x0] * np.array(mult)[None, None]
        fy = self.sy(FEET)
        dusk_m = (.40, .45, .66)
        # outside: MacGilvary's twilight, cooled; beyond the porch
        put(dusk, self.sx(WALL_OUT) - 10, self.sy(-40), self.w, fy - 20, dusk_m)
        # room: Andrews's interior, warm; brighter once the door is open (its light reaches us through the doorway).
        # It continues to the outer face of the wall: the doorway is an opening onto the lit room.
        rm = (lerp(.80, 1.12, lit), lerp(.66, .93, lit), lerp(.52, .66, lit))
        put(room, 0, self.sy(-30), self.sx(WALL_OUT), fy - 18, rm)
        # the door frame: two casing strips (wood from the same interior) under the lintel
        ly = self.sy(FEET - S * LINTEL)
        put(jamb, self.sx(WALL_OUT) - 9, ly, self.sx(WALL_OUT) + 1, fy - 16, (.42, .34, .28))
        put(jamb, self.sx(WALL_IN) - 4, ly, self.sx(WALL_IN) + 6, fy - 16, (.26, .2, .16))
        # wall in section above the lintel and the lintel beam
        put(jamb, self.sx(WALL_IN), 0, self.sx(WALL_OUT), self.sy(FEET - S * LINTEL), (.30, .26, .24))
        put(jamb.transpose(Image.ROTATE_90), self.sx(WALL_IN) - 6, self.sy(FEET - S * LINTEL) - 16, self.sx(WALL_OUT) + 6, self.sy(FEET - S * LINTEL) + 4, (.55, .45, .38))
        # floors: interior boards warm, threshold stone, porch boards at dusk (Andrews's floor, cut into strips)
        put(floor, 0, fy - 22, self.sx(WALL_IN), fy + 30, rm)
        put(floor.crop((700, 0, 1300, 251)), self.sx(WALL_IN), fy - 24, self.sx(SILL), fy + 30, (lerp(.62, 1.05, lit), lerp(.58, .92, lit), lerp(.55, .72, lit)))
        put(floor, self.sx(SILL), fy - 22, self.w, fy + 30, dusk_m)
        # the cut face of the floor (section) below
        put(floor.crop((0, 120, 1800, 251)), 0, fy + 30, self.w, self.h, (.22, .2, .22))
        # light from the open door falling on the porch
        xs = (np.arange(self.w) - self.M - X0) / S
        reach = lerp(0.9, 3.4, lit)
        wgt = np.clip(1 - (xs - WALL_OUT) / reach, 0, 1) ** 1.4 * (xs > WALL_OUT) * 0.75
        wgt = np.convolve(wgt, np.ones(41) / 41, mode='same')
        band = np.zeros(self.h); band[int(fy - 22):int(fy + 30)] = 1.0
        band[int(fy - 60):int(fy - 22)] = np.linspace(0, .35, int(fy - 22) - int(fy - 60))
        L = wgt[None, :] * band[:, None] * lerp(0.35, 1.0, lit)
        c = c * (1 + L[..., None] * np.array([.9, .55, .2])[None, None]) + L[..., None] * np.array([34, 20, 6])[None, None]
        return np.clip(c, 0, 255)

    def frame(self, t, cam):
        o = openness(t)
        base = self.A * (1 - o) + self.B * o
        img = Image.fromarray(base.astype(np.uint8)).convert('RGBA')
        # the screen door: hinged at the outer face of the wall, opening outward over the porch (a screen door opens out);
        # seen at an angle its width is W sin(theta)
        th = door_angle(t); wv = 0.92 * math.sin(math.radians(th))
        Md = T(self.sx(WALL_OUT), self.sy(FEET + 4)) @ Sc(wv * S / 800.0, (S * 2.05) / 1720.0) @ T(-60, -1760)
        draw(img, self.door, Md, mult=(lerp(.42, .62, o), lerp(.42, .56, o), lerp(.5, .5, o)))
        Ai = np.linalg.inv(cam @ T(-self.M, -self.M))
        return img.transform((W, H), Image.AFFINE, data=tuple(Ai[:2].reshape(-1)), resample=Image.BICUBIC)


def light_map(t, cam):
    """Per-column grade for the dog: dusk outside, warm in the door's light."""
    o = openness(t)
    Ci = np.linalg.inv(cam)
    xs_screen = np.arange(W)
    xw = ((Ci[0, 0] * xs_screen + Ci[0, 2]) - X0) / S     # (zoom has no rotation/shear)
    dusk = np.array([.70, .72, .86]); warm = np.array([1.08, .96, .80])
    reach = lerp(0.8, 3.2, o)
    w = np.clip(1 - (xw - WALL_OUT) / reach, 0, 1) ** 1.2 * o
    w = np.where(xw < WALL_OUT, lerp(0.35, 1.0, o), w)
    return dusk[None] * (1 - w[:, None]) + warm[None] * w[:, None]


def main(a, b):
    stage = Stage(); dog = Dog(); person = Person()
    mfile = os.path.join(HERE, 'cache', 'measure.json')
    meas = json.load(open(mfile)) if os.path.exists(mfile) else {}
    for i in range(a, b + 1):
        t = i / FPS
        cam, z = camera(t)
        frame = stage.frame(t, cam)
        pinfo = person.render(frame, i, t, cam)
        body, headL, info = dog.render(i, t, cam)
        lm = light_map(t, cam)
        for L in (body, headL):
            arr = np.asarray(L).astype(float)
            if False:
                # contre-jour: the head has entered the room's light; a warm rim where the light wraps the edge
                a = arr[..., 3] / 255.
                er = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))).astype(float) / 255.
                rim = np.clip(a - er, 0, 1) * info['silhouette']
                arr[..., :3] *= np.array([1.08, .97, .82])[None, None]   # in the room's light, not the dusk
                arr[..., :3] = arr[..., :3] * (1 - rim[..., None]) + rim[..., None] * np.array([255, 205, 130])[None, None]
                frame.alpha_composite(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))); continue
            arr[..., :3] *= lm[None]; L2 = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            frame.alpha_composite(L2)
        frame.convert('RGB').save(os.path.join(FD, f'f_{i:04d}.jpg'), quality=92)
        # ---- measurement from the rendered dog layers
        ab = np.asarray(body)[..., 3] > 128; ah = np.asarray(headL)[..., 3] > 128
        ys, xs = np.nonzero(ab); yh, xh = np.nonzero(ah); ya = np.concatenate([ys, yh])
        Ci = np.linalg.inv(cam)
        cxs = float(xs.mean()) if len(xs) else None
        xw = (ap(Ci, (cxs, 0))[0] - X0) / S if cxs is not None else None
        rec = {'i': i, 't': round(t, 4), 'body_cx_screen': cxs, 'body_cy_screen': float(ys.mean()) if len(ys) else None,
               'x_world_body_centroid': xw, 'mask_top_screen': int(ya.min()) if len(ya) else None,
               'mask_px': int(ab.sum() + ah.sum()), 'head_cx_screen': float(xh.mean()) if len(xh) else None,
               'head_top_screen': int(yh.min()) if len(yh) else None, 'head_w_screen': int(xh.max() - xh.min()) if len(xh) else None,
               'head_view': info.get('head_view'), 'cam_zoom': z}
        for k in ('nose', 'neck', 'back', 'hind_paw', 'hind_target'):
            if k in info: rec[k + '_screen'] = [round(info[k][0], 1), round(info[k][1], 1)]
        rec.update({k: info[k] for k in ('x_score', 'turn', 'lie', 'model', 'body_dir', 'posture')})
        rec['person_x'] = pinfo['x']; rec['hind_reach_ok'] = info.get('hind_reach_ok')
        meas[str(i)] = rec
        if i % 48 == 0: print('frame', i, flush=True)
    json.dump(meas, open(mfile, 'w'))


if __name__ == '__main__':
    a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, N - 1)
    main(a, b)
