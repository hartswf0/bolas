"""99 ways, page 43 "The morning before" (reduction and expansion; medium: rol-cutout).
Rule: the day from dawn to four is compressed into the top two tiers; the incident itself fits in the bottom tier.
Grammar of the rol-cutout kit (build_page04 / p21: press prints with white scissor margins, pasted caption slips,
jumping red/black cover lettering in the shared pen hand).
- Tier 1 "Dawn to noon" (cool morning card), four prints: the empty office at first light (99-ways-template office
  plate = Rothstein 1937 with the clerk removed), the 7:40 (Agence Rol 1933 double-deck carriage), a man off the
  train at the window (Rol 49112 cutout behind the glass, his order as a balloon), the memo written (Rothstein P1
  rest layers, close on the slip).
- Tier 2 "Noon to four" (warm card), three pieces: noon at the empty desk with the memo slip, a passenger for the 2:12
  (Rol 57642 walking man as a free cutout), five to four (Rothstein P4 rest).
- every tier-1/2 piece carries the office clock cut out (LoC clock pieces) with its own hands re-set to that hour, so
  the hands race through the day; the bottom tier has none but the 4:10 already in the E2 print.
- Tier 3 "4:08 to 4:11" (butter card): E0-E5 in six narrow prints (rest layers P1, P4, P5, P6, P7, P8 with the Rol
  34852 stranger behind the glass in E1 and E3), the four canon lines in the shared cut-paper balloons.
Run: python3 -I p43_morning_before.py [--page-only]"""
import json
import math
import sys

import cv2
import numpy as np
from PIL import Image

KIT = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit"
sys.path.insert(0, KIT)
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
import build_page04 as K  # noqa: E402
import build_page01 as b01  # noqa: E402
from cutpaper99 import hexc  # noqa: E402
import b1m2 as B  # noqa: E402

N, PID, TITLE = 43, "the-morning-before", "The morning before"
W, H = pen99.PAGE_W, pen99.PAGE_H
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
PCS = ROOT / "films/sources/99-ways-template/page-cartoonist/pieces"
MAN = json.load(open(PCS / "manifest.json"))
RED, BLACK, BUTTER = K.RED, K.BLACK, K.BUTTER
TIMEC = hexc("#8a3a1c")

Q = ["Pardon me —", "have you", "the right", "time?"]
A = ["Ten past", "four, by", "the clock."]
T = ["Much", "obliged!"]
F = ["Well, here", "I am... and", "what for?"]
for parts, k in ((Q, "question"), (A, "answer"), (T, "thanks"), (F, "forgetting")):
    assert " ".join(parts) == LN[k], (parts, LN[k])
ORDER = ["From the Division:", "freight inspector", "at 4:15. Have the", "SERVICE door open."]


# ------------------------------------------------------------------ material
def plate():
    g = np.asarray(Image.open(PCS / "office.plate.png").convert("L")).astype(np.float32)
    return g


