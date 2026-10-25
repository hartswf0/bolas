"""Moving fig. 1: forward kinematics of the cut pieces, two-bone IK with pinned stance feet, and substitution of turn plates.
Local coordinates are the f006 scan's own pixels; the screen map is q = O + K * (f * (p.x - A.x), p.y - A.y)."""
import json, os, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
PL = os.path.join(HERE, 'cache', 'plates')
META = json.load(open(os.path.join(PL, 'dogL.json')))
TURNM = json.load(open(os.path.join(PL, 'turn.json')))
K = META['K']; RIG = META['rig']; A = META['anchor']
_cache = {}
def plate(name):
    if name not in _cache:
        im = Image.open(os.path.join(PL, name + '.png')); r, g, b, a = im.split()
        _cache[name] = (im, )
    return _cache[name][0]

def rot(v, a):
    c, s = math.cos(a), math.sin(a); return (c * v[0] - s * v[1], s * v[0] + c * v[1])
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def ang(v): return math.atan2(v[1], v[0])
def norm(v): return math.hypot(v[0], v[1])
def lerp(a, b, t): return a + (b - a) * t

def ik(hip, target, l1, l2, bend):
    d = sub(target, hip); dist = max(abs(l1 - l2) + 1e-3, min(norm(d), l1 + l2 - 1e-3))
    base = ang(d)
    c = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    a1 = base + bend * math.acos(max(-1, min(1, c)))
    knee = add(hip, (l1 * math.cos(a1), l1 * math.sin(a1)))
    foot = add(hip, (dist * math.cos(base), dist * math.sin(base)))
    return knee, foot

# gait: lateral-sequence walk; offsets per leg (fraction of a cycle), duty factor
GAIT = {'hind_near': 0.0, 'fore_near': 0.25, 'hind_far': 0.5, 'fore_far': 0.75}
DUTY = 0.62
STRIDE = 0.46 * 132.0   # local px per cycle (0.46 m)
LIFT = 7.0

def solve(p):
    """p: dict with s (local px travelled forward, signed), crouch, lie, head, rest, look, tail, wag_phase, wag, hlook (0/1 head turned back over shoulder).
    returns dict piece -> (pivot_rest, pivot_new, angle) in local coords, plus feet world (local) positions."""
    lie, crouch = p['lie'], p['crouch']
    out = {}
    # torso: drops with crouch and lie; crouch tips the rump down a little
    drop = crouch * 9.0 + lie * 41.0 + 5.5 * min(1, p.get('moving', 0)) * (1 - lie) + 0.8 * p.get('breath', 0.0) * (1 - min(1, p.get('moving', 0)))
    pitch = math.radians(crouch * 5.0 * (1 - lie))   # positive = clockwise: front up / rump down for a left-facing dog
    tp = tuple(RIG['torso']['pivot'])
    tnew = (tp[0], tp[1] + drop)
    out['torso'] = (tp, tnew, pitch)
    T = lambda q: add(tnew, rot(sub(q, tp), pitch))   # torso-attached point → local
    # head: alert 0.9 → 0 deg; low head turns the nose down (counter-clockwise for a left-facing dog)
    hp = tuple(RIG['head']['pivot'])
    hv = p['head'] + 0.035 * p.get('idle', 0.0)
    h_down = (0.9 - hv) * 150.0 if hv < 0.9 else (0.9 - hv) * 40.0
    h_down = max(-12.0, min(78.0, h_down))
    look = p['look'] * lie
    h_down = h_down * (1 - look) + 0.0 * look          # looking in: muzzle level, pushed forward into the room
    rest = p['rest'] * lie
    h_down = h_down * (1 - rest) + 40.0 * rest         # chin down on the forepaws
    if lie > 0: h_down = h_down * (1 - 0.35 * lie * (1 - rest) * (1 - look))
    hang = -math.radians(h_down)
    hshift = (-13.0 * look - 6.0 * rest, 19.0 * rest - 3.0 * look)
    hshift = (hshift[0], hshift[1])
    hnew = add(T(hp), hshift)
    out['head'] = (hp, hnew, hang + pitch)
    # tail: 0.5 → as drawn; 1.35 tucked (clockwise = down for the tail, which is behind/right of the pivot)
    tlp = tuple(RIG['tail']['pivot'])
    tang = math.radians((p['tail'] - 0.5) * 58.0 + p['wag'] * 16.0 * math.sin(p['wag_phase']) - lie * 10)
    out['tail'] = (tlp, T(tlp), tang + pitch)
    feet = {}
    for leg in ['fore_far', 'hind_far', 'hind_near', 'fore_near']:
        P = RIG[leg]; hip0, knee0, foot0 = tuple(P['pivot']), tuple(P['knee']), tuple(P['foot'])
        l1, l2 = norm(sub(knee0, hip0)), norm(sub(foot0, knee0))
        hip = T(hip0)
        front = leg.startswith('fore')
        # standing / walking target: home under the hip, displaced by the gait; forward is -x
        u = (p['s'] / STRIDE + GAIT[leg]) % 1.0
        if u < DUTY:
            rel = STRIDE * (DUTY / 2 - u); lift = 0.0
        else:
            w = (u - DUTY) / (1 - DUTY)
            rel = STRIDE * DUTY * (-0.5 + w); lift = LIFT * math.sin(math.pi * w) * p.get('moving', 1)
        # rel is measured forward (toward the head): local x decreases forward
        tx = foot0[0] - rel
        ty = foot0[1] - lift
        bend = -1 if front else 1       # fore: joint forward; hind: hock back
        knee, foot = ik(hip, (tx, ty), l1, l2, bend)
        a_up = ang(sub(knee, hip)) - ang(sub(knee0, hip0))
        a_lo = ang(sub(foot, knee)) - ang(sub(foot0, knee0))
        if lie > 0:
            # lying: forelegs stretched forward along the floor (sphinx), hind legs folded under the haunch
            if front:
                la_up = math.radians(150.0); la_lo = math.radians(178.0)     # absolute directions (pointing forward-down / forward)
            else:
                la_up = math.radians(160.0); la_lo = math.radians(8.0)
            r_up = la_up - ang(sub(knee0, hip0)); r_lo = la_lo - ang(sub(foot0, knee0))
            # unwrap so the interpolation takes the short way
            r_up = a_up + ((r_up - a_up + math.pi) % (2 * math.pi) - math.pi)
            r_lo = a_lo + ((r_lo - a_lo + math.pi) % (2 * math.pi) - math.pi)
            a_up = lerp(a_up, r_up, lie); a_lo = lerp(a_lo, r_lo, lie)
            knee = add(hip, rot(sub(knee0, hip0), a_up)); foot = add(knee, rot(sub(foot0, knee0), a_lo))
        out[leg + '_up'] = (hip0, hip, a_up)
        out[leg + '_lo'] = (knee0, knee, a_lo)
        feet[leg] = foot
    return out, feet

