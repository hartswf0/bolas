"""boucle-la U1 rig (SCION 32): pinned paper pieces cut from the Daumier print, posed by forward kinematics.

Importable by the page animator / editor:  import rig; R = rig.Rig(); gray, alpha, joints = R.render(pose, frame, (w, h))

Joint graph (root -> leaf, fixed multiplication order):
  feet (root lean)  -> body -> neck pin -> head
                       body -> elbow pin -> forearm(+hand) -> hand anchor (-> note, Odette)
Angles are image-space degrees, clockwise positive (y down).  Semantic sign per figure:
  gustave (faces right): lean + toward her | head + nods in/down, - jerks back nose-up | fore - raises the hand
  odette  (faces left):  lean - toward him, + recoils | head - forward/down at him, + back | fore + raises the hand
Draw order (back to front): backdrop, gustave head, gustave body, gustave fore, odette head, odette body, odette fore.
The head sits BEHIND its body so the neck underlap tucks under Daumier's collar line (no throat gap);
the forearm sits ON TOP with its round elbow cap over the upper sleeve.
frame = (s, ox, oy): s = output px per THUMB px (960-wide view), (ox, oy) = output position of thumb (0, 0).
"""
import json
import math
import os

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
INK, PAGE = 13, 251
ORDER = [("gustave", "head"), ("gustave", "body"), ("gustave", "fore"),
         ("odette", "head"), ("odette", "body"), ("odette", "fore")]


def R(deg, c):
    a = math.radians(deg)
    co, si = math.cos(a), math.sin(a)
    cx, cy = c
    return np.array([[co, -si, cx - co * cx + si * cy], [si, co, cy - si * cx - co * cy], [0, 0, 1]], np.float64)


def T(s, tx, ty):
    return np.array([[s, 0, tx], [0, s, ty], [0, 0, 1]], np.float64)


def ap(M, p):
    v = M @ np.array([p[0], p[1], 1.0])
    return (float(v[0]), float(v[1]))


class Rig:
    def __init__(self, manifest=None):
        manifest = manifest or os.path.join(ROOT, "films/swarm/boucle-la/cutouts.json")
        self.cj = json.load(open(manifest))
        self.K = self.cj["source"]["K"]
        self.pieces = {}
        for k, v in self.cj["pieces"].items():
            im = np.asarray(Image.open(os.path.join(ROOT, v["file"])).convert("RGBA"))
            self.pieces[k] = (im[..., 0].astype(np.float32), im[..., 3].astype(np.float32) / 255.0, v["offset"])
        r = self.cj["rig"]
        self.j = {f: {n: tuple(np.array(r["joints"][f][n]) * self.K) for n in r["joints"][f]} for f in r["joints"]}

    def fk(self, pose, frame):
        """Matrices source-px -> output-px for every piece; plus the joints in output px."""
        s, ox, oy = frame
        base = T(s / self.K, ox, oy)
        Ms, J = {}, {}
        for f in ("gustave", "odette"):
            P = pose[f]
            jf = self.j[f]
            root = base @ R(P.get("lean", 0.0), jf["feet"])
            Ms[f + "_body"] = root
            Ms[f + "_head"] = root @ R(P.get("head", 0.0), jf["neck"])
            Ms[f + "_fore"] = root @ R(P.get("fore", 0.0), jf["elbow"])
            J[f] = {"feet": ap(root, jf["feet"]), "neck": ap(root, jf["neck"]),
                    "neck_on_head": ap(Ms[f + "_head"], jf["neck"]),
                    "elbow": ap(root, jf["elbow"]), "elbow_on_fore": ap(Ms[f + "_fore"], jf["elbow"]),
                    "hand": ap(Ms[f + "_fore"], jf["hand"]), "mouth": ap(Ms[f + "_head"], jf["mouth"])}
        return Ms, J

    def warp(self, canvas, cov, key, M, size, shadow=True):
        g, a, (x0, y0) = self.pieces[key]
        Mo = M @ np.array([[1, 0, x0], [0, 1, y0], [0, 0, 1]], np.float64)
        w, h = size
        gw = cv2.warpAffine(g, Mo[:2], (w, h), flags=cv2.INTER_CUBIC, borderValue=PAGE)
        aw = cv2.warpAffine(a, Mo[:2], (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
        if shadow:  # paper on paper: faint 3 px contact shadow, down-right
            sh = cv2.GaussianBlur(np.roll(np.roll(aw, 3, 0), 3, 1), (0, 0), 1.5) * 0.20
            canvas[:] = canvas * (1 - sh) + INK * sh
        canvas[:] = canvas * (1 - aw) + np.clip(gw, INK, PAGE) * aw
        cov[:] = np.maximum(cov, aw)

    def render(self, pose, frame, size, ground=PAGE, backdrop=True):
        w, h = size
        cv_ = np.full((h, w), float(ground), np.float32)
        cov = np.zeros((h, w), np.float32)
        Ms, J = self.fk(pose, frame)
        if backdrop and "backdrop" in self.pieces:
            s, ox, oy = frame
            self.warp(cv_, cov, "backdrop", T(s / self.K, ox, oy), size, shadow=False)
        for f, pn in ORDER:
            self.warp(cv_, cov, f"{f}_{pn}", Ms[f"{f}_{pn}"], size)
        return np.clip(cv_, 0, 255), cov, J


def pose_from(d):
    return {"gustave": dict(d["gustave"]), "odette": dict(d["odette"])}
