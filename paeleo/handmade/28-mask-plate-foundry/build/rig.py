"""Tracker + composite integrator, part 2: the dog and the person as parented layer stacks animated to the score.
Every frame returns a list of layer records: (name, plate rgb, alpha, src->screen matrix, depth class, grade kind)."""
import json, os
import numpy as np
from comp import mT, mS, mR, apply, BezierMask, mask_stack
import camera as cam
import dogplates as DP

HERE = os.path.dirname(os.path.abspath(__file__))
SCORE = json.load(open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'score', 'threshold-score.json')))
FR = SCORE['frames']
SCALE = 1.5                    # f010 source px -> screen px (dog 0.95 m long)
STRIDE = 0.50                  # metres per gait cycle; feet are locked to the floor during stance
T_TURN1 = (3.45, 3.95); T_HEADBACK = 7.46; T_RISE_END = 8.0; T_TURN2 = (8.0, 8.5); T_LOOK = (26.5, 28.35)
LOOK_ROT = -52; LOOK_SC = 0.78
T_APPROACH = 14.708; T_LIE = 23.792


def ease(u):
    u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)


def act(i):
    return FR[i]['dog']['act']


def smooth_series(key, i, w=3):
    a = [act(j)[key] for j in range(max(0, i - w), min(len(FR), i + w + 1))]
    return float(np.mean(a))


# ---------------------------------------------------------------- gait: distance-driven phase, foot lock
class Gait:
    def __init__(self):
        xs = np.array([f['dog']['x'] for f in FR])
        self.dist = np.concatenate([[0], np.cumsum(np.abs(np.diff(xs)))])
        self.dx = np.concatenate([[0], np.diff(xs)])

    def leg_angle(self, i, off, L_src, moving):
        """rotation (deg, source space) of a rigid leg so its foot stays planted in stance and swings forward."""
        if not moving: return 0.0, 0.0
        u = (self.dist[i] / STRIDE + off) % 1.0
        A = 0.5 * STRIDE * 0.6 * DP_PXM          # stance travel / 2, in source px
        if u < 0.6:
            rel = A * (1 - 2 * u / 0.6); lift = 0
        else:
            w = (u - 0.6) / 0.4; rel = -A + 2 * A * ease(w); lift = np.sin(np.pi * w)
        return rel, lift


DP_PXM = cam.px_per_m_on_path() / SCALE      # source px per metre


