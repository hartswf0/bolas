#!/usr/bin/env python3
"""Render a parallel film by hand-set pairs: two pictures side by side, each with its own sound on its own side, each labelled with what is known of its date.
films/<film>/pairs.json = {"pairs":[{"dur":s,"left":{"clip":n,"in":s,"gain":1},"right":{...},"why":".."}]}. A shot shorter than dur holds its last frame, and the ledger says so."""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SR = 48000; film = sys.argv[1]; d = os.path.join(ROOT, "films", film)
P = json.load(open(os.path.join(d, "pairs.json")))["pairs"]; db = json.load(open(os.path.join(d, "forage.json"))); byn = {str(c["n"]): c for c in db["clips"].values()}
F = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 22); W, H, PW, PH = 960, 720, 472, 354; fps = 24; tmp = tempfile.mkdtemp(); parts = []; led = []; T = 0; chan = []
def run(*a):
    r = subprocess.run(a, capture_output=True)
    if r.returncode: sys.exit(r.stderr.decode()[-800:])
def snd(p, i, dur):
    o = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(i,0):.3f}", "-t", f"{dur:.3f}", "-i", p, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    a = np.frombuffer(o, dtype=np.float32).copy(); n = int(0.03 * SR)
    if a.size > 2 * n: a[:n] *= np.linspace(0, 1, n); a[-n:] *= np.linspace(1, 0, n)
    return a
for k, p in enumerate(P):
    dur = round(p["dur"] * fps) / fps; L, R = p["left"], p["right"]; cl, cr = byn[str(L["clip"])], byn[str(R["clip"])]
    pl, pr = [os.path.join(ROOT, "clips", c["id"] + ".mp4") for c in (cl, cr)]
    lab = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lab)
    for x, c, s in ((4, cl, L), (484, cr, R)):
        dr.text((x + 2, (H + PH) // 2 + 8), str(c.get("sourceYear") or "date unknown"), fill="#ddd", font=F)
        dr.text((x + 2, (H + PH) // 2 + 36), (c.get("sourceTitle") or "")[:30], fill="#888", font=F)
    lp = os.path.join(tmp, f"l{k}.png"); lab.save(lp); o = os.path.join(tmp, f"{k:03d}.mp4")
    one = lambda i: f"[{i}:v]scale={PW}:{PH}:force_original_aspect_ratio=decrease:flags=lanczos,pad={PW}:{PH}:(ow-iw)/2:(oh-ih)/2:black,fps={fps},tpad=stop_mode=clone:stop_duration={dur + 1},setsar=1[v{i}]"
    fc = f"{one(0)};{one(1)};color=black:s={W}x{H}:r={fps}[bg];[bg][v0]overlay=4:{(H - PH) // 2}:shortest=0[a];[a][v1]overlay=484:{(H - PH) // 2}[b];[b][2:v]overlay=0:0,format=yuv420p[out]"
    run("ffmpeg", "-y", "-v", "error", "-ss", f"{L['in']:.3f}", *(["-t", str(L["t"])] if L.get("t") else []), "-i", pl, "-ss", f"{R['in']:.3f}", *(["-t", str(R["t"])] if R.get("t") else []), "-i", pr, "-loop", "1", "-i", lp, "-filter_complex", fc, "-map", "[out]", "-frames:v", str(round(dur * fps)), "-c:v", "libx264", "-crf", "16", "-preset", "medium", o)
    parts.append(o); chan.append((T, dur, pl, L, pr, R))
    for side, c, s, pth in (("left", cl, L, pl), ("right", cr, R, pr)):
        used = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pth], capture_output=True, text=True).stdout) - s["in"]
        led.append({"pair": k + 1, "side": side, "at": round(T, 3), "dur": dur, "source": c.get("sourceTitle"), "year": c.get("sourceYear"), "slug": c.get("sourceSlug"), "clip": c["id"], "source_in": round(c["startSeconds"] + s["in"], 3), "source_out": round(c["startSeconds"] + min(s["in"] + dur, s["in"] + used), 3), "transforms": (["last frame held"] if used < dur else []) + ["reduced to half frame, side by side"], "why": p.get("why", "")})
    T += dur
N = int(T * SR); LR = np.zeros((2, N), dtype=np.float32)
for t, dur, pl, L, pr, R in chan:
    for ci, (pth, s) in enumerate(((pl, L), (pr, R))):
        a = snd(pth, s["in"], dur) * s.get("gain", 1); o = int(t * SR); e = min(N, o + a.size); LR[ci, o:e] += a[:e - o]
LR = np.clip(LR, -1, 1); w = os.path.join(tmp, "m.f32"); LR.T.astype(np.float32).tofile(w); lst = os.path.join(tmp, "l.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts)); out = os.path.join(d, film + ".mp4")
run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", w, "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{T:.3f}", out)
json.dump({"film": film, "duration": round(T, 3), "shots": led}, open(os.path.join(d, "ledger.json"), "w"), indent=1); print(out, f"{T:.2f}s")
