"""Exposure pass: read the score, derive the puppet channels, run the paw-contact solver.

Writes build/out/rig.json (per-frame puppet parameters + planted paws) and build/out/events.json
(paw touchdowns, door, voice) that the sound pass uses.  The acting rules added on top of the score:
  * the head leads every turn (head swings over the withers at the choice frame, body follows);
  * a turn of the flat puppet is foreshortening (sx = |turn|) and, near edge-on, a replacement
    end-on puppet: rear view when turning away (3.9-4.2 s), front view when turning back (8.1-8.2 s);
  * the door leaf swing is the Straight Talk door re-timed (mask widths, frames 31 -> 18 reversed).
"""
import json, math
import numpy as np
from theatre import *

def door_curve():
    m = json.load(open(os.path.join(KIT, 'archive-door', 'masks.json')))
    widths = {}
    for k in range(18, 32):
        best = 0
        for p in m[str(k)]:
            if len(p) < 3: continue
            xs = [q[0] for q in p]
            if min(xs) < 150: best = max(best, max(xs) - min(xs))
        widths[k] = best
    w = np.array([widths[k] for k in range(31, 17, -1)], float)      # closing, reversed = opening
    s = (w[0] - w) / (w[0] - w[-1])
    return s, widths

def run():
    sc = load_score(); fr = sc['frames']; n = len(fr)
    s_door, widths = door_curve()
    t_open = 6.2
    i_open = int(round(t_open * FPS))
    # acting channels
    turn = np.array([f['dog']['act']['turn'] for f in fr])
    t = np.array([f['t'] for f in fr])
    hb = np.zeros(n); hbmode = [''] * n
    i_ref = int(round(3.417 * FPS)); i_ret = int(round(7.458 * FPS))
    cross1 = next(i for i in range(i_ref, n) if turn[i] < 0)
    cross2 = next(i for i in range(i_ret, n) if turn[i] > 0)
    for i in range(n):
        if i_ref <= i < cross1: hb[i] = min(1, (i - i_ref) / 5.0); hbmode[i] = 'avert'
        if i_ret <= i < cross2: hb[i] = min(1, (i - i_ret) / 5.0)
    call = np.zeros(n); soft = np.zeros(n)
    c = s_ = 0
    for i, f in enumerate(fr):
        v = f['person']['voice']
        c += ((1.0 if v == 'call' else 0.0) - c) * 0.35
        s_ += ((1.0 if v == 'soft' else 0.0) - s_) * 0.2
        call[i] = c; soft[i] = s_
    # unwrap walk phase into a monotone gait clock
    phase = np.zeros(n); acc = 0; prev = None
    for i, f in enumerate(fr):
        wpz = f['dog']['act']['walk_phase']
        if prev is not None:
            dp = (wpz - prev) % (2 * math.pi)
            if dp > math.pi: dp -= 2 * math.pi
            acc += abs(dp)
        prev = wpz; phase[i] = acc
    dog = DogRig(); frames = []
    xs = np.array([f['dog']['x'] for f in fr])
    for i, f in enumerate(fr):
        a = f['dog']['act']; p = f['person']
        tr = turn[i]
        endon = None
        if abs(tr) < 0.4:
            endon = 'front'   # both turns pass through the front view (the head turned to us first)
        dirW = -1 if tr > 0 else 1
        sx = max(0.4, abs(tr))
        vx = xs[i] - xs[i - 1] if i else 0.0
        DP = dict(t=f['t'], x=f['dog']['x'], dirW=dirW, sx=sx, endon=endon, turn=tr,
                  crouch=a['crouch'], lie=a['lie'], ear=a['ear'], tail=a['tail'], wag=a['wag'],
                  head=a['head'], rest=a['rest'], look=a['look'], hb=float(hb[i]), hbmode=hbmode[i],
                  phase=float(phase[i]), moving=a['moving'], vx=float(vx))
        feet = dog.step(i, DP)
        # door leaf: hinged at the right jamb, ajar = 0.45 of the opening; opens on the archive curve
        if i < i_open: leaf = 0.45
        else:
            k = (i - i_open) / 2.0          # archive 12 fps -> scene 24 fps: each archive frame held twice
            s = np.interp(k, np.arange(len(s_door)), s_door)
            leaf = lerp(0.45, 0.10, s)
        PP = dict(t=f['t'], x=p['x'], sit=p['sit'], reach=p['reach'], low=p['low'], call=float(call[i]),
                  soft=float(soft[i]), mouth=p['mouth'], walking=bool(i and abs(p['x'] - fr[i - 1]['person']['x']) > 1e-4))
        frames.append(dict(i=i, t=f['t'], state=f['dog']['state'], dog=DP,
                           feet={k: list(v) for k, v in feet.items()}, person=PP, leaf=leaf,
                           voice=p['voice'], hand=p['hand'], door=f['door']))
    os.makedirs(OUT, exist_ok=True)
    json.dump(frames, open(os.path.join(OUT, 'rig.json'), 'w'))
    ev = dict(paws=dog.events, door_open_frame=i_open, door_widths_archive=widths,
              voice=[[f['t'], f['person']['voice']] for f in fr])
    json.dump(ev, open(os.path.join(OUT, 'events.json'), 'w'))
    print('frames', n, 'paw events', len(dog.events), 'hb cross', cross1, cross2)

if __name__ == '__main__':
    run()