def head_tip(sol):
    """the nose tip in local coords (for measuring where the head points)"""
    hp, hn, a = sol["head"]; nose = (87.0, 91.0)
    return add(hn, rot(sub(nose, hp), a))

def to_screen(q, O, f):
    return (O[0] + K * f * (q[0] - A[0]), O[1] + K * (q[1] - A[1]))

def draw_piece(canvas_ink, canvas_cov, name, pr, pn, a, O, f, extra_ink=0.0):
    """affine-map one cut piece onto the frame. canvas arrays are float HxW."""
    im = plate('dogL_' + name)
    org = META['pieces'][name]['origin']
    w, h = im.size
    # corners of the plate in local coords → screen bbox
    cs = []
    for (u, v) in [(0, 0), (w, 0), (0, h), (w, h)]:
        p = (org[0] + u / K, org[1] + v / K)
        q = add(pn, rot(sub(p, pr), a)); cs.append(to_screen(q, O, f))
    x0 = int(math.floor(min(c[0] for c in cs))) - 1; x1 = int(math.ceil(max(c[0] for c in cs))) + 1
    y0 = int(math.floor(min(c[1] for c in cs))) - 1; y1 = int(math.ceil(max(c[1] for c in cs))) + 1
    H, W = canvas_ink.shape
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if X1 <= X0 or Y1 <= Y0: return None
    # inverse: screen (X,Y) → local p = pr + rot(-a)( ( (X-O0)/(K f) + A0 , (Y-O1)/K + A1 ) - pn ) → plate u = (p - org) * K
    c, s = math.cos(-a), math.sin(-a)
    # local q from screen: qx = A0 + (X - O0)/(K f), qy = A1 + (Y - O1)/K   (X, Y measured from region origin X0, Y0)
    # p = pr + R(q - pn); u = K (p - org)
    ax = 1.0 / (K * f); ay = 1.0 / K
    qx0 = A[0] + (X0 - O[0]) * ax - pn[0]; qy0 = A[1] + (Y0 - O[1]) * ay - pn[1]
    # u = K*(pr.x - org.x + c*qx - s*qy), with qx = qx0 + ax*X, qy = qy0 + ay*Y
    ua = K * c * ax; ub = -K * s * ay; uc = K * (pr[0] - org[0] + c * qx0 - s * qy0)
    va = K * s * ax; vb = K * c * ay; vc = K * (pr[1] - org[1] + s * qx0 + c * qy0)
    reg = im.transform((X1 - X0, Y1 - Y0), Image.AFFINE, (ua, ub, uc, va, vb, vc), resample=Image.BICUBIC)
    arr = np.asarray(reg, np.float32) / 255.
    ink, cov = arr[..., 0], arr[..., 3]
    ink = np.clip(ink + extra_ink * cov, 0, 1)
    ci = canvas_ink[Y0:Y1, X0:X1]; cc = canvas_cov[Y0:Y1, X0:X1]
    canvas_ink[Y0:Y1, X0:X1] = np.clip(ci * (1 - cov) + ink, 0, 1)
    canvas_cov[Y0:Y1, X0:X1] = cc + cov * (1 - cc)
    return (X0, Y0, X1, Y1)

