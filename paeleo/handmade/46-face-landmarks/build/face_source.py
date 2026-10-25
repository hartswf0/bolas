"""Source face annotator (SCION 46): cuts the person's face from the public-domain cartoon profile in
'We Learn About the Telephone I' (found-frames 'face', SAM masks; copied to sources/face/), records its landmarks
and registers each mouth-state frame to the reference by the static upper face.

Landmarks were annotated by hand on a 20 px grid (an automatic pass on the coarse SAM polygons found the nose but
mislabelled brow and chin; the SCION allows user-adjusted landmarks). Registration is then *measured*: for each frame,
the profile edge (rightmost dark outline pixel) is found on rows of the upper face, which does not move when the mouth
opens; the per-row difference to the reference is the registration residual. Mouth states are source frames, never warped.
Writes build/cache/face/face_<state>_<frame>.png (RGBA cut) and build/cache/face/manifest.json."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from geom import CACHE

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sources', 'face')
OUT = os.path.join(CACHE, 'face')
FRAMES = {'closed': 4, 'half': 12, 'open': 7}
# hand-annotated landmarks, source pixels (384 x 288)
LANDMARKS = {
    'closed': dict(bridge=[151, 5], nose_tip=[188, 42], upper_lip=[131, 118], mouth=[112, 140], chin=[104, 198]),
    'half':   dict(bridge=[151, 5], nose_tip=[188, 42], upper_lip=[132, 118], mouth=[100, 140], chin=[106, 197]),
    'open':   dict(bridge=[151, 5], nose_tip=[188, 42], upper_lip=[131, 112], mouth=[78, 150], chin=[110, 197]),
}
PIVOT = [40, 95]
SKIN = (198, 152, 124)   # one flat skin tone replaces the source's stripes and light bands
INK = (40, 28, 30)          # skull pivot in source pixels (where the drawn cranium is hinged on the neck)
ROWS = (5, 20, 40, 60, 90)   # upper-face rows used to measure registration


def edge_x(a, y):
    d = np.where(a[y] < 75)[0]
    return int(d.max()) if len(d) else -1


def main():
    os.makedirs(OUT, exist_ok=True)
    masks = json.load(open(os.path.join(SRC, 'masks.json')))
    clip = json.load(open(os.path.join(SRC, 'clip.json')))
    man = {'source': {'title': 'We Learn About the Telephone I', 'archive_url': 'https://archive.org/details/WeLearnA1965',
                      'clip_id': clip.get('clip_id'), 'rights': 'public_domain', 'label': clip.get('label'),
                      'frames_from': 'hartswf0/secondhand-motion/shots/face-sam/frames (copied to sources/face/)', 'masks': 'SAM masks.json'},
           'typology': 'caricature: a drawn cartoon profile, not a photograph of a real person',
           'treatment': 'flattened: the source contour line (dark pixels within 4 px of the mask edge) is kept; interior bands and stripes are replaced by one skin tone; geometry untouched',
           'fit': 'similarity only (rotation, uniform scale, translation), pivot ' + str(PIVOT),
           'landmarks_method': 'hand-annotated on a 20 px grid', 'frames': {}}
    ref = None
    for state, i in FRAMES.items():
        im = Image.open(os.path.join(SRC, f'f{i:03d}.jpg')).convert('RGB')
        a = np.asarray(im.convert('L')).astype(float)
        rows = [edge_x(a, y) for y in ROWS]
        if ref is None: ref = rows
        res = float(np.sqrt(np.mean((np.array(rows) - np.array(ref)) ** 2)))
        poly = max(masks[str(i)], key=len)
        m = Image.new('L', im.size, 0); ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
        m = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
        # flatten: the source's light bands and stripe tones go; only its outline ink near the contour stays
        mk = np.asarray(m, float) / 255.0
        band = (np.asarray(m.filter(ImageFilter.MaxFilter(9)), float) > 0) & (np.asarray(m.filter(ImageFilter.MinFilter(9)), float) < 255)
        ink = (a < 92) & band
        rgb = np.zeros(a.shape + (3,), np.uint8); rgb[...] = SKIN
        rgb[ink] = INK
        rgba = Image.fromarray(rgb); rgba.putalpha(m)
        fn = f'face_{state}_{i:03d}.png'; rgba.save(os.path.join(OUT, fn))
        man['frames'][fn] = dict(state=state, source_frame=f'f{i:03d}.jpg', landmarks=LANDMARKS[state], pivot=PIVOT,
                                 upper_face_edge_x=dict(zip(map(str, ROWS), rows)), registration_residual_px=round(res, 2),
                                 to_reference='identity (the drawing does not move between these frames; measured residual above)')
        print(fn, 'edge rows', rows, 'residual px', round(res, 2))
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
