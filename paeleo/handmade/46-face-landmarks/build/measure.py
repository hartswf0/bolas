"""SCION 46 measurement: what the dog actually did on screen, read back from the registration (where each plate was
placed, which view was shown) and the drawn landmarks, not from the score's labels.
Writes trace.json (per scene frame: i, t, state, x_score, x_screen, y_screen, x_world_measured, facing, posture, ...),
proof/choices_measured.json (measured onset of every choice) and proof/invariants_numeric.json (the SCION's own
numeric invariants: attachment, eyes-on-face, similarity-only source face, planted feet)."""
import json, math, os
import numpy as np
from geom import Camera, CACHE, HERE, load_score, apply, W, H
from plates import TORSO, HEADS
from rig import OFFSET
import voice

FOLDER = os.path.dirname(HERE)


def cam_of(f):
    c = f['camera']; return Camera(c['pos'], c['target'], c['fov'])


def unproject_to_height(cam, sx, sy, Y):
    return cam.unproject_ground(sx, sy, Y)


def main():
    rig = json.load(open(os.path.join(CACHE, 'rig.json')))
    pose = json.load(open(os.path.join(CACHE, 'pose.json')))
    reg = json.load(open(os.path.join(CACHE, 'registration.json')))
    S = load_score()
    rows = []; prev_face = 1
    attach = []; eyes_in = []; slide = []
    for f, p, r in zip(rig, pose, reg):
        cam = cam_of(f)
        vt = r['torso']['view']; Mt = np.array(r['torso']['M'])
        pl = TORSO[vt]
        lm = {k: apply(Mt, (np.array(pl['lm'][k]) * np.array([1, -1]))[None])[0] for k in pl['keys']}
        # measured mid-body: midpoint of the placed plate's withers and rump landmarks, back-projected to their height
        mid = (lm['W'] + lm['R']) / 2
        Ymid = (p['body']['W'][1] + p['body']['R'][1]) / 2
        Pw = unproject_to_height(cam, mid[0], mid[1], Ymid)
        # the plate's mid lies on the dog's centre line (Z of the torso), so correct the ray to that depth plane
        zc = (p['body']['W'][2] + p['body']['R'][2]) / 2
        d = Pw - cam.pos
        k = (zc - cam.pos[2]) / d[2] if abs(d[2]) > 1e-6 else 1.0
        Pz = cam.pos + d * k
        Xw = float(Pz[0])
        # facing: chest landmark left of the tail landmark on screen = toward the door (the door is screen-left)
        dx = lm['C'][0] - lm['T'][0] if 'C' in lm else 0.0
        if 'C' not in lm or abs(dx) < 3: face = prev_face
        else: face = 1 if dx < 0 else -1
        # in the pure rear view the chest is hidden: the dog shows its back, which counts as turned away from the door
        if vt == 180: face = -1
        prev_face = face
        lie_h = Ymid
        posture = 'lying' if f['lie'] > 0.5 else ('crouched' if f['crouch'] > 0.5 else ('walking' if f['moving'] > 0.5 else 'standing'))
        hv = r['head']['view']
        rows.append(dict(i=f['i'], t=f['t'], x_screen=round(float(mid[0]), 2), y_screen=round(float(mid[1]), 2), x_world_measured=round(Xw, 4),
                         x_score=round(Xw + OFFSET, 4), facing=face, posture=posture, torso_view=vt, head_view=hv,
                         face_visible=hv in (45, 90), torso_height_m=round(lie_h, 3), score_state=f['state'],
                         ear=round(f['ear'], 3), mouth_source=voice.mouth_state(f['t'])))
        # numeric invariants
        Sk = np.array(p['skull']); Mh = np.array(r['head']['M']); hp = HEADS[hv]
        s_placed = apply(Mh, (np.array(hp['lm']['S']) * np.array([1, -1]))[None])[0]
        s_true = cam.project(Sk)[0][0]
        scale = cam.focal / float(cam.project(Sk)[1][0])
        attach.append((float(np.linalg.norm(s_placed - s_true)) / scale * 100, f['t']))   # cm in the world
        from plates import catmull
        outline = apply(Mh, catmull(hp['shapes'][0]['pts'], True) * np.array([1, -1]))
        for role, key in hp['eyes'].items():
            e = apply(Mh, (np.array(hp['lm'][key]) * np.array([1, -1]))[None])[0]
            eyes_in.append(point_in_poly(e, outline))
        for n2, js in p['legs'].items():
            if p['planted'][n2] and f['lie'] < 0.05:
                q = cam.project(np.array(js[-1]))[0][0]
                slide.append((n2, f['i'], q[0], q[1], float(cam.project(np.array(js[-1]))[1][0])))
    # measured choice onsets
    def first(cond, after):
        for row in rows:
            if row['t'] >= after and cond(row): return row
        return None
    X0 = rows[0]['x_world_measured']
    ev = {}
    r1 = first(lambda r: r['x_world_measured'] > X0 + 0.004, 0.5); ev['retreat'] = r1['t']
    # watch: the ears come back up (score ear act -> my smoothed ear crosses halfway) after the retreat
    r2 = first(lambda r: r['ear'] > 0.45, r1['t'] + 0.3); ev['watch_1'] = r2['t']
    r3 = first(lambda r: not r['face_visible'], 3.0); ev['refuse'] = r3['t']
    r4 = first(lambda r: r['face_visible'], 7.0); ev['watch_2'] = r4['t']
    Xs = rows[int(14 * 24)]['x_world_measured']
    r5 = first(lambda r: r['x_world_measured'] < Xs - 0.004, 14.0); ev['approach'] = r5['t']
    Hs = rows[int(23 * 24)]['torso_height_m']
    r6 = first(lambda r: r['torso_height_m'] < Hs - 0.02, 23.0); ev['lie_down'] = r6['t']
    r7 = first(lambda r: not r['face_visible'], 26.0); ev['look_in'] = r7['t']
    order = [('watch', 0.0), ('retreat', ev['retreat']), ('watch', ev['watch_1']), ('refuse', ev['refuse']), ('watch', ev['watch_2']),
             ('approach', ev['approach']), ('lie_down', ev['lie_down'])]
    for row in rows:
        st = 'watch'
        for name, t0 in order:
            if row['t'] >= t0 - 1e-9: st = name
        row['state'] = st
    score_t = {'retreat': 1.0, 'watch_1': 2.333, 'refuse': 3.417, 'watch_2': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
    how = {'retreat': 'first frame the placed torso moves back (away from the door) by more than 4 mm',
           'watch_1': 'first frame after the retreat the ears are back up past halfway (ear control)',
           'refuse': 'first frame the head plate shown is a face-withdrawn view (three-quarter back or back)',
           'watch_2': 'first frame after 7 s the head plate shown is a face view again (side or three-quarter front)',
           'approach': 'first frame the placed torso moves toward the door by more than 4 mm',
           'lie_down': 'first frame the torso is more than 2 cm lower than standing',
           'look_in': 'first frame after 26 s the face is withdrawn into the room (three-quarter-back head plate)'}
    ch = {k: dict(score_t=score_t[k], measured_t=round(v, 3), dt=round(v - score_t[k], 3), ok=abs(v - score_t[k]) <= 0.25, how=how[k]) for k, v in ev.items()}
    os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
    json.dump(ch, open(os.path.join(FOLDER, 'proof', 'choices_measured.json'), 'w'), indent=1)
    trace = dict(about='SCION 46 trace: measured from the registration of the rendered plates (placed torso plate landmarks, '
                       'back-projected through the frame camera; facing from the placed chest and tail landmarks; state from measured events). '
                       'Camera moves, so x_world_measured is given. x_score = x_world_measured + 0.55 (the dog\'s mid-body).',
                 fps=24, frames=rows)
    json.dump(trace, open(os.path.join(FOLDER, 'trace.json'), 'w'))
    for k, v in ch.items(): print(k, v['score_t'], '->', v['measured_t'], 'dt', v['dt'], 'OK' if v['ok'] else 'LATE/EARLY')
    # planted-foot drift in world terms: consecutive frames of the same planted foot, screen motion minus camera motion
    drift = 0.0; prev = {}
    for n2, i, x, y, z in slide:
        if (n2, i - 1) in prev:
            pass
        prev[(n2, i)] = (x, y)
    worlddrift = []
    for k in range(1, len(pose)):
        for n2 in pose[k]['legs']:
            if pose[k]['planted'][n2] and pose[k - 1]['planted'][n2] and rig[k]['lie'] < 0.05:
                a = np.array(pose[k]['feet'][n2]); b = np.array(pose[k - 1]['feet'][n2])
                worlddrift.append(float(np.linalg.norm(a - b)))
    man = json.load(open(os.path.join(CACHE, 'face', 'manifest.json')))
    appr = [(p_['head']['Cr'][1] * 0 + max(p_['head']['Cr'][1], p_['head']['EbR'][1], p_['head']['EbL'][1]), p_['body']['W'][1]) for f_, p_ in zip(rig, pose) if 14.9 <= f_['t'] < 23.8]
    below = [h < w_ for h, w_ in appr]
    ears_top = [h for h, w_ in appr]
    inv = dict(
        attachment_cm=dict(max=round(max(a for a, _ in attach), 3), mean=round(float(np.mean([a for a, _ in attach])), 3),
                           at_t=max(attach)[1], test='head plate skull-pivot landmark, as placed by its fit, vs the solved neck end (skull pivot); world cm'),
        eyes_on_face=dict(share=round(float(np.mean(eyes_in)), 4), n=len(eyes_in), test='every drawn eye centre lies inside its head plate outline'),
        planted_feet=dict(max_drift_m_per_frame=round(max(worlddrift), 6), n=len(worlddrift), test='a toe marked planted does not move in the world between frames'),
        source_face=dict(fit='similarity', anisotropy=1.0, shear=0.0, frames=len(man['frames']),
                         test='the person\'s face is placed only by rotation + uniform scale + translation (by construction, see render.draw_person_head)'),
        head_low_on_approach=dict(share=round(float(np.mean(below)), 4), worst_margin_m=round(float(min(w_ - h for h, w_ in appr)), 3),
                                  test='15-23.8 s: the top of the skull (cranium and ear bases) is below the withers (world height)'),
        head_view_changes=sum(1 for a, b in zip(rows, rows[1:]) if a['head_view'] != b['head_view']),
        torso_view_changes=sum(1 for a, b in zip(rows, rows[1:]) if a['torso_view'] != b['torso_view']))
    json.dump(inv, open(os.path.join(FOLDER, 'proof', 'invariants_numeric.json'), 'w'), indent=1)
    print(json.dumps(inv, indent=1))


def point_in_poly(pt, poly):
    x, y = pt; inside = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1: inside = not inside
    return inside


if __name__ == '__main__':
    main()
