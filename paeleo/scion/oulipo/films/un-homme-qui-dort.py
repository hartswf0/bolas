"""Un homme qui dort -- one 35-second picture, screened twice with two timings of the same words.

Assembly of the SCION swarm (plan-r2 / beats-r2 / aesthetic-r2), montage editor, repair round 1.

PICTURE (foraged, Library of Congress FSA/OWI negatives, "No known restrictions"):
  S1 WAKE   LoC 2017862347 (Esther Bubley, Jan 1943, master TIFF 8d33590u.tif) -- the same sitter as S3/S4,
            head bowed over a newspaper against the pale flash-lit wall; GrabCut head lifts (weighted rotation).
  S2        LoC 2017735081 (Russell Lee, 1936) wall telephone (U1's frames).
  S3 + S4   LoC 2017862340 (Bubley, Jan 1943, master TIFF 8d33583u.tif), one framing on the reference layout;
            the head turns 9 deg toward the bell with its cast shadow (weighted warp), then the 7.5 s hold.
  S5 = S7   LoC 2017811447 (John Vachon, 1940) stair flight, climber cut out and moved (byte-identical twice).
  S6        LoC 2017714056 (Carl Mydans, 1935) stairwell (U1's frames).
  Pre-caption PNG sequences come from editor-r2 (S1, S3, S4, S5, S7; scripts in
  films/swarm/un-homme-qui-dort/editor-r2-build/) and U1 (S2, S6); they are pasted unchanged here.
  Each plate carries one monotone neutral print curve (recorded); no grain, vignette or filter is added.

SOUND (foraged, Wikimedia Commons, CC BY 4.0 / CC BY 3.0): U2's four pass stems (room tone,
  crank-telephone bell through the wall, near stair footfalls, stairwell footfalls), mixed identically in
  both passes; U2's room-tone handles carry the two cards, cross-faded under card II so the room never
  restarts audibly at 37.0.

HANDMADE: the cards (numerals I / II) and the captions (U3's takeA / takeB, Instrument Serif 26 px
  #efefef on a neutral #1e1e1e band at 60 %).

Layout (film seconds): CARD-I 0-1, PASS-A 1-36, CARD-II 36-37, PASS-B 37-72.

    python3 films/un-homme-qui-dort.py                 # render assets/films/un-homme-qui-dort.mp4
    python3 films/un-homme-qui-dort.py --stills 2.5 ... # stills
    python3 films/un-homme-qui-dort.py --timings OUT   # write final caption timings + checks (JSON)
"""
import hashlib
import json
import re
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import Film, FPS, H, W  # noqa: E402

SLUG = "un-homme-qui-dort"
ROOT = Path(__file__).resolve().parent.parent
SWARM = ROOT / "films" / "swarm" / SLUG
SRC = ROOT / "films" / "sources" / SLUG
U2 = SRC / "u2-sound-sound-editor-distance-breath-withheld-cues-"
EDITOR = SRC / "editor"

BLACK = (0x1E, 0x1E, 0x1E)        # reference anchor black
CAPTION = (0xEF, 0xEF, 0xEF)      # reference palette white
BAND_ALPHA = int(round(255 * 0.60))
CAP_SIZE = 26

PASS = 35.0
PASS_FRAMES = int(round(PASS * FPS))          # 840
LAYOUT = {"CARD-I": (0.0, 1.0), "PASS-A": (1.0, 36.0), "CARD-II": (36.0, 37.0), "PASS-B": (37.0, 72.0)}
TOTAL = 72.0
SHOTS = [("S1", 0.0, 5.5), ("S2", 5.5, 8.5), ("S3", 8.5, 11.5), ("S4", 11.5, 19.0),
         ("S5", 19.0, 24.5), ("S6", 24.5, 27.0), ("S7", 27.0, 35.0)]
SIL_H = (11.5, 19.0)
GUARD = 0.1


# ------------------------------------------------------------ material ---
def shot_frames():
    """Pass frame index -> PNG path, in shot order (e2-picture-ledger shot_dirs)."""
    out = []
    dirs = json.loads((SWARM / "e2-picture-ledger.json").read_text())["shot_dirs"]
    for sid, a, b in SHOTS:
        n = int(round((b - a) * FPS))
        files = sorted(Path(dirs[sid]).glob(f"{sid}_*.png"))
        assert len(files) == n, (sid, len(files), n)
        out += files
    assert len(out) == PASS_FRAMES
    return out


FRAMES = shot_frames()


def parse_srt(p):
    txt = Path(p).read_text(encoding="utf-8")
    cues = []
    for blk in re.split(r"\n\s*\n", txt.strip()):
        lines = blk.strip().splitlines()
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", lines[1])
        g = [int(x) for x in m.groups()]
        on = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        off = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        cues.append({"text": " ".join(lines[2:]).strip(), "on": on, "off": off})
    return cues


