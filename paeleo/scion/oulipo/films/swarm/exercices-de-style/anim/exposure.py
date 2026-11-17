"""Writes anim/exposure.json: frame-indexed exposure sheets, 24 fps, puppets on twos (keys on even frames).
Timing comes from incident/anthology.json (repair 2: S5c = 51.5-61.75 s).  Units: frame px, degrees."""
import sys, json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import es_lib as L

FPS = 24
A = json.load(open(HERE.parent / 'incident' / 'anthology.json'))
sched = {s['shot']: s for s in A['schedule']}
V = L.Visitor()
rnd = lambda v, n=2: round(float(v), n)

def walk_extras(st, walking):
    ph = st['phase']
    if not walking:
        return dict(lean=0.0, head=0.0, arm=0.0, hem=0.0)
    return dict(lean=-2.0, arm=rnd(7.0 * math.sin(2 * math.pi * ph)),                          # arm counter-swings the near leg
                hem=rnd(2.6 * math.sin(2 * math.pi * 2 * (ph - 0.07))),                           # #41: hem lags ~3 frames
                head=rnd(1.2 * math.sin(2 * math.pi * 2 * ph + 0.6)))

def vis_frame(st, extra, dy=0.0):
    return dict(hip=[rnd(st['hip'][0]), rnd(st['hip'][1] + dy)], sc=round(st['sc'], 5),
                near=[rnd(st['legs']['near'][0]), st['legs']['near'][1]], far=[rnd(st['legs']['far'][0]), st['legs']['far'][1]], **extra)

out = dict(fps=FPS, on='twos (puppet keys on even frames; hold each drawing 2 frames)', units='960x540 frame px, degrees (+ turns a piece\'s down toward -x)',
           rig=str(L.PM / 'cut' / 'rig_walker.json'), lib='anim/es_lib.py', anthology_rev=A['rev'])

# ===================================================================== S5c TEST SHOT
t0, t1 = sched['S5c']['t0'], sched['S5c']['t1']
dur = round(t1 - t0, 3); N = int(round(dur * FPS))
sc0 = 230.0 / V.height
K_CONTACT = 30                                                     # local frame 30 = film 52.75 s (still from 53.167, before 54.0)
REST = (420.0, 357.0)                                              # bow-bottom contact on the bench top
SET = L.settle(10, 6.0, 4, 3.0)
key = {}
for k in range(0, K_CONTACT + len(SET) + 1):
    if k < K_CONTACT:
        f = k / K_CONTACT
        drop = 300 * (1 - f) ** 1.6                                 # lowered, slowing into the wood
        key[str(k)] = dict(x=rnd(REST[0] + 26 * (1 - f)), y=rnd(REST[1] - drop), a=rnd(-6.0 - 4 * (1 - f)))
    else:
        a, dy = SET[min(k - K_CONTACT, len(SET) - 1)]
        key[str(k)] = dict(x=REST[0], y=rnd(REST[1] + dy), a=rnd(-a))
hand = {}
REL = K_CONTACT + 2                                                # releases 2 frames after the touch
for k in range(0, 64):
    if k <= REL:
        hand[str(k)] = dict(visible=True, lift=0.0, rot=0.0, dx=0.0)
    else:
        u = min(1.0, (k - REL) / 22.0); e = u * u * (3 - 2 * u)
        hand[str(k)] = dict(visible=e < 0.999, lift=rnd(560 * e), rot=rnd(-6 * e), dx=rnd(60 * e))
WALK0 = 2.5                                                        # repair 1: he is THERE from frame 0 (no rise from the bench)
HAND_GONE = next(int(k) for k in sorted(hand, key=int) if not hand[k]['visible'])   # the close-up arm has folded back into him
wk = L.Walk(600.0, 350.0, sc0, WALK0, step=0.40, amp=26.0, leg=V.leg, dur=dur + 0.2, recede=0.97, bob=6.0)
vis = {}
for k in range(0, N + 2, 2):
    st = wk.at(k)
    fr = vis_frame(st, walk_extras(st, k / FPS >= WALK0))
    fr['own_arm'] = k >= HAND_GONE                                 # while the close-up arm is out, his own arm piece is not drawn
    vis[str(k)] = fr
