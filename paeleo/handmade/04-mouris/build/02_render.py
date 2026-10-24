"""SCION-04 · render the 32 s scene, frame for frame with the score, as an image torrent.
Writes cache/scene.mp4 (video only), cache/stats.json (per-frame replacement counts: the sound is made from these),
../trace.json (what the dog did, measured from its rendered mould).
Usage: python3 02_render.py [first_frame last_frame step]  (a partial range writes PNGs to cache/test/ for checking)."""
import json, math, os, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import scene as SC
from scene import lerp, clamp, ease
import torrent as TR

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(OUT, '../score/threshold-score.json')))
FR = SCORE['frames']; FPS = 24; W, H = 1280, 720
FONTS = os.path.abspath(os.path.join(OUT, '../../../tools/paeleo/fonts'))
lib = TR.Library()
rng = np.random.default_rng(4)

# ------------------------------------------------------------------ camera (world metres -> screen px)
def camera(t):
    k = ease((t - 24.6) / 2.8)
    return dict(cx=lerp(1.6, -0.32, k), ppm=lerp(175, 245, k), gy=lerp(600, 628, k))
def sx(C, x): return W / 2 + (x - C['cx']) * C['ppm']
def sy(C, y): return C['gy'] - y * C['ppm']

# ------------------------------------------------------------------ timeline signals from the score
T = np.arange(len(FR)) / FPS
voice = [f['person']['voice'] for f in FR]
def env(kind, tau):
    e = np.zeros(len(FR)); v = 0.
    for i in range(len(FR)):
        v = 1. if voice[i] == kind else v * math.exp(-1 / (FPS * tau)); e[i] = v
    return e
CALL = env('call', 0.45); SOFT = env('soft', 1.2)
REACH = np.array([f['person']['reach'] for f in FR])
door_open_t = next(f['t'] for f in FR if f['door'] == 'open')
def door_amt(t): return ease((t - door_open_t) / 1.1)
CHOICES = [c['t'] for c in SCORE['choices']] + [26.4]
def onsets(kind): return [FR[i]['t'] for i in range(1, len(FR)) if voice[i] == kind and voice[i - 1] != kind]
CALL_ON, SOFT_ON = onsets('call'), onsets('soft')
HOLDS = [(11.9, 14.6), (29.0, 32.1)]
FLIPS = [FR[i]['t'] for i in range(1, len(FR)) if (FR[i]['dog']['act']['turn'] >= 0) != (FR[i - 1]['dog']['act']['turn'] >= 0)]
BIG_BURSTS = [c['t'] for c in SCORE['choices'] if c['to'] in ('refuse', 'lie_down')]   # the two choices cut as a burst of the whole frame
TRUST = np.array([f['dog']['trust'] for f in FR])
def in_hold(t): return any(a <= t < b for a, b in HOLDS)

# ------------------------------------------------------------------ drawing moulds
SS = 2   # supersampling for anti-aliased moulds
def mould(polys_px, size=(W, H)):
    out = np.zeros((size[1], size[0]), np.float32)
    pts = np.array([p for poly in polys_px for p in poly], np.float64)
    if len(pts) == 0: return out
    bx0 = int(max(0, math.floor(pts[:, 0].min()) - 2)); by0 = int(max(0, math.floor(pts[:, 1].min()) - 2))
    bx1 = int(min(size[0], math.ceil(pts[:, 0].max()) + 2)); by1 = int(min(size[1], math.ceil(pts[:, 1].max()) + 2))
    if bx1 <= bx0 or by1 <= by0: return out
    im = Image.new('L', ((bx1 - bx0) * SS, (by1 - by0) * SS), 0); d = ImageDraw.Draw(im)
    for poly in polys_px: d.polygon([((x - bx0) * SS, (y - by0) * SS) for x, y in poly], fill=255)
    out[by0:by1, bx0:bx1] = np.asarray(im.reduce(SS), np.float32) / 255.
    return out
_CACHE = {}
def cached(key, fn):
    if key not in _CACHE:
        if len(_CACHE) > 64: _CACHE.clear()
        _CACHE[key] = fn()
    return _CACHE[key]
