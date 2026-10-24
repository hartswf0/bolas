"""SCION 08 · Sutherland — the solve pass.

Reads the PAELEO score, builds the drawing (porch, door frame, door leaf, person, dog) as
constraint graphs, performs the prompts as light-pen manipulations, solves every frame
with the relaxation solver (warm-started from the previous frame: no teleporting), and
writes a display file per frame (screen-space strokes) plus solver traces and sound events.

World: metres. x along the porch (threshold 0, inside negative, steps at 4.9), y up,
z toward the viewer (0 = wall face).  Camera: orthographic, 14 degrees of elevation.
"""
import json, math, os, pickle, sys
import numpy as np
from solver import Graph
from font import text_strokes, text_width

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SCORE = os.path.join(ROOT, 'paeleo', 'handmade', 'score', 'threshold-score.json')
RIG = os.path.join(ROOT, 'paeleo', 'handmade', 'kit', 'archive-dog', 'pose_agent_v8.json')
CACHE = os.path.join(HERE, '_cache')
FPS = 24
TITLE_N = 72
END_N = 72
W, H = 1280, 720
ELEV = math.radians(24)
KX = 0.45          # oblique: nearer points sit to the right, so depth reads as a diagonal
CE, SE = math.cos(ELEV), math.sin(ELEV)
UP = np.array([0.0, 1.0, 0.0])

score = json.load(open(SCORE))
SF = score['frames']
N_SCENE = len(SF)

def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))

def lerp(a, b, t):
    return a + (b - a) * t

def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)

def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v

# ----------------------------------------------------------------------------
# Proportions measured from the archive dog's rig keys (median over 25 keys)
# ----------------------------------------------------------------------------
def rig_ratios():
    d = json.load(open(RIG))
    R = {k: [] for k in ['nose_neck', 'neck_chest', 'chest_tail', 'fore_h', 'hind_h', 'neck_h']}
    for v in d.values():
        P = {n: np.array(v[n], float) for n in ['nose', 'neck', 'chest', 'tail', 'f1', 'f2', 'h1', 'h2']}
        L = lambda a, b: float(np.linalg.norm(P[a] - P[b]))
        fy = (P['f1'][1] + P['f2'][1]) / 2; hy = (P['h1'][1] + P['h2'][1]) / 2
        R['nose_neck'].append(L('nose', 'neck')); R['neck_chest'].append(L('neck', 'chest'))
        R['chest_tail'].append(L('chest', 'tail')); R['fore_h'].append(fy - P['chest'][1])
        R['hind_h'].append(hy - P['tail'][1]); R['neck_h'].append(fy - P['neck'][1])
    med = {k: float(np.median(v)) for k, v in R.items()}
    base = med['chest_tail']
    return {k: v / base for k, v in med.items()}, len(d)

RATIOS, N_KEYS = rig_ratios()
TORSO = 0.62                         # metres, chest -> tail root (declared scale)
DOG = {
    'spine': TORSO * 0.97 / 2,       # W-M and M-P
    'neck': TORSO * RATIOS['neck_chest'] * 0.95,   # withers -> poll
    'head': TORSO * RATIOS['nose_neck'] * 0.82,    # poll -> nose (rig "neck" key sits low on the neck)
    'withers_h': TORSO * RATIOS['neck_h'],         # standing withers height
    'croup_h': TORSO * RATIOS['hind_h'],
    'fore': [0.15, 0.19, 0.075],
    'hind': [0.19, 0.21, 0.15],
    'tail': 0.14,
    'lat_f': 0.065, 'lat_h': 0.07,
}
LANE = 0.18          # dog walks this far out from the wall face: over the sill's depth
SILL = dict(x0=-0.56, x1=0.56, z0=-0.12, z1=0.24, h=0.04)
DOOR = dict(x0=-0.46, x1=0.46, top=2.05)
LEAF_W = DOOR['x1'] - DOOR['x0']

def floor_y(x, z):
    if SILL['x0'] <= x <= SILL['x1'] and z <= SILL['z1'] + 0.02:
        return SILL['h']
    if x > 4.9:
        return -0.18 if x < 5.22 else (-0.36 if x < 5.54 else -0.54)
    return 0.0

# ----------------------------------------------------------------------------
# Camera (Sketchpad's scale knob): orthographic + elevation, then 2-D window
# ----------------------------------------------------------------------------
class Cam:
    def __init__(self, S=150.0, xc=1.45, yc=0.0, px=640.0, py=415.0):
        self.S, self.xc, self.yc, self.px, self.py = S, xc, yc, px, py
    def p(self, v):
        x, y, z = v
        sy = y * CE - z * SE
        return (self.px + self.S * (x + KX * z - self.xc), self.py - self.S * (sy - self.yc))
    def pa(self, A):
        A = np.asarray(A, float)
        sy = A[:, 1] * CE - A[:, 2] * SE
        return np.stack([self.px + self.S * (A[:, 0] + KX * A[:, 2] - self.xc), self.py - self.S * (sy - self.yc)], 1)

CAM0 = Cam()
CAM1 = Cam(S=200.0, xc=-0.15, yc=0.80, px=640.0, py=292.0)

def cam_at(t):
    """Wide until the dog has lain down, then the scale knob turns in (24.6 s -> 26.2 s)."""
    k = smooth((t - 24.6) / 1.6)
    return Cam(lerp(CAM0.S, CAM1.S, k), lerp(CAM0.xc, CAM1.xc, k), lerp(CAM0.yc, CAM1.yc, k),
               640.0, lerp(CAM0.py, CAM1.py, k))

# ----------------------------------------------------------------------------
# Display file
# ----------------------------------------------------------------------------
class DF:
    """A display file: ordered strokes in screen pixels. kinds: line (polyline), dot."""
    def __init__(self):
        self.items = []
        self.occ = []      # screen polygons that hide strokes drawn behind them
    def line(self, pts, I=1.0, tag='world', dash=None, closed=False):
        pts = [tuple(map(float, p)) for p in pts]
        if closed:
            pts = pts + [pts[0]]
        if len(pts) >= 2:
            self.items.append(('line', np.array(pts, np.float32), float(I), tag, dash))
    def dot(self, p, I=1.0, tag='world', r=0):
        self.items.append(('dot', np.array([p], np.float32), float(I), tag, r))
    def text(self, s, x, y, size=12, I=0.8, tag='text', track=1.5):
        strokes, _ = text_strokes(s, x, y, size, track)
        for pl in strokes:
            if len(pl) == 2 and abs(pl[0][0] - pl[1][0]) + abs(pl[0][1] - pl[1][1]) < size * 0.12:
                self.dot(pl[0], I * 1.4, tag)
            else:
                self.line(pl, I, tag)

def arc_pts(c, r, a0, a1, n=None):
    n = n or max(6, int(abs(a1 - a0) * r / 3) + 2)
    a = np.linspace(a0, a1, n)
    return np.stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)], 1)

def capsule(df, A, B, ra, rb, I, tag, ends=(True, True)):
    """Outline of a tapered limb between screen points A, B with radii ra, rb (px)."""
    A = np.asarray(A, float); B = np.asarray(B, float)
    d = B - A; L = np.linalg.norm(d)
    if L < 1e-6:
        df.line(arc_pts(A, ra, 0, 2 * math.pi), I, tag); return
    u = d / L; n = np.array([-u[1], u[0]])
    df.line([A + n * ra, B + n * rb], I, tag)
    df.line([A - n * ra, B - n * rb], I, tag)
    ang = math.atan2(n[1], n[0])
    if ends[1]:
        df.line(arc_pts(B, rb, ang, ang - math.pi), I, tag)
    if ends[0]:
        df.line(arc_pts(A, ra, ang, ang + math.pi), I, tag)

