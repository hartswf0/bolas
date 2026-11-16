"""Write films/swarm/la-belle-hortense/scenes.json: per slot the clip / frame function, planes, ratios, streak,
rig poses and measured invariants; plus silhouette checks, evidence records, handmade items and absences."""
import os, sys, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene as S
import beats as B

ROOT = S.ROOT
rel = lambda p: os.path.relpath(p, ROOT)
ST = json.load(open(os.path.join(S.SW, 'structure.json')))
TM = json.load(open(os.path.join(S.AN, 'testshot_measures.json')))
CL = os.path.join(S.ED, 'clips'); STL = os.path.join(S.ED, 'stills')

def runner_checks(fn_pose_root, ts):
    """pivot errors (child pivot carried by child vs parent, px) and per-frame shin change."""
    emax = 0.0; shins = []
    for t in ts:
        pose, (x, y, s, lean) = fn_pose_root(t)
        M = S.RUN.mats(x, y, s, lean, pose)
        emax = max(emax, max(S.RUN.pivot_errors(M).values()))
        shins.append((round(pose['kneeN'], 2), round(pose['hipN'], 2)))
    changes = all(shins[i] != shins[i + 1] for i in range(len(shins) - 1))
    return dict(pivot_max_px=round(emax, 6), pivot_ok=emax <= 1.0, shin_pose_changes_every_frame=changes,
                sample_poses=[dict(t=round(ts[i], 3), kneeN=shins[i][0], hipN=shins[i][1]) for i in range(0, len(ts), 6)])
FR = [(k + 0.5) / S.FPS for k in range(36)]

def bell_check(theta0=26.0, tau=1.5, t0=0.1):
    th = [S.bell_angles(t - t0, theta0, tau)[0] for t in np.arange(0, 3.0, 1 / 240)]
    th = np.array(th); pk = [abs(th[i]) for i in range(1, len(th) - 1) if abs(th[i]) >= abs(th[i - 1]) and abs(th[i]) >= abs(th[i + 1]) and abs(th[i]) > 0.5]
    tt = np.arange(len(pk)); slope = np.polyfit(tt, np.log(pk), 1)[0] if len(pk) > 2 else None
    return dict(model='theta(t)=theta0*exp(-t/tau)*sin(2*pi*f*t); clapper child pendulum, lag 0.9 rad, tau*0.8',
                theta0_deg=theta0, tau_s=tau, f_hz=1.05, peaks_deg=[round(p, 2) for p in pk[:6]],
                log_peak_slope_per_halfcycle=round(float(slope), 4) if slope is not None else None,
                expected_slope=round(-1 / (2 * 1.05 * tau), 4), limits_ok=bool(np.all(np.abs(th) <= 38)))

def par(ratios, speed):
    d = [round(r * speed / S.FPS, 2) for r in ratios]
    return dict(ratios=ratios, px_per_frame=d, order_ok=all(d[i] < d[i + 1] for i in range(len(d) - 1)))

clip = lambda n: rel(os.path.join(CL, n + '.mp4'))
still = lambda n: rel(os.path.join(STL, n + '_mid.png'))
BEAT = {b[0]: b for b in B.BEATS}
def beat_entry(name, fn_name, extra=None):
    b = BEAT[name]
    e = dict(clip=clip(name), still=still(name), frame_function=f'beats.{fn_name}(t_local, sil=False)', n_sub=b[3],
             shutter_deg=180 if b[3] > 1 else None, planes=b[4], streak_px_ground=b[5])
    if extra: e.update(extra)
    return e

RUN_STAGE = ['far 0.35 (shed wall/quoins/bushes: Bourre 50866795131 + 50866798791)', 'mid 0.6 (platform wall + far meadow)',
             'ground 1.0 (meadow grass, earth)', 'figure 1.0 (camera-locked)', 'near 1.6 (close grass)']
