"""TEST SHOT: S3 laugh (rue Royale) -> S4 jump cut (place de Clichy), film time 6.0-11.0 s.
Local frame f = film frame - 144. Jump cut at local 48 = film frame 192 (8.000 s).

Run:  python3 test_shot.py [--stills t ...] [--sheet]
  (from anywhere; paths are absolute). Writes test-shot.mp4 into the swarm folder via kit.Film.
"""
import sys, json, math, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
SW = ROOT / "films/swarm/zazie-dans-le-metro"
MED = ROOT / "films/sources/zazie-dans-le-metro/test-shot"
sys.path.insert(0, str(ROOT / "films"))
sys.path.insert(0, str(SW / "test-shot-build"))
import kit                                    # noqa: E402  (read-only use)
import puppet as pp                           # noqa: E402

FPS = 24
T0 = 6.0
N = 120                                       # 5.0 s
CUT = 48                                      # local frame of the jump cut (film frame 192)
HOLD = (40, 47)                               # declared 1/3 s hold at full laugh (7.667-8.000 s)
PW, PH = pp.PW, pp.PH

pp.load_paper(MED / "paper/kraft.png")

# ------------------------------------------------------------------ exposure sheet (canonical state)
LAUGH = [4, 5, 4, 6]                          # mouth cycle after the opening 1


def acting(g):
    """Puppet acting clock: stands still through the hold and the cut drawing (40..49)."""
    return g if g <= HOLD[0] else max(HOLD[0], g - 10)


def sheet_row(f):
    """frame -> pose/replacement ids. Drawings change on twos (the even frame rules)."""
    g = f - (f % 2)
    if HOLD[0] <= f <= CUT + 1:     # declared hold; the cut frame shows the same drawing on the new plate
        g = HOLD[0]
    row = dict(f=f, film_frame=f + 144, drawing=g, plate="P1" if f < CUT else "P2")
    if g < 12:                                # out of breath: closed smile, half eyes
        row.update(mouth=1 if g < 8 else 4, eyes="half", laugh=0.0)
    elif g < 72:                              # the laugh: 1-4-5-4-6-4..., 4 frames per mouth; acting clock skips the hold
        a = acting(g)
        k = (a - 12) // 4
        m = [1] + LAUGH * 20
        row.update(mouth=m[k], eyes="squeeze", laugh=1.0)
        if g == HOLD[0]:
            row["mouth"] = 5
    elif g < 84:                              # 9.0 s: eyes open on the tram, a tiny gulp
        row.update(mouth=2, eyes="open_r", laugh=0.0)
    elif g < 98:                              # decides: grin
        row.update(mouth=4, eyes="open_r", laugh=0.35)
    else:                                     # and laughs again, shorter
        k = (g - 98) // 4
        row.update(mouth=[5, 4, 6, 4, 5, 4][min(k, 5)], eyes="squeeze", laugh=0.8)
    return row


def wind_at(t):
    """Gust curve (local s). Starts 6.6 s film time, sweeps L->R, ends 9.6 s; nothing drives the hair after that."""
    if t < 0.6 or t > 3.6:
        return 0.0
    a = min(1.0, (t - 0.6) / 0.35)
    d = 1.0 if t < 2.7 else max(0.0, 1 - (t - 2.7) / 0.9)
    turb = 1 + 0.28 * math.sin(t * 11.3) + 0.18 * math.sin(t * 23.1 + 1.0)
    return a * d * turb


