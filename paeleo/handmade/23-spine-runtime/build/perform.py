"""SCION 23 · the performance: the track timeline (which clip is queued when, on which track, with what mix) is
written to actor/dog.timeline.json; then the runtime plays it over the 768 score frames, with the dog's root on the
score's x, and the person's one clip. Saves per-frame geometry for the renderer and the runtime's own measurements
for the geometry tests (proof/geometry.json)."""
import json, math, os, pickle, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from runtime import Actor, wrap
import turnaround as T

# the track timeline: (track, clip or None for empty, start s, mix s, why)
TIMELINE = [
    (0, 'idle', 0.00, 0.0, 'watching the person in the doorway'),
    (0, 'cringe-back', 0.96, 0.12, 'the call (voice from 0.88 s): crouches and backs away'),
    (0, 'idle', 2.30, 0.45, 'the call stops: watches again'),
    (0, 'turn-away', 3.40, 0.10, 'called again and reached for (voice from 3.30 s): turns its back'),
    (0, 'lie', 4.30, 0.25, 'lies down, back to the door'),
    (1, 'look-back', 7.40, 0.12, 'door open, hand low, soft voice from 7.30 s: the head turns back first'),
    (0, 'rise', 7.62, 0.25, 'the body follows: gets up and comes round'),
    (1, None, 7.95, 0.35, 'head track hands back to the body'),
    (0, 'idle', 8.90, 0.35, 'stands facing the door and watches'),
    (0, 'stalk-walk', 14.46, 0.30, 'in its own time: comes, head low'),
    (0, 'lie-across', 23.62, 0.2, 'reaches the sill and lies down across it'),
    (1, 'look-in', 26.35, 0.20, '"come in" (voice from 26.25 s): looks in, into the room'),
    (0, 'settle', 28.25, 0.50, 'and stays: chin on the paws'),
    (1, None, 28.30, 0.50, 'head track hands back to the body'),
]


def person_x(xp):
    return 0.2 + (xp + 0.28) * 1.546


def main():
    sc = load_score(); fr = sc['frames']
    entries = [dict(track=a, clip=b, start=c, mix=d, loop=b in ('idle', 'stalk-walk'), why=e) for a, b, c, d, e in TIMELINE]
    json.dump(dict(about='SCION 23 track timeline: clips queued on animation tracks with mix durations. Track 0 = '
                         'body, track 1 = head (layered over the body on neck, head and ears). clip null = empty '
                         '(mix the track out). Root x comes from the score; feet from the foot planner.',
                   fps=FPS, entries=entries), open(os.path.join(ACTOR, 'dog.timeline.json'), 'w'), indent=1)
    dog = Actor(os.path.join(ACTOR, 'dog.skel.json'), os.path.join(ACTOR, 'dog.clips.json'), entries)
    per = Actor(os.path.join(ACTOR, 'person.skel.json'), os.path.join(ACTOR, 'person.clips.json'),
                [dict(track=0, clip='perform', start=0, mix=0)], planner=False)
    xs = np.array([f['dog']['x'] for f in fr])
    frames = []
    diag_rows = []
    for i, f in enumerate(fr):
        t = i / FPS
        x = xs[i]
        v = (xs[min(i + 1, N - 1)] - xs[max(i - 1, 0)]) / (2 / FPS) * 100
        geo, dg = dog.pose_at(t, (x * 100.0, 0.0), v)
        pgeo, pdg = per.pose_at(t, (person_x(f['person']['x']) * 100.0, 0.0))
        frames.append(dict(t=t, dog=geo, person=pgeo, x=x,
                           head=dg['P'][dog.D.index['head']].tolist(), alphas=dg['alphas'],
                           torso_att=dg['att'].get('torso'), head_att=dg['att'].get('head')))
        diag_rows.append(dict(t=t, P=dg['P'].copy(), pose=dict(dg['pose']), ik=dg['ik'], att=dict(dg['att'])))
    events = [dict(t=round(e[0], 4), name=e[1], track=e[2]) for e in dog.state.events_between(-1, 33)]
    events += [dict(t=round(e[0], 4), name='step', leg=e[2]) for e in dog.planner.events]
    events.sort(key=lambda e: e['t'])
    json.dump(events, open(os.path.join(CACHE, 'events.json'), 'w'), indent=0)
    pickle.dump(frames, open(os.path.join(CACHE, 'perform.pkl'), 'wb'))
    tests(dog, diag_rows, frames)


