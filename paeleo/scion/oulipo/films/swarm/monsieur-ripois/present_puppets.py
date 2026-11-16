"""PRESENT-TENSE puppets for « Rien n'y manquait » (U2 present-cutout, full build).

FORAGED: LoC 2017831564 (John Vachon, May 1942, FSA/OWI, no known restrictions) cut into GrabCut pieces (SCION #29)
articulated by FK at pivots with angle limits (#32); her gloved hand from the sister frame LoC 2017831565 (8d04831) (same sitting).
HANDMADE: silver box (silver_box.py, geometry from box-spec.json), pawn receipt (typeset, stamped, folded, paper tooth).
Every gesture is keyed to a speech event (SCION #47) read from dialogue-cues.json, falling back to plan §6 times.

API (all return 720x540 RGB PIL images, picture area only):
    render_twoshot(t, keys=None)        t = film time in seconds (S1 2-9, S3b 21.5-29, S4 29-31.5, S5 36-43)
    render_box_insert(t, state='open')  state: closed | lid33 | lid66 | open | receipt ; t = seconds into the insert
    render_receipt_insert(t)            t = seconds into the receipt insert (0..4.5)
keys: None/'master' | 'late' | 'baseline' | dict overriding DEFAULT_KEYS (see below).
"""
import numpy as np, cv2, json, math, os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import silver_box as box
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/present/"
FPS = 24

# ---------------------------------------------------------------- keys (plan §6 fallbacks; overridden by dialogue-cues.json)
DEFAULT_KEYS = dict(
    setdown=(2.15, 2.95),        # she lowers the closed box onto her lap (S1 opening), settles with a small bounce
    lean_on=(3.4, 3.9), lean_off=5.0, lean_deg=3.0,   # his lean on « rapportée »
    lean2_start=22.6, lean2_end=25.2, lean2_deg=4.0,   # S3b: he leans in again during « Rien n'y… »
    lid_crack=(7.7, 8.15), lid_crack_deg=10.5,          # CUE-2a: thumbs lift the lid 10 % under « ouverte »
    setdown_px=76.0,
    head_drop=24.4, head_drop_deg=-11.0, head_drop_frames=8,   # CUE-3: onset of « manquait »
    his_stop=24.65,              # his lean stops (he notices)
    arm_withdraw=(27.0, 28.0),   # his right arm comes off the sofa back (the arm the shadow hid)
    pocket=(29.25, 29.5), receipt_fall=(29.4, 30.2),
    look_receipt=30.6, look_receipt_deg=-14.0,
    lid_open_by=19.5,            # box opened during the flashback (insert S3a lands on it open)
    receipt_to_slot=(36.6, 38.4),
    lid_close=(39.42, 39.5),     # 2 drawings
    turn_away=40.5, turn_away_deg=8.0,
    baseline=False,
)

def load_keys(variant="master"):
    """keys from U1's dialogue-cues.json gesture_keys[variant] (by cue_id); plan §6 times if absent"""
    k = dict(DEFAULT_KEYS); k["source"] = "plan §6 fallback"
    p = os.path.join(HERE, "dialogue-cues.json")
    try:
        gk = json.load(open(p))["gesture_keys"]
        cues = {c["cue_id"]: c for c in gk["master" if variant == "baseline" else variant]}
        F = lambda c, f="action_onset_frame": cues[c][f] / FPS
        k["lean_on"] = (F("CUE-1"), F("CUE-1", "action_end_frame")); k["lean_deg"] = cues["CUE-1"].get("value") or 3.0
        k["lean_off"] = 106 / FPS
        k["setdown"] = (F("CUE-1b"), F("CUE-1b", "action_end_frame") + 6 / FPS)     # contact at 70 % = action_end, settle +6 fr
        k["lid_crack"] = (F("CUE-2a"), F("CUE-2a", "action_end_frame")); k["lid_crack_deg"] = 105 * (cues["CUE-2a"].get("value") or 0.1)
        k["lid_open_by"] = F("CUT-S3a")
        k["lean2_start"] = F("CUE-3pre"); k["lean2_end"] = F("CUE-3pre", "action_end_frame"); k["lean2_deg"] = cues["CUE-3pre"].get("value") or 4.0
        k["head_drop"] = F("CUE-3"); k["head_drop_deg"] = cues["CUE-3"].get("value") or -11.0
        k["head_drop_frames"] = cues["CUE-3"]["action_end_frame"] - cues["CUE-3"]["action_onset_frame"]
        k["his_stop"] = F("CUE-3s")
        k["arm_withdraw"] = (F("CUE-3h"), F("CUE-3h", "action_end_frame"))
        k["receipt_fall"] = (F("CUE-4"), F("CUE-4", "action_end_frame")); k["pocket"] = (F("CUE-4") - 2 / FPS, F("CUE-4") + 6 / FPS)
        k["look_receipt"] = F("CUE-4L"); k["look_receipt_deg"] = -6.0
        k["receipt_to_slot"] = (F("CUE-5a"), F("CUE-5a", "action_end_frame"))
        k["lid_close"] = (F("CUE-5b"), F("CUE-5b", "action_end_frame"))
        k["turn_away"] = F("CUE-5c"); k["turn_away_deg"] = cues["CUE-5c"].get("value") or 8.0
        k["source"] = f"dialogue-cues.json gesture_keys[{'master' if variant == 'baseline' else variant}]"
    except Exception as e:
        k["source"] += f" ({type(e).__name__}: {e})"
        if variant == "late": k["head_drop"] = 25.2 + 12 / FPS
    if variant == "baseline":
        k["baseline"] = True; k["his_stop"] = 99.0
    if variant == "late" and k["source"].startswith("dialogue"):
        k["his_stop"] = max(k["his_stop"], k["lean2_end"])
    return k

