"""Assemble film.mp4: 3 s title + the 32 s scene (768 frames, score-aligned) + 3 s end card, with sound.
Writes trace.json (measured from the rendered dog layer), the contact sheet used on the end card, and stills."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
from common import *
import render
from render import Scene, dog_plan, FACING, W, H, FPS, font, X, CH
from pieces import CORR

FILM = os.path.join(OUT, 'film.mp4')
PIC = os.path.join(CACHE, 'picture.mp4')


def title_card():
    im = Image.new('RGB', (W, H), (12, 12, 18))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 300), 'PAE-02 · SCION 30 · SAM 2', font=font('f8.woff2', 72), fill=(232, 222, 206), anchor='mm')
    d.text((W / 2, 372), 'Prompted Mask Proposal Swarm', font=font('f2.woff2', 40), fill=(200, 170, 120), anchor='mm')
    d.text((W / 2, 440), 'the threshold, assembled from accepted mask proposals of archive frames',
           font=font('f14.woff2', 20), fill=(150, 150, 160), anchor='mm')
    return im


def used_dog_frames():
    used = {}
    for i in range(768):
        p = dog_plan(i)
        if p['state'] == 'lie_down':
            for f, m, part in ((4, 1, 'body'), (19, 1, 'tail'), (40, 0, 'head'), (44, 0, 'head'), (47, 0, 'head')):
                used.setdefault((f, m), set()).add(part)
        else:
            used.setdefault((p['f'], p['m']), set()).add('whole')
    return used


def end_card(used, props):
    im = Image.new('RGB', (W, H), (12, 12, 18))
    d = ImageDraw.Draw(im)
    rows = {r['frame']: r for r in props['dog']['rows']}
    frames = sorted(set(f for f, m in used))
    tw, th = 112, 84
    cols = 10
    x0, y0 = 32, 64
    d.text((32, 22), 'what the dog is made of: accepted SAM 2 proposals, object dog#1, Amateur Film New Jersey C (public domain)',
           font=font('f14.woff2', 17), fill=(220, 210, 190))
    for k, f in enumerate(frames):
        fr = src_frame('dog', f).convert('RGB')
        a = raster(src_masks('dog')[str(f)], fr.size)
        arr = np.asarray(fr, np.float32) * (0.28 + 0.72 * a[..., None])
        t = Image.fromarray(arr.astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        x = x0 + (k % cols) * (tw + 10); y = y0 + (k // cols) * (th + 24)
        im.paste(t, (x, y))
        parts = sorted(set().union(*[used[(f, m)] for m in (0, 1) if (f, m) in used]))
        mir = 'm' if any(m for (ff, m) in used if ff == f) else ''
        d.text((x, y + th + 2), 'f%02d %s c%.2f %s' % (f, mir, rows[f]['conf'], ','.join(p[0] for p in parts)),
               font=font('f14.woff2', 12), fill=(170, 170, 180))
    yb = y0 + ((len(frames) + cols - 1) // cols) * (th + 24) + 8
    lines = [
        'c = confidence proxy (mask stability x edge agreement); m = proposal mirrored; w whole, b body, h head, t tail part',
        'rejected: f23, f49 (mask leaked into ground and shadow). Lying: no frame shows this dog lying, so its legs are not',
        'made: f04 sinks behind the porch board; lying, its body takes a tail (f19) and heads (f40, f44, f47) at the neck point.',
        'door leaf: Straight Talk f31 (door#5)   person: Straight Talk f02, our box+colour proposal, shown as a silhouette',
        'sitting person: Survival Stresses f36   hand: Door to Heaven (1941) f20, f30 + forearm stroke   all public domain',
        'porch, room, light and sky computed; voice synthesized (flite); sound synthesized. Nothing of the dog is drawn.',
    ]
    for k, ln in enumerate(lines):
        d.text((32, yb + k * 24), ln, font=font('f14.woff2', 15), fill=(200, 196, 186) if k else (150, 150, 160))
    return im


def small(alpha):
    return np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).resize((320, 180), Image.BOX)) > 127


def main():
    props = json.load(open(os.path.join(CACHE, 'proposals.json')))
    used = used_dog_frames()
    tc, ec = title_card(), end_card(used, props)
    ec.save(os.path.join(CACHE, 'end_card.jpg'), quality=92)
    sc = Scene()
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', PIC], stdin=subprocess.PIPE)
    def push(img, n=1):
        b = np.asarray(img.convert('RGB')).tobytes()
        for _ in range(n):
            ff.stdin.write(b)
    for k in range(72):   # title with a short fade out
        a = min(1, (72 - k) / 12.)
        push(Image.blend(Image.new('RGB', (W, H)), tc, a))
    frames = []; prev = None
    for i in range(768):
        img, plan, used_p, meas, alpha = sc.frame(i)
        if i < 6:
            img = Image.blend(Image.new('RGB', (W, H)), img, (i + 1) / 7.)
        push(img)
        sm = small(alpha)
        iou = float((sm & prev).sum() / max((sm | prev).sum(), 1)) if prev is not None else 1.0
        prev = sm
        fr = render.FR[i]['dog']
        facing = 1 if plan['state'] == 'lie_down' else FACING[(plan['f'], plan['m'])]
        frames.append(dict(i=i, t=round(i / FPS, 4), state=plan['state'], x_score=fr['x'], x_screen=meas['cx'], y_screen=meas['cy'],
                           facing=facing, posture=plan['posture'], proposals=used_p, bbox=[meas['x0'], meas['y0'], meas['x1'], meas['y1']],
                           area=meas['area'], iou_prev=round(iou, 3)))
        if i % 96 == 0:
            print('frame', i, flush=True)
    for k in range(72):
        a = min(1, (k + 1) / 10.)
        push(Image.blend(Image.new('RGB', (W, H)), ec, a))
    ff.stdin.close(); ff.wait()
    onsets = measure_onsets(frames)
    trace = dict(summary=dict(about='SCION 30 / SAM 2: per scene frame, what the dog did, measured from the rendered dog layer '
                                    '(x_screen, y_screen = alpha-weighted centroid in px; bbox; iou_prev = IoU of the dog silhouette '
                                    'with the previous frame at 320x180). state = the state the picture shows from its measured onset. '
                                    'facing: +1 toward the door (right), -1 away, 0 toward the camera.',
                              measured_onsets=onsets, mapping='x_screen ~ 985 - 205 * (x_score - 0.59) for the body centroid; fixed camera'),
                 frames=frames)
    jdump(trace, os.path.join(OUT, 'trace.json'))
    jdump(CORR, os.path.join(CACHE, 'corrections_runtime.json'))
    print(json.dumps(onsets, indent=1))


def measure_onsets(fr):
    """onsets measured from the render (not from the plan): the first frame of a visible change near each choice."""
    out = []
    cx = np.array([f['x_screen'] for f in fr]); y0 = np.array([f['bbox'][1] for f in fr]); iou = np.array([f['iou_prev'] for f in fr])
    v = np.diff(cx, prepend=cx[0])
    def first(cond, lo, hi):
        for i in range(max(1, lo), min(len(fr) - 7, hi)):
            if cond(i):
                return i
        return None
    names = ['retreat', 'watch', 'refuse', 'watch', 'approach', 'lie_down']
    def departs(i, win=24):
        """the silhouette changes more than any idle substitution in the second before (departure from the hold)"""
        base = iou[max(1, i - win):i]
        return len(base) > 0 and iou[i] < base.min() - .03
    def busy(i):
        return iou[i] < .97 and int((iou[i:i + 6] < .97).sum()) >= 3
    for c, nm in zip(CH, names):
        i0 = int(round(c * FPS)); lo, hi = i0 - 12, i0 + 13
        if nm == 'watch' and c < 3:
            k = first(lambda i: departs(i, 12), lo, hi); sig = 'leaves the backing gait: head comes up (IoU below the gait minimum of the half second before)'
        elif nm == 'lie_down':
            k = first(lambda i: all(y0[j + 1] >= y0[j] for j in range(i, i + 6)) and y0[i + 6] - y0[i] >= 6, lo, hi)
            sig = 'body top starts a sustained lowering (>= 6 px over 6 frames)'
        else:
            k = first(busy, lo, hi); sig = 'the silhouette starts changing every frame or two (>= 3 changes of IoU<0.97 in 6 frames), where the idle hold changes once in 7'
        out.append(dict(choice=nm, score_t=c, measured_t=None if k is None else round(k / FPS, 3),
                        dt=None if k is None else round(k / FPS - c, 3), signal=sig))
    # look in: head proposal changes to the level head (u40) after 26.0
    k = next((f['i'] for f in fr if f['t'] >= 26.0 and any(p.get('part') == 'head' and p.get('frame') == 40 for p in f['proposals'])), None)
    out.append(dict(choice='look in', score_t=26.4, measured_t=None if k is None else round(k / FPS, 3),
                    dt=None if k is None else round(k / FPS - 26.4, 3), signal='head proposal u47 (nose down) -> u40 (level, muzzle into the room)'))
    return out


if __name__ == '__main__':
    main()
