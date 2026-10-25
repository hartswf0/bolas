"""SCION 46 rig: turns the PAELEO score into a per-frame pose state, in metres and seconds (time base: score frame i, t=i/24).
Writes build/cache/rig.json. Nothing here draws: it only decides where the dog's and the person's landmarks are.

Typed state per frame:
  dog.body   {X_mid, lift, pitch, heading}          torso pivots (world)
  dog.neck   {elev, yaw}                             skull/neck pivots
  dog.head   {yaw, pitch}                            head pose (world yaw), view chosen later by view-matching
  dog.ctrl   {ear, lid, gaze, mouth, tail, wag}      eye/mouth/ear controls
  dog.feet   4 x world (X,Y,Z)                       planted by the stepper: a foot never slides while it bears weight
  person     {X, Z, sit, lean, reach, low, mouth, voice}
  door       angle (deg, 0 closed)
  camera     pos, target, hfov
Score x -> world: X_mid = x - 0.55 (the dog's mid-body; at the score's sill, 0.56, its front half is in the doorway)."""
import json, math, os
import numpy as np
from geom import load_score, smoothstep, CACHE, FPS

OFFSET = 0.55
TH_WATCH = 172.0     # facing the door, a little toward the viewer
TH_DOOR = 180.0
TH_REFUSE = 318.0    # back turned: rump toward the door, head away, turned through the far side (away from camera)


def ease(a, b, t0, t1, t):
    return a + (b - a) * smoothstep(t0, t1, t)


def unwrap_lerp(a, b, s):
    return a + (b - a) * s


class OneEuro:
    """temporal smoothing of a landmark-driving signal (the SCION's smoothing primitive); cutoff rises with speed so
    deliberate action is kept and only jitter is removed"""
    def __init__(self, mincut=1.2, beta=0.4, dcut=1.0):
        self.mc, self.b, self.dc = mincut, beta, dcut; self.x = None; self.dx = 0.0

    def _a(self, cut, dt):
        r = 2 * math.pi * cut * dt; return r / (r + 1)

    def __call__(self, x, dt=1 / FPS):
        if self.x is None: self.x = x; return x
        dx = (x - self.x) / dt
        self.dx = self.dx + self._a(self.dc, dt) * (dx - self.dx)
        cut = self.mc + self.b * abs(self.dx)
        self.x = self.x + self._a(cut, dt) * (x - self.x)
        return self.x


def body_heading(t):
    # watch -> refuse turn (head leads at 3.42, body 3.50-3.95); refuse -> watch body turn 8.00-8.55 (head leads at 7.46)
    if t < 3.46: return TH_WATCH
    if t < 3.95: return unwrap_lerp(TH_WATCH, TH_REFUSE, smoothstep(3.46, 3.92, t))
    if t < 7.98: return TH_REFUSE
    if t < 8.55: return unwrap_lerp(TH_REFUSE, TH_WATCH, smoothstep(7.98, 8.55, t))
    if t < 14.75: return TH_WATCH
    return ease(TH_WATCH, TH_DOOR, 14.75, 15.6, t)


def head_yaw(t, th_body, lie_head_target):
    h = _head_yaw(t, th_body, lie_head_target)
    if 3.42 <= t < 3.95 or 7.9 <= t < 8.6:   # during the body's turns the head leads by at most 70 degrees
        d = (h - th_body + 180) % 360 - 180
        d = max(-70, min(70, d)); h = th_body + d
    return h


def _head_yaw(t, th_body, lie_head_target):
    """world yaw of the head. It leads every turn: the choice is seen in the face first."""
    if t < 3.42: return th_body - 4 * smoothstep(1.0, 1.3, t) * (t < 2.4)
    if t < 3.95:   # head swings away first, through the far side
        return unwrap_lerp(TH_WATCH, TH_REFUSE + 14, smoothstep(3.42, 3.80, t))
    if t < 7.46: return TH_REFUSE + 14 - 6 * smoothstep(5.0, 6.0, t)
    if t < 8.55:   # 7.46: the head comes round over the shoulder to the door, before the body
        h = unwrap_lerp(TH_REFUSE + 8, 192.0, smoothstep(7.44, 7.66, t))
        return unwrap_lerp(h, TH_WATCH, smoothstep(8.1, 8.6, t))
    if t < 23.8: return th_body
    return lie_head_target(t)


def lying_head(t):
    # after lying at the sill: head toward the person (seated inside, nearer the viewer), then 'come in' -> into the room
    toward_person = 140.0
    into_room = 232.0
    if t < 24.2: return ease(TH_DOOR, toward_person, 23.8, 24.6, t)
    if t < 26.36: return toward_person
    if t < 28.0: return ease(toward_person, into_room, 26.36, 26.62, t)
    return ease(into_room, 215.0, 28.0, 29.0, t)


