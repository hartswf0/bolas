"""SCION-36 · title card and end card (1280x720). The end card shows the actual weight heat maps the film was
skinned with (proof/heat_*.png, written by rigs.py) and the measured test numbers (proof/tests.json)."""
import json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(OUT, '..', '..', '..'))
FONTS = os.path.join(ROOT, 'tools/paeleo/fonts')
CACHE = os.path.join(HERE, 'cache'); PROOF = os.path.join(OUT, 'proof')
BIG = lambda s: ImageFont.truetype(os.path.join(FONTS, 'f8.woff2'), s)
MONO = lambda s: ImageFont.truetype(os.path.join(FONTS, 'f14.woff2'), s)
BG = (14, 13, 12); INK = (226, 214, 196); DIM = (150, 140, 128); WARM = (236, 180, 110)


def title():
    im = Image.new('RGB', (1280, 720), BG); d = ImageDraw.Draw(im)
    d.text((110, 250), 'PAE-02 · SCION 36 · Bounded Biharmonic Weights', font=BIG(58), fill=INK)
    d.text((112, 335), 'the threshold, auto-rigged from found silhouettes of a real dog', font=MONO(22), fill=DIM)
    d.text((112, 372), 'Amateur Film New Jersey C · Home Movies, Internet Archive · public domain', font=MONO(18), fill=DIM)
    im.save(os.path.join(CACHE, 'title.png'))


def endcard():
    T = json.load(open(os.path.join(PROOF, 'tests.json')))
    FR = json.load(open(os.path.join(OUT, 'assets.json')))['assets'][0]['distinct_archive_frames_in_film']
    im = Image.new('RGB', (1280, 720), BG); d = ImageDraw.Draw(im)
    d.text((60, 34), 'what it is made of', font=BIG(40), fill=INK)
    tiles = [('heat_W_f010.png', 'f010  watch · walk · lie · look'), ('heat_r5_f005.png', 'f005  looking in'),
             ('heat_t40_f040.png', 'f040  in the turn'), ('heat_P_person.png', 'Straight Talk f000  the person')]
    x = 60
    for fn, cap in tiles:
        h = Image.open(os.path.join(PROOF, fn)).convert('RGB')
        s = 250 / h.size[1]; h = h.resize((int(h.size[0] * s), 250))
        if h.size[0] > 330: h = h.resize((330, int(250 * 330 / h.size[0])))
        im.paste(h, (x, 100)); d.text((x, 360), cap, font=MONO(14), fill=DIM); x += h.size[0] + 22
    w = T['views']['W']
    leak_b = sum(v['leg_leak_bbw']['mean'] for v in T['views'].values() if v['leg_leak_bbw']) / len(T['views'])
    leak_s = sum(v['leg_leak_shepard_baseline']['mean'] for v in T['views'].values() if v['leg_leak_shepard_baseline']) / len(T['views'])
    nb = T['stability_neighbours']
    stab = sum(v['mean_abs_dw'] for v in nb.values()) / len(nb)
    lines = [
        'The dog: %d whole frames of a real dog (%s), one mesh each, never cut into' % (len(FR), ', '.join('f%03d' % f for f in FR)),
        'pieces; ragged SAM edge, blur and grain as found (Amateur Film New Jersey C, public domain); f010 also mirrored.',
        'Each frame: auto-triangulated, handles placed from its medial axis (points: nose, tail tip; bones: neck, back,',
        'tail, legs), weights solved as bounded biharmonic weights; nothing painted by hand. Heat maps above.',
        'Tests: weights in [0, 1], partition of unity to %.0e; mean leak across the gaps between legs %.4f' % (
            max(v['partition_of_unity_max_err'] for v in T['views'].values()), leak_b),
        '(shape-blind inverse-distance weights %.4f); neighbouring archive frames f008, f009, f011: mean |dw| %.3f.' % (leak_s, stab),
        'The person: one frame of Straight Talk (NTIS 1992, public domain), rigged the same way, kept in shadow.',
        'Porch, door, light and sound are computed. Score: PAELEO threshold, 768 frames.']
    y = 400
    for ln in lines:
        d.text((60, y), ln, font=MONO(16), fill=INK if not ln.startswith('Tests') else WARM); y += 30
    im.save(os.path.join(CACHE, 'endcard.png'))


if __name__ == '__main__':
    title(); endcard(); print('cards ok')