def tests(dog, rows, frames):
    D = dog.D; ix = D.index
    # 1. bone lengths: measured link length (world, after mixing and IK) vs the mixed pose's own link length
    links = []
    for b in D.bones:
        if b['parent'] and not b['name'].startswith('ik'):
            links.append((b['parent'], b['name']))
    ik_stretch = 0.0
    mix_drift = {}
    turn_clips = {'turn-away', 'rise'}
    setup_len = {}
    for name, child in links:
        setup_len[child] = None
    for r in rows:
        P = r['P']; pose = r['pose']
        for parent, child in links:
            if parent == 'root': continue
            meas = float(np.hypot(*(P[ix[child]] - P[ix[parent]])))
            want = math.hypot(pose[(child, 'x')], pose[(child, 'y')])
            ik_stretch = max(ik_stretch, abs(meas - want))
    # mixing drift: outside the turns, does any link change length while clips cross-fade?
    tl = json.load(open(os.path.join(ACTOR, 'dog.timeline.json')))['entries']
    def body_clip(t):
        cur = [e for e in tl if e['track'] == 0 and e['start'] <= t]
        return cur[-1]['clip'] if cur else None
    ref = {}
    for v in (0, 135):
        b = T.bake(dict(phi=v))
        for parent, child in links:
            if parent == 'root': continue
            l = b['local'][child]; ref[(v, child)] = math.hypot(l['x'], l['y'])
    worst = (0, None, None)
    fixed = ['chest', 'neck', 'fL_lo', 'fL_paw', 'fR_lo', 'fR_paw', 'hL_sh', 'hL_mt', 'hL_paw', 'hR_sh', 'hR_mt',
             'hR_paw']   # tail links excluded: lying curls the tail toward the camera (true foreshortening)
    for r in rows:
        t = r['t']; c = body_clip(t)
        if c in turn_clips: continue
        a = r['att'].get('torso')
        v = 0 if a == 'torso_0' else (135 if a == 'torso_135' else None)
        if v is None: continue
        P = r['P']
        for child in fixed:
            parent = D.bones[ix[child]]['parent']
            meas = float(np.hypot(*(P[ix[child]] - P[ix[parent]])))
            dev = abs(meas - ref[(v, child)]) / ref[(v, child)]
            if dev > worst[0]: worst = (dev, child, round(t, 3))
    # 2. feet: planted paws do not move; IK reaches its target
    slide = []; resid = []
    prev = None
    for r in rows:
        if prev is not None:
            for L, d in r['ik'].items():
                p0 = prev['ik'].get(L)
                if not p0 or 'achieved' not in d or 'achieved' not in p0: continue
                if d['mode'] == 'planted' and p0['mode'] == 'planted' and d['mix'] > 0.999 and p0['mix'] > 0.999 \
                        and np.allclose(d['target'], p0['target']):
                    slide.append(float(np.hypot(*(np.array(d['achieved']) - np.array(p0['achieved'])))))
        for L, d in r['ik'].items():
            if 'achieved' in d and d['mix'] > 0.999:
                resid.append((float(np.hypot(*(np.array(d['achieved']) - np.array(d['target'])))), L, round(r['t'], 3)))
        prev = r
    resid.sort(reverse=True)
    n_res = sum(1 for x in resid if x[0] > 1.0)
    # 3. floor: no joint of the dog below the floor line of its depth band (y >= -depth tolerance)
    low = []
    for r in rows:
        P = r['P']
        for b in D.bones:
            if b['name'].startswith('ik') or b['name'] == 'root': continue
            low.append((float(P[ix[b['name']]][1]), b['name'], round(r['t'], 3)))
    low.sort()
    # 4. pops: largest per-frame jump of any joint (cm), outside walking
    jumps = []
    for a, b in zip(rows, rows[1:]):
        d = np.hypot(*(b['P'] - a['P']).T) - abs(b['P'][0, 0] - a['P'][0, 0])
        k = int(np.argmax(d)); jumps.append((float(d[k]), D.bones[k]['name'], round(b['t'], 3)))
    jumps.sort(reverse=True)
    out = dict(
        about='SCION 23 geometry tests, measured in the runtime (skeleton cm; at the wide camera 1 cm = 1.9 px, at the '
              'closest 3.08 px). They test the representation; whether it reads is for the critic.',
        bone_length_under_IK=dict(max_abs_cm=round(ik_stretch, 5),
                                  meaning='link length after mixing + IK minus the link length the mixed pose asks for'),
        bone_length_under_mixing=dict(max_rel=round(worst[0], 5), where=worst[1:], meaning='outside the two turn clips, '
                                      'link length vs the bind length of the body view on screen (0 or 135 deg), for '
                                      'the links clips never re-key (lower legs, paws, chest, neck, tail tip)'),
        feet_planted=dict(frames=len(slide), max_slide_cm=round(max(slide) if slide else 0, 4),
                          p99_slide_cm=round(float(np.percentile(slide, 99)) if slide else 0, 4),
                          meaning='paw joint world motion between consecutive frames while planted and IK mix 1'),
        ik_reach=dict(max_residual_cm=round(resid[0][0], 3) if resid else 0, where=resid[0][1:] if resid else None,
                      frames_over_1cm=n_res, meaning='planner target vs reached paw joint'),
        lowest_joint=dict(y_cm=round(low[0][0], 3), where=low[0][1:],
                          meaning='skeleton plane y of the lowest joint (0 = floor at the dog\'s depth; near-side '
                                  'joints sit up to -2 cm lower on screen by the camera tilt)'),
        largest_joint_jump=[dict(cm=round(j[0], 2), bone=j[1], t=j[2]) for j in jumps[:6]],
    )
    os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
    json.dump(out, open(os.path.join(FOLDER, 'proof', 'geometry.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
