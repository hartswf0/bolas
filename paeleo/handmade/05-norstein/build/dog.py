"""The dog: a maquette of ellipsoids and tapered limbs, re-cut every frame into flat cutout pieces for the glass.

Norstein's cutout puppets are flat pieces moved under the camera, with replacement pieces for new angles. Here the
replacement pieces are cut from a small 3D maquette: every frame each ellipsoid becomes the flat ellipse it projects to,
each limb a flat tapered strip, each ear a flat triangle; they are laid on the dog's glass in depth order and painted.
Because every piece keeps its thickness, a turn passes through real rear and front views (rump, tail, two hind legs;
chest, two forelegs, the face) instead of an edge-on sliver.

Proportions are taken from the archive dog (kit/archive-dog/pose_agent_v8.json, frame 0: nose, neck, chest, tail base,
feet), scaled to a 0.50 m withers height. Feet are solved, not tweened: a foot on the boards stays where it was put
(world position) until the body has moved far enough from it, then it is lifted and put down again ahead.
"""
import math
import numpy as np
from PIL import Image, ImageDraw
from common import *

LEGS = {  # mount on the body (forward f, lateral l), segment lengths
    'LF': dict(f=0.205, l=0.075, front=True), 'RF': dict(f=0.205, l=-0.075, front=True),
    'LH': dict(f=-0.215, l=0.078, front=False), 'RH': dict(f=-0.215, l=-0.078, front=False)}
UPPER_F, LOWER_F = 0.172, 0.168
THIGH, SHIN, META = 0.165, 0.155, 0.14
STAND_H = 0.355  # torso centre height when standing


def interp(v, xs, ys):
    return float(np.interp(v, xs, ys))


def ang_lerp(a, b, u):
    return a + (b - a) * u


