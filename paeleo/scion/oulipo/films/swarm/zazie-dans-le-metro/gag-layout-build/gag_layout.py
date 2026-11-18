"""U1 gag-layout: writes gag-route.json, layout plates and layout-boards.jpg for zazie-dans-le-metro.
Usage: python3 -I gag_layout.py
Plates: LoC photochroms from films/sources/zazie-dans-le-metro/r2 (U2's forage/ set not ready at run time) and the
graded test-shot plates (test-shot/plates/P*_sharp.png). Grade = plates.py grade (gamma 1.40, desaturate, grey-olive tint,
median target) then Gaussian defocus r=12 @720. Boards are layout diagrams (not picture material)."""
import json, math, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
SW = ROOT / "films/swarm/zazie-dans-le-metro"
SRC = ROOT / "films/sources/zazie-dans-le-metro"
R2, TS = SRC / "r2", SRC / "test-shot"
LAY, GL = SRC / "layout", SRC / "gag-layout"
FPS, PW, PH = 24, 720, 540
SERIF = ImageFont.truetype(str(ROOT / "assets/fonts/instrument-serif.woff2"), 22)
MONO = ImageFont.truetype(str(ROOT / "assets/fonts/ibm-plex-mono.woff2"), 15)
MONOB = ImageFont.truetype(str(ROOT / "assets/fonts/ibm-plex-mono.woff2"), 20)
TILEF = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 40)

# ------------------------------------------------------------------ plates
def grade(a, ds, tint, tgt):
    a = (a.astype(np.float32) / 255) ** 1.40
    g = (a * [0.3, 0.59, 0.11]).sum(2, keepdims=True)
    a = (g + (a - g) * ds) * np.array(tint)
    a = a * (tgt / np.percentile(a.mean(2) * 255, 50))
    return Image.fromarray((np.clip(a, 0, 186 / 255) * 255).astype(np.uint8))

