"""Sequence optimizer: dynamic-programming decoder over the pose library.

Time base: the score's 24 fps frames, decided on twos (384 decisions, each held 2 frames).
Candidate states: every library drawing, native or mirrored (a mirror is a rigid flip of
the whole drawing; nothing is bent). Typed inputs per candidate: facing (+1 toward the
door = screen-left, -1 away, 0 front), lie, crouch, head, leg spread, face-to-viewer, rest.

Cost = emission (pose features vs the score's state/acting at that frame)
     + transition (visual distance between the two drawings + a swap cost)
     + hold structure (minimum hold of MIN_HOLD twos; while walking, swaps are paid for
       off the footfalls and holds are paid for across a footfall, so drawings change
       on the steps the score's walk_phase gives).
Protected key poses: in the two turning windows after the 3.42 s and 7.46 s choices the
decoder must show a turning/face-to-viewer drawing; facing errors cost more than anything
but the hold rule, so the turned back can never be averaged away.

Writes work/schedule.json (per frame: candidate, drawing, flip, costs) and
work/candidates.json.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import qd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORE = json.load(open(f'{HERE}/../score/threshold-score.json'))
LIB = json.load(open(f'{HERE}/library/pose_library.json'))
DOGS = {int(json.loads(l)['key_id']): json.loads(l) for l in open(f'{HERE}/library/dogs.ndjson')}

MIN_HOLD = 3          # twos (6 frames = 0.25 s)
W = dict(face=7.0, lie=5.0, crouch=2.0, head=2.5, rest=2.0, spread=1.6, flip=0.25,
         viewer_idle=0.9, front_idle=7.0, turn_need=6.0, swap=0.6, vis=2.4,
         hold_over_step=2.2, swap_off_step=1.6, headlow=6.0, profile=6.0, walk_swap_off_step=30.0, stale_stride=8.0)
LONG_HOLD = 24        # twos (2 s): while walking or backing, an identity change at most every 2 s (critic repair 1)
TURN_WINDOWS = [(7.458, 7.458 + 0.36)]  # the refusal at 3.42 cuts straight to the back (tried a front in-between first: it hid the refusal)


def candidates():
    C = []
    for e in LIB['dogs']:
        for flip in (0, 1):
            if e['face'] == 'F' and flip:
                continue
            face = {'L': 1, 'R': -1, 'F': 0}[e['face']]
            if flip:
                face = -face
            post = e['posture']
            C.append(dict(key_id=e['key_id'], idx=e['idx'], flip=flip, face=face, posture=post,
                          lie=1.0 if post == 'lie' else 0.0,
                          crouch={'crouch': .8, 'stand': .12, 'front': .2, 'sit': .3, 'lie': 0.}[post],
                          head=e['head'], spread=e['spread'], viewer=e['viewer'], rest=e['rest'],
                          front=1.0 if post in ('front', 'sit') else 0.0,
                          headlow=float(e.get('headlow', 0)), profile=float(e.get('profile', 0))))
    return C


def placed(c, M=150.0):
    """Return strokes in metres*M px, feet on y=0 and registered at x=0 by the drawing's ink
    centroid (a body registration, so substituted drawings do not jump), mirrored if flip.
    Canonical sizes: side standing/crouching width 1.2 m, lying 1.4 m, front/sitting height 0.85 m,
    and no dog taller than 0.95 m."""
    d = DOGS[int(c['key_id'])]
    S = qd.strokes_np(d)
    x0, y0, x1, y1 = qd.bbox(S)
    w, h = max(x1 - x0, 1), max(y1 - y0, 1)
    if c['posture'] in ('front', 'sit'):
        sc = 0.85 / h
    elif c['posture'] == 'lie':
        sc = 1.4 / w
    else:
        sc = 1.2 / w
    sc = min(sc, 0.95 / h)
    cx = np.concatenate(qd.densify(S, 2.0))[:, 0].mean()
    out = []
    for s in S:
        X = (s[:, 0] - cx) * sc
        Y = (s[:, 1] - y1) * sc
        if c['flip']:
            X = -X
        out.append(np.stack([X * M, Y * M], 1))
    return out


def vis_vectors(C):
    V = []
    for c in C:
        S = placed(c, 34)  # 1 m = 34 px
        img = Image.new('L', (80, 44), 0)
        dr = ImageDraw.Draw(img)
        for s in S:
            pts = [(p[0] + 40, p[1] + 42) for p in s]
            dr.line(pts if len(pts) > 1 else pts * 2, fill=255, width=2)
        a = np.asarray(img, float) / 255
        for _ in range(3):  # box blur so near-misses count as near
            a = (np.roll(a, 1, 0) + a + np.roll(a, -1, 0)) / 3
            a = (np.roll(a, 1, 1) + a + np.roll(a, -1, 1)) / 3
        v = a.ravel()
        V.append(v / (np.linalg.norm(v) + 1e-9))
    V = np.array(V)
    return 1 - V @ V.T  # cosine distance


def main():
    C = candidates()
    N = len(C)
    D = vis_vectors(C)
    frames = SCORE['frames']
    T = len(frames) // 2
    # step events from walk_phase (footfalls at multiples of pi), mapped to twos
    ph = np.array([f['dog']['act']['walk_phase'] for f in frames])
    mov = np.array([f['dog']['act']['moving'] for f in frames])
    un = np.unwrap(ph)
    stepk = np.floor(un / np.pi).astype(int)
    foot = np.zeros(len(frames), bool)
    foot[1:] = (stepk[1:] != stepk[:-1]) & (mov[1:] > 0.3)
    foot2 = np.array([foot[2 * t] or foot[2 * t + 1] for t in range(T)])
    step_parity = stepk % 2

    def attr(k):
        return np.array([c[k] for c in C], float)
    WALKPAIR = {2830, 135}  # the stride twins: dome body, round head low at the chest
    for c in C:
        c['walkpair'] = float(c['idx'] in WALKPAIR)
    A = {k: attr(k) for k in ('face', 'lie', 'crouch', 'head', 'spread', 'viewer', 'rest', 'front', 'flip', 'headlow', 'profile', 'walkpair')}
    E = np.zeros((T, N))
    for t in range(T):
        f = frames[2 * t]
        a = f['dog']['act']
        tt = f['t']
        face_t = f['dog']['face']
        inturn = any(lo <= tt < hi for lo, hi in TURN_WINDOWS)
        e = np.zeros(N)
        if inturn:
            e += W['turn_need'] * (1 - np.maximum(A['front'], A['viewer']))
        else:
            e += W['face'] * (A['face'] != face_t) * (A['front'] == 0)
            e += W['front_idle'] * A['front'] + W['viewer_idle'] * A['viewer']
        st = f['dog']['state']
        lie_t = a['lie']
        crouch_t = a['crouch']
        head_raw = a['head']
        # the choice is the state change: from the frame the state changes, the target is the
        # new state's pose, not the act values easing toward it (a drawn animator keys the change)
        if st == 'retreat':
            crouch_t, head_raw = max(crouch_t, .8), min(head_raw, .5)
        elif st == 'approach':
            crouch_t, head_raw = .12, .45
        elif st == 'lie_down':
            lie_t = 1.0
        e += W['lie'] * np.abs(lie_t - A['lie'])
        e += W['crouch'] * np.abs(crouch_t - A['crouch']) * (1 - A['lie'])
        head_t = min(head_raw, 1.0)
        if a['look'] > 0.5:
            head_t = 1.0
        e += W['head'] * np.abs(head_t - A['head'])
        e += W['rest'] * np.abs(a['rest'] - A['rest']) * A['lie']
        if a['moving'] > 0.3:
            spread_t = 0.85 if step_parity[2 * t] == 0 else 0.15
            e += W['spread'] * a['moving'] * np.abs(spread_t - A['spread'])
        e += W['flip'] * A['flip']
        # round 2 (critic repairs 3 and 4): the approach is head low; looking in is a profile head
        if st == 'approach':
            e += W['headlow'] * (1 - A['headlow'])
            e += 50.0 * (1 - A['walkpair'])  # at most two drawings in the walk, one head shape
        if a['look'] > 0.5:
            e += W['profile'] * (1 - A['profile'])
        E[t] = e

    # Viterbi over states (candidate, hold counter k in 1..MIN_HOLD, MIN_HOLD means "held enough")
    K = LONG_HOLD
    # swaps need MIN_HOLD twos of hold, but LONG_HOLD inside a walk (retreat/approach) once the
    # state is 0.25 s old; the first swap into a new state is free of the long rule
    states = [frames[2 * t]['dog']['state'] for t in range(T)]
    start = [0] * T
    for t in range(1, T):
        start[t] = start[t - 1] if states[t] == states[t - 1] else t
    need = [LONG_HOLD if states[t] in ('approach', 'retreat') and t - start[t] >= 1 else MIN_HOLD for t in range(T)]
    INF = 1e9
    V = np.full((N, K), INF)
    V[:, 0] = E[0]
    BP = np.zeros((T, N, K, 2), np.int32)
    TR = W['swap'] + W['vis'] * D  # N x N
    np.fill_diagonal(TR, INF)
    for t in range(1, T):
        mv = frames[2 * t]['dog']['act']['moving'] > 0.3
        hold_pen = W['hold_over_step'] if (mv and foot2[t]) else 0.0
        swap_pen = W['swap_off_step'] if (mv and not foot2[t]) else 0.0
        if states[t] == 'approach' and t - start[t] >= 3 and not foot2[t]:
            swap_pen = W['walk_swap_off_step']
        NV = np.full((N, K), INF)
        # hold: k -> min(k+1, K)
        stale = W['stale_stride'] if (states[t] == 'approach' and foot2[t]) else 0.0
        for k in range(K):
            k2 = min(k + 1, K - 1)
            cand = V[:, k] + hold_pen + (stale if k == K - 1 else 0.0)
            better = cand < NV[:, k2]
            NV[better, k2] = cand[better]
            BP[t, better, k2] = np.stack([np.nonzero(better)[0], np.full(better.sum(), k)], 1)
        # swap: only from k = K-1 (held long enough) into k = 0 of another drawing
        ready = V[:, need[t] - 1:].min(1)   # held at least need[t] twos (counter saturates at K)
        rk = need[t] - 1 + V[:, need[t] - 1:].argmin(1)
        M = ready[:, None] + TR + swap_pen  # from a (rows) to b (cols)
        a_best = M.argmin(0)
        cand = M[a_best, np.arange(N)]
        better = cand < NV[:, 0]
        NV[better, 0] = cand[better]
        BP[t, better, 0] = np.stack([a_best[better], rk[a_best[better]]], 1)
        V = NV + E[t][:, None]
    # backtrack
    n, k = np.unravel_index(V.argmin(), V.shape)
    path = [0] * T
    for t in range(T - 1, -1, -1):
        path[t] = int(n)
        if t:
            n, k = BP[t, n, k]
    total = float(V.min())
    sched = []
    for i, f in enumerate(frames):
        t2 = i // 2
        c = C[path[t2]]
        sched.append(dict(i=i, t=f['t'], cand=path[t2], key_id=c['key_id'], idx=c['idx'], flip=c['flip'],
                          posture=c['posture'], facing={1: 'toward door', -1: 'away', 0: 'front'}[c['face']],
                          face=c['face'], emission=float(E[t2, path[t2]]), footfall=bool(foot[i])))
    swaps = [s['t'] for a, s in zip(sched, sched[1:]) if s['cand'] != a['cand']]
    used = sorted({s['key_id'] for s in sched})
    print(f'total cost {total:.1f}; swaps {len(swaps)}; distinct drawings used {len(used)}; candidates {N}')
    json.dump(dict(total_cost=total, weights=W, min_hold_twos=MIN_HOLD, turn_windows=TURN_WINDOWS,
                   swaps=swaps, used=used, frames=sched), open(f'{HERE}/work/schedule.json', 'w'))
    json.dump(C, open(f'{HERE}/work/candidates.json', 'w'))
    # human-readable segments
    seg = []
    for s in sched:
        if not seg or seg[-1]['cand'] != s['cand']:
            seg.append(dict(cand=s['cand'], t0=s['t'], key=s['key_id'], post=s['posture'], facing=s['facing'], flip=s['flip'], n=0))
        seg[-1]['n'] += 1
    for g in seg:
        print(f"{g['t0']:6.2f}s  {g['n']:3d}f  {g['post']:6s} {g['facing']:11s} flip={g['flip']}  key {g['key']}")


if __name__ == '__main__':
    main()
