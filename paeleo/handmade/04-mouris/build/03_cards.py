"""SCION-04 · the title card and the closing card (what it is made of), each 3 s, letters filled by the torrent."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torrent as TR

HERE = os.path.dirname(os.path.abspath(__file__)); W, H = 1280, 720
FONTS = os.path.abspath(os.path.join(HERE, '../../../../tools/paeleo/fonts'))
lib = TR.Library(); rng = np.random.default_rng(40)

def font(f, size, wght):
    F = ImageFont.truetype(os.path.join(FONTS, f), size)
    try: F.set_variation_by_axes([wght])
    except Exception: pass
    return F

def text_mask(lines):
    im = Image.new('L', (W * 2, H * 2), 0); d = ImageDraw.Draw(im)
    for (txt, F, x, y) in lines:
        F2 = F.font_variant(size=F.size * 2)
        try: F2.set_variation_by_axes([F._wght])
        except Exception: pass
        if x == 'c': x = (W - d.textlength(txt, font=F2) / 2) / 2
        d.text((x * 2, y * 2), txt, font=F2, fill=255)
    return np.asarray(im.reduce(2), np.float32) / 255.

def plain(canvas, lines, col=(0.93, 0.89, 0.80)):
    m = text_mask(lines)[..., None]
    canvas[:] = canvas * (1 - m) + np.array(col, np.float32) * m

def bg_layer(pool):
    return TR.Layer('bg', pool, kind=1, maxlevel=0, contrast=0.5)

def card(path, frames_fn, n=72):
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '24', '-i', '-',
                           '-c:v', 'libx264', '-crf', '15', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    counts = []
    for i in range(n):
        img, c = frames_fn(i); counts.append(c)
        ff.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    return counts

def main():
    big = font('f8.woff2', 96, 900); big._wght = 900
    mono = font('f20.woff2', 22, 600); mono._wght = 600
    mono_s = font('f14.woff2', 19, 400); mono_s._wght = 400
    lit = font('f27.woff2', 34, 500); lit._wght = 500
    # ---------------- title
    title_mask = text_mask([('PAE-02 · SCION 04', big, 'c', 200), ('FRANK MOURIS', big, 'c', 318)])
    L_t = TR.Layer('title', 'every', kind=0, maxlevel=2, contrast=0.9, split_std=1)
    L_b = bg_layer('sky')
    def title(i):
        cv = np.zeros((H, W, 3), np.float32)
        r = 0.02 + 0.9 * max(0, 1 - i / 40)   # a flood that settles into letters
        a = TR.render_layer(lib, L_b, np.ones((H, W), np.float32), np.full((H, W, 3), (0.10, 0.09, 0.16), np.float32), 0, 0, r * 0.3, rng, i, cv, None, 2, bbox=(0, 0, W, H))
        TR.outline(cv, title_mask, 7, alpha=0.95)
        b = TR.render_layer(lib, L_t, title_mask, np.full((H, W, 3), (0.95, 0.80, 0.42), np.float32), 0, 0, r, rng, i, cv, None, 2)
        plain(cv, [('the threshold, as an image torrent', lit, 'c', 470)])
        return cv, a['replaced'] + b['replaced']
    tc = card(os.path.join(HERE, 'cache/title.mp4'), title)
    # ---------------- what it is made of
    usage = json.load(open(os.path.join(HERE, '..', 'trace.json')))['usage']
    pl = json.load(open(os.path.join(HERE, 'cache/placements.json')))
    nshots = len(usage); total = sum(pl.values())
    nframes = sum(s['n'] for s in lib.shots if (s['category'] + ('(kit)' if 'kit/' in s['dir'] else '')) in usage)
    lines = [
        ('MADE OF', mono, 70, 60),
        (f'{total:,} placements of {nframes:,} found frames from {nshots} public-domain films (Internet Archive, NTIS, NARA)', mono_s, 70, 100),
        (f'the dog      {pl["dog"]:,} pictures of animals: giraffe, horse, cow, cat, lion, tiger, rabbit, sheep,', mono_s, 70, 150),
        ('             monkey, rhinoceros, a migrating herd, and a real dog (Amateur Film New Jersey C)', mono_s, 70, 176),
        (f'the person   {pl["person"] + pl["face"] + pl["hand"]:,} pictures of faces, eyes, hats, hands and bodies', mono_s, 70, 214),
        (f'the door     {pl["panel"] + pl["trim"]:,} pictures of doors, ladders, windmills, lighthouses (Straight Talk ...)', mono_s, 70, 252),
        (f'the house    {pl["wall"]:,} cups, stoves, clocks, books, vases, brooms', mono_s, 70, 290),
        (f'the light    {pl["inside"] + pl["spill"]:,} lanterns, light bulbs, stars        the dusk  clouds, sea, river, bats, swans', mono_s, 70, 328),
        (f'the voice    {pl["words"]:,} pictures: COME HERE in alarms, trumpets, cannons; it\'s all right in flowers', mono_s, 70, 366),
        ('no figure is drawn: the moulds are computed from the PAELEO score, the sound from the torrent itself', mono_s, 70, 420),
        ('Quick, Draw! not used. Sources and rights: assets.json', mono_s, 70, 446),
    ]
    L_e = bg_layer('every')
    def end(i):
        cv = np.zeros((H, W, 3), np.float32)
        a = TR.render_layer(lib, L_e, np.ones((H, W), np.float32), np.full((H, W, 3), (0.07, 0.06, 0.10), np.float32), 0, 0, 0.004, rng, i, cv, None, 4, bbox=(0, 0, W, H))
        cv *= 0.55
        plain(cv, lines)
        return cv, a['replaced']
    ec = card(os.path.join(HERE, 'cache/end.mp4'), end)
    json.dump(dict(title=tc, end=ec), open(os.path.join(HERE, 'cache/card_stats.json'), 'w'))

if __name__ == '__main__':
    main()
