"""Exercices de style: une gare, six faits, cinq manieres (SCION build round, direction 1 « Narré par la clé »).

One frozen incident (incident/ledger.json@rev) told five ways on one illustrated-book page grammar:
S0 title, S1 register (baseline), S2 reverse log, S3 sensory shadow theatre, S4 rigid notice, S5a-d the key
narrates (S5c = the approved test shot), S6 coverage matrix drawn from incident/coverage.json.

FORAGED (credits/exercices-de-style.json): Agence Rol 57642 walking man (Commons, PD) cut + articulated;
Edna C. Rex key watercolour (NGA, CC0); 1927 Berlin platform still (movingimagearchive.com, PD US);
bell strike from Communications and Our Town (1947) and room tone from Wreckless (1935) (movingimagearchive.com);
one footfall on gravel (Commons, Gravity Sound, CC BY 4.0); thud (Commons PD, gregoryweir).
HANDMADE: page, ghost words, type, band, strip, cut-paper bench / door / guichet / notice / stamp / envelope,
the straight-ahead tear, the silhouette puppet (rotoscoped from the walker's matte), arrows, the matrix.
KIT SYNTH (declared, nothing open was found): typewriter clicks, brass tick of the key, paper tear, pen scratch.

Motion: anim/exposure.json.  Text + timing: incident/anthology.json.  Library: anim/es_lib.py.  Rendered
through films/kit.py (unedited).  Run from the project root:
    python3 films/exercices-de-style.py                 -> assets/films/exercices-de-style.mp4
    python3 films/exercices-de-style.py --stills 2 8 30 -> films/stills/exercices-de-style/*.png
    python3 films/exercices-de-style.py --check         -> INV-DOOR + timing fixtures + verify.py only
    python3 films/exercices-de-style.py --sheets        -> beat-5 pair + aesthetic side-by-side sheets
"""
import sys, json, math, subprocess, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FILMS = Path(__file__).resolve().parent
SW = FILMS / 'swarm' / 'exercices-de-style'
sys.path.insert(0, str(SW / 'anim')); sys.path.insert(0, str(FILMS))
import kit
from kit import Film, ease, ramp, clamp
import es_lib as L
import test_shot_s5c as TS          # the approved S5c test shot (anim/), re-used verbatim as a shot

FPS = 24
W, H = L.W, L.H
ANTH = json.load(open(SW / 'incident' / 'anthology.json'))
COV = json.load(open(SW / 'incident' / 'coverage.json'))
LEDGER = json.load(open(SW / 'incident' / 'ledger.json'))
X = json.load(open(SW / 'anim' / 'exposure.json'))
V = TS.V
VAR = ANTH['variants']
SCHED = {s['shot']: (s['t0'], s['t1']) for s in ANTH['schedule']}
DUR = ANTH['schedule'][-1]['t1']                       # 74.25 s (timing_revision)
SRC = L.SRC
CLOCKS = {'E1': '18:00', 'E2': '18:02', 'E3': '18:04', 'E4': '18:05', 'E5': '18:06', 'E6': '18:07'}
EV = ['E1', 'E2', 'E3', 'E4', 'E5', 'E6']
CREAMY = (250, 244, 226)


def ix(v):
    return int(round(v))


def shot_at(t):
    for s in ANTH['schedule']:
        if s['t0'] <= t < s['t1']:
            return s['shot']
    return 'S6'


def beat_at(variant, t, default=0):
    """Index (0..5) of the event whose timing window holds t (latest started)."""
    idx = default
    for tm in VAR[variant]['timing']:
        if t >= tm['t_in']:
            idx = EV.index(tm['event'])
    return idx


def beat_at_rev(t):
    idx = None
    for tm in VAR['rev']['timing']:
        if t >= tm['t_in']:
            idx = EV.index(tm['event'])
    return 5 if idx is None else idx


# ------------------------------------------------------------------ puppet helpers
ARM = V.P['arm']
FINGER = tuple(X['S5c']['arm']['fingertip_src'])


def hand_pos(hip, sc, lean, arm):
    base = V.xf(hip, sc, lean, ARM['pivot'])
    v = L.R(lean + arm, (FINGER[0] - ARM['pivot'][0], FINGER[1] - ARM['pivot'][1]))
    return (base[0] + sc * v[0], base[1] + sc * v[1])


def pose_of(f):
    return dict(lean=f['lean'], head=f['head'], arm=f['arm'], hem=f['hem'],
                legs={'near': tuple(f['near']), 'far': tuple(f['far'])})


_env_small = {}
def small_envelope(opened):
    k = bool(opened)
    if k not in _env_small:
        w, h = 30, 20
        e = L.cut_paper([(1, 1), (w - 1, 1), (w - 1, h - 1), (1, h - 1)], CREAMY, 301, 0.7, size=(w, h))
        d = ImageDraw.Draw(e)
        if opened:
            d.polygon([(2, 2), (w - 2, 2), (w / 2, 0)], fill=(60, 40, 20, 255))
            d.line([(2, 3), (w / 2, 10), (w - 2, 3)], fill=(120, 96, 60, 255), width=1)
        else:
            d.line([(2, 2), (w / 2, 11), (w - 2, 2)], fill=(150, 120, 80, 255), width=1)
            d.ellipse([w / 2 - 3, 8, w / 2 + 3, 14], fill=L.RED + (255,))
        _env_small[k] = L.with_shadow(e, off=(1, 1), blur=1.2, alpha=0.3)
    return _env_small[k]


KEY_S1 = L.key(70)
KEY_HELD = L.key(34).rotate(70, expand=True, resample=Image.BICUBIC)

# ------------------------------------------------------------------ S1 stage (baseline): eye-level medium wide
S1X = X['S1']
DX1 = -60                                              # whole stage shifted left so the register has room
STATION = Image.open(SRC / 'forage' / 'station_berlin1927.png')
DECKLE = L.deckle(STATION, (214, 158))
BENCH_EYE = L.bench_eye(S1X['bench']['x'] + DX1, S1X['bench']['y'], S1X['bench']['w'])
DOOR_S1 = tuple(S1X['door_xy'])
S1_KEY = S1X['key_on_bench']