# ------------------------------------------------------------------------------------------------ the controller
def controller():
    """per scene frame: the dog's acting parameters. Choices and their times come from the score; how the body
    performs them (turn path, the head leading, how low the head is carried) is this studio's acting."""
    P = []
    prev_state = None
    wag_phase = 0.0
    sm = {}

    def ease(name, target, rate):
        v = sm.get(name, target)
        v = v + (target - v) * rate
        sm[name] = v
        return v

    for i in range(N):
        t = i / FPS
        d = FR[i]['dog']
        a = d['act']
        st = d['state']
        x, z = dog_path(t)
        # --- body yaw: pi = facing the door (screen left), pi/2 = rump to camera, 0 = back turned, -pi/2 = chest to camera
        if t < 3.42:
            psi = math.pi
        elif t < 3.92:  # the refusal turn: quick, away from camera, through the rear view (the back is shown by ~3.65)
            u = smooth(3.42, 3.92, t)
            psi = ang_lerp(math.pi, 0.32, u)
        elif t < 8.0:
            psi = 0.32
        elif t < 8.95:  # turning back to the door, the head already round: through the front view
            u = smooth(8.0, 8.95, t)
            psi = ang_lerp(0.32, -math.pi, u)
        else:
            psi = -math.pi - 0.20 * smooth(2.4, 1.0, x) - 0.12 * smooth(23.7, 24.6, t)
        # spine bend: the head end leads every turn
        bend = 0.0
        if 3.42 <= t < 3.92:
            bend = -0.38 * math.sin(math.pi * smooth(3.42, 3.92, t))
        if 7.40 <= t < 8.95:
            bend = -0.7 * smooth(7.38, 7.6, t) * (1 - smooth(8.15, 8.95, t))
        # --- head yaw relative to the body
        head_rel = 0.0
        if 7.40 <= t < 8.95:  # looks back over the shoulder at the opened door, on time (7.46)
            target = keyed([(7.38, psi + bend), (7.58, -2.8), (8.0, -2.9), (8.95, -math.pi)], t)
            head_rel = target - psi - bend
        if 9.0 <= t < 14.7:  # watching: small looks between the low hand and the light
            head_rel = 0.18 * math.sin((t - 9.0) * 0.9) * smooth(9.0, 10.0, t)
        lie = a['lie']
        look = a['look']
        if st == 'lie_down' or t > 23.7:
            head_rel = -0.5 * look
        # --- head carriage (alpha: neck angle above horizontal, degrees)
        hv = a['head']
        alpha = interp(hv, [0, 0.15, 0.35, 0.45, 0.7, 0.9, 1.25], [-48, -42, -30, -24, 6, 30, 52])
        if st == 'approach':
            alpha = min(alpha, -40.0 + 10.0 * smooth(23.2, 23.8, t))
        if 3.42 <= t < 4.3:  # turning away, the head is still carried: it shows over the back in the rear view
            alpha = max(alpha, lerp(14, -40, smooth(3.95, 4.35, t)))
        if 7.38 <= t < 8.9:  # the head lifts high as it comes round, so the look over the shoulder clears the back
            alpha = max(alpha, lerp(-30, 48, smooth(7.38, 7.56, t)) * (1 - smooth(8.3, 8.9, t)) + 30 * smooth(8.3, 8.9, t))
        if st == 'lie_down':  # lying, the head is lifted on the neck, never stood up on it
            alpha = min(alpha, 22.0)
        # the choice to stop backing and watch (2.33) is shown at once: the head comes up while the body still drifts
        if 2.32 <= t < 2.9:
            alpha = max(alpha, 25.0)
        alpha = ease('alpha', alpha, 0.5 if 2.30 <= t < 2.7 else 0.35)
        # --- the rest of the body
        crouch = ease('crouch', a['crouch'] if not (2.30 <= t < 2.7) else min(a['crouch'], 0.3), 0.3)
        ear = ease('ear', max(clamp(a['ear'], 0, 1), 0.5 * (1 - smooth(3.9, 4.4, t)) if t > 3.4 else 0), 0.4)
        tail = ease('tail', a['tail'], 0.3)
        wag = ease('wag', a['wag'], 0.2)
        wag_phase += 2 * math.pi * (2.0 + 1.2 * wag) / FPS
        rest = ease('rest', a['rest'], 0.25)
        if 7.36 <= t < 9.0:  # the chin comes off the paws as the head comes round
            rest = min(rest, 1 - smooth(7.36, 7.5, t))
        breath = math.sin(t * 2 * math.pi * (0.55 if st != 'lie_down' else 0.32))
        eye = 1.0
        if t > 30.3:  # settles: the eyes close slowly
            eye = 1 - smooth(30.3, 31.2, t)
        for bt in (12.2, 19.5):  # blinks
            if abs(t - bt) < 0.07:
                eye = 0.0
        P.append(dict(i=i, t=t, state=st, x=x, z=z, psi=psi, bend=bend, head_rel=head_rel, alpha=alpha, lie=lie,
                      crouch=crouch, ear=ear, tail=tail, wag=wag, wag_phase=wag_phase, rest=rest, look=look,
                      breath=breath, eye=eye, moving=a['moving']))
    solve_feet(P)
    return P


def body_frame(p):
    """forward and lateral unit vectors (world XZ) for the front and rear halves of the body."""
    def fv(yaw):
        return np.array([math.cos(yaw), 0.0, math.sin(yaw)]), np.array([-math.sin(yaw), 0.0, math.cos(yaw)])
    return fv(p['psi'] + p['bend']), fv(p['psi'] - 0.3 * p['bend'])


def mount_world(p, leg):
    L = LEGS[leg]
    (ff, lf), (fr, lr) = body_frame(p)
    fwd, lat = (ff, lf) if L['front'] else (fr, lr)
    root = np.array([p['x'], 0.0, p['z']])
    return root + fwd * L['f'] + lat * L['l'], fwd, lat


