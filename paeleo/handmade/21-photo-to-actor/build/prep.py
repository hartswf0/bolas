"""Photograph preparer: archive frames -> photo masks -> photo-textured parts and angle artwork (RGBA sprites).

Inputs : kit/archive-dog frames + SAM masks (masks.json), kit/archive-door frames + masks, spec.py (hand annotations).
Outputs: actor/parts/*.png (sprites, 2x source resolution, alpha = SAM mask n hand cut, feathered),
         actor/parts.json (every sprite: source frame, cut, anchors in sprite pixels, operation),
         sources/ (the archive frames actually used, copied, with their masks).
"""
import json, os, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FOLDER, '..', '..', '..'))
sys.path.insert(0, HERE)
import spec

UP = 2                      # sprites are stored at 2x source pixels
OUT = os.path.join(FOLDER, 'actor', 'parts')
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(FOLDER, 'sources', 'dog'), exist_ok=True)
os.makedirs(os.path.join(FOLDER, 'sources', 'door'), exist_ok=True)

DOGM = json.load(open(os.path.join(ROOT, spec.KIT_DOG, 'masks.json')))
DOORM = json.load(open(os.path.join(ROOT, spec.KIT_DOOR, 'masks.json')))
used = {'dog': set(), 'door': set()}


def frame(kind, i):
    used[kind].add(i)
    kit = spec.KIT_DOG if kind == 'dog' else spec.KIT_DOOR
    return Image.open(os.path.join(ROOT, kit, 'frames', 'f%03d.jpg' % i))


def sam_mask(kind, i, grow=0):
    M = DOGM if kind == 'dog' else DOORM
    m = Image.new('L', (384, 288), 0)
    d = ImageDraw.Draw(m)
    for poly in M[str(i)]:
        if len(poly) >= 3:
            d.polygon([tuple(p) for p in poly], fill=255)
    if grow:
        m = m.filter(ImageFilter.MaxFilter(2 * grow + 1))
    return m


def poly_mask(poly, size=(384, 288)):
    m = Image.new('L', size, 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
    return m


def strip_poly(a, b, w, ext=0.0):
    a, b = np.array(a, float), np.array(b, float)
    d = b - a; L = np.hypot(*d); u = d / L; n = np.array([-u[1], u[0]])
    a2, b2 = a - u * ext * L, b + u * ext * L
    return [tuple(a2 + n * w / 2), tuple(b2 + n * w / 2), tuple(b2 - n * w / 2), tuple(a2 - n * w / 2)]


def develop(img):
    """photographic development of a blurred 1950s amateur frame: grey, local contrast, a little unsharp."""
    g = img.convert('L')
    g = ImageOps.autocontrast(g, cutoff=1)
    g = g.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    return g


def cut(kind, i, alpha_src, box=None, feather=1.2, name=None, anchors=None, op='', mirror=False, fade=None):
    """alpha_src: L mask 384x288. box: crop (x0,y0,x1,y1) in source px. Saves RGBA at UPx. anchors: source px points."""
    img = develop(frame(kind, i)) if kind == 'dog' else frame(kind, i).convert('RGB')
    a = alpha_src
    if box is None:
        bb = a.getbbox(); box = (bb[0] - 3, bb[1] - 3, bb[2] + 3, bb[3] + 3)
    x0, y0, x1, y1 = box
    W, H = (x1 - x0) * UP, (y1 - y0) * UP
    rgb = img.crop(box).resize((W, H), Image.LANCZOS).convert('RGB')
    al = a.crop(box).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(feather * UP))
    if fade is not None:   # fade the alpha toward point fade[0] (source px) over radius fade[1]
        yy, xx = np.mgrid[0:H, 0:W]
        fx, fy = (fade[0][0] - x0) * UP, (fade[0][1] - y0) * UP
        dist = np.hypot(xx - fx, yy - fy) / (fade[1] * UP)
        k = np.clip(dist, 0, 1) ** 0.8
        al = Image.fromarray((np.array(al) * k).astype(np.uint8))
    rgba = rgb.copy(); rgba.putalpha(al)
    anc = {k: [(v[0] - x0) * UP, (v[1] - y0) * UP] for k, v in (anchors or {}).items()}
    if mirror:
        rgba = ImageOps.mirror(rgba)
        anc = {k: [W - v[0], v[1]] for k, v in anc.items()}
    rgba.save(os.path.join(OUT, name + '.png'))
    return {'file': 'actor/parts/%s.png' % name, 'source': '%s/frames/f%03d.jpg' % (spec.KIT_DOG if kind == 'dog' else spec.KIT_DOOR, i),
            'frame': i, 'box_src': list(box), 'size': [W, H], 'scale_from_source': UP, 'mirrored': mirror,
            'anchors': anc, 'operation': op}