TAKE = {"A": parse_srt(SWARM / "takeA.srt"), "B": parse_srt(SWARM / "takeB.srt")}
U1L = json.loads((SWARM / "e2-picture-ledger.json").read_text())   # measured picture ledger (repair round 1)
U2L = json.loads((SWARM / "u2-sound-ledger.json").read_text())
BEATS = json.loads((SWARM / "beats.json").read_text())


def fr(t):
    return int(round(t * FPS))


# --------------------------------------------- invariants (re-asserted) ---
def pixel_sha1(p):
    return hashlib.sha1(np.asarray(Image.open(p).convert("RGB")).tobytes()).hexdigest()


def invariants():
    rep = {}
    # I5: S5 == S7 27.0-32.5, by SHA-1 of decoded pixels (and S7 tail = S5 last frame)
    s5 = [pixel_sha1(p) for p in FRAMES[fr(19.0):fr(24.5)]]
    s7 = [pixel_sha1(p) for p in FRAMES[fr(27.0):fr(32.5)]]
    tail = {pixel_sha1(p) for p in FRAMES[fr(32.5):fr(35.0)]}
    assert len(s5) == len(s7) == 132 and s5 == s7, "S5 != S7"
    assert tail == {s5[-1]}, "S7 tail is not S5's last frame held"
    rep["S5_eq_S7_sha1"] = {"frames": 132, "equal": True, "tail_held_frames": fr(35.0) - fr(32.5)}
    # I6: identical strings, order, durations across tracks
    A, B = TAKE["A"], TAKE["B"]
    assert [c["text"] for c in A] == [c["text"] for c in B]
    assert all(abs((a["off"] - a["on"]) - (b["off"] - b["on"])) < 1e-6 for a, b in zip(A, B))
    rep["strings_identical"] = [c["text"] for c in A]
    # P3: onset = event -/+ 1.2 +/- 0.05, against measured event times where U1 measured them
    ev = {e["id"]: e for e in BEATS["events"]}
    m = U1L["measured"]["events"]
    measured_on = {"E1": m["E1"]["authored_frames"][0] / FPS, "E2": 6.0, "E3": 9.0,
                   "E4": m["E4_enter"]["measured_t"], "E6": m["E6_enter"]["measured_t"]}
    binds = ["E1", "E2", "E3", "E4", "E6"]
    offs = []
    for i, eid in enumerate(binds):
        da = A[i]["on"] - measured_on[eid]
        db = B[i]["on"] - measured_on[eid]
        assert abs(da + 1.2) <= 0.05 + 1e-9, (eid, da)
        assert abs(db - 1.2) <= 0.05 + 1e-9, (eid, db)
        offs.append({"clause": f"c{i + 1}", "event": eid, "event_t": round(measured_on[eid], 4),
                     "planned_t": ev[eid]["t_on"], "A_offset": round(da, 4), "B_offset": round(db, 4)})
    rep["onset_offsets"] = offs
    # I3: no caption inside SIL-H (+ guard), either pass; and no caption frame in S4
    for k in "AB":
        for c in TAKE[k]:
            assert c["off"] <= SIL_H[0] - GUARD + 1e-9 or c["on"] >= SIL_H[1] + GUARD - 1e-9, (k, c)
            assert not (fr(c["on"]) < fr(SIL_H[1]) and fr(c["off"]) > fr(SIL_H[0])), (k, c)
    rep["SIL_H_caption_free"] = True
    # D and Bl on U1's per-frame figure-alpha coverage (S5 frames 0..131, S7 frames 0..191)
    cov = U1L["measured"]["figure_alpha_coverage"]
    shad = U1L["measured"]["shadow_alpha_coverage"]
    pcov = {}
    for sid, t0 in (("S5", 19.0), ("S7", 27.0)):
        for i, x in enumerate(cov[sid]):
            pcov[fr(t0) + i] = max(x, shad[sid][i] if i < len(shad[sid]) else 0.0)
    c5 = B[4]
    zero = [f for f in range(fr(c5["on"]), fr(c5["off"])) if pcov[f] <= 0.0]
    assert len(zero) / FPS >= 0.8, len(zero)
    c4 = B[3]
    vis = [pcov[f] > 0 for f in range(fr(c4["on"]), fr(c4["off"]))]
    assert all(vis), "Bl: c4.B not wholly inside figure-visible frames"
    assert pcov[fr(A[3]["on"])] <= 0 and pcov[fr(A[4]["on"])] <= 0, "pass I c4/c5 not on empty stair"
    rep["D"] = {"c5B": [c5["on"], c5["off"]], "zero_figure_and_shadow_frames": len(zero),
                "seconds": round(len(zero) / FPS, 3), "first_zero_pass_frame": zero[0],
                "film_t": [round(37.0 + zero[0] / FPS, 3), round(37.0 + c5["off"], 3)]}
    rep["Bl"] = {"c4B": [c4["on"], c4["off"]], "frames": len(vis), "all_figure_visible": True}
    rep["A_baseline_empty_onsets"] = {"c4A_frame_cov": pcov[fr(A[3]["on"])], "c5A_frame_cov": pcov[fr(A[4]["on"])]}
    # captions never straddle into a shot holding a different event (allowed crossings: own shot)
    return rep


