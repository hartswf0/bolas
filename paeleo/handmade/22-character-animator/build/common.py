"""SCION 22 shared constants: score, time base, camera, easing."""
import json, os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(FOLDER)))
CACHE = os.path.join(HERE, 'cache')
os.makedirs(CACHE, exist_ok=True)
SCORE = json.load(open(os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')))
FPS = 24
N = 768
W, H = 1280, 720
SILL = SCORE['places']['sill']

# my world (side view along the floor, metres, score x): the wall band (door frame) spans WALL_IN..WALL_OUT,
# the sill board sits on it; inside is x < WALL_IN.  The person's places are mine (beside = PERSON_BESIDE).
WALL_IN, WALL_OUT = 0.34, 0.56
DOOR_TOP = 2.05
DOOR_W = 0.86            # door leaf width (swings into the room, hinge at the wall's inner face)
PERSON_DOORWAY = -0.20
PERSON_BESIDE = -1.05
STEPS_X = 4.9


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def ramp(t, t0, t1):
    return ease((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)


def lerp(a, b, u):
    return a + (b - a) * u


def score_frame(i):
    return SCORE['frames'][min(max(i, 0), N - 1)]


def load(name):
    return json.load(open(os.path.join(CACHE, name)))


def save(name, obj):
    json.dump(obj, open(os.path.join(CACHE, name), 'w'))


# ---- camera: a locked-off wide stage until the dog commits, then a slow push that keeps the person and the dog in frame
def camera_track():
    xs = np.array([f['dog']['x'] for f in SCORE['frames']])
    cams = []
    s_prev = None
    left_prev = None
    for i in range(N):
        t = i / FPS
        if t < 14.6:
            s_goal, left_goal = 190.0, -1.45
        else:
            # look ahead a little so the frame anticipates where the dog is going
            xa = xs[min(N - 1, i + 18)]
            s_goal = min(318.0, 1280.0 / (xa + 0.75 + 1.48))
            left_goal = -1.48
        if s_prev is None:
            s, left = s_goal, left_goal
        else:
            k = 0.035
            s = s_prev + (s_goal - s_prev) * k
            left = left_prev + (left_goal - left_prev) * k
        s_prev, left_prev = s, left
        camx = left + 640.0 / s
        floor = 600.0 + (s - 196.0) / (318.0 - 196.0) * 22.0   # floor line drifts a touch lower as we push in
        cams.append({"s": float(s), "camx": float(camx), "floor": float(floor)})
    return cams


def w2s(cam, x, y):
    return (640.0 + (x - cam['camx']) * cam['s'], cam['floor'] - y * cam['s'])


def s2w_x(cam, sx):
    return cam['camx'] + (sx - 640.0) / cam['s']
