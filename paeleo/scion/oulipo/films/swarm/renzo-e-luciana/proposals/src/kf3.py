"""KF3 · Cartellini: the rule as a handmade light-box score. Three slotted card strips (Renzo's break, Luciana's
break, the safe corner) are stacked on a light box; light passes only where all three slots coincide, and that lit
slot is the stage on which two small cut-paper lovers stand. Beat: late-bell version, t = 33 s: Luciana's strip is
sliding from [12:00,12:04) to [12:03,12:07) and its edge is closing the window on them (now 12:02 -> 12:03)."""
import sys; sys.path.insert(0, '.')
from common import *
import math
K = 2; CW, CH = W * K, H * K
def Pi(a): return (int(round(a[0] * K)), int(round(a[1] * K)))
X0, PX = 170, 118                         # x of 12:00 and px per minute on the score
def xm(m): return X0 + m * PX
BX0, BX1, BY0, BY1 = 120, 1170, 282, 512   # light box aperture
# desk: grey board with fibre; light box frame
desk = cv2.resize(paper(W, H, base=92, seed=31, fibre=9), (CW, CH))
img = np.stack([desk] * 3, -1).astype(np.float32)
Y, X = np.mgrid[0:CH, 0:CW].astype(np.float32)
glow = np.exp(-(((X - CW * .5) / (CW * .55)) ** 2 + ((Y - CH * .53) / (CH * .45)) ** 2))
img *= (0.8 + 0.35 * glow)[..., None]
cv2.rectangle(img, Pi((BX0 - 26, BY0 - 30)), Pi((BX1 + 26, BY1 + 30)), (38, 37, 36), -1)
# strips: (label, slot [a,b) in minutes, y-band, offset)
STR = [('ANGOLO SICURO · dietro le cassette', (1, 4), (BY0 - 10, BY1 + 10), 0, 201),
       ('LUCIANA · reparto 5 · pausa', (0 + 2.0, 4 + 2.0), (BY0 - 2, BY1 + 2), 0, 214),   # sliding late: +2.0 of +3 min
       ('RENZO · reparto 3 · pausa', (0, 3), (BY0 + 6, BY1 - 6), 0, 226)]
trans = np.ones((CH, CW), np.float32)       # light transmission through the stack
inbox = np.zeros((CH, CW), np.float32); cv2.rectangle(inbox, Pi((BX0, BY0)), Pi((BX1, BY1)), 1, -1)
rng = np.random.default_rng(4)
for i, (lab, (a, b), (y0, y1), off, tone) in enumerate(STR):
    m = np.zeros((CH, CW), np.uint8)
    sx0, sx1 = 60 + i * 6, 1230 - i * 4
    cv2.rectangle(m, Pi((sx0, y0)), Pi((sx1, y1)), 255, -1)
    slot = np.zeros_like(m); cv2.rectangle(slot, Pi((xm(a), y0 + 26 + 8 * i)), Pi((xm(b), y1 - 12)), 255, -1)
    m = cut_edge(cv2.subtract(m, slot), seed=40 + i, amp=.05)
    mf = m.astype(np.float32) / 255
    # shadow of this strip on what's below (only outside the lit box it reads)
    sh = cv2.GaussianBlur(np.roll(np.roll(mf, 6 * K, 0), 5 * K, 1), (0, 0), 5 * K)
    img *= (1 - .38 * sh * (1 - inbox))[..., None]
    card = cv2.resize(paper(W, H, base=tone, seed=50 + i, fibre=6), (CW, CH))
    img = img * (1 - mf[..., None]) + np.stack([card] * 3, -1) * mf[..., None]
    trans *= (1 - .42 * mf)
    STR[i] = (lab, (a, b), (y0, y1), m)
# backlight: where the stack lies over the light box the cards glow; the coincident slot is white
light = 255 * trans * inbox
lit = inbox > 0
img[lit] = (img[lit] * .15 + (np.stack([light, light * .97, light * .9], -1)[lit]) * .9)
img[(inbox > 0) & (trans > .99)] = (250, 248, 240)
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(im)
f1 = font(15 * K, '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf'); f2 = font(13 * K, '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf')
fs = font(30 * K); ft = font(18 * K, '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')
# printed labels on the left tail of each strip (the ink sits on the card, outside the box)
labs = [('ANGOLO SICURO', 'accesso 12:01-12:04', 196), ('LUCIANA  rep. 5', 'pausa 12:00-12:04  >> +3', 196 + 0), ('RENZO  rep. 3', 'pausa 12:00-12:03', 196)]
# score ruler: printed minute scale above the box, on a separate card
d.rectangle([Pi((BX0 - 10, 196)), Pi((BX1 + 10, 252))], fill=(214, 211, 202))
for m in range(0, 9):
    x = xm(m); d.line([Pi((x, 234)), Pi((x, 252))], fill=(30, 30, 30), width=3 * K)
    d.text(Pi((x - 26, 204)), f'12:0{m}', font=f1, fill=(30, 30, 30))
    if m < 8:
        for q in range(1, 4): xq = x + q * PX / 4; d.line([Pi((xq, 244)), Pi((xq, 252))], fill=(30, 30, 30), width=K)
