"""SCION 08 · Sutherland — compose display files and rasterise them as a vector CRT.

Every frame is a display file (ordered strokes).  The display draws it spot by spot at a
fixed beam rate, so a long display file refreshes more slowly; at the instant a film frame is
captured, the spots the beam has just drawn are in their bright blue-white P7 flash and the
rest glow in the long yellow-green persistence.  Moving strokes leave a short persistence trail.
The trace (where the dog actually is on screen) is measured from the rasterised dog spots.
"""
import json, math, os, pickle, sys, subprocess
import numpy as np
from multiprocessing import Pool
import world as Wd
from world import (DF, Cam, cam_at, CAM0, SF, N_SCENE, TITLE_N, END_N, FPS, LEGS, UP, DOOR, SILL, LEAF_W,
                   build_dog, build_person, draw_world, draw_dog, draw_ears, draw_tail, draw_graph,
                   draw_person, draw_pins, draw_pen, draw_panel, voice_arcs, constraint_glyphs,
                   clip_poly, hatch, arc_pts, prompt_at, door_frame_pts, smooth, clamp, lerp, unit, Door)
from font import text_width

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..'))
W, H = 1280, 720
CLIP_Y = 543.0
BACK = np.array(['world', 'frame', 'light', 'door', 'dusk', 'glyph'])
BEAM_RATE = 150000.0      # spots per second
FLASH_TAU = 0.010         # s, the blue flash of a P7 spot
TRAIL = (0.26, 0.08)      # persistence of the previous two frames

S = None

def init():
    global S
    S = pickle.load(open(os.path.join(HERE, '_cache', 'solve.pkl'), 'rb'))
    S['dog'] = build_dog(SF[0]['dog']['x'])
    S['per'] = build_person(SF[0]['person']['x'])
    S['door'] = Door()
    sc = S['scene']
    S['hard_max_dog'] = max(f['dres']['hard_max'] for f in sc)
    S['hard_max_per'] = max(f['pres']['hard_max'] for f in sc)
    S['hard_max_door'] = max(f['doorres']['hard_max'] for f in sc)

# ----------------------------------------------------------------------------
def light_and_leaf(df, cam, fr, I=1.0):
    g = S['door'].g
    g.P[:] = fr['doorP']
    ang = fr['door_angle']
    openk = clamp((ang - Door.AJAR) / (Door.OPEN - Door.AJAR))
    Hb, Ht, Eb, Et = (g.p(n) for n in ('Hb', 'Ht', 'Eb', 'Et'))
    # interior light: the opening, clipped (Sutherland-Hodgman) to the side the leaf leaves open
    op = [cam.p((DOOR['x0'], SILL['h'], 0)), cam.p((DOOR['x1'], SILL['h'], 0)),
          cam.p((DOOR['x1'], DOOR['top'], 0)), cam.p((DOOR['x0'], DOOR['top'], 0))]
    a, b = cam.p(Eb), cam.p(Et)
    poly = clip_poly(op, a, b)
    left = cam.p((DOOR['x0'] + 0.01, 1.0, 0))
    test = clip_poly([left, (left[0] + 0.1, left[1]), (left[0], left[1] + 0.1)], a, b)
    if not test:
        poly = clip_poly(op, b, a)
    lamp = 0.30 + 0.55 * openk
    for (p, q) in hatch(poly, 4.0):
        df.line([p, q], I * lamp * 0.42, 'light')
    # light thrown out onto the porch boards
    ex = Eb[0]
    pool = [(DOOR['x0'], 0.0), (ex, 0.0), (ex + 1.15, 1.9), (DOOR['x0'] - 0.55, 1.9)]
    pool = clip_poly(pool, (-2.9, 1.0), (-2.9, 0.0))
    if openk > 0.01 or True:
        zz = 0.04
        while zz < 1.9:
            # horizontal span of the pool at depth zz
            xs = []
            for k in range(len(pool)):
                (x1, z1), (x2, z2) = pool[k - 1], pool[k]
                if (z1 <= zz < z2) or (z2 <= zz < z1):
                    xs.append(x1 + (zz - z1) * (x2 - x1) / (z2 - z1))
            if len(xs) >= 2:
                fall = (1 - zz / 1.9) ** 1.3
                df.line(cam.pa([[min(xs), 0.0, zz], [max(xs), 0.0, zz]]), I * (0.06 + 0.42 * openk) * fall, 'light')
            zz += 0.055
    # the leaf: a constrained rectangle on its hinge, with one panel and a knob
    df.line(cam.pa([Hb, Eb, Et, Ht]), I * 0.75, 'door')
    for u0, u1, v0, v1 in ((0.18, 0.82, 0.08, 0.45), (0.18, 0.82, 0.55, 0.92)):
        pts = []
        for (u, v) in ((u0, v0), (u1, v0), (u1, v1), (u0, v1), (u0, v0)):
            pts.append(Hb + (Eb - Hb) * u + (Ht - Hb) * v)
        df.line(cam.pa(pts), I * 0.35, 'door')
    hp = cam.p(S['door'].handle())
    df.line(arc_pts(hp, 3.2, 0, 2 * math.pi, 10), I * 0.9, 'door')
    return openk

