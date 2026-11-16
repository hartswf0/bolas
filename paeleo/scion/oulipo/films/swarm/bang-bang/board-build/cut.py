# Bang Bang, board unit: GrabCut extraction of every puppet piece (SCION #29) for the rig (SCION #2).
#   python3 -I cut.py
# Sources (all foraged, PD/CC0; see rig.json "sources"):
#   LIL-START  sources/bang-bang/lilienthal_start.jpg      glider + pilot torso, legs (hip pin), pilot alone (A1/A2)
#   PENAUD     sources/bang-bang/penaud_models.jpg         helicoptere shaft, top rotor, bottom rotor
#   EKSTERS    sources/bang-bang/board/src/eksters_960.jpg magpie body, head (neck pin)          [if downloaded]
#   PENNY-WING sources/bang-bang/board/src/penny_magpie_wing.jpg  spread magpie wing for the flying pose [if downloaded]
# Method per piece: line-art closing (threshold -> dilate -> close -> fill holes) gives the probable foreground;
# scribble seeds (definite FG strokes, definite BG polygons) constrain cv2.grabCut (GC_INIT_WITH_MASK);
# keep only components touching a FG seed (no background islands); a scissor edge; manual contour repair where an
# occluder was removed.  Every piece is printed as warm ink (45,38,32) on cream (242,228,212); alpha = the cut.
# Exports: <piece>.png (RGBA), <piece>_mask.png, <src>_fail_mask.png (ink rejected by the cut), cut_manifest.json.
import os, sys, json
import numpy as np, cv2
from PIL import Image

FILMS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SRC = os.path.join(FILMS, "sources", "bang-bang")
OUT = os.path.join(SRC, "board")
os.makedirs(OUT, exist_ok=True)
CARD = np.array((242, 228, 212), np.float32)
INKC = np.array((45, 38, 32), np.float32)
MAN = {"pieces": {}, "mask_stats": [], "repairs": [], "absent": []}


def fill_holes(m, maxarea):
    inv = (m == 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    out = m.copy()
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < maxarea and x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
            out[lab == i] = 255
    return out


def keep_seeded(m, seed):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = list(set(np.unique(lab[(seed > 0) & (m > 0)])) - {0})
    return np.isin(lab, keep).astype(np.uint8) * 255


def largest(m):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        return m
    return np.where(lab == 1 + int(np.argmax(st[1:, 4])), 255, 0).astype(np.uint8)


def scissor(m, seed, amt=1.0):
    r = np.random.default_rng(seed); H_, W_ = m.shape
    nz = cv2.resize(r.normal(0, 1, (H_ // 10 + 2, W_ // 10 + 2)).astype(np.float32), (W_, H_), interpolation=cv2.INTER_CUBIC)
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2) + nz * amt * 40
    return np.where(a > 127, 255, 0).astype(np.uint8)


def line_closing(g, thr=170, dil=7, close=9, holes=5000):
    ink = (g < thr).astype(np.uint8) * 255
    s = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dil, dil)))
    s = cv2.morphologyEx(s, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)))
    return ink, fill_holes(s, holes)


def ink_cov(g, lo=70, hi=205):
    return np.clip((hi - g.astype(np.float32)) / (hi - lo), 0, 1) ** 0.85