def catmull(pts, n=6, closed=False):
    P = [np.asarray(p, float) for p in pts]
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
    else:
        P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return np.array(out)

# ----------------------------------------------------------------------------
# Sutherland-Hodgman polygon clipping (Sutherland & Hodgman, 1974)
# ----------------------------------------------------------------------------
def clip_poly(poly, a, b):
    """Keep the part of poly on the left of directed line a->b."""
    def inside(p):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0
    def inter(p, q):
        x1, y1 = p; x2, y2 = q; x3, y3 = a; x4, y4 = b
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-12:
            return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    out = []
    for i in range(len(poly)):
        cur, prev = poly[i], poly[i - 1]
        if inside(cur):
            if not inside(prev):
                out.append(inter(prev, cur))
            out.append(cur)
        elif inside(prev):
            out.append(inter(prev, cur))
    return out

def hatch(poly, spacing, axis=0):
    """Scan lines (y = const in poly coords) across a convex polygon -> list of segments."""
    if len(poly) < 3:
        return []
    ys = [p[1] for p in poly]
    segs = []
    y = math.ceil(min(ys) / spacing) * spacing
    while y <= max(ys):
        xs = []
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i - 1], poly[i]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        if len(xs) >= 2:
            segs.append(((min(xs), y), (max(xs), y)))
        y += spacing
    return segs

# ----------------------------------------------------------------------------
# The dog: a constraint graph
# ----------------------------------------------------------------------------
LEGS = [('LH', 'h', -1, 0.00), ('LF', 'f', -1, 0.25), ('RH', 'h', 1, 0.50), ('RF', 'f', 1, 0.75)]

def build_dog(x0):
    g = Graph('dog')
    g.side = np.array([0, 0, -1.0])
    hw, hc = DOG['withers_h'], DOG['croup_h']
    f = np.array([-1.0, 0, 0])
    C = np.array([x0, 0, LANE])
    g.point('W', C + f * DOG['spine'] + UP * hw)
    g.point('M', C + UP * (hw + hc) / 2)
    g.point('P', C - f * DOG['spine'] + UP * hc)
    g.point('N', g.p('W') + f * 0.12 + UP * 0.2)
    g.point('Z', g.p('N') + f * 0.2 - UP * 0.1)
    g.point('T1', g.p('P') - f * 0.12 + UP * 0.03)
    g.point('T2', g.p('T1') - f * 0.12)
    g.point('T3', g.p('T2') - f * 0.12 - UP * 0.04)
    g.dist('W', 'M', DOG['spine']); g.dist('M', 'P', DOG['spine'])
    g.dist('W', 'N', DOG['neck']); g.dist('N', 'Z', DOG['head'])
    g.dist('P', 'T1', DOG['tail']); g.dist('T1', 'T2', DOG['tail']); g.dist('T2', 'T3', DOG['tail'])
    for name, kind, lr, _ in LEGS:
        lat = (DOG['lat_f'] if kind == 'f' else DOG['lat_h']) * lr
        root = 'W' if kind == 'f' else 'P'
        base = g.p(root) - UP * (0.14 if kind == 'f' else 0.07) + np.array([0, 0, -lat])
        L = DOG['fore'] if kind == 'f' else DOG['hind']
        n0 = name + '0'
        g.point(n0, base)
        g.point(name + '1', base - UP * L[0] + f * (-0.03 if kind == 'f' else 0.04))
        g.point(name + '2', g.p(name + '1') - UP * L[1])
        g.point(name + '3', np.array([g.p(name + '2')[0], 0.03, g.p(name + '2')[2]]))
        g.dist(n0, name + '1', L[0]); g.dist(name + '1', name + '2', L[1]); g.dist(name + '2', name + '3', L[2])
        def mk(root=root, kind=kind, lat=lat):
            def fn(G):
                Wp, Pp = G.P[G.idx['W']], G.P[G.idx['P']]
                a = unit(Wp - Pp); s = G.side; ub = np.cross(s, a)
                if kind == 'f':
                    return Wp + a * 0.03 - ub * 0.14 + s * lat
                return Pp + a * 0.05 - ub * 0.07 + s * lat
            return fn
        fn = mk()
        g.P[g.idx[n0]] = fn(g)
        g.rigid(n0, [root, 'M'])
        g.attach_pt(n0, fn, 0.5)
        if kind == 'f':
            g.bend(n0, name + '1', name + '2', -1, 0.015)      # elbow points back
            g.bend(name + '1', name + '2', name + '3', 1, 0.002)  # carpus never buckles backwards
        else:
            g.bend(n0, name + '1', name + '2', 1, 0.02)       # stifle points forward
            g.bend(name + '1', name + '2', name + '3', -1, 0.02)  # hock points back
        g.floor(name + '3', 0.03)
        g.floor(name + '1', 0.03); g.floor(name + '2', 0.03)
    g.floor('Z', 0.025); g.floor('N', 0.05); g.floor('T3', 0.02); g.floor('T2', 0.02)
    g.dist('LF0', 'RF0'); g.dist('LH0', 'RH0')
    # the threshold as a constraint: inside the door frame no part of the dog passes the door plane
    for n in g.names:
        g.wall(n, SILL['x0'], SILL['x1'], 0.0)
    g.vmax = 0.09
    return g

def set_floor(g, name, y0):
    i = g.idx[name]
    for k, (kind, prm) in enumerate(g.hard):
        if kind == 'floor' and prm[0] == i:
            g.hard[k] = ('floor', (i, y0))

