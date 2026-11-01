#!/usr/bin/env python3
"""Fetch clips and lay them out as timecoded filmstrips with their waveform, so a cut can be chosen by eye and ear.
usage: look.py <film> <n>[:step] [<n>[:step] ...]     n is the #number on a forage sheet; step is seconds between frames (default: fit 12 frames)
       look.py <film> <n>:step:in:out   only that stretch of the clip"""
import json, os, subprocess, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); F = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 11)
def run(*a): return subprocess.run(a, capture_output=True, text=True)
def fetch(c):
    p = os.path.join(ROOT, "clips", c["id"] + ".mp4")
    if not os.path.exists(p) or not os.path.getsize(p):
        with urllib.request.urlopen(urllib.request.Request(c["videoUrl"], headers={"user-agent": "cineosis-44-research"}), timeout=180) as r: open(p + ".tmp", "wb").write(r.read())
        os.replace(p + ".tmp", p)
    return p
def probe(p):
    o = json.loads(run("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", p).stdout); v = [s for s in o["streams"] if s["codec_type"] == "video"][0]
    return float(o["format"]["duration"]), v["width"], v["height"], any(s["codec_type"] == "audio" for s in o["streams"]), v["r_frame_rate"]
def main():
    film = sys.argv[1]; db = json.load(open(os.path.join(ROOT, "films", film, "forage.json"))); byn = {c["n"]: c for c in db["clips"].values()}
    os.makedirs(os.path.join(ROOT, "films", film, "strips"), exist_ok=True); rows = []
    for a in sys.argv[2:]:
        bits = a.split(":"); c = byn[int(bits[0])]; p = fetch(c); dur, w, h, au, fps = probe(p)
        i = float(bits[2]) if len(bits) > 2 else 0; o = min(float(bits[3]), dur) if len(bits) > 3 else dur
        step = float(bits[1]) if len(bits) > 1 and bits[1] else max((o - i) / 12, 0.25); ts = []; t = i + step / 2
        while t < o and len(ts) < 36: ts.append(t); t += step
        fw, fh = 200, 150; cols = 6; n = len(ts); r = (n + cols - 1) // cols
        H = 34 + r * fh + (r * 36 if au else 0); sh = Image.new("RGB", (cols * fw, H), "#111"); d = ImageDraw.Draw(sh)
        d.text((4, 2), f"#{c['n']} {c.get('sourceTitle')} ({c.get('sourceYear')}) dur {dur:.1f}s {w}x{h} {fps} {'SOUND' if au else 'SILENT'} src@{c['startSeconds']:.1f}", fill="#fc6", font=F)
        d.text((4, 16), c["id"], fill="#888", font=F); wav = None
        if au:
            wp = "/tmp/_w.png"; run("ffmpeg", "-y", "-v", "error", "-ss", str(i), "-t", str(o - i), "-i", p, "-filter_complex", f"[0:a]aformat=channel_layouts=mono,compand,showwavespic=s={cols*fw*r}x30:colors=#7cf", "-frames:v", "1", wp)
            try: wav = Image.open(wp).convert("RGB")
            except Exception: wav = None
        for k, t in enumerate(ts):
            fp = f"/tmp/_f{k}.jpg"; run("ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", p, "-frames:v", "1", "-vf", f"scale={fw-2}:{fh-2}:force_original_aspect_ratio=decrease", "-q:v", "3", fp)
            x, y = fw * (k % cols), 34 + (k // cols) * (fh + (36 if au else 0))
            try: sh.paste(Image.open(fp), (x + 1, y + 1))
            except Exception: pass
            d.rectangle((x + 1, y + 1, x + 52, y + 14), fill="#000"); d.text((x + 3, y + 2), f"{t:.2f}", fill="#fff", font=F)
        if wav:
            for rr in range(r):
                t0 = rr * cols; y = 34 + rr * (fh + 36) + fh + 2
                sh.paste(wav.crop((t0 * fw // 1 * 1, 0, (t0 + cols) * fw, 30)) if False else wav.crop((rr * cols * fw, 0, (rr + 1) * cols * fw, 30)), (0, y))
        out = os.path.join(ROOT, "films", film, "strips", f"{c['n']}" + (f"_{i:.0f}-{o:.0f}" if len(bits) > 2 else "") + ".jpg"); sh.save(out, quality=80); print(out)
main()