def head_motion(f):
    """Head (rig root) transform per drawing: angle (rad) about the neck pin, dx, dy (2x px)."""
    row = sheet_row(f); g0 = row["drawing"]; g = acting(g0) if g0 < 72 else g0; t = g / FPS
    lg = row["laugh"]
    ang = 0.0; dx = 0.0; dy = 0.0
    if g < 12:      # breathing after the run
        dy = 6 * math.sin(2 * math.pi * t / 0.5)
    tipped = min(1.0, max(0.0, (g - 12) / 14)) if g < 72 else max(0.0, 1 - (g - 72) / 6)
    if g >= 98:
        tipped = min(1.0, (g - 98) / 8) * 0.7
    dy += -14 * tipped                                         # head tips back 3 deg ~ rises
    ang += math.radians(-3.0) * tipped * 0.4
    rock = math.radians(3.5) * math.sin(2 * math.pi * (g - 12) / 16) * lg   # rock on the neck pin
    shake = (1 if (g // 4) % 2 == 0 else -1) * lg                            # 4-frame alternation
    ang += rock + math.radians(1.0) * shake
    dy += 6 * shake                                             # shoulders/head shake 3 px @720
    if row["eyes"] == "open_r" and g >= 72:
        dx += 10 * min(1, (g - 72) / 4)                         # turns toward the tram a touch
    return ang, dx, dy


def make_xform(ang, dx, dy):
    c, s = math.cos(ang), math.sin(ang); px, py = pp.NECK_PIN

    def X(p):
        x, y = p[0] - px, p[1] - py
        return (px + x * c - y * s + dx, py + x * s + y * c + dy)
    return X


# ------------------------------------------------------------------ simulate secondary dynamics (24 Hz, 8 substeps)
def simulate():
    strands, slivers = pp.make_fringe()
    states = {}
    log = []
    prev = None; prev_v = np.zeros(2); prev_om = 0.0
    for f in range(N):
        if HOLD[0] < f <= CUT + 1:            # declared hold: puppet time stops, state carried across the cut
            states[f] = states[f - 1]
            log.append(dict(f=f, held=True, e=log[-1]["e"], wind=0.0))
            continue
        ang, dx, dy = head_motion(f)
        X = make_xform(ang, dx, dy)
        pos = np.array(X(pp.CROWN))
        if prev is None:
            prev = (ang, pos); v = np.zeros(2); om = 0.0
        dt = 1 / FPS
        om = (ang - prev[0]) / dt; v = (pos - prev[1]) / dt; acc = (v - prev_v) / dt
        t = f / FPS
        W = wind_at(t)
        wv = np.array([1.0, -0.25]) * W
        sub = 8
        for _ in range(sub):
            for s in strands + slivers:
                s.step(dt / sub, ang, om, acc, wv, t)
        for s in slivers:
            if s.detach_at is not None and s.free is None and t >= s.detach_at:
                s.detach(X)
        prev = (ang, pos); prev_v = v
        e = sum(s.energy(ang) for s in strands)
        states[f] = dict(X=(ang, dx, dy), strands=[s.points(X) for s in strands], slivers=[s.points(X) for s in slivers],
                         wind=W, strand_phi=[list(map(float, s.phi)) for s in strands],
                         strand_om=[list(map(float, s.om)) for s in strands])
        log.append(dict(f=f, held=False, e=float(e), wind=W))
    return strands, slivers, states, log


# ------------------------------------------------------------------ plates
_plates = {}


def plate(name, blur):
    key = (name, round(blur, 1))
    if key not in _plates:
        im = Image.open(MED / f"plates/{name}_sharp.png").convert("RGB")
        _plates[key] = im.filter(ImageFilter.GaussianBlur(blur))
    return _plates[key]


def plate_blur(f):
    if f < CUT:
        return 24.0                            # r 12 @720
    if f < 72:
        return 22.0
    if f < 98:                                 # rack focus to the far plane as she looks at the tram
        return 22.0 - 15.0 * min(1, (f - 72) / 8)
    return 7.0 + 15.0 * min(1, (f - 98) / 6)


def puppet_blur(f):
    if 72 <= f < 104:
        return 3.0 * min(1, (f - 72) / 8) * (1 if f < 98 else max(0, 1 - (f - 98) / 6))
    return 0.0


# ------------------------------------------------------------------ handmade plaque (blue enamel, cut card)
def plaque():
    W, H = 300, 136
    s = pp.Sheet(W + 40, H + 40)
    body = pp.cut([(20, 26), (W + 20, 20), (W + 22, H + 18), (18, H + 22)], (47, 63, 85), 501, rough=0.4)
    s.lay(body, shadow=False)
    rim = pp.cut([(30, 34), (W + 10, 30), (W + 12, H + 8), (28, H + 12)], (47, 63, 85), 502, rough=0.2)
    d = ImageDraw.Draw(s.img)
    d.rounded_rectangle((30, 34, W + 10, H + 10), radius=10, outline=(206, 194, 168, 255), width=4)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
    d.text((W / 2 + 20, 50), "17e ARRt", font=fs, fill=(206, 194, 168, 255), anchor="mm")
    d.text((W / 2 + 20, 80), "PLACE", font=fb, fill=(214, 202, 176, 255), anchor="mm")
    d.text((W / 2 + 20, 116), "DE CLICHY", font=fb, fill=(214, 202, 176, 255), anchor="mm")
    return s.img


# ------------------------------------------------------------------ compose one drawing
STATIC = pp.build_static()
MOUTHS = {m: pp.mouth_piece(m) for m in (1, 2, 4, 5, 6)}
EYEP = {k: [pp.eye_piece(k, ex, ey, fl, 300 + 20 * i) for i, ((ex, ey), fl) in enumerate(zip(pp.EYES, (-1, 1)))]
        for k in ("squeeze", "half", "open_r")}
PLAQUE = None
_draw_cache = {}
STRANDS = []


def draw_puppet(f, states):
    row = sheet_row(f); g = row["drawing"]
    if g in _draw_cache:
        return _draw_cache[g]
    st = states[g]
    ang, dx, dy = st["X"]
    lg = row["laugh"]
    W = st["wind"]
    # ---- body sheet (does not rotate with the head; shakes with the shoulders)
    body = pp.Sheet()
    sdy = dy * 0.5
    for k in ("jumper", "neck", "collar_l", "collar_r", "collar_fold"):
        body.lay(STATIC[k], 0, sdy)
    # ---- head sheet (neutral rig coords; rotated about the neck pin afterwards)
    head = pp.Sheet()
    for pc in pp.back_hair(W):
        head.lay(pc)
    head.lay(STATIC["ear_l"]); head.lay(STATIC["ear_l_in"], shadow=False)
    head.lay(STATIC["ear_r"]); head.lay(STATIC["ear_r_in"], shadow=False)
    head.lay(STATIC["face"])
    face_mask = Image.new("L", (PW, PH), 0); face_mask.paste(STATIC["face"].img.getchannel("A"), (STATIC["face"].ox, STATIC["face"].oy))
    lift = 12 * lg                                    # cheeks rise 6 px @720
    for k in ("jaw_tissue", "socket_l", "socket_r"):
        head.lay(STATIC[k], shadow=False, clip=face_mask)
    head.lay(STATIC["cheek_l"], 0, -lift, shadow=False, clip=face_mask)
    head.lay(STATIC["cheek_r"], 0, -lift, shadow=False, clip=face_mask)
    for pc in pp.laugh_folds(1.0 if row["mouth"] in (4, 5, 6) else 0.0):
        head.lay(pc, shadow=False)
    for side in EYEP[row["eyes"]]:
        for pc in side:
            head.lay(pc, 0, -lift * 0.5 if row["eyes"] == "squeeze" else 0, sh_off=(3, 4), sh_a=0.3, sh_blur=3)
    for pc in pp.brows(16 * lg + (8 if row["eyes"] == "open_r" else 0)):
        head.lay(pc, sh_off=(4, 5), sh_a=0.3, sh_blur=4)
    head.lay(STATIC["nose"], sh_off=(6, 8)); head.lay(STATIC["nose_sh"], shadow=False)
    head.lay(STATIC["nostril_l"], shadow=False); head.lay(STATIC["nostril_r"], shadow=False)
    for pc in MOUTHS[row["mouth"]]:
        head.lay(pc, sh_off=(4, 5), sh_a=0.32, sh_blur=4)
    sway = 0.0
    if g > 0:
        sway = -40 * (ang - states[max(0, g - 2)]["X"][0]) * 10
    for pc in pp.side_locks(W, sway):
        head.lay(pc)
    head.lay_rot = None
    headimg = head.img.rotate(-math.degrees(ang), resample=Image.BICUBIC, center=pp.NECK_PIN, translate=(dx, dy))
    # ---- assemble: body, head, then the fringe (strands are already in world coords from the sim)
    out = pp.Sheet()
    out.img = body.img
    out.img.alpha_composite(headimg)
    # fringe casts a deeper shadow on the face (separate plane, farther from the face card)
    for i, pts in enumerate(st["strands"]):
        S_ = STRANDS[0][i]
        pc = pp.cut(pp.ribbon(pp.catmull(pts, 6), S_.width, 14), S_.tone, S_.seed, rough=0.7)
        out.lay(pc, sh_off=(12, 15), sh_a=0.42, sh_blur=9)
    X = make_xform(ang, dx, dy)
    cx, cy = X(pp.CROWN)
    pp.brad(out, cx + 10, cy + 70, 9)
    for i, pts in enumerate(st["slivers"]):
        if pts[0][0] > PW + 200:
            continue
        S_ = STRANDS[1][i]
        pc = pp.cut(pp.ribbon(pp.catmull(pts, 6), S_.width, 4), S_.tone, S_.seed, rough=0.5)
        out.lay(pc, sh_off=(10, 12), sh_a=0.35, sh_blur=8)
    # overcast light from upper left: gentle falloff across the paper (one tabletop object, one light)
    a = np.asarray(out.img).astype(np.float32)
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
    lightf = 1.06 - 0.12 * (xx / PW) - 0.06 * (yy / PH)
    a[..., :3] = np.clip(a[..., :3] * lightf[..., None], 0, 255)
    img = Image.fromarray(a.astype(np.uint8), "RGBA")
    _draw_cache[g] = img
    return img


def compose(f, states):
    """Full 720x540 picture for local frame f."""
    row = sheet_row(f)
    g = row["drawing"]
    ang, dx, dy = states[g]["X"]
    name = row["plate"]
    bl = plate_blur(g)
    P = plate(name, bl)
    # multiplane: plate drifts at 0.25x of the head's lateral motion, plus a slow drift
    ox = (P.width - PW) / 2 - 0.25 * (dx + 300 * ang) - (6 * (g / FPS) if name == "P1" else -4 * ((g - CUT) / FPS))
    oy = (P.height - PH) / 2 - 0.25 * dy * 0.3
    pic = P.crop((int(ox), int(oy), int(ox) + PW, int(oy) + PH)).convert("RGBA")
    if name == "P2" and f >= 52:
        global PLAQUE
        if PLAQUE is None:
            PLAQUE = plaque()
        k = f - 52
        sc = [0.55, 1.14, 0.96, 1.03, 1.0][min(k, 4)]
        pl = PLAQUE.resize((int(PLAQUE.width * sc), int(PLAQUE.height * sc)), Image.LANCZOS)
        S = pp.Sheet(); S.img = pic
        sh = pl.getchannel("A").filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.45))
        dark = Image.new("RGBA", pl.size, (20, 10, 4, 0)); dark.putalpha(sh)
        cxp, cyp = 1250, 120
        pic.alpha_composite(dark, (int(cxp - pl.width / 2 + 9), int(cyp - pl.height / 2 + 11)))
        pic.alpha_composite(pl, (int(cxp - pl.width / 2), int(cyp - pl.height / 2)))
    pup = draw_puppet(f, states)
    pb = puppet_blur(row["drawing"])
    if pb > 0.2:
        pup = pup.filter(ImageFilter.GaussianBlur(pb))
    pic.alpha_composite(pup)
    return pic.convert("RGB").resize((720, 540), Image.LANCZOS)


