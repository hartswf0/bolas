"""Shared paths, score access and the stage mapping for SCION 34 (ARAP)."""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # paeleo/handmade/34-arap
REPO = os.path.abspath(os.path.join(ROOT, '..', '..', '..'))
KIT = os.path.join(ROOT, '..', 'kit')
SCORE_PATH = os.path.join(ROOT, '..', 'score', 'threshold-score.json')
CACHE = os.path.join(HERE, 'cache')
ASSETS = os.path.join(ROOT, 'assets')
DRAW = os.path.join(ASSETS, 'drawings')
MESH = os.path.join(ASSETS, 'mesh')
FPS = 24
N_SCENE = 768
W, H = 1280, 720
for d in (CACHE, DRAW, MESH):
    os.makedirs(d, exist_ok=True)


def score():
    return json.load(open(SCORE_PATH))


# ---- stage: a cutaway seen from the side. The door plane (wall) is vertical, crossed by the dog's path.
# World metres along the porch use the score's x for the dog. The door plane is placed at the sill (x = 0.56):
# a dog centred at x = 0.59 lies with its front half inside the door frame and its back half on the porch.
DOOR_X = 0.56
# Two fixed camera set-ups (a cut at CUT_T): A wide, B closer on the sill.
CUT_T = 20.5
CAMS = {
    'A': dict(s=205.0, door_px=392.0, floor_px=618.0),
    'B': dict(s=300.0, door_px=500.0, floor_px=640.0),
}


def cam_for(t):
    return CAMS['A'] if t < CUT_T else CAMS['B']


def world_to_px(x, y, cam):
    """x metres (score frame), y metres above the porch floor -> screen px."""
    return cam['door_px'] + cam['s'] * (x - DOOR_X), cam['floor_px'] - cam['s'] * y


def px_to_world_x(px, cam):
    return (px - cam['door_px']) / cam['s'] + DOOR_X


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)
