"""Cercle vicieux TEST SHOT: end of H on page 2 -> purposeful p2->p3 leaf turn -> X (hinge, 5.2 s) -> H again.
Pages are composed from the canonical panels (panels.py) at 2x and are the same bytes in page and film.
Run: python3 -I build.py   (writes test-page.png, test-page-p2.png, test-shot.mp4, test-shot-compare.jpg)"""
import sys, math, json, wave, hashlib
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/cercle-vicieux/test-shot-build")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films")
import numpy as np, cv2
from PIL import Image, ImageDraw
import panels as P
import ink as K
from pathlib import Path
import kit

ROOT = "/home/user/bolas/paeleo/scion/oulipo/"
WS = ROOT + "films/swarm/cercle-vicieux/"
SRC = P.SRC
SS = P.SS
PW, PH = 2400, 1350
PAPER = 250.0           # #FAFAF8 (neutral, B channel -2)
DESK = 26.0

# ---------------------------------------------------------------- layout (1x page px)
CW, CH = 800, 590
P2 = {"E": (385, 70), "F": (1215, 70), "G": (385, 690), "H": (1215, 690)}
P3 = {"X": (60, 70), "H": (690, 70), "G": (1520, 70), "F": (690, 690), "E": (1520, 690)}


def border_mask(boxes, seed):
    m = Image.new("L", (PW * SS, PH * SS), 0); d = ImageDraw.Draw(m)
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        K.brush_poly(d, [(x0 * SS, y0 * SS), (x1 * SS, y0 * SS), (x1 * SS, y1 * SS), (x0 * SS, y1 * SS)], 12, seed + i, fill=255)
    return np.asarray(m, np.float32) / 255


def folio(img, n):
    im = Image.fromarray(img.astype(np.uint8), "L")
    im, _ = K.letter_line(im, "- %d -" % n, PW * SS / 2, 1316 * SS, 26 * SS, seed=900 + n)
    return np.asarray(im, np.float32)


_static = {}


def page_base(n):
    """Paper, folio and the hand-jogged panel borders for page n (static)."""
    if n not in _static:
        lay = P2 if n == 2 else P3
        paper = np.full((PH * SS, PW * SS), PAPER, np.float32)
        paper = folio(paper, n)
        bm = np.zeros_like(paper)
        for k, (x, y) in lay.items():         # each panel's border is part of the panel: same jogs everywhere
            w, h = (600, 1210) if k == "X" else (CW, CH)
            bm = np.maximum(bm, border_mask([(x, y, x + w, y + h)], 40 + ord(k)))
        _static[n] = (paper, bm, None)
    return _static[n]


_cells = {}


def cell(name, k=None):
    key = (name, k)
    if key not in _cells:
        if name == "H":
            _cells[key] = P.panel_h(k)
        elif name == "G":
            _cells[key] = P.panel_g()[0]
        elif name == "F":
            _cells[key] = P.panel_f()
        elif name == "E":
            _cells[key] = P.panel_e()
    return _cells[key]


H_STILL = int(3.5 * 24) - 1


def page(n, xk=P.X_CYCLE - 1, hk=H_STILL):
    """Page n as an RGB uint8 array at 2x. xk/hk = frame of X and H cycles shown."""
    paper, bm, boxes = page_base(n)
    g = paper.copy()
    warm_full = np.zeros_like(g)
    lay = P2 if n == 2 else P3
    for name, (x, y) in lay.items():
        if name == "X":
            v, warm = P.panel_x(xk)
            g[y * SS:y * SS + v.shape[0], x * SS:x * SS + v.shape[1]] = v
            warm_full[y * SS:y * SS + v.shape[0], x * SS:x * SS + v.shape[1]] = warm
        else:
            v = cell(name, hk if name == "H" else None)
            g[y * SS:y * SS + v.shape[0], x * SS:x * SS + v.shape[1]] = v
    g = g * (1 - bm) + P.BLACK * bm
    warm_full *= (1 - bm)
    rgb = np.stack([g, g, g - 2], -1)          # neutral paper #FAFAF8
    tint = np.array([1.0, 242 / 246, 230 / 246], np.float32)   # frosted pane #F6F2E6: the only warm tint
    rgb = rgb * (1 - warm_full[..., None]) + (g[..., None] * tint) * warm_full[..., None]
    return np.clip(rgb, 0, 255).astype(np.uint8)


def to1x(a):
    return cv2.resize(a, (PW, PH), interpolation=cv2.INTER_AREA)


# ---------------------------------------------------------------- camera
FW, FH = 960, 540