class DogDriver:
    """Turns the score's acting intentions into requests on the dog's constraint graph."""
    STRIDE = 0.55          # metres per gait cycle (= the score's walk_phase: 11.4 rad/m)
    DUTY = 0.62

    def __init__(self):
        f0 = SF[0]['dog']
        self.g = build_dog(f0['x'])
        self.travel = 0.0
        self.prev_x = f0['x']
        self.prev_turn = f0['act']['turn']
        self.turn_used = None
        self.feet = {}
        for name, kind, lr, off in LEGS:
            p = self.g.p(name + '3').copy(); p[1] = 0.03
            self.feet[name] = {'pin': p, 'stance': True, 'lift': p.copy()}
        self.events = []
        self.lying_prev = False
        # pre-relax so frame 0 is already a solved drawing
        for _ in range(4):
            self.step(0, record=False)

    def yaw_vectors(self, turn):
        fx = -turn
        fz = -math.sqrt(max(0.0, 1 - turn * turn))      # turns through the wall side: we see its back
        f = unit(np.array([fx, 0.0, fz]))
        side = np.cross(f, UP)
        return f, side

    def step(self, i, record=True):
        fr = SF[i]; d = fr['dog']; a = d['act']; t = fr['t']
        g = self.g
        g.clear_frame()
        turn = a['turn']
        if d['state'] == 'refuse' and t < 5.0:
            turn = min(turn, 1 - 2 * smooth((t - 3.47) / 0.8))     # the back turns from the moment of choosing
        if 7.458 <= t < 9.5:
            turn = max(turn, -1 + 2 * smooth((t - 7.62) / 0.7))      # rises, then the body comes round
        # yaw is a parameter of the graph: the body rotates in depth (z), never a mirror flip.
        # refusing turns through the wall side (we see its back); coming round turns through
        # the camera side (we see its face).
        phi_b = (math.pi - math.acos(clamp(turn, -1, 1))) if t < 7.458 else (math.acos(clamp(turn, -1, 1)) - math.pi)
        f = np.array([math.cos(phi_b), 0.0, math.sin(phi_b)])
        side = np.cross(f, UP)
        # the head leads the body: it turns first at the moment of choosing, up to 130 deg off the body
        if 3.417 <= t < 7.458:
            goal, tc = 0.0, 3.417
        elif 7.458 <= t < 9.5:
            goal, tc = -math.pi, 7.458
        else:
            goal, tc = phi_b, t
        dphi = clamp(goal - phi_b, -2.27, 2.27) * smooth((t - tc) / 0.35)
        phi_h = phi_b + dphi
        self.phi = (phi_b, phi_h)
        fhead = np.array([math.cos(phi_h), 0.0, math.sin(phi_h)])
        g.side = side
        x = d['x']
        dx = x - self.prev_x
        dyaw = abs(math.acos(clamp(turn, -1, 1)) - math.acos(clamp(self.prev_turn, -1, 1)))
        lie = a['lie']; crouch = a['crouch']
        if lie < 0.03:
            self.travel += abs(dx) + 0.32 * dyaw
        self.prev_x, self.prev_turn = x, turn
        C = np.array([x, 0.0, LANE])
        # --- torso requests -------------------------------------------------
        hw = DOG['withers_h'] * (1 - 0.16 * crouch)
        hc = DOG['croup_h'] * (1 - 0.22 * crouch)
        hw = lerp(hw, 0.30, lie); hc = lerp(hc, 0.21, lie)
        sh = floor_y(x - f[0] * 0.3, LANE)
        bob = 0.012 * a['moving'] * math.sin(4 * math.pi * self.travel / self.STRIDE)
        Wg = C + f * DOG['spine'] + UP * (hw + sh + bob)
        Pg = C - f * DOG['spine'] + UP * (hc + bob)
        g.goal('W', Wg, 0.35, 'withers'); g.goal('P', Pg, 0.35, 'croup')
        g.goal('M', (Wg + Pg) / 2 + UP * 0.005, 0.15, 'back')
        # --- head ---------------------------------------------------------------
        look = a['look']
        fh = unit(fhead * math.cos(look * 1.0) + np.array([0, 0, -1.0]) * math.sin(look * 1.0))
        hd = clamp(a['head'], 0, 1.3)
        al = math.radians(lerp(-20, 42, min(hd, 1.0)) + 25 * max(0.0, hd - 1.0)) * (1 - 0.3 * lie) + math.radians(22) * look
        be = math.radians(lerp(-62, -8, clamp(hd, 0, 1.2)))
        Wp = g.p('W')
        Ng = Wp + DOG['neck'] * (math.cos(al) * fh + math.sin(al) * UP)
        Zg = Ng + DOG['head'] * (math.cos(be) * fh + math.sin(be) * UP)
        lead = smooth((t - 7.458) / 0.35) if 7.458 <= t < 9.5 else 0.0
        rest = a['rest'] * lie * (1 - lead)        # the chin leaves the paws as the head swings round
        if rest > 0:
            Nr = Wp + f * 0.20 + UP * (0.17 - Wp[1])
            Zr = Nr + f * DOG['head'] * 0.97 + UP * (0.07 - 0.17)
            Ng = lerp(Ng, Nr, rest); Zg = lerp(Zg, Zr, rest)
        g.goal('N', Ng, 0.3, 'poll'); g.goal('Z', Zg, 0.3, 'nose')
        # --- tail ---------------------------------------------------------------
        tl = a['tail']
        wag = a['wag'] * math.sin(2 * math.pi * 2.6 * t)
        gam = math.radians(lerp(30, -82, tl / 1.35) + 14 * wag)
        back = -unit(np.array([f[0], 0, f[2]]))
        prev = g.p('P')
        for k, nm in enumerate(['T1', 'T2', 'T3']):
            gg = gam - math.radians(12) * k * (1 - lie * 0.5)
            dvec = math.cos(gg) * back + math.sin(gg) * UP + side * (0.25 * wag * k)
            tgt = prev + DOG['tail'] * unit(dvec)
            g.goal(nm, tgt, 0.25, 'tail')
            prev = tgt
        # --- feet ---------------------------------------------------------------
        cyc = self.travel / self.STRIDE
        mdir = np.sign(dx) if abs(dx) > 1e-5 else 0.0
        lying = lie >= 0.03
        for name, kind, lr, off in LEGS:
            ft = self.feet[name]
            nm3 = name + '3'
            lat = (DOG['lat_f'] if kind == 'f' else DOG['lat_h']) * lr
            root = Wg if kind == 'f' else Pg
            home = root.copy() + side * lat + f * (0.02 if kind == 'f' else -0.02)
            home[1] = 0.03 + floor_y(home[0], home[2])
            set_floor(g, nm3, 0.03 + floor_y(g.p(nm3)[0], g.p(nm3)[2]))
            if lying:
                if kind == 'f':
                    tgt = Wg + f * 0.26 + side * lat * 0.9
                else:
                    tgt = Pg + f * 0.22 + side * lat * 1.9
                tgt = tgt.copy(); tgt[1] = 0.03 + floor_y(tgt[0], tgt[2])
                base = home      # rise from / sink toward the standing footprint under the body as it is now
                g.goal(nm3, lerp(base, tgt, smooth(lie * 1.15)), 0.5, 'foot')
                if kind == 'f':
                    elb = Wg + f * 0.05 + side * lat; elb[1] = 0.05
                    g.goal(name + '1', lerp(g.p(name + '1'), elb, 0), 0.0)
                ft['stance'] = False
                continue
            if self.lying_prev and not lying:
                p = g.p(nm3).copy(); p[1] = 0.03 + floor_y(p[0], p[2]); ft['pin'] = p; ft['stance'] = True
            local = (cyc + off) % 1.0
            in_stance = local < self.DUTY
            moving = (abs(dx) > 1e-5 or dyaw > 1e-4)
            if not moving and ft['stance']:
                g.pin(nm3, ft['pin']); continue
            if in_stance:
                if not ft['stance']:
                    p = g.p(nm3).copy(); p[1] = 0.03 + floor_y(p[0], p[2])
                    ft['pin'] = p; ft['stance'] = True
                    if record:
                        self.events.append({'t': t, 'kind': 'paw', 'leg': name, 'x': float(p[0])})
                g.pin(nm3, ft['pin'])
            else:
                if ft['stance']:
                    ft['stance'] = False; ft['lift'] = g.p(nm3).copy()
                s = (local - self.DUTY) / (1 - self.DUTY)
                land = home + np.array([mdir * self.STRIDE * 0.28, 0, 0])
                p = lerp(ft['lift'], land, smooth(s))
                p[1] = max(p[1], 0.03) + 0.075 * math.sin(math.pi * s)
                g.goal(nm3, p, 0.7, 'foot')
            # keep knees / elbows near their leg plane (soft)
        for name, kind, lr, off in LEGS:
            for j in ('1', '2'):
                g.plane(name + j, name + '0', side, 0.4)
        self.lying_prev = lying
        res = g.solve(iters=60, tol=2e-4, hard_tail=150)
        if record and lying and a['wag'] > 0.3:
            pass
        return res, f, side

# ----------------------------------------------------------------------------
# The person: a constraint graph
# ----------------------------------------------------------------------------
PZ_DOOR, PZ_BESIDE = -0.04, 0.32