def draw_puppet(ink, cov, p, O, f, layers=None, headf=None, hc=None):
    """f = +1 left-facing (as scanned), -1 reversed impression. headf: draw the head with its own facing (turned back)."""
    sol, feet = solve(p)
    order = ['fore_far_lo', 'fore_far_up', 'hind_far_lo', 'hind_far_up', 'tail', 'torso', 'head',
             'hind_near_up', 'hind_near_lo', 'fore_near_up', 'fore_near_lo']
    for n in order:
        pr, pn, a = sol[n]
        if n == 'head' and headf is not None and headf != f:
            # head turned back over the shoulder: the head plate in its own facing, its pivot on the reversed body's neck
            neck = to_screen(pn, O, f)
            Oh = (neck[0] - K * headf * (pn[0] - A[0]), O[1])
            draw_piece(ink, cov, n, pr, pn, p.get('hback_a', math.radians(4)), Oh, headf)
            if hc is not None: draw_piece(hc[0], hc[1], n, pr, pn, p.get('hback_a', math.radians(4)), Oh, headf)
            continue
        if n == 'head' and p.get('rear'):
            # substitution: the back of the head (designed analog), the dog looking away from us into the room
            draw_piece(ink, cov, 'head_rear', pr, pn, a * 0.3, O, f)
            if hc is not None: draw_piece(hc[0], hc[1], 'head_rear', pr, pn, a * 0.3, O, f)
            continue
        if n == 'head' and hc is not None: draw_piece(hc[0], hc[1], n, pr, pn, a, O, f)
        draw_piece(ink, cov, n, pr, pn, a, O, f)
    joints = []
    for n in ['head', 'tail', 'fore_near_up', 'fore_near_lo', 'hind_near_up', 'hind_near_lo']:
        pr, pn, a = sol[n]
        joints.append((to_screen(pn, O, f), a, n))
    return sol, feet, joints

def draw_turn(ink, cov, f_scan, O, height_px):
    """a whole documented frame, scaled to the puppet's height, standing on the ground line at O."""
    im = plate('turn_f%03d' % f_scan)
    m = TURNM[str(f_scan)]
    bb = m['bbox_scan']; box = m['box']
    s = height_px / ((bb[3] - bb[1]) * K)
    w, h = im.size
    W, H = int(w * s), int(h * s)
    reg = im.resize((max(1, W), max(1, H)), Image.BICUBIC)
    # bottom of bbox on the ground, horizontal centre of bbox at O.x
    cx = ((bb[0] + bb[2]) / 2 - box[0]) * K * s; by = (bb[3] - box[1]) * K * s
    X0 = int(round(O[0] - cx)); Y0 = int(round(O[1] - by))
    arr = np.asarray(reg, np.float32) / 255.
    Hc, Wc = ink.shape
    xa, ya = max(0, X0), max(0, Y0); xb, yb = min(Wc, X0 + W), min(Hc, Y0 + H)
    sub_ = arr[ya - Y0:yb - Y0, xa - X0:xb - X0]
    i_, c_ = sub_[..., 0], sub_[..., 3]
    ink[ya:yb, xa:xb] = np.clip(ink[ya:yb, xa:xb] * (1 - c_) + i_, 0, 1)
    cov[ya:yb, xa:xb] = cov[ya:yb, xa:xb] + c_ * (1 - cov[ya:yb, xa:xb])
