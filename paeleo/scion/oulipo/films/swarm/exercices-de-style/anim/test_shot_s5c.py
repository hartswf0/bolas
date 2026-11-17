"""TEST SHOT S5c « Narré par la clé », beat 5 (film 56.167-66.25 s per incident/anthology.json timing_revision).

FORAGED: Rol 57642 'Homme marchant dans la rue' (Jan 1920, PD) cut + articulated (walk, rise, the lowering arm);
CC0 Edna C. Rex key (NGA 24027); MIA 'Communications and Our Town' (1947) belfry still in strip cell 2;
sound: Wreckless (1935) optical-track room tone (MIA), Commons 'Footstep on Gravel' (Gravity Sound, CC BY 4.0) steps,
Commons 'Dull thud' (PD) landing.  HANDMADE: page, ghost, type, bench, door, strip, band (es_lib).
Motion comes from anim/exposure.json (written by exposure.py).  Rendered through films/kit.py, unedited.
Run: python3 test_shot_s5c.py            -> sources/exercices-de-style/anim/test-shot.mp4
     python3 test_shot_s5c.py --stills t... (local seconds)
"""
import sys, json, math, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films')
import es_lib as L
import kit
from kit import Film, ease

X = json.load(open(HERE / 'exposure.json'))
S = X['S5c']
T0, DUR = S['film_t0'], S['duration']
FPS = 24
TS = L.SRC / 'test-shot'
ANTH = json.load(open(HERE.parent / 'incident' / 'anthology.json'))

# ---------------------------------------------------------------- static planes
PAGE = L.page(1).convert('RGBA')
GHOST = L.ghost('Je', (150, -200), 660)
BENCH = L.bench_low(top=S['bench_top'])
V = L.Visitor()
KEY = L.key(S['key_length']); KW, KH = KEY.size
KEY_CONTACT = (0.10 * KW, 0.985 * KH)                # bow bottom touches the wood
KEY_GRIP = (0.115 * KW, 0.06 * KH)                   # fingertips pinch the bow's top
ARM = V.P['arm']
FINGER = tuple(S['arm']['fingertip_src'])            # fingertip in mirrored source px

LINES = []
for c in ANTH['variants']['key']['claims']:
    if c['t_in'] >= T0 - 0.01 and c['role'] == 'caption':
        LINES.append(dict(text=c['text'], t_in=c['t_in'] - T0, t_end=c['t_type_end'] - T0, cps=c['cps'],
                          red='d6280a' in c.get('style', '')))
CAP_F = L.font(L.SERIF_I, 24)

def cam(t):
    return S['camera']['drift_px'] * ease(t, S['camera']['t0'], S['camera']['t1'])

def ix(v):
    return int(round(v))

def captions(img, t):
    d = ImageDraw.Draw(img)
    d.text((S['captions']['x'], S['captions']['y'] - 22), '— la clé, 18:06', font=L.font(L.SANS, 15), fill=(118, 86, 36))
    for i, ln in enumerate(LINES):
        if t < ln['t_in']:
            continue
        n = int((t - ln['t_in']) * ln['cps'])                      # 14 chars/s, revealed by whole words
        words, shown, cum = ln['text'].split(' '), [], 0
        for w in words:
            cum += len(w) + (1 if shown else 0)
            if cum <= n + 1 or t >= ln['t_end']:
                shown.append(w)
        if shown:
            d.text((S['captions']['x'], S['captions']['y'] + i * S['captions']['lead']), ' '.join(shown), font=CAP_F,
                   fill=L.RED if ln['red'] else L.BLACK)

def title(img):
    L.set_title(img, [('Narré', L.RED), ('par', L.BLACK), ('la', L.RED), ('clé', L.BLACK)], x=30, base=70, size=48, seed=5)

def key_layer(img, k, dx):
    kf = S['key'][str(min(k, S['key_last']))]
    x, y, a = kf['x'] + dx, kf['y'], kf['a']
    L.place(img, KEY, (0, 0), KEY_CONTACT, (x, y), a, 1.0)
    return x, y, a

REL = S['hand_retract']['frames'][0]; GONE = S['hand_retract']['frames'][1]
BENCH_A = np.asarray(BENCH.getchannel('A'), np.float32) / 255.0

