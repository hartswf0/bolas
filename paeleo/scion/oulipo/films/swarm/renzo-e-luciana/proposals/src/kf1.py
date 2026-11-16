"""KF1 · Il paravento: articulated silhouette theatre (handmade cut black paper on a back-lit screen).
Beat: late-bell version, 12:03 (t = 42 s): the bell rings over the doorway; Luciana is already up and turned
to the door, her trailing hand a finger short of the cup Renzo still holds out; the foreman's light reaches the corner."""
import sys; sys.path.insert(0, '.')
from common import *
import math
K = 2
CW, CH = W * K, H * K
def P(x, y): return (x * K, y * K)
def Pi(a): return (int(round(a[0] * K)), int(round(a[1] * K)))
def cr(pts, n=10, closed=True):
    """Catmull-Rom through pts -> dense outline (the scissors follow a smooth curve)."""
    pts = list(pts); m = len(pts); out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0, p1, p2, p3 = pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        if not closed:
            p0 = pts[max(i - 1, 0)]; p3 = pts[min(i + 2, m - 1)]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out
def frame(o, ang, pts, flip=1):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    return [(o[0] + u * c - v * flip * s, o[1] + u * s + v * flip * c) for u, v in pts]
def seg(p, ang, L): a = math.radians(ang); return (p[0] + L * math.cos(a), p[1] + L * math.sin(a))
# --- back-lit screen -----------------------------------------------------------------------------------
Y, X = np.mgrid[0:CH, 0:CW].astype(np.float32)
lamp = np.exp(-(((X - 0.5 * CW) / (0.62 * CW)) ** 2 + ((Y - 0.40 * CH) / (0.78 * CH)) ** 2))
scr = 118 + 118 * lamp + cv2.resize(paper(W, H, base=0, seed=21, fibre=5), (CW, CH))
spill = np.zeros((CH, CW), np.uint8)
cv2.fillPoly(spill, [np.array([Pi((1060, 250)), Pi((1060, 604)), Pi((520, 604)), Pi((760, 380))], np.int32)], 255)
scr = scr + 24 * cv2.GaussianBlur(spill, (0, 0), 16 * K).astype(np.float32) / 255
base = np.stack([scr, scr * .985, scr * .955], -1)
sil = Image.new('L', (CW, CH), 0); d = ImageDraw.Draw(sil)
def fill(pts, v=255): d.polygon([Pi(p) for p in pts], fill=v)
def disc(c, r, v=255): d.ellipse([Pi((c[0] - r, c[1] - r)), Pi((c[0] + r, c[1] + r))], fill=v)
def stroke(a, b, w): d.line([Pi(a), Pi(b)], fill=255, width=max(1, int(w * K))); disc(a, w / 2); disc(b, w / 2)
def limb(a, b, wa, wm, wb, bulge=.4, flip=1):
    """tapered limb with a muscle bulge, as one cut piece; joint discs make the pin overlap."""
    L = math.dist(a, b); ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    top = [(0, -wa), (L * bulge, -wm), (L, -wb)]; bot = [(L, wb), (L * (bulge + .15), wm * .9), (0, wa)]
    fill(cr(frame(a, ang, top + bot, flip), 8)); disc(a, wa * .95); disc(b, wb * .95)
GROUND = 604
# --- floor: black card, terrace tiles cut out in perspective rows -------------------------------------------
fill([(0, GROUND), (W, GROUND), (W, H), (0, H)])
# --- tube deck chairs -----------------------------------------------------------------------------------------
def chair(x, flip=1):
    f = lambda dx: x + flip * dx
    stroke((f(-72), GROUND), (f(52), 472), 6); stroke((f(44), GROUND), (f(-58), 472), 6)
    stroke((f(-60), 472), (f(74), 470), 5); stroke((f(-84), 392), (f(-60), 472), 5); stroke((f(-84), 392), (f(-96), 380), 5)
    fill(cr([(f(-60), 474), (f(70), 472), (f(40), 500), (f(-20), 512)], 6))