def solve_feet(P):
    """the foot-plant solver: planted feet hold their world position; a foot steps only when the body has left it."""
    feet = {}
    for k, p in enumerate(P):
        prev = P[k - 1] if k else p
        v = np.array([p['x'] - prev['x'], 0.0, p['z'] - prev['z']]) * FPS
        yaw_rate = abs(p['psi'] - prev['psi']) * FPS
        lying = p['lie'] > 0.35
        out = {}
        swinging = [n for n, s in feet.items() if s['mode'] == 'swing']
        ideal = {}
        for leg in LEGS:
            m, fwd, lat = mount_world(p, leg)
            ideal[leg] = np.array([m[0], 0.0, m[2]]) + v * 0.20
        if not feet or lying:
            for leg in LEGS:
                feet[leg] = dict(mode='plant', P=ideal[leg].copy())
        else:
            errs = sorted(LEGS, key=lambda n: -np.linalg.norm(ideal[n] - feet[n].get('P', ideal[n])))
            for leg in errs:
                s = feet[leg]
                if s['mode'] != 'plant':
                    continue
                e = np.linalg.norm(ideal[leg] - s['P'])
                if e < (0.11 if yaw_rate < 0.5 else 0.07):
                    continue
                side = leg[0]
                girdle = leg[1]
                busy = [n for n in LEGS if feet[n]['mode'] == 'swing']
                if len(busy) >= 2 or any(n[0] == side or n[1] == girdle for n in busy):
                    continue
                dur = 0.24 if np.linalg.norm(v) > 0.2 else 0.20
                feet[leg] = dict(mode='swing', A=s['P'].copy(), u=0.0, du=1.0 / (dur * FPS))
            for leg in LEGS:
                s = feet[leg]
                if s['mode'] == 'swing':
                    s['u'] += s['du']
                    target = ideal[leg] + v * 0.12
                    if s['u'] >= 1.0:
                        feet[leg] = dict(mode='plant', P=target.copy(), landed=True)
                    else:
                        s['B'] = target
        for leg in LEGS:
            s = feet[leg]
            if s['mode'] == 'plant':
                out[leg] = (s['P'].copy(), 0.0, s.pop('landed', False))
            else:
                u = s['u']
                e = u * u * (3 - 2 * u)
                pos = s['A'] + (s['B'] - s['A']) * e
                out[leg] = (pos, 0.065 * math.sin(math.pi * u), False)
        p['feet'] = out


# ------------------------------------------------------------------------------------------------ the maquette
def ik2(J, T, l1, l2, bend_dir):
    """two-bone IK from joint J to target T; the middle joint is pushed along bend_dir."""
    d = T - J
    L = np.linalg.norm(d)
    L = min(L, l1 + l2 - 1e-4)
    u = d / (np.linalg.norm(d) + 1e-9)
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    b = bend_dir - u * np.dot(bend_dir, u)
    b = b / (np.linalg.norm(b) + 1e-9)
    K = J + u * a + b * h
    return K, J + u * L


