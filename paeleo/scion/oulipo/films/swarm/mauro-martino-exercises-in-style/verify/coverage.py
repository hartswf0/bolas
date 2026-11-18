"""U4 VERIFY: variant authors' delta log, render-operator pinning and coverage verifier for
"Exercises in Style" (Mauro Martino), SCION controlled variation.

Uses rig/rig.py and stage/stage.py (read-only) to render the six samples
    {baseline (street-side, cut-paper), d-treatment (photographic-plate), d-camera (overhead)} x {0417, 0418}
and measures, from rendered masks and frames:
    - manifests + PromptDeltas, asserting keys(diff) == {field}          -> verify/manifests.json
    - render attempts pinned: generator_rev, seeds, settings, conditioning -> verify/render-attempts.json
    - per-anchor masks for all six samples (visible | partial | lost)
    - outline IoU between treatments (puppets: must be 1.0; stage outlines reported)
    - protected-mask identity between seeds (every frame, side and plan)
    - byte-identical replay of frames 0, 29, 132 (fresh subprocess)
    - per-clip audio PCM hashes once the editor's mix exists (else "pending")
    - the counterexample: an RNG-coupled overhead projector, which the harness must reject
    - comparison-sheet.jpg (six samples at clip t=1.20 + baseline beside the reference, measured)
                                                                           -> verify/coverage.json
Run:  python3 -I coverage.py            (full; ~5 min)
      python3 -I coverage.py --replay OUT.json   (internal: fresh-process replay hashes)
"""
import sys, json, hashlib, math, time, subprocess, importlib.util, builtins, functools, runpy
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
SLUG = "mauro-martino-exercises-in-style"
WS = ROOT / "films/swarm" / SLUG
VDIR = WS / "verify"
MEDIA = ROOT / "films/sources" / SLUG / "verify"
SCRIPT = ROOT / "films" / (SLUG + ".py")
REF = ROOT / "assets/references/martinoCharcoal.webp"
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")   # has Δ (the Plex woff2 subset lacks it)
SEEDS = (417, 418)
FPS, NF = 24, 168
REPLAY_FRAMES = (0, 29, 132)
CONDS = ("baseline", "d-treatment", "d-camera")
# film time of each clip window (plan.md section 5): S1 S2 | S4 S5 | S7 S8
CLIP_AT = {("baseline", 417): 4.0, ("baseline", 418): 11.0, ("d-treatment", 417): 20.0, ("d-treatment", 418): 27.0,
           ("d-camera", 417): 36.0, ("d-camera", 418): 43.0}
SHOT = {("baseline", 417): "S1", ("baseline", 418): "S2", ("d-treatment", 417): "S4", ("d-treatment", 418): "S5",
        ("d-camera", 417): "S7", ("d-camera", 418): "S8"}
PAPER_TOK, INK_TOK, TINT_TOK, SHADE_TOK = (238, 230, 214), (34, 33, 31), (149, 142, 133), (211, 203, 188)


def sha1b(b):
    return hashlib.sha1(b).hexdigest()


def sha1f(p):
    return sha1b(Path(p).read_bytes())


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def load_film():
    """Import the delivered film script as a module (no rendering): its render(M, seed, t) is the
    render path checked here, with its stage rebinds (Vilgrain/Wilson crowd and fills, outline-
    preserving photographic layers, roof-light cell) applied to stage.py/rig.py in-process."""
    sys.path.insert(0, str(ROOT / "films"))
    spec = importlib.util.spec_from_file_location("mmes_film", SCRIPT)
    F = importlib.util.module_from_spec(spec); sys.modules["mmes_film"] = F; spec.loader.exec_module(F)
    return F, F.R, F.S


F, R, S = load_film()


