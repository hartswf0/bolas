"""Shadow reader: measure what the render did and test the PAELEO invariants against it.

Inputs: build/out/measure.json (per scene frame, measured from the rendered dog mask and the
muzzle / cranium measurement masks), build/out/rig.json, the score.  Outputs: trace.json,
exposure-sheet.csv, build/out/invariants.json (printed).  Stills are cut from film.mp4.
"""
import csv, json, math, os, subprocess, sys
import numpy as np
from theatre import *

ROOTD = ROOT
meas = sorted(json.load(open(os.path.join(OUT, 'measure.json'))), key=lambda m: m['i'])
rig = json.load(open(os.path.join(OUT, 'rig.json')))
sc = load_score(); fr = sc['frames']

def posture(R, m):
    d = R['dog']; row = m['row']
    if str(row.get('body', '')).startswith('endon'): return 'end-on, turning (' + row['body'][6:] + ' view)'
    if d['lie'] > 0.5:
        if d['look'] > 0.5: return 'lying across the sill, snout raised into the doorway, looking in'
        if d['rest'] > 0.5: return 'lying, chin on paws'
        if d['hb'] > 0.5: return 'lying, looking back over its shoulder'
        return 'lying'
    if 0.05 < d['lie'] <= 0.5: return 'getting up' if R['t'] < 10 else 'lying down'
    mv = d['moving'] > 0.2
    if R['state'] == 'retreat' and mv: return 'backing away, crouched, tail tucked'
    if d['crouch'] > 0.35: return 'crouched, head low'
    if mv: return 'walking, head low' if d['head'] < 0.6 else 'walking'
    return 'standing'

trace = []
for m in meas:
    i = m['i']; R = rig[i]
    bb = m.get('bbox', [0, 0, 0, 0])
    trace.append(dict(i=i, t=round(R['t'], 4), state=R['state'], x_score=round(R['dog']['x'], 4),
                      x_screen=m.get('x_screen'), y_screen=m.get('y_screen'),
                      facing=m['facing'], gaze=m['gaze'], posture=posture(R, m),
                      bbox=bb, left_m=round((bb[0] - OX) / S, 3), right_m=round((bb[2] - OX) / S, 3),
                      height_m=round((bb[3] - bb[1]) / S, 3), x_centroid_m=round((m.get('x_screen', 0) - OX) / S, 3)))
json.dump(dict(about='Measured from the rendered frames of SCION-02 (Reiniger). x_screen/y_screen: centroid of the '
                     'rendered dog silhouette (px, 1280x720, scene frame i = film frame i+72). facing: 1 = muzzle '
                     'toward the door (left), -1 = away, 0 = no muzzle visible (end-on body or head turned into depth); '
                     'measured from separately rendered muzzle and cranium masks. left_m/right_m: silhouette extent in '
                     'score metres (x = (px - 352)/175). posture: from the puppet state that produced the frame.',
               mapping=dict(OX=OX, S=S, FY=FY, formula='x_screen_of_dog_centre = 352 + 175 * x_score'),
               frames=trace), open(os.path.join(ROOTD, 'trace.json'), 'w'), indent=0)

# exposure sheet
keys = ['i', 't', 'state', 'head', 'body', 'spine_y', 'fore_deg', 'hind_deg', 'neck_deg', 'head_deg', 'ear_deg',
        'tail_deg', 'nf_paw', 'ff_paw', 'nh_paw', 'fh_paw', 'p_hand', 'p_mouth', 'p_skirt', 'p_lean', 'p_arm', 'leaf']
