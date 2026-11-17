"""Author the handmade glyph-stroke table page/glyphs.json (single-stroke pen alphabet, units of cap height,
baseline y=0, y up). Base strokes from the approved test shot's table, extended for this page by hand.
Each glyph: [advance, [[kind, data], ...]], kind L = polyline points, E = elliptic arc (cx,cy,rx,ry,a0,a1 deg), D = dot."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "test-shot-build"))
from common import GLYPHS as BASE
L = lambda *p: ["L", [list(q) for q in p]]
E = lambda *a: ["E", list(a)]
D = lambda x, y: ["D", [x, y]]
G = {k: [v[0], [[s[0], [list(q) for q in s[1]] if s[0] == "L" else list(s[1])] for s in v[1]]] for k, v in BASE.items()}
G.update({
 "O": [.64, [E(.32, .5, .3, .5, 90, 452)]],
 "N": [.54, [L((.02, 0), (.02, 1), (.5, 0), (.5, 1.02))]],
 "D": [.52, [L((.02, 0), (.02, 1), (.22, 1), (.4, .9), (.48, .7), (.48, .3), (.4, .1), (.22, 0), (.02, 0))]],
 "K": [.50, [L((.02, 1), (.02, 0)), L((.46, 1), (.04, .42)), L((.16, .55), (.48, 0))]],
 "Y": [.52, [L((0, 1), (.26, .52), (.52, 1)), L((.26, .52), (.26, 0))]],
 "U": [.54, [L((.02, 1), (.02, .3), (.1, .07), (.26, 0), (.42, .07), (.5, .3), (.5, 1))]],
 "B": [.52, [L((.02, 0), (.02, 1), (.28, 1), (.42, .92), (.44, .78), (.34, .57), (.04, .55)),
             L((.04, .55), (.34, .53), (.46, .4), (.48, .2), (.38, .04), (.22, 0), (.02, 0))]],
 "A": [.54, [L((0, 0), (.27, 1.02), (.54, 0)), L((.1, .36), (.44, .36))]],
 "M": [.66, [L((0, 0), (.03, 1), (.32, .34), (.62, 1), (.65, 0))]],
 "L": [.44, [L((.02, 1), (.02, 0), (.42, 0))]],
 "H": [.52, [L((.02, 1), (.02, 0)), L((.5, 1), (.5, 0)), L((.02, .52), (.5, .52))]],
 "G": [.58, [E(.3, .5, .3, .5, 40, 330), L((.58, .42), (.58, .12)), L((.36, .42), (.58, .42))]],
 ":": [.14, [D(.05, .58), D(.05, .06)]],
 "1": [.32, [L((.03, .8), (.19, 1), (.19, 0))]],
 "0": [.48, [E(.24, .5, .22, .5, 90, 452)]],
 "—": [.72, [L((.02, .46), (.7, .44))]],
 "-": [.36, [L((.02, .44), (.32, .44))]],
 "c": [.44, [E(.24, .31, .22, .31, 40, 320)]],
 "d": [.48, [E(.22, .31, .21, .31, 0, 360), L((.44, 1.05), (.44, 0))]],
 "b": [.47, [L((.02, 1.05), (.02, 0)), E(.24, .31, .21, .3, 180, 540)]],
 "v": [.46, [L((0, .62), (.23, 0), (.46, .62))]],
 "x": [.44, [L((0, .62), (.42, 0)), L((.42, .62), (0, 0))]],
 "'": [.12, [L((.06, 1.02), (.04, .72))]],
})
json.dump({"note": "HANDMADE single-stroke pen alphabet for 99-ways-template (not a typeface). Units: cap height=1, baseline 0, y up.",
           "glyphs": G}, open(Path(__file__).resolve().parent / "glyphs.json", "w"), indent=0)
print(len(G), "glyphs")