chair(318, 1); chair(830, -1)
# --- Renzo (bare-shouldered, as the reference): seated, leaning in, cup out -----------------------------------
hip = (346, 486); TA = -60
torso = frame(hip, TA, [(0, -30), (55, -36), (118, -34), (150, -24), (160, -6), (158, 16), (140, 28), (100, 30), (60, 22), (20, 30), (-6, 20)])
fill(cr(torso, 8))
sh = seg(hip, TA, 148)
neck = seg(sh, TA - 8, 22); hc = seg(neck, TA - 5, 30)
fill(cr(frame(sh, TA - 8, [(-4, -14), (30, -12), (30, 12), (-4, 16)]), 4))
head = [(-27, 4), (-26, -16), (-14, -31), (6, -35), (22, -26), (27, -14), (30, -6), (41, 4), (31, 9), (34, 14), (31, 19), (31, 25), (20, 32), (2, 30), (-14, 22)]
hd = frame(hc, 0, head); fill(cr(hd, 6))
fill(cr([(hc[0] - 30, hc[1] - 6), (hc[0] - 26, hc[1] - 30), (hc[0] - 4, hc[1] - 44), (hc[0] + 24, hc[1] - 40), (hc[0] + 30, hc[1] - 26), (hc[0] + 12, hc[1] - 26), (hc[0] - 6, hc[1] - 18)], 6))  # hair wave
el = seg(sh, 8, 92); wr = seg(el, -16, 84)
limb(sh, el, 15, 16, 10); limb(el, wr, 10, 12, 7)
fill(cr([(wr[0] - 4, wr[1] - 8), (wr[0] + 18, wr[1] - 12), (wr[0] + 30, wr[1] - 6), (wr[0] + 18, wr[1] + 6), (wr[0] - 2, wr[1] + 8)], 5))
cup = (wr[0] + 26, wr[1] - 20)
fill(cr([(cup[0] - 24, cup[1] - 18), (cup[0] + 24, cup[1] - 18), (cup[0] + 18, cup[1] - 2), (cup[0] + 8, cup[1] + 6), (cup[0] - 8, cup[1] + 6), (cup[0] - 18, cup[1] - 2)], 5))
fill([(cup[0] - 36, cup[1] + 8), (cup[0] + 36, cup[1] + 8), (cup[0] + 30, cup[1] + 13), (cup[0] - 30, cup[1] + 13)])
for k in range(3):                     # steam, cut as three thin curls
    xs = cup[0] - 10 + k * 10
    pts = [(xs + 4 * math.sin(t / 3), cup[1] - 22 - t) for t in range(0, 26, 2)]
    for a, b in zip(pts, pts[1:]): stroke(a, b, 2.2)
el2 = seg(sh, 36, 74); wr2 = seg(el2, -30, 62); limb(sh, el2, 13, 13, 9); limb(el2, wr2, 9, 10, 7)
kn = seg(hip, -6, 116); ft = seg(kn, 94, 114)
limb(hip, kn, 26, 24, 15); limb(kn, ft, 15, 16, 9, bulge=.3)
fill(cr([(ft[0] - 12, ft[1] - 10), (ft[0] + 8, ft[1] - 4), (ft[0] + 34, ft[1] - 2), (ft[0] + 38, ft[1] + 4), (ft[0] - 12, ft[1] + 6)], 4))
kn2 = seg(hip, 10, 108); ft2 = seg(kn2, 104, 108); limb(hip, kn2, 24, 22, 14); limb(kn2, ft2, 14, 15, 9, bulge=.3)
fill(cr([(ft2[0] - 12, ft2[1] - 10), (ft2[0] + 32, ft2[1] - 2), (ft2[0] + 34, ft2[1] + 6), (ft2[0] - 12, ft2[1] + 6)], 4))
# --- Luciana: risen, profile to the door, the trailing hand still toward the cup --------------------------------
lh = (866, 446)
body = [(0, -20), (40, -24), (88, -20), (120, -16), (132, -4), (132, 12), (118, 18), (96, 14), (84, 24), (64, 26), (40, 18), (6, 18)]
LA = -86
fill(cr(frame(lh, LA, body), 8))
skirt = [(lh[0] - 26, lh[1] - 4), (lh[0] + 22, lh[1] - 6), (lh[0] + 48, lh[1] + 40), (lh[0] + 70, lh[1] + 86), (lh[0] + 30, lh[1] + 92),
         (lh[0] - 10, lh[1] + 90), (lh[0] - 58, lh[1] + 84), (lh[0] - 40, lh[1] + 40)]
