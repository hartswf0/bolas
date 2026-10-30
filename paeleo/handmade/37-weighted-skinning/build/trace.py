"""SCION 37 trace: what the dog did, measured from the render's own G-buffer (cache/measure/*.json, written by render.py
from the pixels the rasterizer actually covered with the dog's skin), never from the score's labels.
  x_screen, y_screen   centroid of the dog's visible pixels (px, 1280x720)
  x_world_measured     mean world X of the visible dog surface, minus the fixed placement offset (score metres); the
                       camera dollies in during the approach, so this is the position the checker should use
  facing               +1 when the visible head pixels (weight of head/neck2/ears > 0.5) lie nearer the door than the
                       visible trunk pixels, else -1
  posture              from the visible back height: standing > 0.60 m, low 0.45-0.60, lying < 0.45
  state                switches at the measured onsets below, so the trace's choices are evidence"""
import glob, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
FR = SCORE['frames']; FPS = 24
DOG_X_OFFSET = -.17


def main():
    M = {}
    for p in glob.glob(os.path.join(HERE, 'cache', 'measure', '*.json')):
        m = json.load(open(p)); M[m['i']] = m
    assert len(M) == 768, len(M)
    T = np.arange(768) / FPS
    g = lambda k: np.array([M[i].get(k, np.nan) for i in range(768)], float)
    xw, topy, hx, hy, bx, backy, hcx, hcy = g('x_world'), g('top_y_world'), g('head_x_world'), g('head_y_world'), g('body_x_world'), g('back_y_world'), g('head_cx'), g('head_cy')
    hty = g('head_top_y_world')
    def first(cond, t0):
        for i in range(int(round(t0 * FPS)), 768):
            if cond(i): return i
        return None
    ons = []
    i0 = int(.9 * FPS)
    on_ret = first(lambda i: xw[i] - xw[i0] > .01 or topy[i0] - topy[i] > .01, .9)
    ons.append(('watch -> retreat', 1.0, on_ret, 'visible body moves away > 1 cm or drops > 1 cm (crouch) from its 0.90 s place'))
    lo = lambda i: np.nanmin(hy[int(1.5 * FPS):i + 1])
    on_w1 = first(lambda i: hy[i] - lo(i) > .02, 1.6)
    ons.append(('retreat -> watch', 2.333, on_w1, 'visible head rises > 2 cm above its lowest point in the retreat'))
    i1 = int(3.30 * FPS)
    on_ref = first(lambda i: np.hypot(hcx[i] - hcx[i1], hcy[i] - hcy[i1]) > 3, 3.30)
    ons.append(('watch -> refuse', 3.417, on_ref, 'visible head starts to turn away: its pixel centroid leaves its 3.30 s place by > 3 px'))
    i2 = int(7.30 * FPS)
    on_w2 = first(lambda i: np.hypot(hcx[i] - hcx[i2], hcy[i] - hcy[i2]) > 3, 7.30)
    ons.append(('refuse -> watch', 7.458, on_w2, 'visible head starts to come round: its pixel centroid leaves its 7.30 s place by > 3 px'))
    i3 = int(14.5 * FPS)
    on_app = first(lambda i: xw[i3] - xw[i] > .015, 14.5)
    ons.append(('watch -> approach', 14.708, on_app, 'visible body moves toward the door > 1.5 cm from its 14.5 s place'))
    walk_back = np.nanmin(backy[int(22.5 * FPS):int(23.5 * FPS)])
    on_lie = first(lambda i: walk_back - backy[i] > .02, 23.5)
    ons.append(('approach -> lie_down', 23.792, on_lie, 'visible back drops > 2 cm below its lowest walking height'))
    i4 = int(26.2 * FPS)
    on_look = first(lambda i: np.hypot(hcx[i] - hcx[i4], hcy[i] - hcy[i4]) > 3 and hx[i] < hx[i4], 26.2)
    ons.append(('hears come in: looks in', 26.4, on_look, 'visible head moves > 3 px and toward the room (its world X decreases)'))
    onsets = [{'choice': c, 'score_t': st, 't': None if i is None else round(i / FPS, 3),
               'dt': None if i is None else round(i / FPS - st, 3), 'within_0.25s': None if i is None else abs(i / FPS - st) <= .25,
               'signal': sig} for c, st, i, sig in ons]
    # states from the measured onsets
    seq = [('watch', 0), ('retreat', on_ret), ('watch', on_w1), ('refuse', on_ref), ('watch', on_w2), ('approach', on_app), ('lie_down', on_lie)]
    state = []
    for i in range(768):
        s = 'watch'
        for nm, at in seq:
            if at is not None and i >= at: s = nm
        state.append(s)
    frames = []
    for i in range(768):
        m = M[i]
        facing = 1 if (np.isfinite(hx[i]) and np.isfinite(bx[i]) and hx[i] < bx[i]) else -1
        posture = 'standing' if backy[i] > .60 else ('low' if backy[i] > .45 else 'lying')
        frames.append({'i': i, 't': round(i / FPS, 3), 'state': state[i], 'score_state': FR[i]['dog']['state'],
                       'x_score': FR[i]['dog']['x'], 'x_screen': round(m['cx'], 2), 'y_screen': round(m['cy'], 2),
                       'x_world_measured': round(xw[i] - DOG_X_OFFSET, 4), 'facing': facing, 'posture': posture,
                       'back_y_m': round(backy[i], 3), 'head_y_m': round(hy[i], 3), 'head_top_y_m': round(hty[i], 3),
                       'head_below_back': bool(hty[i] < backy[i]) if np.isfinite(hty[i]) else None,
                       'inside_door_share': round(m['inside_door_share'], 3), 'inside_room_share': round(m['inside_room_share'], 3),
                       'muzzle_x_m': round(m['muzzle_world'][0], 3), 'muzzle_toward_camera': round(m['muzzle_away_from_camera'], 3),
                       'dog_px': m['dog_px']})
    app = [f for f in frames if 14.9 <= f['t'] < 23.6]
    hbb = sum(1 for f in app if f['head_below_back']) / len(app)
    end = frames[-1]
    look = [f for f in frames if 26.6 <= f['t'] <= 28.2]
    summary = {'onsets_measured': onsets, 'head_below_back_share_approach': round(hbb, 3),
               'end_inside_door_frame_share': end['inside_door_share'], 'end_inside_room_share': end['inside_room_share'],
               'look_in_muzzle_x_min_m': min(f['muzzle_x_m'] for f in look),
               'look_in_back_of_head_to_camera_share': round(sum(1 for f in look if f['muzzle_toward_camera'] < 0) / len(look), 3),
               'min_dog_px': min(f['dog_px'] for f in frames),
               'facade_x_m': .35, 'room_starts_x_m': .20}
    json.dump({'about': __doc__, 'summary': summary, 'frames': frames}, open(os.path.join(ROOT, 'trace.json'), 'w'), indent=0)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
