"""strip/second_fold.py - plan.md section 4/8 inquiry: a second pleat on a FRESH copy.

Pleat 2: mountain A2 = 1990, valley M2 = 2100 (inside P2), so B2 = 2*M2 - A2 = 2210 lands
on A2 and D2 = 220. Visible front V2(x') = S(x') for x' < A2, S(x' + D2) for x' >= A2.
Records which fragments stay visible, are hidden, or are cut, and the order-of-operations
note for doing it on top of pleat 1. No content is added for it.
Writes strip/second-fold.json (and strip/second-fold-preview.png when the art exists).
"""
import os, sys, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold as F

A2, M2 = 1990, 2100
B2 = 2 * M2 - A2
D2 = B2 - A2
SJ = F._sheet


def classify(x0, x1):
    if x1 <= A2: return "visible (unchanged)", [x0, x1]
    if x0 >= B2: return "visible (shifted by -D2)", [x0 - D2, x1 - D2]
    if x0 >= A2 and x1 <= B2: return "hidden", None
    parts = []
    if x0 < A2: parts.append(f"left part {x0}-{A2} visible")
    if x1 > B2: parts.append(f"right part {B2}-{x1} visible at {B2 - D2}-{x1 - D2}")
    return "cut by pleat 2: " + "; ".join(parts) + f"; {max(x0, A2)}-{min(x1, B2)} hidden", None


def main():
    frs = []
    for f in SJ["fragments"]:
        x0, y0, x1, y1 = f["bbox"]
        st, pos = classify(x0, x1)
        frs.append(dict(id=f["id"], text=f["text"], sheet_bbox=f["bbox"], pleat2=st, pleat2_folded_x=pos))
    rec = dict(
        id="caids-strip-r1 / second pleat on a fresh copy (inquiry only, no content added)",
        pleat2=dict(A2_mountain=A2, M2_valley=M2, B2=B2, D2=D2, check_B2_eq_2M2_minus_A2=B2 == 2 * M2 - A2,
                    check_2A2_minus_M2_gt_P2x0=2 * A2 - M2 > SJ["panels"]["P2"]["x"][0]),
        visible_faces_fresh_copy="V2(x') = S(x') for x' < 1990; S(x' + 220) for x' >= 1990 (width 2180 u)",
        fragments=frs,
        reading="Pleat 2 does not hide 'OH? REALLY?' cleanly: the balloon (2114-2316) is cut at 2210, so "
                "the left of 'OH? / REALLY?' and the right end of 'I HAD IT' disappear and the boys lose "
                "their left half. It yields no coherent new utterance, which is why the work uses one pleat. "
                "To hide the boys' line wholly a pleat would need A2 <= 2102 and B2 >= 2328, i.e. D2 >= 226 "
                "with both edges inside P2 (for example A2 = 2090, M2 = 2210, B2 = 2330) - but that also "
                "cuts the boys' figures.",
        order_of_operations="On a copy already folded with pleat 1 (A-first, then M), pleat 2 acts on the folded "
                            "packet in x' coordinates: A2' = A2 - D = 810, M2' = 920. The visible faces are the "
                            "same as folding pleat 2 first and then pleat 1 (they act on disjoint ranges: "
                            "pleat 1 on 620-1800, pleat 2 on 1990-2210), but the light-box stack differs: pleat 2 "
                            "adds two layers over x' 810-920 only.",
    )
    json.dump(rec, open(os.path.join(HERE, "second-fold.json"), "w"), indent=1)
    p = os.path.join(HERE, "strip-art.png")
    if os.path.exists(p):
        S = np.asarray(Image.open(p).convert("L"))
        V2 = np.concatenate([S[:, :A2], S[:, B2:]], 1)
        Image.fromarray(V2).save(os.path.join(HERE, "second-fold-preview.png"))
    return rec


if __name__ == "__main__":
    for f in main()["fragments"]:
        print(f["id"], f["pleat2"])