# ================================================================== (1) manifests + PromptDeltas
def canon(m):
    return json.dumps(m, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def mhash(m):
    return sha1b(canon(m).encode())


def diff(a, b):
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


def apply_delta(M0, d):
    assert d["baseline_hash"] == mhash(M0), "P1: delta written against another baseline"
    assert d["field"] in ("camera", "treatment"), "P2: field outside the variation axes"
    assert M0[d["field"]] == d["old"] and d["new"] != d["old"], "P2: old/new mismatch"
    M = dict(M0); M[d["field"]] = d["new"]
    assert set(diff(M0, M)) == {d["field"]}, "P3: diff touches more than the named field"
    return M


def manifests():
    M0 = R.baseline_manifest()
    h0 = mhash(M0)
    assert h0 == R.manifest_sha1(M0)
    D = [dict(id="d-camera", baseline_hash=h0, field="camera", old="street-side", new="overhead",
              intended_effect="plan view of the same world: the shove reads as a displacement of the man's hat disc onto the stanchion dot; "
                              "same seeds, same anchor times, same runner count; long neck and seat-in-window predicted lost"),
         dict(id="d-treatment", baseline_hash=h0, field="treatment", old="cut-paper", new="photographic-plate",
              intended_effect="same outlines, photographic fill: every puppet outline identical (IoU 1.0), the bus, facade and cobbles "
                              "refilled with Rol 1916 plate texture inside the baseline's carved outlines, crowd in the Rol 1919 cutouts' own greys, "
                              "puppet parts filled with Rol 1919 cloth swatches")]
    out = dict(schema=dict(Manifest="{scene, camera, treatment, seeds, duration, fps, drawings_per_second, size, generator_rev, destination}",
                           PromptDelta="{baseline_hash, field, old, new, intended_effect}"),
               canonical_form="json.dumps(m, sort_keys=True, separators=(',', ':'), ensure_ascii=False); sha1 of UTF-8",
               baseline=dict(id="baseline", manifest=M0, sha1=h0), deltas=[])
    for d in D:
        M = apply_delta(M0, d)
        df = diff(M0, M)
        out["deltas"].append(dict(d, manifest=M, sha1=mhash(M), diff={k: dict(old=v[0], new=v[1]) for k, v in df.items()},
                                  diff_keys=sorted(df), assert_diff_eq_field=sorted(df) == [d["field"]]))
    # self-test: a two-field delta must be refused
    try:
        bad = dict(D[0]); M = dict(M0); M["camera"] = "overhead"; M["treatment"] = "photographic-plate"
        assert set(diff(M0, M)) == {bad["field"]}
        refused = False
    except AssertionError:
        refused = True
    out["self_test_two_field_delta_refused"] = refused
    return out


# ================================================================== rendering the six samples
def render(cond, seed, t):
    """One sample frame (RGB PIL), exactly as the film renders it: F.render(F.manifest(cond), seed, t)."""
    return F.render(F.manifest(cond), seed, t).convert("RGB")


def frame_hash(im):
    return sha1b(np.asarray(im).tobytes())


# ================================================================== (3a) per-anchor masks
def part_mask(P, names, Pz):
    """Screen-px mask of the named parts of one puppet (side elevation), clipped like the rig clips it."""
    polys, _, _ = R.parts_world(P)
    im = Image.new("L", (R.W * 2, R.H * 2), 0); d = ImageDraw.Draw(im)
    for z, n, p in polys:
        if n in names:
            d.polygon([tuple(q * 2) for q in p], fill=255)
    m = cv2.resize(np.asarray(im, np.float32) / 255, (R.W, R.H), interpolation=cv2.INTER_AREA)
    r = R._clip_rect(P, Pz)
    if r is not None:
        x0, y0, x1, y1 = [int(round(v)) for v in r]
        c = np.zeros_like(m); c[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = 1; m *= c
    return m


def puppet(Pz, pid):
    for q in Pz["puppets"]:
        if q["id"] == pid:
            return q
    return None


def side_occluder(seed, cond, Pz, group):
    """Alpha of what lies in front of a puppet group in the side view (bus front hardware, and the street runners for platform puppets)."""
    tr = "cut-paper" if cond == "baseline" else "photographic-plate"
    front = np.asarray(S.shift(S.bus_front(seed, tr), Pz["dx"]), np.float32)[..., 3] / 255
    occ = front.copy()
    if group in ("platform", "window"):
        occ = np.maximum(occ, R.side_mask(Pz, group="street"))
    return occ


def board_contrast(img, rect):
    a = np.asarray(img.convert("L"), np.float32)
    x0, y0, x1, y1 = [int(round(v)) for v in rect]
    c = a[max(0, y0):y1, max(0, x0):x1]
    if c.size == 0:
        return 0.0, 0.0
    return float((c > 170).mean()), float((c < 80).mean())


def anchor_list():
    return json.loads((WS / "rig/anchors.json").read_text())["anchors"]


ANCHOR_T = {"A0": 3.0, "A1": 0.90, "A2": 1.05, "A3": 1.20, "A4": 4 / 3, "A4c": 1.50, "A5": 2.60, "A5v": 4.0, "A5d": 4.5,
            "A6": 5.50, "A6w": 5.50, "A7": 6.00, "A8": 6.80, "A-neck": 1.20, "A-hat": 1.20}


def cover(cond, seed):
    """Coverage of one sample: anchor id -> {status, px, t, why}. Also returns mask tiles for the sheet."""
    res, tiles = {}, []
    for A in anchor_list():
        aid = A["id"]; t = ANCHOR_T.get(aid, A["t"]) + 1e-6
        Pz = R.pose(seed, t)
        img = render(cond, seed, t)
        side = cond != "d-camera"
        M = puppet(Pz, "man"); J = puppet(Pz, "jostler"); C = puppet(Pz, "conductor")
        mask = np.zeros((R.H, R.W), np.float32); status, why, px = "lost", "", 0
        if aid == "A0":
            if side:
                bx0, by0, bx1, by1 = S.board_rect(); rect = (bx0 + Pz["dx"], by0, bx1 + Pz["dx"], by1)
            else:
                x0, y0, x1, y1 = S.plan_bus_rect(); rect = (x0 + 120 + Pz["dx"], y1 - 35, x0 + 430 + Pz["dx"], y1 - 13)
            lt, dk = board_contrast(img, rect)
            mask[int(rect[1]):int(rect[3]), int(rect[0]):int(rect[2])] = 1
            px = int(mask.sum()); status = "visible" if lt > 0.08 and dk > 0.2 else ("partial" if lt > 0.02 else "lost")
            why = "board light-letter fraction %.3f, ink fraction %.3f (%s board)" % (lt, dk, "side" if side else "roof-edge")
        elif aid in ("A1", "A8"):
            tr = "cut-paper" if cond != "d-treatment" else "photographic-plate"
            lay = S.shift(S.bus_body(seed, tr), Pz["dx"]) if side else S.shift(S.plan_bus(seed), Pz["dx"])
            mask = np.asarray(lay, np.float32)[..., 3] / 255; px = int((mask > 0.5).sum())
            dxs = [S.bus_x(f / FPS) for f in range(NF)]
            stop_f = next(f for f in range(1, NF) if dxs[f] == dxs[f - 1])
            if side:
                status = "visible" if px > 1000 else "lost"
                why = "bus layer %d px; layer slide stops at frame %d (t %.3f); wheels rotate with travel and stop with it" % (px, stop_f - 1, (stop_f - 1) / FPS)
            else:
                status = "partial" if px > 1000 else "lost"
                why = ("roof layer %d px slides and stops at frame %d, but the rotating wheels (the anchor's prop) are under the roof: "
                       "stop reads only as the roof halting" % (px, stop_f - 1))
            if aid == "A8":
                why = "bus dx at 6.80 = %.1f px (pull-away); " % Pz["dx"] + why.split(";", 1)[0]
        elif aid == "A2":
            if side:
                mask = R.side_mask(Pz, group="street")
                g = R.geo(); x0 = int(g["plat0"] - 260); mask[:, :max(0, x0)] = 0
            else:
                mask = R.plan_mask(Pz, group="street"); g = R.geo(); mask[:, :max(0, int(g["plat0"] - 260))] = 0
            px = int((mask > 0.5).sum()); status = "visible" if px > 200 else "lost"
            why = "%d runners in pose; street-mask px near the platform %d" % (sum(1 for q in Pz["puppets"] if q["group"] == "street"), px)
        elif aid == "A3":
            if side:
                hand = part_mask(J, ("fore_n",), Pz); man = R.side_mask(Pz, ids=("man",))
            else:
                hand = R.plan_mask(Pz, ids=("jostler",), parts=("arm",)); man = R.plan_mask(Pz, ids=("man",))
            contact = cv2.dilate((hand > 0.3).astype(np.uint8), np.ones((5, 5), np.uint8)) & (man > 0.3).astype(np.uint8)
            mask = np.maximum(hand, man * 0.5); px = int(contact.sum())
            status = "visible" if px > 3 else "lost"
            why = "jostler %s within 2 px of the man: %d contact px" % ("forearm/hand" if side else "plan arm bar", px)
        elif aid == "A4":
            stx = R.geo()["stx"] + Pz["dx"]
            if side:
                man = R.side_mask(Pz, ids=("man",)); col = np.zeros_like(man); col[:, int(stx) - 3:int(stx) + 3] = 1
                hit = (man > 0.3) * col; why = "man's back within 3 px of the stanchion line x=%.1f: %d px; contact flag %s" % (stx, int(hit.sum()), M.get("contact"))
            else:
                man = R.plan_mask(Pz, ids=("man",)); sy = S.plan_xy(0, S.WORLD["bus_z1"] - 6)[1]
                yy, xx = np.mgrid[0:R.H, 0:R.W]; col = ((xx - (stx + 3)) ** 2 + (yy - sy) ** 2 < 14 ** 2).astype(np.float32)
                hit = (man > 0.3) * col; why = "man's plan forms within 9.5 px of the stanchion dot: %d px" % int(hit.sum())
            mask = np.maximum(man * 0.5, col * 0.3); px = int(hit.sum()); status = "visible" if px > 3 else "lost"
        elif aid == "A4c":
            P2 = dict(Pz); P2["cord"] = None
            if side:
                a = R.side_mask(Pz, ids=("man",)); b = R.side_mask(P2, ids=("man",))
            else:
                a = R.plan_mask(Pz, ids=("man",)); b = R.plan_mask(P2, ids=("man",))
            mask = np.clip(a - b, 0, 1); px = int((mask > 0.3).sum())
            sim = R.simulate(); ang = [sim[2 * d]["end_angle"] for d in range(R.ND)]
            status = ("visible" if side else "partial") if px > 3 else "lost"
            why = ("cord px (mask with cord minus without) %d at t 1.50; " % px) + ("3-link braid end" if side else ("short tail on the notched ring" if px > 3 else "the plan cord tail falls inside the hat disc, so the swing adds no pixels: cord swing not readable from above"))
        elif aid in ("A5", "A5d", "A6", "A6w", "A-hat", "A-neck"):
            names = {"A5": ("fore_n", "arm_n"), "A5d": None, "A6": None, "A6w": None, "A-hat": ("hat",), "A-neck": ("neck",)}[aid]
            if side:
                mask = part_mask(M, names, Pz) if names else R.side_mask(Pz, ids=("man",))
                occ = side_occluder(seed, cond, Pz, M["group"])
                vis = mask * (1 - occ); px = int((vis > 0.3).sum())
                status = "visible" if px > 20 else ("partial" if px > 0 else "lost")
                why = "%s px unoccluded %d (of %d drawn); man in group '%s'" % ("+".join(names) if names else "man", px, int((mask > 0.3).sum()), M["group"])
            else:
                if aid == "A-neck":
                    plan_names = [n for n, _ in R.plan_parts(M, Pz)]
                    px = 0; status = "lost"
                    why = "plan forms drawn for the man: %s; the neck is a vertical part under the hat disc and has no plan form (0 px)" % plan_names
                elif aid == "A-hat":
                    mask = R.plan_mask(Pz, ids=("man",), parts=("hat", "ring")); px = int((mask > 0.3).sum())
                    status = "partial" if px > 20 else "lost"
                    why = "hat disc + notched cord ring %d px: hat legible, braid transformed into a ring of 14 notches" % px
                elif aid == "A5":
                    mask = R.plan_mask(Pz, ids=("man",), parts=("arm",)); px = int((mask > 0.3).sum())
                    status = "partial" if px > 0 else "lost"
                    why = "plan arm bars of the man %d px: the open hand raised toward the jostler projects only as a short bar; head turn not readable from above" % px
                else:
                    mask = R.plan_mask(Pz, ids=("man",)); px = int((mask > 0.3).sum())
                    if aid == "A6":
                        mask = F.seat_cell_mask(Pz, ids=("man",)); px = int((mask > 0.3).sum())
                        status = "visible" if px > 20 else "lost"
                        why = "man's hat disc + cord ring inside the rear-bay roof-light cell at t %.2f: %d px (seat A taken, seen from above)" % (t, px)
                    elif aid == "A6w":
                        mask = np.zeros((R.H, R.W), np.float32); px = 0; status = "lost"
                        why = "the rear side pane is a feature of the side elevation; from above there is no window to see the seat through (the seat itself reads via the roof-light, A6)"
                    else:
                        status = "partial" if px > 20 else "lost"
                        why = "man plan px %d: his disc moves toward the bulkhead; the stoop itself has no plan form" % px
        elif aid == "A5v":
            if side:
                win = R.geo()["win"]
                mask = R.side_mask(Pz, group="window"); px = int((mask > 0.3).sum())
                P0 = R.pose(seed, 3.5); m0 = R.side_mask(P0, group="window")
                status = "visible" if abs(int((m0 > 0.3).sum()) - px) > 50 else "partial"
                why = "window-group px %d at t 4.0 vs %d at t 3.5 (seed vacates %s)" % (px, int((m0 > 0.3).sum()), Pz["vacate"])
            else:
                mask = F.seat_cell_mask(Pz); px = int((mask > 0.3).sum())
                m0 = F.seat_cell_mask(R.pose(seed, 3.5)); px0 = int((m0 > 0.3).sum())
                status = "visible" if abs(px0 - px) > 50 else ("partial" if abs(px0 - px) > 0 else "lost")
                why = "roof-light cell: seated plan px %d at t 3.5 vs %d at t 4.0 (p1 slides out of seat A)" % (px0, px)
        elif aid == "A7":
            if side:
                Pb = R.pose(seed, 5.80 + 1e-6)
                a = R.side_mask(Pz, ids=("conductor",)); b = R.side_mask(Pb, ids=("conductor",))
                tas = np.asarray(S.shift(S.bell_tassel(seed, Pz["bell_pull"], "cut-paper"), Pz["dx"]), np.float32)[..., 3] / 255
                mask = np.maximum(a, tas); px = int((np.abs(a - b) > 0.3).sum())
                status = "visible" if px > 10 and Pz["bell_pull"] > 0 else "partial"
                why = "conductor mask change 5.80 -> 6.00: %d px; bell_pull %.2f; tassel drawn" % (px, Pz["bell_pull"])
            else:
                Pb = R.pose(seed, 5.80 + 1e-6)
                a = R.plan_mask(Pz, ids=("conductor",)); b = R.plan_mask(Pb, ids=("conductor",))
                mask = a; px = int((np.abs(a - b) > 0.3).sum())
                status = "partial" if (a > 0.3).sum() > 20 else "lost"
                why = "conductor present in plan (%d px), change 5.80 -> 6.00 %d px; the bell cord pull is vertical and has no plan form" % (int((a > 0.3).sum()), px)
        res[aid] = dict(status=status, px=px, t=round(t, 4), why=why)
        tiles.append((aid, status, img, mask))
    return res, tiles


def mask_sheet(cond, seed, tiles, out):
    tw, th = 320, 180; cols = 5; rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * tw, rows * (th + 22)), PAPER_TOK); d = ImageDraw.Draw(sheet); f = font(13)
    for i, (aid, st, img, mask) in enumerate(tiles):
        a = np.asarray(img, np.float32) * 0.55 + 0.45 * 238
        m = np.clip(mask, 0, 1)[..., None]
        a = a * (1 - 0.8 * m) + np.array((178, 40, 30), np.float32) * 0.8 * m
        tile = Image.fromarray(a.clip(0, 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        x, y = (i % cols) * tw, (i // cols) * (th + 22)
        sheet.paste(tile, (x, y + 22))
        d.rectangle([x, y, x + tw - 1, y + 21], fill=INK_TOK)
        d.text((x + 6, y + 3), "%s  %s" % (aid, st), fill=PAPER_TOK, font=f)
    sheet.save(out, quality=86)


@functools.lru_cache(None)
def font(sz):
    try:
        return ImageFont.truetype(str(FONT), sz)
    except Exception:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", sz)


# ================================================================== (3b) outline IoU between treatments
def puppet_alpha(Pz, fill):
    lay = Image.new("RGBA", (R.W, R.H), (0, 0, 0, 0))
    for g in ("window", "platform", "street"):
        lay = R.draw_side(lay, Pz, fill, group=g, halo=False)
    return np.asarray(lay)[..., 3] > 127


def iou(a, b):
    u = np.logical_or(a, b).sum()
    return 1.0 if u == 0 else float(np.logical_and(a, b).sum() / u)


def outline_iou():
    frames = sorted(set(list(range(0, NF, 8)) + [int(round(ANCHOR_T[k] * FPS)) for k in ANCHOR_T] + [29, 132]))
    rows = []
    for s in SEEDS:
        for f in frames:
            Pz = R.pose(s, f / FPS)
            rows.append(dict(seed=s, f=f, iou=iou(puppet_alpha(Pz, F.carve_fill(Pz)), puppet_alpha(Pz, F.photo_fill(Pz)))))
    st = {}
    for nm, fn in (("backdrop_key_blocks", lambda s, tr: F.backdrop_outline(s, tr)),
                   ("crowd", lambda s, tr: S.crowd(s, tr)), ("bus_shadow", lambda s, tr: S.bus_shadow(s, 0.0)),
                   ("bus_body", lambda s, tr: S.bus_body(s, tr)), ("bus_front", lambda s, tr: S.bus_front(s, tr)),
                   ("bell_tassel", lambda s, tr: S.bell_tassel(s, 0.6, tr)),
                   ("wheel_front", lambda s, tr: S.wheel(s, "front", 37.0, tr)[0]), ("wheel_rear", lambda s, tr: S.wheel(s, "rear", 37.0, tr)[0])):
        vals = []
        for s in SEEDS:
            a, b = fn(s, "cut-paper"), fn(s, "photographic-plate")
            a = a if isinstance(a, np.ndarray) else np.asarray(a)[..., 3] > 127
            b = b if isinstance(b, np.ndarray) else np.asarray(b)[..., 3] > 127
            vals.append(round(iou(a, b), 5))
        st[nm] = vals
    v = [r["iou"] for r in rows]
    smin = min(min(x) for x in st.values())
    assert min(v) == 1.0 and smin == 1.0, ("outline leak between treatments", min(v), st)
    return dict(puppets=dict(frames_checked=len(rows), min=min(v), all_equal_1=all(x == 1.0 for x in v),
                             method="rig.draw_side on a transparent layer with the film's cut-paper fill (ink + carved lines) vs its photographic fill (Rol 1919 swatches); alpha>127; IoU per frame, both seeds",
                             worst=sorted(rows, key=lambda r: r["iou"])[:3]),
                stage_layers_iou_seed417_418=st, stage_min=smin, asserted=True,
                note="Asserted 1.0 for puppets and every stage layer (backdrop key blocks as laid, crowd, bus shadow, bus body, bus front, bell tassel, both wheels): Δ treatment changes fill only.")


# ================================================================== (3c) protected-mask identity between seeds
def protected_identity():
    side_max = plan_max = 0.0; unprot = []
    for f in range(NF):
        t = f / FPS; a, b = R.pose(SEEDS[0], t), R.pose(SEEDS[1], t)
        side_max = max(side_max, float(np.abs(R.side_mask(a, ids=R.PROTECTED) - R.side_mask(b, ids=R.PROTECTED)).max()))
        plan_max = max(plan_max, float(np.abs(R.plan_mask(a, ids=R.PROTECTED) - R.plan_mask(b, ids=R.PROTECTED)).max()))
        if f in (29, 132):
            ua = R.side_mask(a) > 0.3; ub = R.side_mask(b) > 0.3
            unprot.append(dict(f=f, all_puppet_mask_xor_px=int(np.logical_xor(ua, ub).sum())))
    return dict(frames=NF, side_protected_max_abs_diff=side_max, plan_protected_max_abs_diff=plan_max,
                identical=side_max == 0.0 and plan_max == 0.0, protected=list(R.PROTECTED),
                seed_differences=dict(runner_count={str(s): len(R.runners_spec(s)) for s in SEEDS},
                                      vacate={str(s): R.vacate_choice(s) for s in SEEDS}, all_puppet_xor=unprot,
                                      note="Both seeds happen to vacate seat A; the vacate draw is still seeded (rng(seed,'vacate'))."))


# ================================================================== (3d) replay
FILES_READ = set()


def _track_reads():
    o_open, o_img = builtins.open, Image.open
    def op(f, *a, **k):
        if isinstance(f, (str, Path)):
            FILES_READ.add(str(Path(f).resolve()))
        return o_open(f, *a, **k)
    def im(f, *a, **k):
        if isinstance(f, (str, Path)):
            FILES_READ.add(str(Path(f).resolve()))
        return o_img(f, *a, **k)
    builtins.open = op; Image.open = im
    o_rb, o_rt = Path.read_bytes, Path.read_text
    Path.read_bytes = lambda self: (FILES_READ.add(str(self.resolve())), o_rb(self))[1]
    Path.read_text = lambda self, *a, **k: (FILES_READ.add(str(self.resolve())), o_rt(self, *a, **k))[1]


def replay_main(out):
    hashes = {}
    for c in CONDS:
        for s in SEEDS:
            for f in REPLAY_FRAMES:
                hashes["%s/%04d/f%03d" % (c, s, f)] = frame_hash(render(c, s, f / FPS))
    reads = sorted(p for p in FILES_READ if p.startswith(str(ROOT)) and not p.endswith(".py") and "__pycache__" not in p)
    Path(out).write_text(json.dumps(dict(hashes=hashes, files_read=reads), indent=1))


def replay():
    first = {}
    for c in CONDS:
        for s in SEEDS:
            for f in REPLAY_FRAMES:
                im = render(c, s, f / FPS); first["%s/%04d/f%03d" % (c, s, f)] = frame_hash(im)
                im.save(MEDIA / "replay" / ("%s_%04d_f%03d.png" % (c, s, f)))
    out = MEDIA / "replay" / "fresh-process.json"
    subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--replay", str(out)], check=True)
    fresh = json.loads(out.read_text())
    rows = {k: dict(in_process=v, fresh_process=fresh["hashes"][k], identical=v == fresh["hashes"][k]) for k, v in first.items()}
    return dict(frames=list(REPLAY_FRAMES), method="sha1 of RGB bytes; second render in a fresh python -I process",
                all_identical=all(r["identical"] for r in rows.values()), samples=rows), fresh["files_read"]


# ================================================================== (3e) audio
def audio_hashes():
    import kit
    film = F.film
    mix = kit.Mix(film.seconds, seed=film.seed)
    if film._sound:
        film._sound(mix)
    pcm = mix.master(); rate = kit.RATE; arr_ = np.asarray(pcm).reshape(-1, 2)
    rows = {}
    wins = dict(("%s/%04d" % k, v) for k, v in CLIP_AT.items()); wins["grid/S9"] = 50.0
    for k, at in wins.items():
        a0 = int(round(at * rate)); a1 = a0 + int(round(7.0 * rate))
        rows[k] = dict(film_window=[at, at + 7.0], samples=[a0, a1], pcm_sha1=sha1b(arr_[a0:a1].tobytes()))
    hs = {r["pcm_sha1"] for r in rows.values()}
    # stems (before mastering): the one clip track the script lays under every window
    stem = np.asarray(F.clip_audio())
    out = dict(status="measured", rate=rate, clips=rows, identical=len(hs) == 1, windows=len(rows),
               stem_sha1=sha1b(np.ascontiguousarray(stem).tobytes()),
               method="kit.Mix rebuilt in-process from the film module's sound function, mastered exactly as Film.render does, s16 PCM sliced per 7.0 s window "
                      "(6 clip windows + the S9 grid window), hashed BEFORE the AAC encode")
    mp4 = ROOT / "assets/films" / (SLUG + ".mp4")
    if mp4.exists():
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(mp4), "-f", "s16le", "-ac", "2", "-ar", str(rate), "-"],
                             check=True, capture_output=True).stdout
        dec = np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float64)
        ref = None; snr = {}
        for k, r_ in rows.items():
            a0, a1 = r_["samples"]
            seg = dec[a0:a1]
            if ref is None:
                ref = seg
            n = min(len(ref), len(seg))
            e = seg[:n] - ref[:n]
            snr[k] = None if k == next(iter(rows)) else round(10 * math.log10((ref[:n] ** 2).mean() / max((e ** 2).mean(), 1e-9)), 1)
        vals = [v for v in snr.values() if v is not None]
        out["aac_decoded"] = dict(file=rel(mp4), file_sha1=sha1f(mp4), snr_db_vs_first_window=snr, min_snr_db=min(vals),
                                  note="the mp4's AAC 96 kb/s track is lossy and its 1024-sample frames do not align with the 7.0 s windows, "
                                       "so decoded windows are NOT bit-identical; identity is claimed for the PCM before encoding only")
    return out


