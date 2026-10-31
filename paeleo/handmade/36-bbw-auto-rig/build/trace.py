"""SCION-36 · trace.json from what the render measured (meas_*.json): the dog's contact point on the floor inverted
through the camera (x_world_measured), its covered pixels' centroid (x_screen, y_screen), its facing (head left or
right of the tail in the frame), and the choice onsets found from those measurements, not from the score's labels."""
import json, os, glob
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(OUT, '..', '..', '..'))
CACHE = os.path.join(HERE, 'cache')
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
FPS = 24


def main():
    M = []
    for f in sorted(glob.glob(os.path.join(CACHE, 'meas_*.json'))):
        M += json.load(open(f))
    M = sorted({m['i']: m for m in M}.values(), key=lambda m: m['i'])
    assert len(M) == 768, len(M)
    t = np.array([m['i'] / FPS for m in M])
    xw = np.array([m['dog']['x_world_measured'] for m in M])
    xws = np.convolve(np.pad(xw, 2, mode='edge'), np.ones(5) / 5, 'valid')
    v = np.gradient(xws) * FPS
    sc = np.array([m['dog']['scale'] for m in M])
    head_h = np.array([(m['dog']['ground'][1] - m['dog']['head'][1]) / m['dog']['scale'] for m in M])   # source px above ground
    back_h = np.array([(m['dog']['ground'][1] - m['dog']['back_y']) / m['dog']['scale'] for m in M])
    facing = np.array([m['dog']['facing'] for m in M])
    headx = np.array([m['dog']['head'][0] for m in M])
    on = {}
    k = lambda cond, after: int(next(i for i in range(len(M)) if t[i] >= after and cond(i)))
    on['retreat'] = k(lambda i: xw[i] > xw[0] + .02, .3)
    on['watch_1'] = k(lambda i: abs(v[i]) < .35, t[on['retreat']] + .5)
    h0 = head_h[int(3.3 * FPS)]
    on['refuse'] = k(lambda i: head_h[i] < h0 * .92, 3.0)
    on['watch_2'] = k(lambda i: facing[i] == -1, 7.0)
    x14 = xw[int(14.0 * FPS)]
    on['approach'] = k(lambda i: xw[i] < x14 - .02, 14.0)
    b0 = back_h[int(23.5 * FPS)]
    on['lie_down'] = k(lambda i: back_h[i] < b0 * .92, 23.3)
    heady = np.array([m['dog']['head'][1] for m in M])
    hy0 = heady[int(26.2 * FPS)]
    on['look_in'] = k(lambda i: heady[i] < hy0 - 4, 26.2)
    order = [('watch', 0), ('retreat', on['retreat']), ('watch', on['watch_1']), ('refuse', on['refuse']),
             ('watch', on['watch_2']), ('approach', on['approach']), ('lie_down', on['lie_down'])]
    frames = []
    for i, m in enumerate(M):
        st = [s for s, j in order if j <= i][-1]
        d = m['dog']; p = d['pose']
        fold = p.get('fold') or 0
        posture = 'lying' if fold > .6 else ('walking' if SCORE['frames'][i]['dog']['act']['moving'] > .3 else
                                             ('crouched' if (p.get('crouch') or 0) > .3 else 'standing'))
        frames.append({'i': i, 't': round(t[i], 4), 'state': st, 'x_score': SCORE['frames'][i]['dog']['x'],
                       'x_screen': round(d['x_screen'], 1), 'y_screen': round(d['y_screen'], 1),
                       'x_world_measured': round(d['x_world_measured'], 3), 'facing': int(d['facing']),
                       'posture': posture, 'view': d['view'], 'archive_frame': d['frame'],
                       'head_screen': [round(a, 1) for a in d['head']], 'zoom': round(d['zoom'], 3)})
    score_t = {'retreat': 1.0, 'watch_1': 2.333, 'refuse': 3.417, 'watch_2': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
    onsets = {k2: {'frame': j, 't': round(j / FPS, 3), 'score_t': score_t[k2], 'dt': round(j / FPS - score_t[k2], 3)} for k2, j in on.items()}
    how = {'retreat': 'first frame the measured floor position moves away from the door by > 2 cm',
           'watch_1': 'first frame after that the measured speed falls under 0.35 m/s',
           'refuse': 'first frame the head drops more than 8 % below its height at 3.3 s (the flinch that starts the turn)',
           'watch_2': 'first frame the measured head is again on the door side of the tail (facing the door)',
           'approach': 'first frame the measured floor position moves toward the door by > 2 cm',
           'lie_down': 'first frame the measured back line sinks more than 8 % below its height at 23.5 s',
           'look_in': 'first frame the head is 4 px higher on screen (further into the room) than at 26.2 s'}
    json.dump({'about': 'Measured per scene frame from the rendered, skinned meshes (build/render.py writes meas_*.json, '
                        'build/trace.py turns them into this). The camera closes in from 21.5 s to 25 s, so x_world_measured '
                        '(the dog\'s floor contact inverted through that frame\'s camera, metres along the score\'s x) is the '
                        'position measure. facing: -1 = head toward the door (left), +1 = head away. state comes from the '
                        'measured onsets below, not from the score labels.',
               'onsets_measured': onsets, 'onset_rules': how, 'frames': frames},
              open(os.path.join(OUT, 'trace.json'), 'w'), indent=0)
    json.dump({'onsets': onsets}, open(os.path.join(CACHE, 'onsets.json'), 'w'), indent=1)
    for k2, o in onsets.items(): print(k2, o)


if __name__ == '__main__':
    main()
