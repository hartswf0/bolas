"""Contact sheets: each era's A and B crops beside its reference, with 6-colour palettes and tone numbers (PIL).
Run: python3 -I contact.py"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OUL, PLATES, dump

def stats(im):
    a = np.asarray(im.convert("RGB"), np.float32); L = a @ np.array([0.299, 0.587, 0.114], np.float32)
    h, w = L.shape; c = L[h//3:2*h//3, w//3:2*w//3].mean()
    k = np.concatenate([L[:h//5, :w//5].ravel(), L[:h//5, -w//5:].ravel(), L[-h//5:, :w//5].ravel(), L[-h//5:, -w//5:].ravel()]).mean()
    q = im.convert("RGB").quantize(6, method=Image.MEDIANCUT); pal = q.getpalette()[:18]
    cnt = sorted(q.getcolors(), reverse=True)
    hsv = np.asarray(im.convert("RGB").convert("HSV"), np.float32)
    return {"lt40": round(float((L < 40).mean() * 100), 1), "gt200": round(float((L > 200).mean() * 100), 1),
            "median": round(float(np.median(L)), 1), "p5_p95": [round(float(np.percentile(L, 5))), round(float(np.percentile(L, 95)))],
            "corner_centre": round(float(k / max(c, 1)), 2), "R_minus_B": round(float((a[..., 0] - a[..., 2]).mean()), 1),
            "sat": round(float(hsv[..., 1].mean() / 255), 3),
            "palette": ["#%02x%02x%02x" % tuple(pal[3*i:3*i+3]) for _, i in cnt]}

def tile(im, label, s):
    t = Image.new("RGB", (480, 330), (20, 20, 20)); t.paste(im.convert("RGB").resize((480, 270), Image.LANCZOS), (0, 0))
    d = ImageDraw.Draw(t)
    d.text((4, 273), label, fill="white")
    d.text((4, 287), f"<40 {s['lt40']}%  >200 {s['gt200']}%  med {s['median']}  c/c {s['corner_centre']}  sat {s['sat']}", fill=(200, 200, 200))
    for i, hx in enumerate(s["palette"]):
        d.rectangle([4 + i * 79, 303, 78 + i * 79, 326], fill=hx); d.text((6 + i * 79, 309), hx, fill="white" if int(hx[1:3], 16) < 128 else "black")
    return t

REF = f"{OUL}/assets/references"
out = {}
for era, ref in (("1959", "orchard3.webp"), ("2009", "orchardAK08.webp"), ("2059", "orchardAK17.webp")):
    r = Image.open(f"{REF}/{ref}"); A = Image.open(f"{PLATES}/{era}/crop_A_start.png"); B = Image.open(f"{PLATES}/{era}/crop_B_start.png")
    sr, sa, sb = stats(r), stats(A), stats(B)
    S = Image.new("RGB", (1440, 330))
    S.paste(tile(r, f"REFERENCE {ref}", sr), (0, 0)); S.paste(tile(A, f"{era} plate crop A (start)", sa), (480, 0)); S.paste(tile(B, f"{era} plate crop B (start)", sb), (960, 0))
    if era == "1959":
        I = Image.open(f"{PLATES}/1959/crop_B_insert_start.png"); si = stats(I)
        S2 = Image.new("RGB", (1440, 660)); S2.paste(S, (0, 0)); S2.paste(tile(I, "1959 beak insert (start)", si), (480, 330)); S = S2
        out["1959_insert"] = si
    p = f"{PLATES}/contact_{era}.jpg"; S.save(p, quality=90)
    out[era] = {"reference": ref, "ref": sr, "A": sa, "B": sb, "sheet": p}
dump(out, f"{PLATES}/contact_stats.json")
print(json.dumps({k: (v["ref"]["palette"], v["A"]["palette"]) for k, v in out.items() if "ref" in v}))
