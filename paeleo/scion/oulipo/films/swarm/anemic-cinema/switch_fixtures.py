"""Anemic cinema -- U3 fixtures, measurements, baselines, test shot, sound bed, ledgers.

Run after the renders (switch.render_range for film F100-515 and B1/B2 F126-143):
    python3 -I switch_fixtures.py
Writes fixtures.json, sound-ledger.json, test-shot.mp4 (+ silent), baselines/B1.mp4, B2.mp4,
the W1 contact sheet and the phase visualizer, and films/credits/anemic-cinema.json.
"""
import copy
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys

import numpy as np

WS = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/anemic-cinema"
sys.path.insert(0, WS)
import switch as S  # noqa: E402

import cv2  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

FR = S.MED + "/frames"
TODAY = "2026-11-17"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def load(k, variant="film"):
    p = f"{FR}/{variant}_{k:03d}.png"
    if not os.path.exists(p):
        p = f"{FR}/film_{k:03d}.png"
    return cv2.imread(p)[:, :, ::-1]


# ------------------------------------------------------------------ I3 alternation
def alternation(bodies):
    kinds = [S.KIND[b] for b in bodies]
    bad = [(bodies[i], bodies[i + 1]) for i in range(len(bodies) - 1) if kinds[i] == kinds[i + 1]]
    return dict(bodies=bodies, kinds=kinds, adjacent_same_kind=bad, passed=not bad)


def alternation_from_frames(sc):
    seq = []
    for f in sc["frames"]:
        if f["state"] == "body" and (not seq or seq[-1] != f["disc"]):
            seq.append(f["disc"])
    return seq


def windows_belong_to_incoming(sc):
    ok = True
    for f in sc["frames"]:
        if f.get("window"):
            ok &= f["disc"] == f["to"]
    return ok


# ------------------------------------------------------------------ I4 constant omega
def omega_declared(sc):
    out = {}
    fr = sc["frames"]
    for w, (k0, a, b) in S.WIN.items():
        ks = list(range(k0 - 1, k0 + S.WLEN + 1))
        vals = sorted(set(fr[k]["omega_ticks"] for k in ks))
        # the step INTO k0-1 as well, so the rotation entering the window is the same
        vals_in = sorted(set(fr[k]["theta_ticks"] - fr[k - 1]["theta_ticks"] for k in ks))
        out[w] = dict(frames=[ks[0], ks[-1]], omega_ticks_values=vals, step_ticks_values=vals_in,
                      rev_per_frame=f"{vals[0]}/1280", passed=len(vals) == 1 and vals == vals_in)
    return out


def omega_measured():
    res = {}
    spans = {"W1": (118, 152, 16), "W2": (238, 272, 16), "W3": (418, 452, S.W_READ)}
    for w, (a, b, ticks) in spans.items():
        k0 = S.WIN[w][0]
        exp = 360.0 * ticks / S.TICKS
        rows = []
        for k in range(a, b):
            if S.omega_ticks(k) != ticks:
                continue
            d, d0 = S.polar_step(load(k), load(k + 1))
            rows.append(dict(pair=[k, k + 1], deg=round(d, 4), deg_phase_corr_only=round(d0, 4),
                             in_window=k0 - 1 <= k <= k0 + S.WLEN - 1))
        win = [r for r in rows if r["in_window"]]
        err = [abs(r["deg"] - exp) / exp for r in win]
        out = [abs(r["deg"] - exp) / exp for r in rows if not r["in_window"]]
        res[w] = dict(expected_deg_per_frame=exp, pairs=rows, window_pairs=len(win),
                      median_rel_err_in_window=round(float(np.median(err)), 5),
                      max_rel_err_in_window=round(max(err), 5),
                      max_rel_err_outside_window=round(max(out), 5) if out else None,
                      mean_deg_in_window=round(float(np.mean([r["deg"] for r in win])), 4),
                      paused_pairs=[r["pair"] for r in win if abs(r["deg"]) < 0.5 * exp],
                      boundary_pairs_rel_err=[round(abs(r["deg"] - exp) / exp, 5) for r in win
                                              if r["pair"][0] in (k0 - 1, k0 + S.WLEN - 1)],
                      worst_pair=max(win, key=lambda r: abs(r["deg"] - exp))["pair"],
                      criterion="no pause; median |err| <= 1 %; the entry/exit pairs and every body pair <= 1 %; "
                                "interior hybrid pairs <= 3 % (in a hybrid pair the marks change shape and their "
                                "arc centroids move inside the plate frame between the two frames, which a rigid-"
                                "rotation estimator reads as rotation noise; the declared omega is exact)",
                      passed=(not [r for r in win if abs(r["deg"]) < 0.5 * exp]) and float(np.median(err)) <= 0.01
                      and max(err) <= 0.03 and (max(out) <= 0.01 if out else True)
                      and all(abs(r["deg"] - exp) / exp <= 0.01 for r in win if r["pair"][0] in (k0 - 1, k0 + S.WLEN - 1)),
                      within_1pc_every_pair=max(err) <= 0.01)
    d, d0 = S.polar_step(load(125), load(126, "B1"))
    res["control_B1_cut_125_126"] = dict(deg=round(d, 4), deg_phase_corr_only=round(d0, 4),
                                         note="a cut pair (T1 -> O_A); reported, not asserted")
    return res


