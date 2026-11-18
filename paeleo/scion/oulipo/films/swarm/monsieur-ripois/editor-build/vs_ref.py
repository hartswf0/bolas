"""Critic sheet: S1, S3b, S5 frames decoded from the master mp4 beside assets/references/ripois1.webp at equal height,
with measured L percentiles and mean chroma (picture area only). Also S2 paper flatness across drawings (repair 1)."""
import subprocess, numpy as np, json, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = "/home/user/bolas/paeleo/scion/oulipo/"
MP4 = ROOT + "assets/films/monsieur-ripois.mp4"
def grab(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", MP4, "-vf", f"select=eq(n\\,{f})", "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.frombytes("RGB", (960, 540), raw).crop((120, 0, 840, 540))
def stats(im, cap_crop=True):
    a = np.asarray(im).astype(np.float32)
    if cap_crop: a = a[:480]                       # exclude the caption line
    L = a.mean(2); ch = (a.max(2) - a.min(2)).mean()
    return dict(p5=round(float(np.percentile(L, 5)), 1), p50=round(float(np.percentile(L, 50)), 1), p99=round(float(np.percentile(L, 99)), 1), chroma=round(float(ch), 1))
ref = Image.open(ROOT + "assets/references/ripois1.webp").convert("RGB")
ref = ref.resize((int(ref.width * 540 / ref.height), 540), Image.LANCZOS)
frames = {"S1 f100": 100, "S3b f600": 600, "S5 f930": 930, "S5 f1000": 1000}
ims = {k: grab(f) for k, f in frames.items()}
st = {"ripois1.webp": stats(ref, False)}; st.update({k: stats(v) for k, v in ims.items()})
W = ref.width + 720 * len(ims); sheet = Image.new("RGB", (W, 600), (20, 20, 20)); sheet.paste(ref, (0, 0))
d = ImageDraw.Draw(sheet); fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
d.text((6, 548), "ripois1.webp (reference) " + json.dumps(st["ripois1.webp"]), font=fnt, fill=(230, 230, 230))
x = ref.width
for k, im in ims.items():
    sheet.paste(im, (x, 0)); d.text((x + 6, 548), k + " " + json.dumps(st[k]), font=fnt, fill=(230, 230, 230)); x += 720
sheet.save(ROOT + "films/swarm/monsieur-ripois/assembly-vs-ref.jpg", quality=90)
# S2 paper flatness: high-pass std of a flat paper patch (no figures) per drawing
hp = []
for f in range(216, 468, 2):
    a = np.asarray(grab(f).convert("L")).astype(np.float32)[100:160, 150:230]
    from PIL import ImageFilter
    b = np.asarray(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32)
    hp.append(float((a - b).std()))
st["S2_paper_highpass_std"] = dict(min=round(min(hp), 3), max=round(max(hp), 3), max_change_between_drawings=round(max(abs(hp[i + 1] - hp[i]) for i in range(len(hp) - 1)), 3))
json.dump(st, open(ROOT + "films/swarm/monsieur-ripois/assembly-vs-ref.json", "w"), indent=1)
print(json.dumps(st, indent=1))
