#!/usr/bin/env python3
"""Montage-editor checks on the FINAL render (assets/films/un-homme-qui-dort.mp4).

- decodes final frames with ffmpeg and re-runs the aesthetic measurement beside
  assets/references/sommeil.webp (study only; the reference is never in the film);
- compares each final frame with U1's pre-caption PNG (encode error only, caption band excluded);
- checks that SIL-H frames carry no caption band in either pass;
- decodes the final audio and measures SIL-H (floor, max transient) in both passes and
  pass I vs pass II audio identity;
- writes a gate-shaped picture file (measured events + per-frame figure alpha) for u3-gate.py.

    python3 -I editor-check.py
"""
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MP4 = ROOT / "assets/films/un-homme-qui-dort.mp4"
REF = ROOT / "assets/references/sommeil.webp"
DIRS = {k: Path(v) for k, v in json.loads((HERE / "e3-picture-ledger.json").read_text())["shot_dirs"].items()}  # repair round 2
W, H, FPS = 960, 540, 24
SHOTS = [("S1", 0.0, 5.5), ("S2", 5.5, 8.5), ("S3", 8.5, 11.5), ("S4", 11.5, 19.0),
         ("S5", 19.0, 24.5), ("S6", 24.5, 27.0), ("S7", 27.0, 35.0)]
# representative pass times (U1's), each measured in BOTH passes of the final film
REP = {"S1": 1.25, "S2": 7.0, "S3": 11.0, "S4": 15.0, "S5": 22.0, "S6": 25.75, "S7": 33.25}
PASS0 = {"A": 1.0, "B": 37.0}


def decode_video():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(MP4), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def decode_audio():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(MP4), "-f", "s16le", "-ac", "1", "-ar", "44100", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768.0


def stats(a):
    a = a.astype(np.float32)
    chroma = float((a.max(2) - a.min(2)).mean())
    L = a.mean(2)
    p = np.percentile(L, [1, 50, 99])
    return {"mean_chroma": round(chroma, 3), "p1": round(float(p[0]), 1), "p50": round(float(p[1]), 1),
            "p99": round(float(p[2]), 1), "below60": round(float((L < 60).mean()), 3),
            "above220": round(float((L > 220).mean()), 3), "mid": round(float(((L >= 60) & (L <= 220)).mean()), 3)}


def shot_frame(pt):
    k = int(round(pt * FPS))
    for sid, a, b in SHOTS:
        if a <= pt < b:
            return sid, DIRS[sid] / f"{sid}_{k - int(round(a * FPS)):04d}.png"


