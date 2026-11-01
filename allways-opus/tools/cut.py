#!/usr/bin/env python3
"""Render a hand-written edit list. Nothing here chooses anything: every in, out and sound comes from films/<film>/edl.json.
edl = {"size":[960,720], "fps":24, "shots":[{"clip":"<n or id>", "in":s, "out":s, "why":"...",
         "sound":"own"|"none"|[{"clip":..,"in":..,"out":..,"at":offset from shot head,"gain":1,"fade":0.03}...], "gain":1, "lead":s (own sound starts s before the cut), "tail":s (own sound rings s after it),
         "speed":1, "vf":"extra ffmpeg filter"}]}
Writes films/<film>/<film>.mp4 and ledger.json (shot -> source film, source seconds, transformations). usage: cut.py <film> [out_suffix]"""
import json, os, subprocess, sys, tempfile
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SR = 48000
def run(*a):
    r = subprocess.run(a, capture_output=True)
    if r.returncode: sys.exit(r.stderr.decode()[-1500:])
    return r.stdout
def audio(path, i, dur):
    o = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(i,0):.3f}", "-t", f"{dur:.3f}", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(o, dtype=np.float32).copy()
def main():
    film = sys.argv[1]; suf = sys.argv[2] if len(sys.argv) > 2 else ""; d = os.path.join(ROOT, "films", film)
    e = json.load(open(os.path.join(d, f"edl{suf}.json"))); db = json.load(open(os.path.join(d, "forage.json")))
    byn = {str(c["n"]): c for c in db["clips"].values()}; byn.update({i: c for i, c in db["clips"].items()})
    W, H = e.get("size", [960, 720]); fps = e.get("fps", 24); tmp = tempfile.mkdtemp(); parts = []; ledger = []; T = 0.0; marks = []
    for k, s in enumerate(e["shots"]):
        sp = s.get("speed", 1); hold = s.get("hold", 0); dur = round(((s["out"] - s["in"]) / sp + hold) * fps) / fps
        if s.get("file"): src = s["file"] if os.path.isabs(s["file"]) else os.path.join(d, s["file"]); c = {"id": s["file"], "sourceTitle": s.get("title", "derived"), "startSeconds": 0, "sourceSlug": None}
        else: c = byn[str(s["clip"])]; src = os.path.join(ROOT, "clips", c["id"] + ".mp4")
        vf = [f"setpts=(PTS-STARTPTS)/{sp}"] if sp != 1 else []
        if s.get("vf"): vf.append(s["vf"])
        vf += ([f"tpad=stop_mode=clone:stop_duration={hold}"] if hold else []) + [f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos", f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black", f"fps={fps}", "setsar=1", "format=yuv420p"]
        p = os.path.join(tmp, f"{k:03d}.mp4")
        run("ffmpeg", "-y", "-v", "error", "-ss", f"{s['in']:.3f}", "-t", f"{(s['out']-s['in']):.3f}", "-i", src, "-an", "-vf", ",".join(vf), "-frames:v", str(round(dur * fps)), "-c:v", "libx264", "-crf", "16", "-preset", "medium", p)
        if s.get("caption"):
            from PIL import Image, ImageDraw, ImageFont
            cap = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(cap); fnt = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", e.get("capsize", 26)); lines = s["caption"].split("\n")
            for li, tx in enumerate(lines):
                y = H - 22 - (e.get("capsize", 26) + 10) * (len(lines) - li); bb = dr.textbbox((24, y), tx, font=fnt); dr.rectangle((bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4), fill=(0, 0, 0, 215)); dr.text((24, y), tx, fill="#eee", font=fnt)
            cp = os.path.join(tmp, f"c{k}.png"); cap.save(cp); p2 = p[:-4] + "c.mp4"
            run("ffmpeg", "-y", "-v", "error", "-i", p, "-i", cp, "-filter_complex", "[0:v][1:v]overlay=0:0,format=yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "medium", p2); p = p2
        parts.append(p); marks.append((T, dur, s, src, c, sp))
        ledger.append({"position": k + 1, "at": round(T, 3), "dur": round(dur, 3), "source": c.get("sourceTitle"), "year": c.get("sourceYear"), "slug": c.get("sourceSlug"), "clip": c["id"],
                       "source_in": round(c.get("startSeconds", 0) + s["in"], 3), "source_out": round(c.get("startSeconds", 0) + s["out"], 3), "transforms": [x for x in [f"speed {sp}" if sp != 1 else None, s.get("vf"), f"last frame held {hold}s" if hold else None] if x], "why": s.get("why", "")})
        T += dur
    pad = e.get("tailpad", 0.0); N = int((T + pad + 4) * SR); mix = np.zeros(N, dtype=np.float32)
    def lay(a, t, gain=1.0, fi=0.012, fo=0.012):
        if a.size == 0: return
        a = a * gain; n = a.size; f = int(fi * SR); g = int(fo * SR)
        if f: a[:min(f, n)] *= np.linspace(0, 1, min(f, n))
        if g: a[-min(g, n):] *= np.linspace(1, 0, min(g, n))
        o = int(t * SR)
        if o < 0: a = a[-o:]; o = 0
        mix[o:o + a.size] += a[:max(0, N - o)]
    for t, dur, s, src, c, sp in marks:
        so = s.get("sound", "own")
        if so == "own":
            lead, tail = s.get("lead", 0), s.get("tail", 0)
            lay(audio(src, s["in"] - lead, s["out"] - s["in"] + lead + tail), t - lead, s.get("gain", 1), s.get("fi", 0.012), s.get("fo", 0.012))
        elif isinstance(so, list):
            for x in so:
                if x.get("file"):
                    fp = x["file"] if os.path.isabs(x["file"]) else os.path.join(d, x["file"]); ld = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", fp], capture_output=True, text=True).stdout)
                    lay(audio(fp, x.get("in", 0), x.get("out", ld) - x.get("in", 0)), t + x.get("at", 0), x.get("gain", 1), x.get("fi", 0.01), x.get("fo", 0.05))
                    ledger[marks.index((t, dur, s, src, c, sp))].setdefault("sound_from", []).append({"source": x.get("credit", x["file"]), "authored": True}); continue
                cc = byn[str(x["clip"])]; lay(audio(os.path.join(ROOT, "clips", cc["id"] + ".mp4"), x["in"], x["out"] - x["in"]), t + x.get("at", 0), x.get("gain", 1), x.get("fi", 0.03), x.get("fo", 0.03))
                ledger[marks.index((t, dur, s, src, c, sp))].setdefault("sound_from", []).append({"source": cc.get("sourceTitle"), "year": cc.get("sourceYear"), "source_in": round(cc["startSeconds"] + x["in"], 3), "source_out": round(cc["startSeconds"] + x["out"], 3)})
    end = int((T + pad) * SR); mix = mix[:end]; pk = np.abs(mix).max() or 1
    if pk > 0.97: mix = np.tanh(mix * 1.0 / 0.97) * 0.97 if pk < 1.6 else mix / pk * 0.97
    wav = os.path.join(tmp, "m.f32"); mix.astype(np.float32).tofile(wav)
    lst = os.path.join(tmp, "l.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    out = os.path.join(d, f"{film}{suf}.mp4")
    run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", wav, "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-movflags", "+faststart", "-t", f"{T:.3f}", out)
    json.dump({"film": film, "duration": round(T, 3), "shots": ledger}, open(os.path.join(d, f"ledger{suf}.json"), "w"), indent=1)
    print(out, f"{T:.2f}s", len(parts), "shots")
main()
