"""Render Sh4 frames (global frame f, t = f/24, f = 663..839), the Sh5 RGBA pellet layer (f = 840..911),
measurements, phase visualizer and the locked/detuned A/B.
usage: python3 render.py sh4 <worker> <nworkers> | sh5 | measure | ab | phase
"""
import sys, json, math
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import trees as T
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/harmonic-trees-to-granule-camera-unit-c-sh4-sh5-falling-pellets-")
SW = Path("/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene")
F_SH4 = (663, 839)
F_SH5 = (840, 911)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def u8(im): return (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)
def save(p, im): cv2.imwrite(str(p), cv2.cvtColor(im, cv2.COLOR_RGB2BGR))

def sh4(worker, nw):
    d = OUT / "sh4"; d.mkdir(parents=True, exist_ok=True)
    for f in range(F_SH4[0] + worker, F_SH4[1] + 1, nw):
        im, _ = T.frame(f / 24.0)
        save(d / f"f{f:04d}.png", u8(im))

def all_trees(): return T.FRONT_T + T.BACK_T

def align_metric(t, detune):
    """max over all trees i, levels k of |theta_ik(t)| (deg) and RMS pellet orbit displacement (px)"""
    mth = max(abs(math.degrees(tr.theta(k, t, detune))) for tr in all_trees() for k in range(1, tr.K + 2))
    ds = []
    for tr in T.FRONT_T:
        if t < tr.t_cut(): continue
        for p in tr.pellets:
            d, e = T.pellet_disp(p, tr, t, detune); ds.append(float(np.hypot(*d)))
    return mth, (float(np.sqrt(np.mean(np.square(ds)))) if ds else 0.0)

def measure():
    res = {}
    for name, dt in (("locked", 0.0), ("detuned", 1.0)):
        ts = np.arange(32.8, 34.4, 1 / 240)
        m = np.array([align_metric(t, dt) for t in ts])
        i = int(np.argmin(m[:, 0] + m[:, 1]))
        res[name] = dict(at_33_60=dict(max_abs_theta_deg=round(align_metric(33.6, dt)[0], 6),
                                       rms_pellet_disp_px=round(align_metric(33.6, dt)[1], 6)),
                         best_alignment_t=round(float(ts[i]), 4), best_max_theta_deg=round(float(m[i, 0]), 5),
                         best_rms_disp_px=round(float(m[i, 1]), 4),
                         at_32_60=dict(max_abs_theta_deg=round(align_metric(32.6, dt)[0], 3), rms_pellet_disp_px=round(align_metric(32.6, dt)[1], 2)))
    # independent check: phase of every oscillator at 33.6 wrapped to (-pi, pi]
    ph = []
    for tr in all_trees():
        for k in range(1, tr.K + 2):
            x = k * tr.n * T.OMEGA * (33.6 - T.T_IN); ph.append(abs((x + math.pi) % (2 * math.pi) - math.pi))
    res["locked"]["max_wrapped_phase_rad_at_33_60"] = float(max(ph))
    # alignment frame: 33.60 s = frame 806.4 -> nearest rendered frames 806 (33.583) and 807 (33.625)
    res["frames"] = {"806": dict(t=806 / 24, max_theta_deg=round(align_metric(806 / 24, 0)[0], 4), rms_disp_px=round(align_metric(806 / 24, 0)[1], 3)),
                     "807": dict(t=807 / 24, max_theta_deg=round(align_metric(807 / 24, 0)[0], 4), rms_disp_px=round(align_metric(807 / 24, 0)[1], 3))}
    (SW / "harmonic-build" / "measure.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))

def phase_png():
    """phase visualizer: rows = oscillators (tree i, level k), x = time 27.6-35.0; colour = sin(phase) (warm +, blue -);
    right panel: phase wheels at 33.60 s, locked vs detuned; bottom: alignment metric vs time."""
    Wd, rowh = 1500, 9
    osc = [(tr, k) for tr in all_trees() for k in range(1, tr.K + 2)]
    Hh = 70 + rowh * len(osc) + 220
    img = Image.new("RGB", (Wd, Hh), (8, 8, 10)); d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 13); fs = ImageFont.truetype(FONT, 10)
    x0, x1 = 150, 1050
    tx = lambda t: x0 + (t - T.T_IN) / (T.T_OUT - T.T_IN) * (x1 - x0)
    d.text((10, 10), "Whitney oscillator bank, le-chant-du-styrene Sh4: theta_ik(t) = A_k env(t) sin(k n_i (2pi/6 s)(t - 27.60)); rows = tree i, level k", fill=(220, 215, 200), font=f)
    d.text((10, 30), "colour = sin(phase): amber +, blue -, black 0.  All columns go black together at 27.60 and 33.60 s (locked).", fill=(170, 165, 150), font=f)
    ts = np.linspace(T.T_IN, T.T_OUT, x1 - x0)
    for r, (tr, k) in enumerate(osc):
        y = 60 + r * rowh
        v = np.sin(k * tr.n * T.OMEGA * (ts - T.T_IN))
        col = np.where(v[:, None] > 0, v[:, None] * np.array([235, 160, 50]), -v[:, None] * np.array([40, 90, 210])).astype(np.uint8)
        strip = np.repeat(col[None], rowh - 2, 0)
        img.paste(Image.fromarray(strip), (x0, y))
        if k == 1: d.text((10, y - 1), f"{'front' if tr.plane == 'front' else 'back'} {tr.idx % 10}  n={tr.n}", fill=(170, 165, 150), font=fs)
    yb = 60 + rowh * len(osc)
    for tm, lab in ((T.T_META, "31.0 beading"), (33.6, "33.6 alignment"), (35.0, "35.0 cut")):
        d.line([(tx(tm), 50), (tx(tm), yb + 200)], fill=(232, 226, 210), width=1); d.text((tx(tm) + 3, yb + 4), lab, fill=(232, 226, 210), font=fs)
    # metric traces
    tt = np.linspace(T.T_IN, T.T_OUT, 450)
    for name, dt, colr in (("locked", 0.0, (240, 170, 60)), ("detuned (n_i(1+eps_i), |eps| 3-8%)", 1.0, (90, 140, 255))):
        m = np.array([align_metric(t, dt)[0] for t in tt])
        pts = [(tx(t), yb + 190 - 20 * v) for t, v in zip(tt, m)]
        d.line(pts, fill=colr, width=2)
        d.text((x0 + (0 if dt == 0 else 300), yb + 196 - 180), f"max|theta| (deg): {name}", fill=colr, font=fs)
    # phase wheels at 33.6
    for j, (name, dt) in enumerate((("locked", 0.0), ("detuned", 1.0))):
        cx, cy = 1180 + j * 160, 160
        d.text((cx - 40, 60), f"{name} @ 33.60 s", fill=(220, 215, 200), font=f)
        for r, (tr, k) in enumerate(osc):
            R = 20 + r * 1.35
            ph = k * tr.n * (1 + dt * tr.eps) * T.OMEGA * (33.6 - T.T_IN)
            px, py = cx + R * math.cos(ph - math.pi / 2), cy + R * math.sin(ph - math.pi / 2)
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(240, 170, 60) if dt == 0 else (90, 140, 255))
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], outline=(120, 120, 120))
    img.save(SW / "harmonic-phase-visualizer.png")

