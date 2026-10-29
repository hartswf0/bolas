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
    lh = json.load(open(os.path.join(ROOT, 'data', 'learned_vs_handset.json')))
    lines = ['%d archive frames in, %d layers out' % (len(rep['train']), rep['K_final']),
             'pins: where two layers carry one point together',
             '',
             'unseen frames, silhouette IoU:',
             '  learned layers  %.2f' % hs['learned']['mean_iou'],
             '  hand-cut rig    %.2f' % hs['authored_rig']['mean_iou'],
             '  one rigid cut   %.2f' % hs['rigid_K1']['mean_iou'],
             '',
             '16 archive frames of the dog turning:',
             '  learned motion      %.2f' % lh['mean_iou_learned'],
             '  hand-set on hinges  %.2f' % lh['mean_iou_handset'],
             '  (learned better on %d of %d)' % (lh['learned_better_on'], lh['n'])]
    y = 230
    for ln in lines:
        d.text((80 + sw.width + 50, y), ln, font=font('f14.woff2', 20), fill=(220, 210, 190)); y += 32
    bg.save(os.path.join(HERE, 'cache', 'title.png'))
    st.save(os.path.join(ROOT, 'proof', 'structure.png'))
    # end card
    bg = Image.new('RGB', (1280, 720), (14, 14, 24)); d = ImageDraw.Draw(bg)
    d.text((80, 60), 'What it is made of', font=font('f2.woff2', 52), fill=(240, 226, 200))
    txt = [
        'The dog: one frame of Amateur Film New Jersey C (Home Movies, Internet Archive, public domain), split into',
        '%d layers by EM / gradient descent on %d frames (seams, pins); the split ties a hand-cut split (IoU %.2f / %.2f).' % (rep['K_final'], len(rep['train']), hs['learned']['mean_iou'], hs['authored_rig']['mean_iou']),
        'The acting is rig-driven: backing off, the turned back, approach, lying, look back, look in are hand-set',
        'rotations on the learned hinges, timed by the score. The learned model carries only the walk and the turns:',
    ]
    y = 140
    for ln in txt:
        d.text((80, y), ln, font=font('f14.woff2', 17), fill=(215, 205, 190)); y += 28
    # side by side: learned pose vs best hand-set pose of the same layers, on archive turning frames
    H_ = np.load(os.path.join(ROOT, 'model', 'handset_turn.npz')); Tn = np.load(os.path.join(ROOT, 'model', 'turn.npz'))
    rows = {r['frame']: r for r in lh['rows']}
    from puppet import to3, load_frame
    from scipy import ndimage as ndi
    show = [15, 16, 17, 19, 32]
    pw, ph = 200, 150
    x0 = 80; y0 = y + 12
    d.text((x0, y0), 'learned', font=font('f14.woff2', 16), fill=(240, 200, 120))
    d.text((x0, y0 + ph + 26), 'hand-set', font=font('f14.woff2', 16), fill=(150, 185, 235))
    for j, f in enumerate(show):
        im, mk = load_frame(f)
        ys, xs = np.nonzero(mk); cx, cy = xs.mean(), ys.mean()
        sc = 1.15
        P = np.array([[sc, 0, pw / 2 - sc * cx], [0, sc, ph / 2 - sc * cy], [0, 0, 1.0]])
        edge = mk ^ ndi.binary_erosion(mk, iterations=1)
        for rr, (A, colr, key) in enumerate(((Tn['learned'][list(Tn['frames']).index(f)], (240, 200, 120), 'learned_iou'),
                                             (H_['handset'][list(H_['frames']).index(f)], (150, 185, 235), 'handset_iou'))):
            can = np.full((ph, pw, 3), 0.08, np.float32)
            G = np.stack([P @ to3(a) for a in A])
            pp.tail_angle = 0.0
            pp.render(G, np.eye(3), can, tint=np.array([0.85, 0.85, 0.9]))
            ey, ex = np.nonzero(edge); qx = (P[0, 0] * ex + P[0, 2]).astype(int); qy = (P[1, 1] * ey + P[1, 2]).astype(int)
            ok = (qx >= 0) & (qx < pw) & (qy >= 0) & (qy < ph)
            can[qy[ok], qx[ok]] = np.array(colr) / 255.
            tile = Image.fromarray((np.clip(can, 0, 1) * 255).astype(np.uint8))
            px = x0 + 110 + j * (pw + 12); py = y0 + rr * (ph + 26)
            bg.paste(tile, (px, py))
            d.text((px + 4, py + ph - 20), 'f%02d  IoU %.2f' % (f, rows[f][key]), font=font('f14.woff2', 14), fill=colr)
    d.text((x0, y0 + 2 * ph + 60), 'Archive turning frames, real outline drawn over each pose. Learned better on %d of %d frames (mean %.2f vs %.2f).'
           % (lh['learned_better_on'], lh['n'], lh['mean_iou_learned'], lh['mean_iou_handset']), font=font('f14.woff2', 15), fill=(200, 190, 175))
    d.text((x0, y0 + 2 * ph + 86), 'Cut pieces of the same film: the tail (frame 6) and the head turned round at 7.5 s (frame 39). Person, house,',
           font=font('f14.woff2', 15), fill=(200, 190, 175))
    d.text((x0, y0 + 2 * ph + 108), 'porch, light: drawn here (numpy, Pillow). Sound synthesized here. Score: PAELEO threshold machine.',
           font=font('f14.woff2', 15), fill=(200, 190, 175))
    bg.save(os.path.join(HERE, 'cache', 'end.png'))


if __name__ == '__main__':
    main()