# ------------------------------------------------------------------ tests (secondary dynamics bar)
def unit_tests():
    res = {}
    # lag: step-rotate the head 6 deg in one frame; time for the strand tip to reach its half response
    s = pp.Strand((0, 0), [math.radians(100)] * 3, 300, 60, (0, 0, 0), 0)
    s.rest = np.array([math.radians(90), math.radians(96), math.radians(108)]); s.phi = s.rest.copy()
    tip_ang = []
    for f in range(30):
        ang = math.radians(6) if f >= 1 else 0.0
        om = math.radians(6) * FPS if f == 1 else 0.0
        for _ in range(8):
            s.step(1 / FPS / 8, ang, om if _ == 0 else 0.0, np.zeros(2), np.zeros(2), 0)
        tip_ang.append(float(s.phi[-1] - s.rest[-1]))
    target = math.radians(6)
    lag = next(i for i, v in enumerate(tip_ang) if v >= 0.5 * target) - 1
    res["strand_tip_half_response_lag_frames"] = lag
    res["lag_ok_2_3"] = 2 <= lag <= 3
    return res, tip_ang


def energy_tests(log):
    gust_end = 3.6
    peak = max(r.get("e", 0) for r in log if r["f"] / FPS < gust_end + 1e-9)
    after = [r for r in log if gust_end + 1.0 <= r["f"] / FPS < gust_end + 1.05 and not r["held"]]
    e1 = after[0]["e"] if after else None
    return dict(energy_peak=peak, energy_1s_after_gust=e1, ratio=(e1 / peak if e1 is not None else None),
                decay_ok=(e1 is not None and e1 / peak < 0.10))


