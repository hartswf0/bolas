"""Reference beside three frames of the test shot, labelled, with PIL measurements (python3 -I compare.py frames...)."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUL = "/home/user/bolas/paeleo/scion/oulipo"
REF = f"{OUL}/assets/references/orchard3.webp"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def stats(im):
    a = np.asarray(im.convert("RGB").resize((960, 540)), np.float32)
    L = a.mean(2)
    h, w = L.shape
    c = L[h // 3: 2 * h // 3, w // 3: 2 * w // 3].mean()
    k = np.concatenate([L[:h // 6, :w // 8].ravel(), L[:h // 6, -w // 8:].ravel(), L[-h // 6:, :w // 8].ravel(), L[-h // 6:, -w // 8:].ravel()]).mean()
    q = im.convert("RGB").quantize(6)
    pal = q.getpalette()[:18]
    cnt = sorted(q.getcolors(), reverse=True)
    hexes = ["#%02x%02x%02x" % tuple(pal[3 * i:3 * i + 3]) for _, i in cnt]
    return {"R-B": round(float((a[..., 0] - a[..., 2]).mean()), 1), "<40": round(float((L < 40).mean() * 100), 1),
            ">200": round(float((L > 200).mean() * 100), 1), "median": int(np.median(L)),
            "p5/p95": [int(np.percentile(L, 5)), int(np.percentile(L, 95))], "corner/centre": round(float(k / c), 2),
            "palette": hexes}


def main(frames, labels, out):
    ref = Image.open(REF).convert("RGB")
    tiles = [(ref, "REFERENCE  orchard3 (1959 section)")] + [(Image.open(f).convert("RGB"), l) for f, l in zip(frames, labels)]
    W, H = 640, 360
    sheet = Image.new("RGB", (2 * W + 30, 2 * (H + 92) + 20), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    fnt = ImageFont.truetype(FONT, 15)
    sm = ImageFont.truetype(FONT, 12)
    for i, (im, lab) in enumerate(tiles):
        x, y = 10 + (i % 2) * (W + 10), 10 + (i // 2) * (H + 92)
        sheet.paste(im.resize((W, H)), (x, y))
        s = stats(im)
        d.text((x, y + H + 6), lab, font=fnt, fill=(235, 235, 235))
        d.text((x, y + H + 28), f"<40: {s['<40']}%   >200: {s['>200']}%   median {s['median']}   p5/p95 {s['p5/p95']}   corner/centre {s['corner/centre']}   R-B {s['R-B']}", font=sm, fill=(200, 200, 200))
        for j, hx in enumerate(s["palette"]):
            d.rectangle((x + j * 60, y + H + 50, x + j * 60 + 56, y + H + 66), fill=hx)
            d.text((x + j * 60 + 2, y + H + 70), hx, font=sm, fill=(180, 180, 180))
        print(lab, s)
    sheet.save(out, quality=90)


if __name__ == "__main__":
    n = (len(sys.argv) - 2) // 2
    main(sys.argv[1:1 + n], sys.argv[1 + n:1 + 2 * n], sys.argv[-1])
