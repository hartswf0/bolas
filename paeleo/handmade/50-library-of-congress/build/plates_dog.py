"""Fig. 1, the dog, engraved after the scan.
Puppet: frame f006 of Amateur Film New Jersey C, traced into 11 cut pieces (legs split at the joint), each engraved with the
scan's own tone. Turn plates: whole masked frames (SAM masks) of the same film, engraved the same way, used unaltered in shape.
Output: cache/plates/dog_<piece>.png (R = ink, A = coverage) at screen scale K, and cache/plates/dog.json (pivots in plate px)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from eng import engrave, poly_mask, dilate, erode, contour, blur, blurf
from rig import RIGS, ORDER, LEGS, GROUND, ANCHOR, FEATURES
KIT = os.path.join(HERE, '..', '..', 'kit', 'archive-dog')
OUT = os.path.join(HERE, 'cache', 'plates'); os.makedirs(OUT, exist_ok=True)
K = 1.44          # screen px per scan px (S = 190 px/m; the f006 dog is 132 scan px nose to rump = 1.0 m)
SS = 2            # supersampling of the engraving
HK = K * SS

def scan_tone(frame, box, mask_hi):
    """the scan's luminance inside the dog, contrast-stretched to a printing tone (1 = black)."""
    im = Image.open(os.path.join(KIT, 'frames', 'f%03d.jpg' % frame)).convert('L').crop(box)
    w, h = mask_hi.shape[1], mask_hi.shape[0]
    L = np.asarray(im.resize((w, h), Image.BICUBIC), np.float32) / 255.
    v = L[mask_hi > 0.5]
    lo, hi = np.percentile(v, 4), np.percentile(v, 97)
    t = 1 - np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1)
    return np.clip(t ** 1.15 * 0.92 + 0.06, 0, 1)

def down(a):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)

def save_plate(name, ink, cov):
    ink_im, cov_im = down(ink), down(cov)
    z = Image.new('L', ink_im.size, 0)
    Image.merge('RGBA', (ink_im, z, z, cov_im)).save(os.path.join(OUT, name + '.png'))