parts = {}
F = spec.BODY_FRAME
sam9 = sam_mask('dog', F, grow=2)

# ---- torso: SAM mask n hand cut (head and legs removed)
tor = Image.fromarray(np.minimum(np.array(sam9), np.array(poly_mask(spec.TORSO_POLY))))
parts['torso'] = cut('dog', F, tor, name='torso', anchors=spec.JOINTS, op='SAM mask n hand cut polygon, feathered 1.2 px')

# ---- neck strip
nk = spec.NECK
m = Image.fromarray(np.minimum(np.array(sam9), np.array(poly_mask(strip_poly(nk['a'], nk['b'], nk['w'], 0.15)))))
parts['neck'] = cut('dog', F, m, name='neck', anchors={'a': nk['a'], 'b': nk['b']}, op='SAM mask n strip a->b, feathered')

# ---- legs: two segments each
for ln, L in spec.LEGS.items():
    p0, p1, p2 = L['pts']
    for si, (a, b, w) in enumerate([(p0, p1, L['w'][0]), (p1, p2, L['w'][1])]):
        ext = 0.18 if si == 0 else 0.12
        m = Image.fromarray(np.minimum(np.array(sam_mask('dog', F, grow=3)), np.array(poly_mask(strip_poly(a, b, w, ext))))) \
            if si == 1 else poly_mask(strip_poly(a, b, w, ext))   # upper segment: inside the body, keep the fur under the strip
        name = '%s_%d' % (ln, si)
        fade = (a, (np.hypot(b[0] - a[0], b[1] - a[1])) * 0.55) if si == 0 else None
        parts[name] = cut('dog', F, m, name=name, anchors={'a': a, 'b': b}, op='strip a->b n SAM mask' + (', proximal alpha fade (blends into torso)' if fade else ''), fade=fade)

# ---- tail (frame 12)
T = spec.TAIL
m = Image.fromarray(np.minimum(np.array(sam_mask('dog', T['frame'], grow=2)), np.array(poly_mask(strip_poly(T['a'], T['b'], T['w'], 0.08)))))
parts['tail'] = cut('dog', T['frame'], m, name='tail', anchors={'a': T['a'], 'b': T['b']}, op='SAM mask n strip, frame 12', feather=0.8)

# ---- heads: angle artwork from five frames; every head is stored muzzle-left (or viewer/away) so the rig faces left
for hn, Hd in spec.HEADS.items():
    i = Hd['frame']
    m = np.minimum(np.array(sam_mask('dog', i, grow=2)), np.array(poly_mask(Hd['poly']))).astype(float)
    # a soft ellipse inscribed in the cut: photo heads keep no square corners of background
    xs = [q[0] for q in Hd['poly']]; ys = [q[1] for q in Hd['poly']]
    cx, cy, rx, ry = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2
    yy, xx = np.mgrid[0:288, 0:384]
    e = np.clip((1.0 - np.hypot((xx - cx) / rx, (yy - cy) / ry)) / 0.18 + 0.3, 0, 1)
    if Hd.get('key') == 'dark':
        # the back of the head is the dark fur mass; the bright path behind it is keyed out by luminance
        L = np.array(develop(frame('dog', i)).filter(ImageFilter.GaussianBlur(1.2))).astype(float)
        m = m * np.clip((Hd['key_level'] - L) / 45.0, 0, 1)
    m = Image.fromarray((m * e).astype(np.uint8))
    mirror = Hd['faces'] == 'right'
    parts['head_' + hn] = cut('dog', i, m, name='head_' + hn, anchors={'pivot': Hd['pivot']}, mirror=mirror,
                              op='SAM mask (grown 3 px) n hand head cut' + (', mirrored to face left' if mirror else ''))
    parts['head_' + hn]['view'] = hn