def clock_at(hh, mm, scale):
    """The office clock cut out, its own hands re-set on the arbor to hh:mm. Returns grey, alpha uint8."""
    case = np.asarray(Image.open(PCS / "clock.case.png")).astype(np.float32)
    g = case[..., 0].copy()
    a = case[..., 3].copy()
    arb = MAN["pieces"]["clock.case"]["pivots_local"]["arbor"]
    h, w = g.shape
    angs = {"clock.hour": ((hh % 12) + mm / 60.0) * 30.0, "clock.minute": mm * 6.0}
    for n in ("clock.hour", "clock.minute"):
        im = np.asarray(Image.open(PCS / f"{n}.png")).astype(np.float32)
        p = MAN["pieces"][n]
        piv = p["pivots_local"]["arbor"]
        rot = angs[n] - p["source_angle_deg"]
        M = cv2.getRotationMatrix2D((float(piv[0]), float(piv[1])), -rot, 1.0)
        M[0, 2] += arb[0] - piv[0]
        M[1, 2] += arb[1] - piv[1]
        hg = cv2.warpAffine(im[..., 0], M, (w, h), flags=cv2.INTER_CUBIC)
        ha = cv2.warpAffine(im[..., 3], M, (w, h), flags=cv2.INTER_LINEAR) / 255
        g = g * (1 - ha) + hg * ha
    g = cv2.resize(g, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    a = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return g, a.astype(np.uint8)


def behind_glass(g_print, rgba_g, rgba_a, s, cx, top, flip=False, op=0.8, fade=0.30):
    """Paste a cutout into a print as seen through the ticket-window glass (veiled, lost below the counter)."""
    g, a = rgba_g, rgba_a.astype(np.float32) / 255
    if flip:
        g, a = g[:, ::-1], a[:, ::-1]
    gh, gw = int(g.shape[0] * s), int(g.shape[1] * s)
    g = cv2.resize(g, (gw, gh), interpolation=cv2.INTER_AREA)
    a = cv2.resize(a, (gw, gh), interpolation=cv2.INTER_AREA)
    a = cv2.GaussianBlur(a, (0, 0), 0.8) * op
    a *= np.clip((gh - np.arange(gh)[:, None]) / (gh * fade), 0, 1)
    x0 = int(cx - gw / 2)
    ph, pw = g_print.shape
    ys, ye = max(0, top), min(ph, top + gh)
    xs, xe = max(0, x0), min(pw, x0 + gw)
    sa = a[ys - top:ye - top, xs - x0:xe - x0]
    sg = g[ys - top:ye - top, xs - x0:xe - x0] * 0.92 + 14
    g_print[ys:ye, xs:xe] = g_print[ys:ye, xs:xe] * (1 - sa) + sg * sa
    return g_print


def tone(g, kind):
    """dawn: cool grey-blue and dim; day: the kit's sepia; noon: a touch warmer."""
    L = np.clip(g / 255.0, 0, 1)
    if kind == "dawn":
        L = L ** 1.25
        lo, hi = np.array([34, 38, 52], np.float32), np.array([196, 200, 212], np.float32)
        return lo + (hi - lo) * L[..., None]
    if kind == "noon":
        return K.sepia(np.dstack([g] * 3), 0.13).astype(np.float32)
    return K.sepia(np.dstack([g] * 3)).astype(np.float32)


def card(img, F_, x0, y0, x1, y1, top, bot, seed):
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.int32(np.array([(x0, y0 + 3), (x1, y0), (x1 - 2, y1), (x0 + 2, y1 - 3)]) * 4)], 255,
                 cv2.LINE_AA, shift=2)
    K.shadow(img, m, off=(8, 10), blur=7, op=0.42)
    a = m.astype(np.float32)[..., None] / 255
    t = np.clip((np.arange(H)[:, None, None] - y0) / max(1, (y1 - y0)), 0, 1)
    c = np.asarray(top, np.float32) * (1 - t) + np.asarray(bot, np.float32) * t + F_[..., None] * 0.8
    img[:] = img * (1 - a) + c * a


def print_at(img, rgb, cx, cy, height, deg, margin=12):
    ph, pw = rgb.shape[:2]
    s = height / ph
    M = K.affine(cx, cy, s, deg, pw, ph)
    K.paste(img, rgb, np.full((ph, pw), 255, np.uint8), M, margin=margin, op=0.4)
    return M, s


def clock_on(img, hh, mm, cx, cy, scale, deg):
    cg, ca = clock_at(hh, mm, scale)
    crgb = K.sepia(np.dstack([cg] * 3), 0.05) * 0.88
    ch, cw = cg.shape
    K.paste(img, crgb, ca, K.affine(cx, cy, 1.0, deg, cw, ch), margin=7, margin_col=hexc("#ece7da"), op=0.45)


def time_mark(img, tm, x, y, cap=44, seed=0):
    m = pen99.letter([tm], cap, seed, weight=0.17)
    K.ink_at(img, m, x - m.shape[1] / 2, y, TIMEC)


def bal(img, lines, cap, centre, tip, seed):
    K.balloon(img, lines, cap, centre, tip, seed)


# ------------------------------------------------------------------ the page
TOP_CELLS = 7


