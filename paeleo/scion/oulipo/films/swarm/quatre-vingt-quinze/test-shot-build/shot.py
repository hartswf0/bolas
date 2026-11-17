"""Test shot: the DOWN route, G -> B -> E -> (H), film time 41.0-47.5 s.

Run:  python3 -I shot.py      (writes ../test-shot.mp4, ../test-page.png, JSON reports)
The shot clock is film time: shot u = 0 is film t = 41.0. The beat (down E) starts at 44.0;
44.5 s is the decisive frame.
"""
import json
import math
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import qvq  # noqa: E402
from qvq import CELLS, CW, CH, PW, PH, PAPER  # noqa: E402

sys.path.insert(0, str(qvq.FILMS))
from kit import Film, Ink  # noqa: E402

OUT = HERE.parent
T0, T1 = 41.0, 47.5
DOWN = "ADGBEHCFI"
assert 32 + 3 * DOWN.index("E") == 44 <= 44.5 < 47, "beat clock"
FW, FH = 1280, 720
VIEW_H = CH / 0.62
VIEW_W = VIEW_H * FW / FH


def local(c, t):
    """Cell-local time on the down route (cells start at 32 + 3*index)."""
    return t - (32 + 3 * DOWN.index(c))


# ------------------------------------------------------------ static ---
def build_static():
    page = Image.new("RGB", (PW, PH), PAPER)
    for c in CELLS:
        page.paste(qvq.cell_image(c, None), qvq.cell_origin(c))
    return page


def arrow_sprite(angle, size):
    ink = Ink(0, 0, (240, 240), boil=0, wobble=1.4)
    import random
    ink.rng = random.Random(int(angle * 10 + size * 100))
    ink.img = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    qvq.arrow(ink, 120, 120, angle, size * 2, 1)
    return ink.img.resize((120, 120), Image.LANCZOS)


ARROWS = {  # transition -> (gutter point, angle)
    "G>B": ((1185, 720), -50),
    "B>E": ((1680, 905), 90),
    "E>H": ((1680, 1595), 90),
}


