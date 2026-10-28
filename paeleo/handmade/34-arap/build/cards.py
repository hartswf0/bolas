"""Title card and end card (3 s each). The end card shows the mesh: the rest triangulation and the same triangles
solved into the lying pose, with what the film is made of."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from rig import DogP, pose_P
from raster import Tex, draw_pieces

SERIF = '/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf'
SERIF_I = '/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
BG = (24, 26, 34)
INKL = (232, 222, 200)


def mesh_image(d, X, Xh, scale, ox, oy, size, tex=True, wire=0.9):
    S = np.stack([ox + scale * X[:, 0], oy - scale * X[:, 1]], 1)
    Sh = np.stack([ox + scale * Xh[:, 0], oy - scale * Xh[:, 1]], 1)
    tb = Tex(os.path.join(DRAW, 'P_body.png')); th = Tex(os.path.join(DRAW, 'P_head.png'))
    pm, _ = draw_pieces(size, [(S, d.body.T, d.body.uv, tb, d.body.layer, False), (Sh, d.head.T, d.head.uv, th, d.head.layer, False)],
                        wire=[wire, wire])
    return pm


def title():
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(SERIF, 54); f2 = ImageFont.truetype(SERIF_I, 30); f3 = ImageFont.truetype(MONO, 18)
    t1 = 'PAE-02 · SCION 34 · ARAP'
    t2 = 'Preserve-Shape Deformation Swarm'
    t3 = 'the threshold: an engraved dog bent as rigidly as possible'
    for txt, f, y, col in ((t1, f1, 270, INKL), (t2, f2, 345, (200, 190, 170)), (t3, f3, 420, (150, 146, 140))):
        w = dr.textlength(txt, font=f)
        dr.text(((W - w) / 2, y), txt, font=f, fill=col)
    return im


def endcard():
    d = DogP()
    rest = pose_P(d, dict(head=0.9, ear=1.0, tail=0.5))
    X0, Xh0 = d.solve(rest, iters=30, X0=d.body.V.copy()); X0, Xh0 = X0.copy(), Xh0.copy()
    lie = pose_P(d, dict(lie=1.0, head=0.6, ear=0.7, tail=0.3))
    X1, Xh1 = d.solve(lie, iters=60, X0=X0)
    im = Image.new('RGB', (W, H), BG)
    base = np.asarray(im).astype(np.float32) / 255
    for X, Xh, ox in ((X0, Xh0, 300), (X1, Xh1, 900)):
        pm = mesh_image(d, X, Xh, 0.36, ox, 360, (W, H), wire=0.85)
        base = base * (1 - pm[..., 3:4]) + pm[..., :3] * np.array([0.95, 0.93, 0.88])
    im = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(SERIF, 30); f2 = ImageFont.truetype(SERIF_I, 21); f3 = ImageFont.truetype(MONO, 15)
    dr.text((300 - dr.textlength('rest mesh', font=f2) / 2, 385), 'rest mesh', font=f2, fill=(200, 190, 170))
    dr.text((900 - dr.textlength('the same triangles, lying', font=f2) / 2, 385), 'the same triangles, lying', font=f2, fill=(200, 190, 170))
    t = 'What it is made of'
    dr.text(((W - dr.textlength(t, font=f1)) / 2, 40), t, font=f1, fill=INKL)
    lines = [
        'The dog, the woman and the place are engravings drawn here in code (no found pixels).',
        'Each figure is a Delaunay triangle mesh (dog: 1,086 + 265 vertices) bent by a local-global',
        'as-rigid-as-possible solve (one rotation per vertex cell, hard handles, sparse LU) from',
        '13-17 handles. The turns are substitutions between a profile, a rear and a front drawing.',
        'Trees and moon: Quick, Draw! (CC BY 4.0, Google Creative Lab and contributors).',
        'Voice, boards, door and dusk are synthesized. Timing: the PAELEO threshold score.',
    ]
    y = 450
    for l in lines:
        dr.text(((W - dr.textlength(l, font=f3)) / 2, y), l, font=f3, fill=(176, 170, 160)); y += 26
    return im


if __name__ == '__main__':
    out = os.path.join(CACHE, 'cards'); os.makedirs(out, exist_ok=True)
    title().save(os.path.join(out, 'title.png'))
    endcard().save(os.path.join(out, 'end.png'))