def puppet(rigname):
    R = RIGS[rigname]; f = R['frame']
    allp = [p for P in R['parts'].values() for p in P['poly']]
    x0, y0 = min(p[0] for p in allp) - 6, min(p[1] for p in allp) - 6
    x1, y1 = max(p[0] for p in allp) + 6, max(p[1] for p in allp) + 6
    box = (int(x0), int(y0), int(x1) + 1, int(y1) + 1)
    W, H = int((box[2] - box[0]) * HK), int((box[3] - box[1]) * HK)
    masks = {n: poly_mask((H, W), [P['poly']], HK, box[:2]) for n, P in R['parts'].items()}
    union = np.clip(sum(masks.values()), 0, 1)
    union = (blur(union, 2.0) > 0.5).astype(np.float32)          # smooth the traced silhouette a little
    tone = scan_tone(f, box, union)
    meta = {'frame': f, 'box': box, 'K': K, 'pieces': {}}
    edge = contour(union, 2.2 * SS)
    for n, P in R['parts'].items():
        m = masks[n]
        far = n.endswith('_far')
        t = np.clip(tone + (0.18 if far else 0.0), 0, 1)
        if n == 'head': t = np.clip(t * 0.78, 0, 1)
        # overlap 3 scan px into neighbours at cut edges, but never beyond the silhouette (or a far leg's own outline)
        cov = dilate(m, int(3 * HK)) * (union if not far else 1) if n in ('torso', 'head') else dilate(m, int(2 * HK)) * (union if not far else 1)
        if far: cov = dilate(m, int(1 * HK))
        own_edge = contour(cov, 2.0 * SS) if far or n == 'tail' else edge
        if n == 'head':
            # a cut piece: a thin white line of paper parts the head from the shoulders, inside it the engraved contour
            cov = dilate(m, int(2 * HK))
            inner = erode(cov, max(1, int(0.6 * HK)))
            # round 2: no hard collar where the neck runs into the shoulders: the parting and contour fade out near the pivot
            yy_, xx_ = np.mgrid[0:H, 0:W].astype(np.float32)
            px_, py_ = (P['pivot'][0] - box[0]) * HK, (P['pivot'][1] - box[1]) * HK
            dd = np.hypot(xx_ - px_, (yy_ - py_) * 1.0) / HK
            wcol = np.clip((dd - 9.0) / 10.0, 0, 1)
            own_edge = contour(inner, 1.6 * SS) * wcol
        ink = engrave(t, angle=-16 if n != 'head' else -40, period=3.3 * SS, warp_amp=1.4, cross=0.62, ox=box[0] * HK, oy=box[1] * HK)
        ink = np.maximum(ink * 0.95, own_edge)
        if n == 'head': ink = ink * (inner * wcol + (1 - wcol))
        if n == 'head':
            # engraver's interpretation where the scan is unreadable at this size: eye, nostril, mouth, ear fold (inferred)
            from PIL import ImageDraw as _D
            fi = Image.new('L', (W, H), 0); d = _D.Draw(fi)
            T = lambda p: ((p[0] - box[0]) * HK, (p[1] - box[1]) * HK)
            ex, ey = T(FEATURES['eye']); r = 1.3 * HK
            d.ellipse([ex - r, ey - r * 0.8, ex + r, ey + r * 0.8], fill=255)
            nx, ny = T(FEATURES['nostril']); r = 1.4 * HK
            d.ellipse([nx - r, ny - r, nx + r, ny + r], fill=255)
            d.line([T(p) for p in FEATURES['mouth']], fill=255, width=int(0.9 * HK))
            d.line([T(p) for p in FEATURES['ear']], fill=255, width=int(0.8 * HK))
            ink = np.maximum(ink, np.asarray(fi, np.float32) / 255. * m)
        pieces = []
        if n in LEGS:
            ky = (P['knee'][1] - box[1]) * HK
            yy = np.arange(H, dtype=np.float32)[:, None]
            up = np.clip((ky + 2.5 * HK - yy) / 2, 0, 1); lo = np.clip((yy - (ky - 2.5 * HK)) / 2, 0, 1)
            pieces = [(n + '_up', cov * up), (n + '_lo', cov * lo)]
        else:
            pieces = [(n, cov)]
        for pn, c in pieces:
            ys, xs = np.nonzero(c > 0.01)
            if len(xs) == 0: continue
            bx0, by0, bx1, by1 = xs.min() // SS * SS, ys.min() // SS * SS, (xs.max() // SS + 1) * SS, (ys.max() // SS + 1) * SS
            save_plate('dog%s_%s' % (rigname, pn), ink[by0:by1, bx0:bx1] * (c[by0:by1, bx0:bx1] > 0), c[by0:by1, bx0:bx1])
            # plate origin in scan coords
            meta['pieces'][pn] = {'origin': [box[0] + bx0 / HK, box[1] + by0 / HK]}
    # designed analog (no frame of the film shows it): the back of the head, turned away from us into the room.
    # Drawn here from an ellipse and two ears, toned with the scan's own head-and-neck tone; pivot as the head's.
    import math as _m
    hp = R['parts']['head']['pivot']
    skull = [(112 + 15 * _m.cos(a), 95 + 14 * _m.sin(a)) for a in np.linspace(0, 2 * _m.pi, 40)]
    neck = [(102, 100), (122, 100), (132, 112), (128, 122), (100, 122), (96, 112)]
    earL = [(99, 90), (101, 70), (109, 84)]; earR = [(115, 84), (123, 69), (126, 90)]
    polys = [skull, neck, earL, earR]
    bx0, by0 = 88, 62; bw, bh = int(50 * HK), int(64 * HK)
    m = poly_mask((bh, bw), polys, HK, (bx0, by0))
    yy = np.arange(bh, dtype=np.float32)[:, None] / HK + by0; xx = np.arange(bw, dtype=np.float32)[None, :] / HK + bx0
    # tone: the dark saddle of the scan's neck (sampled), lighter at the crown where the lamp catches the fur
    tvals = tone[(union > 0.5)]
    dark = float(np.percentile(tvals, 80))
    t = np.clip(dark - 0.35 * np.exp(-(((xx - 112) / 9) ** 2 + ((yy - 88) / 7) ** 2)), 0, 1) * np.ones_like(m)
    ink = engrave(t, angle=-60, period=3.3 * SS, warp_amp=1.4, cross=0.62)
    ink = np.maximum(ink, contour(m, 1.8 * SS))
    from PIL import ImageDraw as _D
    fi = Image.new('L', (bw, bh), 0); d = _D.Draw(fi)
    T = lambda p: ((p[0] - bx0) * HK, (p[1] - by0) * HK)
    d.line([T((102, 87)), T((103, 76))], fill=255, width=int(0.8 * HK)); d.line([T((121, 86)), T((121, 75))], fill=255, width=int(0.8 * HK))
    d.line([T((112, 84)), T((112, 104))], fill=170, width=int(0.6 * HK))   # the parting of the fur down the nape
    ink = np.maximum(ink, np.asarray(fi, np.float32) / 255. * m)
    save_plate('dog%s_head_rear' % rigname, ink * (m > 0), m)
    meta['pieces']['head_rear'] = {'origin': [bx0, by0]}
    meta['tone_mean'] = float(tone[union > 0.5].mean())
    meta['rig'] = R['parts']; meta['order'] = ORDER; meta['ground'] = GROUND; meta['anchor'] = ANCHOR
    json.dump(meta, open(os.path.join(OUT, 'dog%s.json' % rigname), 'w'), indent=0)
    return meta

TURN = [28, 30, 33, 36, 38, 40, 43, 44]   # f016, f017, f026 dropped in round 2: head hidden, read as a lump   # the film's own turn, left profile → facing camera → right
def turn_plates():
    M = json.load(open(os.path.join(KIT, 'masks.json')))
    meta = {}
    for f in TURN:
        im = Image.open(os.path.join(KIT, 'frames', 'f%03d.jpg' % f))
        m = Image.new('L', im.size, 0); d = ImageDraw.Draw(m)
        polys = M[str(f)]
        # keep the largest polygon (the dog), drop detached shadow fragments
        polys = sorted(polys, key=lambda P: -len(P))[:1]
        for P in polys: d.polygon([tuple(p) for p in P], fill=255)
        bb = m.getbbox(); box = (bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)
        W, H = int((box[2] - box[0]) * HK), int((box[3] - box[1]) * HK)
        mh = poly_mask((H, W), polys, HK, box[:2])
        mh = (blur(mh, 3.0 * SS) > 0.5).astype(np.float32)
        tone = scan_tone(f, box, mh) * 0.84      # printed a shade lighter, to sit with the cut-piece plates
        ink = engrave(tone, angle=-16, period=3.3 * SS, warp_amp=1.4, cross=0.68, ox=box[0] * HK, oy=box[1] * HK)
        ink = np.maximum(ink * 0.95, contour(mh, 2.2 * SS)) * mh
        save_plate('turn_f%03d' % f, ink, mh)
        meta[f] = {'box': box, 'bbox_scan': list(bb)}
    json.dump(meta, open(os.path.join(OUT, 'turn.json'), 'w'), indent=0)

if __name__ == '__main__':
    puppet('L'); turn_plates(); print('dog plates ok')
