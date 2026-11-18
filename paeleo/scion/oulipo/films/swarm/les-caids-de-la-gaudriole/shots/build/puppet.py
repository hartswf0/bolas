"""Forward kinematics of the U2 rig from puppets/rig.json + part PNGs (read-only).
world(part) = world(parent) @ L2P @ R(angle - base, pivot); draw = world @ T(origin).
Compositing (SCION #45 holdout): canvas = canvas*(1-matte) + matte; canvas *= (1-ink).
Then the front layer (balloons, lettering, frames, marks) multiplies on top, margins cleared
exactly as rig_build.draw_front does."""
import os, json, math
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.normpath(os.path.join(HERE, "../.."))
PUP = os.path.join(WS, "puppets")
RIG = json.load(open(os.path.join(PUP, "rig.json")))
SHEET = json.load(open(os.path.join(WS, "strip/sheet.json")))
SW, SH = SHEET["W"], SHEET["H"]
P1 = SHEET["panels"]["P1"]["x"]; P2 = SHEET["panels"]["P2"]["x"]; PY0, PY1 = SHEET["panels"]["P1"]["y"]
PARTS = {p["name"]: p for p in RIG["parts"]}
DRAW = [n for n in RIG["draw_order"] if n in PARTS]


def T(tx, ty): return np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]], float)


def R(deg, cx=0.0, cy=0.0):
    t = math.radians(deg); c, s = math.cos(t), math.sin(t)
    return T(cx, cy) @ np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], float) @ T(-cx, -cy)


def m3(l): return np.vstack([np.array(l, float), [0, 0, 1]])


_img = {}
for n, p in PARTS.items():
    la = np.asarray(Image.open(os.path.join(PUP, p["png"])).convert("LA"), np.float32) / 255.0
    mat = la[..., 1]; ink = (1 - la[..., 0]) * mat
    _img[n] = (ink, mat)
BACK = np.asarray(Image.open(os.path.join(PUP, "parts/layer-back.png")).convert("L"), np.float32) / 255.0
FRONT = np.asarray(Image.open(os.path.join(PUP, "parts/layer-front.png")).convert("L"), np.float32) / 255.0


def world(n, pose):
    p = PARTS[n]
    ang = pose.get(n, p["rest_deg"])
    Wp = world(p["parent"], pose) if p["parent"] else np.eye(3)
    return Wp @ m3(p["L2P"]) @ R(ang - p["base_deg"], *p["pivot_local"])


def render(pose):
    cv = BACK.copy()
    for n in DRAW:
        p = PARTS[n]; ink, mat = _img[n]
        A2 = (world(n, pose) @ T(*p["origin_local"]))[:2].astype(np.float32)
        ik = cv2.warpAffine(ink, A2, (SW, SH), flags=cv2.INTER_LINEAR, borderValue=0)
        mt = cv2.warpAffine(mat, A2, (SW, SH), flags=cv2.INTER_LINEAR, borderValue=0)
        cv = cv * (1 - mt) + mt
        cv = cv * (1 - ik)
    a = np.clip(cv * 255 + 0.5, 0, 255).astype(np.uint8)
    a[:, :P1[0] - 3] = 255; a[:, P2[1] + 4:] = 255; a[:PY0 - 3] = 255; a[PY1 + 4:] = 255
    a[:, P1[1] + 4:P2[0] - 3] = 255
    out = np.minimum(a.astype(np.float32), FRONT * 255)  # front ink drawn over
    out = np.where(HOLD, FRONT * 255, out)               # balloon cards hold out the figures
    return out.astype(np.uint8)


def _holdout():
    global HOLD
    HOLD = np.zeros((SH, SW), bool)
    art = np.asarray(Image.open(os.path.join(WS, "strip/strip-art.png")).convert("L")).astype(int)
    r = render({}).astype(int)
    m = ((art > r + 2)).astype(np.uint8)
    # balloon interiors (sheet.json) + the tail patches where the printed balloon covers ink
    for k, (x0, x1, y0, y1) in SHEET["balloons"].items():
        if isinstance(x0, (int, float)):
            m[int(y0) + 3:int(y1) - 3, int(x0) + 3:int(x1) - 3] = 1
    HOLD = cv2.dilate(m, np.ones((3, 3), np.uint8)).astype(bool) & (np.abs(FRONT * 255 - art) <= 2)


HOLD = np.zeros((SH, SW), bool)
_holdout()


if __name__ == "__main__":
    art = np.asarray(Image.open(os.path.join(WS, "strip/strip-art.png")).convert("L")).astype(int)
    r = render({}).astype(int)
    d = np.abs(r - art)
    print("rest vs strip-art max", d.max(), "n>2", (d > 2).sum(), "mean", d.mean())