def ab():
    rows = []
    f = ImageFont.truetype(FONT, 16)
    for t in (33.0, 33.6):
        pair = []
        for name, dt in (("A locked", 0.0), ("B detuned", 1.0)):
            im = u8(T.frame(t, dt)[0])
            m = align_metric(t, dt)
            pi = Image.fromarray(im); dr = ImageDraw.Draw(pi)
            dr.text((10, 8), f"{name}  t={t:.2f}  max|theta|={m[0]:.2f} deg  rms orbit disp={m[1]:.1f} px", fill=(232, 226, 210), font=f)
            pair.append(np.asarray(pi))
        rows.append(np.hstack([pair[0], np.full((408, 8, 3), 40, np.uint8), pair[1]]))
    out = np.vstack([rows[0], np.full((8, rows[0].shape[1], 3), 40, np.uint8), rows[1]])
    Image.fromarray(out).save(SW / "harmonic-ab-locked-vs-detuned.png")

# ---------------------------------------------------------------- Sh5: the last handmade pellets falling onto the real heap
def heap_surface():
    a = np.asarray(Image.open(OUT.parent / "cutout/sh5/heap_rgba_960x408.png"))[..., 3]
    m = (a > 128).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    ys = np.array([np.argmax(m[:, x]) if m[:, x].any() else 407 for x in range(960)], float)
    ys = cv2.GaussianBlur(ys.reshape(1, -1).astype(np.float32), (0, 0), 6).ravel()
    return ys

