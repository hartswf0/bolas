"""Constraint graph + iterative relaxation solver (SCION 08, Sutherland).

Sketchpad (1963) satisfied constraints by *relaxation*: every constraint is an error
function of a few point coordinates, and the program repeatedly moves variables to
reduce the errors until they are within tolerance.  This module does the same thing
in 3-D metres, Gauss-Seidel style, with typed constraints:

  Dist     a-b distance equals L                (bone length; hard)
  Pin      point is held (inverse mass 0)       (planted foot; hard)
  Floor    point.y >= y0                        (contact / supported-on; hard, inequality)
  Bend     joint j lies on one side of line a-b (joint limit / elbow configuration; hard, inequality)
  Plane    dot(point - anchor, n) == 0           (leg stays in its plane; soft)
  Goal     point -> target with stiffness k     (the animator's / score's request; soft)
  Attach   point := f(graph)                    (attached-to; dependent point, not a variable)

Hard residuals are reported honestly after the last pass; soft goal errors are reported
separately (an unsatisfiable goal is a *state*, not a bug: the reach that cannot reach).
"""
import math
import numpy as np


class Graph:
    def __init__(self, name):
        self.name = name
        self.names = []
        self.idx = {}
        self.P = np.zeros((0, 3))
        self.invm = np.zeros(0)
        self.hard = []      # (kind, params)
        self.soft = []
        self.attach = []    # (i, fn)
        self.last = {}
        self.omega = 1.5
        self.vmax = None
        self.sides = {}
        self.vmax_pt = {}     # metres per frame a goal may pull a point
        self.P0 = None     # successive over-relaxation in the hard-only passes

    # ----- building -------------------------------------------------------
    def point(self, name, xyz, invm=1.0):
        self.idx[name] = len(self.names)
        self.names.append(name)
        self.P = np.vstack([self.P, np.asarray(xyz, float)[None]])
        self.invm = np.append(self.invm, invm)
        self.base_invm = self.invm.copy()
        return self.idx[name]

    def mass(self, name, invm):
        """Relative inertia: a heavy point (small inverse mass) moves less when constraints disagree."""
        self.base_invm[self.idx[name]] = invm

    def i(self, n):
        return self.idx[n]

    def p(self, n):
        return self.P[self.idx[n]]

    def dist(self, a, b, L=None):
        ia, ib = self.idx[a], self.idx[b]
        if L is None:
            L = float(np.linalg.norm(self.P[ia] - self.P[ib]))
        self.hard.append(('dist', (ia, ib, float(L))))

    def wall(self, a, x0, x1, z0):
        """behind / in-front-of: between x0 and x1 the point may not pass the plane z = z0."""
        self.hard.append(('wall', (self.idx[a], x0, x1, z0)))

    def floor(self, a, y0=0.0):
        self.hard.append(('floor', (self.idx[a], y0)))

    def bend(self, a, j, b, sign, margin=0.012, key=None):
        """j must sit on the `sign` side of line a->b, measured in the joint's plane.
        The plane normal is supplied per frame through self.side (lateral axis)."""
        self.hard.append(('bend', (self.idx[a], self.idx[j], self.idx[b], sign, margin, key)))

    def attach_pt(self, name, fn, soft=0.0):
        """attached-to. soft=0: a dependent point (overwritten each pass).
        soft>0: a real variable pulled toward fn(G) (used with rigid distances)."""
        self.attach.append((self.idx[name], fn, soft))

    def rigid(self, name, refs):
        """Hold `name` at its current distances from the reference points (a rigid link)."""
        for r in refs:
            self.dist(name, r)

    def dist_names(self):
        return [(self.names[a], self.names[b], L) for k, (a, b, L) in
                [(k, p) for k, p in self.hard if k == 'dist']]

    # ----- per-frame requests --------------------------------------------
    def clear_frame(self):
        self.soft = []
        self.invm[:] = self.base_invm

    def pin(self, n, xyz):
        i = self.idx[n]
        self.P[i] = xyz
        self.invm[i] = 0.0

    def goal(self, n, xyz, k=0.3, tag=None):
        self.soft.append(('goal', (self.idx[n], np.asarray(xyz, float), k, tag or n)))

    def plane(self, n, anchor, normal, k=0.5):
        self.soft.append(('plane', (self.idx[n], self.idx[anchor], np.asarray(normal, float), k)))

    # ----- solving ---------------------------------------------------------
    def _attach(self):
        for i, fn, soft in self.attach:
            if soft == 0.0:
                self.P[i] = fn(self)

    def _project_hard(self, omega=1.0):
        P, w = self.P, self.invm
        side = self.side
        for kind, prm in self.hard:
            if kind == 'dist':
                a, b, L = prm
                wa, wb = w[a], w[b]
                s = wa + wb
                if s == 0:
                    continue
                d = P[b] - P[a]
                n = math.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]) + 1e-12
                c = omega * (n - L) / (n * s)
                P[a] += wa * c * d
                P[b] -= wb * c * d
            elif kind == 'floor':
                a, y0 = prm
                if P[a][1] < y0 and w[a] > 0:
                    P[a][1] = y0
            elif kind == 'wall':
                a, x0, x1, z0 = prm
                if x0 < P[a][0] < x1 and P[a][2] < z0 and w[a] > 0:
                    P[a][2] = z0
            elif kind == 'bend':
                a, j, b, sign, m, key = prm
                if w[j] == 0:
                    continue
                side = self.sides[key] if key else self.side
                ab = P[b] - P[a]
                L = np.linalg.norm(ab) + 1e-12
                u = ab / L
                perp = np.cross(side, u)          # in-plane perpendicular to a->b
                off = float(np.dot(P[j] - P[a], perp)) * sign
                if off < m:
                    P[j] += perp * sign * (m - off)

    def _apply_soft(self):
        P, w = self.P, self.invm
        for i, fn, soft in self.attach:
            if soft > 0.0 and w[i] > 0:
                P[i] += soft * (fn(self) - P[i])
        for kind, prm in self.soft:
            if kind == 'goal':
                i, t, k, _ = prm
                if w[i] > 0:
                    vm = self.vmax_pt.get(i, self.vmax)
                    if vm is not None:
                        # no hidden teleporting: a request farther than vm from where the point
                        # was last frame is only followed vm of the way this frame
                        d = t - self.P0[i]; n = math.sqrt(float(d @ d))
                        if n > vm:
                            t = self.P0[i] + d * (vm / n)
                    P[i] += k * (t - P[i])
            elif kind == 'plane':
                i, a, n, k = prm
                if w[i] > 0:
                    e = float(np.dot(P[i] - P[a], n))
                    P[i] -= k * e * n

    def residuals(self):
        P, w = self.P, self.invm
        out = {'dist': 0.0, 'floor': 0.0, 'bend': 0.0, 'wall': 0.0}
        worst = None
        for kind, prm in self.hard:
            if kind == 'dist':
                a, b, L = prm
                e = abs(np.linalg.norm(P[b] - P[a]) - L)
            elif kind == 'floor':
                a, y0 = prm
                e = max(0.0, y0 - P[a][1])
            elif kind == 'wall':
                a, x0, x1, z0 = prm
                e = max(0.0, z0 - P[a][2]) if x0 < P[a][0] < x1 else 0.0
            else:
                a, j, b, sign, m, key = prm
                ab = P[b] - P[a]
                u = ab / (np.linalg.norm(ab) + 1e-12)
                perp = np.cross(self.sides[key] if key else self.side, u)
                off = float(np.dot(P[j] - P[a], perp)) * sign
                e = max(0.0, -off)                # only a *wrong-side* joint is a violation
            if e > out[kind]:
                out[kind] = e
            if worst is None or e > worst[0]:
                worst = (e, kind, prm)
        goals = {}
        for kind, prm in self.soft:
            if kind == 'goal':
                i, t, k, tag = prm
                goals[tag] = float(np.linalg.norm(P[i] - t))
        hard_max = max(out.values()) if out else 0.0
        return hard_max, out, goals

    def solve(self, iters=80, tol=2e-4, hard_tail=25, check_every=5):
        """Relaxation: alternate soft requests and hard projections; finish with
        hard-only passes until the worst hard error is under tol (or budget ends)."""
        n_used = 0
        self.P0 = self.P.copy()
        for it in range(iters):
            self._apply_soft()
            self._attach()
            self._project_hard()
            n_used += 1
        for it in range(hard_tail):
            self._attach()
            self._project_hard(self.omega)
            n_used += 1
            if it % check_every == check_every - 1:
                hm, _, _ = self.residuals()
                if hm < tol:
                    break
        self._attach()
        hm, per, goals = self.residuals()
        self.last = {'iters': n_used, 'hard_max': hm, 'per_kind': per, 'goals': goals}
        return self.last
