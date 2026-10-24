"""SCION 08 · Sutherland — trace.json and the invariant checks, measured from the solved graphs and
from the rasterised dog spots (render_meas.json).  Writes ../trace.json and ../checks.json."""
import json, math, os, pickle
import numpy as np
import world as Wd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..'))
S = pickle.load(open(os.path.join(HERE, '_cache', 'solve.pkl'), 'rb'))
RM = json.load(open(os.path.join(HERE, '_cache', 'render_meas.json')))
meas = {int(k): v for k, v in RM['meas'].items()}
sc = S['scene']
SF = Wd.SF
g = Wd.build_dog(SF[0]['dog']['x'])
pg = Wd.build_person(SF[0]['person']['x'])
I = g.idx

def facing_of(P):
    """unit horizontal direction croup -> withers; -x faces the door/person."""
    v = P[I['W']] - P[I['P']]
    v = np.array([v[0], v[2]]); return v / (np.linalg.norm(v) + 1e-12)

trace = []
rows = []
for k, fr in enumerate(sc):
    P = fr['dogP']
    xw = float((P[I['W']][0] + P[I['P']][0]) / 2)
    wh = float(P[I['W']][1])
    fv = facing_of(P)
    face_cos = float(-fv[0])                       # 1 = faces the door, -1 = back turned
    hd = P[I['Z']] - P[I['N']]
    head_in = float(-hd[2] / (np.linalg.norm(hd) + 1e-9))   # >0: muzzle points into the house (-z)
    posture = 'standing' if wh > 0.47 else ('crouched' if wh > 0.38 else 'lying')
    m = meas.get(k, {})
    row = dict(i=k, t=fr['t'], state=SF[k]['dog']['state'], x_score=SF[k]['dog']['x'], x_world=round(xw, 4),
               x_screen=round(m.get('cx', float('nan')), 2), y_screen=round(m.get('cy', float('nan')), 2),
               facing=('door' if face_cos > 0.2 else ('back_turned' if face_cos < -0.2 else 'turning')),
               face_cos=round(face_cos, 3), posture=posture, withers_h=round(wh, 3), head_in=round(head_in, 3),
               frac_in_door_frame=round(m.get('frac_in_frame', float('nan')), 3),
               screen_scale=m.get('S'), dog_hard_max_mm=round(fr['dres']['hard_max'] * 1000, 3),
               dog_passes=fr['dres']['iters'], person_hard_max_mm=round(fr['pres']['hard_max'] * 1000, 3))
    trace.append(row)
json.dump({'about': 'SCION 08 trace: per scene frame, measured from the solved constraint graph (x_world, facing, posture, '
                    'withers_h, head_in) and from the rasterised dog spots (x_screen, y_screen = intensity-weighted centroid in '
                    'film pixels; frac_in_door_frame = share of dog spots between the jambs). state and x_score are the score\'s.',
           'frames': trace}, open(os.path.join(OUT, 'trace.json'), 'w'))

T = np.array([r['t'] for r in trace]); X = np.array([r['x_world'] for r in trace])
V = np.gradient(X, T)
FC = np.array([r['face_cos'] for r in trace]); WH = np.array([r['withers_h'] for r in trace])
HI = np.array([r['head_in'] for r in trace])

def first(cond, after):
    idx = np.where((T >= after) & cond)[0]
    return float(T[idx[0]]) if len(idx) else None

