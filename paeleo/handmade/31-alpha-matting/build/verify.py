"""Round 3 verification on the ENCODED film (not on the render): decode scene frames from film.mp4, render a plate of the
same frame without the dog (NODOG=1: same grain seeds, same shadows), and take |film - plate| as the dog's mask on screen.
Measures the five repair conditions and writes proof/round5_verify.json plus full-frame and cropped proof sheets.

python3 verify.py            (needs build/cache/render_trace.json from the render, and ../film.mp4)
"""
import json, os, subprocess, sys, wave
import numpy as np
os.environ['NODOG'] = '1'
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render
from lib_matte import blur
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, 'cache'); OUT = os.path.join(HERE, '..')
FILM = os.path.join(OUT, 'film.mp4')
W, H, GY = 1280, 720, render.GY
TR = json.load(open(os.path.join(C, 'render_trace.json')))
DIFF = None


def film_frames(i0, i1):
    """scene frames i0..i1-1 decoded from the film (film frame = scene frame + 72)"""
    a, b = i0 + 72, i1 + 72
    cmd = ['ffmpeg', '-loglevel', 'error', '-i', FILM, '-vf', 'select=between(n\\,%d\\,%d)' % (a, b - 1), '-vsync', '0',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(raw) // (W * H * 3)
    assert n == i1 - i0, (n, i0, i1)
    return np.frombuffer(raw, np.uint8).reshape(n, H, W, 3)


def mask_of(film, i):
    global DIFF
    plate, _, _ = render.render(i)
    d = np.abs(film.astype(np.int16) - plate.astype(np.int16)).max(2)
    DIFF = d
    m = d > 22
    # clean codec noise: keep pixels with at least 4 of 8 neighbours set
    p = np.pad(m, 1)
    nb = sum(p[1 + dy:H + 1 + dy, 1 + dx:W + 1 + dx].astype(np.int8) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    m = m & (nb >= 4)
    # only the dog's neighbourhood counts (its solid extent from the render trace, grown 40 px): codec noise and the
    # woman elsewhere in the frame are not the dog
    r = TR[str(i)]; pad = 40
    roi = np.zeros_like(m)
    roi[max(0, int(r['dog_top'] - pad)):int(r['dog_bottom'] + pad), max(0, int(r['dog_left'] - pad)):int(r['dog_right'] + pad)] = True
    return m & roi, plate


def head_point(m, facing, i=None):
    sol = m.copy(); sol[GY - 14:] = False
    if i is not None:     # tight horizontal margin: the woman's low hand comes within 40 px of the dog at the sill
        r = TR[str(i)]; sol[:, :max(0, int(r['dog_left'] - 8))] = False; sol[:, int(r['dog_right'] + 8):] = False
    cs = np.nonzero(sol.sum(0) > 0)[0]
    if len(cs) == 0:
        return None
    band = (np.arange(W) <= cs.min() + 45) if facing == 1 else (np.arange(W) >= cs.max() - 45)
    yy, xx = np.nonzero(sol & band[None, :])
    return float(xx.mean()), float(yy.mean())


def components(m):
    """connected pieces of a mask (4-neighbour BFS over set pixels only) -> list of sizes, largest first"""
    ys, xs = np.nonzero(m)
    seen = set(); sizes = []
    S = set(zip(ys.tolist(), xs.tolist()))
    for p in S:
        if p in seen: continue
        st = [p]; seen.add(p); n = 0
        while st:
            y, x = st.pop(); n += 1
            for q in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if q in S and q not in seen:
                    seen.add(q); st.append(q)
        sizes.append(n)
    return sorted(sizes, reverse=True)


def pieces_gap(m, min_px=4, rmax=12):
    """for each piece of >= min_px other than the largest: its gap to the largest piece in px (dilation steps), as (size, gap)"""
    ys, xs = np.nonzero(m)
    S = set(zip(ys.tolist(), xs.tolist())); seen = set(); P = []
    for p in S:
        if p in seen: continue
        st = [p]; seen.add(p); pts = []
        while st:
            y, x = st.pop(); pts.append((y, x))
            for q in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if q in S and q not in seen:
                    seen.add(q); st.append(q)
        P.append(pts)
    P.sort(key=len, reverse=True)
    if len(P) < 2:
        return []
    main = np.zeros_like(m); a = np.array(P[0]); main[a[:, 0], a[:, 1]] = True
    from lib_matte import dilate
    out = []
    for pts in P[1:]:
        if len(pts) < min_px: continue
        a = np.array(pts); g = None; d = main
        for r in range(1, rmax + 1):
            d = dilate(d, 1)
            if d[a[:, 0], a[:, 1]].any():
                g = r; break
        out.append((len(pts), g))
    return out


def paws_of(m, p, i):
    """film paw x for each gait leg pair: mean column of the lowest 4 mask rows within +-16 px of the render's paw"""
    out = {}
    for leg in ('fore', 'hind'):
        rows = m[GY - 10:GY + 5] if leg == 'fore' else m[GY - 30:GY + 5]    # the hind paws stand ~15 px higher
        L = p['legs'][leg]
        ex = L['paw_screen_x']
        x0, x1 = int(ex - 16), int(ex + 16)
        ys, xs = np.nonzero(rows[:, max(x0, 0):x1])
        if len(xs):
            # difference-weighted centroid of the paw's lowest rows (steadier than the binary mask's edge under codec noise)
            y0r = (GY - 10 if leg == 'fore' else GY - 30) + ys.max() - 5
            D = DIFF[y0r:y0r + 6, max(x0, 0):x1].astype(np.float32)
            w = np.clip(D - 12, 0, 60)
            cx = float((w.sum(0) * np.arange(w.shape[1])).sum() / max(w.sum(), 1e-6)) + max(x0, 0)
            out[leg] = dict(x=round(cx, 2), plant=L['plant'], planted=L['planted'], expected=ex)
    return out


def plant_stats(paws):
    drift = {}; per_plant = []; step = {}
    for leg, d in paws.items():
        ep = {}
        for i, v in sorted(d.items()):
            if v['planted']:
                ep.setdefault(v['plant'], []).append((i, v['x']))
        worst = 0.
        for pl, lst in ep.items():
            xs = [x for _, x in lst]
            if len(lst) >= 2:
                span = max(xs) - min(xs); worst = max(worst, span)
                per_plant.append(dict(leg=leg, plant=pl, frames=[lst[0][0], lst[-1][0]], n=len(lst), paw_x_range_px=round(span, 2)))
        drift[leg] = round(worst, 2)
        st = [abs(d[i]['x'] - d[i - 1]['x']) for i in sorted(d) if i - 1 in d]
        step[leg] = round(max(st), 2) if st else None
    return drift, per_plant, step


def lum(img):
    return img.astype(np.float32).mean(2) / 255.


def main():
    R = {}
    sheets = {}
    # ---------------- 1 + 5: the retreat (frames 20-60) and the sill (566-600): paws and head point from the film
    walk = film_frames(20, 61)
    heads = {}; paws = {'fore': {}, 'hind': {}}; ret_imgs = []
    for k, i in enumerate(range(20, 61)):
        m, _ = mask_of(walk[k], i)
        p = TR[str(i)]['pose']
        heads[i] = head_point(m, p.get('facing', 1), i)
        ret_imgs.append((i, walk[k]))
        if p.get('kind') == 'gait':
            for leg, v in paws_of(m, p, i).items():
                paws[leg][i] = v
    drift, per_plant, _ = plant_stats(paws)
    body = [TR[str(i)]['x_screen'] for i in range(20, 61)]
    R['1_retreat_planted_paws'] = dict(max_paw_x_range_while_planted_px=drift, plants=per_plant,
                                       body_travel_px=round(max(body) - min(body), 1),
                                       method='film mask = |film - no-dog plate| > 22/255; paw x = mean column of the lowest 4 mask rows within +-16 px of the render trace paw, rows GY-10..GY+4 (fore), GY-30..GY+4 (hind)')
    sill = film_frames(566, 601)
    for k, i in enumerate(range(566, 601)):
        m, _ = mask_of(sill[k], i)
        heads[i] = head_point(m, TR[str(i)]['pose'].get('facing', 1), i)
    def jumps(a, b):
        out = []
        for i in range(a + 1, b):
            if heads.get(i) and heads.get(i - 1):
                out.append((round(float(np.hypot(heads[i][0] - heads[i - 1][0], heads[i][1] - heads[i - 1][1])), 1), i))
        mx = max(out)
        return dict(max_jump_px=mx[0], at_frame=mx[1], at_s=round(mx[1] / 24, 3), per_frame={str(i): j for j, i in out})
    R['5_head_jumps_film'] = {'0.83-2.54s': jumps(20, 61), '23.58-25.0s': jumps(566, 601)}
    # whole film from the render trace (same head-point definition, measured on the composited matte)
    hp = [(TR[str(i)].get('head_x'), TR[str(i)].get('head_y')) for i in range(768)]
    jj = [(float(np.hypot(hp[i][0] - hp[i - 1][0], hp[i][1] - hp[i - 1][1])), i) for i in range(1, 768) if hp[i][0] is not None and hp[i - 1][0] is not None]
    R['5_head_jumps_render_all_frames'] = dict(over_30px=[(round(j, 1), i, round(i / 24, 3)) for j, i in jj if j > 30])
    # ---------------- 3: 9.0-10.2 s detached fragments
    wf = film_frames(216, 246); frag = []
    for k, i in enumerate(range(216, 246)):
        m, plate = mask_of(wf[k], i)
        sky = lum(plate) > .3          # only where a piece could be seen: against the sky (against the tree line the dark legs vanish into it)
        frag.append((i, pieces_gap((m & sky)[:GY - 2])))
    R['3_fragments_9.0-10.2s'] = dict(frames=len(frag), pieces_ge4px_size_and_gap_px=[(i, s) for i, s in frag if s], max_gap_px=max([g or 99 for _, s in frag for _, g in s] or [0]),
                                      method='4-connected pieces of the film mask where the backdrop is sky (plate luminance > 0.3); the dog is the largest; gap = px between a piece and the dog body (99 = more than 12 px)')
    # ---------------- 4: 26.5-28.3 s rim against the dark lower doorway, and ear-tip specks
    lf = film_frames(636, 680); rims = []; specks = []
    for k, i in enumerate(range(636, 680)):
        m, plate = mask_of(lf[k], i)
        L = lum(lf[k]); Lp = lum(plate)
        mf = m.astype(np.float32)
        inner = blur(mf, 3, 2) > .999                 # >= ~5 px inside the edge
        edge = m & ~(blur(mf, 1, 1) > .999)          # the outermost 1-2 px of the dog
        din = blur(inner.astype(np.float32), 5, 2); Lin = blur(L * inner, 5, 2) / np.maximum(din, 1e-4)
        out_ = ~m; dout = blur(out_.astype(np.float32), 4, 2); Lout = blur(Lp * out_, 4, 2) / np.maximum(dout, 1e-4)
        reg = np.zeros_like(m); reg[542:584, 245:415] = True     # the dark lower doorway
        e = edge & reg & (din > .02) & (dout > .02)
        Le = blur(L, 1, 1)
        rim = e & (Le > np.maximum(Lin, Lout) + .03)
        rims.append((i, int(e.sum()), int(rim.sum()), round(float(rim.sum()) / max(1, e.sum()), 3),
                     round(float((Le[e] - np.maximum(Lin, Lout)[e]).mean()) if e.sum() else 0., 4)))
        # ear tips: the top 20 rows of the dog in the doorway; a speck = a pixel brighter than the fur and the light behind it
        cols = np.nonzero(m[:, 245:415].any(0))[0]
        ys = np.nonzero(m[:, 245:415].any(1))[0]
        if len(ys):
            top = ys.min(); r2 = np.zeros_like(m); r2[top:top + 20, 245:415] = True
            sp = m & r2 & (L > np.maximum(Lin, Lout) + .08) & (din > .02)
            specks.append((i, int(sp.sum())))
    R['4_rim_lower_doorway_26.5-28.3s'] = dict(
        edge_px_total=sum(r[1] for r in rims), rim_px_total=sum(r[2] for r in rims),
        max_rim_share=max(r[3] for r in rims), mean_edge_minus_brighter_side=round(float(np.mean([r[4] for r in rims])), 4),
        per_frame=rims, method='edge = outermost 1-2 px of the film mask inside x245-415 y542-584; rim = edge luminance > max(fur 5 px in, plate backdrop outside) + 0.03')
    R['4_ear_tip_specks'] = dict(frames_with_specks=[s for s in specks if s[1] > 0], max_px=max(s[1] for s in specks))
    # ================= round 4 conditions
    # R4-1: 22.2-23.8 s, does the siding show through the dog? Siding line rows are darker in the plate; inside the dog
    # (film mask eroded 2 px) the same rows should be no darker than their neighbours. transfer = film line contrast inside
    # the dog / plate line contrast at the same pixels (about 1 - alpha)
    tr = {'solid': [], 'all': [], 'rear': [], 'legs': []}; sid_imgs = []; alpha_stats = []; feet = []
    yy = np.arange(H)[:, None] * np.ones((1, W))
    xx = np.ones((H, 1)) * np.arange(W)[None, :]
    wall = (xx < 596) & (yy < 584) & ~((xx >= 229) & (xx < 432) & (yy >= 181))   # siding, not the door or casing
    def hp(L):
        k_ = np.ones(9) / 9.
        return L - np.apply_along_axis(lambda c: np.convolve(c, k_, 'same'), 0, L)
    for a0 in range(528, 572, 22):
        b0 = min(a0 + 22, 572); FF = film_frames(a0, b0)
        for k, i in enumerate(range(a0, b0)):
            m, plate = mask_of(FF[k], i)
            # where the dog is: the render's own alpha placed on screen, EVERY pixel of it with alpha >= 0.3 (round 4: the
            # round 3 test used only alpha >= 0.95 and so never looked at the pale far hind leg)
            os.environ.pop('NODOG', None)
            pose_, Ps_, lft, tp, _ = render.dog_layer(i)
            os.environ['NODOG'] = '1'
            al = np.zeros((H, W), np.float32); X0, Y0 = int(round(lft)), int(round(tp)); hh, ww = Ps_.shape[:2]
            al[max(Y0, 0):Y0 + hh, max(X0, 0):X0 + ww] = Ps_[max(-Y0, 0):H - Y0, max(-X0, 0):W - X0, 3][:min(hh, H - max(Y0, 0)), :min(ww, W - max(X0, 0))]
            body = blur((al >= .3).astype(np.float32), 1, 1) > .999           # the dog less its outermost pixel
            # render-side alpha inside the dog (the condition itself): share of the dog's pixels below 0.95
            alpha_stats.append((i, round(float((al[body] < .95).mean()), 4), round(float(al[body].min()), 3)))
            xs_ = np.nonzero(body.any(0))[0]; xmid = (xs_.min() + xs_.max()) / 2.
            wl = render.ST['wall']; render.ST['wall'] = render.ST['wall_nolines']
            plate_nl, _, _ = render.render(i); render.ST['wall'] = wl
            hf = hp(lum(FF[k])); hpat = hp(lum(plate) - lum(plate_nl))
            solid = blur((al >= .95).astype(np.float32), 1, 1) > .999
            zones = {'solid': solid & wall, 'all': body & wall, 'rear': body & wall & (xx >= xmid), 'legs': body & wall & (yy >= 540)}
            for nm, zone in zones.items():
                den = float((hpat[zone] ** 2).sum())
                if zone.sum() > 30 and den > 0:
                    sh = np.roll(hpat, 11, 0)
                    tr[nm].append((i, round(float((hf[zone] * hpat[zone]).sum()) / den, 3), int(zone.sum()),
                                   round(float((hf[zone] * sh[zone]).sum()) / max(float((sh[zone] ** 2).sum()), 1e-9), 3)))
            # feet: the lowest solid row under each leg pair, in the render (alpha > 0.5) and on the film (mask)
            if pose_.get('kind') == 'gait':
                rec = dict(i=i)
                for leg in ('fore', 'hind'):
                    ex = pose_['legs'][leg]['paw_screen_x']
                    c0, c1 = int(ex - 16), int(ex + 16)
                    r_rows = np.nonzero((al[:, c0:c1] > .5).any(1))[0]; f_rows = np.nonzero(m[GY - 40:GY + 10, c0:c1].any(1))[0]
                    rec[leg + '_render_bottom'] = int(r_rows.max()) if len(r_rows) else None
                    rec[leg + '_film_bottom'] = int(f_rows.max() + GY - 40) if len(f_rows) else None
                    rec[leg + '_planted'] = pose_['legs'][leg]['planted']
                feet.append(rec)
            if i in (528, 534, 545, 552, 560, 570):
                sid_imgs.append((i, FF[k]))
    def summ(L):
        return dict(mean=round(float(np.mean([t[1] for t in L])), 3), max=max(t[1] for t in L), control_mean=round(float(np.mean([t[3] for t in L])), 3), frames=len(L)) if L else None
    floor = GY + 3
    hind_gap = [abs(f['hind_film_bottom'] - floor) for f in feet if f['hind_planted'] and f['hind_film_bottom'] is not None]
    hind_gap_r = [abs(f['hind_render_bottom'] - floor) for f in feet if f['hind_planted'] and f['hind_render_bottom'] is not None]
    level = [abs(f['hind_film_bottom'] - f['fore_film_bottom']) for f in feet if f['hind_planted'] and f['fore_planted'] and f['hind_film_bottom'] and f['fore_film_bottom']]
    R['r5_1_siding_through_dog_22.0-23.8s'] = dict(
        transfer={k: summ(v) for k, v in tr.items()},
        render_alpha_inside_dog=dict(max_share_below_095=max(t[1] for t in alpha_stats), min_alpha=min(t[2] for t in alpha_stats)),
        per_frame=tr, per_frame_alpha=alpha_stats,
        method='render alpha placed on screen; zones: all = alpha >= 0.3 less its outer pixel (includes any pale limb), solid = alpha >= 0.95, rear = rear half, legs = rows 540-583; transfer = regression of the film luminance vertical high-pass on the siding pattern (no-dog plate minus the same plate with unlined siding), ~ 1 - alpha; control = pattern shifted half a clapboard; validated at 1.01-1.04 outside the dog')
    R['r5_2_feet_on_floor_22.0-23.8s'] = dict(floor_line_y=floor, planted_hind_film_max_gap_px=max(hind_gap) if hind_gap else None,
                                              planted_hind_render_max_gap_px=max(hind_gap_r) if hind_gap_r else None,
                                              hind_vs_fore_film_max_px=max(level) if level else None, per_frame=feet,
                                              method='lowest row of the film mask / render alpha within +-16 px of each leg pair paw; floor line = GY+3')
    # R4-2: 7.38-7.79 s, the head coming round: the head piece placed by the render, and on the film the centroid of the
    # dog mask inside that piece's box (grown 6 px)
    lb = film_frames(177, 188); hp_r = {}; hp_f = {}; lb_imgs = []
    for k, i in enumerate(range(177, 188)):
        m, _ = mask_of(lb[k], i)
        h = TR[str(i)].get('headpiece')
        if h:
            hp_r[i] = (h['x'], h['y'])
            x0, y0, x1, y1 = [int(v) for v in h['box']]
            sub = m[max(0, y0 - 6):y1 + 6, max(0, x0 - 6):x1 + 6]
            ys, xs = np.nonzero(sub)
            if len(xs):
                hp_f[i] = (float(xs.mean() + max(0, x0 - 6)), float(ys.mean() + max(0, y0 - 6)))
        lb_imgs.append((i, lb[k]))
    def steps(d):
        return {str(i): round(float(np.hypot(d[i][0] - d[i - 1][0], d[i][1] - d[i - 1][1])), 1) for i in sorted(d) if i - 1 in d}
    sr, sf = steps(hp_r), steps(hp_f)
    R['kept_look_back_7.38-7.79s'] = dict(max_step_render_px=max(sr.values()), max_step_film_px=max(sf.values()),
                                         frames_head_moving=[int(i) for i, v in sr.items() if v > 3],
                                         steps_render=sr, steps_film=sf, bridge=[TR[str(i)]['pose'].get('bridge') for i in range(177, 188)],
                                         method='render: alpha centroid of the head piece on screen; film: centroid of the film mask inside that piece box grown 6 px')
    # R4-5: the approach on the gait: paws from the film, planted drift and the largest one-frame paw move
    apaws = {'fore': {}, 'hind': {}}; app_imgs = []
    for a0 in range(357, 572, 30):
        b0 = min(a0 + 30, 572); FF = film_frames(a0, b0)
        for k, i in enumerate(range(a0, b0)):
            p = TR[str(i)]['pose']
            if p.get('kind') != 'gait':
                continue
            m, _ = mask_of(FF[k], i)
            for leg, v in paws_of(m, p, i).items():
                apaws[leg][i] = v
            if i in (360, 420, 480, 540):
                app_imgs.append((i, FF[k]))
    ad, aplants, astep = plant_stats(apaws)
    held_changes = sum(1 for i in range(354, 572) if TR[str(i)]['pose'].get('kind') == 'frame' and TR[str(i - 1)]['pose'].get('kind') == 'frame'
                       and TR[str(i)]['pose'].get('f') != TR[str(i - 1)]['pose'].get('f'))
    R['kept_approach_feet'] = dict(held_drawing_changes_during_approach=held_changes, max_paw_x_range_while_planted_px=ad,
                                   max_paw_move_one_frame_px=astep, plants=len(aplants), worst_plants=sorted(aplants, key=lambda d: -d['paw_x_range_px'])[:4],
                                   method='as the retreat; one-frame move = largest |paw x(i) - paw x(i-1)| of either pair, planted or swinging')
    # R5-3: the standing-to-crouching hand-off at 23.79 -> 23.83: head point and hip (top of the back over the rear fifth),
    # from the film mask (ROI) and the render trace
    sw = film_frames(560, 586); hips = {}; hds = {}
    for k, i in enumerate(range(560, 586)):
        m, _ = mask_of(sw[k], i)
        r = TR[str(i)]; c0, c1 = int(r['dog_left']), int(r['dog_right']); wd = c1 - c0
        rc = range(c1 - int(.2 * wd), c1 + 1)
        tops = [np.nonzero(m[:GY - 2, c])[0].min() for c in rc if m[:GY - 2, c].any()]
        hips[i] = float(np.mean(tops)) if tops else None
        hds[i] = head_point(m, r['pose'].get('facing', 1), i)
    hip_steps = {str(i): round(hips[i] - hips[i - 1], 1) for i in range(561, 586) if hips[i] is not None and hips[i - 1] is not None}
    hd_steps = {str(i): round(float(np.hypot(hds[i][0] - hds[i - 1][0], hds[i][1] - hds[i - 1][1])), 1) for i in range(561, 586) if hds[i] and hds[i - 1]}
    rh = {str(i): round(TR[str(i)]['hip_y'] - TR[str(i - 1)]['hip_y'], 1) for i in range(561, 586) if TR[str(i)].get('hip_y') and TR[str(i - 1)].get('hip_y')}
    R['r5_3_lie_handoff_23.33-24.42s'] = dict(film_max_hip_drop_px=max(hip_steps.values()), film_max_head_step_px=max(hd_steps.values()),
                                              render_max_hip_drop_px=max(rh.values()), hip_steps_film=hip_steps, head_steps_film=hd_steps,
                                              swap_frame_571_572=dict(hip_drop_film=hip_steps.get('572'), head_step_film=hd_steps.get('572')),
                                              method='hip = mean top row of the film mask over the rear fifth of the dog; head = head point (45 px nearest the facing side)')
    # R5-5: the reach begins before the turn (render trace: the hand is drawn from the first frame with reach > 0.02)
    r0 = next(i for i in range(60, 120) if TR[str(i)].get('reach', 0) > .02)
    R['r5_5_reach'] = dict(first_reach_frame=r0, first_reach_s=round(r0 / 24, 3), lead_before_turn_3417_s=round(3.417 - r0 / 24, 3))
    rf = film_frames(72, 86)
    # ---------------- 2: sound, from the film's own AAC track
    wav = os.path.join(C, 'verify_audio.wav')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', FILM, '-ac', '1', '-ar', '48000', wav], check=True)
    with wave.open(wav) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    os.remove(wav)
    SR = 48000
    X = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); X[(f < 150) | (f > 1600)] = 0
    v = np.fft.irfft(X, len(a))
    hop = int(.01 * SR)
    e = np.array([np.sqrt((v[k:k + hop] ** 2).mean()) for k in range(0, len(v) - hop, hop)])
    edb = 20 * np.log10(e + 1e-9)
    base = np.median(edb[int(3.1 / .01):int(3.6 / .01)])
    lv = json.load(open(os.path.join(C, 'sound_levels.json')))
    marks = lv['marks_s']
    ons = {}
    for name, (t0, t1) in marks.items():
        lo, hi = int((t0 + 3 - .1) / .01), int((t1 + 3) / .01)
        seg = edb[lo:hi]
        k = next((j for j in range(len(seg)) if seg[j] > base + 12), None)
        s0 = None if k is None else round((lo + k) * .01 - 3, 2)
        rms = 20 * np.log10(np.sqrt((a[int((t0 + 3) * SR):int((t1 + 3) * SR)] ** 2).mean()) + 1e-12)
        ons[name] = dict(onset_scene_s=s0, rms_dBFS=round(float(rms), 2))
    ot = json.load(open(os.path.join(OUT, 'trace.json')))['onsets_measured']
    calls = [ons[k]['rms_dBFS'] for k in ons if k.startswith('call')]
    soft = [ons[k]['rms_dBFS'] for k in ons if k.startswith('soft') or k == 'come_in']
    R['2_sound_from_film'] = dict(voice=ons, reactions=dict(retreat_motion_starts=ot['retreat_motion_starts'], turn_choice=3.417,
                                                            turn_away_first_new_frame=ot['turn_away_first_new_frame'], look_back=ot['head_toward_door_again']),
                                  call_1_lead_s=round(ot['retreat_motion_starts'] - ons['call_1']['onset_scene_s'], 2),
                                  call_2_lead_before_turn_3417_s=round(3.417 - ons['call_2']['onset_scene_s'], 2),
                                  quietest_call_minus_loudest_soft_dB=round(min(calls) - max(soft), 2),
                                  soft_1_lead_before_look_back_7458_s=round(7.458 - ons['soft_1']['onset_scene_s'], 2),
                                  method='voice band 150-1600 Hz, 10 ms RMS; onset = first window 12 dB over the 3.1-3.6 s film-time floor')
    json.dump(R, open(os.path.join(OUT, 'proof/round5_verify.json'), 'w'), indent=1)
    # ---------------- proof sheets from the film: full frames and crops
    def sheet(items, box, sc, cols, path):
        ims = []
        for i, img in items:
            im = Image.fromarray(img).crop(box); im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
            ImageDraw.Draw(im).text((4, 4), 'scene %d %.3fs (film)' % (i, i / 24), fill=(255, 255, 0)); ims.append(im)
        w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
        s = Image.new('RGB', (w * cols, h * rows))
        for k, im in enumerate(ims): s.paste(im, ((k % cols) * w, (k // cols) * h))
        s.save(path, quality=88)
    P = os.path.join(OUT, 'proof')
    sheet(sid_imgs, (300, 400, 640, 610), 1.0, 3, os.path.join(P, 'r5_siding_22.0-23.8_crop.jpg'))
    for i, img in sid_imgs:      # the three moments the coordinator asked for, 2x
        if i in (534, 552, 570):
            sheet([(i, img)], (330, 420, 640, 620), 2.0, 1, os.path.join(P, 'r5_crop_%.2fs.jpg' % (i / 24)))
    sheet([(i, sw[i - 560]) for i in range(566, 578)], (250, 400, 620, 620), 1.0, 4, os.path.join(P, 'r5_lie_handoff_crop.jpg'))
    sheet([(i, rf[i - 72]) for i in range(72, 86, 2)], (150, 250, 560, 500), .8, 7, os.path.join(P, 'r5_reach_crop.jpg'))
    lie_fr = film_frames(150, 151)[0], film_frames(175, 176)[0], film_frames(600, 601)[0], film_frames(760, 761)[0]
    sheet([(150, lie_fr[0]), (175, lie_fr[1])], (940, 460, 1240, 615), 2.0, 2, os.path.join(P, 'r5_lying_refusal_shoulder_tail_2x.jpg'))
    sheet([(600, lie_fr[2]), (760, lie_fr[3])], (250, 460, 560, 615), 2.0, 2, os.path.join(P, 'r5_lying_sill_shoulder_tail_2x.jpg'))
    fa, fb = film_frames(89, 93), film_frames(193, 197)     # R4-4: the frontal turn frames, heads at 3x and full frame
    fr = [(89 + k, fa[k]) for k in range(4)] + [(193 + k, fb[k]) for k in range(4)]
    sheet(fr, (1010, 400, 1180, 520), 2.5, 4, os.path.join(P, 'r5_frontal_heads_crop.jpg'))
    sheet([fr[0], fr[2], fr[4], fr[6]], (0, 0, W, H), .4, 2, os.path.join(P, 'r5_frontal_full.jpg'))
    sheet(lb_imgs, (980, 400, 1250, 610), 1.0, 6, os.path.join(P, 'r5_look_back_crop.jpg'))
    sheet([lb_imgs[k] for k in (1, 3, 5, 7)], (0, 0, W, H), .4, 2, os.path.join(P, 'r5_look_back_full.jpg'))
    sheet(app_imgs, (0, 0, W, H), .4, 2, os.path.join(P, 'r5_approach_full.jpg'))
    sheet(ret_imgs[4:37:2], (760, 470, 1210, 615), 1.0, 3, os.path.join(P, 'r5_retreat_paws_crop.jpg'))
    sheet([ret_imgs[k] for k in (4, 12, 20, 28, 36)], (0, 0, W, H), .4, 3, os.path.join(P, 'r5_retreat_full.jpg'))
    sheet([(i, sill[i - 566]) for i in range(568, 578)], (200, 400, 600, 620), 1.0, 5, os.path.join(P, 'r5_sill_pop_crop.jpg'))
    sheet([(i, wf[i - 216]) for i in range(216, 246, 3)], (940, 380, 1240, 610), 1.0, 5, os.path.join(P, 'r5_watch_9.0-10.2_crop.jpg'))
    sheet([(i, lf[i - 636]) for i in (636, 645, 655, 665, 672, 679)], (280, 460, 440, 590), 3.0, 3, os.path.join(P, 'r5_lookin_rim_crop3x.jpg'))
    sheet([(i, lf[i - 636]) for i in (640, 660, 679)], (0, 0, W, H), .5, 3, os.path.join(P, 'r5_lookin_full.jpg'))
    print(json.dumps({k: (v if k.startswith('2') else {kk: vv for kk, vv in v.items() if kk not in ('per_frame', 'plants')} if isinstance(v, dict) else v) for k, v in R.items()}, indent=1, default=str)[:6000])


if __name__ == '__main__':
    main()
