"""Title card (written by the board), end card (the machine shown honestly: its states and transitions, its drive curves,
its choices against the score) and the spoken words as a destination-sign strip on the board during speech.
python3 cards.py -> cache/frames/t%04d.jpg (72), cache/frames/e%04d.jpg (72), captions burned into cache/frames/s%04d.jpg,
cache/card_flips.json"""
import json, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import render as R

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
FR = os.path.join(CACHE, 'frames')
FONTS = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'paeleo', 'fonts')
BIG = os.path.join(FONTS, 'f8.woff2')       # Big Shoulders Display 900
MONO = os.path.join(FONTS, 'f14.woff2')     # JetBrains Mono 400
DEJAVU_B = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'


def text_cells(lines, W=R.GW, H=R.GH):
    """lines: (text, font path, px size, y cell, x cell or None for centred) -> bool cell mask"""
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    for txt, fp, sz, y, x in lines:
        f = ImageFont.truetype(fp, sz)
        w = d.textlength(txt, font=f)
        d.text(((W - w) / 2 if x is None else x, y), txt, font=f, fill=255)
    return np.array(im) > 110


def board(state, em=None, flipm=None):
    if em is None:
        em = np.zeros(state.shape + (3,), np.float32)
    if flipm is None:
        flipm = np.zeros(state.shape, bool)
    return R.compose(state, em, flipm)


def title():
    SB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    m = text_cells([('PAE-02 · SCION 48', SB, 22, 34, None), ('STATE MACHINES', SB, 30, 66, None),
                    ('characters that can refuse', DEJAVU_B, 11, 122, None), ('the threshold', DEJAVU_B, 11, 138, None)])
    # a thin LED rule of dusk under the name
    em = np.zeros((R.GH, R.GW, 3), np.float32)
    rule = np.zeros((R.GH, R.GW), bool); rule[114, 60:260] = True
    em[rule] = np.array([1.0, 0.55, 0.25]) * 0.8
    prev = np.zeros((R.GH, R.GW), np.int8)
    counts = []
    for k in range(72):
        col = min(R.GW + 1, (k + 1) / 18 * R.GW)
        reveal = np.arange(R.GW)[None, :] < col
        st = np.where(m & reveal, 1, 0).astype(np.int8)
        rl = rule & (np.arange(R.GW)[None, :] < (k - 14) / 14 * R.GW)
        st[rl] = 2
        if k >= 66:   # the board clears for the scene
            st[:, :int((k - 65) / 6 * R.GW)] = 0
        flip = (st == 1) != (prev == 1)
        counts.append(int(flip.sum()))
        Image.fromarray(board(st, em, flip)).save(os.path.join(FR, f't{k:04d}.jpg'), quality=92)
        prev = st
    return counts


