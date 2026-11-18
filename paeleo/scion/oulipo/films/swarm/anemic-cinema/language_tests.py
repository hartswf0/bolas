"""U2 language unit: reading-speed study, aesthetic measurements beside spiralTextPom, still pass.

Run: python3 -I language_tests.py            (renders clips + sheets, writes results into glyphpaths.json)
     python3 -I language_tests.py --nomedia  (simulation and measurements only)

Reading model (structural; the perceptual part is my own frame-by-frame look, labelled as such):
  a reader reads the T2 disc aloud at rho chars/s, token after token along the GlyphPath, starting at a
  half-separator of their choosing at a time of their choosing inside the declared reading interval;
  a token read at time t sits at screen angle a = phi_i - theta(t) (image coords, cw positive), and its
  letter's 'up' is the outward normal, so its tilt from upright is a + 90 deg.
  |tilt| <= 60: upright; 60-110: rotated, readable with effort; > 110: inverted = reading position lost.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/anemic-cinema")
import glyphs as G  # noqa: E402

FPS = 24
OUT = G.MED
PREP = ("/home/user/bolas/paeleo/scion/oulipo/films/sources/anemic-cinema/language-language-agent-and-glyph-"
        "layout-owns-the-two-original-puns-glyphpath-text-discs-t1-and-t2-reading-speed-still-pass-layout-")
REF = "/home/user/bolas/paeleo/scion/oulipo/assets/references/spiralTextPom.webp"
K_READ = 288                               # declared reading interval starts at F288 (plan section 6)


def theta_at_288():
    """Plate angle at F288: from score.json if U3 has published it, else the plan's placeholder."""
    p = G.WS + "/score.json"
    if os.path.exists(p):
        try:
            sc = json.load(open(p))
            fr = sc.get("frames") or sc.get("exposure") or sc
            for f in fr:
                if int(f.get("k", -1)) == K_READ:
                    return float(f["theta"]), "score.json"
        except Exception:
            pass
    # placeholder: F24..263 at 1/80 (3 whole revolutions), F264..287 easing 1/80 -> 1/256
    rev = sum(1 / 80 + (1 / 256 - 1 / 80) * ((j + 0.5) / 24) for j in range(24))
    return 2 * math.pi * (rev % 1.0), "plan placeholder (score.json absent)"


TH0, TH_SRC = G.THETA_READ, G.THETA_READ_SOURCE
OMEGA_READ = 1 / 128                       # chosen reading speed (see glyphpaths.json reading_speed)
VARIANTS = {
    "A_256_5.75s": dict(omega=1 / 256, seconds=5.75),
    "B_384_5.75s": dict(omega=1 / 384, seconds=5.75),
    "C_256_8.0s": dict(omega=1 / 256, seconds=8.0),
    "D_128_7.0s": dict(omega=1 / 128, seconds=7.0),   # added after the simulated sweep: the 12 o'clock feed rate
}


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def _halves(pun):
    """(start token, end token exclusive, text) of every half laid on the disc, in order."""
    text = G.disc_text(pun)
    out, i0 = [], 0
    for part in text.split(G.SEP):
        out.append((i0, i0 + len(part), part))
        i0 += len(part) + len(G.SEP)
    return out


def _read_half(path, h, t0, omega, rho):
    a0, a1, _ = h
    tilts = []
    for q, i in enumerate(range(a0, a1)):
        t = t0 + q / rho
        th = TH0 + 2 * math.pi * omega * t * FPS
        if path[i]["ch"] != " ":
            tilts.append(math.degrees(wrap(path[i]["phi"] - th + math.pi / 2)))
    turns = sorted({path[i]["turn"] for i in range(a0, a1)})
    return tilts, t0 + (a1 - a0) / rho, turns


