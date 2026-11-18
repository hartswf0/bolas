"""Editor beats for La Belle Hortense: the slots the animator unit left to print-sound / the editor.

Built with the animator's own scene module (same dyed plates, same cut pieces, same key, same integrator),
so every motif keeps one signature.  Output: silent 960x540 24 fps clips (no type; the film script lays
U4's slot type over everything) in films/sources/la-belle-hortense/editor/clips/.

    python3 -I films/swarm/la-belle-hortense/editor/editor_beats.py [name ...]

Streak progression (camera drift during the 180-degree shutter, integrated over N sub-frames, never a blur
kernel): module II 60 px/s, III 120 px/s, IV 200 px/s, VI 0.
"""
import os, sys, math, json
import numpy as np, cv2
from PIL import Image

ROOT = '/home/user/bolas/paeleo/scion/oulipo'
sys.path.insert(0, os.path.join(ROOT, 'films/swarm/la-belle-hortense/animator'))
import scene as S                      # noqa: E402  (animator unit's module, our own code)
import beats as B                      # noqa: E402
from scene import W, H, FPS, T, R, SY, tp, over, paint, sm   # noqa: E402

PRINT = os.path.join(ROOT, 'films/sources/la-belle-hortense/print-sound/print')
OUT = os.path.join(ROOT, 'films/sources/la-belle-hortense/editor/clips')
STILLS = os.path.join(ROOT, 'films/sources/la-belle-hortense/editor/stills')
os.makedirs(OUT, exist_ok=True); os.makedirs(STILLS, exist_ok=True)


def png(name):
    return np.asarray(Image.open(os.path.join(PRINT, name)).convert('RGBA'), np.float32) / 255.


def place(fr, rgba, cx, cy, s=1.0, ang=0.0, sy=1.0, shade=1.0):
    """paint a print object centred at (cx, cy), scale s, rotation ang (deg), vertical foreshortening sy."""
    h, w = rgba.shape[:2]
    M = T(cx, cy) @ R((0, 0), ang) @ np.diag([s, s * sy, 1.0]) @ T(-w / 2, -h / 2)
    p = rgba if shade == 1.0 else np.dstack([rgba[..., :3] * shade, rgba[..., 3]])
    return paint(fr, p, M), M


