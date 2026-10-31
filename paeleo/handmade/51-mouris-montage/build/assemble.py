"""SCION 51 · title and end cards, the 38 s soundtrack, the encode, the stills and proof sheets.
film = 3 s title + 32 s scene (768 frames) + 3 s end card = 912 frames at 24 fps."""
import json, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import OUT, REPO, FPS, W, H

C = os.path.join(OUT, 'build/cache'); FR = os.path.join(C, 'frames')
FONTS = os.path.join(REPO, 'tools/paeleo/fonts')


def font(f, s):
    fo = ImageFont.truetype(os.path.join(FONTS, f), s)
    ax = {'f8.woff2': [800], 'f34.woff2': [18, 420], 'f14.woff2': None}.get(f)
    if ax:
        fo.set_variation_by_axes(ax)
    return fo


def card(lines, path):
    im = Image.new('RGB', (W, H), (16, 15, 20)); d = ImageDraw.Draw(im)
    y = 0
    blocks = []
    for txt, f, s, col in lines:
        fo = font(f, s); bb = d.textbbox((0, 0), txt, font=fo); blocks.append((txt, fo, bb, col)); y += (bb[3] - bb[1]) + s * 0.55
    y = (H - y) / 2
    for txt, fo, bb, col in blocks:
        d.text((90, y - bb[1]), txt, font=fo, fill=col); y += (bb[3] - bb[1]) + fo.size * 0.55
    im.save(path, quality=95)


def cards():
    cs = json.load(open(os.path.join(OUT, 'cutting-score.json')))
    ncut = cs['n_cuts']
    card([('PAE-02 · SCION 51 · Academy Mouris Collection — Montage Research', 'f8.woff2', 44, (236, 226, 206)),
          ('the threshold, by whole-image substitution on a measured cutting score', 'f34.woff2', 28, (200, 190, 172)),
          ('the Mouris collection itself was not viewed: these are independently licensed public-domain images', 'f14.woff2', 18, (150, 146, 140))],
         os.path.join(C, 'title.jpg'))
    # name only what the viewer can see: the dog's images held >= 6 frames somewhere
    seen = {}
    for c in cs['cuts']:
        for key in ('dog_body', 'dog_head_legs'):
            if c['hold'] >= 6:
                seen[c[key].split('.')[1].replace('-', ' ')] = 1
    nl = sorted(seen); half = (len(nl) + 1) // 2
    names1, names2 = ', '.join(nl[:half]) + ',', ', '.join(nl[half:]) + '.'
    card([('What it is made of', 'f8.woff2', 40, (236, 226, 206)),
          ('The dog: cut-outs from whole public-domain archive images, re-cut and substituted', 'f34.woff2', 21, (214, 204, 186)),
          (f'{ncut} times on a cutting score (2-frame cuts on the calls, holds of 12 to 46 frames on the soft voice and the light).', 'f34.woff2', 21, (214, 204, 186)),
          ('Its pieces are cut from: ' + names1, 'f34.woff2', 21, (214, 204, 186)),
          (names2, 'f34.woff2', 21, (214, 204, 186)),
          ('An invisible 3D pose of spheres decides where each piece is cut; its shading is not shown.', 'f34.woff2', 21, (214, 204, 186)),
          ('The wall, door and lit room take images from the same archive. Letters are cut from those images.', 'f34.woff2', 21, (214, 204, 186)),
          ('The person is cut the same way (a jacket, a suit, a head and hands from the same archive). Floor and house are', 'f34.woff2', 21, (214, 204, 186)),
          ('ray-cast planes made here; voices and sound are synthesized. No Mouris footage was used.', 'f34.woff2', 21, (214, 204, 186)),
          ('Sources: Internet Archive / Moving Image Archive public-domain films (see assets.json).', 'f14.woff2', 17, (150, 146, 140))],
         os.path.join(C, 'end.jpg'))


def audio():
    with wave.open(os.path.join(C, 'scene.wav')) as f:
        sr = f.getframerate(); x = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32)
    x = x[:32 * sr]
    if len(x) < 32 * sr:
        x = np.pad(x, (0, 32 * sr - len(x)))
    pad = np.zeros(3 * sr, np.float32)
    y = np.concatenate([pad, x, pad]).astype(np.int16)
    with wave.open(os.path.join(C, 'film.wav'), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(y.tobytes())


def encode(crf=27):
    n = len([f for f in os.listdir(FR) if f.startswith('s')])
    assert n == 768, n
    out = os.path.join(OUT, 'film.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error',
           '-loop', '1', '-framerate', str(FPS), '-t', '3', '-i', os.path.join(C, 'title.jpg'),
           '-framerate', str(FPS), '-i', os.path.join(FR, 's%03d.jpg'),
           '-loop', '1', '-framerate', str(FPS), '-t', '3', '-i', os.path.join(C, 'end.jpg'),
           '-i', os.path.join(C, 'film.wav'),
           '-filter_complex', '[0:v]format=yuv420p,setsar=1[a];[1:v]format=yuv420p,setsar=1[b];[2:v]format=yuv420p,setsar=1[c];[a][b][c]concat=n=3:v=1:a=0[v]',
           '-map', '[v]', '-map', '3:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-maxrate', '2300k', '-bufsize', '4600k',
           '-pix_fmt', 'yuv420p', '-r', str(FPS), '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-t', '38', out]
    subprocess.run(cmd, check=True)
    return out


def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                        'stream=nb_read_frames,codec_name,width,height', '-show_entries', 'format=duration,size', '-of', 'json', path],
                       capture_output=True, text=True)
    return json.loads(r.stdout)


def stills():
    """stills from the ENCODED film (scene t + 3 s title)"""
    os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
    for t in ('03.6', '09.0', '19.0', '28.0'):
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(float(t) + 3.0 + 0.5 / FPS), '-i', os.path.join(OUT, 'film.mp4'),
                        '-frames:v', '1', '-q:v', '3', os.path.join(OUT, 'stills', f'still_{t}s.jpg')], check=True)


if __name__ == '__main__':
    import sys
    cards(); audio()
    if 'encode' in sys.argv:
        p = encode(int(os.environ.get('CRF', '21'))); print(json.dumps(probe(p))); stills()
