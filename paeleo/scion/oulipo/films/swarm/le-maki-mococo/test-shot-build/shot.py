"""le-maki-mococo TEST SHOT: the defining beat ("hangs"), condensed into one held close-up, 10 s.

Four passages of the same held shot (film-time ellipses shown in the cue strip):
  A  0:15.5-0:18.5  TEXT cue: the paper mouth says L1 (real voice); its words type on measured onsets; the guessed gong hangs on the knot.
  B  0:38.0-0:40.5  IMAGE cue: the Brehm binturong arrives on the same knot; the gong tears into 12 wedges and falls. Mouth opens slowly.
  C  0:44.0-0:46.5  Reader A's reconsideration caption; mouth 'O', then closes. Declared silence (room tone only).
  D  0:52.0-0:54.0  The mouth says "hangs" once more; a red-pencil underline draws itself under "hangs".
Run:  python3 -I shot.py            (needs voice/ files; writes ../test-shot.mp4)
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OULIPO = HERE.parents[3]
sys.path.insert(0, str(OULIPO / "films"))
import kit  # noqa: E402
import paper as P  # noqa: E402
import mouth as M  # noqa: E402
import hang as Hg  # noqa: E402
import voice as V  # noqa: E402

SWARM = HERE.parent
SECONDS = 10.0
FPS = 24
INK = (42, 36, 34)          # #2a2422
MUTED = (107, 98, 91)       # #6b625b
ROSE = (190, 110, 118)
PENCIL = (184, 36, 40)
CAL = "/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf"
INTER = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
INTER_M = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
S = P.S
F_POEM = ImageFont.truetype(CAL, 30 * S)
F_CAP = ImageFont.truetype(INTER, 19 * S)
F_LAB = ImageFont.truetype(INTER_M, 13 * S)
F_CUE = ImageFont.truetype(INTER, 13 * S)
F_TAG = ImageFont.truetype(INTER, 11 * S)

POEM = ["In the dark it hangs and swings,", "binturong, binturong,", "smells of popcorn, never rings —", "binturong, binturong."]
X0, BASE0, LEAD = 462, 330, 36
CUES = {"sound": 2.0, "text": 15.5, "image": 38.0}
SEGS = [(0.0, 3.0, 15.5), (3.0, 5.5, 38.0), (5.5, 8.0, 44.0), (8.0, 10.01, 52.0)]
RESP_A = dict(speaker="Reader A (fictional)", t_said=44.0, cites=["image", "text"],
              quoted_span="Oh — it hangs by its tail. ‘Never rings’: it was never a gong.")


def film_time(T):
    for a, b, f0 in SEGS:
        if a <= T < b:
            return f0 + (T - a)
    return SEGS[-1][2] + T - SEGS[-1][0]


# ---------------------------------------------------------------- glyph table (fixed boxes) ---
def glyph_table():
    tab = []
    for li, line in enumerate(POEM):
        base = BASE0 + li * LEAD
        for ci, ch in enumerate(line):
            x = X0 + F_POEM.getlength(line[:ci]) / S
            w = F_POEM.getlength(ch) / S
            tab.append(dict(line=li, i=ci, ch=ch, x=round(x, 2), base=base, w=round(w, 2)))
    return tab


GLYPHS = glyph_table()


def word_box(line, word, nth=0):
    s = POEM[line]
    i = s.index(word)
    g = [g for g in GLYPHS if g["line"] == line and i <= g["i"] < i + len(word)]
    return (g[0]["x"], g[0]["base"] - 22, g[-1]["x"] + g[-1]["w"], g[0]["base"] + 7)


HANGS_BOX = word_box(0, "hangs")

# ------------------------------------------------------------------ voice + visemes (#47) ---
VO = V.build()               # assembled real recordings, measured timing
VO_A = 0.30                  # shot time where L1 starts (passage A)
VO_D = 8.12                  # shot time where "hangs" is said again (passage D)
LEAD_S = 1 / 24              # mouth leads the sound by one frame


def phone_at(T):
    """Return (pose class, energy 0..1) of the voice at shot time T, from the measured track."""
    for start, track in ((VO_A, VO["L1"]), (VO_D, VO["hangs"])):
        t = T + LEAD_S - start
        for ph in track["phones"]:
            if ph["t0"] <= t < ph["t1"]:
                k = int(t * 100)
                env = track["env"]
                e = env[k] if 0 <= k < len(env) else 0
                return ph["v"], e
    return None, 0.0


def gesture(T):
    """Silent acting: the reader's thought (B surprise, C 'O' then close)."""
    ft = film_time(T)
    if 38.0 <= ft < 40.5:
        return ("rest" if ft < 38.3 else "surprise"), None
    if 44.0 <= ft < 46.5:
        if ft < 44.1:
            return "surprise", None
        if ft < 45.0:
            return "O", None
        if ft < 45.5:
            return "hm", None
        return "rest", None
    return None, None