slot_map = {
    'I.1': beat_entry('I1_manteau', 'I1', dict(rig='folded coat: 3 hinged pieces (fold lines y=330, 485 of the coat panel), fold=0.84 (z-fold 145 deg), bundle laid -90 deg and squashed 0.5 on the seat')),
    'I.2': beat_entry('I2_cloche', 'I2', dict(rig='visitor front profile (LoC 2017750548) walking: legs below the hem alternate lift+foreshorten at 0.9 Hz; bell damped pendulum struck at film 4.6', bell=bell_check())),
    'I.3': beat_entry('I3_cle', 'I3', dict(rig='HANDMADE envelope: flap hinged at the top edge, theta 0->180 deg over 0.5 s (cos foreshortening, reverse printed 0.8); key slides out 0.55-1.3 s')),
    'I.4': beat_entry('I4_banc', 'I4', dict(rig='visitor bows (upper body compress 0.32 about the waist, 0.1-0.55 s), key travels hand->coat on an arc (0.3-0.75 s), contact shadow, she straightens (0.95-1.4 s)',
                                            silhouette_check=rel(os.path.join(S.AN, 'checks/sil_I4.png')))),
    'I.5': beat_entry('I5_recu', 'I5', dict(rig='receipt: terminal fall 170 px/s, lateral drift 60 px at 0.9 Hz, rotation 40 deg at 1.1 Hz, flip cos(2pi 0.8 t); lands at her feet ~1.2 s')),
    'I.6': beat_entry('I6_porte', 'I6', dict(rig='visitor back profile (LoC 2017750547) walking off right and away (scale 0.9->0.55); camera push 1.00->1.07 toward the shed door')),
    'II.2': beat_entry('II2_manteau', 'II2', dict(rig='coat unfolds on its hinges as it is lifted (fold 0.84->0, lift 520 px); brass glint on frames 6-11 (6 frames); at 0.9 s cut through the bench holdout: conductor (walk pose 1 Hz) drawn BEHIND the bench plane',
                                                 silhouette_check=[rel(os.path.join(S.AN, 'checks/sil_II2.png')), rel(os.path.join(S.AN, 'checks/sil_II2_swap.png'))],
                                                 runner=runner_checks(lambda t: (S.walk_pose(max(t - 0.9, 0), 1.0)[0], (500, 400, 0.42 * 1.45 * 0.6, 4.0)), FR))),
    'III.4': beat_entry('III4_manteau', 'III4', dict(parallax=par([0.35, 1.0], 160), runner=runner_checks(lambda t: (S.run_pose(t)[0], (300 + 440 * t, 300, 0.14, -8.0)), FR),
                                                     rig='same coat cutout and dye at 0.14 scale (1/5 of V.3), running gait 2.3 Hz')),
    'IV.5': beat_entry('IV5_manteau', 'IV5', dict(parallax=par([0.35, 0.6, 1.0, 1.6], 1500), runner=runner_checks(lambda t: (S.run_pose(t)[0], (1700 - 2400 * t, 120, 1.9, 8.0)), FR),
                                                   planes_list=RUN_STAGE, rig='coat at 1.9 scale crossing at 2400 px/s: its own 50 px smear per exposure')),
    'V.1': beat_entry('V1_banc', 'V1', dict(parallax=par([0.35, 0.6, 0.8, 1.0, 1.6], 4200), planes_list=RUN_STAGE + ['bench plane 0.8'])),
    'V.2': beat_entry('V2_recu', 'V2', dict(parallax=par([0.35, 0.6, 1.0, 1.6], 4200), planes_list=RUN_STAGE,
                                            runner=runner_checks(lambda t: (S.run_pose(40.5 + t)[0], (S.X_LOCK, S.HIP_Y, S.SCALE, S.LEAN)), FR))),
    'V.3': dict(clip=rel(os.path.join(S.ED, 'clips/V3_manteau_clean.mp4')), typed_clip=rel(os.path.join(S.SW, 'testshot.mp4')),
                window_film_s=TM['window'], frame_function='scene.v3_sub(film_t) integrated by scene.integrate(..., n=36, shutter=0.5)',
                n_sub=36, shutter_deg=180, planes=RUN_STAGE, parallax_ratios=[0.35, 0.6, 1.0, 1.0, 1.6],
                streak_px_per_exposure=TM['streak_px_per_exposure'], parallax_px_per_frame=TM['parallax_px_per_frame'],
                parallax_order_all_frames=TM['parallax_order_near_gt_ground_gt_mid_gt_far_all_frames'],
                pivot_max_px=TM['pivot_max_px'], rig='runner FK (rig_runner.json): hip/knee per leg, coat tails at the waist, sleeve at the shoulder, forearm at the elbow; gait 2.3 Hz, lean -10 deg (forward), bob 9 px',
                coat_height_frac=TM['coat_height_frac'], cap_top_y=TM['cap_top_y'], key_drop=dict(TM['key_drop'], positions=TM['key_drop']['positions']),
                still=rel(os.path.join(S.SW, 'testshot_43.3.png')), board=rel(os.path.join(S.SW, 'testshot-board.jpg')),
                measures_43_3=TM['still_measures'], reference_measures=TM['reference_measures'],
                silhouette_check=rel(os.path.join(S.AN, 'checks/sil_V3_43.3.png'))),
    'V.4': beat_entry('V4_cle', 'V4', dict(parallax=par([0.35, 0.6, 1.0, 1.6], 4200), planes_list=RUN_STAGE,
                                           rig='key on the ground plane (moves with ratio 1.0), one bounce; camera Hermite brake 43.5-44.2 with overshoot, rests on the key (the plate re-forms as a still photograph); forearm piece turned -105 deg comes down 44.35, takes the key 44.7')),
    'V.5': beat_entry('V5_porte', 'V5', dict(rig='key turns in the lock (x-foreshortening about its shaft, 0-0.35 s); right door leaf (cut from the plate along its frame) swings in on its outer hinge 0->82 deg (perspective quad, free edge recedes 10%); behind it true black')),
    'VI.1': beat_entry('VI1_cloche', 'VI1', dict(bell=dict(model='continuation of V.6 (theta0 26 deg, tau 1.5) with an added damper tau 0.6 s from 48.0', amplitude_at_48_deg=round(26 * math.exp(-1.4 / 1.5), 2),
                                                                amplitude_at_49_5_deg=round(26 * math.exp(-1.4 / 1.5) * math.exp(-1.5 / 0.6), 2)))),
}
bell_slots = {'II.4': 16.5, 'III.5': 27.0, 'IV.3': 33.0, 'V.6': 46.5}
for sid in bell_slots:
    slot_map[sid] = beat_entry('bell_strike', 'bell_clip', dict(note='same bell clip; strike at local 0.1 s = film ' + str(round(bell_slots[sid] + 0.1, 1)), bell=bell_check()))
