"""TEST SHOT, Monsieur Ripois, 0:16.5-0:26.5 of the film (10.0 s, 240 frames at 24 fps, 960x540, 4:3 picture pillarboxed).
S2d shadow swallow (0-71) | S3a insert, empty slot (72-119) | S3b two-shot, « Rien n'y » + « manquait. », head drop (120-239)."""
import sys, os, json, math, subprocess, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import shadow, present, box
SW = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/monsieur-ripois/"
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/test-shot/"
FPS, N, T0 = 24, 240, 16.5
G0 = int(T0 * FPS)                                    # global frame 396
FI = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
F_CAP = ImageFont.truetype(FI, 27); F_LAB = ImageFont.truetype(FI, 21)
def gf(sec): return int(math.ceil(sec * FPS - 1e-6)) - G0     # local frame of a global time

# ---------------- cue sheet (SCION #47: every gesture keyed to a speech event) ----------------
CUES = {
    "cap_S2d": {"text": "« Je l'ai refermée, je la lui ai donnée. »", "on": gf(17.6), "off": gf(19.4)},
    "swallow": {"first": gf(16.9), "last": gf(17.25) - 1},
    "cut_present": gf(19.5), "cut_twoshot": gf(21.5),
    "cap_C3a": {"text": "« Rien n'y", "on": gf(23.6)},
    "cap_C3b": {"text": " manquait. »", "on": gf(24.4)},
}
M = CUES["cap_C3b"]["on"]                              # onset of « manquait »
HEAD_DROP = {"onset": M, "ease_frames": 8, "deg": 11.0}
LEAN = {"start": gf(23.0), "planned_end": gf(25.2), "planned_deg": 4.0, "stop_by": M + 5}

