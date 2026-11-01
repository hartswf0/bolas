#!/usr/bin/env python3
"""
Generates Shot-by-Shot Temporal Proof Strips (entry, 38%, 66%, exit frames of every segment)
and runs Automated Structural Checks (Rule 10a) on all rendered films in films/.
"""
import json
import subprocess
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path("/Users/gaia/WORLDBUILDING-TERMS/allways_studio")
sys.path.insert(0, str(BASE_DIR))
import build_screening_room

FILMS_DIR = BASE_DIR / "films"
MANIFESTS_DIR = BASE_DIR / "manifests"
FORAGE_DIR = BASE_DIR / "forage"
STRIPS_DIR = FORAGE_DIR / "critic_strips"
STRIPS_DIR.mkdir(parents=True, exist_ok=True)

def get_font(size=13, bold=False):
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

def measure_audio_rms(mp4_path: Path, start_s: float, end_s: float) -> float:
    dur = max(0.1, end_s - start_s)
    cmd = [
        "ffmpeg", "-v", "error",
        "-ss", f"{start_s:.2f}", "-t", f"{dur:.2f}",
        "-i", str(mp4_path),
        "-f", "s16le", "-ac", "1", "-ar", "8000", "-"
    ]
    try:
        raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        if not raw:
            return -96.0
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(samples ** 2)) + 1e-9)
        return round(20.0 * np.log10(rms), 1)
    except Exception:
        return -96.0

def extract_frames_at(cap, timestamps):
    frames = []
    for t in timestamps:
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t * 1000.0))
        ok, frame = cap.read()
        if not ok or frame is None:
            frames.append(np.zeros((135, 240, 3), dtype=np.uint8))
        else:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            small = cv2.resize(rgb, (240, 135), interpolation=cv2.INTER_AREA)
            frames.append(small)
    return frames

