"""SCION 42 · from the score's acting intentions to a pose of the learned puppet.

Learned:   the layers, their hinges, and every example motion (library walk_up: the source dog's own walk, frames 0-13;
           walk_low: frames 40-46, mirrored).  Gait = the walk_up example poses, looped where the learned pose comes back
           closest to itself; head-low walking = walk_up legs with the head/neck local motion of walk_low.
Override:  rotations about the learned hinges, used only outside the examples (lying, chin down, the look in) and named
           in the trace as 'override' with the extrapolation amount.
Part names come from the kit's hand-placed keypoints on the template frame (naming only; the parts were not drawn).
"""
import os
import numpy as np

NAMES = None
HL = [12, 18]
LOOK = [0, -38]   # neck, head (deg): muzzle brought level, pointing into the room   # neck, head (deg) for the head carried low: neck down, muzzle kept forward


def name_parts(pp):
    import json, os
    from scipy.spatial import cKDTree
    kp = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit', 'archive-dog',
                                     'pose_agent_v8.json')))[str(int(pp.M['template_frame']))]
    t = cKDTree(pp.M['p']); lab = pp.M['lab']
    def at(q): return int(lab[t.query(q)[1]])
    n = {}
    n['head'] = at(kp['nose']); n['foreleg'] = at(kp['f2']); n['hind'] = at(kp['h2']); n['tail'] = at(kp['tail'])
    n['trunk'] = int(pp.root)
    n['neck'] = int(pp.parent[n['head']]) if int(pp.parent[n['head']]) != n['trunk'] else -1
    n['shoulder'] = int(pp.parent[n['foreleg']]) if int(pp.parent[n['foreleg']]) != n['trunk'] else -1
    rest = [k for k in range(pp.K) if k not in n.values()]
    for k in rest: n['back%d' % k] = k
    return n


def lerp_rel(a, b, t): return a * (1 - t) + b * t