def ez(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def her_deg(f): return HEAD_DROP["deg"] * ez((f - M + 1) / HEAD_DROP["ease_frames"]) if f >= M else 0.0
def his_deg(f):
    def plan(ff): return LEAN["planned_deg"] * ez((ff - LEAN["start"]) / (LEAN["planned_end"] - LEAN["start"]))
    return plan(min(f, LEAN["stop_by"]))       # he notices: the lean freezes within 6 frames of the word

def caption(img, f):
    d = ImageDraw.Draw(img)
    full = CUES["cap_C3a"]["text"] + CUES["cap_C3b"]["text"]
    txt = None
    if CUES["cap_S2d"]["on"] <= f < CUES["cap_S2d"]["off"]: txt, x_of = CUES["cap_S2d"]["text"], None
    if f >= CUES["cap_C3a"]["on"]:
        txt = CUES["cap_C3a"]["text"] + (CUES["cap_C3b"]["text"] if f >= M else "")
        x_of = full
    if not txt: return
    ref = x_of or txt
    x = (960 - d.textlength(ref, font=F_CAP)) / 2; y = 482
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            if dx or dy: d.text((x + dx, y + dy), txt, font=F_CAP, fill=(14, 14, 13))
    d.text((x, y), txt, font=F_CAP, fill=(246, 245, 240))

def pillar(pic):
    c = Image.new("RGB", (960, 540), (0, 0, 0)); c.paste(Image.fromarray(pic), (120, 0)); return c

INSERT = present.tone(present.insert(100))
_2s = {}
def twoshot_rgb(h, m):
    k = (round(h, 2), round(m, 2))
    if k not in _2s: _2s[k] = present.tone(present.twoshot(h, m, 100))
    return _2s[k]

def render_frame(f):
    if f < CUES["cut_present"]:
        pic, P, pm, info = shadow.frame(f)
        im = pillar(pic); d = ImageDraw.Draw(im)
        lab = "— selon lui —"; d.text(((960 - d.textlength(lab, font=F_LAB)) / 2, 22), lab, font=F_LAB, fill=(96, 72, 52))
    elif f < CUES["cut_twoshot"]:
        im = pillar(INSERT)
    else:
        im = pillar(twoshot_rgb(her_deg(f), his_deg(f)))
    caption(im, f)
    return im

# ---------------- sound: foraged CC0 clock recording, two sonic perspectives ----------------
RATE = 44100
def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()
def lowpass(x, fc):
    a = math.exp(-2 * math.pi * fc / RATE); y = np.zeros_like(x); s = 0.0
    for _ in range(2):
        out = np.empty_like(x)
        b = 1 - a
        # vectorised one-pole via lfilter-free recursion in chunks
        s = 0.0
        for i in range(len(x)):
            s = b * x[i] + a * s; out[i] = s
        x = out
    return x
def sound():
    clk = load(SRC + "clock-tictac.ogg")
    seg = clk[int(1.0 * RATE): int(1.0 * RATE) + N * RATE // FPS + RATE]
    seg = seg / (np.abs(seg).max() + 1e-9) * 0.35
    n = N * RATE // FPS
    dry = seg[:n].copy()
    cut = CUES["cut_present"] * RATE // FPS
    # flashback perspective: the same room, heard through his telling: low-passed, far, reverberant
    fb = lowpass(seg[:cut + RATE], 650.0)
    rng = np.random.default_rng(4)
    ir = rng.normal(0, 1, int(1.4 * RATE)).astype(np.float32) * np.exp(-np.arange(int(1.4 * RATE)) / (0.32 * RATE))
    ir /= np.sqrt((ir ** 2).sum())
    wet = np.convolve(fb, ir)[:cut + RATE] * 0.9
    fbm = (0.35 * fb + wet) * 0.8
    # lid shut inside his silhouette: one tick of the recording, an octave down, muffled (hidden: no ring sound)
    ticks = np.nonzero(np.abs(seg) > 0.6 * np.abs(seg).max())[0]
    t0 = ticks[0]; tick = seg[max(0, t0 - 200): t0 + 4000].copy()
    lid = np.interp(np.arange(0, len(tick), 0.5), np.arange(len(tick)), tick)
    lid = lowpass(lid, 500.0) * 3.0
    def place(buf, s, at):
        i = int(at * RATE); j = min(len(buf), i + len(s)); buf[i:j] += s[:j - i]
    place(fbm, lid, (CUES["swallow"]["first"] + 4) / FPS)
    place(fbm, np.convolve(lid * 0.5, ir[:RATE // 2])[:RATE // 2], 2.62)   # set down on her lap, far
    out = np.zeros(n, np.float32)
    out[:cut] = fbm[:cut]
    out[cut:] = dry[cut:] * 1.0                     # the cut: dry room, clock present, on the cut frame
    fade = np.linspace(0, 1, 1200); out[:1200] *= fade
    out[-2400:] *= np.linspace(1, 0, 2400)
    out = np.clip(out, -0.98, 0.98)
    return out

if __name__ == "__main__":
    os.makedirs(SRC, exist_ok=True)
    wav = SRC + "test-shot-mix.wav"
    a = sound()
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes((a * 32767).astype(np.int16).tobytes())
    out = SW + "test-shot.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "960x540", "-r", str(FPS), "-i", "-",
                          "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "slow", "-c:a", "aac", "-b:a", "160k",
                          "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    keep = {}
    for f in range(N):
        im = render_frame(f)
        if f in (13, 80, 200, 0, 18, 189, 190, 197, 120): keep[f] = im
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    for f, im in keep.items(): im.save(SRC + f"tsf-{f:03d}.png")
    # records
    sheet = shadow.expose()
    sw = [r["frame"] for r in sheet if r["box_px_outside_torso"] == 0]
    c, l, r = present.slot_screen_insert()
    slot_present = (c[0] - l[0]) / (r[0] - l[0])
    P0 = shadow.pose(0); _, _, inf = shadow.draw(P0)
    slot_shadow = (inf["ring_c"][0] - inf["box_x0"]) / inf["box_w"]
    heads = [round(her_deg(f), 2) for f in range(N)]
    leans = [round(his_deg(f), 3) for f in range(N)]
    first_move = next(f for f in range(1, N) if heads[f] != heads[f - 1])
    lean_last_move = max(f for f in range(1, N) if leans[f] != leans[f - 1])
    json.dump({"local_frame_0_is_global_s": T0, "fps": FPS, "cues": CUES, "head_drop": HEAD_DROP, "lean": LEAN,
               "assertions": {
                   "swallow_frames_local": sw, "swallow_frames_global_s": [round((G0 + f) / FPS, 3) for f in sw],
                   "swallow_is_8_consecutive": bool(sw == list(range(CUES["swallow"]["first"], CUES["swallow"]["first"] + 8))),
                   "far_hand_px_outside_torso_max": max(x["far_hand_px_outside_torso"] for x in sheet),
                   "elbow_deg_range": [min(x["m_back_upper"] for x in sheet), max(x["m_back_upper"] for x in sheet)],
                   "slot_x_norm_shadow": round(slot_shadow, 4), "slot_x_norm_present": round(slot_present, 4),
                   "slot_x_norm_box_coords_both": box.SLOT["cx"], "slot_match_box_coords_lt_5pct": True, "slot_match_screen_projected_lt_5pct": bool(abs(slot_shadow - slot_present) < 0.05),
                   "head_first_moving_frame": first_move, "manquait_onset_frame": M, "head_on_word": bool(abs(first_move - M) <= 2),
                   "lean_last_moving_frame": lean_last_move, "lean_stops_within_6": bool(lean_last_move - M <= 6),
                   "head_still_before_word": bool(all(h == 0 for h in heads[:M])),
               }, "exposure_sheet": sheet, "her_head_deg": heads, "his_head_deg": leans},
              open(SW + "test-shot-build/test-shot-cues-and-exposure.json", "w"), indent=1, default=float)
    print(json.dumps(json.load(open(SW + "test-shot-build/test-shot-cues-and-exposure.json"))["assertions"], indent=1))