REPORT = invariants()


# --------------------------------------------------------------- picture ---
_cache = {}


def plate(i):
    if i not in _cache:
        if len(_cache) > 4:
            _cache.clear()
        im = Image.open(FRAMES[i]).convert("RGB")
        assert im.size == (W, H)
        _cache[i] = im
    return _cache[i]


def caption_at(track, pf):
    for c in TAKE[track]:
        if fr(c["on"]) <= pf < fr(c["off"]):
            return c["text"]
    return None


def draw_caption(ink, s):
    y = H - 46
    tw, th = ink.text_size(s, "serif", CAP_SIZE)
    ink.d.rectangle([W / 2 - tw / 2 - 14, y - th / 2 - 10, W / 2 + tw / 2 + 14, y + th / 2 + 12],
                    fill=BLACK + (BAND_ALPHA,))
    ink.text((W / 2, y), s, "serif", CAP_SIZE, CAPTION, anchor="mm")


def card(ink, numeral):
    ink.fill(BLACK)
    ink.text((W / 2, H / 2), numeral, "serif", 54, CAPTION, anchor="mm")


def segment(k):
    """film frame -> (segment id, pass frame or None)."""
    if k < fr(1.0):
        return "CARD-I", None
    if k < fr(36.0):
        return "PASS-A", k - fr(1.0)
    if k < fr(37.0):
        return "CARD-II", None
    return "PASS-B", min(k - fr(37.0), PASS_FRAMES - 1)


def picture(t, ink):
    ink.paper(BLACK, grain=False)          # kit grain off on every frame; vignette never called
    seg, pf = segment(ink.i)
    if seg == "CARD-I":
        return card(ink, "I")
    if seg == "CARD-II":
        return card(ink, "II")
    ink.paste(plate(pf))
    s = caption_at("A" if seg == "PASS-A" else "B", pf)
    if s:
        draw_caption(ink, s)


# ----------------------------------------------------------------- sound ---
def read_wav(p):
    with wave.open(str(p)) as w:
        assert w.getframerate() == 44100 and w.getnchannels() == 1 and w.getsampwidth() == 2, p
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0


STEMS = ["ST-BELL", "ST-STEPS-NEAR", "ST-STEPS-ABOVE"]


def sound(mix):
    stems = {n: read_wav(U2 / "kit44k1" / f"{n}.wav") for n in STEMS}
    # room tone: U2's 37 s handles file (1 s pre-roll + the 35 s pass excerpt + 1 s post-roll, same gain).
    # Its 35 s core equals U2's ST-ROOM stem sample for sample after the first 62 ms; the kit44k1 ST-ROOM
    # copy starts with 24 ms of digital silence (resampler edge), which made a dropout at each pass start.
    h = read_wav(EDITOR / "ST-ROOM-HANDLES-37s-44k1.wav")
    r = 44100
    stems["ST-ROOM"] = h[r:36 * r]
    for at in (LAYOUT["PASS-A"][0], LAYOUT["PASS-B"][0]):      # identical in both passes
        for n in ["ST-ROOM"] + STEMS:
            mix.add(stems[n], at)
    # cards: the handles' pre-roll / post-roll (sample-continuous with the core)
    mix.add(h[:r], 0.0)                     # CARD-I: pre-roll leading into pass A's room
    # CARD-II: pass A's room continues past its end (post-roll) and cross-fades, equal power over the
    # card, into the pre-roll that leads sample-continuously into pass B's room at 37.0 (no restart click)
    u = np.linspace(0.0, 1.0, r, endpoint=False)
    mix.add(h[36 * r:37 * r] * np.cos(u * np.pi / 2) + h[:r] * np.sin(u * np.pi / 2), 36.0)


film = Film(SLUG, TOTAL, boil=0, wobble=0)
film.poster_at = 37.0 + 15.0               # S4 held close-up, pass II
film.picture(picture)
film.sound(sound)

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--timings":
        out = {"layout": LAYOUT, "shots_pass_t": SHOTS,
               "captions_film_t": {k: [{"text": c["text"], "pass_t": [c["on"], c["off"]],
                                        "film_t": [round(c["on"] + LAYOUT["PASS-" + k][0], 3),
                                                   round(c["off"] + LAYOUT["PASS-" + k][0], 3)],
                                        "frames_film": [fr(c["on"]) + fr(LAYOUT["PASS-" + k][0]),
                                                        fr(c["off"]) + fr(LAYOUT["PASS-" + k][0])]}
                                       for c in TAKE[k]] for k in "AB"},
               "invariants": REPORT}
        Path(sys.argv[2]).write_text(json.dumps(out, indent=1))
        print("timings ->", sys.argv[2])
    else:
        film.render()
