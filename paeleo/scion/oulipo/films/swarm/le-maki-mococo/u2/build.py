"""U2 build: provisional onsets (measured from the CC0 Lingua Libre takes), pieces, pose sheets, metrics,
comparison PNG, decoder path, mouth_test.mp4, mouth_rig.json.

Run:  python3 -I films/swarm/le-maki-mococo/u2/build.py [--no-video]
Audio is decoded only with ffmpeg (via the test-shot voice.py).  The rig itself (mouth_rig.py) is PIL+numpy.
"""
import json
import shutil
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SW = HERE.parent
sys.path.insert(0, str(SW))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SW / "test-shot-build"))
OULIPO = SW.parents[2]
sys.path.insert(0, str(OULIPO / "films"))
import mouth_rig as M  # noqa: E402
import measure as Q  # noqa: E402

SRC = OULIPO / "films" / "sources" / "le-maki-mococo"
MOUTH = SRC / "mouth"
MEDIA = SRC / "u2-paper-mouth-puppet-and-kinetic-type-mouth-shape-designer-pose-library-typesetter-"
REF = OULIPO / "assets" / "references" / "maki.webp"
for d in (MOUTH, MOUTH / "pieces", MEDIA):
    d.mkdir(parents=True, exist_ok=True)
INTER = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
INTER_M = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
NOVIDEO = "--no-video" in sys.argv