STEPS = int(SECONDS * 12) + 1
SIM = {("EI", "LNT"): .45, ("LNT", "EI"): .45, ("A", "surprise"): .5, ("surprise", "A"): .5, ("O", "UW"): .4,
       ("UW", "O"): .4, ("rest", "MBP"): .5, ("MBP", "rest"): .5, ("hm", "rest"): .6, ("rest", "hm"): .6}


def targets():
    out = []
    for s in range(STEPS):
        T = s / 12
        v, e = phone_at(T)
        g, _ = gesture(T)
        want = v or g or "rest"
        costs = {}
        for pid in M.POSE_IDS:
            c = 0.0 if pid == want else 1.0 - SIM.get((want, pid), 0.0)
            if want in M.KEY_POSES and pid != want:
                c *= 2.5            # protected key poses: never averaged away
            costs[pid] = c
        out.append(costs)
    return out


PATH = M.decode(targets())


def jaw_at(T, pose):
    """FK jaw angle = pose base + measured-energy articulation (speech) or eased gesture (silence)."""
    base = M.POSES[pose]["jaw"]
    v, e = phone_at(T)
    if v:
        return base * (0.75 + 0.45 * e)
    ft = film_time(T)
    if pose == "surprise" and 38.0 <= ft < 40.5:
        return 0.6 + (base - 0.6) * kit.smooth(kit.clamp((ft - 38.3) / 1.1))      # slow opening
    return base


# ------------------------------------------------------------------------- layers ---
mouth = M.Mouth()
hanging = Hg.Hanging()
WHITE = np.full((P.CH, P.CW, 3), 255, np.float32)
_mcache = {}


def mouth_img(pose, jaw):
    key = (pose, round(jaw, 1))
    if key not in _mcache:
        _mcache[key] = mouth.render(pose, key[1], WHITE)
    return _mcache[key]


def typed_chars(T):
    """Passage A: letters land as each word is said (onset->nucleus end); from B on, all four lines are set."""
    ft = film_time(T)
    if ft >= 38.0:
        return {(g["line"], g["i"]): 1.0 for g in GLYPHS}, None
    out, cursor = {}, None
    line = POEM[0]
    pos = 0
    for w in VO["L1"]["words"]:
        i = line.index(w["text"], pos)
        pos = i + len(w["text"])
        t0, t1 = VO_A + w["t0"], VO_A + w["t0"] + max(0.12, (w["t1"] - w["t0"]) * 0.8)
        n = len(w["text"]) + (1 if pos < len(line) and line[pos] in ",." else 0)
        for k in range(n):
            tk = t0 + (t1 - t0) * k / max(1, n)
            if T >= tk:
                out[(0, i + k)] = min(1.0, 0.35 + (T - tk) * 24 / 2 * 0.65)
                cursor = (0, i + k)
        # the space after a word is set with it
    return out, cursor


