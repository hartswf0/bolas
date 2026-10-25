"""Render the scene: score -> per-frame layer list (render dependencies: node ids + matrices, or recorded synthetic ops)
-> composite -> frames. Writes lineage/render_deps.jsonl.gz, build/cache/frames/*.png (lossless, hashed), the measured
trace (trace.json) and the sound events (build/cache/events.json)."""
import gzip, hashlib, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lineage import Graph, FOLDER, REPO, sha
import compose, dogrig, world as Wd, cast as Cs
from dogrig import K11, ANCHOR, T, R, S, ap

W, H, FPS = 1280, 720, 24
APPM = 125.0                 # archive px per metre (dog clip): nose-to-rump of the archive dog ~ 1 m
SCORE = json.load(open(os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
FONTS = os.path.join(REPO, 'tools/paeleo/fonts/')
CACHE = os.path.join(FOLDER, 'build', 'cache')
TURN_SEQ = [11, 14, 18, 26, 30, 34, 38, 42, 44]
T_BACK = 7.65             # the body follows the head round, through the found frames
OFF_END = 20.0
T_TURN1 = 3.417
T_TURN2 = 7.458
VIEW = {11: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1, 19: 1, 26: 0, 28: 0, 30: 0, 32: 0, 34: 0, 36: 0, 38: 0, 40: -1, 42: -1, 44: -1, 45: -1, 46: -1}


def smooth(a):
    a = min(1, max(0, a)); return a * a * (3 - 2 * a)


def lerp(a, b, u):
    return a + (b - a) * u


def camera(t):
    """(cx, cy, zoom): wide on the porch, then a push toward the threshold during the approach, held at the sill."""
    w = (1.42, 1.30, 1.12)
    c = (0.05, 0.95, 1.80)
    e = (0.00, 0.88, 1.92)
    if t < 14.7:
        return w
    if t < 24.0:
        u = smooth((t - 14.7) / 9.3)
        return tuple(lerp(a, b, u) for a, b in zip(w, c))
    u = smooth((t - 24.0) / 8.0)
    base = tuple(lerp(a, b, u) for a, b in zip(c, e))
    # when it hears 'come in' the dog looks in, and the frame looks in with it: along its line of sight into the lit room
    look = smooth((t - 26.5) / 0.9) * (1 - smooth((t - 28.3) / 1.2))
    return (base[0] - 0.62 * look, base[1] + 0.05 * look, base[2] - 0.12 * look)


def cam_M(t):
    """world metres -> screen px"""
    cx, cy, z = camera(t); s = 160 * z
    return np.array([[s, 0, 640 - cx * s], [0, -s, 360 + cy * s], [0, 0, 1]], float), s


def plate_M(t):
    Mw, s = cam_M(t)
    # plate px -> world: x = px/PPM + XMIN ; y = YMAX - py/PPM
    Mp = np.array([[1 / Wd.PPM, 0, Wd.XMIN], [0, -1 / Wd.PPM, Wd.YMAX], [0, 0, 1]], float)
    return Mw @ Mp


def interp_head(h):
    return float(np.interp(h, [0.0, 0.15, 0.45, 0.9, 1.3], [-90, -82, -72, 0, 6]))


def door_index(t):
    """which found door frame: frame 20 (narrow, ajar) until 6.2 s, then its own swing at its own 12 fps."""
    if t < 6.2:
        return 0
    return min(len(Cs.DOOR_FRAMES) - 1, int((t - 6.2) * 12))


def light(t):
    return door_index(t) / (len(Cs.DOOR_FRAMES) - 1)


def font(fid, size, wght=None):
    f = ImageFont.truetype(FONTS + fid + '.woff2', size)
    if wght:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


SPEECH = [(1.0, 2.3, 'Come here.', 'call'), (3.4, 4.6, 'Come here!', 'call'), (7.4, 9.4, "It's all right.", 'soft'),
          (10.4, 11.6, "It's all right.", 'soft'), (26.4, 27.4, 'Come in.', 'soft')]


class Scene:
    def __init__(self):
        L = json.load(open(os.path.join(FOLDER, 'lineage', 'lineage.json')))
        self.L = L
        self.G = Graph()
        self.G.nodes = L['nodes']
        self.P = L['roots']['dog']; self.plates = L['roots']['plates']; self.C = L['roots']['cast']
        self.turn = {e['f']: e for e in self.C['turn']}
        self.events = []

    # ---------------- the dog ----------------
    def dog(self, i, t, f):
        d = f['dog']; a = d['act']; st = d['state']
        Mw, s = cam_M(t)
        x = d['x']
        k = s / APPM
        root = ap(Mw, (x, 0.0))
        lampk = 0.72 * light(t) * max(0.0, min(1.0, 1 - (x - 0.46) / 4.4)) ** 1.1
        info = {'mode': 'rig', 'view': 1}
        # footage turn windows
        n = len(TURN_SEQ)
        u1 = (t - T_TURN1) * FPS; u2 = (t - T_BACK) * FPS
        seq = None
        if 0 <= u1 < n:
            seq = TURN_SEQ[int(u1)]
        elif 0 <= u2 < n:
            seq = TURN_SEQ[::-1][int(u2)]
        back_turned = (t >= T_TURN1 + n / FPS) and (t < T_BACK)
        if seq is not None:
            e = self.turn[seq]
            j = TURN_SEQ.index(seq) / (n - 1)
            off = lerp(142 - ANCHOR[0], OFF_END, j)      # bbox centre relative to the body anchor: frame 11 -> frame 44
            cx = e['origin'][0] + e['size'][0] / 2
            bottom = e['origin'][1] + e['size'][1] - 5
            M = T(*root) @ S(k, k) @ T(-(cx - off), -bottom) @ T(*e['origin'])
            layers = [{'node': e['dusk'], 'M': M, 'op': 1.0, 'role': 'dog_turn', 'src': 'NJC#%03d' % seq}]
            if lampk > 0.01:
                layers.append({'node': e['lamp'], 'M': M, 'op': lampk, 'role': 'dog_turn_lit'})
            info.update(mode='turn', view=VIEW[seq], frame=seq)
            return layers, info
        # the rig
        pose = {'k': k, 'root': tuple(root), 'facing': -1 if back_turned else 1}
        if back_turned:
            info['view'] = -1
            if t >= T_TURN2:            # 7.46: the head comes round to the door before the body does
                pose['head_flip'] = True
                info['view'] = 1
        pose['crouch'] = min(1.0, a['crouch'] * 1.1)
        pose['head'] = 'up'
        hr = interp_head(a['head'])
        pose['tail_rot'] = (a['tail'] - 0.5) * 52 + math.sin(t * 2 * math.pi * 2.1) * a['wag'] * 28
        lie = a['lie'] if st == 'lie_down' else 0.0
        pose['lie'] = lie
        if lie > 0:
            rest, look = a['rest'], a['look']
            base = lerp(hr, -60, lie)
            hr = lerp(base, -84, rest)
            hr = lerp(hr, -34, look)
            pose['tail_rot'] = lerp(pose['tail_rot'], -28, lie)    # the tail lies out behind on the boards
        if pose.get('head_flip'):
            hr = -22.0
        pose['head_rot'] = hr + math.sin(t * 2 * math.pi * 0.3) * 1.2
        pose['breath'] = math.sin(t * 2 * math.pi * 0.42)
        if a['moving'] > 0.02:
            pose['walk'] = min(1.0, a['moving'] * 1.2)
            pose['s'] = (4.0 - x) * APPM
        L, feet = dogrig.dog_layers(self.P, pose)
        keys = feet.pop('_keys')
        info['keys_px'] = {kk: [round(float(v[0]), 2), round(float(v[1]), 2)] for kk, v in keys.items() if v is not None}
        layers = []
        for pc, v, M, role in L:
            layers.append({'node': self.P[pc]['dusk'], 'M': M, 'op': 1.0, 'role': 'dog_' + role, 'src': 'NJC#018' if pc in ('tail',) else 'NJC#011'})
            if lampk > 0.01:
                layers.append({'node': self.P[pc]['lamp'], 'M': M, 'op': lampk, 'role': 'dog_' + role + '_lit'})
        info.update(feet={kk: [round(float(vv[0]), 2), round(float(vv[1]), 2)] for kk, vv in feet.items()}, pose={kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in pose.items() if kk not in ('root',)})
        return layers, info

    # ---------------- the person ----------------
    def person(self, t, f):
        p = f['person']
        Mw, s = cam_M(t)
        sit = smooth(p['sit']); x = p['x']
        reach = p['reach']; low = p['low']
        voice = p['voice']; mouth = p['mouth']
        hip_y = lerp(0.90, 0.47, sit)
        lean = (4.0 * mouth if voice == 'call' else 0.0) + 7.0 * reach + 30.0 * low * sit
        tor = self.C['torso']; m = tor['m_per_px']
        hip = np.array([x, hip_y])
        # torso piece: full-frame px -> world (y up), rotated about the hip by the lean (forward = toward +x)
        ang = math.radians(lean)
        Rw = np.array([[math.cos(ang), math.sin(ang), 0], [-math.sin(ang), math.cos(ang), 0], [0, 0, 1]])
        Mt_world = T(*hip) @ Rw @ np.array([[m, 0, 0], [0, -m, 0], [0, 0, 1]]) @ T(-tor['hip'][0], -tor['hip'][1]) @ T(*tor['origin'])
        layers = []
        # legs (drawn): standing -> walking back -> sitting on the floor, knees up
        walkph = (x + 0.28) / 0.32 * math.pi
        stepping = 1.0 if (-1.24 < x < -0.29) else 0.0
        shapes = []
        for side, ph in (('far', 0.0), ('near', math.pi)):
            sw = math.sin(walkph + ph) * 0.13 * stepping
            hipx = x + (0.03 if side == 'near' else -0.03)
            knee_st = (hipx + sw * 0.5 + 0.02, 0.48); foot_st = (hipx + sw + 0.03, 0.05 + max(0, math.cos(walkph + ph)) * 0.05 * stepping)
            knee_si = (hipx + 0.42, 0.50 if side == 'near' else 0.48); foot_si = (hipx + 0.48, 0.03)
            knee = (lerp(knee_st[0], knee_si[0], sit), lerp(knee_st[1], knee_si[1], sit))
            foot = (lerp(foot_st[0], foot_si[0], sit), lerp(foot_st[1], foot_si[1], sit))
            hp_ = (hipx, hip_y + 0.02)
            col = [10, 8, 12, 255] if side == 'far' else [16, 12, 16, 255]
            shapes += leg_shapes(Mw, hp_, knee, foot, col)
        layers.append({'synth': 'draw', 'params': {'shapes': shapes}, 'role': 'person_legs'})
        layers.append({'node': tor['node'], 'M': Mw @ Mt_world, 'op': 1.0, 'role': 'person_torso', 'src': 'ST#000'})
        # the arm: drawn upper arm + the found forearm and hand
        g = max(reach, low)
        if g > 0.01:
            sh = ap(Rw, np.array([0.14, 0.54])) + hip
            a1 = lerp(lerp(8, 82, reach), lerp(8, 50, low), low / max(1e-6, reach + low))
            a2 = lerp(lerp(78, -6, reach), lerp(84, 48, low), low / max(1e-6, reach + low))
            el = sh + 0.30 * np.array([math.sin(math.radians(a1)), -math.cos(math.radians(a1))])
            shapes = [{'t': 'line', 'pts': [list(map(float, ap(Mw, sh))), list(map(float, ap(Mw, el)))], 'outline': [16, 12, 16, 255], 'w': 0.11 * s}]
            arm = self.C['arm']; ma = arm['m_per_px']
            Ma = T(*el) @ np.array([[math.cos(math.radians(-a2)), -math.sin(math.radians(-a2)), 0], [math.sin(math.radians(-a2)), math.cos(math.radians(-a2)), 0], [0, 0, 1]]) @ np.array([[ma, 0, 0], [0, -ma, 0], [0, 0, 1]]) @ T(-arm['elbow'][0], -arm['elbow'][1])
            op = min(1.0, g * 3)
            layers.append({'synth': 'draw', 'params': {'shapes': shapes, 'opacity': op}, 'role': 'person_upperarm'})
            layers.append({'node': arm['node'], 'M': Mw @ Ma, 'op': op, 'role': 'person_hand', 'src': 'DtH#001'})
        head = ap(Mw, ap(Rw, np.array([0.0, 0.78])) + hip)
        return layers, {'head_px': [float(head[0]), float(head[1])], 'hip': [x, hip_y]}

    # ---------------- the frame ----------------
    def frame_layers(self, i):
        t = i / FPS; f = FR[i]
        Mp = plate_M(t)
        Mw, s = cam_M(t)
        Lf = light(t)
        layers = [{'node': self.plates['dusk'], 'M': Mp, 'op': 1.0, 'role': 'plate'}]
        if Lf > 0:
            layers.append({'node': self.plates['lit'], 'M': Mp, 'op': Lf, 'role': 'plate_lit'})
        # lamp and its glow
        lamp = self.C['lamp']; lw, lh = lamp['size']
        lm = 0.34 / lh
        Ml = Mw @ T(Wd.LAMP[0], Wd.LAMP[1] + 0.20) @ np.array([[lm, 0, 0], [0, -lm, 0], [0, 0, 1]]) @ T(-lw / 2, 0)
        layers.append({'node': lamp['dusk'], 'M': Ml, 'op': 1.0, 'role': 'lamp', 'src': 'MSHA#020'})
        layers.append({'node': lamp['lit'], 'M': Ml, 'op': 0.35 + 0.65 * Lf, 'role': 'lamp_lit'})
        gm = (1.6 + 1.0 * Lf) / 400
        layers.append({'node': self.C['glow'], 'M': Mw @ T(Wd.LAMP[0], Wd.LAMP[1]) @ np.array([[gm, 0, 0], [0, -gm, 0], [0, 0, 1]]) @ T(-200, -200), 'op': 0.45 + 0.55 * Lf, 'role': 'glow'})
        # door: the found door's swing
        di = door_index(t); dd = self.C['door'][di]
        dw, dh = dd['size']; md = 2.04 / dh
        Md = Mw @ T(Wd.WALL_IN, 0) @ np.array([[md, 0, 0], [0, -md, 0], [0, 0, 1]]) @ T(-dw, -dh)
        layers.append({'node': dd['dusk'], 'M': Md, 'op': 1.0, 'role': 'door', 'src': 'ST#%03d' % dd['f']})
        layers.append({'node': dd['lit'], 'M': Md, 'op': 0.25 + 0.75 * Lf, 'role': 'door_lit'})
        # person
        pl, pinfo = self.person(t, f)
        layers += pl
        # the light that comes out: through the doorway, then onto the porch
        cw, ch = int(0.92 * Wd.PPM), int(Wd.LINTEL * Wd.PPM)
        Mc = Mw @ T(Wd.WALL_IN + 0.03, Wd.LINTEL) @ np.array([[0.86 / cw, 0, 0], [0, -Wd.LINTEL / ch, 0], [0, 0, 1]])
        layers.append({'node': self.C['channel'], 'M': Mc, 'op': 0.10 + 0.78 * Lf, 'role': 'channel'})
        if Lf > 0:
            layers.append({'node': self.C['beam'], 'M': Mp, 'op': Lf, 'role': 'beam'})
        else:
            layers.append({'node': self.C['beam'], 'M': Mp, 'op': 0.10, 'role': 'beam_ajar'})
        # dog
        dl, dinfo = self.dog(i, t, f)
        layers += dl
        # speech, set where it is said
        for t0, t1, text, kind in SPEECH:
            if t0 <= t < t1 + 0.35:
                fade = min(1.0, (t - t0) / 0.12, (t1 + 0.35 - t) / 0.35)
                hp = pinfo['head_px']
                call = kind == 'call'
                layers.append({'synth': 'text', 'params': {'text': text, 'x': hp[0] + (0.30 if call else -0.10) * s, 'y': hp[1] - (0.30 if call else 0.32) * s,
                                                           'anchor': 'ls' if call else 'rs', 'size': int(30 if call else 23),
                                                           'font': 'f27', 'color': [242, 228, 206] if kind == 'call' else [214, 196, 176], 'alpha': fade * (1.0 if kind == 'call' else 0.8)}, 'role': 'speech'})
        # the lineage rail: where this frame's pieces came from
        srcs = []
        for l in layers:
            if l.get('src') and l['src'] not in srcs:
                srcs.append(l['src'])
        layers.append({'synth': 'rail', 'params': {'i': i, 'srcs': srcs}, 'role': 'rail'})
        return layers, dinfo, pinfo


def leg_shapes(Mw, hip, knee, foot, col):
    pts = []
    def capsule(a, b, wa, wb):
        a = np.array(a, float); b = np.array(b, float)
        d = b - a; n = np.array([-d[1], d[0]]) / (np.hypot(*d) + 1e-9)
        q = [a + n * wa, b + n * wb, b - n * wb, a - n * wa]
        return {'t': 'poly', 'pts': [list(map(float, ap(Mw, p))) for p in q], 'fill': col}
    sh = [capsule(hip, knee, 0.075, 0.055), capsule(knee, foot, 0.055, 0.04)]
    toe = (foot[0] + 0.13, foot[1] - 0.01)
    sh.append(capsule((foot[0] - 0.02, foot[1] + 0.02), toe, 0.035, 0.025))
    return sh


_fcache = {}
_pcache = {}
BIG = ('plate', 'plate_lit', 'beam', 'beam_ajar')


def get_font(fid, size):
    k = (fid, size)
    if k not in _fcache:
        _fcache[k] = font(fid, size)
    return _fcache[k]


def compose_frame(G, layers, want_alpha=False):
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    dog_alpha = Image.new('L', (W, H), 0) if want_alpha else None
    parts = {}
    for l in layers:
        if 'node' in l and l['role'] in BIG:
            key = (l['node'], tuple(np.round(np.array(l['M'], float).ravel(), 4)))
            if key not in _pcache:
                lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                compose.place(lay, G.get(l['node']), np.array(l['M'], float), 1.0, None, Image.BILINEAR)
                if len(_pcache) > 6:
                    _pcache.clear()
                _pcache[key] = lay
            lay = _pcache[key]
            if l['op'] < 0.999:
                lay = lay.copy(); lay.putalpha(lay.getchannel('A').point(lambda v, o=l['op']: int(v * o)))
            canvas.alpha_composite(lay)
        elif 'node' in l:
            role = l['role']
            ao = None
            if want_alpha and role.startswith('dog_') and not role.endswith('_lit'):
                ao = Image.new('L', (W, H), 0) if role in ('dog_body', 'dog_head', 'dog_turn') else dog_alpha
            compose.place(canvas, G.get(l['node']), np.array(l['M'], float), l['op'], ao)
            if ao is not None and ao is not dog_alpha:
                dog_alpha.paste(255, (0, 0), ao)
                parts[role] = ao
        elif l['synth'] == 'draw':
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            for sh in l['params']['shapes']:
                if sh['t'] == 'poly':
                    d.polygon([tuple(p) for p in sh['pts']], fill=tuple(sh['fill']))
                elif sh['t'] == 'line':
                    d.line([tuple(p) for p in sh['pts']], fill=tuple(sh['outline']), width=max(1, int(sh['w'])), joint='curve')
            op = l['params'].get('opacity', 1.0)
            if op < 1:
                lay.putalpha(lay.getchannel('A').point(lambda v: int(v * op)))
            canvas.alpha_composite(lay)
        elif l['synth'] == 'text':
            p = l['params']
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            fo = get_font(p['font'], p['size']); an = p.get('anchor', 'ls')
            d.text((p['x'] + 1.5, p['y'] + 1.5), p['text'], font=fo, fill=(8, 6, 10, int(170 * p['alpha'])), anchor=an)
            d.text((p['x'], p['y']), p['text'], font=fo, fill=tuple(p['color']) + (int(255 * p['alpha']),), anchor=an)
            canvas.alpha_composite(lay)
        elif l['synth'] == 'rail':
            p = l['params']
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            txt = 'f%03d  ' % p['i'] + '  '.join(p['srcs'])
            d.text((22, H - 18), txt, font=get_font('f14', 12), fill=(200, 190, 210, 96), anchor='ls')
            canvas.alpha_composite(lay)
    return canvas.convert('RGB'), dog_alpha, parts


def jsonable(layers):
    def clean(v):
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [clean(x) for x in v]
        if isinstance(v, (float, np.floating)):
            return round(float(v), 4)
        if isinstance(v, np.integer):
            return int(v)
        return v
    out = []
    for l in layers:
        l2 = clean(dict((k, v) for k, v in l.items() if k != 'M'))
        if 'M' in l:
            l2['M'] = [[round(float(v), 5) for v in row] for row in np.array(l['M'])[:2]] + [[0.0, 0.0, 1.0]]
        out.append(l2)
    return out


def measure(dinfo, dog_alpha, parts, t):
    a = np.asarray(dog_alpha, float) / 255
    ys, xs = np.nonzero(a > 0.5)
    if len(xs) == 0:
        return {}
    Mw, s = cam_M(t)
    Mi = np.linalg.inv(Mw)
    cx, cy = float(xs.mean()), float(ys.mean())
    body = parts.get('dog_body') or parts.get('dog_turn')
    b = np.asarray(body, float) / 255 if body is not None else a
    by, bx = np.nonzero(b > 0.5)
    bcx = float(bx.mean())
    wx = ap(Mi, (bcx, float(by.max())))[0]
    out = {'x_screen': round(cx, 2), 'y_screen': round(cy, 2), 'bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
           'x_world_measured': round(float(ap(Mi, (bcx, 0))[0]), 4),
           'front_world': round(float(ap(Mi, (xs.min(), 0))[0]), 4), 'rear_world': round(float(ap(Mi, (xs.max(), 0))[0]), 4),
           'top_world': round(float(ap(Mi, (0, ys.min()))[1]), 4)}
    hd = parts.get('dog_head')
    if hd is not None:
        h = np.asarray(hd, float) / 255
        hy, hx = np.nonzero(h > 0.5)
        if len(hx):
            out['head_world'] = [round(float(v), 4) for v in ap(Mi, (hx.mean(), hy.mean()))]
            out['head_low_world'] = round(float(ap(Mi, (0, hy.min()))[1]), 4)      # top of the head, metres
            # the back line: top of the body piece at the withers
            out['back_world'] = round(float(ap(Mi, (0, by.min()))[1]), 4)
            out['facing_measured'] = 1 if hx.mean() < bcx else -1
            kp = dinfo.get('keys_px', {})
            if 'nose' in kp and 'withers' in kp:
                # the skull: rendered head pixels within 0.22 m of the (transformed) nose key; its top against the withers
                r = 0.22 * s
                near = (hx - kp['nose'][0]) ** 2 + (hy - kp['nose'][1]) ** 2 < r * r
                if near.any():
                    out['skull_top_world'] = round(float(ap(Mi, (0, hy[near].min()))[1]), 4)
                out['nose_world'] = [round(float(v), 4) for v in ap(Mi, kp['nose'])]
                out['withers_world'] = round(float(ap(Mi, kp['withers'])[1]), 4)
                out['rump_world'] = round(float(ap(Mi, kp['rump'])[1]), 4)
    return out


_SC = None


def render_one(i):
    global _SC
    if _SC is None:
        _SC = Scene()
    sc = _SC
    t = i / FPS
    layers, dinfo, pinfo = sc.frame_layers(i)
    layers = jsonable(layers)          # the frame is composed from exactly what render_deps records
    img, dog_alpha, parts = compose_frame(sc.G, layers, want_alpha=True)
    img.save(os.path.join(CACHE, 'frames', 'scene_%04d.png' % i), compress_level=1)
    h = sha(img.tobytes())
    m = measure(dinfo, dog_alpha, parts, t)
    f = FR[i]
    st = f['dog']['state']
    if dinfo['mode'] == 'turn':
        facing = dinfo['view']
        posture = 'turning (found frame %03d)' % dinfo['frame']
    else:
        facing = m.get('facing_measured', 1)
        ps = dinfo['pose']
        if ps.get('facing') == -1:
            facing = 1 if ps.get('head_flip') else -1
            posture = 'back turned, looking round at the door' if ps.get('head_flip') else 'standing, back turned, head low'
        elif ps.get('lie', 0) > 0.6:
            a = f['dog']['act']
            posture = 'lying' + (', looking in' if a['look'] > 0.5 else (', chin down' if a['rest'] > 0.5 else ''))
        elif ps.get('lie', 0) > 0.05:
            posture = 'lying down'
        elif ps.get('walk', 0) > 0.3:
            posture = 'backing away, low' if f['dog']['v'] > 0 else 'walking, head low'
        else:
            posture = 'standing, watching'
    tr = {'i': i, 't': round(t, 4), 'state': st, 'x_score': f['dog']['x'], 'x_screen': m.get('x_screen'), 'y_screen': m.get('y_screen'),
          'x_world_measured': m.get('x_world_measured'), 'facing': facing, 'posture': posture, 'mode': dinfo['mode'],
          'measured': {k: v for k, v in m.items() if k not in ('x_screen', 'y_screen', 'x_world_measured')},
          'feet_px': dinfo.get('feet')}
    return {'i': i, 'sha256_rgb': h, 'layers': layers}, tr


def main(only=None, procs=4):
    os.makedirs(os.path.join(CACHE, 'frames'), exist_ok=True)
    rng = list(range(len(FR))) if only is None else only
    if procs > 1 and len(rng) > 8:
        import multiprocessing as mp
        with mp.Pool(procs) as pool:
            res = pool.map(render_one, rng, chunksize=8)
    else:
        res = [render_one(i) for i in rng]
    deps = [r[0] for r in res]; trace = [r[1] for r in res]
    if only is None:
        with gzip.open(os.path.join(FOLDER, 'lineage', 'render_deps.jsonl.gz'), 'wt') as fz:
            for d in deps:
                fz.write(json.dumps(d) + '\n')
        json.dump({'about': 'SCION 54 dog trace, measured from the rendered dog matte of every scene frame (x_world_measured: the body piece centre '
                            'at the floor, metres, through the inverse camera). x_score is the score position the render was asked to put the dog at. '
                            'state is the score state the choreography performed; facing: 1 toward the door, -1 back turned, 0 end-on (found frontal frame).',
                   'frames': trace}, open(os.path.join(FOLDER, 'trace.json'), 'w'), indent=0)
    return trace


if __name__ == '__main__':
    if len(sys.argv) > 1:
        only = [int(v) for v in sys.argv[1].split(',')]
        tr = main(only)
        for f in tr:
            print(f['i'], f['posture'], f['x_world_measured'], f['facing'])
    else:
        main()