def dusk(df, cam, I=1.0):
    m = cam.p((3.55, 2.05, -6))
    r = 15 * cam.S / 150
    df.line(arc_pts(m, r, math.radians(70), math.radians(290), 30), I * 0.8, 'dusk')
    df.line(arc_pts((m[0] - r * 0.42, m[1] - r * 0.1), r * 0.86, math.radians(62), math.radians(298), 26), I * 0.5, 'dusk')
    rng = np.random.RandomState(7)
    for k in range(14):
        x = rng.uniform(2.55, 6.4); y = rng.uniform(1.35, 2.5)
        if abs(x - 3.55) < 0.25 and abs(y - 2.05) < 0.25:
            continue
        df.dot(cam.p((x, y, -6)), I * rng.uniform(0.25, 0.7), 'dusk')

def set_graphs(fr):
    S['dog'].P[:] = fr['dogP']; S['dog'].side = fr['dog_side']
    S['per'].P[:] = fr['perP']; S['per'].side = np.array([0, 0, 1.0])

def gap_of(fr):
    if fr['hand_req'] is None:
        return 0.0
    return float(np.linalg.norm(fr['perP'][S['per'].idx['WrR']] - fr['hand_req']))

def compose_scene(df, i, cam, Iscale=1.0, panel=True, build=None):
    """build: None for the finished drawing, else dict(reveal, frame_pts, actors) for the title."""
    fr = S['scene'][i]
    t = fr['t']
    set_graphs(fr)
    dog, per = S['dog'], S['per']
    Lw = S['Lw']
    if build is None:
        draw_world(df, cam, Lw, I_scale=Iscale)
        constraint_glyphs(df, cam, 0.30 * Iscale)
    else:
        draw_world(df, cam, Lw, frame_pts=build['frame_pts'], I_scale=Iscale, reveal=build['reveal'])
    dusk(df, cam, Iscale * (1 if build is None else build['actors']))
    if build is not None and build['actors'] <= 0:
        return None
    A = 1.0 if build is None else build['actors']
    openk = light_and_leaf(df, cam, fr, Iscale * A)
    a = SF[i]['dog']['act']
    # the person (graph dim, outline bright)
    gI = 0.30 if build is None else 0.30 + 0.5 * (1 - A)
    draw_graph(df, cam, per, gI * Iscale, 'pgraph', skip=())
    mouth = draw_person(df, cam, per, Iscale * A)
    draw_pins(df, cam, fr['ppins'], 0.35 * Iscale)
    voice_arcs(df, cam, mouth, t, Iscale)
    # the dog: graph + attached outline
    draw_graph(df, cam, dog, 0.26 * Iscale * (1 if build is None else 1.5), 'dgraph')
    draw_tail(df, cam, dog, Iscale * A)
    draw_dog(df, cam, dog, fr['dog_f'], fr['dog_side'], Iscale * A)
    draw_ears(df, cam, dog, fr['dog_side'], a['ear'], Iscale * A)
    draw_pins(df, cam, fr['pins'], 0.32 * Iscale)
    if a['look'] > 0.25:
        Np_, Zp_ = dog.p('N'), dog.p('Z')
        eye = Np_ + (Zp_ - Np_) * 0.4
        tgt = eye + unit(Zp_ - Np_) * 0.25 + np.array([0, 0, -1.0]) * 2.2
        df.line(cam.pa([eye, tgt]), 0.55 * a['look'] * Iscale, 'glyph', dash=(2, 6))
    # goal markers set by the pen (diamonds), rubber band for an unsatisfiable goal
    for mk in (fr['sit_marker'] if t < 7.5 else None, fr['hand_marker'] if 6.85 <= t < 8.5 else None):
        if mk is not None:
            c = cam.p(mk)
            df.line([(c[0], c[1] - 6), (c[0] + 6, c[1]), (c[0], c[1] + 6), (c[0] - 6, c[1]), (c[0], c[1] - 6)], 0.55 * Iscale, 'glyph')
    gap = gap_of(fr)
    if gap > 0.04:
        hand = cam.p(fr['perP'][per.idx['WrR']])
        df.line([hand, cam.p(fr['hand_req'])], 0.8 * Iscale, 'glyph', dash=(5, 5))
    if build is None and fr['mode'] != 'idle' or (build is None and np.linalg.norm(fr['pen'] - Wd.PARK) > 0.05):
        draw_pen(df, cam.p(fr['pen']), fr['mode'], Iscale)
    elif build is None:
        draw_pen(df, cam.p(fr['pen']), 'idle', 0.5 * Iscale)
    if panel:
        nd = len(dog.names); md = len(dog.hard)
        npn = len(per.names); mp = len(per.hard)
        dres, pres = fr['dres'], fr['pres']
        lines = [
            ('DOG     %2d POINTS  %2d CONSTRAINTS  RELAXATION %3d PASSES  MAX |E| %5.2f MM' % (nd, md, dres['iters'], dres['hard_max'] * 1000), 0.55),
            ('PERSON  %2d POINTS  %2d CONSTRAINTS  RELAXATION %3d PASSES  MAX |E| %5.2f MM' % (npn, mp, pres['iters'], pres['hard_max'] * 1000), 0.55),
        ]
        rel = []
        if gap > 0.04:
            rel.append(('HAND GOAL UNSATISFIABLE: ARM AT FULL LENGTH, GAP %.2f M' % gap, 1.0 if int(t * 4) % 2 == 0 else 0.6))
            if np.linalg.norm(fr['pen'] - fr['dogP'][dog.idx['N']]) < 0.9:
                rel.append(('THE DOG IS NOT SELECTABLE', 0.8))
        else:
            ang = math.degrees(fr['door_angle'])
            dog_rel = 'DOG: %d PAWS HELD-TO FLOOR' % len(fr['pins'])
            if a['look'] > 0.25:
                dog_rel = 'DOG: LOOKING IN, ALIGNED-WITH THE DOOR AXIS'
            elif a['lie'] > 0.5:
                xs = fr['dogP'][:, 0]
                inside = DOOR['x0'] < xs.min() < DOOR['x1']
                dog_rel = 'DOG: LYING, SUPPORTED-ON SILL AND PORCH' if (inside and fr['dogP'][:, 0].mean() < 1.0) else 'DOG: LYING, SUPPORTED-ON PORCH'
            rel.append((dog_rel + '   DOOR: HINGED-TO FRAME AT %2d DEG' % round(ang), 0.42))
        pr = prompt_at(t)
        if pr is not None and t - pr[0] > 5.0:
            pr = (t, '')
        draw_panel(df, t, fr['op'] if fr['mode'] in ('point', 'drag') else None, pr, lines + rel)
    return openk

