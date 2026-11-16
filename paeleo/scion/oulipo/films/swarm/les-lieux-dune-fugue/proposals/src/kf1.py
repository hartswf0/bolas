"""KF1 Bench in the Door (warm stone). Archive-led direction.
Door plate: Highsmith, Columbus courthouse doorway (LoC 2010719611, no known restrictions).
Memory: Highsmith, park bench Sacramento (LoC 2013633886, no known restrictions).
Occlusion compositing: the memory is visible only through the door's dark."""
import sys
sys.path.insert(0, sys.path[0])
from common import *

W, H = 1280, 720
door = load(SRC + "/hs_10700_10776.jpg")          # 2000x1333
plate = fit_crop(door, (160, 225, 1760, 1125), (W, H))
plate = warm(plate, keep=0.18, gamma=0.95)

# opening in plate coords (measured): x 380..639, y 155..696
ox0, oy0, ox1, oy1 = 372, 98, 672, 716
mem = load(SRC + "/bench/sac_23429.jpg")
mw, mh = ox1 - ox0, oy1 - oy0
memc = fit_crop(mem, (560, 560, 560 + 480, 560 + 1000), (mw, mh))
# memory grade: colder, paler, lower contrast: another time
mL = lum(memc)
memg = np.stack([mL * 0.86 + 0.06, mL * 0.90 + 0.06, mL * 0.98 + 0.07], -1)
memg = (0.30 + (memg - 0.35) * 0.9) * 0.72

# matte: where the plate is dark (the opening), feathered; stone stays in front
pl = lum(plate)
m = np.clip((0.30 - pl) / 0.18, 0, 1)
box = np.zeros((H, W), np.float32); box[oy0:oy1, ox0:ox1] = 1
m = m * box
mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
m = np.asarray(mi).astype(np.float32) / 255 * 0.60     # frame at ~60% of the 3 s fade-in

layer = np.zeros_like(plate); layer[oy0:oy1, ox0:ox1] = memg
# screen blend through the matte
scr = 1 - (1 - plate) * (1 - layer)
out = plate * (1 - m[..., None]) + scr * m[..., None]

# 16 mm softness and gentle vignette (on the composite, not to fake the source)
yy, xx = np.mgrid[0:H, 0:W]
v = 1 - 0.22 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
out = out * v[..., None]
im = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
d = ImageDraw.Draw(im)
mono = font("mono", 15)
d.rectangle((0, 0, W, 62), fill=(16, 13, 10))
d.text((22, 18), "P01 porte · capture 2 (même position, plus tard)", font=mono, fill=(230, 220, 196))
d.text((22, 38), "mémoire: P03 banc · « vers l'hiver » = intervalle · lien INFÉRÉ", font=mono, fill=(214, 170, 120))
d.text((W - 120, 18), "00:31 / 00:56", font=mono, fill=(230, 220, 196))
ser = font("serif", 34)
cap = "« Le banc, c'était l'hiver, à peu près. »"
tw = d.textlength(cap, font=ser)
d.text(((W - tw) / 2 + 1, H - 66 + 1), cap, font=ser, fill=(10, 8, 6))
d.text(((W - tw) / 2, H - 66), cap, font=ser, fill=(242, 234, 214))
im.save(OUT + "/kf-1.png")
print("ok")
