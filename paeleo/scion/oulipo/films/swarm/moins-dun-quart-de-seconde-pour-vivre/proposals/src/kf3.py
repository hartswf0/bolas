"""KF3 · PROOF PRESS AND LETTER STAMPS (stop-motion of a handmade print shop, top-down).
The plate is a white-line block (the brush plate cut as a relief and locked on a
registration jig), pulled four times on one paper strip: one inked relief, one
impression model, so the four prints are the same bytes. Balloons are cut paper
pasted on the print; their words are pressed in one rubber letter at a time,
by hand, from a tray of wooden stamps. Frame shown: 0:12, strip A panel 2,
the stamp for the next letter hovering over the balloon."""
import os, sys, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from plate import draw_plate, art_hash
from hand import layout, letter, balloon_shape, brush, GLYPHS

OUT = os.path.join(os.path.dirname(__file__), '..')
K = 2
W, H = 1280 * K, 720 * K
PS = 288
G = 16
PX0, PY0 = 40, 172
INK = np.array([24, 22, 27], np.float32) / 255
PAPER = np.array([236, 228, 208], np.float32) / 255

A = [["IF I OPEN IT,", "I'LL KNOW."], ["IF I DON'T,", "I CAN STILL", "HOPE."], None, ["HOPE IT IS,", "THEN."]]


def noise(h, w, s, rng):
    # generate with margin so large blurs keep real variance on small tiles
    m = int(min(3 * s, 400))
    n = cv2.GaussianBlur(rng.normal(0, 1, (h + 2 * m, w + 2 * m)).astype(np.float32), (0, 0), s)
    n = n / (n.std() + 1e-6)
    return n[m:m + h, m:m + w]


def wood(h, w, rng, base=(92, 60, 38)):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    warp = noise(h, w, 40, rng) * 10 + noise(h, w, 9, rng) * 2.0 + xx * 0.04
    g = np.sin((yy + warp) / 5.0) * 0.5 + 0.5
    g2 = noise(h, w, 2, rng) * 0.04
    pores = (noise(h, w, 0.8, rng) > 2.3).astype(np.float32) * 0.12
    k = 0.8 + 0.12 * g ** 3 + g2 - pores + 0.05 * noise(h, w, 60, rng)
    return np.clip(k[..., None] * np.array(base, np.float32)[None, None] / 255, 0, 1)


