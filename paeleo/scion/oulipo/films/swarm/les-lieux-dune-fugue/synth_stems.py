#!/usr/bin/env python3
"""U3 synth_stems.py -- the HANDMADE (kit.Mix-synthesized) sound stems for les-lieux-dune-fugue.

Each stem is rendered alone, mono-in-stereo, 44.1 kHz 16-bit, peak-normalised to -6 dBFS,
to films/sources/les-lieux-dune-fugue/narration-sound-writer/stems/<name>.wav.
Gains, pans and times live in sound_cues.json (the editor places stems with mix.add).
Nothing here is foraged. kit.py is imported, not edited.
"""
import math, os, sys, wave
import numpy as np

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
sys.path.insert(0, ROOT + "/films")
import kit  # noqa: E402

OUT = ROOT + "/films/sources/les-lieux-dune-fugue/narration-sound-writer/stems"
os.makedirs(OUT, exist_ok=True)
R = kit.RATE


def save(name, x):
    x = np.asarray(x, np.float64)
    pk = np.abs(x).max()
    if pk > 0:
        x = x / pk * 0.5
    st = np.stack([x, x], 1)
    with wave.open(f"{OUT}/{name}.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(R)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    print(name, f"{len(x)/R:.2f}s")


def fade(x, a=0.4, b=0.4):
    n = len(x); e = np.ones(n)
    ia, ib = int(a * R), int(b * R)
    e[:ia] = np.linspace(0, 1, ia); e[n - ib:] = np.linspace(1, 0, ib)
    return x * e


def present_tone(seconds=44.0, seed=11):
    """Room/courtyard air + far traffic swell (no music, no speech)."""
    m = kit.Mix(seconds, seed=seed)
    air = m.lowpass(m.noise(seconds, "pink"), 700) * 0.55
    rumble = m.lowpass(m.noise(seconds, "brown"), 220)
    t = m.t(seconds)
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 13.0 + 1.1) * np.sin(2 * np.pi * t / 5.3)
    hum = 0.04 * np.sin(2 * np.pi * 50 * t)
    return fade(air + rumble * swell * 0.8 + hum, 0.3, 0.05)


def park_tone(seconds=9.0, seed=12):
    """Wind in trees (brown noise, slow gusts) + a few sparse synthesized chirps."""
    m = kit.Mix(seconds, seed=seed)
    x = m.band(m.noise(seconds, "pink"), 150, 2500)
    t = m.t(seconds)
    x *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.17 * t + 0.4) ** 2
    x += 0.6 * m.lowpass(m.noise(seconds, "brown"), 300)
    rs = np.random.RandomState(seed)
    for at in (1.3, 1.45, 3.9, 6.2, 6.33, 6.46, 7.8):
        d = rs.uniform(0.06, 0.11); tt = np.arange(int(d * R)) / R
        f0 = rs.uniform(3200, 4200)
        ch = np.sin(2 * np.pi * np.cumsum(f0 + 900 * np.sin(np.pi * tt / d)) / R) * np.sin(np.pi * tt / d) ** 2
        i = int(at * R); x[i:i + len(ch)] += ch * 0.35
    return fade(x, 0.25, 0.05)


def creak(seconds=1.6, seed=13):
    """Hinge creak: band noise 300-900 Hz with 7 Hz stick-slip modulation."""
    m = kit.Mix(seconds, seed=seed)
    x = m.band(m.noise(seconds), 300, 900) * np.sin(np.linspace(0, math.pi, int(seconds * R))) ** 2
    x *= 0.6 + 0.4 * np.sin(2 * math.pi * 7 * np.arange(len(x)) / R)
    return x


def thud(freq=62, seconds=0.6, click_gain=0.35, seed=14):
    """Heavy wooden leaf landing: kit thud body + a short wood click + a little rattle."""
    m = kit.Mix(seconds, seed=seed)
    m.thud(0.0, freq=freq, gain=1.0, seconds=0.35)
    m.click(0.0, gain=click_gain, bright=1800)
    m.click(0.11, gain=click_gain * 0.35, bright=1500)   # rattle of the latch
    return m.L


def knock(seed=15):
    return thud(freq=85, seconds=0.35, click_gain=0.5, seed=seed)


def bell_far(seconds=4.2, seed=16):
    """Remembered bell: kit inharmonic bell, 311 Hz, low-passed 650 Hz, with a far room tail."""
    m = kit.Mix(seconds, seed=seed)
    m.bell(0.0, freq=311, seconds=3.8, gain=1.0)
    b = m.lowpass(m.L, 650)
    tail = np.zeros_like(b)
    for d, g in ((0.071, 0.5), (0.113, 0.4), (0.167, 0.3), (0.229, 0.22)):
        k = int(d * R); tail[k:] += b[:-k] * g
    return b + 0.6 * tail


if __name__ == "__main__":
    save("present_tone_44s", present_tone())
    save("park_tone_9s", park_tone())
    save("creak", creak())
    save("thud_heavy", thud())
    save("knock_light", knock())
    save("bell_far_lp650", bell_far())
