"""Exercises in Style (Mauro Martino) - SCION controlled variation, Direction 1 'Cut-Paper Platform'.

One small bus incident (the shove on the rear platform) frozen as an exposure sheet and re-rendered
under single-field instructions: baseline, Δ treatment = photographic-plate, Δ camera = overhead,
each at seeds 0417 and 0418. Built on films/kit.py (Film, Mix); the stage is
swarm/<slug>/stage/stage.py, the puppets swarm/<slug>/rig/rig.py (both imported, not edited).

FORAGED: Agence Rol 1916 bus plate, Agence Rol 1919 crowd plates (Gallica via Commons, PD);
engine (CC BY 4.0), street (PD) and bell (CC0) recordings via Commons. HANDMADE: facade, pavement,
platform, board, puppets, plan stage, cards. SYNTHETIC (declared): kit thud at the shove, kit click
at the stanchion and on the cards.

Run from the project root:  python3 films/mauro-martino-exercises-in-style.py   [--stills t ...]
"""
import functools, hashlib, importlib.util, json, math, os, subprocess, sys
from multiprocessing import get_context
from pathlib import Path

import numpy as np, cv2
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kit
from kit import Film

SLUG = "mauro-martino-exercises-in-style"
ROOT = HERE.parent
WS = HERE / "swarm" / SLUG
SRC = HERE / "sources" / SLUG
U1 = SRC / "plates"
CACHE = Path(os.environ.get("MMES_CACHE", "/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/mmes-cache"))

# ------------------------------------------------------------------ stage + rig (one shared stage module)
def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return m

S = _load("stage", WS / "stage/stage.py")
R = _load("rig", WS / "rig/rig.py")
W, H = 960, 540
FPS = 24
CLIP = 7.0
NF = 168
PAPER = tuple(S.PALETTE["paper"]); INKC = tuple(S.PALETTE["ink"]); SHADE = tuple(S.PALETTE["shade"])
TINT = tuple(S.PALETTE["tint"]); DTINT = tuple(S.PALETTE["dtint"])

# ------------------------------------------------------------------ manifests (one changed field per delta)
BASE = R.baseline_manifest()
BASE_SHA1 = R.manifest_sha1(BASE)
DELTAS = {"baseline": {}, "d-treatment": {"treatment": "photographic-plate"}, "d-camera": {"camera": "overhead"}}
LABEL = {"baseline": "baseline", "d-treatment": "Δ treatment", "d-camera": "Δ camera"}


def manifest(cond):
    M = dict(BASE); M.update(DELTAS[cond])
    diff = {k for k in set(M) | set(BASE) if M.get(k) != BASE.get(k)}
    assert len(diff) == (0 if cond == "baseline" else 1), (cond, diff)   # each delta changes exactly one field
    return M


# ------------------------------------------------------------------ waiting crowd: Agence Rol 1919 GrabCut cutouts
# U1 replaced the 1933 Bourse plate (PD basis not verifiable in the US); this re-implements stage._crowd
# with U1's accepted Vilgrain 1919 cutouts A-H at the same two placements (right of platform, left of cab).
CROWD_RIGHT = ["C_man_overcoat", "A_woman_shawl", "G_man_bowler_right", "F_woman_basket", "E_woman_white", "H_man_far"]
CROWD_LEFT = ["D_man_back", "B_woman_walking"]


@functools.lru_cache(None)
def _cut(name):
    a = np.asarray(Image.open(U1 / "crowd" / f"{name}_rgba.png").convert("RGBA")).astype(np.float32)
    return a[..., 0], a[..., 3] / 255.0


