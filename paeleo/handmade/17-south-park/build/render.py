"""SCION 17 // render v1: performance -> frames (piped to ffmpeg), trace.json measured from the render, stills, proofs.

python3 render.py [--frames a:b] [--proof t1,t2,...]   (no args: the whole film, video only, to build/cache/video.mp4)
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import kit, dog, person, stage, direct, dialogue
from paint import paint

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
FONTS = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'paeleo', 'fonts')
SS = stage.SS; W, H = stage.W, stage.H
TITLE_N, END_N = 72, 72


def font(file, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, file), size)
    if weight:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f


def world_M(cam, x, mirror_unused=False):
    """figure cm (origin at world x, y=0) -> canvas px at SS"""
    C = stage.cam_matrix(cam)
    F = np.array([[0.01, 0, x], [0, 0.01, 0], [0, 0, 1.0]])
    return C @ F


BG = {}


def background(cam):
    if cam not in BG:
        im = Image.new('RGB', (W * SS, H * SS), (30, 30, 60))
        pcs = sorted(stage.static_pieces(cam), key=lambda p: p.z)
        paint(im, [p for p in pcs if p.z < 30], stage.cam_matrix(cam), edge=2 * SS)
        fg = [p for p in pcs if p.z >= 30]
        BG[cam] = (im, fg)
    return BG[cam]


MASKS = {}
GRAIN = stage.paper_grain()


def gaze_vec(src, dst, flip):
    dx, dy = dst[0] - src[0], dst[1] - src[1]
    if flip: dx = -dx
    n = math.hypot(dx, dy * 1.4) or 1.0
    return (dx / n, max(-1, min(1, dy * 1.4 / n)))


def dog_targets(fr, pinfo):
    px = fr['person']['x']
    hx, hy = pinfo['head']; nx, ny = pinfo['hand_n']
    return {'person': (px + hx / 100.0, hy / 100.0), 'hand': (px + nx / 100.0, ny / 100.0), 'doorway': (0.0, 1.05), 'door': (0.0, 1.0),
            'floor_away': (fr['dog']['x'] + 1.2, -0.2), 'away': (fr['dog']['x'] + 2.5, 0.3)}


def compose(fr, measure=True):
    cam = fr['cam']; t = fr['t']
    bg, fg = background(cam)
    im = bg.copy(); d = ImageDraw.Draw(im)
    light = stage.DOOR_STATES[fr['door']]['light']
    C = stage.cam_matrix(cam)
    paint(im, sorted(stage.door_pieces(fr['door'], light), key=lambda p: p.z), C, edge=2 * SS, draw=d)
    # person
    pp = dict(fr['person']['pose'])
    ppcs, pinfo = person.build(pp)
    hx, hy = pinfo['head']
    dg = fr['dog']; dpose = dict(dg['pose'])
    dog_head = (dg['x'] + (0.3 if dpose.get('mirror') else -0.3), 0.75 if dpose['draw'] == 'STAND' else 0.42)
    pp['gaze'] = gaze_vec((fr['person']['x'] + hx / 100.0, hy / 100.0), dog_head, False)
    ppcs, pinfo = person.build(pp)
    paint(im, ppcs, world_M(cam, fr['person']['x']), edge=2 * SS, draw=d)
    # dog
    tg = dog_targets(fr, pinfo)
    flip = bool(dpose.get('mirror')) != bool(dpose.get('head_mirror'))
    dpose['gaze'] = gaze_vec(dog_head, tg[dg['gaze_target']], flip)
    dpcs = dog.build(dpose)
    MD = world_M(cam, dg['x']) @ np.diag([1.0, 1.0, 1.0])
    paint(im, dpcs, MD, edge=2 * SS, draw=d)
    # porch floor strip in front of the figures' line
    paint(im, fg, C, edge=2 * SS, draw=d)
    # caption: the spoken words, near the speaker; size and type carry the register (call / soft)
    cap = fr['caption']
    if cap:
        draw_caption(im, d, cap, cam, fr['person']['x'] + hx / 100.0, hy / 100.0)
    small = im.reduce(SS)
    a = np.asarray(small, np.float32)
    key = (cam, fr['door'])
    if key not in MASKS: MASKS[key] = stage.light_mask(cam, light)
    m = MASKS[key][..., None] * 0.62
    dusk = np.array([0.93, 0.93, 1.0], np.float32); warm = np.array([1.32, 1.12, 0.84], np.float32)
    a = a * (dusk + (warm - dusk) * m) * GRAIN
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    meas = measure_dog(dpcs, cam, dg['x']) if measure else None
    return out, meas


CAPF = {}


def draw_caption(im, d, cap, cam, hx, hy):
    s = stage.CAMERAS[cam]['s'] / 170.0
    if cap['reg'] == 'call':
        f = CAPF.setdefault(('call', cam), font('f8.woff2', int(46 * SS * min(s, 1.4)), 900)); text = cap['text'].upper()
        fill, paper, rot = (30, 22, 34), (250, 246, 230), -3
    else:
        f = CAPF.setdefault(('soft', cam), font('f27.woff2', int(26 * SS * min(s, 1.4)))); text = cap['text']
        fill, paper, rot = (70, 60, 80), (236, 230, 214), 0
    sx, sy = stage.world_to_px(cam, hx, hy)
    sx, sy = sx * SS + 40 * SS * min(s, 1.4), sy * SS - 110 * SS * min(s, 1.4)
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad = 12 * SS
    slip = Image.new('RGBA', (tw + 2 * pad, th + 2 * pad + 6 * SS), (0, 0, 0, 0))
    sd = ImageDraw.Draw(slip)
    pts = kit.handcut([(0, 0), (tw + 2 * pad, 0), (tw + 2 * pad, th + 2 * pad), (0, th + 2 * pad)], 'slip' + text, 3)
    sd.polygon([tuple(p) for p in pts], fill=paper + (255,), outline=(27, 22, 34, 255), width=2 * SS)
    sd.text((pad - bb[0], pad - bb[1]), text, font=f, fill=fill)
    if rot: slip = slip.rotate(rot, expand=True, resample=Image.BICUBIC)
    x = int(min(max(sx, 20 * SS), W * SS - slip.width - 20 * SS)); y = int(max(sy, 16 * SS))
    im.paste(slip, (x, y), slip)


def measure_dog(dpcs, cam, x):
    """measured from the render: the dog's painted silhouette (1x mask) and its drawn nose/skull pieces"""
    M = world_M(cam, x)
    M1 = M.copy(); M1[:2] /= SS
    m = Image.new('L', (W, H), 0); md = ImageDraw.Draw(m)
    nose = skull = body = None
    for p in dpcs:
        q = p.pts @ M1[:2, :2].T + M1[:2, 2]
        md.polygon([tuple(v) for v in q.tolist()], fill=255)
        if p.tag == 'nose' and nose is None: nose = q.mean(0)
        if p.tag == 'skull' and skull is None: skull = q.mean(0)
        if p.tag == 'body' and body is None: body = q.mean(0)
    A = np.asarray(m) > 0
    ys, xs = np.nonzero(A)
    cx, cy = float(xs.mean()), float(ys.mean())
    if nose is not None and skull is not None:
        dx = nose[0] - skull[0]
        facing = 1 if dx < -2 else -1 if dx > 2 else 0
    else:
        facing = None
    return dict(cx=cx, cy=cy, bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], facing=facing,
                body_x=float(body[0]) if body is not None else None, area=int(A.sum()))