def grabcut(a_rgb, init, iters=6):
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    m = init.copy()
    cv2.grabCut(cv2.cvtColor(a_rgb, cv2.COLOR_RGB2BGR), m, None, bg, fg, iters, cv2.GC_INIT_WITH_MASK)
    return np.where((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)


def save_piece(name, src_id, m, cov, pivots, note=""):
    """pivots: {name: (x, y) source px}.  Crops, prints warm ink on cream, writes piece + mask, returns record."""
    ys, xs = np.nonzero(m); x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    c = cov[y0:y1, x0:x1, None]
    rgb = CARD * (1 - c) + INKC * c
    p = np.dstack([rgb, m[y0:y1, x0:x1]]).astype(np.uint8)
    Image.fromarray(p, "RGBA").save(os.path.join(OUT, name + ".png"))
    cv2.imwrite(os.path.join(OUT, name + "_mask.png"), m[y0:y1, x0:x1])
    n, _, _, _ = cv2.connectedComponentsWithStats(m, 8)
    holes = int(((fill_holes(m, 10 ** 9) > 0) & (m == 0)).sum())
    rec = {"file": f"board/{name}.png", "mask": f"board/{name}_mask.png", "source": src_id, "size": [x1 - x0, y1 - y0],
           "offset_src": [x0, y0], "pivots": {k: [round(v[0] - x0, 1), round(v[1] - y0, 1)] for k, v in pivots.items()},
           "components": int(n - 1), "area_px": int((m > 0).sum()), "interior_holes_px": holes, "note": note}
    MAN["pieces"][name] = rec
    MAN["mask_stats"].append({"piece": name, "components": rec["components"], "area_px": rec["area_px"]})
    return rec


# ================================================================ LIL-START: glider + pilot torso; legs; pilot alone
lil = Image.open(os.path.join(SRC, "lilienthal_start.jpg")).convert("RGB")
a = np.asarray(lil); g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
ink, solid = line_closing(g)
init = np.full(g.shape, cv2.GC_BGD, np.uint8); init[solid > 0] = cv2.GC_PR_FGD
fg_scr = np.zeros_like(g)
for pts in [[(30, 133), (200, 130), (360, 215)], [(330, 270), (720, 128)], [(330, 270), (940, 330)], [(650, 30), (715, 30), (700, 80)],
            [(400, 175), (410, 240)], [(385, 285), (378, 345)], [(408, 285), (410, 345)], [(360, 222), (480, 290)]]:
    cv2.polylines(fg_scr, [np.int32(pts)], False, 255, 5)
init[(fg_scr > 0) & (solid > 0)] = cv2.GC_FGD
gnd = np.zeros_like(g)   # BG scribbles: the engraved ground under the feet is not part of the puppet
for poly in [[(180, 312), (352, 300), (352, 372), (180, 390)], [(426, 330), (700, 300), (700, 399), (426, 399)], [(340, 362), (440, 362), (440, 399), (340, 399)]]:
    cv2.fillPoly(gnd, [np.int32(poly)], 255)
init[gnd > 0] = cv2.GC_BGD
cut = grabcut(a, init)
cut = keep_seeded(cut, fg_scr)
cut = fill_holes(cv2.morphologyEx(cut, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)), 5000)
cut = keep_seeded(scissor(cut, 1), fg_scr)
cv2.imwrite(os.path.join(OUT, "lil_fail_mask.png"), ((ink > 0) & (cut == 0)).astype(np.uint8) * 255)
MAN["mask_stats"].append({"source": "LIL-START", "fail_mask": "board/lil_fail_mask.png", "ink_rejected_px": int(((ink > 0) & (cut == 0)).sum()),
                          "note": "rejected ink is the engraved ground hatching under the feet (BG scribbles)"})
cov = ink_cov(g)
HIP = (404, 271)
legs_poly = np.int32([(352, 271), (428, 268), (437, 276), (446, 368), (342, 368), (346, 300)])
lp = np.zeros_like(g); cv2.fillPoly(lp, [legs_poly], 255)
cap = np.zeros_like(g); cv2.circle(cap, HIP, 15, 255, -1)
legs_m = largest(keep_seeded(cut & lp, fg_scr & lp))
legs_m = np.maximum(legs_m, cap & ~lp)
cov_legs = cov.copy(); cov_legs[(cap > 0) & (lp == 0)] = 0
body_m = cut.copy(); body_m[lp > 0] = 0
body_m = largest(keep_seeded(cv2.morphologyEx(body_m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)), fg_scr & ~lp))
# the nose of the glider is the left wing tip (he runs right-to-left); the tail is the kite-shaped surface top right
save_piece("glider", "LIL-START", body_m, cov, {"hip": HIP, "nose": (40, 133), "tail": (700, 40), "wing_root_R": (640, 300)},
           "glider frame, both wings, tail and the pilot's torso and arms (one piece: he is strapped in)")
save_piece("legs", "LIL-START", legs_m, cov_legs, {"hip": HIP}, "legs below the waist; r=15 px blank-card joint cap hidden under the body")
MAN["repairs"].append({"piece": "legs", "what": "joint cap (r=15 px blank card) added above the waist cut so the hip wedge never opens"})