def build(p):
    """the dog's 3D maquette for one frame: a list of primitives with tags and tones."""
    (ff, lf), (fr, lr) = body_frame(p)
    up = np.array([0.0, 1.0, 0.0])
    root = np.array([p['x'], 0.0, p['z']])
    lie = p['lie']
    c = p['crouch']
    br = p['breath'] * 0.006
    hf = lerp(STAND_H - 0.07 * c, 0.128, lie)  # torso centre height at the front
    hr = lerp(STAND_H - 0.115 * c, 0.118, lie)  # and at the rear (afraid: hindquarters drop)

    def Fp(f, y, l=0.0):  # a point in the front-half frame
        return root + ff * f + up * y + lf * l

    def Rp(f, y, l=0.0):
        return root + fr * f + up * y + lr * l

    prims = []

    def ell(cen, a1, a2, a3, tone, tag):
        prims.append(('ell', cen, np.stack([a1, a2, a3], 1), tone, tag))

    def cap(p0, p1, r0, r1, tone, tag):
        prims.append(('cap', p0, p1, r0, r1, tone, tag))

    # torso
    ell(Fp(0.17, hf + 0.035), ff * 0.18, up * (0.132 + br), lf * 0.11, 1.0, 'torso')          # chest
    ell(Fp(-0.01, (hf + hr) / 2 + 0.065), ff * 0.16, up * 0.085, lf * 0.095, 1.0, 'torso')     # waist
    ell(Rp(-0.20 - 0.02 * lie, hr + 0.045), fr * (0.13 + 0.035 * lie), up * 0.108, lr * (0.10 + 0.02 * lie), 1.0, 'torso')               # hip
    ell(Fp(0.0, (hf + hr) / 2 + 0.105), (ff + fr) / 2 * 0.31, up * 0.05, lf * 0.09, 1.0, 'torso')  # back
    ell(Fp(0.19, hf + 0.12), ff * 0.09, up * 0.07, lf * 0.105, 1.0, 'torso')                   # withers
    # neck and head
    alpha = math.radians(p['alpha'])
    psi_h = p['psi'] + p['bend'] + p['head_rel']
    hfw = np.array([math.cos(psi_h), 0.0, math.sin(psi_h)])
    hlat = np.array([-math.sin(psi_h), 0.0, math.cos(psi_h)])
    nb = Fp(0.25, hf + 0.10)
    # the neck turns gradually from the body's heading to the head's
    nmid_dir = (ff + hfw)
    nmid_dir = nmid_dir / (np.linalg.norm(nmid_dir) + 1e-6) if np.linalg.norm(nmid_dir) > 0.2 else ff * 0.3 + hlat * 0.7
    head = nb + (nmid_dir * 0.08 + hfw * 0.12) * math.cos(alpha) + up * 0.20 * math.sin(alpha)
    rest = p['rest'] * lie
    head_rest = Fp(0.40, 0.085) + hfw * 0.02
    head = head * (1 - rest) + head_rest * rest
    beta = math.radians(lerp(-12 + 0.35 * p['alpha'], -4, rest))
    dh = hfw * math.cos(beta) + up * math.sin(beta)
    hup = np.cross(dh, hlat)
    hup = hup if hup[1] > 0 else -hup
    for k, u in enumerate((0.2, 0.5, 0.8)):
        q = nb + (head - dh * 0.04 - nb) * u
        ell(q, (head - nb) / (np.linalg.norm(head - nb) + 1e-6) * 0.07, up * lerp(0.085, 0.062, u), lf * lerp(0.085, 0.064, u),
            1.0, 'neck')
    ell(head, dh * 0.092, hup * 0.08, hlat * 0.075, 1.0, 'head')
    ell(head + dh * 0.105 - hup * 0.024, dh * 0.08, hup * 0.045, hlat * 0.043, 1.12, 'head')   # muzzle
    ell(head + dh * 0.18 - hup * 0.012, dh * 0.018, hup * 0.019, hlat * 0.022, 0.25, 'head')   # nose
    for s in (1, -1):  # eyes
        prims.append(('eye', head + dh * 0.048 + hup * 0.026 + hlat * 0.05 * s, 0.0115, p['eye'], 'head'))
        # ears: flat triangles, pricked (ear=1) or laid back (ear=0)
        e = p['ear']
        base = head - dh * 0.02 + hup * 0.055 + hlat * 0.036 * s
        tipd = (hup * lerp(0.25, 1.0, e) + dh * lerp(-1.0, 0.15, e) + hlat * 0.25 * s)
        tipd = tipd / np.linalg.norm(tipd)
        prims.append(('tri', [base - dh * 0.036, base + dh * 0.036, base + tipd * lerp(0.08, 0.088, e)], 0.85, 'head'))
    # legs
    feet = p['feet']
    for leg, L in LEGS.items():
        fwd, lat = (ff, lf) if L['front'] else (fr, lr)
        PtL = Fp if L['front'] else Rp
        Jy = (hf + 0.02) if L['front'] else (hr + 0.03)
        J = PtL(L['f'], Jy, L['l'])
        foot, lift, _ = feet[leg]
        foot = foot + up * (0.025 + lift)
        if L['front']:
            K, Wr = ik2(J, foot + up * 0.02, UPPER_F, LOWER_F, -fwd)
            # lying pose (sphinx: forelegs along the boards)
            Kl, Wl, Fl = PtL(0.12, 0.04, L['l']), PtL(0.31, 0.028, L['l'] * 0.8), PtL(0.38, 0.022, L['l'] * 0.8)
            K, Wr = K * (1 - lie) + Kl * lie, Wr * (1 - lie) + Wl * lie
            paw = Wr - up * 0.02 * (1 - lie) + fwd * (0.03 + 0.045 * lie)
            segs = [(J, K, 0.052, 0.034), (K, Wr, 0.031, 0.024)]
        else:
            hock = foot + up * 0.12 - fwd * 0.045
            K, hock2 = ik2(J, hock, THIGH, SHIN, fwd)
            Kl, Hl, Fl = PtL(-0.12, 0.06, L['l'] * 1.6), PtL(-0.29, 0.03, L['l'] * 1.6), PtL(-0.13, 0.022, L['l'] * 1.6)
            K, hock2 = K * (1 - lie) + Kl * lie, hock2 * (1 - lie) + Hl * lie
            paw = hock2 - up * lerp(0.12, 0.01, lie) + fwd * lerp(0.075, 0.15, lie)
            segs = [(J, K, 0.075, 0.042), (K, hock2, 0.04, 0.026), (hock2, paw, 0.025, 0.022)]
        for a_, b_, r0, r1 in segs:
            cap(a_, b_, r0, r1, 1.0, 'leg_' + leg)
        ell(paw, fwd * 0.04, up * 0.022, lat * 0.03, 1.0, 'leg_' + leg)
    # tail
    tau = p['tail']
    th = math.radians(interp(tau, [0, 0.5, 1.0, 1.35], [38, -32, -62, -82]))
    kap = math.radians(interp(tau, [0, 0.5, 1.35], [10, 7, -14]))
    th = th * (1 - lie) + math.radians(-14) * lie
    kap = kap * (1 - lie) + math.radians(4) * lie
    sweep = p['wag'] * 0.75 * math.sin(p['wag_phase'])
    q = Rp(-0.33, hr + 0.065)
    for k in range(6):
        ang = th + kap * k
        yaw = sweep * (k + 1) / 6
        dirw = -fr * math.cos(ang) * math.cos(yaw) + lr * math.cos(ang) * math.sin(yaw) + up * math.sin(ang)
        q2 = q + dirw * 0.05
        cap(q, q2, lerp(0.03, 0.012, k / 6), lerp(0.026, 0.009, k / 6), 0.95, 'tail')
        q = q2
    return prims


