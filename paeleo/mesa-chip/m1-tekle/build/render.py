#!/usr/bin/env python3
"""SCION-TEKLE · MESA CHIP, handmade. One window, cut once. No piece of glass moves for 24 s: every figure, every blow and every fallen
piece is light passing through fixed glass. Run: python3 render.py  (numpy, Pillow, scipy, ffmpeg)."""
import sys, os, json, math, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from common import *
from figures import *
sc = score(); rng = np.random.default_rng(1961)
WL, WR = sx(6.2) - 32, sx(6.2) + 32

# ---------- 1. the cutting: fixed for the whole film ----------
def cutting():
    # seeds: large pieces in the dune and the wall, small where the figures will pass (the glazier cuts knowing the story)
    pts = []
    while len(pts) < 4200:
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        band = 190 < y < FLOOR + 40 or (790 < x < 895 and 40 < y < SILL + 6)
        d = 8.5 if band else (12 if y > FLOOR else 20)
        if rng.uniform() < (8.5 / d) ** 2: pts.append((x, y))
    pts = np.array(pts); yy, xx = np.mgrid[0:H, 0:W]
    _, lab = cKDTree(pts).query(np.stack([xx.ravel(), yy.ravel()], 1)); lab = lab.reshape(H, W)
    lead = np.zeros((H, W), bool)
    lead[:, 1:] |= lab[:, 1:] != lab[:, :-1]; lead[1:, :] |= lab[1:, :] != lab[:-1, :]
    im = Image.new('L', (W, H)); d = ImageDraw.Draw(im)
    # the architecture is cut in lead: dune line, wall edge, window arch, sill, floor line, the steps, the mirror floor joints
    d.line([(0, 58), (180, 44), (400, 62), (640, 40), (960, 56)], 255, 4)
    d.line([(760, 58), (752, 200), (770, 430)], 255, 4)
    d.line([(WL, SILL), (WL, 78)], 255, 3); d.line([(WR, SILL), (WR, 78)], 255, 3); d.arc([WL, 46, WR, 110], 180, 360, 255, 3); d.line([(WL - 6, SILL + 2), (WR + 6, SILL + 2)], 255, 4)
    d.line([(0, FLOOR + 1), (W, FLOOR + 1)], 255, 3)
    d.line([(0, FLOOR - 60), (sx(-6.9), FLOOR - 60), (sx(-6.9), FLOOR - 30), (sx(-6.55), FLOOR - 30), (sx(-6.55), FLOOR)], 255, 3)
    for k in range(1, 5): d.line([(0, FLOOR + k * k * 4.2), (W, FLOOR + k * k * 4.2)], 255, 2)
    # calligraphic lead: sweeps over the dark nave, thick and thin, as Tekle draws with lead
    for k in range(7):
        x0 = 60 + k * 100; pts_ = [(x0 + 70 * math.sin(u * 3 + k) + u * 40, 66 + u * 120) for u in np.linspace(0, 1, 40)]
        for i in range(len(pts_) - 1): d.line([pts_[i], pts_[i + 1]], 255, int(2 + 4 * math.sin(math.pi * i / 39)))
    for k in range(3): d.arc([140 + k * 190, 70, 300 + k * 190, 200], 200, 340, 255, 3)
    for tk, who in ((2.0, 'mk'), (8.0, 'm'), (13.0, 'mk'), (17.0, 'm'), (23.5, 'm'), (6.8, 'k')):   # every held pose of each figure gets its own cut
        fr = sc['frames'][int(tk * FPS)]
        ops = (mesa(tk, fr, 1).ops if 'm' in who else []) + ([('poly', q, c, l) for _, q, c, l in knight_plates(knight_pose(tk, fr))] if 'k' in who else [])
        for op in ops:
            pm = Image.new('L', (W, H)); dd = ImageDraw.Draw(pm)
            if op[0] == 'cap':
                a, b, r = op[1], op[2], op[3]; dd.line([a, b], 255, int(2 * r)); dd.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], 255); dd.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], 255)
            elif op[0] == 'poly': dd.polygon(op[1], 255)
            else: cc, rx, ry = op[1], op[2], op[3]; dd.ellipse([cc[0] - rx, cc[1] - ry, cc[0] + rx, cc[1] + ry], 255)
            m_ = np.asarray(pm) > 0; edge = m_ & ~ndimage.binary_erosion(m_, iterations=2 if tk != 2.0 else 1)
            lead |= edge
    extra = np.asarray(im) > 0; lead |= extra
    cells, n = ndimage.label(~lead)
    # glass in each cell: a pot colour (jewel tones in the nave, ochres in the dune and wall, pale opal where the figures pass) and a body texture
    cy = ndimage.mean(yy, cells, np.arange(1, n + 1)); cx = ndimage.mean(xx, cells, np.arange(1, n + 1))
    jewels = np.array([(40, 70, 190), (30, 120, 170), (150, 30, 70), (30, 140, 90), (90, 50, 160), (30, 80, 160)], float)
    zone = ndimage.gaussian_filter(rng.normal(0, 1, (H // 8, W // 8)), 3); zone = (zone - zone.min()) / np.ptp(zone)
    tint = np.zeros((n + 1, 3)); kind = np.zeros(n + 1, int)
    for i in range(n):
        y, x = cy[i], cx[i]
        if y < 52: tint[i + 1] = (226, 150, 64) + rng.normal(0, 14, 3); kind[i + 1] = 1          # the dune
        elif x > 762 and not (WL < x < WR and 46 < y < SILL) and y < FLOOR: tint[i + 1] = (210, 120, 64) + rng.normal(0, 16, 3); kind[i + 1] = 2  # the canyon wall
        elif WL < x < WR and 46 < y < SILL: tint[i + 1] = (70, 110, 220) + rng.normal(0, 10, 3); kind[i + 1] = 3   # the window's own glass
        elif y > FLOOR: tint[i + 1] = (160, 180, 210) + rng.normal(0, 12, 3); kind[i + 1] = 4   # the mirror floor
        elif x < sx(-6.55) and y > FLOOR - 60: tint[i + 1] = (180, 130, 86) + rng.normal(0, 10, 3); kind[i + 1] = 5  # the steps
        elif y > 190: z = zone[int(y) // 8, int(x) // 8]; tint[i + 1] = (lerp(40, 70, z), lerp(80, 60, z), lerp(170, 200, z)) + rng.normal(0, 12, 3)  # the nave where they fight: one blue, many glasses
        else: z = zone[int(y) // 8, int(x) // 8]; tint[i + 1] = jewels[int(z * 5.99)] + rng.normal(0, 14, 3)
    tint = np.clip(tint, 0, 255)
    # body texture: thicker at the centre of each piece, streaked like antique glass
    dist = ndimage.distance_transform_edt(~lead); tex = .78 + .22 * np.clip(dist / 5, 0, 1)
    streak = ndimage.gaussian_filter(rng.normal(0, 1, (H, W)), (0.8, 6)); tex *= 1 + .06 * streak / streak.std()
    return cells, n, lead, tint, kind, tex.astype(np.float32), cx, cy

cells, NC, lead, tint, kind, tex, CX, CY = cutting()
_g = Image.new('L', (W, H)); _d = ImageDraw.Draw(_g)
for _, q, c, l in knight_plates(knight_pose(2.0, sc['frames'][48])): _d.polygon(q, 255)
GHOST = (np.asarray(_g) > 0).astype(np.float32)
WINF = np.zeros((H, W), np.float32); WINF[50:int(SILL), int(WL):int(WR)] = 1
print('cutting:', NC, 'pieces')
leadshade = np.clip(ndimage.gaussian_filter(lead.astype(np.float32), .7), 0, 1)[..., None]

# ---------- 2. the light timeline ----------
def backlight(t, fr):
    """background light field: deep nave, the dune glowing, columns coming down; the day curve rises then the last light moves on"""
    gain = .55 + .45 * ease(t / 5.0)
    yy = np.arange(H)[:, None]; xx = np.arange(W)[None, :]
    base = np.ones((H, W, 3), np.float32) * np.array([.85, .85, .9], np.float32)
    cols = np.zeros((H, W), np.float32)
    lx = sx(fr['light_x'])
    for cxk, wk, gk in ((lx, 46, 1.0), (180, 26, .45), (620, 30, .5), (430, 20, .35)):
        slant = cxk + (yy - 50) * .18
        cols += gk * np.exp(-((xx - slant) / wk) ** 2) * (yy > 50)
    if t > 20.5:
        cx_ = sx(lerp(-6.0, 0.5, ease((t - 20.5) / 3.5))); cols += 1.4 * np.exp(-((xx - cx_) / 70) ** 2) * (yy > FLOOR - 30) * ease((t - 20.5) / .8)
    light = base * gain + cols[..., None] * np.array([1.1, .95, .62], np.float32) * gain
    if t > 19.5: light = light + GHOST[..., None] * np.array([1.6, 1.3, .7], np.float32) * ease((t - 19.5) / 1.5)
    for p_ in sc['pieces']:   # the empty window answers every shot in its colour
        if p_['t'] <= t < p_['t'] + .8 and t > 5: light = light + WINF[..., None] * (np.array(hexrgb(p_['paint']), np.float32) / 255 * 1.8) * math.exp(-(t - p_['t']) / .3)
    return light

def paint_light(t, fr, pieces_state):
    """the light field (RGB 0..1 multipliers or colours) and the label field drawn by the figures"""
    L = Image.new('RGB', (W, H), (0, 0, 0)); M = Image.new('L', (W, H), 0)
    dl, dm = ImageDraw.Draw(L), ImageDraw.Draw(M)
    def draw(ops, mirror=False, dim=1.0):
        for op in ops:
            def P(p): return (p[0], FLOOR + 4 + (FLOOR - p[1]) * .32) if mirror else p   # the mirror floor, seen from above: the figure foreshortened in it
            c = tuple(int(v * dim) for v in op[-2]); lab = 0 if mirror else op[-1]
            if op[0] == 'cap':
                a, b, r = P(op[1]), P(op[2]), op[3]
                for d_, v in ((dl, c), (dm, lab)):
                    d_.line([a, b], v, int(2 * r)); d_.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], v); d_.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], v)
            elif op[0] == 'poly':
                q = [P(p) for p in op[1]]; dl.polygon(q, c); dm.polygon(q, lab)
            else:
                cc, rx, ry = P(op[1]), op[2], op[3]; bb = [cc[0] - rx, cc[1] - ry, cc[0] + rx, cc[1] + ry]; dl.ellipse(bb, c); dm.ellipse(bb, lab)
    # the window's glass label (so the window can be found in the picture)
    dm.rectangle([WL + 1, 78, WR - 1, SILL - 1], 3); dm.pieslice([WL + 1, 47, WR - 1, 109], 180, 360, 3)
    facing = -1 if fr['mesa']['state'] == 'walk' else 1
    m = mesa(t, fr, facing)
    kops = []
    if t < 19.5:
        P = knight_pose(t, fr); plates = knight_plates(P)
        for pid, q, c, lab in plates:
            if pid in pieces_state['freed_by'] and t >= pieces_state['freed_by'][pid][1]: continue
            kops.append(('poly', q, c, lab))
    # reflections in the mirror floor, then the fallen pieces, then the figures
    draw(m.ops, True, .55); draw(kops, True, .55)
    for (pid, shot, t0, q0, land, ang, col) in sorted(pieces_state['flying'], key=lambda p: -p[1]):   # the last shot's pieces lie under the earlier ones
        if t < t0: continue
        u = min(1, (t - t0) / .5); cx0 = np.mean([p[0] for p in q0]); cy0 = np.mean([p[1] for p in q0])
        X = lerp(cx0, land[0], u); Y = lerp(cy0, land[1], u * u) - 30 * math.sin(math.pi * u) * (1 - u)
        flat = lerp(1, .55, ease(u)); a = ang * u
        q = [rot(((p[0] - cx0) * 1.35 + X, (p[1] - cy0) * flat * 1.35 + Y), (X, Y), a) for p in q0]
        g = .72 + (.5 * math.exp(-((X - sx(lerp(-6.0, 0.5, ease((t - 20.5) / 3.5)))) / 70) ** 2) * ease((t - 20.5) / .8) if t > 20.5 else 0)
        dl.polygon(q, tuple(int(min(255, v * g)) for v in col)); dm.polygon(q, 10 + shot)
    draw(kops); draw(m.ops)
    return np.asarray(L).astype(np.float32) / 255, np.asarray(M)

# the pieces: every plate of the knight, and which shot frees it (the fractions are the score's, the order is this window's)
def pieces_plan():
    P = knight_pose(9.5, sc['frames'][int(9.5 * FPS)]); plates = knight_plates(P)
    shoulder = (P['X'] - 3 * S, FLOOR - 136 * S)
    d = np.array([math.hypot(np.mean([p[0] for p in q]) - shoulder[0], np.mean([p[1] for p in q]) - shoulder[1]) for _, q, _, _ in plates])
    first = list(np.argsort(d)); n = len(plates); k1 = int(round(.12 * n)); rest = first[k1:]; rng.shuffle(rest)
    order = first[:k1] + rest
    rel = releases(sc, n, order); freed_by = {}
    for shot, t, paint, ids in rel:
        for pid in ids: freed_by[int(pid)] = (shot, t, paint)
    return freed_by, n

freed_by, NPL = pieces_plan()
flying = []
def launch(t):
    fr = sc['frames'][min(len(sc['frames']) - 1, int(round(t * FPS)))]; P = knight_pose(t, fr); plates = knight_plates(P)
    for pid, q, c, lab in plates:
        if pid in freed_by and abs(freed_by[pid][1] - t) < 1e-6:
            shot, _, paint = freed_by[pid]; spread = 130 if shot == 5 else 46
            land = (np.mean([p[0] for p in q]) + rng.uniform(-spread, spread) * .6 - 16, FLOOR + 8 + rng.uniform(0, 1) ** 1.5 * (52 if shot == 5 else 30))
            flying.append((pid, shot, t, q, land, rng.uniform(-2, 2), hexrgb(paint)))
for p in sc['pieces']: launch(p['t'])
state = dict(freed_by=freed_by, flying=flying)

# ---------- 3. the frames ----------
def frame(f):
    t = f / FPS; fr = sc['frames'][f]
    BL = backlight(t, fr); Lf, Mf = paint_light(t, fr, state)
    # each piece of glass takes the light that most of it receives: the figure (crisp, by majority) or the backlight
    idx = cells.ravel() * 16 + Mf.ravel()
    cnt = np.bincount(idx, minlength=(NC + 1) * 16).reshape(NC + 1, 16)
    fig = Lf.reshape(-1, 3); bg = BL.reshape(-1, 3)
    maj = cnt.argmax(1); figcov = cnt[:, 1:].sum(1) / np.maximum(1, cnt.sum(1))
    sums = np.stack([np.bincount(idx, weights=fig[:, c], minlength=(NC + 1) * 16).reshape(NC + 1, 16) for c in range(3)], 2)
    lit_fig = sums[np.arange(NC + 1), maj] / np.maximum(1, cnt[np.arange(NC + 1), maj])[:, None]
    bgm = np.stack([ndimage.mean(bg[:, c].reshape(H, W), cells, np.arange(NC + 1)) for c in range(3)], 1)
    # the reflection is light too (label 0 but drawn): any figure light in a floor piece
    reflcov = np.bincount(cells.ravel(), weights=(fig.sum(1) > 0) & (Mf.ravel() == 0), minlength=NC + 1) / np.maximum(1, np.bincount(cells.ravel(), minlength=NC + 1))
    reflc = np.stack([np.bincount(cells.ravel(), weights=fig[:, c] * (Mf.ravel() == 0), minlength=NC + 1) for c in range(3)], 1) / np.maximum(1, np.bincount(cells.ravel(), weights=(fig.sum(1) > 0) & (Mf.ravel() == 0), minlength=NC + 1))[:, None]
    glass = tint / 255
    col = glass * bgm * .9                                   # backlight through the pot colour
    isfig = (maj > 0) & (maj != 3)
    col[isfig] = lit_fig[isfig] * (.86 + .14 * glass[isfig] / np.maximum(.2, glass[isfig].max(1, keepdims=True)))  # opal glass lit in the figure's colour
    refl = (~isfig) & (reflcov > .35) & (kind == 4)
    col[refl] = col[refl] * .35 + reflc[refl] * 1.1
    figcell = np.zeros(NC + 1, bool); figcell[isfig] = True; figcell[0] = False
    ring = np.zeros(NC + 1, bool); fm = figcell[cells]
    edge = ndimage.binary_dilation(fm, iterations=3) & ~fm & ~lead
    ring[np.unique(cells[edge])] = True; ring &= ~figcell; ring &= (kind != 4)
    col[ring] *= .22   # the light is stopped around a figure: dark glass draws its contour, whatever pose it is in
    col[0] = 0
    img = col[cells] * tex[..., None]
    img = img * (1 - leadshade) + leadshade * np.array([.09, .08, .075])
    rgb = np.clip(img * 255, 0, 255).astype(np.uint8)
    lab = maj[cells].astype(np.uint8); lab[lead] = 0
    return rgb, lab

# ---------- 4. sound: bells, a choir, glass ----------
def sound():
    buf = tl(24.0); r = np.random.default_rng(7)
    n = len(buf); tt = np.arange(n) / SR
    for f0, g in ((110, .5), (164.8, .35), (220, .3), (277.2, .18)):     # the choir: a held chord, breathing
        v = np.sin(2 * np.pi * f0 * tt + .6 * np.sin(2 * np.pi * 5.1 * tt)) * (.55 + .45 * np.sin(2 * np.pi * .11 * tt + f0))
        buf += g * .08 * v * np.clip(tt / 4, 0, 1) * np.clip((23.8 - tt) / 2, 0, 1)
    def bell(t, f, g=1.0): add(buf, t, chime(f, 4.0), .5 * g)
    bell(0.0, 98, .8); bell(3.0, 196, .5); add(buf, 4.5, chime(620, 1.2), .3)
    add(buf, 6.0, chime(1320, 1.4), .35)                                   # the sword
    add(buf, 6.5, noise(.05, r, .03), .4)                                  # the gun comes up
    notes = [784, 659, 880, 740, 988, 523]
    for i, p in enumerate(sc['pieces']):
        add(buf, p['t'], noise(.04, r, .02), .9)                           # the shot: a wet pop
        for k in range(4 if i < 5 else 16): add(buf, p['t'] + .02 + .05 * k + r.uniform(0, .04), chime(notes[i] * (1 + .5 * r.uniform()), 1.4), .25)
    bell(12.2, 73.4, 1.2); add(buf, 12.2, noise(.25, r, .12), .6)          # struck down
    bell(14.0, 146.8, .5); bell(22.0, 98, .9)
    write_wav(os.path.join(HERE, 'sound.wav'), buf)

if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
    sound(); meter = Meter(sc); film = Film(os.path.join(OUT, 'film.mp4')); still = set(int(round(s * FPS)) for s in STILL_T)
    for f in range(len(sc['frames'])):
        rgb, lab = frame(f); film.put(rgb)
        meter.frame(f, lab[::2, ::2], rgb)
        if f in still: Image.fromarray(rgb).save(os.path.join(OUT, 'stills', f'still_{f / FPS:04.1f}s.jpg'), quality=90)
        if f % 48 == 0: print('frame', f, flush=True)
    film.close(os.path.join(HERE, 'sound.wav'))
    rep = meter.report(); json.dump(rep, open(os.path.join(OUT, 'invariants.json'), 'w'), indent=1)
    json.dump(dict(swarm='SCION-TEKLE', pieces_of_glass=int(NC), knight_plates=NPL, frames=meter.rows), open(os.path.join(OUT, 'trace.json'), 'w'))
    contact(os.path.join(OUT, 'stills'), os.path.join(OUT, 'stills', 'contact.jpg'))
    print({k: (v['ok'] if isinstance(v, dict) else v) for k, v in rep.items()})
