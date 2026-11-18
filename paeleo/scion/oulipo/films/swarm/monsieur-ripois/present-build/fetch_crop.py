"""Fetch a crop of an uncompressed 8-bit gray single-strip LoC master TIFF by HTTP multi-range requests
(one byte range per row). Bytes are decoded only as raw pixels into numpy. Usage: url W off x0 y0 x1 y1 out.png"""
import subprocess, sys, re, numpy as np
from PIL import Image
url, W, OFF, x0, y0, x1, y1, out = sys.argv[1], *map(int, sys.argv[2:8]), sys.argv[8]
cw = x1 - x0; rows = list(range(y0, y1)); img = np.zeros((len(rows), cw), np.uint8)
hdrf = out + ".hdr"
for bi in range(0, len(rows), 300):
    rr = rows[bi:bi + 300]
    spec = ",".join(f"{OFF + r * W + x0}-{OFF + r * W + x1 - 1}" for r in rr)
    data = subprocess.run(["curl", "-sS", "--fail", "-A", "oulipo-film-research/1.0", "-H", f"Range: bytes={spec}", "-D", hdrf, url],
                          capture_output=True, check=True).stdout
    m = re.search(r"boundary=(\S+)", open(hdrf).read())
    bnd = ("--" + m.group(1)).encode()
    for p in data.split(bnd):
        if b"ontent-" not in p[:200] or b"\r\n\r\n" not in p: continue
        head, body = p.split(b"\r\n\r\n", 1)
        cr = re.search(rb"bytes (\d+)-(\d+)", head, re.I)
        if not cr: continue
        a, b = int(cr.group(1)), int(cr.group(2))
        r = (a - OFF) // W
        img[r - y0, :] = np.frombuffer(body[: b - a + 1], np.uint8)
Image.fromarray(img).save(out)
print("ok", img.shape)