fill(cr(skirt, 8))
lsh = seg(lh, LA, 124)
lneck = seg(lsh, -84, 20); lhc = seg(lneck, -80, 24)
fill(cr(frame(lsh, -84, [(-2, -9), (22, -8), (22, 8), (-2, 9)]), 4))
lhead = [(-24, 0), (-22, -16), (-8, -26), (10, -26), (22, -14), (25, -4), (34, 6), (26, 10), (28, 14), (25, 17), (26, 22), (16, 27), (2, 26), (-12, 18)]
fill(cr(frame(lhc, 0, lhead), 6))
fill(cr([(lhc[0] - 26, lhc[1] + 2), (lhc[0] - 34, lhc[1] + 28), (lhc[0] - 18, lhc[1] + 34), (lhc[0] - 8, lhc[1] + 14)], 5))  # dark hair at the nape
# bucket hat, frayed raffia brim cut as a fringe
hb = (lhc[0] + 2, lhc[1] - 12)
fill(cr([(hb[0] - 26, hb[1] - 4), (hb[0] - 22, hb[1] - 40), (hb[0] + 2, hb[1] - 50), (hb[0] + 26, hb[1] - 42), (hb[0] + 30, hb[1] - 4)], 6))
fill([(hb[0] - 44, hb[1] + 8), (hb[0] - 28, hb[1] - 10), (hb[0] + 32, hb[1] - 10), (hb[0] + 50, hb[1] + 8)])
for i in range(16):
    x = hb[0] - 44 + i * 6.2
    fill([(x, hb[1] + 7), (x + 5.5, hb[1] + 7), (x + 2.5 + (i % 2), hb[1] + 15 + (i * 7 % 5))])
# trailing arm back toward the cup; fingers stop 18 px short of the saucer rim
def ik2(a, t, l1, l2, bend=1):
    """two-link IK (#33): elbow position for shoulder a reaching target t."""
    D = min(math.dist(a, t), l1 + l2 - 1e-3); base_ = math.atan2(t[1] - a[1], t[0] - a[0])
    c = (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D); ang = base_ + bend * math.acos(max(-1, min(1, c)))
    return (a[0] + l1 * math.cos(ang), a[1] + l1 * math.sin(ang))