def camera(t):
    keys = [(41.0, "G"), (41.5, "B"), (44.0, "B"), (44.5, "E"), (47.0, "E"), (47.5, "H")]
    for (ta, ca), (tb, cb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            u = 0 if tb == ta else (t - ta) / (tb - ta)
            u = u * u * u * (u * (6 * u - 15) + 10)
            a, b = qvq.cell_center(ca), qvq.cell_center(cb)
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
    return qvq.cell_center(keys[-1][1])


def cell_drawing(c, t):
    lt = local(c, t)
    if c == "B" and 0 <= lt < 3:
        return min(31, int(lt * 12)) if lt < 2.6 else 31
    if c == "E" and 0 <= lt < 3:
        return qvq.e_drawing_of(lt)
    return None


def wash_alpha(c, t):
    i = DOWN.index(c)
    lt = local(c, t)
    if lt < 0:
        return 0.55            # not yet read on this route
    if lt < 0.5:
        return 0.55 * (1 - lt / 0.5)   # the wash lifts as the camera enters
    return 0.0


STATIC = None
SCAF = None
SPRITES = {}


def page_at(t):
    global STATIC, SCAF
    if STATIC is None:
        STATIC = build_static()
        SCAF = qvq.scaffold("down", "down", 2).resize((PW, PH), Image.LANCZOS)
        for k, (pt, ang) in ARROWS.items():
            SPRITES[(k, 1)] = arrow_sprite(ang, 0.62)
            SPRITES[(k, 2)] = arrow_sprite(ang, 1.0)
    page = STATIC.copy()
    for c in "BE":
        d = cell_drawing(c, t)
        page.paste(qvq.cell_image(c, d), qvq.cell_origin(c))
    paper = None
    for c in CELLS:
        a = wash_alpha(c, t)
        if a > 0:
            x0, y0 = qvq.cell_origin(c)
            box = (x0, y0, x0 + CW, y0 + CH)
            reg = page.crop(box)
            page.paste(Image.blend(reg, Image.new("RGB", reg.size, PAPER), a), box[:2])
    page.paste(SCAF, (0, 0), SCAF)
    # the red cut-paper arrow steps into the gutter being crossed (2 drawings), then stays
    for k, start in (("G>B", 41.0), ("B>E", 44.0), ("E>H", 47.0)):
        nxt = start + 3.0
        if start <= t < nxt:
            st = 1 if t < start + 1 / 12 else 2
            sp = SPRITES[(k, st)]
            (x, y), ang = ARROWS[k]
            back = 0 if st == 2 else 14
            dx, dy = -math.cos(math.radians(ang)) * back, -math.sin(math.radians(ang)) * back
            page.paste(sp, (int(x - 60 + dx), int(y - 60 + dy)), sp)
    return page


def frame_at(t):
    page = page_at(t)
    cx, cy = camera(t)
    sx = VIEW_W / FW
    x0, y0 = cx - VIEW_W / 2, cy - VIEW_H / 2
    return page.transform((FW, FH), Image.AFFINE, (sx, 0, x0, 0, sx, y0), resample=Image.BICUBIC, fillcolor=PAPER)


# ------------------------------------------------------------- sound ---
SRC = qvq.SRC


def wav(path):
    w = wave.open(str(path))
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0
    if w.getnchannels() == 2:
        x = x.reshape(-1, 2).mean(1)
    return x, w.getframerate()


def sound(mix):
    bell, r = wav(SRC / "bell_fridingen.wav")
    keys, r2 = wav(SRC / "keys.wav")
    assert r == r2 == mix.rate

    def seg(x, a, b, fade=0.25):
        s = x[int(a * r):int(b * r)].copy()
        n = int(fade * r)
        s[-n:] *= np.linspace(1, 0, n) ** 2
        s[:64] *= np.linspace(0, 1, 64)
        return s
    mix.room(0.0, T1 - T0, gain=0.012, hum=50)
    # B's own cue: two consecutive strikes of the Fridingen station bell (the recording's own 1.2 s spacing),
    # placed where the drawn clapper strikes: B local 1.4 and 2.6 s.
    b0 = 32 + 3 * DOWN.index("B")
    mix.add(seg(bell, 10.55, 11.75, 0.08), b0 + qvq.B_STRIKES[0] - T0 - 0.05, gain=0.75, pan=-0.1)
    mix.add(seg(bell, 11.75, 12.88, 0.35), b0 + qvq.B_STRIKES[1] - T0 - 0.03, gain=0.75, pan=-0.1)
    # E's own cue: one key-on-key clink grain at the top of the lift (E local 1.0 s)
    e0 = 32 + 3 * DOWN.index("E")
    mix.add(seg(keys, 0.31, 0.62, 0.12), e0 + 1.0 - T0, gain=0.55, pan=0.1)
    mix.reverb(amount=0.32, size=1.7)   # the waiting hall


def main():
    film = Film("test-shot", seconds=T1 - T0, size=(FW, FH), boil=0)
    film.poster_at = 44.5 - T0

    def picture(t, ink):
        ink._grain = False
        ink.img = frame_at(T0 + t)
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
    film.picture(picture)
    film.sound(sound)
    if "--stills" in sys.argv:
        for t in (41.25, 42.4, 43.6, 44.0, 44.25, 44.5, 45.0, 46.0, 47.25):
            frame_at(t).save(HERE / f"still_{t:05.2f}.png")
        return
    film.render(out_dir=OUT)
    # reports -------------------------------------------------------
    qvq.build_page().save(OUT / "test-page.png")
    errs = {}
    for rec in qvq.JOINT_LOG:
        for k, v in rec["errors"].items():
            errs[k] = max(errs.get(k, 0), v)
    feet = [rec["ankle"] for rec in qvq.JOINT_LOG if rec["cell"] == "E"]
    feet2 = [rec["ankle2"] for rec in qvq.JOINT_LOG if rec["cell"] == "E"]
    sheet = [{"film_t": round(T0 + k / 24, 4), "B": cell_drawing("B", T0 + k / 24), "E": cell_drawing("E", T0 + k / 24)}
             for k in range(int((T1 - T0) * 24))]
    holds = {}
    for c in "BE":
        seq = [s[c] for s in sheet]
        runs, n = [], 1
        for a, b in zip(seq, seq[1:]):
            if a == b:
                n += 1
            else:
                runs.append(n)
                n = 1
        runs.append(n)
        holds[c] = min(runs[1:-1]) if len(runs) > 2 else min(runs)
    rep = {
        "fk_bone_length_error_px_max_by_joint": {k: round(v, 6) for k, v in errs.items()},
        "fk_planted_ankle_y_range_px_E": [round(min(p[1] for p in feet), 3), round(max(p[1] for p in feet), 3)],
        "fk_planted_ankle2_y_range_px_E": [round(min(p[1] for p in feet2), 3), round(max(p[1] for p in feet2), 3)],
        "key_attachment": "the key is pasted in the wrist frame at a constant offset (6, 22) px; it cannot drift by construction",
        "pose_dp_E_heads": qvq.E_HEADS, "pose_dp_cost": qvq.E_HEAD_COST,
        "pose_dp_targets_deg": [qvq.e_head_target(k) for k in range(1, 13)],
        "protected_pose_E_up_turned_at_top": qvq.E_HEADS[-1] == "v_up",
        "min_hold_frames_at_24fps_interior": holds,
        "bell_strikes_film_t": [32 + 9 + s for s in qvq.B_STRIKES],
        "exposure_sheet": sheet,
    }
    (HERE / "test-shot-report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: v for k, v in rep.items() if k != "exposure_sheet"}, indent=1))


if __name__ == "__main__":
    main()