def build_person(x0):
    g = Graph('person')
    g.side = np.array([0, 0, 1.0])
    z = PZ_DOOR
    f = np.array([1.0, 0, 0])
    g.point('Pv', [x0, 0.98, z]); g.point('Ch', [x0, 1.48, z]); g.point('Hd', [x0 + 0.02, 1.70, z])
    for s, lz in (('L', -0.1), ('R', 0.1)):
        g.point('Hp' + s, [x0, 0.92, z + lz]); g.point('Kn' + s, [x0 + 0.03, 0.52, z + lz])
        g.point('An' + s, [x0, 0.11, z + lz]); g.point('To' + s, [x0 + 0.17, 0.03, z + lz])
        g.dist('Hp' + s, 'Kn' + s, 0.45); g.dist('Kn' + s, 'An' + s, 0.43); g.dist('An' + s, 'To' + s, 0.17)
        g.bend('Hp' + s, 'Kn' + s, 'An' + s, 1, 0.02)
        g.floor('An' + s, 0.08); g.floor('To' + s, 0.03); g.floor('Kn' + s, 0.08)
        g.point('Sh' + s, [x0, 1.42, z + lz * 1.7]); g.point('El' + s, [x0 - 0.04, 1.13, z + lz * 1.8])
        g.point('Wr' + s, [x0, 0.87, z + lz * 1.8])
        g.dist('Sh' + s, 'El' + s, 0.29); g.dist('El' + s, 'Wr' + s, 0.28)
        g.bend('Sh' + s, 'El' + s, 'Wr' + s, -1, 0.012)
        g.floor('Wr' + s, 0.04)
        def hip(G, lz=lz):
            return G.P[G.idx['Pv']] + G.side * lz
        def sho(G, lz=lz):
            Cp, Pp = G.P[G.idx['Ch']], G.P[G.idx['Pv']]
            a = unit(Cp - Pp)
            return Cp - a * 0.06 + G.side * lz * 1.75
        g.attach_pt('Hp' + s, hip, 0.5); g.attach_pt('Sh' + s, sho, 0.5)
    g.dist('Pv', 'Ch', 0.5); g.dist('Ch', 'Hd', 0.23)
    for s in 'LR':
        g.P[g.idx['Hp' + s]] = g.attach[[n for n, (i, fn, k) in enumerate(g.attach) if g.names[i] == 'Hp' + s][0]][1](g)
        g.P[g.idx['Sh' + s]] = g.attach[[n for n, (i, fn, k) in enumerate(g.attach) if g.names[i] == 'Sh' + s][0]][1](g)
        g.rigid('Hp' + s, ['Pv', 'Ch']); g.rigid('Sh' + s, ['Ch', 'Pv'])
    g.dist('HpL', 'HpR'); g.dist('ShL', 'ShR')
    g.vmax = 0.08
    for n, m in (('Pv', 0.08), ('Ch', 0.2), ('HpL', 0.2), ('HpR', 0.2), ('ShL', 0.4), ('ShR', 0.4), ('Hd', 0.5)):
        g.mass(n, m)
    g.floor('Pv', 0.12)
    g.side = np.array([0, 0, 1.0])
    return g

class PersonDriver:
    def __init__(self):
        p0 = SF[0]['person']
        self.g = build_person(p0['x'])
        self.feet = {}
        for s in 'LR':
            self.feet[s] = {'pin': self.g.p('An' + s).copy(), 'swing': None}
        self.events = []
        for _ in range(4):
            self.step(0, None, None, record=False)

    def step(self, i, hand_req, pelvis_req, record=True, tt=None):
        fr = SF[i]; p = fr['person']; t = fr['t'] if tt is None else tt
        g = self.g
        g.clear_frame()
        f = np.array([1.0, 0, 0])
        g.side = np.array([0, 0, 1.0])
        sit = p['sit']
        x = p['x']
        mv = smooth((x - (-0.28)) / (-1.25 + 0.28))
        z = lerp(PZ_DOOR, PZ_BESIDE, mv)
        stand_y = 0.97 + floor_y(x, z)
        Pg = np.array([x - 0.02 * sit, lerp(stand_y, 0.14, smooth(sit)), z])
        if pelvis_req is not None:
            Pg = pelvis_req
        g.goal('Pv', Pg, 0.8, 'pelvis')
        reach = p['reach']
        lean = 0.0
        Cg = Pg + UP * 0.5
        if hand_req is not None and reach > 0.05:
            dirh = unit(hand_req - g.p('Ch'))
            Cg = Pg + 0.5 * unit(UP + dirh * 0.42 * reach)
        Cg = Cg + f * 0.04 * sit
        g.goal('Ch', Cg, 0.6, 'chest')
        hdir = unit(UP + f * (0.25 + 0.2 * p['low']))
        g.goal('Hd', g.p('Ch') + 0.23 * hdir, 0.4, 'head')
        # arms
        low = p['low']
        for s in 'LR':
            sh = g.p('Sh' + s)
            if s == 'R' and hand_req is not None and reach > 0.05:
                g.goal('Wr' + s, hand_req, 0.3, 'hand')
            elif s == 'R' and low > 0.02:
                tgt = np.array([Pg[0] + 0.62, 0.32, Pg[2] + 0.12])
                rest = sh + np.array([0.05, -0.52, 0.0])
                g.goal('Wr' + s, lerp(rest, tgt, smooth(low)), 0.4, 'hand')
            else:
                if sit > 0.5:
                    knee = g.p('Kn' + s)
                    g.goal('Wr' + s, knee + UP * 0.05 + f * 0.02, 0.2 * smooth((sit - 0.5) * 2), 'rest_hand')
                g.goal('Wr' + s, sh + np.array([0.04, -0.54, 0.0]), 0.12, 'hang')
        # feet: planted unless the stance is strained, then one step at a time
        for s, lz in (('L', -0.1), ('R', 0.1)):
            ft = self.feet[s]
            other = self.feet['R' if s == 'L' else 'L']
            if sit > 0.35:
                home = np.array([Pg[0] + lerp(0.1, 0.5, smooth((sit - 0.35) / 0.5)), 0.08, Pg[2] + lz * 1.4])
            else:
                home = np.array([Pg[0] + 0.03, 0.08 + floor_y(Pg[0], Pg[2]), Pg[2] + lz])
            if ft['swing'] is None:
                if np.linalg.norm((ft['pin'] - home)[[0, 2]]) > 0.13 and other['swing'] is None:
                    ft['swing'] = (ft['pin'].copy(), t, 0.28)
            if ft['swing'] is not None:
                a0, t0, dur = ft['swing']
                k = (t - t0) / dur
                if k >= 1:
                    pq = g.p('An' + s).copy(); pq[1] = home[1]
                    ft['pin'] = pq; ft['swing'] = None
                    if record:
                        self.events.append({'t': t, 'kind': 'step', 'x': float(home[0])})
                    g.pin('An' + s, ft['pin'])
                else:
                    q = lerp(a0, home, smooth(k)); q[1] += 0.08 * math.sin(math.pi * k)
                    g.goal('An' + s, q, 0.7, 'foot')
            else:
                g.pin('An' + s, ft['pin'])
            g.goal('To' + s, g.p('An' + s) + f * 0.16 + UP * -0.06, 0.3, 'toe')
        res = g.solve(iters=50, tol=2e-4, hard_tail=150)
        return res