# repair 1: the figure's whole bounding-box height (head to lowest foot) must never grow, frame to frame. The leg
# pendulum lengthens the figure by up to 4 px as the stance leg passes vertical, so each drawing's scale is trimmed
# (<= 2 %) until its height is <= the previous drawing's; the scale itself stays non-increasing.
from PIL import Image as _I
import numpy as _np
def _bbox_h(fr, sc):
    lay = _I.new('RGBA', (1400, 540), (0, 0, 0, 0))
    pose = dict(lean=fr['lean'], head=fr['head'], arm=fr['arm'], hem=fr['hem'], own_arm=True,
                legs={'near': tuple(fr['near']), 'far': tuple(fr['far'])})
    V.draw(lay, (fr['hip'][0] + 300, fr['hip'][1]), sc, pose, shadow=False)
    a = _np.asarray(lay.getchannel('A')) > 40; ys = _np.where(a.any(1))[0]
    return int(ys[-1] - ys[0] + 1) if len(ys) else 0
h_prev, sc_prev, bbox_h = None, None, {}
for k in range(0, N + 2, 2):
    fr = vis[str(k)]
    if fr['hip'][0] < -200:
        break
    sc = fr['sc'] if sc_prev is None else min(fr['sc'], sc_prev)
    h = _bbox_h(fr, sc)
    while h_prev is not None and h > h_prev:
        sc *= 0.997; h = _bbox_h(fr, sc)
    fr['sc'] = round(sc, 5); bbox_h[str(k)] = h; h_prev, sc_prev = h, sc
contacts = [round(c, 3) for c in wk.contacts if c <= dur]
exit_k = next((k for k in range(0, N + 2, 2) if vis[str(k)]['hip'][0] < -70), None)
heights = [vis[str(k)]['sc'] for k in range(0, N + 2, 2)]
bh = [bbox_h[k] for k in sorted(bbox_h, key=int)]
out['S5c'] = dict(
    film_t0=t0, film_t1=t1, duration=dur, frames=N, bench_top=352, key_length=380.0,
    door_xy=[804, 36], captions=dict(x=440, y=48, lead=34, source='anthology key.5-key.8 (14 chars/s, word reveal, held)'),
    camera=dict(drift_px=40, t0=2.0, t1=dur, planes={'bench': 1.0, 'key': 1.0, 'hand': 1.0, 'visitor': 0.55, 'door': 0.55,
                'ghost': 0.25, 'print (title, captions, strip, band)': 0.0}, note='#44: near moves more than far; door moves by whole pixels only'),
    key_contact_frame=K_CONTACT, key_settle=dict(frames=[K_CONTACT, K_CONTACT + 10], angle_deg='6 -> 0, one overshoot', bounce='3 px, peak on settle frame 4',
                                                 still_from_frame=K_CONTACT + 10, still_from_film_t=round(t0 + (K_CONTACT + 10) / FPS, 3)),
    key=key, key_last=max(int(k) for k in key),
    arm=dict(piece='arm (his own right sleeve + hand, Rol 57642)', scale=1.7, angle=24.0,
             fingertip_src=[1414.0, 1492.0]),
    hand=hand, hand_last=max(int(k) for k in hand),
    visitor=vis, visitor_last=max(int(k) for k in vis),
    walk=dict(start_s=WALK0, step_s=0.40, swing_deg=26, recession='x0.97 per step', bob_px=6, substitution='leg_straight in stance / leg_bent in swing',
              steps_in_shot=round(wk.at(N)['steps'], 2), exit_frame=exit_k, exit_film_t=round(t0 + exit_k / FPS, 3) if exit_k else None,
              height_monotonic_nonincreasing=all(a >= b for a, b in zip(heights, heights[1:])),
              bbox_height_px=bbox_h, bbox_height_nonincreasing=all(a >= b for a, b in zip(bh, bh[1:]))),
    contacts=contacts,
    step_grain_onsets=[8.59, 9.76, 10.38, 13.8, 15.29, 15.98, 4.47, 0.67, 1.13],
    pair_frame=dict(local_t=2.5, film_t=round(t0 + 2.5, 3), baseline_film_t=11.0, note='bar 54.0 s = S5c start 51.5 + 2.5 s, as written (repair 2: no re-anchor)'),
    hand_retract=dict(frames=[REL, HAND_GONE], rule='shoulder, scale and angle tween from the close-up arm to his own arm pin; swaps to his own arm piece on frame HAND_GONE, clipped behind the bench lip'),
)

# ===================================================================== S1 BASELINE (eye level, 3.0-13.0)
b = A['variants']['baseline']
beats = [c for c in b['claims'] if c['id'] != 'baseline.7']
s1 = dict(film_t0=3.0, film_t1=13.0, bench=dict(x=300, y=330, w=300), door_xy=[800, 100], visitor_scale=round(200.0 / V.height, 5),
          ground=340, beats=[], frames={})