# ---------------------------------------------------------------- cards
def card(lines, seed, icon=None, foot=None):
    im = Image.new('RGB', (W * SS, H * SS), (34, 36, 72))
    d = ImageDraw.Draw(im)
    g = np.random.default_rng(seed)
    for k, c in enumerate([(46, 46, 90), (70, 58, 108), (112, 76, 118)]):
        y0 = (H * SS) * (0.62 + 0.12 * k)
        pts = [(0, y0)] + [(x, y0 + g.uniform(-8, 8) * SS) for x in range(0, W * SS + 80, 80 * SS)] + [(W * SS, H * SS), (0, H * SS)]
        d.polygon(pts, fill=c)
    y = 150 * SS
    for text, f, col in lines:
        bb = d.textbbox((0, 0), text, font=f)
        d.text(((W * SS - (bb[2] - bb[0])) / 2 - bb[0], y), text, font=f, fill=col)
        y += (bb[3] - bb[1]) + 26 * SS
    if icon:
        paint(im, icon[0], icon[1], edge=2 * SS)
    out = im.reduce(SS)
    a = np.asarray(out, np.float32) * GRAIN
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def title_card():
    big = font('f8.woff2', 64 * SS, 900); mid = font('f5.woff2', 34 * SS, 700); sm = font('f27.woff2', 24 * SS)
    feet = {'frontn': (-23, 0.5), 'frontf': (-20, 0.5), 'hindn': (24, 0.5), 'hindf': (21, 0.5)}
    icon = dog.build(dict(body='F', head_view='F', gaze=(0, 0), tail=40))
    M = np.array([[2.2 * SS, 0, 640 * SS], [0, -2.2 * SS, 660 * SS], [0, 0, 1]])
    return card([('PAE-02 · SCION 17 · South Park', big, (250, 244, 228)),
                 ('repeatable graphic grammar', mid, (236, 200, 140)),
                 ('the threshold, handmade', sm, (210, 204, 220))], 3, icon=(icon, M))


