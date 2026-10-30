"""Cards, trace.json (states classified from the render's measurements), film.mp4, stills (taken from the film)."""
import os, json, glob, math, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import *

MEAS = os.path.join(CACHE, 'meas'); FRAMES = os.path.join(CACHE, 'frames'); FILM = os.path.join(CACHE, 'film')
SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
SERIF_B = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
SIL = SCORE['places']['sill']


def card(lines, path):
    im = Image.new('RGB', (W, H), (16, 15, 24))
    d = ImageDraw.Draw(im)
    y = 0
    blocks = []
    for txt, font, size, col in lines:
        f = ImageFont.truetype(font, size)
        bb = d.textbbox((0, 0), txt, font=f)
        blocks.append((txt, f, bb[3] - bb[1], col, bb[2] - bb[0]))
    total = sum(b[2] + 18 for b in blocks)
    y = (H - total) // 2
    for txt, f, h, col, w in blocks:
        d.text(((W - w) // 2, y), txt, font=f, fill=col)
        y += h + 18
    im.save(path, quality=92)


def classify():
    ms = [json.load(open(os.path.join(MEAS, f'{i:04d}.json'))) for i in range(N)]
    # the dog's position: the torso (flank) piece as laid, unprojected at the depth it was laid at
    xw = np.array([m['w_flank'][0] if m.get('w_flank') else m.get('x_world_measured', np.nan) for m in ms])
    # velocity of the measured position (central difference over 0.25 s)
    v = np.zeros(N)
    for i in range(N):
        a, b = max(0, i - 3), min(N - 1, i + 3)
        v[i] = (xw[b] - xw[a]) / ((b - a) / FPS)
    frames = []
    prev_face = 'door'
    prev_state = 'watch'
    for i, m in enumerate(ms):
        sad, sk, no = m.get('w_saddle'), m.get('w_skull'), m.get('w_nose')
        back_y = sad[1] if sad else None
        head_ab = (sk[1] - sad[1]) if (sk and sad) else None
        face = prev_face
        if sk and no:
            s = -(no[0] - sk[0]) + max(0.0, no[2] - sk[2]) * 0.8
            if s > 0.02:
                face = 'door'
            elif s < -0.02:
                face = 'away'
        prev_face = face
        if back_y is None:
            posture = None
        elif back_y < 0.32:
            posture = 'lying'
        elif back_y < 0.50:
            posture = 'low'
        else:
            posture = 'standing'
        near_sill = xw[i] < 1.3
        if back_y is not None and near_sill and back_y < 0.45 and abs(v[i]) < 0.1:
            state = 'lie_down'
        elif face == 'away':
            state = 'refuse'
        elif v[i] < -0.03:
            state = 'approach'
        elif v[i] > 0.06 and head_ab is not None and head_ab < 0.0:
            state = 'retreat'          # backing away from the door with the head below the back
        else:
            state = 'watch'
        prev_state = state
        f = FR[i]
        frames.append(dict(i=i, t=round(i / FPS, 4), state=state, state_score=f['dog']['state'], x_score=f['dog']['x'],
                           x_world_measured=round(float(xw[i]), 4), x_centroid_world=m.get('x_world_measured'), x_screen=m.get('x_screen'), y_screen=m.get('y_screen'),
                           facing=face, posture=posture, speed_measured=round(float(v[i]), 4),
                           back_height_m=round(back_y, 4) if back_y is not None else None,
                           head_above_back_m=round(head_ab, 4) if head_ab is not None else None,
                           head_heading_deg=m.get('hh'), body_heading_deg=m.get('hb'), z_root=m.get('z_root'),
                           head_world=m.get('w_skull'), nose_world=m.get('w_nose'), head_visible_share=m.get('head_visible_share'),
                           camera=m.get('cam'), focus_z=m.get('focus_z'), door_angle=m.get('door_angle'), dog_area_px=m.get('area_px'),
                           head_inside_door=bool(sk and sk[2] > 0.0 and abs(sk[0]) < 0.46)))
    # onsets: first frame of each new state run
    onsets = []
    for c in SCORE['choices']:
        hit = next((fr for fr in frames if fr['t'] >= c['t'] - 0.5 and fr['state'] == c['to']), None)
        onsets.append({'score_t': c['t'], 'to': c['to'], 'measured_t': hit['t'] if hit else None,
                       'dt': round(hit['t'] - c['t'], 3) if hit else None})
    def mh(fr):
        n, k = fr['nose_world'], fr['head_world']
        return math.degrees(math.atan2(n[2] - k[2], n[0] - k[0])) if n and k else None
    for fr in frames:
        fr['muzzle_heading_measured_deg'] = round(mh(fr), 1) if mh(fr) is not None else None
    look = next((fr for fr in frames if fr['t'] >= 25.0 and fr['muzzle_heading_measured_deg'] is not None and abs(fr['muzzle_heading_measured_deg'] - 90) < 22), None)
    onsets.append({'score_t': 26.4, 'to': 'looks in: muzzle heading (skull -> nose, laid pieces unprojected) within 22 deg of straight into the room (+Z)',
                   'measured_t': look['t'] if look else None, 'dt': round(look['t'] - 26.4, 3) if look else None})
    return frames, onsets


def main():
    frames, onsets = classify()
    about = ('SCION 44 Multiplane Parallax: what the dog did, measured per scene frame from the render. x_world_measured: the '
             'centroid of the dog pass (alpha of every dog piece after all nearer occluders: wall jamb, railing) unprojected '
             'at the dog root depth with the moving camera is kept as x_centroid_world; x_world_measured is the torso (flank) piece '
             'as laid, unprojected at its laid depth (less disturbed by the head and tail). facing: from the skull and nose pieces as laid, unprojected at their '
             'laid depths (door = muzzle toward the threshold or deeper into the house than the skull). posture: from the back '
             '(saddle piece) height in metres. state is classified from those measurements only (speed of x_world_measured, '
             'facing, back height, head above back, near the sill); state_score is the score state that drove the acting. '
             'x_score is the score x that placed the dog root.')
    json.dump({'about': about, 'onsets_measured': onsets, 'frames': frames}, open(os.path.join(FOLDER, 'trace.json'), 'w'))
    print(json.dumps(onsets, indent=0))
    # cards
    os.makedirs(FILM, exist_ok=True)
    for f in glob.glob(os.path.join(FILM, '*')):
        os.remove(f)
    card([('PAE-02 · SCION 44 · Multiplane Parallax', SERIF_B, 46, (236, 222, 200)),
          ('spatial collage swarm', SERIF, 26, (190, 180, 200)),
          ('a dog at a threshold, built as a stack of cut planes at measured depths', SANS, 20, (150, 145, 165))],
         os.path.join(CACHE, 'title.jpg'))
    card([('What it is made of', SERIF_B, 32, (236, 222, 200)),
          ('Fourteen collage planes at measured depths, from sky (140 m) to the porch railing (2.1 m in front of the wall).', SANS, 18, (205, 200, 215)),
          ('Found fragments (public domain unless noted), among them: clouds (Top Of The Cloud), trees keyed from Golden Gate windmill footage,', SANS, 18, (205, 200, 215)),
          ('the door, curtain and person cut from Straight Talk, the room wall from an Anthracite lantern shot, the bulb from', SANS, 18, (205, 200, 215)),
          ('Light Of Your Life, boards and railing from the logs of Billie, the Buffalo Baby; a Quick, Draw! moon (CC BY 4.0).', SANS, 18, (205, 200, 215)),
          ('The dog: 30 pieces cut from the dog of Amateur Film New Jersey C, each at its own depth, re-stacked as it turns.', SANS, 18, (205, 200, 215)),
          ('Drawn by code: the door casing, the window frame, the table, the person\'s cut-paper profile. All sound synthesized.', SANS, 18, (205, 200, 215)),
          ('The camera only translates through the stack; parallax, occlusion and focus give the depth.', SANS, 18, (205, 200, 215)),
          ('The dog\'s choices follow the PAELEO threshold score.', SANS, 18, (160, 155, 175))],
         os.path.join(CACHE, 'end.jpg'))
    k = 0
    for _ in range(3 * FPS):
        os.symlink(os.path.join(CACHE, 'title.jpg'), os.path.join(FILM, f'f{k:04d}.jpg')); k += 1
    for i in range(N):
        src = os.path.join(FRAMES, f's{i:04d}.jpg')
        assert os.path.exists(src), src
        os.symlink(src, os.path.join(FILM, f'f{k:04d}.jpg')); k += 1
    for _ in range(3 * FPS):
        os.symlink(os.path.join(CACHE, 'end.jpg'), os.path.join(FILM, f'f{k:04d}.jpg')); k += 1
    assert k == 912
    # audio: 3 s quiet + scene + 3 s tail
    wav = os.path.join(CACHE, 'film.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(CACHE, 'scene.wav'), '-af',
                    'afade=t=in:st=0:d=0.25,afade=t=out:st=31.4:d=0.6,adelay=3000|3000,apad=whole_dur=38', '-ar', '48000', wav], check=True)
    out = os.path.join(FOLDER, 'film.mp4')
    for crf in (24, 27, 30):
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(FILM, 'f%04d.jpg'), '-i', wav,
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                        '-t', '38', '-movflags', '+faststart', out], check=True)
        if os.path.getsize(out) <= 11.5e6:
            break
    print('film', os.path.getsize(out), 'crf', crf)
    # stills from the film itself
    os.makedirs(os.path.join(FOLDER, 'stills'), exist_ok=True)
    for t in (3.6, 9.0, 19.0, 28.0):
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{t + 3:.3f}', '-i', out, '-frames:v', '1', '-q:v', '2',
                        os.path.join(FOLDER, 'stills', f'still_{t:04.1f}s.jpg')], check=True)


if __name__ == '__main__':
    main()
