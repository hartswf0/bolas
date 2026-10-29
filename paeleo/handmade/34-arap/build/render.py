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
        for n in ('P_body', 'P_head', 'P_lie', 'L_head', 'R0_body', 'R0_head', 'F0_body', 'F0_head', 'Q_stand', 'Q_sit', 'Q_arm'):
            self.tex[n] = Tex(os.path.join(DRAW, n + '.png'), scale=0.7)
        self.worlds = {k: World(v) for k, v in CAMS.items()}
        self.font = ImageFont.truetype(FONT_I, 30)
        self.prevX = {}
        self.used = {}

    def expand(self, f):
        """The frame's layers, with the profile split further into stand/lie bodies and P/L heads where they blend."""
        a = f['acts']; out = []
        for L in f['layers']:
            if L['view'] != 'P':
                out.append((L['view'], L['mirror'], L['extra'], {}, L['w']))
                continue
            # hard swaps (no dissolve): the lying mesh from lie >= 0.55, the head turned in from look >= 0.45
            body = 'lie' if a['lie'] >= 0.55 else 'stand'
            hv = 'L' if a['look'] >= 0.45 else 'P'
            out.append(('P', L['mirror'], L['extra'], dict(body=body, head_view=hv), L['w']))
        tot = sum(o[-1] for o in out)
        return [(o[0], o[1], o[2], o[3], o[4] / tot) for o in out]

    def dog_layer(self, f, view, mirror, ex, sub):
        a = f['acts']
        i = f['i']
        key = view + ('_' + sub.get('body', '') if view == 'P' else '')
        first = self.used.get(key, -9) != i - 1 and self.used.get(key, -9) != i
        self.used[key] = i
        iters = 40 if first else 8
        withers = None
        if view == 'P':
            d = self.dog
            aa = dict(a)
            if sub['body'] == 'stand':
                aa['lie'] = min(a['lie'], 0.5)      # the standing mesh never starts the fold: deep crouch only
            pose = pose_P(d, aa, paws={L: f['paws'][L] for L in LEGS}, lifts=f['lifts'])
            if sub['body'] == 'lie':
                pose['body'] = 'lie'
                pose = dict(pose); pose.update({k: v for k, v in pose_P(d, a).items() if k in ('settle', 'neck_a_lie', 'head_a_lie', 'tail_a_lie', 'neck_len', 'ear')})
                pose['breath'] = a['breath'] * 0.6
            if sub.get('head_view') == 'L':
                pose['head_view'] = 'L'; pose['L_a'] = -0.42
            if ex.get('head_flip'):
                pose['head_flip'] = True
                pose['head_flip_abs'] = -0.12      # muzzle level, a little down: at or below its back line
            if first and sub['body'] == 'stand':
                d.solver.X = d.body.V.copy()
            X, Xh = d.solve(pose, iters=iters)
            body, head = d.cur_body, d.cur_head
            items = [(X, body, body.name), (Xh, head, head.name)]
            nose, joint = d.cur_head_nose, d.cur_head_joint
            solver = d.lsolver if sub['body'] == 'lie' else d.solver
            inv = solver.inverted(X) + {'P_head': (d.hsolver_m if pose.get('head_flip') else d.hsolver), 'L_head': d.lhsolver}[head.name].inverted(Xh)
            energy = solver.energy(X)
            withers = X[(d.K if sub['body'] == 'lie' else d.H)['shoulder']].mean(0)
        else:
            v = self.views[view]
            aa = dict(a); aa.update(ex)
            if view == 'F0':
                aa['crouch'] = a['crouch'] + 0.4 * a['lie']
                aa['ear'] = max(a['ear'], 0.8)
                aa['lie'] = 0.0
            else:
                aa['ear'] = a['ear']; aa['lie'] = 0.0
            X, Xh = v.solve(aa, iters=iters, X0=None if not first else v.body.V.copy())
            if view == 'R0':
                items = [(Xh, v.head, 'R0_head'), (X, v.body, 'R0_body')]
                nose = None; joint = Xh.mean(0)
            else:
                items = [(X, v.body, 'F0_body'), (Xh, v.head, 'F0_head')]
                nose = Xh[v.G['nose']].mean(0); joint = Xh[v.G['skull']].mean(0)
            inv = v.solver.inverted(X) + v.hsolver.inverted(Xh)
            energy = v.solver.energy(X)
        return items, nose, joint, inv, energy, withers

    def frame(self, f):
        t = f['t']
        cam = cam_for(t)
        world = self.worlds['A' if t < CUT_T else 'B']
        s = cam['s'] / 1000.0
        # ---- dog: one or more layers (a view change overlaps two drawings for two frames)
        cx, fy = world_to_px(f['x'], 0.0, cam)
        layers = self.expand(f)
        dog_pm = np.zeros((H, W, 4), np.float32)
        inv = 0; prim = None
        for view, mirror, ex, sub, w in layers:
            items, nose_l, joint_l, inv_l, energy_l, withers_l = self.dog_layer(f, view, mirror, ex, sub)
            sign = -1.0 if mirror else 1.0
            fs = ex.get('fs', 1.0)

            def to_screen(X, sign=sign, fs=fs):
                return np.stack([cx + sign * fs * s * X[:, 0], fy - s * X[:, 1]], 1)
            dog_items = [(to_screen(X), piece.T, piece.uv, self.tex[tname], piece.layer, mirror) for X, piece, tname in items]
            pm, _ = draw_pieces((W, H), dog_items, ss=3, wire=None)
            dog_pm += pm * w
            inv += inv_l
            if prim is None or w > prim[0]:
                prim = (w, nose_l, joint_l, energy_l, withers_l, to_screen)
        _, nose, joint, energy, withers, to_screen = prim
        self.withers = withers
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
        per_pm, _ = draw_pieces((W, H), pitems, ss=3, wire=None)
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
