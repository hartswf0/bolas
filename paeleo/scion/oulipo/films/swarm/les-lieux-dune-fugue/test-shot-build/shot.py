"""Render the test shot: python3 shot.py [--bake] [--stills t ...]"""
import sys, os, math, json, pickle, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films")
import scene
from scene import *
from pathlib import Path
import kit

if "--bake" in sys.argv or not os.path.exists(CUT + "/bake.pkl"):
    scene.bake()
B = pickle.load(open(CUT + "/bake.pkl", "rb"))
MEM_BG, BT, BA, BPOS = B["mem"]

SERIF_I = "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"
MONO = ROOT + "/assets/fonts/ibm-plex-mono.woff2"
f_cap = ImageFont.truetype(SERIF_I, 25)
f_gl = ImageFont.truetype(SERIF_I, 15)
f_mono = ImageFont.truetype(MONO, 13)
f_rec = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
CREAM, MUTED_L, MUTED_D = (236, 226, 200), (168, 156, 134), (82, 70, 52)

CAPTION = (2.2, 6.5, "« Le banc, c'était l'hiver, à peu près. »", "The bench: it was winter, roughly.")
RECORD = "souvenir · vers l'hiver (intervalle) · lien P01→P03 : INFÉRÉ"


def leaves_layer(tl, tr, c):
    """warp both leaves (2x supersampled) with their FK poses; returns rgb, alpha at stage res"""
    S2 = (SW * 2, SH * 2)
    rgb = np.zeros((SH * 2, SW * 2, 3), np.float32); A = np.zeros((SH * 2, SW * 2), np.float32)
    poses = {}
    for i, (th, left) in enumerate([(tl, True), (tr, False)]):
        lf = B["leaves"][i]
        M, proj = leaf_pose(th, left, c * 0.95)
        t = cv2.warpPerspective(lf["tex"], M, S2, flags=cv2.INTER_LINEAR)
        a = cv2.warpPerspective(lf["a"], M, S2, flags=cv2.INTER_LINEAR)
        shade = 0.30 + 0.70 * math.cos(math.radians(th))          # turns away from lamp B into the passage
        # paper card thickness: free edge shows the lighter core as it swings (lamp side)
        rgb = rgb * (1 - a[..., None]) + t * shade * a[..., None]
        A = np.maximum(A, a)
        kx, ky = lf["knob"]
        poses["L" if left else "R"] = dict(theta=round(th, 3), knob_px=[round(v / 2 - P, 2) for v in ptx(M, kx * 2, ky * 2)],
                                           hinge_top=[round(v / 2 - P, 2) for v in ptx(M, 0 if left else lf['w'] * 2, 0)],
                                           hinge_bottom=[round(v / 2 - P, 2) for v in ptx(M, 0 if left else lf['w'] * 2, 1440)])
    rgb = cv2.resize(rgb, (SW, SH), interpolation=cv2.INTER_AREA)
    A = cv2.resize(A, (SW, SH), interpolation=cv2.INTER_AREA)
    return rgb, A, poses


def p01_frame(t):
    tl, tr, c, settle = state(t)
    # memory (depth 1.0 park, 0.6 bench) lit by its own cold light through the aperture
    mem = MEM_BG.copy()
    bx, by = BPOS[0] - c * 0.4, BPOS[1] + settle
    h, w = BA.shape
    sh = np.zeros((SH, SW), np.float32)
    X, Y = int(round(bx)), int(round(by))
    sh[Y:Y + h, X:X + w] = BA
    sh = shift(sh, bx - X + MEM_LIGHT["dx"], by - Y + MEM_LIGHT["dy"])
    mem *= (1 - MEM_LIGHT["strength"] * cv2.GaussianBlur(sh, (0, 0), MEM_LIGHT["blur"]))[..., None]
    bl = np.zeros((SH, SW), np.float32); bl[Y:Y + h, X:X + w] = BA
    bc = np.zeros((SH, SW, 3), np.float32); bc[Y:Y + h, X:X + w] = BT
    bl, bc = shift(bl, bx - X, by - Y), shift(bc, bx - X, by - Y)
    mem = mem * (1 - bl[..., None]) + bc * bl[..., None]
    ap = np.zeros((SH, SW), np.float32); ap[OY0 + P:, OX0 + P:OX1 + P] = 1
    ap = cv2.GaussianBlur(shift(ap, MEM_LIGHT["aperture_dx"], MEM_LIGHT["aperture_dy"]), (0, 0), 14)
    mem = mem * (0.42 + 0.58 * ap)[..., None]
    mem = mem * 0.86 + np.array([0.20, 0.22, 0.25], np.float32) * 0.14 * (0.5 + 0.5 * ap)[..., None]   # haze
    # leaves
    lr, la, poses = leaves_layer(tl, tr, c)
    ls = shift(B["leaf_shadow"], -c * 0.95, 0)
    lr = lr * (1 - 0.5 * ls)[..., None] * B["fac_rgb"].mean() / max(B["fac_rgb"].mean(), 1e-3)
    img = mem * (1 - la[..., None]) + lr * la[..., None]
    # facade on top (depth 0)
    fr, fa = shift(B["fac_rgb"], -c, 0), shift(B["fac_a"], -c, 0)
    img = img * (1 - fa[..., None]) + fr * fa[..., None]
    img = img[P:P + H, P:P + W]
    return img, dict(t=round(t, 4), theta_L=tl, theta_R=tr, truck=c, bench_settle=settle, leaves=poses)


