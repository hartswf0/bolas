"""TEST SHOT: E5, forgetting (page P6 -> P8), 9.75 s, 960x540, 24 fps, animation on twos.
Renders with kit.Film (kit's added grain switched off: only the photographs' own grain and the sheet's
fibre). Writes ../test-shot.mp4, ../timing.json. Run: python3 -I shot.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from panels import *  # noqa
sys.path.insert(0, str(ROOT / "films"))
from kit import Film  # noqa

FPS = 24
A_END = 84                      # P6 shot: frames 0..83
TOTAL = 234
CAM_A = (1.19, 1745, 1225)      # scale, page x0, page y0
CAM_B = (0.52, 614, 2176)
DROP = [(-40, 10), (-14, 4), (0, 0), (-6, 2), (0, 0)]   # 4 frames of fall + rest; lands on the 3rd
A_DROP0 = 12
B_DROP0 = 62

ARM_KEYS = {0: 45, 12: 50, 14: 28, 16: 10, 18: -3, 20: 0}
HEAD_KEYS = {0: (0, 1.0), 32: (-4, .985), 38: (-8, .97), 44: (-11, .955)}
SCR_KEYS = {0: 0, 52: 3, 54: 0, 56: 3, 58: 0}


def held(keys, L):
    v = None
    for k in sorted(keys):
        if L >= k:
            v = keys[k]
    return v


def state(f):
    if f < A_END:
        if f < A_DROP0:
            return ("A", None)
        i = min(f - A_DROP0, 4)
        return ("A", DROP[i])
    L = f - A_END
    arm = held(ARM_KEYS, L)
    hd, sq = held(HEAD_KEYS, L)
    scr = held(SCR_KEYS, L)
    b = None if L < B_DROP0 else DROP[min(L - B_DROP0, 4)]
    return ("B", (arm, hd, sq, scr), b)


BASE = page_base()
put_panel(BASE, "P6", panel_P6(balloon=False))
put_panel(BASE, "P7", panel_P7())
put_panel(BASE, "P8", panel_P8(ARRIVE, balloon=False))
finish(BASE)
_cache = {}


def render_state(st):
    if st in _cache:
        return _cache[st]
    if st[0] == "A":
        s, x0, y0 = CAM_A
        pg = BASE.copy()
        if st[1] is not None:
            put_panel(pg, "P6", panel_P6(True, st[1][0], st[1][1]))
            finish(pg, PANELS["P6"])
    else:
        s, x0, y0 = CAM_B
        pg = BASE.copy()
        arm, hd, sq, scr = st[1]
        b = st[2]
        c = panel_P8(dict(arm=arm, head=hd, squash=sq, scratch=scr), balloon=b is not None,
                     dy=b[0] if b else 0, lift=b[1] if b else 0)
        put_panel(pg, "P8", c)
        finish(pg, PANELS["P8"])
    w, h = int(round(960 / s)), int(round(540 / s))
    crop = pg[y0:y0 + h, x0:x0 + w]
    if crop.shape[1] < w:   # beyond the page edge: the sheet continues (replicate its edge)
        crop = np.pad(crop, ((0, 0), (0, w - crop.shape[1]), (0, 0)), mode="edge")
    img = cv2.resize(crop.clip(0, 255).astype(np.uint8), (960, 540), interpolation=cv2.INTER_AREA)
    out = Image.fromarray(img)
    _cache[st] = out
    return out


film = Film("test-shot", seconds=TOTAL / FPS, boil=0, wobble=0)
film.poster_at = 8.0


@film.picture
def picture(t, ink):
    ink._grain = False
    f = min(TOTAL - 1, int(round(t * FPS)))
    ink.paste(render_state(state(f)), (0, 0))


@film.sound
def sound(mix):
    sec = TOTAL / FPS
    mix.room(0, sec, gain=0.022, hum=60)
    tap = lambda at, g=0.5: (mix.click(at, gain=g, bright=2600, seconds=0.04), mix.thud(at, freq=120, gain=g * 0.35, seconds=0.12))
    tap((A_DROP0 + 2) / FPS)
    for i, at in enumerate([0.95, 1.45, 1.95, 2.45, 2.95]):        # the visitor walking off the platform
        mix.step(at, gain=0.16 * (0.72 ** i), pan=-0.5 - 0.1 * i, surface="wood")
    b = A_END / FPS
    mix.whoosh(b + 12 / FPS, seconds=0.3, gain=0.03, pan=0.2)       # paper arm sliding up
    for L in (32, 38, 44):                                         # card hinge clicks
        mix.click(b + L / FPS, gain=0.12, bright=5000, seconds=0.015)
    for L in (52, 56):                                             # pencil scratching the temple
        x = mix.band(mix.noise(0.07), 1800, 7000) * np.hanning(int(0.07 * mix.rate))
        mix.add(x, b + L / FPS, 0.10, 0.1)
    tap(b + (B_DROP0 + 2) / FPS)
    mix.click(b + 4.1, gain=0.08, bright=3000, seconds=0.02)       # one clock tick in the hold


if __name__ == "__main__":
    timing = {"fps": FPS, "frames": TOTAL, "shots": {"P6": [0, A_END - 1], "P8": [A_END, TOTAL - 1]},
              "balloon_land": {"Thanks!": A_DROP0 + 2, "What the hell...": A_END + B_DROP0 + 2},
              "arm_poses": {A_END + k: v for k, v in ARM_KEYS.items()},
              "head_steps": {A_END + k: v for k, v in HEAD_KEYS.items()},
              "scratches": {A_END + k: v for k, v in SCR_KEYS.items()},
              "final_hold_frames": [A_END + B_DROP0 + 4, TOTAL - 1],
              "final_hold_s": (TOTAL - 1 - (A_END + B_DROP0 + 4)) / FPS,
              "rest_equals_page": "last frame of each shot renders panel_P6()/panel_P8(REST) = the page panels"}
    json.dump(timing, open(BUILD / "timing.json", "w"), indent=1)
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        for f in map(int, sys.argv[2:]):
            render_state(state(f)).save(f"/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/f{f:03d}.png")
    else:
        film.render(out_dir=SWARM)
