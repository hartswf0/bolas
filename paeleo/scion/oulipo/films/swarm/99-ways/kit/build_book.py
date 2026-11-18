"""99 ways: front matter (title page, contents) and the book PDF (HANDMADE, editor).

Title page, contents pages and the end leaf are lettered in the shared pen hand (pen99) on the LoC 1934
sheet ground (99-ways-template:loc-blank-sheet-1934). The book PDF binds: title page, contents (every page's
number, constraint title and rule, read from pages/NN.json), the 99 page JPGs in order, the end leaf.
Pages in the PDF are re-encoded at 1100x1425 (JPEG q82, 150 dpi) so the book stays small; the 2200x2850 page
JPGs in assets/pages/99-ways/ remain the full-resolution deliverables.

Run:  python3 films/swarm/99-ways/kit/build_book.py
Writes films/sources/99-ways/book/{title,contents-1..,end}.png and assets/pages/99-ways/99-ways-book.pdf
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
import pen99  # noqa: E402
import penlib  # noqa: E402  (loaded by pen99)

ROOT = KIT.parents[3]
PAGES = ROOT / "films" / "swarm" / "99-ways" / "pages"
OUTD = ROOT / "films" / "sources" / "99-ways" / "book"
JPG = ROOT / "assets" / "pages" / "99-ways"
PDF = JPG / "99-ways-book.pdf"
W, H = pen99.PAGE_W, pen99.PAGE_H


def records():
    out = []
    for f in sorted(PAGES.glob("[0-9][0-9].json")):
        p = json.load(open(f))
        out.append(p)
    assert [p["n"] for p in out] == list(range(1, 100))
    return out


def width(s, cap):
    s = pen99.clean(s)
    return sum(penlib.GLYPHS[c][0] * cap + cap * .1 for c in s) - cap * .1


def put(img, s, x, base, cap, seed, align="left", weight=0.13):
    m = pen99.letter([s], cap, seed, weight=weight)
    if align == "centre":
        x = x - width(s, cap) / 2
        align = "left"
    pen99._paste_ink(img, m, x, base, cap, align)


def wrap(s, cap, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if cur and width(t, cap) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def rule(img, x0, x1, y, seed, w=4):
    m = np.zeros(img.shape[:2], np.uint8)
    penlib.brush_line(m, [(x0, y), ((x0 + x1) / 2, y + 2), (x1, y)], w, seed)
    penlib.ink_onto(img, m)


def margin(img, label, mark, seed):
    put(img, label, pen99.FOLIO_X0, pen99.FOLIO_BASE_Y, pen99.FOLIO_CAP, seed)
    if mark:
        put(img, mark, pen99.FOLIO_X1, pen99.FOLIO_BASE_Y, pen99.FOLIO_CAP, seed + 1, align="right")


def title_page():
    img = pen99.sheet99()
    put(img, "99 ways", W / 2, 1150, 230, 7001, align="centre", weight=0.12)
    rule(img, 700, 1500, 1290, 7002)
    put(img, "one small station, one key, one clock,", W / 2, 1460, 58, 7003, align="centre")
    put(img, "one man who forgets what he came for:", W / 2, 1560, 58, 7004, align="centre")
    put(img, "the same quarter of a minute told ninety-nine times,", W / 2, 1660, 58, 7005, align="centre")
    put(img, "each page under one rule", W / 2, 1760, 58, 7006, align="centre")
    put(img, "foraged and handmade", W / 2, 2450, 40, 7007, align="centre")
    return img


def contents_pages(recs):
    pages, img, y, k = [], None, 0, 0
    cap_t, cap_r, maxw = 40, 27, 1660
    lh_t, lh_r = cap_t * 1.5, cap_r * 1.45
    top, bottom = 470, 2640

    def new():
        nonlocal img, y, k
        if img is not None:
            pages.append(img)
        k += 1
        img = pen99.sheet99()
        put(img, "Contents" if k == 1 else "Contents, continued", W / 2, 330, 70 if k == 1 else 50, 7100 + k,
            align="centre")
        margin(img, "Contents", ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"][k - 1], 7150 + k)
        y = top

    new()
    for p in recs:
        rl = wrap(p["rule"], cap_r, maxw)
        need = lh_t + lh_r * len(rl) + 26
        if y + need > bottom:
            new()
        s = 7200 + p["n"] * 7
        put(img, f"{p['n']:02d}", 200, y + cap_t, cap_t, s)
        put(img, p["title"], 360, y + cap_t, cap_t, s + 1)
        yy = y + lh_t
        for i, ln in enumerate(rl):
            put(img, ln, 360, yy + cap_r, cap_r, s + 2 + i, weight=0.12)
            yy += lh_r
        y = yy + 26
    pages.append(img)
    return pages


def end_leaf():
    img = pen99.sheet99()
    put(img, "99 ways", W / 2, 1380, 90, 7901, align="centre")
    put(img, "end", W / 2, 1500, 50, 7902, align="centre")
    return img


def u8(a):
    return Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8))


def main():
    OUTD.mkdir(parents=True, exist_ok=True)
    recs = records()
    front = [("title", title_page())] + [(f"contents-{i + 1}", c) for i, c in enumerate(contents_pages(recs))]
    back = [("end", end_leaf())]
    for name, a in front + back:
        u8(a).save(OUTD / f"{name}.png")
        print("wrote", (OUTD / f"{name}.png").relative_to(ROOT))
    small = (1100, 1425)
    leaves = [u8(a).resize(small, Image.LANCZOS) for _, a in front]
    for p in recs:
        f = JPG / f"{p['n']:02d}-{p['id']}.jpg"
        leaves.append(Image.open(f).convert("RGB").resize(small, Image.LANCZOS))
    leaves += [u8(a).resize(small, Image.LANCZOS) for _, a in back]
    # 150 dpi at 1100 px -> 7.33 x 9.5 in, the page proportion of 2200x2850
    leaves[0].save(PDF, "PDF", save_all=True, append_images=leaves[1:], resolution=150.0, quality=82,
                   title="99 ways", author="this production (99 ways swarm)",
                   subject="99 one-page retellings of one station incident, each under one constraint")
    print("wrote", PDF.relative_to(ROOT), f"{PDF.stat().st_size / 1e6:.1f} MB", len(leaves), "leaves")


if __name__ == "__main__":
    main()
