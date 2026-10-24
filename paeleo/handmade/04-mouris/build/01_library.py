"""SCION-04 · image corpus. Cuts every frame of the chosen public-domain archive shots into tiles:
a full-frame tile and a subject tile (crop to the SAM mask's box, 4:3), at 64x48 / 32x24 / 16x12 / 8x6.
Stores per-tile mean colour, luminance, shot id and frame index (so a tile can play its own shot forward).
Output: build/cache/library.npz + build/cache/library.json (provenance index)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))   # /home/user/bolas
KIT = os.path.join(ROOT, 'paeleo/handmade/kit')
SHOTS = '/home/user/hartswf0/secondhand-motion/shots'
CACHE = os.path.join(HERE, 'cache'); os.makedirs(CACHE, exist_ok=True)

# pools: the subject of the tiny images means something
POOLS = {
  'animal': ['cat', 'horse', 'cow', 'sheep', 'rabbit', 'lion', 'tiger', 'monkey', 'giraffe', 'rhinoceros', 'animal-migration'],
  'person': ['hand', 'face', 'eye', 'yoga', 'hat'],
  'door':   ['door', 'ladder', 'windmill', 'lighthouse'],
  'house':  ['stove', 'microwave', 'vase', 'book', 'alarm-clock', 'coffee-cup', 'mug', 'frying-pan', 'broom', 'umbrella'],
  'light':  ['lantern', 'light-bulb', 'star'],
  'sky':    ['cloud', 'ocean', 'river', 'bat', 'swan'],
  'floor':  ['basket', 'hammer', 'shovel', 'wheel', 'paintbrush', 'garden-hose'],
  'yard':   ['palm-tree', 'flower', 'ant', 'spider'],
  'alarm':  ['alarm-clock', 'traffic-light', 'ambulance', 'trumpet', 'cannon'],
  'soft':   ['flower', 'swan', 'cloud', 'butterfly'],
}
SIZES = [(64, 48), (32, 24), (16, 12), (8, 6)]

def subject_box(polys, W=384, H=288, pad=0.12):
    if not polys: return None
    pts = np.array([p for poly in polys for p in poly], float)
    if len(pts) < 3: return None
    x0, y0 = pts.min(0); x1, y1 = pts.max(0)
    w, h = x1 - x0, y1 - y0
    if w < 12 or h < 12: return None
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = w * (1 + pad), h * (1 + pad)
    if w / h > 4 / 3: h = w * 3 / 4
    else: w = h * 4 / 3
    w = min(max(w, 64), W); h = w * 3 / 4
    if h > H: h = H; w = H * 4 / 3
    x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    return (x0, y0, x0 + w, y0 + h)

def load_shot(cat):
    """returns list of (frame Image, polys), meta"""
    if cat == 'dog-archive':
        d = os.path.join(KIT, 'archive-dog'); src = json.load(open(os.path.join(d, 'source.json')))['source']
        meta = dict(category='dog', source_title=src['source_title'], source_url=src['original_source_url'], rights='public_domain', dir='paeleo/handmade/kit/archive-dog')
    elif cat == 'door-archive':
        d = os.path.join(KIT, 'archive-door'); src = json.load(open(os.path.join(d, 'source.json')))['source']
        meta = dict(category='door', source_title=src['source_title'], source_url=src['original_source_url'], rights='public_domain', dir='paeleo/handmade/kit/archive-door')
    else:
        d = os.path.join(SHOTS, cat + '-sam')
        ff = {s['category']: s for s in json.load(open(os.path.join(KIT, 'found-frames.json')))}[cat]
        meta = dict(category=cat, source_title=ff['source_title'], source_url=ff['source_url'], rights=ff['rights'], clip_id=ff['clip_id'], dir=ff['frames'].replace('hartswf0/', '/home/user/hartswf0/'))
    masks = json.load(open(os.path.join(d, 'masks.json')))
    names = sorted(os.listdir(os.path.join(d, 'frames')))
    out = []
    for i, n in enumerate(names):
        im = Image.open(os.path.join(d, 'frames', n)).convert('RGB')
        if im.size != (384, 288): im = im.resize((384, 288))
        out.append((im, masks.get(str(i), []), n))
    return out, meta

def main():
    cats = ['dog-archive', 'door-archive'] + sorted({c for v in POOLS.values() for c in v})
    pools = {k: (['dog-archive'] if k == 'animal' else ['door-archive'] if k == 'door' else []) + v for k, v in POOLS.items()}
    tiles = {s: [] for s in SIZES}; info = []; shots = []
    for si, cat in enumerate(cats):
        frames, meta = load_shot(cat)
        meta['n'] = len(frames); meta['shot'] = si; meta['first_tile'] = len(info); shots.append(meta)
        for fi, (im, polys, name) in enumerate(frames):
            for kind in ('subject', 'full'):
                box = subject_box(polys) if kind == 'subject' else (0, 0, 384, 288)
                if box is None: box = (0, 0, 384, 288)
                crop = im.crop(tuple(int(round(v)) for v in box))
                for s in SIZES:
                    tiles[s].append(np.asarray(crop.resize(s, Image.LANCZOS if s[0] >= 32 else Image.BILINEAR), np.uint8))
                a = np.asarray(crop.resize((16, 12), Image.BILINEAR), np.float32) / 255.
                lum = (a @ np.array([.299, .587, .114])).mean()
                info.append(dict(shot=si, frame=fi, kind=kind, file=name, mean=[round(float(v), 4) for v in a.reshape(-1, 3).mean(0)], lum=round(float(lum), 4), std=round(float((a @ np.array([.299, .587, .114])).std()), 4)))
        print(cat, len(frames), file=sys.stderr)
    np.savez_compressed(os.path.join(CACHE, 'library.npz'), **{f't{s[0]}': np.stack(tiles[s]) for s in SIZES})
    json.dump(dict(shots=shots, tiles=info, pools=pools, sizes=SIZES), open(os.path.join(CACHE, 'library.json'), 'w'))

if __name__ == '__main__':
    main()