@functools.lru_cache(None)
def _crowd(seed, treatment):
    SS = S.SS; Hd, Wd = H * SS, W * SS
    alpha = np.zeros((Hd, Wd), np.float32); fill = np.full((Hd, Wd), 128, np.float32)
    r = S.rng(seed, "crowd")
    feet_y = S.side_ground_y(S.WORLD["crowd_z"])
    plan = []
    x = 728 + r.uniform(-4, 10)
    for nm in CROWD_RIGHT:
        plan.append((nm, x)); x += r.uniform(30, 44)
    x = 6 + r.uniform(-6, 6)
    for nm in CROWD_LEFT:
        plan.append((nm, x)); x += r.uniform(40, 52)
    for nm, x0 in plan:
        g, a = _cut(nm)
        ys = np.nonzero(a.sum(1) > 0)[0]
        hh = ys.max() - ys.min() + 1
        target = r.uniform(100, 114) * (0.86 if nm.startswith(("E_", "H_", "F_")) else 1.0)
        sc = target / hh * SS
        tw, th = max(1, int(a.shape[1] * sc)), max(1, int(a.shape[0] * sc))
        cm = cv2.resize(a, (tw, th), interpolation=cv2.INTER_AREA)
        cg = cv2.resize(g, (tw, th), interpolation=cv2.INTER_AREA)
        X = int(x0 * SS); Y = int(feet_y * SS - ys.max() * sc)
        x0_, y0_ = max(0, X), max(0, Y); x1_, y1_ = min(Wd, X + tw), min(Hd, Y + th)
        if x1_ <= x0_ or y1_ <= y0_:
            continue
        aa = cm[y0_ - Y:y1_ - Y, x0_ - X:x1_ - X]
        fill[y0_:y1_, x0_:x1_] = fill[y0_:y1_, x0_:x1_] * (1 - aa) + cg[y0_ - Y:y1_ - Y, x0_ - X:x1_ - X] * aa
        alpha[y0_:y1_, x0_:x1_] = np.maximum(alpha[y0_:y1_, x0_:x1_], aa)
    if treatment == "cut-paper":
        a = S.print_block(np.clip(alpha * 1.15, 0, 1), seed, "crowd", starve=0.04, edge=0.3)
        img = np.empty((Hd, Wd, 3), np.float32); img[:] = S.INK2
        return img, a
    return S._grade(fill), cv2.GaussianBlur(alpha, (0, 0), 0.6)


S._crowd = _crowd   # stage.crowd() resolves _crowd at call time

# ------------------------------------------------------------------ photographic puppet fills (U1 swatches)
SWATCH_FOR = {"man": "coat_dark_long", "jostler": "coat_light_overcoat", "conductor": "cape_officer"}
RUN_SWATCHES = ["coat_black_shawl", "trouser_wilson", "coat_dark_long", "cape_officer", "trouser_dark", "coat_light_overcoat"]