# ------------------------------------------------------------------ sound
def wav_mono(path):
    w = wave.open(str(path)); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x


def sound(mix):
    R = kit.RATE
    # L1: thin street ambience (kit murmur + room), thinning toward the hold
    mix.murmur(0.0, 1.66, gain=0.035, pitch=140, pan=-0.2, seed=3)
    mix.room(0.0, 1.66, gain=0.015)
    # foraged wind gust from 0.6 s (Commons, CC BY-SA 4.0); hard stop at the declared hold
    wv = wav_mono(MED / "sound/wind.wav")
    seg = wv[int(0.2 * R): int(0.2 * R) + int(1.06 * R)].copy()
    n = len(seg); env = np.ones(n); a = int(0.25 * R); env[:a] = np.linspace(0, 1, a)
    seg *= env
    mix.add(seg, 0.6, gain=1.8, pan=0.25)
    # declared silence 1.667-2.000 (film 7.667-8.000): nothing is added in that window
    # 2.000 jump cut: hard cut into a busier square, tram bell close and centre, hooves
    seg2 = wv[int(1.6 * R): int(1.6 * R) + int(1.7 * R)].copy()
    e2 = np.ones(len(seg2)); r = int(0.8 * R); e2[-r:] = np.linspace(1, 0, r); seg2 *= e2
    mix.add(seg2, 2.0, gain=1.3, pan=0.25)
    mix.murmur(2.0, 3.0, gain=0.07, pitch=125, pan=0.0, seed=7)
    mix.room(2.0, 3.0, gain=0.02)
    mix.bell(2.02, freq=1180, seconds=1.4, gain=0.22, pan=0.1)
    mix.bell(2.32, freq=1180, seconds=1.4, gain=0.16, pan=0.1)
    for k in range(10):
        mix.step(2.1 + k * 0.29, gain=0.10, pan=0.35, surface="stone")
    mix.click(2.167, gain=0.35, pan=0.6, bright=3200, seconds=0.04)     # paper snap: plaque pops in (film frame 196)
    mix.click(3.0, gain=0.10, pan=0.0, bright=900, seconds=0.06)        # gulp


