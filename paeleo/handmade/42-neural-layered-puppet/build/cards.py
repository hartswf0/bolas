"""SCION 42 · title and end cards (1280x720).  The title card shows what the fit found: the template frame split into the
learned layers, the hinge pins where neighbouring layers agree, and the tree that links them.
python3 cards.py  -> cache/title.png, cache/end.png, ../proof/structure.jpg
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from puppet import Puppet

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FONTS = os.path.abspath(os.path.join(ROOT, '..', '..', '..', 'tools', 'paeleo', 'fonts'))
PAL = np.array([[222, 120, 80], [90, 150, 210], [226, 190, 90], [130, 190, 120], [190, 120, 200], [90, 190, 190],
                [230, 150, 170], [170, 140, 90], [220, 220, 220], [120, 120, 230], [170, 230, 150], [240, 130, 60]])


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def structure_image(pp, scale=3, names=None, show_uncert=False):
    im = pp.tim; mk = pp.tmask
    x0, y0, x1, y1 = [int(v) for v in pp.bbox]
    x0 -= 12; y0 -= 12; x1 += 12; y1 += 12
    H, W = (y1 - y0) * scale, (x1 - x0) * scale
    out = np.zeros((H, W, 4), np.float32)
    from scipy import ndimage
    ys, xs = np.nonzero(mk)
    lab = pp.lab[:9 * len(xs)].reshape(-1, 9)[:, 4]
    lab_img = -np.ones(mk.shape, int); lab_img[ys, xs] = lab
    big = np.kron(lab_img[y0:y1, x0:x1], np.ones((scale, scale), int))
    g = np.kron(im[y0:y1, x0:x1], np.ones((scale, scale)))
    inside = big >= 0
    col = PAL[np.clip(big, 0, None) % len(PAL)] / 255.
    out[..., :3] = (0.35 + 0.65 * g[..., None]) * col
    out[..., 3] = inside
    e = np.zeros_like(inside)
    e[:, 1:] |= big[:, 1:] != big[:, :-1]; e[1:, :] |= big[1:, :] != big[:-1, :]
    out[e & inside, :3] = 0.05
    img = Image.fromarray((out * 255).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(img)
    M = pp.M
    # tree and pins
    for k in range(pp.K):
        p = int(pp.parent[k])
        if p < 0: continue
        pv = pp.pivot[(k, p)]
        cpar = pp.P[pp.lab == p].mean(0); ck = pp.P[pp.lab == k].mean(0)
        S = lambda q: ((q[0] - x0) * scale, (q[1] - y0) * scale)
        d.line([S(cpar), S(pv), S(ck)], fill=(255, 255, 255, 200), width=2)
    for k in range(pp.K):
        p = int(pp.parent[k])
        if p < 0: continue
        pv = pp.pivot[(k, p)]
        q = ((pv[0] - x0) * scale, (pv[1] - y0) * scale)
        d.ellipse([q[0] - 6, q[1] - 6, q[0] + 6, q[1] + 6], fill=(240, 200, 110, 255), outline=(20, 20, 20, 255), width=2)
    return img


def main():
    pp = Puppet()
    rep = json.load(open(os.path.join(ROOT, 'data', 'fit_report.json')))
    st = structure_image(pp, 3)
    bg = Image.new('RGB', (1280, 720), (14, 14, 24))
    d = ImageDraw.Draw(bg)
    d.text((80, 70), 'PAE-02 · SCION 42 · Neural Layered Puppet', font=font('f2.woff2', 58), fill=(240, 226, 200))
    d.text((82, 150), 'Few-shot structure: a dog whose parts and hinges were found, not drawn.', font=font('f14.woff2', 20), fill=(190, 180, 170))
    sw = st.resize((int(st.width * 1.0), int(st.height * 1.0)))
    bg.paste(sw, (80, 210), sw)
    hs = rep['heldout_summary']
    lines = ['%d archive frames in, %d layers out' % (len(rep['train']), rep['K_final']),
             'pins: where two layers carry one point together',
             '',
             'unseen frames, silhouette IoU:',
             '  learned layers  %.2f' % hs['learned']['mean_iou'],
             '  hand-cut rig    %.2f' % hs['authored_rig']['mean_iou'],
             '  one rigid cut   %.2f' % hs['rigid_K1']['mean_iou']]
    y = 230
    for ln in lines:
        d.text((80 + sw.width + 50, y), ln, font=font('f14.woff2', 20), fill=(220, 210, 190)); y += 32
    bg.save(os.path.join(HERE, 'cache', 'title.png'))
    st.save(os.path.join(ROOT, 'proof', 'structure.png'))
    # end card
    bg = Image.new('RGB', (1280, 720), (14, 14, 24)); d = ImageDraw.Draw(bg)
    d.text((80, 60), 'What it is made of', font=font('f2.woff2', 52), fill=(240, 226, 200))
    txt = [
        'The dog: the pixels of one frame of Amateur Film New Jersey C (Home Movies, Internet Archive, public domain),',
        'split into %d layers by EM / gradient descent on %d frames of the same dog. Each layer moves by its own affine;' % (rep['K_final'], len(rep['train'])),
        'the seams and pins you see are the learned layers and the learned hinges. On unseen frames the learned layers',
        'fit about as well as a hand-cut rig (IoU %.2f vs %.2f), better than one rigid cut (%.2f).' % (hs['learned']['mean_iou'], hs['authored_rig']['mean_iou'], hs['rigid_K1']['mean_iou']),
        'Body motion: the source dog\'s own walk, re-fitted to the layers.',
        'Hand-set on the learned hinges (pale pins): the leg swing, the head carried low, lying down, the look in.',
        'Turning: real archive frames of the dog turning (3/4 and front views), shown whole;',
        'the layers never learned a turn.',
        '',
        'The person, the house, the porch, the dusk and the light: drawn and computed here (numpy, Pillow).',
        'Sound: synthesized here, the voice included (formant synthesis).',
        'Score: PAELEO threshold machine, 32 s.   Code: paeleo/handmade/42-neural-layered-puppet/build',
    ]
    y = 150
    for ln in txt:
        d.text((80, y), ln, font=font('f14.woff2', 18), fill=(215, 205, 190)); y += 34
    bg.save(os.path.join(HERE, 'cache', 'end.png'))


if __name__ == '__main__':
    main()