def build_film_strip(manifest_path: Path, pool: dict, ver_tag: str = "v2"):
    raw_m = json.loads(manifest_path.read_text())
    m = build_screening_room.normalize_manifest(raw_m, pool)
    fid = m["film_id"]
    mp4_path = FILMS_DIR / f"{fid}.mp4"
    if not mp4_path.exists():
        return None

    cap = cv2.VideoCapture(str(mp4_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    actual_dur = total_frames / fps if fps else 0.0

    segments = m.get("segments", [])
    raw_edl = raw_m.get("edl", [])
    rows = []
    structural_issues = []

    for idx, seg in enumerate(segments):
        s_t = float(seg.get("start_sec", 0.0))
        e_t = float(seg.get("end_sec", s_t + 3.0))
        dur = max(0.1, e_t - s_t)
        raw_seg = raw_edl[idx] if idx < len(raw_edl) else {}

        ts = [
            s_t + dur * 0.12,
            s_t + dur * 0.38,
            s_t + dur * 0.65,
            s_t + dur * 0.88,
        ]
        frames = extract_frames_at(cap, ts)
        motion_diff = float(np.mean(np.abs(frames[2].astype(np.float32) - frames[0].astype(np.float32))))
        luma_mean = float(np.mean(frames[1]))
        db = measure_audio_rms(mp4_path, s_t, e_t)

        mode = seg.get("mode", "shot")
        label = seg.get("label", f"Seg {idx+1}")
        cid = seg.get("clip_id", "")
        src_title = seg.get("source_title", "")
        src_year = seg.get("source_year", "")
        in_sec = raw_seg.get("in_s", raw_seg.get("in_sec", 0.0))
        out_sec = raw_seg.get("out_s", raw_seg.get("out_sec", 0.0))

        if mode != "card" and motion_diff < 1.2:
            structural_issues.append(f"Seg #{idx+1} ({s_t:.1f}s-{e_t:.1f}s) near-static motion_diff={motion_diff:.2f}")
        if mode != "card" and luma_mean < 8.0:
            structural_issues.append(f"Seg #{idx+1} ({s_t:.1f}s-{e_t:.1f}s) near-black luma={luma_mean:.1f}")
        if "→" in str(label) or "→" in json.dumps(raw_seg, ensure_ascii=False):
            structural_issues.append(f"Seg #{idx+1} ({s_t:.1f}s-{e_t:.1f}s) contains Unicode arrow '→' which renders as missing glyph box in Helvetica")

        rows.append({
            "idx": idx + 1,
            "mode": mode,
            "start_sec": round(s_t, 2),
            "end_sec": round(e_t, 2),
            "dur": round(dur, 2),
            "clip_id": cid,
            "in_sec": in_sec,
            "out_sec": out_sec,
            "source_title": src_title,
            "source_year": src_year,
            "label": label,
            "motion_diff": round(motion_diff, 2),
            "luma_mean": round(luma_mean, 1),
            "audio_dbfs": db,
            "frames": frames,
            "ts": ts,
        })

    cap.release()

    header_h = 58
    row_h = 148
    img_w = 380 + 4 * 248 + 16
    img_h = header_h + len(rows) * row_h + 12
    sheet = Image.new("RGB", (img_w, img_h), (16, 18, 17))
    draw = ImageDraw.Draw(sheet)
    f_title = get_font(15, bold=True)
    f_meta = get_font(11, bold=False)
    f_small = get_font(10, bold=False)

    draw.text((14, 10), f"[{ver_tag.upper()}] {fid} — {m.get('title', '')} (Duration: {actual_dur:.2f}s | {len(rows)} segments)", fill=(240, 234, 220), font=f_title)
    draw.text((14, 32), f"Theorem: {str(m.get('creative_theorem') or '')[:140]}", fill=(167, 206, 186), font=f_meta)

    for r_i, r in enumerate(rows):
        y0 = header_h + r_i * row_h
        draw.line([(10, y0 - 4), (img_w - 10, y0 - 4)], fill=(45, 54, 48), width=1)
        draw.text((14, y0 + 4), f"#{r['idx']:02d} [{r['mode'].upper()}] {r['start_sec']:05.2f}s - {r['end_sec']:05.2f}s ({r['dur']:.2f}s)", fill=(223, 204, 157), font=f_meta)
        draw.text((14, y0 + 22), f"Label: {str(r['label'])[:46]}", fill=(240, 234, 220), font=f_meta)
        if r["clip_id"]:
            draw.text((14, y0 + 40), f"Clip: {r['clip_id'][:12]} [{r['in_sec']}s..{r['out_sec']}s]", fill=(190, 197, 186), font=f_small)
            draw.text((14, y0 + 56), f"Src: {str(r['source_title'])[:38]} ({r['source_year']})", fill=(167, 206, 186), font=f_small)
        draw.text((14, y0 + 76), f"MotionΔ: {r['motion_diff']:.1f} | Luma: {r['luma_mean']:.0f} | Audio: {r['audio_dbfs']} dBFS", fill=(231, 157, 123), font=f_small)

        for f_i, (fr, t_val) in enumerate(zip(r["frames"], r["ts"])):
            x0 = 380 + f_i * 248
            pil_fr = Image.fromarray(fr)
            sheet.paste(pil_fr, (x0, y0 + 4))
            draw.rectangle([x0, y0 + 4, x0 + 239, y0 + 22], fill=(0, 0, 0))
            draw.text((x0 + 5, y0 + 6), f"t={t_val:05.2f}s", fill=(223, 204, 157), font=f_small)

    out_jpg = STRIPS_DIR / f"{fid}_{ver_tag}_strip.jpg"
    sheet.save(out_jpg, quality=88)

    for r in rows:
        del r["frames"]
        r["ts"] = [round(x, 2) for x in r["ts"]]

    return {
        "film_id": fid,
        "version": ver_tag,
        "title": m.get("title", ""),
        "actual_duration_sec": round(actual_dur, 2),
        "segment_count": len(rows),
        "strip_image": str(out_jpg),
        "structural_issues": structural_issues,
        "segments": rows,
    }

def main():
    ver_tag = sys.argv[1] if len(sys.argv) > 1 else "v2"
    pool_path = FORAGE_DIR / "candidate_pool_metadata.json"
    pool = json.loads(pool_path.read_text()) if pool_path.exists() else {}
    manifest_files = (
        sorted(MANIFESTS_DIR.glob("SCION_*.json"))
        + sorted(MANIFESTS_DIR.glob("BROLL_*.json"))
        + sorted(MANIFESTS_DIR.glob("STUDY_*.json"))
        + sorted(MANIFESTS_DIR.glob("COLL_*.json"))
    )
    diagnostics = {}
    for mp in manifest_files:
        res = build_film_strip(mp, pool, ver_tag=ver_tag)
        if res:
            diagnostics[res["film_id"]] = res
            print(f"Built {ver_tag} strip for {res['film_id']}: {res['segment_count']} segs, {res['actual_duration_sec']}s, issues={len(res['structural_issues'])}")
    out_json = FORAGE_DIR / f"{ver_tag}_structural_diagnostics.json"
    out_json.write_text(json.dumps(diagnostics, indent=2))
    print(f"Saved {len(diagnostics)} film diagnostics to {out_json}")

if __name__ == "__main__":
    main()
