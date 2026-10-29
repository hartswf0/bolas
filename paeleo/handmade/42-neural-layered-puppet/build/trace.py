"""SCION 42 · trace.json from what the render measured (data/measure.json): choice onsets measured on screen, states
switched at those onsets, facing measured from the head (puppet) or the kit's nose keypoint (archive views), the head
against the back line during the approach, feet against travel.  Also writes build/cache/perform_sound.json.
"""
import json, os
import numpy as np
import world as Wo

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
M = json.load(open(os.path.join(ROOT, 'data', 'measure.json')))
M.sort(key=lambda r: r['i'])
assert len(M) == 768, len(M)
t = np.array([r['t'] for r in M]); xs = np.array([r['x_screen'] for r in M]); ys = np.array([r['y_screen'] for r in M])
ht = np.array([r.get('head_top_y', np.nan) for r in M]); hx = np.array([r['head_xy'][0] if r.get('head_xy') else np.nan for r in M])
mode = [r['mode'] for r in M]
hy = np.array([r['head_xy'][1] if r.get('head_xy') else np.nan for r in M])


def first(cond, t0):
    for i in range(len(M)):
        if t[i] >= t0 and cond(i): return i
    return None


def at(tq): return int(np.argmin(np.abs(t - tq)))


on = []
i09 = at(0.9)
on.append(('watch -> retreat', 1.0, first(lambda i: xs[i] - xs[i09] > 1.0, 0.9), 'dog centroid moves right (away from the door) > 1 px from its 0.9 s position'))
lo = np.nanmax(ht[at(1.4):at(2.2)])
on.append(('retreat -> watch', 2.333, first(lambda i: ht[i] < lo - 2.0, 2.0), 'head rises: head top > 2 px above its lowest point of the retreat (1.4-2.2 s)'))
on.append(('watch -> refuse', 3.417, first(lambda i: mode[i] in ('turn-learned', 'turn-blend', 'view'), 3.0), 'the turn away begins: first frame the puppet leaves its profile pose for the learned turning pose'))
on.append(('refuse -> watch', 7.458, first(lambda i: mode[i] == 'head-swing', 7.0), 'the head starts to swing up and round (head-and-neck layers leave their resting pose)'))
hd_door = first(lambda i: mode[i] == 'head-swing' and M[i]['head_xy'][0] < M[i]['neck_hinge_xy'][0], 7.0)
i145 = at(14.5)
on.append(('watch -> approach', 14.708, first(lambda i: xs[i] < xs[i145] - 1.0 or ht[i] > ht[i145] + 2.0, 14.5), 'centroid moves toward the door > 1 px, or the head drops > 2 px, from 14.5 s'))
i236 = at(23.6)
on.append(('approach -> lie_down', 23.792, first(lambda i: ys[i] > ys[i236] + 2.0, 23.6), 'the body goes down: centroid > 2 px lower than at 23.6 s'))
i262 = at(26.2)
on.append(('hears come in: looks in', 26.4, first(lambda i: np.hypot(hx[i] - hx[i262], hy[i] - hy[i262]) > 2.0, 26.2), 'the head leaves its resting place: head centre moves > 2 px from its 26.2 s position (it lifts and turns into the room)'))
onsets = []
for name, ts, i, how in on:
    tt = None if i is None else float(t[i])
    onsets.append(dict(choice=name, score_t=ts, t=tt, dt=None if tt is None else round(tt - ts, 3), within_0_25s=tt is not None and abs(tt - ts) <= 0.25, measure=how))

# states switched at the measured onsets
seq = [(0, 'watch')] + [(onsets[k]['t'], s) for k, s in enumerate(['retreat', 'watch', 'refuse', 'watch', 'approach', 'lie_down'])]
def state_at(tq):
    s = 'watch'
    for ts, st in seq:
        if ts is not None and tq >= ts - 1e-6: s = st
    return s


def facing(r):
    if r['mode'] == 'head-swing':
        return 1 if r['head_xy'][0] < r['neck_hinge_xy'][0] else -1
    if r.get('head_xy') is not None:
        return 1 if r['head_xy'][0] < r['x_screen'] else -1
    if 'nose_rel' in r: return 1 if r['nose_rel'] < 0 else -1
    return {31: 0, 38: 0, 41: -1}.get(r['view'], 0)