def text(im, t):
    d = ImageDraw.Draw(im, "RGBA")
    if t < T_CUT:
        d.text((16, 12), "P01 · prise B · soir", font=f_mono, fill=MUTED_L + (230,))
        a0, a1, fr_, en = CAPTION
        al = min(1, max(0, (t - a0) / 0.35)) * min(1, max(0, (a1 - t) / 0.35))
        if al > 0:
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            x = 140
            dl.text((x, 650), fr_, font=f_cap, fill=(12, 10, 10, int(200 * al)), anchor="ls")
            dl.text((x, 674), en, font=f_gl, fill=(12, 10, 10, int(200 * al)), anchor="ls")
            lay = lay.filter(ImageFilter.GaussianBlur(2.2))
            im.alpha_composite(lay)
            d = ImageDraw.Draw(im, "RGBA")
            d.text((x, 650), fr_, font=f_cap, fill=CREAM + (int(255 * al),), anchor="ls")
            d.text((x, 674), en, font=f_gl, fill=(196, 186, 164, int(235 * al)), anchor="ls")
            d.text((946, 706), RECORD, font=f_rec, fill=MUTED_D + (int(255 * al),), anchor="rs")
    else:
        d.text((16, 12), "P03 · retour · silence déclarée", font=f_mono, fill=(70, 62, 48, 235))
    return im


from PIL import ImageFilter
EVENTS = []


def render_frame(t):
    if t < T_CUT:
        img, ev = p01_frame(t)
        EVENTS.append(ev)
    else:
        img = B["p03"][P:P + H, P:P + W]
        EVENTS.append(dict(t=round(t, 4), shot="P03 retour", audio="digital silence"))
    im = Image.fromarray(to8(img)).convert("RGBA")
    return text(im, t).convert("RGB")


# ---------------------------------------------------------------- sound
SND = TS + "/dl"


def load_wav(path, mix, speed=1.0):
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = tmp + "/a.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(int(44100 / speed)), out], check=True)
        with wave.open(out) as wf:
            x = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float64) / 32768
    return x / max(np.abs(x).max(), 1e-6)   # played back at 44.1k -> pitched/slowed by `speed`


SOUND_LOG = []


