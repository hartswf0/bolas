"""Stage 2 of NOBODY HOME's removal, from a saved mask. For each half second: the median of this pixel across nearby frames where it was unmasked. Recorded and revealed pixels only; anything never revealed goes to unknown.png and is inpainted as an authored fill.
usage: erase_plate.py <clip> <in> <out> <dir> [dilate-already-in-mask]"""
import json, os, subprocess, sys, tempfile
import cv2, numpy as np
clip, a, b, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]; FPS = 24; tmp = tempfile.mkdtemp()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", clip, "-vf", f"fps={FPS},scale=640:480:flags=lanczos", "-q:v", "2", "-start_number", "0", f"{tmp}/%05d.jpg"], check=True)
names = sorted(x for x in os.listdir(tmp) if x.endswith(".jpg")); n = len(names); F = np.stack([cv2.imread(f"{tmp}/{x}") for x in names]); H, W = F.shape[1:3]
D = np.unpackbits(np.load(f"{out}/mask.npy"))[: n * H * W].reshape(n, H, W).astype(bool); print("frames", n, "mask mean", round(float(D.mean()), 4), flush=True)
def median_of(idx):
    ix = np.array(idx); st = F[ix][::1].astype(np.float32); st[D[ix]] = np.nan
    pl = np.empty((H, W, 3), np.float32)
    for r in range(0, H, 60): pl[r:r + 60] = np.nanmedian(st[:, r:r + 60], axis=0)
    return pl
import warnings; warnings.filterwarnings("ignore")
whole = median_of(list(range(0, n, 8))); never = D.all(axis=0); cv2.imwrite(f"{out}/unknown.png", never.astype(np.uint8) * 255); print("never revealed", float(never.mean()), flush=True)
pl_never = np.isnan(whole[..., 0]); w8 = cv2.inpaint(np.nan_to_num(whole).astype(np.uint8), (pl_never * 255).astype(np.uint8), 5, cv2.INPAINT_TELEA)
PL = {}; STEP = 12; R = 60
for c in range(0, n, STEP):
    p = median_of(list(range(max(0, c - R), min(n, c + R + 1), 4))); m = np.isnan(p[..., 0]); p[m] = w8[m]; PL[c] = p.astype(np.uint8); print(c, flush=True) if c % 120 == 0 else None
w = cv2.VideoWriter(f"{tmp}/d.mp4", cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H)); w2 = cv2.VideoWriter(f"{tmp}/m.mp4", cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
for i in range(n):
    c = (i // STEP) * STEP; soft = cv2.GaussianBlur(D[i].astype(np.float32), (0, 0), 2)[..., None]
    w.write((F[i] * (1 - soft) + PL[c] * soft).astype(np.uint8)); w2.write(np.where(D[i, ..., None], (F[i] * 0.45 + np.array([40, 40, 200]) * 0.55).astype(np.uint8), F[i]))
w.release(); w2.release()
for s, t in (("d", "derived.mp4"), ("m", "maskview.mp4")): subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/{s}.mp4", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", f"{out}/{t}"], check=True)
json.dump({"clip": clip, "in": a, "out": b, "fps": FPS, "never_revealed_fraction": float(never.mean()), "method": "SAM 2.1 small tracked mask from clicks chosen by eye; replacement pixels are the median of the same pixel in unmasked frames within 2.5 s (recomputed each half second); never-revealed pixels Telea-inpainted, listed in unknown.png"}, open(f"{out}/removal.json", "w"), indent=1); print("DONE", flush=True)