class Dog:
    def __init__(self):
        self.p = DP.build()
        self.g = Gait()
        F = DP.F10
        self.legs = {k: dict(alpha=self.p[k], pivot=np.array(F[k + '_pivot'], float), foot=np.array(F[k + '_foot'], float))
                     for k in ('fore_far', 'fore_near', 'hind')}
        h = DP.F10['head_pivot']; n = DP.F10['nose']
        self.e0 = np.degrees(np.arctan2(h[1] - n[1], h[0] - n[0]))        # f010 head elevation (deg above horizontal, facing left)
        th = {}
        for i in DP.TURN:
            a = self.p['turn'][i]['alpha']; ys, xs = np.nonzero(a > .5)
            th[i] = dict(bottom=float(ys.max()), cx=float(xs.mean()), height=float(ys.max() - ys.min()))
        a = self.p['body10']; ys, _ = np.nonzero(self.p['f10'].alpha > .5)
        self.h10 = float(ys.max() - ys.min()); self.turnfit = th

    # -- head elevation from the score's head / rest values (deg above horizontal, toward where it faces)
    @staticmethod
    def elevation(h, rest, approach):
        e = float(np.interp(h, [0.15, 0.45, 0.7, 0.9, 1.25], [-38, -24, 0, 22, 32]))
        if approach: e = -33.0                     # coming: head clearly below the line of the back
        return e * (1 - rest) + (-30) * rest

    def root(self, i, flip):
        x = FR[i]['dog']['x']
        s = x - cam.OFFSET
        p, _ = cam.project(cam.path_point(s))
        g = DP.F10['ground']
        return mT(p[0, 0], p[0, 1]) @ mS(-SCALE if flip else SCALE, SCALE) @ mT(-g[0], -g[1]), s

    def frame(self, i):
        t = i / 24.0
        a = act(i); st = FR[i]['dog']['state']
        L = []
        # ---------------- turn 1: plate substitution through the dog's own turn (f016 .. f040), heads its own
        if T_TURN1[0] <= t < T_TURN1[1]:
            k = int((t - T_TURN1[0]) / (T_TURN1[1] - T_TURN1[0]) * len(DP.TURN))
            return self.turn_plate(i, DP.TURN[k], own_head=True), dict(mode='turn1', plate=DP.TURN[k], body_facing=DP.TURN_FACING[DP.TURN[k]] or -1,
                                                                        head_facing=DP.TURN_FACING[DP.TURN[k]] or -1, lie=0.0)
        if T_TURN2[0] <= t < T_TURN2[1]:
            seq = DP.TURN[::-1]
            k = int((t - T_TURN2[0]) / (T_TURN2[1] - T_TURN2[0]) * len(seq))
            return self.turn_plate(i, seq[k], own_head=False), dict(mode='turn2', plate=seq[k], body_facing=DP.TURN_FACING[seq[k]] or 1,
                                                                     head_facing=1, lie=0.0)
        flip = T_TURN1[1] <= t < T_TURN2[0]          # body faces away from the door (its back to the person)
        R, s = self.root(i, flip)
        lie = a['lie']; crouch = a['crouch']
        if T_HEADBACK <= t < T_RISE_END:              # rising: a little later than the head, so the head leads
            lie = float(np.interp(t, [T_HEADBACK, 7.62, T_RISE_END], [1.0, 0.9, 0.0]))
        rest = a['rest']
        moving = abs(self.g.dx[i]) > 1e-4 or abs(self.g.dx[min(i + 1, len(FR) - 1)]) > 1e-4
        drop = 36 * lie + 7 * crouch * (1 - lie)
        pitch = 0.0
        B = R @ mT(0, drop) @ mT(150, 160) @ mR(pitch) @ mT(-150, -160)
        # legs: foot lock while walking, folded while lying
        sdir = np.sign(self.g.dx[i]) if moving else 0
        # in source space the dog faces -x; travelling toward the facing direction means source -x
        src_dir = sdir * (-1 if flip else 1)        # mirrored root: screen +x is source -x
        legrecs = {}
        for k, off, far in (('hind', 0.0, False), ('fore_near', 0.25, False), ('hind_far', 0.5, True), ('fore_far', 0.75, True)):
            base = 'hind' if k == 'hind_far' else k
            lg = self.legs[base]; pv = lg['pivot'].copy(); ft = lg['foot']
            Ls = float(np.hypot(*(ft - pv)))
            rel, lift = self.g.leg_angle(i, off, Ls, moving)
            dxs = src_dir * rel
            th = -np.degrees(np.arcsin(np.clip(dxs / Ls, -.95, .95)))
            ys = 1 - 0.12 * lift - (drop / Ls * 0.55 if lie < .05 and crouch > .2 else 0)
            if k.startswith('fore'):
                fold = 90 * ease(lie / 0.8)
            else:
                fold = 62 * ease(lie / 0.8)
            th = th * (1 - min(1, lie * 1.5)) + fold
            shift = mT(-8 if k == 'hind_far' else 0, 0)
            M = B @ shift @ mT(*pv) @ mR(th) @ mS(1, max(.6, ys)) @ mT(-pv[0], -pv[1])
            legrecs[k] = (M, lg['alpha'], far)
        # head: which plate, and its elevation
        approach = st == 'approach'
        look = a['look']
        if T_LOOK[0] <= t < T_LOOK[1] and look > .4:
            # looking in: the head turns away from the camera into the room -- the f000 plate shows the back of the
            # dog's head; it is set level on the neck track (no lift), scaled a little smaller (receding into depth)
            hp = 'head00'; hd = DP.F00_HEAD
            Hm = B @ mT(*DP.F10['head_pivot']) @ mT(-4, 2) @ mR(LOOK_ROT) @ mS(LOOK_SC) @ mT(-hd['pivot'][0], -hd['pivot'][1])
            head_facing = 1; head_kind = 'look-in: back of head (f000) on the neck track'
        else:
            e = self.elevation(smooth_series('head', i), rest, approach)
            hp = 'head10'; pv = DP.F10['head_pivot']
            if flip and t >= T_HEADBACK:
                # the head comes round first: an unmirrored head (facing the door) on the mirrored body's neck track
                neck = apply(B, [pv])[0]
                e = 20
                Hm = mT(*neck) @ mS(SCALE) @ mR(e - self.e0) @ mT(-pv[0], -pv[1])
                head_facing = 1; head_kind = 'head10 over shoulder'
            else:
                Hm = B @ mT(*pv) @ mR(e - self.e0) @ mT(-pv[0], -pv[1]) @ mT(0, 0)
                head_facing = -1 if flip else 1; head_kind = 'head10 e=%d' % e
            if rest > .3:
                Hm = Hm @ mT(*pv) @ mT(-6 * rest, 10 * rest) @ mT(-pv[0], -pv[1])
        f10 = self.p['f10'].rgb
        # stacking order: far legs, body, near legs, head (head on top of the near shoulder)
        for k in ('hind_far', 'fore_far'):
            M, al, _ = legrecs[k]
            L.append(('dog:' + k, f10 * (0.72 if k == 'hind_far' else 1.0), al, M))
        L.append(('dog:body', f10, self.p['body10'], B))
        for k in ('hind', 'fore_near'):
            M, al, _ = legrecs[k]
            L.append(('dog:' + k, f10, al, M))
        if hp == 'head00':
            L.append(('dog:head-look', self.p['f00'].rgb, self.p['head00'], Hm))
        else:
            L.append(('dog:head', f10, self.p['head10'], Hm))
        info = dict(mode='rig', body_facing=-1 if flip else 1, head_facing=head_facing, lie=float(lie), head=head_kind,
                    s=float(s), crouch=float(crouch))
        return L, info

    def turn_plate(self, i, k, own_head):
        tp = self.p['turn'][k]; fit = self.turnfit[k]
        sc = SCALE * self.h10 / fit['height'] * 0.97
        x = FR[i]['dog']['x']; s = x - cam.OFFSET
        p, _ = cam.project(cam.path_point(s))
        M = mT(p[0, 0], p[0, 1]) @ mS(sc) @ mT(-fit['cx'], -fit['bottom'])
        L = [('dog:turn%d' % k, tp['plate'].rgb, tp['alpha'] if own_head else tp['headless'], M)]
        if not own_head:
            pv = DP.F10['head_pivot']; neck = apply(M, [tp['neck']])[0]
            Hm = mT(*neck) @ mS(SCALE) @ mR(24 - self.e0) @ mT(-pv[0], -pv[1])
            L.append(('dog:head', self.p['f10'].rgb, self.p['head10'], Hm))
        return L


