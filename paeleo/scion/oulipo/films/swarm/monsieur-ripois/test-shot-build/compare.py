"""test-shot-compare.jpg: the reference beside 3 frames of the shot (extracted from the encoded mp4), labelled, equal height; plus tone stats."""
import subprocess, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
SW = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/monsieur-ripois/"
REF = "/home/user/bolas/paeleo/scion/oulipo/assets/references/ripois1.webp"
FI = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
def grab(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SW + "test-shot.mp4", "-vf", f"select=eq(n\\,{f})", "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.frombytes("RGB", (960, 540), raw).crop((120, 0, 840, 540))
def stats(im):
    a = np.asarray(im.convert("RGB")).astype(int); L = np.asarray(im.convert("L"))
    return {"p": [int(np.percentile(L, q)) for q in (1, 5, 25, 50, 75, 95, 99)], "chroma": round(float((a.max(-1) - a.min(-1)).mean()), 1)}
H = 420
ref = Image.open(REF).convert("RGB")
panels = [(ref, "Reference: Monsieur Ripois (1954) still"), (grab(13), "f13 · 17.04 s · shadow: box swallowed"),
          (grab(84), "f84 · 20.0 s · insert: slot empty"), (grab(200), "f200 · 24.83 s · « manquait. »: head −11°")]
St = {lab: stats(im) for im, lab in panels}
St["f150 two-shot before cue"] = stats(grab(150))
ims = [im.resize((int(im.width * H / im.height), H), Image.LANCZOS) for im, _ in panels]
Wt = sum(i.width for i in ims) + 10 * (len(ims) + 1)
out = Image.new("RGB", (Wt, H + 60), (16, 16, 16)); d = ImageDraw.Draw(out); f = ImageFont.truetype(FI, 19)
x = 10
for im, (_, lab) in zip(ims, panels):
    out.paste(im, (x, 10)); d.text((x + 4, H + 18), lab, font=f, fill=(225, 222, 214)); x += im.width + 10
out.save(SW + "test-shot-compare.jpg", quality=92)
json.dump(St, open(SW + "test-shot-build/tone-stats.json", "w"), indent=1)
print(json.dumps(St, indent=0))