def type_layer(T, img):
    lay = Image.new("RGBA", (P.CW, P.CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    chars, cursor = typed_chars(T)
    for g in GLYPHS:
        a = chars.get((g["line"], g["i"]))
        if a:
            d.text((g["x"] * S, g["base"] * S), g["ch"], font=F_POEM, fill=INK + (int(255 * a),), anchor="ls")
    if cursor is not None and (int(T * 4) % 2 == 0 or True):
        g = next(g for g in GLYPHS if (g["line"], g["i"]) == cursor)
        x = (g["x"] + g["w"] + 2) * S
        d.rectangle([x, (g["base"] - 24) * S, x + 2.5 * S, (g["base"] + 5) * S], fill=ROSE + (230,))
    ft = film_time(T)
    # cue strip + timestamp (the ledger on every frame)
    m = int(ft // 60); sec = int(ft % 60)
    x = 462 * S; y = 22 * S
    d.text((x, y), f"{m}:{sec:02d}", font=F_LAB, fill=MUTED + (255,), anchor="lm")
    x += 44 * S
    for name, tq in CUES.items():
        on = ft >= tq
        r = 4.2 * S
        d.ellipse([x - r, y - r, x + r, y + r], outline=MUTED + (255,), width=int(1.3 * S), fill=(MUTED + (255,)) if on else None)
        d.text((x + 9 * S, y), name, font=F_CUE, fill=MUTED + (255,), anchor="lm")
        x += (F_CUE.getlength(name) / S + 30) * S
    # layer tag beside the hanging thing (typed graph: hypothesis vs cue)
    tag = ("Reader A’s gong", "(guess)") if ft < 38.5 else ("Brehm, 1895", "(image cue)")
    d.text((772 * S, 128 * S), tag[0], font=F_TAG, fill=MUTED + (255,), anchor="rs")
    d.text((772 * S, 143 * S), tag[1], font=F_TAG, fill=MUTED + (255,), anchor="rs")
    # caption: Reader A's reconsideration (cites image released 0:38 <= 0:44)
    if ft >= 44.1:
        a = kit.ramp(ft, 44.1, 44.35) * (0.55 if ft >= 52.0 else 1.0)
        A = int(255 * a)
        d.text((462 * S, 468 * S), "READER A (fictional) · 0:44 · cites: image (0:38), text", font=F_LAB,
               fill=MUTED + (A,), anchor="ls")
        words, lines, cur = RESP_A["quoted_span"], [], ""
        txt = "“" + words + "”"
        for w in txt.split(" "):
            if F_CAP.getlength((cur + " " + w).strip()) / S > 470:
                lines.append(cur); cur = w
            else:
                cur = (cur + " " + w).strip()
        lines.append(cur)
        for k, ln in enumerate(lines):
            d.text((462 * S, (494 + 25 * k) * S), ln, font=F_CAP, fill=INK + (A,), anchor="ls")
    arr = np.asarray(lay, np.float32).copy()
    arr[..., 3] /= 255.0
    P.over(img, arr)
    underline(T, img)


_pencil = None


def underline(T, img):
    """Red pencil drawn straight-ahead under 'hangs': dabs along a slightly bowed stroke, skipping on paper tooth."""
    global _pencil
    ft = film_time(T)
    t0, t1 = 52.30, 53.30
    if ft < t0:
        return
    if _pencil is None:
        x0, _, x1, yb = HANGS_BOX
        rs = np.random.RandomState(52)
        n = 260
        u = np.linspace(0, 1, n)
        xs = x0 - 3 + (x1 - x0 + 7) * u
        ys = yb + 2.0 + 1.6 * np.sin(u * np.pi) * -1 + 0.7 * u + rs.normal(0, 0.12, n).cumsum() * 0.05
        press = 0.55 + 0.45 * np.sin(np.clip(u * 1.15, 0, 1) * np.pi) ** 0.5
        tooth = P.fibre_field(1)
        _pencil = (xs, ys, press, tooth)
    xs, ys, press, tooth = _pencil
    k = int(len(xs) * kit.smooth(kit.clamp((ft - t0) / (t1 - t0))))
    if k < 2:
        return
    lay = Image.new("L", (P.CW, P.CH), 0)
    d = ImageDraw.Draw(lay)
    for i in range(k):
        r = (1.25 + 0.5 * press[i]) * S
        d.ellipse([xs[i] * S - r, ys[i] * S - r * 0.8, xs[i] * S + r, ys[i] * S + r * 0.8], fill=int(160 * press[i]))
    a = np.asarray(lay, np.float32) / 255.0
    a = a * np.clip(0.75 + 0.5 * tooth, 0, 1)          # graphite/wax skips on the paper tooth
    img[..., :3] = img[..., :3] * (1 - a[..., None]) + np.array(PENCIL, np.float32) * a[..., None]


def theta_at(ft):
    if ft < 38.0:
        return 0.9 * math.exp(-(ft - 11.5) / 9.0) * math.sin(2 * math.pi * (ft - 11.5) / 1.5)
    return -7.0 * math.exp(-(ft - 38.0) / 1.5) * math.sin(2 * math.pi * (ft - 38.0) / 1.45)


LOG = []


def compose(T):
    k = int(round(T * FPS))
    step = min(len(PATH) - 1, k // 2)          # 12 fps on twos
    pose = PATH[step]
    jaw = jaw_at(step * 2 / FPS, pose)
    img = mouth_img(pose, jaw).copy()
    type_layer(T, img)
    ft = film_time(T)
    hanging.render(img, ft, theta=theta_at(ft))
    LOG.append(dict(k=k, T=round(T, 4), film_t=round(ft, 4), pose=pose, jaw=round(jaw, 2)))
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((960, 540), Image.LANCZOS)
    return out


# ------------------------------------------------------------------------ invariants ---
def check():
    # cue order and citation (P1): every cited cue released before t_said
    assert CUES["sound"] < CUES["text"] < CUES["image"]
    assert all(CUES[c] <= RESP_A["t_said"] for c in RESP_A["cites"]), "anachronistic citation"
    # rewrite precondition (P4): animal only at t >= release(image); knot constant
    assert Hg.KNOT == (840.0, 70.0)
    # poem glyph boxes are a pure function of the fixed strings (no reflow possible)
    assert glyph_table() == GLYPHS
    # skin confined left of 45%
    sk = mouth.head[..., 3] + mouth.jaw[..., 3] + mouth.neck[..., 3]
    xs = np.nonzero(sk.max(0) > 0.5)[0]
    assert xs.max() / S < 0.45 * 960, xs.max() / S


film = kit.Film("test-shot", SECONDS, boil=0, wobble=0)


@film.picture
def picture(t, ink):
    ink.paper((255, 255, 255), grain=False)      # pure white field, no faux grain
    ink.paste(compose(t))


@film.sound
def sound(mix):
    mix.room(0, SECONDS, gain=0.012)            # declared: kit room tone
    mix.add(VO["L1"]["wav"], VO_A, gain=0.9)     # real voice (Lingua Libre, CC0)
    mix.add(VO["hangs"]["wav"], VO_D, gain=0.9)
    # B: the animal's weight lands on the cord: a dull paper flop; wedges tick as they tear. NO ring.
    mix.thud(3.0, freq=95, gain=0.10, seconds=0.25)
    for ft in hanging.gone(38.0):
        T = 3.0 + ft - 38.0
        mix.click(T, gain=0.11, pan=0.55, bright=2600, seconds=0.035)
        x = mix.band(mix.noise(0.09), 700, 3200) * np.exp(-np.linspace(0, 6, int(0.09 * mix.rate)))
        mix.add(x, T + 0.02, gain=0.035, pan=0.6)
    # D: red pencil on paper (band-passed noise shaped by the stroke speed)
    t0 = 8.0 + 0.30
    n = int(1.0 * mix.rate)
    u = np.linspace(0, 1, n)
    sp = np.gradient(np.array([kit.smooth(x) for x in u]))
    x = mix.band(mix.noise(1.0), 1800, 6000) * (sp / sp.max()) * (0.7 + 0.3 * np.random.RandomState(5).rand(n))
    mix.add(x, t0, gain=0.05, pan=0.1)


if __name__ == "__main__":
    check()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        for T in [float(x) for x in sys.argv[2:]]:
            compose(T).save(f"/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/st_{T:05.2f}.png")
        sys.exit()
    film.render(out_dir=SWARM)
    json.dump(dict(glyphs=GLYPHS, hangs_box=HANGS_BOX, knot=Hg.KNOT, segments=SEGS, cues=CUES, response=RESP_A,
                   decoder_path_12fps=PATH, frames=LOG, voice=dict(L1=VO["L1"]["words"], L1_phones=VO["L1"]["phones"],
                                                                     hangs_phones=VO["hangs"]["phones"])),
              open(HERE / "shot_trace.json", "w"), indent=0)