def impression(cov_ink, rng_seed=11):
    """Turn a 0..1 ink-intent map into a relief-print coverage map (one fixed model)."""
    rng = np.random.default_rng(rng_seed)
    h, w = cov_ink.shape
    grain = noise(h, w, 0.9, rng)
    starve = noise(h, w, 6, rng)
    cov = cov_ink.copy()
    # paper tooth: specks where ink skipped, more where the inking roller starved
    skip = (grain + 0.5 * starve) > 2.0
    cov[skip] *= 0.25
    # squash: ink pushed to the edge of each relief area (thin darker rim)
    edge = cv2.morphologyEx((cov_ink > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
    cov = np.clip(cov * 0.9 + edge * 0.1, 0, 1)
    # gouge ridges left standing in cleared areas (a little chatter)
    chatter = (noise(h, w, 1.2, rng) > 2.7) & (noise(h, w, 25, rng) > 1.0)
    cov = np.maximum(cov, chatter.astype(np.float32) * 0.6)
    return cv2.GaussianBlur(cov, (0, 0), 0.6)


def lay(page, cov, x, y, ink=INK, k=0.94):
    h, w = cov.shape
    reg = page[y:y + h, x:x + w]
    page[y:y + h, x:x + w] = reg * (1 - cov[..., None] * k) + ink[None, None] * cov[..., None] * k


def shadow(page, mask, x, y, off=(10, 14), blur=10, k=0.45):
    h, w = mask.shape
    m = np.zeros(page.shape[:2], np.float32)
    x2, y2 = x + off[0], y + off[1]
    m[max(0, y2):y2 + h, max(0, x2):x2 + w] = mask[max(0, -y2):h - max(0, y2 + h - page.shape[0]), max(0, -x2):w - max(0, x2 + w - page.shape[1])]
    m = cv2.GaussianBlur(m, (0, 0), blur)
    page *= (1 - m[..., None] * k)


def stamp_block(page, x, y, w, h, ch, rng, lift=0.0, wood_base=(196, 160, 112)):
    """A wooden letter stamp seen from above; lift raises it (bigger, softer shadow)."""
    sc = 1 + 0.08 * lift
    w2, h2 = int(w * sc), int(h * sc)
    x -= (w2 - w) // 2; y -= (h2 - h) // 2
    m = np.zeros((h2 + 12, w2 + 12), np.float32)
    cv2.rectangle(m, (0, 0), (w2 + 8, h2 + 8), 1, -1)
    shadow(page, m, x, y, off=(int(8 + 26 * lift), int(10 + 34 * lift)), blur=4 + 10 * lift, k=0.55 - 0.15 * lift)
    top = wood(h2, w2, rng, wood_base)
    # side faces (south and east), darker
    side = 8
    page[y + side:y + h2 + side, x + w2:x + w2 + side] = np.array(wood_base, np.float32) / 255 * 0.55
    page[y + h2:y + h2 + side, x + side:x + w2 + side] = np.array(wood_base, np.float32) / 255 * 0.62
    page[y:y + h2, x:x + w2] = top
    # bevel highlight
    page[y:y + 3, x:x + w2] = np.minimum(1, page[y:y + 3, x:x + w2] * 1.18)
    page[y:y + h2, x:x + 3] = np.minimum(1, page[y:y + h2, x:x + 3] * 1.12)
    # the letter printed on the top as a guide (not mirrored)
    if ch.strip():
        im = Image.new('L', (w2, h2), 0)
        d = ImageDraw.Draw(im)
        r = np.random.default_rng(ord(ch))
        st, (tw, th) = layout([ch], h2 * 0.5, r)
        letter(d, st, (w2 - tw) / 2, (h2 - th) / 2, h2 * 0.07, ord(ch), col=255)
        c = np.asarray(im).astype(np.float32)[..., None] / 255 * 0.85
        page[y:y + h2, x:x + w2] = page[y:y + h2, x:x + w2] * (1 - c) + c * np.array([30, 24, 22], np.float32) / 255


def balloon_paper(lines, size, seed, tail, upto_letters=None):
    """A cut-paper balloon (mask) and its stamped-letter coverage, plus the position of the next letter."""
    rng = np.random.default_rng(seed)
    st_all = []
    # per-letter layout so each letter is one stamp impression
    st, (tw, th) = layout(lines, size, rng)
    rw, rh = tw / 2 + size * 1.0, th / 2 + size * 1.0
    Wd, Hd = int(rw * 2 + 160), int(rh * 2 + 200)
    cx, cy = Wd / 2, rh + 30
    pts = balloon_shape(cx, cy, rw * 1.05, rh * 1.1, rng, (cx + tail[0], cy + tail[1]))
    m = Image.new('L', (Wd, Hd), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    mask = np.asarray(m).astype(np.float32) / 255
    # letters: group strokes per character by re-laying out char by char with the same rng stream
    rng2 = np.random.default_rng(seed)
    chars = []
    y = 0
    for line in lines:
        x = 0
        for ch in line:
            gw, gs = GLYPHS.get(ch.upper(), GLYPHS[' '])
            s1, (cw, _) = layout([ch], size, np.random.default_rng(seed * 100 + len(chars)))
            chars.append((ch, x, y, s1))
            x += gw * size * 0.92 + 0.16 * size
        y += size * 1.42
    n = len(chars) if upto_letters is None else upto_letters
    cov = Image.new('L', (Wd, Hd), 0)
    d = ImageDraw.Draw(cov)
    ox, oy = cx - tw / 2, cy - th / 2
    dens = []
    for i, (ch, x, y, s1) in enumerate(chars[:n]):
        letter(d, s1, ox + x, oy + y, size * 0.2, 900 + i, col=255)
    covn = np.asarray(cov).astype(np.float32) / 255
    # each rubber letter inks a little differently
    lab = np.zeros_like(covn)
    covn = covn * (0.82 + 0.18 * np.clip(noise(Hd, Wd, 18, rng) * 0.5 + 0.5, 0, 1))
    covn = impression(covn, seed)
    nxt = None
    if n < len(chars):
        j = n
        while j < len(chars) and not chars[j][0].strip():
            j += 1
        if j < len(chars):
            ch, x, y, _ = chars[j]
            nxt = (ch, ox + x, oy + y)
    return mask, covn, nxt


def build(out='kf-3.png'):
    rng = np.random.default_rng(4)
    page = wood(H, W, rng)
    # vignette from the copy-stand lamps
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.35 * (((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.42) / H) ** 2) * 2.2
    page *= v[..., None]
    # paper strip
    sx0, sy0, sx1, sy1 = 18 * K, 108 * K, 1262 * K, 498 * K
    pm = np.zeros((sy1 - sy0, sx1 - sx0), np.float32) + 1
    shadow(page, pm, sx0, sy0, off=(8, 12), blur=12, k=0.5)
    paper = np.ones((sy1 - sy0, sx1 - sx0, 3), np.float32) * PAPER
    paper *= (1 + 0.025 * noise(sy1 - sy0, sx1 - sx0, 1.0, rng) + 0.02 * noise(sy1 - sy0, sx1 - sx0, 30, rng))[..., None]
    page[sy0:sy1, sx0:sx1] = paper * v[sy0:sy1, sx0:sx1, None] ** 0.5
    # the block: white-line relief = the brush plate inverted (what was ink is cut away)
    plate = np.asarray(draw_plate(PS * K)).astype(np.float32) / 255
    cov0 = impression(plate, 11)     # inverted: plate white shapes become ink relief
    hashes = []
    for c in range(4):
        x, y = (PX0 + c * (PS + G)) * K, PY0 * K
        hashes.append(hash(cov0.tobytes()))
        lay(page, cov0, x, y)
    assert len(set(hashes)) == 1
    # balloons pasted on panels 1 and 2 (panel 2 mid-stamping)
    nxt_pos = None
    for c in (0, 1):
        lines = A[c]
        upto = None if c == 0 else 13
        mask, cov, nxt = balloon_paper(lines, 25, 40 + c, tail=(70, 120), upto_letters=upto)
        x = (PX0 + c * (PS + G)) * K + 20
        y = PY0 * K - 8
        h, w = mask.shape
        shadow(page, mask, x, y, off=(3, 4), blur=2.5, k=0.35)
        reg = page[y:y + h, x:x + w]
        pap = np.ones_like(reg) * PAPER * 1.02
        pap *= (1 + 0.02 * noise(h, w, 1.0, rng))[..., None]
        page[y:y + h, x:x + w] = reg * (1 - mask[..., None]) + pap * mask[..., None]
        # cut edge: slightly darker scissor line
        edge = cv2.morphologyEx((mask > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
        page[y:y + h, x:x + w] *= (1 - 0.25 * edge[..., None])
        lay(page, cov * mask, x, y)
        if nxt:
            nxt_pos = (nxt[0], x + nxt[1], y + nxt[2])
    # the hovering stamp for the next letter (lifted, shadow offset)
    if nxt_pos:
        ch, nx, ny = nxt_pos
        stamp_block(page, int(nx + 8 - 22), int(ny + 12 - 25), 44, 50, ch, rng, lift=1.0)
    # the tray of letter stamps along the bottom of the table
    tray_y = 560 * K
    tray = np.zeros((130 * K, 1180 * K), np.float32) + 1
    shadow(page, tray, 50 * K, tray_y, off=(10, 14), blur=10, k=0.5)
    page[tray_y:tray_y + 130 * K, 50 * K:1230 * K] = wood(130 * K, 1180 * K, rng, (70, 44, 28)) * 0.8
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ'?,.-!"
    for i, ch in enumerate(letters):
        col, row = i % 16, i // 16
        if ch in "C":    # C is in the hand
            continue
        stamp_block(page, (70 + col * 72) * K, tray_y + (14 + row * 58) * K, 54 * K // 2 * 2, 46 * K, ch, rng)
    img = Image.fromarray((np.clip(page, 0, 1) * 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(img)
    # pencil notes on the strip margin
    r = np.random.default_rng(3)
    st, _ = layout(["A  -  TO WAIT"], 26, r)
    letter(d, st, PX0 * K + 6, 128 * K, 3.2, 3, col=(92, 88, 86))
    r = np.random.default_rng(4)
    st, (tw, _) = layout(["0:12"], 26, r)
    letter(d, st, (1280 - PX0) * K - tw - 6, 128 * K, 3.2, 4, col=(92, 88, 86))
    img = img.resize((1280, 720), Image.LANCZOS)
    img.save(os.path.join(OUT, out))
    print('4 identical impressions')


if __name__ == '__main__':
    build()
