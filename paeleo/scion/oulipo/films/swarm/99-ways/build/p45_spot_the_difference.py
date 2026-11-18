"""99 ways, page 45 "Spot the difference" (reader and object; medium: rol-cutout).
A 1930s story-paper puzzle page in the rol-cutout cover grammar (butter ground, warm grey band, jumping red/black cover
lettering in the shared pen hand). The band carries E0-E3 as four small press prints (99-ways-template rest layers,
c1 balloons), the stranger pasted behind the ticket-window glass as the Agence Rol 34852 cutout. Below, two
near-identical tiers built on the same Rothstein set plate with the 99-ways-template FK rig (build/rig45.py):
A, the moment he opens the cupboard (E4); B, a moment later, the forgetting (E5). Exactly five things differ.
The answers run upside down at the foot. The key on its hook is the same in both (it is not a difference).
Writes assets/pages/99-ways/45-spot-the-difference.jpg, films/sources/99-ways/masters/45-spot-the-difference.png,
films/sources/99-ways/beats/45/b01..b07.png, films/swarm/99-ways/pages/45.json.   Run: python3 -I p45_spot_the_difference.py"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "kit"))
import rig45 as rg  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
import build_page01 as b01  # noqa: E402
import build_page04 as k4  # noqa: E402  (rol-cutout cover grammar helpers: ground, paste, jumpy, slip, woman, sepia)
from cutpaper99 import hexc  # noqa: E402

bp = rg.bp
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["n"] == 45][0] if "n" in CANON["constraints"][0] else CANON["constraints"][44]
assert C["id"] == "spot-the-difference", C["id"]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SRC = ROOT / "films/sources/99-ways"
OUT_JPG = ROOT / "assets/pages/99-ways/45-spot-the-difference.jpg"
OUT_PNG = SRC / "masters/45-spot-the-difference.png"
BEATS = SRC / "beats/45"
W, H = pen99.PAGE_W, pen99.PAGE_H
OLD = json.load(open(b01.TPL / "page" / "speech.json"))
RED, BLACK, BAND, SLIP, PRINT_W = k4.RED, k4.BLACK, k4.BAND, k4.SLIP, k4.PRINT_W
PENCIL_RED = hexc("#c0301c")

Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
TH = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
assert " ".join(Q) == LN["question"] and " ".join(A) == LN["answer"] and " ".join(TH) == LN["thanks"] and " ".join(F) == LN["forgetting"]

# ------------------------------------------------------------------ the two tiers (same set plate, same rig)
V = (0.88, 1950, 600)            # Rothstein set plate -> tier px (left: ticket racks and wall; right: cupboard, SERVICE leaf)
TW, TH_ = 1980, 880
CLERK_AT, KC = (1560, 1000), 0.66
POSE_A = dict(arm=-58.0, pencil=26.0, head=0.0)          # just opened the door: hand dropped, pencil in it, eyes down
POSE_B = bp.solve_pencil_to_chin(np.array(bp.CHIN_TOUCH), head=-11.0)  # pencil to the chin, head tipped up
STATE = {"A": dict(pose=POSE_A, swing=0.34, tag=30.0, mm=10, balloon=False),
         "B": dict(pose=POSE_B, swing=0.34, tag=12.0, mm=11, balloon=True)}
CLOCK_AT, CLOCK_K = (560, 250), 0.55


def tier(which):
    st = STATE[which]
    P = bp.Panel(which, bp.view_plate(bp.SETP, *V, TW, TH_))
    Mw = bp.W2P(*V)
    bp.sign_card(P, bp.apply(Mw, (4060, 800)), V[0] * 330, -2)
    dk = rg.door_key(P, *V, swing=st["swing"], tag_deg=st["tag"])
    clk = rg.clock_on(P, CLOCK_AT, CLOCK_K, 4, st["mm"])
    Mc = bp.T(CLERK_AT[0], CLERK_AT[1]) @ bp.S(KC) @ bp.T(-bp.ROOT_[0], -bp.ROOT_[1]) @ bp.MIR()
    fk = rg.clerk(P, Mc, st["pose"])
    bal = None
    if st["balloon"]:
        m = fk["mouth_px"]
        bal = bp.balloon(P, "b_forgot", F, 58, (1120, 170), (m[0] - 18, m[1] + 6), 4583, tail_w=0.22, bend=0.08)
        bal.update(speaker="AGENT (to himself)")
    return P, dict(door_key={k: (np.asarray(v).round(1).tolist() if not np.isscalar(v) else float(v)) for k, v in dk.items()},
                   clock_centre=list(np.asarray(clk).round(1)), clerk=fk, balloon=bal, state=st)


# the five differences (tier px), in the order of the printed answers
def differences(fa, fb):
    dk = fb["door_key"]
    cb = fb["clerk"]
    return [
        dict(n=1, what="his pencil has gone up to his chin", at=cb["pencil_tip_px"], r=(78, 70)),
        dict(n=2, what="his head is tipped up", at=[cb["head_top_px"][0] - 30, cb["head_top_px"][1] + 95], r=(120, 105)),
        dict(n=3, what="the clock has moved on from 4:10 to 4:11", at=fb["clock_centre"], r=(88, 88)),
        dict(n=4, what="the tag has stopped swinging", at=dk["tag"], r=(110, 62)),
        dict(n=5, what="he says 'Well, here I am... and what for?'", at=fb["balloon"]["centre_panel_px"], r=(340, 150)),
    ]


# ------------------------------------------------------------------ page parts
STRIP = [  # rest panel, crop in panel px, event, balloon (lines, cap, centre frac, tail tip in panel px or None)
    ("P1", (0, 160, 740, 930), "E0", None),
    ("P4", (0, 120, 560, 890), "E1", (Q, 40, (0.48, 0.15), (-40, 330))),
    ("P5", (60, 0, 940, 937), "E2", (A, 44, (0.30, 0.14), "P5")),
    ("P6", (0, 120, 600, 890), "E3", (TH, 50, (0.62, 0.17), (-40, 300))),
]
STRIP_CAPS = [["4:09. The memo:", "open SERVICE door", "at 4:15."], ["He gets up. At the", "window, a question."],
              ["He looks at", "the clock."], ["She thanks him", "and goes."]]


def strip_print(i):
    key, (x0, y0, x1, y1), ev, bal = STRIP[i]
    c, used = b01.panel_rest(key)
    c = c[y0:y1, x0:x1].copy()
    if key == "P4":            # the stranger behind the ticket-window glass: Rol 34852 cutout (head and bust)
        g, a = k4.woman()
        g = g.mean(2)
        bust = slice(0, 560)
        g, a = g[bust], a[bust]
        s = 430 / g.shape[0]
        M = k4.affine(165, 40 + 215, s, 1.5, g.shape[1], g.shape[0])
        gw = cv2.warpAffine(g, M, (c.shape[1], c.shape[0]), flags=cv2.INTER_CUBIC)
        aw = cv2.warpAffine(a, M, (c.shape[1], c.shape[0]), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
        L = c.mean(2)
        glass = np.zeros_like(L)
        glass[:560, :400] = 1.0                       # the glazed part of the window in this crop
        glass = cv2.GaussianBlur(glass, (0, 0), 6)
        behind = gw * 0.62 + L * 0.38                 # seen through the glass: lifted, with the glass's own tone
        lit = (L > 150).astype(np.float32)            # the gilt TICKET OFFICE letters stay on top of her
        lit = cv2.GaussianBlur(lit, (0, 0), 1.2)
        aa = (aw * glass * (1 - lit))[..., None]
        c = c * (1 - aa) + behind[..., None] * aa
        used = used + ["rol34852 woman, behind the glass"]
    if bal:
        lines, cap, fr, tip = bal
        h, w = c.shape[:2]
        if tip == "P5":
            o = OLD["P5"][0]["tail_tip_panel_px"]
            tip = (o[0] - x0, o[1] - y0)
        b01.balloon_on(c, lines, cap, tip, (fr[0] * w, fr[1] * h), 4510 + i * 7)
    return c, used


def ring_mask(c, r, seed):
    """a red-pencil ring drawn round a difference (two overlapping passes of the HANDMADE brush line)."""
    m = np.zeros((H, W), np.uint8)
    rnd = np.random.default_rng(seed)
    t = np.linspace(-0.2, 2 * math.pi + 0.35, 90)
    wob = 1 + 0.05 * np.sin(t * 3 + rnd.uniform(0, 6))
    pts = np.stack([c[0] + r[0] * wob * np.cos(t), c[1] + r[1] * wob * np.sin(t)], 1)
    penlib.brush_line(m, [tuple(p) for p in pts], 7, seed, tremor=0.8)
    return m


TA_Y, TB_Y, TX = 800, 1690, 110


def build(stage=8):
    """stage 1: tier B still blank; 2: the full page; 3..7: rings 1..(stage-2) drawn on tier B (the reader's search)."""
    img, F_ = k4.ground()
    rec = {}
    # ---- masthead
    k4.jumpy(img, "Spot the difference!", 140, 225, 96, 4501)
    sub = pen99.letter(["Five things change between picture A and picture B.", "Can you find them all?"], 38, 4502)
    k4.ink_at(img, sub, 2090 - sub.shape[1] + 20, 128, BLACK)
    # ---- the grey band: what came before (E0-E3)
    by0, by1 = 290, 760
    img[by0:by1, 110:2090] = BAND + F_[by0:by1, 110:2090, None] * 1.4
    lab = pen99.letter(["First, at 4:09..."], 36, 4503)
    k4.ink_at(img, lab, 120, by0 + 2, hexc("#fbf7ee"))
    xs = [140, 620, 1100, 1590]
    degs = [-1.3, 0.9, -0.7, 1.2]
    strip = []
    for i in range(4):
        c, used = strip_print(i)
        g = k4.sepia(c)
        ph, pw = g.shape[:2]
        s = 330 / ph
        dw = pw * s
        cx, cy = xs[i] + 230, by0 + 70 + 165
        M = k4.affine(cx, cy, s, degs[i], pw, ph)
        k4.paste(img, g.astype(np.float32), np.full((ph, pw), 255, np.uint8), M, margin=12, op=0.4)
        cap = pen99.letter(STRIP_CAPS[i], 30, 4520 + i)
        k4.ink_at(img, cap, cx - cap.shape[1] / 2, by0 + 70 + 330 + 8, hexc("#fbf7ee"))
        strip.append(dict(panel=STRIP[i][0], event=STRIP[i][2], layers=used, caption=" ".join(STRIP_CAPS[i])))
        k4.jumpy(img, str(i + 1), cx - dw / 2 - 6, by0 + 70 + 40, 46, 4530 + i, (RED,))
    rec["strip"] = strip
    # ---- the two tiers
    tiers = {}
    for which, y in (("A", TA_Y), ("B", TB_Y)):
        P, info = tier(which)
        tiers[which] = info
        if which == "B" and stage < 2:
            blank = np.zeros((TH_, TW, 3), np.float32) + PRINT_W
            k4.paste(img, blank, np.full((TH_, TW), 255, np.uint8), k4.affine(TX + TW / 2, y + TH_ / 2, 1.0, 0, TW, TH_),
                     margin=0, op=0.3)
            q = pen99.letter(["?"], 160, 4540)
            k4.ink_at(img, q, TX + TW / 2 - q.shape[1] / 2, y + TH_ / 2 - q.shape[0] / 2, hexc("#c9c2b4"))
        else:
            g = k4.sepia(P.c)
            k4.paste(img, g.astype(np.float32), np.full((TH_, TW), 255, np.uint8),
                     k4.affine(TX + TW / 2, y + TH_ / 2, 1.0, 0, TW, TH_), margin=0, op=0.4)
        bm = penlib.border_mask((H, W), [(TX, y, TX + TW, y + TH_)], 9, 4550 + (which == "B"))
        penlib.ink_onto(img, bm)
        # the tier's letter tab: a cut slip, A or B, with its time
        tab = ["A  At 4:10 he opens the cupboard."] if which == "A" else ["B  A moment later."]
        k4.slip(img, tab, 38, TX + 24, y + TH_ - 92, 10, 4560 + (which == "B"), deg=-0.6)
        k4.jumpy(img, which, TX + TW - 118, y + 30, 84, 4565 + (which == "B"), (RED,))
    diffs = differences(tiers["A"], tiers["B"])
    rec["tiers"] = tiers
    rec["differences"] = diffs
    # ---- the reader's red-pencil rings (beat frames only, never on the page itself)
    for d in diffs[:max(0, stage - 2)] if 3 <= stage <= 7 else []:
        c = (TX + d["at"][0], TB_Y + d["at"][1])
        penlib.ink_onto(img, ring_mask(c, d["r"], 4570 + d["n"]), PENCIL_RED, 0.92)
        k4.jumpy(img, str(d["n"]), c[0] + d["r"][0] * 0.72, c[1] - d["r"][1] * 0.72 - 10, 52, 4580 + d["n"], (PENCIL_RED,))
    # ---- answers, upside down at the foot
    ans = ["Answers: 1 his pencil goes up to his chin.  2 his head tips up.  3 the clock: 4:10 is now 4:11.",
           "4 the tag on the key stops swinging.  5 he says, \"Well, here I am... and what for?\"",
           "Not a difference: the brass key, still on its hook. The SERVICE door stays shut."]
    am = pen99.letter(ans, 29, 4590)
    am = am[::-1, ::-1].copy()
    k4.ink_at(img, am, (W - am.shape[1]) / 2, 2588, hexc("#3b332a"))
    pen99.folio(img, 45, C["title"])
    return np.clip(np.round(img), 0, 255).astype(np.uint8), rec


def main():
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS, ROOT / "films/swarm/99-ways/pages"):
        p.mkdir(parents=True, exist_ok=True)
    page, rec = build(2)
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    if "--page-only" in sys.argv:
        print(size)
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    bd = []
    for j in range(1, 8):
        im = page if j == 2 else build(j)[0]
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        bd.append(f"b{j:02d}: " + ("tier A and the band; tier B still a blank print with a '?'" if j == 1 else
                                     "tier B laid: the forgetting (the finished page)" if j == 2 else
                                     f"the reader's red pencil rings difference {j - 2}: {rec['differences'][j - 3]['what']}"))
    A_, B_ = rec["tiers"]["A"]["state"], rec["tiers"]["B"]["state"]
    # measured: the tiers differ only where the six differences are
    PA, _ = tier("A")
    PB, _ = tier("B")
    dif = (np.abs(PA.c - PB.c).max(2) > 18).astype(np.uint8)
    cover = np.zeros_like(dif)
    for d in rec["differences"]:
        cv2.ellipse(cover, (int(d["at"][0]), int(d["at"][1])), (int(d["r"][0] * 1.9), int(d["r"][1] * 1.9)), 0, 0, 360, 1, -1)
    outside = float((dif * (1 - cover)).sum() / max(1, dif.sum()))
    record = {
        "n": 45, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "build": "films/swarm/99-ways/build/p45_spot_the_difference.py (rig: build/rig45.py on 99-ways-template build_page.py)",
        "sources": ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:rothstein-tavern-clock-1937",
                    "99-ways-template:anrc-gold-key-1922", "99-ways:rol-34852-sainte-catherine-1913",
                    "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": [
            "rol-cutout cover grammar (page 04's kit: butter ground over the LoC 1934 sheet fibre, warm grey band, jumping red/black cover lettering letter by letter in the shared pen hand; no font)",
            "band: E0-E3 as four small press prints recomposed from the 99-ways-template rest layers P1, P4, P5, P6, with the c1 lines in cut-paper balloons, white print borders, one 7 % warm grade, pen captions",
            "the stranger in print 2 (E1): the Agence Rol 34852 cutout (page 04's GrabCut cut), head and bust only, pasted behind the ticket-window glass (lifted toward the glass tone, the TICKET OFFICE lettering kept on top of her)",
            "tiers A and B: the same Rothstein set plate view (k 0.88), the same SERVICE card, the cupboard door on its left jamb with the ANRC key on its HANDMADE hook and tag, the Rothstein clock case with its own hands re-set on the arbor, the Rothstein clerk on the FK rig at the same place and scale; only five things change between A and B (pencil arm, head, minute hand, tag angle, balloon); door swing, key, hook, card and plate are identical",
            "A: 4:10, tag swinging at 30 deg, hand dropped with the pencil; B: 4:11, tag hanging at rest (12 deg), pencil at the chin (FK solve), head tipped up 11 deg, the forgetting line in a cut-paper balloon",
            "HANDMADE: letter tabs A/B as pasted slips, upside-down answer lines at the foot in the pen hand; red-pencil rings (beats only)",
            "folio '45 / Spot the difference' (pen99.folio)"],
        "events": {"E0": "band print 1: the memo on the desk, caption '4:09. The memo: open SERVICE door at 4:15.'",
                   "E1": "band print 2: the question, tail out to the stranger seen behind the glass",
                   "E2": "band print 3: 'Ten past four, by the clock.' under the clock at 4:10",
                   "E3": "band print 4: 'Much obliged!' from the emptied window",
                   "E4": "tier A: the cupboard just opened, the key on its hook, the clock at 4:10",
                   "E5": "tier B: the same, a moment later: pencil to the chin, 'Well, here I am... and what for?'; key unmoved; SERVICE door shut"},
        "lines": LN,
        "differences": [{k: d[k] for k in ("n", "what")} for d in rec["differences"]],
        "beat": "the difference performed: tier B arrives over a blank print (the forgetting), then a reader's red pencil rings the six differences one by one",
        "beat_frames": bd,
        "self_check": {
            "size_px": [page.shape[1], page.shape[0]], "jpeg_bytes": size, "jpeg_quality": 90,
            "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
            "stated_number": 5, "differences_built": 5,
            "state_A": {k: (v if k != "pose" else {kk: round(vv, 2) for kk, vv in v.items()}) for k, v in A_.items()},
            "state_B": {k: (v if k != "pose" else {kk: round(vv, 2) for kk, vv in v.items()}) for k, v in B_.items()},
            "changed_pixels_outside_the_six_rings_fraction": round(outside, 4),
            "key_same_in_A_and_B": "door, hook and key are laid with identical parameters in A and B; the answers name the key as no difference",
            "check": "A reader finds the stated six differences (maker's judgement from the full-size page; blind reading pending)",
            "evidence": "measured (pixel difference of the two tiers confined to the five ringed regions) and perceptually judged (full-size page) by the maker"},
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/45.json", "w"), indent=1, ensure_ascii=False, default=float)
    print(json.dumps(record["self_check"], indent=1, default=float))


if __name__ == "__main__":
    main()