ev = {}
ev['retreat'] = first(V > 0.05, 0.5)
ev['retreat_to_watch'] = first((np.abs(V) < 0.12) & (X > 3.5), (ev['retreat'] or 1) + 0.3)
ev['refuse'] = first(FC < math.cos(math.radians(15)), 3.0)
wh_min_idx = np.where((T > 6) & (T < 7.46 + 0.6))[0]
base = WH[(T > 6.5) & (T < 7.2)].mean()
ev['refuse_to_watch'] = first((WH > base + 0.01), 7.0)
ev['approach'] = first(V < -0.05, 12.0)
stand = WH[(T > 20) & (T < 23)].mean()
ev['lie_down'] = first(WH < stand - 0.02, 23.0)
ev['look_in'] = first(HI > math.sin(math.radians(15)), 25.0)
score_t = {'retreat': 1.0, 'retreat_to_watch': 2.333, 'refuse': 3.417, 'refuse_to_watch': 7.458,
           'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
choice_rows = []
for k, st in score_t.items():
    mt = ev[k]
    choice_rows.append(dict(choice=k, score_t=st, measured_t=mt, delta=None if mt is None else round(mt - st, 3),
                            within_0_25=(mt is not None and abs(mt - st) <= 0.25)))

# invariant 2: never enters; ends across the threshold
allP = np.stack([f['dogP'] for f in sc])
xs_c = (allP[:, I['W'], 0] + allP[:, I['P'], 0]) / 2
in_open = (np.abs(allP[:, :, 0]) < Wd.DOOR['x1'])
zmin_in_open = float(allP[:, :, 2][in_open].min()) if in_open.any() else None
last = allP[-1]
part_in = int((np.abs(last[:, 0]) <= Wd.DOOR['x1']).sum()); part_out = int((last[:, 0] > Wd.DOOR['x1']).sum())
inv2 = dict(min_centre_x=round(float(xs_c.min()), 4), sill_limit=0.56, centre_never_below_sill=bool(xs_c.min() >= 0.56 - 1e-3),
            min_z_of_any_dog_point_inside_door_jambs=round(zmin_in_open, 4) if zmin_in_open is not None else None,
            wall_inner_face_z=-0.12, never_past_the_wall=bool(zmin_in_open is None or zmin_in_open > -0.12),
            final_points_between_jambs=part_in, final_points_outside_jambs=part_out,
            final_spot_share_between_jambs=trace[-1]['frac_in_door_frame'], final_posture=trace[-1]['posture'])

# invariant 3: commands push away; changed circumstances visible before the approach
perP = np.stack([f['perP'] for f in sc]); pI = pg.idx
pel_y = perP[:, pI['Pv'], 1]; hand_y = perP[:, pI['WrR'], 1]
ang = np.degrees([f['door_angle'] for f in sc])
def t_first(c):
    idx = np.where(c)[0]; return float(T[idx[0]]) if len(idx) else None
inv3 = dict(
    call_at=1.0, x_before_call=round(float(X[T <= 1.0][-1]), 3), x_after_call=round(float(X[(T >= 2.4)][0]), 3),
    reach_at=3.4, face_cos_before_reach=round(float(FC[T <= 3.4][-1]), 3), face_cos_after_reach=round(float(FC[(T >= 5.0)][0]), 3),
    person_seated_at=t_first(pel_y < 0.3), door_open_past_70deg_at=t_first(ang > 70), hand_low_at=t_first((hand_y < 0.45) & (T > 6.5)),
    soft_voice_at=7.4, approach_measured_at=ev['approach'])
inv3['all_circumstances_before_approach'] = all(v is not None and v < (ev['approach'] or 0) for v in
                                                (inv3['person_seated_at'], inv3['door_open_past_70deg_at'], inv3['hand_low_at']))
# invariant 4: position follows the score's x
xs_score = np.array([r['x_score'] for r in trace])
err = np.abs(X - xs_score)
wide = T < 24.6
xs_scr = np.array([r['x_screen'] for r in trace])
A = np.vstack([xs_score[wide], np.ones(wide.sum())]).T
coef, *_ = np.linalg.lstsq(A, xs_scr[wide], rcond=None)
resid = xs_scr[wide] - A @ coef
ap = (T >= 14.708) & (T <= 23.792)
inv4 = dict(max_abs_world_minus_score_m=round(float(err.max()), 4), mean_abs_m=round(float(err.mean()), 4),
            screen_px_per_m_fit_wide=round(float(coef[0]), 2), screen_fit_rms_px=round(float(np.sqrt((resid ** 2).mean())), 2),
            approach_distance_score_m=round(float(xs_score[ap][0] - xs_score[ap][-1]), 3),
            approach_distance_measured_m=round(float(X[ap][0] - X[ap][-1]), 3),
            retreat_direction='+x (away from the door)' if X[(T > 1) & (T < 2.4)].mean() > X[0] else 'WRONG')

# solver honesty
hd = np.array([f['dres']['hard_max'] for f in sc]); hp = np.array([f['pres']['hard_max'] for f in sc])
hdoor = np.array([f['doorres']['hard_max'] for f in sc])
step = np.linalg.norm(np.diff(allP, axis=0), axis=2).max(1)
pstep = np.linalg.norm(np.diff(perP, axis=0), axis=2).max(1)
gaps = [float(np.linalg.norm(f['perP'][pI['WrR']] - f['hand_req'])) for f in sc if f['hand_req'] is not None]
solver = dict(declared_tolerance_mm=1.0,
              dog_hard_max_mm=round(float(hd.max()) * 1000, 3), dog_hard_p95_mm=round(float(np.percentile(hd, 95)) * 1000, 3),
              person_hard_max_mm=round(float(hp.max()) * 1000, 3), door_hard_max_mm=round(float(hdoor.max()) * 1000, 3),
              all_within_tolerance=bool(max(hd.max(), hp.max(), hdoor.max()) < 1e-3),
              dog_max_point_step_per_frame_m=round(float(step.max()), 4), dog_max_step_at_t=float(T[1:][step.argmax()]),
              person_max_point_step_per_frame_m=round(float(pstep.max()), 4),
              planted_paw_slip='0 by construction (a planted paw has inverse mass 0)',
              unsatisfiable_reach_frames=len(gaps), reach_gap_max_m=round(max(gaps), 3) if gaps else None)
checks = dict(choices=choice_rows, invariant2=inv2, invariant3=inv3, invariant4=inv4, solver=solver,
              rig_ratios_from_archive=Wd.RATIOS, rig_keys=Wd.N_KEYS)
json.dump(checks, open(os.path.join(OUT, 'checks.json'), 'w'), indent=1)
print(json.dumps(checks, indent=1))
