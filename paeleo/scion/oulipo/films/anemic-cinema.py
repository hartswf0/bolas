"""Anemic cinema -- variation (SCION swarm assembly, editor).

24.0 s, 960x540, 24 fps. One plate turning about (480, 270), four discs in strict alternation:
  T1 (pun disc, door) -> W1 drawing substitution -> O_A (engraved rings, approaching)
  -> W2 -> T2 (reading disc, key and bell) -> W3 letters become real key cutouts
  -> O_B (key rings, receding) -> still pass (F360 frozen, then F360-362 as a plain strip).

All picture rendering is done by the swarm modules in films/swarm/anemic-cinema/:
  optics.py (U1: engraved ring disc, GrabCut keys, key-ring disc),
  glyphs.py (U2: original puns, GlyphPath, text discs),
  switch.py (U3: score.json ExposureSequence, Substitute W1-W3, 2x render + 180 deg shutter of
             8 sub-frames of the real rotation, INTER_AREA downsample, warm grade on optical discs).
This script only reads score.json, pre-renders every frame with switch.render_frame, asserts the
fixtures, and pastes the decoded frames onto a pure black field through kit.Film. No grain, no
vignette. Sound: one foraged bell strike (Commons, public domain) at the three switches, declared
digital silence elsewhere.

Run from the project root:
  python3 films/anemic-cinema.py                     film -> assets/films/anemic-cinema.mp4
  python3 films/anemic-cinema.py --stills 8 15 ...   stills -> films/stills/anemic-cinema/
  python3 films/anemic-cinema.py --silent            silent variant S0 -> sources/anemic-cinema/editor/
  python3 films/anemic-cinema.py --baseline B1|B2    W1 replaced by a hard cut / an 18-frame dissolve
"""
import hashlib
import json
import math
import os
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WS = HERE / "swarm" / "anemic-cinema"
SRC = HERE / "sources" / "anemic-cinema"
ED = SRC / "editor"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(WS))

import kit  # noqa: E402
from kit import Film  # noqa: E402
import switch as S  # noqa: E402

SLUG = "anemic-cinema"
SECONDS = 24.0
FPS = 24
NFR = int(SECONDS * FPS)
FIELD = 2

# ------------------------------------------------------------------ options
ARGS = sys.argv[1:]
SILENT = "--silent" in ARGS
BASELINE = None
if "--baseline" in ARGS:
    BASELINE = ARGS[ARGS.index("--baseline") + 1].upper()
    assert BASELINE in ("B1", "B2"), BASELINE
STILLS = bool(ARGS) and ARGS[0] == "--stills"
VARIANT = BASELINE or "film"
# kit.Film.render reads sys.argv for --stills; leave only what it understands
if not STILLS:
    sys.argv = sys.argv[:1]

SCORE = json.load(open(WS / "score.json"))
FR = SCORE["frames"]
assert len(FR) == NFR and SCORE["fps"] == FPS
FDIR = ED / "frames"


# ------------------------------------------------------------------ title (HANDMADE type, cream ring stock)
_TITLE = {}


