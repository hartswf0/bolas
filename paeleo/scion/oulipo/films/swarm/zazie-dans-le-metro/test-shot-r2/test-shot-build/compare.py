"""Reference beside 3 frames of the test shot, labelled, with PIL-measured metrics."""
import subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
SW = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/zazie-dans-le-metro"
REF = "/home/user/bolas/paeleo/scion/oulipo/assets/references/zazie1.webp"
def grab(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", f"{SW}/test-shot.mp4", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return Image.frombytes("RGB", (960, 540), raw).crop((120, 0, 840, 540))
def metrics(im):
    a = np.asarray(im).astype(np.float32); L = a.mean(2); S = np.asarray(im.convert("HSV"))[..., 1]
    return "luma p5 %d  p50 %d  p95 %d  max %d   sat %d" % (np.percentile(L, 5), np.percentile(L, 50), np.percentile(L, 95), L.max(), S.mean())
cells = [(Image.open(REF).convert("RGB").resize((720, 540), Image.LANCZOS), "REFERENCE  zazie1.webp (Malle 1960), scaled"),
         (grab(1.5 + 1 / 48), "7.50 s  full laugh, gust across the right eye (rue Royale, P1)"),
         (grab(2.0 + 1 / 48), "8.000 s  frame 192: JUMP CUT, same drawing, place de Clichy (P2)"),
         (grab(3.5 + 1 / 48), "9.50 s  eyes open on her tram, rack focus to the far plate")]
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
B = Image.new("RGB", (720 * 2 + 30, (540 + 62) * 2 + 20), (16, 16, 16)); d = ImageDraw.Draw(B)
for k, (im, lab) in enumerate(cells):
    x = 10 + (k % 2) * 730; y = 10 + (k // 2) * 612
    B.paste(im, (x, y)); d.text((x + 2, y + 546), lab, font=F, fill=(240, 226, 200)); d.text((x + 2, y + 570), metrics(im), font=f2, fill=(190, 180, 160))
B.save(f"{SW}/test-shot-compare.jpg", quality=88)
print([metrics(c[0]) for c in cells])