def rect(C, x0, y0, x1, y1): return [(sx(C, x0), sy(C, y0)), (sx(C, x1), sy(C, y0)), (sx(C, x1), sy(C, y1)), (sx(C, x0), sy(C, y1))]

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)

def light_field(C, L):
    """warm light from the open door, in screen space (a gain map for the guides)"""
    dx = (XX - sx(C, 0.0)) / C['ppm']; dy = (YY - sy(C, 1.0)) / C['ppm']
    d = np.sqrt(dx * dx * 0.7 + dy * dy)
    return (L * np.clip(1.25 - d / 2.4, 0, 1) ** 1.6)[..., None]

DUSK = np.array([0.62, 0.66, 0.92], np.float32); WARM = np.array([1.35, 1.0, 0.62], np.float32)
def lit_raw(base, Lf):
    return np.clip(np.array(base, np.float32) * (DUSK * (1 - Lf) + WARM * Lf * 1.25 + DUSK * Lf * 0.2), 0, 1)

def sky_guide(C):
    yh = sy(C, 0.25); top = np.array([0.10, 0.10, 0.26]); mid = np.array([0.30, 0.20, 0.38]); low = np.array([0.62, 0.36, 0.34])
    u = np.clip((YY - 0) / max(yh, 1), 0, 1)[..., None]
    g = np.where(u < 0.6, top + (mid - top) * (u / 0.6), mid + (low - mid) * ((u - 0.6) / 0.4))
    return g.astype(np.float32)

# ------------------------------------------------------------------ layers (persistent tile states)
LY = dict(
    sky=TR.Layer('sky', 'sky', kind=1, maxlevel=0, contrast=0.5, split_std=0.08),
    moon=TR.Layer('moon', 'moon', kind=0, maxlevel=2, contrast=0.8, keep=0.3),
    yard=TR.Layer('yard', 'yard', kind=1, maxlevel=1, contrast=0.45),
    wall=TR.Layer('wall', 'house', kind=0, maxlevel=0, contrast=0.42, split_std=0.06),
    beam=TR.Layer('beam', 'floor', kind=1, maxlevel=1, contrast=0.6),
    trim=TR.Layer('trim', 'door', kind=1, maxlevel=2, contrast=0.6),
    inside=TR.Layer('inside', 'light', kind=0, maxlevel=1, contrast=0.9, keep=0.15, split_std=0.1),
    panel=TR.Layer('panel', 'door', kind=1, maxlevel=1, contrast=0.75, split_std=0.1),
    floor=TR.Layer('floor', 'floor', kind=1, maxlevel=1, contrast=0.45, split_std=0.06),
    spill=TR.Layer('spill', 'light', kind=0, maxlevel=2, contrast=0.8),
    person=TR.Layer('person', 'person', kind=0, maxlevel=1, contrast=0.85, keep=0.25, split_std=0.07, ragged=True, shadow=0.45),
    face=TR.Layer('face', 'face', kind=0, maxlevel=1, contrast=0.9, keep=0.5, split_std=0.3, ragged=True, shadow=0.4),
    hand=TR.Layer('hand', 'hand', kind=0, maxlevel=2, contrast=0.95, keep=0.55, split_std=0.3, ragged=True, shadow=0.4),
    dog=TR.Layer('dog', 'animal', kind=0, maxlevel=1, contrast=0.95, keep=0.4, split_std=0.06, ragged=True, shadow=0.55),
    flank=TR.Layer('flank', 'animal', kind=0, contrast=1.0, keep=0.72),
    dogeye=TR.Layer('dogeye', 'eye', kind=0, maxlevel=2, contrast=0.9, keep=0.55, ragged=True),
    words=TR.Layer('words', 'alarm', kind=0, maxlevel=2, contrast=0.9, split_std=0.2, ragged=True, shadow=0.7),
)

# ------------------------------------------------------------------ waves of other pictures (the voice made visible)
def hsh(cx, cy):
    return ((int(cx) * 73856093) ^ (int(cy) * 19349663)) % 997 / 997.