def s1_stage(lay, t):
    """bench + key + visitor (with envelope / key in hand) for S1 time t, drawn on an RGBA layer."""
    lay.alpha_composite(BENCH_EYE)
    if t >= S1_KEY['from_film_t']:
        lay.alpha_composite(L.with_shadow(KEY_S1, off=(1, 2), blur=2, alpha=0.3),
                            (S1_KEY['x'] + DX1, S1_KEY['y'] - KEY_S1.size[1]))
    k = ix(t * FPS)
    ks = sorted(int(x) for x in S1X['frames'])
    kk = min(max((k // 2) * 2, ks[0]), ks[-1])
    f = S1X['frames'][str(kk)]
    hip = (f['hip'][0] + DX1, f['hip'][1])
    V.draw(lay, hip, f['sc'], pose_of(f))
    hx, hy = hand_pos(hip, f['sc'], f['lean'], f['arm'])
    if t < 8.0:
        e = small_envelope(t >= 6.7)
        lay.alpha_composite(e, (ix(hx - 14), ix(hy - 6)))
    elif t < S1_KEY['from_film_t']:
        lay.alpha_composite(KEY_HELD, (ix(hx - KEY_HELD.size[0] / 2), ix(hy - KEY_HELD.size[1] + 6)))
    return hip


def wrap(d, text, fnt, width):
    out, cur = [], ''
    for w in text.split(' '):
        tst = (cur + ' ' + w).strip()
        if d.textlength(tst, font=fnt) <= width:
            cur = tst
        else:
            out.append(cur); cur = w
    if cur:
        out.append(cur)
    return out


def page_base(ghost_word, gx=0, gxy=(300, -170), gsize=560):
    img = L.page(1).convert('RGBA')
    g = L.ghost(ghost_word, gxy, gsize)
    img.alpha_composite(g.crop((ix(200 + gx), 0, ix(200 + gx) + W, H)))
    return img


def render_S1(t, strip=True):
    img = page_base('Gare')
    L.set_title(img, [('Le', L.RED), ('registre', L.BLACK)], x=30, base=70, size=48, seed=8)
    img.alpha_composite(DECKLE, (28, 96))
    L.paste_door(img, *DOOR_S1)
    s1_stage(img, t)
    d = ImageDraw.Draw(img); fnt = L.font(L.SERIF_R, 16); y = 96
    for c in VAR['baseline']['claims']:
        if c['t_in'] > t or c['id'] == 'baseline.7':
            continue
        txt = c['text'] + (' ' + VAR['baseline']['claims'][6]['text'] if c['id'] == 'baseline.6' else '')
        for ln in wrap(d, txt, fnt, 225):
            d.text((560, y), ln, font=fnt, fill=L.BLACK); y += 19
        y += 6
    b = beat_at('baseline', t)
    L.band(img, 'Le registre', VAR['baseline']['band']['label'], CLOCKS[EV[b]])
    if strip:
        L.strip(img, cells('S1'), ring=b)
    return img


# ------------------------------------------------------------------ S2 reverse log
TAB_BOX = (34, 108, 404, 316)                         # tableau card on the page
TAB_SRC = (190, 130, 670, 400)                        # S1 stage region (shifted coords) shown in the tableau
_tabcard = None
def tab_card():
    global _tabcard
    if _tabcard is None:
        w, h = TAB_BOX[2] - TAB_BOX[0], TAB_BOX[3] - TAB_BOX[1]
        _tabcard = L.with_shadow(L.cut_paper([(0, 0), (w, 0), (w, h), (0, h)], CREAMY, 401, 1.2, size=(w, h)),
                                 off=(3, 4), blur=4, alpha=0.3)
    return _tabcard


S1_BEATS = {b['event']: b for b in S1X['beats']}


def tableau(t1):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    s1_stage(lay, t1)
    w, h = TAB_BOX[2] - TAB_BOX[0] - 16, TAB_BOX[3] - TAB_BOX[1] - 16
    return lay.crop(TAB_SRC).resize((w, h), Image.LANCZOS)


def arrow_pts(x, y0, y1, bulge, u):
    """cause line y0 (lower) up to effect line y1: a hand-ruled arc bulging left; u = drawn fraction."""
    pts = []
    n = 24
    for i in range(int(n * u) + 1):
        s = i / n
        pts.append((x - bulge * math.sin(math.pi * s), y0 + (y1 - y0) * s))
    return pts


def render_S2(t, strip=True):
    v = VAR['rev']
    img = page_base('Rebours', gxy=(240, -170))
    L.set_title(img, [('Journal', L.RED), ('à', L.BLACK), ('rebours', L.RED)], x=30, base=70, size=46, seed=12)
    d = ImageDraw.Draw(img)
    d.text((30, 92), v['claims'][0]['text'].upper(), font=L.font(L.SANS, 12), fill=L.BLACK)
    img.alpha_composite(tab_card(), TAB_BOX[:2])
    cur = None
    for tm in v['timing']:
        if t >= tm['t_in']:
            cur = tm
    if cur is not None:
        u = min(t - cur['t_in'], tm_len(cur))
        t1 = S1_BEATS[cur['event']]['t_in'] + u                       # plays FORWARD inside the tableau
        img.alpha_composite(tableau(t1), (TAB_BOX[0] + 8, TAB_BOX[1] + 8))
        d.text((TAB_BOX[0] + 12, TAB_BOX[3] - 20), CLOCKS[cur['event']], font=L.font(L.MONO, 12), fill=L.BLACK)
    L.paste_door(img, *DOOR_S1)
    ys = v['log_line_y']; fnt = L.font(L.SERIF_R, 19); fst = L.font(L.MONO, 15)
    for c in v['claims'][1:]:
        if t < c['t_in']:
            continue
        ev = c['events'][0]; y = ys[ev]
        stamp, body = c['text'].split(' · ', 1)
        d.text((540, y), stamp, font=fst, fill=L.RED, anchor='lm')
        n = len(body) if t >= c['t_type_end'] else int((t - c['t_in']) * c['cps'])
        d.text((600, y), body[:n], font=fnt, fill=L.BLACK, anchor='lm')
    for i, a in enumerate(v['arrows']):
        if t < a['t_in']:
            continue
        u = clamp((t - a['t_in']) / (a['t_drawn'] - a['t_in']))
        u = math.floor(u * 8) / 8                                       # 8 drawings, one per frame
        x = 526 if a['style'] == 'solid' else 500
        bulge = (8 + 9 * abs(a['y_from'] - a['y_to']) / 30) * (1.0 if a['style'] == 'solid' else 1.6)
        pts = arrow_pts(x, a['y_from'], a['y_to'], bulge, u)
        if len(pts) > 1:
            if a['style'] == 'dotted':                                # round dots every 7 px of arc: plainly not a ruled line
                acc, last = 7.0, pts[0]
                for q in pts[1:] if len(pts) > 1 else []:
                    for j in range(1, 9):
                        p_ = (last[0] + (q[0] - last[0]) * j / 8, last[1] + (q[1] - last[1]) * j / 8)
                        acc += math.hypot(q[0] - last[0], q[1] - last[1]) / 8
                        if acc >= 7.0:
                            d.ellipse([p_[0] - 2, p_[1] - 2, p_[0] + 2, p_[1] + 2], fill=L.RED); acc = 0.0
                    last = q
            else:
                d.line(pts, fill=L.RED, width=2, joint='curve')
        if u >= 1:
            ex, ey = pts[-1]
            d.polygon([(ex, ey - 1), (ex - 5, ey + 8), (ex + 5, ey + 8)], fill=L.RED)   # head points UP at the effect
            if a['label']:
                d.text((x - bulge - 8, (a['y_from'] + a['y_to']) / 2), a['label'], font=L.font(L.SERIF_I, 16), fill=L.RED, anchor='rm')
    b = beat_at_rev(t)
    L.band(img, 'Journal à rebours', v['band']['label'], CLOCKS[EV[b]])
    if strip:
        L.strip(img, cells('S2'), ring=b)
    return img


def tm_len(tm):
    return tm['t_out'] - tm['t_in']


# ------------------------------------------------------------------ S3 sensory inventory (shadow theatre)
S3X = X['S3']
SIL = V.silhouette_pieces()
PANE = L.frosted_pane((360, 250))
GUI = L.guichet((440, 330), (40, 62, 400, 312))
GUI_XY, GUI_S = (36, 100), 0.8
CARD3 = L.with_shadow(L.cut_paper([(0, 0), (520, 0), (520, 254), (0, 254)], CREAMY, 501, 1.2, size=(520, 254)),
                      off=(3, 4), blur=4, alpha=0.3)
S3K = sorted(int(x) for x in S3X['frames'])


def _card_whole(hx, hy):                  # the envelope held out by one corner: 40 x 26 px card, clear of the coat
    return [(hx - 6, hy - 4), (hx + 34, hy - 8), (hx + 37, hy + 18), (hx - 3, hy + 22)]


def _card_torn(hx, hy):                   # the top strip torn off: a jagged upper edge
    return [(hx - 5, hy + 4), (hx + 3, hy + 1), (hx + 10, hy + 4), (hx + 17, hy), (hx + 24, hy + 3), (hx + 30, hy - 1),
            (hx + 35, hy + 1), (hx + 37, hy + 18), (hx - 3, hy + 22)]


ENV_CARD = {'whole': _card_whole, 'torn': _card_torn}


def s3_window(t):
    k = ix(t * FPS)
    kk = min(max((k // 2) * 2, S3K[0]), S3K[-1])
    fr = S3X['frames'][str(kk)]
    head = S3X['bell_head_on_ones'].get(str(k), fr['head'])          # the bell reaction is on ones
    rise = S3X['bell_rise_on_ones'].get(str(k), 0.0)                  # ... and the whole body starts with it
    hip = (fr['hip'][0], fr['hip'][1] + rise)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    SIL.draw(lay, hip, fr['sc'], dict(pose_of(fr), head=head), shadow=False)
    if fr.get('envelope'):                                            # a flat black card on the hand pin (Reiniger)
        hx, hy = hand_pos(hip, fr['sc'], fr['lean'], fr['arm'])
        ImageDraw.Draw(lay).polygon(ENV_CARD[fr['envelope']](hx, hy), fill=(12, 10, 8, 255))
    p = S3X['pane']
    m = lay.getchannel('A').crop((p['x'], p['y'], p['x'] + 360, p['y'] + 250))
    lit = L.shadow_through_glass(PANE, m, blur=fr['blur_px'])
    if fr.get('glint', 0) > 0:                                        # E4: a brief glint, never a key shape
        hx, hy = hand_pos(tuple(fr['hip']), fr['sc'], fr['lean'], fr['arm'])
        gl = Image.new('L', (360, 250), 0)
        ImageDraw.Draw(gl).ellipse([hx - p['x'] - 5, hy - p['y'] - 5, hx - p['x'] + 5, hy - p['y'] + 5], fill=255)
        gl = gl.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * fr['glint']))
        lit = Image.composite(Image.new('RGB', (360, 250), (255, 252, 236)), lit, gl)
    g = Image.new('RGBA', (440, 330), (0, 0, 0, 0)); g.paste(lit, (40, 62)); g.alpha_composite(GUI)
    g = g.resize((ix(440 * GUI_S), ix(330 * GUI_S)), Image.LANCZOS)
    return L.with_shadow(g, off=(3, 4), blur=4, alpha=0.3)


def render_S3(t, strip=True):
    v = VAR['sense']
    img = page_base('Sens', gxy=(330, -170))
    L.set_title(img, [('Inventaire', L.RED), ('des', L.BLACK), ('sens', L.RED)], x=30, base=70, size=44, seed=21)
    img.alpha_composite(s3_window(t), GUI_XY)
    img.alpha_composite(CARD3, (418, 100))
    d = ImageDraw.Draw(img); fnt = L.font(L.MONO, 14); y = 124
    d.text((432, 112), 'GUICHET 3 · RELEVÉ', font=L.font(L.SANS, 11), fill=L.BLACK, anchor='lm')
    for c in v['claims']:
        if t < c['t_in']:
            continue
        col = L.RED if c['kind'] == 'omit' else L.BLACK
        f = L.font(L.MONO, 14 if c['kind'] != 'omit' else 15)
        for ln in wrap(d, c['text'], f, 490):
            d.text((432, y), ln, font=f, fill=col); y += 22
        y += 4
    b = beat_at('sense', t)
    L.band(img, 'Inventaire des sens', v['band']['label'], CLOCKS[EV[b]])
    if strip:
        L.strip(img, cells('S3'), ring=b)
    return img


# ------------------------------------------------------------------ S4 rigid notice
S4X = X['S4']
CARD_XY = (226, 30)
CARD_SIZE = (720, 330)
ROWS = [[f.strip() for f in c['text'].split('|')] for c in VAR['notice']['claims'] if c['role'] == 'row']
FIELD_T = [c['field_times'] for c in VAR['notice']['claims'] if c['role'] == 'row']
KEY_S4 = L.key(S4X['key_length'])
KEY_REST = (765, 418)                                  # bottom-left of the key's box when resting (clipped to card bottom)
_notice_cache = {}


def notice_img(t):
    filled = []
    for r, row in enumerate(ROWS):
        filled.append([val if t >= FIELD_T[r][i] else '' for i, val in enumerate(row)])
    showfoot = t >= [c for c in VAR['notice']['claims'] if c['role'] == 'footnote'][0]['t_in']
    k = (json.dumps(filled), showfoot)
    if k not in _notice_cache:
        _notice_cache[k] = L.notice(filled, size=CARD_SIZE, footnote=VAR['notice']['claims'][-2]['text'] if showfoot else '')
    return _notice_cache[k]


def render_S4(t, strip=True):
    v = VAR['notice']
    img = page_base('Avis', gxy=(360, -170))
    L.set_title(img, [('Avis', L.RED)], x=30, base=70, size=54, seed=31)
    if t >= v['claims'][0]['t_in']:
        img.alpha_composite(notice_img(t), CARD_XY)
    k = ix(t * FPS); ks = sorted(int(x) for x in S4X['frames'])
    if k >= ks[0]:
        f = S4X['frames'][str(min(k, ks[-1]))]
        kimg = KEY_S4.rotate(f['a'], expand=True, resample=Image.BICUBIC)
        x, y = KEY_REST[0], KEY_REST[1] + f['dy'] - kimg.size[1]
        img.alpha_composite(L.with_shadow(kimg, off=(2, 3), blur=2.5, alpha=0.32), (ix(x), ix(y)))
        if k >= S4X['clink_frame']:                                     # the drawn paper clip goes on after it lands
            d = ImageDraw.Draw(img); cx = KEY_REST[0] + 30; cy = CARD_XY[1] + CARD_SIZE[1] - 18
            d.rounded_rectangle([cx, cy, cx + 14, cy + 52], radius=7, outline=(90, 88, 84), width=2)
            d.rounded_rectangle([cx + 4, cy + 8, cx + 11, cy + 44], radius=4, outline=(120, 118, 112), width=2)
    st = S4X['stamp']
    if t >= st['t']:
        i = ix((t - st['t']) * FPS)
        sq = st['squash_frames'][i] if i < len(st['squash_frames']) else 0.0
        s = L.stamp(squash=sq, size=st['size'], angle=st['angle'])
        img.alpha_composite(s, (ix(st['xy'][0] - s.size[0] / 2), ix(st['xy'][1] - s.size[1] / 2)))
    b = beat_at('notice', t)
    L.band(img, 'Avis', v['band']['label'], CLOCKS[EV[b]])
    if strip:
        L.strip(img, cells('S4'), ring=b)
    return img


# ------------------------------------------------------------------ S5a/b: inside the envelope, the tear
KV = VAR['key']
ENV = L.envelope_interior((W, L.BAND_Y), lamp=1.0).convert('RGBA')
TEAR = L.Tear(X['S5b']['tear']['n_frames'], (W, L.BAND_Y), seed=X['S5b']['tear']['seed'], y=X['S5b']['tear']['y'])
TEAR_T0 = X['S5b']['tear']['start_t']
LIT = L.page(1).convert('RGBA')
GHOST_DARK = Image.new('RGBA', (W + 400, H), (0, 0, 0, 0))
ImageDraw.Draw(GHOST_DARK).text((150, -200), 'Je', font=L.font(L.SERIF_R, 660), fill=(243, 228, 196, 26))
CAP_F = L.font(L.SERIF_I, 24)
S5_LINES = [c for c in KV['claims'] if c['t_in'] < SCHED['S5c'][0]]
TEAR_END = TEAR_T0 + X['S5b']['tear']['n_frames'] / FPS
SLIDE = (55.0, SCHED['S5c'][0])                        # the hand pulls the key (us) out of the envelope


def typed(text, t, t_in, t_end, cps):
    if t >= t_end:
        return text
    n = int((t - t_in) * cps)
    shown, cum = [], 0
    for w in text.split(' '):
        cum += len(w) + (1 if shown else 0)
        if cum <= n + 1:
            shown.append(w)
    return ' '.join(shown)


def render_S5ab(t, strip=True):
    img = LIT.copy()
    env = ENV.copy()
    env.alpha_composite(GHOST_DARK.crop((200, 0, 200 + W, L.BAND_Y)))
    slide = ease(t, *SLIDE) * (L.BAND_Y + 40)
    if t >= TEAR_T0:                                   # straight-ahead tear: re-cut every 2 frames, light through it
        k = ix((t - TEAR_T0) * FPS)
        m, fringe = TEAR.mask(k)
        fr = Image.new('RGBA', env.size, (236, 214, 170, 255))
        env.paste(fr, (0, 0), fringe)
        hole = Image.new('RGBA', env.size, (0, 0, 0, 0))
        env.paste(hole, (0, 0), m)
    img.alpha_composite(env, (0, ix(slide)))
    if t >= TEAR_END + 0.2:                            # the hand reaches in through the opening, toward us (the key)
        u = ease(t, TEAR_END + 0.2, SLIDE[0])
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        tip = (470 - 20 * u, 150 + 70 * u - 120 * ease(t, *SLIDE))
        L.place(lay, ARM['img'], ARM['origin'], FINGER, tip, 24 + 10 * (1 - u), 0.8 + 0.9 * u)
        img.alpha_composite(L.lift_shadow(lay, (4, 5), 5, 0.3)); img.alpha_composite(lay)
    L.set_title(img, [('Narré', L.RED), ('par', (236, 214, 170) if slide < 60 else L.BLACK), ('la', L.RED),
                      ('clé', (236, 214, 170) if slide < 60 else L.BLACK)], x=30, base=70, size=48, seed=5)
    d = ImageDraw.Draw(img)
    cx, lead = X['S5c']['captions']['x'], X['S5c']['captions']['lead']
    cy = 290                                           # below the tear line, on the envelope paper
    lines = [c for c in S5_LINES if (c['t_out'] <= SCHED['S5b'][0] + 0.01) == (t < SCHED['S5b'][0])]
    for i, c in enumerate(lines):
        if t < c['t_in']:
            continue
        box = np.asarray(img.convert('L').crop((cx, cy + i * lead, cx + 420, cy + i * lead + 30)), np.float32)
        col = (243, 228, 196) if np.median(box) < 150 else L.BLACK      # cream on the envelope, black on the page
        d.text((cx, cy + i * lead), typed(c['text'], t, c['t_in'], c['t_type_end'], c['cps']), font=CAP_F, fill=col)
    b = beat_at('key', t)
    L.band(img, 'Narré par la clé', KV['band']['label'], CLOCKS[EV[b]])
    if strip:
        L.strip(img, cells('S5'), ring=b)
    return img


# ------------------------------------------------------------------ S5c/S5d: the test shot (approved), then the hold
T5 = SCHED['S5c'][0]


def render_S5cd(t, strip=True):
    tl = t - T5
    img = TS.render(tl, ix(tl * FPS), with_strip=False)
    b = beat_at('key', t)
    L.band(img, 'Narré par la clé', KV['band']['label'], CLOCKS[EV[b]])
    if strip:
        ring = 5 if t >= SCHED['S5d'][0] else b
        L.strip(img, cells('S5'), ring=ring)
    return img


# ------------------------------------------------------------------ S0 title, S6 matrix
def render_S0(t, strip=True):
    pt = ANTH['page_text']['S0']
    img = page_base('Gare', gx=-20 * ease(t, 0, 3.0), gxy=(300, -170))
    n = int((t - pt['title']['t_in']) * pt['title']['cps']) if t >= pt['title']['t_in'] else 0
    words = pt['title']['text'].split(' ')
    cols = [L.RED if c.lower() == '#d6280a' else L.BLACK for c in pt['title']['colour_by_word']]
    L.set_title(img, list(zip(words, cols)), x=300, base=230, size=66, seed=2, letters=n)
    L.band(img, pt['band'], '', None)
    if strip:
        blank = Image.new('RGB', (64, 64), L.PAGE_TOP)
        L.strip(img, [blank] * 6, ring=None)
    return img


MATRIX = COV['matrix']
CELL_T0 = SCHED['S6'][0] + 0.4
MFONT = L.font('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)   # has the check mark glyph


def render_S6(t, strip=True):
    pt = ANTH['page_text']['S6']
    img = page_base(pt['ghost'], gxy=(120, -170))
    L.set_title(img, [('Matrice', L.RED)], x=30, base=70, size=50, seed=41)
    d = ImageDraw.Draw(img)
    x0, y0, cw0, cw, rh = 40, 100, 170, 146, 32
    cols = MATRIX['columns']
    d.line([(x0, y0 + rh - 4), (x0 + cw0 + cw * len(cols), y0 + rh - 4)], fill=L.BLACK, width=2)
    for j, c in enumerate(cols):
        d.text((x0 + cw0 + cw * j + cw / 2, y0 + 12), c, font=L.font(L.SERIF_B, 18), fill=L.BLACK, anchor='mm')
    n = 0
    for i, row in enumerate(MATRIX['rows']):
        y = y0 + rh * (i + 1) + 12
        d.text((x0, y), row['label'], font=L.font(L.SERIF_R, 17), fill=L.BLACK, anchor='lm')
        d.line([(x0, y + rh / 2 - 2), (x0 + cw0 + cw * len(cols), y + rh / 2 - 2)], fill=(150, 120, 70), width=1)
        for j, c in enumerate(cols):
            cell = row['cells'][c]
            if t >= CELL_T0 + 0.08 * n:
                cx = x0 + cw0 + cw * j + cw / 2
                red = cell['circle_red']
                d.text((cx, y), cell['mark'], font=MFONT, fill=L.RED if red else L.BLACK, anchor='mm')
                if red:
                    tw = d.textlength(cell['mark'], font=MFONT)
                    d.ellipse([cx - tw / 2 - 8, y - 12, cx + tw / 2 + 8, y + 12], outline=L.RED, width=2)
            n += 1
    d.text((40, 352), "photographies d'archives (Agence Rol, 1920 ; Berlin, 1927) : rôles inventés", font=L.font(L.SANS, 13), fill=(96, 76, 40))
    L.band(img, pt['band'], 'EXERCICE 6 · COUVERTURE', None)
    if strip:
        L.strip(img, cells('S6'), ring=None)
    return img


# ------------------------------------------------------------------ strip cells: each episode's own beat frames
_cells = {}
CELL_BEATS = {
    'S1': [(3.9, 'hip'), (5.6, 'hip'), (7.2, 'hip'), (8.8, 'hip'), (10.4, 'key'), (12.2, 'hip')],
}


def crop_sq(img, cx, cy, s):
    x0, y0 = ix(cx - s / 2), ix(cy - s / 2)
    x0 = max(0, min(W - s, x0)); y0 = max(0, min(L.BAND_Y - s, y0))
    return img.convert('RGB').crop((x0, y0, x0 + s, y0 + s))


def cells(ep):
    if ep in _cells:
        return _cells[ep]
    if ep == 'S5':
        _cells[ep] = TS.cells(); return _cells[ep]
    out = []
    if ep == 'S1':
        for tt, what in CELL_BEATS['S1']:
            im = render_S1(tt, strip=False)
            if what == 'key':
                out.append(crop_sq(im, S1_KEY['x'] + DX1 + 30, S1_KEY['y'] - 30, 150))
            else:
                f = S1X['frames'][str((ix(tt * FPS) // 2) * 2)]
                out.append(crop_sq(im, f['hip'][0] + DX1, f['hip'][1] - 40, 190))
    elif ep == 'S2':
        for tm in VAR['rev']['timing']:
            im = render_S2(tm['t_out'] - 0.05, strip=False)
            out.append(crop_sq(im, (TAB_BOX[0] + TAB_BOX[2]) / 2, (TAB_BOX[1] + TAB_BOX[3]) / 2, 220))
        out = out[::-1]                                  # cells stay in event order; the cursor walks 6 -> 1
    elif ep == 'S3':
        for tm in VAR['sense']['timing']:
            im = render_S3((tm['t_in'] + tm['t_out']) / 2, strip=False)
            out.append(crop_sq(im, GUI_XY[0] + 176, GUI_XY[1] + 140, 230))
    elif ep == 'S4':
        im = render_S4(45.5, strip=False)
        for r in range(6):
            out.append(crop_sq(im, CARD_XY[0] + 120 + 80 * r, CARD_XY[1] + 90 + 36 * r, 150))
    elif ep == 'S6':
        out = [cells('S1')[4], cells('S2')[4], cells('S3')[3], cells('S4')[4], cells('S5')[4]]
        dd = Image.new('RGBA', (200, 320), L.PAGE + (255,)); dd.alpha_composite(L.door(), (25, 10))
        out.append(dd.convert('RGB').crop((0, 0, 200, 200)))
    _cells[ep] = out
    return out


# ------------------------------------------------------------------ dispatch + page-turn wipe
RENDER = {'S0': render_S0, 'S1': render_S1, 'S2': render_S2, 'S3': render_S3, 'S4': render_S4,
          'S5a': render_S5ab, 'S5b': render_S5ab, 'S5c': render_S5cd, 'S5d': render_S5cd, 'S6': render_S6}
TURNS = [SCHED[s][0] for s in ('S1', 'S2', 'S3', 'S4', 'S5a', 'S6')]   # page-turn wipes between episodes
WIPE = 8
_last = {}


def render(t):
    s = shot_at(t)
    img = RENDER[s](t)
    for tb in TURNS:
        if tb <= t < tb + WIPE / FPS:
            if tb not in _last:
                tp = tb - 1 / FPS
                _last[tb] = RENDER[shot_at(tp)](tp).convert('RGB')
            u = ease(t, tb, tb + WIPE / FPS)
            edge = ix(W * (1 - u))
            old = _last[tb].copy()
            sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rectangle([max(0, edge - 22), 0, edge, H], fill=90)
            sh = sh.filter(ImageFilter.GaussianBlur(8))
            old = Image.composite(Image.new('RGB', (W, H), (60, 40, 10)), old, sh)
            new = img.convert('RGB')
            old.paste(new.crop((edge, 0, W, H)), (edge, 0))
            return old
    return img.convert('RGB')


# ------------------------------------------------------------------ sound (decoded foraged recordings + declared kit synth)
R = kit.RATE


def decode(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'f32le', '-ac', '1', '-ar', str(R), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


FR = SRC / 'forager-cutout-rigger'
BELL_ONSET = 0.065                                       # strike onset inside bell_strike_mia.wav (measured, 10 ms RMS)


def sound(mix):
    bell = decode(FR / 'bell_strike_mia.wav'); bell /= np.abs(bell).max()
    room = decode(FR / 'room_tone_wreckless1935.wav')
    steps = decode(SRC / 'editor' / 'footstep_gravel.wav')   # Gravity Sound, CC BY 4.0 (repair 1: replaces the BY-SA steps)
    thud = decode(FR / 'thud_dull.wav'); thud /= np.abs(thud).max()
    lp = mix.lowpass

    # room tone: the Wreckless optical-track bed, looped with crossfades, from 0 to the declared silence at 71.25
    seg = room[int(2.0 * R): int(22.0 * R)]
    seg = seg / (np.sqrt(np.mean(seg ** 2)) + 1e-9) * 0.012
    silence = ANTH['page_text']['S6']['declared_silence_from']
    bed = np.zeros(int(silence * R)); pos = 0; xf = int(1.0 * R)
    while pos < len(bed):
        n = min(len(seg), len(bed) - pos); s2 = seg[:n].copy()
        if pos > 0:
            s2[:xf] *= np.linspace(0, 1, xf)
        if n == len(seg):
            s2[-xf:] *= np.linspace(1, 0, xf)
        bed[pos:pos + n] += s2; pos += len(seg) - xf
    bed[:int(2.0 * R)] *= np.linspace(0, 1, int(2.0 * R))                 # S0: room tone fades in
    bed[-int(0.25 * R):] *= np.linspace(1, 0, int(0.25 * R))
    mix.add(bed, 0.0, 1.0, -0.05)

    def bell_at(t, gain=0.5, cut=None, pan=0.15, strokes=3, gap=0.9):
        for i in range(strokes):
            b = bell if cut is None else lp(bell, cut)
            mix.add(b, t - BELL_ONSET + i * gap, gain * (1 - 0.15 * i), pan)

    grain = steps[int(0.085 * R): int(0.40 * R)].copy()           # the one recorded footfall (onset 0.09 s measured)
    grain[:int(0.003 * R)] *= np.linspace(0, 1, int(0.003 * R)); grain[-int(0.05 * R):] *= np.linspace(1, 0, int(0.05 * R))
    def step(t, gain=0.4, cut=None, pan=0.0, i=0):
        rate = (0.90, 1.06, 0.96, 1.10, 0.93, 1.02, 0.98)[i % 7]    # each footfall resampled a little: no two identical
        n = int(len(grain) / rate)
        g = np.interp(np.arange(n) * rate, np.arange(len(grain)), grain); g /= (np.abs(g).max() + 1e-9)
        if cut:
            g = lp(g, cut)
        mix.add(g, t, gain, pan)

    def tear(t, seconds=1.2, gain=0.22, cut=None):    # KIT SYNTH (declared): fibre crackle, no open recording found
        n = int(seconds * R); x = np.zeros(n); rs = np.random.RandomState(int(t * 100))
        k = 0
        while k < n - 400:
            ln = rs.randint(60, 380); x[k:k + ln] += mix.rs.normal(0, 1, ln) * np.exp(-np.linspace(0, 5, ln)) * rs.uniform(0.3, 1)
            k += rs.randint(80, 700)
        x = mix.band(x, 900, 7000 if cut is None else cut) * mix.env(n, 0.02, 0.1, 0.8, 0.25)
        mix.add(x / (np.abs(x).max() + 1e-9), t, gain, 0.05)

    def scratch(t, seconds=0.33, gain=0.06):          # KIT SYNTH: pen on paper
        n = int(seconds * R); x = mix.band(mix.noise(seconds), 2500, 8000)
        x *= (0.6 + 0.4 * np.sin(np.linspace(0, 40, n))) * mix.env(n, 0.02, 0.05, 1.0, 0.05)
        mix.add(x / (np.abs(x).max() + 1e-9), t, gain, 0.25)

    def tick(t, gain=0.2, cut=None):                  # KIT SYNTH: brass on wood
        mix.click(t, gain, -0.1, bright=7500 if cut is None else cut, seconds=0.025)

    # S1 baseline: full point of hearing
    for i, c in enumerate(S1X['walk_in_contacts']):
        step(c, 0.38 * (0.6 + 0.4 * i / 6), pan=0.4 - 0.08 * i, i=i)
    bell_at(VAR['baseline']['sound'][1]['t'], 0.55)
    tear(VAR['baseline']['sound'][2]['t'])
    tick(S1_KEY['from_film_t'], 0.18); mix.add(thud[int(0.03 * R):], S1_KEY['from_film_t'], 0.18, -0.1)
    for i, c in enumerate(S1X['walk_out_contacts']):
        step(c, 0.38 * (1 - 0.15 * i), pan=-0.1 - 0.12 * i, i=i + 3)

    # S2 reverse log: the same events in REVERSE ORDER, each played forward
    for s in VAR['rev']['sound']:
        t = s['t']
        if s['event'] == 'E6':
            for i in range(3):
                step(t + 0.42 * i, 0.36 * (1 - 0.2 * i), pan=-0.1 - 0.15 * i, i=i)
        elif s['event'] == 'E5':
            tick(t, 0.18); mix.add(thud[int(0.03 * R):], t, 0.18, -0.1)
        elif s['event'] == 'E3':
            tear(t)
        elif s['event'] == 'E2':
            bell_at(t, 0.5)
        elif s['event'] == 'E1':
            for i in range(3):
                step(t + 0.42 * i, 0.22 + 0.06 * i, pan=0.4 - 0.1 * i, i=i + 4)
    for a in VAR['rev']['arrows']:
        scratch(a['t_in'], a['t_drawn'] - a['t_in'])

    # S3 through glass: everything low-passed; the bell onset lands on the head-up frame
    GL = 1300
    for i in range(3):
        step(24.2 + 0.42 * i, 0.22, GL, 0.3, i)
    bell_at(S3X['bell_onset_frame'] / FPS, 0.32, cut=GL)
    tear(28.2, cut=GL, gain=0.12)
    tick(30.8, 0.12, cut=1800); mix.add(lp(thud[int(0.03 * R):], GL), 30.8, 0.15, -0.1)
    for i in range(3):
        step(32.0 + 0.42 * i, 0.2 * (1 - 0.25 * i), GL, -0.2 - 0.15 * i, i + 2)

    # S4 notice: typewriter per field + the stamp; NO bell (declared in the grid footnote)
    for ft in FIELD_T:
        for x in ft:
            mix.click(x, 0.16, 0.1, bright=5200, seconds=0.02)
    tick(S4X['clink_frame'] / FPS, 0.16)
    mix.add(thud[int(0.03 * R):], VAR['notice']['claims'][-1]['t_in'], 0.6, 0.0)

    # S5a muffled through the paper; S5b the tear unmuffles
    for i in range(3):
        step(46.2 + 0.42 * i, 0.3, 300, 0.0, i)
    bell_at(KV['sound'][1]['t'], 0.6, cut=420)
    tear(TEAR_T0, seconds=TEAR_END - TEAR_T0, gain=0.3)

    # S5c the test shot's own mix (landing thud + tick on the contact frame; steps on foot contacts, receding)
    S = X['S5c']
    tland = T5 + S['key_contact_frame'] / FPS
    mix.add(thud[int(0.030 * R): int(0.33 * R)], tland, 0.55, -0.1)
    tick(tland, 0.22); mix.click(tland + 4 / FPS, 0.06, -0.1, bright=7000, seconds=0.015)
    cts = S['contacts']
    for i, tc in enumerate(cts):
        dist = i / max(1, len(cts) - 1)
        step(T5 + tc, 0.42 * (1 - 0.75 * dist), 5200 * (1 - 0.7 * dist), 0.2 - 0.7 * dist, i)

    # S6 one stroke at the matrix, then declared silence
    bell_at(ANTH['page_text']['S6']['bell_stroke_t'] + BELL_ONSET, 0.5, strokes=1)
    mix.L[int(silence * R):] = 0; mix.R[int(silence * R):] = 0
    SOUND_LOG.update(landing=tland, s3_bell=S3X['bell_onset_frame'] / FPS, silence=silence)


SOUND_LOG = {}

# ------------------------------------------------------------------ invariants + fixtures (asserted)
DOOR = L.door()
DOOR_A = np.asarray(DOOR.getchannel('A')) == 255


def door_expected(occluded_rows=None):
    a = DOOR_A.copy()
    if occluded_rows is not None:
        a[occluded_rows:] = False
    return hashlib.sha256(np.asarray(DOOR.convert('RGB'))[a].tobytes()).hexdigest()[:16]


def door_box(t):
    s = shot_at(t)
    if s in ('S1', 'S2'):
        return (DOOR_S1[0], DOOR_S1[1], DOOR_S1[0] + 150, DOOR_S1[1] + 300), None
    if s in ('S5c', 'S5d'):
        dx = X['S5c']['door_xy'][0] + TS.DOOR_SIGN * TS.ix(0.55 * TS.cam(t - T5))
        y = X['S5c']['door_xy'][1]
        assert y + 300 <= X['S5c']['bench_top'] - 14, 'S5c door must sit wholly above the bench lip (one hash)'
        return (dx, y, dx + 150, y + 300), None
    return None, None


def check_door(t, img):
    if any(tb <= t < tb + WIPE / FPS for tb in TURNS):
        return None
    box, occ = door_box(t)
    if box is None or box[2] > W:
        return None
    a = DOOR_A.copy()
    if occ is not None:
        a[occ:] = False
    got = hashlib.sha256(np.asarray(img.convert('RGB').crop(box))[a].tobytes()).hexdigest()[:16]
    exp = door_expected(occ)
    assert got == exp, f'INV-DOOR broken at {t:.3f}s: {got} != {exp}'
    return got


def timing_fixtures():
    sc = ANTH['schedule']
    assert abs(sc[0]['t0']) < 1e-9 and all(abs(a['t1'] - b['t0']) < 1e-6 for a, b in zip(sc, sc[1:])), 'shots not contiguous'
    assert 60.0 <= DUR <= 75.0, DUR
    stamps = [c['stamp'] for c in VAR['rev']['claims'] if c.get('role') == 'log']
    assert stamps == sorted(stamps, reverse=True) and len(set(stamps)) == 6, 'reverse log timestamps must strictly decrease'
    for a in VAR['rev']['arrows']:
        assert a['y_from'] > a['y_to'], 'arrows must be drawn UP from cause to effect'
        assert VAR['rev']['log_line_y'][a['from']] == a['y_from'] and VAR['rev']['log_line_y'][a['to']] == a['y_to']
    edges = {(e['from'], e['to']) for e in LEDGER['edges']}
    assert {(a['from'], a['to']) for a in VAR['rev']['arrows']} == edges
    head_k = min(int(k) for k, v in S3X['bell_head_on_ones'].items() if v != 0.0)
    assert abs(head_k - S3X['bell_onset_frame']) <= 2, 'S3 head-up must start within 2 frames of the bell'
    np_ = [c for c in VAR['sense']['claims'] if c['kind'] == 'omit'][0]
    assert np_['t_out'] - np_['t_in'] >= 2.0
    assert all('clé' not in c['text'] for c in VAR['sense']['claims'])
    first_field = min(min(ft) for ft in FIELD_T)
    assert first_field - VAR['notice']['claims'][0]['t_in'] >= 1.0, 'empty grid must show >= 1 s'
    assert all(len(r) == 6 for r in ROWS)
    S = X['S5c']
    land = T5 + S['key_contact_frame'] / FPS
    assert abs(land - KV['test_shot']['landing_s']) <= 2 / FPS + 1e-6, (land, KV['test_shot']['landing_s'])
    still = T5 + S['key_settle']['still_from_frame'] / FPS
    assert still <= KV['test_shot']['settle_done_by_s'], (still, KV['test_shot']['settle_done_by_s'])
    keys = [S['key'][str(k)] for k in range(S['key_contact_frame'], S['key_last'] + 1)]
    assert len({(round(k['a'], 2), round(k['y'], 2)) for k in keys}) >= 8, 'settle needs >= 8 distinct frames'
    cts = S['contacts']; assert len(cts) >= 4
    hs = [S['visitor'][str(k)]['sc'] for k in sorted(int(x) for x in S['visitor']) if S['visitor'][str(k)]]
    assert all(b <= a + 1e-9 for a, b in zip(hs, hs[1:])), 'visitor scale must not grow while he walks away'
    assert all(S['visitor'][str(k)] is not None for k in range(0, S['key_contact_frame'] + 2, 2)), 'visitor must be there at contact'
    bh = visitor_bbox_heights()
    assert all(b <= a for a, b in zip(bh, bh[1:])), 'visitor on-screen bbox height must be non-increasing 57.4-65.4 s'
    for c in KV['claims']:
        assert KV['window'][0] <= c['t_in'] and c['t_type_end'] <= KV['window'][1]
    return dict(bbox_h_first_last=(bh[0], bh[-1]), bbox_frames=len(bh), landing_s=round(land, 3), still_s=round(still, 3), s3_head_up_frame=head_k, s3_bell_frame=S3X['bell_onset_frame'],
                empty_grid_s=round(first_field - VAR['notice']['claims'][0]['t_in'], 2), contacts=len(cts))


def visitor_bbox_heights():
    """The visitor's own layer, unoccluded, drawn exactly as TS.visitor_layer draws him, film 57.417-65.4 s."""
    out = []
    for k in range(X['S5c']['key_contact_frame'], 222, 1):
        lay = Image.new('RGBA', (W + 600, H), (0, 0, 0, 0))
        f = TS._vis(k)
        pose = dict(lean=f['lean'], head=f['head'], arm=f['arm'], hem=f['hem'], own_arm=True,
                    legs={'near': tuple(f['near']), 'far': tuple(f['far'])})
        V.draw(lay, (f['hip'][0] + 300, f['hip'][1]), f['sc'], pose, shadow=False)
        a = np.asarray(lay.getchannel('A')) > 40; ys = np.where(a.any(1))[0]
        out.append(int(ys[-1] - ys[0] + 1))
    return out


def run_verify():
    r = subprocess.run([sys.executable, str(SW / 'incident' / 'verify.py')], capture_output=True, text=True, cwd=str(SW))
    assert r.returncode == 0, 'incident/verify.py failed:\n' + r.stdout[-2000:] + r.stderr[-2000:]
    return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'ok'


# ------------------------------------------------------------------ film
film = Film('exercices-de-style', DUR, boil=0)
DOOR_HASHES = set()


@film.picture
def _pic(t, ink):
    img = render(t)
    if ink.i % 6 == 0:
        h = check_door(t, img)
        if h:
            DOOR_HASHES.add(h)
    ink.img = img
    ink._grain = False                    # no synthetic grain: texture is the real prints and the paper


film.sound(sound)
film.poster_at = KV['test_shot']['beat5_pair_frame_s']   # 58.667


PAIR_T = KV['test_shot']['beat5_pair_frame_s']          # 58.667 = S5c start + 2.5 s (plan §10 revision 1: the bar's 54.0 re-anchored)


def page_like_median(a_):
    """median of the page-coloured pixels above the band (L* 80-96, b* > 25), as the critic measured."""
    px = a_[:L.BAND_Y].reshape(-1, 3).astype(np.float64)
    lab = np.array([L.lab(p) for p in px[::37]])
    sel = px[::37][(lab[:, 0] > 80) & (lab[:, 0] < 96) & (lab[:, 2] > 25)]
    return np.median(sel, 0), len(sel) / len(lab)


def sheets():
    out = FILMS / 'stills'; out.mkdir(exist_ok=True)
    a = render(11.0); b = render(PAIR_T)
    pair = Image.new('RGB', (1940, 600), (30, 26, 20)); pair.paste(a, (0, 40)); pair.paste(b, (980, 40))
    d = ImageDraw.Draw(pair)
    d.text((10, 10), 'S1 Le registre, 11.0 s: eye level, the key placed (no settle)', font=L.font(L.SANS, 18), fill=(255, 255, 255))
    d.text((990, 10), f'S5c Narré par la clé, {PAIR_T:.3f} s (S5c + 2.5 s): key height, key still, same visitor, bench, door', font=L.font(L.SANS, 18), fill=(255, 255, 255))
    pair.save(out / 'exercices-de-style-beat5-pair.jpg', quality=90)
    ref = Image.open(L.ROOT / 'assets' / 'references' / 'styleBook.webp').convert('RGB')
    rh = ref.resize((int(ref.size[0] * 540 / ref.size[1]), 540))
    ts = [2.0, 8.0, 30.0, 40.0, PAIR_T]
    sheet = Image.new('RGB', (rh.size[0] + 20 + 960, len(ts) * 560), (30, 26, 20))
    rows = []
    for i, t in enumerate(ts):
        f = render(t)
        sheet.paste(rh, (0, i * 560)); sheet.paste(f, (rh.size[0] + 20, i * 560))
        a_ = np.asarray(f)
        pm, frac = page_like_median(a_)
        bm = np.median(a_[500:525, 300:700].reshape(-1, 3), 0)
        rows.append(dict(t=t, page='#%02x%02x%02x' % tuple(int(v) for v in pm), dE_page=round(L.dE(pm, L.PAGE), 2), page_like_fraction=round(frac, 2),
                         band='#%02x%02x%02x' % tuple(int(v) for v in bm), dE_band=round(L.dE(bm, L.BAND), 2)))
        lab = 'S5c + 2.5 s (bar 54.0 re-anchored)' if t == PAIR_T else ''
        ImageDraw.Draw(sheet).text((rh.size[0] + 30, i * 560 + 544), f"{t:.3f} s {lab}  page {rows[-1]['page']} dE76 {rows[-1]['dE_page']} ({rows[-1]['page_like_fraction']:.0%} page-like)  band {rows[-1]['band']} dE76 {rows[-1]['dE_band']}",
                                   font=L.font(L.MONO, 12), fill=(255, 255, 255))
    sheet.save(out / 'exercices-de-style-aesthetic.jpg', quality=85)
    json.dump(rows, open(SW / 'aesthetic-measure.json', 'w'), indent=1)
    print(json.dumps(rows, indent=1))


if __name__ == '__main__':
    fx = timing_fixtures(); print('timing fixtures ok', fx)
    print('verify.py:', run_verify())
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        hs = set()
        for k in range(0, int(DUR * FPS), 6):
            t = k / FPS; h = check_door(t, render(t))
            if h: hs.add(h)
        print('INV-DOOR ok, hashes:', sorted(hs))
    elif len(sys.argv) > 1 and sys.argv[1] == '--sheets':
        sheets()
    elif len(sys.argv) > 1 and sys.argv[1] == '--stills':
        pdir = FILMS / 'stills' / 'exercices-de-style'; pdir.mkdir(parents=True, exist_ok=True)
        for t in [float(x) for x in sys.argv[2:]]:
            render(t).save(pdir / f'{t:06.2f}.png')
        print('stills ->', pdir)
    else:
        film.render()
        print('INV-DOOR hashes over rendered frames:', sorted(DOOR_HASHES), 'sound:', SOUND_LOG)
