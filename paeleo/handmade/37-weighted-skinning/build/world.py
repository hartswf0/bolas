"""SCION 37 world: the porch, the house front with its doorway and sill, the lit room, a crate to sit on.
Plain faceted geometry (subdivided quads) with procedural materials computed per pixel from world position; nothing is
drawn by hand except what is listed here. World: X along the porch (score x; the facade face at X = 0.35, the room X < 0.2),
Y up (porch floor 0), Z across (the camera side is +Z)."""
import numpy as np

MAT = {'floor': 1, 'siding': 2, 'trim': 3, 'door': 4, 'ifloor': 5, 'iwall': 6, 'rug': 7, 'crate': 8, 'ground': 9,
       'window': 10, 'beam': 11, 'sill': 12, 'step': 13, 'dog': 20, 'person': 21, 'lamp': 14, 'picture': 15}
FACADE_X, WALL_IN_X = .35, .20
DOOR_Z, DOOR_H = .45, 2.05
WIN = (1.15, 2.05, .95, 1.95)           # z0 z1 y0 y1
LIGHT_POS = np.array([-1.05, 1.65, .10])


class Geo:
    def __init__(self):
        self.V = []; self.F = []; self.M = []; self.n = 0

    def quad(self, o, u, v, mat, nu=None, nv=None, cell=.18):
        o, u, v = (np.asarray(a, float) for a in (o, u, v))
        nu = nu or max(1, int(np.ceil(np.linalg.norm(u) / cell))); nv = nv or max(1, int(np.ceil(np.linalg.norm(v) / cell)))
        a, b = np.meshgrid(np.linspace(0, 1, nu + 1), np.linspace(0, 1, nv + 1), indexing='ij')
        P = o + a[..., None] * u + b[..., None] * v
        idx = np.arange((nu + 1) * (nv + 1)).reshape(nu + 1, nv + 1) + self.n
        i0, i1, i2, i3 = idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()
        # outward normal = u x v; the rasterizer keeps faces counter-clockwise seen from outside
        F = np.concatenate([np.stack([i0, i1, i2], 1), np.stack([i0, i2, i3], 1)])
        self.V.append(P.reshape(-1, 3)); self.F.append(F); self.M.append(np.full(len(F), mat)); self.n += len(P.reshape(-1, 3))

    def box(self, x0, x1, y0, y1, z0, z1, mat, faces='xXyYzZ', cell=.18):
        if 'x' in faces: self.quad((x0, y0, z0), (0, 0, z1 - z0), (0, y1 - y0, 0), mat, cell=cell)
        if 'X' in faces: self.quad((x1, y0, z0), (0, y1 - y0, 0), (0, 0, z1 - z0), mat, cell=cell)
        if 'y' in faces: self.quad((x0, y0, z0), (x1 - x0, 0, 0), (0, 0, z1 - z0), mat, cell=cell)
        if 'Y' in faces: self.quad((x0, y1, z0), (0, 0, z1 - z0), (x1 - x0, 0, 0), mat, cell=cell)
        if 'z' in faces: self.quad((x0, y0, z0), (0, y1 - y0, 0), (x1 - x0, 0, 0), mat, cell=cell)
        if 'Z' in faces: self.quad((x0, y0, z1), (x1 - x0, 0, 0), (0, y1 - y0, 0), mat, cell=cell)

    def done(self):
        return np.concatenate(self.V), np.concatenate(self.F), np.concatenate(self.M)