# ================================================================== (4) counterexample: RNG-coupled overhead projector
def project_honest(seed, t):
    """The real overhead projector: plan forms from the side pose's world (x, z); draws no RNG."""
    Pz = R.pose(seed, t)
    return render("d-camera", seed, t), Pz


def project_drift(seed, t):
    """REJECTED CANDIDATE, built on purpose. A 'helpful' overhead projector that re-lays out the street
    crowd for the plan from ONE shared RNG stream (np.random.RandomState(seed)) and adds plan jitter to
    every puppet. Only `camera` was edited, yet the runner count and positions change."""
    Pz = R.pose(seed, t)
    shared = np.random.RandomState(seed)                      # shared stream: the P4 violation
    _ = shared.rand(64)                                        # e.g. gouge jitter for the plan backdrop
    n = int(shared.randint(4, 10))                             # crowd re-laid out for 'readability from above'
    street = [q for q in Pz["puppets"] if q["group"] == "street"]
    rest = [dict(q) for q in Pz["puppets"] if q["group"] != "street"]
    for q in rest:                                             # plan jitter, protected puppets included
        q["x"] = q["x"] + float(shared.normal(0, 2.5))
    new_street = []
    for i in range(n):
        q = dict(street[i % len(street)]); q["id"] = "runner%d" % i
        q["x"] = float(shared.uniform(40, 700)); q["z"] = float(shared.uniform(*S.WORLD["runner_z"]))
        new_street.append(q)
    P2 = dict(Pz); P2["puppets"] = rest + new_street
    img = F.draw_cell(S.plan_stage(seed, t), P2)
    return R.draw_plan(img, P2, R.INK).convert("RGB"), P2


