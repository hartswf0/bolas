"""SCION 23 · the skeletal runtime. 2D only: it reads a skeleton JSON, a clip library and a track timeline and, for
any time t, poses the actor.

  AnimationState  tracks of queued clips; each entry has a start and a mix duration. Within a track the incoming
                  clip cross-fades the outgoing one channel by channel (translate, rotate by the short arc, scale,
                  IK mix); attachments and draw order switch at alpha 0.5 (Spine's attachment threshold). A higher
                  track (the head) is layered over the lower (the body) on the channels it keys; an empty entry
                  mixes a track out.
  world transform position and rotation inherit from the parent, scale does not ("noScale").
  IK              two-bone constraints per leg; the bend side follows the posed (FK) knee; the paw (and for hind
                  legs the metatarsus) keep their posed world angle.
  foot planner    holds each paw where it was planted while the IK mix is on; steps a paw (a timed swing with a
                  lift) when the pose wants it elsewhere, at most two paws in the air and never both of a girdle;
                  leads the step by the root's velocity. It is the only thing that moves feet over the ground.
  geometry        region attachments (affine, optionally foreshortened by the bone's scaleX) and weighted mesh
                  attachments (linear blend skinning), in draw order, in skeleton-world centimetres.
"""
import json, math
import numpy as np

D2R = math.pi / 180


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


class Clip:
    def __init__(self, name, d):
        self.name, self.dur, self.loop = name, d['duration'], d.get('loop', False)
        self.bones = {}
        for b, tl in d['bones'].items():
            ch = {}
            if tl.get('rotate'):
                ch['r'] = (np.array([k['time'] for k in tl['rotate']]), np.array([k['value'] for k in tl['rotate']]))
            if tl.get('translate'):
                tt = np.array([k['time'] for k in tl['translate']])
                ch['x'] = (tt, np.array([k['x'] for k in tl['translate']]))
                ch['y'] = (tt, np.array([k['y'] for k in tl['translate']]))
            if tl.get('scale'):
                ch['sx'] = (np.array([k['time'] for k in tl['scale']]), np.array([k['x'] for k in tl['scale']]))
            self.bones[b] = ch
        self.att = {s: [(k['time'], k['name']) for k in v['attachment']] for s, v in d.get('slots', {}).items()}
        self.order = [(k['time'], k['order']) for k in d.get('drawOrder', [])]
        self.ik = {c: (np.array([k['time'] for k in v]), np.array([k['mix'] for k in v])) for c, v in d.get('ik', {}).items()}
        self.events = d.get('events', [])

    def local_time(self, t):
        if self.loop: return t % self.dur
        return min(max(t, 0.0), self.dur)

    def sample(self, t):
        u = self.local_time(t)
        vals = {}
        for b, ch in self.bones.items():
            for c, (tt, vv) in ch.items():
                if c == 'r':
                    i = np.searchsorted(tt, u, side='right') - 1
                    if i < 0: v = vv[0]
                    elif i >= len(tt) - 1: v = vv[-1]
                    else:
                        f = (u - tt[i]) / (tt[i + 1] - tt[i])
                        v = vv[i] + wrap(vv[i + 1] - vv[i]) * f
                    vals[(b, c)] = v
                else:
                    vals[(b, c)] = float(np.interp(u, tt, vv))
        for c, (tt, vv) in self.ik.items():
            vals[('ik', c)] = float(np.interp(u, tt, vv))
        att = {}
        for s, ks in self.att.items():
            cur = ks[0][1]
            for kt, nm in ks:
                if kt <= u + 1e-6: cur = nm
            att[s] = cur
        order = None
        for kt, od in self.order:
            if kt <= u + 1e-6 or order is None: order = od
        return vals, att, order


class SkeletonData:
    def __init__(self, skel_path, clips_path):
        d = json.load(open(skel_path))
        self.d = d
        self.bones = d['bones']
        self.index = {b['name']: i for i, b in enumerate(self.bones)}
        self.parent = [self.index[b['parent']] if b['parent'] else -1 for b in self.bones]
        self.slots = d['slots']
        self.slot_bone = {s['name']: s['bone'] for s in self.slots}
        self.skin = d['skins'][0]['attachments']
        self.ik = d.get('ik', [])
        c = json.load(open(clips_path))['animations']
        self.clips = {k: Clip(k, v) for k, v in c.items()}
        self.setup_order = [s['name'] for s in self.slots]
        self.setup_att = {s['name']: s['attachment'] for s in self.slots}


def lerp_ch(c, a, b, f):
    if c == 'r': return a + wrap(b - a) * f
    return a + (b - a) * f