def shoot(img2x, cx, cy, w):
    """Rostrum camera: rect centred (cx,cy) in page px, width w, 16:9; desk beyond the page edge."""
    h = w * 9 / 16
    s = FW / (w * SS)
    M = np.array([[s, 0, FW / 2 - cx * SS * s], [0, s, FH / 2 - cy * SS * s]], np.float32)
    if s < 0.5:      # pre-reduce to avoid aliasing on wide shots
        f = 0.5 / s
        small = cv2.resize(img2x, (int(img2x.shape[1] / f), int(img2x.shape[0] / f)), interpolation=cv2.INTER_AREA)
        M[:, :2] *= f
        img2x = small
    return cv2.warpAffine(img2x, M, (FW, FH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                          borderValue=(DESK, DESK, DESK))


def lerpcam(a, b, u):
    u = u * u * (3 - 2 * u)
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


FULL = (1200, 675, 2544)
H2 = (1215 + 400, 690 + 295, 1090)
H3 = (690 + 400, 70 + 295, 1090)
PANE = (500, 560, 1050)

# timeline (s)
T_PULL = (0.6, 1.3)
T_TURN = (1.3, 2.8)
T_X = 2.8
T_PUSH = (3.3, 4.1)
T_LEAVE = (6.8, 8.0)
T_H = 8.0
DUR = 10.0


def leaf_turn(p2, p3, u):
    """Physical leaf: page 2 lifts at its right edge, hinged at the left (recto-only booklet), its blank back
    comes over onto the desk; its cast shadow sweeps across page 3 (over X) as it goes."""
    phi = math.pi * (u * u * (3 - 2 * u))
    cx, cy, w = FULL
    h = w * 9 / 16
    scale = FW / w
    canvas = np.full((FH, FW, 3), DESK, np.float32)
    ox, oy = (cx - w / 2), (cy - h / 2)
    def C(x, y): return ((x - ox) * scale, (y - oy) * scale)
    p3s = cv2.resize(p3, (int(PW * scale), int(PH * scale)), interpolation=cv2.INTER_AREA).astype(np.float32)
    x0, y0 = C(0, 0)
    xi, yi = int(round(x0)), int(round(y0))
    canvas[yi:yi + p3s.shape[0], xi:xi + p3s.shape[1]] = p3s[:FH - yi, :FW - xi]
    # cast shadow on page 3
    xe = PW * math.cos(phi)
    if phi < math.pi / 2:
        a, b = xe, xe + PW * 0.22 * math.sin(phi)
    else:
        a, b = 0, PW * 0.40 * math.sin(phi)
    xs = np.arange(FW) / scale + ox
    sh = np.clip((xs - a) / max(1, b - a), 0, 1)
    dark = np.where((xs >= a) & (xs <= b), 0.55 + 0.45 * sh, 1.0) if b > a else np.ones(FW)
    page_rows = slice(yi, yi + p3s.shape[0])
    canvas[page_rows] *= dark[None, :, None]
    # the leaf
    g = 1 + 0.10 * math.sin(phi)
    top, bot = 0 - PH * (g - 1) / 2, PH + PH * (g - 1) / 2
    if abs(math.cos(phi)) > 1e-3:
        if phi < math.pi / 2:
            srcimg = cv2.resize(p2, (int(PW * scale), int(PH * scale)), interpolation=cv2.INTER_AREA).astype(np.float32)
            shade = 0.80 + 0.20 * math.cos(phi)
        else:
            srcimg = np.full((int(PH * scale), int(PW * scale), 3), PAPER, np.float32)   # blank verso
            srcimg[..., 2] -= 2
            shade = 0.70 + 0.28 * abs(math.cos(phi))
        sw, shh = srcimg.shape[1], srcimg.shape[0]
        src = np.float32([[0, 0], [sw, 0], [sw, shh], [0, shh]])
        dst = np.float32([C(0, 0), C(xe, top), C(xe, bot), C(0, PH)])
        Mx = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(srcimg, Mx, (FW, FH), flags=cv2.INTER_LINEAR)
        mask = cv2.warpPerspective(np.ones((shh, sw), np.float32), Mx, (FW, FH), flags=cv2.INTER_LINEAR)
        # light falls off across the curling leaf
        canvas = canvas * (1 - mask[..., None]) + warped * shade * mask[..., None]
    return np.clip(canvas, 0, 255).astype(np.uint8)


def frame_at(k):
    t = k / 24
    if t < T_TURN[0]:
        img = page(2)
        cam = H2 if t < T_PULL[0] else lerpcam(H2, FULL, (t - T_PULL[0]) / (T_PULL[1] - T_PULL[0]))
        return shoot(img, *cam)
    if t < T_TURN[1]:
        u = (t - T_TURN[0]) / (T_TURN[1] - T_TURN[0])
        return leaf_turn(to1x(page(2)), to1x(page(3, xk=0, hk=0)), u)
    if t < T_H:
        xk = min(P.X_CYCLE - 1, int(round((t - T_X) * 24)))
        img = page(3, xk=xk, hk=0)
        if t < T_PUSH[0]:
            cam = FULL
        elif t < T_PUSH[1]:
            cam = lerpcam(FULL, PANE, (t - T_PUSH[0]) / (T_PUSH[1] - T_PUSH[0]))
        elif t < T_LEAVE[0]:
            cam = PANE
        else:
            cam = lerpcam(PANE, H3, (t - T_LEAVE[0]) / (T_LEAVE[1] - T_LEAVE[0]))
        return shoot(img, *cam)
    hk = min(H_STILL, int(round((t - T_H) * 24)))
    return shoot(page(3, hk=hk), *H3)


# ---------------------------------------------------------------- sound
def read_wav(path):
    w = wave.open(path)
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    if w.getnchannels() == 2:
        a = a.reshape(-1, 2).mean(1)
    return a, w.getframerate()


def sound(mix):
    rate = mix.rate
    bell, br = read_wav(SRC + "bell.wav")
    strike = bell[int(2.20 * br):int(5.70 * br)]            # one clean strike of the foraged theatre bell
    strike = mix.band(strike, 120, 2600)                    # muffled: heard through the station's hush
    strike *= np.minimum(1, np.arange(len(strike)) / 40)
    room, rr = read_wav(SRC + "roomtone.wav")
    room = room[:int(DUR * rate)]
    room = room / (np.abs(room).max() + 1e-9)
    n = mix.n
    t = np.arange(n) / rate
    g = np.interp(t, [0, 0.6, 1.25, 2.75, 3.3, 8.0, 10.0], [0.10, 0.10, 0.004, 0.004, 0.07, 0.07, 0.08])
    bed = np.zeros(n); bed[:len(room)] = room[:n]
    mix.add(bed * g, 0.0, 1.0)
    # paper: the leaf lifting and laying down (synthesized from noise, declared)
    nz = mix.noise(1.5, "pink")
    env = np.interp(np.arange(len(nz)) / rate, [0, .15, .6, 1.2, 1.38, 1.5], [0, .5, .25, .35, 1.0, 0])
    mix.add(mix.band(nz, 500, 7000) * env * 0.10, T_TURN[0], 1.0, pan=0.2)
    # bell strikes exactly where the simulated clapper hits the rim
    _, _, _, _, _, strikes = P.simulate_x()
    for ts, v in strikes:
        if v > 1.0:
            mix.add(strike, T_X + ts, min(1.0, v / 10) * 0.55, pan=-0.1)
    # cord creak at each pull (synthesized friction grains, declared)
    for t0 in (1.25, 2.55):
        m = mix.noise(0.30)
        grains = (np.sin(2 * np.pi * 38 * np.arange(len(m)) / rate) > 0.6).astype(float)
        cr = mix.band(m, 350, 1400) * grains * np.exp(-np.arange(len(m)) / rate / 0.12)
        mix.add(cr * 0.06, T_X + t0, 1.0, pan=-0.05)


# ---------------------------------------------------------------- outputs
def main():
    # pages: the test page (page 3 with every panel at its held still) and page 2 (its neighbour)
    p3 = to1x(page(3)); p2 = to1x(page(2))
    Image.fromarray(p3).save(WS + "test-page.png")
    Image.fromarray(p2).save(WS + "test-page-p2.png")
    L = cv2.cvtColor(p3, cv2.COLOR_RGB2GRAY)
    tone = dict(white=float((L > 200).mean()), black=float((L < 60).mean()), mid=float(((L >= 60) & (L <= 200)).mean()))
    print("page 3 tone", tone)
    film = kit.Film("test-shot", seconds=DUR, boil=0, wobble=0)

    def pic(t, inkc):
        inkc.paper(grain=False)
        inkc.img.paste(Image.fromarray(frame_at(int(round(t * 24)))))
    film.picture(pic)
    film.sound(sound)
    film.poster_at = 4.6
    film.render(out_dir=Path(WS))
    # identity check: H's panel layer on p2 equals H's panel layer on p3 (still)
    a = page(2)[690 * SS:(690 + CH) * SS, 1215 * SS:(1215 + CW) * SS]
    b = page(3)[70 * SS:(70 + CH) * SS, 690 * SS:(690 + CW) * SS]
    print("H identical p2/p3 (panel layer):", hashlib.sha256(a.tobytes()).hexdigest() == hashlib.sha256(b.tobytes()).hexdigest())
    json.dump(tone, open(SRC + "work/tone.json", "w"))


if __name__ == "__main__":
    main()
