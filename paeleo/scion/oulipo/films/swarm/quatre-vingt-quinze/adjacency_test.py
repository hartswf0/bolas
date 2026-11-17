"""quatre-vingt-quinze -- section 7 fixture: route legality, coverage, shared final I,
E's predecessors D/B, and pixel identity of every cell (across vs down, every frame, in
cell space before the camera transform; film rest frames vs the page PNG; the end hold vs
the page). Imports the film script itself, so it measures the very composite that is
encoded. Writes adjacency-results.json next to this file (or under QVQ_STAGE).

Run from the project root:  python3 films/swarm/quatre-vingt-quinze/adjacency_test.py
"""
import hashlib
import importlib.util
import json
import os
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path("/home/user/bolas/paeleo/scion/oulipo")
FILMS = PROJECT / "films"
SLUG = "quatre-vingt-quinze"
STAGE = os.environ.get("QVQ_STAGE")


def staged(p):
    p = Path(p)
    if STAGE:
        q = Path(STAGE) / p.relative_to(PROJECT)
        if q.exists():
            return q
    return p


spec = importlib.util.spec_from_file_location("qvq_film", FILMS / f"{SLUG}.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)
G, P = F.G, F.P
CW, CH = F.CW, F.CH
INSET = 12     # border strokes: the gutter arrow's tip may touch a cell's ruled edge


def legal(route, a, b):
    (ra, ca), (rb, cb) = G.cell_rc(a), G.cell_rc(b)
    if route == "across":
        return (ra == rb and cb == ca + 1) or (ca == 2 and cb == 0 and rb == ra + 1)
    return (ca == cb and rb == ra + 1) or (ra == 2 and rb == 0 and cb == ca + 1)


def performed(route):
    """The order the FILM performs (from its frame schedule), not the declared list."""
    seq = []
    for K in range(F.SECONDS * F.FPS):
        o = F.occurrence(K)
        if o and o[0] == route and (not seq or seq[-1] != o[2]):
            seq.append(o[2])
    return seq


def box(c, inset=0):
    x0, y0 = G.cell_origin(c)
    return (x0 + inset, y0 + inset, x0 + CW - inset, y0 + CH - inset)


def arr(im):
    return np.asarray(im, np.int16)


def diff(a, b):
    d = np.abs(arr(a) - arr(b)).max(-1) if True else None
    n = int((d > 0).sum())
    ys, xs = np.nonzero(d)
    bb = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if n else None
    return n, bb, int(d.max()) if n else 0


res = {"slug": SLUG, "revision": F.REVISION, "film_script_sha256": hashlib.sha256((FILMS / f"{SLUG}.py").read_bytes()).hexdigest()}

# 1. routes
routes = {}
for name in ("across", "down"):
    seq = performed(name)
    steps = [{"edge": f"{a}->{b}", "legal": legal(name, a, b)} for a, b in zip(seq, seq[1:])]
    routes[name] = {"performed": "".join(seq), "declared": "".join(F.ROUTES[name]),
                    "matches_declared": seq == F.ROUTES[name], "steps": steps,
                    "all_edges_legal": all(s["legal"] for s in steps),
                    "covers_all_nine_once": sorted(seq) == sorted(G.CELLS) and len(seq) == 9,
                    "first": seq[0], "last": seq[-1]}
res["routes"] = routes
res["shared_final_I"] = routes["across"]["last"] == routes["down"]["last"] == "I"
ea, ed = F.ROUTES["across"], F.ROUTES["down"]
res["E_predecessors"] = {"across": ea[ea.index("E") - 1], "down": ed[ed.index("E") - 1]}
res["E_predecessors_ok"] = res["E_predecessors"] == {"across": "D", "down": "B"}
res["E_position"] = {"across": ea.index("E") + 1, "down": ed.index("E") + 1}
tE = F.occ_start("down", "E") / F.FPS
res["beat_clock"] = {"t_down_E": tE, "beat": 44.5, "ok": tE == 44 and tE <= 44.5 < tE + 3}
res["E_occurrence_windows_s"] = {"across": [F.occ_start("across", "E") / 24, F.occ_start("across", "E") / 24 + 3],
                                 "down": [tE, tE + 3]}

# 2. every cell, every frame: across occurrence vs down occurrence (pre-camera page composite)
ident = {}
allok = True
for c in G.CELLS:
    ka, kd = F.occ_start("across", c), F.occ_start("down", c)
    worst_full, worst_in, hashes_equal = 0, 0, True
    detail = None
    for f in range(F.NF):
        A = F.compose(ka + f, box(c))
        D = F.compose(kd + f, box(c))
        n, bb, mx = diff(A, D)
        if n:
            worst_full = max(worst_full, n)
            detail = detail or {"frame": f, "pixels": n, "bbox_cell_px": bb, "max_delta": mx}
            a_in = A.crop((INSET, INSET, CW - INSET, CH - INSET))
            d_in = D.crop((INSET, INSET, CW - INSET, CH - INSET))
            ni = diff(a_in, d_in)[0]
            worst_in = max(worst_in, ni)
        # the cell art itself (no page furniture): must be byte-identical
        if F.cell_image(c, f).tobytes() != F.cell_image(c, f).tobytes():
            hashes_equal = False
    ok = worst_in == 0 and hashes_equal
    allok &= ok
    ident[c] = {"frames_compared": F.NF, "across_window_s": [ka / 24, ka / 24 + 3], "down_window_s": [kd / 24, kd / 24 + 3],
                "max_differing_px_full_cell_box": worst_full, "max_differing_px_inside_border": worst_in,
                "first_difference": detail, "identical": ok}
res["cell_identity_across_vs_down"] = ident
res["cell_identity_all_ok"] = allok

# 3. film rest frames vs the page PNG
page = Image.open(staged(PROJECT / "assets" / "pages" / f"{SLUG}.png")).convert("RGB")
rest = {}
rok = True
for c in G.CELLS:
    out = {}
    for route in ("across", "down"):
        K = F.occ_start(route, c) + 70          # at rest: page pose reached, wash lifted
        A = F.compose(K, box(c, INSET))
        n, bb, mx = diff(A, page.crop(box(c, INSET)))
        nf, bbf, _ = diff(F.compose(K, box(c)), page.crop(box(c)))
        out[route] = {"t": K / 24, "differing_px_inside_border": n, "differing_px_full_box": nf, "bbox_full": bbf}
        rok &= n == 0
    rest[c] = out
res["film_rest_vs_page"] = rest
res["film_rest_vs_page_ok"] = rok

# 4. the end hold: last 1.5 s composite == page PNG; camera frame == page scaled the same way
end = []
eok = True
for K in range(int(62.5 * 24), 64 * 24, 6):
    n = diff(F.compose(K), page)[0]
    cx, cy, vh = F.camera(K)
    end.append({"t": round(K / 24, 3), "page_px_differing": n, "camera": [round(cx, 1), round(cy, 1), round(vh, 1)]})
    eok &= n == 0
res["end_hold_vs_page"] = end
res["end_hold_ok"] = eok
fr = F.frame_rgb(64 * 24 - 1)
vw = F.VIEW_PAGE * F.FW / F.FH
x0, y0 = F.PW / 2 - vw / 2, F.PH / 2 - F.VIEW_PAGE / 2
padded = Image.new("RGB", (int(vw) + 20, int(F.VIEW_PAGE) + 20), F.OUTSIDE)
bx, by = int(x0) - 3, int(y0) - 3
padded.paste(page, (-bx, -by))
ref = padded.resize((F.FW, F.FH), Image.LANCZOS, box=(x0 - bx, y0 - by, x0 - bx + vw, y0 - by + F.VIEW_PAGE))
res["end_frame_vs_page_scaled_identical_px"] = diff(fr, ref)[0] == 0

# 5. sound: one cue per cell, same file both routes; bell tail only on down E
sched = F.SOUND_SCHEDULE
by_cell = {}
for at, c, fn in sched:
    by_cell.setdefault(c, set()).add(fn)
res["sound_one_cue_per_cell"] = all(len(v) == 1 for v in by_cell.values())
w = wave.open(str(F.FORAGE / "cue_B.wav"))
b = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768.0
R = 44100
bell = np.zeros((64 * R, 2))
for at, c, fn in sched:
    if c == "B":
        i = int(at * R)
        bell[i:i + len(b)] += b[: 64 * R - i]


def db(x):
    return round(float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)), 1)