class AnimationState:
    """entries: list of dict(track, clip (None = empty), start, mix, loop)"""
    def __init__(self, data, entries):
        self.data = data
        self.tracks = {}
        for e in sorted(entries, key=lambda e: (e['track'], e['start'])):
            self.tracks.setdefault(e['track'], []).append(e)

    def current(self, track, t):
        es = self.tracks.get(track, [])
        cur = prev = None
        for e in es:
            if e['start'] <= t + 1e-9: prev, cur = cur, e
        return prev, cur

    def apply(self, t):
        D = self.data
        pose = {}
        for b in D.bones:
            pose[(b['name'], 'x')] = b['x']; pose[(b['name'], 'y')] = b['y']
            pose[(b['name'], 'r')] = b['rotation']; pose[(b['name'], 'sx')] = b.get('scaleX', 1.0)
        for c in D.ik: pose[('ik', c['name'])] = c.get('mix', 1.0)
        att = dict(D.setup_att); order = list(D.setup_order)
        alphas = {}
        for track in sorted(self.tracks):
            prev, cur = self.current(track, t)
            if cur is None: continue
            a = 1.0 if cur['mix'] <= 0 else min(1.0, (t - cur['start']) / cur['mix'])
            alphas[track] = (cur['clip'], a)
            vc, ac, oc = ({}, {}, None)
            if cur['clip']:
                vc, ac, oc = D.clips[cur['clip']].sample(t - cur['start'])
            vp, ap, op = ({}, {}, None)
            if prev is not None and prev['clip'] and a < 1:
                vp, ap, op = D.clips[prev['clip']].sample(t - prev['start'])
            keys = set(vc) | set(vp)
            for k in keys:
                base = pose[k]
                c = k[1] if k[0] != 'ik' else 'm'
                if k in vc and k in vp: pose[k] = lerp_ch(c, vp[k], vc[k], a)
                elif k in vc: pose[k] = lerp_ch(c, base, vc[k], a)
                else: pose[k] = lerp_ch(c, base, vp[k], 1 - a)
            if a >= 0.5 or not ap:
                att.update(ac)
                if oc: order = oc
            else:
                att.update(ap)
                if op: order = op
        return pose, att, order, alphas

    def events_between(self, t0, t1):
        out = []
        for track, es in self.tracks.items():
            for e in es:
                if not e['clip']: continue
                for ev in self.data.clips[e['clip']].events:
                    te = e['start'] + ev['time']
                    nxt = [x for x in es if x['start'] > e['start']]
                    if nxt and te >= nxt[0]['start']: continue
                    if t0 < te <= t1: out.append((te, ev['name'], track))
        return out


def world_transforms(D, pose, root_xy):
    n = len(D.bones)
    P = np.zeros((n, 2)); TH = np.zeros(n); SX = np.ones(n)
    for i, b in enumerate(D.bones):
        nm = b['name']
        lx, ly, r, sx = pose[(nm, 'x')], pose[(nm, 'y')], pose[(nm, 'r')], pose[(nm, 'sx')]
        p = D.parent[i]
        if p < 0:
            P[i] = (root_xy[0] + lx, root_xy[1] + ly); TH[i] = r * D2R
        else:
            c, s = math.cos(TH[p]), math.sin(TH[p])
            P[i] = (P[p][0] + lx * c - ly * s, P[p][1] + lx * s + ly * c)
            TH[i] = TH[p] + r * D2R
        SX[i] = sx
    return P, TH, SX


def two_bone(Pu, a, b, T, elbow_hint, side=None):
    v = T - Pu
    d0 = math.hypot(*v)
    d = max(abs(a - b) + 1e-3, min(a + b - 1e-3, d0))
    ca = (a * a + d * d - b * b) / (2 * a * d)
    A = math.acos(max(-1.0, min(1.0, ca)))
    base = math.atan2(v[1], v[0])
    best = None
    for sgn in (1, -1):
        t1 = base + sgn * A
        E = Pu + a * np.array([math.cos(t1), math.sin(t1)])
        dist = np.hypot(*(E - elbow_hint))
        if side is not None:   # side: the sign of cross(girdle->target, girdle->knee) the knee must keep
            cr = v[0] * (E[1] - Pu[1]) - v[1] * (E[0] - Pu[0])
            dist = -side * cr
        if best is None or dist < best[0]: best = (dist, t1, E)
    _, t1, E = best
    T2 = Pu + v / max(d0, 1e-9) * d if d0 > 0 else T
    t2 = math.atan2(T2[1] - E[1], T2[0] - E[0])
    return t1, t2


