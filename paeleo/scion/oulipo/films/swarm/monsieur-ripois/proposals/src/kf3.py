"""KF3 - Le reçu sur la table: archive-led. Foraged Bubley print (LoC 2017848680) as the present-tense
encounter; a handmade pawn receipt is printed, filled in by hand, then laid on the photographed table by
a perspective warp, with contact shadow matching the print's key light."""
import sys; sys.path.insert(0, __file__.rsplit('/', 1)[0])
import numpy as np, cv2, json
from PIL import Image, ImageDraw, ImageFilter
from common import *

g = Image.open(SRC + "8d27149.jpg").convert("L").crop((280, 230, 980, 755))   # 700x525, 4:3
PW, PH = 960, 720
g = np.array(g.resize((PW, PH), Image.LANCZOS)).astype(np.float32)

# ---- the receipt: a handmade printed form (paper, rules, type, then handwriting) ----
RW, RH = 900, 520
r = Image.new("L", (RW, RH), 228); d = ImageDraw.Draw(r)
d.rectangle([14, 14, RW - 15, RH - 15], outline=60, width=3); d.rectangle([24, 24, RW - 25, RH - 25], outline=90, width=1)
d.text((RW / 2, 64), "PRÊT SUR GAGES", font=font(SERIF_B, 54), fill=40, anchor="mm")
d.text((RW / 2, 112), "BUREAU AUXILIAIRE N° 7  ·  RECONNAISSANCE", font=font(SERIF, 26), fill=55, anchor="mm")
d.line([60, 140, RW - 60, 140], fill=70, width=2)
f = font(MONO, 26); y0 = 172
for i, lab in enumerate(["N°", "Engagé le", "Objet", "Prêt", "Déposant"]):
    y = y0 + i * 62; d.text((70, y), lab + " :", font=f, fill=55)
    d.line([250, y + 34, RW - 70, y + 34], fill=120, width=1)
hw = font(SERIF_I, 38)   # the clerk's hand
vals = ["48 112", "14 mars 1953", "une bague or, un brillant", "9 000 F", "A. R."]
for i, v in enumerate(vals):
    d.text((262, y0 + i * 62 - 6), v, font=hw, fill=28)
# stamp, slightly off-axis, in a lighter ink
st = Image.new("L", (300, 120), 0); sd = ImageDraw.Draw(st)
sd.rounded_rectangle([4, 4, 296, 116], 14, outline=255, width=5); sd.text((150, 60), "ENGAGÉ", font=font(SERIF_B, 52), fill=255, anchor="mm")
st = st.rotate(9, expand=True, resample=Image.BICUBIC)
r.paste(Image.new("L", st.size, 120), (560, 300), st.point(lambda v: v * 0.55))
ra = np.array(r).astype(np.float32)
ra += cv2.GaussianBlur(rng.normal(0, 1, ra.shape).astype(np.float32), (0, 0), 1.5) * 6   # paper tooth
# a fold across the middle
ra[:, RW // 2 - 2:RW // 2 + 2] *= 0.86; ra[:, RW // 2 + 2:] *= 0.95

# ---- lay it on the table plane (perspective from the table edge and the ashtray ellipse) ----
dst = np.float32([[262, 630], [660, 620], [742, 790], [196, 806]])
src = np.float32([[0, 0], [RW, 0], [RW, RH], [0, RH]])
M = cv2.getPerspectiveTransform(src, dst)
warp = cv2.warpPerspective(ra, M, (PW, PH), flags=cv2.INTER_AREA)
mask = cv2.warpPerspective(np.ones((RH, RW), np.float32), M, (PW, PH), flags=cv2.INTER_AREA)
# light falls off toward the camera like the table in the print; the key is high-left
fall = np.linspace(1.0, 0.62, PH)[:, None] * np.linspace(0.95, 0.78, PW)[None, :]
warp = warp * fall * 0.80
warp = cv2.GaussianBlur(warp, (0, 0), 0.9)          # match the print's focus
sh = cv2.GaussianBlur(np.roll(np.roll(mask, 6, 0), 9, 1), (0, 0), 6)
out = g * (1 - 0.45 * sh * (1 - mask))
out = out * (1 - mask) + warp * mask
pic = grain(silver(np.clip(out, 0, 255)), 6, 3)
im = Image.fromarray(pic)
fr = pillar(im)
subtitle(fr, "« Je la lui ai rendue le 14 mars, en main propre. »", 576)
fr.save(OUT + "kf-3.png")
json.dump({"receipt_quad": dst.tolist(), "source": "LoC 2017848680"}, open(OUT + "src/kf3-layout.json", "w"), indent=1)
print("ok")