# --- right wing (viewer's right) as its own piece on a root pin for the impact droop (#41)
WROOT = (640, 300)
wr_poly = np.int32([(640, 215), (960, 250), (960, 345), (640, 330)])
wr = np.zeros_like(g); cv2.fillPoly(wr, [wr_poly], 255)
wing_m = largest(body_m & wr)
body2 = body_m.copy(); body2[wing_m > 0] = 0
body2 = largest(cv2.morphologyEx(body2, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)))
capw = np.zeros_like(g); cv2.circle(capw, WROOT, 12, 255, -1)
wing_m = np.maximum(wing_m, capw & body_m)
save_piece("glider_core", "LIL-START", body2, cov, {"hip": HIP, "wing_root_R": WROOT, "nose": (40, 133)},
           "glider without its right (aft) lower wing panel; used from impact on so the wing can droop")
save_piece("glider_wingR", "LIL-START", wing_m, cov, {"root": WROOT}, "outer half of the right lower wing on a pin at its mid-spar (droop at impact)")

# --- the pilot alone (A1 paper wing, A2 rotor): torso + head, right arm on a shoulder pin; spars removed and re-inked
pil_poly = np.int32([(352, 212), (372, 203), (390, 197), (395, 178), (393, 165), (405, 156), (426, 157), (433, 170), (431, 188),
                     (441, 200), (448, 225), (447, 252), (439, 268), (404, 276), (370, 271), (371, 246), (379, 233), (357, 233), (349, 222)])
arm_poly = np.int32([(347, 208), (395, 196), (402, 214), (386, 234), (347, 234)])
SHO = (394, 207)
pm = np.zeros_like(g); cv2.fillPoly(pm, [pil_poly], 255)
am = np.zeros_like(g); cv2.fillPoly(am, [arm_poly], 255)
spars = [(300, 190, 480, 291), (330, 266, 427, 246), (320, 274, 499, 256), (322, 273, 395, 221)]
band = np.zeros_like(g)
for x0, y0, x1, y1 in spars:
    cv2.line(band, (x0, y0), (x1, y1), 255, 5)
band &= pm
fig_ink = (ink > 0) & (pm > 0)
kept = fig_ink & (band == 0)
# repair: re-ink the figure's own contour across the erased band (directional closing = a pen stroke bridging the gap)
reink = cv2.morphologyEx(kept.astype(np.uint8) * 255, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
reink = cv2.erode(reink, np.ones((2, 2), np.uint8))
reink = (reink > 0) & (band > 0) & ~kept
pcov = cov * kept + 0.85 * reink
pilot_m = cv2.dilate((kept | reink).astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
pilot_m = fill_holes(cv2.morphologyEx(pilot_m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))), 4000) & pm
pilot_m = largest(scissor(pilot_m, 7, 0.6))
arm_m = largest(pilot_m & am)
torso_m = pilot_m.copy(); torso_m[arm_m > 0] = 0; torso_m = largest(torso_m)
caps = np.zeros_like(g); cv2.circle(caps, SHO, 9, 255, -1)
arm_m = np.maximum(arm_m, caps & pilot_m)
pcov_t = pcov.copy(); pcov_t[(cap > 0) & (lp == 0) & (pilot_m == 0)] = 0
save_piece("pilot_torso", "LIL-START", torso_m, pcov_t, {"hip": HIP, "shoulder_R": SHO, "hand_L": (424, 247)},
           "the pilot alone: head and torso, spars erased and contour re-inked; legs pin at the hip")
save_piece("pilot_arm", "LIL-START", arm_m, pcov, {"shoulder": SHO, "hand": (356, 222)}, "pilot's right arm on the shoulder pin (flaps the paper wing)")
MAN["repairs"].append({"piece": "pilot_torso/pilot_arm", "what": "four spar lines crossing the figure (Hough-detected: " + str(spars) +
                       ") erased in a 5 px band; the figure's own contour re-inked across the band by an 11 px closing thinned to pen width (checked visually in pilot_repair_map.png)",
                       "erased_px": int((fig_ink & (band > 0)).sum()), "reinked_px": int(reink.sum())})