def build():
    S = load_score(); F = S['frames']; n = len(F)
    out = []
    lift_f = OneEuro(2.0, 0.6); pitch_f = OneEuro(2.0, 0.5)
    elev_f = OneEuro(2.5, 0.6); hp_f = OneEuro(2.5, 0.6); ear_f = OneEuro(3.0, 0.6); tail_f = OneEuro(2.0, 0.5)
    for i, fr in enumerate(F):
        t = fr['t']; d = fr['dog']; a = d['act']; p = fr['person']
        x = d['x']
        if 2.333 <= t < 2.75:   # it stops to watch: the last 11 cm of the backing are taken in 0.17 s, not 0.42 s
            j = min(len(F) - 1, int(round((2.333 + (t - 2.333) * 2.4) * FPS)))
            x = F[j]['dog']['x']
        X_mid = x - OFFSET
        th = body_heading(t)
        lie = a['lie']
        # the refusal lie (4.5-7.4) follows the score's lie; the sill lie follows it too
        crouch = a['crouch']
        lift = lift_f(-0.27 * lie - 0.07 * crouch * (1 - lie))
        pitch = pitch_f(7.0 * crouch * (1 - lie) - 2.0 * lie)
        # neck elevation: head act 0 down .. 1 up ; approach (head .45) must keep the head below the back line
        head = a['head']
        if d['state'] == 'approach' or (14.7 <= t < 23.9):
            elev_t = -38.0 + 6 * math.sin(t * 1.3)
        else:
            elev_t = -30 + 85 * min(1.2, head)
        if lie > 0.5 and t > 23.8:
            rest = a['rest']; look = a['look']
            elev_t = (1 - rest) * (-5 + 55 * min(1.2, head)) + rest * (-62)
        elif lie > 0.5:
            elev_t = -40 - 25 * a['rest']
        elev = elev_f(elev_t)
        hpitch = hp_f(-12 + 22 * min(1.2, head) - 30 * (d['state'] == 'approach') - 25 * a['rest'] * lie)
        hy = head_yaw(t, th, lying_head)
        # ears: score's ear act, plus attention flicks toward the soft voice
        ear = a['ear']
        if 7.4 <= t < 7.7 or 10.4 <= t < 10.7: ear = max(ear, 0.75)
        ear = ear_f(min(1.1, max(-0.1, ear)))
        # eyes: lid openness. wide when afraid, heavy when resting; blinks are choices (a blink before it comes)
        lid = 0.92 - 0.35 * a['rest'] + 0.12 * (crouch > 0.6)
        for tb in (0.55, 2.9, 9.85, 12.7, 14.35, 14.6, 22.2, 25.3, 27.9, 29.6, 31.2):
            if tb <= t < tb + 0.17: lid = min(lid, 0.15 + 4.0 * abs(t - tb - 0.085))
        mouth = 0.0
        if 24.4 <= t < 25.4: mouth = 0.45 * math.sin(math.pi * (t - 24.4))   # the sigh after lying down
        if 15.5 <= t < 23.5: mouth = 0.12
        tail = tail_f(a['tail'])
        wag = a['wag']
        # door
        door = {'closed': 0.0, 'ajar': 9.0, 'open': 96.0}[fr['door']]
        out.append(dict(i=i, t=t, state=d['state'], x_score=x, X_mid=X_mid, heading=th, lift=lift, pitch=pitch, lie=lie,
                        crouch=crouch, elev=elev, hpitch=hpitch, hyaw=hy, ear=ear, lid=lid, mouth=mouth, tail=tail, wag=wag,
                        moving=a['moving'], look=a['look'], rest=a['rest'], door_target=door,
                        person=dict(sit=p['sit'], reach=p['reach'], low=p['low'], mouth=p['mouth'], voice=p['voice'],
                                    place=p['place'], px=p['x'])))
    # door swing: open from 6.2 over 1.1 s with a slow last few degrees; ajar before
    for f in out:
        t = f['t']
        f['door'] = 9.0 + (96 - 9) * (smoothstep(6.2, 7.3, t) ** 0.8)
    person_track(out)
    camera_track(out)
    return out


def person_track(out):
    """the person: stands in the doorway (X=-0.28, Z=0), leans and reaches at the second call, then steps aside inside,
    toward the viewer, and sits on the floor beside the door (X=-1.05, Z=0.72); the hand goes out, low."""
    for f in out:
        t = f['t']; p = f['person']
        step = smoothstep(5.0, 6.1, t)
        X = -0.30 + (-1.25 + 0.30) * step
        Z = 0.0 + 0.40 * smoothstep(5.0, 5.9, t)
        sit = smoothstep(5.6, 6.6, t)
        lean = 0.0
        if 0.95 <= t < 2.35: lean = 0.35 * smoothstep(0.95, 1.2, t) * (1 - smoothstep(2.1, 2.35, t))
        lean = max(lean, 0.9 * p['reach'])
        reach = p['reach']
        low = smoothstep(6.8, 7.4, t)
        p.update(X=X, Z=Z, sit2=sit, lean=lean, reach2=reach, low2=low, walk=step)


def camera_track(out):
    """camera: wide while the dog keeps its distance; it comes closer only as the dog does (14.7-24)."""
    wide = dict(pos=np.array([1.30, 1.30, 7.3]), target=np.array([1.30, 0.62, 0.0]), fov=50.0)
    close = dict(pos=np.array([0.35, 1.38, 4.3]), target=np.array([-0.45, 0.42, 0.0]), fov=44.0)
    for f in out:
        t = f['t']
        s = smoothstep(15.2, 24.6, t)
        s = s * s * (3 - 2 * s)
        drift = 0.06 * smoothstep(8.6, 14.6, t)       # a slow lean-in during the long wait
        pos = wide['pos'] * (1 - s) + close['pos'] * s + np.array([0, -0.05, -0.5]) * drift * (1 - s)
        tgt = wide['target'] * (1 - s) + close['target'] * s
        fov = wide['fov'] * (1 - s) + close['fov'] * s - 3.0 * drift * (1 - s)
        f['camera'] = dict(pos=pos.tolist(), target=tgt.tolist(), fov=fov)


if __name__ == '__main__':
    os.makedirs(CACHE, exist_ok=True)
    out = build()
    json.dump(out, open(os.path.join(CACHE, 'rig.json'), 'w'))
    print('rig frames', len(out))
