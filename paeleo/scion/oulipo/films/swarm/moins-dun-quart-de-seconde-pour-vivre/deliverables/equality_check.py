"""Section 7 fixture: one plate, eight occurrences, page = film.

Run:  python3 films/swarm/moins-dun-quart-de-seconde-pour-vivre/deliverables/equality_check.py
Writes equality-check.json next to this file. Exit code 0 only if every check passes
(and both negative controls FAIL strict mode, as they must).

Film frames come from film.frame(k) of films/moins-dun-quart-de-seconde-pour-vivre.py,
before encoding. Art-only film rasters are rendered with the balloon plane removed
(module flag ART_ONLY, I2); lettered rasters with it on.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
SWARM = HERE.parent
SLUG = SWARM.name
FILMS = SWARM.parent.parent
ROOT = FILMS.parent
SRC = FILMS / "sources" / SLUG

spec = importlib.util.spec_from_file_location("film_mod", FILMS / f"{SLUG}.py")
m = importlib.util.module_from_spec(spec)
sys.argv = [sys.argv[0]]
spec.loader.exec_module(m)

P = 540
FX0 = 210            # panel x in the 960x540 frame at 1:1 (panel centred)


def sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def L(img):
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    assert np.abs(a[..., 0] - a[..., 1]).max() <= 2 and np.abs(a[..., 1] - a[..., 2]).max() <= 2, "colour found"
    return a[..., 0].astype(np.uint8)


def panel(page, key):
    x, y = m.POS[key]
    return page[y:y + P, x:x + P]


def strict(rasters, ref):
    """Strict mode: every art-only raster is byte-equal to the frozen plate."""
    return all(sha(r) == ref for r in rasters)


plate = np.asarray(Image.open(SRC / "plate" / "plate-540.png").convert("L"))
PLATE_SHA = sha(plate)
plate_json = json.load(open(SWARM / "plate.json"))
out = dict(slug=SLUG, plate_id=plate_json["plate"]["plate_id"], plate_sha256_pixels=PLATE_SHA,
           plate_sha_matches_plate_json=PLATE_SHA == plate_json["plate"]["sha256_pixels"])

# ---- page
page = L(Image.open(m.PAGE_OUT))
unlet = L(Image.open(HERE / "page-unlettered.png"))
out["page_size"] = list(page.shape[::-1])
page_art = {k: sha(panel(unlet, k)) for k in m.PANELS}
out["page_art_only_sha256"] = page_art
out["page_art_identical_8"] = len(set(page_art.values())) == 1 and PLATE_SHA in page_art.values()
# I2: lettered page panel = plate + balloon PNG; removing the plane restores the art
i2 = {}
for k in m.PANELS:
    want = m.composite(plate, m.FINAL[k]) if k in m.FINAL else plate
    i2[k] = bool((panel(page, k) == want).all())
out["page_panel_equals_plate_plus_balloon"] = i2

# ---- film: art-only over every frame of every panel slot, lettered at every hold frame
m.ART_ONLY = True
film_art, film_art_distinct = {}, {}
for k in m.PANELS:
    hs = set()
    for f in range(m.F0[k], m.HOLD_END[k] + 1):
        fr = L(m.film.frame(f))
        hs.add(sha(fr[:, FX0:FX0 + P]))
    film_art_distinct[k] = len(hs)
    film_art[k] = sorted(hs)[0] if len(hs) == 1 else sorted(hs)
m.ART_ONLY = False
out["film_art_only_sha256_per_panel_slot"] = film_art
out["film_art_only_distinct_per_slot"] = film_art_distinct
out["film_art_identical_8"] = all(v == 1 for v in film_art_distinct.values()) and len({film_art[k] for k in m.PANELS}) == 1 \
    and film_art["A1"] == PLATE_SHA
out["page_art_equals_film_art"] = out["page_art_identical_8"] and out["film_art_identical_8"] and page_art["A1"] == film_art["A1"]

holds = {}
B = m.balloons()
for k in m.PANELS:
    end_f = B[k].end_f if k in B else 0
    first = m.F0[k] + end_f
    frames_eq = []
    for f in range(first, m.HOLD_END[k] + 1):
        fr = L(m.film.frame(f))
        frames_eq.append(bool((fr[:, FX0:FX0 + P] == panel(page, k)).all()))
    last = L(m.film.frame(m.HOLD_END[k]))
    holds[k] = dict(hold_frames=[first, m.HOLD_END[k]], hold_s=round((m.HOLD_END[k] + 1 - first) / 24, 3),
                    last_frame=m.HOLD_END[k], last_frame_equals_page_panel=bool((last[:, FX0:FX0 + P] == panel(page, k)).all()),
                    every_hold_frame_equals_page_panel=all(frames_eq),
                    lettered_sha256=sha(panel(page, k)))
out["film_holds_vs_page"] = holds
out["page_equals_film_at_holds"] = all(h["last_frame_equals_page_panel"] and h["every_hold_frame_equals_page_panel"] for h in holds.values())

# ---- strings
bj = json.load(open(SWARM / "balloons.json"))
pa = bj["panels"]
A_strings = [" / ".join(pa[k]["strings"]) for k in ("A1", "A2", "A4")]
B_strings = [" / ".join(pa[k]["strings"]) for k in ("B1", "B2", "B3", "B4")]
a3_beat = [b for b in bj["beats"] if b["panel"] == "A3"]
out["strip_A"] = dict(layer_hashes=[page_art[k] for k in ("A1", "A2", "A3", "A4")], strings=A_strings,
                      distinct_non_empty=len(set(s for s in A_strings if s)), silence=pa["A3"].get("silence", False),
                      silence_beat=a3_beat[0] if a3_beat else None)
out["strip_B"] = dict(layer_hashes=[page_art[k] for k in ("B1", "B2", "B3", "B4")], strings=B_strings,
                      distinct_non_empty=len(set(s for s in B_strings if s)))
out["strings_ok"] = (out["strip_A"]["distinct_non_empty"] == 3 and out["strip_A"]["silence"] and bool(a3_beat)
                     and a3_beat[0].get("kind") == "Silence" and out["strip_B"]["distinct_non_empty"] == 4
                     and len(set(out["strip_A"]["layer_hashes"])) == 1 and len(set(out["strip_B"]["layer_hashes"])) == 1)

# ---- negative controls: each must FAIL strict mode
arts = [panel(unlet, k) for k in m.PANELS]
shifted = np.full_like(plate, m.PAPER)
shifted[:, 1:] = plate[:, :-1]                         # plate pasted at x+1 in panel B3
nc1 = arts.copy(); nc1[6] = shifted
crop1 = np.asarray(Image.open(SRC / "plate" / "plate-crop1px.png").convert("L"))
nc1b = arts.copy(); nc1b[6] = crop1
mouth = np.asarray(Image.open(SRC / "plate" / "plate-mouth-redraw.png").convert("L"))
nc2 = arts.copy(); nc2[7] = mouth                       # mouth subtly redrawn in panel B4
out["negative_controls"] = {
    "pasted_1px_off_in_B3": dict(strict_pass=strict(nc1, PLATE_SHA), diff_px=int((shifted != plate).sum())),
    "plate-crop1px.png_in_B3": dict(strict_pass=strict(nc1b, PLATE_SHA), diff_px=int((crop1 != plate).sum())),
    "plate-mouth-redraw.png_in_B4": dict(strict_pass=strict(nc2, PLATE_SHA), diff_px=int((mouth != plate).sum())),
}
out["negative_controls_all_fail"] = not any(v["strict_pass"] for v in out["negative_controls"].values())
out["positive_control_strict_pass"] = strict(arts, PLATE_SHA)

# ---- tones (aesthetic guard: two tones, mid only on edges)
pg = page.astype(np.int16)
mid = (pg >= 60) & (pg <= 200)
out["page_tones"] = dict(mid_share=round(float(mid.mean()), 4), ink_min=int(pg.min()), paper_max=int(pg.max()))

out["all_pass"] = bool(out["plate_sha_matches_plate_json"] and out["page_art_identical_8"] and all(i2.values())
                       and out["film_art_identical_8"] and out["page_art_equals_film_art"] and out["page_equals_film_at_holds"]
                       and out["strings_ok"] and out["negative_controls_all_fail"] and out["positive_control_strict_pass"])
json.dump(out, open(HERE / "equality-check.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if isinstance(v, bool)}, indent=1))
sys.exit(0 if out["all_pass"] else 1)
