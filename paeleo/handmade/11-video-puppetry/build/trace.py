"""SCION 11 · trace.json from what the render shows (build/cache/measure.jsonl).

x_screen, y_screen : centroid of the dog's rendered silhouette (alpha > .5), px
facing             : +1 when the dog's rendered head pixels lie left of its centroid (toward the door), else -1
posture            : from the silhouette height against its standing height (standing / crouched / lying)
state              : segmented at onsets measured on these signals, not copied from the score
x_score            : the performance's x (the score's metres, unchanged)
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
M = [json.loads(l) for l in open(os.path.join(HERE, 'cache', 'measure.jsonl'))]
PERF = json.load(open(os.path.join(HERE, '..', 'data', 'performance.json')))['frames']
assert len(M) == 768, len(M)
t = np.array([m['t'] for m in M])
cx = np.array([m['cx'] for m in M]); cy = np.array([m['cy'] for m in M])
hx = np.array([m['hx'] if m['hx'] is not None else m['cx'] for m in M])
hy = np.array([m['hy'] if m['hy'] is not None else m['cy'] for m in M])
top = np.array([m['top'] for m in M]); bot = np.array([m['bottom'] for m in M])
hgt = bot - top
stand_h = np.median(hgt[(t > 9) & (t < 14)])


def first(cond, after):
    idx = np.nonzero(cond & (t >= after))[0]
    return int(idx[0]) if len(idx) else None


def at(tt):
    return int(round(tt * 24))


on = []
# 1 retreat: the silhouette starts to move away from the door (right) or to sink
i0 = at(0.6)
i = first((cx - cx[i0] > 1.5) | (hgt[i0] - hgt > 3), 0.6)
on.append(('watch', 'retreat', 1.0, i, 'centroid moves right >1.5 px or silhouette sinks >3 px from 0.6 s'))
# 2 watch: the head comes back up (head pixels rise >3 px from their lowest in the retreat)
base = np.median(hy[(t > 1.4) & (t < 2.2)])
i = first(hy < base - 5, 1.4)
on.append(('retreat', 'watch', 2.333, i, 'head pixels rise >5 px above their median height while backing (1.4-2.2 s; the walk bobs them +-3 px)'))
# 3 refuse: the head starts round (head pixels move >3 px from 3.2 s)
i0 = at(3.2)
i = first(np.abs(hx - hx[i0]) > 3, 3.2)
on.append(('watch', 'refuse', 3.417, i, 'head pixels move >3 px from their 3.2 s place (the turn begins)'))
# 4 watch: lying with its back turned, the head starts to come round / up
i0 = at(7.2)
i = first(np.hypot(hx - hx[i0], hy - hy[i0]) > 3, 7.2)
on.append(('refuse', 'watch', 7.458, i, 'head pixels move >3 px from their 7.2 s place'))
# 5 approach: the centroid starts toward the door
i0 = at(14.2)
i = first(cx[i0] - cx > 1.5, 14.2)
on.append(('watch', 'approach', 14.708, i, 'centroid moves left >1.5 px from 14.2 s'))
# 6 lie down: the silhouette's top drops (after the last step)
i0 = at(23.6)
i = first(top - top[i0] > 3, 23.6)
on.append(('approach', 'lie_down', 23.792, i, 'silhouette top drops >3 px from 23.6 s'))
# 7 look in (not a state change): head pixels rise into the doorway
i0 = at(26.2)
i = first(hy < hy[i0] - 3, 26.2)
look = dict(choice='hears come in: looks in', score_t=26.4, t=float(t[i]) if i is not None else None,
            dt=round(float(t[i]) - 26.4, 3) if i is not None else None, measure='head pixels rise >3 px from 26.2 s')

states = np.array(['watch'] * 768, dtype=object)
summary = []
for a, b, st, i, how in on:
    if i is not None:
        states[i:] = b
    summary.append(dict(choice='%s -> %s' % (a, b), score_t=st, t=float(t[i]) if i is not None else None,
                        dt=round(float(t[i]) - st, 3) if i is not None else None,
                        within_0_25s=bool(i is not None and abs(t[i] - st) <= .25), measure=how))
summary.append(look)

fr = []
for k, m in enumerate(M):
    face = 1 if hx[k] < cx[k] - 2 else -1
    r = hgt[k] / stand_h
    posture = 'lying' if r < .62 else 'crouched' if r < .88 else 'standing'
    fr.append(dict(i=m['i'], t=m['t'], state=states[k], x_score=PERF[k]['dog']['x'], x_screen=round(float(cx[k]), 2),
                   y_screen=round(float(cy[k]), 2), facing=face, posture=posture,
                   head_x=round(float(hx[k]), 1), head_y=round(float(hy[k]), 1), height_px=int(hgt[k]),
                   in_door_frame_share=round(m['in_door'], 3), warp_det_min=round(m['det_min'], 3),
                   head_top_px=m.get('head_top'), withers_line_px=round(m.get('withers_y', 0), 1)))
sc = np.array([f['dog']['x'] for f in SCORE['frames']])
r = float(np.corrcoef(cx, sc)[0, 1])
endshare = fr[-1]['in_door_frame_share']
out = dict(about=__doc__.strip(), camera='static (one fixed tabletop camera); x_screen is in that one frame',
           mapping='screen x of the dog anchor = 320 + 200 px/m * x_score; the ground line draws in toward the sill for x < 1.75 m',
           summary=dict(onsets_measured=summary, corr_x_screen_vs_score_x=round(r, 4),
                        final_silhouette_share_inside_door_frame=endshare,
                        final_posture=fr[-1]['posture'], stand_height_px=float(stand_h),
                        approach_14_8_to_23_7_frames_head_top_below_withers='%d/%d' % (
                            sum(1 for f in fr if 14.8 <= f['t'] <= 23.7 and f['head_top_px'] is not None and f['head_top_px'] > f['withers_line_px']),
                            sum(1 for f in fr if 14.8 <= f['t'] <= 23.7)),
                        frames_with_body_sheet_fold=sum(1 for f in fr if f['warp_det_min'] < 0)),
           frames=fr)
json.dump(out, open(os.path.join(HERE, '..', 'trace.json'), 'w'), indent=0)
for s in summary:
    print(s)
print('corr', round(r, 4), 'end in-door share', endshare, fr[-1]['posture'])
