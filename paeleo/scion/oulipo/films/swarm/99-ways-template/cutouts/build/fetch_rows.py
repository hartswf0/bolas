"""Fetch a strided row/column window of an uncompressed one-row-per-strip 8-bit grey LoC master TIFF via
HTTP multi-range (multipart/byteranges). The response is parsed as bytes only; nothing is executed.
usage: python3 -I fetch_rows.py URL HDR.bin W H Y0 Y1 X0 X1 STRIDE OUT.png"""
import struct, subprocess, sys, re, os
import numpy as np
from PIL import Image
URL, HDR = sys.argv[1], sys.argv[2]
W, H, Y0, Y1, X0, X1, S = map(int, sys.argv[3:10]); OUT = sys.argv[10]
b = open(HDR, "rb").read()
E = "<" if b[:2] == b"II" else ">"
off = struct.unpack(E + "I", b[4:8])[0]; n = struct.unpack(E + "H", b[off:off + 2])[0]
so = None
for i in range(n):
    e = b[off + 2 + 12 * i: off + 14 + 12 * i]
    tag, typ, cnt = struct.unpack(E + "HHI", e[:8])
    if tag == 273: so = struct.unpack(E + "I", e[8:])[0]
offs = struct.unpack(E + "%dI" % H, b[so:so + 4 * H])
rows = list(range(Y0, Y1, S))
out = np.zeros((len(rows), (X1 - X0 + S - 1) // S), np.uint8)
tmp = OUT + ".part"; total = 0
for bi in range(0, len(rows), 200):
    chunk = rows[bi:bi + 200]
    rng = ",".join("%d-%d" % (offs[r] + X0, offs[r] + X1 - 1) for r in chunk)
    for attempt in range(5):
        hdrs = subprocess.run(["curl", "-sS", "--http1.1", "-A", "oulipo-film-research/1.0", "-H", "Range: bytes=" + rng,
                               "-D", "-", "-o", tmp, URL], capture_output=True, text=True).stdout
        m = re.search(r"boundary=([^\s;]+)", hdrs)
        if m: break
    data = open(tmp, "rb").read(); total += len(data)
    got = {}
    for p in data.split(("--" + m.group(1)).encode()):
        hm = re.search(rb"Content-Range: bytes (\d+)-(\d+)/", p)
        if hm: got[int(hm.group(1))] = p.split(b"\r\n\r\n", 1)[1][: X1 - X0]
    for j, r in enumerate(chunk):
        out[bi + j] = np.frombuffer(got[offs[r] + X0], np.uint8)[::S][: out.shape[1]]
os.remove(tmp)
Image.fromarray(out).save(OUT)
print(out.shape, "bytes", total)
