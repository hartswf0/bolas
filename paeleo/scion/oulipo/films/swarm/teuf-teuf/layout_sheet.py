import sys, json, subprocess, os
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/teuf-teuf")
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import layout_wall as L
D = L.OUT; LW = L.ROOT + "/films/sources/teuf-teuf/layout-wall"
os.makedirs(LW, exist_ok=True)
ref = Image.open(L.REF).convert("RGB")
A = Image.open(D + "/frameA.png"); B = Image.open(D + "/frameB.png")
AG = Image.open(D + "/frameA_with_ghosts.png"); AT = Image.open(D + "/frameA_title.png")
mref = L.measure(np.asarray(ref))
# band masks for A / B
master, bands, _ = L.build_master()
mm = {}
for nm, cam, im in (("A", L.CAM_A, A), ("B", L.CAM_B, B)):
    tm = L.to_cam(bands["top"], cam) > 0.5; bm = L.to_cam(bands["bottom"], cam) > 0.5
    mm[nm] = L.measure(np.asarray(im), tm, bm)
mm["A_with_title_and_ghosts"] = L.measure(np.asarray(AG))
# sheet
cw = 760; f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
def fit(im): return im.resize((cw, int(im.height * cw / im.width)), Image.LANCZOS)
tiles = [("REFERENCE teuf.webp (Cite Films still) - not used in the film", fit(ref), mref),
         ("FRAME A (wide) - toned real Cueva rock + handmade charcoal", fit(A), mm["A"]),
         ("FRAME A + title + ghosts 1.2/3.0/8.0 m", fit(AT), None),
         ("FRAME B (x2.2 close-up, stone rear at tau 2.2)", fit(B), mm["B"])]
th = max(t[1].height for t in tiles)
sheet = Image.new("RGB", (cw * 2 + 30, (th + 110) * 2 + 10), (24, 24, 20))
d = ImageDraw.Draw(sheet)
for i, (lab, im, m) in enumerate(tiles):
    x = 10 + (i % 2) * (cw + 10); y = 10 + (i // 2) * (th + 110)
    sheet.paste(im, (x, y + 22)); d.text((x, y), lab, font=f, fill=(235, 230, 205))
    if m:
        t = (f"pale(blur>150) {m['pale_fraction']*100:.0f}%  median rgb {tuple(m['pale_median_rgb'])}  lum {m['pale_median_lum']}\n"
             f"below 60: {m['frac_below_60']*100:.1f}%")
        if m.get("top_band_mean_rgb") or m.get("bottom_band_mean_rgb"):
            t += f"   bands top {m.get('top_band_mean_rgb')} bottom {m.get('bottom_band_mean_rgb')}"
        d.text((x, y + 26 + im.height), t, font=f, fill=(200, 196, 170))
# overlay of ghosts on A in the third tile instead: replace with ghosts image
sheet.paste(fit(Image.blend(AT, AG, 0.5)), (10, 10 + th + 110 + 22))
sheet.save(L.ROOT + "/films/swarm/teuf-teuf/layout-vs-ref.jpg", quality=90)
json.dump(dict(ref=mref, ours=mm), open(LW + "/measurements.json", "w"), indent=1)
# title reveal preview over frame A: 1.2 s write-on + 1 s hold, 24 fps
fr = LW + "/title_preview"; os.makedirs(fr, exist_ok=True)
lumA = np.load(D + "/frameA_lum.npy")
rubA = np.asarray(Image.open(D + "/title_rub_A.png")).astype(np.float32) / 255
for k in range(53):
    j = min(k, 28)
    a = np.asarray(Image.open(f"{D}/title_reveal/title_{j:02d}.png")).astype(np.float32) / 255
    rub = rubA * min(1.0, (k + 6) / 12)                          # the rub goes on first, quickly
    l = lumA * (1 - rub) + 0.26 * rub
    l = l * (1 - a) + 0.99 * a
    Image.fromarray(L.print_rgb(l, 1)).save(f"{fr}/f{k:03d}.png")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", fr + "/f%03d.png", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-crf", "18", LW + "/title_reveal_preview.mp4"], check=True)
print(json.dumps(dict(ref=mref, ours=mm)))
