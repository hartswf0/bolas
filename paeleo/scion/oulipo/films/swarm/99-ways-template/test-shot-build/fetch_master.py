"""Fetch every 3rd row (cols X0..X1) of the Rothstein master TIFF via HTTP multi-range.
Data parsed as bytes only; nothing from the download is executed."""
import struct, subprocess, sys, re, os
import numpy as np
from PIL import Image
URL = "https://tile.loc.gov/storage-services/master/pnp/fsa/8b16000/8b16700/8b16710u.tif"
D = sys.argv[1]
b = open(os.path.join(D, "hdr.bin"), "rb").read()
W, H = 13818, 10504
offs = struct.unpack("<%dI" % H, b[450:450 + 4 * H])
Y0, Y1, X0, X1, S = 300, 9600, 480, 13560, 3
rows = list(range(Y0, Y1, S))
out = np.zeros((len(rows), (X1 - X0 + S - 1) // S), np.uint8)
B = 200
for bi in range(0, len(rows), B):
    chunk = rows[bi:bi + B]
    rng = ",".join("%d-%d" % (offs[r] + X0, offs[r] + X1 - 1) for r in chunk)
    tmp = os.path.join(D, "part.bin")
    for attempt in range(4):
        hdrs = subprocess.run(["curl", "-sS", "-A", "oulipo-film-research/1.0", "-H", "Range: bytes=" + rng,
                               "-D", "-", "-o", tmp, URL], capture_output=True, text=True).stdout
        m = re.search(r"boundary=([^\s;]+)", hdrs)
        if m: break
    data = open(tmp, "rb").read()
    bnd = ("--" + m.group(1)).encode()
    parts = data.split(bnd)
    got = {}
    for p in parts:
        hm = re.search(rb"Content-Range: bytes (\d+)-(\d+)/", p)
        if not hm: continue
        s = int(hm.group(1)); body = p.split(b"\r\n\r\n", 1)[1][: X1 - X0]
        got[s] = body
    for j, r in enumerate(chunk):
        row = np.frombuffer(got[offs[r] + X0], np.uint8)
        out[bi + j] = row[::S][: out.shape[1]]
    print(bi, len(rows), flush=True)
os.remove(tmp)
Image.fromarray(out).save(os.path.join(D, "rothstein_master_s3.png"))
print(out.shape)