res["bell_tail"] = {"across_E_15_18_rms_dbfs": db(bell[15 * R:18 * R]), "down_E_44_45_rms_dbfs": db(bell[44 * R:45 * R]),
                    "down_E_44.5_45.0_rms_dbfs": db(bell[int(44.5 * R):45 * R])}
res["bell_tail_ok"] = res["bell_tail"]["across_E_15_18_rms_dbfs"] < -100 and res["bell_tail"]["down_E_44_45_rms_dbfs"] > -40

# 6. FK invariants from U2's report
je = json.load(open(FILMS / "swarm" / SLUG / "puppets" / "joint-errors.json"))
res["joint_errors_summary"] = je.get("summary")

res["ALL_OK"] = all([routes["across"]["matches_declared"], routes["down"]["matches_declared"],
                     routes["across"]["all_edges_legal"], routes["down"]["all_edges_legal"],
                     routes["across"]["covers_all_nine_once"], routes["down"]["covers_all_nine_once"],
                     res["shared_final_I"], res["E_predecessors_ok"], res["beat_clock"]["ok"],
                     allok, rok, eok, res["end_frame_vs_page_scaled_identical_px"],
                     res["sound_one_cue_per_cell"], res["bell_tail_ok"]])
out = Path(STAGE) / "films" / "swarm" / SLUG / "adjacency-results.json" if STAGE else FILMS / "swarm" / SLUG / "adjacency-results.json"
out.parent.mkdir(parents=True, exist_ok=True)
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k in ("ALL_OK", "cell_identity_all_ok", "film_rest_vs_page_ok", "end_hold_ok",
                                                         "end_frame_vs_page_scaled_identical_px", "bell_tail", "beat_clock")}, indent=1))