def sh5():
    d = OUT / "sh5_pellets_rgba"; d.mkdir(parents=True, exist_ok=True)
    pv = OUT / "sh5_preview"; pv.mkdir(exist_ok=True)
    heap = np.asarray(Image.open(OUT.parent / "cutout/sh5/heap_rgba_960x408.png")).astype(np.float32) / 255
    heap_rgb = heap[..., :3] * heap[..., 3:4]
    ys = heap_surface()
    rng = np.random.default_rng(5)
    # the last pellets: those with the latest release in Sh4 (largest fall_delay), from the front trees, keep their own shape/dye
    cand = [(p["fall_delay"], ti, pi) for ti, tr in enumerate(T.FRONT_T) for pi, p in enumerate(tr.pellets)]
    cand.sort(reverse=True)
    chosen = cand[:34]
    drops = []
    for j, (_, ti, pi) in enumerate(chosen):
        tr = T.FRONT_T[ti]; p = tr.pellets[pi]; st = tr.strands[p["strand"]]
        r = st["r"][p["idx"]] * T.bead_mult(st, 1.0)[p["idx"]]
        r = r * np.clip((st["pitch"] / 2 - np.abs(p["dist"])) / (0.18 * st["pitch"]), 0, 1) ** 0.5
        loc = st["pts"][p["idx"]] - st["pts"][p["centre_i"]]
        x = float(rng.uniform(90, 900)) if j > 5 else float(rng.uniform(560, 880))   # densest above the heap's crest
        t0 = 35.0 + float(rng.random() ** 1.6 * 0.62)
        y0 = -20 - float(rng.random() * 90)
        v0 = float(rng.uniform(250, 600))         # still moving from the Sh4 fall
        ysurf = ys[int(np.clip(x, 0, 959))] + float(rng.uniform(2, 9))
        drops.append(dict(tree=ti, pellet=pi, loc=loc, r=r, w=tr.w, opal=tr.opal, absv=tr.absv, x=x, t0=t0, y0=y0, v0=v0, ys=ysurf,
                          spin0=float(rng.uniform(0, 6.28)), spin_v=float(rng.normal(0, 9)), slide=float(rng.normal(0, 7))))
    g = T.G_FALL
    def state(dr, t):
        """ballistic fall, one bounce (restitution 0.25), short slide; returns pos, angle, rest flag"""
        if t < dr["t0"]: return None
        y0, v0, ysf = dr["y0"], dr["v0"], dr["ys"]
        # first impact time
        a, b, c = 0.5 * g, v0, y0 - ysf
        t1 = (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
        tl = t - dr["t0"]
        if tl < t1:
            return np.array([dr["x"], y0 + v0 * tl + 0.5 * g * tl * tl]), dr["spin0"] + dr["spin_v"] * tl, False
        vimp = v0 + g * t1; vb = -0.25 * vimp; t2 = -2 * vb / g
        ang1 = dr["spin0"] + dr["spin_v"] * t1
        if tl < t1 + t2:
            u = tl - t1
            return np.array([dr["x"] + dr["slide"] * u / t2, ysf + vb * u + 0.5 * g * u * u]), ang1 + 0.3 * dr["spin_v"] * u, False
        u = min(tl - t1 - t2, 0.15); e = 1 - (1 - u / 0.15) ** 2
        return np.array([dr["x"] + dr["slide"] * (1 + 0.6 * e), ysf + 1.5 * e]), ang1 + 0.3 * dr["spin_v"] * t2, (tl - t1 - t2) >= 0.15
    last_motion = 0.0
    for f in range(F_SH5[0], F_SH5[1] + 1):
        t = f / 24.0
        rgb = np.zeros((408, 960, 3), np.float32); alpha = np.zeros((408, 960), np.float32)
        moving = False
        for dr in sorted(drops, key=lambda q: q["w"]):
            s = state(dr, t)
            if s is None: continue
            pos, ang, rest = s
            moving |= not rest
            th = np.zeros((408, 960), np.float32); nr = np.zeros_like(th); cv = np.zeros_like(th)
            c, sn = math.cos(ang), math.sin(ang)
            q = pos[None] + np.stack([c * dr["loc"][:, 0] - sn * dr["loc"][:, 1], sn * dr["loc"][:, 0] + c * dr["loc"][:, 1]], 1)
            T.stamp(th, nr, cv, q[:, 0], q[:, 1], dr["r"])
            cvb = cv2.GaussianBlur(cv, (0, 0), 0.45); thb = cv2.GaussianBlur(th, (0, 0), 0.45); nrb = cv2.GaussianBlur(nr, (0, 0), 0.45)
            E, Tbg = T.shade(thb, nrb, cvb, dr["w"], dr["opal"], 1.0, dr["absv"])
            a = (cvb * 0.94)[..., None]
            rgb = rgb * (1 - a) + E * a; alpha = alpha + (1 - alpha) * a[..., 0]
        if moving: last_motion = t
        # straight-alpha RGBA, colour = emitted light after the shared roll-off
        col = np.where(alpha[..., None] > 1e-4, rgb / np.maximum(alpha[..., None], 1e-4), 0)
        col = T.halation_rolloff(col * (alpha[..., None] > 1e-4))
        rgba = np.dstack([u8(col), u8(alpha)])
        Image.fromarray(rgba, "RGBA").save(d / f"f{f:04d}.png")
        comp = heap_rgb * (1 - alpha[..., None]) + col * alpha[..., None]
        save(pv / f"f{f:04d}.png", u8(comp))
    json.dump(dict(drops=[{k: (v if not isinstance(v, np.ndarray) else None) for k, v in dr.items() if k not in ("loc", "r", "absv")} for dr in drops],
                   last_motion_t=last_motion, surface_from="alpha>128 of cutout/sh5/heap_rgba_960x408.png, closed 9px, blurred 6px"),
              open(OUT / "sh5_drops.json", "w"), indent=1, default=float)
    print("last motion", last_motion)

if __name__ == "__main__":
    w = sys.argv[1]
    if w == "sh4": sh4(int(sys.argv[2]), int(sys.argv[3]))
    elif w == "sh5": sh5()
    elif w == "measure": measure()
    elif w == "ab": ab()
    elif w == "phase": phase_png()