# ---- whole-body angle artwork for the turns
for bn, B in spec.BODY_VIEWS.items():
    i = B['frame']
    m = sam_mask('dog', i, grow=1)
    bb = m.getbbox()
    anc = {'foot_mid': ((bb[0] + bb[2]) / 2, bb[3] - 2), 'top': ((bb[0] + bb[2]) / 2, bb[1])}
    mirror = B['faces'] == 'right'
    parts['body_' + bn] = cut('dog', i, m, name='body_' + bn, anchors=anc, mirror=mirror,
                              op='whole SAM mask' + (', mirrored to face left' if mirror else ''))
    parts['body_' + bn]['view'] = bn

# ---- the person (Straight Talk): photo cut by hand (no SAM mask of her exists), grey
for pn, P in spec.PERSON.items():
    i = P['frame']
    m = poly_mask(P['poly'])
    parts['person_' + pn] = cut('door', i, m, name='person_' + pn, op='hand cut polygon (no SAM mask covers the person), feathered', feather=1.5)

# ---- door leaf (SAM mask of f030) and the lit hallway
m = sam_mask('door', spec.DOOR_LEAF['frame'])
parts['door_leaf'] = cut('door', spec.DOOR_LEAF['frame'], m, name='door_leaf', op='SAM mask of f030 (the door leaf)', feather=0.6)
bx = spec.ROOM['box']
parts['room'] = cut('door', spec.ROOM['frame'], poly_mask([(bx[0], bx[1]), (bx[2], bx[1]), (bx[2], bx[3]), (bx[0], bx[3])]),
                    box=bx, name='room', op='rectangular crop of the lit hallway past the door', feather=0.0)

# ---- copy the sources actually used
for i in sorted(used['dog']):
    shutil.copy(os.path.join(ROOT, spec.KIT_DOG, 'frames', 'f%03d.jpg' % i), os.path.join(FOLDER, 'sources', 'dog', 'f%03d.jpg' % i))
for i in sorted(used['door']):
    shutil.copy(os.path.join(ROOT, spec.KIT_DOOR, 'frames', 'f%03d.jpg' % i), os.path.join(FOLDER, 'sources', 'door', 'f%03d.jpg' % i))
json.dump({'dog': {str(i): DOGM[str(i)] for i in sorted(used['dog'])}, 'door': {str(i): DOORM[str(i)] for i in sorted(used['door'])}},
          open(os.path.join(FOLDER, 'sources', 'masks_used.json'), 'w'))
shutil.copy(os.path.join(ROOT, spec.KIT_DOG, 'source.json'), os.path.join(FOLDER, 'sources', 'dog', 'source.json'))
shutil.copy(os.path.join(ROOT, spec.KIT_DOOR, 'source.json'), os.path.join(FOLDER, 'sources', 'door', 'source.json'))
os.makedirs(os.path.join(FOLDER, 'sources', 'cloud'), exist_ok=True)   # the sky: one frame of Top of the Cloud (public domain)
shutil.copy('/home/user/hartswf0/secondhand-motion/shots/cloud-sam/frames/f020.jpg', os.path.join(FOLDER, 'sources', 'cloud', 'f020.jpg'))
json.dump(parts, open(os.path.join(FOLDER, 'actor', 'parts.json'), 'w'), indent=1)
print('parts', len(parts), 'dog frames', sorted(used['dog']), 'door frames', sorted(used['door']))
