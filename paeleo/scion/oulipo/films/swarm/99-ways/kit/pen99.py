"""The shared pen hand of 99 ways (HANDMADE). Every page's folio line is drawn with folio() so the 99 read as one book.

- Glyphs: the 99-ways-template table (page/glyphs.json) + its variant supplement ('2', 'F'), + glyphs99.json
  (authored here, same pen and units: cap height 1, baseline 0, y up) for the characters the 99 titles need.
- Drawing: penlib.letter_lines (single tapered pen strokes with tremor), unchanged.
Use:   import sys; sys.path.insert(0, ".../films/swarm/99-ways/kit"); from pen99 import folio, letter, sheet99
Only decoded pixels are produced; nothing foraged is executed."""
import json
import sys
from pathlib import Path

import numpy as np

KIT = Path(__file__).resolve().parent
ROOT = KIT.parents[3]                                    # .../oulipo
TPL = ROOT / "films" / "swarm" / "99-ways-template"
sys.path.insert(0, str(TPL / "page"))
import penlib  # noqa: E402  (99-ways-template pen tools: letter_lines, sheet, balloon_piece, ink_onto ...)

for extra in (TPL / "variants" / "glyphs_extra.json", KIT / "glyphs99.json"):
    for k, v in json.load(open(extra))["glyphs"].items():
        penlib.GLYPHS.setdefault(k, (v[0], [tuple(st) for st in v[1]]))

PAGE_W, PAGE_H = 2200, 2850
FOLIO_BASE_Y, FOLIO_CAP, FOLIO_X0, FOLIO_X1 = 2800, 34, 110, 2090
INK = penlib.INK
SUBST = {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "…": "...", "×": "x"}


def clean(s):
    s = "".join(SUBST.get(c, c) for c in s)
    missing = sorted({c for c in s if c not in penlib.GLYPHS})
    if missing:
        raise ValueError(f"pen99: no glyph for {missing!r}; add it to glyphs99.json (same pen) rather than a font")
    return s


def letter(lines, cap, seed, weight=0.13):
    """uint8 mask of hand-lettered lines (centred), as penlib.letter_lines."""
    return penlib.letter_lines([clean(l) for l in lines], cap, seed, weight=weight)


def sheet99(w=PAGE_W, h=PAGE_H):
    """The LoC 1934 sheet ground at the 99-ways page size (float RGB)."""
    return penlib.sheet(w, h)


def _paste_ink(img, m, x, y_base, cap, align):
    # letter_lines puts the first baseline at cap*1.15 from the mask top
    H, W = m.shape
    top = int(round(y_base - cap * 1.15))
    left = int(round(x if align == "left" else x - W + cap * 0.6))   # mask has ~0.6 cap padding each side
    if align == "left":
        left = int(round(x - cap * 0.6))
    ys, xs = max(0, top), max(0, left)
    ye, xe = min(img.shape[0], top + H), min(img.shape[1], left + W)
    sub = np.zeros(img.shape[:2], np.uint8)
    sub[ys:ye, xs:xe] = m[ys - top:ye - top, xs - left:xe - left]
    penlib.ink_onto(img, sub)


def folio(img, n, title, seed=None):
    """Draw the folio line on a 2200x2850 float/uint8 RGB page IN PLACE: title bottom-left, 'NN' bottom-right."""
    assert img.shape[:2] == (PAGE_H, PAGE_W), img.shape
    f = img.astype(np.float32) if img.dtype != np.float32 else img
    seed = 9900 + n if seed is None else seed
    _paste_ink(f, letter([title], FOLIO_CAP, seed), FOLIO_X0, FOLIO_BASE_Y, FOLIO_CAP, "left")
    _paste_ink(f, letter([f"{n:02d}"], FOLIO_CAP, seed + 1), FOLIO_X1, FOLIO_BASE_Y, FOLIO_CAP, "right")
    if f is not img:
        img[:] = np.clip(np.round(f), 0, 255).astype(img.dtype)
    return img