def simulate(pun, omega, seconds, rho, allow_jump, pause=0.35):
    """Best reading of the pun (first half, then second half) inside the interval.
    allow_jump=False: one contiguous run along the spiral (half A, separator, the B that follows it).
    allow_jump=True: after half A the reader may re-anchor (one saccade during a 0.35 s pause at the
    separator) on ANY copy of half B on the disc - the disc carries A.B.A.B, so B is offered on several turns."""
    path, _ = G.glyph_path(pun)
    hs = _halves(pun)
    A, B = [x.strip() for x in G.PUNS[pun].split(G.SEP.strip())]
    nfr = int(round(seconds * FPS))
    best = None
    for ia, ha in enumerate(hs):
        if ha[2] != A:
            continue
        for f0 in range(nfr):
            t0 = f0 / FPS
            ta, t1, turns_a = _read_half(path, ha, t0, omega, rho)
            cands = [hb for hb in hs if hb[2] == B and (allow_jump or hb[0] == ha[1] + len(G.SEP))]
            for hb in cands:
                tb_start = t1 + (pause if allow_jump else len(G.SEP) / rho)
                tb, t2, turns_b = _read_half(path, hb, tb_start, omega, rho)
                if t2 > seconds:
                    continue
                til = ta + tb
                inv = sum(1 for x in til if abs(x) > 110)
                key = (inv, max(abs(x) for x in til))
                if best is None or key < best[0]:
                    lost = [q for q, x in enumerate(til) if abs(x) > 110]
                    best = (key, dict(
                        start_s=round(t0, 2), ends_s=round(t2, 2),
                        first_half_tokens=[ha[0], ha[1]], first_half_turns=turns_a,
                        second_half_tokens=[hb[0], hb[1]], second_half_turns=turns_b,
                        jumped=hb[0] != ha[1] + len(G.SEP),
                        max_tilt_deg=round(key[1], 1), inverted_letters=inv,
                        letters_beyond_60deg=sum(1 for x in til if abs(x) > 60),
                        first_inverted_letter=None if not lost else lost[0]))
    if best is None:
        return dict(feasible=False, reason="the pun at %.0f chars/s (%.2f s + pause) does not fit the %.2f s interval"
                    % (rho, len(G.PUNS[pun]) / rho, seconds))
    out = best[1]
    out["feasible"] = out["inverted_letters"] == 0
    letters = [c for c in G.PUNS[pun] if c not in " \u00b7"]
    if out["first_inverted_letter"] is not None:
        q = out["first_inverted_letter"]
        out["position_lost_near"] = "".join(letters[max(0, q - 2):q + 4])
    return out