# ------------------------------------------------------------------------------------------------ cutting the pieces
def ellipse_poly(cx, cy, M, n=28):
    w, V = np.linalg.eigh(M)
    w = np.sqrt(np.maximum(w, 1e-9))
    ts = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = (V @ np.stack([w[0] * np.cos(ts), w[1] * np.sin(ts)])).T + [cx, cy]
    return [tuple(q) for q in pts]


def capsule_poly(a, b, r0, r1, n=8):
    d = np.array(b) - np.array(a)
    L = np.linalg.norm(d) + 1e-9
    u = d / L
    nrm = np.array([-u[1], u[0]])
    pts = []
    base = math.atan2(nrm[1], nrm[0])
    for k in range(n + 1):  # cap around b
        th = base - math.pi * k / n
        pts.append(tuple(np.array(b) + r1 * np.array([math.cos(th), math.sin(th)])))
    for k in range(n + 1):  # cap around a
        th = base + math.pi - math.pi * k / n
        pts.append(tuple(np.array(a) + r0 * np.array([math.cos(th), math.sin(th)])))
    return pts


def cut(prims, c, near_sign_ref=None):
    """project the maquette into flat 2D pieces (screen px): [(depth, kind, polygon/circle, tone, tag)]."""
    out = []
    for pr in prims:
        kind = pr[0]
        if kind == 'ell':
            _, cen, A, tone, tag = pr
            sx, sy, zc = project(cen, c)
            Jm = np.array([[F / zc, 0, -F * (cen[0] - c[0]) / zc ** 2], [0, -F / zc, F * (cen[1] - c[1]) / zc ** 2]])
            B = Jm @ A
            out.append((zc, 'poly', ellipse_poly(sx, sy, B @ B.T), tone, tag))
        elif kind == 'cap':
            _, p0, p1, r0, r1, tone, tag = pr
            a = project(p0, c)
            b = project(p1, c)
            zc = (a[2] + b[2]) / 2
            out.append((zc, 'poly', capsule_poly(a[:2], b[:2], r0 * F / a[2], r1 * F / b[2]), tone, tag))
        elif kind == 'tri':
            _, pts, tone, tag = pr
            q = [project(v, c) for v in pts]
            zc = sum(v[2] for v in q) / 3 - 0.005
            out.append((zc, 'poly', [v[:2] for v in q], tone, tag))
        elif kind == 'eye':
            _, cen, r, op, tag = pr
            sx, sy, zc = project(cen, c)
            out.append((zc - 0.01, 'eye', (sx, sy, r * F / zc, op), 0.0, tag))
    return out


