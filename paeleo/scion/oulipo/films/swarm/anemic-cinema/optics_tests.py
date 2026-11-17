"""U1 depth tests and groove-aliasing measurement for optics.py.

  python3 -I optics_tests.py alias     groove aliasing, 100x100 px crop, 3 pitches x 2 speeds
  python3 -I optics_tests.py depth     4 s test clips (96 frames, 0.30 rev/s) per profile
  python3 -I optics_tests.py stills    reference stills + section 9 measurements
Media -> films/sources/anemic-cinema/optics/ ; numbers -> optics/tests.json (merged into the
ledger by hand). Clock: theta_k = 2*pi*k/80 (omega_fast, integer clock as in score.json);
omega_read = 1/256 rev/frame.
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/anemic-cinema")
import optics as O  # noqa: E402

MED = O.MED
TJ = MED + "/tests.json"
FAST, READ = 1 / 80, 1 / 256


def tests_load():
    return json.load(open(TJ)) if os.path.exists(TJ) else {}


def tests_save(d):
    json.dump(d, open(TJ, "w"), indent=1)


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- aliasing
def area(img, f):
    h, w = img.shape
    return img.reshape(h // f, f, w // f, f).mean(axis=(1, 3))


def alias():
    x0, y0, w, h = 610, 170, 100, 100        # 1x crop over rings 1-4 on the upper right
    out = {}
    for pitch in (1.5, 2.5, 3.5):
        for name, om in (("0.30rev_s", FAST), ("0.09375rev_s", READ)):
            errs, gc2, gct, flick2, flickt = [], [], [], [], []
            prev2 = prevt = None
            for k in range(12):
                th = 2 * math.pi * om * k
                L2, A2 = O._rings_region(x0, y0, w, h, 2, th, 1.0, omega=om, groove=pitch)
                Lt, At = O._rings_region(x0, y0, w, h, 8, th, 1.0, omega=om, groove=pitch)
                i2 = cv2.resize(L2 * A2, (w, h), interpolation=cv2.INTER_AREA)
                it = area(Lt * At, 8)
                inner = cv2.erode((area(At, 8) > 0.99).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
                errs.append(float(np.sqrt(np.mean((i2 - it)[inner] ** 2))))
                hp2 = i2 - cv2.GaussianBlur(i2, (0, 0), 2.0)
                hpt = it - cv2.GaussianBlur(it, (0, 0), 2.0)
                gc2.append(float(hp2[inner].std()))
                gct.append(float(hpt[inner].std()))
                if prev2 is not None:
                    flick2.append(float(np.abs(i2 - prev2)[inner].mean()))
                    flickt.append(float(np.abs(it - prevt)[inner].mean()))
                prev2, prevt = i2, it
                if k == 0:
                    big = np.concatenate([i2, np.full((h, 4), 255, np.float32), it], axis=1)
                    big = cv2.resize(np.clip(big, 0, 255).astype(np.uint8), None, fx=4, fy=4,
                                     interpolation=cv2.INTER_NEAREST)
                    cv2.imwrite(f"{MED}/alias_crop_p{pitch}_{name}.png", big)
            out[f"pitch{pitch}_{name}"] = dict(
                groove_pitch_1x=pitch, omega_rev_per_frame=om,
                alias_rmse_L_vs_8x_truth=round(float(np.mean(errs)), 2),
                groove_contrast_1x_render=round(float(np.mean(gc2)), 2),
                groove_contrast_1x_truth=round(float(np.mean(gct)), 2),
                frame_to_frame_change_render=round(float(np.mean(flick2)), 2),
                frame_to_frame_change_truth=round(float(np.mean(flickt)), 2))
            print(pitch, name, out[f"pitch{pitch}_{name}"])
    d = tests_load()
    d["alias"] = dict(crop_1x_xywh=[x0, y0, w, h], frames=12, gain=1.0,
                      method="2x render (the film) area-downsampled vs 8x analytic render of the same "
                             "shutter-integrated rotation, inside the ring interiors; groove contrast = std "
                             "of the high-pass (L - gauss2) at 1x; crops saved x4 nearest (left = film, "
                             "right = truth)",
                      results=out)
    tests_save(d)


# ---------------------------------------------------------------- depth clips
PROFILES = {
    "OA_rise_locked": dict(disc="A", g=lambda j: 0.7 + 0.3 * smooth(j / 95), detune=0.0),
    "OA_fall_locked": dict(disc="A", g=lambda j: 1.0 - 0.3 * smooth(j / 95), detune=0.0),
    "OA_rise_detuned2": dict(disc="A", g=lambda j: 0.7 + 0.3 * smooth(j / 95), detune=0.02),
    "OB_fall_locked": dict(disc="B", g=lambda j: 1.0 - 0.3 * smooth(j / 95), detune=0.0),
    "OB_rise_locked": dict(disc="B", g=lambda j: 0.7 + 0.3 * smooth(j / 95), detune=0.0),
    "OB_fall_detuned2": dict(disc="B", g=lambda j: 1.0 - 0.3 * smooth(j / 95), detune=0.02),
}
_PL = {}


def frame_job(args):
    prof, j = args
    p = PROFILES[prof]
    th = 2 * math.pi * j / 80           # unwrapped (needed by the detuned orbit)
    g = p["g"](j)
    if p["disc"] not in _PL:
        _PL[p["disc"]] = O.plate(p["disc"])[0]
    if p["disc"] == "A":
        ly = O.render_rings(th, g, omega=FAST, detune=p["detune"])
    else:
        ly = O.render_keys(th, g, omega=FAST, detune=p["detune"])
    im = O.compose(_PL[p["disc"]], [ly], warm=True)
    d = f"{MED}/depth/{prof}"
    Image.fromarray(im).save(f"{d}/f{j:03d}.png")
    return j


def depth(names=None):
    names = names or list(PROFILES)
    jobs = []
    for prof in names:
        os.makedirs(f"{MED}/depth/{prof}", exist_ok=True)
        jobs += [(prof, j) for j in range(96)]
    with Pool(4) as pool:
        for _ in pool.imap_unordered(frame_job, jobs, chunksize=4):
            pass
    d = tests_load()
    d.setdefault("depth", {})
    for prof in names:
        mp4 = f"{MED}/depth_{prof}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i",
                        f"{MED}/depth/{prof}/f%03d.png", "-c:v", "libx264", "-crf", "17",
                        "-pix_fmt", "yuv420p", mp4], check=True)
        d["depth"][prof] = dict(clip=mp4, frames=96, rev_per_s=0.30,
                                gain_first_last=[round(PROFILES[prof]["g"](0), 3),
                                                 round(PROFILES[prof]["g"](95), 3)],
                                detune=PROFILES[prof]["detune"])
    tests_save(d)


# ---------------------------------------------------------------- stills + section 9 numbers
def measure(im):
    """Section 9 numbers on a 960x540 RGB optical frame."""
    a = im.astype(np.float32)
    L = a.mean(axis=2)
    corners = float(np.mean([L[:20, :20].mean(), L[:20, -20:].mean(), L[-20:, :20].mean(), L[-20:, -20:].mean()]))
    rows = np.nonzero((L > 8).any(axis=1))[0]
    ring = (L > 90) & (L < 175)
    rb = (a[..., 0] - a[..., 2])[ring]
    # radial scan along screen x through the centre row (both sides)
    line = L[270, :]
    runs = []
    cur, n = None, 0
    for v in line[250:711]:
        s = v > 75
        if s == cur:
            n += 1
        else:
            if cur is not None:
                runs.append((bool(cur), n))
            cur, n = s, 1
    runs.append((bool(cur), n))
    inner = runs[1:-1]
    rr = [n for s, n in inner if s]
    gg = [n for s, n in inner if not s]
    gap_px = (L > 8) & (L < 60)
    return dict(field_corner_L=round(corners, 2),
                field_noise_sigma=round(float(L[:40, :40].std()), 3),
                disc_height_frac=round(float((rows.max() - rows.min() + 1) / 540), 3),
                ring_pixels_L_p10_p50_p90=[float(np.percentile(L[ring], q)) for q in (10, 50, 90)],
                ring_R_minus_B_mean=round(float(rb.mean()), 2),
                gap_rgb_mean=[round(float(a[..., c][gap_px].mean()), 1) for c in range(3)],
                centre_row_ring_runs_px=rr, centre_row_gap_runs_px=gg,
                ring_over_gap_mean=round(float(np.mean(rr) / max(np.mean(gg), 1)), 3) if rr and gg else None)


def stills():
    d = tests_load()
    pA = O.plate("A")[0]
    pB = O.plate("B")[0]
    res = {}
    for name, th, g in (("OA_gain1.0_k48", 2 * math.pi * 48 / 80, 1.0), ("OA_gain0.7_k0", 0.0, 0.7)):
        im = O.compose(pA, [O.render_rings(th, g, omega=FAST)], warm=True)
        Image.fromarray(im).save(f"{MED}/cmp_duchamp2_{name}.png")
        res[name] = measure(im)
    for name, th, g, om in (("OB_gain1.0_k48_fast", 2 * math.pi * 48 / 80, 1.0, FAST),
                            ("OB_gain1.0_k48_read", 2 * math.pi * 48 / 80, 1.0, READ)):
        im = O.compose(pB, [O.render_keys(th, g, omega=om)], warm=True)
        Image.fromarray(im).save(f"{MED}/cmp_duchamp2_{name}.png")
        m = measure(im)
        keys = im.astype(np.float32).mean(axis=2) > 80
        m["key_pixels_L_p10_p50_p90"] = [float(np.percentile(im.astype(np.float32).mean(axis=2)[keys], q)) for q in (10, 50, 90)]
        res[name] = m
    # 100 % crops of one key at both speeds (1:1 legibility of teeth and bow hole)
    for nm in ("OB_gain1.0_k48_fast", "OB_gain1.0_k48_read"):
        im = np.asarray(Image.open(f"{MED}/cmp_duchamp2_{nm}.png"))
        cv2.imwrite(f"{MED}/key_crop100_{nm}.png",
                    cv2.resize(im[30:130, 400:560][..., ::-1], None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST))
    # reference numbers sampled from duchamp2.webp with PIL (read only; no pixels copied)
    ref = np.asarray(Image.open("/home/user/bolas/paeleo/scion/oulipo/assets/references/duchamp2.webp").convert("RGB")).astype(np.float32)
    rL = ref.mean(axis=2)
    rring = (rL > 90) & (rL < 175)
    res["duchamp2_reference_numbers"] = dict(
        size=list(ref.shape[:2]), field_corner_L=round(float(rL[:15, :15].mean()), 1),
        ring_pixels_L_p10_p50_p90=[float(np.percentile(rL[rring], q)) for q in (10, 50, 90)],
        ring_R_minus_B_mean=round(float((ref[..., 0] - ref[..., 2])[rring].mean()), 2))
    d["stills"] = res
    tests_save(d)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "alias":
        alias()
    elif what == "depth":
        depth(sys.argv[2].split(",") if len(sys.argv) > 2 else None)
    elif what == "stills":
        stills()
