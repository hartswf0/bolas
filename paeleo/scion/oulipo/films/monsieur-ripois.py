"""Monsieur Ripois / « Rien n'y manquait » — SCION swarm assembly (editor).

A man on a sofa tells a woman he returned her family's silver box with nothing missing.
PRESENT: a real 1942 LoC photograph (John Vachon, PD) cut into GrabCut pieces and articulated
(films/swarm/monsieur-ripois/present_puppets.py, U2) with a handmade silver box and pawn receipt.
FLASHBACK (« selon lui »): handmade jointed-card shadow theatre (shadow_theatre.py, U3).
SOUND: foraged Commons recordings mixed by U1 (sound-manifest.json); voice is captions only.

  python3 films/monsieur-ripois.py                 master  -> assets/films/monsieur-ripois.mp4
  python3 films/monsieur-ripois.py --baseline      control -> films/swarm/monsieur-ripois/cuts/
  python3 films/monsieur-ripois.py --late          late reaction -> films/swarm/monsieur-ripois/cuts/
  python3 films/monsieur-ripois.py --stills 5 20   stills -> films/stills/<slug>/
  python3 films/monsieur-ripois.py --check         cue-timing assertions only (P4)
Timing = plan.md §6 (frames from dialogue-cues.json)."""
import json, math, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SW = HERE / "swarm" / "monsieur-ripois"
sys.path.insert(0, str(SW))
from kit import Film, W, H, FPS

ARGS = sys.argv[1:]
VARIANT = "baseline" if "--baseline" in ARGS else "late" if "--late" in ARGS else "master"
CHECK_ONLY = "--check" in ARGS
sys.argv = [sys.argv[0]] + [a for a in ARGS if a == "--stills" or a.replace(".", "", 1).isdigit()]

CUES = json.load(open(SW / "dialogue-cues.json"))
SOUND = json.load(open(SW / "sound-manifest.json"))
SECONDS, NF = 45.0, 1080                # repair 2: S6 is a 2 s end card (1032-1079)
PX, PW = (W - 720) // 2, 720          # 4:3 picture area, pillarboxed

# ------------------------------------------------------------ shot list (frames, plan §6)
S0, S1, S2, S3A, S3B, S4, S4I, S5, S6 = 0, 48, 216, 468, 516, 696, 756, 864, 1032


def shot_at(f):
    if f < S1: return "S0"
    if f < S2: return "S1"
    if f < S3A: return "S2"
    if f < S3B: return "S3a" if VARIANT != "baseline" else "S3a-base"
    if f < S4: return "S3b"
    if f < S4I: return "S4"
    if f < S5: return "S4i" if VARIANT != "baseline" else "S4-base"
    if f < S6: return "S5"
    return "S6"


# ------------------------------------------------------------ P4 cue assertions (cheap: state only)
def check_cues():
    import present_puppets as PP
    out = {}
    for v in ("master", "late", "baseline"):
        k = PP.load_keys(v)
        her = [PP.state_at(f / FPS, k)["her_head"] for f in range(NF)]
        his = [PP.state_at(f / FPS, k)["his_head"] for f in range(NF)]
        moving = [f for f in range(1, NF) if abs(her[f] - her[f - 1]) > 1e-6]
        first = moving[0] if moving else None
        cap = next(c for c in CUES["captions"] if c["cue_id"] == "CAP-C3")
        onset = cap["parts"][1]["onset"]; end = cap["spoken_end"]
        assert all(abs(h) < 1e-9 for h in her[:onset]), f"{v}: her head moves before « manquait » (C1/C2)"
        if v == "master":
            assert first is not None and abs(first - onset) <= 2, f"master head first moves {first}, onset {onset}"
            last_his = max(f for f in range(onset, 700) if abs(his[f] - his[f - 1]) > 1e-6)
            assert last_his - onset <= 6, f"his lean continues to {last_his}"
        elif v == "late":
            assert first is not None and first >= end + 12, f"late head first moves {first} < {end + 12}"
            assert first >= cap["off"] + 12, f"late head first moves {first} before the caption clears + 12 ({cap['off'] + 12})"
        else:
            assert first is None, "baseline head must stay neutral"
        for a in CUES["assertions"].get(v, []):
            assert a["action_onset_frame"] >= a["onset_frame"], (v, a)
        out[v] = dict(first_head_frame=first, manquait_onset=onset, spoken_end=end)
    return out


CHECK = check_cues()
print("P4 cue timing OK:", CHECK)
if CHECK_ONLY:
    sys.exit(0)

import present_puppets as PP
import shadow_theatre as ST
KEYS = PP.load_keys(VARIANT)

# Repair 1: the shadow screen carries NO synthetic grain or noise texture. Its only modulation is the backlight's own
# falloff (hot spot behind the screen, ~214 centre -> ~180 edges, warmed +5 %), plus the blinds far plane foraged from
# the Vachon print. render_flashback(grain=False) is used, so a flat paper patch is identical between drawings.
def _backlit_paper():
    yy, xx = np.mgrid[0:ST.H, 0:ST.W].astype(np.float32)
    r = np.sqrt(((xx - 330) / 520) ** 2 + ((yy - 230) / 380) ** 2)
    lum = 214.0 - 34.0 * np.clip(r, 0, 1.3) ** 1.6
    return lum[..., None] * np.array([1.05, 1.00, 0.95], np.float32)[None, None]