@functools.lru_cache(None)
def _tex(name):
    g = np.asarray(Image.open(U1 / "swatches" / f"{name}.png").convert("L")).astype(np.float32)
    g = np.concatenate([g, g[:, ::-1]], 1); g = np.concatenate([g, g[::-1]], 0)      # mirror tile: no seams
    t = np.tile(g, (H // g.shape[0] + 2, W // g.shape[1] + 2))[:H, :W]
    lo, hi = np.percentile(t, 2), np.percentile(t, 98)
    t = np.clip((t - lo) / max(hi - lo, 1), 0, 1) * 0.44             # keep the cloth dark: ink .. 44 % toward paper
    return S._grade(t * 255)


def photo_fill(P):
    out = {}
    for k, pp in enumerate(P["puppets"]):
        pid = pp["id"]
        if pid in SWATCH_FOR:
            nm = SWATCH_FOR[pid]
        elif pid.startswith("runner"):
            nm = RUN_SWATCHES[int(pid[6:] or 0) % len(RUN_SWATCHES)]
        else:
            nm = "cape_officer"
        out[pid] = np.roll(_tex(nm), int(round(pp.get("x", 0))), axis=1)   # texture rides with the puppet
    out["default"] = _tex("coat_dark_long")
    return out


R._bourse_fill = lambda: _tex("coat_dark_long")   # the 1933 plate is not used anywhere in the film

# ------------------------------------------------------------------ render(M, seed, t)
def render(M, seed, t):
    """One clip frame (untagged RGB) for manifest M at clip time t."""
    seed = int(seed)
    P = R.pose(seed, t)
    if M["camera"] == "overhead":
        img = S.plan_stage(seed, t)
        return R.draw_plan(img, P, R.INK).convert("RGB")
    tr = M["treatment"]
    dx = P["dx"]
    layers = [S.backdrop(seed, tr), S.crowd(seed, tr), S.bus_shadow(seed, dx), S.shift(S.bus_body(seed, tr), dx)]
    travel = S.bus_x(0) - S.bus_x(t)                 # rolls in, stops at A1, rolls again after A8 (v/r)
    for name in ("front", "rear"):
        tile, (cx, cy) = S.wheel(seed, name, S.wheel_angle_for(travel), tr)
        layers.append((tile, (cx + dx - tile.size[0] / 2, cy - tile.size[1] / 2)))
    img = S.compose(layers)
    fill = R.INK if tr == "cut-paper" else photo_fill(P)
    halo = True                      # the cleared rim: a cut edge, in both treatments (fill-independent)
    img = R.draw_side(img, P, fill, group="window", halo=halo)
    img = R.draw_side(img, P, fill, group="platform", halo=halo)
    img.alpha_composite(S.shift(S.bus_front(seed, tr), dx))
    img.alpha_composite(S.shift(S.bell_tassel(seed, P["bell_pull"], tr), dx))
    img.alpha_composite(S.shadow_slivers(seed, "runners", R.feet(P), 150))
    img = R.draw_side(img, P, fill, group="street", halo=halo)
    return img.convert("RGB")


def dtext(d, xy, s, font, fill, spacing=2):
    """Text with a hand-drawn delta: the kit fonts carry no Δ glyph, so the triangle is drawn."""
    x, y = xy
    if "Δ" not in s:
        d.text((x, y), s, font=font, fill=fill, spacing=spacing)
        return d.textlength(s, font=font)
    x0 = x
    for i, part in enumerate(s.split("Δ")):
        if i:
            sz = font.size
            asc = d.textbbox((0, 0), "H", font=font)
            top, bot = y + asc[1], y + asc[3]
            w_ = (bot - top) * 0.95
            d.polygon([(x, bot), (x + w_ / 2, top), (x + w_, bot)], outline=fill, fill=None, width=max(1, int(sz / 11)))
            x += w_ + sz * 0.15
        if part:
            d.text((x, y), part, font=font, fill=fill)
            x += d.textlength(part, font=font)
    return x - x0


def tag(img, text, size=13, xy=(12, None)):
    d = ImageDraw.Draw(img)
    f = kit.font("mono", size)
    b = d.textbbox((0, 0), text.replace("Δ", "M"), font=f)
    tw, th = b[2] - b[0], b[3] - b[1]
    x = xy[0]; y = (img.size[1] - th - 22) if xy[1] is None else xy[1]
    d.rectangle([x, y, x + tw + 14, y + th + 10], fill=INKC)
    dtext(d, (x + 7, y + 5 - b[1]), text, f, PAPER)
    return img


def clip_tag(cond, seed, t):
    extra = {"baseline": "", "d-treatment": " photographic-plate", "d-camera": " overhead"}[cond]
    return f"{LABEL[cond]}{extra} · seed {seed:04d} · t {t:4.2f}"


# ------------------------------------------------------------------ frame cache (precomputed in parallel)
CONDS = ("baseline", "d-treatment", "d-camera")
SEEDS = (417, 418)


def _cpath(cond, seed, f):
    return CACHE / f"{cond}_{seed}_{f:03d}.png"


def _job(args):
    cond, seed, fs = args
    M = manifest(cond)
    for f in fs:
        p = _cpath(cond, seed, f)
        if not p.exists():
            render(M, seed, f / FPS).save(p, compress_level=1)
    return len(fs)


def precompute():
    CACHE.mkdir(parents=True, exist_ok=True)
    jobs = []
    for c in CONDS:
        for s in SEEDS:
            for k in range(4):
                jobs.append((c, s, list(range(k, NF, 4))))
    ctx = get_context("fork")                       # forked workers: nothing is pickled
    procs = [ctx.Process(target=lambda js=jobs[w::4]: [_job(j) for j in js]) for w in range(4)]
    for p_ in procs:
        p_.start()
    for p_ in procs:
        p_.join()
        assert p_.exitcode == 0, "frame worker failed"


@functools.lru_cache(maxsize=64)
def clip_frame(cond, seed, f):
    f = max(0, min(NF - 1, f))
    p = _cpath(cond, seed, f)
    if p.exists():
        return Image.open(p).convert("RGB")
    return render(manifest(cond), seed, f / FPS)


# ------------------------------------------------------------------ cards (paper and ink)
def _paper():
    return Image.new("RGB", (W, H), PAPER)


MANIFEST_LINES = [("scene", "platform-bus encounter"), ("camera", "street-side"), ("treatment", "cut-paper"),
                  ("seeds", "0417 0418"), ("duration", "7.0 s · 24 fps · puppets on twos"),
                  ("destination", "MADELEINE – BASTILLE")]


def _ink_tab(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=INKC)


def card_manifest(k):
    """S0: title + baseline manifest typing out, cream on an ink tab."""
    img = _paper(); d = ImageDraw.Draw(img)
    d.text((64, 70), "one incident, three instructions", font=kit.font("serif", 50), fill=INKC)
    d.text((66, 132), "Exercises in Style (after Mauro Martino) · baseline manifest", font=kit.font("mono", 14), fill=DTINT)
    _ink_tab(d, 60, 176, 600, 6 * 34 + 26)
    f = kit.font("mono", 18)
    chars = max(0, k - 8) * 2.4
    used = 0
    for i, (key, val) in enumerate(MANIFEST_LINES):
        s = f"{key}: {val}"
        n = int(max(0, min(len(s), chars - used)))
        used += len(s)
        if n:
            d.text((80, 192 + i * 34), s[:n] + ("_" if n < len(s) and (k // 6) % 2 == 0 else ""), font=f, fill=PAPER)
    if k > 70:
        d.text((64, 430), f"manifest sha1 {BASE_SHA1}", font=kit.font("mono", 14), fill=INKC)
        d.text((64, 452), "rendered by render(M, seed, t) · same exposure sheet for every condition", font=kit.font("mono", 13), fill=DTINT)
    return img


def card_delta(k, field, old, new, effect):
    """S3/S6: the changed line is struck through over 6 frames, then the new value is typed."""
    img = _paper(); d = ImageDraw.Draw(img)
    dtext(d, (64, 56), f"Δ {field}", kit.font("serif", 50), INKC)
    d.text((66, 118), "PromptDelta · one field changed · everything else frozen", font=kit.font("mono", 14), fill=DTINT)
    _ink_tab(d, 60, 160, 640, 6 * 34 + 26)
    f = kit.font("mono", 18)
    for i, (key, val) in enumerate(MANIFEST_LINES):
        y = 176 + i * 34
        if key != field:
            d.text((80, y), f"{key}: {val}", font=f, fill=(150, 144, 135))
            continue
        head = f"{key}: "
        d.text((80, y), head + old, font=f, fill=PAPER)
        b0 = d.textbbox((80, y), head, font=f); b1 = d.textbbox((80, y), head + old, font=f)
        strike = kit.clamp((k - 4) / 6)                              # 6 frames
        if strike > 0:
            ym = (b1[1] + b1[3]) / 2
            d.line([(b0[2], ym), (b0[2] + (b1[2] - b0[2]) * strike, ym)], fill=PAPER, width=3)
        n = int(max(0, min(len(new), (k - 12) * 1.2)))
        if n:
            d.text((b1[2] + 18, y), new[:n], font=f, fill=PAPER)
    if k > 30:
        d.text((64, 410), f"diff keys: {{{field}}}   (asserted: exactly one)", font=kit.font("mono", 15), fill=INKC)
        d.text((64, 434), f"intended effect: “{effect}”", font=kit.font("mono", 15), fill=INKC)
    return img


@functools.lru_cache(None)
def coverage():
    return json.loads((WS / "verify/coverage.json").read_text())


@functools.lru_cache(None)
def drift_strip():
    im = Image.open(WS / "verify/rejected-drift-strip.jpg").convert("RGB")
    im = im.crop((0, 283, im.size[0], im.size[1]))   # overhead rows only (accepted vs drift); the side row is not reused
    w = 340; return im.resize((w, int(im.size[1] * w / im.size[0])), Image.LANCZOS)


def card_coverage(k):
    C = coverage()
    img = _paper(); d = ImageDraw.Draw(img)
    d.text((40, 26), "coverage report", font=kit.font("serif", 40), fill=INKC)
    d.text((42, 74), "observed in 6 inspected samples of one procedural engine (stage.py + rig.py on kit.py)",
           font=kit.font("mono", 12), fill=DTINT)
    ie = C["intended_effect_rate"]
    lost = C["lost_anchor_ids"]["d-camera"]; part = C["partial_anchor_ids"]["d-camera"]
    pred = C["predicted_losses_overhead"]["predicted"]
    iou = C["outline_iou"]["puppets"]["min"]
    au = pcm_report()
    rows = [
        ("intended effect", ""),
        ("  baseline", ie["baseline"]["rate"]),
        ("  Δ treatment", ie["d-treatment"]["rate"] + f" · IoU {iou:.1f}"),
        ("  Δ camera", ie["d-camera"]["rate"] + " · shove = shift"),
        ("lost in overhead", " ".join(lost)),
        ("  predicted", " ".join(pred) + " · others unpredicted"),
        ("partial in overhead", " ".join(part)),
        ("seeds", "procedural generator, seeds repeatable,"),
        ("", "verified by frame hash (frames 0 29 132 × 6)"),
        ("", "seed moves runners (7 vs 8) only;"),
        ("", "protected masks identical"),
        ("sound", ("bed + bell PCM identical in all 7 clip windows" if au["identical"] else "PCM DIFFERS across clip windows")),
        ("", "sha1 " + au["sha1"][0][:16] + " · hold: declared silence"),
        ("not claimed", "anything about text-to-video"),
        ("", "generators in general"),
    ]
    f = kit.font("mono", 13)
    y = 108
    for i, (a, b) in enumerate(rows):
        if k < 6 + i * 4:
            break
        dtext(d, (42, y), a, f, INKC)
        d.text((200, y), b, font=f, fill=INKC)
        y += 27 if a and not a.startswith(" ") else 22
    if k > 40:
        st = drift_strip()
        x0, y0 = 590, 140
        _ink_tab(d, x0 - 6, y0 - 30, st.size[0] + 12, st.size[1] + 36)
        d.text((x0 + 2, y0 - 24), "REJECTED DRIFT · RNG-coupled overhead projector", font=kit.font("mono", 12), fill=PAPER)
        img.paste(st, (x0, y0))
        ce = C["counterexample"]
        d = ImageDraw.Draw(img)
        d.text((x0, y0 + st.size[1] + 16), f"seed 0417: {ce['observed']['runners_overhead_drift']} runners overhead vs "
               f"{ce['observed']['runners_side']} side", font=kit.font("mono", 12), fill=INKC)
        for j, b in enumerate(ce["broken"]):
            d.text((x0, y0 + st.size[1] + 34 + j * 15), ("fails: " if j == 0 else "       ") + b, font=kit.font("mono", 11), fill=INKC)
    return img


# ------------------------------------------------------------------ S9 comparison grid
CHIPS = [("stop", "A1", 0.90), ("shove", "A3", 1.20), ("stanchion", "A4", 1.333), ("cord", "A4c", 1.25),
         ("protest", "A5", 2.00), ("vacate", "A5v", 3.60), ("seat", "A6", 5.50), ("seat-in-window", "A6w", 5.00),
         ("bell", "A7", 6.00), ("destination", "A0", 0.00), ("neck", "A-neck", 0.00)]


def grid_frame(tt, hold):
    C = coverage()
    img = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(img)
    f = 29 if hold else min(NF - 1, int(round(tt * FPS)))
    t = f / FPS
    cw, ch = 300, 169
    fs = kit.font("mono", 10)
    for r_, cond in enumerate(CONDS):
        y = 8 + r_ * 178
        lab = {"baseline": ["baseline"], "d-treatment": ["Δ treat-", "  ment"], "d-camera": ["Δ camera"]}[cond]
        for j, ln in enumerate(lab):
            dtext(d, (8, y + 4 + j * 15), ln, kit.font("mono", 12), INKC)
        d.text((8, y + 40), {"baseline": "street-side\ncut-paper", "d-treatment": "photo-\ngraphic-\nplate", "d-camera": "overhead"}[cond],
               font=fs, fill=DTINT, spacing=2)
        for c_, seed in enumerate(SEEDS):
            x = 88 + c_ * 304
            cell = clip_frame(cond, seed, f).resize((cw, ch), Image.LANCZOS)
            img.paste(cell, (x, y))
            tag(img, f"{seed:04d}", size=9, xy=(x + 4, y + ch - 20))
        # anchor chips for this row, one box per seed
        px = 700
        lost = set(C["lost_anchor_ids"][cond]); part = set(C["partial_anchor_ids"][cond])
        dd = ImageDraw.Draw(img)
        for i, (nm, aid, at) in enumerate(CHIPS):
            yy = y + 1 + i * 15
            on = hold or tt >= at
            is_lost = aid in lost
            col = DTINT if is_lost else INKC
            dd.text((px + 34, yy + 1), nm, font=fs, fill=col)
            for s_ in range(2):
                bx = px + s_ * 15
                if is_lost and on:
                    dd.rectangle([bx, yy + 1, bx + 11, yy + 12], fill=PAPER, outline=DTINT)
                    dd.line([(bx, yy + 12), (bx + 11, yy + 1)], fill=INKC, width=1)
                elif on and aid in part:
                    dd.rectangle([bx, yy + 1, bx + 11, yy + 12], fill=PAPER, outline=INKC)
                    dd.polygon([(bx, yy + 12), (bx + 11, yy + 1), (bx + 11, yy + 12)], fill=INKC)
                else:
                    dd.rectangle([bx, yy + 1, bx + 11, yy + 12], fill=INKC if on else PAPER, outline=INKC)
            if is_lost and on:
                tw = dd.textlength(nm, font=fs)
                dd.line([(px + 34, yy + 7), (px + 34 + tw, yy + 7)], fill=INKC, width=1)
                dd.text((px + 40 + tw, yy + 1), "lost", font=fs, fill=INKC)
    d = ImageDraw.Draw(img)
    tag(img, ("HOLD" if hold else "sync"), size=11, xy=(8, 470))
    tag(img, f"t {t:4.2f}", size=11, xy=(8, 498))
    return img


# ------------------------------------------------------------------ the shot list (plan.md section 5)
SHOTS = [  # (start, end, kind, args)
    (0.0, 4.0, "card0", None),
    (4.0, 11.0, "clip", ("baseline", 417)),
    (11.0, 18.0, "clip", ("baseline", 418)),
    (18.0, 20.0, "delta", ("treatment", "cut-paper", "photographic-plate", "same outlines, photographic fill")),
    (20.0, 27.0, "clip", ("d-treatment", 417)),
    (27.0, 34.0, "clip", ("d-treatment", 418)),
    (34.0, 36.0, "delta", ("camera", "street-side", "overhead", "plan view; shove as displacement")),
    (36.0, 43.0, "clip", ("d-camera", 417)),
    (43.0, 50.0, "clip", ("d-camera", 418)),
    (50.0, 58.0, "grid", None),
    (58.0, 64.0, "report", None),
]
CLIP_WINDOWS = [s for s, e, kind, a in SHOTS if kind == "clip"] + [50.0]
SECONDS = 64.0

film = Film(SLUG, seconds=SECONDS, boil=0, wobble=0, seed=417)
film.poster_at = 5.25


@film.picture
def picture(t, ink):
    ink._grain = False              # the stage carries its own fixed paper grain; no per-frame boil
    k = int(round(t * FPS))
    for s, e, kind, a in SHOTS:
        if s <= t < e or (kind == "report" and t >= s):
            break
    ks = k - int(round(s * FPS))
    if kind == "card0":
        img = card_manifest(ks)
    elif kind == "delta":
        img = card_delta(ks, *a)
    elif kind == "clip":
        cond, seed = a
        img = clip_frame(cond, seed, ks).copy()
        tag(img, clip_tag(cond, seed, ks / FPS))
    elif kind == "grid":
        img = grid_frame(ks / FPS, ks >= NF)
    else:
        img = card_coverage(ks)
    ink.img = img
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ------------------------------------------------------------------ sound
def _decode(path, rate=kit.RATE):
    """Decode a foraged wav with ffmpeg to float stereo at the kit rate."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "s16le", "-ac", "2", "-ar", str(rate), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float64) / 32768.0


@functools.lru_cache(None)
def clip_audio():
    """The one 7.0 s clip track: foraged bed + foraged bell at A7, kit thud at A3 and click at A4
    (both declared synthetic). Built once; the identical array is laid under every clip window."""
    n = int(round(CLIP * kit.RATE))
    m = kit.Mix(CLIP, seed=1201)
    bed = _decode(U1 / "audio/bed_7.0s.wav")[:n]
    bell = _decode(U1 / "audio/bell_conductor_2.6s.wav")
    m.thud(1.20, freq=62, gain=0.55, seconds=0.3)
    m.click(1.333, gain=0.25, bright=6000)
    st = np.stack([m.L, m.R], 1)
    st[:len(bed)] += bed * 0.85
    i = int(round((6.00 - 0.011) * kit.RATE))
    b = bell[:n - i].copy() * 0.7
    tail = int(0.06 * kit.RATE)
    b[-tail:] *= np.linspace(1, 0, tail)[:, None]                 # cut at the clip end: no spill into the next window
    st[i:i + len(b)] += b
    return st


@functools.lru_cache(None)
def pcm_report():
    """Rebuild the film's mix exactly as Film.render does and hash each 7.0 s clip window (s16 PCM)."""
    m = kit.Mix(SECONDS, seed=film.seed)
    sound(m)
    pcm = np.asarray(m.master()).reshape(-1, 2)
    hs = []
    for at in CLIP_WINDOWS:
        a0 = int(round(at * kit.RATE)); a1 = a0 + int(round(CLIP * kit.RATE))
        hs.append(hashlib.sha1(pcm[a0:a1].tobytes()).hexdigest())
    return dict(windows=CLIP_WINDOWS, sha1=hs, identical=len(set(hs)) == 1, rate=kit.RATE)


def _lay(mix, st, at):
    i = int(round(at * kit.RATE))
    n = min(len(st), mix.n - i)
    mix.L[i:i + n] += st[:n, 0]; mix.R[i:i + n] += st[:n, 1]


@film.sound
def sound(mix):
    clip = clip_audio()
    for at in CLIP_WINDOWS:
        _lay(mix, clip, at)
    street = _decode(U1 / "audio/street_bed_7.0s.wav")
    def bed(at, dur, fade_in, fade_out, gain=0.35):
        seg = street[:int(round(dur * kit.RATE))].copy() * gain
        n = len(seg); env = np.ones(n)
        fi, fo = int(fade_in * kit.RATE), int(fade_out * kit.RATE)
        if fi: env[:fi] = np.linspace(0, 1, fi)
        if fo: env[-fo:] = np.linspace(1, 0, fo)
        _lay(mix, seg * env[:, None], at)
    bed(0.0, 4.0, 2.5, 0.12, gain=0.25)            # S0: bed fades in (about -18 dB at the start)
    bed(18.0, 2.0, 0.1, 0.12)                      # S3
    bed(34.0, 2.0, 0.1, 0.12)                      # S6
    bed(58.0, 6.0, 0.1, 5.0)                       # S10: bed fades out
    # 57.0-58.0: the grid hold is declared silence.
    for c in range(32):                            # key clicks under the typing (kit click, declared synthetic)
        mix.click(0.36 + c * 0.083, gain=0.08, bright=5000)
    for at in (18.18, 18.6, 18.66, 18.72, 18.78, 34.18, 34.6, 34.66, 34.72):
        mix.click(at, gain=0.09, bright=5000)


if __name__ == "__main__":
    if not (len(sys.argv) > 1 and sys.argv[1] == "--stills"):
        precompute()
    film.render()
