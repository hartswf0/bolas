"""Frame regression renderer: solves every handle set in order (warm-started), rasterises the engraved meshes,
lights them with the place, writes JPEG frames to build/cache/frames/ and the measurements to cache/measure.json.

usage: python3 render.py [first last]   (scene frame range; default all 768)
"""
import json, os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from rig import DogP, DogView, pose_P, LEGS
from prig import Person
from raster import Tex, draw_pieces
from world import World

FR = os.path.join(CACHE, 'frames')
os.makedirs(FR, exist_ok=True)
FONT_I = '/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf'
WIRE_DOG = 0.30
WIRE_PERSON = 0.22

SPEECH = [(1.0, 2.3, 'Come here.'), (3.4, 4.6, 'Come here!'), (7.4, 9.4, "It's all right."),
          (10.4, 11.6, "It's all right."), (26.4, 27.4, 'Come in.')]


def speech_at(t):
    for a, b, s in SPEECH:
        if a - 0.05 <= t < b + 0.35:
            return s, (t - a), (b + 0.35 - t)
    return None


class Renderer:
    def __init__(self):
        self.dog = DogP()
        self.views = {'R0': DogView('R0'), 'F0': DogView('F0')}
        self.per = Person()
        self.tex = {}
        for n in ('P_body', 'P_head', 'R0_body', 'R0_head', 'F0_body', 'F0_head', 'Q_stand', 'Q_sit', 'Q_arm'):
            self.tex[n] = Tex(os.path.join(DRAW, n + '.png'), scale=0.5)
        self.worlds = {k: World(v) for k, v in CAMS.items()}
        self.font = ImageFont.truetype(FONT_I, 30)
        self.prevX = {}
        self.last_view = None

    def dog_pieces(self, f):
        view, mirror, ex = f['view'], f['mirror'], f['extra']
        a = f['acts']
        first = (view, mirror) != self.last_view
        self.last_view = (view, mirror)
        iters = 40 if first else 8
        if view == 'P':
            d = self.dog
            pose = pose_P(d, a, paws={L: f['paws'][L] for L in LEGS}, lifts=f['lifts'])
            if ex.get('head_flip'):
                pose['head_flip'] = True
                pose['head_flip_a'] = 0.15 if f['t'] > 7 else -0.35
            X, Xh = d.solve(pose, iters=iters, X0=None if not first else d.body.V.copy())
            items = [(X, d.body, 'P_body'), (Xh, d.head, 'P_head')]
            nose = Xh[d.G['nose']].mean(0); joint = Xh[d.G['skull']].mean(0)
            inv = d.solver.inverted(X) + d.hsolver.inverted(Xh) if not pose.get('head_flip') else d.solver.inverted(X)
            energy = d.solver.energy(X)
            self.withers = X[d.H['shoulder']].mean(0)
        else:
            self.withers = None
            v = self.views[view]
            aa = dict(a); aa.update(ex)
            if view == 'F0':
                aa['crouch'] = a['crouch'] + 0.4 * a['lie']
                aa['ear'] = max(a['ear'], 0.8)
            else:
                aa['ear'] = a['ear']
            X, Xh = v.solve(aa, iters=iters, X0=None if not first else v.body.V.copy())
            if view == 'R0':
                items = [(Xh, v.head, 'R0_head'), (X, v.body, 'R0_body')]
                nose = None; joint = Xh.mean(0)
            else:
                items = [(X, v.body, 'F0_body'), (Xh, v.head, 'F0_head')]
                nose = Xh[v.G['nose']].mean(0); joint = Xh[v.G['skull']].mean(0)
            inv = v.solver.inverted(X) + v.hsolver.inverted(Xh)
            energy = v.solver.energy(X)
        return items, nose, joint, inv, energy

    def frame(self, f):
        t = f['t']
        cam = cam_for(t)
        world = self.worlds['A' if t < CUT_T else 'B']
        s = cam['s'] / 1000.0
        # ---- dog
        items, nose, joint, inv, energy = self.dog_pieces(f)
        sign = -1.0 if f['mirror'] else 1.0
        fs = f['extra'].get('fs', 1.0)
        cx, fy = world_to_px(f['x'], 0.0, cam)

        def to_screen(X):
            return np.stack([cx + sign * fs * s * X[:, 0], fy - s * X[:, 1]], 1)
        dog_items = []
        for X, piece, tname in items:
            dog_items.append((to_screen(X), piece.T, piece.uv, self.tex[tname], piece.layer, f['mirror']))
        dog_pm, dog_bb = draw_pieces((W, H), dog_items, wire=[WIRE_DOG] * len(dog_items))
        # ---- person
        p = f['person']
        px_c = cam['door_px'] + cam['s'] * p['x']
        pitems = []
        for nm, X in self.per.solve(p, t):
            piece = {'stand': self.per.st, 'sit': self.per.si, 'arm': self.per.ar}[nm]
            tn = {'stand': 'Q_stand', 'sit': 'Q_sit', 'arm': 'Q_arm'}[nm]
            Sx = np.stack([px_c + s * X[:, 0], fy - s * X[:, 1]], 1)
            if nm == 'sit':
                Sx[:, 0] += 0.0
            pitems.append((Sx, piece.T, piece.uv, self.tex[tn], piece.layer, False))
        per_pm, _ = draw_pieces((W, H), pitems, wire=[WIRE_PERSON] * len(pitems))
        # ---- contact shadows (soft ellipses on the boards)
        sh = np.zeros((H, W), np.float32)
        ys, xs = np.mgrid[0:H, 0:W]
        dog_a = dog_pm[..., 3]
        if dog_a.sum() > 0:
            cols = np.nonzero(dog_a.sum(0) > 0.5)[0]
            x0, x1 = cols.min(), cols.max()
            rx = (x1 - x0) / 2 * 0.95; mx = (x0 + x1) / 2
            sh += 0.45 * np.exp(-(((xs - mx) / max(rx, 1)) ** 4 + ((ys - fy - 3) / (0.03 * cam['s'])) ** 2))
        sh += 0.35 * np.exp(-(((xs - (px_c + 0.05 * cam['s'])) / (0.3 * cam['s'])) ** 4 + ((ys - fy - 3) / (0.03 * cam['s'])) ** 2))
        rgb, L = world.compose(t, f['door_open'], [])
        rgb = rgb * (1 - np.clip(sh, 0, 0.6)[..., None])
        Lo = world.Lobj
        rgb = rgb * (1 - per_pm[..., 3:4]) + per_pm[..., :3] * Lo
        rgb = rgb * (1 - dog_pm[..., 3:4]) + dog_pm[..., :3] * Lo
        # ---- the spoken words, quietly, at the foot of the frame
        img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
        sp = speech_at(t)
        if sp:
            txt, since, until = sp
            al = min(1.0, since / 0.15, until / 0.3)
            dr = ImageDraw.Draw(img, 'RGBA')
            soft = txt in ("It's all right.", 'Come in.')
            col = (235, 222, 196, int(255 * al * (0.62 if soft else 0.9)))
            tw = dr.textlength(txt, font=self.font)
            dr.text(((W - tw) / 2, 668), txt, font=self.font, fill=col)
        # ---- measurements from the render
        m = {}
        if dog_a.sum() > 0:
            tot = dog_a.sum()
            m['cx'] = float((dog_a * xs).sum() / tot); m['cy'] = float((dog_a * ys).sum() / tot)
            rows = np.nonzero(dog_a.sum(1) > 0.5)[0]; cols = np.nonzero(dog_a.sum(0) > 0.5)[0]
            m['bbox'] = [int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max())]
            m['area'] = float(tot)
        if nose is not None:
            ns = to_screen(nose[None])[0]; js = to_screen(joint[None])[0]
            m['nose'] = [float(ns[0]), float(ns[1])]; m['joint'] = [float(js[0]), float(js[1])]
        if self.withers is not None:
            m['withers_y'] = float(to_screen(self.withers[None])[0][1])
        m['inverted'] = int(inv); m['energy'] = round(float(energy), 5)
        m['x_world_measured'] = float(px_to_world_x(m['cx'], cam)) if 'cx' in m else None
        m['door_inside_share'] = None
        if 'cx' in m:
            colsum = dog_a.sum(0)
            m['inside_share'] = float(colsum[:int(cam['door_px'])].sum() / colsum.sum())
        m['beam_at_dog'] = float((world.beam * dog_a).sum() / max(dog_a.sum(), 1))
        return img, m


def main():
    plan = json.load(open(os.path.join(CACHE, 'perform.json')))
    a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, N_SCENE)
    R = Renderer()
    meas = {}
    mpath = os.path.join(CACHE, 'measure_%04d_%04d.json' % (a, b))
    t0 = time.time()
    # warm the solvers from the start of a view run when starting mid-film
    for i in range(a, b):
        img, m = R.frame(plan[i])
        img.save(os.path.join(FR, 'f%04d.jpg' % i), quality=92)
        meas[str(i)] = m
        if i % 48 == 0:
            print(i, '%.2fs/frame' % ((time.time() - t0) / (i - a + 1)), m.get('inverted'), flush=True)
    json.dump(meas, open(mpath, 'w'))


if __name__ == '__main__':
    main()
