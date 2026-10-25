"""SCION 46 pose solver: rig.json -> world landmark vectors per frame (build/cache/pose.json).
Solver passes: torso pivots -> neck/skull pivots -> head landmark vector -> ear/eye controls -> foot stepper (planted
feet, no sliding while a foot bears weight) -> two-bone leg IK -> tail pivot chain. All world metres."""
import json, math, os
import numpy as np
from geom import BODY, HEAD, CACHE, FPS, smoothstep
HS = 1.22   # the dog's head is cast a little larger than life so its face can carry the choices

UP = np.array([0.0, 1.0, 0.0])


def wrap(d): return (d + 180.0) % 360.0 - 180.0


def fwd_of(th):
    r = math.radians(th); return np.array([math.cos(r), 0.0, math.sin(r)])


def right_of(th):
    r = math.radians(th); return np.array([-math.sin(r), 0.0, math.cos(r)])


def torso_point(p, f):
    u, v, s = p
    rho = math.radians(f['pitch']); mid = 0.45
    u2 = u * math.cos(rho) - (v - mid) * math.sin(rho)
    v2 = mid + u * math.sin(rho) + (v - mid) * math.cos(rho) + f['lift']
    O = np.array([f['X_mid'], 0.0, 0.0])
    return O + u2 * fwd_of(f['heading']) + v2 * UP + s * right_of(f['heading'])


def head_point(q, S, yaw, pitch):
    h, v, s = q
    r = math.radians(pitch)
    h2 = h * math.cos(r) - v * math.sin(r); v2 = h * math.sin(r) + v * math.cos(r)
    return S + h2 * fwd_of(yaw) + v2 * UP + s * right_of(yaw)


def ik2(root, target, L1, L2, bend_dir):
    d = target - root; dist = np.linalg.norm(d)
    dist_c = min(max(dist, 1e-4), (L1 + L2) * 0.999)
    dn = d / max(dist, 1e-6)
    a = (L1 * L1 + dist_c * dist_c - L2 * L2) / (2 * L1 * dist_c)
    a = max(-1.0, min(1.0, a))
    ang = math.acos(a)
    b = bend_dir - (bend_dir @ dn) * dn
    if np.linalg.norm(b) < 1e-6: b = UP - (UP @ dn) * dn
    b = b / np.linalg.norm(b)
    mid = root + L1 * (math.cos(ang) * dn + math.sin(ang) * b)
    end = root + dn * dist_c
    return mid, end


LEGS = {  # name: (root key, fore?, side)
    'FR': ('SjR', True, 1), 'FL': ('SjL', True, -1), 'HR': ('HjR', False, 1), 'HL': ('HjL', False, -1)}
PAIR = {'FR': 'FL', 'FL': 'FR', 'HR': 'HL', 'HL': 'HR'}
SIDE = {'FR': 'HR', 'HR': 'FR', 'FL': 'HL', 'HL': 'FL'}


def neutral_of(f, name):
    rk, fore, sg = LEGS[name]
    root = torso_point(BODY[rk], f); fw = fwd_of(f['heading']); rt = right_of(f['heading'])
    return np.array([root[0], 0.0, root[2]]) + fw * (0.04 if fore else -0.03) + rt * 0.01 * sg, root


