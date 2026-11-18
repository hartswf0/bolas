"""E3 editor: acceptance checks for repair round 1, measured on the DECODED mp4 (ffmpeg) + the rig masks.
Run from the oulipo root: python3 -I films/swarm/le-maki-mococo/e3_check.py  -> e3_check.json"""
import json, subprocess, sys, importlib.util
from pathlib import Path
import numpy as np, cv2
from PIL import Image
SW = Path(__file__).resolve().parent
OUL = SW.parents[2]
MP4 = OUL / "assets" / "films" / "le-maki-mococo.mp4"
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location("film_lmm", OUL / "films" / "le-maki-mococo.py")
F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
M = F.M
OUT = OUL / "films" / "sources" / "le-maki-mococo" / "editor" / "e3"
OUT.mkdir(parents=True, exist_ok=True)


def frame(t):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.4f}", "-i", str(MP4), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(540, 960, 3)


def zoom_mask(a2x):
    z = M.ZOOM
    im = Image.fromarray((np.clip(a2x, 0, 1) * 255).astype(np.uint8)).resize((int(round(960 * z)), int(round(540 * z))), Image.BILINEAR)
    ox, oy = int(round(M.ZOOM_C[0] * (z - 1))), int(round(M.ZOOM_C[1] * (z - 1)))
    return np.asarray(im.crop((ox, oy, ox + 960, oy + 540))) > 127


def lower_lip_mask(t):
    pose, jaw = F.TRACK.frame(t)
    L = M.rig().lip(pose, F.lip_set(t))
    a = Image.fromarray((L["lo_a"] * 255).astype(np.uint8))
    jq = round(jaw / 0.25) * 0.25
    if jq > 1e-3:
        a = a.rotate(-jq, resample=Image.BICUBIC, center=(M.HINGE[0] * M.S, M.HINGE[1] * M.S))
    m = zoom_mask(np.asarray(a, np.float32) / 255) & ~zoom_mask(M.rig().a_head)
    return m, pose


res = {}
# 1 fibre: luma std of the 1-3 px band-pass inside the lower lip (eroded 4 px), decoded mp4
fib = {}
for t in (6.0, 17.0, 29.0, 46.0, 54.0):
    f = frame(t).astype(np.float64)
    L = f @ [0.299, 0.587, 0.114]
    m, pose = lower_lip_mask(t)
    m = cv2.erode(m.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    hp = L - cv2.GaussianBlur(L, (0, 0), 3)
    fib[f"{t}"] = dict(pose=pose, std=round(float(hp[m].std()), 2), px=int(m.sum()))
    if t == 6.0:
        ys, xs = np.nonzero(m); cy, cx = int(ys.mean()), int(xs.mean())
        Image.fromarray(f.astype(np.uint8)[cy - 60:cy + 60, cx - 80:cx + 80]).resize((640, 480), Image.NEAREST).save(OUT / "closeup_4x_06.png")
res["fibre_luma_std_lower_lip"] = fib
res["fibre_pass"] = all(v["std"] >= 4 for v in fib.values())
# 2 scissor wobble: lower-lip and head contours vs a smooth (sigma 12 px along the arc) version, per 20 px window
def wobble(mask):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=len)[:, 0, :].astype(np.float64)
    keep = (c[:, 0] > 2) & (c[:, 0] < 957) & (c[:, 1] > 2) & (c[:, 1] < 537)   # cut edges only, not frame edges
    k_ = np.exp(-0.5 * (np.arange(-36, 37) / 12.0) ** 2); k_ /= k_.sum()
    sm = np.stack([np.convolve(np.r_[c[-36:, k], c[:, k], c[:36, k]], k_, "valid") for k in (0, 1)], 1)
    dev = np.linalg.norm(c - sm, axis=1)
    win = [dev[i:i + 20].max() for i in range(0, len(c) - 20, 20) if keep[i:i + 20].all()]
    return dict(windows=len(win), frac_ge_1px=round(float(np.mean(np.array(win) >= 1.0)), 3), median_max_dev=round(float(np.median(win)), 2))