def sound(mix):
    n8 = int(T_CUT * mix.rate)
    # present tone: room + distant street (synthesized, kit) ; ducks 6 dB under the remembered bell
    room = mix.lowpass(mix.noise(T_CUT, "pink"), 700) * 0.05 + mix.lowpass(mix.noise(T_CUT, "brown"), 200) * 0.05
    tt = np.arange(len(room)) / mix.rate
    duck = 1 - 0.5 * np.clip((tt - 1.4) / 0.6, 0, 1) * np.clip((6.9 - tt) / 0.6, 0, 1)
    mix.add(room * duck, 0.0, 0.9)
    mix.room(0.0, T_CUT, gain=0.012)
    SOUND_LOG.append(dict(cue="present room/street tone", at=0.0, until=T_CUT, source="synthesized (kit noise + room)", duck_db=-6))
    # creak while the leaves move (foraged if present)
    creak_p = SND + "/Door_handle_creaking.ogg"
    if os.path.exists(creak_p) and os.path.getsize(creak_p) > 1000:
        cr = mix.lowpass(load_wav(creak_p, mix, speed=0.62), 2500)
        mix.add(cr[: int(2.2 * mix.rate)] * np.hanning(int(2.2 * mix.rate))[: len(cr[: int(2.2 * mix.rate)])], T_OPEN + 0.05, 0.16, -0.3)
        mix.add(cr[int(2.4 * mix.rate): int(3.6 * mix.rate)], T_CLOSE + 0.1, 0.12, -0.2)
        SOUND_LOG.append(dict(cue="creak (slowed 0.62x, lowpass 2.5 kHz)", at=[T_OPEN + 0.05, T_CLOSE + 0.1], source="Door handle creaking.ogg (Commons, PD)"))
    else:
        for k, at in enumerate([T_OPEN + 0.1, T_CLOSE + 0.15]):
            x = mix.band(mix.noise(1.4), 300, 900) * np.sin(np.linspace(0, math.pi, int(1.4 * mix.rate))) ** 2
            x *= 0.6 + 0.4 * np.sin(2 * math.pi * 7 * np.arange(len(x)) / mix.rate)
            mix.add(x, at, 0.06, -0.3)
        SOUND_LOG.append(dict(cue="creak", at=[T_OPEN + 0.1, T_CLOSE + 0.15], source="synthesized (kit band noise)"))
    # remembered bell: far, low-passed, dislocated (belongs to the memory, not the place)
    for at in (1.55, 4.35):
        sub = kit.Mix(4.0, seed=3); sub.bell(0.0, freq=311, seconds=3.8, gain=1.0)
        b = mix.lowpass(sub.L, 650)
        mix.add(b, at, 0.22, 0.35)
    SOUND_LOG.append(dict(cue="remembered bell x2, lowpass 650 Hz", at=[1.55, 4.35], source="synthesized (kit bell)"))
    # closing: small knock (left leaf), the thud (right leaf contact frame)
    mix.thud(CONTACT_L, freq=85, gain=0.22, pan=-0.2, seconds=0.25)
    mix.click(CONTACT_L, gain=0.10, bright=1800)
    thud_p = SND + "/Close_door__Gravity_Sound_.wav"
    if os.path.exists(thud_p) and os.path.getsize(thud_p) > 1000:
        th = load_wav(thud_p, mix, speed=0.7)
        i = int(np.argmax(np.abs(th) > 0.5))
        th = mix.lowpass(th[max(i - 200, 0):], 3000)
        mix.add(th[: int(0.4 * mix.rate)] * np.linspace(1, 0, len(th[: int(0.4 * mix.rate)])) ** 2, CONTACT_R - 200 / mix.rate, 0.55, 0.0)
        SOUND_LOG.append(dict(cue="door thud (slowed 0.7x)", at=CONTACT_R, source="Close door (Gravity Sound).wav (Commons, CC BY 4.0)"))
    mix.thud(CONTACT_R, freq=62, gain=0.55, seconds=0.32)
    SOUND_LOG.append(dict(cue="thud body", at=CONTACT_R, source="synthesized (kit thud)"))
    # HARD CUT TO DIGITAL SILENCE: every sample after T_CUT is exactly 0
    mix.L[n8:] = 0.0
    mix.R[n8:] = 0.0
    SOUND_LOG.append(dict(cue="DIGITAL SILENCE", at=T_CUT, until=DUR, source="samples = 0"))


class Shot(kit.Film):
    def frame(self, k):
        return render_frame(k / self.fps)


if __name__ == "__main__":
    if "--stills" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1:]]
        for t in ts:
            render_frame(t).save(f"{CUT}/still_{t:05.2f}.png")
        print("stills ok")
        sys.exit()
    film = Shot("test-shot", DUR, size=(W, H))
    film.poster_at = 3.5
    film.sound(sound)
    film.render(out_dir=Path(OUTDIR))
    json.dump(dict(events=EVENTS, sound=SOUND_LOG, contact_L=CONTACT_L, contact_R=CONTACT_R, cut=T_CUT,
                   pieces=B["log"]["pieces"], prints=B["log"]["prints"]),
              open(OUTDIR + "/test-shot-build/stage_events.json", "w"), indent=1, ensure_ascii=False)