def solve(rig):
    feet = {}; swing = {}; out = []
    prev_root = None
    contacts = []   # (t, leg) for the sound of paws
    for k, f in enumerate(rig):
        t = f['t']; th = f['heading']; fw = fwd_of(th); rt = right_of(th)
        L = {key: torso_point(BODY[key], f) for key in BODY}
        # ---- neck and skull pivots
        N = L['N']; dyaw = wrap(f['hyaw'] - th)
        nyaw = th + 0.5 * dyaw
        e = math.radians(f['elev'])
        Sk = N + 0.17 * (math.cos(e) * fwd_of(nyaw) + math.sin(e) * UP)
        Hd = {q: head_point(np.array(HEAD[q]) * HS, Sk, f['hyaw'], f['hpitch']) for q in HEAD}
        low = min(Hd['J'][1], Hd['Nz'][1])
        if low < 0.035:   # the chin rests on the floor/paws, it does not pass through
            dy = 0.035 - low; Sk = Sk + dy * UP; Hd = {q: v + dy * UP for q, v in Hd.items()}
        ear = f['ear']
        ears = {}
        for side, sg in (('R', 1), ('L', -1)):
            pr = np.array([-0.012, 0.095, 0.03 * sg]); fl = np.array([-0.09, -0.015, 0.045 * sg])
            off = (fl + (pr - fl) * ear) * HS
            base = np.array(HEAD['Eb' + side]) * HS
            ears[side] = (Hd['Eb' + side], head_point(base + off, Sk, f['hyaw'], f['hpitch']))
        # ---- feet: stepper (standing) blended with lying targets
        vel = np.zeros(3)
        if k > 0:
            vel = (np.array([f['X_mid'], 0, 0]) - np.array([rig[k - 1]['X_mid'], 0, 0])) * FPS
        lie = f['lie']
        legs = {}
        for name, (rk, fore, sg) in LEGS.items():
            root = L[rk]
            neutral = np.array([root[0], 0.0, root[2]]) + fw * (0.04 if fore else -0.03) + rt * 0.01 * sg
            lie_t = (L['C'] + fw * 0.13 + rt * 0.065 * sg) if fore else (L['B'] + fw * 0.0 + rt * 0.16 * sg)
            lie_t = np.array([lie_t[0], 0.02, lie_t[2]])
            if name not in feet: feet[name] = neutral.copy()
            if name in swing:
                s0, s1, t0, dur = swing[name]
                u = (t - t0) / dur
                if u >= 1:
                    feet[name] = s1.copy(); del swing[name]; contacts.append((t, name))
                else:
                    pos = s0 + (s1 - s0) * smoothstep(0, 1, u)
                    pos = pos + UP * 0.055 * math.sin(math.pi * u)
                    legs[name] = pos
            if name not in swing and lie < 0.25:
                fut = rig[min(len(rig) - 1, k + 6)]
                pred, _ = neutral_of(fut, name)
                disp = np.linalg.norm((feet[name] - neutral)[[0, 2]])
                reach = np.linalg.norm(feet[name] + UP * (0.06 if fore else 0.13) - fw * (0.012 if fore else 0.045) - root) / (0.42 if fore else 0.44)
                turning = abs(wrap(fut['heading'] - th)) > 4
                thr = 0.15 if np.linalg.norm(vel) > 0.05 else (0.06 if turning else 0.08)
                n_sw = len(swing)
                ok = n_sw < 2 and PAIR[name] not in swing and SIDE[name] not in swing
                if (disp > thr and ok) or (reach > 0.97 and n_sw < 3):
                    swing[name] = (feet[name].copy(), pred, t, 0.17 if turning else 0.24)
            if name not in legs:
                legs[name] = feet[name].copy()
            # lying blend (feet go to their lying places; when lying, the stepper re-plants them there)
            if lie > 0.0:
                w = smoothstep(0.0, 1.0, lie)
                legs[name] = legs[name] * (1 - w) + lie_t * w
                if lie > 0.25:
                    feet[name] = legs[name].copy()
                    swing.pop(name, None)
        # ---- leg IK
        joints = {}
        for name, (rk, fore, sg) in LEGS.items():
            root = L[rk]; foot = legs[name]
            if fore:
                wrist = foot + UP * (0.06 * (1 - lie) + 0.025 * lie) - fw * (0.012 + 0.05 * lie)
                elbow, wrist2 = ik2(root, wrist, 0.20, 0.22, -fw)
                if elbow[1] < 0.035: elbow = elbow + UP * (0.035 - elbow[1])
                toe = foot + fw * 0.05
                joints[name] = [root, elbow, wrist2, toe]
            else:
                hock = foot + UP * (0.13 * (1 - lie) + 0.025 * lie) - fw * (0.045 * (1 - lie) + 0.13 * lie)
                stifle, hock2 = ik2(root, hock, 0.23, 0.21, fw)
                if stifle[1] < 0.05: stifle = stifle + UP * (0.05 - stifle[1])
                toe = foot + fw * 0.05
                joints[name] = [root, stifle, hock2, foot, toe]
        # ---- tail pivot chain
        tail = f['tail']; T = L['T']
        gamma = -35 + 100 * min(tail, 0.75) + 90 * max(0.0, tail - 0.75)
        gamma = min(gamma, 112.0)
        chain = [T]; cur = T.copy()
        wagph = math.sin(2 * math.pi * 2.6 * t)
        for j in range(5):
            g = math.radians(gamma + (8 + 3 * j) * j * (1 if tail < 0.6 else 0.5))
            lam = math.radians(f['wag'] * 40 * wagph * (0.4 + 0.25 * j))
            dirb = -fw * math.cos(g) - UP * math.sin(g)
            dirb = dirb * math.cos(lam) + rt * math.sin(lam) * 1.0
            cur = cur + 0.075 * dirb / np.linalg.norm(dirb)
            if cur[1] < 0.02: cur[1] = 0.02
            chain.append(cur.copy())
        out.append(dict(i=f['i'], t=t, body={k2: v.tolist() for k2, v in L.items()}, skull=Sk.tolist(),
                        head={q: v.tolist() for q, v in Hd.items()}, ears={s2: [a.tolist(), b.tolist()] for s2, (a, b) in ears.items()},
                        legs={n2: [j.tolist() for j in js] for n2, js in joints.items()}, tail=[c.tolist() for c in chain],
                        planted={n2: (n2 not in swing) for n2 in LEGS}))
    return out, contacts


if __name__ == '__main__':
    rig = json.load(open(os.path.join(CACHE, 'rig.json')))
    out, contacts = solve(rig)
    json.dump(out, open(os.path.join(CACHE, 'pose.json'), 'w'))
    json.dump(contacts, open(os.path.join(CACHE, 'contacts.json'), 'w'))
    print('pose frames', len(out), 'paw contacts', len(contacts))
