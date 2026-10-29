"""Gather the per-chunk measurements into trace.json (measured onsets), then encode film.mp4 and the stills."""
import glob, json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); C = os.path.join(HERE, 'cache')
sys.path.insert(0, HERE)
import controls as CT
from stage import U0, KX, KZ

def gather():
    M = {}
    for f in glob.glob(os.path.join(C, 'meas_corrected_*.json')):
        for m in json.load(open(f)):
            M[m['i']] = m
    assert len(M) == 768, len(M)
    return [M[i] for i in range(768)]

def onsets(ms, ctrl):
    """choice onsets read from the render (not from the score labels)."""
    cx = np.array([m['cx'] for m in ms]); top = np.array([m['top'] for m in ms]); bot = np.array([m['bottom'] for m in ms])
    hgt = bot - top; hd = np.array([m['head_dir'] for m in ms]); nose_left = np.cos(np.radians(hd)) < 0
    t = np.array([m['t'] for m in ms]); away = np.array([c['away'] for c in ctrl])
    def first(cond, t0):
        idx = np.nonzero(cond & (t >= t0))[0]; return float(t[idx[0]]) if len(idx) else None
    h0 = np.median(hgt[:20]); x0 = cx[0]
    out = {}
    # retreat: the body starts to lower (crouch) or move away from the door
    out['retreat'] = first((hgt < h0 - 2) | (cx > x0 + 2), 0.5)
    # retreat -> watch: the crouched back starts to come up (top of the dog rises 2 px above its crouched level)
    tc = np.median(top[(t >= 1.5) & (t <= 2.2)])
    out['watch'] = first(top < tc - 2, 2.0)
    # refuse: the head direction swings more than 12 degrees off its watching direction
    hw = np.median(hd[60:80])
    dd = np.abs((hd - hw + 180) % 360 - 180)
    out['refuse'] = first(dd > 12, 3.0)
    # refuse -> watch: the nose points back toward the door (screen-left)
    out['watch_again'] = first(nose_left, 7.0)
    # approach: the dog starts to travel toward the door
    out['approach'] = first(cx < cx[340] - 2, 14.0)
    # lie_down: the top of the dog starts to drop at the sill (3 px below its standing level)
    ts = np.median(top[540:568])
    out['lie_down'] = first(top > ts + 3, 22.5)
    # look in: the head starts to turn away into the room (head turn control read with head direction change)
    hr = np.median(hd[620:630])
    out['look_in'] = first(np.abs((hd - hr + 180) % 360 - 180) > 8, 26.0)
    return out

if __name__ == '__main__':
    ctrl = CT.controls(); ms = gather(); on = onsets(ms, ctrl)
    seq = [('watch', 0.0), ('retreat', on['retreat']), ('watch', on['watch']), ('refuse', on['refuse']), ('watch', on['watch_again']),
           ('approach', on['approach']), ('lie_down', on['lie_down'])]
    frames = []
    for m, c in zip(ms, ctrl):
        st = [s for s, t0 in seq if t0 is not None and m['t'] >= t0 - 1e-6][-1]
        facing = 1 if np.cos(np.radians(m['head_dir'])) < 0 else -1
        lie = c['lie']; post = 'lie' if lie > .5 else ('crouch' if c['crouch'] > .5 else ('walk' if abs(c['X'] - ctrl[max(0, m['i'] - 1)]['X']) > 1e-4 else 'stand'))
        if c['away'] > .3: post = 'look_in'
        if 86 <= m['i'] <= 92 or 192 <= m['i'] <= 206: post = 'turn'
        frames.append({'i': m['i'], 't': m['t'], 'state': st, 'state_score': c['state'], 'x_score': c['x_score'],
                       'x_screen': round(m['cx'], 1), 'y_screen': round(m['cy'], 1), 'facing': facing, 'posture': post,
                       'x_world_measured': round((m['cx'] - U0 - KZ * CT.DOG_Z) / KX + CT.X_OFF, 3),
                       'withers_y': m.get('withers_y'), 'head_top_y': m.get('head_top_y'),
                       **{k: m[k] for k in ['top', 'bottom', 'left', 'right', 'head_dir', 'body_dir', 'psi', 'psi_h', 'mirror', 'head_rel', 'ood', 'mahal', 'view_support', 'reach_err']}})
    sc = {'retreat': 1.0, 'watch': 2.333, 'refuse': 3.417, 'watch_again': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
    tr = {'about': 'SCION 15 trace: measured from the rendered frames (alpha centroid, bbox, nose direction from the posed layers). state = segmentation by the measured onsets below; state_score = the score label.',
          'mapping': 'torso centre world X = score x - %.2f m; screen u = %.0f + %.0f * X (oblique projection, static camera); x_world_measured = (centroid u - %.0f - %.0f*%.2f)/%.0f + %.2f' % (CT.X_OFF, U0, KX, U0, KZ, CT.DOG_Z, KX, CT.X_OFF),
          'onsets_measured': {k: {'score': sc[k], 'measured': on[k], 'dt': None if on[k] is None else round(on[k] - sc[k], 3)} for k in sc},
          'frames': frames}
    gap = [f['head_top_y'] - f['withers_y'] for f in frames if 15.0 <= f['t'] <= 23.5 and f['head_top_y'] is not None]
    tr['head_low_approach'] = {'about': 'head top (topmost head-layer pixel) minus withers y, screen px, 15.0-23.5 s; positive = below',
                               'min_px': round(min(gap), 1), 'mean_px': round(sum(gap) / len(gap), 1), 'n': len(gap)}
    print('head low', tr['head_low_approach'])
    json.dump(tr, open(os.path.join(ROOT, 'trace.json'), 'w'), indent=0)
    print(json.dumps(tr['onsets_measured'], indent=1))