# ---------------------------------------------------------------- the person
class Person:
    def __init__(self, plate_loader):
        self.w_rgb, self.w_a = plate_loader('woman0', True)
        # plate extension: the source frame ends at mid-calf; repeat the last rows (she is a silhouette)
        ext = 46
        self.w_rgb = np.concatenate([self.w_rgb, np.repeat(self.w_rgb[-1:], ext, 0)], 0)
        col = self.w_a[-1:].copy()
        ramp = np.linspace(1, .9, ext)[:, None]
        legs = np.repeat(col, ext, 0) * ramp
        # narrow the extension toward the feet
        xs = np.arange(self.w_a.shape[1])
        c = (xs * col[0]).sum() / max(1, col[0].sum())
        for r in range(ext):
            half = 30 - r * 0.25
            legs[r] *= np.clip(half - np.abs(xs - c), 0, 1)
        self.w_a = np.concatenate([self.w_a, legs], 0)
        self.s_rgb, self.s_a = plate_loader('seated', True)
        self.arm_rgb, self.arm_a = plate_loader('arm', True)

    def frame(self, i):
        t = i / 24.0
        pf = FR[i]['person']
        L = []
        # standing in the doorway (inside, s=-0.30), then stepping out to the left, then seated outside beside the door
        stand_P = cam.path_point(-0.30)
        seat_P = np.array([-0.86, 0, 0.30])
        u = ease((t - 4.6) / 0.8)
        if t < 5.45:
            P = stand_P * (1 - u) + seat_P * u
            p, z = cam.project(P)
            hpx = 1.62 * cam.F / z[0]
            sc = hpx / 316.0
            M = mT(p[0, 0], p[0, 1]) @ mS(sc) @ mT(-262, -334)
            L.append(('person:standing', self.w_rgb, self.w_a, M, 'silhouette' if u < .5 else 'dusk'))
            shoulder = apply(M, [(318, 100)])[0]
            reach = pf['reach']
            if reach > 0.02 or 3.4 <= t < 4.7:
                ang = float(np.interp(reach, [0, 1], [78, 14]))     # degrees below horizontal, pointing at the dog
                arm_sc = 0.55 * cam.F / z[0] / 200.0
                Ma = mT(*shoulder) @ mR(ang) @ mS(-arm_sc, arm_sc) @ mT(-384, -70)
                L.append(('person:arm', self.arm_rgb, self.arm_a, Ma, 'silhouette'))
            return L, dict(person='standing', at=P.tolist())
        p, z = cam.project(seat_P)
        hpx = 0.86 * cam.F / z[0]
        sc = hpx / 175.0
        drop = (1 - ease((t - 5.45) / 0.4)) * 30
        M = mT(p[0, 0], p[0, 1] - drop) @ mS(-sc, sc) @ mT(-205, -226)
        L.append(('person:seated', self.s_rgb, self.s_a, M, 'dusk'))
        low = pf['low']
        if low > 0.02:
            shoulder = apply(M, [(196, 104)])[0]
            ang = float(np.interp(low, [0, 1], [80, 34]))
            arm_sc = 0.62 * cam.F / z[0] / 200.0
            Ma = mT(*shoulder) @ mR(ang) @ mS(-arm_sc, arm_sc) @ mT(-384, -70)
            L.append(('person:hand', self.arm_rgb, self.arm_a, Ma, 'hand'))
        return L, dict(person='seated', at=seat_P.tolist())