def main():
    strands, slivers, states, log = simulate()
    STRANDS[:] = [strands, slivers]
    ut, tip = unit_tests()
    et = energy_tests(log)
    # anchor continuity across the cut (frames 47 -> 48)
    a47, a48 = states[HOLD[0]]["X"], states[CUT]["X"]
    anchor = dict(root_dx_px_2x=abs(a48[1] - a47[1]), root_dy_px_2x=abs(a48[2] - a47[2]), ang_deg=math.degrees(abs(a48[0] - a47[0])),
                  mouth_47=sheet_row(47)["mouth"], mouth_48=sheet_row(48)["mouth"],
                  hair_state_carried=states[CUT]["strand_phi"] == states[CUT - 1]["strand_phi"] == states[HOLD[0]]["strand_phi"],
                  plate_47=sheet_row(47)["plate"], plate_48=sheet_row(48)["plate"])
    # centroid delta at 720 px (rig root at the crown)
    X47 = make_xform(*a47)(pp.CROWN); X48 = make_xform(*a48)(pp.CROWN)
    anchor["crown_delta_px_720"] = math.hypot(X48[0] - X47[0], X48[1] - X47[1]) / 2
    anchor["ok"] = anchor["crown_delta_px_720"] <= 8 and anchor["mouth_47"] == anchor["mouth_48"] and anchor["plate_47"] != anchor["plate_48"]
    json.dump(dict(unit_tests=ut, energy=et, anchor=anchor, exposure_sheet=[sheet_row(f) for f in range(N)],
                   energy_log=log), open(SW / "test-shot-build/test-results.json", "w"), indent=1, default=str)
    print(json.dumps(dict(unit_tests=ut, energy=et, anchor=anchor), indent=1))

    film = kit.Film("test-shot", seconds=N / FPS, boil=0, wobble=0, seed=1960)

    def frame(t, ink):
        f = int(round(t * FPS))
        ink.fill((6, 6, 6))
        pic = compose(f, states)
        ink.paste(pic, (120, 0))
        if 78 <= f < 100:          # caption is the voice, 6 frames after she sees it
            al = min(1.0, (f - 78) / 3) * (1.0 if f < 96 else (100 - f) / 4)
            s = "« … le tram ! »"
            fnt = kit.font("serif", 26)
            tw = ink.d.textlength(s, font=fnt)
            ink.d.rectangle([480 - tw / 2 - 12, 492, 480 + tw / 2 + 12, 526], fill=(14, 10, 8, int(120 * al)))
            ink.text((480, 508), s, "serif", 26, (239, 228, 204), anchor="mm", alpha=int(255 * al))
    film.picture(frame)
    film.sound(sound)
    film.poster_at = 1.5
    if "--stills" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1:]]
        out = MED / "stills"; out.mkdir(exist_ok=True)
        for t in ts:
            film.frame(int(round(t * FPS))).save(out / f"{t:05.2f}.png")
        print("stills ->", out)
        return
    film.render(out_dir=SW)


if __name__ == "__main__":
    main()
