"""Round 2 search (critic repairs 1, 3, 4): head-low walking dogs over the full 4,164, and lying
dogs with a profile head. Candidate pools by stroke features; the picks were made by eye."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import qd
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = json.load(open(f'{HERE}/work/dog_features.json'))
dogs = qd.load('dog')


def sheet(items, path, cols=10, rows=6, cw=150, ch=120):
    img = Image.new('RGB', (cols * cw, rows * ch), 'white'); dr = ImageDraw.Draw(img)
    for k, f in enumerate(items[:cols * rows]):
        S = qd.strokes_np(dogs[f['idx']]); x0, y0, x1, y1 = qd.bbox(S)
        sc = min((cw - 16) / max(x1 - x0, 1), (ch - 26) / max(y1 - y0, 1))
        cx, cy = (k % cols) * cw, (k // cols) * ch
        for s in S:
            pts = [(cx + 8 + (p[0] - x0) * sc, cy + 18 + (p[1] - y0) * sc) for p in s]
            dr.line(pts if len(pts) > 1 else pts * 2, fill='black', width=2)
        dr.text((cx + 3, cy + 2), str(f['idx']), fill=(200, 0, 0))
        dr.rectangle([cx, cy, cx + cw - 1, cy + ch - 1], outline=(220, 220, 220))
    img.save(path)


if __name__ == '__main__':
    ok = [f for f in F if f['recognized'] and 3 <= f['ns'] <= 12 and f['sym'] < 0.6]
    # head low: the back (middle third) is the highest part; both ends lower; legs visible
    hl = [f for f in ok if 1.3 < f['aspect'] < 2.6 and f['legrows'] >= 0.15 and f['tm'] < f['tl'] and f['tm'] < f['tr']]
    hl.sort(key=lambda f: f['npts'])
    print('head-low pool', len(hl))
    for k in range(0, min(len(hl), 300), 60):
        sheet(hl[k:k + 60], f'{HERE}/sheets/r2-headlow-{k // 60}.png')