sc1 = 200.0 / V.height
wk_in = L.Walk(700.0, 340.0, sc1, 3.0, step=0.40, amp=22.0, leg=V.leg, dur=13.2, recede=1.0, bob=6.0)
STOP = 500.0
poses = {'E1': dict(lean=0, head=0, arm=0, hem=0), 'E2': dict(lean=-1, head=-9, arm=0, hem=0.5),
         'E3': dict(lean=4, head=4, arm=-38, hem=0), 'E4': dict(lean=0, head=-3, arm=-62, hem=0),
         'E5': dict(lean=12, head=6, arm=-24, hem=1.0), 'E6': dict(lean=-2, head=0, arm=0, hem=0)}
for c in beats:
    s1['beats'].append(dict(event=c['events'][0], caption=c['text'], t_in=c['t_in'], frame_in=int(round(c['t_in'] * FPS)),
                            hold_s=1.6, pose=poses[c['events'][0]],
                            note={'E5': 'placed, no settle (baseline: the key is just put down)'}.get(c['events'][0], '')))
stop_k = None; out_start = 11.2
for k in range(72, 312 + 2, 2):
    t = k / FPS
    st = wk_in.at(k)
    if stop_k is None and st['hip'][0] <= STOP and st['legs']['near'][1] == 'stance' and abs(st['legs']['near'][0]) < 4:
        stop_k = k
    if stop_k is None:
        s1['frames'][str(k)] = vis_frame(st, walk_extras(st, True)); continue
    if t < out_start:
        ev = max((bb for bb in s1['beats'] if bb['t_in'] <= t), key=lambda bb: bb['t_in'], default=s1['beats'][0])
        tgt = poses[ev['event']]; since = t - ev['t_in']; e = min(1.0, since / 0.33)     # 8-frame move into each pose, then hold
        prevp = poses['E%d' % max(1, int(ev['event'][1]) - 1)]
        ex = {kk: rnd(prevp[kk] + (tgt[kk] - prevp[kk]) * (e * e * (3 - 2 * e))) for kk in tgt}
        hold = dict(hip=s1['frames'][str(stop_k - 2)]['hip'] if str(stop_k - 2) in s1['frames'] else [rnd(STOP), rnd(st['hip'][1])],
                    sc=round(sc1, 5), near=[0.0, 'stance'], far=[0.0, 'stance'], **ex)
        s1['frames'][str(k)] = hold
    else:
        if 'wk_out' not in locals():
            hx = s1['frames'][str(k - 2)]['hip'][0]
            wk_out = L.Walk(hx, 340.0, sc1, out_start, step=0.40, amp=22.0, leg=V.leg, dur=13.2, recede=1.0)
        st2 = wk_out.at(k); s1['frames'][str(k)] = vis_frame(st2, walk_extras(st2, True))
s1['walk_in_contacts'] = [round(c, 3) for c in wk_in.contacts if c < (stop_k or 0) / FPS]
s1['walk_out_contacts'] = [round(c, 3) for c in wk_out.contacts if c <= 13.0]
s1['key_on_bench'] = dict(from_film_t=9.6 + 0.33, x=360, y=322, angle=0.0, note='no settle in the baseline')
out['S1'] = s1

# ===================================================================== S3 SHADOW (Reiniger, 12 fps, behind the frosted pane)
sense = A['variants']['sense']
bell_t = next(c['t_in'] for c in sense['claims'] if c['id'] == 'sense.2') - 0.1    # bell onset 26.4 (timing E2 t_in)
bell_k = int(round(bell_t * FPS))
s3 = dict(film_t0=24.0, film_t1=36.0, pane=dict(x=300, y=96, w=360, h=250), silhouette_scale=round(280.0 / V.height, 5),
          bell_onset_frame=bell_k, rule='head-up starts on the bell frame: 3 frames up (-14 deg), then a 6-frame overshoot (+4 -> 0)',
          frames={})
sc3 = 280.0 / V.height                                             # repair 1: closer to the glass, the head reads
def rise3(k):
    d = k - bell_k                                                     # the whole body starts: hip up 7 px with the head
    if 0 <= d < 3: return rnd(-12.0 * (d + 1) / 3)
    if 3 <= d < 9: return rnd(-12.0 - 5.0 * math.sin(math.pi * (d - 3) / 6))
    if 9 <= d < 15: return rnd(-12.0 * (1 - (d - 9) / 6))
    return 0.0
