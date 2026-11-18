"""Freeze strip/sheet.json rev 1 and strip/fragments.csv (paper-engineer-writer).

Geometry is the plan's (plan.json "geometry"); this script only spells it out as a
constraint graph and lays the balloon text fragments with pen.text_width so every
fragment has an exact sheet bbox and its folded / light-box ghost position.
Re-run only to refresh strip_art (sha256) - geometry and text are frozen.
"""
import os, sys, json, csv, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pen import text_width

SW, SH = 2400, 900
P1, P2 = (40, 1180), (1220, 2360)
PY = (50, 850)
A, M = 620, 1210
B = 2 * M - A
D = B - A
TAU = 5
CAP = 36
LINE_Y = [112, 168, 224]          # cap tops
GAP = 12                          # L ends at A-12 / B-12, R starts at A+12 / B+12
BALLOON = {"P1": (80, 1140, 80, 276), "P2": (1260, 2320, 80, 276)}   # x0,x1,y0,y1 (u)
FLOOR = {"P1": ((50, 790), (1170, 794)), "P2": ((1230, 790), (2350, 794))}

# The balloon lines. Folded reading (L of A from P1 + R of B from P2) is frozen:
# THE KEY? I HAD IT / IN MY POCKET / ALL ALONG.
P1_LINES = [("THE KEY?", "I SWEAR, NOT"), ("IN MY", "ENVELOPE!"), ("ALL", "I CARRY IS PAPER.")]
P2_LINES = [("HERE! SILLY ME -", "I HAD IT"), ("IN THE COAT", "POCKET"), ("ALL", "ALONG.")]
# Small balloons: 'borrowed' made explicit in the open state (A..M, hidden when folded).
SMALL = [
    dict(id="P1.porter.ask", panel="P1", speaker="porter-P1", lines=["WHO BORROWED", "IT, THEN?"],
         centre=(1010, 372), size=26, bbox=[856.3, 315.4, 1163.7, 518.6]),
    dict(id="P2.boys.say", panel="P2", speaker="boys", lines=["OH?", "REALLY?"],
         centre=(2215, 430), size=26),
]


def facet(x):
    if x <= A: return "F0"
    if x <= M: return "F1"
    if x <= B: return "F2"
    return "F3"


def mapping(x0, x1):
    """Folded / light-box position of sheet x-range [x0,x1]."""
    f = facet((x0 + x1) / 2)
    if f == "F0":
        return dict(facet=f, depth=1, face="up", folded=[x0, x1], state="visible", mirrored=False)
    if f == "F1":
        return dict(facet=f, depth=2, face="down", folded=[round(2 * A - x1, 1), round(2 * A - x0, 1)], state="hidden (light-box ghost)", mirrored=True)
    if f == "F2":
        return dict(facet=f, depth=3, face="up", folded=[round(x0 - D, 1), round(x1 - D, 1)], state="hidden (light-box ghost)", mirrored=False)
    return dict(facet=f, depth=3, face="up", folded=[x0 - D, x1 - D], state="visible", mirrored=False)


def small_bbox(s):
    w = max(text_width(t, s["size"]) for t in s["lines"]) + 50
    h = len(s["lines"]) * s["size"] * 1.6 + 30
    cx, cy = s["centre"]
    return [round(cx - w / 2, 1), round(cy - h / 2, 1), round(cx + w / 2, 1), round(cy + h / 2 + 90, 1)]


