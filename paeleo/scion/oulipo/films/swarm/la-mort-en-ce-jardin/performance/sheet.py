# puppet-sheet.png: the three handmade card puppets (rest pose, pieces, split pins) and the key poses, all drawn by
# FK from poses.json (the same keys the trace and the gate use).   python3 -I sheet.py
import sys, json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import puppets as PP  # noqa: E402
from puppets import S, draw_figure, bag_piece, HairSim  # noqa: E402
from rig import fk, sample, pose, STAND, HIP_ABOVE  # noqa: E402
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films")
from kit import font  # noqa: E402

OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/la-mort-en-ce-jardin/performance")
P = json.load(open(HERE / "poses.json"))
W, H = 2000, 1500
C = np.zeros((H, W, 3), np.float32) + 92
labels = []


def place(who, root, ab, s, at, ex=None, props=(), hair=True, label=""):
    """draw a pose with its hip at screen point `at` (pose root offset removed), scale s."""
    J = fk((0, 0), ab, s)
    J = {b: ((p0[0] + at[0], p0[1] + at[1]), (p1[0] + at[0], p1[1] + at[1]), a) for b, (p0, p1, a) in J.items()}
    ex = ex or {}
    hs = None
    if who == "B" and hair:
        sim = HairSim(); [sim.step(ab["head"], (0, 0)) for _ in range(30)]; hs = sim.a
    sh = None
    def fcb(Cn):
        if "shoe" in props:
            p0, p1, ang = J["hand_n"]; im = S.shoe_img(int(50 * s), -ang + 20); h, w = im.shape[:2]
            S.over(Cn, im, p0[0] + (p1[0] - p0[0]) * .7 - w * .45, p0[1] + (p1[1] - p0[1]) * .7 - h * .5)
    draw_figure(C, J, s, who, 1, gaze=ex.get("gaze", 0), brow=ex.get("brow", 0), mouth=ex.get("mouth", 0), hair=hs,
                front_hand_cb=fcb, light=(at[1] - 260 * s, at[1] + 120 * s))
    if "bag" in props or "bag_n" in props:
        bone = "hand_n" if "bag_n" in props else "hand_f"
        hx, hy = J[bone][1]; bag_piece(C, hx, hy - 3, 0.95 * s, 0)
    if label: labels.append((at[0], at[1] + 125 * s + 6, label))


# row 1: the three puppets at rest, large
rest = pose(-90, -90, (100, 94, 94), (80, 86, 86), *STAND)
for k, who in enumerate("ABC"):
    place(who, None, rest, 1.75, (230 + 300 * k, 540), props=("bag",) if who == "B" else (),
          label={"A": "A  tall man, hat", "B": "B  woman, wet hair (14 strands), bag", "C": "C  man, pencilled headband"}[who])
# row 1 right: retrieval sequence keys (shared by L-S5 and E-S4), from poses.json L
rk = [k for k in P["L"]["keys"]["B"] if k["tag"].startswith("retrieve")]
for j, k in enumerate(rk):
    ab = {b: int(round(v)) for b, v in k["a"].items()}
    props = ("bag",) if j <= 1 else (("shoe",) if j >= 4 else ())
    place("B", None, ab, 0.95, (1050 + 120 * (j % 4) + 480 * 0, 300 + 300 * (j // 4)), ex=k, props=props,
          label=k["tag"].replace("retrieve", "R") + " s")
# row 3: walk on the plank (A, L 6.0-12.5) every 1/6 s over one stride, with liana hand; C crossing with the bag high
wk = [k for k in P["L"]["keys"]["A"] if k["tag"] == "walk A" and 7.0 <= k["t"] <= 7.9]
for j, k in enumerate(wk[:10:2]):
    ab = {b: int(round(v)) for b, v in k["a"].items()}
    place("A", None, ab, 1.0, (140 + 150 * j, 1210), label=f"walk {k['t']:.2f}")
ck = [k for k in P["L"]["keys"]["C"] if k["tag"] == "walk C" and 26.0 <= k["t"]][:1]
for k in ck:
    place("C", None, {b: int(round(v)) for b, v in k["a"].items()}, 1.0, (930, 1210), props=("bag_n",), label="C crosses, bag high")
bk = [k for k in P["L"]["keys"]["B"] if k["tag"] == "walk B" and 32.0 <= k["t"]][:1]
for k in bk:
    place("B", None, {b: int(round(v)) for b, v in k["a"].items()}, 1.0, (1100, 1210), props=("shoe",), label="B crosses, shoe")
wr = [k for k in P["L"]["keys"]["A"] if k["tag"] == "write ledger"][:1]
for k in wr:
    place("A", None, {b: int(round(v)) for b, v in k["a"].items()}, 1.0, (1290, 1240), ex=k, label="A writes the ledger")
rc = [k for k in P["L"]["keys"]["C"] if k["tag"].startswith("receive")]
for j, k in enumerate(rc[2:5]):
    place("C", None, {b: int(round(v)) for b, v in k["a"].items()}, 1.0, (1480 + 170 * j, 1240), ex=k,
          props=("bag_n",), label=k["tag"].replace("receive ", ""))
im = Image.fromarray(np.clip(C, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(im)
f = font("sans", 20); fb = font("serif", 34)
d.text((40, 24), "La planche: puppets and key poses (handmade grey card, split pins; FK rig, poses on twos)", font=fb, fill=(230, 230, 230))
d.text((1050, 80), "kneel - reach - grasp - rise (identical keys L-S5 / E-S4), t relative to the hand-off", font=f, fill=(220, 220, 220))
d.text((40, 960), "walk with weight on the deflecting plank, far hand on the liana; crossings; ledger; receiving the bag", font=f, fill=(220, 220, 220))
for x, y, t in labels:
    d.text((x, y), t, font=f, fill=(225, 225, 225), anchor="ma")
im.save(OUT / "puppet-sheet.png")
im.save(HERE.parent / "puppet-sheet.png")
print("ok")