def head3(k, t, base):
    d = k - bell_k
    if 0 <= d < 3: return rnd(-26.0 * (d + 1) / 3)                                   # 3 frames up (repair 1: -26 deg)
    if 3 <= d < 9: return rnd(-26.0 - 8.0 * math.sin(math.pi * (d - 3) / 6))            # 6-frame overshoot
    if d >= 9 and t < 27.6: return -26.0
    if 27.6 <= t < 27.95: return rnd(-26.0 * (1 - (t - 27.6) / 0.35))
    return base
wk3 = L.Walk(700.0, 400.0, sc3, 24.0, step=0.42, amp=20.0, leg=V.leg, dur=36.2, recede=1.0)
stop3 = None
for k in range(int(24.0 * FPS), int(36.0 * FPS) + 2, 2):
    t = k / FPS
    st = wk3.at(k)
    walking_in = st['hip'][0] > 455 and t < 26.1
    if walking_in:
        fr = vis_frame(st, walk_extras(st, True))
    else:
        if stop3 is None:
            stop3 = s3['frames'][str(k - 2)]['hip']
        fr = dict(hip=list(stop3), sc=round(sc3, 5), near=[0.0, 'stance'], far=[0.0, 'stance'], lean=0.0, head=0.0, arm=0.0, hem=0.0)
        if t >= 32.0:                                                  # E6: he walks back, away from the pane
            st2 = L.Walk(stop3[0], 400.0, sc3, 32.0, step=0.42, amp=20.0, leg=V.leg, dur=36.2, recede=0.96).at(k)
            fr = vis_frame(st2, walk_extras(st2, True))
        if 25.6 <= t < 28.2: fr['arm'] = rnd(-55.0 * min(1.0, (t - 25.6) / 0.5))   # repair 1: holds the envelope out, clear of the coat
        if 25.6 <= t < 29.6: fr['envelope'] = 'whole' if t < 28.2 else 'torn'
        if 28.2 <= t < 29.6: fr['arm'] = -55.0; fr['lean'] = 3.0         # E3 tear: the card loses its top strip
        elif 29.6 <= t < 30.8: fr['arm'] = -58.0                          # E4: a glint (no key shape ever)
        elif 30.8 <= t < 32.0: fr['lean'] = 14.0; fr['arm'] = -20.0       # E5: stoops at the bench
    fr['head'] = head3(k, t, fr.get('head', 0.0))
    fr['blur_px'] = rnd(5.0 + 4.0 * max(0.0, min(1.0, (t - 32.0) / 3.0)))                # 5 -> 9 px as he steps back
    fr['glint'] = rnd(max(0.0, 1 - abs(t - 30.0) / 0.25)) if 29.75 <= t <= 30.25 else 0.0
    s3['frames'][str(k)] = fr
s3['bell_head_on_ones'] = {str(k): head3(k, k / FPS, 0.0) for k in range(bell_k - 2, bell_k + 14)}
s3['bell_rise_on_ones'] = {str(k): rise3(k) for k in range(bell_k - 2, bell_k + 16)}
s3['envelope_card'] = dict(size_src=[150, 100], note='flat black card on the hand pin (Reiniger): whole 25.6-28.2, torn 28.2-29.6')
out['S3'] = s3

# ===================================================================== S4 KEY DROP ON THE NOTICE
s4 = dict(film_t0=36.0, film_t1=46.0, card_xy=[150, 60], key_length=190.0, drop_start_t=42.45, drop_px=40, clip='drawn paper clip at the card top-left',
          stamp=dict(t=44.0, frame=int(44.0 * FPS), squash_frames=[1.0, 0.5, 0.0], xy=[598, 393], size=24, angle=-4, note='repair 1: below the table, straddling the card edge; no field cell covered'), frames={})
k0 = int(round(42.45 * FPS)); st4 = L.settle(10, 6.0, 4, 3.0)
for i in range(0, 8):
    u = (i + 1) / 8
    s4['frames'][str(k0 + i)] = dict(dy=rnd(-40 * (1 - u * u)), a=-6.0)
for i, (a, dy) in enumerate(st4):
    s4['frames'][str(k0 + 8 + i)] = dict(dy=rnd(dy), a=rnd(-a))
s4['clink_frame'] = k0 + 8
out['S4'] = s4

