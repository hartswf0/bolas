# TEST SHOT L-S5 (film 20.0-22.4 = Version L local 18.0-20.4): CLOSE at the plank foot.
#   python3 -I render_ls5.py [--stills t ...]
# The close is a camera reframing of the world trace (rig.py): FK joints in world px are mapped by the camera
# (zoom Z about a moving window), so poses, hands and the shoe/bag holders are those the gate checked.
# Planes (#44): P0 far wall 0.15x, P1 buttress flange 0.35x, P2 (water, bank, plank, puppets) 1x, P3 leaves 1.5x,
# P4 fern + root diagonal 2.0x; per-plane depth blur only (in the approved r2 cut plates).  Water: a 1927 flood-water
# film still (archive) x the jungle's own reflection; near bank: a photograph of root-laced forest floor (CC BY-SA).
import sys, json, math, subprocess, hashlib
from pathlib import Path
import numpy as np, cv2
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import puppets as PP  # noqa: E402
from puppets import S, lay, pencil, over, gblur, bag_piece, draw_figure, HairSim  # noqa: E402
from rig import fk, sample, bone_error, water_y, N_GROUND, PLANK_N, PLANK_F, smoothstep  # noqa: E402

OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/la-mort-en-ce-jardin/performance")
SEQ = OUT / "L-S5"
TS = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/la-mort-en-ce-jardin/test-shot")
RENO = "/home/user/hartswf0/cineosis-lab/lab/thumbs/4bc92290-7671-5797-bbb6-c637ebc27f24.jpg"
PW, PH, FPS = 800, 540, 24
T_START, T_END = 18.0, 20.4
Z = 2.6
POSES = json.load(open(HERE / "poses.json"))["L"]["keys"]
TRACE = json.load(open(HERE / "trace-L.json"))


def grade(L):
    p2, p98 = np.percentile(L, 2), np.percentile(L, 98)
    return np.clip(35 + (L - p2) * 185 / max(p98 - p2, 1), 0, 255)


# --- foraged water: [Reno Flood] 1927 still, rows of open flood water (320x240 source, scaled 1.5x)
_r = np.asarray(Image.open(RENO).convert("L"), np.float32)[118:236, :]
_r = grade(_r)
_r = cv2.resize(_r, (480, int(_r.shape[0] * 1.5)), interpolation=cv2.INTER_CUBIC)
RENO_W = np.concatenate([_r, _r[:, ::-1], _r], 1)                      # 1440 wide, mirrored joins
# --- foraged bank: "Buttress roots.JPG" (Patti Neumann, CC BY-SA 3.0): the forest floor with surface roots
_b = np.asarray(Image.open(TS / "plates/Buttress_roots_JPG.jpg").convert("L"), np.float32)[600:960, 0:1280]
BANK = grade(_b) * 0.92
BANK = cv2.resize(BANK, (int(BANK.shape[1] * 0.8), int(BANK.shape[0] * 0.8)), interpolation=cv2.INTER_AREA)


# the plates' one monotone curve for this close (p2/p98 -> L35/220 with a lifted mid: the wet bright middle)
P0C = S.load_cut("P0_far", 0.80, blur=0.6, gamma=0.62)
P1C = S.load_cut("P1_flange", 0.62, blur=0.5, gamma=0.72)