class Poser:
    def __init__(self, pp):
        self.pp = pp
        self.n = name_parts(pp)
        up = pp.lib['walk_up']; low = pp.lib['walk_low']
        # a loop in the learned walk: the pair of example frames (gap >= 6) whose poses are closest
        best = None
        for i in range(len(up)):
            for j in range(i + 6, len(up)):
                d = np.sum((up[i] - up[j])[:, :2] ** 2 * np.array([2000, 2000, 1])[None, None])
                if best is None or d < best[0]: best = (d, i, j)
        self.loop = (best[1], best[2]); self.loop_err = float(np.sqrt(best[0] / self.pp.K))
        self.up = up; self.low = low
        # local (parent-relative) motion of head and neck in the head-low examples (mean)
        def local(rel, k):
            p = int(pp.parent[k]); return np.linalg.inv(rel[:, p]) @ rel[:, k]
        self.low_local = {}
        for nm in ('head', 'neck'):
            k = self.n[nm]
            if k >= 0: self.low_local[k] = local(low, k).mean(0)
        self.up_local = {}
        for nm in ('head', 'neck'):
            k = self.n[nm]
            if k >= 0: self.up_local[k] = local(up, k).mean(0)
        self.stand = up[self.loop[0]]
        # learned depth-turn of the head: the anisotropic stretch of the head layer (relative to the neck) fitted to
        # archive frame 20, where the dog's head is turned across the line of sight
        try:
            Tn = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model', 'turn.npz'))
            j = list(Tn['frames']).index(20); A = Tn['learned'][j]
            def t3(a): m = np.eye(3); m[:2] = a; return m
            hk, nk = self.n['head'], int(pp.parent[self.n['head']])
            L = np.linalg.inv(t3(A[nk])) @ t3(A[hk])
            U, S_, Vt = np.linalg.svd(L[:2, :2])
            self.head_depth_stretch = Vt.T @ np.diag(S_ / S_.max()) @ Vt       # symmetric stretch, major axis 1
            self.head_depth_src = dict(frame=20, singular_values=S_.tolist())
        except Exception:
            self.head_depth_stretch = None
        # authored depth: the head and neck are in front of the chest in profile
        pp.front = [k for k in (self.n['neck'], self.n['head']) if k >= 0]

    def gait(self, phase):
        """learned pose at walk phase (radians): interpolate the looped example frames"""
        i0, i1 = self.loop; L = i1 - i0
        u = (phase / (2 * np.pi)) % 1.0 * L
        a = int(np.floor(u)); f = u - a
        A = self.up[i0 + a]; B = self.up[i0 + (a + 1) % L if a + 1 < L else i0]
        return lerp_rel(A, B, f)

    def head_low_mix(self, rel, amt):
        """replace head/neck local motion by a blend toward the learned head-low local motion"""
        if amt <= 0: return rel
        rel = rel.copy(); pp = self.pp
        for nm in ('neck', 'head'):
            k = self.n[nm]
            if k < 0: continue
            p = int(pp.parent[k])
            cur = np.linalg.inv(rel[p]) @ rel[k]
            tgt = lerp_rel(cur, self.low_local[k], amt)
            rel[k] = rel[p] @ tgt
        return rel

    def pose(self, phase=0.0, moving=0.0, head_low=0.0, lie=0.0, rest=0.0, look=0.0, crouch=0.0, breathe=0.0,
             head_lift=0.0, wag=0.0, lie_angles=None, head_depth=0.0):
        """returns (T: K x 3x3 dog space, info dict).  head_low 0..1 (1 = the learned head-low), lie/rest/look 0..1"""
        n = self.n
        rel = lerp_rel(self.stand, self.gait(phase), np.clip(moving, 0, 1))
        rel = self.head_low_mix(rel, head_low)
        ang = {}
        ov = 0.0
        # leg swing keyed to the score's walk phase (override): stance sweeps the foot back at the travel speed
        # (stride 0.55 m per cycle = 71 template px at the film's scale), swing returns it fast
        if moving > 0.05:
            for nm, off, L in (('shoulder', 0.0, 73.0), ('hind', np.pi, 46.0)):
                k = n[nm] if n[nm] >= 0 else n['foreleg']
                A = 71.0 * 0.6 / (2 * L)
                u = ((phase + off) / (2 * np.pi)) % 1.0
                th = A - 2 * A * u / 0.6 if u < 0.6 else -A + 2 * A * (0.5 - 0.5 * np.cos(np.pi * (u - 0.6) / 0.4))
                ang[k] = ang.get(k, 0) + th * min(1, moving)
                if nm == 'shoulder' and u >= 0.6 and n['foreleg'] >= 0:
                    ang[n['foreleg']] = ang.get(n['foreleg'], 0) + 0.5 * np.sin(np.pi * (u - 0.6) / 0.4) * min(1, moving)
        # head carried low (override beyond the learned head-low examples, which only lower it a little)
        if head_low > 0:
            if n['neck'] >= 0: ang[n['neck']] = ang.get(n['neck'], 0) - np.radians(HL[0]) * head_low
            ang[n['head']] = ang.get(n['head'], 0) - np.radians(HL[1]) * head_low
            ov = max(ov, 0.5 * head_low)
        # lying down (override): fore leg folded under the chest (elbow forward, paw tucked), hind leg folded up along
        # the belly (drawn behind the trunk, the haunch stays in front), trunk lowered on to the boards
        LA = dict(shoulder=10, foreleg=72, hind=120)
        if lie_angles: LA.update(lie_angles)
        self.pp.behind = {n['hind']} if lie > 0.5 else set()
        self.pp.hard_set = {n['hind']} if lie > 0.3 else set()
        if lie > 0:
            if n['foreleg'] >= 0: ang[n['foreleg']] = ang.get(n['foreleg'], 0) + np.radians(LA['foreleg']) * lie
            if n['shoulder'] >= 0: ang[n['shoulder']] = ang.get(n['shoulder'], 0) + np.radians(LA['shoulder']) * lie
            ang[n['hind']] = np.radians(LA['hind']) * lie
            if n['tail'] >= 0 and int(self.pp.parent[n['tail']]) == n['hind']:
                ang[n['tail']] = -np.radians(LA['hind']) * lie
            ov = max(ov, lie)
        # chin down (override)
        if rest > 0:
            if n['neck'] >= 0: ang[n['neck']] = ang.get(n['neck'], 0) - np.radians(30) * rest
            ang[n['head']] = ang.get(n['head'], 0) - np.radians(30) * rest
            ov = max(ov, rest)
        # look in (override): head lifts and reaches forward into the room
        if look > 0:
            # the look in: the head lifts off the paws (the turn into depth is head_depth, learned from frame 20)
            if n['neck'] >= 0: ang[n['neck']] = ang.get(n['neck'], 0) + np.radians(LOOK[0]) * look
            ang[n['head']] = ang.get(n['head'], 0) + np.radians(LOOK[1]) * look
            ov = max(ov, look)
        if wag and n['tail'] >= 0:
            ang[n['tail']] = ang.get(n['tail'], 0) + wag
        if head_lift:
            ang[n['head']] = ang.get(n['head'], 0) + head_lift
        T = self.pp.articulate(rel, ang)
        if head_depth > 0 and self.head_depth_stretch is not None:
            # the head turns in depth (learned stretch from frame 20), about the neck hinge
            hk = n['head']; nk = int(self.pp.parent[hk])
            piv = self.pp.pivot[(hk, nk)]
            Sm = np.eye(2) * (1 - head_depth) + self.head_depth_stretch * head_depth
            C = np.eye(3); C[:2, :2] = Sm; C[:2, 2] = piv - Sm @ piv
            T[hk] = T[hk] @ C
        if head_low > 0:
            # head carried low: head and neck lowered and brought forward of the chest (override)
            Tr = np.eye(3); Tr[0, 2] = -7.0 * head_low; Tr[1, 2] = 24.0 * head_low
            for k in (n['head'], n['neck']):
                if k >= 0: T[k] = Tr @ T[k]
        # trunk lowered (lie, crouch) and breathing: a translation/scale of the whole dog in dog space
        drop = 44.0 * lie + 9.0 * crouch
        S = np.eye(3); S[1, 2] = drop
        if breathe:
            c = self.pp.anchor
            B = np.eye(3); B[1, 1] = 1 + breathe; B[1, 2] = -breathe * c[1]
            S = S @ B
        T = np.einsum('ij,kjl->kil', S, T)
        return T, dict(override=float(ov), angles={int(k): float(v) for k, v in ang.items()})