def end_card(M):
    b, _ = R.dog_body(M['frames'][0]['body'], 3.0, 0.0, 0.0)
    global NSEG
    NSEG = len(b.RA)
    W, H = 1280, 720
    img = Image.new('RGB', (W, H), (7, 7, 9))
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(BIG, 40); fm = ImageFont.truetype(MONO, 15); fs = ImageFont.truetype(MONO, 12)
    amber, warm, pale, grey = (236, 205, 112), (255, 150, 80), (215, 215, 205), (120, 120, 118)
    d.text((48, 26), 'WHAT IT IS MADE OF', font=fb, fill=amber)
    lines = ['A board of 320 x 180 flip-discs and LEDs, computed every frame:',
             'what gives light is lit (sky, room), what receives light is flipped.',
             f'The dog is not drawn: {NSEG} rounded segments posed by its own state',
             'machine, cast into discs. No footage; no keys for its choices:',
             'its 11 parameters were tuned (tune.py) until its own decisions',
             'fell on the score\'s times; the score\'s states are never an input.',
             'Voices formant-synthesized. Every flip clicks; a relay clacks',
             'each time the machine decides.']
    for k, ln in enumerate(lines):
        d.text((50, 84 + k * 21), ln, font=fm, fill=pale)
    # ---- state chart
    nodes = {'watch': (840, 120), 'retreat': (1130, 70), 'refuse': (1130, 190), 'approach': (840, 260), 'lie_down': (1080, 300)}
    for nm, (x, y) in nodes.items():
        d.rounded_rectangle((x - 62, y - 20, x + 62, y + 20), 9, outline=amber, width=2)
        d.text((x, y), nm, font=fm, fill=amber, anchor='mm')
    d.text((1080, 332), 'rest <-> look_in', font=fs, fill=warm, anchor='mm')
    tr = [e for e in M['events'] if e['e'] == 'transition']

    def arrow(a, b, label, off=0):
        (x0, y0), (x1, y1) = nodes[a], nodes[b]
        dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
        nx, ny = -uy * off, ux * off
        sx, sy = x0 + ux * 66 + nx, y0 + uy * 26 + ny
        ex, ey = x1 - ux * 66 + nx, y1 - uy * 26 + ny
        d.line((sx, sy, ex, ey), fill=pale, width=2)
        ang = math.atan2(ey - sy, ex - sx)
        for s in (2.6, -2.6):
            d.line((ex, ey, ex + 10 * math.cos(ang + s), ey + 10 * math.sin(ang + s)), fill=pale, width=2)
        lx, ly = sx + (ex - sx) * 0.42 + nx * 2.4, sy + (ey - sy) * 0.42 + ny * 2.4
        d.text((lx, ly), label, font=fs, fill=warm, anchor='mm')
    pairs = {(x['from'], x['to']) for x in tr}
    for e in tr:
        arrow(e['from'], e['to'], f"{e['t']:.2f}s", off=11 if (e['to'], e['from']) in pairs else 0)
    d.text((48, 262), 'utility per behaviour, every tick; the best wins', font=fs, fill=grey)
    d.text((48, 279), 'if it beats the current one by a margin, and the', font=fs, fill=grey)
    d.text((48, 296), 'current one has had its minimum time (danger may cut in).', font=fs, fill=grey)
    d.text((48, 313), 'the dog sees only where its head points; it hears all round.', font=fs, fill=grey)
    # ---- drive curves
    x0, x1, y0, y1 = 70, 1230, 400, 640
    d.rectangle((x0, y0, x1, y1), outline=(40, 40, 42))
    fr = M['frames']
    tx = lambda t: x0 + (x1 - x0) * t / 32
    ty = lambda v: y1 - (y1 - y0) * max(0, min(1, v))
    for nm, col in (('fear', (230, 90, 70)), ('trust', amber), ('curiosity', (120, 180, 230))):
        pts = [(tx(f['t']), ty(f['drives'][nm])) for f in fr]
        d.line(pts, fill=col, width=2)
    for k, (nm, col) in enumerate((('fear', (230, 90, 70)), ('trust', amber), ('curiosity', (120, 180, 230)))):
        d.text((x0 + 10 + k * 130, y0 - 22), nm, font=fm, fill=col)
    d.text((x0 + 420, y0 - 22), 'drives over the 32 s   |  machine choice    o score (+-0.25 s)', font=fs, fill=grey)
    for o in M['onsets'][:6]:
        if o['machine'] is not None:
            d.line((tx(o['machine']), y0, tx(o['machine']), y1), fill=(200, 200, 190), width=1)
        xs = tx(o['score'])
        d.ellipse((xs - 5, y1 + 6, xs + 5, y1 + 16), outline=pale, width=2)
        k6 = M['onsets'].index(o)
        d.text((tx(o['machine'] or o['score']), y1 + 20 + 12 * (k6 % 2)), o['to'], font=fs, fill=pale, anchor='mt')
    for s in range(0, 33, 4):
        d.text((tx(s), y1 + 48), f'{s}s', font=fs, fill=grey, anchor='mt')
    d.text((48, 694), 'PAE-02 · SCION 48 · state machines.  Rights: all computed here; fonts SIL OFL.', font=fs, fill=grey)
    return img


def captions():
    """the person's words on a strip of the board, bottom left, while they are spoken"""
    spans = [(1.05, 2.3, 'COME HERE.'), (3.42, 4.6, 'COME HERE. COME ON.'), (7.45, 9.4, "IT'S ALL RIGHT."),
             (10.45, 11.6, "IT'S ALL RIGHT."), (26.45, 27.5, 'COME IN.')]
    for a, b, txt in spans:
        m = text_cells([(txt, DEJAVU_B, 9, 0, 0)], 160, 12)
        ys, xs = np.nonzero(m)
        m = m[:ys.max() + 1, :xs.max() + 1]
        for i in range(int(round(a * 24)), int(round(b * 24))):
            fn = os.path.join(FR, f's{i:04d}.jpg')
            im = np.array(Image.open(fn))
            cx0, cy0 = 6, R.GH - 6 - m.shape[0]
            k = i - int(round(a * 24))
            n_show = min(len(txt), k + 1) if k < len(txt) else len(txt)
            colw = m.shape[1] * n_show / len(txt)
            reveal = np.arange(m.shape[1])[None, :] < colw + 1
            sub = np.zeros((m.shape[0] + 4, m.shape[1] + 4), np.int8)
            sub[2:-2, 2:-2] = (m & reveal).astype(np.int8)
            st = sub
            tile = R.compose(st, np.zeros(st.shape + (3,), np.float32), np.zeros(st.shape, bool)) if False else None
            # draw with the board's own discs
            big_on = np.repeat(np.repeat(st == 1, R.PITCH, 0), R.PITCH, 1)
            tf = np.tile(R.T_FULL, st.shape)
            col = np.where(big_on[..., None], R.ON_C, R.OFF_C)
            patch = R.BG_C[None, None] * (1 - tf[..., None]) + col * tf[..., None]
            y0, x0 = (cy0 - 2) * R.PITCH, (cx0 - 2) * R.PITCH
            im[y0:y0 + patch.shape[0], x0:x0 + patch.shape[1]] = (np.clip(patch, 0, 1) * 255).astype(np.uint8)
            Image.fromarray(im).save(fn, quality=92)


if __name__ == '__main__':
    M = json.load(open(os.path.join(CACHE, 'machine.json')))
    tc = title()
    e = end_card(M)
    ec = []
    prev = None
    for k in range(72):
        e.save(os.path.join(FR, f'e{k:04d}.jpg'), quality=94)
    ec = [3000 if k == 0 else 0 for k in range(72)]
    json.dump({'title': tc, 'end': ec}, open(os.path.join(CACHE, 'card_flips.json'), 'w'))
    captions()
    print('cards ok')