def fragments():
    out = []
    for panel, lines, f, spk in [("P1", P1_LINES, A, "miller"), ("P2", P2_LINES, B, "porter")]:
        for i, (l, r) in enumerate(lines):
            y0, y1 = LINE_Y[i], LINE_Y[i] + CAP
            wl, wr = text_width(l, CAP), text_width(r, CAP)
            for side, txt, x0, x1 in [("L", l, f - GAP - wl, f - GAP), ("R", r, f + GAP, f + GAP + wr)]:
                bb = [round(x0, 1), y0, round(x1, 1), y1]
                out.append(dict(id=f"{panel}.{spk}.line{i+1}.{side}", panel=panel, speaker=spk, layer="balloon",
                                line=i + 1, side=side, text=txt, bbox=bb, **mapping(bb[0], bb[2])))
    for s in SMALL:
        bb = s.get("bbox") or small_bbox(s)
        out.append(dict(id=s["id"], panel=s["panel"], speaker=s["speaker"], layer="balloon", line=None, side="",
                        text=" / ".join(s["lines"]), bbox=bb, **mapping(bb[0], bb[2])))
    # image fragments: frozen zones (the art must keep each figure inside its zone; fixture checks)
    figs = [
        ("P1.miller.body", "P1", "miller", "figure", "miller body, sack, sleeve cut at A (cuff crosses x=A)", [44, 300, A, 846]),
        ("P1.miller.hand-open", "P1", "miller", "figure", "miller's empty open hand reaching past A (open state only)", [A, 420, 760, 640]),
        ("P1.porter", "P1", "porter-P1", "figure", "porter (Busch farmer, mirrored) listening, neck joint", [800, 330, 1176, 846]),
        ("P2.porter", "P2", "porter", "figure", "porter (Busch farmer) with pen-drawn striped forearm to the wrist at B", [1232, 290, B, 846]),
        ("P2.door", "P2", "-", "furniture", "closed service door, pen-drawn, behind the porter (common seed)", [1236, 300, 1560, 790]),
        ("P2.hand-key", "P2", "porter/miller", "figure", "hand + brass bit-key beyond B (reads as the miller's hand when folded)", [B, 420, 1960, 700]),
        ("P2.boys", "P2", "boys", "figure", "the two boys (Busch plate 001)", [1880, 560, 2356, 846]),
    ]
    for fid, panel, spk, lay, what, bb in figs:
        out.append(dict(id=fid, panel=panel, speaker=spk, layer=lay, line=None, side="", text=what, bbox=bb,
                        **mapping(bb[0], bb[2])))
    return out


def constraints():
    c = [
        dict(id="C1", kind="equality", expr="B = 2M - A", value=[B, 2 * M - A]),
        dict(id="C2", kind="equality", expr="D = B - A", value=D),
        dict(id="C3", kind="inequality", expr="2A - M > 0 (hidden facet stays on the sheet)", value=2 * A - M),
        dict(id="C4", kind="interval", expr="P1.x0 <= A < P1.x1 and P2.x0 < B < P2.x1", value=[P1, A, P2, B]),
        dict(id="C5", kind="equality", expr="folded panel width (A-P1.x0)+(P2.x1-B) = panel width", value=[(A - P1[0]) + (P2[1] - B), P1[1] - P1[0]]),
        dict(id="C6", kind="contact", expr="mark A coincides with mark B after the pleat (top and bottom margins)", value=[A, B - D]),
        dict(id="C7", kind="seam", expr="frame top border y at x=A (P1) == at x=B (P2)", y=PY[0], tol=TAU),
        dict(id="C8", kind="seam", expr="frame bottom border", y=PY[1], tol=TAU),
        dict(id="C9", kind="seam", expr="balloon top border", y=BALLOON["P1"][2], tol=TAU),
        dict(id="C10", kind="seam", expr="balloon bottom border", y=BALLOON["P1"][3], tol=TAU),
        dict(id="C11", kind="seam", expr="floor line (both panels 790->794 across the same x-offset)", y=792, tol=TAU),
        dict(id="C12", kind="seam", expr="miller cuff at x=A == porter wrist at x=B: same y-band, slope, width", y_band=[440, 600], tol=TAU),
        dict(id="C13", kind="baseline", expr="each balloon line i: L and R fragments share LINE_Y[i] and cap height", LINE_Y=LINE_Y, cap=CAP),
        dict(id="C14", kind="clearance", expr="L fragment ends <= f-12, R fragment starts >= f+12 (f = A or B)", gap=GAP),
        dict(id="C15", kind="region", expr="'OH? REALLY?' and the boys wholly in x >= B+12", xmin=B + GAP),
        dict(id="C16", kind="region", expr="'WHO BORROWED IT, THEN?' and porter-P1 wholly in A+12..M-12 (open state only)", x=[A + GAP, M - GAP]),
        dict(id="C17", kind="ink", expr="folded view == V(x') pixel for pixel; no ink without a sheet source", tol_digital=0),
        dict(id="C18", kind="ghost", expr="light-box ghosts: F1 at 2A-x mirrored, F2 at x-D unmirrored, within 2 u", tol=2),
    ]
    return c


