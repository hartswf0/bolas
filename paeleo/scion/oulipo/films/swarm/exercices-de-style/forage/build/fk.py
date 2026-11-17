# Minimal FK assembler for rig.json (for the check sheet; the animator's es_lib can import draw_pose).
import json, math, numpy as np
from PIL import Image
ROOT = '/home/user/bolas/paeleo/scion/oulipo/'
def load(rigp=ROOT + 'films/swarm/exercices-de-style/forage/rig.json'):
    rig = json.load(open(rigp)); imgs = {k: Image.open(ROOT + p['file']).convert('RGBA') for k, p in rig['pieces'].items()}; return rig, imgs
def M_rot(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def M_tr(x, y): return np.array([[1, 0, x], [0, 1, y], [0, 0, 1.0]])
def draw_pose(rig, imgs, pose, canvas, at, scale):
    P = rig['pieces']; world = {}
    def wm(k):
        if k in world: return world[k]
        p = P[k]; piv = p['pivot_crop']
        if p['parent'] is None: m = M_tr(*at) @ np.diag([scale, scale, 1]) @ M_rot(pose.get(k, 0)) @ M_tr(-piv[0], -piv[1])
        else: m = wm(p['parent']) @ M_tr(*piv) @ M_rot(pose.get(k, 0)) @ M_tr(-piv[0], -piv[1])
        world[k] = m; return m
    for k in rig['z_order']:
        p = P[k]; m = wm(k) @ M_tr(*p['origin_in_crop'])  # local piece pixel -> canvas
        inv = np.linalg.inv(m)
        canvas.alpha_composite(imgs[k].transform(canvas.size, Image.AFFINE, tuple(inv[:2].ravel()), Image.BICUBIC))
    return world