def motion(omega):
    path, _ = G.glyph_path("T2")
    rs = [path[0]["r"] / G.SS, path[len(path) // 2]["r"] / G.SS, path[-1]["r"] / G.SS]
    return dict(deg_per_s=360 * omega * FPS,
                outer_px_per_s=2 * math.pi * rs[0] * omega * FPS,
                outer_blur_px_180deg=2 * math.pi * rs[0] * omega * 0.5,
                mid_blur_px=2 * math.pi * rs[1] * omega * 0.5,
                chars_per_s_past_12_outer=2 * math.pi * rs[0] * omega * FPS / (path[0]["adv"] / G.SS),
                stroke_px_1x=round(G.CAP / G.SS * 0.16, 2))


def frame(pun, k_off, omega, still=False):
    th = TH0 + 2 * math.pi * omega * k_off
    L, A, _ = G.render_text(pun, th, omega=None if still else omega)
    return G.to_1x(L)


def render_clip(name, omega, seconds):
    nfr = int(round(seconds * FPS))
    d = OUT + "/reading_" + name
    os.makedirs(d, exist_ok=True)
    for k in range(nfr):
        Image.fromarray(frame("T2", k, omega)).save(d + "/f_%04d.png" % k)
    mp4 = OUT + "/reading_%s.mp4" % name
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", d + "/f_%04d.png",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", mp4], check=True)
    # contact sheet: every 12 frames (0.5 s), 4 columns, 480 px wide cells
    idx = list(range(0, nfr, 12))
    cw, ch = 480, 270
    cols = 4
    rows = (len(idx) + cols - 1) // cols
    sheet = Image.new("L", (cols * cw, rows * (ch + 18)), 0)
    dr = ImageDraw.Draw(sheet)
    for q, k in enumerate(idx):
        im = Image.open(d + "/f_%04d.png" % k).convert("L").resize((cw, ch), Image.LANCZOS)
        x, y = (q % cols) * cw, (q // cols) * (ch + 18)
        sheet.paste(im, (x, y))
        dr.text((x + 6, y + ch + 2), "%s  +%.1f s  (F%d)" % (name, k / FPS, K_READ + k), fill=200)
    sheet.save(OUT + "/reading_%s_sheet.jpg" % name, quality=88)
    return mp4


def measure(img):
    a = np.asarray(img).astype(np.float32)
    Lm = a.mean(axis=2) if a.ndim == 3 else a
    h, w = Lm.shape
    cx, cy, R = w / 2, h / 2, 232
    def samp(dx, dy):
        x, y = int(cx + dx * R), int(cy + dy * R)
        p = Lm[y - 3:y + 4, x - 3:x + 4]
        return float(np.median(p))
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - cx, yy - cy)
    inside = rr < R - 3
    letters = inside & (Lm > 220)
    corner = Lm[:30, :30]
    rb = (a[..., 0] - a[..., 2])[inside] if a.ndim == 3 else np.zeros(1)
    return dict(field_corner_L=float(corner.mean()), field_noise_sigma=float(corner.std()),
                plate_top=samp(0, -0.85), plate_upper_left=samp(-0.6, -0.6), plate_centre_ring=samp(0.0, -0.05),
                plate_lower_right=samp(0.6, 0.6), plate_bottom=samp(0, 0.85),
                plate_mean_abs_R_minus_B=float(np.abs(rb).mean()),
                letter_px_L_p10_p50_p90=[float(x) for x in np.percentile(Lm[letters], [10, 50, 90])] if letters.any() else None,
                disc_height_frac=2 * R / h)


def compare_sheet(frames, path):
    ref = Image.open(REF).convert("RGB")
    H = 540
    rw = int(ref.width * H / ref.height)
    ref = ref.resize((rw, H), Image.LANCZOS)
    W = rw + 960 + 12
    sheet = Image.new("RGB", (W, H * len(frames) + 22 * len(frames)), (0, 0, 0))
    dr = ImageDraw.Draw(sheet)
    for q, (lab, im) in enumerate(frames):
        y = q * (H + 22)
        sheet.paste(ref, (0, y))
        sheet.paste(Image.fromarray(im).convert("RGB"), (rw + 12, y))
        dr.text((6, y + H + 4), "reference: spiralTextPom.webp (Centre Pompidou), for comparison only", fill=(160, 160, 160))
        dr.text((rw + 18, y + H + 4), lab, fill=(200, 200, 200))
    sheet.save(path, quality=90)