def main(strip_art=None):
    fr = fragments()
    sheet = {
        "id": "caids-strip-r1", "revision": 1, "frozen": True, "frozen_by": "paper-engineer-writer, 2026-11-17",
        "units": "u", "W": SW, "H": SH, "scale": "1 u = 0.1 mm (240 x 90 mm printed); A3 300 dpi: 1 u = 1.1811 px",
        "px_per_u_300dpi": 300 / 254.0,
        "faces": {"front": "ink (strip-art.png)", "back": "blank paper, mirrored show-through"},
        "panels": {"P1": {"x": list(P1), "y": list(PY)}, "P2": {"x": list(P2), "y": list(PY)}, "gutter": [P1[1], P2[0]]},
        "folds": [
            {"id": "A", "x": A, "kind": "mountain", "order": 1, "mark": "dash-dot + small mountain glyph"},
            {"id": "M", "x": M, "kind": "valley", "order": 2, "mark": "dashed + small V glyph", "where": "gutter"},
            {"id": "B", "x": B, "kind": "registration", "note": "not a crease: B = 2M-A lands on A"},
        ],
        "pleat": "one marked pleat: fold so that mark B lies on mark A (A mountain first, then M valley)",
        "A": A, "M": M, "B": B, "D": D, "tau_u": TAU, "tau_digital_u": 0,
        "facets": [
            {"id": "F0", "x": [0, A], "map": "x", "face": "up", "layer": 1},
            {"id": "F1", "x": [A, M], "map": "2A - x", "face": "down", "layer": 2},
            {"id": "F2", "x": [M, B], "map": "x - D", "face": "up", "layer": 3},
            {"id": "F3", "x": [B, SW], "map": "x - D", "face": "up", "layer": 3, "note": "never leaves the table (z = 0)"},
        ],
        "V": "V(x') = Sheet(x') for x' < A; Sheet(x' + D) for x' >= A; width (A-40)+(2360-B) = 1140 u",
        "lightbox_stack": "for x' < A: layer1 Sheet(x') up, layer2 Sheet(2A - x') face down (reads mirrored), layer3 Sheet(x' + D) up",
        "LINE_Y": LINE_Y, "cap_u": CAP, "fragment_gap_u": GAP,
        "balloons": {k: list(v) for k, v in BALLOON.items()},
        "floor_lines": {k: [list(a), list(b)] for k, (a, b) in FLOOR.items()},
        "marks": {"top_y": 18, "bottom_y": SH - 18, "at": [A, M, B]},
        "text": {
            "P1_miller": [" ".join(p) for p in P1_LINES],
            "P1_porter": "WHO BORROWED IT, THEN?",
            "P2_porter": [" ".join(p) for p in P2_LINES],
            "P2_boys": "OH? REALLY?",
            "folded_miller": [P1_LINES[i][0] + " " + P2_LINES[i][1] for i in range(3)],
            "folded_boys": "OH? REALLY?",
            "revision_note": "rev 1: porter-P1 'WHO TOOK IT, THEN?' -> 'WHO BORROWED IT, THEN?' (borrowed explicit in the open state; lies in A..M, hidden when folded). All other lines unchanged; folded line frozen.",
        },
        "readings": {
            "open": ["P1 miller balloon lines 1-3", "P1 porter 'WHO BORROWED IT, THEN?'", "P2 porter balloon lines 1-3", "P2 boys 'OH? REALLY?'"],
            "folded": ["folded balloon 'THE KEY? I HAD IT / IN MY POCKET / ALL ALONG.'", "'OH? REALLY?'"],
        },
        "constraints": constraints(),
        "fragments": fr,
        "evidence": json.load(open(os.path.join(HERE, "evidence.json"))) if os.path.exists(os.path.join(HERE, "evidence.json")) else None,
        "strip_art": strip_art or {"path": "strip/strip-art.png", "sha256": "pending (adopted from puppets/art-layers.png when U2 delivers)"},
    }
    json.dump(sheet, open(os.path.join(HERE, "sheet.json"), "w"), indent=1)
    with open(os.path.join(HERE, "fragments.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "panel", "speaker", "layer", "text", "x0", "y0", "x1", "y1", "facet", "depth_layer", "face",
                    "folded_x0", "folded_x1", "state", "mirrored"])
        for g in fr:
            w.writerow([g["id"], g["panel"], g["speaker"], g["layer"], g["text"], *g["bbox"], g["facet"], g["depth"],
                        g["face"], round(g["folded"][0], 1), round(g["folded"][1], 1),
                        g["state"], g["mirrored"]])
    return sheet


if __name__ == "__main__":
    art = None
    p = os.path.join(HERE, "strip-art.png")
    if os.path.exists(p):
        art = {"path": "strip/strip-art.png", "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(),
               "adopted_from": "puppets/art-layers.png"}
    s = main(art)
    for g in s["fragments"]:
        print(g["id"], g["bbox"], g["facet"], g["folded"], g["state"])
