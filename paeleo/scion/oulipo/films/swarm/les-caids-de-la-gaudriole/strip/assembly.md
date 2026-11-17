# Assembly - the folded strip (sheet caids-strip-r1)

Print `assets/pages/les-caids-de-la-gaudriole.pdf` (A3 landscape, 300 dpi) at **100 %**, with no "fit to page".
The ruler under the strip must measure **240 mm**. If it does not, the printer has scaled the page and the seam will not meet.

## Steps

1. Print the page at 100 %.
2. Cut the strip out along the four corner crop marks. It should measure 240 x 90 mm.
3. **Mountain-fold on A** (the dash-dot line, glyph Λ, 62.0 mm from the left edge). Fold the paper away from you, so that the crease ridge points up.
4. **Valley-fold on M** (the dashed line, glyph V, 121.0 mm, in the gutter). Fold it toward you.
5. Slide the pleat until mark **B** (180.0 mm) lies under mark **A**, at the top and at the bottom. Press the creases flat with a fingernail.
6. Read it.

## What you should see

- **Open** (reading order 1 to 4, as numbered above the strip):
  1. The miller: "THE KEY? I SWEAR, NOT / IN MY ENVELOPE! / ALL I CARRY IS PAPER."
  2. The porter, at the right of panel 1: "WHO BORROWED IT, THEN?"
  3. The porter in panel 2, by the closed service door, holding out the key: "HERE! SILLY ME - I HAD IT / IN THE COAT POCKET / ALL ALONG."
  4. The boys: "OH? REALLY?"
- **Folded**:
  1. The miller, now in one panel: "THE KEY? I HAD IT / IN MY POCKET / ALL ALONG." His sleeve, cut at A, ends in the hand that holds the key.
  2. The boys: "OH? REALLY?"

## Tolerances and checks

- Seam tolerance: 0.5 mm (5 u). A hand fold of three paper thicknesses creeps by about 0.2 mm, which is inside it.
- Check at the seam: the panel frame (top and bottom), the balloon's top and bottom border, and the floor line must run straight through. The cuff must meet the wrist. `strip/seam-100x.png` shows what the digital fold gives (0 u).
- Hold the folded strip against a window or a light box. Behind the miller's balloon you will see "...NOT / ...ENVELOPE! / ...IS PAPER." **mirrored**: that is facet A..M, lying face down. "HERE! SILLY ME - / IN THE COAT" and the porter appear **unmirrored**: that is facet M..B, face up. Their positions are listed in `strip/fragments.csv` (`folded_x0..x1`).

## Geometry (frozen in `strip/sheet.json` rev 1)

- The sheet is 2400 x 900 u, at 1 u = 0.1 mm. Panel 1 runs from x 40 to 1180 and panel 2 from x 1220 to 2360; both span y 50 to 850.
- A = 620 (mountain), M = 1210 (valley), B = 2M - A = 1800, D = B - A = 1180.
- Map: x <= A goes to x (face up, layer 1); A..M goes to 2A - x (face down, layer 2); M and beyond goes to x - D (face up, layer 3).
- The folded panel is (620 - 40) + (2360 - 1800) = 1140 u wide, the same width as a panel.
- Fold A first. Folding M first gives the same visible faces but a different layer stack on the light box. The film folds A first.