def _vis(k):
    return S['visitor'][str(min((k // 2) * 2, S['visitor_last']))]

def own_arm_xf(k, dx):
    """his own arm pin: where the close-up arm folds back to (shoulder, angle, scale)."""
    f = _vis(k); hip = (f['hip'][0] + dx, f['hip'][1])
    return V.xf(hip, f['sc'], f['lean'], ARM['pivot']), f['lean'] + f['arm'], f['sc']

def hand_layer(img, k, keypose, dx_vis, c):
    """The close-up arm lowers the key; after release it folds back into the visitor (repair 1): shoulder, scale and
    angle tween to his own arm pin, then his own arm piece takes over (same paper, same transform: no pop)."""
    if k >= GONE:
        return
    kk = min(k, REL)
    x, y, a = key_layer_pose(kk, c)
    g = L.R(a, (KEY_GRIP[0] - KEY_CONTACT[0], KEY_GRIP[1] - KEY_CONTACT[1]))
    tip = (x + g[0] + 2, y + g[1] + 6)
    sc, ang = S['arm']['scale'], S['arm']['angle']
    v = L.R(ang, (FINGER[0] - ARM['pivot'][0], FINGER[1] - ARM['pivot'][1]))
    shoulder = (tip[0] - v[0] * sc, tip[1] - v[1] * sc)
    if k > REL:
        u = (k - REL) / (GONE - REL); e = u * u * (3 - 2 * u)
        sh2, ang2, sc2 = own_arm_xf(k, dx_vis)
        v2 = L.R(ang2, (FINGER[0] - ARM['pivot'][0], FINGER[1] - ARM['pivot'][1]))
        tip2 = (sh2[0] + v2[0] * sc2, sh2[1] + v2[1] * sc2)           # his own fingertip
        tip = (tip[0] + (tip2[0] - tip[0]) * e, tip[1] + (tip2[1] - tip[1]) * e)
        ang = ang + (ang2 - ang) * (1 - (1 - e) ** 2)
        sc = sc * (sc2 / sc) ** (1 - (1 - e) ** 2)                   # geometric, fast first: the arm recedes into depth
        v = L.R(ang, (FINGER[0] - ARM['pivot'][0], FINGER[1] - ARM['pivot'][1]))
        shoulder = (tip[0] - v[0] * sc, tip[1] - v[1] * sc)
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    L.place(lay, ARM['img'], ARM['origin'], ARM['pivot'], shoulder, ang, sc)
    if k > REL:                                                      # it passes behind the bench lip, like his body
        bc = BENCH_A[:, ix(200 + c): ix(200 + c) + L.W]
        al = np.asarray(lay.getchannel('A'), np.float32) * (1.0 - bc)
        lay.putalpha(Image.fromarray(al.clip(0, 255).astype(np.uint8)))
    img.alpha_composite(L.lift_shadow(lay, (4, 5), 5, 0.30 * (1 - (k - REL) / (GONE - REL) if k > REL else 1))); img.alpha_composite(lay)

def key_layer_pose(k, c):
    kf = S['key'][str(min(k, S['key_last']))]
    return kf['x'] - 1.0 * c, kf['y'], kf['a']

def visitor_layer(img, k, dx):
    f = _vis(k)
    pose = dict(lean=f['lean'], head=f['head'], arm=f['arm'], hem=f['hem'], own_arm=f.get('own_arm', True),
                legs={'near': tuple(f['near']), 'far': tuple(f['far'])})
    V.draw(img, (f['hip'][0] + dx, f['hip'][1]), f['sc'], pose)

DOOR_POS = tuple(S['door_xy'])
DOOR_SIGN = -1                               # camera drifts right: every plane slides left by its depth factor
CELLS = None

def render(t, k, with_strip=True):
    c = cam(t)
    img = PAGE.copy()
    img.alpha_composite(GHOST.crop((ix(200 + 0.25 * c), 0, ix(200 + 0.25 * c) + L.W, L.H)))
    title(img)
    L.paste_door(img, DOOR_POS[0] + DOOR_SIGN * ix(0.55 * c), DOOR_POS[1])   # whole-pixel move only (INV-DOOR)
    visitor_layer(img, k, -0.55 * c)
    img.alpha_composite(BENCH.crop((ix(200 + 1.0 * c), 0, ix(200 + 1.0 * c) + L.W, L.H)))
    kp = key_layer(img, k, -1.0 * c + 0)
    hand_layer(img, k, kp, -0.55 * c, c)
    captions(img, t)
    L.band(img, 'Narré par la clé', 'Exercice 5 · voix : la clé', '18:06')
    if with_strip:
        L.strip(img, cells(), ring=4)
    return img

def cells():
    global CELLS
    if CELLS is None:
        pm = L.PM
        wk = Image.open(pm / 'dl' / 'homme_marchant_1920.jpg').convert('RGB')
        c1 = L.tint_bw(wk.crop((560, 1000, 1000, 1440))).convert('RGB')                      # E1: the coat that hid the envelope
        c2 = L.tint_bw(Image.open(pm / 'stills' / 'bell_6.jpg').crop((40, 0, 280, 240))).convert('RGB')  # E2: the belfry (MIA 1947)
        env = L.envelope_interior((200, 200), lamp=1.4).convert('RGBA'); tear = L.Tear(20, (200, 200), y=100, x0=-10, x1=210)
        m, _ = tear.mask(19); lit = Image.new('RGBA', (200, 200), L.PAGE_TOP + (255,)); env.paste(lit, (0, 0), m); c3 = env.convert('RGB')
        c4 = Image.new('RGBA', (240, 240), L.PAGE + (255,)); kk = KEY.copy(); kk.thumbnail((230, 230))
        c4.alpha_composite(kk, (5, 120 - kk.size[1] // 2))
        arm = ARM['img'].copy(); arm.thumbnail((400, 400)); c4.alpha_composite(arm.crop((0, arm.size[1] - 200, arm.size[0], arm.size[1])), (10, -40))
        c4 = c4.convert('RGB')
        CELLS = [c1, c2, c3, c4, None, None]
        f5 = render(2.2, int(2.2 * FPS), with_strip=False).convert('RGB').crop((300, 150, 560, 410))
        f6 = render(7.6, int(7.6 * FPS), with_strip=False).convert('RGB').crop((40, 150, 300, 410))
        CELLS[4], CELLS[5] = f5, f6
    return CELLS

# ---------------------------------------------------------------- sound
def readwav(p):
    w = wave.open(str(p)); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    if w.getnchannels() == 2: x = x.reshape(-1, 2).mean(1)
    return x, w.getframerate()

def sound(mix):
    r = kit.RATE
    room, rr = readwav(TS / 'room.wav')
    seg = room[int(5.0 * rr): int(5.0 * rr) + int(DUR * rr) + 10]
    seg = seg / (np.sqrt(np.mean(seg ** 2)) + 1e-9) * 0.012
    n = min(len(seg), mix.n); mix.L[:n] += seg[:n]; mix.R[:n] += seg[:n] * 0.95
    th, _ = readwav(TS / 'thud.wav'); th = th / np.abs(th).max()
    tland = S['key_contact_frame'] / FPS
    mix.add(th[int(0.030 * r): int(0.33 * r)], tland, 0.55, -0.1)
    mix.click(tland, 0.22, -0.1, bright=7500, seconds=0.025)              # declared kit synth: brass tick
    mix.click(tland + 4 / FPS, 0.06, -0.1, bright=7000, seconds=0.015)    # the one bounce returns (frame 4)
    st, _ = readwav(L.SRC / 'editor' / 'footstep_gravel.wav')
    cts = S['contacts']
    gr = st[int(0.085 * r): int(0.40 * r)].copy(); gr[:int(0.003 * r)] *= np.linspace(0, 1, int(0.003 * r))
    for i, tc in enumerate(cts):
        rate = (0.90, 1.06, 0.96, 1.10, 0.93, 1.02, 0.98)[i % 7]
        g = np.interp(np.arange(int(len(gr) / rate)) * rate, np.arange(len(gr)), gr); g = g / (np.abs(g).max() + 1e-9)
        dist = i / max(1, len(cts) - 1)
        g = mix.lowpass(g, 5200 * (1 - 0.7 * dist))
        mix.add(g, tc, 0.42 * (1 - 0.75 * dist), 0.2 - 0.7 * dist)

film = Film('test-shot', DUR, boil=0)
@film.picture
def _pic(t, ink):
    ink.img = render(t, ink.i).convert('RGB')
    ink._grain = False                       # no synthetic grain: texture is the real material and paper
film.sound(sound)
film.poster_at = S['pair_frame']['local_t']   # S5c start + 2.5 s: the beat-5 pair frame

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        for tt in [float(x) for x in sys.argv[2:]]:
            render(tt, int(round(tt * FPS))).convert('RGB').save(f'/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/s5c_{tt:.2f}.png')
    else:
        film.render(out_dir=L.MEDIA)
