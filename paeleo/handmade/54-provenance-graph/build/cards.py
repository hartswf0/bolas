"""Title card and end card, and the assembled sequence (symlinks) for ffmpeg."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lineage import FOLDER, REPO
FONTS = os.path.join(REPO, 'tools/paeleo/fonts/')
CACHE = os.path.join(FOLDER, 'build', 'cache')
W, H = 1280, 720
BG = (14, 13, 24)


def F(fid, size, wght=None):
    f = ImageFont.truetype(FONTS + fid + '.woff2', size)
    if wght:
        axes = f.get_variation_axes()
        f.set_variation_by_axes([wght if a['name'] == b'Weight' else a['default'] for a in axes])
    return f


def dag_points(L):
    """lay the dog's lineage out left (sources) to right (pieces), for the end card's faint graph."""
    nodes = L['nodes']
    dog = L['roots']['dog']
    ends = [v['dusk'] for v in dog.values()] + [e['dusk'] for e in L['roots']['cast']['turn']]
    depth = {}
    def d(n):
        if n in depth:
            return depth[n]
        ps = nodes[n]['parents']
        depth[n] = 0 if not ps else 1 + max(d(p) for p in ps)
        return depth[n]
    keep = set()
    for e in ends:
        st = [e]
        while st:
            k = st.pop()
            if k in keep:
                continue
            keep.add(k); st.extend(nodes[k]['parents'])
    for k in keep:
        d(k)
    maxd = max(depth[k] for k in keep)
    cols = {}
    for k in sorted(keep):
        cols.setdefault(depth[k], []).append(k)
    pos = {}
    for c, ks in cols.items():
        for j, k in enumerate(ks):
            pos[k] = (700 + c / maxd * 520, 70 + (j + 0.5) / len(ks) * 560)
    edges = [(p, k) for k in keep for p in nodes[k]['parents'] if p in pos]
    return pos, edges, {k: nodes[k] for k in keep}


def main():
    L = json.load(open(os.path.join(FOLDER, 'lineage', 'lineage.json')))
    n_nodes = len(L['nodes'])
    os.makedirs(os.path.join(CACHE, 'cards'), exist_ok=True)
    big = F('f8', 74, 800); mid = F('f27', 30); mono = F('f14', 15); small = F('f34', 21)
    for k in range(72):
        a = min(1, k / 10, (72 - k) / 10)
        im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
        c = tuple(int(v * a + BG[i] * (1 - a)) for i, v in enumerate((238, 226, 204)))
        c2 = tuple(int(v * a + BG[i] * (1 - a)) for i, v in enumerate((170, 156, 180)))
        d.text((W / 2, 300), 'PAE-02 · SCION 54 · Provenance Graph', font=big, fill=c, anchor='mm')
        d.text((W / 2, 380), 'the threshold, handmade: archive-to-puppet lineage', font=mid, fill=c2, anchor='mm')
        d.text((W / 2, 640), 'every piece of this film is a node with a parent, a hash and a rights record', font=mono, fill=c2, anchor='mm')
        im.save(os.path.join(CACHE, 'cards', 'title_%02d.png' % k))
    pos, edges, nd = dag_points(L)
    lines = ['Made of:',
             'a home-movie dog (Amateur Film New Jersey C, PD), cut',
             'into seven rigged pieces, and ten of its own turning frames;',
             'the door’s own swing and a woman, from Straight Talk (PD);',
             'a hand from The Door to Heaven (1941, PD); a miner’s lantern;',
             'found cloud; Quick, Draw! moon, trees, fence (CC BY 4.0);',
             'drawn cut lines and walls; synthesised sound.',
             '',
             '%d nodes in lineage.json; every frame rebuilt from them.' % n_nodes]
    for k in range(72):
        a = min(1, k / 8, (72 - k) / 12)
        im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im, 'RGBA')
        for p, q in edges:
            d.line([pos[p], pos[q]], fill=(150, 130, 170, int(60 * a)), width=1)
        for kk, (x, y) in pos.items():
            src = nd[kk]['kind'] == 'source'
            r = 4 if src else 2.5
            col = (236, 200, 150, int(220 * a)) if src else (180, 170, 210, int(150 * a))
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        d.text((720, 40), 'the dog’s lineage: sources → mattes → cuts → pieces', font=mono, fill=(170, 156, 180, int(200 * a)))
        y = 150
        for i, t in enumerate(lines):
            d.text((70, y), t, font=small if i else F('f41', 30, 600), fill=(238, 226, 204, int(255 * a)))
            y += 44 if i == 0 else 34
        d.text((70, 640), 'PAE-02 · SCION 54 · Provenance Graph', font=mono, fill=(170, 156, 180, int(200 * a)))
        im.save(os.path.join(CACHE, 'cards', 'end_%02d.png' % k))
    # sequence
    seq = os.path.join(CACHE, 'seq'); os.makedirs(seq, exist_ok=True)
    for f in os.listdir(seq):
        os.remove(os.path.join(seq, f))
    n = 0
    def link(src):
        nonlocal n
        os.symlink(src, os.path.join(seq, '%04d.png' % n)); n += 1
    for k in range(72):
        link(os.path.join(CACHE, 'cards', 'title_%02d.png' % k))
    for i in range(768):
        link(os.path.join(CACHE, 'frames', 'scene_%04d.png' % i))
    for k in range(72):
        link(os.path.join(CACHE, 'cards', 'end_%02d.png' % k))
    print(n, 'frames in sequence')


if __name__ == '__main__':
    main()