# ===================================================================== S5b tear (straight-ahead)
out['S5b'] = dict(film_t0=sched['S5b']['t0'], film_t1=sched['S5b']['t1'], tear=dict(cls='es_lib.Tear', n_frames=28, recut_every=2, y=200, seed=101,
                  start_t=sched['S5b']['t0'] + 0.1), hand='arm piece reaches in 0.1 s after the tear completes; the envelope slides away over the last 0.45 s of S5b')


# ===================================================================== evidence (foraged), handmade, absences
SRCD = str(L.SRC)
out['evidence'] = dict(see='forage/evidence.json', note='repair 1: provenance has ONE record, forage/evidence.json (rewritten from what the film opens); this sheet no longer keeps its own copy',
                       ids=['rol57642', 'key_rex', 'station', 'bell', 'room_tone', 'steps', 'thud'])
out['handmade'] = [
 dict(what='butter page #fddb8c, top-centre lift to #fee498/#ffefb2, fibre mottle', where='es_lib.page()'),
 dict(what='ghost words in #fdefb1 (L* 94.2 > page 88.7)', where='es_lib.ghost()'),
 dict(what='mixed-face title setter, per-letter face/size x0.75-1.25/baseline +-8, red #d6280a / black #191304 by word', where='es_lib.set_title()'),
 dict(what='warm grey band #8e847b 108 px, mottle, white Instrument Sans 40/15', where='es_lib.band()'),
 dict(what='six-cell strip, 64 px cells (thicker than plan 44 px per user review), red ring', where='es_lib.strip()'),
 dict(what='cut-paper bench (low lip and eye-level), #283716/#2f4a20 + cream, scissor jitter, fibre, dark cut edge', where='es_lib.bench_low(), bench_eye()'),
 dict(what='THE service door, one RGBA asset, pasted at whole-pixel offsets only', where=str(L.MEDIA / 'door.png') + '; es_lib.door(), paste_door(), door_hash()'),
 dict(what='deckled station-vignette frame', where='es_lib.deckle()'), dict(what='GUICHET 3 window (stencil read backwards) + procedural frosted pane + shadow_through_glass', where='es_lib.guichet(), frosted_pane(), shadow_through_glass()'),
 dict(what='notice grid (empty boxes always drawn) + red rubber stamp with squash', where='es_lib.notice(), stamp()'),
 dict(what='envelope interior (lamp through paper) + straight-ahead torn edge re-cut every 2 frames', where='es_lib.envelope_interior(), Tear'),
 dict(what='Visitor FK puppet with drawing substitution (stance/swing legs from the print), Walk sim (planted feet), Reiniger silhouette from the same matte', where='es_lib.Visitor, Walk, Visitor.silhouette_pieces()'),
 dict(what='kit synth brass ticks at landing (declared)', where='test_shot_s5c.sound(): kit Mix.click'),
]
out['absences'] = [
 'No PD/CC full-figure walking man in a BOWLER found in the time box: Commons search ("Agence Rol sortant chapeau melon", "homme marchant rue", "portrait en pied pardessus") and LoC Bain "walking" (50 results, contact sheet viewed) gave frontal walkers in groups; Rol 57642 (wide-brim felt hat) was the one clean single full figure with real legs.',
 'Rol 57642 is frontal/three-quarter, not profile: mirrored, he walks to frame left as a flat cutout (Gilliam/Reiniger convention); his face stays toward camera.',
 'Commons original (3058x4184) download was refused with HTTP 429 repeatedly; the 1920 px thumbnail was used.',
 'No openly licensed metal-key-on-wood clink foraged; kit synth tick layered on the PD thud (declared).',
]
out['notes'] = [
 'S5c is rendered at the anthology timing_revision length 10.083 s (56.167-66.25), not 6.5 s: the review asked for 14 chars/s typing with holds and a real exit, which do not fit 6.5 s.',
 'Layout: captions x=440 so no caption crosses the door; door at 804,52; key rests at bow-bottom 420,357; strip of six 64 px cells at left on the band.',
 'INV-DOOR: door interior (rows above the bench lip and its lift shadow) has 1 distinct hash over 21 sampled frames (measurements.json).',
]

json.dump(out, open(HERE / 'exposure.json', 'w'), indent=1, ensure_ascii=False)
s = out['S5c']
print('S5c', s['duration'], 'frames', s['frames'], 'contacts', len(s['contacts']), 'steps', s['walk']['steps_in_shot'], 'exit', s['walk']['exit_frame'], s['walk']['exit_film_t'], 'mono', s['walk']['height_monotonic_nonincreasing'])
print('S1 stop', stop_k, 'S3 bell', bell_k)