GAP = 18                                     # the window just closed: fingertips stop GAP px short of the saucer
tip = (cup[0] + 36 + GAP + 15, cup[1] + 8)
lwr = (tip[0] + 2, tip[1] + 2)
lel = ik2((lsh[0] - 6, lsh[1] + 4), lwr, 96, 92, bend=-1)
limb((lsh[0] - 6, lsh[1] + 4), lel, 10, 11, 8); limb(lel, lwr, 8, 9, 5.5)
for k, a in enumerate((168, 178, 188, 197)): stroke(lwr, seg(lwr, a, 17 - k * 2), 3.2)
stroke(lwr, seg(lwr, 214, 10), 3.4)  # thumb
fill(cr([(lwr[0] + 50, lwr[1] - 4), (lwr[0] + 58, lwr[1] + 2), (lwr[0] + 50, lwr[1] + 6)], 3))  # bangle
lel2 = seg(lsh, 70, 64); lwr2 = seg(lel2, 30, 48); limb(lsh, lel2, 9, 9, 7); limb(lel2, lwr2, 7, 7, 5)
lkn = seg(lh, 70, 92); lft = seg(lkn, 96, 78); limb(lh, lkn, 18, 17, 10); limb(lkn, lft, 10, 11, 5, bulge=.3)
fill([(lft[0] - 4, lft[1] - 8), (lft[0] + 30, lft[1] + 4), (lft[0] + 26, lft[1] + 8), (lft[0] - 2, lft[1] + 4)]); stroke((lft[0] - 2, lft[1] + 2), (lft[0] - 4, GROUND), 3)
lkn2 = seg(lh, 112, 88); lft2 = seg(lkn2, 74, 84); limb(lh, lkn2, 18, 17, 10); limb(lkn2, lft2, 10, 11, 5, bulge=.3)
fill([(lft2[0] - 4, lft2[1] - 8), (lft2[0] + 30, lft2[1] + 4), (lft2[0] + 26, lft2[1] + 8), (lft2[0] - 2, lft2[1] + 4)]); stroke((lft2[0] - 2, lft2[1] + 2), (lft2[0] - 4, GROUND), 3)
# --- the doorway wall, the bell, the clock ------------------------------------------------------------------------
fill([(1050, 140), (1258, 140), (1258, GROUND), (1050, GROUND)])
fill([(1040, 132), (1268, 132), (1268, 146), (1040, 146)])
bel = (1154, 92); stroke((1154, 132), (1154, 116), 6)
fill(cr([(bel[0] - 30, bel[1] + 18), (bel[0] - 22, bel[1] - 4), (bel[0] - 14, bel[1] - 26), (bel[0], bel[1] - 32), (bel[0] + 14, bel[1] - 26), (bel[0] + 22, bel[1] - 4), (bel[0] + 30, bel[1] + 18)], 5))
disc((bel[0] + 16, bel[1] + 24), 7)
cc = (612, 140); disc(cc, 58)
# proscenium: black border, scalloped valance
fill([(0, 0), (W, 0), (W, 22), (0, 22)]); fill([(0, 0), (20, 0), (20, H), (0, H)]); fill([(W - 20, 0), (W, 0), (W, H), (W - 20, H)])
for i in range(0, W + 40, 40): disc((i, 22), 15)
s = np.asarray(sil).copy()
def cutp(pts): cv2.fillPoly(s, [np.array([Pi(p) for p in pts], np.int32)], 0)
# tiles cut out of the floor (perspective rows like the reference's tiled terrace)
for row in range(4):
    y0 = GROUND + 16 + row * (18 + row * 6); sz = 8 + row * 4; gap = 7 + row * 3
    for i in range(-2, 120):
        x0 = i * (sz + gap) + (row % 2) * (sz // 2)
        cutp([(x0, y0), (x0 + sz, y0), (x0 + sz, y0 + sz * .55), (x0, y0 + sz * .55)])
# dress stripes cut as slits (the reference's striped dress)
for k in range(6):
    y = lh[1] - 108 + k * 18
    cutp([(lh[0] - 14, y), (lh[0] + 16, y - 3), (lh[0] + 16, y + 2.4), (lh[0] - 14, y + 5.4)])
for k in range(5):
    y = lh[1] + 14 + k * 15
    cutp([(lh[0] - 34 - k * 4, y + 4), (lh[0] + 36 + k * 6, y - 2), (lh[0] + 37 + k * 6, y + 3), (lh[0] - 33 - k * 4, y + 9)])
cutp([(1072, 204), (1236, 204), (1236, GROUND), (1072, GROUND)])   # the lit doorway
cv2.circle(s, Pi(cc), 49 * K, 0, -1)
# foreman, second sheet, standing in the light: cap, coat, watch raised
fm = Image.new('L', (CW, CH), 0); fd = ImageDraw.Draw(fm)
def ff(pts): fd.polygon([Pi(p) for p in pts], fill=255)
ff(cr([(1128, GROUND), (1132, 520), (1124, 440), (1116, 360), (1124, 318), (1146, 304), (1180, 306), (1198, 330), (1200, 400), (1192, 470), (1196, GROUND)], 6))
ff(cr([(1142, 300), (1140, 268), (1152, 254), (1170, 254), (1180, 268), (1178, 296), (1166, 306), (1150, 306)], 5))
ff([(1140, 262), (1180, 256), (1182, 266), (1120, 274)])                 # cap peak toward the couple
ff(cr([(1124, 330), (1104, 372), (1098, 380), (1108, 386), (1130, 360)], 4)); fd.ellipse([Pi((1090, 366)), Pi((1108, 384))], fill=255)
s = np.maximum(s, np.asarray(fm))
# clock: ticks + hands at 12:03
def cl(a, b, w): cv2.line(s, Pi(a), Pi(b), 255, max(1, int(w * K)))
for k in range(60):
    a = math.radians(k * 6 - 90); r0 = 40 if k % 5 == 0 else 45
    cl((cc[0] + r0 * math.cos(a), cc[1] + r0 * math.sin(a)), (cc[0] + 48 * math.cos(a), cc[1] + 48 * math.sin(a)), 3.5 if k % 5 == 0 else 1.2)
hm = frame(cc, 18 - 90, [(-8, 0), (0, -3.2), (42, -1.2), (44, 0), (42, 1.2), (0, 3.2)]); cv2.fillPoly(s, [np.array([Pi(p) for p in hm], np.int32)], 255)
hh = frame(cc, 1.5 - 90, [(-6, 0), (0, -5), (28, -2), (30, 0), (28, 2), (0, 5)]); cv2.fillPoly(s, [np.array([Pi(p) for p in hh], np.int32)], 255)
cv2.circle(s, Pi(cc), 5 * K, 255, -1)
for rr in (42, 56, 70):
    cv2.ellipse(s, Pi(bel), (rr * K, int(rr * .8 * K)), 0, -160, -20, 255, int(2.6 * K))
s = cut_edge(s, seed=13, amp=.07)
a = cv2.GaussianBlur(s, (0, 0), .7 * K).astype(np.float32) / 255
ink = np.array([22, 20, 19], np.float32)
out = base * (1 - a[..., None]) + ink * a[..., None]
outI = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
grain(outI, amt=4, seed=8).save(OUT + '/kf-1.png'); print('kf-1')
