"""Page 40 Not unlike (voice and language; medium: brush-plate).

Every caption states its fact by denying the opposite. The pictures are the one HANDMADE brush plate of the office
(page 07's plate, re-inked heavier for page 29: dab-chain brush after moins-dun-quart-de-seconde-pour-vivre, build/
brushkit.py), printed in six panels, each panel a different framing (crop) of the same unchanged plate, so the plate is
one and the eye moves; only the figures (b1m2 model, brushed), the clock hands and the cupboard door change.
Captions on pasted slips in the shared pen hand; the four canon lines in the brushed balloons.
Run: python3 -I p40_not_unlike.py
"""
import hashlib
import json
import re
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p29_one_fixed_lens as p29  # noqa: E402
from p29_one_fixed_lens import (background, clock_hands, door_closed, door_open, figs, bal, agent, stranger, agent_mouth,
                                plate, WX, AGENT_Y, PW, PH)  # noqa: E402
import p07_two_panels as p7  # noqa: E402
from b1m2 import pen99, slip, frame_border, save_page, save_beats, write_record, credit_pages, ROOT  # noqa: E402

N, PID, TITLE = 40, "not-unlike", "Not unlike"
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == PID][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SHEET = cv2.GaussianBlur(pen99.sheet99(), (0, 0), 0.8)

CAPTIONS = [
    ["He was not idle. The memo was no riddle:", "not later than 4:15, and not without the key."],
    ["He had not gone far when a voice,", "not his own, came through the glass."],
    ["He did not guess. The clock was not slow."],
    ["She did not linger. It was no long delay."],
    ["The cupboard was not locked.", "The key was not hidden."],
    ["Not a thing was missing but the reason.", "The key did not move; the door did not open."],
]


def st1(c):   # E0 at the desk, the memo: he rises
    clock_hands(c, 4, 9, 4011); door_closed(c, 4012)
    figs(c, agent(930, AGENT_Y, face=-1, scale=0.86, legs=(4, -4), sh=30, el=-70, wr=10, tilt=18, pencil_deg=200), 4013)


def st2(c):   # E1 the question at the window
    clock_hands(c, 4, 10, 4021); door_closed(c, 4012)
    figs(c, stranger(WX - 10, p29.SILL + 6, face=1, scale=1.25, glove=True), 4022)
    figs(c, agent(1010, AGENT_Y, face=-1, scale=0.86, legs=(8, -8), sh=6, el=10, tilt=-2, pencil_deg=200), 4023)
    bal(c, ["Pardon me —", "have you the", "right time?"], 80, (760, 420), (300, 470), 4024)


def st3(c):   # E2 he looks up at the clock and answers
    clock_hands(c, 4, 10, 4021); door_closed(c, 4012)
    a = agent(1010, AGENT_Y, face=-1, scale=0.86, legs=(8, -8), sh=10, el=-20, tilt=-26, pencil_deg=200)
    figs(c, a, 4033)
    bal(c, ["Ten past four,", "by the clock."], 80, (1080, 290), agent_mouth(a), 4034)


def st4(c):   # E3 the thanks; she turns from the window; he walks on
    clock_hands(c, 4, 10, 4021); door_closed(c, 4012)
    figs(c, stranger(WX - 60, p29.SILL + 6, face=-1, scale=1.2, tilt=-6), 4042)
    figs(c, agent(1060, AGENT_Y, face=1, scale=0.86, legs=(14, -12), sh=-8, el=16, pencil_deg=200), 4043)
    bal(c, ["Much", "obliged!"], 84, (760, 360), (330, 450), 4044)


def st5(c):   # E4 the cupboard opened, the key on its hook
    clock_hands(c, 4, 11, 4051); door_open(c, 4052)
    figs(c, agent(1262, AGENT_Y, face=1, scale=0.86, legs=(4, -4), sh=-4, el=12, pencil_deg=200), 4053)


def st6(c):   # E5 the forgetting: pencil to his chin
    clock_hands(c, 4, 11, 4051); door_open(c, 4052)
    a = p7.agent2()
    figs(c, a, 4063)
    fp = p7.face_points(a)
    bal(c, ["Well, here I am...", "and what for?"], 80, (1560, 330), (fp["nose"][0] + 4, fp["lip_lo"][1] + 11), 4064,
        ctrl=(1440, 470))


STATES = [st1, st2, st3, st4, st5, st6]
GX, GY = 30, 30
PWp = (1980 - GX) // 2
PHp = (2620 - 2 * GY) // 3
ASP = PWp / PHp
# the framing of the one plate in each panel: (x0, y0, width) in plate px; height follows the panel's aspect
CROPS = [(380, 70, 1000), (0, 40, 1150), (380, 20, 1000), (0, 40, 1150), (880, 130, 1100), (880, 130, 1100)]
BOXES = []
for r in range(3):
    for col in range(2):
        x0 = 110 + col * (PWp + GX)
        y0 = 110 + r * (PHp + GY)
        BOXES.append((x0, y0, x0 + PWp, y0 + PHp))
LAID = []


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


def build(upto=6):
    page = SHEET.copy()
    for k, b in enumerate(BOXES):
        x0, y0, x1, y1 = b
        p = panel(k, k < upto)
        page[y0:y1, x0:x1] = page[y0:y1, x0:x1] * (p / 255.0)
        if k < upto:
            slip(page, x0 + 14, y0 + 14, CAPTIONS[k], 40, 4090 + k, pad=(20, 12), shadow=0.3, weight=0.14)
    frame_border(page, BOXES, w=10, seed=4099)
    return page


def check_captions():
    return all(re.search(r"\b(not|no)\b", " ".join(c), re.I) for c in CAPTIONS)


if __name__ == "__main__":
    assert check_captions()
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, "panel", PWp, PHp, "plate hashes", len(set(LAID)))
    frames = []
    for u in range(1, 7):
        p = img if u == 6 else np.clip(np.round(build(u)), 0, 255).astype(np.uint8)
        if u < 6:
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
        "build": "films/swarm/99-ways/build/p40_not_unlike.py (plate and states machinery: p29_one_fixed_lens.py, p07_two_panels.py, brushkit.py, b1m2.py)",
        "sources": src,
        "made": [
            "the ONE HANDMADE brush plate of the office (page 07's plate geometry, inked with page 29's heavier dab-chain brush after moins-dun-quart-de-seconde-pour-vivre): window with TICKET OFFICE, clock, desk and lamp, cupboard, SERVICE door with its card, wainscot and floor; printed unchanged in all six panels (sha256 of the plate as laid recorded), each panel a different framing of it",
            "changing parts only: the clock hands (4:09, 4:10, 4:11), the cupboard door (closed / opened overlay with the ANRC 1922 key printed in ink on its hook and a SERVICE tag), and the brushed b1m2 figures (agent with spectacles, waistcoat, pencil; the stranger in her hat behind the glass)",
            "six captions on pasted slips in the shared pen hand, each stating its fact by denying the opposite ('He was not idle', 'The clock was not slow', 'The cupboard was not locked', 'The key did not move; the door did not open')",
            "the four canon lines verbatim in the brushed balloons; hand-ruled borders; folio '40 / Not unlike' (pen99.folio)"],
        "captions": [" ".join(c) for c in CAPTIONS],
        "events": {"E0": "P1: memo slip on the desk ('4:15 - open SERVICE door. Key in cupboard.'), he rises; 'He was not idle. The memo was no riddle'",
                   "E1": "P2: the stranger at the glass, question balloon; 'He had not gone far when a voice, not his own...'",
                   "E2": "P3: head up to the clock at 4:10, answer balloon; 'He did not guess. The clock was not slow.'",
                   "E3": "P4: she turns from the window, thanks balloon, he walks on; 'She did not linger. It was no long delay.'",
                   "E4": "P5: the cupboard open, key on its hook; 'The cupboard was not locked. The key was not hidden.'",
                   "E5": "P6: pencil to his chin, forgetting balloon; 'Not a thing was missing but the reason. The key did not move; the door did not open.'"},
        "lines": LN,
        "substitutions": "none: the four lines verbatim (balloons are speech, not captions)",
        "beat": "the six framings of the one plate are printed in turn, each with its caption slip pasted on: the reader's eye moves across the same drawing while the denials carry the facts",
        "beat_frames": [f"b{u:02d}: panels 1-{u} printed with their caption slips" for u in range(1, 7)],
        "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "every_caption_has_not_or_no": check_captions(),
                       "plate_hashes_as_laid": sorted(set(LAID)), "plate_identical_in_all_panels": len(set(LAID)) == 1,
                       "crops_plate_px": CROPS,
                       "pending": "independent blind reading not run by the maker"},
    }
    write_record(rec)
    print(json.dumps(rec["self_check"], indent=1))
