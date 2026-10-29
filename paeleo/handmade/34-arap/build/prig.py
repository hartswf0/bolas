"""The person's handles: standing and seated bodies and the near arm, each its own ARAP mesh."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import Piece, rot
from arap import ARAP, rigid_targets


class Person:
    def __init__(self):
        st, si, ar = Piece('Q_stand'), Piece('Q_sit'), Piece('Q_arm')
        self.st, self.si, self.ar = st, si, ar
        H = {}
        H['foot_f'] = st.group(np.array([130.0, 30.0]), 120, parts=['shoe_front'])
        H['foot_b'] = st.group(np.array([-60.0, 30.0]), 110, parts=['shoe_back'])
        H['hip'] = st.group(np.array([0.0, 1050.0]), 75, parts=['torso', 'smock'])
        H['chest'] = st.group(np.array([20.0, 1300.0]), 75, parts=['torso'])
        H['head'] = st.group(np.array([30.0, 1600.0]), 85, parts=['head', 'hair'])
        H['hem'] = st.group(np.array([20.0, 300.0]), 70, parts=['smock'])
        self.Hs = {k: v for k, v in H.items() if len(v)}
        self.cs = {k: st.V[v].mean(0) for k, v in self.Hs.items()}
        self.ss = ARAP(st.V, st.T, st.weight, self.Hs)
        G = {}
        G['hip'] = si.group(np.array([-20.0, 500.0]), 80, parts=['torso', 'smock'])
        G['knee'] = si.group(np.array([360.0, 520.0]), 55, parts=['smock'])
        G['foot'] = si.group(np.array([420.0, 30.0]), 120, parts=['shoe_front'])
        G['chest'] = si.group(np.array([30.0, 880.0]), 75, parts=['torso'])
        G['head'] = si.group(np.array([45.0, 1210.0]), 85, parts=['head', 'hair'])
        self.Hi = {k: v for k, v in G.items() if len(v)}
        self.ci = {k: si.V[v].mean(0) for k, v in self.Hi.items()}
        self.si_s = ARAP(si.V, si.T, si.weight, self.Hi)
        A = {'shoulder': ar.group(np.array([0.0, -30.0]), 45), 'elbow': ar.group(np.array([8.0, -260.0]), 30),
             'hand': ar.group(np.array([28.0, -570.0]), 48)}
        self.Ha = {k: v for k, v in A.items() if len(v)}
        self.ca = {k: ar.V[v].mean(0) for k, v in self.Ha.items()}
        self.sa = ARAP(ar.V, ar.T, ar.weight, self.Ha)

    def solve(self, p, t):
        """p: person plan entry. Returns list of (piece, X) in the person's frame (mm, feet at y=0, facing right)."""
        out = []
        lean = p['lean']; ha = p['head_a']
        if p['sit'] < 0.5:
            pre = np.clip((p['sit'] - 0.15) / 0.35, 0, 1)        # bending toward the stool
            tg = {}
            ph = p['step_phase']
            k = int(ph); u = ph - k
            lift = np.sin(np.pi * u) if p['walk'] < 1 and p['walk'] > 0 else 0.0
            back = -950.0 * p['walk']                              # the body moves back with her steps (mm)
            # feet: alternate; each step moves one foot back by a share of the distance
            nsteps = 3
            fb = back
            ff_cnt = np.clip(ph - 0.0, 0, nsteps); fb_cnt = np.clip(ph - 0.5, 0, nsteps)
            dfoot = -950.0 / nsteps
            def foot_x(cnt):
                kk = int(cnt); uu = cnt - kk
                return dfoot * (kk + (uu * uu * (3 - 2 * uu)))
            off_f = foot_x(ff_cnt); off_b = foot_x(fb_cnt)
            lf = 40 * np.sin(np.pi * (ff_cnt % 1)) if 0 < ff_cnt < nsteps else 0
            lb = 40 * np.sin(np.pi * (fb_cnt % 1)) if 0 < fb_cnt < nsteps else 0
            tg['foot_f'] = rigid_targets(self.st.V, self.Hs['foot_f'], self.cs['foot_f'], self.cs['foot_f'] + [off_f, lf], 0)
            tg['foot_b'] = rigid_targets(self.st.V, self.Hs['foot_b'], self.cs['foot_b'], self.cs['foot_b'] + [off_b, lb], 0)
            hipc = self.cs['hip'] + [back - 160 * pre, -330 * pre + 12 * np.sin(np.pi * u) * (0 < p['walk'] < 1)]
            tg['hip'] = rigid_targets(self.st.V, self.Hs['hip'], self.cs['hip'], hipc, 0.25 * pre)
            hem = self.cs['hem'] + [back * 0.98 + 60 * pre, -40 * pre]
            tg['hem'] = rigid_targets(self.st.V, self.Hs['hem'], self.cs['hem'], hem, 0)
            L = -lean - 0.35 * pre
            for k2 in ('chest', 'head'):
                c = self.cs[k2]
                newc = hipc + rot(c - self.cs['hip'], L)
                tg[k2] = rigid_targets(self.st.V, self.Hs[k2], c, newc, L + (ha if k2 == 'head' else 0))
            X = self.ss.solve_repair(tg, iters=6)
            out.append(('stand', X))
            shoulder = hipc + rot(np.array([15.0, 1360.0]) - self.cs['hip'], L)
            body_rot = L
        else:
            settle = np.clip((0.75 - p['sit']) / 0.25, 0, 1)        # arrives a little high and settles
            tg = {}
            for k2 in ('foot',):
                tg[k2] = rigid_targets(self.si.V, self.Hi[k2], self.ci[k2], self.ci[k2], 0)
            hipc = self.ci['hip'] + [0, 60 * settle]
            tg['hip'] = rigid_targets(self.si.V, self.Hi['hip'], self.ci['hip'], hipc, 0)
            tg['knee'] = rigid_targets(self.si.V, self.Hi['knee'], self.ci['knee'], self.ci['knee'] + [0, 40 * settle], 0)
            L = -0.12 * p['low'] - 0.5 * lean
            for k2 in ('chest', 'head'):
                c = self.ci[k2]
                newc = hipc + rot(c - self.ci['hip'], L)
                tg[k2] = rigid_targets(self.si.V, self.Hi[k2], c, newc, L + (ha if k2 == 'head' else 0))
            X = self.si_s.solve_repair(tg, iters=6)
            out.append(('sit', X))
            shoulder = hipc + rot(np.array([30.0, 970.0]) - self.ci['hip'], L)
            body_rot = L
        # the arm: shoulder pinned to the body; elbow and hand by the plan's angles (0 = hanging; + = forward)
        sh = p['sh'] - body_rot * 0.0
        el = p['el']
        a1 = sh + body_rot
        elbow = shoulder + rot(np.array([8.0, -260.0]), a1)
        hand = elbow + rot(np.array([20.0, -310.0]), a1 + el)
        tg = {'shoulder': rigid_targets(self.ar.V, self.Ha['shoulder'], self.ca['shoulder'], shoulder + rot(self.ca['shoulder'], a1), a1),
              'elbow': rigid_targets(self.ar.V, self.Ha['elbow'], self.ca['elbow'], elbow, a1 + el * 0.5),
              'hand': rigid_targets(self.ar.V, self.Ha['hand'], self.ca['hand'], hand, a1 + el + p['hand_a'])}
        Xa = self.sa.solve_repair(tg, iters=6)
        out.append(('arm', Xa))
        return out