# ------------------------------------------------------------------ 1. provisional onsets ----------
def provisional():
    import voice as V                     # test-shot-build/voice.py: ffmpeg decode + envelope measurement
    vo = V.build()["L1"]
    wav = vo["wav"]
    pcm = (np.clip(wav / max(1e-9, np.abs(wav).max()) * 0.9, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(MEDIA / "voice_L1.wav"), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(44100); wf.writeframes(pcm.tobytes())
    env = [round(float(x), 4) for x in vo["env"]]
    words = vo["words"]
    L1_ids = [k for k, v in M.SYL.items() if v["line"] == 0]
    assert [M.SYL[k]["text"] for k in L1_ids] == [w["text"] for w in words]

    def l1_at(t0):
        syl = []
        for sid, w in zip(L1_ids, words):
            ph = [(round(t0 + p["t0"], 3), round(t0 + p["t1"], 3), p["v"]) for p in vo["phones"] if p["word"] == w["text"]]
            syl.append(dict(seg_id=sid, t0=round(t0 + w["t0"], 3), t1=round(t0 + w["t1"], 3), phones=ph,
                            timing="measured (envelope onset/nucleus/coda of the CC0 take)"))
        return syl

    def estimated(t_start):
        """L2-L4: no measured audio yet (U1 owns the full-poem voice).  Estimated 0.16 s syllables."""
        syl, t = [], t_start
        for li in (1, 2, 3):
            ids = [k for k, v in M.SYL.items() if v["line"] == li]
            for k, sid in enumerate(ids):
                d = 0.24 if M.SYL[sid]["text"] == "rong" else 0.16
                syl.append(dict(seg_id=sid, t0=round(t, 3), t1=round(t + d, 3), timing="estimated (provisional)"))
                t += d + (0.08 if sid.endswith(".s1") or "rong" in M.SYL[sid]["text"] else 0.02)
            t += 0.30
        return syl

    S3_T0 = 15.60
    s1 = l1_at(2.05)
    s1 += estimated(s1[-1]["t1"] + 0.35)
    tl = dict(status="provisional",
              note="PROVISIONAL onsets (U1's cue_timeline.json was not present when U2 ran). L1 timing is measured "
                   "from the assembled CC0 takes (speaker Grendelkhan, Lingua Libre); L2-L4 in S1/S3 are estimated "
                   "placeholders only. Replace with U1's measured syllables.",
              voice_L1=str(MEDIA / "voice_L1.wav"),
              sections=dict(
                  S1=dict(t_voice=2.05, syllables=s1, env=env, t_env0=2.05),
                  S3=dict(t_voice=S3_T0, syllables=l1_at(S3_T0) + estimated(S3_T0 + words[-1]["t1"] + 0.35),
                          env=env, t_env0=S3_T0),
                  S8=dict(t_voice=52.40, syllables=l1_at(52.40), env=env, t_env0=52.40)))
    json.dump(tl, open(MOUTH / "provisional_onsets.json", "w"), indent=1)
    return tl


# ------------------------------------------------------------------ helpers -------------------------
def on_white(im):
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return bg.convert("RGB")


def masks(pose, lip_set, jaw):
    """Visible region masks at film res (skin, lips, cavity) using the rig's own alphas and FK rotation."""
    R = M.rig()
    L = R.lip(pose, lip_set)
    def img(a):
        return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L")
    def rot(a):
        return np.asarray(img(a).rotate(-jaw, resample=Image.BICUBIC, center=(M.HINGE[0] * M.S, M.HINGE[1] * M.S)),
                          np.float32) / 255 if jaw > 1e-3 else a
    def film(a):
        return np.asarray(img(a).resize((M.W, M.H), Image.BILINEAR), np.float32) / 255 > 0.5
    up, lo = L["up_a"], rot(L["lo_a"])
    head, jawa, neck = R.a_head, rot(R.a_jaw), R.a_neck
    lip = (up > 0.5) | ((lo > 0.5) & (head < 0.5))
    skin = ((head > 0.5) | (jawa > 0.5) | (neck > 0.5)) & ~lip
    cav = np.asarray(R.cavity.getchannel("A"), np.float32) / 255 > 0.5
    cav = cav & ~lip & ~(head > 0.5) & ~(jawa > 0.5)
    return film(skin), film(lip), film(cav)


def pose_metrics():
    out = {}
    for ls in ("A", "B"):
        for pid in M.POSE_IDS:
            j = M.POSES[pid]["jaw"]
            fr = np.asarray(on_white(M.mouth_image(pid, ls, int(round(j / 0.25)))))
            sk, lp, cv = masks(pid, ls, j)
            out[f"{ls}:{pid}"] = Q.measure(fr, sk, lp, cv)
    return out


# ------------------------------------------------------------------ 2. pieces + sheets -------------
def save_pieces():
    R = M.rig()
    paths = {}
    for name in ("head", "neck", "teeth_up", "teeth_lo", "cavity"):
        p = MOUTH / "pieces" / f"{name}.png"
        getattr(R, name).save(p); paths[name] = str(p)
    p = MOUTH / "pieces" / "jaw_skin.png"
    M.to_rgba(R.jaw_rgb, R.a_jaw).save(p); paths["jaw_skin"] = str(p)
    for k, im in R.tongue.items():
        p = MOUTH / "pieces" / f"tongue_{k}.png"; im.save(p); paths[f"tongue_{k}"] = str(p)
    for ls in ("A", "B"):
        for pid in M.POSE_IDS:
            L = R.lip(pid, ls)
            for part in ("up", "lo"):
                p = MOUTH / "pieces" / f"lip{ls}_{pid}_{part}.png"
                L[part].save(p); paths[f"lip{ls}_{pid}_{part}"] = str(p)
    return paths


def pose_sheet():
    fl = ImageFont.truetype(INTER_M, 15)
    fs = ImageFont.truetype(INTER, 12)
    cw, ch = 300, 290
    sheet = Image.new("RGB", (cw * 5 + 40, (ch + 26) * 4 + 70), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((20, 18), "le-maki-mococo · U2 paper-mouth replacement library (#38) · 10 drawings per lip set · jaw on FK hinge",
           font=fl, fill=(42, 36, 34))
    for r, ls in enumerate(("A", "A", "B", "B")):
        for c in range(5):
            pid = M.POSE_IDS[(r % 2) * 5 + c]
            j = M.POSES[pid]["jaw"]
            im = on_white(M.mouth_image(pid, ls, int(round(j / 0.25)))).crop((110, 0, 450, 330)).resize((cw - 10, ch - 10))
            x, y = 20 + c * cw, 50 + r * (ch + 26)
            sheet.paste(im, (x, y))
            d.text((x, y + ch - 6), f"{M.LIP_SETS[ls]['name']} · {pid} · jaw {j:.1f}°", font=fs, fill=(107, 98, 91))
    p = MOUTH / "pose_sheet.png"
    sheet.save(p)
    return str(p)


def compare(track, onsets):
    """Frame (film t=17.6 s, mid 'hangs') next to maki.webp at equal height."""
    t = 17.45
    fr = Image.new("RGBA", (M.W, M.H), (255, 255, 255, 255))
    fr.alpha_composite(M.mouth_layer(t, track, "A"))
    fr.alpha_composite(M.type_layer(t, onsets))
    ref = Image.open(REF).convert("RGB").resize((M.W, M.H), Image.LANCZOS)
    out = Image.new("RGB", (M.W * 2 + 20, M.H + 40), (255, 255, 255))
    out.paste(fr.convert("RGB"), (0, 40)); out.paste(ref, (M.W + 20, 40))
    d = ImageDraw.Draw(out)
    f = ImageFont.truetype(INTER, 15)
    d.text((10, 12), f"U2 paper mouth, film t={t:.2f} s (S3, 'hangs'), handmade", font=f, fill=(42, 36, 34))
    d.text((M.W + 30, 12), "reference: assets/references/maki.webp (not traced, not pasted into the film)", font=f,
           fill=(42, 36, 34))
    p = MOUTH / "compare_maki.png"
    out.save(p)
    fr.convert("RGB").save(MEDIA / "still_S3_hangs.png")
    return str(p), np.asarray(fr.convert("RGB"))


# ------------------------------------------------------------------ 3. test render -----------------
def render_test(track, onsets, voice):
    import kit
    T0, SEC = 15.30, 4.6
    film = kit.Film("mouth_test", SEC, boil=0, wobble=0)

    @film.picture
    def pic(t, ink):
        ink.paper((255, 255, 255), grain=False)
        ft = T0 + t
        lay = Image.new("RGBA", (M.W, M.H), (255, 255, 255, 255))
        lay.alpha_composite(M.mouth_layer(ft, track, M.lip_set_at(ft)))
        lay.alpha_composite(M.type_layer(ft, onsets))
        ink.paste(lay)

    @film.sound
    def snd(mix):
        mix.room(0, SEC, gain=0.010)                                  # declared: kit room tone
        mix.add(voice, 15.60 - T0, gain=0.9)                         # real voice (CC0)

    film.render(out_dir=MOUTH)
    return str(MOUTH / "mouth_test.mp4")


def load_voice():
    with wave.open(str(MEDIA / "voice_L1.wav")) as wf:
        x = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float64) / 32767
    return x * 0.075 / (np.sqrt(np.mean(x ** 2)) + 1e-9)          # same RMS as the test shot's assembly


if __name__ == "__main__":
    tl = provisional()
    events, onsets_by, status = M.film_events()
    track = M.make_track(events, M.BREATHS, seconds=66.0)
    assert M.flicker_count(track.path) == 0
    onsets_S3 = onsets_by["S3"]
    pieces = save_pieces()
    sheet = pose_sheet()
    cmp_path, cmp_frame = compare(track, {k: v for k, v in onsets_S3.items() if k.startswith("L1")})
    metrics = pose_metrics()
    # the comparison frame itself
    pid, jaw = track.frame(17.45)
    sk, lp, cv = masks(pid, "A", jaw)
    cmp_metrics = Q.measure(cmp_frame, sk, lp, cv)
    json.dump(dict(status=status, metrics=metrics, compare_frame=dict(pose=pid, jaw=jaw, **cmp_metrics),
                   reference=Q.reference(), pieces=pieces, sheet=sheet, compare=cmp_path,
                   S1_path=track.ledger(2.0, 9.6), S3_path=track.ledger(15.5, 19.4),
                   onsets_S3=onsets_S3, flicker=M.flicker_count(track.path)),
              open(HERE / "build_out.json", "w"), indent=1)
    if not NOVIDEO:
        print(render_test(track, {k: v for k, v in onsets_S3.items() if k.startswith("L1")}, load_voice()))
    print("ok", status)