def frame_pts_title(k):
    """The door frame drawn crooked, then relaxed square by its constraints, one pass per frame."""
    rng = np.random.RandomState(3)
    fp = door_frame_pts()
    crook = fp + np.c_[rng.uniform(-0.32, 0.32, 4), rng.uniform(-0.3, 0.3, 4), np.zeros(4)]
    P = crook.copy()
    x0, x1, top, h = DOOR['x0'], DOOR['x1'], DOOR['top'], SILL['h']
    errs = []
    for it in range(k):
        # sill on the floor line; jambs vertical (perpendicular to the sill); head parallel; equal jambs; width 0.92
        P[0, 1] += 0.11 * (h - P[0, 1]); P[3, 1] += 0.11 * (h - P[3, 1])
        mx = (P[0, 0] + P[1, 0]) / 2; P[0, 0] += 0.11 * (mx - P[0, 0]); P[1, 0] += 0.11 * (mx - P[1, 0])
        mx = (P[2, 0] + P[3, 0]) / 2; P[2, 0] += 0.11 * (mx - P[2, 0]); P[3, 0] += 0.11 * (mx - P[3, 0])
        my = (P[1, 1] + P[2, 1]) / 2; P[1, 1] += 0.11 * (my - P[1, 1]); P[2, 1] += 0.11 * (my - P[2, 1])
        Lj = ((P[1, 1] - P[0, 1]) + (P[2, 1] - P[3, 1])) / 2
        P[1, 1] += 0.11 * ((top - h) - Lj) * 0.5; P[2, 1] += 0.11 * ((top - h) - Lj) * 0.5
        wdt = P[3, 0] - P[0, 0]; c = (P[3, 0] + P[0, 0]) / 2
        for j in (0, 1):
            P[j, 0] += 0.11 * ((c - 0.46) - P[j, 0])
        for j in (2, 3):
            P[j, 0] += 0.11 * ((c + 0.46) - P[j, 0])
        cc = (P[:, 0].mean()); P[:, 0] += 0.11 * (0.0 - cc)
    err = float(np.abs(P - fp).max())
    return P, err

