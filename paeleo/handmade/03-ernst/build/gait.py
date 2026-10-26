"""SCION 03 Ernst · the step solver: nothing slides while it is held.

A foot is a constraint: planted, it stays where it was put (world coordinates) until its turn comes to be lifted; then
it is swung along an arc and set down where the body will want it half a stance later (the solver knows the whole
timeline, so it looks ahead).  Turns come from a gait clock that advances with distance travelled and with the body's
rotation (one stride per 0.54 m, like the score's walk phase), in the lateral sequence of a walking dog:
left hind, left fore, right hind, right fore.  When the clock is still, a foot left too far behind steps by itself.
"""
import numpy as np


def solve(desired, clock=None, offsets=None, period=None, fps=24, thr=0.1, swing=5, lift=0.06, settle=0.07,
          thr_fn=None, pairs=(), free=None, turn_pairs=()):
    """free[i]: the body is turning in place: feet step as soon as they are left behind, one per side at a time,
    quickly (4 frames), landing where the body will want them 3 frames later."""
    feet = list(desired)
    n = len(next(iter(desired.values())))
    pos = {k: np.zeros((n, 3)) for k in feet}
    contact = {k: np.zeros(n, bool) for k in feet}
    planted = {k: desired[k][0].copy() for k in feet}
    st = {k: None for k in feet}
    last_lift = {k: -99 for k in feet}
    events = []
    blocked = {k: set() for k in feet}
    for a, b in pairs:
        blocked[a].add(b); blocked[b].add(a)
    tblocked = {k: set() for k in feet}
    for a, b in turn_pairs:
        tblocked[a].add(b); tblocked[b].add(a)
    for i in range(n):
        th = thr if thr_fn is None else thr_fn(i)
        for k in feet:
            if st[k] is not None:
                continue
            e = np.linalg.norm((planted[k] - desired[k][i])[[0, 2]]) + 2.0 * abs(planted[k][1] - desired[k][i][1])
            go = False
            sw = swing
            if free is not None and free[i]:
                sw = 4
                go = e > 0.05 and i - last_lift[k] > sw
                if go and any(st[o] is not None for o in tblocked[k]):
                    go = False
            elif clock is not None and offsets is not None:
                ph = (clock[i] - offsets[k]) % 1.0
                moving = clock[min(n - 1, i + 6)] - clock[max(0, i - 6)] > 0.02
                if moving:
                    go = ph < 0.2 and e > 0.02 and i - last_lift[k] > swing + 2
                else:
                    go = e > max(th, settle)
            else:
                go = e > th
            if go and any(st[o] is not None for o in blocked[k]):
                go = False
            if go:
                per = period[i] if period is not None else 24
                lead = int(np.clip(0.5 * (per - swing), 1, 16))
                if free is not None and free[i]:
                    lead = 3
                j = min(n - 1, i + sw + lead)
                st[k] = (i, planted[k].copy(), desired[k][j].copy(), sw)
                last_lift[k] = i
        for k in feet:
            s_ = st[k]
            if s_ is None:
                pos[k][i] = planted[k]; contact[k][i] = True
                continue
            i0, a, b, dur = s_
            s = min((i - i0 + 1) / dur, 1.0)
            e = s * s * (3 - 2 * s)
            p = a + (b - a) * e
            dist = np.linalg.norm((b - a)[[0, 2]])
            p[1] += lift * min(1.0, dist / 0.12 + 0.25) * np.sin(np.pi * s)
            pos[k][i] = p
            if s >= 1.0:
                planted[k] = b.copy(); st[k] = None; contact[k][i] = True
                events.append((i, k, float(dist)))
    return pos, contact, events
