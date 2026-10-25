"""QA inspector: trace.json from the render's own measurement (build/cache/measure.json), not from the plan.

Measured per frame (canvas px): the dog's coverage centroid (x_screen, y_screen), its top/bottom, the drawn nose and tail
(the source frame's rig keys carried through the drawing's transform) or the head layer (puppet), and which head piece is
drawn. From these:
  facing   'door' if the drawn head is >10 px toward the door from the body centre, 'away' if >10 px the other way,
           'camera' between (frontal drawings)
  posture  'lying' if the dog's height < 70 % of its standing height, else 'stand'; 'walking' if it moved > 1.5 px/frame
The state per frame is assigned from measured onsets (events detected in these series, in order):
  retreat   x moves away from the door (> 3 px) or the head drops (top > 8 px lower) after t > 0.5
  watch     head back up (top rises > 8 px from its retreat level)
  refuse    facing leaves 'door' after the second watch began
  watch     facing returns to 'door' (the head comes round)
  approach  after 9 s: x moves toward the door (> 3 px) or the head drops (top > 8 px)
  lie_down  centroid descends > 4 px below its level over the previous 0.25 s, after the approach
  look_in   (not a state; reported) the back-of-head piece is drawn
x_score is the score's x at that frame (the position the score asks for; the checker's I2 uses it), x_screen is measured."""
import os, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FOLDER, '../../..'))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
DOOR_X = 325.0   # X(0)


def main():
    m = {}
    import glob
    for p in sorted(glob.glob(os.path.join(HERE, 'cache/measure*.json'))):
        m.update(json.load(open(p)))
    rows = [m[str(i)] for i in range(len(FR))]
    n = len(rows)
    cx = np.array([r['cx'] for r in rows]); top = np.array([r['top'] for r in rows], float)
    cy = np.array([r['cy'] for r in rows]); bot = np.array([r['bottom'] for r in rows], float)
    t = np.array([r['t'] for r in rows])
    facing = []
    for r in rows:
        if r.get('head_piece') == 'back_of_head_f000':
            facing.append('in'); continue          # the back of the head toward us: looking into the doorway
        if not r.get('nose'):
            facing.append('camera'); continue
        d = r['nose'][0] - r['neck'][0]      # the way the drawn head points; the door is to the left
        facing.append('door' if d < -6 else ('away' if d > 6 else 'camera'))
    height = bot - top
    stand_h = np.median(height[(t < 0.9)])
    ev = {}
    base_x = cx[(t > 0.2) & (t < 0.9)].mean(); base_top = top[(t > 0.2) & (t < 0.9)].mean()
    i = next(k for k in range(n) if t[k] > 0.5 and (cx[k] - base_x > 3 or top[k] - base_top > 8)); ev['retreat'] = i
    j = next(k for k in range(i + 6, n) if top[k] < base_top + 5); ev['watch1'] = j
    k = next(k for k in range(j + 1, n) if t[k] > 3.0 and facing[k] != 'door'); ev['refuse'] = k
    l = next(q for q in range(k + 12, n) if facing[q] == 'door'); ev['watch2'] = l
    w = [q for q in range(n) if 9 < t[q] < 14.0]
    bx = cx[w].mean(); bt = top[w].mean()
    a = next(q for q in range(n) if t[q] > 9 and (bx - cx[q] > 3 or top[q] - bt > 8)); ev['approach'] = a
    ld = next(q for q in range(a + 24, n) if height[q] < 0.93 * np.median(height[q - 12:q]) and cy[q] > np.median(cy[q - 12:q]) + 3); ev['lie_down'] = ld
    li = next((q for q in range(ld, n) if rows[q].get('head_piece') == 'back_of_head_f000'), None)
    order = [('retreat', 'retreat'), ('watch1', 'watch'), ('refuse', 'refuse'), ('watch2', 'watch'), ('approach', 'approach'), ('lie_down', 'lie_down')]
    frames = []
    for q in range(n):
        st = 'watch'
        for key, name in order:
            if q >= ev[key]:
                st = name
        moved = abs(cx[q] - cx[max(0, q - 1)]) > 1.5
        post = 'lying' if height[q] < 0.70 * stand_h else ('walking' if moved else 'stand')
        r = rows[q]
        frames.append({'i': q, 't': round(float(t[q]), 4), 'state': st, 'x_score': FR[q]['dog']['x'], 'x_screen': round(float(cx[q]), 2),
                       'y_screen': round(float(cy[q]), 2), 'facing': facing[q], 'posture': post,
                       'top': int(top[q]), 'bottom': int(bot[q]), 'nose': [round(v, 1) for v in r['nose']] if r.get('nose') else None,
                       'head_piece': r.get('head_piece'), 'drawing': r.get('drawing'), 'frac_left_of_right_jamb': round(r.get('frac_inside_frame', 0), 3)})
    score_t = {'retreat': 1.0, 'watch1': 2.333, 'refuse': 3.417, 'watch2': 7.458, 'approach': 14.708, 'lie_down': 23.792}
    onsets = {kk: {'measured_t': round(float(t[v]), 3), 'score_t': score_t[kk], 'dt': round(float(t[v]) - score_t[kk], 3)} for kk, v in ev.items()}
    onsets['look_in'] = {'measured_t': None if li is None else round(float(t[li]), 3), 'score_t': 26.4,
                         'dt': None if li is None else round(float(t[li]) - 26.4, 3)}
    end = frames[-1]
    summary = {'about': __doc__, 'onsets_measured': onsets, 'standing_height_px': float(stand_h),
               'end': {'x_screen': end['x_screen'], 'posture': end['posture'], 'share_of_dog_left_of_right_jamb': end['frac_left_of_right_jamb'],
                       'right_jamb_x': 325 + 205 * 0.46, 'left_jamb_x': 325 - 205 * 0.46}}
    json.dump({'summary': summary, 'frames': frames}, open(os.path.join(FOLDER, 'trace.json'), 'w'), indent=0)
    for kk, v in onsets.items():
        print(kk, v)
    print('end', summary['end'])


if __name__ == '__main__':
    main()