def far_side_tone(p, tag, c):
    """the far legs are painted darker, as on a cutout where the far limbs are a separate, shadowed piece."""
    if not tag.startswith('leg_'):
        return 1.0
    leg = tag[4:]
    m, fwd, lat = mount_world(p, leg)
    root = np.array([p['x'], 0.0, p['z']])
    tocam = np.array([c[0], 0, c[2]]) - root
    near = np.dot(m - root, tocam) > 0
    return 1.0 if near else 0.72


SS = 3  # supersampling for the cutout edges


def render(p, c):
    """draw the dog's pieces. Returns (x0, y0, tone L-image, alpha L-image, torso pass, head pass) at screen scale."""
    prims = build(p)
    pieces = cut(prims, c)
    pts = np.array([q for d in pieces if d[1] == 'poly' for q in d[2]])
    x0, y0 = np.floor(pts.min(0)) - 6
    x1, y1 = np.ceil(pts.max(0)) + 6
    w, h = int(x1 - x0), int(y1 - y0)
    tone = Image.new('L', (w * SS, h * SS), 0)
    alpha = Image.new('L', (w * SS, h * SS), 0)
    torso = Image.new('L', (w * SS, h * SS), 0)
    headm = Image.new('L', (w * SS, h * SS), 0)
    dt, da, dto, dh = (ImageDraw.Draw(im) for im in (tone, alpha, torso, headm))
    pieces.sort(key=lambda d: -d[0])  # far first

    def S(poly):
        return [((u - x0) * SS, (v - y0) * SS) for u, v in poly]

    zs = [d[0] for d in pieces]
    zmin = min(zs)
    for zc, kind, geo, t0, tag in pieces:
        if kind == 'poly':
            tn = t0 * far_side_tone(p, tag, c) * (1 - 0.7 * clamp(zc - zmin, 0, 0.35))
            poly = S(geo)
            dt.polygon(poly, fill=int(clamp(tn * 160, 0, 255)))
            da.polygon(poly, fill=255)
            if tag == 'torso':
                dto.polygon(poly, fill=255)
            if tag == 'head':
                dh.polygon(poly, fill=255)
        else:
            sx, sy, r, op = geo
            if op > 0.1:
                R = r * SS
                cx_, cy_ = (sx - x0) * SS, (sy - y0) * SS
                rr = R * max(op, 0.15)
                dt.ellipse([cx_ - R, cy_ - rr, cx_ + R, cy_ + rr], fill=18)
                g = R * 0.45
                dt.ellipse([cx_ - g * 0.2 - g, cy_ - rr * 0.35 - g, cx_ - g * 0.2 + g, cy_ - rr * 0.35 + g], fill=250)
            else:
                dt.line([((sx - r - x0) * SS, (sy - y0) * SS), ((sx + r - x0) * SS, (sy - y0) * SS)], fill=30, width=SS)
    # the torso pass is drawn whole (not occluded): it locates the body for measurement
    for zc, kind, geo, t0, tag in pieces:
        if kind == 'poly' and tag == 'torso':
            dto.polygon(S(geo), fill=255)
    rs = (w, h)
    return int(x0), int(y0), tone, alpha, torso.resize(rs, Image.BILINEAR), headm.resize(rs, Image.BILINEAR)