def cam_window(t):
    """world window top-left (x0, y0); tilts down to follow her reach to the water, then back up as she rises."""
    keys = [(18.0, 2.0, 196.0), (18.5, 4.0, 198.0), (19.2, 26.0, 236.0), (19.8, 26.0, 236.0), (20.4, 18.0, 214.0)]
    for (ta, xa, ya), (tb, xb, yb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            u = smoothstep((t - ta) / (tb - ta)); return xa + (xb - xa) * u, ya + (yb - ya) * u
    return keys[-1][1], keys[-1][2]


def to_screen(J, win):
    x0, y0 = win
    return {b: (((p0[0] - x0) * Z, (p0[1] - y0) * Z), ((p1[0] - x0) * Z, (p1[1] - y0) * Z), a) for b, (p0, p1, a) in J.items()}


def W2S(p, win): return ((p[0] - win[0]) * Z, (p[1] - win[1]) * Z)


HAIR = HairSim()
HAIR_CACHE = {}


def hair_at(t):
    """B's strands simulated on twos from the start of the shot (deterministic)."""
    q = int(math.floor((t - T_START) * 12 + 1e-6))
    if q in HAIR_CACHE: return HAIR_CACHE[q]
    sim = HairSim()
    out = None
    for k in range(q + 1):
        tt = T_START + k / 12
        r, ab, _ = sample(POSES["B"], tt)
        out = [row[:] for row in sim.step(ab["head"], r)]
        HAIR_CACHE[k] = out
    return out


def frame(t, stats=None):
    i = int(round(t * FPS))
    st = TRACE["frames"][i]
    win = cam_window(t)
    dx = (win[0] - 2.0) * Z; dy = (win[1] - 198.0) * Z           # camera travel in screen px at the P2 plane
    C = np.zeros((PH, PW, 3), np.float32) + 96
    # P0 far wall (0.15x) and P1 buttress flange (0.35x): the approved r2 cut plates
    over(C, P0C, -150 - dx * .15, -150 - dy * .15)
    over(C, P1C, -360 - dx * .35, 150 - dy * .35)
    # water plane (P2): flood-water still x reflection of the jungle above the waterline
    wl = int(round(W2S((0, st["water_y"]), win)[1]))
    if wl < PH:
        hh = PH - wl
        refl = C[max(wl - hh, 0):wl][::-1].copy()
        if refl.shape[0] < hh: refl = np.concatenate([refl, np.repeat(refl[-1:], hh - refl.shape[0], 0)], 0)
        ph = math.floor(t * 12) / 12
        for yy in range(hh):
            refl[yy] = np.roll(refl[yy], int(round((1 + yy * 0.03) * math.sin(yy * 0.13 + ph * 6))), axis=0)
        off = int(ph * 12 * 3) % 480 + int(dx * 0.5) % 300
        wtx = RENO_W[: hh, off:off + PW]
        if wtx.shape[0] < hh: wtx = np.concatenate([wtx, wtx[::-1]], 0)[:hh]
        water = 0.58 * wtx[..., None] + 0.42 * gblur(refl, 1.0) * 0.85
        C[wl:] = water
        g = np.zeros((PH, PW), np.float32); g[wl:wl + 3] = 0.35
        C[:] = C * (1 - g[..., None]) + 190 * g[..., None]
    # near bank (P2): photographed forest floor with surface roots, torn edge dropping into the water
    edge_x = W2S((PLANK_N[0] + 4, 0), win)[0]
    gy = W2S((0, N_GROUND), win)[1]
    bh, bw = BANK.shape
    ys = np.arange(PH)[:, None]; xs = np.arange(PW)[None, :]
    torn = edge_x + 10 * np.sin(ys * 0.07) + 6 * np.sin(ys * 0.21 + 1) - (ys - gy) * 0.45
    top = gy + 4 * np.sin(xs * 0.05) + 3 * np.sin(xs * 0.13)
    m = ((xs < torn) & (ys > top)).astype(np.float32)
    m = gblur(m, 1.2)
    ox = int(dx * 1.0) % 200
    tex = np.zeros((PH, PW), np.float32)
    y0 = max(int(gy) - 10, 0)
    patch = BANK[: PH - y0, ox:ox + PW]
    tex[y0:y0 + patch.shape[0], :patch.shape[1]] = patch
    wet = np.clip(1 - (torn - xs) / 60, 0, 1)                       # wet, darker mud toward the water's edge
    tex = tex * (1 - 0.35 * wet)
    C[:] = C * (1 - 0.45 * gblur(m, 6)[..., None] * (1 - m[..., None]))          # the bank's soft shadow on the water
    C[:] = C * (1 - m[..., None]) + tex[..., None] * m[..., None]
    # plank (handmade pale card), its foot resting on the bank edge, running off to the far bank
    # in the close the plank is seen running away from the camera: its foot on the bank edge, rising to the far bank
    pn = W2S((PLANK_N[0] - 14, PLANK_N[1] + 2), win)
    S.plank(C, (pn[0], pn[1]), (pn[0] + 420, pn[1] - 165), 8 * Z, 3.5 * Z, seed=700, tone=204)
    # puppets (world FK -> camera), shoe and bag from the trace holders
    rC, aC, eC = sample(POSES["C"], t); rB, aB, eB = sample(POSES["B"], t)
    JCw, JBw = fk(rC, aC), fk(rB, aB)
    JC, JB = to_screen(JCw, win), to_screen(JBw, win)
    errs = [max(bone_error(JC, Z).values()), max(bone_error(JB, Z).values())]
    light = (W2S((0, 150), win)[1], W2S((0, N_GROUND), win)[1])
    shoe_h = st["shoe"][0] if st["shoe"] else None
    bag_h = st["bag"][0]
    SHOE_W = int(50 * Z)

    def shoe_cb(Cn):
        if shoe_h == "water":
            sp = W2S(st["shoe_pos"], win)
            S.shoe_on_water(Cn, sp[0], W2S((0, st["water_y"]), win)[1], SHOE_W, 4, t)
        elif shoe_h == "B.R":
            tr = [e for e in TRACE["events"] if e["event"] == "retrieve"][0]["t"]
            rise = smoothstep((t - tr - 0.3) / 0.7)
            p0, p1, ang = JB["hand_n"]
            rot = (1 - rise) * (-ang + 30) + rise * 4
            sh = S.shoe_img(SHOE_W, rot); h, w = sh.shape[:2]
            px = p0[0] + (p1[0] - p0[0]) * .7; py = p0[1] + (p1[1] - p0[1]) * .7
            over(Cn, sh, px - w * (.45 - .05 * rise), py - h * (.5 - .12 * rise))
    draw_figure(C, JC, Z, "C", 1, mud=1.15, gaze=eC["gaze"], brow=eC["brow"], mouth=eC["mouth"], light=light,
                contact=(JC["root"][1][0] + 40, W2S((0, N_GROUND), win)[1], 90, 9, .45))
    draw_figure(C, JB, Z, "B", 1, mud=1.0, gaze=eB["gaze"], brow=eB["brow"], mouth=eB["mouth"], hair=hair_at(t),
                front_hand_cb=shoe_cb, light=light, contact=(JB["root"][1][0] + 50, W2S((0, N_GROUND), win)[1] + 2, 110, 9, .5))
    # the bag hangs nearest the camera from the holder's hand bone; the holder's hand card is re-laid over the strap
    who, hand = bag_h.split(".")
    J = JB if who == "B" else JC
    bone = "hand_f" if hand == "L" else "hand_n"
    hx, hy = J[bone][1]
    bag_piece(C, hx, hy - 4, 0.95 * Z, 4 if who == "B" else -6)
    lay(C, [S.bpoly(J, bone, PP.HAND, Z, 1)], PP.TONES[who]["skin"] * .95, 1.7, PP.SEED[who] + 31, 2)
    # P3 leaves (1.5x) frame the top; P4 fern right and the root diagonal low left (2.0x)
    over(C, S.P3, 560 - dx * 1.5, -470 - dy * 1.5)
    over(C, S.P3f, -650 - dx * 1.5, -560 - dy * 1.5)
    over(C, S.FERN, 690 - dx * 2.0, -40 - dy * 2.0)
    over(C, S.P4R, -420 - dx * 2.0, 400 - dy * 2.0)
    C = np.clip(C, 0, 255)
    rec = dict(i=i, film_t=round(20.0 + (t - T_START), 4), local_t=round(t, 4), cam_window=[round(win[0], 2), round(win[1], 2)], zoom=Z,
               bag=bag_h, shoe=shoe_h, screen_rig_error_px=round(max(errs), 4),
               head_B_frac_H=round(41 * PP.HEAD_SCALE * Z / PH, 3))
    hc = JB["head"][0]
    if shoe_h == "B.R":
        p0, p1, _ = JB["hand_n"]; sc = (p0[0] + (p1[0] - p0[0]) * .7, p0[1] + (p1[1] - p0[1]) * .7)
        rec["shoe_to_face_px"] = round(math.dist(sc, hc) - 0.5 * SHOE_W, 1)
    assert max(errs) < 0.5, errs
    return C, rec


def measure(C):
    L = C.mean(2)
    p = [int(round(x)) for x in np.percentile(L, [1, 5, 25, 50, 75, 95, 99])]
    gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3) / 8
    hp = L - gblur(L, 2)
    return dict(p=p, below60=round(float((L < 60).mean() * 100), 1), above200=round(float((L > 200).mean() * 100), 1),
                grad=round(float(np.hypot(gx, gy).mean()), 2), hp_sigma=round(float(hp.std()), 2),
                rb=round(float(np.abs(C[..., 0] - C[..., 2]).mean()), 2))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        for tt in [float(x) for x in sys.argv[2:]]:
            C, rec = frame(tt)
            Image.fromarray(C.astype(np.uint8)).save(OUT / f"still-{tt:05.2f}.png"); print(rec, measure(C))
        sys.exit()
    SEQ.mkdir(parents=True, exist_ok=True)
    n = int(round((T_END - T_START) * FPS))
    recs = []
    for k in range(n):
        tt = T_START + k / FPS
        C, rec = frame(tt)
        rec["stats"] = measure(C)
        im = Image.fromarray(C.astype(np.uint8))
        im.save(SEQ / f"L-S5_{k:03d}.png")
        rec["png"] = f"L-S5/L-S5_{k:03d}.png"
        rec["sha1"] = hashlib.sha1(np.asarray(im).tobytes()).hexdigest()[:16]
        recs.append(rec)
        print(k, rec["bag"], rec["shoe"], rec["stats"]["p"], rec["stats"]["above200"], rec["stats"]["grad"], flush=True)
    json.dump(dict(shot="L-S5", film=[20.0, 22.4], local=[T_START, T_END], fps=FPS, picture=[PW, PH], frames=recs),
              open(OUT / "L-S5.json", "w"), indent=0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", str(SEQ / "L-S5_%03d.png"),
                    "-vf", "pad=960:540:80:0:color=0x1b1b1b", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    str(OUT / "L-S5-preview.mp4")], check=True)