class FootPlanner:
    LEGS = ('fL', 'fR', 'hL', 'hR')
    PARTNER = dict(fL='fR', fR='fL', hL='hR', hR='hL')

    def __init__(self):
        self.st = {}
        self.last_lift = -9.0
        self.events = []

    def update(self, t, desired, fk_pos, mix, vel, girdle=None, reach=None):
        moving = abs(vel) > 3.0
        thresh = (7.0 if abs(vel) < 40 else 5.0) if moving else 3.2
        Tsw = 0.26 if moving else 0.22
        lift = 4.5 if moving else 3.0
        if abs(vel) > 40:
            lead = np.array([vel * 0.18 * 0.6, 0.0])
        else:
            lead = np.array([vel * Tsw * 0.5 + (math.copysign(min(8.0, abs(vel) * 0.25), vel) if moving else 0.0), 0.0])
        out = {}
        for L in self.LEGS:
            s = self.st.get(L)
            if s is None:
                s = self.st[L] = dict(mode='planted', pos=np.array(desired[L], float))
            if mix[L] < 0.5:
                s.update(mode='free', pos=np.array(fk_pos[L], float))
                continue
            if s['mode'] == 'free':
                s['mode'] = 'planted'
            if s['mode'] == 'swing':
                p = (t - s['t0']) / s['dur']
                goal = desired[L] + lead
                if p >= 1:
                    s['mode'] = 'planted'; s['pos'] = goal.copy()
                    self.events.append((t, 'step', L))
                else:
                    e = p * p * (3 - 2 * p)
                    s['cur'] = s['start'] + (goal - s['start']) * e + np.array([0.0, s['lift'] * math.sin(math.pi * p)])
        swinging = [L for L in self.LEGS if self.st[L]['mode'] == 'swing']
        cands = []
        for L in self.LEGS:
            s = self.st[L]
            if s['mode'] != 'planted': continue
            err = np.hypot(*(desired[L] - s['pos']))
            over = girdle is not None and np.hypot(*(s['pos'] - girdle[L])) > 0.95 * reach[L]
            if err > thresh or (over and err > 1.5): cands.append((err + (100 if over else 0), L))
        cands.sort(reverse=True)
        if abs(vel) > 40:
            # fast (the scramble backwards): trot, diagonal pairs swing together, alternating
            if cands and not swinging:
                L = cands[0][1]
                pair = ('fL', 'hR') if L in ('fL', 'hR') else ('fR', 'hL')
                for Q in pair:
                    s = self.st[Q]
                    if s['mode'] == 'planted':
                        s.update(mode='swing', start=s['pos'].copy(), t0=t, dur=0.18, lift=lift, cur=s['pos'].copy())
                self.last_lift = t
        else:
            for err, L in cands:
                if len(swinging) >= 2 or t - self.last_lift < 0.07: break
                if self.PARTNER[L] in swinging: continue
                s = self.st[L]
                s.update(mode='swing', start=s['pos'].copy(), t0=t, dur=Tsw, lift=lift, cur=s['pos'].copy())
                swinging.append(L); self.last_lift = t
                break
        for L in self.LEGS:
            s = self.st[L]
            out[L] = s['cur'] if s['mode'] == 'swing' else s['pos']
        return out, {L: self.st[L]['mode'] for L in self.LEGS}


