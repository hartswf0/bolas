"""Shot output: frames pass through kit.Ink (boil=0, wobble=0, paper(grain=False), no vignette),
written as pre-caption PNG sequences. Records SHA-1 per frame."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
import kit  # noqa: E402  (project kit; read-only use)
from lib import *  # noqa

BAND = (30, 30, 30)  # #1e1e1e ground under the plates (never visible: plates cover the frame)

SHOT_T0 = {"S1": 0.0, "S2": 5.5, "S3": 8.5, "S4": 11.5, "S5": 19.0, "S6": 24.5, "S7": 27.0}
SHOT_N = {"S1": 132, "S2": 72, "S3": 72, "S4": 180, "S5": 132, "S6": 60, "S7": 192}


def through_kit(g8, fi_pass):
    ink = kit.Ink(fi_pass / FPS, fi_pass, (W, H), boil=0, wobble=0)
    ink.paper(color=BAND, grain=False)
    ink.paste(Image.fromarray(to_rgb(g8), "RGB"))
    return ink.finish()


def write_shot(shot, frames_iter):
    """frames_iter yields uint8 HxW grey frames. Returns list of sha1 and path."""
    d = U1 / "shots" / shot
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.png"):
        f.unlink()
    shas = []
    f0 = int(round(SHOT_T0[shot] * FPS))
    for i, g8 in enumerate(frames_iter):
        img = through_kit(g8, f0 + i)
        p = d / f"{shot}_{i:04d}.png"
        img.save(p, optimize=False, compress_level=6)
        shas.append(sha1(p))
    assert len(shas) == SHOT_N[shot], (shot, len(shas))
    return shas, str(d)
