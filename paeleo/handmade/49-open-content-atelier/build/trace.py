"""Build ../trace.json from build/cache/measure.json (what render.py measured on its own rendered dog layers).
State labels are NOT copied from the score: each choice's onset is detected in the measurements, then states are
assigned between onsets. Detectors (all on the render):
  retreat   first frame the dog's body-layer centroid moves away from the door by > 3 mm/frame
  watch     first frame after the retreat that the head pitch (neck->nose vector of the drawn head) rises by > 1 deg/frame
  refuse    first frame after 3.0 s that the head pitch drops > 1 deg/frame or the drawn body narrows (the turn begins)
  watch     first frame after 7.0 s that the drawn head points at the door (nose left of neck) while the body faces away
  approach  first frame after 14 s the body centroid moves toward the door by > 3 mm/frame
  lie_down  first frame after 23 s the body centroid sinks > 1.5 cm below the median of the previous 12 frames (world units)
  look_in   (event) first frame after 26 s the nose moves > 3 cm toward the room from its 25.5-26.3 s median
x_world_measured = body-layer centroid x, un-done through the camera (the camera pushes in from 21 s)."""
import json, math, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, 'cache', 'measure.json')))
SCORE = json.load(open(os.path.join(HERE, '..', '..', 'score', 'threshold-score.json')))
N = len(SCORE['frames']); FPS = 24
S, X0, FEET = 185.0, 340.0, 650.0
def ease(u): u = min(max(u, 0.), 1.); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
def cam_inv(t, X, Y):
    u = ease((t - 21.0) / 3.3); z = lerp(1.0, 1.32, u); cx = lerp(640, 330, u); cy = lerp(360, 455, u)
    return (X - 640) / z + cx, (Y - 360) / z + cy

fr = [M[str(i)] for i in range(N)]
xw = np.array([f['x_world_body_centroid'] for f in fr])
yw = np.array([(FEET - cam_inv(f['t'], f['body_cx_screen'], f['body_cy_screen'])[1]) / S for f in fr])
def pitch(f):
    (nx, ny), (kx, ky) = f['nose_screen'], f['neck_screen']
    return math.degrees(math.atan2(ky - ny, abs(nx - kx)))
pt = np.array([pitch(f) for f in fr])
nose_w = np.array([(cam_inv(f['t'], *f['nose_screen'])[0] - X0) / S for f in fr])
width_proxy = np.array([abs(f['turn']) if f['model'] == 'woodcock' else 1.0 for f in fr])  # drawn horizontal scale of the body
t = np.arange(N) / FPS

def first(cond, start):
    for i in range(int(start * FPS), N):
        if cond(i): return i
    return None
on = {}
on['retreat'] = first(lambda i: xw[i] - xw[i - 1] > 0.003, 0.3)
on['watch1'] = first(lambda i: pt[i] - pt[i - 1] > 1.0, t[on['retreat']] + 0.3)
on['refuse'] = first(lambda i: pt[i] - pt[i - 1] < -1.0 or width_proxy[i] < 0.995, 3.0)
on['watch2'] = first(lambda i: fr[i]['body_dir'] == -1 and fr[i]['nose_screen'][0] < fr[i]['neck_screen'][0], 7.0)
on['approach'] = first(lambda i: xw[i - 1] - xw[i] > 0.003, 14.0)
on['lie_down'] = first(lambda i: np.median(yw[i - 12:i]) - yw[i] > 0.015, 23.0)
base = np.median(nose_w[int(25.5 * FPS):int(26.3 * FPS)])
on['look_in'] = first(lambda i: base - nose_w[i] > 0.03, 26.0)
order = [('watch', 0), ('retreat', on['retreat']), ('watch', on['watch1']), ('refuse', on['refuse']), ('watch', on['watch2']),
         ('approach', on['approach']), ('lie_down', on['lie_down'])]

def state(i):
    s = 'watch'
    for name, k in order:
        if k is not None and i >= k: s = name
    return s

frames = []
for i, f in enumerate(fr):
    frames.append({'i': i, 't': round(i / FPS, 4), 'state': state(i), 'x_score': round(f['x_score'], 4),
                   'x_screen': round(f['body_cx_screen'], 2), 'y_screen': round(f['body_cy_screen'], 2),
                   'x_world_measured': round(float(xw[i]), 4), 'y_world_measured': round(float(yw[i]), 4),
                   'facing': int(f['body_dir']), 'head_toward_door': bool(f['nose_screen'][0] < f['neck_screen'][0]),
                   'head_pitch_deg': round(float(pt[i]), 1), 'nose_x_world': round(float(nose_w[i]), 3),
                   'posture': f['posture'], 'model': f['model'], 'cam_zoom': round(f['cam_zoom'], 4)})
score_t = {'retreat': 1.0, 'watch1': 2.333, 'refuse': 3.417, 'watch2': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
meas = [{'choice': k, 'score_t': score_t[k], 'measured_onset_t': None if v is None else round(v / FPS, 4),
         'dt': None if v is None else round(v / FPS - score_t[k], 3)} for k, v in on.items()]
json.dump({'about': 'PAE-02 SCION 49: what the dog did, measured per frame from the rendered dog layers (build/cache/measure.json). '
           'facing: +1 the drawn body faces the door (left), -1 its back is turned. x_world_measured is the body-layer '
           'centroid in metres along the porch with the camera undone (the camera pushes in from 21 s); its offset from '
           'the score x differs by cut (standing pointer vs lying Juno). States are assigned from measured onsets (see build/trace.py).',
           'choices_measured': meas, 'frames': frames}, open(os.path.join(HERE, '..', 'trace.json'), 'w'), indent=0)
for m in meas: print(m)