def m2x(a): return zoom_mask(a)
pose = "A"
Lp = M.rig().lip(pose, "A")
res["wobble"] = dict(lower_lip=wobble(m2x(Lp["lo_a"])), upper_lip=wobble(m2x(Lp["up_a"])), head=wobble(m2x(M.rig().a_head)))
# 3 gong: max luma of the assembled card gong (frame at 20 s, gong region)
f = frame(20.0).astype(np.float64); Lg = f @ [0.299, 0.587, 0.114]
g = Lg[150:330, 760:940]; gm = cv2.erode((np.abs(f[150:330, 760:940, 0] - f[150:330, 760:940, 2]) > 40).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
res["gong_max_luma"] = round(float(g[gm].max()), 1); res["gong_pass"] = res["gong_max_luma"] <= 240
# 4 popcorn medial p: decoded pose path between 'po' and 'corn' in S1 / S3, and a pixel openness metric
def path(t0, t1):
    return [(round(k / 24, 3), F.TRACK.frame(k / 24)[0]) for k in range(int(t0 * 24), int(t1 * 24) + 1)]
pc = {}
for sec in ("S1", "S3"):
    syl = {s["seg_id"]: s for s in F.FT[sec]["syllables"]}
    a, b = syl["L3.w3.s1"], syl["L3.w3.s2"]
    p = path(a["t0"] - 0.05, b["t0"] + 0.15)
    # closed (onset p) -> open (o) -> closed again for >= 2 frames (medial p) -> before 'corn'
    seq = [x[1] in ("MBP", "hm") for x in p if x[0] < b["t0"] + 0.02]
    i = seq.index(True); j = seq.index(False, i); k = seq.index(True, j) if True in seq[j:] else None
    run = 0
    if k is not None:
        while k + run < len(seq) and seq[k + run]: run += 1
    closed = [None] * run
    op = []
    for tt, _ in p:
        fr = frame(tt + 0.001).astype(np.float64)
        reg = fr[150:400, 150:450]; lum = reg @ [0.299, 0.587, 0.114]
        cav = ((reg[..., 0] - reg[..., 2] > 25) & (lum < 95)) | ((lum > 205) & (np.abs(reg[..., 0] - reg[..., 2]) < 40))
        op.append((tt, int(cav.sum())))
    pc[sec] = dict(po=(a["t0"], a["t1"]), corn=(b["t0"], b["t1"]), path=p, closed_frames_after_po_vowel=len(closed), openness_px=op)
res["popcorn"] = pc
res["popcorn_pass"] = all(v["closed_frames_after_po_vowel"] >= 2 for v in pc.values())
# 5 frames where the cavity wedge poked (critic 0:08.2, 0:21.7)
for t in (8.2, 21.7):
    Image.fromarray(frame(t)[100:420, 150:470]).resize((640, 640), Image.NEAREST).save(OUT / f"fv_{t}.png")
# 6 S5 room-tone level (decoded audio)
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(MP4), "-f", "s16le", "-ac", "1", "-ar", "44100", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
def dbfs(a, b):
    s = x[int(a * 44100):int(b * 44100)]; return round(float(20 * np.log10(np.sqrt((s * s).mean()) + 1e-12)), 1)
res["room_tone_dBFS"] = {"S0 0.0-1.9": dbfs(0.0, 1.9), "S5 31.5-37.5": dbfs(31.5, 37.5), "S7 46-51.5": dbfs(46, 51.5)}
# 7 captions: first visible frame vs ledger
cap = {}
for rid in ("R1", "R2", "R3", "R4"):
    r = F.RESP[rid]; t = r["t_said"]
    cap[rid] = dict(t_said=t, label=r["on_screen_label"], first_frame=F.SHOW[rid][0])
res["captions"] = cap
json.dump(res, open(SW / "e3_check.json", "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "popcorn"}, indent=1))
print({s: (v["closed_frames_after_po_vowel"], v["path"]) for s, v in pc.items()})
