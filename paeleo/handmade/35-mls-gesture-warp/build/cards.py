"""SCION 35 · title and end cards, printed like the scene: solid blue ink, an orange plate misregistered under it,
a small screened specimen of the dog print with its dot grid, on cream stock."""
import numpy as np, os
from PIL import Image, ImageDraw, ImageFont
from common import CACHE, W, H, PAPER, inks, screen
import render, anim

SERIF = '/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf'
SERIF_R = '/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'


def plate(draw_fn):
    im = Image.new('L', (W, H), 0)
    draw_fn(ImageDraw.Draw(im))
    return np.asarray(im, np.float32) / 255


def card(lines_fn, specimen_at=None, specimen_q=None):
    blue = plate(lambda d: lines_fn(d, 0, 0))
    orange = plate(lambda d: lines_fn(d, 4, 3))       # the orange plate, off register
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    tint = 0.10 + 0.06 * np.sin(xx / 210.0) * np.cos(yy / 170.0)
    ib = blue
    io = orange * 0.85
    img = inks(PAPER, ib, io)
    if specimen_q is not None:
        rgb, cov, _, _ = render.warp_print(*specimen_q)
        img = img * (1 - cov[..., None]) + rgb * cov[..., None]
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))


def title():
    f1 = ImageFont.truetype(SERIF, 64); f2 = ImageFont.truetype(SERIF_R, 30); f3 = ImageFont.truetype(MONO, 16)

    def lines(d, ox, oy):
        d.text((90 + ox, 170 + oy), 'PAE-02 · SCION 35 · Moving Least Squares', font=f1, fill=255)
        d.text((92 + ox, 250 + oy), 'Gesture Warp Swarm', font=f1, fill=255)
        d.text((94 + ox, 345 + oy), 'the threshold, as a two-colour print bent by its handles', font=f2, fill=255)
        d.text((94 + ox, 640 + oy), 'cohort 9 · rigid skull · similarity legs · affine coat', font=f3, fill=255)
    # a specimen of the dog print, standing, at the right
    sh, Q, root, _ = anim.dog_pose(240, with_stretch=False)
    dx = np.array([1010.0, 560.0]) - root
    Q = {k: v + dx for k, v in Q.items()}
    return card(lines, specimen_q=(sh, Q))


def end_lines():
    import json
    from dogprint import PRINTS
    words = {13: 'thirteen', 15: 'fifteen', 17: 'seventeen', 19: 'nineteen'}
    n = words.get(len(PRINTS), str(len(PRINTS)))
    L = [
        'What this is made of',
        '',
        'A two-colour risograph print made in code: a blue plate and an orange plate,',
        'screened into dots, on cream stock. No photographs, no footage, no recordings.',
        '',
        'The dog is %s view prints (profile, three-quarter, rear, lying), each bent' % n,
        'every frame by moving-least-squares handles: a rigid skull, similarity legs,',
        'neck and tail, an affine coat. Its views change behind a swing of the body.',
        'Where the warp strains the print, the dots stretch; that is left in.',
    ]
    p = os.path.join(os.path.dirname(CACHE), '..', 'trace.json')
    if os.path.exists(p):
        d = json.load(open(p))['summary']['distortion_by_family']
        g = sum(v.get('fold_guard_layer_frames', 0) for v in d.values())
        L += ['',
              'Measured dot stretch, largest per layer (median / 95th percentile over the film):',
              'coat %.2f / %.2f   legs, neck, tail %.2f / %.2f   skull and ears %.2f / %.2f.' % (
                  d['affine']['aniso_max_median'], d['affine']['aniso_max_p95'], d['similarity']['aniso_max_median'],
                  d['similarity']['aniso_max_p95'], d['rigid']['aniso_max_median'], d['rigid']['aniso_max_p95']),
              'The skull is a rigid fit: in a fast view swing its handles change shape and it stretches',
              'up to %.1f. No folded cells; %d layer-frames (mostly the neck) fell back to a two-handle fit.' % (d['rigid']['aniso_max_max'], g)]
    L += ['', 'The person is printed and bent the same way. The porch is screened in place.',
          'Sound: synthesised here: a formant voice, nails on boards, a door, crickets.']
    return L


def end():
    f1 = ImageFont.truetype(SERIF, 38); f2 = ImageFont.truetype(SERIF_R, 22)

    END = end_lines()

    def lines(d, ox, oy):
        y = 60
        for k, s in enumerate(END):
            d.text((92 + ox, y + oy), s, font=f1 if k == 0 else f2, fill=255)
            y += 48 if k == 0 else 29
    return card(lines)


if __name__ == '__main__':
    title().save(os.path.join(CACHE, 'title.jpg'), quality=94)
    end().save(os.path.join(CACHE, 'end.jpg'), quality=94)
    print('cards ok')