class RngProbe:
    """Records every numpy RandomState constructed outside the keyed rng(seed, element_id) helpers of rig.py
    / stage.py while a projector runs (P4: renderer/projector draw nothing from a shared stream)."""
    def __enter__(self):
        self.violations = []; self.keyed = 0
        self._orig = np.random.RandomState; probe = self; orig = self._orig
        class Tracked(orig):
            def __init__(s, *a, **k):
                fr = sys._getframe(1)
                if fr.f_code.co_name == "rng" and Path(fr.f_code.co_filename).name in ("rig.py", "stage.py"):
                    probe.keyed += 1
                else:
                    probe.violations.append("%s:%d %s()" % (Path(fr.f_code.co_filename).name, fr.f_lineno, fr.f_code.co_name))
                super().__init__(*a, **k)
        np.random.RandomState = Tracked
        self._glob = {n: getattr(np.random, n) for n in ("rand", "randn", "randint", "uniform", "normal", "random", "choice", "shuffle", "permutation")}
        for n, fn in self._glob.items():
            setattr(np.random, n, (lambda fn_, n_: (lambda *a, **k: (probe.violations.append("np.random.%s (global stream)" % n_), fn_(*a, **k))[1]))(fn, n))
        return self
    def __exit__(self, *a):
        np.random.RandomState = self._orig
        for n, fn in self._glob.items():
            setattr(np.random, n, fn)