# ----------------------------------------------------------------------------
# The door leaf: hinge + equal edges, dragged by the pen
# ----------------------------------------------------------------------------
class Door:
    AJAR = math.radians(32)
    OPEN = math.radians(82)
    def __init__(self):
        g = Graph('door')
        hx = DOOR['x1']
        g.point('Hb', [hx, 0.04, 0.0], 0.0); g.point('Ht', [hx, DOOR['top'], 0.0], 0.0)
        a = self.AJAR
        g.point('Eb', [hx - LEAF_W * math.cos(a), 0.04, -LEAF_W * math.sin(a)])
        g.point('Et', [hx - LEAF_W * math.cos(a), DOOR['top'], -LEAF_W * math.sin(a)])
        g.dist('Hb', 'Eb', LEAF_W); g.dist('Ht', 'Et', LEAF_W); g.dist('Eb', 'Et', DOOR['top'] - 0.04)
        g.dist('Hb', 'Et'); g.dist('Ht', 'Eb')       # the leaf stays a rectangle (equal diagonals)
        g.side = np.array([0, 0, 1.0])
        self.g = g
        self.angle = a
    def handle(self):
        Eb, Et = self.g.p('Eb'), self.g.p('Et')
        Hb = self.g.p('Hb')
        return Eb + (Et - Eb) * (1.0 - 0.04) / (DOOR['top'] - 0.04) + (Hb - Eb) * 0.08
    def step(self, req):
        g = self.g; g.clear_frame()
        g.invm[g.idx['Hb']] = 0; g.invm[g.idx['Ht']] = 0
        if req is not None:
            # the pen drags the handle; the request is carried by the free edge
            h = self.handle()
            dlt = req - h
            g.goal('Eb', g.p('Eb') + dlt, 0.5, 'edge'); g.goal('Et', g.p('Et') + dlt, 0.5, 'edge')
        res = g.solve(iters=20, tol=1e-4, hard_tail=30)
        Eb = g.p('Eb')
        self.angle = math.atan2(-Eb[2], DOOR['x1'] - Eb[0])
        return res

# ----------------------------------------------------------------------------
# The light pen: a script of manipulations (the prompts, performed)
# ----------------------------------------------------------------------------
PARK = np.array([-2.35, -0.25, 1.9])

def pen_script():
    """(t0, t1, mode, target_name, op). mode: move | point | drag."""
    return [
        (0.40, 0.95, 'move', 'head', None),
        (0.95, 2.30, 'point', 'head', 'CALL'),
        (2.30, 2.85, 'move', 'hand', None),
        (2.85, 3.40, 'point', 'hand', 'CALL'),
        (3.40, 4.60, 'drag', 'hand', 'REACH'),
        (4.60, 5.05, 'move', 'pelvis', None),
        (5.05, 5.40, 'point', 'pelvis', None),
        (5.40, 5.95, 'drag', 'pelvis', 'MOVE'),
        (5.95, 6.20, 'move', 'handle', None),
        (6.20, 6.60, 'drag', 'handle', 'OPEN'),
        (6.60, 6.85, 'move', 'hand', None),
        (6.85, 7.25, 'drag', 'hand', 'HAND'),
        (7.25, 7.45, 'move', 'head', None),
        (7.45, 9.40, 'point', 'head', 'SOFT'),
        (9.40, 10.40, 'move', 'hover', None),
        (10.40, 11.60, 'point', 'head', 'SOFT'),
        (11.60, 12.60, 'move', 'park', None),
        (25.80, 26.40, 'move', 'head', None),
        (26.40, 27.40, 'point', 'head', 'SOFT'),
        (27.40, 28.40, 'move', 'park', None),
    ]

PROMPTS = score['prompts']

def prompt_at(t):
    cur = None
    for t0, s in PROMPTS:
        if t >= t0:
            cur = (t0, s)
    return cur

def voice_at(t):
    v = 'none'; t0 = None
    for tt, ch in score['timeline']:
        if 'voice' in ch and t >= tt:
            v = ch['voice']; t0 = tt
    return v, t0

# ----------------------------------------------------------------------------
# Static drawing (world)
# ----------------------------------------------------------------------------
def world_lines():
    """Static world in metres: list of (pts3d, I, group). Built as constrained primitives."""
    L = []
    def ln(pts, I, grp):
        L.append((np.array(pts, float), I, grp))
    WX0, WX1, EAVE = -2.9, 2.4, 2.62
    PFZ = 1.9
    # porch floor: wall base, front edge, boards (copies of one master board: instances)
    ln([[WX0, 0, 0], [DOOR['x0'] - 0.10, 0, 0]], 0.7, 'porch')
    ln([[DOOR['x1'] + 0.10, 0, 0], [WX1, 0, 0]], 0.7, 'porch')
    ln([[WX1, 0, 0], [4.9, 0, 0]], 0.35, 'porch')
    ln([[WX0, 0, PFZ], [4.9, 0, PFZ]], 0.9, 'porch')
    ln([[WX0, -0.16, PFZ], [4.9, -0.16, PFZ]], 0.45, 'porch')
    xb = -2.85
    while xb < 4.9:
        ln([[xb, 0, 0.0], [xb, 0, PFZ]], 0.12, 'boards')
        xb += 0.25
    # steps at the porch end
    for z in (0.0, PFZ):
        ln([[4.9, 0, z], [4.9, -0.18, z], [5.22, -0.18, z], [5.22, -0.36, z], [5.54, -0.36, z], [5.54, -0.54, z], [6.6, -0.54, z]], 0.55 if z else 0.8, 'steps')
    for xs, ys in ((4.9, 0), (4.9, -0.18), (5.22, -0.18), (5.22, -0.36), (5.54, -0.36), (5.54, -0.54)):
        ln([[xs, ys, 0], [xs, ys, PFZ]], 0.35, 'steps')
    # wall: corner, eave; clapboards (instances), clipped out of the door and window
    ln([[WX1, 0, 0], [WX1, EAVE, 0]], 0.75, 'wall')
    ln([[WX0, EAVE, 0], [WX1, EAVE, 0]], 0.6, 'wall')
    win = (-2.45, -1.75, 0.95, 1.95)
    yb = 0.22
    while yb < EAVE - 0.05:
        segs = [(WX0, WX1)]
        cut = []
        if yb < DOOR['top'] + 0.12:
            cut.append((DOOR['x0'] - 0.10, DOOR['x1'] + 0.10))
        if win[2] - 0.08 < yb < win[3] + 0.08:
            cut.append((win[0] - 0.08, win[1] + 0.08))
        for c0, c1 in cut:
            new = []
            for s0, s1 in segs:
                if c1 <= s0 or c0 >= s1:
                    new.append((s0, s1)); continue
                if c0 > s0: new.append((s0, c0))
                if c1 < s1: new.append((c1, s1))
            segs = new
        for s0, s1 in segs:
            ln([[s0, yb, 0], [s1, yb, 0]], 0.10, 'clapboard')
        yb += 0.2
    # window (dark at dusk): frame + mullions
    x0, x1, y0, y1 = win
    ln([[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y1, 0], [x0, y0, 0]], 0.5, 'window')
    ln([[(x0 + x1) / 2, y0, 0], [(x0 + x1) / 2, y1, 0]], 0.3, 'window')
    ln([[x0, (y0 + y1) / 2, 0], [x1, (y0 + y1) / 2, 0]], 0.3, 'window')
    ln([[x0 - 0.08, y0 - 0.06, 0], [x1 + 0.08, y0 - 0.06, 0]], 0.4, 'window')
    # porch roof: fascia at the front, posts (one master post, instanced)
    ln([[WX0, EAVE, PFZ], [5.05, EAVE, PFZ]], 0.7, 'roof')
    ln([[WX0, EAVE + 0.16, PFZ], [5.05, EAVE + 0.16, PFZ]], 0.5, 'roof')
    ln([[5.05, EAVE, PFZ], [5.05, EAVE + 0.16, PFZ]], 0.5, 'roof')
    ln([[WX1, EAVE, 0], [5.05, EAVE, 0]], 0.25, 'roof')
    for px in (4.72,):
        for dxp in (0.0, 0.12):
            ln([[px + dxp, 0, PFZ - 0.06], [px + dxp, EAVE, PFZ - 0.06]], 0.7, 'post')
    # the sill (a slab across the threshold)
    s = SILL
    ln([[s['x0'], s['h'], s['z1']], [s['x1'], s['h'], s['z1']]], 0.85, 'sill')
    ln([[s['x0'], 0, s['z1']], [s['x1'], 0, s['z1']]], 0.5, 'sill')
    ln([[s['x0'], 0, s['z1']], [s['x0'], s['h'], s['z1']], [s['x0'], s['h'], 0]], 0.5, 'sill')
    ln([[s['x1'], 0, s['z1']], [s['x1'], s['h'], s['z1']], [s['x1'], s['h'], 0]], 0.5, 'sill')
    ln([[DOOR['x0'], s['h'], 0], [DOOR['x1'], s['h'], 0]], 0.4, 'sill')
    # dusk beyond the corner: horizon, a distant fence (instances of one picket), the moon
    ln([[WX1 + 0.02, 1.05, -6], [6.6, 1.05, -6]], 0.22, 'dusk')
    xp = 2.55
    while xp < 6.6:
        ln([[xp, 1.05, -6], [xp, 1.22, -6]], 0.16, 'fence')
        xp += 0.17
    ln([[2.45, 1.16, -6], [6.6, 1.16, -6]], 0.12, 'fence')
    return L