def wave_override(t, C, src_mouth, door_xy):
    waves = []
    for t0 in CALL_ON: waves.append((t0, src_mouth, 950., 'alarm', 0.95, 0.9, 1.0))
    for t0 in SOFT_ON: waves.append((t0, src_mouth, 260., 'soft', 0.42, 2.2, 0.0))
    waves.append((door_open_t, door_xy, 520., 'light', 0.6, 1.6, 0.4))
    live = [w for w in waves if 0 <= t - w[0] < 6]
    if not live: return None
    def f(L, cx, cy):
        for (t0, (mx, my), v, pool, amp, tau, extra) in live:
            d = math.hypot(cx - mx, cy - my); th = t0 + d / v
            if t >= th:
                p = amp * math.exp(-(t - th) / tau)
                if hsh(cx, cy) < p: return (pool, extra)
        return None
    return f

# ------------------------------------------------------------------ words: the voice as letters made of pictures
F_LOUD = ImageFont.truetype(os.path.join(FONTS, 'f8.woff2'), 150)
try: F_LOUD.set_variation_by_axes([900])
except Exception: pass
F_SOFT = ImageFont.truetype(os.path.join(FONTS, 'f27.woff2'), 76)
try: F_SOFT.set_variation_by_axes([600])
except Exception: pass
SPEECH = []   # (t0, t1, text, font, pool, colour, anchor)
for i in range(1, len(FR)):
    if voice[i] != 'none' and voice[i - 1] != voice[i]:
        j = i
        while j < len(FR) and voice[j] == voice[i]: j += 1
        txt = 'COME HERE.' if voice[i] == 'call' else ("come in." if FR[i]['t'] > 20 else "it's all right.")
        SPEECH.append((FR[i]['t'], FR[j - 1]['t'] + 1 / FPS, txt, voice[i]))
