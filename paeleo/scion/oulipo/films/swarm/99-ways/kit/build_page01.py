"""99 ways, page 01 "Template" (canon c1 base page).
Re-laid from the 99-ways-template b1/r2 rest layers (FORAGED photo pieces, HANDMADE memo, cards, hook, tag) with the
old balloons left out and the four c1 lines lettered afresh as cut-paper balloons in the shared pen hand; hand-ruled
borders; the 99-ways folio line. Writes:
  assets/pages/99-ways/01-template.jpg (2200x2850, q90), films/sources/99-ways/masters/01-template.png,
  films/sources/99-ways/beats/01/b01..b06.png (960x1242), films/swarm/99-ways/pages/01.json,
  and the page-01 entries of films/credits/99-ways.json.
Run: python3 -I build_page01.py"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pen99  # noqa: E402
from pen99 import penlib, ROOT, TPL  # noqa: E402

CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C1 = CANON["constraints"][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
REST = TPL / "page" / "rest"
OLD = json.load(open(TPL / "page" / "speech.json"))
W0, H0 = 2550, 3300
PANELS = {"P1": (150, 150, 890, 1090), "P2": (950, 150, 1610, 1090), "P3": (1670, 150, 2400, 1090),
          "P4": (150, 1160, 710, 2100), "P5": (770, 1160, 1740, 2100), "P6": (1800, 1160, 2400, 2100),
          "P7": (150, 2170, 1150, 3150), "P8": (1210, 2170, 2400, 3150)}
SRC = ROOT / "films/sources/99-ways"
OUT_JPG = ROOT / "assets/pages/99-ways/01-template.jpg"
OUT_PNG = SRC / "masters/01-template.png"
BEATS = SRC / "beats/01"

# c1 balloons: (panel, old balloon id for its tail tip, lines, cap, speaker)
BAL = [("P4", "b_what_time", ["Pardon me —", "have you the", "right time?"], 46, "STRANGER", "E1"),
       ("P5", "b_ten_past", ["Ten past four,", "by the clock."], 56, "AGENT", "E2"),
       ("P6", "b_thanks", ["Much", "obliged!"], 64, "STRANGER", "E3"),
       ("P8", "b_forgot", ["Well, here I am...", "and what for?"], 56, "AGENT", "E5")]
assert " ".join(" ".join(b[2]) for b in BAL).replace("— ", "— ") and \
    " ".join(BAL[0][2]) == LN["question"] and " ".join(BAL[1][2]) == LN["answer"] and \
    " ".join(BAL[2][2]) == LN["thanks"] and " ".join(BAL[3][2]) == LN["forgetting"]


def panel_rest(key):
    """Recompose a rest panel from its layers, leaving out the b1 balloons and the border."""
    d = REST / key
    c = None
    used = []
    for r in json.load(open(d / "layers.json"))["layers"]:
        if r["name"].startswith("b_") or r["name"] == "border":
            continue
        im = np.asarray(Image.open(d / r["file"])).astype(np.float32)
        if c is None:
            c = im[..., :3].copy()
        else:
            a = im[..., 3:4] / 255
            c = c * (1 - a) + im[..., :3] * a
        used.append(r["name"])
    return c, used


def balloon_on(canvas, lines, cap, tip_old, centre_old, seed):
    """Lay a c1 balloon, its centre moved only as far as needed to keep the paper inside the panel."""
    h, w = canvas.shape[:2]
    let = pen99.letter(lines, cap, seed + 1)
    rx = let.shape[1] * 0.5 * 1.18 + cap * 0.35 + 14
    ry = let.shape[0] * 0.5 * 1.10 + cap * 0.30 + 14
    cx = float(np.clip(centre_old[0], rx + 18, w - rx - 18))
    cy = float(np.clip(centre_old[1], ry + 18, h - ry - 18))
    tip = (tip_old[0] - cx, tip_old[1] - cy)
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, tip, seed, tail_w=0.24, bend=0.09)
    penlib.lay_balloon(canvas, b, (cx, cy))
    return [cx, cy], [rx, ry]


def build(reveal=8):
    pg = penlib.sheet(W0, H0)
    rec = {}
    for i, (k, box) in enumerate(PANELS.items()):
        if i >= reveal:
            continue
        x0, y0, x1, y1 = box
        c, used = panel_rest(k)
        bals = []
        for (pk, oid, lines, cap, spk, ev) in BAL:
            if pk != k:
                continue
            o = OLD[k][0]
            ctr, rad = balloon_on(c, lines, cap, o["tail_tip_panel_px"], o["centre_panel_px"], 7300 + i * 11)
            bals.append(dict(event=ev, speaker=spk, lines=lines, centre_panel_px=ctr, radii_px=rad,
                             tail_tip_panel_px=o["tail_tip_panel_px"], tail_target=o["tail_target"]))
        pg[y0:y1, x0:x1] = c
        rec[k] = dict(layers=used, balloons=bals)
    bm = penlib.border_mask((H0, W0), list(PANELS.values()), 9, 900)
    penlib.ink_onto(pg, bm)
    img = Image.fromarray(np.clip(np.round(pg), 0, 255).astype(np.uint8)).resize((pen99.PAGE_W, pen99.PAGE_H), Image.LANCZOS)
    a = np.asarray(img).astype(np.float32).copy()
    pen99.folio(a, 1, C1["title"])
    return np.clip(np.round(a), 0, 255).astype(np.uint8), rec


def main():
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS, ROOT / "films/swarm/99-ways/pages"):
        p.mkdir(parents=True, exist_ok=True)
    page, rec = build(8)
    Image.fromarray(page).save(OUT_PNG, optimize=False, compress_level=6)
    q = 90
    Image.fromarray(page).save(OUT_JPG, quality=q, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    # beats: the reading performed, one panel (and its balloon) laid at a time over P1-P3
    beat_desc = []
    for j, rv in enumerate([3, 4, 5, 6, 7, 8], 1):
        im, _ = build(rv) if rv < 8 else (page, None)
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        beat_desc.append(f"b{j:02d}: panels P1-P{rv}")
    L = np.asarray(Image.fromarray(page).convert("L")).astype(np.float32)
    checks = {
        "size_px": list(page.shape[1::-1]), "jpeg_bytes": size, "jpeg_quality": q,
        "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
        "pct_L_gt_220": round(float((L > 220).mean() * 100), 1), "pct_L_lt_40": round(float((L < 40).mean() * 100), 1),
        "margin_band_ink_only_folio": "folio line drawn by pen99.folio at baseline y=2800",
        "balloons": {k: v["balloons"] for k, v in rec.items() if v["balloons"]},
    }
    record = {
        "n": 1, "id": C1["id"], "title": C1["title"], "rule": C1["rule"], "medium": C1["medium"],
        "family": C1["family"], "canon_revision": CANON["revision"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)),
        "beats_dir": str(BEATS.relative_to(ROOT)),
        "sources": ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:rothstein-tavern-clock-1937",
                    "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934"],
        "made": ["page re-laid from films/swarm/99-ways-template/page/rest/P1..P8 (b1 r2) with the b1 balloons left out",
                 "four new cut-paper balloons lettered with the canon c1 lines in the shared pen hand (penlib.balloon_piece)",
                 "hand-ruled borders (penlib.border_mask), page scaled 2550x3300 -> 2200x2850",
                 "folio line '01 / Template' (pen99.folio); glyph supplement films/swarm/99-ways/kit/glyphs99.json"],
        "events": {"E0": "P1 memo on the desk; P2 desk left; P3 walking past the SERVICE card",
                   "E1": "P4 question, tail out through the ticket window", "E2": "P5 answer under the clock at 4:10",
                   "E3": "P6 thanks from the emptied window", "E4": "P7 cupboard open, key on its hook",
                   "E5": "P8 the forgetting line, key unmoved, SERVICE card on the closed door"},
        "lines": {k: v for k, v in LN.items()},
        "beat": "the reading performed: P1-P3 lie on the sheet, then P4 to P8 are laid one by one, each with its "
                "balloon; the last state brings the self-addressed line beside the key that stays on its hook",
        "beat_frames": beat_desc,
        "self_check": checks,
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/01.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: checks[k] for k in ("size_px", "jpeg_bytes", "in_target_0.4_1.2MB", "pct_L_gt_220", "pct_L_lt_40")}))


if __name__ == "__main__":
    main()
