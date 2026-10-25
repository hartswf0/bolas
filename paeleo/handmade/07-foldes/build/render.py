"""SCION 07 · renders the registered sequence (cache/seq.pkl) to frames: drawn place, door, the door-to-light metamorphosis,
the person and the dog, pen and wash. Then title and end cards. Frames go to cache/frames/NNNN.png."""
import math, os, pickle, sys
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import stage as ST
from draw import Canvas, SS, cr, INK
from paint import paint

ROOT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(ROOT, '..', '..', '..'))
FONTS = os.path.join(REPO, 'tools/paeleo/fonts')
OUTD = os.path.join(HERE, 'cache', 'frames')
G = {}

DOG_WASH = (216, 198, 166)
P_WASH = {'coat': (92, 100, 126), 'head': (228, 206, 184), 'hair': (64, 54, 50), 'armN': (92, 100, 126), 'armF': (80, 88, 112),
          'legN': (66, 66, 78), 'legF': (58, 58, 70)}
WARM = (252, 220, 150)


def init():
    G['bg0'] = ST.background(0.0, 1.0)
    G['bg1'] = ST.background(1.0, 1.0)
    m = Image.new('L', (ST.W // 2, ST.H // 2), 0)
    ImageDraw.Draw(m).polygon([(x / 2, y / 2) for x, y in ST.POOL], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(14)).resize((ST.W * SS, ST.H * SS), Image.BILINEAR)
    G['pool'] = m
    G['seq'] = pickle.load(open(os.path.join(HERE, 'cache', 'seq.pkl'), 'rb'))
    G['font_say'] = ImageFont.truetype(os.path.join(FONTS, 'f27.woff2'), 30)
    G['font_soft'] = ImageFont.truetype(os.path.join(FONTS, 'f27.woff2'), 23)


SAY = [(1.0, 2.3, 'Come here.', 'call'), (3.4, 4.6, 'Come here!', 'call'), (7.4, 9.4, "It's all right.", 'soft'),
       (10.4, 11.6, "It's all right.", 'soft'), (26.4, 27.4, 'Come in.', 'soft')]


def render_frame(k):
    fr = G['seq'][k]
    t = fr['t']
    im = Image.blend(G['bg0'], G['bg1'], min(1.0, fr['late']))
    cv = Canvas(im)
    # ---- the leaf
    leaf = ST.door_leaf(fr['theta'])
    cv.fill(leaf, (86, 64, 54), 1.0)
    cv.line(leaf + [leaf[0]], 2.2, INK, 1.0, 1.0, taper=(1, 1))
    # panels on the leaf follow its parallelogram
    def on_leaf(u, v):
        (ax, ay), (bx, by), (cx_, cy_), (dx, dy) = leaf
        top = (ax + (bx - ax) * u, ay + (by - ay) * u); bot = (dx + (cx_ - dx) * u, dy + (cy_ - dy) * u)
        return (top[0] + (bot[0] - top[0]) * v, top[1] + (bot[1] - top[1]) * v)
    for (u0, u1, v0, v1) in ((0.18, 0.82, 0.08, 0.44), (0.18, 0.82, 0.52, 0.92)):
        pts = [on_leaf(u0, v0), on_leaf(u1, v0), on_leaf(u1, v1), on_leaf(u0, v1), on_leaf(u0, v0)]
        cv.line(pts, 1.4, (40, 30, 28), 0.7, taper=(1, 1))
    kx, ky = on_leaf(0.88, 0.52)
    cv.dot(kx, ky, 3.2, (40, 30, 28), 0.9)
    # ---- light comes out: the pool on the boards (wash), and the leaf's outline carried out to become it
    lit = fr['lit']
    if lit > 0.01:
        m = G['pool'].point(lambda v: int(v * 0.62 * lit))
        im.paste(WARM, (0, 0), m)
    mu = fr['meta_u']
    if 0.0 < mu < 1.0:
        start = ST.door_leaf(math.radians(24))
        Q = [(a[0] + (b[0] - a[0]) * mu, a[1] + (b[1] - a[1]) * mu) for a, b in zip(start, ST.POOL)]
        cv.fill(Q, WARM, 0.35 * math.sin(math.pi * mu))
        cv.line(Q + [Q[0]], 1.8, INK, 0.85 * (1 - max(0.0, (mu - 0.6) / 0.4)), 2.0, taper=(1, 1))
    # ---- person
    paint(cv, fr['person'], (92, 100, 126), ST.S, fwd=1.0, washes=P_WASH, seed=3.0)
    # ---- dog
    lf = ST.light_field(lit)
    paint(cv, fr['dog'], DOG_WASH, ST.S, fwd=fr['fwd'], seed=0.0, light=lf)
    out = im.reduce(SS)
    # ---- the person's words, said: small italic under the scene
    d = ImageDraw.Draw(out)
    for t0, t1, txt, kind in SAY:
        if t0 - 0.05 <= t <= t1 + 0.35:
            a = min(1.0, (t - t0 + 0.05) / 0.2, (t1 + 0.35 - t) / 0.35)
            f = G['font_say'] if kind == 'call' else G['font_soft']
            col = (246, 240, 226) if kind == 'call' else (226, 220, 206)
            w = d.textlength(txt, font=f)
            ov = Image.new('RGBA', out.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).text((ST.W / 2 - w / 2, 678), txt, font=f, fill=col + (int(255 * a),))
            out = Image.alpha_composite(out.convert('RGBA'), ov).convert('RGB')
            d = ImageDraw.Draw(out)
    out.save(os.path.join(OUTD, '%04d.png' % (72 + k)))
    return k


def card(lines, path, rule=True):
    im = Image.new('RGB', (ST.W, ST.H), ST.PAPER)
    d = ImageDraw.Draw(im)
    y = 250
    for txt, fnt, size, col in lines:
        f = ImageFont.truetype(os.path.join(FONTS, fnt), size)
        w = d.textlength(txt, font=f)
        d.text((ST.W / 2 - w / 2, y), txt, font=f, fill=col)
        y += size + 18
    im.save(path)
    return im


def cards():
    ink = (30, 28, 34)
    title = card([('PAE-02 · SCION 07 · Peter Foldès', 'f5.woff2', 64, ink),
                  ('drawn metamorphosis: the threshold, handmade', 'f27.woff2', 30, (70, 66, 70)),
                  ('a new work inspired by the lineage of Hunger (1974); not by or endorsed by Peter Foldès', 'f14.woff2', 17, (110, 104, 104))],
                 os.path.join(HERE, 'cache', 'title.png'))
    end = card([('What it is made of', 'f5.woff2', 44, ink),
                ('The dog, the person, the house and the dusk are key contour drawings, drawn here as coordinates.', 'f34.woff2', 22, ink),
                ('The dog was studied from the outline of the archive dog in Amateur Film New Jersey C (public domain).', 'f34.woff2', 22, ink),
                ('Every in-between is a blend of corresponding points between keys; turns pass through drawn views.', 'f34.woff2', 22, ink),
                ('The door\'s outline becomes the light on the boards. The paws are planted; they step.', 'f34.woff2', 22, ink),
                ('No footage, no photographs, no generated images. The voices and sounds are synthesized.', 'f34.woff2', 22, ink),
                ('The dog\'s choices follow the PAELEO threshold score; their onsets, measured from the drawing, are in trace.json.', 'f27.woff2', 22, (70, 66, 70))],
               os.path.join(HERE, 'cache', 'end.png'))
    # title: the first key contour draws itself on (pen travels the outline); end: hold
    for i in range(72):
        title.save(os.path.join(OUTD, '%04d.png' % i))
    for i in range(72):
        end.save(os.path.join(OUTD, '%04d.png' % (72 + 768 + i)))


if __name__ == '__main__':
    os.makedirs(OUTD, exist_ok=True)
    only = sys.argv[1:]
    if only and only[0] == '--chunk':
        # resumable: render the next N missing scene frames (this environment stops long single processes)
        n = int(only[1])
        have = set(os.listdir(OUTD))
        todo = [k for k in range(768) if '%04d.png' % (72 + k) not in have][:n]
        if not os.path.exists(os.path.join(OUTD, '0000.png')):
            cards()
        if todo:
            with Pool(4, initializer=init) as p:
                list(p.imap_unordered(render_frame, todo, chunksize=4))
        print('rendered', len(todo), 'frames this chunk')
        sys.exit()
    if only and only[0] == '--clean':
        for f in os.listdir(OUTD):
            os.remove(os.path.join(OUTD, f))
        sys.exit()
    if only:
        init()
        for a in only:
            render_frame(int(a))
        sys.exit()
    cards()
    with Pool(4, initializer=init) as p:
        n = 0
        for _ in p.imap_unordered(render_frame, range(768), chunksize=8):
            n += 1
            if n % 96 == 0:
                print('rendered', n, flush=True)