# strip tags: little typed labels clipped onto the strips' tails, left of the box (one per strip, stepped)
tagy = [548, 598, 648]
names = [('RENZO', 'pausa  12:00 - 12:03', 'reparto 3'), ('LUCIANA', 'pausa  12:00 - 12:04  ->  12:03 - 12:07', 'reparto 5 · campanella in ritardo'), ('ANGOLO', 'accessibile  12:01 - 12:04', 'dietro le cassette')]
for k, (n, l1, l2) in enumerate(names):
    y = tagy[k]; x = 140
    d.rectangle([Pi((x, y)), Pi((x + 520, y + 42))], fill=(222, 218, 208))
    d.text(Pi((x + 10, y + 4)), n, font=f1, fill=(20, 20, 20)); d.text(Pi((x + 130, y + 4)), l1, font=f2, fill=(30, 30, 30))
    d.text(Pi((x + 130, y + 22)), l2, font=f2, fill=(70, 70, 70))
for k, (n, y) in enumerate([('ANGOLO', BY0 - 10 + 4), ('LUCIANA', BY0 - 2 + 12), ('RENZO', BY0 + 6 + 20)]):
    pass
# title card top-left, typeset
d.text(Pi((60, 52)), 'Pausa delle dodici', font=fs, fill=(226, 222, 212))
d.text(Pi((62, 102)), 'B · la campanella suona in ritardo', font=ft, fill=(200, 196, 186))
# the moving strip's direction, punched as three holes on the Luciana tail (index marks the feed travels)
im = im.convert('RGBA')
# two small cut-paper lovers standing on the light, in the coincident slot [12:02.4, 12:03)
gx0, gx1 = xm(2.0), xm(3)
floor = BY1 - 18
f = np.zeros((CH, CW), np.uint8)
def put(mask, crop, h, x_right=None, x_left=None, flip=False):
    m = mask[crop[1]:crop[3], crop[0]:crop[2]]
    if flip: m = m[:, ::-1]
    sc = h * K / m.shape[0]; m = cv2.resize(m, (int(m.shape[1] * sc), int(h * K)), interpolation=cv2.INTER_AREA)
    y = int(floor * K) - m.shape[0]
    x = int((x_left if x_left is not None else x_right - m.shape[1] / K) * K)
    x0 = max(x, 0); f[y:y + m.shape[0], x0:x + m.shape[1]] = np.maximum(f[y:y + m.shape[0], x0:x + m.shape[1]], m[:, x0 - x:])
def cr(pts, n=8):
    m = len(pts); out = []
    for i in range(m):
        p0, p1, p2, p3 = pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out
def bust(cx, base, sc, face=1, hat=False):
    """small cut-paper profile bust: shoulders, neck, profile head (face = +1 looks right, -1 left)."""
    T = lambda u, v: (cx + face * u * sc, base - v * sc)
    sh = [T(-46, 0), T(-44, 30), T(-30, 52), T(-8, 60), T(14, 58), T(34, 46), T(44, 24), T(46, 0)]
    neck = [T(-8, 56), T(-9, 76), T(9, 78), T(12, 56)]
    hd = [T(-20, 92), T(-18, 108), T(-6, 118), T(10, 118), T(20, 108), T(23, 100), T(31, 92), T(24, 88), T(26, 84), T(23, 80), T(23, 74), T(12, 70), T(-2, 72), T(-14, 80)]
    for p in (sh, neck, hd): cv2.fillPoly(f, [np.array([Pi(q) for q in cr(p)], np.int32)], 255)
    if hat:
        cap = [T(-24, 110), T(-20, 138), T(0, 146), T(22, 138), T(26, 110)]
        cv2.fillPoly(f, [np.array([Pi(q) for q in cr(cap)], np.int32)], 255)
        cv2.fillPoly(f, [np.array([Pi(T(-42, 104)), Pi(T(-26, 118)), Pi(T(28, 118)), Pi(T(46, 104))], np.int32)], 255)
        for i in range(14):
            u = -42 + i * 6.4
            cv2.fillPoly(f, [np.array([Pi(T(u, 105)), Pi(T(u + 5.5, 105)), Pi(T(u + 2.5, 98 - (i * 7 % 4)))], np.int32)], 255)
    else:
        hair = [T(-22, 96), T(-20, 116), T(-4, 126), T(18, 122), T(24, 110), T(10, 112), T(-8, 108)]
        cv2.fillPoly(f, [np.array([Pi(q) for q in cr(hair)], np.int32)], 255)
mid = (gx0 + gx1) / 2
bust(mid - 37, floor, .86, face=1)                 # Renzo, from the left
bust(mid + 36, floor, .8, face=-1, hat=True)      # Luciana, from the right, the bucket hat
# the strips are opaque on top of the lovers outside the slot: occlude by the stack outside the coincident slot
slot = np.zeros_like(f); cv2.rectangle(slot, Pi((gx0, BY0 + 6 + 26 + 16)), Pi((gx1, BY1 - 18)), 255, -1)
f = np.minimum(f, slot)
f = cut_edge(f, seed=70, amp=.03)
fa = cv2.GaussianBlur(f, (0, 0), .6 * K).astype(np.float32) / 255
shadow = cv2.GaussianBlur(np.roll(fa, 3 * K, 1), (0, 0), 3 * K) * .25
arr = np.asarray(im.convert('RGB')).astype(np.float32)
arr *= (1 - shadow[..., None]); arr = arr * (1 - fa[..., None]) + np.array([24, 22, 21]) * fa[..., None]
# travel arrow printed on Luciana's strip (right tail), outside the box
im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
d.text(Pi((900, 548)), 'B: +3 min', font=f1, fill=(226, 222, 212))
d.text(Pi((900, 570)), 'finestra 12:02 -> 12:03 -> chiusa', font=f2, fill=(200, 196, 186))
im = im.resize((W, H), Image.LANCZOS)
grain(im, amt=4, seed=9).save(OUT + '/kf-3.png'); print('kf-3')