def still_pass(omega):
    """F360 frozen full size, then F360-362 stacked as a plain strip (no sprockets): spec + preview."""
    ks = [360, 361, 362]
    fr = {k: frame("T2", k - K_READ, omega) for k in ks}   # same pixels as in motion (shutter on)
    Image.fromarray(fr[360]).save(OUT + "/still_F360.png")
    cell_h = 175
    cell_w = int(round(960 * cell_h / 540))                 # 311
    gap = 4
    strip = Image.new("L", (960, 540), 2)
    top = (540 - (3 * cell_h + 2 * gap)) // 2
    x0 = (960 - cell_w) // 2
    for q, k in enumerate(ks):
        im = Image.fromarray(fr[k]).resize((cell_w, cell_h), Image.LANCZOS)
        strip.paste(im, (x0, top + q * (cell_h + gap)))
    strip.save(OUT + "/still_strip_F360-362.png")
    for k in ks:
        Image.fromarray(fr[k]).save(PREP + "/still_F%d.png" % k)
    strip.save(PREP + "/still_strip_F360-362.png")
    return dict(
        part1=dict(film_frames="F516-551 (1.5 s)", shows="F360 of T2 frozen at 960x540, the identical pixels of the moving "
                   "frame (same theta, same 180-degree shutter integration); no zoom, no grade change"),
        part2=dict(film_frames="F552-575 (1.0 s)", shows="F360, F361, F362 stacked top to bottom as a plain vertical strip, "
                   "each scaled to %dx%d (INTER_AREA/LANCZOS downscale of the real frames), %d px black gaps, "
                   "centred at x=%d, top y=%d on the L=2 field; no sprocket holes, no edge printing, no frame lines, "
                   "no grain" % (cell_w, cell_h, gap, x0, top),
                   cells=[dict(k=k, x=x0, y=top + q * (cell_h + gap), w=cell_w, h=cell_h) for q, k in enumerate(ks)]),
        theta_source=TH_SRC, omega_read=omega,
        note="theta(F360) must be taken from score.json at assembly; the preview files here use %s" % TH_SRC,
        preview_files=[OUT + "/still_F360.png", OUT + "/still_strip_F360-362.png"])


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PREP, exist_ok=True)
    media = "--nomedia" not in sys.argv
    res = dict(theta_F288=TH0, theta_source=TH_SRC, model=__doc__.split("Reading model")[1].strip(), variants={})
    for name, v in VARIANTS.items():
        r = dict(omega_rev_per_frame=v["omega"], seconds=v["seconds"], motion=motion(v["omega"]),
                 reader={})
        for rho in (10, 13):
            for jump in (False, True):
                r["reader"]["%d_chars_per_s_%s" % (rho, "reanchor" if jump else "contiguous")] = \
                    simulate("T2", v["omega"], v["seconds"], rho, jump)
        if media and "--stills" not in sys.argv:
            r["clip"] = render_clip(name, v["omega"], v["seconds"])
            r["sheet"] = OUT + "/reading_%s_sheet.jpg" % name
        res["variants"][name] = r
        print(name, {a: (b.get("inverted_letters"), b.get("max_tilt_deg"), b.get("position_lost_near"), b.get("first_half_turns"), b.get("second_half_turns")) for a, b in r["reader"].items()})
    # simulation-only sweep (not rendered), to see which way the optimum lies
    res["sweep_simulated_only"] = {}
    for secs in (5.75, 7.0):
        for P in (80, 96, 112, 128, 144, 160, 192, 256, 320, 384):
            res["sweep_simulated_only"]["1/%d @ %.2f s" % (P, secs)] = {
                "%d_%s" % (rho, "reanchor" if j else "contig"): (lambda d: dict(feasible=d.get("feasible"),
                    inverted=d.get("inverted_letters"), max_tilt=d.get("max_tilt_deg")))(simulate("T2", 1 / P, secs, rho, j))
                for rho in (10, 13) for j in (False, True)}
    for k, v in res["sweep_simulated_only"].items():
        print(k, {a: (b["inverted"], b["max_tilt"]) for a, b in v.items()})
    meas = {}
    if media:
        t1 = G.to_1x(G.render_text("T1", 2 * math.pi * 0.3, omega=1 / 80)[0])
        t2 = frame("T2", 360 - K_READ, OMEGA_READ)
        Image.fromarray(t1).save(OUT + "/T1_frame_omega80.png")
        Image.fromarray(t2).save(OUT + "/T2_frame_F360.png")
        meas = dict(T1_at_omega_fast=measure(Image.fromarray(t1).convert("RGB")),
                    T2_F360=measure(Image.fromarray(t2).convert("RGB")),
                    reference_spiralTextPom_note="sampled values for the reference are in plan.md section 9")
        compare_sheet([("T2 F360 at the chosen 1/128 rev/frame, 180-degree shutter (U2 glyphs.py)", t2),
                       ("T1 at 1/80 rev/frame, 180-degree shutter (U2 glyphs.py)", t1)],
                      OUT + "/T2_T1_beside_spiralTextPom.jpg")
        res["still_pass"] = still_pass(OMEGA_READ)
        Image.fromarray(t1).save(PREP + "/T1_frame_omega80.png")
        Image.fromarray(t2).save(PREP + "/T2_frame_F360.png")
    res["measurements"] = meas
    json.dump(res, open(OUT + "/reading_results.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(meas, indent=1))
