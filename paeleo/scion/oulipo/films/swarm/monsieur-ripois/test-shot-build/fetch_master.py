"""Fetch a crop of LoC 2017831564 master TIFF (8d04830u.tif, 12901x9837, 8-bit gray, uncompressed,
single strip at offset 8) by HTTP multi-range requests: one byte range per row, only the crop columns.
Output: crop as PNG (decoded only as raw bytes -> numpy; nothing executed)."""
import subprocess, sys, re, numpy as np
from PIL import Image
URL = "https://tile.loc.gov/storage-services/master/pnp/fsa/8d04000/8d04800/8d04830u.tif"
OUT = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/test-shot/"
W, H, OFF = 12901, 9837, 8
S = W / 1024.0
x0, x1, y0, y1 = [int(round(v * S)) for v in (220, 840, 330, 740)]
cw = x1 - x0
rows = list(range(y0, y1))
img = np.zeros((len(rows), cw), np.uint8)
B = 300
for bi in range(0, len(rows), B):
    rr = rows[bi:bi + B]
    spec = ",".join(f"{OFF + r * W + x0}-{OFF + r * W + x1 - 1}" for r in rr)
    data = subprocess.run(["curl", "-sS", "--fail", "-A", "oulipo-film-research/1.0", "-H", f"Range: bytes={spec}",
                           "-D", OUT + "h.txt", URL], capture_output=True, check=True).stdout
    hdr = open(OUT + "h.txt").read()
    m = re.search(r"boundary=(\S+)", hdr)
    if not m: raise SystemExit("no multipart: " + hdr[:300])
    bnd = ("--" + m.group(1)).encode()
    parts = [p for p in data.split(bnd) if b"Content-Range" in p or b"content-range" in p]
    for p in parts:
        head, body = p.split(b"\r\n\r\n", 1)
        cr = re.search(rb"bytes (\d+)-(\d+)", head, re.I)
        a, b = int(cr.group(1)), int(cr.group(2))
        body = body[: b - a + 1]
        r = (a - OFF) // W
        img[r - y0, :] = np.frombuffer(body, np.uint8)
    print(bi, len(parts), flush=True)
Image.fromarray(img).save(OUT + "v0-master-crop.png")
open(OUT + "v0-master-crop.txt", "w").write(f"crop of {URL}\nmaster px x {x0}..{x1}, y {y0}..{y1}; service-jpg coords x 220..840 y 330..740 (scale {S:.4f})\n")
print("ok", img.shape)