def drop_shadow(fr, M, size, k=0.55, off=(6, 8), blur=7):
    """contact shadow of a flat object: its own quad, offset and softened (a cut mask, not an image blur)."""
    w, h = size
    m = cv2.warpAffine(np.ones((h, w), np.float32), (T(*off) @ M)[:2], (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    m = cv2.GaussianBlur(m, (0, 0), blur)
    return fr * (1 - (1 - k) * m[..., None])


# ------------------------------------------------------------------ the shed door (Bourre 50866795131, dyed)
DOOR_C = (500.0, 545.0)          # centre of the goods-shed door, plate px (leaves meet at x=500)
PLATE_AT = (470.0, 505.0)        # handmade enamel "6", screwed to the LEFT leaf (the right leaf swings in V.5)
PLATE_PX = 30.0                  # its width in plate px
ENAMEL = png('enamel_plate_6.png')


def door_view(z, c):
    sh = S.plate('shed')
    M = np.float32([[z, 0, W / 2 - c[0] * z], [0, z, H / 2 - c[1] * z]])
    return cv2.warpAffine(sh, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT), M


def to_screen(M, p):
    return (M[0, 0] * p[0] + M[0, 2], M[1, 1] * p[1] + M[1, 2])


def door_rattle(fr, M, amp):
    """the two leaves shake in their frame: the leaf region of the print shifted by a few px."""
    if amp == 0:
        return fr
    x0, y0 = to_screen(M, (442, 458)); x1, y1 = to_screen(M, (559, 622))
    x0, y0, x1, y1 = [int(round(v)) for v in (x0, y0, x1, y1)]
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W), min(y1, H)
    if x1 <= x0 or y1 <= y0:
        return fr
    region = fr[y0:y1, x0:x1].copy()
    Ms = np.float32([[1, 0, amp], [0, 1, 0.3 * amp]])
    fr[y0:y1, x0:x1] = cv2.warpAffine(region, Ms, (x1 - x0, y1 - y0), borderMode=cv2.BORDER_REPLICATE)
    return fr


def enamel_on(fr, M, s_extra=1.0, drop=0.0):
    x, y = to_screen(M, PLATE_AT)
    s = PLATE_PX * M[0, 0] / ENAMEL.shape[1] * s_extra
    fr, Mp = place(fr, ENAMEL, x, y - drop, s)
    return fr


# the conductor's hand: forearm piece of LoC 2017844115 printed monochrome (no red: the coat is still on the bench)
FORE_MONO = S.rgba(S.mono(S.G), S.PZ['fore_a'])
GRIP = (128.0, 238.0)            # the closed fingers, piece px


def II1(t):
    """12.0-13.5  tight on the door: the conductor's hand comes in from the right, grips, rattles. Locked."""
    cx = DOOR_C[0] - 8 + 60 * t / 2.6
    fr, M = door_view(2.6, (cx, DOOR_C[1] - 5))
    gx, gy = to_screen(M, (503, 548))
    reach = sm((t - 0.05) / 0.25) * (1 - sm((t - 1.05) / 0.3))
    rattle = 0.0
    if 0.2 <= t < 0.62:
        rattle = 5.0 * math.sin(2 * math.pi * 9 * (t - 0.2))
    fr = door_rattle(fr, M, 0.35 * rattle)
    hx = gx + (1 - reach) * 520
    hy = gy + (1 - reach) * 140 + 0.6 * rattle
    Mh = T(hx, hy) @ R((0, 0), -8 + rattle) @ np.diag([1.45, 1.45, 1.0]) @ T(-GRIP[0], -GRIP[1])
    fr = paint(fr, FORE_MONO, Mh)
    return fr


def III2(t):
    """22.5-24.0  the door, wider: still locked; the leaves rattle (handle_rattle_b at 22.7)."""
    fr, M = door_view(2.1, (DOOR_C[0] + 20 - 120 * t / 2.1, DOOR_C[1] - 25))
    amp = 2.4 * math.sin(2 * math.pi * 11 * (t - 0.2)) * (1 - sm((t - 0.45) / 0.25)) if t >= 0.2 else 0.0
    return door_rattle(fr, M, amp)


RECEIPT = {k: png(f'receipt_{k}.png') for k in ('0_plain', '1_struck', '2_underlined', '2b_underlined_unstruck', '3_rendu')}
STRIKE = [png(f'receipt_strike_{i:02d}.png') for i in range(1, 8)]
UNDER = [png(f'receipt_underline_{i:02d}.png') for i in range(1, 15)]


def IV1(t):
    """30.0-31.5  the enamel 6 is laid on the door; the underlined receipt slides in beside it: N 6 = door 6."""
    fr, M = door_view(2.2, (DOOR_C[0] + 70 - 200 * t / 2.2, DOOR_C[1] - 30))
    u = sm((t - 0.10) / 0.22)
    if u > 0:
        x, y = to_screen(M, PLATE_AT)
        s = PLATE_PX * M[0, 0] / ENAMEL.shape[1] * (1.35 - 0.35 * u)
        _, Mp = place(fr.copy(), ENAMEL, x, y - 40 * (1 - u), s)
        fr = drop_shadow(fr, Mp, (ENAMEL.shape[1], ENAMEL.shape[0]), 0.5 + 0.5 * u if u < 1 else 0.78, (3, 4), 3)
        fr, _ = place(fr, ENAMEL, x, y - 40 * (1 - u), s)
    v = sm((t - 0.45) / 0.45)
    if v > 0:
        rx = 1180 - 460 * v; ry = 170
        _, Mr = place(fr.copy(), RECEIPT['2_underlined'], rx, ry, 0.56, -4 + 6 * (1 - v))
        fr = drop_shadow(fr, Mr, (600, 340), 0.6)
        fr, _ = place(fr, RECEIPT['2_underlined'], rx, ry, 0.56, -4 + 6 * (1 - v))
    return fr


def IV4(t):
    """34.5-36.0  close on the lock between the leaves: dark, shut.  The enamel 6 at the top left."""
    z = 3.5 + 0.35 * sm(t / 1.5)
    fr, M = door_view(z, (DOOR_C[0] + 2 - 200 * t / z / 3, DOOR_C[1] + 2))
    amp = 1.6 * math.sin(2 * math.pi * 12 * (t - 0.2)) * (1 - sm((t - 0.5) / 0.25)) if t >= 0.2 else 0.0
    fr = door_rattle(fr, M, amp)
    return enamel_on(fr, M)


def VI3_from(v5_last):
    """51.0-52.5  the door stands open: the last V.5 pose (leaf swung in, dark inside) + enamel, slow push."""
    def f(t):
        z = 1.0 + 0.05 * sm(t / 1.5)
        cxs, cys = 480.0, 280.0
        M = np.float32([[z, 0, cxs - cxs * z], [0, z, cys - cys * z]])
        return cv2.warpAffine(v5_last, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return f


V5_M = np.float32([[1.15, 0, -int(500 * 1.15 - W / 2)], [0, 1.15, -int(545 * 1.15 - H / 2)]])    # beats.V5 framing


def ground_view(t, speed, z=1.0):
    """the gravel and grass at the bench (meadow plate, dyed), seen from above as in I.3, drifting."""
    g = S.plate('meadow')
    c = (520.0 + speed * t / z, 780.0)
    M = np.float32([[1.5 * z, 0, W / 2 - c[0] * 1.5 * z], [0, 1.5 * z, H / 2 - c[1] * 1.5 * z]])
    return cv2.warpAffine(g, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


REC_X, REC_Y, REC_S, REC_A = 650.0, 200.0, 0.84, -3.0      # the receipt held up to the lens (clear of the type block)


def receipt_held(fr, img, jolt=0.0):
    _, Mr = place(fr.copy(), img, REC_X, REC_Y + jolt, REC_S, REC_A)
    fr = drop_shadow(fr, Mr, (600, 340), 0.5, (10, 14), 9)
    fr, _ = place(fr, img, REC_X, REC_Y + jolt, REC_S, REC_A)
    return fr


def II3(t):
    """15.0-16.5  he picks up the ticket from the gravel: it rises and turns to us; 'remise au banc' legible."""
    fr = ground_view(t, 60)
    u = sm((t - 0.15) / 0.8)
    x = 520 + (REC_X - 520) * u; y = 380 + (REC_Y - 380) * u - 40 * math.sin(math.pi * u)
    s = 0.45 + (REC_S - 0.45) * u; a = 24 + (REC_A - 24) * u; sy = 0.45 + 0.55 * u
    _, Mr = place(fr.copy(), RECEIPT['0_plain'], x, y, s, a, sy)
    fr = drop_shadow(fr, Mr, (600, 340), 0.45 + 0.1 * u, (4 + 10 * u, 5 + 14 * u), 2 + 7 * u)
    fr, _ = place(fr, RECEIPT['0_plain'], x, y, s, a, sy, shade=0.92 + 0.08 * u)
    return fr


def II6(t):
    """19.5-21.0  'une cle' is struck through in red, typed over (7 strokes from 19.7 s, one per 0.085 s)."""
    fr = ground_view(1.5 + t, 60)
    k = int((t - 0.2) / 0.085) + 1 if t >= 0.2 else 0
    img = RECEIPT['0_plain'] if k == 0 else STRIKE[min(k, 7) - 1]
    return receipt_held(fr, img)


def III6(t):
    """28.5-30.0  'remise au banc' underlined in red (14 strokes from 28.7 s, one per 0.07 s)."""
    fr = ground_view(3.0 + t, 120)
    k = int((t - 0.2) / 0.07) + 1 if t >= 0.2 else 0
    img = RECEIPT['1_struck'] if k == 0 else UNDER[min(k, 14) - 1]
    return receipt_held(fr, img)


def VI4(t):
    """52.5-54.0  the RENDU stamp thumps onto the ticket at 52.65 s (local 0.15)."""
    fr = ground_view(0.0, 0)
    stamped = t >= 0.15
    jolt = 5.0 * math.exp(-(t - 0.15) / 0.05) if stamped else 0.0
    return receipt_held(fr, RECEIPT['3_rendu'] if stamped else RECEIPT['2_underlined'], jolt)


def III1(t):
    """21.0-22.5  the visitor as a shadow-theatre silhouette (Reiniger replacement turn): front profile turns
    (x foreshortened by cos) to the back profile, as if walking off with something in her closed hand."""
    v = B.View(1.5, (380.0 + 120 * t / 1.5, 600.0))
    fr = B.wide_bg(v)
    u = sm((t - 0.35) / 0.8)
    sx = math.cos(math.pi * u)
    src = S.VISF if sx >= 0 else S.VISB
    sil = np.dstack([np.zeros_like(src[..., :3]) + S.INK, src[..., 3]])
    hh = 400.0
    s = hh / src.shape[0]
    x, y = 300.0, 500.0
    M = T(x, y) @ np.diag([s * max(abs(sx), 0.06), s, 1.0]) @ T(-src.shape[1] / 2, -src.shape[0])
    fr = B.shadow(fr, x, y, 50, 9)
    return paint(fr, sil, M)


HOOK_AT = (612.0, 470.0)         # a nail in the shed wall right of the door, plate px


def hook_draw(fr, x, y, s):
    """HANDMADE: a bent iron wire hook (cut and bent for this film, drawn as its own flat object)."""
    m = np.zeros((H, W), np.float32)
    pts = np.int32([[x - 2 * s, y - 14 * s], [x, y], [x + 1 * s, y + 9 * s], [x + 7 * s, y + 12 * s], [x + 11 * s, y + 6 * s]])
    cv2.polylines(m, [pts], False, 1.0, max(2, int(3.2 * s)), cv2.LINE_AA)
    cv2.circle(m, (int(x - 2 * s), int(y - 14 * s)), max(2, int(3.5 * s)), 1.0, -1, cv2.LINE_AA)
    fr = fr * (1 - 0.35 * cv2.GaussianBlur(m, (0, 0), 2)[..., None])     # its contact shade on the wall
    return over(fr, np.array([0.09, 0.085, 0.075], np.float32), m)


def VI5(t):
    """54.0-55.5  the key hung back on its hook (tink at 54.2), swinging as a damped pendulum to rest."""
    fr, M = door_view(2.6, (590.0, 500.0))
    fr = enamel_on(fr, M)
    hx, hy = to_screen(M, HOOK_AT)
    s = 2.7
    kh, kw = S.KEY.shape[:2]
    bow = (kw / 2, kh * 0.80)                 # the bow hole: the key hangs from it, shaft down
    u = sm(t / 0.2)
    if t < 0.2:
        ang = 30 * (1 - u); dy = 90 * (1 - u)
    else:
        tt = t - 0.2
        ang = 16 * math.exp(-tt / 0.9) * math.cos(2 * math.pi * 1.15 * tt); dy = 0.0
    fr = S.draw_key(fr, hx, hy + 6 + dy, 180 + ang, kp=bow, s=s)
    return hook_draw(fr, hx, hy, 3.0)


def TITLE(t):
    """0-3 s  a real pan exposure over the run stage: each frame integrates 420 px of ground-plane travel."""
    planes = S.run_stage()
    n = 40
    acc = np.zeros((H, W, 3), np.float32)
    c0 = 900 + 40 * t
    for i in range(n):
        cx = c0 + 420 * ((i + 0.5) / n - 0.5)
        fr = np.zeros((H, W, 3), np.float32)
        for p in planes:
            p.draw(fr, cx, 1200)
        acc += fr
    return acc / n


def write(name, fn, nframes, n_sub, shutter=0.5, still_at=None):
    w = S.Writer(os.path.join(OUT, name + '.mp4'))
    for k in range(nframes):
        t = (k + 0.5) / FPS
        a = S.integrate(fn, t, n_sub, shutter) if n_sub > 1 else fn(t)
        img = S.to_img(a)
        w.add(img)
        if k == (still_at if still_at is not None else nframes // 2):
            img.save(os.path.join(STILLS, name + '_mid.png'))
    w.close()
    print('wrote', name, flush=True)


def VI3():
    v5 = B.V5(1.5)
    v5 = enamel_on(v5, V5_M)
    return VI3_from(v5)


JOBS = {
    'TITLE': (TITLE, 72, 1), 'II1_porte': (II1, 36, 6), 'II3_recu': (II3, 36, 6), 'II6_cle': (II6, 36, 1),
    'III1_cle': (III1, 36, 6), 'III2_porte': (III2, 36, 6), 'III6_recu': (III6, 36, 1),
    'IV1_recu': (IV1, 36, 8), 'IV4_porte': (IV4, 36, 8), 'VI3_porte': (None, 36, 1), 'VI4_recu': (VI4, 36, 1),
    'VI5_cle': (VI5, 36, 1),
}

def BASE_I1(t):
    """baseline only: the wide station with NO coat on the bench."""
    v = B.View(1.0)
    return B.draw_bench(B.wide_bg(v), v)


def BASE_I4(t):
    """baseline only: I.4 with the key laid on the bare bench (no coat)."""
    v = B.View(1.0)
    fr = B.draw_bench(B.wide_bg(v), v)
    bend, u = B.lay_key_state(t)
    x, y = v.pt((560, 690))
    fr = B.shadow(fr, x, y, 18, 4)
    fr, hand = S.walker_draw(fr, S.VISF, x, y, 0.9 * B.VIS_S, 0.0, hz=0.0, bend=bend)
    hx_, hy_ = hand[0] + 18 + 30 * bend, hand[1] + 40 * bend
    kx, ky = B.key_on_coat_pt(v)
    ky += 14
    if u < 1:
        px = hx_ + (kx - hx_) * u; py = hy_ + (ky - hy_) * u - 30 * math.sin(math.pi * u)
        return S.draw_key(fr, px, py, 30 + 40 * u, s=0.5)
    fr = B.shadow(fr, kx + 2, ky + 4, 10, 2.5, 0.6)
    return S.draw_key(fr, kx, ky, 70, s=0.5)


BASEJOBS = {'BASE_I1': (BASE_I1, 36, 1), 'BASE_I4': (BASE_I4, 36, 4)}

if __name__ == '__main__':
    if sys.argv[1:] == ['baseline']:
        for name, (fn, nf, ns) in BASEJOBS.items():
            write(name, fn, nf, ns)
        sys.exit()
    only = sys.argv[1:]
    for name, (fn, nf, ns) in JOBS.items():
        if only and name not in only:
            continue
        if name == 'VI3_porte':
            fn = VI3()
        write(name, fn, nf, ns)
