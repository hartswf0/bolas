"""Render the plate: title card (3 s), the 32 s scene aligned to the score frame for frame, the end card (3 s).
Writes raw RGB frames to ffmpeg (cache/video.mp4), measures the dog from its own render layer each scene frame
(trace.json), and logs the plate-substitution and footfall events for the sound (cache/events.json).
usage: python3 render.py [--frames a:b] [--stills] [--no-video]"""
import os, sys, json, math, subprocess, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
import dogpose as D
import person as PER
from world import W, H, S, XS, YG, WALL, LINTEL, PLATE, sx
from cutout import blit

SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
FR = SCORE['frames']
FPS = 24
N = len(FR)
assert N == 768
WD = np.load(os.path.join(HERE, 'cache', 'world.npz'))
FONT = os.path.join(HERE, 'cache', 'fonts')
def font(name, size): return ImageFont.truetype(os.path.join(FONT, name + '.ttf'), size)

PAPER = np.array([238, 229, 208], np.float32) / 255.
INKC = np.array([31, 25, 22], np.float32) / 255.
RED = (168, 38, 30)
rng = np.random.default_rng(3)
fib = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
fib = np.asarray(Image.fromarray(np.clip(fib * 40 + 128, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255. - 0.5
PAPER_FIELD = PAPER[None, None, :] * (1 + 0.035 * fib[..., None])
Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
VIGN = 1 - 0.07 * (((X - W / 2) / (W / 2)) ** 2 + ((Y - H / 2) / (H / 2)) ** 2)
PAPER_FIELD = PAPER_FIELD * VIGN[..., None]

def smooth(a, b, t):
    if t <= a: return 0.0
    if t >= b: return 1.0
    u = (t - a) / (b - a); return u * u * (3 - 2 * u)

def lerp(a, b, u): return a + (b - a) * u

# ---------------------------------------------------------------- the dog's plan, from the score
TURN_OUT = [26, 26, 28, 28, 30, 33, 36, 38, 40, 43, 44, 44]     # round 2: f016/f017 dropped (headless lumps)     # 3.417 → 3.917: the film's own turn, re-timed
TURN_BACK = [33, 30, 28, 26]                         # 8.04 → 8.62: back toward the door, re-timed
T_REFUSE = 3.417; T_BACK = 7.458; T_RISE_END = 8.04; T_TURNB = 8.04; T_TURNB_END = 8.62
TURN_FACING = {16: 1, 17: 1, 18: 1, 26: 0, 28: 0, 30: 0, 33: -1, 36: -1, 38: -1, 40: -1, 43: -1, 44: -1}

def dog_plan(i):
    """which drawing is on the stage at scene frame i, and its pose parameters."""
    t = i / FPS; d = FR[i]['dog']; a = d['act']
    p = dict(s=0.0, crouch=a['crouch'], lie=a['lie'], head=a['head'], rest=a['rest'], look=a['look'], tail=a['tail'],
             wag=a['wag'], wag_phase=t * 2 * math.pi * 2.6, moving=a['moving'],
             breath=math.sin(t * 2 * math.pi * 0.42), idle=math.sin(t * 2 * math.pi * 0.21) * (1 - a['moving']))
    if t >= 23.792:
        p['lie'] = max(a['lie'], smooth(23.792, 24.45, t))
        p['rest'] = max(a['rest'], smooth(25.2, 25.9, t) * (1 - smooth(26.4, 26.7, t)) * 0.9)
    if 26.72 <= t < 28.2:
        p['rear'] = 1
    if t < T_REFUSE:
        return ('puppet', 1, None, p)
    k = int((t - T_REFUSE) * FPS + 1e-6)
    if k < len(TURN_OUT):
        return ('turn', TURN_OUT[k], None, p)
    if t < T_BACK:
        p['head'] = min(a['head'], 0.3); p['tail'] = max(a['tail'], 1.0)
        return ('puppet', -1, None, p)
    if t < T_TURNB:
        # the head comes round to the door first, while the body still lies with its back turned; then it rises
        p['head'] = 0.9; p['rest'] = 0; p['look'] = 0
        p['hback_a'] = math.radians(8 * (1 - smooth(T_BACK, T_BACK + 0.25, t)))
        return ('puppet', -1, 1, p)
    k = int((t - T_TURNB) / (T_TURNB_END - T_TURNB) * len(TURN_BACK))
    if k < len(TURN_BACK):
        return ('turn', TURN_BACK[k], None, p)
    return ('puppet', 1, None, p)

# distance walked (local px) from the score's x: forward = toward the door
SCAN_PX_PER_M = 132.0
s_acc = [0.0]
for j in range(1, N):
    s_acc.append(s_acc[-1] - (FR[j]['dog']['x'] - FR[j - 1]['dog']['x']) * SCAN_PX_PER_M)

# ---------------------------------------------------------------- the person's plan
DOOR_FEET = 372.0; BENCH_FEET = 200.0
def blend_pose(a, b, u):
    out = {}
    for k in set(a) | set(b):
        va, vb = a.get(k, 0.0 if k != 'pelvis' else (0, 0)), b.get(k, 0.0 if k != 'pelvis' else (0, 0))
        out[k] = (lerp(va[0], vb[0], u), lerp(va[1], vb[1], u)) if isinstance(va, tuple) else lerp(va, vb, u)
    return out

def person_plan(t):
    P = PER.POSES
    if t < 4.6:
        x = DOOR_FEET + 40 * smooth(3.4, 3.9, t) - 40 * smooth(4.35, 4.6, t)
        pose = P['stand']
        pose = blend_pose(pose, P['call'], smooth(0.95, 1.25, t) * (1 - smooth(2.2, 2.5, t)))
        if t >= 3.3: pose = blend_pose(P['stand'], P['reach'], smooth(3.35, 3.75, t) * (1 - smooth(4.4, 4.7, t)))
        # a beckoning pulse while calling
        if 1.0 <= t < 2.3: pose['farm'] += 0.25 * math.sin((t - 1.0) * 2 * math.pi * 1.6)
        return x, pose
    if t < 5.2:
        u = smooth(4.6, 5.2, t)
        x = lerp(DOOR_FEET, BENCH_FEET, u)
        pose = dict(P['stand']); ph = (t - 4.6) * 2 * math.pi * 2.0
        # she steps back out of the doorway into the room, still facing the porch
        pose['thigh'] = 0.18 * math.sin(ph); pose['shin'] = -0.10 * math.sin(ph); pose['lean'] = -0.04
        pose['pelvis'] = (0, -3 * abs(math.sin(ph)))
        return x, pose
    x = BENCH_FEET
    pose = blend_pose(P['stand'], P['sit'], smooth(5.2, 5.6, t))
    pose = blend_pose(pose, P['low'], smooth(6.8, 7.3, t))
    # soft voice: the head bows a little more
    soft = max(smooth(7.35, 7.6, t) * (1 - smooth(9.3, 9.6, t)), smooth(10.35, 10.6, t) * (1 - smooth(11.5, 11.8, t)),
               smooth(26.35, 26.6, t) * (1 - smooth(27.3, 27.6, t)))
    pose['head'] += 0.12 * soft
    # 'come in': the low hand draws back toward her, making room
    pose = blend_pose(pose, P['sit'], smooth(26.3, 26.9, t))
    return x, pose

def door_angle(t):
    return math.radians(lerp(18, 84, smooth(6.2, 7.05, t)))

CAPTIONS = [  # (t0, t1, text, soft)
    (1.0, 2.3, 'Come here.', False), (3.4, 4.6, 'Come here.', False),
    (7.4, 9.4, "It's all right.", True), (10.4, 11.6, "It's all right.", True), (26.4, 27.4, 'Come in.', True)]

# ---------------------------------------------------------------- compositing
def compose(ink, washes, extra=None):
    base = PAPER_FIELD.copy()
    for field, color, amt in washes:
        if amt <= 0: continue
        c = np.array(color, np.float32)
        base = base * (1 - (field * amt)[..., None] * (1 - c[None, None, :]))
    img = base * (1 - ink[..., None]) + INKC[None, None, :] * ink[..., None]
    return Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8))

def door_layer(ink, cov, t):
    a = door_angle(t)
    leaf = D.plate('../plates/door_leaf') if False else None
    im = _door()
    w = max(2, int(round(0.9 * S * math.sin(a))))
    reg = im.resize((w, int(2.0 * S)), Image.BICUBIC)
    arr = np.asarray(reg, np.float32) / 255.
    x0 = int(round(WALL[0] - w)); y0 = int(round(YG - 2.0 * S))
    i_ = arr[..., 0] * (0.75 + 0.25 * math.sin(a)); c_ = arr[..., 3]
    # edge thickness of the leaf (its section) at the free edge
    ink[y0:y0 + reg.height, x0:x0 + w] = np.clip(ink[y0:y0 + reg.height, x0:x0 + w] * (1 - c_) + i_, 0, 1)
    ink[y0:y0 + reg.height, max(0, x0 - 3):x0 + 1] = 0.9
    return x0

_D = {}
def _door():
    if 'im' not in _D: _D['im'] = Image.open(os.path.join(HERE, 'cache', 'plates', 'door_leaf.png'))
    return _D['im']

def light_level(t):
    a = door_angle(t)
    return 0.10 + 0.90 * (1 - math.cos(a) - (1 - math.cos(math.radians(18)))) / (1 - math.cos(math.radians(84)) - (1 - math.cos(math.radians(18))))

def caption(dr, t, px, py):
    for t0, t1, text, soft in CAPTIONS:
        if t0 - 0.05 <= t < t1 + 0.35:
            al = smooth(t0 - 0.05, t0 + 0.12, t) * (1 - smooth(t1 + 0.1, t1 + 0.35, t))
            f = font('Literata-Italic', 20 if soft else 27)
            col = tuple(int(lerp(v_p, v_i, al * (0.72 if soft else 0.97))) for v_p, v_i in zip((214, 212, 210), (31, 25, 22)))
            tw = dr.textlength(text, font=f)
            if al > 0.02:
                bg = tuple(int(lerp(a_, b_, al)) for a_, b_ in zip((200, 196, 186), (240, 232, 212)))
                pad = 7
                hh = 30 if not soft else 24
                dr.rectangle([px - tw / 2 - pad, py - 2, px + tw / 2 + pad, py + hh], fill=bg, outline=tuple(int(lerp(200, 90, al)) for _ in range(3)))
            dr.text((px - tw / 2, py), text, font=f, fill=col)

def margin(dr, img, t, source, posture_text):
    f1 = font('JetBrainsMono-Regular', 11); f2 = font('Literata-Italic', 14)
    y = PLATE[3] + 8; x = PLATE[0] + 92
    dr.text((x, y), 'PL. I   THE THRESHOLD', font=font('JetBrainsMono-SemiBold', 11), fill=(60, 50, 44))
    dr.text((x + 160, y - 2), 'a motion study: nothing here happened; the sources are documented, the re-posed motion invented', font=f2, fill=(80, 66, 56))
    dr.text((x, y + 18), source[0].replace('engraved after ', 'after ').replace('Internet Archive; public domain), frame ', 'Internet Archive, public domain), f'), font=f1, fill=(70, 60, 52))
    dr.text((x, y + 34), source[1], font=f1, fill=(RED if 'invented' in source[1] else (70, 60, 52)))
    for k, rt in enumerate(['fig. 2 figure: drawn; hand after The Door to Heaven (1941) f000, PD',
                            'fig. 3 door: after Straight Talk f030 (NTIS 1992), PD',
                            'wall: fieldstone after fig. 1 film f000, PD']):
        dr.text((PLATE[2] - dr.textlength(rt, font=f1), y + 18 + 16 * k), rt, font=f1, fill=(70, 60, 52))

_thumbs = {}
def scan_thumb(frame):
    if frame not in _thumbs:
        im = Image.open(os.path.join(ROOT, '..', 'kit', 'archive-dog', 'frames', 'f%03d.jpg' % frame)).convert('L')
        im = im.resize((80, 60), Image.LANCZOS)
        a = np.asarray(im, np.float32) / 255.
        col = np.stack([a * 0.93 + 0.04, a * 0.9 + 0.04, a * 0.82 + 0.05], -1)  # printed as a toned collotype
        _thumbs[frame] = Image.fromarray(np.clip(col * 255, 0, 255).astype(np.uint8))
    return _thumbs[frame]

def measure(cov, hcov):
    m = cov > 0.5
    if not m.any(): return None
    ys, xs = np.nonzero(m)
    r = {'cx': float(xs.mean()), 'cy': float(ys.mean()), 'x0': int(xs.min()), 'x1': int(xs.max()), 'y0': int(ys.min()), 'y1': int(ys.max())}
    if hcov is not None and (hcov > 0.5).any():
        hy, hx = np.nonzero(hcov > 0.5); r['hx'] = float(hx.mean()); r['hy'] = float(hy.mean())
    return r

def title_card(i, kind):
    img = Image.fromarray(np.clip(PAPER_FIELD * 255, 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(img)
    pm = (150, 90, 1130, 630)
    dr.rectangle(pm, outline=(60, 50, 44), width=2)
    if kind == 'title':
        a = smooth(0, 10, i) * (1 - smooth(62, 72, i))
        c = lambda base: tuple(int(lerp(p_, b_, a)) for p_, b_ in zip((238, 229, 208), base))
        f = font('BigShoulders-800', 64)
        t1 = 'PAE-02 · SCION 50 · Library of Congress'
        dr.text((640 - dr.textlength(t1, font=f) / 2, 230), t1, font=f, fill=c((31, 25, 22)))
        f2 = font('Literata-Italic', 30)
        t2 = 'Historical Print Stage: The threshold, handmade'
        dr.text((640 - dr.textlength(t2, font=f2) / 2, 320), t2, font=f2, fill=c((60, 48, 40)))
        f3 = font('JetBrainsMono-Regular', 15)
        for k, t3 in enumerate(['An engraved motion study after public-domain film frames.',
                                'The sources are documented. The re-posed movement is invented (red pins);',
                                "the two turns are the film's own frames, re-timed."]):
            dr.text((640 - dr.textlength(t3, font=f3) / 2, 400 + 24 * k), t3, font=f3, fill=c((80, 66, 56)))
    else:
        a = smooth(0, 10, i) * (1 - smooth(64, 72, i))
        c = lambda base: tuple(int(lerp(p_, b_, a)) for p_, b_ in zip((238, 229, 208), base))
        f = font('Literata-Italic', 26)
        dr.text((200, 118), 'What this plate is made of', font=f, fill=c((31, 25, 22)))
        f3 = font('JetBrainsMono-Regular', 14)
        lines = [
            'fig. 1  the dog: line-engraved after 12 frames of Amateur Film New Jersey C (6, 16, 17, 26-44)',
            '        (Home Movies, Internet Archive, archive.org/details/NewJerseyC; public domain).',
            '        Frame 6 traced into 11 cut pieces and re-posed (invented motion, red pins);',
            '        the two turns are the film\'s own frames, re-timed. Eye, nostril, mouth: drawn.',
            '        No frame shows it lying down or the back of its head: both are invented.',
            'fig. 2  the figure: drawn; its hand after The Door to Heaven (1941), f000 (public domain;',
            '        the card it holds in the source is cropped away).',
            'fig. 3  the door: after Straight Talk f030 (NTIS 1992, archive.org, public domain).',
            '        Wall: fieldstone after the pillar in fig. 1\'s film, f000. Room, porch, sky: drawn.',
            'Sound: synthesized here (voice-like formant calls, paper, boards, room tone).',
            'No Library of Congress item was used; the LoC collections were not reachable.',
            'The events are fiction: the person, the call and the refusal never happened.',
        ]
        for k, ln in enumerate(lines):
            dr.text((200, 172 + 30 * k), ln, font=f3, fill=c((52, 44, 38)))
    return img

_pm = {}
def puppet_meas(i):
    """the cut-piece dog's own silhouette at frame i (drawn off stage): centroid x, height, lowest point relative to the ground"""
    if i not in _pm:
        kind, a, headf, p = dog_plan(i); assert kind == 'puppet'
        p['s'] = s_acc[i]
        di = np.zeros((H, W), np.float32); dc = np.zeros((H, W), np.float32)
        D.draw_puppet(di, dc, p, (XS + FR[i]['dog']['x'] * S, YG), a, headf=headf)
        ys, xs = np.nonzero(dc > 0.5)
        _pm[i] = (float(xs.mean()), float(ys.max() - ys.min()), float(ys.max() - YG))
    return _pm[i]

# ---------------------------------------------------------------- main
def render_scene_frame(i, events, prev):
    t = i / FPS; d = FR[i]['dog']
    LT = light_level(t)
    ink = WD['inkS'].copy()
    cov_dummy = np.zeros((H, W), np.float32)
    # door leaf (inside the room, behind the person)
    door_layer(ink, cov_dummy, t)
    # person
    pi_ = np.zeros((H, W), np.float32); pc = np.zeros((H, W), np.float32)
    px, ppose = person_plan(t)
    pinfo = PER.draw(pi_, pc, ppose, (px, YG))
    ink = ink * (1 - pc) + pi_
    # dog, on its own layer (measured before compositing)
    di = np.zeros((H, W), np.float32); dc = np.zeros((H, W), np.float32)
    hi_ = np.zeros((H, W), np.float32); hc = np.zeros((H, W), np.float32)
    kind, a, headf, p = dog_plan(i)
    O = (XS + d['x'] * S, YG)
    joints = []
    p['s'] = s_acc[i]
    if kind == 'puppet':
        sol, feet, joints = D.draw_puppet(di, dc, p, O, a, headf=headf, hc=(hi_, hc))
        src_frame = 6
        facing_m = None
    else:
        ib = i
        while dog_plan(ib)[0] != 'puppet': ib -= 1
        ia = i
        while dog_plan(ia)[0] != 'puppet': ia += 1
        mb, ma = puppet_meas(ib), puppet_meas(ia)
        u = (i - ib) / (ia - ib)
        D.draw_turn(di, dc, a, (lerp(mb[0], ma[0], u), YG + lerp(mb[2], ma[2], u) - 0.0), lerp(mb[1], ma[1], u))
        src_frame = a
        facing_m = TURN_FACING[a]
    ink = ink * (1 - dc) + di
    msr = measure(dc, hc if kind == 'puppet' else None)
    if kind == 'puppet':
        facing_m = 1 if msr['hx'] < msr['cx'] else -1
    # washes: dusk outside (deepening), the lamp in the room, light out of the open door
    dusk = 0.78 + 0.22 * smooth(0, 32, t)
    washes = [(WD['wash_dusk'], (0.62, 0.70, 0.86), dusk),
              (WD['wash_room'], (1.0, 0.80, 0.52), 0.55 + 0.25 * LT),
              (WD['spill'], (1.0, 0.82, 0.50), 0.85 * LT)]
    img = compose(ink, washes)
    dr = ImageDraw.Draw(img)
    # red brads where the drawing is re-posed (invented motion); none on the documented turn frames
    if kind == 'puppet':
        for (q, ang, n) in joints:
            r = 2.2
            dr.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=RED)
    # speech, printed as a legend near the speaker
    if t < 4.7: cx_, cy_ = pinfo['head'][0] + 95, pinfo['head'][1] - 44
    else: cx_, cy_ = 230, 196
    caption(dr, t, cx_, cy_)
    # margin: the scan crop in use and its status
    th = scan_thumb(src_frame)
    img.paste(th, (PLATE[0], PLATE[3] + 8))
    dr.rectangle([PLATE[0], PLATE[3] + 8, PLATE[0] + 79, PLATE[3] + 67], outline=(60, 50, 44))
    if kind == 'puppet':
        st = ('fig. 1 dog: engraved after Amateur Film New Jersey C (Home Movies, Internet Archive; public domain), frame %03d' % src_frame,
              'state of the drawing: frame 006 cut into 11 pieces and re-posed%s: invented motion' % (' (reversed impression)' if a == -1 else ''))
    else:
        st = ('fig. 1 dog: engraved after Amateur Film New Jersey C (Home Movies, Internet Archive; public domain), frame %03d' % src_frame,
              "state of the drawing: frame %03d as photographed, outline from its mask; the film's own turn, re-timed" % src_frame)
    margin(dr, img, t, st, '')
    # events for the sound and the ledger
    if prev is not None and (prev['kind'], prev['a']) != (kind, a): events.append({'t': t, 'type': 'paper', 'from': prev['kind'], 'to': kind})
    if kind == 'puppet' and headf is not None and (prev is None or prev.get('headf') is None): events.append({'t': t, 'type': 'paper', 'what': 'head round'})
    if kind == 'puppet' and prev is not None and bool(p.get('rear')) != bool(prev.get('rear')): events.append({'t': t, 'type': 'paper', 'what': 'head rear' if p.get('rear') else 'head profile'})
    if kind == 'puppet' and prev is not None and prev.get('feet') is not None and p['lie'] < 0.2:
        for leg, fp in feet.items():
            # a footfall: the foot was lifted last frame and is on its ground now
            u = (p['s'] / D.STRIDE + D.GAIT[leg]) % 1.0
            pu = (prev['s'] / D.STRIDE + D.GAIT[leg]) % 1.0
            if abs(p['s'] - prev['s']) > 0.05 and ((pu >= D.DUTY and u < D.DUTY and p['s'] > prev['s']) or (pu < D.DUTY and u >= D.DUTY and p['s'] < prev['s'])):
                events.append({'t': t, 'type': 'step', 'leg': leg, 'v': abs(p['s'] - prev['s'])})
    rec = {'kind': kind, 'a': a, 'headf': headf, 'rear': bool(p.get('rear')), 's': p['s'], 'feet': feet if kind == 'puppet' else None,
           'msr': msr, 'facing_m': facing_m, 'joints': [(j[0], j[2]) for j in joints], 'src': src_frame}
    return img, rec

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--frames', default=None); ap.add_argument('--stills', action='store_true')
    ap.add_argument('--no-video', action='store_true'); ap.add_argument('--out', default=os.path.join(HERE, 'cache', 'video.mp4'))
    args = ap.parse_args()
    if args.frames:
        a, b = map(int, args.frames.split(':'))
        events = []; prev = None
        os.makedirs(os.path.join(HERE, 'cache', 'probe'), exist_ok=True)
        for i in range(a, b):
            img, prev = render_scene_frame(i, events, prev)
            img.save(os.path.join(HERE, 'cache', 'probe', 'p%03d.png' % i))
        return
    ff = None
    if not args.no_video:
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS),
                               '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-tune', 'grain', '-pix_fmt', 'yuv420p', args.out],
                              stdin=subprocess.PIPE)
    for i in range(72):
        if ff: ff.stdin.write(title_card(i, 'title').tobytes())
    events = []; prev = None; recs = []
    for i in range(N):
        img, prev = render_scene_frame(i, events, prev)
        recs.append(prev)
        if ff: ff.stdin.write(img.tobytes())
        t = i / FPS
        if args.stills:
            for ts in (3.6, 9.0, 19.0, 28.0):
                if i == int(round(ts * FPS)):
                    os.makedirs(os.path.join(ROOT, 'stills'), exist_ok=True)
                    img.save(os.path.join(ROOT, 'stills', 'still_%04.1fs.jpg' % ts), quality=92)
        if i % 96 == 0: print('frame', i, flush=True)
    for i in range(72):
        if ff: ff.stdin.write(title_card(i, 'end').tobytes())
    if ff: ff.stdin.close(); ff.wait()
    json.dump(events, open(os.path.join(HERE, 'cache', 'events.json'), 'w'))
    json.dump([{k: v for k, v in r.items() if k != 'feet'} | {'feet': {kk: list(vv) for kk, vv in (r['feet'] or {}).items()}} for r in recs],
              open(os.path.join(HERE, 'cache', 'measure.json'), 'w'))
    print('rendered', N, 'scene frames')

if __name__ == '__main__':
    main()
