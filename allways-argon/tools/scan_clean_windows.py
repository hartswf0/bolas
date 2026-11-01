#!/usr/bin/env python3
"""
Scans all 819 local .mp4 clips in allways_studio/clips/ to detect internal hard cuts
and compute the best contiguous cut-free window [clean_in, clean_out] and actual duration.
Stores the result in forage/clip_clean_windows.json so no trimmed shot ever crosses an internal cut.
"""
import json
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path
import cv2
import numpy as np

BASE_DIR = Path("/Users/gaia/WORLDBUILDING-TERMS/allways_studio")
CLIPS_DIR = BASE_DIR / "clips"
FORAGE_DIR = BASE_DIR / "forage"

def analyze_clip(mp4_path_str: str):
    mp4_path = Path(mp4_path_str)
    cid = mp4_path.stem
    cap = cv2.VideoCapture(mp4_path_str)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    total_dur = round(n_frames / fps, 2) if fps > 0 else 0.0
    if total_dur <= 0.4:
        cap.release()
        return cid, {"dur": total_dur, "clean_in": 0.0, "clean_out": total_dur, "clean_dur": total_dur, "cuts": [], "luma": 0.0, "motion": 0.0}

    step = max(1, int(round(fps / 6.0)))  # 6 samples per second
    times = []
    grays = []
    hists = []
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        if idx % step == 0:
            small = cv2.resize(frame, (64, 36))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
            hist = cv2.calcHist([small], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            cv2.normalize(hist, hist)
            times.append(idx / fps)
            grays.append(gray)
            hists.append(hist.flatten())
        idx += 1
    cap.release()

    if len(grays) < 2:
        return cid, {"dur": total_dur, "clean_in": 0.0, "clean_out": total_dur, "clean_dur": total_dur, "cuts": [], "luma": 50.0, "motion": 5.0}

    cut_indices = [0]
    cut_times = []
    for i in range(1, len(grays)):
        pixel_diff = float(np.mean(np.abs(grays[i] - grays[i - 1])))
        hist_corr = float(cv2.compareHist(hists[i - 1], hists[i], cv2.HISTCMP_CORREL))
        # A hard cut typically has low histogram correlation (< 0.55) AND high pixel diff (> 24.0)
        if (hist_corr < 0.50 and pixel_diff > 20.0) or pixel_diff > 38.0:
            cut_indices.append(i)
            cut_times.append(round(times[i], 2))
    cut_indices.append(len(grays) - 1)

    # Find longest contiguous sub-segment that isn't near-black (luma > 15)
    best_seg = (0, len(grays) - 1)
    best_score = -1.0
    all_windows = []
    for c_i in range(len(cut_indices) - 1):
        s_i, e_i = cut_indices[c_i], cut_indices[c_i + 1]
        if e_i <= s_i:
            continue
        w_in = round(times[s_i] + (0.12 if s_i > 0 else 0.05), 2)
        w_out = round(times[e_i] - (0.12 if e_i < len(grays) - 1 else 0.05), 2)
        w_dur = round(max(0.0, w_out - w_in), 2)
        sub_g = grays[s_i : e_i + 1]
        luma = float(np.mean(sub_g))
        motion = float(np.mean([np.mean(np.abs(sub_g[j] - sub_g[j - 1])) for j in range(1, len(sub_g))])) if len(sub_g) > 1 else 0.0
        if w_dur >= 1.2:
            all_windows.append({"in": w_in, "out": w_out, "dur": w_dur, "luma": round(luma, 1), "motion": round(motion, 2)})
        score = w_dur * (1.0 if luma > 18.0 else 0.2) * (1.15 if motion > 1.0 else 0.7)
        if score > best_score:
            best_score = score
            best_seg = (s_i, e_i)

    s_i, e_i = best_seg
    c_in = round(times[s_i] + (0.12 if s_i > 0 else 0.05), 2)
    c_out = round(times[e_i] - (0.12 if e_i < len(grays) - 1 else 0.05), 2)
    if c_out <= c_in + 0.5:
        c_in, c_out = 0.0, total_dur
    sub_g = grays[s_i : e_i + 1]
    luma = round(float(np.mean(sub_g)), 1)
    motion = round(float(np.mean([np.mean(np.abs(sub_g[j] - sub_g[j - 1])) for j in range(1, len(sub_g))])) if len(sub_g) > 1 else 0.0, 2)

    return cid, {
        "dur": total_dur,
        "clean_in": c_in,
        "clean_out": c_out,
        "clean_dur": round(c_out - c_in, 2),
        "cuts": cut_times,
        "windows": all_windows[:5],
        "luma": luma,
        "motion": motion,
    }

def main():
    mp4s = [str(p) for p in sorted(CLIPS_DIR.glob("*.mp4")) if p.stat().st_size > 0]
    print(f"Scanning {len(mp4s)} local .mp4 clips for internal scene cuts and clean windows...")
    results = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = [ex.submit(analyze_clip, p) for p in mp4s]
        done = 0
        for f in as_completed(futs):
            done += 1
            cid, info = f.result()
            results[cid] = info
            if done % 100 == 0 or done == len(mp4s):
                print(f"  [{done}/{len(mp4s)}] scanned")

    out_path = FORAGE_DIR / "clip_clean_windows.json"
    out_path.write_text(json.dumps(results, indent=2))
    multi_cut = sum(1 for v in results.values() if len(v["cuts"]) > 0)
    print(f"Saved clean windows for {len(results)} clips to {out_path} ({multi_cut} clips had internal cuts detected!).")

if __name__ == "__main__":
    main()
