"""Render the E4 test shot through kit.Film (boil=0, wobble=0, no grain), with foraged sound.
Run: python3 -I film.py   (from any directory)"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, cv2
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films')
import lightbox as lb, e4
from kit import Film

SW = HERE.parent
SRC = Path('/home/user/bolas/paeleo/scion/oulipo/films/sources/99-ways-subjective/test-shot')


def decode(p, rate=44100):
    """untrusted media: decoded only by ffmpeg to raw float mono"""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-ac', '1', '-ar', str(rate), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def ok(p):
    return p.exists() and subprocess.run(['ffprobe', '-v', 'error', str(p)], capture_output=True).returncode == 0


page = lb.make_page()
shot = e4.Shot(page)
film = Film('test-shot', seconds=e4.DUR, size=(1280, 720), boil=0, wobble=0)
film.poster_at = 9.5


@film.picture
def picture(t, ink):
    ink.paper(grain=False)
    im = shot.render(t)
    ink.img = Image.fromarray(cv2.resize(im, (1280, 720), interpolation=cv2.INTER_AREA))


SOUND_LOG = []


@film.sound
def sound(mix):
    r = mix.rate
    # 1) watch tick: single ticks cut from a PD clock recording, high-passed to a small wristwatch voice,
    #    re-timed to a 5-beat/s watch escapement; starts only when the dial faces the eye (local 6.5)
    clk = decode(SRC / 'Clock_ticking.ogg')
    w = int(0.06 * r)
    ticks = []
    for sec in range(3):
        seg = clk[sec * r: sec * r + r]
        k = int(np.argmax(np.abs(seg)))
        a = max(0, k - int(0.008 * r))
        tk = seg[a:a + w].copy()
        tk = mix.band(tk, 2200, 9000) * np.exp(-np.linspace(0, 7, len(tk)))
        ticks.append(tk / (np.abs(tk).max() + 1e-9))
    t = 6.5; n = 0
    while t < e4.DUR:
        g = 0.10 * min(1.0, (t - 6.5) / 0.5 + 0.25) * (1.0 if n % 2 == 0 else 0.75)
        if t > 8.4: g *= 0.8                                    # quiet under the answer
        mix.add(ticks[n % len(ticks)], t, g, -0.25)             # the watch sits centre-left
        t += 0.2; n += 1
    SOUND_LOG.append(dict(cue='watch tick', start=6.5, rate_hz=5, pan=-0.25, source='Clock_ticking.ogg'))
    # 2) the last footfall settling at the foot of the stair (local 0.12), from the foraged stair recording
    pas = decode(SRC / 'Pasos_en_escalera_de_caracol.ogg')
    env = np.convolve(np.abs(pas), np.ones(441) / 441, 'same')
    k = int(np.argmax(env[int(7.2 * r):int(8.6 * r)])) + int(7.2 * r)    # one strong step
    step = pas[k - int(0.04 * r): k + int(0.32 * r)] * np.hanning(int(0.36 * r)) ** 0.3
    mix.add(mix.lowpass(step, 2500) / (np.abs(step).max() + 1e-9), 0.12, 0.22, 0.0)
    SOUND_LOG.append(dict(cue='last footfall', start=0.12, source='Pasos_en_escalera_de_caracol.ogg', src_t=round(k / r, 2)))
    # 3) cloth: arm rising, cuff pulled back, wrist roll. Foraged rustle if the PD file arrived, else band noise.
    rus = SRC / 'rustle.ogg'
    use_f = ok(rus)
    src = decode(rus) if use_f else None
    for a, b, g, pan in ((2.6, 3.7, 0.10, -0.35), (5.05, 5.9, 0.16, -0.1), (6.0, 6.6, 0.07, -0.25)):
        n_ = int((b - a) * r)
        if use_f:
            off = int((10 + 7 * a) * r); x = src[off:off + n_].copy()
        else:
            x = mix.noise(b - a, 'pink')
        x = mix.band(x, 300, 4200) * np.hanning(n_)
        x /= (np.abs(x).max() + 1e-9)
        mix.add(x, a, g, pan)
    SOUND_LOG.append(dict(cue='cloth rustle', source='rustle.ogg (PD)' if use_f else 'synthesized band-limited noise (no foraged cloth recording obtained: Commons rate limit)'))
    # 4) paper strip drawn through the window during the head turn: very faint slide
    x = mix.band(mix.noise(3.0, 'pink'), 1500, 7000) * np.hanning(int(3.0 * r))
    mix.add(x / (np.abs(x).max() + 1e-9), 1.0, 0.025, 0.3)
    SOUND_LOG.append(dict(cue='strip slide (faint)', source='synthesized'))


film.render(out_dir=SW)
json.dump(shot.log, open(SW / 'test-shot-build' / 'frame-log.json', 'w'))
json.dump(SOUND_LOG, open(SW / 'test-shot-build' / 'sound-log.json', 'w'), indent=1)
print('frames logged', len(shot.log))