def _keys(keys):
    if keys is None or keys == "master": return load_keys("master")
    if isinstance(keys, str): return load_keys(keys)
    k = load_keys("master"); k.update(keys); return k

def ease(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def twos(t): return math.floor(t * FPS / 2) * 2 / FPS            # drawings on twos

# ---------------------------------------------------------------- assets
g = cv2.imread(SRC + "plate-1440.png", 0).astype(np.float32) / 255
plate = cv2.imread(SRC + "plate-inpainted.png", 0).astype(np.float32) / 255
PJ = json.load(open(SRC + "pieces.json"))["pieces"]
masks = {n: cv2.imread(SRC + f"piece-{n}-mask.png", 0).astype(np.float32) / 255 for n in ("her_head", "his_head", "his_arm", "pocket")}
hand = cv2.imread(SRC + "v1-master-hand.png", 0).astype(np.float32) / 255
hand_a = cv2.imread(SRC + "piece-her_hand-mask.png", 0).astype(np.float32) / 255
m = cv2.imread(SRC + "v0-master-crop.png", 0).astype(np.float32) / 255
# editor repair 1: her glove JOINED to its coat sleeve (same V1 crop, GrabCut; editor-build/arm_piece.py) and the
# foreground sofa-arm occluder of V0 (editor-build/sofa_arm_mask.py): the box now sits on HER lap, behind that arm.
arm_a = cv2.imread(SRC + "piece-her_arm-mask.png", 0).astype(np.float32) / 255
OCC = cv2.imread(SRC + "sofa-arm-occluder-mask.png", 0).astype(np.float32) / 255
# repaint of the infill strip right of her profile: the first inpaint left a lighter jagged patch where his head's
# shadow falls on the wall; carry the plate's own border column (just outside her head mask) leftward, faded in.
def _fix_infill(pl):
    pl = pl.copy(); hm = cv2.imread(SRC + "piece-her_head-mask.png", 0) > 20
    for y in range(80, 500):
        xs = np.where(hm[y])[0]
        if len(xs) == 0: continue
        xr = min(1439, xs.max() + 4)
        ref = float(np.median(g[y, xr:xr + 6]))
        x0 = max(xs.min(), xr - 140)
        w = np.clip((np.arange(x0, xr) - x0) / max(1, xr - x0), 0, 1) ** 1.2
        pl[y, x0:xr] = pl[y, x0:xr] * (1 - w) + (ref + (pl[y, x0:xr] - cv2.GaussianBlur(pl, (0, 0), 3)[y, x0:xr])) * w
    return pl
plate = _fix_infill(plate)
def _ring_inpaint(pl):
    """the head mask was cut tight, so a fringe of curls/halo stays on the plate just outside it and shows as a jagged
    light line once the head card turns. Re-inpaint a ring across the old contour (Telea) from both sides."""
    hm = (cv2.imread(SRC + "piece-her_head-mask.png", 0) > 20).astype(np.uint8)
    ring = cv2.dilate(hm, np.ones((23, 23), np.uint8)) - cv2.erode(hm, np.ones((9, 9), np.uint8))
    ring[485:] = 0                                            # keep her collar and his arm below the neck as photographed
    u8 = np.clip(pl * 255, 0, 255).astype(np.uint8)
    out = cv2.inpaint(u8, ring, 9, cv2.INPAINT_TELEA).astype(np.float32) / 255
    rs = cv2.GaussianBlur(ring.astype(np.float32), (0, 0), 3)
    grain = g - cv2.GaussianBlur(g, (0, 0), 2)               # put the print's own grain back over the smooth fill
    return pl * (1 - rs) + (out + np.roll(grain, 40, 1)) * rs
plate = _ring_inpaint(plate)

# film grain sampled from the print itself (high-pass of a plain wall patch at native resolution)
_patch = m[126:1000, 4662:5922]
_res = _patch - cv2.GaussianBlur(_patch, (0, 0), 6)
_res = cv2.resize(_res, (_res.shape[1] // 2, _res.shape[0] // 2), interpolation=cv2.INTER_AREA)
GRAIN_STD_SRC = float(_res.std())
def grain_field(h, w, seed):
    r = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); ph, pw = _res.shape
    for y in range(0, h, ph):
        for x in range(0, w, pw):
            t = np.roll(np.roll(_res, r.integers(0, ph // 2), 0), r.integers(0, pw // 2), 1)
            out[y:y + ph, x:x + pw] = t[:min(ph, h - y), :min(pw, w - x)]
    return out
GRAINS = [grain_field(540, 720, s) for s in range(6)]       # grain changes per frame like film (cycled)

# darkroom burn of the background plate (separately from the figures), key pool on the faces (V0 key: camera-right flash)
couple = cv2.imread(SRC + "matte-couple.png", 0).astype(np.float32) / 255
COUPLE_POLY = [(30,520),(150,470),(230,330),(330,80),(500,100),(600,330),(700,370),(800,250),(820,60),(950,10),(1060,60),(1060,300),(1180,420),(1270,560),(1330,750),(1340,880),(1380,1080),(840,1080),(780,840),(700,770),(400,700),(30,690)]
_P = np.zeros_like(couple); cv2.fillPoly(_P, [np.array(COUPLE_POLY, np.int32)], 1.0)
FIG = cv2.GaussianBlur(np.maximum(couple, cv2.erode(_P, np.ones((41, 41), np.uint8))) * _P, (0, 0), 3)
_yy, _xx = np.mgrid[0:1080, 0:1440].astype(np.float32)
KEYF = 0.50 + 0.55 * np.exp(-(((_xx - 820) / 700) ** 2 + ((_yy - 330) / 560) ** 2))
_HEADS = cv2.GaussianBlur(cv2.dilate(((masks["her_head"] + masks["his_head"]) > 0.05).astype(np.float32), np.ones((61, 61), np.uint8)), (0, 0), 10)
FIG_S = FIG * (1 - _HEADS) + cv2.GaussianBlur(FIG, (0, 0), 45) * _HEADS     # smooth burn field where heads turn (no edge tied to the old contour)
BURN = (0.60 + 0.40 * FIG_S) * KEYF
BURN_PIECE = (0.60 + 0.40 * cv2.GaussianBlur(couple, (0, 0), 3)) * KEYF

def tone(x, seed=0, gmask=None):
    """ONE unifying curve for every present shot (fixed constants): print blacks ~34, paper white on the key highlights,
    the print's own grain, a faint green-grey cast in the shadows (reference chroma ~6)."""
    x = np.clip(x, 0, 1.25)
    y = np.clip((x - 0.05) / 0.74, 0, 1) ** 1.7
    gr = GRAINS[seed % len(GRAINS)][:x.shape[0], :x.shape[1]] * 255
    if gmask is not None: gr = gr * gmask          # editor repair 1: the print grain goes on the Vachon plate only
    L = 34 + (252 - 34) * y + gr
    L = np.clip(L, 0, 255)
    sh = np.clip(1 - L / 150, 0, 1)
    rgb = np.stack([L - 5 * sh, L + 5 * sh, L + 0.5 * sh], -1)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")

def rot(img, a, piv, deg, size=(1440, 1080)):
    M = cv2.getRotationMatrix2D(tuple(map(float, piv)), deg, 1.0)
    return (cv2.warpAffine(img, M, size, flags=cv2.INTER_CUBIC), cv2.warpAffine(a, M, size, flags=cv2.INTER_LINEAR))

# ---------------------------------------------------------------- the handmade receipt (texture)
FONT_DIR = "/usr/share/fonts/truetype/"
def _font(name, size):
    for p in (FONT_DIR + name,):
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def _receipt_tex():
    W, H = 1000, 640
    rng = np.random.default_rng(1953)
    tooth = sum(cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), s) * a for s, a in ((0.6, 0.5), (2, 0.35), (9, 0.6), (40, 1.0)))
    base = 0.84 + 0.018 * tooth
    img = Image.fromarray(np.clip(base * 255, 0, 255).astype(np.uint8), "L")
    d = ImageDraw.Draw(img)
    serifB = _font("dejavu/DejaVuSerif-Bold.ttf", 54); serif = _font("liberation/LiberationSerif-Regular.ttf", 30)
    mono = _font("liberation/LiberationMono-Regular.ttf", 27); hand_f = _font("liberation/LiberationSerif-Italic.ttf", 40)
    ink = 38
    d.rectangle([22, 22, W - 22, H - 22], outline=ink + 30, width=3); d.rectangle([32, 32, W - 32, H - 32], outline=ink + 60, width=1)
    d.text((W // 2, 62), "MONT-DE-PIÉTÉ", font=serifB, fill=ink, anchor="mt")
    d.text((W // 2, 128), "Bureau auxiliaire n° 7  ·  Reconnaissance  N° 48 213", font=serif, fill=ink + 10, anchor="mt")
    d.line([(70, 178), (W - 70, 178)], fill=ink + 40, width=2)
    rows = [("Engagé le", "14 mars 1953", 222), ("Objet", "une bague or, un brillant", 302), ("Prêt", "9 000 F", 382), ("Déposant :", "A. R.", 462)]
    for lab, val, y in rows:
        d.text((80, y), lab, font=mono, fill=ink + 20)
        x0 = 80 + int(d.textlength(lab, font=mono)) + 18
        for x in range(x0, W - 80, 12): d.line([(x, y + 34), (x + 5, y + 34)], fill=ink + 70, width=2)   # dotted fill-in line
        d.text((x0 + 14, y - 8), val, font=hand_f, fill=22)                                              # clerk's hand
    d.text((80, 548), "Le présent bulletin doit être représenté pour tout dégagement.", font=_font("liberation/LiberationSerif-Italic.ttf", 22), fill=ink + 40)
    a = np.asarray(img).astype(np.float32) / 255
    # off-axis ENGAGÉ stamp: double frame, ink that breaks up on the paper tooth
    st = Image.new("L", (440, 170), 0); sd = ImageDraw.Draw(st)
    sd.rectangle([4, 4, 436, 166], outline=255, width=7); sd.rectangle([18, 18, 422, 152], outline=255, width=3)
    sd.text((220, 88), "ENGAGÉ", font=_font("dejavu/DejaVuSerif-Bold.ttf", 92), fill=255, anchor="mm")
    st = st.rotate(-13, resample=Image.BICUBIC, expand=True)
    S = np.zeros((H, W), np.float32); sx, sy = 455, 262
    sa = np.asarray(st).astype(np.float32) / 255
    hh, ww = sa.shape; S[sy:sy + hh, sx:sx + ww] = sa[:H - sy, :W - sx]
    brk = np.clip(0.55 + 0.9 * (cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.2) + 0.4 * tooth), 0, 1)
    a = a * (1 - 0.52 * S * brk)
    a = a * (1 - 0.06 * np.clip(-tooth, 0, 3))
    return a
RECEIPT = _receipt_tex()

def _folded_slip(w, h, ang):
    """the slip folded across its middle; ang 180 = shut, 0 = flat open. Returns gray, alpha of size (h, w*?)"""
    R = cv2.resize(RECEIPT, (w, h), interpolation=cv2.INTER_AREA)
    out = np.zeros((h, w), np.float32); al = np.zeros_like(out)
    lo = R[h // 2:]; out[h // 2:] = lo; al[h // 2:] = 1
    c = math.cos(math.radians(ang)); hh = int(round(abs(c) * (h // 2)))
    if hh >= 1:
        if c > 0: top = cv2.resize(R[:h // 2], (w, hh), interpolation=cv2.INTER_AREA) * (0.86 + 0.14 * c)
        else:     # back of the paper: the same sheet seen from behind, its print showing through faintly, mirrored
            bk = cv2.resize(R[:h // 2][:, ::-1], (w, hh), interpolation=cv2.INTER_AREA)
            top = (0.80 + 0.22 * (bk - 0.84)) * (0.9 + 0.1 * abs(c))
        if c > 0: out[h // 2 - hh:h // 2] = top; al[h // 2 - hh:h // 2] = 1
        else:     out[h // 2:h // 2 + hh] = top; al[h // 2:h // 2 + hh] = 1
    crease = np.exp(-((np.arange(h) - h / 2) / 2.5) ** 2)[:, None]
    out = out * (1 - 0.18 * crease)
    return out, al

# ---------------------------------------------------------------- the two-shot
BOX_W_PX = None
BOX_CX, BOX_CY, BOX_F = 900.0, 820.0, 470.0
def _box_cam(drop):
    # editor repair 2: the box sits LOW, in the lower third (centre >= 0.667H), on the sofa seat edge between them,
    # just beyond the end of the foreground sofa arm, which still occludes its left foot; she reaches over the arm to it.
    return box.Cam(yaw=-14, pitch=50, dist=2.4, f=BOX_F, cx=BOX_CX, cy=BOX_CY - drop)
# at two-shot scale the mirror lid should read as a silvered glint of the room, not as a second picture
ENV2S = np.clip(cv2.GaussianBlur(g, (0, 0), 14) * 255, 0, 255).astype(np.uint8)
_box_cache = {}
def _lap_box(lid, drop, receipt):
    key = (round(lid, 1), int(round(drop)), round(receipt, 2))
    if key not in _box_cache:
        if len(_box_cache) > 40: _box_cache.clear()
        _box_cache[key] = box.render(_box_cam(drop), (1440, 1080), lid, ENV2S, ss=2, receipt=receipt)
    return _box_cache[key]

def _place(canvas_g, canvas_a, img, a, M, size=(1440, 1080)):
    ti = cv2.warpAffine(img, M, size, flags=cv2.INTER_AREA if M[0, 0] < 1 else cv2.INTER_CUBIC)
    ta = cv2.warpAffine(a, M, size, flags=cv2.INTER_LINEAR)
    return ti, ta

def _hand_M(anchor, scale, mirror, roll):
    """V1 hand crop -> plate: the knuckle line of the glove (src ~ (450, 520)) is placed on `anchor`"""
    sx = -scale if mirror else scale
    c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
    A = np.array([[sx * c, -scale * s], [sx * s, scale * c]])
    src = np.array([450.0, 520.0]); t = np.array(anchor) - A @ src
    return np.hstack([A, t[:, None]]).astype(np.float32)

TURN_DEG = -14.0      # her final head angle after the turn away (plan sign: − = down/away); limit declared in assembly.md

def state_at(t, k):
    """all puppet parameters at film time t (also written to present-manifest for the editor)"""
    td = twos(t)
    s = {}
    # box set down (S1): lifted 46 px in her hands, lowered with ease-in, one fabric bounce, settle
    a0, a1 = k["setdown"]
    A0 = k["setdown_px"]
    if t < a0: drop = A0
    elif t < a1:
        u = (td - a0) / (a1 - a0)
        drop = A0 * (1 - (u / 0.7) ** 2) if u < 0.7 else -4 * math.sin(math.pi * (u - 0.7) / 0.3)   # accelerate, contact, squash-settle
    else: drop = 0.0
    s["box_drop"] = drop
    s["box_landed"] = float(t >= a0 + 0.7 * (a1 - a0))
    # lid
    lid = 0.0
    if not k["baseline"] and t >= k["lid_crack"][0]:
        lid = k["lid_crack_deg"] * (0.5 if td < k["lid_crack"][1] else 1.0)
    if t >= k["lid_open_by"] and not k["baseline"]: lid = 105.0
    c0, c1 = k["lid_close"]
    if t >= c0 and lid > 0: lid = 55.0
    if t >= c1: lid = 0.0
    s["lid"] = lid
    # her head (plan sign: negative = drops toward the box)
    her = 0.0
    if not k["baseline"]:
        f = (t - k["head_drop"]) * FPS
        if f >= 0: her = k["head_drop_deg"] * ease(f / k["head_drop_frames"])
        if t >= k["look_receipt"] and t < k["receipt_to_slot"][1] + 0.5:
            her = her + (k["look_receipt_deg"] - k["head_drop_deg"]) * ease((td - k["look_receipt"]) / (10 / FPS))
        if t >= k["receipt_to_slot"][1] + 0.5:
            her = k["head_drop_deg"]
        s["her_shift"] = 0.0
        if t >= k["turn_away"]:
            # editor repair 1: the TURN AWAY as a cutout card turn (replacement by the mirrored head card): the head
            # card narrows to edge-on over 4 frames, swaps to its mirror and opens over 4 frames, so her face ends
            # looking toward frame-left, away from him, dropped 14 deg; her figure leans back from him 16 plate px,
            # following 2 frames behind the head (overlapping action). Drawings on twos.
            f = round((td - k["turn_away"]) * FPS, 6)
            # editor repair 2: no edge-on sliver drawings. The head card first drops toward the box (4 frames), then
            # ONE hard replacement cut to the mirrored card (Reiniger-style substitution), which keeps dropping.
            sx = 1.0 if f < 4 else -1.0
            s["her_flip"] = sx
            her = k["head_drop_deg"] + (TURN_DEG - k["head_drop_deg"]) * ease(f / 8)
            s["her_shift"] = -16.0 * ease((f - 2) / 12)
    s.setdefault("her_shift", 0.0)
    s["her_head"] = her
    # his head lean
    l0, l1 = k["lean_on"]; L = k["lean_deg"]
    his = 0.0
    if l0 <= t < k["lean_off"]: his = L * ease((td - l0) / (l1 - l0))
    elif k["lean_off"] <= t < k["lean_off"] + 0.6: his = L * (1 - ease((td - k["lean_off"]) / 0.6))
    if t >= k["lean2_start"]:
        tt = min(td, k["his_stop"])
        his = k["lean2_deg"] * ease((tt - k["lean2_start"]) / (k["lean2_end"] - k["lean2_start"]))
    s["his_head"] = his
    # his arm off the sofa back
    w0, w1 = k["arm_withdraw"]
    s["his_arm"] = -5.0 * ease((td - w0) / (w1 - w0)) if t >= w0 else 0.0
    # pocket flap + receipt
    s["pocket"] = 0.0; s["receipt"] = None; s["receipt_in_slot"] = 0.0
    if not k["baseline"]:
        p0, p1 = k["pocket"]
        if p0 <= t < p1 + 0.3: s["pocket"] = 8.0 * math.sin(math.pi * min(1, (t - p0) / (p1 + 0.3 - p0)))
        f0, f1 = k["receipt_fall"]
        start = np.array([1146.0, 702.0]); land = np.array([1170.0, 935.0])     # editor repair 2: lands on his thigh, right of the box
        if f0 <= t < f1:
            u = (t - f0) / (f1 - f0)
            if u < 0.40:   # slides out of the welt (editor repair: held ~7 frames instead of 3 so it reads)
                v = u / 0.40; s["receipt"] = (start + [0, -26 * v], 0.0, 1.0)
            elif u < 0.80:  # falls: constant acceleration (gravity), slight forward drift, tumbling
                v = (u - 0.40) / 0.40
                p = start + [0, -26] + (land - start - [0, -26]) * np.array([v, v * v])
                s["receipt"] = (p, 70 * v * v, 1.0)
            else:           # one small bounce (restitution ~0.25) and settle
                v = (u - 0.80) / 0.20
                hb = 12 * math.sin(math.pi * min(1, v / 0.6)) if v < 0.6 else 0
                s["receipt"] = (land - [0, hb], 70 + 8 * math.sin(math.pi * v), 1.0)
        elif f1 <= t:
            r0, r1 = k["receipt_to_slot"]
            if t < 36.0: s["receipt"] = (land, 78.0, 1.0)          # on his thigh until the insert (she has picked it up)
            elif t < r1:
                # S5: the folded slip is in her gloved fingers; her arm carries it over the box and lowers it into the slit
                v = ease((td - r0) / (r1 - r0)) if t >= r0 else 0.0
                s["carry"] = v; s["receipt"] = "in_hand"
            else:
                s["receipt_in_slot"] = 1.0 if lid > 0 else 0.0
                s["carry"] = max(0.0, 1.0 - ease((td - r1) / 0.6))
    return s

PLATE_BURNED = (g * BURN).astype(np.float32)
_ny, _nx = np.mgrid[0:1080, 0:1440].astype(np.float32)
NECK_A = cv2.GaussianBlur((masks["her_head"] > 0.05).astype(np.float32), (0, 0), 2) * np.clip((_ny - 448) / 22, 0, 1) * np.clip((548 - _nx) / 14, 0, 1)
CARD_FEATHER = 1 - np.clip((_ny - 452) / 30, 0, 1)
FLIP_AXIS_X = 430.0   # her head card turns about its own centre line

def _flip_M(piv, deg, sx):
    """cutout 'card turn' (Reiniger): rotate the head card about the neck pin, then narrow it about its centre line;
    sx runs 1 -> 0.15 (card edge-on), swaps to the mirrored card, -0.15 -> -1: she now faces away from him."""
    Rm = np.vstack([cv2.getRotationMatrix2D(tuple(map(float, piv)), deg, 1.0), [0, 0, 1]])
    S = np.array([[sx, 0, FLIP_AXIS_X * (1 - sx)], [0, 1, 0], [0, 0, 1]], np.float64)
    return (S @ Rm)[:2].astype(np.float32)

def render_twoshot(t, keys=None, return_state=False):
    k = _keys(keys); s = state_at(t, k)
    c = plate.copy()
    # pieces under the box: his arm (on the sofa back) and the pocket flap ride on the plate
    layers = []
    # cv2 angle: + = counter-clockwise. her_head (plan sign) − = drop toward the box = clockwise; his + = lean toward her
    for n, deg in (("his_arm", s["his_arm"]), ("pocket", s["pocket"]), ("his_head", s["his_head"]), ("her_head", s["her_head"])):
        piv = PJ[n]["pivot"]
        if n == "her_head" and s.get("her_flip", 1.0) != 1.0:
            M = _flip_M(piv, deg, s["her_flip"])
            pi = cv2.warpAffine(g, M, (1440, 1080), flags=cv2.INTER_CUBIC); pa = cv2.warpAffine(masks[n], M, (1440, 1080))
        else:
            pi, pa = rot(g, masks[n], piv, deg)
        sh = np.roll(np.roll(cv2.GaussianBlur(pa, (0, 0), 5), 4, 0), -5, 1)
        c = c * (1 - (0.08 if n == 'her_head' else 0.18) * sh * (1 - pa))          # each card casts a faint contact shadow away from the key
        # the piece carries the plate's burn at its border (any wall it took with it matches the plate) and the key on its core
        core = cv2.GaussianBlur(cv2.erode((masks[n] > 0.5).astype(np.float32), np.ones((31, 31), np.uint8)), (0, 0), 8)
        if n == "her_head" and s.get("her_flip", 1.0) != 1.0:
            pb = cv2.warpAffine(BURN * (1 - core) + BURN_PIECE * core, _flip_M(piv, deg, s["her_flip"]), (1440, 1080), flags=cv2.INTER_LINEAR)
        else:
            pb, _ = rot(BURN * (1 - core) + BURN_PIECE * core, masks[n], piv, deg)
        layers.append((n, pi * pb, pa))
    c = c * BURN
    for n, pi, pa in layers:
        c = c * (1 - pa) + pi * pa
    if s.get("her_flip", 1.0) != 1.0:
        # editor repair 2: the mirrored head card's lower edge and the old jaw line met the collar in a hard horizontal
        # seam. Repaint that nape band (between both head contours and the collar) with her own curls continued down.
        hp = [pa for n, pi, pa in layers if n == "her_head"][0]
        band = (((masks["her_head"] > 0.05) | (hp > 0.05)) & (_ny > 458) & (_ny < 503)).astype(np.uint8)
        band = cv2.dilate(band, np.ones((5, 9), np.uint8)); band[:446] = 0; band[506:] = 0
        y0, y1 = 420, 530
        # curls at the nape: the hair just above the band continues down (rows reflected about y=458, so the texture
        # is the photograph's own curls, not a smooth smear), and dissolves into the collar along an irregular edge.
        ys = np.arange(y0, y1)
        src = np.clip(np.where(ys < 458, ys, 916 - ys), 0, 1079)
        ramp = np.clip((ys.astype(np.float32) - 458) / 46, 0, 1)[:, None]
        fill = c[src] * (1 - 0.18 * ramp)
        rng_ = np.random.default_rng(5)
        edge = cv2.GaussianBlur(rng_.normal(0, 1, (1, 1440)).astype(np.float32), (0, 0), 7)[0]; edge = edge / (edge.std() + 1e-6) * 5
        bot = np.clip((ys[:, None] - (494 + edge[None, :])) / 8, 0, 1)                # irregular lower edge of the hair
        band_f = band[y0:y1].astype(np.float32) * (1 - bot)
        bs = cv2.GaussianBlur(band_f, (0, 0), 2.0)
        c[y0:y1] = c[y0:y1] * (1 - bs) + fill * bs
    # her figure leans back from him (turn away): a smooth displacement of everything left of the gap between them
    if s.get("her_shift", 0.0) != 0.0:
        c = cv2.remap(c, *_shift_maps(s["her_shift"]), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # the receipt slip (folded), lying on / falling across his side
    SLIP = 1.3
    def slip_layer(p, ang, sc):
        sg, sa = _folded_slip(int(70 * sc * SLIP) + 2, int(84 * sc * SLIP) + 2, 180)
        sg = sg[sg.shape[0] // 2:]; sa = sa[sa.shape[0] // 2:]
        M = cv2.getRotationMatrix2D((sg.shape[1] / 2, sg.shape[0] / 2), ang, 1.0)
        M[:, 2] += [p[0] - sg.shape[1] / 2, p[1] - sg.shape[0] / 2]
        return cv2.warpAffine(sg, M, (1440, 1080), flags=cv2.INTER_CUBIC), cv2.warpAffine(sa, M, (1440, 1080))
    # editor repair 2: the made objects (box, slip) now carry the print's own sampled grain like everything else in the
    # photograph; only the V1 glove/sleeve (a photograph with its own grain) is kept out of the grain mask.
    made = np.zeros((1080, 1440), np.float32)
    if s["receipt"] is not None and s["receipt"] != "in_hand":
        ti, ta = slip_layer(*s["receipt"])
        sh = np.roll(np.roll(cv2.GaussianBlur(ta, (0, 0), 3), 3, 0), -3, 1)
        c = c * (1 - 0.3 * sh * (1 - ta))
        c = c * (1 - ta) + ti * KEYF * 0.95 * ta
    # the box on the sofa seat edge between them; soft contact shadow on the cushion / his trouser, growing as it lands.
    # Sharpness matched to the plate (MTF ~1.2-1.5 px at 720).
    C, A, S = _lap_box(s["lid"], s["box_drop"], s["receipt_in_slot"])
    C = cv2.GaussianBlur(C, (0, 0), 2.8); A = cv2.GaussianBlur(A, (0, 0), 1.8)
    lift = max(0.0, s["box_drop"]) / k["setdown_px"]
    S2 = cv2.GaussianBlur(np.roll(S, int(lift * 30), 0), (0, 0), 3 + 8 * lift)
    soft = cv2.GaussianBlur(np.roll(np.roll(A, 10, 0), -14, 1), (0, 0), 22)        # broad occlusion on the fabric
    c = c * (1 - (0.66 - 0.35 * lift) * S2) * (1 - 0.30 * soft * (1 - A))
    c = c * (1 - A) + (C * (0.80 + 0.25 * KEYF)) * A
    # the FOREGROUND sofa arm stays in front of the box's left foot (and of her lap): re-composite the burned plate there
    c = c * (1 - OCC) + PLATE_BURNED * OCC
    # her right arm: coat sleeve + glove (one real piece from V1), reaching from her coat OVER the end of the sofa arm,
    # fingers curled over the box's left end. In S5 the arm swings (pinned at the elbow inside her coat) to the slit.
    cam = _box_cam(s["box_drop"])
    zr = box.H_ * 0.85
    Lp = np.array(cam.P((0.10, 0.30, zr)))
    breathe = 0.8 * math.sin(2 * math.pi * twos(t) / 3.1)
    hold = Lp + [8, -30 + breathe]
    roll = -30.0
    cv_ = s.get("carry", 0.0)
    if cv_ > 0:
        slot = np.array(box.slot_screen(cam)[0])
        tgt = slot + [-6, -58] + [0, 34 * min(1, max(0, (cv_ - 0.6) / 0.4))]       # over the slit, then down into it
        hold = hold + (tgt - hold) * min(1.0, cv_ / 0.6 if cv_ < 0.6 else 1.0)
        roll = -30.0 + 24.0 * min(1.0, cv_ / 0.6)
    M = _hand_M(hold, 0.34, False, roll)
    hi = cv2.warpAffine(hand, M, (1440, 1080), flags=cv2.INTER_AREA); ha = cv2.warpAffine(arm_a, M, (1440, 1080))
    if s["receipt"] == "in_hand":
        # the folded slip pinched under the glove's fingertips (drawn before the hand so the fingers overlap it)
        tip = M[:, :2] @ np.array([470.0, 700.0]) + M[:, 2]
        ti, ta = slip_layer(tip + [4, 10], -8.0 + 10 * cv_, 1.0)
        c = c * (1 - ta) + ti * KEYF * 0.95 * ta
    sh = np.roll(np.roll(cv2.GaussianBlur(ha, (0, 0), 4), 5, 0), -4, 1)
    c = c * (1 - 0.30 * sh * (1 - ha))
    c = c * (1 - ha) + hi * KEYF * 0.97 * ha
    made = np.maximum(made, ha)
    out = cv2.resize(c, (720, 540), interpolation=cv2.INTER_AREA)
    gm = 1 - cv2.resize(made, (720, 540), interpolation=cv2.INTER_AREA)
    img = tone(out, seed=int(t * FPS), gmask=gm)
    if return_state:
        ys, xs = np.where(cv2.resize(A, (720, 540), interpolation=cv2.INTER_AREA) > 0.5)
        if len(ys): s["box_bbox_pic"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    return (img, s) if return_state else img

_yy2, _xx2 = np.mgrid[0:1080, 0:1440].astype(np.float32)
_XDIV = np.interp(_yy2, [0, 480, 820, 1080], [650, 650, 800, 860])
_WSH = np.clip((_XDIV - _xx2) / 130, 0, 1) * np.clip((_yy2 - 110) / 90, 0, 1)
def _shift_maps(dx):
    return (_xx2 - dx * _WSH).astype(np.float32), _yy2.astype(np.float32)

# ---------------------------------------------------------------- inserts
_lapsrc = m[3244:4444, 3909:5509]                     # skirt/lap fabric in the master, a shallow-focus plane
LAP = cv2.GaussianBlur(cv2.resize(_lapsrc, (760, 570), interpolation=cv2.INTER_AREA), (0, 0), 3.0)
ENV_INS = np.clip(cv2.GaussianBlur(g, (0, 0), 7) * 255, 0, 255).astype(np.uint8)   # the lid mirrors the room out of focus
STATE_LID = dict(closed=0.0, lid33=35.0, lid66=70.0, open=105.0, empty=105.0, receipt=105.0)

def insert_cam(t):
    # slight motion: a slow push-in and a breath of drift (hand-held box, not a held still)
    yaw = -12 + 1.2 * math.sin(2 * math.pi * t / 5.3); pitch = 52 + 0.6 * math.sin(2 * math.pi * t / 4.1 + 1)
    return box.Cam(yaw=yaw, pitch=pitch, dist=2.1 - 0.025 * t, f=740, cx=372 + 3 * math.sin(t * 0.9), cy=318 + 2 * math.sin(t * 1.3))

def render_box_insert(t, state="open"):
    lid = STATE_LID[state]
    cam = insert_cam(t)
    C, A, S = box.render(cam, (720, 540), lid, ENV_INS, ss=3, receipt=1.0 if state == "receipt" else 0.0)
    # editor repair 2: the box shot sharp but not digital: a lens/print softness (~0.9 px) and, below, the print's grain
    C = cv2.GaussianBlur(C, (0, 0), 0.9); A = cv2.GaussianBlur(A, (0, 0), 0.7)
    ox, oy = int(20 + 6 * math.sin(t * 0.7)), int(15 + 4 * math.sin(t * 0.5))
    lap = LAP[oy:oy + 540, ox:ox + 720]
    yy2, xx2 = np.mgrid[0:540, 0:720].astype(np.float32)
    pool = np.exp(-(((xx2 - 420) / 330) ** 2 + ((yy2 - 280) / 260) ** 2))    # flash pool from camera-right
    # editor repair 1: the flash pool lights only the photographed lap plane; the handmade box keeps its own shading
    # (key from camera-right, silver_box.KEY) graded to the plate's black/white points, with no print grain on it
    soft = cv2.GaussianBlur(np.roll(np.roll(A, 18, 0), -22, 1), (0, 0), 30)       # broad soft occlusion on the skirt
    c = lap * (1 - 0.62 * S) * (1 - 0.35 * soft * (1 - A)) * (0.28 + 0.58 * pool)
    made = np.zeros_like(A)
    c = c * (1 - A) + (0.04 + 0.98 * C) * A
    # her right glove grips the box's right end (fingers over the front edge)
    zr = box.H_ * 0.88
    R = np.array(cam.P((box.W_ * 0.985, 0.16, zr)))
    # editor repair 1: glove joined to its coat sleeve (mirrored card: the forearm leaves frame-right, toward her body)
    M = _hand_M(R + [-10, -64 + 1.2 * math.sin(t * 2.0)], 0.62, True, 14)
    hi = cv2.warpAffine(hand, M, (720, 540), flags=cv2.INTER_AREA); ha = cv2.warpAffine(arm_a, M, (720, 540))
    c = c * (1 - 0.35 * np.roll(np.roll(cv2.GaussianBlur(ha, (0, 0), 5), 6, 0), -5, 1) * (1 - ha))
    c = c * (1 - ha) + hi * 0.98 * ha          # her glove is a real photograph: its own grain, the key of its own print
    made = np.maximum(made, ha)
    return tone(c, seed=int(t * FPS) + 3, gmask=1 - made)

def render_receipt_insert(t):
    """her hands unfold the slip on her lap (3 drawings, on twos), then a slow push onto the date line"""
    td = twos(t)
    ang = 180 if td < 0.4 else 120 if td < 0.8 else 55 if td < 1.2 else 0
    push = 1.0 + 0.10 * ease((t - 1.6) / 2.9)
    cx, cy = 360 + 40 * ease((t - 1.6) / 2.9), 270 - 25 * ease((t - 1.6) / 2.9)
    lap = LAP[10:550, 20:740].copy()
    yy2, xx2 = np.mgrid[0:540, 0:720].astype(np.float32)
    pool = np.exp(-(((xx2 - 430) / 330) ** 2 + ((yy2 - 260) / 280) ** 2))
    c = lap * (0.34 + 0.60 * pool)
    sw, shh = 560, 360
    sg, sa = _folded_slip(sw, shh, ang)
    # lay on the lap with a little perspective (paper lies on a slanted skirt) and a slight tilt
    src = np.float32([[0, 0], [sw, 0], [sw, shh], [0, shh]])
    x0, y0 = 360 - sw / 2, 280 - shh / 2
    dst = np.float32([[x0 + 18, y0 + 6], [x0 + sw - 10, y0 - 4], [x0 + sw + 14, y0 + shh + 8], [x0 - 12, y0 + shh + 2]])
    Mp = cv2.getPerspectiveTransform(src, dst)
    ti = cv2.warpPerspective(sg, Mp, (720, 540), flags=cv2.INTER_AREA); ta = cv2.warpPerspective(sa, Mp, (720, 540))
    c = c * (1 - 0.45 * np.roll(np.roll(cv2.GaussianBlur(ta, (0, 0), 6), 7, 0), -6, 1) * (1 - ta))
    keyx = 0.86 + 0.14 * np.clip(xx2 / 720, 0, 1)             # the room's key, from camera-right (no radial vignette)
    c = c * (1 - ta) + ti * 0.80 * keyx * ta
    made = ta.copy()
    # her gloved hands hold the lower corners; the right one lifts the top half as it opens
    for anchor, mir, roll in (((x0 + sw - 10, y0 + shh - 36), True, 40), ((x0 + 20, y0 + shh - 20), False, -40)):
        M = _hand_M(anchor, 0.42, mir, roll)
        hi = cv2.warpAffine(hand, M, (720, 540), flags=cv2.INTER_AREA); ha = cv2.warpAffine(arm_a, M, (720, 540))
        c = c * (1 - 0.3 * np.roll(np.roll(cv2.GaussianBlur(ha, (0, 0), 5), 6, 0), -5, 1) * (1 - ha))
        c = c * (1 - ha) + hi * 0.95 * ha
        made = np.maximum(made, ha)
    # push-in (camera, not a zoom filter: resample the composed card)
    M = cv2.getRotationMatrix2D((cx, cy), 0, push); M[:, 2] += [360 - cx, 270 - cy]
    c = cv2.warpAffine(c, M, (720, 540), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    made = cv2.warpAffine(made, M, (720, 540), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return tone(c, seed=int(t * FPS) + 5, gmask=1 - made)

def slot_screen_insert(t=0.0):
    cam = insert_cam(t); zv = box.H_ * 0.82; sy = box.WALL + box.SLOT["cy"] * (box.D_ - 2 * box.WALL)
    c = cam.P((box.SLOT["cx"] * box.W_, sy, zv)); l = cam.P((0, sy, zv)); r = cam.P((box.W_, sy, zv))
    return dict(slot=c, left=l, right=r, norm_x=(c[0] - l[0]) / (r[0] - l[0]))
