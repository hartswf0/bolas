"""Page 55 Stairs (layout and page grammar; medium: brush-plate).

Six wide, shallow panels step diagonally from top left to bottom right, each one lower (and further right) than the
last, a staircase down into forgetting. The pictures are the ONE HANDMADE brush plate of the office (page 07's plate,
re-inked for page 29 with the dab-chain brush after moins-dun-quart-de-seconde-pour-vivre: build/brushkit.py), with
page 40's changing parts (clock hands, cupboard door, brushed b1m2 figures, brushed balloons); each panel is a framing
of that plate. Round the panels the page itself is brushed as a stair: a banister rail with balusters falls through
the empty upper right onto the panels' top edges, and the stringer under the steps fills the lower left in ink.
Run: python3 -I p55_stairs.py
"""
import hashlib
import json
import math
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p40_not_unlike as p40  # noqa: E402
import p29_one_fixed_lens as p29  # noqa: E402
from p29_one_fixed_lens import background, clock_hands, door_closed, plate, PW, PH  # noqa: E402
import brushkit  # noqa: E402
from b1m2 import (pen99, frame_border, comp, INK, save_page, save_beats, write_record, credit_pages, ROOT,  # noqa: E402
                  slip, W, H)

N, PID, TITLE = 55, "stairs", "Stairs"
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == PID][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SHEET = p40.SHEET

NP = 6
PWp, PHp = 1180, 410
GAP = 32
XSTEP = (1980 - PWp) // (NP - 1)                      # 160
BOXES = [(110 + k * XSTEP, 110 + k * (PHp + GAP), 110 + k * XSTEP + PWp, 110 + k * (PHp + GAP) + PHp) for k in range(NP)]
ASP = PWp / PHp
# framing of the one plate per panel: (x0, y0, width) in plate px; height = width / ASP
CROPS = [(40, 350, 1450), (0, 170, 1450), (230, 100, 1650), (0, 150, 1450), (880, 362, 1100), (800, 362, 1100)]
STEP_LABELS = ["4:09", "4:10", "4:10", "4:10", "4:11", "4:11"]
LAID = []


def door_open_tag_high(c, seed):
    """p29's door_open with the SERVICE tag hung beside the key's bow (the wide shallow steps cannot show
    the tag below the bit, where page 40 hangs it)"""
    orig = p29.slip

    def moved(c_, x, y, *a, **k):
        k["tilt"] = -6
        return orig(c_, x + 52, y - 128, *a, **k)
    p29.slip = moved
    try:
        p29.door_open(c, seed)
    finally:
        p29.slip = orig


def st5(c):   # E4 the cupboard opened, the key on its hook
    clock_hands(c, 4, 11, 4051); door_open_tag_high(c, 4052)
    p29.figs(c, p29.agent(1262, p29.AGENT_Y, face=1, scale=0.86, legs=(4, -4), sh=-4, el=12, pencil_deg=200), 4053)


def st6(c):   # E5 the forgetting: pencil to his chin; the balloon to his left (over the open leaf), low enough for the shallow step
    clock_hands(c, 4, 11, 4051); door_open_tag_high(c, 4052)
    a = p40.p7.agent2()
    p29.figs(c, a, 4063)
    fp = p40.p7.face_points(a)
    p29.bal(c, ["Well, here", "I am... and", "what for?"], 46, (1052, 500), (fp["nose"][0] - 20, fp["lip_lo"][1] + 11), 4064)


STATES = [p40.st1, p40.st2, p40.st3, p40.st4, st5, st6]


def panel(k, show=True):
    c = background()
    LAID.append(hashlib.sha256(plate().tobytes()).hexdigest())
    if show:
        STATES[k](c)
    else:
        clock_hands(c, 4, 9, 4011); door_closed(c, 4012)
    x0, y0, w = CROPS[k]
    h = int(round(w / ASP))
    assert y0 + h <= PH and x0 + w <= PW, (k, y0 + h, x0 + w)
    return cv2.resize(c[y0:y0 + h, x0:x0 + w], (PWp, PHp), interpolation=cv2.INTER_AREA)


# ------------------------------------------------------------------ the brushed stair round the panels
SSB = 2


def stair_mask(seed=5501):
    """rail + balusters (upper right) and the inked stringer (lower left), brushed at 2x and reduced"""
    im = Image.new("L", (W * SSB, H * SSB), 0)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    S = lambda pts: [(x * SSB, y * SSB) for x, y in pts]
    # the stringer: the stepped line of the panels' lower-left corners, inked solid beneath
    prof = [(96, BOXES[0][3] + 14)]
    for k in range(1, NP):
        prof += [(BOXES[k][0] - 14, BOXES[k - 1][3] + 14), (BOXES[k][0] - 14, BOXES[k][3] + 14)]
    prof += [(BOXES[-1][0] - 14, 2726)]
    poly = prof + [(96, 2726)]
    d.polygon(S(poly), fill=255)
    # tread nosings: a white brushed line along each tread inside the ink
    # rail: from above panel 1's top-right corner, falling at the stair's pitch, to the foot
    pitch = (PHp + GAP) / XSTEP
    rx0 = BOXES[0][2] + 30
    ry0 = BOXES[0][1] + 10
    rx1 = 2080
    rail = lambda x: ry0 + (x - rx0) * pitch * 0.5 + 0.0
    # rail meets the stepped tops; keep it above the top edges (rail y < top of the panel beneath)
    def top_under(x):
        for b in BOXES:
            if b[0] <= x <= b[2]:
                return b[1]
        return None
    # choose the rail pitch so its lowest point sits just above the last panel's top at the page edge
    end_y = BOXES[-1][1] - 60
    pr = (end_y - ry0) / (rx1 - rx0)
    rail = lambda x: ry0 + (x - rx0) * pr
    brushkit.brush(d, S([(rx0, ry0), (rx1, rail(rx1))]), 22 * SSB, rng, col=255, taper=(0.1, 0.1), press=0.2)
    brushkit.brush(d, S([(rx0 + 4, ry0 + 30), (rx1, rail(rx1) + 30)]), 8 * SSB, rng, col=255, taper=(0.1, 0.1))
    x = rx0 + 36
    while x < rx1 - 10:
        ytop = rail(x) + 18
        yb = None
        for b in BOXES:
            if b[0] - 6 <= x <= b[2] + 6 and b[1] > ytop + 40:
                yb = b[1] - 8 if yb is None else min(yb, b[1] - 8)
        if yb is not None:
            brushkit.brush(d, S([(x, ytop), (x + rng.uniform(-2, 2), yb)]), 9 * SSB, rng, col=255, taper=(0.15, 0.15))
        x += 46
    # newel post at the head of the rail
    brushkit.brush(d, S([(rx0, ry0 - 26), (rx0, BOXES[0][1] + PHp * 0.55)]), 26 * SSB, rng, col=255, taper=(0.05, 0.05))
    m = np.asarray(im.resize((W, H), Image.LANCZOS))
    # keep the panels clear
    m = m.copy()
    for b in BOXES:
        m[b[1] - 6:b[3] + 6, b[0] - 6:b[2] + 6] = 0
    # white nosing strokes along each tread in the stringer
    nm = Image.new("L", (W * SSB, H * SSB), 0)
    dn = ImageDraw.Draw(nm)
    for k in range(NP - 1):
        y = BOXES[k][3] + 30
        brushkit.brush(dn, S([(100, y), (BOXES[k + 1][0] - 30, y)]), 11 * SSB, rng, col=255, taper=(0.3, 0.3))
    for k in range(1, NP):
        x = BOXES[k][0] - 30
        brushkit.brush(dn, S([(x, BOXES[k - 1][3] + 34), (x, BOXES[k][3] + 22)]), 9 * SSB, rng, col=255, taper=(0.3, 0.3))
    nos = np.asarray(nm.resize((W, H), Image.LANCZOS))
    m = (m.astype(np.float32) * (1 - nos.astype(np.float32) / 255)).astype(np.uint8)
    return m


def build(upto=NP, stair=True):
    page = SHEET.copy()
    if stair:
        comp(page, stair_mask(), INK)
    for k, b in enumerate(BOXES):
        x0, y0, x1, y1 = b
        p = panel(k, k < upto)
        page[y0:y1, x0:x1] = page[y0:y1, x0:x1] * (p / 255.0)
    frame_border(page, BOXES, w=10, seed=5590)
    return page


def check_tops():
    tops = [b[1] for b in BOXES]
    return all(b > a for a, b in zip(tops, tops[1:])), tops


if __name__ == "__main__":
    ok, tops = check_tops()
    assert ok
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, "tops", tops, "plate hashes", len(set(LAID)))
    frames = []
    for u in range(1, NP + 1):
        p = img if u == NP else np.clip(np.round(build(u)), 0, 255).astype(np.uint8)
        if u < NP:
            pen99.folio(p, N, TITLE)
        frames.append(p)
    save_beats(N, frames)
    src = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
    credit_pages(src, N)
    rec = {
        "n": N, "id": PID, "title": TITLE, "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p55_stairs.py (plate and states: p40_not_unlike.py, p29_one_fixed_lens.py, p07_two_panels.py, brushkit.py, b1m2.py)",
        "sources": src,
        "made": [
            "six wide panels (1180 x 410) stepping down the page diagonally from top left to bottom right, each 442 px lower and 160 px further right than the last",
            "each panel a framing of the ONE HANDMADE brush plate of the office (page 07's plate geometry, page 29's heavier dab-chain brush after moins-dun-quart-de-seconde-pour-vivre): TICKET OFFICE window, clock, desk with the memo slip, cupboard, SERVICE door with its card; plate hash recorded per panel",
            "changing parts from page 40 (steps 1-4 as there; steps 5-6 re-staged here with the SERVICE tag hung beside the key's bow and the forgetting balloon set to his left, over the open leaf): clock hands 4:09/4:10/4:11, the cupboard door closed or opened on its left jamb with the ANRC 1922 key printed in ink on its hook tagged SERVICE, the brushed b1m2 figures (agent: spectacles, waistcoat, pencil; the stranger in her hat behind the glass), the four canon lines in brushed balloons",
            "the page brushed as a staircase round the panels (brushkit dab-chain brush, ink only): a banister rail with a newel post and balusters standing on the panels' top edges in the upper right; the stringer under the steps inked solid in the lower left with white brushed nosings",
            "hand-ruled borders; folio '55 / Stairs' (pen99.folio)"],
        "events": {"E0": "step 1: at the desk, the memo slip '4:15 - open SERVICE door. Key in cupboard.', he rises (4:09)",
                   "E1": "step 2: the stranger at the TICKET OFFICE glass, question balloon",
                   "E2": "step 3: head up to the clock at 4:10, answer balloon",
                   "E3": "step 4: she turns from the window, thanks balloon; he walks on",
                   "E4": "step 5: the cupboard open on its left jamb, the key on its hook tagged SERVICE",
                   "E5": "step 6, the lowest: pencil to his chin, forgetting balloon; the key on its hook, the SERVICE door shut"},
        "lines": LN,
        "substitutions": "none",
        "beat": "the panels are printed step by step down the stair, each one lower, until the last step is the forgetting",
        "beat_frames": [f"b{u:02d}: steps 1-{u} printed (later steps blank plate)" for u in range(1, NP + 1)],
        "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "panel_tops_px": tops, "every_top_lower_than_previous": ok,
                       "panel_lefts_px": [b[0] for b in BOXES],
                       "plate_hashes_as_laid": sorted(set(LAID)), "plate_identical_in_all_panels": len(set(LAID)) == 1,
                       "crops_plate_px": CROPS,
                       "pending": "independent blind reading not run by the maker"},
        "weaknesses": [
            "the six steps are framings of page 40's (and 29's) plate and states, so the drawings repeat those pages; the new work is the stair layout, the brushed banister and stringer, and the re-hung tag and re-placed balloon in steps 5-6",
            "the panels are shallow (1180 x 410): figures are cut at the chest or waist, and in step 2 the agent's head sits behind the question balloon (as on page 40)",
            "in steps 5-6 the SERVICE tag hangs beside the key's bow rather than from it, to keep the bit in the shallow frame; the bit is near the panel's lower edge",
            "the solid stringer is a heavy black mass on the lower left"],
    }
    write_record(rec)
    print(json.dumps(rec["self_check"], indent=1))