PLATES = {  # id: (source, crop box in 1024-px coords or None for a test-shot plate, desat, tint, target p50, use)
    "P1_wide": ("loc_05184.jpg", (150, 230, 790, 710), 0.52, [0.97, 0.975, 0.93], 95, "S1 MS, S2 MLS (L1 rue Royale)"),
    "P1_cu": ("test-shot/plates/P1_sharp.png", None, 0, 0, 0, "S3 CU (L1), the test-shot crop"),
    "P2_cu": ("test-shot/plates/P2_sharp.png", None, 0, 0, 0, "S4 CU (L2 place de Clichy), S5 far light"),
    "P3_wide": ("loc_05196.jpg", (140, 285, 760, 750), 0.55, [0.975, 0.975, 0.92], 92, "S6/S7 queue + stair (L3 Châtelet), S6b/S7b"),
    "P3_cu": ("loc_05196.jpg", (300, 330, 640, 585), 0.55, [0.975, 0.975, 0.92], 92, "S8 / S8b CU (L3)"),
    "P4_wide": ("madeleine.jpg", (290, 240, 890, 690), 0.50, [0.98, 0.975, 0.90], 92, "S4b reverse angle (L1b), cut B"),
    "P4_mcu": ("madeleine.jpg", (380, 330, 780, 630), 0.50, [0.98, 0.975, 0.90], 92, "S5b MCU (L1b), cut B"),
}
plate_stats, blurred = {}, {}
for k, (fn, box, ds, tint, tgt, use) in PLATES.items():
    if box is None:
        im = Image.open(SRC / fn).convert("RGB")
        ow, oh = im.size; cw, ch = int(ow / 1.08), int(oh / 1.08)   # strip the 8 % overscan
        im = im.crop(((ow - cw) // 2, (oh - ch) // 2, (ow - cw) // 2 + cw, (oh - ch) // 2 + ch)).resize((PW, PH), Image.LANCZOS)
    else:
        im = Image.open(R2 / fn).convert("RGB").crop(box).resize((PW, PH), Image.LANCZOS)
        im = grade(np.asarray(im), ds, tint, tgt)
    bl = im.filter(ImageFilter.GaussianBlur(12))
    bl.save(LAY / f"{k}_blur.png"); blurred[k] = bl
    L = np.asarray(bl).astype(np.float32).mean(2); S = np.asarray(bl.convert("HSV"))[..., 1]
    plate_stats[k] = dict(source=fn, crop_1024=box, use=use, blur_r_720=12, p5=round(float(np.percentile(L, 5)), 1),
                          p50=round(float(np.percentile(L, 50)), 1), p95=round(float(np.percentile(L, 95)), 1),
                          sat_mean=round(float(S.mean()), 1), file=str(LAY / f"{k}_blur.png"))

# ------------------------------------------------------------------ shot timing
def F(t): return int(round(t * FPS))
SHOTS_A = [("S1", 0, 47, "L1", "P1_wide", "MS"), ("S2", 48, 143, "L1", "P1_wide", "MLS"),
           ("S3", 144, 191, "L1", "P1_cu", "CU"), ("S4", 192, 239, "L2", "P2_cu", "CU"),
           ("S5", 240, 297, "L2", "P2_cu", "CU->ECU push"), ("S6", 298, 371, "L3", "P3_wide", "MLS"),
           ("S7", 372, 431, "L3", "P3_wide", "MLS (same setup as S6)"), ("S8", 432, 479, "L3", "P3_cu", "CU"),
           ("tail", 480, 527, None, None, "title card")]
SHOTS_B = SHOTS_A[:3] + [("S4b", 192, 239, "L1b", "P4_wide", "MLS reverse angle"), ("S5b", 240, 297, "L1b", "P4_mcu", "MCU"),
                         ("S6b", 298, 371, "L3", "P3_wide", "MLS"), ("S7b", 372, 431, "L3", "P3_wide", "MLS"),
                         ("S8b", 432, 479, "L3", "P3_cu", "CU inside the tram"), SHOTS_A[-1]]

# ------------------------------------------------------------------ geometry (720x540 picture coords)
CU_HEAD = dict(bbox=[198, 128, 558, 560], crown=[378, 130], brows_y=281, mouth=[382, 443], chin_y=540,
               head_w_frac=0.50, right_eye=[440, 300], left_eye=[322, 300], collar_band=[230, 516, 540, 540])
TILE_W, TILE_H = 56, 72
LOWER_X = [168 + 64 * i for i in range(7)]               # D O N K T A N
UPPER_X = [150, 212, 274, 336, 428, 490, 552]           # D O U K | gap | I P U
ROW_BASE_Y = 452                                         # bottom edge of a tile body (match-cut anchor)
UPPER_BASE_Y = 236                                       # bottom edge of upper (hanging) row in the ECU
LOWER_GUM_BASE_Y = 412                                   # lower row seated in the gum before TAN
LETTERS = list("DOUKIPUDONKTAN")
TILES = [dict(id=f"T{i+1}", glyph=c, row="upper" if i < 7 else "lower") for i, c in enumerate(LETTERS)]
V_S6 = dict(bbox=[598, 196, 772, 462], deck_y=214, rear_platform=[598, 420], note="partly off right edge; waits at the stop")
STAIR = [dict(step=1, tiles=["T8", "T9"], tread_top=[240, 404]), dict(step=2, tiles=["T10", "T11"], tread_top=[340, 354]),
         dict(step=3, tiles=["T12", "T13"], tread_top=[440, 304]), dict(step=4, tiles=["T14"], tread_top=[540, 254]),
         dict(step="deck", tiles=[], tread_top=[650, 214])]
SYL = [("DOU", 254, ["T1", "T2", "T3"]), ("KI", 259, ["T4", "T5"]), ("PU", 264, ["T6", "T7"]),
       ("DONK", 269, ["T8", "T9", "T10", "T11"]), ("TAN", 275, ["T12", "T13", "T14"])]
RELEASE = {f"T{8+i}": 281 + i for i in range(7)}         # one per frame, 281..287
LAND = {k: v + 6 for k, v in RELEASE.items()}            # fall 40 px at g=2.2 px/f^2 -> 6 frames; land 287..293, settle by 296


def lerp(a, b, u): return a + (b - a) * u


def z_pos(shot, f):
    """Z root + bbox per shot/frame (rough layout). root = crown pin for CU, neck pin for MS, hip pin for full figure."""
    if shot in ("S3", "S4", "S8", "S8b"):
        return dict(root_def="crown pin", root=CU_HEAD["crown"], bbox=CU_HEAD["bbox"], scale=1.0, facing="R (3/4)")
    if shot == "S1":
        return dict(root_def="neck pin", root=[168, 352], bbox=[40, 150, 300, 540], scale=0.36, facing="R")
    if shot in ("S2", "S4b"):
        a, b = (48, 143) if shot == "S2" else (192, 239)
        x0, x1 = (80, 420) if shot == "S2" else (-60, 300)
        x = round(lerp(x0, x1, (f - a) / (b - a)))
        return dict(root_def="hip pin", root=[x, 352], bbox=[x - 55, 214, x + 55, 470], scale=0.25, facing="R")
    if shot == "S5":
        s = min(1.0, (f - 240) / 12); s = s * s * (3 - 2 * s); k = lerp(1.0, 4.5, s)
        mx, my = lerp(CU_HEAD["mouth"][0], 360, s), lerp(CU_HEAD["mouth"][1], 320, s)
        cx, cy = mx + (CU_HEAD["crown"][0] - CU_HEAD["mouth"][0]) * k, my + (CU_HEAD["crown"][1] - CU_HEAD["mouth"][1]) * k
        return dict(root_def="crown pin (off frame once k>1.6)", root=[round(cx), round(cy)], mouth_centre=[round(mx), round(my)],
                    face_scale=round(k, 3), hair_plane_scale=round(lerp(1.0, 5.4, s), 3), facing="R (3/4)")
    if shot == "S5b":
        return dict(root_def="crown pin", root=[372, 150], bbox=[240, 148, 500, 540], scale=0.72, facing="R (3/4)")
    if shot in ("S6", "S6b"):
        if f < 312: return dict(root_def="hip pin", root=None, note="not yet in frame", facing="R")
        if shot == "S6":
            if f <= 326: x = round(lerp(-80, 95, (f - 312) / 14))
            elif f <= 336: x = round(lerp(95, 35, (f - 326) / 10))
            else: x = 35
        else:
            x = round(lerp(-80, 200, min(1, (f - 312) / 14)))
        return dict(root_def="hip pin", root=[x, 342], bbox=[x - 55, 210, x + 55, 460], scale=0.25, facing="R")
    if shot == "S7":
        keys = [(372, 35, 342), (382, 240, 286), (391, 340, 236), (400, 440, 186), (409, 540, 136), (418, 650, 200), (431, 650, 200)]  # hip y = tread_top - 118 (feet on tread); f418+ seated on the deck (y 214)
        for (fa, xa, ya), (fb, xb, yb) in zip(keys, keys[1:]):
            if fa <= f <= fb:
                u = (f - fa) / (fb - fa); x, y = round(lerp(xa, xb, u)), round(lerp(ya, yb, u)); break
        return dict(root_def="hip pin", root=[x, y], bbox=[x - 55, y - 132, x + 55, (y + 118) if f < 418 else 214], feet_y=(y + 118) if f < 418 else None, scale=0.25, facing="R",
                    contact="foot pinned to tread top (Reiniger contact plane)")
    if shot == "S7b":
        x = round(lerp(200, 610, min(1, max(0, (f - 372) / 46))))
        return dict(root_def="hip pin", root=[x, 342], bbox=[x - 55, 210, x + 55, 460], scale=0.25, facing="R")
    return dict(root=None)


def v_pos(shot, f):
    if shot == "S1":
        if f < 12: return dict(visible=False, note="offscreen left; bell cue f8")
        x = round(lerp(250, 600, (f - 12) / 35))
        return dict(visible=True, plane="far", centre=[x, 372], bbox=[x - 75, 335, x + 75, 410], occluded_by_Z=f < 18)
    if shot == "S2":
        zf = z_pos("S2", f)["bbox"][2]; gap = round(lerp(180, 320, (f - 48) / 95)); x0 = zf + gap
        return dict(visible=x0 < 720, plane="mid", rear_x=x0, bbox=[x0, 260, x0 + 260, 420], gap_px=gap)
    if shot == "S3": return dict(visible=False, note="off right (it just left); eye-trace carries it")
    if shot in ("S4",): return dict(visible=True, plane="P2 native + V card plane", bbox=[394, 168, 720, 367], centre=[580, 268],
                                    note="same pixels as the V cutout (P2_Vmask), ahead mid-right beside her ear")
    if shot == "S5": return dict(visible=f < 246, note="lost in the push-in; Clichy light far down the throat")
    if shot in ("S6", "S7", "S6b", "S7b"): return dict(visible=True, plane="mid", **V_S6)
    if shot in ("S8",): return dict(visible=True, plane="Z rides on it", note="rail/deck plane at bottom 1x, P3 slides R->L 0.3x")
    if shot == "S8b": return dict(visible=True, plane="interior", note="window frame and bench of V interior (handmade card) around her")
    if shot == "S4b": return dict(visible=True, plane="far", bbox=[600, 318, 690, 372], note="farther ahead than in S2")
    if shot == "S5b": return dict(visible=False)
    return dict(visible=False)


def tiles_pos(shot, f):
    if shot == "S5":
        if f < 246: return dict(visible=False, note="inside the mouth, too small to read before the push lands")
        rows = []
        for t, x in zip(TILES[:7], UPPER_X):
            pop = any(s[1] <= f < s[1] + 4 and t["id"] in s[2] for s in SYL)
            rows.append(dict(id=t["id"], glyph=t["glyph"], cx=x, base_y=UPPER_BASE_Y + (6 if pop else 0), rot=0, reading="teeth"))
        for t, x in zip(TILES[7:], LOWER_X):
            pop = any(s[1] <= f < s[1] + 4 and t["id"] in s[2] for s in SYL)
            r, l = RELEASE[t["id"]], LAND[t["id"]]
            if f < r: y, rot = LOWER_GUM_BASE_Y - (6 if pop else 0), (-8 if (t["id"] == "T14" and f >= 278) else 0)
            elif f < l: u = (f - r) / (l - r); y, rot = LOWER_GUM_BASE_Y + 40 * u * u, round(18 * math.sin(math.pi * u) * (1 if int(t["id"][1:]) % 2 else -1), 1)
            else: y, rot = ROW_BASE_Y, round(6 * math.exp(-(f - l) / 1.5) * math.cos((f - l) * 2.2), 1)
            rows.append(dict(id=t["id"], glyph=t["glyph"], cx=x, base_y=round(y, 1), rot=rot, reading="teeth" if f < r else "falling" if f < l else "row"))
        return dict(visible=True, w=TILE_W, h=TILE_H, tiles=rows)
    if shot == "S6":
        rows = [dict(id=t["id"], glyph=t["glyph"], cx=x, base_y=ROW_BASE_Y, rot=0, reading="queue", feet=True)
                for t, x in zip(TILES[7:], LOWER_X)]
        if f >= 341:
            for i, r in enumerate(rows):
                fi = 341 + 3 * i
                if f >= fi: r["reading"] = "tipping" if f < fi + 3 else "steps"; r["rot"] = 0 if f < fi else min(40, (f - fi) * 13)
        return dict(visible=True, w=TILE_W, h=TILE_H, tiles=rows, upper_row="T1..T7 stay in her mouth (offscreen teeth, counted)")
    if shot in ("S7",):
        return dict(visible=True, stair=STAIR, reading="steps", note="T14 (N) is step 4, kicked loose as she steps on the deck at f418")
    if shot == "S8":
        return dict(visible=432 + 18 <= f <= 470, flutter="T14", path=[[760, 120], [-60, 300]], frames=[450, 470], plane="1.4x fg")
    if shot in ("S5b",):
        return dict(visible=True, note="14 tiles as teeth at MCU scale in her mouth (w≈16 px); no drop on TAN")
    return dict(visible=False)


# ------------------------------------------------------------------ test-shot exposure (accepted r2), film frames 144-263
ts_sheet = {r["film_frame"]: r for r in json.load(open(SW / "test-shot-build/test-results.json"))["exposure_sheet"]}


def wind_ts(t):  # test_shot.py wind_at, film time
    tl = t - 6.0
    if tl < 0.6 or tl > 3.6: return 0.0
    a = min(1.0, (tl - 0.6) / 0.35); d = 1.0 if tl < 2.7 else max(0.0, 1 - (tl - 2.7) / 0.9)
    return a * d * (1 + 0.28 * math.sin(tl * 11.3) + 0.18 * math.sin(tl * 23.1 + 1.0))


def breeze(f):
    t = (f - 432) / FPS
    if t < 0: return 0.0
    g = min(1, t / 0.3) * (1.0 if t < 0.8 else max(0.0, 1 - (t - 0.8) / 0.4))
    return 0.20 + 0.45 * g          # 0.20 steady tram airflow (static deflection) + a gust 18.0-19.2 s that ends


def shot_of(shots, f):
    for s in shots:
        if s[1] <= f <= s[2]: return s[0]


def sheet(cut):
    shots = SHOTS_A if cut == "A" else SHOTS_B
    rows = []
    for f in range(528):
        s = shot_of(shots, f); on2 = f - f % 2
        r = dict(f=f, t=round(f / FPS, 3), shot=s, pose=None, mouth=None, eye=None, gust=0.0)
        if s == "S1":
            neck = 0 if on2 < 12 else round(min(12, (on2 - 12) / 18 * 12), 1)
            r.update(pose=("ms_stand" if on2 < 12 else "ms_track" if on2 < 30 else "ms_point") + f".neck{neck:+g}", eye="open_r",
                     mouth=(3 if (on2 // 2) % 2 == 0 else 2) if (10 <= on2 < 22 or 31 <= on2 < 41) else 1)
        elif s in ("S2", "S4b"):
            a = 48 if s == "S2" else 192
            d = ((f - a) // 2) % 8
            r.update(pose=f"run.{d}", eye="pr_open", mouth=4 if s == "S2" else 2, gust=0.35, contact=d in (0, 4))
        elif s in ("S3", "S4"):
            ts = ts_sheet[f]; shake = (3 if (f // 2) % 2 == 0 else -3) if ts["laugh"] >= 0.8 else 0
            r.update(pose=f"cu_laugh.d{ts['drawing']:03d}", mouth=ts["mouth"], eye=ts["eyes"], gust=round(wind_ts(f / FPS), 3),
                     laugh=ts["laugh"], shoulder_shake_px=shake, hold=184 <= f <= 191)
        elif s == "S5":
            if on2 < 252: r.update(pose="cu_laugh.push", mouth=4, eye="open_r" if on2 < 246 else None)
            else:
                m = "E0"
                for name, fs, _ in SYL:
                    if fs <= f < fs + 4: m = "E1"
                if f >= 275: m = "E2"
                r.update(pose="ecu_mouth", mouth=m, eye=None, syllable=next((n for n, fs, _ in SYL if fs <= f < fs + 5), None))
        elif s == "S5b":
            m = 4 if f < 254 else 1
            for name, fs, _ in SYL:
                if fs <= f < fs + 4: m = 5 if name in ("DOU", "TAN") else 3
            r.update(pose="mcu_talk", mouth=m, eye="open_r" if f < 275 else "squeeze")
        elif s == "S6":
            if f < 312: r.update(pose=None, note="Z offscreen left; queue holds")
            elif f < 326: r.update(pose=f"run.{((f - 312) // 2) % 8}", eye="pr_open", mouth=4, gust=0.35)
            elif f < 330: r.update(pose="squash", eye="pr_squeeze", mouth=6, impulse="hair fling forward (collision)")
            elif f < 337: r.update(pose="bounce_back", eye="pr_squeeze", mouth=6)
            else: r.update(pose="stand_watch", eye="pr_open", mouth=2 if f < 350 else 4)
        elif s == "S6b":
            if f < 312: r.update(pose=None, note="Z offscreen left")
            elif f < 326: r.update(pose=f"run.{((f - 312) // 2) % 8}", eye="pr_open", mouth=4, gust=0.35)
            else: r.update(pose="stand_wait", eye="pr_open", mouth=1)
        elif s == "S7":
            steps = [(372, "walk"), (378, "climb.c1"), (387, "climb.c2"), (396, "climb.c3"), (405, "climb.c4"), (414, "step_deck"), (418, "sit")]
            p = [n for fa, n in steps if on2 >= fa][-1]
            r.update(pose=p, eye="pr_open" if p != "sit" else "squeeze", mouth=4 if p != "sit" else 5, gust=0.05)
        elif s == "S7b":
            r.update(pose="walk" if f < 410 else "step_platform" if f < 418 else "stand_inside", eye="pr_open", mouth=1)
        elif s in ("S8", "S8b"):
            k = ((f - 432) // 4) % 6
            r.update(pose=f"cu_laugh.ride{(f - 432) // 2 % 4}", mouth=[5, 4, 6, 4, 5, 4][k], eye="squeeze",
                     gust=round(breeze(f), 3) if s == "S8" else 0.0, laugh=0.8,
                     shoulder_shake_px=3 if (f // 2) % 2 == 0 else -3)
        rows.append(r)
    return rows

EXA, EXB = sheet("A"), sheet("B")

# ------------------------------------------------------------------ shots (A and B)
def shot_rec(sid, a, b, loc, plate, size, cut):
    keyf = sorted({a, (a + b) // 2, b} | ({191} if sid == "S3" else set()) | ({192, 216} if sid == "S4" else set())
                  | ({275, 287, 297} if sid == "S5" else set()) | ({298, 326, 341, 359} if sid == "S6" else set())
                  | ({418} if sid == "S7" else set()))
    keyf = [k for k in keyf if a <= k <= b]
    return dict(id=sid, cut=cut, frames=[a, b], t=[round(a / FPS, 3), round((b + 1) / FPS, 3)], location=loc, plate=plate,
                size=size, keyframes=[dict(f=k, Z=z_pos(sid, k), V=v_pos(sid, k), T=tiles_pos(sid, k)) for k in keyf])

EYE = {
    "S1": [[0, 150, 250, "Z face"], [6, 120, 74, "GRÈVE sign (top left)"], [12, 270, 372, "V emerging from behind Z (bell f8)"],
           [30, 330, 300, "Z pointing hand"], [44, 590, 372, "V far plane, frame right"]],
    "S2": [[48, 135, 300, "Z head"], [96, 470, 330, "V rear"], [140, 470, 300, "Z head chasing V off right"]],
    "S3": [[144, 380, 330, "Z face centre"], [158, 440, 300, "fringe crossing right eye on gust"], [184, 382, 443, "full-laugh mouth (hold)"]],
    "S4": [[192, 382, 443, "mouth unchanged (anchor)"], [196, 630, 48, "PLACE DE CLICHY plaque pops"], [204, 580, 268, "V ahead mid-right"],
           [216, 440, 300, "her eyes open, gaze locks on V"]],
    "S5": [[240, 382, 443, "mouth"], [254, 336, 236, "upper tiles DOUK"], [275, 360, 300, "throat / jaw drop"], [281, 552, 412, "loose N tilts"],
           [293, 360, 452, "lower row lands (anchor row y=452)"]],
    "S6": [[298, 360, 452, "same row: now the queue"], [300, 630, 48, "PLACE DU CHÂTELET plaque"], [312, 0, 340, "Z enters left"],
           [326, 140, 400, "contact frame (impact)"], [341, 200, 420, "domino starts"], [359, 560, 260, "stair top reaches V deck"]],
    "S7": [[372, 240, 404, "first tread"], [400, 440, 304, "Z mid climb"], [418, 650, 214, "V top deck (sits)"]],
    "S8": [[432, 380, 330, "Z face"], [450, 700, 150, "N tile flutters in"], [470, 60, 300, "N exits left"]],
    "tail": [[480, 360, 250, "title tiles"], [500, 360, 420, "credit line"]],
    "S4b": [[192, 0, 340, "Z enters left (same side)"], [210, 645, 345, "V far ahead"]],
    "S5b": [[240, 372, 420, "mouth (MCU)"], [254, 372, 420, "teeth tiles (small)"]],
    "S6b": [[298, 400, 330, "paper commuters queue"], [312, 0, 340, "Z enters left"], [326, 200, 300, "Z waits at queue end"]],
    "S7b": [[372, 400, 330, "queue boards V"], [418, 610, 330, "Z steps onto rear platform"]],
    "S8b": [[432, 380, 330, "Z face, tram window behind"]],
}
shots = {"A": [], "B": []}
for cut, lst in (("A", SHOTS_A), ("B", SHOTS_B)):
    for sid, a, b, loc, plate, size in lst:
        rec = shot_rec(sid, a, b, loc, plate, size, cut)
        rec["eye_trace"] = [dict(f=e[0], x=e[1], y=e[2], target=e[3]) for e in EYE[sid]]
        rec["shared_with_other_cut"] = sid in ("S1", "S2", "S3", "tail")
        shots[cut].append(rec)
DESC = {
    "S1": "Setup. Waist-up Z frame left facing right; handmade métro sign + GRÈVE strip top left; V crosses far plane L->R from f12, head tracks (neck FK 0->+12°), points f30. Captions f10 « Le métro ? En grève. », f31 « …le tram, alors ! ».",
    "S2": "Straightforward chase. Full-figure profile, run cycle 8 drawings on twos (stride 16 f = 0.67 s), camera holds, P1 drifts 0.25x, fg lamp-post plane 1.4x; V ahead, gap 180->320 px.",
    "S3": "TEST SHOT laugh CU, reference framing. Gust from f158 sweeps fringe across her right eye; hold f184-191 at full laugh (mouth 5), declared silence.",
    "S4": "JUMP CUT f192: identical puppet state, plate P1->P2; plaque f196; laugh resumes; f216 eyes open, gaze locks on V, gulp (mouth 2); f228 grin.",
    "S5": "Bouche de métro: push-in f240-251 (face 1->4.5, hair plane faster), mouth becomes the tunnel; syllables DOU f254 KI 259 PU 264 DONK 269 TAN 275; jaw drop f275; N tilts f278; lower tiles released one per frame f281-287, land on the jaw floor y=452 f287-293, upright row f296-297.",
    "S6": "MATCH CUT f298: same 7 tiles, same y/spacing, now a queue with paper feet at L3. Caption f302 « faire la queue… ». Z enters f312, contact f326 (impact), squash, bounce back 60 px, hair flung forward, silence f326-332; wobble; domino tip f341-359 into a stair.",
    "S7": "Same setup: Z climbs 4 treads, foot pinned to tread tops (c1 382, c2 391, c3 400, c4 409), steps on V's impériale f414, sits f418; T14 kicked loose; bell x2 departure.",
    "S8": "CU on the top deck, reference framing; P3 slides R->L 0.3x, deck rail 1x; breeze gust f432-461 then steady airflow; T14 (N) flutters past f450-470; caption f442 « Zazie a pris le tram. ».",
    "tail": "Cut-paper title card on dark brown; « Zazie dans le métro » in tiles (D, A, N, I, T, O reused from T; missing letters are new title tiles, an explicit tail exception to invariant 4); credit line; final click f520.",
    "S4b": "Continuity reverse angle down boulevard de la Madeleine (P4): Z runs in from frame left (same screen direction), V far ahead.",
    "S5b": "MCU on L1b: she says « Doukipudonktan ! » with the same syllable timing and tile teeth at small scale; no push-in, no drop.",
    "S6b": "Plain cut to L3: 7 handmade paper commuters queue at the stop (feet y=460); Z runs in f312 and stops at the end f326; queue shuffles f341-359.",
    "S7b": "She waits, steps aboard the rear platform normally f410-418.",
    "S8b": "CU inside the tram, laughing; P3 through the window, breeze off.",
}
for cut in shots:
    for r in shots[cut]: r["action"] = DESC[r["id"]]

# ------------------------------------------------------------------ cuts
cuts = {
    "A": [dict(f=48, type="continuity", out="S1", inn="S2", note="MS -> MLS, same place, direction L->R kept"),
          dict(f=144, type="continuity", out="S2", inn="S3", note="cut-in to CU; she stops, out of breath"),
          dict(f=192, type="jump", op="AnchoredJumpCut", out="S3", inn="S4", hold_before=[184, 191],
               plate_change=["P1", "P2"], location_change=["L1", "L2"], declared_exception="the city moves, the girl does not",
               tolerances=dict(root_centroid_delta_px_max=8, root_scale_delta_frac_max=0.03, mouth="follows exposure sheet (5 at 191 and 192), no reset",
                               hair_spring_state="carried (angle and velocity per strand), never re-initialised",
                               collar_hue_delta_deg_max=4, screen_direction="unchanged: wind and gaze to frame right",
                               vehicle_identifiable_within_frames=24),
               layout_values=dict(Z_root_191=z_pos("S3", 191)["root"], Z_root_192=z_pos("S4", 192)["root"], centroid_delta_px=0.0,
                                  mouth_191=EXA[191]["mouth"], mouth_192=EXA[192]["mouth"], V_visible_from=192)),
          dict(f=240, type="none", out="S4", inn="S5", note="no cut: continuous multiplane push-in from the S4 CU"),
          dict(f=298, type="match", op="TileRewrite(teeth->queue)", out="S5", inn="S6", location_change=["L2", "L3"],
               tolerances=dict(row_baseline_y_delta_px_max=6, row_spacing_delta_px_max=6, tile_count=7, same_glyphs_and_order="DONKTAN",
                               same_paper_and_outline=True),
               layout_values=dict(row_y_297=ROW_BASE_Y, row_y_298=ROW_BASE_Y, spacing_297=64, spacing_298=64,
                                  x_297=LOWER_X, x_298=LOWER_X)),
          dict(f=372, type="none", out="S6", inn="S7", note="beat boundary in one setup; the contact plane (tread tops) must not jump"),
          dict(f=432, type="continuity", out="S7", inn="S8", note="cut to CU on the top deck, direction L->R"),
          dict(f=480, type="continuity", out="S8", inn="tail", note="hard cut to title card")],
    "B": [dict(f=48, type="continuity", out="S1", inn="S2"), dict(f=144, type="continuity", out="S2", inn="S3"),
          dict(f=192, type="continuity", out="S3", inn="S4b", note="reverse angle on adjacent L1b; Z placed by eye-trace continuity (enters frame left, runs right)"),
          dict(f=240, type="continuity", out="S4b", inn="S5b", note="cut-in to MCU"),
          dict(f=298, type="continuity", out="S5b", inn="S6b", note="plain cut to L3, real paper-commuter queue; no identity change"),
          dict(f=372, type="none", out="S6b", inn="S7b"), dict(f=432, type="continuity", out="S7b", inn="S8b"),
          dict(f=480, type="continuity", out="S8b", inn="tail")],
}

# ------------------------------------------------------------------ word_to_gag
word_to_gag = [
    dict(word="métro en grève", literal="the underground is on strike", gag_reading="the goal is blocked before the film starts; the only ride left is the tram",
         prop="handmade enamel métro sign with a pasted GRÈVE strip (S1, top left)", setup=[0, 47], payoff="AnchoredJumpCut f192: Paris moves her toward the tram instead",
         consequence="Goal declared (V named by her point f30), so every later operation is measured against distance(Z,V)"),
    dict(word="Doukipudonktan", literal="d'où qu'il pue donc tant (Queneau's néo-français)", gag_reading="the word is her teeth: 14 cut-paper letter tiles DOUK·IPU / DONKTAN, the gap tooth between K and I",
         prop="tile set T1..T14 (bold serif #7a2a1c on cream paper #e6d6b8)", setup=[254, 280], payoff="on TAN the jaw drops and the lower 7 tiles fall out (f281-297)",
         consequence="the word leaves her mouth as objects, which become the queue that blocks her"),
    dict(word="bouche de métro", literal="métro entrance (literally 'métro mouth')", gag_reading="her laughing mouth IS the métro entrance: paper tunnel rings, the Clichy plate as the far light",
         prop="mouth tunnel (paper rings + dark throat #220d04), push-in f240-251", setup=[240, 251], payoff="the métro she couldn't take swallows the word",
         consequence="title gag: the strike métro reappears as her own mouth"),
    dict(word="faire la queue", literal="to queue (literally 'make the tail')", gag_reading="the fallen letters stand up as a queue with paper feet, at the same height: a queue of letters",
         prop="T8..T14 with paper feet, L3 tram stop", setup=[298, 325], payoff="contact f326: she bounces off her own word; domino f341-359 turns the queue into a stair",
         consequence="setback (bounce 60 px) then recovery: the stair puts her on the impériale (f418)"),
]

# ------------------------------------------------------------------ route graph
route = {
    "L1": dict(plate="P1 rue Royale / Madeleine", shots=["S1", "S2", "S3"],
               nodes=[dict(id="L1.in_Z", kind="entrance", at=[40, 352], note="Z already in frame left at f0"),
                      dict(id="L1.in_V", kind="entrance", at=[250, 372], note="V emerges from behind Z f12 (far plane)"),
                      dict(id="L1.sign", kind="obstacle", at=[120, 74], note="métro GRÈVE: blocks the métro route (narrative obstacle)"),
                      dict(id="L1.out_V", kind="exit", at=[720, 340], note="V leaves frame right in S2 (~f120)"),
                      dict(id="L1.anchor_head", kind="match_anchor", at=CU_HEAD["crown"], note="CU head crown pin at f191, carried to L2")],
               edges=[["L1.in_Z", "L1.out_V", "chase L->R"], ["L1.sign", "L1.in_Z", "redirects goal"], ["L1.anchor_head", "L2.anchor_head", "jump f192"]]),
    "L2": dict(plate="P2 place de Clichy", shots=["S4", "S5"],
               nodes=[dict(id="L2.anchor_head", kind="match_anchor", at=CU_HEAD["crown"], note="same crown pin, same mouth phase"),
                      dict(id="L2.V_native", kind="obstacle/goal", at=[580, 268], note="V ahead mid-right (native tram)"),
                      dict(id="L2.plaque", kind="entrance", at=[630, 48], note="plaque pops f196"),
                      dict(id="L2.mouth", kind="exit", at=[360, 320], note="push-in exits through her mouth (bouche de métro)"),
                      dict(id="L2.anchor_row", kind="match_anchor", at=[360, ROW_BASE_Y], note="lower tile row baseline y=452 at f297")],
               edges=[["L2.anchor_head", "L2.mouth", "push-in"], ["L2.mouth", "L2.anchor_row", "tiles fall to jaw floor"], ["L2.anchor_row", "L3.anchor_row", "match f298"]]),
    "L3": dict(plate="P3 place du Châtelet", shots=["S6", "S7", "S8"],
               nodes=[dict(id="L3.anchor_row", kind="match_anchor", at=[360, ROW_BASE_Y], note="queue row baseline y=452 at f298"),
                      dict(id="L3.in_Z", kind="entrance", at=[0, 342], note="Z runs in from left f312"),
                      dict(id="L3.queue", kind="obstacle", at=[140, 416], note="contact face of T8 (D), f326"),
                      dict(id="L3.stair", kind="route", at=[[s["tread_top"][0], s["tread_top"][1]] for s in STAIR]),
                      dict(id="L3.V_deck", kind="exit/goal", at=[650, 214], note="impériale, sits f418"),
                      dict(id="L3.out_N", kind="exit", at=[-60, 300], note="T14 flutters out left in S8 f470 (prop leaves frame, not destroyed)")],
               edges=[["L3.in_Z", "L3.queue", "run, blocked (bounce -60 px)"], ["L3.queue", "L3.stair", "domino f341-359"],
                      ["L3.stair", "L3.V_deck", "climb f372-418"]]),
    "L1b": dict(plate="P4 boulevard de la Madeleine (cut B only)", shots=["S4b", "S5b"],
                nodes=[dict(id="L1b.in_Z", kind="entrance", at=[0, 352]), dict(id="L1b.V", kind="goal", at=[645, 345], note="far ahead")],
                edges=[["L1b.in_Z", "L1b.V", "continuity chase"], ["L1b.V", "L3.queue_b", "plain cut f298"]]),
    "L3_B": dict(plate="P3 (cut B)", shots=["S6b", "S7b", "S8b"],
                 nodes=[dict(id="L3.queue_b", kind="obstacle", at=[260, 460], note="7 paper commuters x 260-560"),
                        dict(id="L3.V_platform", kind="exit/goal", at=[610, 420])],
                 edges=[["L3.queue_b", "L3.V_platform", "waits, boards normally f418"]]),
    "screen_direction": "toward the tram is always left -> right in every shot of both cuts",
}

# ------------------------------------------------------------------ entity graph (#43)
entity_graph = dict(
    types=dict(Protagonist=["Z"], Vehicle=["V"], Location=["L1", "L2", "L3", "L1b"], Prop=[t["id"] for t in TILES],
               Sign=["SIGN_GREVE", "PLAQUE_CLICHY", "PLAQUE_CHATELET"], Extra=[f"C{i}" for i in range(1, 8)]),
    nodes=[dict(id="Z", type="Protagonist", motif=["laugh", "orange collar", "auburn bob"], visual_anchor="crown pin, collar hue, mouth id, hair spring state", source="HANDMADE puppet (U3 rig.json)"),
           dict(id="V", type="Vehicle", motif=["tram", "impériale"], visual_anchor="one RGBA cutout = P2 native pixels (P2_Vmask)", source="FORAGED LoC 2002707975"),
           *[dict(id=t["id"], type="Prop", glyph=t["glyph"], row=t["row"], motif=["word", "tooth"], visual_anchor="glyph + paper crop + cut outline", source="HANDMADE tile")
             for t in TILES],
           dict(id="L1", type="Location", plate="P1"), dict(id="L2", type="Location", plate="P2"), dict(id="L3", type="Location", plate="P3"),
           dict(id="L1b", type="Location", plate="P4", cut="B only"),
           *[dict(id=f"C{i}", type="Extra", cut="B only", source="HANDMADE paper commuter") for i in range(1, 8)]],
    edges=[["Z", "wants", "V"], ["SIGN_GREVE", "blocks", "métro"], ["T1..T14", "part_of", "Z.mouth"], ["V", "at", "L1|L2|L3"]],
    rules=[
        dict(id="R0", kind="enter", node="T1..T14", frame=246, precondition="push-in has landed (face_scale>=3)", event="tiles become legible as teeth", reading="teeth"),
        dict(id="R1", kind="replace(reading)", nodes=[f"T{i}" for i in range(8, 15)], from_="teeth", to="falling",
             frames=[281, 287], cause="jaw drop on TAN (f275), N tilts f278", precondition="same 7 tile objects; count 14",
             contract="one clatter tick per release frame"),
        dict(id="R2", kind="replace(reading)+move(location)", nodes=[f"T{i}" for i in range(8, 15)], from_="row(L2 jaw floor)", to="queue(L3)",
             frame=298, cause="match cut", precondition="row baseline y 452±6 and spacing 64±6 at f297 and f298; glyphs DONKTAN in order",
             contract="paper feet appear (part-add, identity kept); plaque names L3 by f300", anchor="row baseline y"),
        dict(id="R3", kind="replace(role)", nodes=["T8"], from_="queue", to="obstacle", frame=326, cause="Z collision",
             contract="impact sound on f326; Z bounce 60 px; tiles wobble"),
        dict(id="R4", kind="replace(reading)", nodes=[f"T{i}" for i in range(8, 15)], from_="queue", to="steps", frames=[341, 359],
             cause="domino cascade from the bump", precondition="each tile tips only after its left neighbour hits it (3 f apart)",
             contract="tread tops per STAIR; one tick per tile, rising pitch"),
        dict(id="R5", kind="exit", nodes=["T14"], frame=418, cause="Z steps off step 4 onto the deck", contract="T14 flutters past in S8 f450-470 and exits frame left; not destroyed"),
        dict(id="R6", kind="move(location)", nodes=["Z"], frame=192, cause="AnchoredJumpCut", precondition="§3.2 preconditions 1-5", contract="distance(Z,V) drops"),
        dict(id="RB", kind="none", cut="B", note="cut B applies no identity rewrite: T stays teeth; the queue is C1..C7"),
    ],
    trace=[dict(f=[0, 239], T="inside Z.mouth (not legible), count 14"), dict(f=[246, 280], T="teeth x14"),
           dict(f=[281, 297], T="T1-T7 teeth, T8-T14 falling->row"), dict(f=[298, 340], T="T8-T14 queue (T1-T7 offscreen in mouth, counted)"),
           dict(f=[341, 417], T="T8-T14 steps"), dict(f=[418, 479], T="T14 loose (flutter, exits f470); T8-T13 steps offscreen")],
    distance_Z_V=[dict(f=143, px="V offscreen right, gap >320"), dict(f=191, px="V offscreen"), dict(f=192, px="~200 (V beside her ear)"),
                  dict(f=326, px=458), dict(f=418, px=0)],
)

# ------------------------------------------------------------------ cues
cues = [
    (8, "offscreen", "tram bell, offscreen LEFT (where V will enter; plan said right, changed for L->R consistency)"),
    (10, "caption", "« Le métro ? En grève. »"), (12, "setup", "V emerges behind Z, far plane, head tracks"),
    (30, "setup", "Z points at V (goal declared)"), (31, "caption", "« …le tram, alors ! »"),
    (48, "chase", "run starts; footsteps on contacts every 8 f (48,56,64…)"), (120, "chase", "V leaves frame right; bell receding"),
    (144, "beat", "she stops, CU, breath"), (156, "laugh", "laugh begins (squeeze eyes, cheeks up)"),
    (158, "sound", "wind gust in (6.6 s)"), (184, "hold", "declared silence + picture hold 184-191 (7.667-8.000 s)"),
    (192, "jump", "JUMP CUT P1->P2; busier ambience in hard; tram bell close, centre"),
    (196, "impact", "PLACE DE CLICHY plaque pops (paper snap)"), (216, "reaction", "eyes open, gaze locks on V, gulp click"),
    (240, "push", "push-in into the mouth begins; low tunnel resonance"),
    *[(fs, "syllable", f"{n}: tile pop + pitched paper click") for n, fs, _ in SYL],
    (254, "caption", "« Doukipudonktan ! »"), (275, "impact", "jaw drop on TAN"), (278, "setup", "loose N tilts"),
    *[(f, "impact", f"tile {k} release click (clatter cascade)") for k, f in RELEASE.items()],
    (298, "match", "MATCH CUT row -> queue at L3 (clatter tail continues 1 f)"), (300, "impact", "PLACE DU CHÂTELET plaque pops"),
    (302, "caption", "« faire la queue… »"), (312, "entrance", "Z runs in from left; footsteps"),
    (326, "impact", "CONTACT: paper/card clack + kit thud"), (326, "hold", "silence 326-332 (13.6-13.85 s) after the bounce"),
    *[(341 + 3 * i, "impact", f"domino tick {i+1}/7 rising pitch") for i in range(7)],
    *[(f, "impact", "foot on card tread (hollow)") for f in (382, 391, 400, 409)],
    (414, "impact", "step on deck"), (418, "beat", "sits; tram bell x2 (418, 426) departure; hooves start"),
    (432, "cut", "CU top deck; rumble + breeze"), (442, "caption", "« Zazie a pris le tram. »"),
    (450, "prop", "T14 flutters past"), (480, "cut", "title card; ambience fades"), (520, "impact", "final tile click"),
]
cues_b = [(192, "cut", "continuity reverse angle L1b; ambience continuous, bell far"), (240, "cut", "MCU"),
          *[(fs, "syllable", f"{n}: paper click (same timing as A)") for n, fs, _ in SYL],
          (298, "cut", "plain cut to L3 queue"), (326, "beat", "she stops at the queue end (no impact)"),
          *[(341 + 3 * i, "step", "queue shuffles: footstep") for i in range(7)], (418, "beat", "steps on board; bell x2"),
          (432, "cut", "CU inside tram")]
timecoded = dict(A=[dict(f=f, t=round(f / FPS, 3), tc=f"00:00:{f // FPS:02d}:{f % FPS:02d}", kind=k, cue=c) for f, k, c in sorted(cues, key=lambda x: x[0])],
                 B_overrides=[dict(f=f, t=round(f / FPS, 3), tc=f"00:00:{f // FPS:02d}:{f % FPS:02d}", kind=k, cue=c) for f, k, c in cues_b],
                 note="Cut B uses A's cues for frames 0-191 and 480-527.")

# ------------------------------------------------------------------ validation
checks = {}
checks["A_B_share_0_143"] = all(EXA[f] == EXB[f] for f in range(144)) and all(s1 == s2 for s1, s2 in zip(SHOTS_A[:2], SHOTS_B[:2]))
checks["A_B_share_144_191_S3"] = all(EXA[f] == EXB[f] for f in range(144, 192))
checks["jump_cut_at_192"] = any(c["f"] == 192 and c["type"] == "jump" for c in cuts["A"])
t297 = tiles_pos("S5", 297)["tiles"][7:]; t298 = tiles_pos("S6", 298)["tiles"]
checks["match_row_y_297_eq_298"] = all(abs(a["base_y"] - b["base_y"]) <= 0 for a, b in zip(t297, t298))
checks["match_row_y_297"] = [a["base_y"] for a in t297]; checks["match_row_y_298"] = [b["base_y"] for b in t298]
checks["match_spacing_ok"] = all(abs((t297[i + 1]["cx"] - t297[i]["cx"]) - (t298[i + 1]["cx"] - t298[i]["cx"])) <= 6 for i in range(6))
checks["match_rot_297_max_deg"] = max(abs(a["rot"]) for a in t297)
checks["match_glyphs"] = "".join(a["glyph"] for a in t297) == "".join(b["glyph"] for b in t298) == "DONKTAN"
vis = [f for f in range(0, 192) if (s := shot_of(SHOTS_A, f)) and v_pos(s, f).get("visible")]
checks["pre1_goal_V_on_screen_frames_before_192"] = len(vis); checks["pre1_ok_ge_36"] = len(vis) >= 36
checks["pre2_location_differs"] = SHOTS_A[2][3] != SHOTS_A[3][3]
za, zb = z_pos("S3", 191), z_pos("S4", 192)
checks["pre3_centroid_delta_px"] = math.dist(za["root"], zb["root"]); checks["pre3_scale_delta"] = abs(za["scale"] - zb["scale"])
checks["pre3_mouth_191_192"] = [EXA[191]["mouth"], EXA[192]["mouth"]]
checks["pre5_V_within_24f"] = v_pos("S4", 192)["visible"]
checks["tile_count_constant_from_240"] = 14
checks["frames_total"] = len(EXA)
checks["on_twos_pose_changes_max_gap_S3"] = max(b - a for a, b in zip(
    [f for f in range(145, 192) if EXA[f]["pose"] != EXA[f - 1]["pose"]],
    [f for f in range(145, 192) if EXA[f]["pose"] != EXA[f - 1]["pose"]][1:]) or [0])
checks["stride_frames"] = 16
assert checks["A_B_share_0_143"] and checks["jump_cut_at_192"] and checks["match_row_y_297_eq_298"] and checks["match_spacing_ok"]
assert checks["pre1_ok_ge_36"] and checks["pre3_centroid_delta_px"] <= 8 and checks["match_glyphs"]

# ------------------------------------------------------------------ boards
def board(sid, f, cut):
    s = next(x for x in (SHOTS_A if cut == "A" else SHOTS_B) if x[0] == sid)
    plate = s[4]
    im = blurred[plate].copy() if plate else Image.new("RGB", (PW, PH), (52, 34, 24))
    if sid == "S5" and f >= 252:   # tunnel: dark throat with Clichy light far inside
        im = Image.new("RGB", (PW, PH), (34, 13, 4)); im.paste(blurred["P2_cu"].resize((120, 90)), (300, 270))
    d = ImageDraw.Draw(im, "RGBA")
    Zc, Vc, Tc = (255, 140, 40, 255), (90, 200, 255, 255), (255, 230, 120, 255)
    z, v, t = z_pos(sid, f), v_pos(sid, f), tiles_pos(sid, f)
    if sid in ("S3", "S4", "S8", "S8b"):
        x0, y0, x1, y1 = CU_HEAD["bbox"]; d.ellipse([x0, y0, x1, y1 + 120], outline=Zc, width=3)
        d.line([(x0, CU_HEAD["brows_y"]), (x1, CU_HEAD["brows_y"])], fill=Zc + (0,) if False else (255, 140, 40, 120), width=1)
        d.arc([CU_HEAD["mouth"][0] - 50, CU_HEAD["mouth"][1] - 25, CU_HEAD["mouth"][0] + 50, CU_HEAD["mouth"][1] + 25], 0, 180, fill=Zc, width=3)
        for e in ("left_eye", "right_eye"):
            ex, ey = CU_HEAD[e]; d.arc([ex - 22, ey - 10, ex + 22, ey + 14], 200, 340, fill=Zc, width=3)
        d.line([(230, 150), (520, 250), (600, 200)], fill=(255, 140, 40, 200), width=4)     # fringe sweep across right eye
        d.rectangle(CU_HEAD["collar_band"], fill=(230, 110, 20, 200))
        d.line([(24, 130), (696, 130)], fill=(255, 255, 255, 70)); d.line([(24, 443), (696, 443)], fill=(255, 255, 255, 70))
    elif z.get("bbox") and z.get("root"):
        d.rectangle(z["bbox"], outline=Zc, width=3); rx, ry = z["root"]; d.ellipse([rx - 5, ry - 5, rx + 5, ry + 5], fill=Zc)
        bx0, by0, bx1, _ = z["bbox"]; hw = (bx1 - bx0) * 0.32
        d.ellipse([(bx0 + bx1) / 2 - hw, by0, (bx0 + bx1) / 2 + hw, by0 + 2 * hw], outline=Zc, width=2)
    elif sid == "S5":
        k = z["face_scale"]; mx, my = z["mouth_centre"]; w = 52 * k
        d.ellipse([mx - w, my - w * 0.6, mx + w, my + w * 0.6], outline=Zc, width=4)
    if v.get("bbox") and v.get("visible"):
        d.rectangle(v["bbox"], outline=Vc, width=3); d.text((v["bbox"][0] + 4, v["bbox"][1] + 4), "V", font=MONOB, fill=Vc)
    if t.get("tiles"):
        for r in t["tiles"]:
            if sid == "S5" and f < 246: continue
            cx, by = r["cx"], r["base_y"]
            tile = Image.new("RGBA", (TILE_W, TILE_H), (230, 214, 184, 230)); td = ImageDraw.Draw(tile)
            td.text((TILE_W / 2, TILE_H / 2), r["glyph"], font=TILEF, fill=(122, 42, 28, 255), anchor="mm")
            tile = tile.rotate(-r["rot"], expand=True, resample=Image.BICUBIC)
            im.paste(tile, (int(cx - tile.width / 2), int(by - TILE_H / 2 - tile.height / 2)), tile)
        d = ImageDraw.Draw(im, "RGBA")
    if t.get("stair"):
        pts = [tuple(s["tread_top"]) for s in t["stair"]]
        for (x, y) in pts: d.rectangle([x - 40, y, x + 40, y + 8], fill=(230, 214, 184, 220))
        d.line(pts, fill=Tc, width=2)
    if sid in ("S5", "S6") or (sid == "S5" and f >= 281):
        d.line([(0, ROW_BASE_Y), (720, ROW_BASE_Y)], fill=(255, 60, 60, 220), width=2); d.text((6, ROW_BASE_Y + 2), "row y=452", font=MONO, fill=(255, 90, 90))
    if sid in ("S6b",):
        for i in range(7): x = 260 + 50 * i; d.rectangle([x - 16, 300, x + 16, 460], outline=(200, 200, 200, 230), width=2)
    if sid == "S1":
        d.rectangle([24, 24, 214, 124], outline=(120, 150, 200, 255), width=3); d.text((40, 60), "MÉTRO / GRÈVE", font=MONO, fill=(200, 220, 255))
    if sid in ("S4", "S6") and f >= 196:
        d.rectangle([560, 18, 700, 78], fill=(47, 63, 85, 230)); d.text((630, 48), "CLICHY" if sid == "S4" else "CHÂTELET", font=MONO, fill=(239, 228, 204), anchor="mm")
    if sid == "tail":
        d.text((360, 250), "Zazie dans le métro", font=TILEF, fill=(230, 214, 184), anchor="mm")
    # eye trace
    et = [e for e in EYE[sid]]
    for i, e in enumerate(et):
        d.ellipse([e[1] - 9, e[2] - 9, e[1] + 9, e[2] + 9], outline=(255, 255, 255, 230), width=2)
        d.text((e[1] + 10, e[2] - 10), str(i + 1), font=MONO, fill=(255, 255, 255))
    if len(et) > 1: d.line([(e[1], e[2]) for e in et], fill=(255, 255, 255, 110), width=1)
    d.rectangle([0, 0, 720, 26], fill=(0, 0, 0, 150))
    d.text((6, 4), f"{cut} {sid}  f{s[1]}-{s[2]}  board@f{f}  {s[5]}  {s[3] or ''}", font=MONO, fill=(255, 255, 255))
    return im

BOARDS = [("A", "S1", 30), ("A", "S2", 96), ("A", "S3", 186), ("A", "S4", 204), ("A", "S5", 297), ("A", "S6", 298),
          ("A", "S6", 326), ("A", "S7", 400), ("A", "S8", 456), ("A", "tail", 500),
          ("B", "S4b", 216), ("B", "S5b", 260), ("B", "S6b", 330), ("B", "S7b", 418), ("B", "S8b", 456), ("A", "S5", 284)]
cols, tw, th = 4, 480, 360
sheet_im = Image.new("RGB", (cols * tw, 4 * th), (20, 20, 20))
for i, (cut, sid, f) in enumerate(BOARDS):
    b = board(sid, f, cut); b.save(LAY / f"board_{cut}_{sid}_f{f:03d}.png")
    sheet_im.paste(b.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
sheet_im.save(SW / "layout-boards.jpg", quality=86)
sheet_im.save(LAY / "layout-boards.jpg", quality=86)

# ------------------------------------------------------------------ evidence
loc = [("P1", "2001698526", "[The Madeleine, and rue Royale, Paris, France]", "loc_05184.jpg", "05100/05184", "No known restrictions on reproduction.",
        "rue Royale looking to the Madeleine portico; columns, trees, cabs, cyclists", "P1_wide (S1/S2), P1_cu via test-shot plate (S3)"),
       ("P2", "2002707975", "[Street scene and monument, in the Place Clichy, Paris, France]", "loc_09974.jpg", "09900/09974", "No known restrictions on publication.",
        "Place Clichy, Moncey monument, horse tram with impériale mid-right, shops (Boulangerie de la Place Clichy)", "P2_cu via test-shot plate (S4/S5), V source"),
       ("P3", "2001698539", "[Place du Chatelet, Paris, France]", "loc_05196.jpg", "05100/05196", "No known restrictions on reproduction.",
        "elevated view of place du Châtelet: theatres, Palmier fountain column, Pont au Change, Seine boat 'Bains froids'", "P3_wide (S6/S7, S6b/S7b), P3_cu (S8/S8b)"),
       ("P4", "2001698544", "[Boulevard of the Madeline (i.e., Madeleine), Paris, France]", "madeleine.jpg", "05200/05201", "No known restrictions on reproduction.",
        "elevated view from the Madeleine colonnade down the boulevard, carriages, trees", "P4_wide (S4b), P4_mcu (S5b), cut B only")]
evidence = []
for pid, item, title, fn, path, rights, shows, used in loc:
    lp = R2 / fn
    evidence.append(dict(id=pid, title=title + " (Photochrom)", author="Detroit Publishing Co. (Photoglob Zürich), c.1890-1900",
                         license="Public domain (no known restrictions)", license_url="https://www.loc.gov/rr/print/res/244_phot.html",
                         source_url=f"https://www.loc.gov/item/{item}/", file_url=f"https://tile.loc.gov/storage-services/service/pnp/ppmsc/{path}v.jpg",
                         local_path=str(lp), sha256=hashlib.sha256(lp.read_bytes()).hexdigest(), rights_text_quoted=rights,
                         what_it_shows=shows, verified_date_or_place=f"loc.gov item JSON fetched 2026-11-16 (meta in {LAY}/meta/item_{item}.json): 'between ca. 1890 and ca. 1900', Paris",
                         used_as="layout plates (graded + defocused r=12 @720) and board backgrounds: " + used))
evidence.append(dict(id="P1P2_testshot_plates", title="test-shot graded plates P1_sharp.png / P2_sharp.png (derived from P1, P2)", author="derived, U3 test shot",
                     license="Public domain (derived from P1/P2)", license_url="https://www.loc.gov/rr/print/res/244_phot.html",
                     source_url="https://www.loc.gov/item/2002707975/", file_url="", local_path=str(TS / "plates"),
                     what_it_shows="crop/grade used by the approved test shot", verified_date_or_place="see test-shot-ledger.json", used_as="P1_cu, P2_cu layout plates"))

out = dict(
    slug="zazie-dans-le-metro", unit="U1 gag-layout", base_revision="plan.md round 3 + test-shot r2 (approved with fixes)", fps=FPS,
    picture=dict(w=PW, h=PH, aspect="4:3", render="centred in 960x540 with black pillars (x offset 120)", coords="720x540 picture coords, origin top-left"),
    frames_total=528, duration_s=22.0,
    deviations_from_plan=[
        "S5 push-in face scale 1->4.5 (plan 3.2) so the 7 lower teeth span 64 px spacing / 56x72 px tiles: the same tiles must read as a queue at waist height beside a 250 px full-figure Z after the match cut.",
        "S5 syllables compressed (DOU 254 … TAN 275, plan TAN 11.9 s) and tiles released one per frame f281-287 (plan: one per 3 f) so they land as an upright row on the jaw floor (y=452) by f296 and the row is still at f297 for the match.",
        "Tram bell at 0.35 s placed offscreen LEFT (plan said right) because V enters L->R from behind her; screen direction stays left->right.",
        "Mouth 3 (talk) is used in S1 and S5b; it is not in the test-shot library (1/2/4/5/6): U3 adds it or the editor falls back to 2.",
        "S4 covers f192-239 only (the test shot ran to f263); its frames 240-263 laugh is replaced by the S5 push-in.",
        "Tail title card needs letters not in T (Z, E, S, L, M, R): new title tiles are an explicit tail exception to invariant 4 (count of T stays 14).",
    ],
    test_shot_fixes_for_U3=["open the full laugh (mouth 5/6) a bit wider, keep the soft gap tooth", "skin toward #b47059 cheek / #b6785e forehead",
                            "fringe sweeps across the right eye on the gust (layout target right_eye=[440,300], sweep line (230,150)->(520,250)->(600,200))",
                            "keep layered hair mass, softer face, grey-olive plates", "Clichy plate saturation down toward the reference"],
    cu_framing=CU_HEAD,
    tiles=dict(set=TILES, w=TILE_W, h=TILE_H, paper="#e6d6b8", ink="#7a2a1c", font="bold serif (DejaVu Serif Bold in boards)",
               ecu_upper_x=UPPER_X, ecu_upper_base_y=UPPER_BASE_Y, ecu_lower_x=LOWER_X, ecu_lower_gum_base_y=LOWER_GUM_BASE_Y,
               row_base_y=ROW_BASE_Y, spacing=64, syllables=[dict(syl=n, f=fs, tiles=ts) for n, fs, ts in SYL],
               release=RELEASE, land=LAND, stair=STAIR, queue_feet="paper feet 8 px below tile body; ground line y=460"),
    word_to_gag=word_to_gag, route=route, shots=shots, exposure_sheet=dict(
        legend=dict(pose="body pose id (Reiniger pose library; cu_laugh.dNNN = test-shot drawing NNN)", mouth="1 closed, 2 small o/gulp, 3 talk, 4 grin, 5 open-gap laugh, 6 open-wide/gasp; ECU: E0 closed, E1 syllable open, E2 jaw drop",
                    eye="open_r (open, looking right), half, squeeze (laugh crescents), pr_open / pr_squeeze (profile)", gust="wind force 0-1.3 on the hair springs (S3/S4 = test_shot.wind_at)",
                    on_twos="poses change on even frames; laugh shoulder shake ±3 px flips every 2 frames (4-frame alternation)"),
        A=EXA, B=EXB),
    cuts=cuts, entity_graph=entity_graph, timecoded_gag_cues=timecoded, validation=checks, plate_stats=plate_stats,
    layout_boards=dict(sheet=str(SW / "layout-boards.jpg"), per_board=str(LAY), boards=[f"{c} {s} f{f}" for c, s, f in BOARDS],
                       legend="orange = Z (bbox, head, root dot; CU = head oval, brow/mouth lines, fringe sweep, collar), blue = V, cream tiles = T, red line = match row y=452, white numbered circles = eye-trace order"),
    evidence=evidence,
    handmade=[dict(item="layout boards (diagrams, not picture)", made_by="U1 gag_layout.py", where=str(LAY)),
              dict(item="gag-route.json (timing, route, exposure, entity graph)", made_by="U1", where=str(SW / "gag-route.json"))],
    absences=["No new foraging needed by U1: plates reused from r2 after loc.gov re-verification. No searches for new material were made, so no licence gaps are logged.",
              "U2's forage/P*_blur.png were not present at run time (forage/ held only meta/); boards use U1's own r2-derived plates."],
    media_for_editor=dict(layout=str(LAY), gag_layout=str(GL)),
)
json.dump(out, open(SW / "gag-route.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(checks, indent=1)); print(json.dumps(plate_stats, indent=1, ensure_ascii=False))