def door_frame_pts():
    """The door frame as a constrained figure: 4 corners, casing offset."""
    x0, x1, top, h = DOOR['x0'], DOOR['x1'], DOOR['top'], SILL['h']
    return np.array([[x0, h, 0], [x0, top, 0], [x1, top, 0], [x1, h, 0]], float)

def draw_world(df, cam, Lw, frame_pts=None, I_scale=1.0, reveal=None):
    """reveal: number of world primitives to draw (title build)."""
    n = len(Lw) if reveal is None else reveal
    for k, (pts, I, grp) in enumerate(Lw[:n]):
        df.line(cam.pa(pts), I * I_scale, 'world')
    fp = door_frame_pts() if frame_pts is None else frame_pts
    sp = cam.pa(fp)
    df.line(sp, 0.95 * I_scale, 'frame')
    # casing: offset outline (a copy of the frame, constrained parallel)
    cas = fp.copy(); cas[0, 0] -= 0.10; cas[1, 0] -= 0.10; cas[1, 1] += 0.10; cas[2, 1] += 0.10; cas[2, 0] += 0.10; cas[3, 0] += 0.10
    df.line(cam.pa(cas), 0.55 * I_scale, 'frame')

def constraint_glyphs(df, cam, I=0.32):
    """Sketchpad shows its constraints as symbols on demand: here, dimly, always."""
    S = cam.S
    for xj in (DOOR['x0'], DOOR['x1']):
        p = cam.p((xj, 1.2, 0))
        df.text('∥', p[0] + (8 if xj > 0 else -16), p[1], 9, I, 'glyph')
    for (xj, yj, sx, sy) in ((DOOR['x0'], SILL['h'], 1, -1), (DOOR['x1'], SILL['h'], -1, -1)):
        p = cam.p((xj, yj, 0))
        q = 7
        df.line([(p[0] + sx * q, p[1]), (p[0] + sx * q, p[1] + sy * q), (p[0], p[1] + sy * q)], I, 'glyph')
    p = cam.p((0, DOOR['top'] + 0.18, 0))
    df.text('= W 0.92', p[0] - 26, p[1], 8, I * 0.9, 'glyph')

# ----------------------------------------------------------------------------
# Drawing the dog and the person from their solved graphs
# ----------------------------------------------------------------------------
def draw_dog(df, cam, g, f, side, I=1.0, show_graph=True, pins=None):
    P = lambda n: g.p(n)
    S = cam.S
    Wp, Mp, Pp, Np, Zp = P('W'), P('M'), P('P'), P('N'), P('Z')
    a = unit(Wp - Pp); ub = unit(np.cross(side, a))
    cz = (Wp[2] + Pp[2]) / 2
    def depthI(pt):
        return I * (0.55 if pt[2] < cz - 0.02 else 1.0)
    order = sorted(LEGS, key=lambda L: g.p(L[0] + '2')[2])
    # far legs first
    for name, kind, lr, off in order:
        A, B, Cc, D = [P(name + k) for k in '0123']
        Ii = depthI(B)
        r1, r2, r3 = (0.045, 0.031, 0.026) if kind == 'f' else (0.062, 0.034, 0.026)
        sA, sB, sC, sD = cam.pa([A, B, Cc, D])
        if kind == 'h':
            capsule(df, sB, sC, r1 * S * 0.75, r2 * S, Ii, 'dog', ends=(True, False))
        else:
            capsule(df, sB, sC, r1 * S * 0.8, r2 * S, Ii, 'dog', ends=(True, False))
        capsule(df, sC, sD, r2 * S, r3 * S, Ii, 'dog', ends=(False, False))
        # paw: a short flattened loop pointing forward
        fwd = unit(np.array([f[0], 0, f[2]]))
        paw = [D + fwd * 0.045 - UP * 0.02, D - fwd * 0.02 - UP * 0.025, D - fwd * 0.03 + UP * 0.012, D + fwd * 0.02 + UP * 0.02]
        df.line(catmull(cam.pa(paw), 4, closed=True), Ii, 'dog')
    # torso outline (attached-to the spine: offsets in the body frame)
    sp = [
        Wp + a * 0.11 - ub * 0.10,      # point of shoulder / chest front
        Wp + a * 0.05 - ub * 0.28,      # brisket
        Mp + a * 0.06 - ub * 0.22,      # belly
        Pp + a * 0.16 - ub * 0.15,      # tuck up
        Pp + a * 0.02 - ub * 0.19,      # stifle line
        Pp - a * 0.07 - ub * 0.10,      # buttock
        Pp - a * 0.03 + ub * 0.025,     # croup
        Mp + ub * 0.045,                # back
        Wp - a * 0.02 + ub * 0.075,     # withers
    ]
    tors = catmull(cam.pa(sp), 6, closed=True)
    df.line(tors, I, 'dog'); df.occ.append(tors)
    # neck: two curves from the body to the head
    hd = unit(Zp - Np); hs = head_side(hd, side); hu = unit(np.cross(hs, hd))
    if hu[1] < 0:
        hu = -hu
    df.line(catmull(cam.pa([Wp + ub * 0.075 - a * 0.02, Wp + (Np - Wp) * 0.5 + ub * 0.06, Np + hu * 0.045 - hd * 0.03]), 5), I, 'dog')
    df.line(catmull(cam.pa([Wp + a * 0.11 - ub * 0.10, Wp + (Np - Wp) * 0.55 - ub * 0.02 + a * 0.05, Np - hu * 0.05 + hd * 0.03]), 5), I, 'dog')
    # head
    Lh = np.linalg.norm(Zp - Np)
    head = [Np - hd * 0.05 + hu * 0.045, Np + hd * 0.05 + hu * 0.075, Np + hd * 0.12 + hu * 0.06,
            Zp - hd * 0.07 + hu * 0.03, Zp + hu * 0.012, Zp - hu * 0.03,
            Zp - hd * 0.05 - hu * 0.045, Np + hd * 0.09 - hu * 0.07, Np - hd * 0.02 - hu * 0.065]
    hpoly = catmull(cam.pa(head), 4, closed=True)
    df.line(hpoly, I, 'dog'); df.occ.append(hpoly)
    neckp = np.concatenate([catmull(cam.pa([Wp + ub * 0.075 - a * 0.02, Wp + (Np - Wp) * 0.5 + ub * 0.06, Np + hu * 0.045 - hd * 0.03]), 5),
                            catmull(cam.pa([Wp + a * 0.11 - ub * 0.10, Wp + (Np - Wp) * 0.55 - ub * 0.02 + a * 0.05, Np - hu * 0.05 + hd * 0.03]), 5)[::-1]])
    df.occ.append(neckp)
    df.dot(cam.p(Zp + hu * 0.005), I * 1.6, 'dog')                 # nose
    eye = Np + hd * 0.085 + hu * 0.03
    df.dot(cam.p(eye), I * 1.3, 'dog')
    # ears: attached to the head frame; the score's 'ear' sets their angle
    return hd, hu