dbg = np.dstack([g, g, g]).copy(); dbg[band > 0] = (255, 160, 0); dbg[reink] = (0, 120, 255)
Image.fromarray(dbg[140:380, 320:470]).resize((300, 480), Image.NEAREST).save(os.path.join(OUT, "pilot_repair_map.png"))

# ================================================================ PENAUD: helicoptere (plate 3, fig. 1)
pen_img = Image.open(os.path.join(SRC, "penaud_models.jpg")).convert("RGB")
a = np.asarray(pen_img); g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
ink, solid = line_closing(g, thr=175, dil=3, close=7, holes=1500)
region = np.zeros_like(g); region[82:242, 112:335] = 255
init = np.full(g.shape, cv2.GC_BGD, np.uint8); init[(solid > 0) & (region > 0)] = cv2.GC_PR_FGD
fg = np.zeros_like(g)
for pts in [[(130, 100), (215, 93)], [(232, 93), (320, 98)], [(222, 100), (222, 210)], [(125, 232), (210, 222)], [(235, 222), (320, 228)]]:
    cv2.polylines(fg, [np.int32(pts)], False, 255, 3)
init[(fg > 0) & (solid > 0)] = cv2.GC_FGD
init[g.shape[0] - 1:, :] = cv2.GC_BGD
init[240:, :] = cv2.GC_BGD                                     # the caption below
hc = grabcut(a, init)
hc = keep_seeded(hc, fg)
hc = keep_seeded(scissor(fill_holes(hc, 1500), 3, 0.5), fg)
cv2.imwrite(os.path.join(OUT, "penaud_fail_mask.png"), ((ink > 0) & (region > 0) & (hc == 0)).astype(np.uint8) * 255)
MAN["mask_stats"].append({"source": "PENAUD-PLATE", "fail_mask": "board/penaud_fail_mask.png",
                          "ink_rejected_px": int(((ink > 0) & (region > 0) & (hc == 0)).sum())})
cov = ink_cov(g, 60, 215)
ys, xs = np.nonzero(hc)
top_y = 112; bot_y = 212
shaft_x0, shaft_x1 = 207, 238
TOPHUB = (222, 95); BOTHUB = (222, 226)
top = hc.copy(); top[top_y:, :] = 0
sh = hc.copy(); sh[:top_y - 14, :] = 0; sh[218:, :] = 0; sh[:, :shaft_x0] = 0; sh[:, shaft_x1:] = 0
bot = hc.copy(); bot[:218, :] = 0;
for hub in (TOPHUB, BOTHUB):   # repair: re-ink the hub bar so both blades of each rotor are one piece
    cv2.line(hc, (hub[0] - 34, hub[1] - 2), (hub[0] + 34, hub[1] - 2), 255, 7); cv2.line(cov, (hub[0] - 34, hub[1] - 2), (hub[0] + 34, hub[1] - 2), 0.9, 2)
top = np.where(np.arange(g.shape[0])[:, None] < top_y, np.maximum(top, hc), top).astype(np.uint8); bot = np.where(np.arange(g.shape[0])[:, None] >= 218, np.maximum(bot, hc), bot).astype(np.uint8)
MAN['repairs'].append({'piece': 'heli_top/heli_bottom', 'what': 'hub bar re-inked by hand (68 px pen line, source px) joining the two blades of each rotor across the shaft gap'})
top[(sh > 0) & (np.arange(g.shape[0])[:, None] > TOPHUB[1] + 4)] = 0
save_piece("heli_top", "PENAUD-PLATE", largest(top), cov, {"hub": TOPHUB}, "top rotor (two feather-ribbed blades) on the hub pin")
save_piece("heli_shaft", "PENAUD-PLATE", largest(sh), cov, {"top_hub": TOPHUB, "bottom_hub": BOTHUB, "grip": (222, 160)},
           "frame and the twisted rubber skein; the band snap is drawn as a pen squiggle from here")
save_piece("heli_bottom", "PENAUD-PLATE", largest(bot), cov, {"hub": BOTHUB}, "bottom rotor (counter-turning) on the lower hub pin")