with open(os.path.join(ROOTD, 'exposure-sheet.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(keys)
    for m in meas:
        r = dict(m['row']); r['t'] = round(m['t'], 3); r['state'] = rig[m['i']]['state']
        r.setdefault('body', 'profile')
        w.writerow([json.dumps(r.get(k, '')) if isinstance(r.get(k), list) else r.get(k, '') for k in keys])

# ---------------------------------------------------------------- invariants (measured)
t = np.array([tr['t'] for tr in trace]); xs = np.array([tr['x_screen'] for tr in trace])
fac = np.array([tr['facing'] for tr in trace]); hgt = np.array([tr['height_m'] for tr in trace])
top = np.array([tr['bbox'][1] for tr in trace], float)
dx = np.diff(xs, prepend=xs[0])
def first(cond, after):
    for k in range(len(t)):
        if t[k] >= after and cond(k): return float(t[k])
    return None
res = {}
res['retreat'] = first(lambda k: dx[k] > 0.5, 0.5)                                    # moves away from the door
# retreat -> watch: the silhouette lifts out of the crouch (top edge rises by >= 2 px over 2 frames)
res['watch_after_retreat'] = first(lambda k: k > 2 and top[k - 2] - top[k] >= 2.0, 2.0)
res['refuse'] = first(lambda k: fac[k] != 1, 3.0)                                     # muzzle leaves the door
res['turns_back_to_look'] = first(lambda k: fac[k] == 1, 7.0)                         # muzzle returns to the door
res['approach'] = first(lambda k: dx[k] < -0.5, 14.0)                                 # moves toward the door
h0 = hgt[int(23.4 * FPS)]
res['lie_down'] = first(lambda k: hgt[k] < h0 - 0.03, 23.4)                           # silhouette lowers
eye = np.array([m.get('eye_area', 1) for m in meas])
res['looks_in'] = first(lambda k: fac[k] == 1 and eye[k] < 0.5 and trace[k]['gaze'].startswith('into'), 26.0)  # snout into the light, eye hidden
res['settles'] = first(lambda k: eye[k] > 0.5, 27.5)
target = dict(retreat=1.0, watch_after_retreat=2.333, refuse=3.417, turns_back_to_look=7.458, approach=14.708,
              lie_down=23.792, looks_in=26.4)
choices = {}
for k, v in target.items():
    mv = res[k]
    choices[k] = dict(score=v, measured=mv, error=None if mv is None else round(mv - v, 3),
                      within_0_25=None if mv is None else abs(mv - v) <= 0.25)
last = trace[-1]
stays = float(np.abs(np.diff(xs[int(28 * FPS):])).max())
inv = dict(
    choices=choices, settles_after_looking=res['settles'],
    stays_still_after_28s_max_px_step=round(stays, 3),
    never_enters=dict(min_centroid_x_m=float(min(tr['x_centroid_m'] for tr in trace)),
                      min_left_extent_m=float(min(tr['left_m'] for tr in trace)),
                      inner_jamb_m=-0.46, ok=min(tr['left_m'] for tr in trace) > -0.46),
    ends_across_threshold=dict(left_m=last['left_m'], right_m=last['right_m'], outer_jamb_m=0.46,
                               ok=last['left_m'] < 0.46 < last['right_m'] and last['left_m'] > -0.46),
    x_follows_score=dict(max_abs_error_m=round(float(max(abs(tr['x_centroid_m'] - tr['x_score']) for tr in trace if tr['posture'][:6] != 'end-on')), 3),
                         note='centroid of the silhouette vs score x; the offset includes head/tail/lying shape',
                         retreat_m=round(float((xs[int(2.6 * FPS)] - xs[int(0.9 * FPS)]) / S), 3),
                         approach_m=round(float((xs[int(14.6 * FPS)] - xs[int(23.8 * FPS)]) / S), 3),
                         score_retreat_m=round(fr[int(2.6 * FPS)]['dog']['x'] - fr[int(0.9 * FPS)]['dog']['x'], 3),
                         score_approach_m=round(fr[int(14.6 * FPS)]['dog']['x'] - fr[int(23.8 * FPS)]['dog']['x'], 3)),
    circumstances_before_approach=dict(
        kneels_t=next(r['t'] for r in rig if r['person']['sit'] > 0.5),
        door_open_t=next(r['t'] for r in rig if r['leaf'] < 0.2),
        hand_low_t=next(r['t'] for r in rig if r['person']['low'] > 0.5),
        soft_voice_t=next(r['t'] for r in rig if r['voice'] == 'soft'),
        approach_t=res['approach'], kind='structural (puppet state that drew the frame), not image-measured'),
    joint_limit_violations=sum(len(m['limits']) for m in meas),
)
json.dump(inv, open(os.path.join(OUT, 'invariants.json'), 'w'), indent=1)
print(json.dumps(inv, indent=1))

if len(sys.argv) > 1 and sys.argv[1] == 'stills':
    film = os.path.join(ROOTD, 'film.mp4'); os.makedirs(os.path.join(ROOTD, 'stills'), exist_ok=True)
    for (ts, name) in [(3.6, 'refusal'), (9.0, 'watching'), (19.0, 'approach'), (28.0, 'lying-across-the-sill')]:
        n = int(round(ts * FPS)) + 72
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', film, '-vf', f'select=eq(n\\,{n})', '-vframes', '1',
                        '-q:v', '2', os.path.join(ROOTD, 'stills', f'{ts:04.1f}s-{name}.jpg')], check=True)