def head_side(hd, side):
    h = np.array([hd[0], 0.0, hd[2]])
    if np.linalg.norm(h) < 0.2:
        return side
    return unit(np.cross(unit(h), UP))

def draw_ears(df, cam, g, side, ear, I=1.0):
    Np, Zp = g.p('N'), g.p('Z')
    hd = unit(Zp - Np); hs = head_side(hd, side); hu = unit(np.cross(hs, hd))
    if hu[1] < 0:
        hu = -hu
    for k, lat in enumerate((-1, 1)):
        base = Np + hu * 0.04 + hd * 0.02 + hs * 0.035 * lat
        ang = math.radians(lerp(-150, -60, clamp(ear, 0, 1)))   # flat back -> pricked
        tipdir = math.cos(ang) * hd + math.sin(ang) * (-hu)
        tip = base - tipdir * 0.10 * (1 if True else 1)
        tip = base + unit(-(math.cos(math.radians(lerp(160, 75, clamp(ear, 0, 1)))) * hd) + math.sin(math.radians(lerp(160, 75, clamp(ear, 0, 1)))) * hu) * 0.12
        b1 = base - hd * 0.045; b2 = base + hd * 0.035
        Ii = I * (0.55 if lat * hs[2] < 0 else 1.0)
        df.line(cam.pa([b1, tip, b2]), Ii, 'dog')

def draw_tail(df, cam, g, I=1.0):
    pts = [g.p('P') - unit(g.p('W') - g.p('P')) * 0.02 + UP * 0.01, g.p('T1'), g.p('T2'), g.p('T3')]
    sp = cam.pa(pts)
    c = catmull(sp, 5)
    S = cam.S
    n = len(c)
    left, right = [], []
    for k in range(n):
        a = c[min(k + 1, n - 1)] - c[max(k - 1, 0)]
        a = a / (np.linalg.norm(a) + 1e-9)
        nn = np.array([-a[1], a[0]])
        r = S * lerp(0.032, 0.012, k / (n - 1)) * (1 + 0.5 * math.sin(math.pi * k / (n - 1)))
        left.append(c[k] + nn * r); right.append(c[k] - nn * r)
    df.line(left + right[::-1], I, 'dog')

def draw_graph(df, cam, g, I=0.35, tag='graph', skip=()):
    for kind, prm in g.hard:
        if kind == 'dist':
            a, b, L = prm
            if g.names[a] in skip or g.names[b] in skip:
                continue
            df.line(cam.pa([g.P[a], g.P[b]]), I, tag)
    for k, n in enumerate(g.names):
        if n in skip:
            continue
        df.dot(cam.p(g.P[k]), I * 1.8, tag)

def draw_person(df, cam, g, I=1.0):
    P = g.p
    S = cam.S
    Pv, Ch, Hd = P('Pv'), P('Ch'), P('Hd')
    for s in ('L', 'R'):
        Ii = I * (0.55 if s == 'L' else 1.0)
        A, B, Cc, D = cam.pa([P('Hp' + s), P('Kn' + s), P('An' + s), P('To' + s)])
        capsule(df, A, B, 0.075 * S, 0.055 * S, Ii, 'person', ends=(False, True))
        capsule(df, B, Cc, 0.055 * S, 0.04 * S, Ii, 'person', ends=(False, False))
        heel = P('An' + s) - np.array([0.05, 0.05, 0])
        df.line(cam.pa([heel, P('An' + s) + UP * 0.02, P('To' + s) + UP * 0.02, P('To' + s) - UP * 0.03, heel + UP * 0.0]), Ii, 'person')
    # torso
    a = unit(Ch - Pv); n = np.array([1.0, 0, 0]) - a * a[0]; n = unit(n)
    tor = [Pv - n * 0.12 - a * 0.04, Pv + n * 0.11 - a * 0.04, Ch + n * 0.12 - a * 0.05, Ch + n * 0.05 + a * 0.05,
           Ch - n * 0.08 + a * 0.05, Ch - n * 0.13 - a * 0.06]
    tp = catmull(cam.pa(tor), 5, closed=True)
    df.line(tp, I, 'person'); df.occ.append(tp)
    # head (an arc: the circle constraint) and neck
    hc = cam.p(Hd + UP * 0.03)
    hcirc = arc_pts(hc, 0.105 * S, 0, 2 * math.pi, 40)
    df.line(hcirc, I, 'person'); df.occ.append(hcirc)
    df.line(cam.pa([Ch + a * 0.04, Hd - UP * 0.07]), I * 0.8, 'person')
    # nose / face direction
    fdir = unit(Hd - Ch); fdir = np.array([1.0, 0, 0])
    df.line(cam.pa([Hd + UP * 0.05 + fdir * 0.105, Hd + UP * 0.01 + fdir * 0.125, Hd - UP * 0.01 + fdir * 0.10]), I * 0.9, 'person')
    for s in ('L', 'R'):
        Ii = I * (0.55 if s == 'L' else 1.0)
        A, B, Cc = cam.pa([P('Sh' + s), P('El' + s), P('Wr' + s)])
        capsule(df, A, B, 0.045 * S, 0.037 * S, Ii, 'person', ends=(True, False))
        capsule(df, B, Cc, 0.037 * S, 0.03 * S, Ii, 'person', ends=(False, False))
        # hand: a small open loop beyond the wrist
        el, wr = P('El' + s), P('Wr' + s)
        u = unit(wr - el)
        hp = [wr + u * 0.0 + UP * 0.025, wr + u * 0.09 + UP * 0.02, wr + u * 0.11, wr + u * 0.08 - UP * 0.025, wr - UP * 0.025]
        df.line(catmull(cam.pa(hp), 3), Ii, 'person')
    return cam.p(Hd + np.array([0.11, -0.02, 0]))

def draw_pins(df, cam, pts, I=0.4):
    """A planted point: the 'held-to-floor' symbol (a short ground hatch)."""
    for p in pts:
        c = cam.p(p - UP * 0.03)
        df.line([(c[0] - 6, c[1] + 2), (c[0] + 6, c[1] + 2)], I, 'glyph')
        for k in (-5, -1, 3):
            df.line([(c[0] + k, c[1] + 2), (c[0] + k - 3, c[1] + 6)], I * 0.8, 'glyph')

def draw_pen(df, xy, mode, I=1.0):
    """Sketchpad's tracking cross: four arms of dots with a gap; a ring when it holds something."""
    x, y = xy
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in range(3, 13, 2):
            df.dot((x + dx * k * 1.25, y + dy * k * 1.25), I * (1.2 if k < 8 else 0.7), 'pen')
    if mode == 'drag':
        df.line(arc_pts((x, y), 6.5, 0, 2 * math.pi, 18), I, 'pen')
    elif mode == 'point':
        df.line(arc_pts((x, y), 4, 0, 2 * math.pi, 12), I * 0.6, 'pen')

