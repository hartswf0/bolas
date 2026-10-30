"""trace.json: what the dog did, per scene frame, measured from the rendered board (cache/measure_*.jsonl: the cells the
dog occupies, where its head cells sit against its body cells), joined to what the machine decided (state, drives).
Also the measured onsets of the choices, found in the measurements alone (no state labels used)."""
import json, glob, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
CACHE = os.path.join(HERE, 'cache')


def load_meas():
    m = {}
    for fn in sorted(glob.glob(os.path.join(CACHE, 'measure_*.jsonl'))):
        for line in open(fn):
            r = json.loads(line)
            m[r['i']] = r
    return [m[i] for i in range(len(m))]


def smooth(a, k=2):
    out = []
    for i in range(len(a)):
        seg = [v for v in a[max(0, i - k):i + k + 1] if v is not None]
        out.append(sum(seg) / len(seg) if seg else None)
    return out


def main():
    M = json.load(open(os.path.join(CACHE, 'machine.json')))
    fr = M['frames']
    ms = load_meas()
    assert len(ms) == len(fr) == 768, (len(ms), len(fr))
    import render as Rn
    rows = []
    for f, m in zip(fr, ms):
        # where the dog's TORSO cells are, cast back onto its path (z = 0) through the camera that rendered the frame
        if m.get('body'):
            Rn.set_camera(m['camera'])
            m['x_world_measured'] = round(Rn.backproject_x(m['body'][0], m['body'][1]), 4)
        hd, bd = m.get('head'), m.get('body')
        facing = None
        if hd and bd:
            facing = 1 if hd[0] < bd[0] else -1          # the door is screen-left in both shots
        h = m['bottom'] - m['top'] if m.get('n') else None
        w = m['right'] - m['left'] if m.get('n') else None
        rows.append({'i': f['i'], 't': round(f['t'], 4), 'state': f['state'], 'sub': f['sub'], 'x_score': f['x'],
                     'x_screen': round(m['cx'], 1) if m.get('n') else None, 'y_screen': round(m['cy'], 1) if m.get('n') else None,
                     'x_world_measured': m.get('x_world_measured'), 'camera': m.get('camera'),
                     'facing': facing, 'height_px': h, 'width_px': w,
                     'head_screen': hd[:2] if hd else None, 'body_screen': bd[:2] if bd else None,
                     'cells': m.get('n'), 'flips': m.get('flips'),
                     'drives': f['drives'], 'U': f['U']})
    # posture, measured: height of the dog's cells against its standing height in the same shot
    for cam in ('wide', 'close'):
        hs = [r['height_px'] for r in rows if r['camera'] == cam and r['state'] in ('watch', 'approach') and r['height_px']]
        ref = sorted(hs)[int(len(hs) * 0.8)] if hs else None
        for r in rows:
            if r['camera'] == cam and r['height_px'] and ref:
                q = r['height_px'] / ref
                r['posture'] = 'lying' if q < 0.62 else ('low' if q < 0.85 else 'standing')
    # ---- measured onsets, from the measurements only
    X = smooth([r['x_world_measured'] for r in rows], 2)
    V = [None] + [None if (X[i] is None or X[i - 1] is None) else (X[i] - X[i - 1]) * 24 for i in range(1, len(X))]
    V = smooth(V, 2)
    T = [r['t'] for r in rows]

    def first(pred, lo, hi, run=3):
        for i in range(len(rows)):
            if lo <= T[i] <= hi and all(0 <= i + k < len(rows) and pred(i + k) for k in range(run)):
                return i
        return None

    def rel(i):
        r = rows[i]
        if not r['head_screen'] or not r['body_screen']:
            return None
        return (r['head_screen'][0] - r['body_screen'][0], r['head_screen'][1] - r['body_screen'][1])

    on = {}
    i = first(lambda k: V[k] is not None and V[k] > 0.04, 0.5, 2.0)
    on['retreat (backs away)'] = i
    pk = max(range(i, i + 40), key=lambda k: V[k] or 0)
    on['retreat -> watch (stops backing)'] = first(lambda k: V[k] is not None and V[k] < 0.75 * V[pk], T[pk], 3.3, run=4)
    r0 = rel(first(lambda k: True, 3.0, 3.1, 1))
    on['refuse (head swings away)'] = first(lambda k: rel(k) and math.hypot(rel(k)[0] - r0[0], rel(k)[1] - r0[1]) > 8, 3.2, 4.5)
    r1 = rel(first(lambda k: True, 7.1, 7.2, 1))
    on['refuse -> watch (head comes round)'] = first(lambda k: rel(k) and math.hypot(rel(k)[0] - r1[0], rel(k)[1] - r1[1]) > 6, 7.2, 8.6)
    on['approach (comes)'] = first(lambda k: V[k] is not None and V[k] < -0.04, 13.0, 16.0)
    hs = [r['height_px'] for r in rows]
    h_app = sum(hs[k] for k in range(int(22.5 * 24), int(23.3 * 24))) / (0.8 * 24)
    on['lie_down (lowers onto the sill)'] = first(lambda k: hs[k] < 0.93 * h_app, 23.0, 25.0)
    r2 = rel(first(lambda k: True, 26.0, 26.1, 1))
    on['looks in (head lifts into the doorway)'] = first(lambda k: rel(k) and math.hypot(rel(k)[0] - r2[0], rel(k)[1] - r2[1]) > 6, 26.1, 27.5)
    r3 = rel(first(lambda k: True, 27.6, 27.7, 1))
    on['settles (chin back down)'] = first(lambda k: rel(k) and math.hypot(rel(k)[0] - r3[0], rel(k)[1] - r3[1]) > 6, 27.7, 30.0)
    score_t = [1.0, 2.333, 3.417, 7.458, 14.708, 23.792, 26.4, 28.1]
    measured = []
    for (k, v), st in zip(on.items(), score_t):
        measured.append({'choice': k, 'score_t': st, 'measured_t': None if v is None else round(T[v], 3), 'dt': None if v is None else round(T[v] - st, 3)})
    mach = M['onsets']
    out = {'about': 'SCION-48 trace: per scene frame, the state the dog\'s own machine chose (state, sub) and what the board showed, measured '
                    'from the rendered cells: x_screen/y_screen = centroid of the dog\'s discs (film pixels), x_world_measured = the centroid of its torso cells '
                    'cast back onto the dog\'s path (score metres; the camera cuts at 24.625 s), facing = +1 when the head cells sit door-side '
                    'of the body cells, posture from the height of the dog\'s cells. x_score is the machine\'s own position.',
           'measured_onsets': measured, 'machine_onsets': mach, 'frames': rows}
    json.dump(out, open(os.path.join(FOLDER, 'trace.json'), 'w'))
    for m in measured:
        print(m)


if __name__ == '__main__':
    main()