def words_mould(t, C, mouth):
    for (t0, t1, txt, kind) in SPEECH:
        if t0 - 0.05 <= t < t1 + 0.7:
            font = F_LOUD if kind == 'call' else F_SOFT
            n = len(txt); shown = n if kind == 'call' else int(clamp((t - t0) / max(0.6 * (t1 - t0), 0.3)) * n + 0.999)
            if kind == 'call': shown = int(clamp((t - t0) / 0.35) * n + 0.999)
            im = Image.new('L', (W * SS, H * SS), 0); d = ImageDraw.Draw(im)
            if kind == 'call': x, y = mouth[0] + 30, max(60, mouth[1] - 230)
            else: x, y = mouth[0] + 20, mouth[1] - 120
            x = min(x, W - 40 - d.textlength(txt, font=font) * 1.0)
            jit = (rng.integers(-4, 5), rng.integers(-4, 5)) if kind == 'call' and t < t1 else (0, 0)
            fs = font.font_variant(size=font.size * SS) if True else font
            try: fs.set_variation_by_axes([900 if kind == 'call' else 600])
            except Exception: pass
            d.text(((x + jit[0]) * SS, (y + jit[1]) * SS), txt[:shown], font=fs, fill=255)
            m = np.asarray(im.reduce(SS), np.float32) / 255.
            fade = clamp((t1 + 0.7 - t) / 0.7)
            if fade < 1:   # the torrent eats the words: cells drop out
                cells = (np.add.outer(np.arange(H) // 12 * 31, np.arange(W) // 16 * 17) % 97) / 97.
                m = m * (cells < fade)
            pool = 'alarm' if kind == 'call' else ('soft' if txt.startswith('it') else 'light')
            col = (0.98, 0.78, 0.18) if kind == 'call' else (0.96, 0.88, 0.74)
            return m, pool, col, kind, txt
    return None

# ------------------------------------------------------------------ the frame
def poly_px(C, polys, ox_m, flip=1.0, base_y=0.0, k=1.0):
    return [[(sx(C, ox_m) + flip * k * x * C['ppm'], sy(C, base_y + k * y)) for x, y in poly] for poly in polys]
DOGK = 1.3   # the dog is drawn 1.3x a real dog's size, so its pictures can be seen

def render(i, stats):
    f = FR[i]; t = f['t']; C = camera(t); dog = f['dog']; a = dog['act']; per = f['person']
    hold = in_hold(t)
    Ld = door_amt(t)
    ck = (round(C['cx'], 4), round(C['ppm'], 3), round(C['gy'], 3))
    Lf = cached(('L', ck, round(Ld, 3)), lambda: light_field(C, Ld))
    _lit = lit_raw
    def lit(base, Lf_, _k=None):
        return cached(('lit', tuple(base), ck, round(Ld, 3), float(Lf_.max())), lambda: _lit(base, Lf_))
    canvas = np.zeros((H, W, 3), np.float32)
    rec = dict(i=i, t=t)
    # rates: the torrent's speed is the scene's pressure
    call = CALL[i]; soft = SOFT[i]
    choice_burst = any(0 <= t - c < 6 / FPS for c in CHOICES) or any(0 <= t - c < 4 / FPS for c in FLIPS)
    big_burst = any(0 <= t - c < 12 / FPS for c in BIG_BURSTS)
    bg_rate = 0.004 + 0.30 * call + (0.0 if hold else 0.004)
    if hold: bg_rate = 0.0015
    if big_burst: bg_rate = 1.0
    adv = 4 if hold else 2
    person_xy = (sx(C, per['x']), sy(C, 0))
    pparts, pinfo = SC.person_parts(per, walk=abs(per['x'] + 0.28) / 0.28 * math.pi)
    mouth = (sx(C, per['x'] + pinfo['mouth'][0]), sy(C, pinfo['mouth'][1]))
    door_xy = (sx(C, 0), sy(C, 1.0))
    ov = wave_override(t, C, mouth, door_xy)

    # sky (dusk), moon, yard
    st = {}
    st['sky'] = TR.render_layer(lib, LY['sky'], np.ones((H, W), np.float32), cached(('skyg', ck), lambda: sky_guide(C)), 0, 0, bg_rate, rng, i, canvas, ov, adv, bbox=(0, 0, W, H))
    moon = cached(('moon', ck), lambda: mould([[(sx(C, 4.25) + x * C['ppm'], sy(C, 2.45) - y * C['ppm']) for x, y in SC.circle((0, 0), 0.2, 40)]]))
    st['moon'] = TR.render_layer(lib, LY['moon'], moon, np.full((H, W, 3), (0.93, 0.88, 0.74), np.float32), int(sx(C, 4.25)), int(sy(C, 2.45)), bg_rate * 2, rng, i, canvas, None, adv)
    yard = cached(('yard', ck), lambda: mould([rect(C, 2.4, 0.0, 9, 0.28), rect(C, -9, -0.40, 9, -3)] + [[(sx(C, 5.25) + x * C['ppm'], sy(C, y)) for x, y in [(-0.25, 0), (-0.4, 1.1), (-0.15, 1.6), (0.0, 2.2), (0.2, 1.5), (0.45, 1.0), (0.3, 0)]]]))
    st['yard'] = TR.render_layer(lib, LY['yard'], yard, np.full((H, W, 3), (0.13, 0.17, 0.15), np.float32), 0, 0, bg_rate, rng, i, canvas, ov, adv)
    # the house wall, the roof beam, the porch post
    wall = cached(('wall', ck), lambda: mould([rect(C, -9, 0.0, 2.6, 3.1)]))
    st['wall'] = TR.render_layer(lib, LY['wall'], wall, lit((0.36, 0.36, 0.44), Lf * 1.2), 0, 0, bg_rate, rng, i, canvas, ov, adv)
    beam = cached(('beam', ck), lambda: mould([rect(C, -9, 3.05, 5.05, 3.32), rect(C, 4.66, 0.0, 4.8, 3.05)]))
    st['beam'] = TR.render_layer(lib, LY['beam'], beam, lit((0.32, 0.26, 0.24), Lf), 0, 0, bg_rate, rng, i, canvas, ov, adv)
    # the doorway: inside (lamps and bulbs; dark while the door is only ajar), the door panel (doors), the trim
    pw = 0.92 * lerp(0.62, 0.07, Ld); x0 = -0.46
    inside = cached(('inside', ck), lambda: mould([rect(C, x0, 0, 0.46, 2.08)]))
    ig = np.zeros((H, W, 3), np.float32)
    gl = lerp(0.16, 1.0, Ld)
    ig[:] = np.array([1.0, 0.80, 0.48]) * gl
    ig *= np.clip(0.75 + 0.35 * (YY / H), 0, 1.1)[..., None]
    st['inside'] = TR.render_layer(lib, LY['inside'], inside, ig, int(sx(C, x0)), int(sy(C, 2.08)), (0.5 if 0 < t - door_open_t < 1.2 else 0.006) + 0.2 * call, rng, i, canvas, None, adv)
    panel = mould([[(sx(C, x0), sy(C, 2.08)), (sx(C, x0 + pw), sy(C, 2.08 - 0.03 * Ld)), (sx(C, x0 + pw), sy(C, 0.01 * Ld)), (sx(C, x0), sy(C, 0))]])
    st['panel'] = TR.render_layer(lib, LY['panel'], panel, lit((0.80, 0.74, 0.62), Lf * 0.5), int(sx(C, x0)), int(sy(C, 2.08)), bg_rate + (0.4 if 0 < t - door_open_t < 1.1 else 0), rng, i, canvas, None, adv)
    trim_l = [rect(C, -0.58, 0, -0.46, 2.2), rect(C, -0.58, 2.08, 0.58, 2.2)]
    trim_r = [rect(C, 0.46, 0, 0.58, 2.2)]
    trim_all = cached(('trim', ck), lambda: mould(trim_l + trim_r))
    # the porch floor and the steps, and the sill
    floor = cached(('floor', ck), lambda: mould([rect(C, -9, 0.0, 4.95, -0.40), rect(C, 4.95, -0.12, 5.6, -0.40), rect(C, -0.52, 0.035, 0.52, -0.02)]))
    fg = lit((0.40, 0.29, 0.22), Lf)
    st['floor'] = TR.render_layer(lib, LY['floor'], floor, fg, 0, 0, bg_rate, rng, i, canvas, ov, adv)
    if Ld > 0.02:
        xg = x0 + pw
        spill = mould([[(sx(C, xg), sy(C, 0)), (sx(C, 0.46 + 3.3 * Ld), sy(C, 0)), (sx(C, 0.46 + 3.9 * Ld), sy(C, -0.40)), (sx(C, xg + 0.25), sy(C, -0.40))]]) * floor
        sg = np.zeros((H, W, 3), np.float32); fall = np.clip(1.1 - (XX - sx(C, 0.46)) / (3.6 * C['ppm']), 0.15, 1)[..., None]
        sg[:] = np.array([0.95, 0.70, 0.38]) * Ld; sg *= fall
        st['spill'] = TR.render_layer(lib, LY['spill'], spill * (0.25 + 0.65 * Ld), sg, 0, 0, bg_rate, rng, i, canvas, None, adv)
    # glow of the doorway into the dusk (a grade, not a picture)
    if Ld > 0.01:
        dx = (XX - sx(C, 0)) / C['ppm']; dy = (YY - sy(C, 1.0)) / C['ppm']
        g = np.exp(-(dx * dx * 0.8 + dy * dy * 0.5) / 1.6)[..., None] * 0.22 * Ld
        canvas[:] = 1 - (1 - canvas) * (1 - g * np.array([1.0, 0.75, 0.4], np.float32))

    # ---------------------------------------------------------------- the person: people, faces and hands
    lab = {'far': [], 'cloth': [], 'skin': [], 'hand': []}
    for l_, poly in pparts: lab[l_].append(poly)
    pr = 0.02 + 0.6 * call + 0.25 * REACH[i]
    if hold: pr = 0.004
    pm_body = mould(poly_px(C, lab['far'] + lab['cloth'], per['x']))
    pm_far = mould(poly_px(C, lab['far'], per['x']))
    pg = lit((0.30, 0.42, 0.55), Lf) * (1 - 0.45 * pm_far[..., None])
    pm_face = mould(poly_px(C, lab['skin'], per['x'])); pm_hand = mould(poly_px(C, lab['hand'], per['x']))
    if big_burst: pr = 1.0
    pax, pay = int(person_xy[0]), int(person_xy[1])
    st['person'] = TR.render_layer(lib, LY['person'], pm_body, pg, pax, pay, pr, rng, i, canvas, None, adv)
    st['face'] = TR.render_layer(lib, LY['face'], pm_face, lit((0.80, 0.60, 0.48), Lf), pax, pay, max(pr, 0.02 + 0.5 * call), rng, i, canvas, None, adv)
    st['hand'] = TR.render_layer(lib, LY['hand'], pm_hand, lit((0.84, 0.58, 0.44), Lf * 0.7), pax, pay, max(pr, 0.02 + 0.5 * call + 0.3 * REACH[i]), rng, i, canvas, None, adv)

    # ---------------------------------------------------------------- the dog: animals (and the archive dog)
    parts, dinfo = SC.dog_parts(a, t)
    turn = a['turn']; sgn = 1.0 if (turn > 0 or (turn == 0 and dog['face'] > 0)) else -1.0
    flip = sgn * (0.62 + 0.38 * abs(turn))   # a cut-out turned over, never seen end-on
    dl = {}
    for l_, poly in parts: dl.setdefault(l_, []).append(poly)
    def dm(names): return mould(poly_px(C, [p for n in names for p in dl.get(n, [])], dog['x'], flip=flip, k=DOGK))
    m_all = dm(['far', 'tail', 'body', 'near', 'head', 'ear'])
    m_far = dm(['far']); m_head = dm(['head', 'ear']); m_near = dm(['near']); m_body = dm(['body']); m_ear = dm(['ear'])
    # shading: far legs dark, ears dark, the head and chest catch the light, the back is dusk
    base = np.ones((H, W, 1), np.float32)
    shade = base * 1.0 - 0.42 * m_far[..., None] * (1 - m_body[..., None]) - 0.25 * m_ear[..., None] + 0.08 * m_head[..., None]
    oy = sy(C, 0)
    vert = np.clip((YY - (oy - 0.8 * C['ppm'])) / (0.8 * C['ppm']), 0, 1)[..., None]
    # the dog's colour follows the score's trust: cold dusk grey when it distrusts, warm as trust grows
    tr_ = clamp((TRUST[i] - 0.1) / 0.8)
    dbase = np.array([lerp(0.46, 0.80, tr_), lerp(0.40, 0.50, tr_), lerp(0.44, 0.28, tr_)], np.float32)
    Lq = Lf * 0.35
    dg = np.clip(dbase * (DUSK * (1 - Lq) + WARM * Lq * 1.2 + 0.25 * DUSK * Lq), 0, 1) * shade * (1.02 - 0.18 * (1 - vert))
    # the dog's rate: frantic when called, a full re-making at each choice, settling as it lies down, nearly held at the end
    dr = 0.05 + 0.55 * dog['threat'] ** 1.5 + 0.18 * a['moving'] + 0.30 * call
    if dog['state'] == 'lie_down': dr *= (1 - 0.85 * a['lie'])
    if hold: dr = 0.004 if t > 20 else 0.01
    if choice_burst or big_burst: dr = 1.0
    # shadow on the floor
    sh = mould([[(sx(C, dog['x']) + x * C['ppm'], sy(C, 0) - y * C['ppm']) for x, y in SC.ellipse((0, 0.0), 0.55 * DOGK, 0.035)]])
    canvas *= (1 - 0.45 * sh[..., None])
    dax, day = int(round(sx(C, dog['x']))), int(round(sy(C, 0)))
    st['dog'] = TR.render_layer(lib, LY['dog'], m_all, dg, dax, day, dr, rng, i, canvas, None, adv)
    # two large flank pictures, pasted on the body (recognisable animals, little colour shift)
    st['flank'] = dict(cells=0, replaced=0)
    if LY['dog'].last_alpha is not None:
        ax0, ay0, A = LY['dog'].last_alpha
        Mx = (dinfo['S'][0] + dinfo['H'][0]) / 2; My = (dinfo['S'][1] + dinfo['H'][1]) / 2
        tw, th = int(round(64 * C['ppm'] / 175 * abs(flip))), int(round(48 * C['ppm'] / 175))
        for k_, off in enumerate((-0.13, 0.13)):
            cx_ = sx(C, dog['x']) + flip * DOGK * (Mx + off) * C['ppm']; cy_ = sy(C, DOGK * (My - 0.005))
            bx, by = int(cx_ - tw / 2), int(cy_ - th / 2)
            stf = LY['flank'].cells.get(k_)
            if stf is None or rng.random() < (1.0 if (choice_burst or big_burst) else 0.6 * dr):
                stf = lib.choose('animal', dbase, 0, rng, k=3, avoid=None if stf is None else stf[0]) + [None, i, 'animal']
                LY['flank'].cells[k_] = stf; LY['flank'].placed += 1; st['flank']['replaced'] += 1
            elif (i - stf[5]) % adv == 0:
                n = lib.shots[stf[0]]['n']; nf = stf[1] + stf[3]
                if nf < 0 or nf >= n: stf[3] = -stf[3]; nf = stf[1] + stf[3]
                stf[1] = int(min(max(nf, 0), n - 1))
            idx = lib.index(stf[0], stf[1], stf[2])
            tile = np.asarray(Image.fromarray(lib.T[64][idx]).resize((max(tw, 4), th), Image.BILINEAR), np.float32) / 255.
            tgt = dg[int(min(max(cy_, 0), H - 1)), int(min(max(cx_, 0), W - 1))]
            out = np.clip(((tile - lib.mean[idx]) + tgt) * (1 - LY['flank'].keep) + tile * LY['flank'].keep, 0, 1)
            # clip to the dog's own tile alpha, and to the frame
            X0, Y0 = max(bx, ax0, 0), max(by, ay0, 0); X1 = min(bx + tile.shape[1], ax0 + A.shape[1], W); Y1 = min(by + th, ay0 + A.shape[0], H)
            if X1 > X0 and Y1 > Y0:
                aa = A[Y0 - ay0:Y1 - ay0, X0 - ax0:X1 - ax0][..., None]
                canvas[Y0:Y1, X0:X1] = canvas[Y0:Y1, X0:X1] * (1 - aa) + out[Y0 - by:Y1 - by, X0 - bx:X1 - bx] * aa
                st['flank']['cells'] += 1
    # the eye: one small found eye picture, pasted whole
    e = dinfo['eye']; st['dogeye'] = dict(cells=0, replaced=0)
    if e is not None:
        ex, ey = sx(C, dog['x']) + flip * DOGK * e[0] * C['ppm'], sy(C, DOGK * e[1])
        ew, eh = (8, 6) if C['ppm'] < 210 else (16, 12)
        eye = np.zeros((H, W), np.float32); eye[int(ey - eh / 2):int(ey + eh / 2), int(ex - ew / 2):int(ex + ew / 2)] = 1
        st['dogeye'] = TR.render_layer(lib, LY['dogeye'], eye, np.full((H, W, 3), (0.30, 0.22, 0.16), np.float32), int(ex - ew / 2), int(ey - eh / 2), 0.02, rng, i, canvas, None, adv)
    # the right jamb in front of the dog: lying across the sill it is half in the doorway, half out
    st['trim'] = TR.render_layer(lib, LY['trim'], trim_all, lit((0.78, 0.72, 0.62), Lf * 0.6), int(sx(C, -0.58)), int(sy(C, 2.2)), bg_rate, rng, i, canvas, None, adv)

    # ---------------------------------------------------------------- the voice as letters of pictures
    wm = words_mould(t, C, mouth)
    if wm is not None:
        m, pool, col, kind, txt = wm
        LY['words'].pool = pool
        st['words'] = TR.render_layer(lib, LY['words'], m, np.full((H, W, 3), col, np.float32), 0, 0, 0.7 if kind == 'call' else 0.04, rng, i, canvas, None, adv)
        rec['words'] = txt

    # ---------------------------------------------------------------- measure the dog from its own rendered mould
    m_torso = mould(poly_px(C, [dinfo['torso']], dog['x'], flip=flip, k=DOGK))
    ys, xs = np.nonzero(m_torso > 0.5)
    hy_, hx_ = np.nonzero(m_head > 0.5)
    ay_, ax_ = np.nonzero(m_all > 0.5)
    cxm = float(xs.mean()); cym = float(ys.mean())
    face_meas = 'door' if hx_.mean() < cxm else 'away'
    height_m = (ay_.max() - ay_.min()) / C['ppm']; top_body_m = (sy(C, 0) - ys.min()) / C['ppm']
    posture = 'lying' if top_body_m < 0.36 * DOGK else ('crouched' if top_body_m < 0.55 * DOGK else 'standing')
    left_m = (ax_.min() - W / 2) / C['ppm'] + C['cx']; right_m = (ax_.max() - W / 2) / C['ppm'] + C['cx']
    trace = dict(i=i, t=round(t, 4), state=dog['state'], x_score=dog['x'], x_screen=round(cxm, 2), y_screen=round(cym, 2),
                 x_world_measured=round((cxm - W / 2) / C['ppm'] + C['cx'], 3), facing=face_meas, posture=posture,
                 body_top_m=round(top_body_m, 3), head_up_m=round((sy(C, 0) - hy_.min()) / C['ppm'], 3) if len(hy_) else None,
                 head_dx_m=round((hx_.mean() - cxm) / C['ppm'], 3) if len(hx_) else None, width_m=round((ax_.max() - ax_.min()) / C['ppm'], 3),
                 extent_m=[round(left_m, 3), round(right_m, 3)], camera=dict(cx=round(C['cx'], 3), ppm=round(C['ppm'], 2)),
                 dog_tiles=st['dog']['cells'], dog_replaced=st['dog']['replaced'])
    stats.append(dict(i=i, t=t, **{k: v['replaced'] for k, v in st.items()}, cells={k: v['cells'] for k, v in st.items()},
                      call=round(float(call), 3), soft=round(float(soft), 3), door=round(Ld, 3), hold=hold, burst=choice_burst,
                      paw=a['walk_phase'], moving=a['moving']))
    img = (np.clip(canvas, 0, 1) * 255).astype(np.uint8)
    return img, trace


def main():
    args = [int(v) for v in sys.argv[1:]]
    full = not args
    rng_frames = range(0, len(FR)) if full else range(args[0], args[1], args[2] if len(args) > 2 else 1)
    os.makedirs(os.path.join(HERE, 'cache/test'), exist_ok=True)
    stats, traces = [], []
    if full:
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '24', '-i', '-',
                               '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', os.path.join(HERE, 'cache/scene.mp4')], stdin=subprocess.PIPE)
    t0 = time.time()
    # when testing a range, run the torrent from 0 anyway so held tiles are what they would be (cheap: skip encode)
    start = 0 if full else max(0, rng_frames.start - 48)
    for i in range(start, rng_frames.stop):
        img, tr = render(i, stats)
        traces.append(tr)
        if full: ff.stdin.write(img.tobytes())
        elif i in rng_frames: Image.fromarray(img).save(os.path.join(HERE, f'cache/test/f{i:03d}.png'))
        if i % 48 == 0: print(f'frame {i} {time.time() - t0:.0f}s', file=sys.stderr, flush=True)
    if full:
        ff.stdin.close(); ff.wait()
        json.dump(stats, open(os.path.join(HERE, 'cache/stats.json'), 'w'))
        json.dump(dict(about='SCION-04 · what the dog did, measured per scene frame from its own rendered mould (centroid of the torso polygon as rendered, head centroid vs torso, height of the back). x_screen/y_screen are px of the torso centroid; x_world_measured inverts the camera; facing: door = head toward the threshold, away = back turned; posture from the height of the back above the porch.',
                       frames=traces, usage={lib.shots[s]['category'] + ('(kit)' if 'kit/' in lib.shots[s]['dir'] else ''): n for s, n in sorted(lib.usage.items())}),
                  open(os.path.join(OUT, 'trace.json'), 'w'))
        json.dump({k: v.placed for k, v in LY.items()}, open(os.path.join(HERE, 'cache/placements.json'), 'w'))

if __name__ == '__main__':
    main()
