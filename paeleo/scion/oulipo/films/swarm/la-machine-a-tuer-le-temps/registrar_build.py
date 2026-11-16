#!/usr/bin/env python3
"""Registrar: freeze the 8-print rostrum pool for La Machine a tuer le temps.

Deterministic: master TIFF (LoC) -> integer box reduce -> per-frame eased 16:9
window -> LANCZOS resample to 1280x720 -> print_op (one tone map) -> RGB PNG.
No randomness, no grain. Re-running yields identical frame md5s.

Usage: python3 registrar_build.py [--only 05] [--measure]
"""
import hashlib, json, os, sys
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "../../sources/la-machine-a-tuer-le-temps"))
MASTERS = os.path.join(SRC, "registrar", "masters")
ASSETS = os.path.join(SRC, "registrar", "assets")
N, OW, OH = 120, 1280, 720
BLACK = (24, 20, 18)
WHITE = (232, 226, 214)
GAMMA = 1.5          # single shared print grade (one paper curve for all 8); see manifest print_op
LO_PCT, HI_PCT = 0.5, 99.5

# Windows and clean bounds were chosen BY LOOKING at gridded previews
# (registrar/preview/grid_*.jpg), in preview pixels of the 1400-px thumbnail;
# they are converted to master pixels with the exact scale below.
# clean = image area inside the rebate, excluding OWI edge codes, notches and
# the print easel border (05 is a copy negative of a file print).
POOL = {
 "01": dict(loc="2017844012", tif="https://tile.loc.gov/storage-services/master/pnp/fsa/8d13000/8d13000/8d13022u.tif",
            prev=(1400, 1078), clean=(55, 35, 1320, 990),
            W0=(55, 150, 1320, 862), W1=(120, 170, 1132, 739)),
 "02": dict(loc="2017844121", tif="https://tile.loc.gov/storage-services/master/pnp/fsa/8d13000/8d13100/8d13131u.tif",
            prev=(1400, 1074), clean=(50, 60, 1370, 1020),
            W0=(50, 230, 1370, 972), W1=(72, 240, 1128, 834)),
 "03": dict(loc="2017844115", tif="https://tile.loc.gov/storage-services/master/pnp/fsa/8d13000/8d13100/8d13125u.tif",
            prev=(1081, 1400), clean=(60, 50, 1020, 1350),
            W0=(60, 270, 1020, 810), W1=(120, 380, 920, 830)),
 "04": dict(loc="2017843935", tif="https://tile.loc.gov/storage-services/master/pnp/fsa/8d25000/8d25000/8d25003u.tif",
            prev=(1314, 1400), clean=(100, 105, 1200, 1300),
            W0=(100, 300, 1200, 919), W1=(100, 230, 1013, 744)),
 "05": dict(loc="2017843923", tif="https://tile.loc.gov/storage-services/master/pnp/cph/3c30000/3c30000/3c30600/3c30642u.tif",
            prev=(1400, 1102), clean=(185, 45, 1195, 1040),
            W0=(185, 230, 1195, 798), W1=(372, 262, 1149, 699)),
 "06": dict(loc="2017843913", tif="https://tile.loc.gov/storage-services/master/pnp/fsa/8d24000/8d24900/8d24980u.tif",
            prev=(1343, 1400), clean=(110, 75, 1250, 1255),
            W0=(110, 300, 1250, 941), W1=(338, 428, 1250, 941)),
 "07": dict(loc="2017843870", tif="https://tile.loc.gov/storage-services/master/pnp/fsa/8d24000/8d24900/8d24937u.tif",
            prev=(1395, 1400), clean=(100, 110, 1260, 1320),
            W0=(100, 280, 1260, 933), W1=(100, 300, 1109, 867)),
 "08": dict(loc="2017843779", tif="https://tile.loc.gov/storage-services/master/pnp/fsa/8d24000/8d24800/8d24845u.tif",
            prev=(1380, 1400), clean=(130, 115, 1275, 1300),
            W0=(130, 470, 1275, 1114), W1=(160, 495, 1250, 1108)),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fix169(box):
    """Make a box exactly 16:9 about its centre, keeping its width."""
    x0, y0, x1, y1 = box
    w = x1 - x0
    h = w * 9 / 16
    cy = (y0 + y1) / 2
    return (x0, cy - h / 2, x1, cy + h / 2)


def ease(t):  # cubic ease in-out, exact in float64
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def load(aid):
    im = Image.open(os.path.join(MASTERS, f"{aid}u.tif"))
    im.load()
    assert im.mode == "L", im.mode
    return im


def geometry(aid, native):
    p = POOL[aid]
    s = native[0] / p["prev"][0]
    sc = lambda b: tuple(round(v * s, 2) for v in b)
    clean = sc(p["clean"])
    W0 = fix169(sc(p["W0"]))
    W1 = fix169(sc(p["W1"]))
    for W in (W0, W1):
        assert clean[0] - 1e-6 <= W[0] and W[2] <= clean[2] + 1e-6 and clean[1] <= W[1] and W[3] <= clean[3], (aid, W, clean)
    return s, clean, W0, W1


def windows(W0, W1):
    out = []
    for i in range(N):
        e = ease(i / (N - 1))
        out.append(tuple(round(a + (b - a) * e, 3) for a, b in zip(W0, W1)))
    return out


# Repair round 1 (critic, acceptance 5): one print-stage levels change per asset,
# chosen by measuring the rendered windows, not the clean area.
#   04: the door window had p1 35.8-39.4 (band 14-36): black point lo raised 11 -> 22
#   01: the clock window had p99 208-210 (band 210-238): white point hi lowered 188 -> 183
LEVELS_OVERRIDE = {"04": {"lo": 22.0}, "01": {"hi": 183.0}}


def levels(im, clean, aid=None):
    a = np.asarray(im.crop(tuple(int(round(v)) for v in clean)))[::2, ::2]
    lo, hi = np.percentile(a, [LO_PCT, HI_PCT])
    o = LEVELS_OVERRIDE.get(aid, {})
    return float(o.get("lo", lo)), float(o.get("hi", hi))


def print_op(gray, lo, hi):
    v = np.clip((gray.astype(np.float64) - lo) / (hi - lo), 0.0, 1.0) ** GAMMA
    rgb = np.stack([BLACK[c] + v * (WHITE[c] - BLACK[c]) for c in range(3)], -1)
    return np.round(rgb).astype(np.uint8)


def render(aid, measure=False):
    p = POOL[aid]
    path = os.path.join(MASTERS, f"{aid}u.tif")
    im = load(aid)
    native = im.size
    s, clean, W0, W1 = geometry(aid, native)
    lo, hi = levels(im, clean, aid)
    # integer box reduce of the very large 4x5 D-series scans (12.8k px) so the
    # per-frame resample stays tractable; exact, deterministic, never upscales
    red = 2 if native[0] > 8000 or native[1] > 8000 else 1
    work = im.reduce(red) if red > 1 else im
    wins = windows(W0, W1)
    rec = dict(asset_id=aid, native_bounds=list(native), preview_scale=s, clean_bounds=list(clean),
               W0=list(W0), W1=list(W1), reduce=red, levels=[lo, hi], frame_md5=[])
    if measure:
        return rec
    od = os.path.join(ASSETS, aid)
    os.makedirs(od, exist_ok=True)
    for i, w in enumerate(wins):
        box = tuple(v / red for v in w)
        fr = work.resize((OW, OH), Image.LANCZOS, box=box)
        rgb = print_op(np.asarray(fr), lo, hi)
        img = Image.fromarray(rgb, "RGB")
        fp = os.path.join(od, f"{i:04d}.png")
        img.save(fp, optimize=False, compress_level=6)
        rec["frame_md5"].append(hashlib.md5(rgb.tobytes()).hexdigest())
    rec["file_md5_note"] = "frame_md5 = md5 of raw RGB24 pixel bytes (row-major 1280x720x3), equal to ffmpeg framemd5 of rgb24"
    rec["windows_first_last"] = [list(wins[0]), list(wins[-1])]
    return rec


if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else sorted(POOL)
    measure = "--measure" in sys.argv
    out = {}
    for aid in only:
        out[aid] = render(aid, measure)
        print(aid, out[aid]["native_bounds"], out[aid]["levels"], len(out[aid]["frame_md5"]), flush=True)
    fn = os.path.join(SRC, "registrar", "render-record.json" if not measure else "measure.json")
    old = {}
    if os.path.exists(fn) and not measure:
        old = json.load(open(fn))
    old.update(out)
    json.dump(old, open(fn, "w"), indent=1)
