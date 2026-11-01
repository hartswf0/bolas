"""NOBODY HOME's removal adapter. It separates three things and never blends them silently:
   recorded pixels (the frame), revealed pixels (the same spot when the person was elsewhere in this clip), and invented pixels (never seen; marked).
1. A person mask, tracked by SAM 2 from clicks chosen by eye.   2. A plate per frame: for each pixel, the median of the frames near it in time in which that pixel was unmasked.
3. Where no frame ever reveals a pixel it stays UNKNOWN and is written to unknown.png; a soft inpaint fills it and that fill is listed as authored.
usage: .venv/bin/python erase.py <clip.mp4> <in> <out> <outdir> '<json clicks: [[t,x,y,label],...]>' [dilate]   (x,y in 0..1 of the frame)"""
import json, os, subprocess, sys, tempfile
import cv2, numpy as np, torch
clip, a, b, out, clicks = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4], json.loads(sys.argv[5]); dil = int(sys.argv[6]) if len(sys.argv) > 6 else 9
L = os.environ.get("SAM2_ROOT", os.path.expanduser("~/sam2-root")); os.makedirs(out, exist_ok=True); tmp = tempfile.mkdtemp(); FPS = 24
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", clip, "-vf", f"fps={FPS},scale=640:480:flags=lanczos", "-q:v", "2", "-start_number", "0", f"{tmp}/%05d.jpg"], check=True)
names = sorted(os.listdir(tmp)); n = len(names); F = np.stack([cv2.imread(f"{tmp}/{x}") for x in names]); H, W = F.shape[1:3]
from sam2.build_sam import build_sam2_video_predictor
dev = "mps" if torch.backends.mps.is_available() else "cpu"
vp = build_sam2_video_predictor("configs/sam2.1/sam2.1_hiera_s.yaml", os.path.join(L, "models", "sam2.1_hiera_small.pt"), device=dev)
st = vp.init_state(tmp, offload_video_to_cpu=True, offload_state_to_cpu=True)
M = np.zeros((n, H, W), dtype=bool); by = {}
for t, x, y, lab in clicks: by.setdefault(round((t - a) * FPS), []).append((x * W, y * H, lab))
with torch.inference_mode():
    for fr, pts in by.items(): vp.add_new_points_or_box(st, frame_idx=fr, obj_id=1, points=np.array([p[:2] for p in pts], dtype=np.float32), labels=np.array([p[2] for p in pts], dtype=np.int32))
    for rev in (False, True):
        for fi, ids, lg in vp.propagate_in_video(st, start_frame_idx=min(by) if not rev else max(by), reverse=rev): M[fi] |= (lg[0, 0] > 0).cpu().numpy()
K = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dil, dil)); D = np.stack([cv2.dilate(m.astype(np.uint8), K) for m in M]).astype(bool)
print("frames", n, "mean mask area", D.mean())
np.save(os.path.join(out, "mask.npy"), np.packbits(D))
R = 72; Fg = F.astype(np.float32); out_frames = np.zeros_like(F); unknown = np.ones((H, W), bool)
for i in range(n):
    lo, hi = max(0, i - R), min(n, i + R + 1); idx = np.arange(lo, hi, 3); stack = Fg[idx].copy(); stack[D[idx]] = np.nan
    pl = np.nanmedian(stack, axis=0); miss = np.isnan(pl[..., 0])
    if miss.any():                                              # widen to the whole clip before giving up
        st2 = Fg[::3].copy(); st2[D[::3]] = np.nan; pw = np.nanmedian(st2, axis=0); pl[miss] = pw[miss]
    miss2 = np.isnan(pl[..., 0]); unknown &= miss2 | True
    fr = F[i].copy(); m = D[i]; soft = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2)[..., None]
    pl8 = np.nan_to_num(pl).astype(np.uint8)
    if miss2.any(): pl8 = cv2.inpaint(pl8, (miss2 * 255).astype(np.uint8), 5, cv2.INPAINT_TELEA)
    out_frames[i] = (fr * (1 - soft) + pl8 * soft).astype(np.uint8)
never = D.all(axis=0); cv2.imwrite(os.path.join(out, "unknown.png"), never.astype(np.uint8) * 255); print("pixels never revealed:", int(never.sum()), f"{never.mean()*100:.2f}%")
def write(arr, name, draw=None):
    w = cv2.VideoWriter(f"{tmp}/w.mp4", cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    for f in arr: w.write(f)
    w.release(); subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/w.mp4", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", os.path.join(out, name)], check=True)
write(out_frames, "derived.mp4"); write(np.stack([np.where(D[i, ..., None], (F[i] * 0.45 + np.array([40, 40, 200]) * 0.55).astype(np.uint8), F[i]) for i in range(n)]), "maskview.mp4")
json.dump({"clip": clip, "in": a, "out": b, "fps": FPS, "clicks": clicks, "dilate": dil, "never_revealed_fraction": float(never.mean()), "method": "SAM 2.1 small tracked mask; replacement = median of the same pixel in frames where it is unmasked, within 3 s, widening to the whole clip; unrevealed pixels Telea-inpainted and marked"}, open(os.path.join(out, "removal.json"), "w"), indent=1)
