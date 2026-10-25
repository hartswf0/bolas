"""Cards, trace, stills, film. Run after render.py and sound.py.
  - title card (3 s) and end card (3 s), painted in the film's dusk
  - trace.json: what the dog did, measured from the render's passes (torso and head ID passes, silhouette)
  - stills/ at 3.6, 9, 19, 28 s; film.mp4 (H.264 + AAC, faststart)
"""
import json, math, os, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import *

FONTS = os.path.join(REPO, 'tools/paeleo/fonts')
SEQ = os.path.join(CACHE, 'seq')
MEAS = os.path.join(CACHE, 'measure')


def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def card_bg():
    yy = np.linspace(0, 1, H)[:, None, None]
    top, low = np.array([24, 28, 52.]), np.array([70, 70, 96.])
    bg = top * (1 - yy) + low * yy
    bg = bg * np.ones((1, W, 1))
    r = np.random.default_rng(4)
    n = np.asarray(Image.fromarray((r.random((90, 160)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    bg = bg * (0.92 + 0.16 * n[..., None])
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))


def title_card():
    im = card_bg()
    d = ImageDraw.Draw(im)
    f1 = font('f8.woff2', 64, 800)
    f2 = font('f34.woff2', 30)
    f3 = font('f27.woff2', 24)
    s = 'PAE-02 · SCION 05 · Yuri Norstein'
    w = d.textlength(s, font=f1)
    d.text(((W - w) / 2, 270), s, font=f1, fill=(226, 220, 204))
    s2 = 'The threshold, handmade'
    w2 = d.textlength(s2, font=f2)
    d.text(((W - w2) / 2, 362), s2, font=f2, fill=(200, 190, 176))
    s3 = 'atmospheric multiplane cinema: glass planes, fog, focus, a cutout dog'
    w3 = d.textlength(s3, font=f3)
    d.text(((W - w3) / 2, 420), s3, font=f3, fill=(160, 156, 170))
    return im


END_LINES = [
    'What it is made of',
    '',
    'The dog: flat cutout pieces re-cut every frame from a small maquette of ellipsoids and limbs,',
    'proportioned from the archive dog of Amateur Film New Jersey C (Home Movies, Internet Archive, public domain),',
    'its coat grain cut from that film. Feet planted by a solver; choices and times from the PAELEO score.',
    'The fog: keyed from time-lapse cloud footage, Top Of The Cloud (archive.org CEP391, public domain).',
    'The bowl in the room: cut from the same home movie.',
    'House, porch, person, door, trees, light: painted in code on glass planes at measured depths.',
    'Sound: synthesized here, voice included (formant synthesis); no recordings.',
]


def end_card():
    im = card_bg()
    d = ImageDraw.Draw(im)
    f1 = font('f8.woff2', 46, 800)
    f2 = font('f34.woff2', 21)
    y = 170
    for k, s in enumerate(END_LINES):
        f = f1 if k == 0 else f2
        w = d.textlength(s, font=f)
        d.text(((W - w) / 2, y), s, font=f, fill=(226, 220, 204) if k == 0 else (196, 190, 180))
        y += 62 if k == 0 else 34
    return im


def fade(im, u):
    a = np.asarray(im, np.float32) * u
    return Image.fromarray(a.astype(np.uint8))


# ------------------------------------------------------------------------------------------------ the trace
def trace():
    M = [json.load(open(os.path.join(MEAS, '%04d.json' % i))) for i in range(N)]
    xw = np.array([m['x_world'] for m in M])
    k = np.ones(7) / 7
    xs = np.convolve(np.pad(xw, 3, 'edge'), k, 'valid')
    v = np.gradient(xs) * FPS
    # reference standing silhouette height (watching, 0-0.9 s)
    h_stand = float(np.median([m['sil_h'] for m in M[:20]]))
    frames = []
    for i, m in enumerate(M):
        fr = FR[i]
        facing = 'door' if m['head_cx'] < m['torso_cx'] else 'away'
        head_rel = (m['torso_top'] - m['head_top']) / max(1, m['sil_h'])  # >0: head above the back line
        lying = m['sil_h'] < 0.66 * h_stand
        if lying:
            posture = 'lying'
        elif abs(v[i]) > 0.08:
            posture = 'walking' if head_rel > -0.05 else 'walking, head low'
        else:
            posture = 'standing' if head_rel > 0.05 else 'standing, head low'
        # the state as measured: what a viewer could see the dog do
        if lying and m['x_world'] < 0.75:
            st = 'lie_down'
        elif facing == 'away':
            st = 'refuse'
        elif v[i] > 0.12 and head_rel < 0.12:
            st = 'retreat'
        elif v[i] < -0.12:
            st = 'approach'
        else:
            st = 'watch'
        frames.append(dict(i=i, t=round(i / FPS, 4), state=st, state_score=fr['dog']['state'], x_score=round(float(xw[i]), 4),
                           x_world_measured=round(float(xw[i]), 4), x_screen=m['torso_cx'], y_screen=m['torso_cy'], facing=facing,
                           posture=posture, speed=round(float(v[i]), 3), head_above_back=round(float(head_rel), 3),
                           head_screen=[m['head_cx'], m['head_cy']], inside_frame_share=m['inside_frame'], tail_end_x=m['right_x'] if facing == 'door' else m['left_x'],
                           camera=m['cam'], focus_z=m['focus_z'], atmosphere=m['atmosphere'], lum_dog=m.get('lum_dog'), lum_around=m.get('lum_around')))
    # hysteresis: a state must hold 3 frames to count (a measurement, not a performance, has jitter)
    for i in range(1, N - 2):
        if frames[i]['state'] != frames[i - 1]['state'] and not (frames[i]['state'] == frames[i + 1]['state'] == frames[i + 2]['state']):
            frames[i]['state'] = frames[i - 1]['state']
    out = dict(about='SCION 05 Norstein: what the dog did, measured per scene frame from the render (torso and head ID passes, '
                     'silhouette). x_score = x_world_measured: the torso pass centroid unprojected at the dog glass depth (metres, '
                     'same axis as the score). state is classified from measurements (facing from head vs torso centroid, speed, '
                     'silhouette height); state_score is the score state that drove the acting.',
               h_stand_px=h_stand, frames=frames)
    json.dump(out, open(os.path.join(FOLDER, 'trace.json'), 'w'))
    # report transitions
    tr = [(f['t'], frames[k - 1]['state'], f['state']) for k, f in enumerate(frames) if k and f['state'] != frames[k - 1]['state']]
    print('measured transitions:', tr)
    return frames


def main():
    if os.path.exists(SEQ):
        shutil.rmtree(SEQ)
    os.makedirs(SEQ)
    tc, ec = title_card(), end_card()
    for k in range(72):
        u = min(1, k / 12, (71 - k) / 12)
        fade(tc, max(0, u)).save(os.path.join(SEQ, 'f%04d.jpg' % k), quality=92)
    for i in range(N):
        src = os.path.join(CACHE, 'frames', 's%04d.jpg' % i)
        os.symlink(src, os.path.join(SEQ, 'f%04d.jpg' % (72 + i)))
    for k in range(72):
        u = min(1, k / 12, (71 - k) / 16)
        fade(ec, max(0, u)).save(os.path.join(SEQ, 'f%04d.jpg' % (72 + N + k)), quality=92)
    frames = trace()
    st = os.path.join(FOLDER, 'stills')
    os.makedirs(st, exist_ok=True)
    for t in (3.6, 9.0, 19.0, 28.0):
        Image.open(os.path.join(CACHE, 'frames', 's%04d.jpg' % int(round(t * FPS)))).save(os.path.join(st, 'still_%04.1fs.jpg' % t), quality=92)
    out = os.path.join(FOLDER, 'film.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(SEQ, 'f%04d.jpg'), '-i', os.path.join(CACHE, 'sound.wav'),
           '-c:v', 'libx264', '-preset', 'slow', '-crf', os.environ.get('CRF', '25'), '-maxrate', '2300k', '-bufsize', '4600k',
           '-pix_fmt', 'yuv420p', '-tune', 'grain', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', '-shortest', out]
    subprocess.run(cmd, check=True)
    print('film', os.path.getsize(out) / 1e6, 'MB')


if __name__ == '__main__':
    main()