ST._assets()
ST.PAPER = _backlit_paper()
# repair 2: « — selon lui — » slightly larger and more opaque for small screens; same place, same frames (every S2 frame)
def _label_big():
    fnt = ImageFont.truetype(ST.FONT, 22)
    im = Image.new("L", (ST.W, 40), 0); d = ImageDraw.Draw(im)
    txt = "« — selon lui — »"
    d.text(((ST.W - d.textlength(txt, font=fnt)) / 2, 8), txt, font=fnt, fill=255)
    return np.asarray(im).astype(np.float32) / 255.0 * 0.97
ST._LABEL = _label_big()

# ------------------------------------------------------------ captions: white serif italic release-print subtitles
CAPF = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", 26)
TITF = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", 44)
WHITE, EDGE = (244, 242, 236), (16, 16, 16)
CAPS = CUES["captions"]


def caption(img, f):
    for c in CAPS:
        if c["on"] <= f < c["off"]:
            full = "".join(p["text"] for p in c["parts"])
            x = PX + PW / 2 - CAPF.getlength(full) / 2       # laid out once: parts append, no re-layout
            d = ImageDraw.Draw(img, "RGBA")
            for p in c["parts"]:
                if f >= p["onset"]:
                    d.text((x, H - 36), p["text"], font=CAPF, fill=WHITE + (255,), anchor="ls",
                           stroke_width=2, stroke_fill=EDGE + (130,))
                x += CAPF.getlength(p["text"])


END_CARD = ["Photographies : John Vachon, 1942 (Library of Congress, FSA/OWI, domaine public).",
            "Les personnes photographiées jouent ici des rôles de fiction.",
            "La boîte, la reconnaissance du Mont-de-Piété et les silhouettes sont des accessoires fabriqués.",
            "Sons : Wikimedia Commons. Aucune voix ; sous-titres seulement."]
ENDF = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", 19)


def end_card(img, f):
    """repair 2 (reviewer): on-screen label that the sitters play fictional roles and the evidence objects are props."""
    a = min(1.0, (f - S6) / 6) * min(1.0, (NF - 1 - f) / 6)
    if a <= 0: return
    d = ImageDraw.Draw(img, "RGBA")
    for i, line in enumerate(END_CARD):
        d.text((W / 2, H / 2 - 48 + 32 * i), line, font=ENDF, fill=WHITE + (int(255 * a),), anchor="mm")


def title(img, f):
    tc = CUES["title_card"]
    a = 0.0
    if tc["on"] <= f < tc["full"]: a = (f - tc["on"]) / (tc["full"] - tc["on"])
    elif tc["full"] <= f < tc["fade"]: a = 1.0
    elif tc["fade"] <= f < tc["off"]: a = 1 - (f - tc["fade"]) / (tc["off"] - tc["fade"])
    if a > 0:
        ImageDraw.Draw(img, "RGBA").text((W / 2, H / 2), tc["text"], font=TITF, fill=WHITE + (int(255 * a),), anchor="mm")


# ------------------------------------------------------------ picture
def picture_at(f):
    t = f / FPS
    s = shot_at(f)
    if s in ("S0", "S6"): return None
    if s == "S2": return ST.render_flashback(t - S2 / FPS, grain=False)    # warm paper + « — selon lui — » inside
    if s == "S3a": return PP.render_box_insert(t - S3A / FPS, "open")      # first frame after S2: empty ring slot
    if s == "S4i": return PP.render_receipt_insert(t - S4I / FPS)
    return PP.render_twoshot(t, KEYS)                                       # S1, S3b, S4, S5, baseline holds


def frame(t, ink):
    f = ink.i
    ink._grain = False                       # every layer already carries its own sampled grain; no second grain
    img = Image.new("RGB", (W, H), (0, 0, 0))
    pic = picture_at(f)
    if pic is not None:
        if VARIANT == "baseline" and f >= 1008:                          # baseline: hold, then fade
            pic = Image.blend(pic, Image.new("RGB", pic.size, (0, 0, 0)), min(1.0, (f - 1008) / 24))
        img.paste(pic, (PX, 0))
    if shot_at(f) == "S0": title(img, f)
    if shot_at(f) == "S6": end_card(img, f)
    caption(img, f)
    ink.img = img
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ------------------------------------------------------------ sound: U1's foraged mix, per sound-manifest.json
def read_wav(p):
    with wave.open(str(p)) as w:
        n, ch = w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), "<i2").astype(np.float64) / 32767
    x = x.reshape(-1, ch)
    return x[:, 0], x[:, -1]


def sound(mix):
    want = f"mix-{VARIANT}-loud.wav"          # repair 1: U1's mix loudness-normalised to about -23 LUFS (ffmpeg loudnorm)
    path = next(Path(e["file"]) for e in SOUND["files"] if Path(e["file"]).name == want)
    L, R = read_wav(path)
    mix.add(L / 1.414, 0.0, 1.0, pan=-1.0)
    mix.add(R / 1.414, 0.0, 1.0, pan=1.0)


slug = "monsieur-ripois" if VARIANT == "master" else f"monsieur-ripois-{VARIANT}"
film = Film(slug, seconds=SECONDS, boil=0, wobble=0)
film.picture(frame)
film.sound(sound)
film.poster_at = 21.0
if __name__ == "__main__":
    out = None if VARIANT == "master" else SW / "cuts"
    film.render(out_dir=out) if out else film.render()