reuse = {'IV.2': 'replay of I.4 exact pixels (clip I4_banc) inside the typed frame I·4 (editor)',
         'VI.2': 'replay of I.4 exact pixels (clip I4_banc) inside the typed frame I·4 (editor)',
         'VI.6': 'the folded coat on the bench again: clip I1_manteau (identical pixels, signature identity)',
         'II.5': 'empty bench: beats.I1 without the coat -> use beats.bench_empty', 'IV.6': 'empty bench: beats.bench_empty',
         'III.3': 'bench, gravel, nothing: beats.bench_empty'}

slots = []
for m in ST['modules']:
    for a in m['appearances']:
        e = dict(id=a['id'], motif=a['motif_fr'], start=a['start'], end=a['end'], function=a['function'], streak_plan=m.get('streak'))
        if a['id'] in slot_map: e.update(slot_map[a['id']]); e['owner'] = 'animator'
        elif a['id'] in reuse: e['animator'] = reuse[a['id']]; e['owner'] = 'animator (reuse) / editor'
        else: e['owner'] = 'print-sound / editor (typeset or insert, not an animated beat of this unit)'
        slots.append(e)

V3m = TM['still_measures']
out = dict(
    unit='animator: scene authors, Reiniger rig, multiplane, stencil dye, pan exposure (SCIONs 2, 29 (cut), 32 (FK), 44)',
    revision='A1', date='2026-11-16',
    module=dict(scene=rel(os.path.join(S.HERE, 'scene.py')), beats=rel(os.path.join(S.HERE, 'beats.py')), cut=rel(os.path.join(S.HERE, 'cut.py')),
                writer=rel(os.path.join(S.HERE, 'scenes_json.py')), rig=rel(os.path.join(S.AN, 'rig_runner.json')),
                pieces=rel(os.path.join(S.AN, 'cut/pieces.npz')), cut_log=rel(os.path.join(S.AN, 'cut/cut_log.json')),
                dye_masks=rel(os.path.join(S.AN, 'dye')), clips=rel(CL), stills=rel(STL),
                usage='python3 -I cut.py; python3 -I scene.py testshot; python3 -I beats.py; python3 -I scenes_json.py. '
                      'Editor: clips are 960x540, 24 fps, 36 frames (1.5 s), silent, no type; or import beats and call the frame functions.'),
    methods=dict(
        stencil='Each plate printed monochrome on its own hard curve (p1 -> black, p99.6 -> paper) and dyed through masks keyed from the plate\'s hues: grass (yellow-green/mid/deep green by original hue, density from the print, cream on the hottest blades), soil (ochre, red earth in the darker half), brick quoins red, plaster yellow-ochre, trees deep green, sky left cream paper. Coat: #e2011b over a print stretched on the coat\'s own p2..p98.5 so the folds stay; warm sheen on the top 12%. Key brass, bell bronze. Masks saved in dye/.',
        multiplane='Long planes assembled from distinct crops of the two Bourre plates joined by 72 px cross-fades (no mirror tiling); far 0.35 / mid 0.6 / bench 0.8 / figure 1.0 / near 1.6; the camera tilted down so no sky enters V.3.',
        pan_exposure='Every frame = mean of n sub-frames over a 180-degree shutter (1/48 s). Streak length per plane = ratio x camera speed / 48. No blur kernel on any picture (contact-shadow and stencil-edge masks are softened, never the image).',
        rig='Reiniger/FK: all runner pieces share the photo\'s pixel frame; child transform = parent @ T(pivot - child_pivot) @ R(child_pivot, angle) @ S; angle limits clamp every pose. Replacement profiles for the visitor (front walking in, back walking off).',
        test_shot_fixes='(1) runner actually runs: new knee joint below the hem (thigh 460->700, shin hinged there, 1.75 stretch), hip -35..40, knee -75..0, 2.3 Hz stride, forward lean -10 deg, sleeve and forearm swing in counter-phase, coat tails swing at the waist; (2) coat keeps its folds (local p2..p98.5 stretch before the dye); (3) colour edge to edge: no sky, planes cut from grass/wall/bush bands, no mirror seams; (4) tonal range: hard print curve (true blacks), cream highlights on hot blades, ochre and red-earth soil dye in the streak; (5) English gloss in cream on a black band.'),
    test_shot=dict(file=rel(os.path.join(S.SW, 'testshot.mp4')), still=rel(os.path.join(S.SW, 'testshot_43.3.png')), board=rel(os.path.join(S.SW, 'testshot-board.jpg')),
                   measures=rel(os.path.join(S.AN, 'testshot_measures.json')),
                   targets=dict(coat_hue_within_8deg_of_minus6=(V3m['coat_hue_deg'] is not None and abs(V3m['coat_hue_deg'] - (-6.0)) <= 8),
                                coat_sat_ge_0_75=(V3m['coat_sat'] or 0) >= 0.75, green_ge_25pct=V3m['green_pct'] >= 25,
                                lower_gy_gx_ge_1_3=V3m['lower_gy_gx'] >= 1.3, coat_height_ge_0_55=TM['coat_height_frac'] >= 0.55,
                                head_at_top_edge=TM['cap_top_y'] <= 0, pivot_le_1px=TM['pivot_max_px'] <= 1.0,
                                parallax_order=TM['parallax_order_near_gt_ground_gt_mid_gt_far_all_frames'],
                                key_parabola=TM['key_drop']['parabola'])),
    silhouette_checks=dict(I4=rel(os.path.join(S.AN, 'checks/sil_I4.png')), II2=[rel(os.path.join(S.AN, 'checks/sil_II2.png')), rel(os.path.join(S.AN, 'checks/sil_II2_swap.png'))],
                           V3=rel(os.path.join(S.AN, 'checks/sil_V3_43.3.png')), method='figures and props painted black on white, colour and stage removed; judged by eye (perceptual, not measured)'),
    slots=slots,
    evidence=json.load(open(os.path.join(S.HERE, 'evidence.json'))),
)
json.dump(out, open(os.path.join(S.SW, 'scenes.json'), 'w'), indent=1, ensure_ascii=False)
print('wrote scenes.json', len(slots), 'slots')
print(json.dumps(out['test_shot']['targets'], indent=1))