def main():
    V = decode_video()
    out = {"film_frames": int(V.shape[0]), "duration_s": V.shape[0] / FPS}
    u1 = json.loads((HERE / "e3-picture-ledger.json").read_text())
    head = u1["measured"]["head_height"]
    timings = json.loads((HERE / "editor-final-timings.json").read_text())
    capfr = {k: [tuple(c["frames_film"]) for c in timings["captions_film_t"][k]] for k in "AB"}

    def has_cap(k):
        return any(a <= k < b for v in capfr.values() for a, b in v)

    ref = np.asarray(Image.open(REF).convert("RGB"))
    out["reference"] = stats(ref)
    rows = []
    out["shots"] = {}
    for sid, pt in REP.items():
        rec = {}
        for p in "AB":
            k = int(round((PASS0[p] + pt) * FPS))
            fa = V[k]
            st = stats(fa)
            _, png = shot_frame(pt)
            src = np.asarray(Image.open(png).convert("RGB")).astype(np.int16)
            body = slice(0, H - 80)  # exclude the caption band zone
            err = np.abs(fa[body].astype(np.int16) - src[body]).mean(2)
            st.update({"film_t": round(k / FPS, 3), "caption_on_frame": has_cap(k),
                       "mean_abs_err_vs_U1_png": round(float(err.mean()), 2),
                       "p99_abs_err_vs_U1_png": round(float(np.percentile(err, 99)), 1)})
            rec[p] = st
            rows.append((f"{sid} pass {'I' if p == 'A' else 'II'} film t={k / FPS:.2f}", fa, st, head.get(sid)))
        out["shots"][sid] = rec
    # targets on caption-free frames
    tg = {}
    for sid, rec in out["shots"].items():
        for p, st in rec.items():
            t = {"neutral": st["mean_chroma"] <= 1.5, "p1_20_40": 20 <= st["p1"] <= 40, "p99_236_250": 236 <= st["p99"] <= 250}
            if sid in ("S3", "S4"):
                t["bimodal_sum_ge_0.55"] = st["below60"] + st["above220"] >= 0.55
                t["below60_pm0.12"] = abs(st["below60"] - 0.416) <= 0.12
                t["above220_pm0.12"] = abs(st["above220"] - 0.326) <= 0.12
            tg[f"{sid}.{p}"] = t
    out["targets"] = tg
    # neutrality across every 12th film frame
    ch = [float((V[k].astype(np.int16).max(2) - V[k].astype(np.int16).min(2)).mean()) for k in range(0, V.shape[0], 12)]
    out["max_mean_chroma_every_12th_frame"] = round(max(ch), 3)
    # SIL-H: no caption band in either pass (frame equals U1 PNG in the band zone up to encode error)
    sil = {}
    for p in "AB":
        ks = range(int(round((PASS0[p] + 11.5) * FPS)), int(round((PASS0[p] + 19.0) * FPS)))
        src = np.asarray(Image.open(DIRS["S4"] / "S4_0000.png").convert("RGB")).astype(np.int16)
        band = [float(np.abs(V[k][H - 80:].astype(np.int16) - src[H - 80:]).mean()) for k in ks]
        sil[p] = {"frames": len(ks), "max_band_zone_err": round(max(band), 2), "caption_frames": sum(has_cap(k) for k in ks)}
    out["SIL_H_picture"] = sil
    # audio
    A = decode_audio()
    r = 44100

    def db(x):
        return 20 * np.log10(max(x, 1e-12))

    aud = {}
    for p in "AB":
        s = A[int((PASS0[p] + 11.5) * r):int((PASS0[p] + 19.0) * r)]
        floor = np.sqrt((s ** 2).mean())
        w50 = int(0.05 * r)
        rms50 = [np.sqrt((s[i:i + w50] ** 2).mean()) for i in range(0, len(s) - w50, w50)]
        w10 = int(0.01 * r)
        rms10 = [np.sqrt((s[i:i + w10] ** 2).mean()) for i in range(0, len(s) - w10, w10)]
        aud[p] = {"rms_floor_dbfs": round(db(floor), 2), "max_50ms_over_floor_db": round(db(max(rms50)) - db(floor), 2),
                  "max_10ms_over_floor_db": round(db(max(rms10)) - db(floor), 2), "nonzero": bool(floor > 0)}
    a = A[int(1.0 * r) + r // 10:int(36.0 * r) - r // 10]
    b = A[int(37.0 * r) + r // 10:int(72.0 * r) - r // 10]
    n = min(len(a), len(b))
    diff = a[:n] - b[:n]
    out["audio"] = {"SIL_H": aud, "passI_vs_passII_rms_diff_dbfs": round(db(np.sqrt((diff ** 2).mean())), 1),
                    "pass_rms_dbfs": round(db(np.sqrt((a ** 2).mean())), 1), "peak_dbfs": round(db(np.abs(A).max()), 2)}
    # gate-shaped picture file (measured events + per-frame figure alpha, pass frames)
    m = u1["measured"]
    cov = m["figure_alpha_coverage"]
    gate_pic = {"events": {
        "E1": {"t_on": m["events"]["E1"]["authored_frames"][0] / FPS,
               "t_off": m["events"]["E1"]["authored_frames"][1] / FPS},
        "E4": {"t_on": m["events"]["E4_enter"]["measured_t"], "exit": m["events"]["E4_exit"]["measured_t"]},
        "E6": {"t_on": m["events"]["E6_enter"]["measured_t"], "exit": m["events"]["E6_exit"]["measured_t"]}},
        "figure_alpha_coverage": {"S5": cov["S5"], "S7": cov["S7"]},
        "note": "derived by editor-check.py from e3-picture-ledger.json measured.*; E2/E2b/E3 are sound events (U2 placed at planned times)"}
    (HERE / "editor-gate-picture.json").write_text(json.dumps(gate_pic, indent=1))
    (HERE / "editor-check.json").write_text(json.dumps(out, indent=1))
    # side-by-side sheet: reference + one caption-free final frame per shot
    tw = 400
    th = int(tw * H / W)
    f = ImageFont.truetype(str(ROOT / "assets/fonts/ibm-plex-mono.woff2"), 12)
    pick = [r_ for r_ in rows if not r_[2]["caption_on_frame"]]
    seen, cells = set(), []
    for lab, fa, st, hh in pick:
        sid = lab[:2]
        if sid in seen:
            continue
        seen.add(sid)
        cells.append((lab, Image.fromarray(fa), st, hh))
    rh = Image.open(REF).convert("RGB")
    rh = rh.resize((int(th * rh.width / rh.height), th))
    cells.insert(0, ("REFERENCE sommeil.webp (study only, not in film)", rh, out["reference"], 0.48))
    cols = 2
    rows_n = (len(cells) + 1) // 2
    sheet = Image.new("RGB", (cols * (tw + 16) + 16, rows_n * (th + 70) + 16), (0x1e, 0x1e, 0x1e))
    d = ImageDraw.Draw(sheet)
    for i, (lab, im, st, hh) in enumerate(cells):
        x, y = 16 + (i % cols) * (tw + 16), 16 + (i // cols) * (th + 70)
        im = im if im.width <= tw else im.resize((tw, th))
        sheet.paste(im, (x, y))
        d.text((x, y + th + 4), lab, font=f, fill=(0xef, 0xef, 0xef))
        d.text((x, y + th + 20), f"chroma {st['mean_chroma']:.2f}  p1 {st['p1']:.0f}  p50 {st['p50']:.0f}  p99 {st['p99']:.0f}",
               font=f, fill=(0xd6, 0xd6, 0xd6))
        d.text((x, y + th + 36), f"<60 {st['below60']:.3f}  >220 {st['above220']:.3f}  mid {st['mid']:.3f}  head/frame "
               + (f"{hh:.2f}" if hh else "n/a"), font=f, fill=(0xd6, 0xd6, 0xd6))
    sheet.save(HERE / "editor-aesthetic-final.jpg", quality=88)
    print(json.dumps({k: out[k] for k in ("duration_s", "max_mean_chroma_every_12th_frame", "SIL_H_picture", "audio")}, indent=1))
    for sid, rec in out["shots"].items():
        for p, st in rec.items():
            print(sid, p, st)
    print({k: v for k, v in tg.items() if not all(v.values())})


if __name__ == "__main__":
    main()