def build(reveal=99):
    """reveal 1..7: tier-1/2 pieces one by one; 8..13: tier-3 prints E0..E5 one by one (99 = all)."""
    img = pen99.sheet99().astype(np.float32)
    F_ = img.mean(axis=2) - img.mean()
    rec = {"tier1": [], "tier2": [], "tier3": []}
    # ---------------- tier 1: dawn to noon
    card(img, F_, 110, 110, 2090, 950, hexc("#d9dde2"), hexc("#ece6d8"), 4301)
    K.jumpy(img, "First light to noon", 160, 200, 66, 4305, colours=(hexc("#2c3a58"), BLACK, RED))
    PL = plate()
    T1 = [  # (x centre, time, caption)
        (360, (5, 50), ["First light. He", "unlocks the office", "and winds the clock."]),
        (845, (7, 40), ["The 7:40 stops two", "minutes: milk cans,", "one mailbag."]),
        (1330, (7, 42), ["A man off the train", "leaves word at", "the window."]),
        (1815, (7, 50), ["He pencils it on a", "memo slip. Key in", "the cupboard."]),
    ]
    py, ph_ = 500, 400
    for i, (cx, (hh, mm), cap) in enumerate(T1):
        if reveal < i + 1:
            break
        deg = [-1.2, 0.9, -0.7, 1.1][i]
        if i == 0:      # the empty office at dawn: desk, ticket window, cupboards
            g = PL[100:2300:3, 2550:4300:3]
            rgb = tone(g, "dawn")
        elif i == 1:
            g = K.wagon()
            g = g[:, 160:1010]
            rgb = tone(g, "day")
        elif i == 2:    # the ticket window from inside, the Rol 49112 man behind the glass
            g = PL[300:2400:2, 0:2300:2].copy()
            mg, ma = K.man()
            g = behind_glass(g, mg.mean(axis=2), ma, 0.55, 560, 420, flip=True, op=0.85, fade=0.25)
            rgb = tone(g, "day")
        else:           # the memo, close: P1 rest layers
            c, used = b01.panel_rest("P1")
            g = c.mean(axis=2)[430:940, 0:620]
            rgb = tone(g, "day")
        M, s = print_at(img, rgb, cx, py, ph_, deg)
        pw = rgb.shape[1] * s
        clock_on(img, hh, mm, cx + pw / 2 - 40, py - ph_ / 2 + 30, 0.34, -4 + 3 * i)
        if i == 2:
            P = lambda q: M @ np.array([q[0], q[1], 1.0])
            tip = P((560, 470))
            bal(img, ORDER, 28, (cx - 20, py - 108), tip, 4310)
        sw, sh = K.slip(img, cap, 33, cx - 205, py + ph_ / 2 + 26, 410, 4320 + i, deg=[0.6, -0.5, 0.7, -0.6][i])
        time_mark(img, f"{hh}:{mm:02d}", cx + pw / 2 - 150, py - ph_ / 2 - 50, 40, 4330 + i)
        rec["tier1"].append({"time": f"{hh}:{mm:02d}", "caption": " ".join(cap)})
    # ---------------- tier 2: noon to four
    card(img, F_, 110, 975, 2090, 1735, hexc("#efe4c6"), hexc("#f4dca8"), 4340)
    if reveal >= 5:
        K.jumpy(img, "Noon to four", 160, 1062, 66, 4341, colours=(BLACK, RED))
    T2 = [
        (520, (12, 0), ["Noon. Dinner at", "the desk. The memo", "waits by the inkwell."]),
        (1100, (2, 12), ["Tickets for the 2:12:", "a gentleman for", "Montpelier."]),
        (1690, (3, 55), ["Five to four. Quiet.", "The memo before him."]),
    ]
    py2, ph2 = 1345, 400
    for j, (cx, (hh, mm), cap) in enumerate(T2):
        i = 4 + j
        if reveal < i + 1:
            break
        deg = [0.9, -1.0, 0.8][j]
        if j == 0:
            g = PL[1700:3060:3, 2500:4300:3].copy()
            rgb = tone(g, "noon")
            M, s = print_at(img, rgb, cx, py2, ph2, deg)
            # the memo slip on the empty desk (a pasted HANDMADE slip in the pen hand)
            sx, sy = M @ np.array([300, 380, 1.0])
            K.slip(img, ["MEMO", "4:15 - open", "SERVICE door.", "Key in cupboard."], 22, sx - 90, sy - 50, 180,
                   4350, deg=-6)
            pw = rgb.shape[1] * s
        elif j == 1:    # the walking man, a free cutout with a white scissor margin
            vi = np.asarray(Image.open(ROOT / "films/sources/exercices-de-style/forage/visitor_rgba.png")).astype(
                np.float32)
            vg = K.sepia(np.dstack([vi[..., :3].mean(axis=2)] * 3)).astype(np.float32)
            va = vi[..., 3].astype(np.uint8)
            vh, vw = va.shape
            s = 470 / vh
            M = K.affine(cx - 120, py2 + 10, s, deg, vw, vh)
            K.paste(img, vg, va, M, margin=12, op=0.4)
            pw = 420
            # his ticket: a small pasted card stub, lettered
            K.slip(img, ["RANDOLPH", "to", "MONTPELIER"], 24, cx - 10, py2 - 120, 190, 4351, deg=7)
        else:
            c, used = b01.panel_rest("P4")
            g = c.mean(axis=2)[0:940, 0:560]
            rgb = tone(g, "day")
            M, s = print_at(img, rgb, cx, py2, ph2, deg)
            pw = rgb.shape[1] * s
        clock_on(img, hh, mm, cx + pw / 2 + 10, py2 - ph2 / 2 + 40, 0.34, 3 - 3 * j)
        sw, sh = K.slip(img, cap, 33, cx - 205, py2 + ph2 / 2 + 24, 410, 4360 + j, deg=[-0.6, 0.6, -0.5][j])
        time_mark(img, f"{hh}:{mm:02d}", cx + pw / 2 - 100, py2 - ph2 / 2 - 50, 40, 4370 + j)
        rec["tier2"].append({"time": f"{hh}:{mm:02d}", "caption": " ".join(cap)})
    # ---------------- tier 3: the incident, 4:08 to 4:11
    card(img, F_, 110, 1760, 2090, 2730, K.BUTTER_TOP, BUTTER, 4380)
    if reveal >= 8:
        K.jumpy(img, "4:08 to 4:11", 160, 1840, 60, 4381)
    # key, event, crop (x0, y0, x1, y1) in rest px, caption, balloon (lines, cap, centre frac, tip in rest px)
    E = [
        ("P1", "E0", (150, 160, 600, 940), ["He sets off", "for the key."], None),
        ("P4", "E1", (40, 60, 520, 940), ["A lady at", "the window:"], (Q, 30, (0.52, 0.17), "her")),
        ("P5", "E2", (360, 0, 900, 940), ["He looks at", "the clock:"], (A, 30, (0.36, 0.20), None)),
        ("P6", "E3", (0, 60, 480, 940), ["She thanks", "him and goes."], (T, 34, (0.62, 0.10), "her")),
        ("P7", "E4", (0, 0, 560, 980), ["He opens the", "cupboard."], None),
        ("P8", "E5", (500, 0, 1080, 980), ["And there", "he stands."], (F, 30, (0.50, 0.12), None)),
    ]
    HER = {"P4": (150, 470), "P6": (100, 285)}
    OLD = K.OLD
    ty, th = 2250, 560
    slot = 1980 / 6
    for k, (key, ev, cr, cap, bl) in enumerate(E):
        if reveal < 8 + k:
            break
        c, used = b01.panel_rest(key)
        g = c.mean(axis=2)
        if key in ("P4", "P6"):
            wg, wa = K.woman()
            wg, wa = wg.mean(axis=2)[:600], wa[:600]
            if key == "P4":
                g = behind_glass(g, wg, wa, 0.42, 140, 430, op=0.82)
            else:
                g = behind_glass(g, wg, wa, 0.48, 95, 250, flip=True, op=0.75)
        x0, y0, x1, y1 = cr
        g = g[y0:y1, x0:x1]
        rgb = tone(g, "day")
        cx = 110 + slot * (k + 0.5)
        deg = [-0.8, 0.7, -0.6, 0.9, -0.7, 0.6][k]
        ph, pw0 = g.shape
        s = th / ph
        if pw0 * s > slot - 26:
            s = (slot - 26) / pw0
        M = K.affine(cx, ty - 60, s, deg, pw0, ph)
        K.paste(img, rgb, np.full((ph, pw0), 255, np.uint8), M, margin=10, op=0.4)
        P = lambda q: M @ np.array([q[0] - x0, q[1] - y0, 1.0])
        hh_ = ph * s
        sw, sh = K.slip(img, cap, 31, cx - 140, ty - 60 + hh_ / 2 + 22, 280, 4390 + k, deg=[0.5, -0.5][k % 2])
        time_mark(img, ["4:08", "4:09", "4:10", "4:10", "4:11", "4:11"][k], cx, ty - 60 + hh_ / 2 + 30 + sh, 36,
                  4396 + k)
        K.jumpy(img, str(k + 1), cx - (pw0 * s) / 2 - 6, ty - 60 - hh_ / 2 + 40, 50, 4400 + k, (RED,))
        if bl:
            lines, bc, (fx, fy), who = bl
            cxy = P((x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)))
            if who == "her":
                tip = P(HER[key])
            else:
                o = OLD[key][0]["tail_tip_panel_px"]
                tip = P(o)
            bal(img, lines, bc, tuple(cxy), tuple(tip), 4410 + k)
        rec["tier3"].append({"event": ev, "print_layers": used, "caption": " ".join(cap),
                             "balloon": " ".join(bl[0]) if bl else None})
    pen99.folio(img, N, TITLE)
    return np.clip(np.round(img), 0, 255).astype(np.uint8), rec


def main():
    page, rec = build()
    out_png = B.MASTERS / f"{N:02d}-{PID}.png"
    out_jpg = B.PAGES_OUT / f"{N:02d}-{PID}.jpg"
    Image.fromarray(page).save(out_png, compress_level=6)
    Image.fromarray(page).save(out_jpg, quality=90, optimize=True)
    print("bytes", out_jpg.stat().st_size)
    json.dump(rec, open(B.SRC / "p43_rec.json", "w"), indent=1, ensure_ascii=False)
    if "--page-only" in sys.argv:
        return
    frames = [build(r)[0] for r in (1, 3, 4, 5, 7, 9, 11)] + [page]
    B.save_beats(N, frames)


if __name__ == "__main__":
    main()