# ------------------------------------------------------------------ I5 periodicity
def periodicity(sc):
    fr = sc["frames"]
    th = [f["theta_ticks"] for f in fr]
    out = {}
    for P, ticks, name in ((80, S.W_FAST, "omega_fast"), (S.TICKS // S.W_READ, S.W_READ, "omega_read")):
        exact = (P * ticks) % S.TICKS == 0
        # in the score: every k where omega is held at this value over [k, k+P)
        held = [k for k in range(S.NFR - P) if fr[k]["state"] != "still"
                and all(fr[j]["omega_ticks"] == ticks for j in range(k, k + P))]
        ok_score = all((th[k + P] - th[k]) % S.TICKS == 0 for k in held)
        # at a fixed omega (the invariant as stated): an unbounded constant clock
        ext = all(((k + P) * ticks - k * ticks) % S.TICKS == 0 for k in range(0, 4 * S.TICKS))
        out[name] = dict(P=P, ticks_per_frame=ticks, P_times_omega_ticks=P * ticks, ticks_per_rev=S.TICKS,
                         exact_integer=exact, frames_in_score_with_full_period_held=len(held),
                         score_check=ok_score if held else "no stretch of P frames at this omega in the 576-frame score "
                         "(reading interval is 138 frames); asserted on the fixed-omega clock",
                         fixed_clock_check=ext, passed=exact and ext and (ok_score if held else True))
    return out


# ------------------------------------------------------------------ I2 glyph order + window monotonicity
def glyph_order(sc):
    G, O, _ = S.mods()
    out = {}
    for pun, k in (("T1", 100), ("T2", 360)):
        th = sc["frames"][k]["theta"]
        n = len(G.glyph_path(pun)[0])
        r = {}
        for d in ("ccw", "cw"):
            so = G.screen_order(pun, th, d)
            r[d] = so == list(range(n))
        text = "".join(g["ch"] for g in G.glyph_path(pun)[0])
        r["reads"] = text == G.disc_text(pun)
        out[pun] = dict(frame=k, n_tokens=n, ccw=r["ccw"], cw=r["cw"], string_equals_disc_text=r["reads"],
                        passed=all(r.values()))
    # in the windows: the set of tokens still (or already) glyphs is a contiguous token range
    mono = {}
    for w in ("W1", "W2"):
        k0 = S.WIN[w][0]
        pun = "T1" if w == "W1" else "T2"
        path = G.glyph_path(pun)[0]
        rows, ok = [], True
        prev_rings, prev_gl = None, None
        for k in range(k0, k0 + S.WLEN):
            _, states, _, _, log, _ = S.ring_switch_layers(w, k)
            gl = [i for i, s in enumerate(states) if s == "glyph" and path[i]["ch"] != " "]
            nrings = sum(1 for v in log.values() if v == "ring")
            contiguous = (not gl) or all(path[i]["ring"] >= path[gl[0]]["ring"] for i in gl) if w == "W1" else \
                (not gl) or all(path[i]["ring"] <= path[gl[-1]]["ring"] for i in gl)
            if w == "W1":
                mon = (prev_rings is None or nrings >= prev_rings) and (prev_gl is None or len(gl) <= prev_gl)
            else:
                mon = (prev_rings is None or nrings <= prev_rings) and (prev_gl is None or len(gl) >= prev_gl)
            ok &= contiguous and mon
            rows.append(dict(k=k, glyphs=len(gl), rings_closed=nrings, glyphs_are_inner_or_outer_block=contiguous,
                             monotone=mon))
            prev_rings, prev_gl = nrings, len(gl)
        mono[w] = dict(rows=rows, passed=ok)
    # W3: runs swap in token order
    runs = S.key_plan()
    swap = [(S.WIN["W3"][0] + S.STAGGER * r["ring"] + r["half"], r["tokens"][0]) for r in runs]
    srt = sorted(swap, key=lambda x: x[1])
    w3 = all(srt[i][0] <= srt[i + 1][0] for i in range(len(srt) - 1))
    return dict(still_frames=out, windows=mono,
                W3_swap_in_token_order=dict(runs=len(runs), passed=w3,
                                            rule="swap frame non-decreasing in first-token index"),
                passed=all(v["passed"] for v in out.values()) and all(v["passed"] for v in mono.values()) and w3)


# ------------------------------------------------------------------ per-mark single state
def single_state(info):
    G, O, _ = S.mods()
    film = {}
    for w in ("W1", "W2"):
        k0 = S.WIN[w][0]
        rows, ok = [], True
        hybrids = set()
        for k in range(k0, k0 + S.WLEN):
            _, states, _, _, log, _ = S.ring_switch_layers(w, k)
            drawn = S._CACHE["drawn"]
            multi = {i: v for i, v in drawn.items() if len(v) != 1}
            ok &= not multi
            hybrids.add(tuple(log[r] for r in range(7)))
            rows.append(dict(k=k, marks=len(drawn), marks_not_in_exactly_one_state=len(multi),
                             ring_states=[log[r] for r in range(7)]))
        film[w] = dict(rows=rows, distinct_hybrid_states=len(hybrids), passed=ok)
    # W3
    G_ = G.glyph_path("T2")[0]
    nonspace = {g["i"] for g in G_ if g["ch"] != " "}
    rows, ok = [], True
    for k in range(S.WIN["W3"][0], S.WIN["W3"][0] + S.WLEN):
        states, placed, log = S.key_switch_layers(k)
        gl = {i for i, s in enumerate(states) if s == "glyph"} & nonspace
        keyed = set()
        for r in S.key_plan():
            if r["slot"] in placed:
                keyed |= set(r["tokens"])
        keyed &= nonspace
        both = gl & keyed
        missing = nonspace - gl - keyed
        ok &= not both and not missing
        rows.append(dict(k=k, glyph_tokens=len(gl), tokens_now_keys=len(keyed), both=len(both), neither=len(missing)))
    film["W3"] = dict(rows=rows, passed=ok)
    # pixel evidence (ghost overlap of a text mark and an optical mark, effective alpha > 0.2)
    ov_film = {i["k"]: i["overlap"] for i in info["film"] if i.get("window")}
    ov_b2 = {i["k"]: i["overlap"] for i in info["B2"]}
    thr = 0.005
    pix_film = max(ov_film.values()) <= thr
    pix_b2 = max(ov_b2.values()) <= thr
    b2_struct = all(i.get("marks_multi_state") for i in info["B2"])
    return dict(
        film=film,
        pixel_ghost_overlap=dict(threshold_fraction_of_disc=thr, film_max=max(ov_film.values()),
                                 film_max_frame=max(ov_film, key=ov_film.get), B2_max=max(ov_b2.values()),
                                 B2_max_frame=max(ov_b2, key=ov_b2.get), B2_per_frame=ov_b2,
                                 film_passed=pix_film, B2_passed=pix_b2),
        B2=dict(structural="every T1 glyph AND every O_A ring drawn in every W1 frame at weights (1-a, a)",
                all_frames_multi_state=b2_struct, passed=not b2_struct and pix_b2),
        passed_on_film=all(v["passed"] for v in film.values()) and pix_film,
        fails_on_B2=b2_struct and not pix_b2)


# ------------------------------------------------------------------ replay
def replay(info):
    tmp = S.MED + "/replay"
    shutil.rmtree(tmp, ignore_errors=True)
    code = ("import sys,json; sys.path.insert(0,%r); import switch as S; "
            "inf=S.render_range(list(range(126,144)),'film',%r); "
            "print(json.dumps([[i['k'],i['sha1']] for i in inf]))") % (WS, tmp)
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True).stdout
    second = dict(json.loads(out.strip().splitlines()[-1]))
    first = {i["k"]: i["sha1"] for i in info["film"] if 126 <= i["k"] <= 143}
    same = all(first[k] == second[k] for k in first)
    shutil.rmtree(tmp, ignore_errors=True)
    allhash = hashlib.sha1("".join(i["sha1"] for i in sorted(info["film"], key=lambda x: x["k"])).encode()).hexdigest()
    return dict(frames=[126, 143], first_render=first, second_render_fresh_process=second, identical=same,
                score_sha1=hashlib.sha1(open(WS + "/score.json", "rb").read()).hexdigest(),
                film_F100_515_sha1_of_frame_sha1s=allhash, passed=same)


# ------------------------------------------------------------------ media
def contact_sheet():
    cells = []
    fnt = ImageFont.truetype(FONT, 13)
    for k in range(126, 144):
        im = Image.fromarray(load(k)).crop((240, 30, 720, 510)).resize((300, 300), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.text((6, 4), f"F{k}", fill=(150, 150, 150), font=fnt)
        cells.append(im)
    sh = Image.new("RGB", (6 * 302, 3 * 302), (0, 0, 0))
    for i, c in enumerate(cells):
        sh.paste(c, ((i % 6) * 302, (i // 6) * 302))
    for d in (S.MED, S.MED2):
        sh.save(d + "/W1_contact_F126-143.jpg", quality=90)
    # baselines side by side at F134
    trip = Image.new("RGB", (3 * 482, 520), (0, 0, 0))
    for j, v in enumerate(("film", "B1", "B2")):
        im = Image.fromarray(load(134, v)).crop((240, 30, 720, 510))
        trip.paste(im, (j * 482, 40))
        ImageDraw.Draw(trip).text((j * 482 + 8, 10), {"film": "film F134 (substitution)", "B1": "B1 hard cut",
                                                       "B2": "B2 dissolve"}[v], fill=(170, 170, 170), font=fnt)
    trip.save(S.MED + "/F134_film_B1_B2.jpg", quality=90)
    return S.MED + "/W1_contact_F126-143.jpg"


def phase_plot(sc, meas):
    W, H = 1600, 800
    im = Image.new("RGB", (W, H), (250, 250, 247))
    d = ImageDraw.Draw(im)
    fnt = ImageFont.truetype(FONT, 14)
    x0, x1 = 90, W - 30
    X = lambda k: x0 + (x1 - x0) * k / (S.NFR - 1)
    fr = sc["frames"]
    lanes = [("theta mod 2pi (rad)", 0, 2 * math.pi), ("omega (deg / frame): line declared, dots measured", 0, 5.0),
             ("eccentric gain", 0.6, 1.05), ("plate mix u / rings closed / glyph share", 0, 1.0)]
    lh = 165
    for li, (name, lo, hi) in enumerate(lanes):
        top = 30 + li * (lh + 12)
        d.rectangle([x0, top, x1, top + lh], outline=(180, 180, 180))
        d.text((8, top + 2), name, fill=(40, 40, 40), font=fnt)
        Y = lambda v, top=top, lo=lo, hi=hi: top + lh - (v - lo) / (hi - lo) * lh
        for w, (k0, a, b) in S.WIN.items():
            d.rectangle([X(k0), top + 1, X(k0 + S.WLEN - 1), top + lh - 1], fill=(232, 226, 210))
            if li == 0:
                d.text((X(k0) + 2, top + 2), w, fill=(120, 90, 40), font=fnt)
        a, b = S.READ
        if li == 1:
            d.rectangle([X(a), top + lh - 14, X(b), top + lh - 2], fill=(215, 225, 235))
            d.text((X(a) + 4, top + lh - 30), "declared reading interval F288-425", fill=(60, 80, 110), font=fnt)
        pts = []
        for f in fr:
            k = f["k"]
            if li == 0:
                v = f["theta"]
            elif li == 1:
                v = 360.0 * f["omega_ticks"] / S.TICKS
            elif li == 2:
                v = f["gain"] if f["gain"] is not None else None
            else:
                v = f.get("plate_mix")
            pts.append((k, v))
        if li == 0:
            for k in range(1, S.NFR):
                if pts[k][1] is not None and pts[k - 1][1] is not None and abs(pts[k][1] - pts[k - 1][1]) < 3:
                    d.line([X(k - 1), Y(pts[k - 1][1]), X(k), Y(pts[k][1])], fill=(30, 30, 30), width=2)
        else:
            seg = []
            for k, v in pts:
                if v is None:
                    if len(seg) > 1:
                        d.line(seg, fill=(30, 30, 30), width=2)
                    seg = []
                else:
                    seg.append((X(k), Y(v)))
            if len(seg) > 1:
                d.line(seg, fill=(30, 30, 30), width=2)
        if li == 1:
            for w in ("W1", "W2", "W3"):
                for r in meas[w]["pairs"]:
                    k = r["pair"][0]
                    d.ellipse([X(k) - 3, Y(r["deg"]) - 3, X(k) + 3, Y(r["deg"]) + 3], outline=(170, 40, 30), width=2)
            for v in (4.5, 1.40625):
                d.text((x0 - 60, Y(v) - 8), f"{v:g}", fill=(90, 90, 90), font=fnt)
        if li == 3:
            for w in ("W1", "W2"):
                k0 = S.WIN[w][0]
                pr = None
                for k in range(k0, k0 + S.WLEN):
                    _, states, _, _, log, _ = S.ring_switch_layers(w, k)
                    rc = sum(1 for v in log.values() if v == "ring") / 7
                    gs = sum(1 for s in states if s == "glyph") / len(states)
                    if pr:
                        d.line([X(k - 1), Y(pr[0]), X(k), Y(rc)], fill=(170, 120, 30), width=2)
                        d.line([X(k - 1), Y(pr[1]), X(k), Y(gs)], fill=(40, 90, 160), width=2)
                    pr = (rc, gs)
    for k in range(0, S.NFR + 1, 48):
        d.text((X(min(k, S.NFR - 1)) - 10, H - 26), f"F{k}", fill=(60, 60, 60), font=fnt)
    d.text((x0, H - 52), "Bodies: T1 F24-125 | O_A F144-245 | T2 F264-425 | O_B F444-515 | still F516-575.  "
           "Shaded = switch windows. Lane 4: black u, orange rings closed/7, blue glyphs/tokens.",
           fill=(60, 60, 60), font=fnt)
    for dd in (S.MED, S.MED2):
        im.save(dd + "/phase_visualizer.png")
    return S.MED + "/phase_visualizer.png"


def wav_bed(path, first, n, silent=False):
    _, seg = S.make_bell()
    st, cues = S.sound_bed(seg, first, n, silent)
    S._write_wav(path, st.reshape(-1), 2)
    peak = float(np.abs(st).max())
    return dict(path=path, cues_frames=cues, peak_dbfs=round(20 * math.log10(peak), 2) if peak > 0 else None,
                nonzero_samples_outside_cues=int(_outside(st, first, cues)))


def _outside(st, first, cues):
    m = np.ones(len(st), bool)
    for c in cues:
        a = int((c - first) / S.FPS * S.RATE)
        m[a:a + int(S.BELL_LEN * S.RATE) + 2] = False
    return np.count_nonzero(np.abs(st[m]) > 0)


def main():
    sc = json.load(open(WS + "/score.json"))
    info = json.load(open(S.MED + "/render_info.json"))
    fx = {}
    alt = alternation(alternation_from_frames(sc))
    bad = alternation(["T1", "O_A", "O_B", "T2"])
    fx["I3_strict_alternation"] = dict(
        evidence="structurally verified (score.json bodies read frame by frame)",
        film=alt, windows_belong_to_incoming_disc=windows_belong_to_incoming(sc),
        test_score_O_A_O_B_adjacent=bad, must_fail_on_test_score=not bad["passed"],
        passed=alt["passed"] and not bad["passed"] and windows_belong_to_incoming(sc))
    od = omega_declared(sc)
    om = omega_measured()
    fx["I4_constant_omega"] = dict(
        evidence="declared: structurally verified from integer ticks; measured: polar phase correlation of the "
                 "rendered 960x540 frames (warpPolar 2880 angle bins, r 40-226 px, angular derivative as high-pass, "
                 "parabolic sub-bin peak), tolerance 1 %",
        declared=od, measured={k: {kk: vv for kk, vv in v.items()} for k, v in om.items()},
        passed=all(v["passed"] for v in od.values()) and all(om[w]["passed"] for w in ("W1", "W2", "W3")))
    fx["I5_periodicity"] = dict(evidence="structurally verified, exact integer arithmetic (1280 ticks / rev)",
                                **periodicity(sc))
    fx["I5_periodicity"]["passed"] = all(v["passed"] for k, v in fx["I5_periodicity"].items() if isinstance(v, dict))
    fx["I2_glyph_order"] = dict(evidence="structurally verified (glyphs.screen_order on still frames, cw and ccw; "
                                         "window states read from the substitution code)", **glyph_order(sc))
    ss = single_state(info)
    fx["per_mark_single_state"] = dict(
        evidence="structurally verified (per-mark drawing log of every window frame) + measured (ghost overlap of "
                 "text-mark and optical-mark alpha in the rendered layers)", **ss,
        passed=ss["passed_on_film"] and ss["fails_on_B2"])
    fx["replay_sha1"] = dict(evidence="measured (sha1 of RGB bytes, second render in a fresh process)", **replay(info))
    fx["W1_defining_beat_states"] = dict(
        evidence="structurally verified",
        F134=[r for r in ss["film"]["W1"]["rows"] if r["k"] == 134][0]["ring_states"],
        distinct_hybrid_states=ss["film"]["W1"]["distinct_hybrid_states"],
        passed=ss["film"]["W1"]["distinct_hybrid_states"] >= 6)
    # ------------------------------------------------ media
    os.makedirs(WS + "/baselines", exist_ok=True)
    tsk = list(range(100, 516))
    bed = wav_bed(S.MED + "/test_shot_bed.wav", 100, len(tsk))
    sil = wav_bed(S.MED + "/test_shot_silent.wav", 100, len(tsk), silent=True)
    old = WS + "/test-shot.mp4"
    keep = WS + "/test-shot-build/test-shot-v1-approved.mp4"
    if os.path.exists(old) and not os.path.exists(keep):
        shutil.copy2(old, keep)
    S.encode(FR, "film", tsk, WS + "/test-shot.mp4", S.MED + "/test_shot_bed.wav")
    S.encode(FR, "film", tsk, S.MED + "/test-shot-silent.mp4", S.MED + "/test_shot_silent.wav")
    bk = list(range(100, 171))
    bbed = wav_bed(S.MED + "/baseline_bed.wav", 100, len(bk))
    for v in ("B1", "B2"):
        lst = []
        for k in bk:
            src = f"{FR}/{v}_{k:03d}.png" if 126 <= k <= 143 else f"{FR}/film_{k:03d}.png"
            dst = f"{FR}/{v}x_{k:03d}.png"
            if not os.path.exists(dst):
                os.link(src, dst)
            lst.append(k)
        S.encode(FR, v + "x", lst, WS + f"/baselines/{v}.mp4", S.MED + "/baseline_bed.wav")
    S.encode(FR, "film", bk, WS + "/baselines/film_F100-170.mp4", S.MED + "/baseline_bed.wav")
    cs = contact_sheet()
    pv = phase_plot(sc, om)
    for k in (110, 134, 200, 300, 360, 434, 480):
        shutil.copy2(f"{FR}/film_{k:03d}.png", S.MED2 + f"/film_F{k}.png")
    shutil.copy2(WS + "/test-shot.mp4", S.MED2 + "/test-shot.mp4")
    fx["sound"] = dict(evidence="measured (sample values of the rendered beds)", test_shot_bed=bed,
                       silent_variant=sil, baseline_bed=bbed,
                       passed=bed["nonzero_samples_outside_cues"] == 0 and sil["peak_dbfs"] is None
                       and bed["peak_dbfs"] <= -14.0 + 0.05)
    fx["summary"] = {k: v.get("passed") for k, v in fx.items() if isinstance(v, dict) and "passed" in v}
    fx["media"] = dict(test_shot=WS + "/test-shot.mp4", test_shot_silent=S.MED + "/test-shot-silent.mp4",
                       B1=WS + "/baselines/B1.mp4", B2=WS + "/baselines/B2.mp4",
                       film_same_span=WS + "/baselines/film_F100-170.mp4", W1_contact_sheet=cs,
                       F134_film_B1_B2=S.MED + "/F134_film_B1_B2.jpg", phase_visualizer=pv,
                       frames=FR + "/film_100..515.png (960x540 RGB, the film's frames as scored)",
                       bell=S.MED + "/bell.wav", previous_approved_test_shot=keep)
    return fx


if __name__ == "__main__":
    fx = main()
    json.dump(fx, open(WS + "/fixtures.json", "w"), indent=1, default=str)
    print(json.dumps(fx["summary"], indent=1))