def compose(n):
    df = DF()
    if n < TITLE_N:
        k = n
        cam = CAM0
        tI = clamp(1.0 - (k - 50) / 18) if k > 50 else 1.0
        title = 'PAE-02 · SCION 08 · IVAN SUTHERLAND'
        sub = 'CONSTRAINT SKETCHPAD — THE THRESHOLD'
        nt = int(clamp(k / 26) * len(title)); ns = int(clamp((k - 18) / 20) * len(sub))
        w = text_width(title, 26); df.text(title[:nt], 640 - w / 2, 300, 26, 1.0 * tI, 'text')
        w2 = text_width(sub, 13); df.text(sub[:ns], 640 - w2 / 2, 340, 13, 0.8 * tI, 'text')
        reveal = int(clamp((k - 24) / 30) * len(S['Lw']))
        fpk = max(0, k - 30)
        fp, err = frame_pts_title(fpk)
        act = clamp((k - 52) / 16)
        if k >= 24:
            compose_scene(df, 0, cam, 0.85, panel=False, build=dict(reveal=reveal, frame_pts=fp, actors=act))
            if 30 <= k < 70:
                df.text('RELAX DOOR FRAME  ∥ ⊥ =   MAX |E| %4.0f MM' % (err * 1000), 40, 600, 11, 0.7, 'text')
        return df, None
    if n < TITLE_N + N_SCENE:
        i = n - TITLE_N
        t = SF[i]['t']
        compose_scene(df, i, cam_at(t), 1.0)
        return df, i
    k = n - TITLE_N - N_SCENE
    fade = clamp(1 - k / 12)
    if fade > 0:
        compose_scene(df, N_SCENE - 1, cam_at(SF[-1]['t']), fade, panel=False)
    sc = S['scene']
    hm = max(S['hard_max_dog'], S['hard_max_per'], S['hard_max_door'])
    dog, per = S['dog'], S['per']
    lines = [
        ('MADE OF', 20, 1.0),
        ('POINTS, LINES AND ARCS ON A SIMULATED VECTOR DISPLAY (P7 PHOSPHOR, DRAWN IN DISPLAY-FILE ORDER)', 11, 0.8),
        ('DOG: %d-POINT CONSTRAINT GRAPH, PROPORTIONS MEASURED FROM %d RIG KEYS OF A REAL DOG' % (len(dog.names), Wd.N_KEYS), 11, 0.8),
        ('   IN AMATEUR FILM NEW JERSEY C (HOME MOVIES, INTERNET ARCHIVE, PUBLIC DOMAIN)', 11, 0.65),
        ('PERSON: %d-POINT GRAPH  ·  DOOR: HINGE + EQUAL DIAGONALS  ·  ALL SOLVED BY RELAXATION' % len(per.names), 11, 0.8),
        ('WORST HARD-CONSTRAINT ERROR IN THE SCENE: %.2f MM  ·  THE DOG\'S CHOICES: THE PAELEO SCORE' % (hm * 1000), 11, 0.8),
        ('THE PROMPTS PERFORMED AS LIGHT-PEN DRAGS  ·  THE DOG IS NEVER DRAGGED', 11, 0.8),
        ('SOUND: SYNTHESIZED (MACHINE ROOM, DISPLAY HUM, PEN, VOICE TONES, PAWS)', 11, 0.8),
    ]
    y = 190
    for s, sz, I in lines:
        nn = int(clamp((k - 6) / 14) * len(s))
        df.text(s[:nn], 80, y, sz, I, 'text')
        y += 2.6 * sz + 14
    df.text('PAE-02 · SCION 08 · IVAN SUTHERLAND', 80, 640, 10, 0.4 * clamp((k - 6) / 10), 'text')
    return df, None

