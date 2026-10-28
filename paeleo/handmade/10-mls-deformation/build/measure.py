"""SCION-10 · the trace, measured from the render: cache/raw/*.json (written by render.py from each frame's own buffers:
the dog's visible pixels, its rendered head and trunk samples in world metres, heights) -> ../trace.json, ../proof/onsets.json.

What is measured (not copied from the score):
  x_screen, y_screen     centroid of the dog's visible pixels in the frame (after depth test against the set)
  x_world_measured       centroid of the rendered trunk samples along the porch, + 0.49 (back into score metres)
  facing                 +1 when the rendered head lies toward the door from the trunk (head x < trunk x), -1 when away
  back_z, head_top_z     95th-percentile height of the rendered trunk / head samples
  posture                lying (back_z < 0.40), crouched (back_z < 0.50 standing), standing
  head_low               head top below the back line (head_top_z < back_z)
  looking_in             the nose handle (which the rendered muzzle passes through: MLS interpolates its handles) is inside
                         the door frame (x < 0) and points into the room (nose x < skull x - 0.12)
  state (measured)       refuse: facing -1 (back to the door)
                         lie_down: lying, facing the door, at the sill (trunk x < 0.75 m world)
                         retreat: facing the door and moving away (> 0.10 m/s), or, once retreating, still cowering
                                  (back_z < 0.47 and head below the back)
                         approach: facing the door, moving toward it (< -0.10 m/s) or head-low and still advancing
                         watch: otherwise
  x_score                the score's x for the frame (what the dog was asked to do), kept for the I2 check"""
import glob, json, os
import numpy as np

H = os.path.dirname(os.path.abspath(__file__))
SCORE = json.load(open(os.path.join(H, '..', '..', 'score', 'threshold-score.json')))
FR = SCORE['frames']
X_OFF = 0.49


def main():
    raws = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(H, 'cache', 'raw', '*.json')))]
    assert len(raws) == len(FR), (len(raws), len(FR))
    t = np.array([r['t'] for r in raws])
    xw = np.array([r['trunk_world'][0] for r in raws])
    hx = np.array([r['head_world'][0] for r in raws])
    back = np.array([r['back_z'] for r in raws]); htop = np.array([r['head_top_z'] for r in raws])
    k = np.exp(-0.5 * (np.arange(-4, 5) / 2.0) ** 2); k /= k.sum()
    xs = np.convolve(np.pad(xw, 4, mode='edge'), k, mode='valid')
    v = np.gradient(xs) * 24
    frames = []
    state = 'watch'
    for i, r in enumerate(raws):
        facing = 1 if hx[i] < xw[i] else -1
        lying = back[i] < 0.40
        crouched = (not lying) and back[i] < 0.50
        head_low = htop[i] < back[i]
        nose, skull = r['nose_world'], r['skull_world']
        looking_in = nose[0] < 0 and nose[0] < skull[0] - 0.12
        if facing < 0:
            s = 'refuse'
        elif lying and xw[i] < 0.75:
            s = 'lie_down'
        elif v[i] > 0.10 or (state == 'retreat' and back[i] < 0.47 and head_low):
            s = 'retreat'
        elif v[i] < -0.10 or (state == 'approach' and head_low and not lying):
            s = 'approach'
        else:
            s = 'watch'
        state = s
        frames.append({'i': i, 't': r['t'], 'state': s, 'score_state': FR[i]['dog']['state'], 'x_score': FR[i]['dog']['x'],
                       'x_screen': round(r['x_screen'], 2), 'y_screen': round(r['y_screen'], 2), 'x_world_measured': round(float(xw[i] + X_OFF), 4),
                       'facing': facing, 'posture': 'lying' if lying else ('crouched' if crouched else 'standing'),
                       'back_z_m': round(float(back[i]), 3), 'head_top_z_m': round(float(htop[i]), 3), 'head_low': bool(head_low),
                       'velocity_mps': round(float(v[i]), 3), 'head_screen': r['head_screen'], 'looking_in': bool(looking_in),
                       'dog_min_x_world_m': round(r['min_x_world'], 3), 'dog_max_x_world_m': round(r['max_x_world'], 3),
                       'paw_z_m': [round(z, 3) for z in r['paw_z']]})
    about = ('SCION-10 trace, measured from the rendered frames (see build/measure.py for every definition). x_world_measured is '
             'the rendered trunk centroid along the porch in score metres; the camera is fixed. state is inferred from measured '
             'facing, posture, head height and velocity, not copied from the score (score_state is kept beside it).')
    json.dump({'about': about, 'frames': frames}, open(os.path.join(H, '..', 'trace.json'), 'w'), indent=0)
    # onsets
    on = []
    for c in SCORE['choices']:
        hit = next((f for f in frames if f['t'] >= c['t'] - 0.5 and f['state'] == c['to']), None)
        on.append({'score_t': c['t'], 'to': c['to'], 'measured_t': hit['t'] if hit else None, 'dt': round(hit['t'] - c['t'], 3) if hit else None})
    li = next((f for f in frames if f['t'] > 26.0 and f['looking_in']), None)
    on.append({'score_t': 26.4, 'to': 'looks in (head into the doorway)', 'measured_t': li['t'] if li else None, 'dt': round(li['t'] - 26.4, 3) if li else None})
    stays = [f for f in frames if f['t'] >= 28.5]
    extra = {'refusal_back_shown_by': next((f['t'] for f in frames if f['t'] > 3.4 and f['facing'] < 0), None),
             'turned_back_to_look_head_round_by': next((f['t'] for f in frames if f['t'] > 7.4 and f['facing'] > 0), None),
             'approach_head_low_share': round(float(np.mean([f['head_low'] for f in frames if f['state'] == 'approach'])), 3),
             'end_lying_share_after_28_5': round(float(np.mean([f['posture'] == 'lying' for f in stays])), 3),
             'dog_reaches_inside_door_frame_m': min(f['dog_min_x_world_m'] for f in frames[-48:]),
             'dog_tail_end_outside_m': max(f['dog_max_x_world_m'] for f in frames[-48:])}
    json.dump({'onsets': on, 'checks': extra}, open(os.path.join(H, '..', 'proof', 'onsets.json'), 'w'), indent=1)
    print(json.dumps(on)); print(json.dumps(extra))


if __name__ == '__main__':
    main()