BUTTONS = ['CALL', 'REACH', 'MOVE', 'OPEN', 'HAND', 'SOFT']

def draw_panel(df, t, op, prompt, lines):
    # lower console, drawn on the same display
    y0 = 560
    df.line([(28, y0 - 14), (1252, y0 - 14)], 0.16, 'text')
    if prompt:
        t0, s = prompt
        n = int(clamp((t - t0) * 32, 0, len(s)))
        txt = '> ' + s[:n].upper()
        df.text(txt, 40, y0 + 18, 15, 0.95, 'text')
        if n < len(s) or (int(t * 2.5) % 2 == 0):
            w = text_width(txt, 15)
            df.line([(40 + w + 4, y0 + 20), (40 + w + 14, y0 + 20)], 0.9, 'text')
    yy = y0 + 54
    for k, (s, I) in enumerate(lines):
        df.text(s, 40, yy + k * 21, 10.5, I, 'text')
    # push buttons
    bx = 1252 - len(BUTTONS) * 82
    for k, b in enumerate(BUTTONS):
        x = bx + k * 82
        on = (b == op)
        I = 1.0 if on else 0.22
        df.line([(x, y0 + 2), (x + 70, y0 + 2), (x + 70, y0 + 26), (x, y0 + 26)], I, 'text', closed=True)
        w = text_width(b, 9)
        df.text(b, x + 35 - w / 2, y0 + 19, 9, I, 'text')

def voice_arcs(df, cam, mouth, t, I=1.0):
    v, t0 = voice_at(t)
    out = []
    if v == 'none' or t0 is None:
        return
    el = t - t0
    if v == 'call':
        speed, period, span, maxr, Iv = 2.6, 0.16, math.radians(28), 2.6, 1.0
    else:
        speed, period, span, maxr, Iv = 0.75, 0.55, math.radians(18), 1.1, 0.55
    k = 0
    while True:
        age = el - k * period
        if age < 0:
            break
        r = age * speed
        if r <= maxr and r > 0.05:
            fade = (1 - r / maxr) * Iv * I
            R = r * cam.S
            df.line(arc_pts(mouth, R, -span, span, max(5, int(R * span / 2.5))), fade, 'voice')
        k += 1
        if k > 80:
            break

# ----------------------------------------------------------------------------
# Main solve pass
# ----------------------------------------------------------------------------
def frame_time(n):
    """display frame n -> ('title'|'scene'|'end', local index, scene time)"""
    if n < TITLE_N:
        return 'title', n, (n - TITLE_N) / FPS
    if n < TITLE_N + N_SCENE:
        i = n - TITLE_N
        return 'scene', i, SF[i]['t']
    return 'end', n - TITLE_N - N_SCENE, SF[-1]['t'] + (n - TITLE_N - N_SCENE + 1) / FPS

def main():
    os.makedirs(CACHE, exist_ok=True)
    Lw = world_lines()
    dog = DogDriver()
    per = PersonDriver()
    door = Door()
    script = pen_script()
    frames = []
    trace = []
    solver_log = []
    events = []
    pen_xy_prev = None
    pen_world = PARK.copy()
    hand_req = None
    pelvis_req = None
    held = None
    hand_low_marker = None
    door_req = None
    sit_target = np.array([-1.25 - 0.02, 0.14, PZ_BESIDE])
    # --- solve the scene first (the title shows frame 0's drawing being built) ---
    scene = []
    for i in range(N_SCENE):
        fr = SF[i]; t = fr['t']
        # pen
        seg = None
        for s in script:
            if s[0] <= t < s[1]:
                seg = s
        def target_world(name):
            if name == 'head':
                return per.g.p('Hd') + np.array([0.13, 0.0, 0])
            if name == 'hand':
                return per.g.p('Wr' + 'R') + np.array([0.08, 0, 0])
            if name == 'pelvis':
                return per.g.p('Pv')
            if name == 'handle':
                return door.handle()
            if name == 'park':
                return PARK
            if name == 'hover':
                return per.g.p('Hd') + np.array([0.5, 0.35, 0])
            return pen_world
        mode, op = 'idle', None
        hand_req = None; pelvis_req = None; door_req = None
        if seg:
            t0, t1, mode, tgt, op = seg
            k = (t - t0) / (t1 - t0)
            if mode == 'move':
                pen_world = lerp(pen_world, target_world(tgt), clamp(0.12 + 0.5 * smooth(k)))
            elif mode == 'point':
                pen_world = lerp(pen_world, target_world(tgt), 0.35)
            elif mode == 'drag':
                if tgt == 'hand' and op == 'REACH':
                    start = per.g.p('Sh' + 'R')
                    dog_head = dog.g.p('N')
                    goal = lerp(start + np.array([0.3, -0.1, 0]), dog_head + np.array([-0.15, 0.0, 0]), smooth(k * 1.6))
                    pen_world = lerp(pen_world, goal, 0.5)
                    hand_req = pen_world.copy()
                elif tgt == 'hand':
                    goal = np.array([-1.25 + 0.62, 0.32, PZ_BESIDE + 0.12])
                    pen_world = lerp(pen_world, goal, 0.25)
                    hand_low_marker = goal
                elif tgt == 'pelvis':
                    pen_world = lerp(pen_world, sit_target, smooth(k) * 0.35 + 0.05)
                elif tgt == 'handle':
                    hz = -LEAF_W * math.sin(Door.OPEN); hx = DOOR['x1'] - LEAF_W * math.cos(Door.OPEN)
                    goal = np.array([hx, 1.0, hz])
                    a = lerp(Door.AJAR, Door.OPEN, smooth(k))
                    goal = np.array([DOOR['x1'] - LEAF_W * 0.92 * math.cos(a), 1.0, -LEAF_W * 0.92 * math.sin(a)])
                    pen_world = goal
                    door_req = goal
        else:
            pen_world = lerp(pen_world, PARK, 0.06)
        dres = door.step(door_req)
        pres = per.step(i, hand_req, None)
        dg = dog.step(i)
        res, f, side = dg
        scene.append(dict(i=i, t=t, mode=mode, op=op, pen=pen_world.copy(),
                          dogP=dog.g.P.copy(), dog_side=side.copy(), dog_f=f.copy(),
                          perP=per.g.P.copy(), doorP=door.g.P.copy(), door_angle=door.angle,
                          hand_req=None if hand_req is None else hand_req.copy(),
                          dres=dict(res), pres=dict(per.g.last), doorres=dict(door.g.last),
                          pins=[dog.feet[n]['pin'].copy() for n, *_ in LEGS if dog.feet[n]['stance']],
                          ppins=[per.feet[s]['pin'].copy() for s in 'LR' if per.feet[s]['swing'] is None],
                          sit_marker=sit_target.copy() if (5.4 <= t) else None,
                          hand_marker=None if hand_low_marker is None else hand_low_marker.copy()))
        if i % 96 == 0:
            print('solve', i, t, 'dog hard max %.2e' % res['hard_max'], 'iters', res['iters'], 'person %.2e' % per.g.last['hard_max'], flush=True)
    events = dog.events + per.events
    pickle.dump({'scene': scene, 'events': events, 'Lw': Lw}, open(os.path.join(CACHE, 'solve.pkl'), 'wb'))
    print('solved', len(scene))

if __name__ == '__main__':
    main()
