"""Source face annotator (SCION 46): cuts the person's face from the public-domain cartoon profile in
'We Learn About the Telephone I' (found-frames 'face', SAM masks), annotates its landmarks automatically from the mask
contour (brow, nose tip, mouth corner, chin), registers every chosen frame to a reference frame by similarity (no shear),
and writes the face fitting manifest + RGBA plates into build/cache/face/. Mouth states are source frames, never warped."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from geom import ROOT, CACHE, fit_similarity, residual, apply

SRC = '/home/user/hartswf0/secondhand-motion/shots/face-sam'
OUT = os.path.join(CACHE, 'face')
FRAMES = {'closed': [4, 14, 33], 'half': [12, 13, 26], 'open': [7, 8, 24]}


def landmarks(poly):
    P = np.array(poly, float)
    # contour of the face edge: points with x>40 (the right-hand profile line), excluding frame borders
    edge = P[(P[:, 0] > 30) & (P[:, 1] > 2) & (P[:, 1] < 286)]
    nose = edge[np.argmax(edge[:, 0] - 0.15 * edge[:, 1])]
    lower = edge[edge[:, 1] > nose[1] + 60]
    chin = lower[np.argmax(lower[:, 0] + 0.35 * lower[:, 1])] if len(lower) else edge[np.argmax(edge[:, 1])]
    upper = edge[edge[:, 1] < nose[1] - 20]
    brow = upper[np.argmin(upper[:, 1])] if len(upper) else nose
    mid = edge[(edge[:, 1] > nose[1] + 30) & (edge[:, 1] < chin[1] - 15)]
    mouth = mid[np.argmin(mid[:, 0])] if len(mid) else (nose + chin) / 2
    return dict(brow=brow.tolist(), nose=nose.tolist(), mouth=mouth.tolist(), chin=chin.tolist())


def main():
    os.makedirs(OUT, exist_ok=True)
    masks = json.load(open(os.path.join(SRC, 'masks.json')))
    man = {'source': {'title': 'We Learn About the Telephone I', 'archive_url': 'https://archive.org/details/WeLearnA1965',
                      'clip_id': 'de79b639-b8b3-5462-912e-b57322df522b', 'rights': 'public_domain',
                      'frames_dir': 'hartswf0/secondhand-motion/shots/face-sam/frames', 'masks': 'SAM masks.json'},
           'typology': 'caricature, drawn profile (not a photograph of a real person)', 'fit': 'similarity only (rotation, uniform scale, translation)',
           'frames': {}}
    ref = None
    for state, ids in FRAMES.items():
        for i in ids:
            im = Image.open(os.path.join(SRC, 'frames', f'f{i:03d}.jpg')).convert('RGB')
            poly = max(masks[str(i)], key=len)
            lm = landmarks(poly)
            m = Image.new('L', im.size, 0); ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
            m = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
            rgba = im.copy(); rgba.putalpha(m)
            fn = f'face_{state}_{i:03d}.png'; rgba.save(os.path.join(OUT, fn))
            keys = ['brow', 'nose', 'chin']
            src = np.array([lm[k] for k in keys])
            if ref is None: ref = src
            M = fit_similarity(src, ref)
            man['frames'][fn] = dict(state=state, source_frame=f'f{i:03d}.jpg', landmarks=lm, to_reference=M.tolist(),
                                     residual_px=round(residual(M, src, ref), 2), scale=round(float(np.hypot(M[0, 0], M[1, 0])), 4))
            print(fn, {k: [round(v) for v in lm[k]] for k in lm}, 'res', man['frames'][fn]['residual_px'], 'scale', man['frames'][fn]['scale'])
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
