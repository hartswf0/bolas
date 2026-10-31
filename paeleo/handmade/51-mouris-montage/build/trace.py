"""SCION 51 · trace.json from measurements of the render (build/cache/meas/*.json, written by render.py from the
depth/part buffers of every frame: which pixels of the dog are visible, and where they are in the world).
States are derived from those measurements by a fixed protocol (below), not copied from the score's labels:
  head angle a  = horizontal angle between the measured muzzle direction (mean visible muzzle pixels - mean visible skull
                  pixels) and the direction to the door (-z). facing: |a|<=60 'door', |a|>=100 'away', else 'side'.
  speed v       = d/dt of x_world_measured (mean world z of visible torso pixels, mapped back to score metres), 5-frame smoothed.
  retreat       : facing the door and v > +0.12 m/s (backing away)
  watch         : facing the door, |v| <= 0.12 m/s, standing or lying with the head toward the door
  refuse        : the head has turned more than 30 deg away from the door (and stays beyond 30 deg) after a call
  approach      : v < -0.12 m/s toward the door
  lie_down      : torso mean height < 0.33 m at the sill
The first frame of each new state is its measured onset."""
import json, math, os
import numpy as np
from lib import OUT, SCORE, FPS, Z_OFF

MEAS = os.path.join(OUT, 'build/cache/meas')


def build():
    M = [json.load(open(os.path.join(MEAS, f'{i:03d}.json'))) for i in range(768)]
    xw = np.array([m['torso_z'] - Z_OFF for m in M])
    v = np.gradient(xw) * FPS
    v = np.convolve(np.pad(v, 2, 'edge'), np.ones(5) / 5, 'valid')
    ang = []
    for m in M:
        d = m.get('muzzle_dir_xz')
        if d is None:
            ang.append(ang[-1] if ang else 0.0); continue
        a = math.degrees(math.atan2(d[0], -d[1]))   # 0 = toward the door (-z); + toward +x
        ang.append(a)
    ang = np.array(ang)
    frames = []; state = 'watch'
    for i, m in enumerate(M):
        t = i / FPS; a = abs(ang[i]); post = 'lying' if m['torso_mean_y'] < 0.33 else ('crouched' if m['torso_mean_y'] < 0.40 else 'standing')
        facing = 'door' if a <= 60 else ('away' if a >= 100 else 'side')
        sc = SCORE['frames'][i]
        # measured state machine
        if state in ('watch',) and a > 30 and t > 3.0 and m['torso_mean_y'] > 0.3 and xw[i] > 3.5:
            state = 'refuse'
        elif state == 'watch' and v[i] > 0.12 and a <= 30:
            state = 'retreat'
        elif state == 'retreat' and v[i] <= 0.12:
            state = 'watch'
        elif state == 'refuse' and a < 90:
            state = 'watch'
        elif state == 'watch' and v[i] < -0.12:
            state = 'approach'
        elif state == 'approach' and m['torso_mean_y'] < 0.33:
            state = 'lie_down'
        frames.append({'i': i, 't': round(t, 3), 'state': state, 'x_score': sc['dog']['x'], 'x_world_measured': round(float(xw[i]), 4),
                       'x_screen': m['x_screen'], 'y_screen': m['y_screen'], 'facing': facing, 'head_angle_to_door_deg': round(float(ang[i]), 1),
                       'posture': post, 'speed_mps': round(float(v[i]), 3), 'torso_mean_y_m': round(m['torso_mean_y'], 3),
                       'torso_top_y_m': round(m['torso_top_y'], 3), 'head_top_y_m': round(m.get('head_top_y', float('nan')), 3),
                       'head_below_back': bool(m.get('head_top_y', 9) < m['torso_top_y']),
                       'frac_dog_px_past_outer_face': m['frac_past_outer_face'], 'tail_z_m': None if m.get('tail_z') is None else round(m['tail_z'], 3),
                       'visible_px': m['visible_px'], 'cut': m['cut'], 'coat_image': m['coat'], 'words_on_screen': m['words'],
                       'score_state': sc['dog']['state']})
    on = []
    for k in range(1, len(frames)):
        if frames[k]['state'] != frames[k - 1]['state']:
            on.append({'t': frames[k]['t'], 'from': frames[k - 1]['state'], 'to': frames[k]['state']})
    # looking in (26.4): first frame after 26.0 the measured head angle leaves the door axis toward the room (-x) by > 12 deg
    look = next((f['t'] for f in frames if f['t'] >= 26.0 and f['head_angle_to_door_deg'] < -12), None)
    ap = [f for f in frames if f['state'] == 'approach']
    summary = {'measured_onsets': on, 'look_in_onset_s': look,
               'approach_head_below_back_share': round(sum(f['head_below_back'] for f in ap) / max(1, len(ap)), 3),
               'end_frac_past_outer_face': frames[-1]['frac_dog_px_past_outer_face'], 'end_tail_z_m': frames[-1]['tail_z_m'],
               'end_posture': frames[-1]['posture'],
               'refuse_facing_away_share': round(sum(f['facing'] == 'away' for f in frames if f['state'] == 'refuse') / max(1, sum(f['state'] == 'refuse' for f in frames)), 3)}
    json.dump({'about': __doc__, 'scene_offset_frames': 72, 'fps': FPS, 'summary': summary, 'frames': frames},
              open(os.path.join(OUT, 'trace.json'), 'w'), indent=0)
    return summary


if __name__ == '__main__':
    print(json.dumps(build(), indent=1))