def title_frame(k):
    """'anémic cinéma · variation' in small cream capitals filled with the same groove stock as the
    rings (2.5 px pitch at 1x, rendered at 2x and area-downsampled), warm grade, fade 6 f in / 6 f out."""
    if "rgb" not in _TITLE:
        import cv2
        O = S.mods()[1]
        ss = 2
        fnt = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 17 * ss)
        txt = "ANÉMIC CINÉMA  ·  VARIATION"
        spacing = 0.22  # open tracking, em
        widths = [fnt.getlength(c) for c in txt]
        total = sum(widths) + spacing * 17 * ss * (len(txt) - 1)
        m = Image.new("L", (960 * ss, 540 * ss), 0)
        d = ImageDraw.Draw(m)
        x = (960 * ss - total) / 2
        for c, w in zip(txt, widths):
            d.text((x, 270 * ss), c, font=fnt, fill=255, anchor="lm")
            x += w + spacing * 17 * ss
        a = np.asarray(m, np.float32) / 255.0
        yy = np.arange(540 * ss, dtype=np.float32)[:, None]
        groove = 1.0 - O.GROOVE_DEPTH * 0.5 * (1 + np.cos(2 * np.pi * yy / (O.GROOVE_1X * ss)))
        L = FIELD + a * (O.STOCK_A * groove - FIELD)
        L = cv2.resize(L, (960, 540), interpolation=cv2.INTER_AREA)
        _TITLE["rgb"] = np.clip(L[..., None] * O.WARM[None, None], 0, 255)
    fade = min(1.0, (k + 1) / 6.0, (24 - k) / 6.0)
    rgb = FIELD + (_TITLE["rgb"] - FIELD) * max(0.0, fade)
    return np.clip(rgb + 0.5, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ frames
def frame_path(k, variant=VARIANT):
    v = variant if (variant != "film" and FR[k].get("window") == "W1") else "film"
    return FDIR / f"{v}_{k:03d}.png"


def body_frame(k):
    """The rendered frame k (decoded from the pre-render; rendered live if missing)."""
    p = frame_path(k)
    if p.exists():
        return np.asarray(Image.open(p).convert("RGB"))
    v = VARIANT if FR[k].get("window") == "W1" else "film"
    rgb, _ = S.render_frame(k, v)
    return rgb


def strip_frame():
    """Still pass part 2: F360, F361, F362 as a plain vertical strip on the black field
    (glyphpaths.json still_pass.part2 cells; real frames area-downsampled; no sprockets, no edges)."""
    import cv2
    out = np.full((540, 960, 3), FIELD, np.uint8)
    for c in json.load(open(WS / "glyphpaths.json"))["still_pass"]["part2"]["cells"]:
        im = body_frame(c["k"])
        im = cv2.resize(im, (c["w"], c["h"]), interpolation=cv2.INTER_AREA)
        out[c["y"]:c["y"] + c["h"], c["x"]:c["x"] + c["w"]] = im
    return out


def compose(k):
    f = FR[k]
    if f["state"] == "title":
        return title_frame(k)
    if f["state"] == "still":
        if isinstance(f.get("shows_frame"), list):
            return strip_frame()
        return body_frame(360)          # part 1: the identical pixels of F360
    return body_frame(k)


# ------------------------------------------------------------------ fixtures (asserted before encoding)
def prerender():
    FDIR.mkdir(parents=True, exist_ok=True)
    stamp = hashlib.sha1(b"".join(open(WS / m, "rb").read() for m in
                                  ("score.json", "switch.py", "optics.py", "glyphs.py"))).hexdigest()
    cache = ED / "render_info.json"
    if cache.exists():
        old = json.load(open(cache))
        if old.get("stamp") == stamp:
            return old
    infos = _prerender()
    infos["stamp"] = stamp
    json.dump(infos, open(cache, "w"), indent=0)
    return infos


def _prerender():
    ks = [k for k in range(NFR) if FR[k]["state"] in ("body", "switch")]
    infos = {"film": S.render_range(ks, "film", str(FDIR))}
    w1 = list(range(126, 144))
    for v in ("B1", "B2"):
        infos[v] = S.render_range(w1, v, str(FDIR))
    return infos


def run_fixtures(infos):
    import switch_fixtures as SF
    SF.FR = str(FDIR)                    # measure the frames this film is cut from
    sc = SCORE
    res = {}
    alt = SF.alternation(SF.alternation_from_frames(sc))
    bad = SF.alternation(["T1", "O_A", "O_B", "T2"])
    assert alt["passed"] and alt["bodies"] == ["T1", "O_A", "T2", "O_B"], alt
    assert not bad["passed"], "alternation must fail on T1,O_A,O_B,T2"
    assert SF.windows_belong_to_incoming(sc)
    res["I3_alternation"] = dict(bodies=alt["bodies"], fails_on_test_score=True, passed=True)
    od = SF.omega_declared(sc)
    assert all(v["passed"] for v in od.values()), od
    om = SF.omega_measured()
    # I4 bar (repair 1, stated before measuring, no post-hoc band): the declared omega is exact on
    # integer ticks; MEASURED on the rendered frames, (a) no pause, (b) the aggregate rate over the
    # whole measured span (W1: F118-152, i.e. the window with 8 body frames each side) within 1 % of
    # the declared rate, (c) the entry/exit pairs and every body pair within 1 %. The largest
    # interior hybrid pair is REPORTED with its error and whether it meets 1 %; it is not asserted.
    meas = {}
    for w in ("W1", "W2", "W3"):
        m = om[w]
        exp = m["expected_deg_per_frame"]
        pairs = m["pairs"]
        agg = float(np.mean([r["deg"] for r in pairs]))
        k0 = S.WIN[w][0]
        edge = [r for r in pairs if (not r["in_window"]) or r["pair"][0] in (k0 - 1, k0 + S.WLEN - 1)]
        edge_err = max(abs(r["deg"] - exp) / exp for r in edge)
        agg_err = abs(agg - exp) / exp
        assert not m["paused_pairs"], (w, m["paused_pairs"])
        assert agg_err <= 0.01, (w, agg, exp)
        assert edge_err <= 0.01, (w, edge_err)
        meas[w] = dict(expected_deg=exp, aggregate_deg=round(agg, 4), aggregate_rel_err=round(agg_err, 5),
                       span=[pairs[0]["pair"][0], pairs[-1]["pair"][1]],
                       entry_exit_and_body_pairs_max_rel_err=round(edge_err, 5),
                       window_median_rel_err=m["median_rel_err_in_window"],
                       interior_hybrid_pair_max_rel_err=m["max_rel_err_in_window"], worst_pair=m["worst_pair"],
                       every_pair_within_1pc=bool(m["max_rel_err_in_window"] <= 0.01))
    res["I4_constant_omega"] = dict(
        declared="exact (integer ticks)", measured=meas,
        bar="no pause; aggregate rate and every entry/exit/body pair within 1 % (asserted); interior hybrid "
            "pairs reported, not asserted",
        passed=True)
    per = SF.periodicity(sc)
    assert all(v["passed"] for v in per.values()), per
    res["I5_periodicity"] = dict(P80=per["omega_fast"]["passed"], P_read=per["omega_read"]["P"],
                                 P_read_passed=per["omega_read"]["passed"], passed=True)
    go = SF.glyph_order(sc)
    assert go["passed"], go
    res["I2_glyph_order"] = dict(T1_F100=go["still_frames"]["T1"]["passed"], T2_F360=go["still_frames"]["T2"]["passed"],
                                 W1=go["windows"]["W1"]["passed"], W2=go["windows"]["W2"]["passed"],
                                 W3_token_order=go["W3_swap_in_token_order"]["passed"], passed=True)
    ss = SF.single_state(infos)
    assert ss["passed_on_film"] and ss["fails_on_B2"], ss["pixel_ghost_overlap"]
    assert ss["film"]["W1"]["distinct_hybrid_states"] >= 6
    res["per_mark_single_state"] = dict(
        film_ghost_max=ss["pixel_ghost_overlap"]["film_max"], B2_ghost_max=ss["pixel_ghost_overlap"]["B2_max"],
        W1_distinct_hybrid_states=ss["film"]["W1"]["distinct_hybrid_states"],
        F134=[r for r in ss["film"]["W1"]["rows"] if r["k"] == 134][0]["ring_states"], passed=True)
    rp = SF.replay(infos)
    assert rp["passed"], "replay hashes differ"
    res["replay_sha1"] = dict(frames="126-143", identical=True, passed=True)
    # still pass equals the moving frame
    a = np.asarray(compose(516)); b = body_frame(360)
    assert np.array_equal(a, b), "still pass part 1 must be the pixels of F360"
    res["still_pass_identical_F360"] = dict(passed=True)
    # honest material: black field, no grain
    f = body_frame(200).astype(np.float32)
    corner = f[:40, :40].mean(), f[:40, :40].std()
    assert corner[0] <= 6 and corner[1] <= 1.5, corner
    res["black_field"] = dict(corner_L=round(float(corner[0]), 2), sigma=round(float(corner[1]), 3), passed=True)
    # I8 safe playback: inter-frame luminance change < 25 % of the frame mean (title excluded)
    # over the motion picture F24-515; the two cuts into and inside the still pass (F516, F552)
    # are single steps (no repetition, so no strobing) and are reported, not asserted
    prev, worst, cuts = None, (0, None), {}
    for k in range(24, NFR):
        m = float(compose(k).astype(np.float32).mean())
        if prev is not None and m > 0:
            rel = abs(m - prev) / max(prev, 1e-6)
            if k in (516, 552):
                cuts[k] = round(rel, 3)
            elif rel > worst[0]:
                worst = (rel, k)
        prev = m
    if VARIANT == "film":
        assert worst[0] < 0.25, worst
    res["I8_luminance_step"] = dict(variant=VARIANT, max_rel_F24_515=round(float(worst[0]), 4), at=worst[1],
                                    declared_cuts_rel_step=cuts, passed=bool(worst[0] < 0.25),
                                    note="asserted on the film only; a baseline may break it (B1 is a hard cut). The two cuts into "
                                         "and inside the still pass (F516, F552) are an ACCEPTED, declared exception: a "
                                         "ramp would break the byte-identity of the frozen F360, which the still pass "
                                         "exists to show; each is a single step with no repetition, so no strobing")
    json.dump(res, open(ED / ("assembly-fixtures.json" if VARIANT == "film" else f"assembly-fixtures-{VARIANT}.json"), "w"), indent=1)
    print("fixtures (%s):" % VARIANT, {k: v["passed"] for k, v in res.items()})
    return res


# ------------------------------------------------------------------ sound
def load_bell():
    with wave.open(str(SRC / "switch" / "bell.wav")) as w:
        assert w.getframerate() == kit.RATE and w.getsampwidth() == 2
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(1)
    return x


class FlatMix(kit.Mix):
    """kit.Mix whose master() only converts: the kit master boosts a track whose peak is < 0.25
    by up to 4x, which would lift the bell from -14.5 dBFS to about -1 dBFS. Here the levelled
    foraged strike is kept as levelled, and the declared silence stays exactly zero."""

    def master(self):
        st = np.stack([self.L, self.R], 1)
        return np.clip(np.round(st * 32767), -32768, 32767).astype(np.int16)


kit.Mix = FlatMix                       # Film.render builds its Mix from the kit namespace

CUES = [c / FPS for c in SCORE["sound_cues"]["bell"]]      # 5.25, 10.25, 17.75 s
assert CUES == [5.25, 10.25, 17.75], CUES


# ------------------------------------------------------------------ the film
film = Film(SLUG, seconds=SECONDS, boil=0, wobble=0)
film.poster_at = 5.583   # F134, the defining hybrid frame of W1


@film.picture
def picture(t, ink):
    ink._grain = False                   # I7: kit grain off, every frame; no vignette is set
    k = int(round(t * FPS))
    ink.fill((FIELD, FIELD, FIELD))
    ink.paste(Image.fromarray(compose(k)), (0, 0))
    ink._grain = False


@film.sound
def sound(mix):
    if SILENT:
        return                            # S0: fully silent variant
    bell = load_bell()
    for at in CUES:
        mix.add(bell, at, gain=1.0, pan=0.0)


def compare_sheets():
    """The 8.0 s and 15.0 s frames beside the references, for the critic (our pixels left)."""
    refs = ROOT / "assets" / "references"
    out = []
    for t, ref in ((8.0, "duchamp2.webp"), (15.0, "spiralTextPom.webp"), (3.0, "spiralTextPom.webp")):
        ours = Image.fromarray(compose(int(t * FPS)))
        r = Image.open(refs / ref).convert("RGB")
        r = r.resize((int(r.width * 540 / r.height), 540), Image.LANCZOS)
        sheet = Image.new("RGB", (960 + 12 + r.width, 540), (0, 0, 0))
        sheet.paste(ours, (0, 0))
        sheet.paste(r, (972, 0))
        p = WS / f"editor-compare-{t:04.1f}s-{ref.split('.')[0]}.jpg"
        sheet.save(p, quality=90)
        out.append(str(p))
    return out


if __name__ == "__main__":
    ED.mkdir(parents=True, exist_ok=True)
    if STILLS:
        film.render()
        sys.exit(0)
    infos = prerender()
    run_fixtures(infos)
    print("compare:", compare_sheets())
    if SILENT or BASELINE:
        name = SLUG + ("-silent" if SILENT else "") + (f"-{BASELINE}" if BASELINE else "")
        film.slug = name
        film.render(out_dir=ED)
    else:
        film.render()
        mp4 = ROOT / "assets" / "films" / f"{SLUG}.mp4"
        assert mp4.stat().st_size <= 6e6, mp4.stat().st_size