def static():
    g = Geo()
    # porch deck and its skirt, the steps, the yard
    g.box(WALL_IN_X - .01, 4.9, -.30, 0, -2.2, 2.6, MAT['floor'], faces='YX')
    g.box(4.9, 5.2, -.30, -.15, -1.2, 1.6, MAT['step'], faces='YXzZ')
    g.box(5.2, 5.5, -.45, -.30, -1.2, 1.6, MAT['step'], faces='YXzZ')
    g.box(-3.2, 4.9, -.45, -.30, 2.6, 2.62, MAT['step'], faces='Z')
    # facade: a grid that leaves the door and the window open
    zs = np.unique(np.r_[np.arange(-3.4, 3.41, .17), -DOOR_Z, DOOR_Z, WIN[0], WIN[1]]); zs = zs[(zs >= -3.4) & (zs <= 3.4)]
    ys = np.unique(np.r_[np.arange(0, 3.21, .16), DOOR_H, WIN[2], WIN[3]])
    for a in range(len(zs) - 1):
        for b in range(len(ys) - 1):
            zc, yc = (zs[a] + zs[a + 1]) / 2, (ys[b] + ys[b + 1]) / 2
            if abs(zc) < DOOR_Z and yc < DOOR_H: continue
            if WIN[0] < zc < WIN[1] and WIN[2] < yc < WIN[3]: continue
            g.quad((FACADE_X, ys[b], zs[a]), (0, ys[b + 1] - ys[b], 0), (0, 0, zs[a + 1] - zs[a]), MAT['siding'], 1, 1)
    # door jambs and head, window reveals (the wall's thickness)
    g.quad((WALL_IN_X, 0, -DOOR_Z), (FACADE_X - WALL_IN_X, 0, 0), (0, DOOR_H, 0), MAT['trim'])          # faces +Z
    g.quad((WALL_IN_X, 0, DOOR_Z), (0, DOOR_H, 0), (FACADE_X - WALL_IN_X, 0, 0), MAT['trim'])           # faces -Z
    g.quad((WALL_IN_X, DOOR_H, -DOOR_Z), (FACADE_X - WALL_IN_X, 0, 0), (0, 0, 2 * DOOR_Z), MAT['trim'])
    # casing around the door, the sill (threshold board), window casing and the lit glass
    g.box(FACADE_X, FACADE_X + .03, 0, DOOR_H + .12, -DOOR_Z - .12, -DOOR_Z, MAT['trim'], faces='XzZY')
    g.box(FACADE_X, FACADE_X + .03, 0, DOOR_H + .12, DOOR_Z, DOOR_Z + .12, MAT['trim'], faces='XzZY')
    g.box(FACADE_X, FACADE_X + .03, DOOR_H, DOOR_H + .12, -DOOR_Z, DOOR_Z, MAT['trim'], faces='XyY')
    g.box(WALL_IN_X - .02, FACADE_X + .10, 0, .035, -DOOR_Z, DOOR_Z, MAT['sill'], faces='YX')
    z0, z1, y0, y1 = WIN
    for (a0, a1, b0, b1) in ((z0 - .08, z0, y0 - .08, y1 + .08), (z1, z1 + .08, y0 - .08, y1 + .08), (z0, z1, y0 - .08, y0), (z0, z1, y1, y1 + .08)):
        g.box(FACADE_X, FACADE_X + .03, b0, b1, a0, a1, MAT['trim'], faces='XzZyY', cell=.1)
    g.quad((FACADE_X - .05, WIN[2], WIN[0]), (0, WIN[3] - WIN[2], 0), (0, 0, WIN[1] - WIN[0]), MAT['window'])
    # the room: floor, back wall, side walls, ceiling, a rug, a picture, a standing lamp
    g.quad((-3.4, .0, -2.2), (0, 0, 4.4), (3.6, 0, 0), MAT['ifloor'], cell=.25)
    g.quad((-3.4, 0, -2.2), (0, 2.7, 0), (0, 0, 4.4), MAT['iwall'], cell=.3)          # back wall faces +X
    g.quad((-3.4, 0, -2.2), (3.6, 0, 0), (0, 2.7, 0), MAT['iwall'], cell=.3)          # faces +Z
    g.quad((-3.4, 0, 2.2), (0, 2.7, 0), (3.6, 0, 0), MAT['iwall'], cell=.3)
    g.quad((-3.4, 2.7, -2.2), (3.6, 0, 0), (0, 0, 4.4), MAT['iwall'], cell=.3)
    g.quad((-2.3, .006, -.75), (0, 0, 1.5), (2.0, 0, 0), MAT['rug'], cell=.12)
    g.quad((-3.39, 1.15, -.55), (0, .62, 0), (0, 0, .85), MAT['picture'], cell=.1)
    g.box(-1.42, -1.30, 0, 1.55, .10, .22, MAT['beam'], cell=.2)
    g.box(-1.55, -1.15, 1.55, 1.85, -.05, .35, MAT['lamp'], cell=.1)
    # the crate the person sits on
    g.box(.46, .98, 0, .42, -1.40, -.86, MAT['crate'], faces='XYzZx', cell=.09)
    # porch posts and the beam above
    return g.done()


def door_geo(angle):
    """the door slab, hinged at the room side of the jamb (Z = -DOOR_Z), opening inward by `angle` radians"""
    g = Geo()
    w, th, h = 2 * DOOR_Z - .02, .045, DOOR_H - .02
    g.box(0, th, .01, h, 0, w, MAT['door'], cell=.2)
    V, F, M = g.done()
    # local: x thickness (0 at the facade side), z along the width; hinge at the origin
    c, s = np.cos(angle), np.sin(angle)
    Rm = np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])            # rotate +Z toward -X
    V = V - [th, 0, 0]
    V = V @ Rm.T + [WALL_IN_X, 0, -DOOR_Z + .01]
    return V, F, M


def door_blocks(P, angle):
    """True where the segment P->LIGHT crosses the door slab (top view)."""
    hinge = np.array([WALL_IN_X, -DOOR_Z]); w = 2 * DOOR_Z
    tip = hinge + w * np.array([-np.sin(angle), np.cos(angle)])
    a = np.stack([P[:, 0], P[:, 2]], 1); b = np.array([LIGHT_POS[0], LIGHT_POS[2]])
    def cr(o, p, q): return (p[..., 0] - o[..., 0]) * (q[..., 1] - o[..., 1]) - (p[..., 1] - o[..., 1]) * (q[..., 0] - o[..., 0])
    d1 = cr(hinge, tip, a); d2 = cr(hinge, tip, b)
    d3 = cr(a, b, hinge[None]); d4 = cr(a, b, tip[None])
    return (np.sign(d1) != np.sign(d2)) & (np.sign(d3) != np.sign(d4))


def through_door(P):
    """True where the segment from P to the room light passes through the doorway or the window (outside points)"""
    L = LIGHT_POS
    t = (FACADE_X - L[0]) / np.where(np.abs(P[:, 0] - L[0]) < 1e-6, 1e-6, P[:, 0] - L[0])
    Y = L[1] + t * (P[:, 1] - L[1]); Z = L[2] + t * (P[:, 2] - L[2])
    t2 = (WALL_IN_X - L[0]) / np.where(np.abs(P[:, 0] - L[0]) < 1e-6, 1e-6, P[:, 0] - L[0])
    Y2 = L[1] + t2 * (P[:, 1] - L[1]); Z2 = L[2] + t2 * (P[:, 2] - L[2])
    door = (np.abs(Z) < DOOR_Z) & (Y < DOOR_H) & (np.abs(Z2) < DOOR_Z) & (Y2 < DOOR_H)
    win = (Z > WIN[0]) & (Z < WIN[1]) & (Y > WIN[2]) & (Y < WIN[3])
    return door, win