# ================================================================ AUDUBON: Common Magpie (Bowen lithograph after Audubon), LoC cph.3a32885
# fig. 1 (male, flying, seen from above) -> fly_body + fly_wingL + fly_wingR (shoulder pins);
# fig. 2 (female, alighting, wings half open, a branch across her) -> pie_body + pie_head (neck pin); branch removed.
mp = Image.open(os.path.join(OUT, "src", "common_magpie_r.jpg")).convert("RGB")
a = np.asarray(mp); g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
bgv = float(np.median(g[560:600, 20:360]))
def two_value(gg):
    return np.clip((bgv - 62 - gg.astype(np.float32)) / 38, 0, 1)   # steep: the plumage prints as ink or paper, with its feather lines
mcov = two_value(g)
def outline_cut(poly_pr, fg_polys, bg_polys, seed):
    init = np.full(g.shape, cv2.GC_BGD, np.uint8)
    cv2.fillPoly(init, [np.int32(poly_pr)], int(cv2.GC_PR_BGD))
    init[init == cv2.GC_PR_BGD] = cv2.GC_PR_FGD          # everything inside the hand-drawn outline is probable FG
    fgm = np.zeros_like(g)
    for p in fg_polys:
        cv2.fillPoly(fgm, [np.int32(p)], 255)
    init[fgm > 0] = cv2.GC_FGD
    for p in bg_polys:
        cv2.fillPoly(init, [np.int32(p)], int(cv2.GC_BGD))
    m = grabcut(a, init, 8)
    m = keep_seeded(m, fgm)
    m = fill_holes(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)), 3000)
    return largest(scissor(m, seed, 0.4)), fgm
# --- male, flying
fly_out = [(84, 88), (110, 90), (150, 120), (190, 150), (200, 120), (240, 40), (330, 8), (345, 30), (300, 170), (330, 205), (348, 255), (330, 292), (265, 292), (235, 268), (190, 275), (120, 272), (95, 255), (100, 225), (130, 210), (100, 160)]
fly_fg = [[(150, 175), (185, 170), (188, 215), (150, 222)], [(195, 218), (235, 218), (235, 255), (200, 258)], [(210, 165), (240, 165), (240, 195), (212, 195)],
          [(95, 100), (130, 105), (150, 140), (120, 150)], [(200, 175), (230, 165), (240, 200), (200, 240), (150, 255), (125, 255), (135, 235), (175, 220)],
          [(110, 120), (140, 140), (175, 190), (165, 205), (120, 170)], [(250, 130), (300, 60), (320, 40), (300, 140), (260, 170)],
          [(250, 215), (300, 215), (320, 255), (290, 270), (255, 245)]]
fm, ffg = outline_cut(fly_out, fly_fg, [], 21)
cv2.imwrite(os.path.join(OUT, "audubon_fly_fail_mask.png"), (((g < bgv - 25) & (fm == 0)) & (np.arange(g.shape[0])[:, None] < 300)).astype(np.uint8) * 255)
SHL, SHR = (192, 178), (238, 212)
wl = np.zeros_like(g); cv2.fillPoly(wl, [np.int32([(80, 85), (150, 95), (196, 160), (196, 178), (175, 200), (140, 228), (80, 230)])], 255)
wr_ = np.zeros_like(g); cv2.fillPoly(wr_, [np.int32([(236, 222), (262, 205), (300, 195), (350, 235), (345, 300), (255, 300), (238, 262)])], 255)
wingL = largest(fm & wl); wingR = largest(fm & wr_)
body = fm.copy(); body[(wingL > 0) | (wingR > 0)] = 0; body = largest(cv2.morphologyEx(body, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)))
for pv, wm in ((SHL, wingL), (SHR, wingR)):
    c_ = np.zeros_like(g); cv2.circle(c_, pv, 7, 255, -1); wm[:] = np.maximum(wm, c_ & fm)
save_piece("fly_body", "AUDUBON-MAGPIE", body, mcov, {"shoulder_L": SHL, "shoulder_R": SHR, "beak": (102, 262), "tail_tip": (330, 15), "centre": (210, 200)},
           "flying magpie (fig. 1, male) body, head and fanned tail; wings cut off at the shoulders")