def end_card():
    mid = font('f5.woff2', 34 * SS, 800); sm = font('f34.woff2', 21 * SS); it = font('f27.woff2', 19 * SS)
    L = [('Made of construction-paper shapes cut in code', mid, (250, 244, 228)),
         ('A dog in five head and three body direction states, a lying drawing and an expression atlas;', sm, (226, 222, 232)),
         ('a person with a ten-shape mouth atlas driven by one phoneme chart, which also drives her synthesized voice.', sm, (226, 222, 232)),
         ('Moved by substitution on twos, pivots, and planted feet solved to the PAELEO score. All sound synthesized.', sm, (226, 222, 232)),
         ('Moon, trees and fence cut from Quick, Draw! doodles: Google Creative Lab and contributors, CC BY 4.0 (key_ids in assets.json).', it, (236, 200, 140)),
         ('No footage and no model-generated images.', it, (236, 200, 140))]
    return card(L, 5)


def main():
    args = sys.argv[1:]
    frames, events = direct.perform()
    if '--proof' in args:
        ts = [float(v) for v in args[args.index('--proof') + 1].split(',')]
        os.makedirs(os.path.join(ROOT, 'build', 'cache', 'proof'), exist_ok=True)
        for tt in ts:
            i = int(round(tt * 24)); im, m = compose(frames[i])
            p = os.path.join(ROOT, 'build', 'cache', 'proof', 'f_%05.2f.png' % tt); im.save(p); print(p, m)
        return
    if '--cards' in args:
        title_card().save(os.path.join(ROOT, 'build', 'cache', 'title.png')); end_card().save(os.path.join(ROOT, 'build', 'cache', 'end.png')); return
    out = os.path.join(ROOT, 'build', 'cache', 'video.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', '24',
                           '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    tc = title_card(); ec = end_card()
    for k in range(TITLE_N): ff.stdin.write(tc.tobytes())
    trace = []
    stills = {86: 'still_03.6s.jpg', 216: 'still_09.0s.jpg', 456: 'still_19.0s.jpg', 672: 'still_28.0s.jpg'}
    os.makedirs(os.path.join(ROOT, 'stills'), exist_ok=True)
    for fr in frames:
        im, m = compose(fr)
        ff.stdin.write(im.tobytes())
        if fr['i'] in stills: im.save(os.path.join(ROOT, 'stills', stills[fr['i']]), quality=90)
        dg = fr['dog']; cam = fr['cam']
        trace.append(dict(i=fr['i'], t=fr['t'], state=dg['state'], x_score=dg['x'],
                          x_screen=round(m['cx'], 2), y_screen=round(m['cy'], 2),
                          x_world_measured=round(stage.px_to_world_x(cam, m['cx']), 4),
                          x_anchor_measured=round(stage.px_to_world_x(cam, m['body_x']), 4) if m['body_x'] is not None else None,
                          facing=m['facing'] if dg['look'] != 'in' else 1, look=dg['look'], posture=dg['posture'],
                          drawing='%s%s/%s%s' % (dg['pose']['draw'] if dg['pose']['draw'] == 'LIE' else dg['pose']['body'], '_R' if dg['pose'].get('mirror') else '',
                                                 dg['pose'].get('head_view', 'P'), '_back' if dg['pose'].get('head_mirror') else ''),
                          cam=cam, bbox=m['bbox']))
        if fr['i'] % 96 == 0: print('frame', fr['i'], flush=True)
    for k in range(END_N): ff.stdin.write(ec.tobytes())
    ff.stdin.close(); ff.wait()
    json.dump(dict(about='SCION 17 trace: what Biscuit did, per scene frame, measured from the render. x_screen/y_screen: centroid of the '
                         'dog\'s painted silhouette (1x px). x_world_measured: that centroid back through the frame\'s camera (metres; the film '
                         'cuts from WIDE to CLOSE at frame %d). x_anchor_measured: centre of the painted body piece, in metres. x_score: the score x '
                         'the dog was staged at. facing: 1 = head toward the door (screen left), -1 = away, 0 = toward camera, from the painted nose '
                         'relative to the painted skull; while look = in the back of the head is up (no nose painted) and facing is recorded as 1.' % direct.CUT_CLOSE,
                   frames=trace), open(os.path.join(ROOT, 'trace.json'), 'w'), indent=0)
    json.dump(events, open(os.path.join(ROOT, 'build', 'cache', 'events.json'), 'w'))
    print('done', out)


if __name__ == '__main__':
    main()
