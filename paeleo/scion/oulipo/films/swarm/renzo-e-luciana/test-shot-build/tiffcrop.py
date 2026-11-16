"""Fetch a region of an LoC master TIFF (uncompressed) with HTTP Range requests and box-downsample it.
Parses the TIFF IFD ourselves (data only). Usage: tiffcrop.py URL OUT.png fx0 fy0 fx1 fy1 K [G]
  crop in fractions of the full frame; K = output downsample factor; G = rows averaged per K rows (default K)."""
import sys, struct, urllib.request, numpy as np
from PIL import Image
UA = 'oulipo-film-research/1.0'
url, out = sys.argv[1], sys.argv[2]; fx0, fy0, fx1, fy1 = map(float, sys.argv[3:7]); K = int(sys.argv[7]); G = int(sys.argv[8]) if len(sys.argv) > 8 else K
got = 0
def rng(a, n):
    global got
    r = urllib.request.Request(url, headers={'User-Agent': UA, 'Range': f'bytes={a}-{a + n - 1}'})
    for k in range(4):
        try:
            d = urllib.request.urlopen(r, timeout=120).read(); got += len(d); return d
        except Exception as e: err = e
    raise err
h = rng(0, 16); bo = '<' if h[:2] == b'II' else '>'
assert struct.unpack(bo + 'H', h[2:4])[0] == 42
ifd = struct.unpack(bo + 'I', h[4:8])[0]
n = struct.unpack(bo + 'H', rng(ifd, 2))[0]; ent = rng(ifd + 2, n * 12)
T = {}
for i in range(n):
    tag, typ, cnt = struct.unpack(bo + 'HHI', ent[i * 12: i * 12 + 8]); val = ent[i * 12 + 8: i * 12 + 12]
    sz = {1: 1, 3: 2, 4: 4, 5: 8}.get(typ, 1); fmt = {1: 'B', 3: 'H', 4: 'I', 5: 'II'}.get(typ, 'B')
    if sz * cnt <= 4: v = list(struct.unpack(bo + fmt * cnt, val[:sz * cnt])) if typ != 5 else None
    else: v = ('off', struct.unpack(bo + 'I', val)[0], typ, cnt)
    T[tag] = v
W, H = T[256][0], T[257][0]; bps = T[258]; comp = T[259][0]; spp = T.get(277, [1])[0]
if isinstance(bps, tuple): bps = [8]
print('tiff', W, H, 'bps', bps, 'comp', comp, 'spp', spp, 'rps', T.get(278), 'planar', T.get(284))
assert comp == 1, 'compressed TIFF not supported'
def arr(v):
    if v[0] != 'off': return v
    _, off, typ, cnt = v; sz = 2 if typ == 3 else 4
    return list(struct.unpack(bo + ('H' if typ == 3 else 'I') * cnt, rng(off, sz * cnt)))
so = arr(T[273]); rps = T.get(278, [H])[0]
B = bps[0] // 8 * spp; row = W * B
x0, x1 = int(fx0 * W) // K * K, int(fx1 * W) // K * K; y0, y1 = int(fy0 * H) // K * K, int(fy1 * H) // K * K
from concurrent.futures import ThreadPoolExecutor
def one(y):
    ys = y + (K - G) // 2                        # central G rows of each K block
    acc = None
    # rows ys..ys+G-1 are contiguous if within one strip (or strips are contiguous)
    s = ys // rps; off = so[s] + (ys - s * rps) * row
    d = rng(off + x0 * B, (G - 1) * row + (x1 - x0) * B) if G > 1 else rng(off + x0 * B, (x1 - x0) * B)
    lines = []
    for g in range(G):
        seg = d[g * row: g * row + (x1 - x0) * B]
        a = np.frombuffer(seg, '>u2' if (bps[0] == 16 and bo == '>') else ('<u2' if bps[0] == 16 else 'u1')).astype(np.float32)
        if spp > 1: a = a.reshape(-1, spp)[:, :3].mean(1)
        lines.append(a)
    a = np.mean(lines, 0)
    return a.reshape(-1, K).mean(1)
with ThreadPoolExecutor(12) as ex: img = np.array(list(ex.map(one, range(y0, y1, K))))
if bps[0] == 16: img = img / 257.0
if T.get(262, [1])[0] == 0: img = 255 - img        # WhiteIsZero
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out)
print('out', img.shape, 'bytes fetched', got, 'crop', x0, y0, x1, y1)