save_piece("fly_wingL", "AUDUBON-MAGPIE", wingL, mcov, {"shoulder": SHL}, "near spread wing on the left shoulder pin (flap = rotation + foreshortening)")
save_piece("fly_wingR", "AUDUBON-MAGPIE", wingR, mcov, {"shoulder": SHR}, "far spread wing on the right shoulder pin")
MAN["repairs"].append({"piece": "fly_wingL/fly_wingR", "what": "the plate's single flying pose was cut into body + two wings and re-pinned at the shoulders (Reiniger replacement practice), so the flap cycle is articulated, not a slide"})
# --- female, alighting, the branch across her removed and inpainted, then re-inked
BR0, BR1 = (163, 330), (276, 500)
band = np.zeros_like(g); cv2.line(band, BR0, BR1, 255, 23)
fem_out = [(15, 362), (60, 365), (165, 395), (190, 345), (205, 336), (250, 345), (290, 395), (300, 425), (350, 455), (345, 470), (300, 475), (240, 478), (150, 478), (120, 465), (175, 445), (170, 420), (100, 418), (25, 380)]
fem_fg = [[(40, 368), (160, 395), (170, 410), (40, 378)], [(250, 440), (300, 440), (320, 460), (250, 465)], [(200, 350), (240, 355), (275, 395), (235, 405)]]
init_g = g.copy()
gi = cv2.inpaint(a, band, 10, cv2.INPAINT_TELEA)
a_saved = a; a = gi; g = cv2.cvtColor(gi, cv2.COLOR_RGB2GRAY)
pm_, pfg = outline_cut(fem_out, fem_fg, [], 23)
pm_[band > 0] = np.where(cv2.morphologyEx(pm_, cv2.MORPH_CLOSE, np.ones((17, 17), np.uint8))[band > 0] > 0, 255, 0)
pm_ = largest(pm_)
fcov = two_value(g)
# re-ink: the bird's contour across the erased band, with a pen line (edge of the repaired mask inside the band)
edge = cv2.morphologyEx(pm_, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
bz = cv2.dilate(band, np.ones((5, 5), np.uint8)) > 0
fcov = np.where(bz, (cv2.GaussianBlur(fcov, (0, 0), 1.0) > 0.5).astype(np.float32), fcov)   # repaired band: ink or paper, no smear
fcov = np.where(edge & (band > 0), np.maximum(fcov, 0.9), fcov)
cv2.imwrite(os.path.join(OUT, "audubon_fem_fail_mask.png"), (((init_g < bgv - 25) & (pm_ == 0) & (band == 0)) & (np.arange(g.shape[0])[:, None] > 320) & (np.arange(g.shape[0])[:, None] < 500)).astype(np.uint8) * 255)
NECK = (268, 425)
hp = np.zeros_like(g); cv2.fillPoly(hp, [np.int32([(272, 425), (300, 428), (360, 440), (360, 480), (285, 480), (268, 455)])], 255)
head = largest(pm_ & hp)
bodyf = pm_.copy(); bodyf[head > 0] = 0; bodyf = largest(bodyf)
c_ = np.zeros_like(g); cv2.circle(c_, NECK, 9, 255, -1); head = np.maximum(head, c_ & pm_)
save_piece("pie_body", "AUDUBON-MAGPIE", bodyf, fcov, {"neck": NECK, "feet": (205, 470), "tail_tip": (20, 365)},
           "the commentator (fig. 2, female): body, half-open wings and long tail; branch removed")
save_piece("pie_head", "AUDUBON-MAGPIE", head, fcov, {"neck": NECK, "beak": (348, 462), "eye": (318, 452)}, "head on the neck pin (held angles, bird-like jerks)")
MAN["repairs"].append({"piece": "pie_body/pie_head", "what": "the branch the female perches across (a 23 px band from (163,330) to (276,500)) was inpainted (cv2.INPAINT_TELEA, r=10) and the bird's outline re-inked across the band; she is re-pinned on a pen fence post",
                       "band_px": int((band > 0).sum())})
a, g = a_saved, init_g

json.dump(MAN, open(os.path.join(OUT, "cut_manifest.json"), "w"), indent=1)
print(json.dumps(MAN["mask_stats"], indent=0))
print(json.dumps(MAN["repairs"], indent=0))