class Actor:
    def __init__(self, skel_path, clips_path, entries, planner=True):
        self.D = SkeletonData(skel_path, clips_path)
        self.state = AnimationState(self.D, entries)
        self.planner = FootPlanner() if planner and self.D.ik else None
        self.t_prev = None

    def pose_at(self, t, root_xy, vel=0.0):
        D = self.D
        pose, att, order, alphas = self.state.apply(t)
        P, TH, SX = world_transforms(D, pose, root_xy)
        ix = D.index
        diag = dict(ik={})
        if D.ik:
            desired, fk_pos, mix = {}, {}, {}
            for c in D.ik:
                L = c['name'][4:]
                desired[L] = P[ix[c['target']]].copy()
                end = c['keepWorldRotation'][-1]
                fk_pos[L] = P[ix[end]].copy()
                mix[L] = pose[('ik', c['name'])]
            if self.planner:
                girdle, reach = {}, {}
                for c in D.ik:
                    L = c['name'][4:]
                    u, l = ix[c['bones'][0]], ix[c['bones'][1]]
                    k0 = ix[c['keepWorldRotation'][0]]
                    girdle[L] = P[u]
                    reach[L] = (math.hypot(pose[(D.bones[l]['name'], 'x')], pose[(D.bones[l]['name'], 'y')]) +
                                math.hypot(pose[(D.bones[k0]['name'], 'x')], pose[(D.bones[k0]['name'], 'y')]))
                    if len(c['keepWorldRotation']) == 2:
                        pw = ix[c['keepWorldRotation'][1]]
                        reach[L] += 0.8 * math.hypot(pose[(D.bones[pw]['name'], 'x')], pose[(D.bones[pw]['name'], 'y')])
                targets, modes = self.planner.update(t, desired, fk_pos, mix, vel, girdle, reach)
            else:
                targets, modes = desired, {L: 'planted' for L in desired}
            for c in D.ik:
                L = c['name'][4:]
                m = mix[L]
                if m <= 1e-4:
                    diag['ik'][L] = dict(mode=modes[L], target=targets[L].tolist(), mix=m); continue
                u, l = ix[c['bones'][0]], ix[c['bones'][1]]
                keep = [ix[k] for k in c['keepWorldRotation']]
                a = math.hypot(pose[(D.bones[l]['name'], 'x')], pose[(D.bones[l]['name'], 'y')])
                k0 = keep[0]
                b = math.hypot(pose[(D.bones[k0]['name'], 'x')], pose[(D.bones[k0]['name'], 'y')])
                T = np.array(targets[L], float)
                keep_th = [TH[k] for k in keep]
                if len(keep) == 2:   # hind: hock = paw joint - metatarsus (at its posed world angle)
                    mt = keep[0]; pw = keep[1]
                    lm = math.hypot(pose[(D.bones[pw]['name'], 'x')], pose[(D.bones[pw]['name'], 'y')])
                    am = TH[mt] + math.atan2(pose[(D.bones[pw]['name'], 'y')], pose[(D.bones[pw]['name'], 'x')])
                    T = T - lm * np.array([math.cos(am), math.sin(am)])
                fwd = P[ix['chest']][0] - P[ix['hips']][0]
                side = None
                if abs(fwd) > 8.0:   # elbows point back, stifles forward (in profile and three-quarter views)
                    side = (1 if fwd > 0 else -1) * (1 if L[0] == 'h' else -1)   # = sign of cross(down, forward)
                t1, t2 = two_bone(P[u], a, b, T, P[l], side)
                pu = D.parent[u]
                r_u = wrap((t1 - TH[pu]) / D2R); r_l = wrap((t2 - t1) / D2R)
                nu, nl = D.bones[u]['name'], D.bones[l]['name']
                pose[(nu, 'r')] = lerp_ch('r', pose[(nu, 'r')], r_u, m)
                pose[(nl, 'r')] = lerp_ch('r', pose[(nl, 'r')], r_l, m)
                # keep the posed world angle of the paw (and metatarsus)
                P2, TH2, _ = world_transforms(D, pose, root_xy)
                for k, th in zip(keep, keep_th):
                    nk = D.bones[k]['name']
                    want = wrap((th - TH2[D.parent[k]]) / D2R)
                    pose[(nk, 'r')] = lerp_ch('r', pose[(nk, 'r')], want, m)
                    P2, TH2, _ = world_transforms(D, pose, root_xy)
                diag['ik'][L] = dict(mode=modes[L], target=targets[L].tolist(), mix=m)
            P, TH, SX = world_transforms(D, pose, root_xy)
            for c in D.ik:
                L = c['name'][4:]
                end = ix[c['keepWorldRotation'][-1]]
                diag['ik'][L]['achieved'] = P[end].tolist()
        geo = self.geometry(P, TH, SX, att, order)
        diag.update(P=P, TH=TH, SX=SX, att=att, order=order, alphas=alphas, pose=pose)
        return geo, diag

    def geometry(self, P, TH, SX, att, order):
        D = self.D; ix = D.index
        out = []
        for sl in order:
            an = att.get(sl)
            if not an: continue
            a = D.skin[sl][an]
            bi = ix[D.slot_bone[sl]]
            if a['type'] == 'region':
                th, sx = TH[bi], (SX[bi] if a.get('inheritScale', True) else 1.0)
                c, s = math.cos(th), math.sin(th)
                Rm = np.array([[c * sx, -s], [s * sx, c]])
                out.append(dict(slot=sl, type='region', path=a['path'], R=Rm, P=P[bi].copy(), x=a['x'], y=a['y'],
                                w=a['width'], h=a['height']))
            else:
                v = a['vertices']; i = 0; pts = []
                scaled = a.get('skinning') == 'scaled'
                while i < len(v):
                    n = v[i]; i += 1; acc = np.zeros(2)
                    for _ in range(n):
                        b, lx, ly, w = v[i], v[i + 1], v[i + 2], v[i + 3]; i += 4
                        k = ix[b]; th = TH[k]; sx = SX[k] if scaled else 1.0
                        c, s = math.cos(th), math.sin(th)
                        acc += w * (P[k] + np.array([lx * sx * c - ly * s, lx * sx * s + ly * c]))
                    pts.append(acc)
                out.append(dict(slot=sl, type='mesh', path=a['path'], pts=np.array(pts), uvs=np.array(a['uvs']).reshape(-1, 2),
                                tris=np.array(a['triangles']).reshape(-1, 3)))
        return out