def check_projector(proj, label):
    frames = [0, 24, 29, 32, 60, 100, 132]
    checks = dict(P4_no_shared_rng=True, world_ids_preserved=True, world_xz_preserved=True, runner_count_equals_side=True,
                  C4_protected_plan_masks_identical_across_seeds=True)
    ev = []; viol = []
    for f in frames:
        t = f / FPS; pm = {}
        for s in SEEDS:
            side = R.pose(s, t)
            with RngProbe() as pr:
                img, drawn = proj(s, t)
            if pr.violations:
                checks["P4_no_shared_rng"] = False; viol += pr.violations[:3]
            ws = {q["id"]: (q["x"], q["z"]) for q in side["puppets"] if q.get("plan_visible", True)}
            wd = {q["id"]: (q["x"], q["z"]) for q in drawn["puppets"] if q.get("plan_visible", True)}
            if set(ws) != set(wd):
                checks["world_ids_preserved"] = False
            if any(abs(ws[k][0] - wd[k][0]) > 1e-6 or abs(ws[k][1] - wd[k][1]) > 1e-6 for k in set(ws) & set(wd)):
                checks["world_xz_preserved"] = False
            ns = sum(1 for q in side["puppets"] if q["group"] == "street"); nd = sum(1 for q in drawn["puppets"] if q["group"] == "street")
            if ns != nd:
                checks["runner_count_equals_side"] = False
            pm[s] = R.plan_mask(drawn, ids=R.PROTECTED)
            ev.append(dict(f=f, seed=s, runners_side=ns, runners_projected=nd, frame_sha1=frame_hash(img)))
        if float(np.abs(pm[SEEDS[0]] - pm[SEEDS[1]]).max()) > 0:
            checks["C4_protected_plan_masks_identical_across_seeds"] = False
    return dict(projector=label, passed=all(checks.values()), checks=checks, rng_violations=sorted(set(viol)), per_frame=ev)