def posture(r):
    if r['mode'] == 'view': return 'turning (archive frame f%02d, whole)' % r['view']
    if r['mode'] == 'turn-blend': return 'turning (learned fit of archive frame f%02d dissolving with the frame)' % r['view']
    if r['mode'] == 'turn-learned':
        v = r['view']
        return 'turning: the puppet at / between its learned poses of archive turning frames' + ('' if not v else ' (near f%02d%s)' % (v[1], ' mirrored' if v[0] == 'm' else ''))
    if r['mode'] == 'head-swing': return 'lying then rising, head swinging round to the door'
    if r['lie'] > 0.5:
        if r['look'] > 0.5: return 'lying across the sill, head reaching in'
        if r['rest'] > 0.5: return 'lying, chin down'
        return 'lying'
    if r['moving'] > 0.5: return 'walking' + (', head low' if r['head_low'] > 0.5 else '')
    return 'standing' + (', head low' if r['head_low'] > 0.5 else '')


frames = []
for r in M:
    f = dict(i=r['i'], t=round(r['t'], 4), state=state_at(r['t']), x_score=r['x_score'], x_screen=round(r['x_screen'], 2),
             y_screen=round(r['y_screen'], 2), facing=facing(r), posture=posture(r), visibility=r['mode'],
             view_frame=r['view'][1] if isinstance(r['view'], list) else r['view'], override=round(r['override'], 2), bbox=r['bbox'])
    if r.get('head_top_y') is not None:
        f['head_top_y'] = round(r['head_top_y'], 1); f['back_top_y'] = round(r['back_top_y'], 1)
        f['head_below_back_px'] = round(r['head_top_y'] - r['back_top_y'], 1)
    frames.append(f)

# head under the back line for the whole approach
ap = [f for f in frames if f['state'] == 'approach' and 'head_below_back_px' in f]
hb = [f['head_below_back_px'] for f in ap]
# feet against travel during the approach: per frame, the fore and hind foot's screen motion vs the body's
fs = []
for a, b in zip(M[:-1], M[1:]):
    if a['t'] < 15.2 or b['t'] > 23.0 or 'foreleg_foot' not in a or 'foreleg_foot' not in b: continue
    body = b['x_screen'] - a['x_screen']
    for k in ('foreleg_foot', 'hind_foot'):
        fs.append((abs(b[k][0] - a[k][0]), abs(body)))
fs = np.array(fs)
planted = float(np.mean(fs[:, 0] < 0.35 * fs[:, 1])) if len(fs) else None
slide = float(np.median(fs[:, 0] / np.maximum(fs[:, 1], 1e-3))) if len(fs) else None
summary = dict(onsets_measured=onsets,
               approach_head_below_back_px=dict(min=float(np.min(hb)), median=float(np.median(hb)), share_below=float(np.mean(np.array(hb) > 0))),
               feet_vs_travel_approach=dict(share_of_foot_frames_planted=planted, median_foot_to_body_speed=slide,
                                            note='a planted foot moves < 0.35 x the body per frame; 1.0 would be a foot that slides with the body'),
               head_toward_door_at=None if hd_door is None else float(t[hd_door]),
               lying_end=dict(bbox_bottom=M[-1]['bbox'][3], floor_y=612, tail_x_range=M[-1].get('tail_x_range'), door_outer_face_x=Wo.X(Wo.WALL_OUT)),
               end=dict(x_score=frames[-1]['x_score'], bbox=frames[-1]['bbox'], door_reveal_screen_x=[Wo.X(Wo.WALL_IN), Wo.X(Wo.WALL_OUT)]),
               override_share=float(np.mean([f['override'] > 0.05 for f in frames])),
               view_share=float(np.mean([f['visibility'] == 'view' for f in frames])),
               visibility_counts={v: sum(f['visibility'] == v for f in frames) for v in sorted(set(f['visibility'] for f in frames))})
about = ("SCION 42 trace, measured from the render. x_screen/y_screen: centroid of the dog's rendered alpha (px, static "
         "camera, 1 m = 190 px, threshold x=0 at screen x 310). facing: +1 toward the door (left); measured from the head "
         "layer's screen position against the centroid for the learned puppet, from the kit nose keypoint for archive "
         "views (0 = facing the camera). visibility: profile-L/-R = learned puppet, view = whole archive frame, "
         "turn-learned = puppet carried into its learned fit of an archive turning frame, turn-blend = that fit dissolving with the real frame, head-swing = head and neck layers swinging round their learned hinge. override: share of the pose that is a "
         "hand-set rotation about learned hinges (lying, chin down, look in, head carried low beyond the examples). "
         "state switches at the onsets measured on screen (summary.onsets_measured).")
json.dump(dict(about=about, summary=summary, frames=frames), open(os.path.join(ROOT, 'trace.json'), 'w'), indent=0)
ev = dict(settle=[4.4, 24.0], sigh=[29.0])
json.dump(dict(frames=[dict(t=r['t'], moving=r['moving'], walk_phase=r['walk_phase'], x_screen=r['x_screen']) for r in M], events=ev),
          open(os.path.join(HERE, 'cache', 'perform_sound.json'), 'w'))
print(json.dumps(summary, indent=1))
