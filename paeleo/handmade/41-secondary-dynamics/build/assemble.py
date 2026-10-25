"""Mux picture + sound into film.mp4, write trace.json (measured from the render), cut the four stills.
python3 build/assemble.py"""
import json, os, subprocess, math
HERE = os.path.dirname(os.path.abspath(__file__)); TOP = os.path.dirname(HERE); C = os.path.join(HERE, 'cache')
ROOT = os.path.abspath(os.path.join(TOP, '../../..'))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
SIM = json.load(open(os.path.join(C, 'sim.json'))); MEAS = json.load(open(os.path.join(C, 'picture-measure.json')))

subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(C, 'picture.mp4'), '-i', os.path.join(C, 'sound.wav'), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', '-shortest', os.path.join(TOP, 'film.mp4')], check=True)

# trace: what the dog did, measured from the render (silhouette centroid of the drawn dog layer, unprojected to the
# dog's walking plane; facing from the drawn head's screen position relative to the drawn rump)
fr = []
mi = {m['i']: m for m in MEAS}
for f in SCORE['frames']:
    i = f['i']; m = mi[i]; me = SIM['meas'][i]
    hd = m['head_dx']; facing = 1 if hd < -0.12 * max(20, (m['bbox'][2] - m['bbox'][0])) else (-1 if hd > 0.12 * max(20, (m['bbox'][2] - m['bbox'][0])) else 0)
    lie = me['lie']; posture = 'lying' if lie > 0.85 else ('lying down' if lie > 0.1 else ('crouched' if me['withers_y'] < 0.43 else 'standing'))
    if posture == 'standing' and abs(f['dog']['v']) > 0.05: posture = 'walking' if f['dog']['v'] < 0 else 'backing'
    fr.append({'i': i, 't': f['t'], 'state': f['dog']['state'], 'x_score': f['dog']['x'], 'x_screen': m['cx'], 'y_screen': m['cy'], 'x_world_measured': m['x_world'],
               'facing': facing, 'posture': posture, 'head_below_back': me['head_below_back'], 'bbox': m['bbox']})
json.dump({'about': 'SCION 41 trace, measured from the render: x_screen/y_screen = centroid of the drawn dog layer (px), x_world_measured = that centroid unprojected to the dog plane Z=0 '
           'with the frame camera (m), facing = +1 head drawn toward the door (screen-left of the rump), -1 away, 0 end-on; posture from the rig heights; state is the score state the rig executed.',
           'facing_convention': {'1': 'faces the door/person', '-1': 'back turned', '0': 'end-on mid-turn'}, 'frames': fr}, open(os.path.join(TOP, 'trace.json'), 'w'))

os.makedirs(os.path.join(TOP, 'stills'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{3.0 + t + 0.5 / 24:.4f}', '-i', os.path.join(TOP, 'film.mp4'), '-frames:v', '1', '-q:v', '2',
                    os.path.join(TOP, 'stills', f'still_{t:04.1f}s.jpg')], check=True)
print('film, trace, stills written; size MB', round(os.path.getsize(os.path.join(TOP, 'film.mp4')) / 1e6, 2))
