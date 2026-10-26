"""Shared geometry for SCION 46: the dog's 3D landmark vector (dog-local), the camera, projections and fits.
Coordinates: world metres. X along the porch (threshold plane X=0, inside negative), Y up, Z toward the camera side.
Dog-local: u forward, v up, s = the dog's right side. Canonical (authoring) views: the dog faces screen-right and we see
its right side when alpha=90; alpha is the camera azimuth measured from the dog's nose (0 front, 90 side, 180 rear)."""
import numpy as np, json, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
CACHE = os.path.join(HERE, 'cache')
W, H = 1280, 720
FPS = 24

# ---- the dog's landmark vector (body), dog-local (u fwd, v up, s right), origin = mid-body on the ground
BODY = {
    'W':  (0.27, 0.60, 0.0),    # withers
    'R':  (-0.30, 0.57, 0.0),   # rump top
    'T':  (-0.41, 0.55, 0.0),   # tail base
    'C':  (0.43, 0.43, 0.0),    # chest front
    'K':  (0.22, 0.30, 0.0),    # brisket
    'B':  (-0.17, 0.35, 0.0),   # belly tuck
    'N':  (0.34, 0.56, 0.0),    # neck base (neck pivot)
    'SjR': (0.25, 0.43, 0.11), 'SjL': (0.25, 0.43, -0.11),   # shoulder joints
    'HjR': (-0.27, 0.45, 0.10), 'HjL': (-0.27, 0.45, -0.10), # hip joints
    'Wd': (0.0, 0.0, 0.0),
}
# torso half-widths used only to place side landmarks for fitting
BODY['FlR'] = (0.0, 0.47, 0.15); BODY['FlL'] = (0.0, 0.47, -0.15)   # flank (widest)
TORSO_KEYS = ['W', 'R', 'C', 'K', 'B', 'SjR', 'SjL', 'HjR', 'HjL', 'FlR', 'FlL', 'T', 'N']

# ---- head landmark vector, head-local (h fwd, v up, s right), origin = skull pivot S
HEAD = {
    'S':   (0.0, 0.0, 0.0),
    'Nz':  (0.25, -0.045, 0.0),   # nose tip
    'Stp': (0.10, 0.045, 0.0),    # stop
    'ER':  (0.075, 0.035, 0.045), 'EL': (0.075, 0.035, -0.045),
    'EbR': (-0.025, 0.085, 0.055), 'EbL': (-0.025, 0.085, -0.055),
    'J':   (0.15, -0.085, 0.0),   # chin
    'Th':  (-0.02, -0.075, 0.0),  # throat
    'Cr':  (0.0, 0.105, 0.0),     # cranium top
    'O':   (-0.085, 0.03, 0.0),   # occiput
    'ChR': (0.03, -0.02, 0.07), 'ChL': (0.03, -0.02, -0.07),
}
HEAD_KEYS = ['S', 'Nz', 'Stp', 'ER', 'EL', 'EbR', 'EbL', 'J', 'Th', 'Cr', 'O', 'ChR', 'ChL']
EAR_LEN = 0.12


def mirror_key(k):
    if len(k) < 2: return k
    if k.endswith('R'): return k[:-1] + 'L'
    if k.endswith('L'): return k[:-1] + 'R'
    return k


def canon_project(p, alpha_deg):
    """orthographic canonical view: dog facing +u, camera at azimuth alpha toward its right side. returns (x right, y up)"""
    a = math.radians(alpha_deg)
    d = np.array([math.cos(a), 0, math.sin(a)])          # camera direction in (u, v, s)
    right = np.cross(-d, [0, 1, 0]); right /= np.linalg.norm(right)   # screen right
    # NB in (u,v,s) with s = right side, handedness: verify at alpha=90 -> right=(1,0,0)
    p = np.asarray(p, float)
    return np.array([p @ right, p[1]])


# ---- fits
def fit_similarity(src, dst):
    src = np.asarray(src, float); dst = np.asarray(dst, float)
    ms, md = src.mean(0), dst.mean(0); a = src - ms; b = dst - md
    # complex least squares: b = z * a
    za = a[:, 0] + 1j * a[:, 1]; zb = b[:, 0] + 1j * b[:, 1]
    z = (np.conj(za) @ zb) / max(1e-12, (np.conj(za) @ za).real)
    M = np.array([[z.real, -z.imag], [z.imag, z.real]])
    t = md - M @ ms
    return np.hstack([M, t[:, None]])


def fit_similarity_reflect(src, dst):
    """similarity that may include a reflection (for mirrored views)"""
    A = fit_similarity(src, dst)
    s2 = np.asarray(src, float).copy(); s2[:, 0] *= -1
    B = fit_similarity(s2, dst); B[:, 0] *= -1
    ea = residual(A, src, dst); eb = residual(B, src, dst)
    return A if ea <= eb else B


def fit_affine(src, dst):
    src = np.asarray(src, float); dst = np.asarray(dst, float)
    X = np.hstack([src, np.ones((len(src), 1))])
    M, *_ = np.linalg.lstsq(X, dst, rcond=None)
    return M.T


def residual(M, src, dst):
    src = np.asarray(src, float); dst = np.asarray(dst, float)
    return float(np.sqrt((((src @ M[:, :2].T + M[:, 2]) - dst) ** 2).sum(1).mean()))


def apply(M, pts):
    pts = np.asarray(pts, float)
    return pts @ M[:, :2].T + M[:, 2]


def two_point(a0, a1, b0, b1):
    """similarity mapping segment a0->a1 onto b0->b1"""
    return fit_similarity([a0, a1], [b0, b1])


# ---- camera
class Camera:
    def __init__(self, pos, target, hfov_deg):
        self.pos = np.asarray(pos, float); self.target = np.asarray(target, float)
        f = self.target - self.pos; self.f = f / np.linalg.norm(f)
        r = np.cross(self.f, [0, 1, 0]); self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.r, self.f)
        self.focal = (W / 2) / math.tan(math.radians(hfov_deg) / 2)

    def project(self, P):
        P = np.atleast_2d(np.asarray(P, float)) - self.pos
        x = P @ self.r; y = P @ self.u; z = P @ self.f
        z = np.maximum(z, 1e-3)
        return np.stack([W / 2 + self.focal * x / z, H / 2 - self.focal * y / z], 1), z

    def unproject_ground(self, sx, sy, Yplane=0.0):
        d = self.f + (sx - W / 2) / self.focal * self.r - (sy - H / 2) / self.focal * self.u
        t = (Yplane - self.pos[1]) / d[1]
        return self.pos + t * d


def load_score():
    return json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if b != a else float(x >= b)
    return t * t * (3 - 2 * t)


if __name__ == '__main__':
    for a in (45, 90, 135, 180):
        print('alpha', a)
        for k in TORSO_KEYS: print('  ', k, np.round(canon_project(BODY[k], a), 3))
        for k in HEAD_KEYS: print('  head', k, np.round(canon_project(HEAD[k], a), 3))
