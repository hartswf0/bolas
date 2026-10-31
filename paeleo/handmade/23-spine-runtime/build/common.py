"""SCION 23 · Spine runtime — shared constants: time base, world <-> screen, camera.

World: metres. x = the score's x (porch distance from the threshold), y up, d = depth away from the camera.
The camera is an orthographic cross-section of the porch and the house, tilted down by EPS degrees, so a point
(x, y, d) lands on the wide-frame screen at  X = X0 + K*x,  Y = YF - K*(y*cos(EPS) + d*sin(EPS)).
Skeleton space: centimetres, y up, root at the dog's mid-body on the floor; the skeleton plane is the camera plane.
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(FOLDER)))
CACHE = os.path.join(HERE, 'cache')
ACTOR = os.path.join(FOLDER, 'actor')
SCORE_PATH = os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')

FPS = 24
N = 768
W, H = 1280, 720
EPS = math.radians(14.0)          # camera tilt
CE, SE = math.cos(EPS), math.sin(EPS)
K = 190.0                         # wide-frame pixels per metre
X0 = 350.0                        # wide-frame screen x of score x = 0
YF = 560.0                        # wide-frame screen y of the floor at depth 0

# the house, in score x (metres): the wall section with the doorway, and the sill board
WALL_IN, WALL_OUT = 0.44, 0.58    # inner and outer face of the wall
SILL = (0.42, 0.60)
DOOR_DEPTH = (-0.46, 0.46)        # doorway in depth
LINTEL = 2.05
PORCH_NEAR, PORCH_FAR = -0.95, 1.65
ROOM_BACK = 2.3

def load_score():
    return json.load(open(SCORE_PATH))

def wide(x, y, d=0.0):
    """world (m) -> wide-frame screen px"""
    return X0 + K * x, YF - K * (y * CE + d * SE)

def smooth(a, b, t):
    if t <= a: return 0.0
    if t >= b: return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)

def camera(t):
    """zoom and the wide-frame point that sits at the screen centre. Wide until 17.5 s, then a slow push-in on the
    doorway that is complete by 23.6 s (before the dog lies down), held to the end."""
    u = smooth(17.5, 23.6, t)
    u = u * u * (3 - 2 * u) * 0.5 + u * 0.5
    z = 1.0 + 0.62 * u
    cx = 640.0 + (wide(0.42, 0)[0] + 18 - 640.0) * u
    cy = 360.0 + (446.0 - 360.0) * u
    return z, cx, cy

def to_screen(z, cx, cy, X, Y):
    return (X - cx) * z + W / 2, (Y - cy) * z + H / 2

def from_screen(z, cx, cy, sx, sy):
    return (sx - W / 2) / z + cx, (sy - H / 2) / z + cy