# ----------------------------------------------------------------------------
def spots(df):
    xs, ys, Is, tg = [], [], [], []
    for it in df.items:
        kind, pts, I, tag, extra = it
        if kind == 'dot':
            xs.append(pts[:, 0]); ys.append(pts[:, 1]); Is.append(np.array([I * 1.6], np.float32)); tg.append([tag])
            continue
        d = np.diff(pts, axis=0)
        L = np.sqrt((d ** 2).sum(1))
        tot = L.sum()
        if tot < 1e-3:
            continue
        n = max(2, int(tot / 1.25) + 1)
        s = np.linspace(0, tot, n)
        cum = np.concatenate([[0], np.cumsum(L)])
        k = np.clip(np.searchsorted(cum, s, side='right') - 1, 0, len(L) - 1)
        u = (s - cum[k]) / np.maximum(L[k], 1e-9)
        px = pts[k, 0] + d[k, 0] * u; py = pts[k, 1] + d[k, 1] * u
        if extra:
            on, off = extra
            m = (s % (on + off)) < on
            px, py, s = px[m], py[m], s[m]
        xs.append(px); ys.append(py); Is.append(np.full(len(px), I * 0.5, np.float32)); tg.append([tag] * len(px))
    if not xs:
        return np.zeros(0), np.zeros(0), np.zeros(0), []
    tags = np.array([t for l in tg for t in l])
    x, y, I = np.concatenate(xs), np.concatenate(ys), np.concatenate(Is)
    # window clipping: the drawing lives above the console line
    keep = (tags == 'text') | (y < CLIP_Y)
    # hidden lines: strokes of the house, door and light behind a body are not drawn
    back = np.isin(tags, BACK)
    for poly in df.occ:
        poly = np.asarray(poly, float)
        x0, y0 = poly.min(0); x1, y1 = poly.max(0)
        cand = np.where(back & keep & (x > x0) & (x < x1) & (y > y0) & (y < y1))[0]
        if len(cand) == 0:
            continue
        inside = np.zeros(len(cand), bool)
        px, py = x[cand], y[cand]
        for k in range(len(poly) - 1):
            ax, ay = poly[k]; bx, by = poly[k + 1]
            if ay == by:
                continue
            c = ((ay > py) != (by > py)) & (px < ax + (py - ay) * (bx - ax) / (by - ay))
            inside ^= c
        keep[cand[inside]] = False
    return x[keep], y[keep], I[keep], list(tags[keep])

def splat(x, y, w):
    buf = np.zeros(H * W, np.float32)
    m = (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1)
    x, y, w = x[m], y[m], w[m]
    x0 = np.floor(x).astype(np.int64); y0 = np.floor(y).astype(np.int64)
    fx = (x - x0).astype(np.float32); fy = (y - y0).astype(np.float32)
    base = y0 * W + x0
    for off, ww in ((0, (1 - fx) * (1 - fy)), (1, fx * (1 - fy)), (W, (1 - fx) * fy), (W + 1, fx * fy)):
        buf += np.bincount(base + off, weights=w * ww, minlength=H * W).astype(np.float32)
    return buf.reshape(H, W)

def box(a, r, axis):
    c = np.cumsum(a, axis=axis, dtype=np.float32)
    pad = [(0, 0), (0, 0)]; pad[axis] = (r + 1, r)
    c = np.pad(c, pad, mode='edge')
    if axis == 0:
        c[:r + 1] = 0
        out = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
    else:
        c[:, :r + 1] = 0
        out = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
    return out

def blur(a, r, passes=2):
    for _ in range(passes):
        a = box(box(a, r, 0), r, 1)
    return a

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = None

def vignette():
    global VIG
    if VIG is None:
        nx = (XX - W / 2) / (W / 2); ny = (YY - H / 2) / (H / 2)
        r = np.sqrt((nx * 0.92) ** 2 + (ny * 1.0) ** 2)
        v = np.clip(1.15 - 0.45 * r ** 2.4, 0, 1)
        # rounded CRT mask
        ex = np.clip((np.abs(nx) - 0.965) / 0.02, 0, 1); ey = np.clip((np.abs(ny) - 0.955) / 0.03, 0, 1)
        mask = 1 - np.clip(np.sqrt(ex ** 2 + ey ** 2), 0, 1)
        VIG = (v * mask).astype(np.float32)
    return VIG