def counterexample():
    good = check_projector(project_honest, "film render, camera=overhead (accepted)")
    bad = check_projector(project_drift, "project_drift: RNG-coupled overhead projector (built on purpose)")
    # strip: seed 0417 at t 1.00 / 1.20 / 1.333 - side baseline, accepted overhead, rejected overhead
    ts = (1.0, 1.2, 4 / 3); tw, th = 400, 225
    strip = Image.new("RGB", (3 * tw + 150, 3 * (th + 24) + 34), PAPER_TOK); d = ImageDraw.Draw(strip); f = font(13)
    d.text((8, 8), "REJECTED DRIFT  ·  seed 0417  ·  only `camera` edited, yet the runner count changed  ·  quarantined", fill=INK_TOK, font=font(15))
    qd = MEDIA / "quarantine"; qd.mkdir(parents=True, exist_ok=True)
    for j, t in enumerate(ts):
        side = render("baseline", 417, t + 1e-6); hon, Ph = project_honest(417, t + 1e-6); drf, Pd = project_drift(417, t + 1e-6)
        drf.save(qd / ("drift_0417_t%.3f.png" % t))
        for i, (lab, im, P_) in enumerate((("baseline side", side, R.pose(417, t + 1e-6)), ("overhead (accepted)", hon, Ph), ("overhead DRIFT (rejected)", drf, Pd))):
            x = 150 + j * tw; y = 34 + i * (th + 24)
            strip.paste(im.resize((tw, th), Image.LANCZOS), (x, y + 24))
            n = sum(1 for q in P_["puppets"] if q["group"] == "street")
            d.rectangle([x, y, x + tw - 2, y + 22], fill=INK_TOK if i < 2 else (120, 34, 28))
            d.text((x + 6, y + 3), "t %.2f  runners %d" % (t, n), fill=PAPER_TOK, font=f)
            if j == 0:
                d.text((6, y + 24 + th // 2), lab, fill=INK_TOK, font=f)
    strip.save(MEDIA / "rejected-drift-strip.jpg", quality=88); strip.save(VDIR / "rejected-drift-strip.jpg", quality=88)
    n_side = len(R.runners_spec(417)); _, Pd = project_drift(417, 1.2); n_d = sum(1 for q in Pd["puppets"] if q["group"] == "street")
    doc = dict(candidate="Δ camera = overhead, projector variant 'project_drift' (verify/coverage.py)",
               defect="the projector lays out runners from np.random.RandomState(seed) (one shared stream) and jitters every plan form, so the camera edit changes what the seed decides",
               observed=dict(seed=417, runners_side=n_side, runners_overhead_drift=n_d,
                             runners_overhead_accepted=sum(1 for q in R.pose(417, 1.2)["puppets"] if q["group"] == "street")),
               harness_accepted=good, harness_rejected=bad,
               broken=[k for k, v in bad["checks"].items() if not v],
               verdict="REJECTED and quarantined (I8); the accepted overhead stays the film render (camera=overhead)",
               quarantine=rel(qd), strip=[rel(MEDIA / "rejected-drift-strip.jpg"), rel(VDIR / "rejected-drift-strip.jpg")])
    (VDIR / "rejected-drift.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    return doc


# ================================================================== (5) measurement + comparison sheet
def srgb_to_lab(rgb):
    c = np.asarray(rgb, np.float64) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def de76(a, b):
    return float(np.linalg.norm(srgb_to_lab(a) - srgb_to_lab(b)))


def measure(im):
    a = np.asarray(im.convert("RGB"), np.float32).reshape(-1, 3)
    L = a @ np.array([0.299, 0.587, 0.114], np.float32)
    p = np.percentile(L, [2, 25, 50, 75, 98])
    paper = np.median(a[L >= np.percentile(L, 90)], 0); ink = np.median(a[L <= np.percentile(L, 10)], 0)
    return dict(p2_25_50_75_98=[round(float(v)) for v in p], mid_70_170=round(float(((L >= 70) & (L <= 170)).mean()), 3),
                chroma=round(float((a.max(1) - a.min(1)).mean()), 1),
                paper_rgb=[int(v) for v in paper], ink_rgb=[int(v) for v in ink],
                dE76_paper_to_eee6d6=round(de76(paper, PAPER_TOK), 1), dE76_ink_to_22211f=round(de76(ink, INK_TOK), 1),
                method="L = Rec.601 luma; paper = median RGB of the top-decile L pixels; ink = median of the bottom decile; ΔE76 in CIELAB (D65)")


def bar5(m):
    p = m["p2_25_50_75_98"]
    return dict(p2_ge_15=p[0] >= 15, p98_222_242=222 <= p[4] <= 242, mid_ge_12pct=m["mid_70_170"] >= 0.12, chroma_le_20=m["chroma"] <= 20,
                paper_dE_le_10=m["dE76_paper_to_eee6d6"] <= 10, ink_dE_le_10=m["dE76_ink_to_22211f"] <= 10)


def comparison_sheet():
    cw, ch = 480, 270; t = 1.20 + 1e-6
    ref = Image.open(REF).convert("RGB")
    base = render("baseline", 417, t)
    film_k = int(round(5.2 * FPS))
    film_frame = F.film.frame(film_k).convert("RGB")          # the delivered film's frame 0:05.2 (tag included)
    film_frame.save(MEDIA / "film_0005.2.png")
    mb, mr = measure(film_frame), measure(ref)
    H2 = 360; bw = int(960 * H2 / 540); rw = int(ref.size[0] * H2 / ref.size[1])
    Wt = max(2 * cw + 40, bw + rw + 60)
    sheet = Image.new("RGB", (Wt, 50 + 3 * (ch + 30) + 30 + H2 + 150), PAPER_TOK); d = ImageDraw.Draw(sheet)
    d.text((20, 14), "Exercises in Style · six samples at clip t = 1.20 (A3 shove) · equal size · rows: condition · columns: seed", fill=INK_TOK, font=font(15))
    labels = {"baseline": "baseline · street-side · cut-paper", "d-treatment": "Δ treatment = photographic-plate", "d-camera": "Δ camera = overhead"}
    x0 = (Wt - 2 * cw - 20) // 2; hashes = {}
    for i, c in enumerate(CONDS):
        for j, s in enumerate(SEEDS):
            im = base if (c, s) == ("baseline", 417) else render(c, s, t)
            im.save(MEDIA / ("sample_%s_%04d_t1.20.png" % (c, s))); hashes["%s/%04d" % (c, s)] = frame_hash(im)
            x = x0 + j * (cw + 20); y = 50 + i * (ch + 30)
            sheet.paste(im.resize((cw, ch), Image.LANCZOS), (x, y + 24))
            lab = "%s · seed %04d" % (labels[c], s)
            d.rectangle([x, y, x + 12 + int(d.textlength(lab, font=font(12))), y + 21], fill=INK_TOK)
            d.text((x + 6, y + 3), lab, fill=PAPER_TOK, font=font(12))
    y = 50 + 3 * (ch + 30) + 20
    d.text((20, y - 4), "film frame 0:05.2 (frame %d of the film's own frame function, = clip t %.3f) beside martinoCharcoal.webp at equal height (reference consulted, never copied)" % (film_k, film_k / FPS - 4.0), fill=INK_TOK, font=font(12))
    y += 18; xb = (Wt - bw - rw - 30) // 2
    sheet.paste(film_frame.resize((bw, H2), Image.LANCZOS), (xb, y)); sheet.paste(ref.resize((rw, H2), Image.LANCZOS), (xb + bw + 30, y))
    for k, (m, x) in enumerate(((mb, xb), (mr, xb + bw + 30))):
        p = m["p2_25_50_75_98"]
        lines = ["%s" % ("FILM 0:05.2 baseline seed 0417" if k == 0 else "REFERENCE martinoCharcoal"),
                 "p2/25/50/75/98  %d/%d/%d/%d/%d" % tuple(p), "mid L70-170  %.1f %%   chroma %.1f" % (100 * m["mid_70_170"], m["chroma"]),
                 "paper #%02x%02x%02x  ΔE %.1f to #eee6d6" % (tuple(m["paper_rgb"]) + (m["dE76_paper_to_eee6d6"],)),
                 "ink   #%02x%02x%02x  ΔE %.1f to #22211f" % (tuple(m["ink_rgb"]) + (m["dE76_ink_to_22211f"],))]
        for li, s_ in enumerate(lines):
            d.text((x, y + H2 + 10 + 20 * li), s_, fill=INK_TOK, font=font(13))
    sheet.save(VDIR / "comparison-sheet.jpg", quality=88); sheet.save(MEDIA / "comparison-sheet.jpg", quality=88)
    meas = {}
    for c in CONDS:
        for s in SEEDS:
            meas["%s/%04d" % (c, s)] = measure(Image.open(MEDIA / ("sample_%s_%04d_t1.20.png" % (c, s))))
    return dict(baseline=mb, baseline_frame="film frame %d (0:05.2), %s" % (film_k, rel(MEDIA / "film_0005.2.png")), reference=mr, bar5_baseline=bar5(mb), bar5_pass=all(bar5(mb).values()), all_samples=meas, frame_sha1=hashes)


# ================================================================== (2) render attempts
def generator_rev():
    parts = {rel(p): sha1f(p) for p in (SCRIPT, WS / "stage/stage.py", WS / "rig/rig.py")}
    return sha1b("".join(parts[k] for k in sorted(parts)).encode()), parts


def render_attempts(files_read, replay_doc, man):
    rev, parts = generator_rev()
    exp = WS / "rig/exposure.json"; anc = WS / "rig/anchors.json"
    plates = {rel(p): sha1f(p) for p in files_read if Path(p).exists() and not str(p).endswith((".json",)) }
    plates_json = {rel(p): sha1f(p) for p in files_read if Path(p).exists() and str(p).endswith(".json")}
    rows = []
    mid = {"baseline": man["baseline"]["sha1"], "d-camera": man["deltas"][0]["sha1"], "d-treatment": man["deltas"][1]["sha1"]}
    for c in CONDS:
        for s in SEEDS:
            at = CLIP_AT[(c, s)]
            rows.append(dict(id="%s/%04d" % (c, s), shot=SHOT[(c, s)], engine="kit.py procedural animatic", generator_rev=rev, manifest_sha1=mid[c], seed=s,
                             settings=dict(fps=FPS, size=[960, 540], duration=7.0, frames=NF, drawings="on twos (12/s)",
                                           projection="plan (film render: stage.plan_stage + roof-light cell + rig.draw_plan)" if c == "d-camera" else "side elevation (film render)",
                                           treatment="photographic-plate" if c == "d-treatment" else "cut-paper",
                                           puppet_fill="film photo_fill: Rol 1919 cloth swatches" if c == "d-treatment" else ("INK + carved lines" if c == "baseline" else "INK")),
                             conditioning=dict(exposure_sheet_sha1=sha1f(exp), anchors_sha1=sha1f(anc), plates_sha1=plates),
                             output=dict(film_seconds=[at, at + 7.0], film_frames=[int(round(at * FPS)), int(round(at * FPS)) + NF - 1],
                                         defining_beat_film_t=round(at + 1.2, 2),
                                         replay_frame_sha1={str(f): replay_doc["samples"]["%s/%04d/f%03d" % (c, s, f)]["in_process"] for f in REPLAY_FRAMES}),
                             observation="see coverage.json samples['%s/%04d']" % (c, s)))
    grid_at = 50.0
    return dict(schema="RenderAttempt = {engine, generator_rev, seed, settings, conditioning, output, observation}",
                generator_rev=dict(sha1=rev, of=parts, rule="sha1 of the concatenated sha1s of the film script, stage.py and rig.py (sorted by path); a change starts a new experiment (P5)",
                                   caveat="the film script is hashed as it stands when coverage.py runs; if the editor rewrites it, rerun coverage.py to repin"),
                stage_rev=S.GENERATOR_REV, rig_rev=R.RIG_REV, seeds=list(SEEDS),
                conditioning_files_read=dict(plates=plates, json=plates_json, method="every file opened by a fresh-process render of all six samples (open/Image.open/Path.read_* traced)"),
                attempts=rows, grid=dict(shot="S9", film_seconds=[grid_at, grid_at + 8.0], cell=[300, 169]))


# ================================================================== evidence
def evidence(files_read):
    """Foraged = exactly the rows of films/credits/<slug>.json (what appears in the film), joined to U1's
    plates.json ledger for local paths, sha1s and the licence read. The dropped 1933 plate is an absence."""
    credits = json.loads((ROOT / "films/credits" / (SLUG + ".json")).read_text())
    ledger = {r["id"]: r for r in json.loads((WS / "plates/plates.json").read_text())["items"]}
    key = {"1-6-16": "rol1916", "Mars 1919": "vilgrain1919", "14-3-19": "wilson1919", "WWS City": "engine", "Bell-ring": "bell", "Sunday in": "street"}
    rows = []
    for c in credits:
        if c.get("synthesized"):
            continue                                 # declared synthetic sounds: no source to join
        lid = next(v for k, v in key.items() if c["title"].startswith(k))
        L = ledger.get(lid, {})
        lp = ROOT / L["local_path"] if L.get("local_path") else None
        fam = [str((ROOT / it["local_path"]).resolve()) for k_, it in ledger.items() if it.get("local_path") and
               (k_ == lid or k_.startswith(lid + ".") or it.get("derived_from") == lid)]
        fam += [str(Path(rel_).resolve()) for rel_ in ((S.ROL,) if lid == "rol1916" else ())]
        used = sorted(rel(p) for p in files_read if p in fam or (lid == "rol1916" and ("/test-shot/plates/" in p)))
        rows.append(dict(c, id="F-" + lid, local_path=L.get("local_path"), local_sha1=sha1f(lp) if lp and lp.exists() else None,
                         read_by_film_render=(used or False) if lid not in ("engine", "bell", "street") else "audio: laid by the film's sound() (see audio_pcm)",
                         verified=L.get("verified_date_or_place", "")))
    derived = sorted(rel(p) for p in files_read if "/films/sources/" in p and Path(p).exists())
    bourse_read = any("bourse1933" in p for p in files_read)
    assert not bourse_read, "the dropped 1933 plate was read by a film render"
    return dict(foraged=rows, files_read_by_film_renders=derived, bourse1933_read_by_any_render=bourse_read,
                handmade=[dict(item="carved facade/arcade/pavement blocks, platform, board, plan stage, roof-light cell, puppets and their carved lines, cards",
                               where="stage/stage.py, rig/rig.py, films/%s.py" % SLUG),
                          dict(item="coverage harness, per-anchor masks, outline IoU, replay, RNG probe", where=rel(Path(__file__))),
                          dict(item="counterexample RNG-coupled overhead projector (rejected)", where=rel(Path(__file__)) + " project_drift; frames in " + rel(MEDIA / "quarantine")),
                          dict(item="comparison sheet, mask sheets, rejected-drift strip", where=rel(MEDIA))],
                absences=[dict(id="F2-bourse1933", title="Greve des autobus - Place de la Bourse, le public attendant la reprise (Peyriras, 1933)",
                               status="dropped: Commons tags it PD France only, with no US rationale; a 1933 photograph is probably under restored US copyright, so not verifiably PD",
                               check="no film render reads films/sources/%s/commons/bourse1933.jpg (traced: %s)" % (SLUG, not bourse_read)),
                          "nothing usable came from the Moving Image Archive cache (U1 logged the 28 sound-clip matches as narrated, scored or hiss)",
                          "no openly licensed pre-1930 motorbus engine or conductor's bell on Commons: a 1991 diesel and a bicycle bell stand in (declared)",
                          "U4 foraged nothing new"])



# ================================================================== puppet print checks (repair round 2)
def puppet_print_checks():
    """Critic round 2: (a) no cream knife line closes on itself in film 0:05.0-0:05.8 (clip t 1.00-1.80,
    baseline 0417); (b) at 0:05.2 no cream rim brighter than the surrounding paper where street puppets
    stand on cream ground; (c) bus framing measured with and without the rear platform."""
    F.CARVE_LOG.clear()
    M = F.manifest("baseline")
    for f in range(24, 44):
        F.render(M, 417, f / FPS)
    ratios = [L / N for _, _, L, N in F.CARVE_LOG]
    open_ok = bool(ratios) and max(ratios) < 0.5
    t = 1.20; P = R.pose(417, t); dx = P["dx"]
    img = np.asarray(F.render(M, 417, t).convert("L"), np.float32)
    ref = np.asarray(F._cut_ref(417, t, dx).convert("L"), np.float32)
    dark = F._darkness(F._cut_ref(417, t, dx))
    m = R.side_mask(P, group="street") > 0.35
    ring = (cv2.dilate(m.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0) & ~(cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    cream = ring & (dark < 0.02) & (ref > 200)
    diff = img[cream] - ref[cream]
    rim_ok = bool(cream.sum() > 50 and float(np.percentile(diff, 99)) <= 2.0)
    ba = np.asarray(S.bus_body(417, "cut-paper"), np.float32)[..., 3] > 128
    xs = np.where(ba.any(0))[0]; ys = np.where(ba.any(1))[0]
    g = R.geo()
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    return dict(
        open_strokes=dict(check="every cream gouge line in the puppets is an open run of one part outline (run/contour < 0.5)",
                          frames="film 0:05.0-0:05.8 (clip frames 24-43, baseline 0417)", strokes=len(ratios),
                          max_run_fraction=round(max(ratios), 3) if ratios else None, passed=open_ok),
        no_rim_on_cream=dict(check="at 0:05.2, ring pixels 1-3 px outside street puppets on cream ground are not brighter than the paper beneath",
                             ring_pixels_on_cream=int(cream.sum()), p99_brightening=round(float(np.percentile(diff, 99)), 2),
                             mean_brightening=round(float(diff.mean()), 2), passed=rim_ok),
        bus_framing=dict(frame_width=960, bus_x0=x0, bus_x1=x1, platform_x0=round(float(g["plat0"]), 1),
                         span_with_platform_pct=round(100 * (x1 - x0) / 960, 1),
                         span_without_platform_pct=round(100 * (float(g["plat0"]) - x0) / 960, 1),
                         bus_y_pct=[round(100 * ys.min() / 540, 1), round(100 * (ys.max() + 1) / 540, 1)],
                         target="bus long side 55-65 % of frame width, y about 32-75 %"))

# ================================================================== main
def main():
    t0 = time.time()
    for d in (MEDIA, MEDIA / "masks", MEDIA / "replay"):
        d.mkdir(parents=True, exist_ok=True)
    man = manifests(); (VDIR / "manifests.json").write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print("manifests", man["baseline"]["sha1"], [d["diff_keys"] for d in man["deltas"]], flush=True)
    rep, files_read = replay(); print("replay", rep["all_identical"], round(time.time() - t0), flush=True)
    samples = {}
    for c in CONDS:
        for s in SEEDS:
            cv, tiles = cover(c, s); samples["%s/%04d" % (c, s)] = cv
            mask_sheet(c, s, tiles, MEDIA / "masks" / ("anchors_%s_%04d.jpg" % (c, s)))
    print("cover", round(time.time() - t0), flush=True)
    io = outline_iou(); print("iou", io["puppets"]["min"], io["stage_layers_iou_seed417_418"], flush=True)
    pid = protected_identity(); print("protected", pid["identical"], flush=True)
    ce = counterexample(); print("counterexample", ce["harness_accepted"]["passed"], ce["harness_rejected"]["passed"], ce["broken"], flush=True)
    cs = comparison_sheet(); print("sheet", cs["baseline"], cs["bar5_baseline"], flush=True)
    au = audio_hashes()
    ra = render_attempts(files_read, rep, man); (VDIR / "render-attempts.json").write_text(json.dumps(ra, indent=1, ensure_ascii=False))

    # intended-effect rate, n of 2 per condition
    prot_ids = [a["id"] for a in anchor_list() if a.get("protected")]
    acc = ce["harness_accepted"]["checks"]
    ie = {}
    for c in CONDS:
        per = {}
        for s in SEEDS:
            cv = samples["%s/%04d" % (c, s)]
            if c == "baseline":
                ok = all(cv[a]["status"] == "visible" for a in prot_ids) and rep["all_identical"]
                crit = "control: every protected anchor visible, replay byte-identical"
            elif c == "d-treatment":
                bc = np.asarray(Image.open(MEDIA / ("sample_baseline_%04d_t1.20.png" % s)), np.float32)
                tc = np.asarray(Image.open(MEDIA / ("sample_d-treatment_%04d_t1.20.png" % s)), np.float32)
                busm = np.asarray(S.bus_body(s, "cut-paper"), np.float32)[..., 3] > 127
                Lb = bc[busm].mean(1); Lt = tc[busm].mean(1)
                levels_b = len(np.unique((Lb // 4).astype(int))); levels_t = len(np.unique((Lt // 4).astype(int)))
                fill_changed = float(np.abs(Lb - Lt).mean()) > 8
                ok = io["puppets"]["all_equal_1"] and fill_changed and all(cv[a]["status"] == "visible" for a in prot_ids)
                crit = ("puppet outline IoU 1.0 on every checked frame; bus-region fill changed (mean |ΔL| %.1f, grey levels/4 %d -> %d); "
                        "all protected anchors visible" % (float(np.abs(Lb - Lt).mean()), levels_b, levels_t))
            else:
                Pa, Pb = R.pose(s, 14 / 12 + 1e-6), R.pose(s, 16 / 12 + 1e-6)
                ma, mb_ = R.plan_mask(Pa, ids=("man",), parts=("hat",)), R.plan_mask(Pb, ids=("man",), parts=("hat",))
                cxa = float((ma * np.arange(R.W)).sum() / ma.sum()); cxb = float((mb_ * np.arange(R.W)).sum() / mb_.sum())
                stx = R.geo()["stx"] + 3
                disp = cxb - cxa
                toward = abs(stx - cxb) < abs(stx - cxa)
                ok = acc["P4_no_shared_rng"] and acc["runner_count_equals_side"] and acc["C4_protected_plan_masks_identical_across_seeds"] \
                    and cv["A3"]["status"] == "visible" and abs(disp) >= 2 and toward
                crit = ("plan projection; shove as displacement: man's hat-disc centroid moves %.1f px from drawing 14 to 16, %s the stanchion dot; "
                        "A3 contact %s; projector passes P4/runner-count/C4" % (disp, "toward" if toward else "away from", cv["A3"]["status"]))
            per[str(s)] = dict(intended=bool(ok), criterion=crit)
        ie[c] = dict(n=sum(v["intended"] for v in per.values()), of=2, rate="%d of 2 inspected samples" % sum(v["intended"] for v in per.values()), per_seed=per)

    lost = {c: sorted({a for s in SEEDS for a, v in samples["%s/%04d" % (c, s)].items() if v["status"] == "lost"}) for c in CONDS}
    partial = {c: sorted({a for s in SEEDS for a, v in samples["%s/%04d" % (c, s)].items() if v["status"] == "partial"}) for c in CONDS}
    pred = ["A-neck", "A6w"]
    assert "A6" not in lost["d-camera"], "protected action A6 (seat taken) lost in overhead"
    doc = dict(
        film=SLUG, unit="U4 verify", run_seconds=round(time.time() - t0), generator_rev=ra["generator_rev"]["sha1"],
        manifests=dict(baseline_sha1=man["baseline"]["sha1"], deltas={d["id"]: dict(field=d["field"], diff_keys=d["diff_keys"], ok=d["assert_diff_eq_field"]) for d in man["deltas"]},
                       two_field_delta_refused=man["self_test_two_field_delta_refused"]),
        intended_effect_rate=ie,
        lost_anchor_ids=lost, partial_anchor_ids=partial,
        predicted_losses_overhead=dict(predicted=pred, observed_lost=[a for a in pred if a in lost["d-camera"]],
                                       unpredicted_losses=[a for a in lost["d-camera"] if a not in pred],
                                       unpredicted_partials=partial["d-camera"]),
        samples=samples, outline_iou=io, protected_mask_identity=pid, replay=rep, audio_pcm=au,
        counterexample=dict(file=rel(VDIR / "rejected-drift.json"), accepted_projector_passed=ce["harness_accepted"]["passed"],
                            drift_projector_passed=ce["harness_rejected"]["passed"], broken=ce["broken"], observed=ce["observed"]),
        aesthetic=cs,
        puppet_print=puppet_print_checks(),
        capability_notes=dict(
            observed=["These results describe six inspected samples (3 conditions x seeds 0417, 0418) of one engine: "
                      "'kit.py procedural animatic' = stage.py + rig.py at generator_rev %s." % ra["generator_rev"]["sha1"][:12],
                      "Seeds are repeatable in this engine: frames 0, 29, 132 of all six samples re-render byte-identically in a fresh process (%s)." % rep["all_identical"],
                      "In this engine the seed governs only unprotected elements (runner count 7 vs 8, positions, phases, idle holds, print grain); protected masks are identical across seeds on all 168 frames, side and plan (%s)." % pid["identical"],
                      "The treatment field changed fill only (puppet outline IoU min %.4f)." % io["puppets"]["min"],
                      "The camera field changed projection and lost anchors %s; partially kept %s." % (lost["d-camera"], partial["d-camera"])],
            not_claimed=["Nothing here is evidence about text-to-video or text-to-image generators in general, or about how Martino's own generator "
                         "handled seeds, fixed actions or prompt deltas; the film is a stand-in engine whose isolation of seed streams is built in by design (P4).",
                         "An intended-effect rate of n of 2 is a count over two inspected samples, not an estimate of a probability.",
                         "The counterexample shows this harness detects one class of drift (projector drawing from a shared stream); it does not prove absence of other drift classes."]),
        evidence=evidence(files_read),
        outputs=dict(manifests=rel(VDIR / "manifests.json"), render_attempts=rel(VDIR / "render-attempts.json"), rejected_drift=rel(VDIR / "rejected-drift.json"),
                     comparison_sheet=rel(VDIR / "comparison-sheet.jpg"), mask_sheets=rel(MEDIA / "masks"), replay_frames=rel(MEDIA / "replay"),
                     samples_t1_20=sorted(rel(p) for p in MEDIA.glob("sample_*.png")), quarantine=rel(MEDIA / "quarantine")))
    (VDIR / "coverage.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    print(json.dumps(dict(ie={k: v["rate"] for k, v in ie.items()}, lost=lost, partial=partial, secs=doc["run_seconds"]), indent=1))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--replay":
        _track_reads(); replay_main(sys.argv[2])
    else:
        main()
