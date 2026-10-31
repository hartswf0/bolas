"""SCION 23 · author the runtime actor: actor/dog.skel.json (bones, slots, skins with region and mesh attachments,
IK constraints) and the clip library actor/dog.clips.json (Spine-style timelines baked from the turnaround sheet).

Conventions (stated once, kept everywhere): units are skeleton centimetres, y up, angles in degrees.
Bone transforms inherit position and rotation from the parent, not scale ("transform": "noScale").
Timeline values are ABSOLUTE local values (rotate.value is the local rotation, not an offset from setup), so a clip
fully describes the pose and the view it plays in. Draw order keys list the slots back to front.
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ACTOR
import turnaround as T

ATLAS = json.load(open(os.path.join(ACTOR, 'actors.atlas.json')))
S = 100.0 / ATLAS['ppm_atlas']          # cm per atlas pixel
STEP = 2 / 24                           # bake a key every two frames


def region_att(name, inherit_scale=True, ref_offset=(0.0, 0.0)):
    r = ATLAS['regions'][name]
    w, h = r['size']; ox, oy = r['origin_m']
    return dict(type='region', path=name, x=round(ox * 100 + w * S / 2 - ref_offset[0], 3),
                y=round(oy * 100 - h * S / 2 - ref_offset[1], 3), rotation=0, width=round(w * S, 3),
                height=round(h * S, 3), inheritScale=inherit_scale)


def rigid_local(v, P, th):
    d = np.asarray(v) - P
    c, s = math.cos(-th), math.sin(-th)
    return d[0] * c - d[1] * s, d[0] * s + d[1] * c


def torso_mesh(phi):
    name = 'torso_%d' % phi
    r = ATLAS['regions'][name]
    w, h = r['size']; ox, oy = r['origin_m']
    b = T.bake(dict(phi=phi))
    (Ph, th_h, _), (Pc, th_c, _) = b['world']['hips'], b['world']['chest']
    cols, rows = 10, 6
    uvs, verts, tris = [], [], []
    seg = Pc - Ph; L2 = max(float(seg @ seg), 1e-6)
    for j in range(rows + 1):
        for i in range(cols + 1):
            u, v = i / cols, j / rows
            X = ox * 100 + u * w * S; Y = oy * 100 - v * h * S
            t = float((np.array([X, Y]) - Ph) @ seg) / L2
            wc = float(np.clip((t - 0.2) / 0.65, 0, 1)); wc = wc * wc * (3 - 2 * wc)
            lh = rigid_local((X, Y), Ph, th_h); lc = rigid_local((X, Y), Pc, th_c)
            uvs += [round(u, 5), round(v, 5)]
            verts += [2, 'hips', round(lh[0], 3), round(lh[1], 3), round(1 - wc, 4),
                      'chest', round(lc[0], 3), round(lc[1], 3), round(wc, 4)]
    for j in range(rows):
        for i in range(cols):
            a = j * (cols + 1) + i
            tris += [a, a + 1, a + cols + 1, a + 1, a + cols + 2, a + cols + 1]
    return dict(type='mesh', path=name, uvs=uvs, triangles=tris, vertices=verts, width=round(w * S, 2),
                height=round(h * S, 2), skinning='rigid', note='weighted to hips and chest at the %d deg bind' % phi)


def tail_mesh():
    r = ATLAS['regions']['tail']
    w, h = r['size']; ox, oy = r['origin_m']
    starts = [0.0, 13.0, 26.0]
    cols, rows = 16, 2
    uvs, verts, tris = [], [], []
    for j in range(rows + 1):
        for i in range(cols + 1):
            u, v = i / cols, j / rows
            X = ox * 100 + u * w * S; Y = oy * 100 - v * h * S
            ws = []
            for k, s0 in enumerate(starts):
                s1 = starts[k + 1] if k < 2 else 1e9
                lo = 1 if k == 0 else np.clip((X - (s0 - 3)) / 6, 0, 1)
                hi = 1 if k == 2 else 1 - np.clip((X - (s1 - 3)) / 6, 0, 1)
                ws.append(float(min(lo, hi)))
            tot = sum(ws); ws = [x / tot for x in ws]
            ent = [sum(1 for x in ws if x > 1e-4)]
            for k, x in enumerate(ws):
                if x > 1e-4: ent += ['tail%d' % (k + 1), round(X - starts[k], 3), round(Y, 3), round(x, 4)]
            uvs += [round(u, 5), round(v, 5)]
            verts += ent
    for j in range(rows):
        for i in range(cols):
            a = j * (cols + 1) + i
            tris += [a, a + 1, a + cols + 1, a + 1, a + cols + 2, a + cols + 1]
    return dict(type='mesh', path='tail', uvs=uvs, triangles=tris, vertices=verts, width=round(w * S, 2),
                height=round(h * S, 2), skinning='scaled', note='bound straight along tail1-tail3 (13+13+12 cm)')


def skeleton():
    setup = T.bake(dict(phi=0))
    bones = []
    for name, parent, a, b, rule in T.BONES:
        l = setup['local'][name]
        bl = T.blen(name)
        bones.append(dict(name=name, parent=parent, length=round(bl * 100, 2) if bl else 0, x=l['x'], y=l['y'],
                          rotation=l['rotation'], scaleX=l['scaleX'], transform='noScale'))
    slots = []
    for sl in setup['drawOrder']:
        bone = {'torso': 'hips', 'tail': 'tail1'}.get(sl, sl)
        slots.append(dict(name=sl, bone=bone, attachment=setup['attachments'][sl]))
    skin = {}
    for sl in T.SLOTS:
        skin[sl] = {}
    for phi in (0, 45, 90, 135):
        skin['torso']['torso_%d' % phi] = torso_mesh(phi)
    skin['tail']['tail'] = tail_mesh()
    for psi in (0, 45, 68, 90, 112, 135, 180):
        skin['head']['head_%d' % psi] = region_att('head_%d' % psi, inherit_scale=False)
    skin['neck']['neck_dL'] = region_att('neck_dL')
    skin['neck']['neck_dR'] = region_att('neck_dR')
    for e in ('earL', 'earR'):
        for k in ('ear_side_near', 'ear_side_far', 'ear_back'):
            skin[e][k] = region_att(k)
    for sl in T.SLOTS:
        if sl[0] in 'fh' and '_' in sl:
            seg = sl.split('_')[1] + ('_f' if sl[0] == 'f' else '_h')
            for nf in ('near', 'far'):
                skin[sl][seg + '_' + nf] = region_att(seg + '_' + nf)
    ik = []
    for s in 'LR':
        ik.append(dict(name='leg_f' + s, bones=['f%s_up' % s, 'f%s_lo' % s], keepWorldRotation=['f%s_paw' % s],
                       target='ik_f' + s, mix=1, bendPositive='fromPose', note='wrist placed on target'))
        ik.append(dict(name='leg_h' + s, bones=['h%s_th' % s, 'h%s_sh' % s],
                       keepWorldRotation=['h%s_mt' % s, 'h%s_paw' % s], target='ik_h' + s, mix=1,
                       bendPositive='fromPose', note='hock solved so the metatarsus, kept at its world angle, '
                                                     'puts the paw joint on target'))
    return dict(skeleton=dict(name='dog', spine='4.1-like (own runtime)', units='cm', yUp=True,
                              images='actors.png', atlas='actors.atlas', fps=24),
                bones=bones, slots=slots, ik=ik, skins=[dict(name='default', attachments=skin)],
                events={k: {} for k in ('step', 'thump', 'sigh', 'whimper', 'jingle', 'scrape')})


# ------------------------------------------------------------------------------------------------ clips
def ease(u): return u * u * (3 - 2 * u)


def interp_params(keys, t):
    """keys: list of (time, params). Params are eased between keys; missing params carry over."""
    full = []
    cur = dict(T.DEFAULT)
    for kt, kp in keys:
        cur = dict(cur); cur.update(kp); full.append((kt, cur))
    if t <= full[0][0]: return dict(full[0][1])
    for (t0, p0), (t1, p1) in zip(full, full[1:]):
        if t0 <= t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1
            return {k: p0[k] + (p1[k] - p0[k]) * u if isinstance(p0[k], (int, float)) else p1[k] for k in p0}
    return dict(full[-1][1])


HEAD_BONES = ['neck', 'head', 'earL', 'earR']


def bake_clip(spec):
    dur = spec['duration']
    keys = spec['keys']
    times = list(np.arange(0, dur + 1e-6, STEP))
    if times[-1] < dur - 1e-6: times.append(dur)
    only = HEAD_BONES if spec.get('track') == 'head' else None
    out = dict(bones={}, slots={}, drawOrder=[], ik={}, events=spec.get('events', []), duration=round(dur, 4),
               loop=spec.get('loop', False), track=spec.get('track', 'body'), note=spec.get('note', ''))
    last_att, last_order = {}, None
    for t in times:
        p = interp_params(keys, t)
        if 'fn' in spec: p.update(spec['fn'](t, p))
        b = T.bake(p)
        for name, parent, a, bb, rule in T.BONES:
            if only and name not in only: continue
            if spec.get('track') == 'head' and name.startswith('ik'): continue
            l = b['local'][name]
            tl = out['bones'].setdefault(name, dict(rotate=[], translate=[], scale=[]))
            tl['rotate'].append(dict(time=round(t, 4), value=l['rotation']))
            tl['translate'].append(dict(time=round(t, 4), x=l['x'], y=l['y']))
            tl['scale'].append(dict(time=round(t, 4), x=l['scaleX'], y=1))
        for sl, an in b['attachments'].items():
            if only and sl not in ('head', 'earL', 'earR', 'neck'): continue
            if last_att.get(sl) != an:
                out['slots'].setdefault(sl, dict(attachment=[]))['attachment'].append(dict(time=round(t, 4), name=an))
                last_att[sl] = an
        if not only and b['drawOrder'] != last_order:
            out['drawOrder'].append(dict(time=round(t, 4), order=b['drawOrder']))
            last_order = b['drawOrder']
        if not only:
            mix = p.get('ikmix', 1.0)
            for c in ('leg_fL', 'leg_fR', 'leg_hL', 'leg_hR'):
                out['ik'].setdefault(c, []).append(dict(time=round(t, 4), mix=round(float(mix), 4)))
    return out


def clip_specs():
    C = {}
    stand = dict(phi=0, lie=0, crouch=0.04, neck_elev=50, head_pitch=-12, ear=0.92, tail=0.45, ikmix=1)
    C['idle'] = dict(duration=4.0, loop=True, keys=[(0, dict(stand)), (2.0, dict(body_y=-0.005, tail_yaw=5)),
                                                    (4.0, dict(body_y=0.0, tail_yaw=0))],
                     note='standing, facing the door, alert; breathing and a slow tail sway')
    C['cringe-back'] = dict(duration=1.4, keys=[(0, dict(stand)),
                                               (0.3, dict(crouch=0.75, rear_drop=0.7, neck_elev=16, head_pitch=-26,
                                                          ear=0.05, tail=1.25)),
                                               (0.55, dict(crouch=0.85, rear_drop=0.8, neck_elev=10, head_pitch=-30,
                                                           ear=0.0, tail=1.35)),
                                               (1.4, dict())],
                            events=[dict(time=0.08, name='whimper')],
                            note='the call lands: haunches drop, head and ears go down, tail tucks (root motion '
                                 'backwards comes from the score, the feet from the foot planner)')
    def turn_fn(t, p):
        u = ease(min(1, max(0, t / 0.88)))
        uh = ease(min(1, max(0, (t + 0.12) / 0.88)))    # the head leads by 0.12 s
        phi = 135 * u
        return dict(phi=phi, neck_yaw=-(135 * uh - phi))
    C['turn-away'] = dict(duration=0.9, fn=turn_fn,
                          keys=[(0, dict(phi=0, crouch=0.3, rear_drop=0.4, neck_elev=22, head_pitch=-22, ear=0.4,
                                         tail=0.9, ikmix=1)),
                                (0.5, dict(crouch=0.5, rear_drop=0.5, neck_elev=4, head_pitch=-30, ear=0.15,
                                           tail=1.15)),
                                (0.9, dict())],
                          note='turns its back: body view 0 -> 45 -> 90 -> 135 deg by attachment swaps and slot '
                               'reorders, head 0.12 s ahead, feet stepping round (planner)')
    lying = dict(phi=135, lie=1, crouch=0.5, neck_elev=0, head_pitch=-24, ear=0.15, tail=1.15)
    C['lie'] = dict(duration=2.4, keys=[(0, dict(phi=135, lie=0, crouch=0.5, rear_drop=0.5, neck_elev=4,
                                                 head_pitch=-30, ear=0.15, tail=1.15, ikmix=1)),
                                        (0.18, dict(ikmix=0.0)),
                                        (0.7, dict(lying, rear_drop=0, ikmix=0)),
                                        (1.3, dict()),
                                        (2.1, dict(neck_elev=-27, head_pitch=-22)),
                                        (2.4, dict())],
                    events=[dict(time=0.62, name='thump')],
                    note='lies down with its back to the door, then rests its chin on its paws')
    rest = dict(lying, rear_drop=0, neck_elev=-27, head_pitch=-22, ikmix=0)
    C['look-back'] = dict(track='head', duration=0.5,
                          keys=[(0, dict(rest)), (0.12, dict(neck_yaw=45, neck_elev=-6, head_pitch=-14, ear=0.6)),
                                (0.3, dict(neck_yaw=104, neck_elev=16, head_pitch=-7, ear=0.95)),
                                (0.42, dict(neck_yaw=116, neck_elev=21, head_pitch=-6)), (0.5, dict())],
                          events=[dict(time=0.05, name='jingle')],
                          note='HEAD TRACK: lifts the head off the paws and turns it back over the shoulder to '
                               'the door, muzzle level, while the body track still lies')
    def rise_fn(t, p):
        u = ease(min(1, max(0, (t - 0.42) / 0.8)))
        phi = 135 * (1 - u)
        return dict(phi=phi, neck_yaw=max(0.0, min(116.0, phi - 19)) if t > 0.42 else 116.0,
                    head_over=1.0 if phi > 30 else 0.0)   # the neck shows over the shoulder while it comes round
    C['rise'] = dict(duration=1.3, fn=rise_fn,
                     keys=[(0, dict(rest, neck_elev=21, head_pitch=-6, ear=0.95, ikmix=0)),
                           (0.3, dict(lie=0.35, crouch=0.3, ikmix=0.2)),
                           (0.45, dict(lie=0.0, crouch=0.2, ikmix=1, tail=0.8)),
                           (1.3, dict(crouch=0.06, neck_elev=46, head_pitch=-10, ear=0.95, tail=0.5))],
                     note='gets up still looking at the door, then the body comes round 135 -> 0 deg under the '
                          'head (attachments swap back, far legs go behind again)')
    C['stalk-walk'] = dict(duration=1.0, loop=True,
                           keys=[(0, dict(phi=0, crouch=0.14, neck_elev=-32, head_pitch=-22, ear=0.5, tail=0.32,
                                          tail_yaw=-9, ikmix=1)),
                                 (0.5, dict(tail_yaw=9)), (1.0, dict(tail_yaw=-9))],
                           note='comes, head low below the line of the back; the legs are not keyed: the foot planner'
                                ' plants each paw (IK) as the root travels with the score')
    C['lie-across'] = dict(duration=2.6, keys=[(0, dict(phi=0, crouch=0.1, neck_elev=-30, head_pitch=-22, ear=0.6,
                                                        tail=0.3, ikmix=1)),
                                               (0.15, dict(ikmix=0.0)),
                                               (0.4, dict(lie=0.6, crouch=0.1, neck_elev=-6, head_pitch=-22)),
                                               (0.8, dict(lie=1, crouch=0.1, neck_elev=22, head_pitch=-9, ear=0.7,
                                                          tail=0.3)),
                                               (1.8, dict()), (2.4, dict(neck_elev=10, head_pitch=-14)),
                                               (2.6, dict())],
                           events=[dict(time=0.6, name='thump')],
                           note='lies down across the sill: forelegs and head inside, haunches and tail outside')
    lyin = dict(phi=0, lie=1, crouch=0.1, neck_elev=10, head_pitch=-14, ear=0.7, tail=0.3, ikmix=0)
    C['look-in'] = dict(track='head', duration=0.7,
                        keys=[(0, dict(lyin)), (0.25, dict(neck_yaw=-24, neck_elev=2, head_pitch=-8, ear=0.72)),
                              (0.55, dict(neck_yaw=-54, neck_elev=-4, head_pitch=-5, ear=0.72)), (0.7, dict())],
                        events=[dict(time=0.05, name='jingle')],
                        note='HEAD TRACK: turns the head into the room, away from the camera: the back of the skull'
                             ' and both ears to the viewer, the muzzle level inside the lit doorway')
    C['settle'] = dict(duration=2.0, keys=[(0, dict(lyin, neck_yaw=-54, neck_elev=-4, head_pitch=-5, ear=0.72)),
                                           (0.35, dict(neck_yaw=-30, neck_elev=8, head_pitch=-12, ear=0.7)),
                                           (0.9, dict(neck_yaw=-6, neck_elev=-25, head_pitch=-21, ear=0.4)),
                                           (2.0, dict())],
                       events=[dict(time=0.95, name='sigh')],
                       note='stays: the chin goes down onto the paws, across the sill')
    return C


def main():
    sk = skeleton()
    json.dump(sk, open(os.path.join(ACTOR, 'dog.skel.json'), 'w'), indent=1)
    clips = {name: bake_clip(spec) for name, spec in clip_specs().items()}
    json.dump(dict(about='SCION 23 dog clip library. Absolute local values per key (cm, deg); drawOrder lists '
                         'slots back to front; ik mix per leg constraint; events fire on the time line.',
                   animations=clips), open(os.path.join(ACTOR, 'dog.clips.json'), 'w'))
    print('bones', len(sk['bones']), 'slots', len(sk['slots']), 'clips', list(clips))
    import person
    person.author()


if __name__ == '__main__':
    main()