def raster(n, t_capture):
    df, i = compose(n)
    x, y, I, tags = spots(df)
    N = len(x)
    # the beam position at the capture instant: recent spots flash
    if N:
        b = (t_capture * BEAM_RATE) % N
        age = ((b - np.arange(N)) % N) / BEAM_RATE
        flash = np.exp(-age / FLASH_TAU).astype(np.float32)
    else:
        flash = np.zeros(0, np.float32)
    rng = np.random.RandomState(n)
    jx = x + rng.normal(0, 0.18, N); jy = y + rng.normal(0, 0.18, N)
    Ep = splat(jx, jy, I)
    Ef = splat(jx, jy, I * flash)
    # persistence of the two previous frames (moving strokes leave a trail)
    for k, wgt in enumerate(TRAIL):
        if n - 1 - k >= 0:
            dfp, _ = compose(n - 1 - k)
            xp, yp, Ip, _ = spots(dfp)
            Ep += splat(xp, yp, Ip * wgt)
    meas = None
    if i is not None:
        tg = np.array(tags)
        m = (tg == 'dog')
        if m.any():
            dx, dy, dI = x[m], y[m], I[m]
            cam = cam_at(SF[i]['t'])
            jl = cam.p((DOOR['x0'], 0, 0))[0]; jr = cam.p((DOOR['x1'], 0, 0))[0]
            inside = ((dx > jl) & (dx < jr)).mean()
            meas = dict(cx=float((dx * dI).sum() / dI.sum()), cy=float((dy * dI).sum() / dI.sum()),
                        xmin=float(dx.min()), xmax=float(dx.max()), ymin=float(dy.min()), ymax=float(dy.max()),
                        frac_in_frame=float(inside), jamb_l=float(jl), jamb_r=float(jr), spots=int(N),
                        S=cam.S, xc=cam.xc, px=cam.px)
    return Ep, Ef, meas, N

CF = np.array([0.78, 0.90, 1.0], np.float32)
CP = np.array([0.50, 1.0, 0.42], np.float32)

def render_frame(n):
    t_cap = n / FPS + 0.0137
    Ep, Ef, meas, N = raster(n, t_cap)
    def glow(E):
        core = blur(E, 1, 1)
        halo = blur(E, 3, 2)
        small = E.reshape(H // 4, 4, W // 4, 4).mean((1, 3))
        bloom = blur(small, 4, 2)
        bloom = np.repeat(np.repeat(bloom, 4, 0), 4, 1)
        return core * 1.0 + halo * 0.9 + bloom * 1.4
    gp = glow(Ep); gf = glow(Ef)
    rgb = gp[..., None] * CP * 1.05 + gf[..., None] * CF * 1.0
    rng = np.random.RandomState(1000 + n)
    rgb += (0.010 + 0.004 * rng.rand(H, W).astype(np.float32))[..., None] * np.array([0.6, 1.0, 0.7], np.float32)
    rgb = 1 - np.exp(-rgb * 1.7)
    rgb *= vignette()[..., None]
    img = (np.clip(rgb, 0, 1) ** (1 / 1.15) * 255).astype(np.uint8)
    return n, img.tobytes(), meas, N

def main():
    nframes = TITLE_N + N_SCENE + END_N
    only = None
    if len(sys.argv) > 1 and sys.argv[1] == 'stills':
        only = [int(a) for a in sys.argv[2:]]
    init()
    if only is not None:
        from PIL import Image
        for n in only:
            _, b, meas, N = render_frame(n)
            Image.frombytes('RGB', (W, H), b).save(os.path.join(HERE, '_cache', 'f%04d.png' % n))
            print(n, N, meas)
        return
    tmp = os.path.join(HERE, '_cache', 'video.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                           '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    meas_all = {}
    counts = []
    with Pool(4, initializer=init) as pool:
        for n, b, meas, N in pool.imap(render_frame, range(nframes), chunksize=4):
            ff.stdin.write(b)
            counts.append(N)
            if meas is not None:
                meas_all[n - TITLE_N] = meas
            if n % 48 == 0:
                print('frame', n, 'spots', N, flush=True)
    ff.stdin.close(); ff.wait()
    json.dump({'meas': meas_all, 'spot_counts': counts}, open(os.path.join(HERE, '_cache', 'render_meas.json'), 'w'))
    print('rendered', nframes)

if __name__ == '__main__':
    main()
