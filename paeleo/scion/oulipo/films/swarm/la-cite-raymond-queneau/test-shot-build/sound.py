"""Sound for the test shot (master f456-f623 = 19.000-26.000 s), editions A and B.

Foraged recordings (Commons, see ledger) are decoded with ffmpeg only; their onsets are
detected and placed on the cue times. Where a foraged file is missing, the cue is synthesized
(HANDMADE) and the cue map says so.  Writes A.wav, B.wav, cues.json into argv[1].
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

RATE = 44100
FPS = 24
K0, K1 = 456, 624
DUR = (K1 - K0) / FPS            # 7.000 s
N = int(round(DUR * RATE))
AUD = "/home/user/bolas/paeleo/scion/oulipo/films/sources/la-cite-raymond-queneau/test-shot/audio"
rs = np.random.RandomState(16)

def decode(name):
    for ext in (".ogg", ".wav", ".oga", ".flac"):
        p = os.path.join(AUD, name + ext)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout
            x = np.frombuffer(raw, np.float32).astype(np.float64)
            return x / (np.abs(x).max() + 1e-9), os.path.basename(p)
    return None, None

def onset(x, thr=0.25):
    env = np.abs(x)
    i = int(np.argmax(env > thr))
    return max(0, i - int(0.002 * RATE))

def lowpass(x, hz):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / RATE); X[f > hz] *= 0.0
    return np.fft.irfft(X, len(x))

def band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / RATE); X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))

class Bus:
    def __init__(self):
        self.L = np.zeros(N); self.R = np.zeros(N)
    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(round(t * RATE))
        if i < 0:
            sig = sig[-i:]; i = 0
        sig = sig[: N - i] * gain
        lg, rg = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        self.L[i:i + len(sig)] += sig * lg * 1.414
        self.R[i:i + len(sig)] += sig * rg * 1.414
    def mute(self, t0, t1, fade=0.012):
        i0, i1 = int(t0 * RATE), int(t1 * RATE); f = int(fade * RATE)
        g = np.ones(N); g[i0:i1] = 0
        g[max(0, i0 - f):i0] = np.linspace(1, 0, i0 - max(0, i0 - f))
        g[i1:i1 + f] = np.linspace(0, 1, len(g[i1:i1 + f]))
        self.L *= g; self.R *= g

def T(frame):                      # master frame -> local seconds
    return (frame - K0) / FPS

def win_pan(i):                    # window bay -> stereo position (perspective: bay 0 far left)
    bay = i % 24
    return -0.85 + 1.6 * (bay / 23.0) ** 0.8

cues = {"A": [], "B": [], "sources": {}}

def place(bus, ed, name, sig, src, frame, offset_ms, gain, pan, picture_event, claim, handmade=False):
    t = T(frame) + offset_ms / 1000.0
    bus.add(sig, t, gain, pan)
    cues[ed].append(dict(sound_event=name, source=src if not handmade else "HANDMADE (synthesized)", t_sound=round(19.0 + t, 4),
                         frame=frame, offset_ms=offset_ms, picture_event_id=picture_event,
                         reading="domestic" if ed == "A" else "surveillance", claim=claim))

def synth_click(dur=0.03, bright=5000):
    n = int(dur * RATE); x = rs.normal(0, 1, n) * np.exp(-np.linspace(0, 9, n))
    return band(x, 300, bright)

# ------------------------------------------------------------- beds ---
def room_tone(seconds, lp=900):
    x = np.cumsum(rs.normal(0, 1, int(seconds * RATE))); x -= np.convolve(x, np.ones(800) / 800, "same")
    x = lowpass(x, lp); return x / (np.abs(x).max() + 1e-9)

def build_A():
    bus = Bus()
    rt = room_tone(DUR + 0.1, 700)
    bus.add(rt * 0.05, 0, 1.0, -0.2); bus.add(room_tone(DUR, 500) * 0.05, 0, 1.0, 0.3)
    latch_o, s_lo = decode("latch_open")
    latch_c, s_lc = decode("latch_close")
    door, s_do = decode("door_old")
    kettle, s_ke = decode("kettle_wws")
    def clink(f0, seconds=0.9):
        # HANDMADE: a spoon tapping a cup, inharmonic ceramic partials
        t = np.arange(int(seconds * RATE)) / RATE
        x = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 9), (2.32, 0.6, 14), (4.25, 0.35, 22), (6.8, 0.2, 30)))
        return x / np.abs(x).max()
    def pitch(x, r):
        return np.interp(np.arange(0, len(x), r), np.arange(len(x)), x)
    if latch_c is None and latch_o is not None:
        latch_c, s_lc = pitch(latch_o[onset(latch_o):], 0.8), s_lo        # a heavier, slower latch from the same lock
    if door is None:
        for fr, w, off, f0 in ((514, 29, 380, 2150), (557, 55, 300, 1870), (600, 81, 330, 2400)):
            place(bus, "A", "spoon on a cup", lowpass(clink(f0), 6000), "", fr, off, 0.10, win_pan(w), f"window_on:{w}",
                  "tea things set out in another flat", True)
    # step 15 (window 3) : a far latch closing, late and soft
    if latch_c is not None:
        x = latch_c[onset(latch_c):][: int(0.6 * RATE)]
        place(bus, "A", "far window latch", lowpass(x, 2500), s_lc, 470, 260, 0.20, win_pan(3), "window_on:3", "someone else coming home")
    else:
        place(bus, "A", "far latch", synth_click(0.05, 2500), "", 470, 260, 0.2, win_pan(3), "window_on:3", "someone else coming home", True)
    # step 16 (window 16): latch +150 ms, near
    if latch_o is not None:
        x = latch_o[onset(latch_o):][: int(0.9 * RATE)]
        place(bus, "A", "door latch (flat door opens)", x, s_lo, 492, 150, 0.55, win_pan(16), "window_on:16",
              "the walker has reached the flat; the door is opened for them")
    else:
        place(bus, "A", "door latch", synth_click(0.08, 3000), "", 492, 150, 0.5, win_pan(16), "window_on:16", "door opened", True)
    # kettle begins to sing as the silhouette rises (f502-518) and sustains
    if kettle is not None:
        # find the whistling part: the loudest 3 s window of the recording
        e = np.convolve(kettle ** 2, np.ones(RATE // 10), "same")
        i = int(np.argmax(e)); seg = kettle[max(0, i - int(2.6 * RATE)): i + int(2.6 * RATE)]
        seg = seg[: int(4.6 * RATE)]
        ramp = np.clip(np.linspace(-0.25, 1.0, len(seg)) * 1.6, 0, 1) ** 1.5      # begins to sing
        ramp[-int(1.2 * RATE):] *= np.linspace(1, 0.15, int(1.2 * RATE))           # lifted off the heat
        place(bus, "A", "kettle begins to sing", seg * ramp, s_ke, 502, 0, 0.30, win_pan(16) + 0.1, "silhouette_rise:16",
              "someone inside has been waiting with the tea")
    # the soft greeting at the head turn: a real recorded "toi" (Lingua Libre, CC BY 4.0), heard through the room
    toi, s_toi = decode("toi_loquax")
    if toi is not None:
        e = np.abs(toi); i0 = onset(toi, 0.08); seg = toi[i0:]
        seg = seg[: int(0.75 * RATE)] * np.linspace(1, 0.6, len(seg[: int(0.75 * RATE)]))
        place(bus, "A", "soft spoken 'toi ?' (real speech)", lowpass(seg, 3200), s_toi, 538, 240, 0.30, win_pan(16) + 0.05,
              "head_turn:16", "the one who waited greets the one who came home")
    # step 17 (window 29): a distant door, irregularly late
    if door is not None:
        x = door[onset(door, 0.2):][: int(1.2 * RATE)]
        place(bus, "A", "distant door closing", lowpass(x, 1800), s_do, 514, 380, 0.16, win_pan(29), "window_on:29", "neighbour home")
    # step 18 (window 42): a soft latch, early-late
    if latch_c is not None:
        x = latch_c[onset(latch_c):][: int(0.6 * RATE)]
        place(bus, "A", "soft latch", lowpass(x, 3500) * 0.8, s_lc, 535, 120, 0.18, win_pan(42), "window_on:42", "neighbour home")
    # step 19 (window 55): a cupboard/door far away (+300 ms)
    if door is not None:
        x = door[onset(door, 0.2):][: int(1.0 * RATE)]
        place(bus, "A", "far door", lowpass(x, 1200), s_do, 557, 300, 0.12, win_pan(55), "window_on:55", "neighbour home")
    # step 20 (window 68): latch (+210 ms) pitched down a little (slower playback = a heavier door)
    if latch_o is not None:
        x = latch_o[onset(latch_o):][: int(0.8 * RATE)]
        x = np.interp(np.arange(0, len(x), 0.88), np.arange(len(x)), x)
        place(bus, "A", "heavier latch", lowpass(x, 2500), s_lo, 578, 210, 0.16, win_pan(68), "window_on:68", "neighbour home")
    # step 21 (window 81): distant door (+330 ms)
    if door is not None:
        x = door[onset(door, 0.2):][: int(0.9 * RATE)]
        place(bus, "A", "distant door", lowpass(x, 1500), s_do, 600, 330, 0.12, win_pan(81), "window_on:81", "neighbour home")
    return bus

def build_B():
    bus = Bus()
    t = np.arange(N) / RATE
    hum = sum(a * np.sin(2 * np.pi * 50 * h * t + h) for h, a in ((1, 1.0), (2, 0.35), (3, 0.5), (5, 0.18)))
    drone = 0.5 * np.sin(2 * np.pi * 73.4 * t) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.13 * t))
    bed = (hum * 0.045 + drone * 0.05) + room_tone(DUR, 400)[:N] * 0.02
    bus.add(bed, 0, 1.0, 0.0)
    cues["B"].append(dict(sound_event="50 Hz mains hum + low drone (bed)", source="HANDMADE (synthesized)", t_sound=19.0, frame=456,
                          offset_ms=0, picture_event_id="shot", reading="surveillance", claim="an apparatus is on"))
    relay, s_re = decode("relay_telerupteur")
    if relay is None:
        relay, s_re = decode("click_heating")        # PD: a heating relay switching on
    if relay is not None:
        e = np.abs(relay); i = int(np.argmax(e)); seg = relay[max(0, i - int(0.15 * RATE)):]
        click = seg[onset(seg, 0.3):][: int(0.25 * RATE)]
        click *= np.linspace(1, 0, len(click)) ** 0.5
        src_click = s_re
    else:
        click = synth_click(0.035, 6000); src_click = ""
    hm = relay is None
    for fr, w in ((470, 3), (492, 16), (514, 29), (535, 42), (578, 68), (600, 81)):
        place(bus, "B", "relay click (same sample every window)", click, src_click, fr, 0, 0.5 if w == 16 else 0.38,
              win_pan(w) * 0.6, f"window_on:{w}", "window logged" if w != 16 else "window 16 logged, exactly on its frame", hm)
    # carriage return at f518 (end of the rise)
    ding, s_di = decode("typewriter_ding")
    tw, s_tw = decode("typewriter_wws")
    if ding is not None:
        x = ding[onset(ding, 0.2):][: int(1.0 * RATE)]
        place(bus, "B", "typewriter carriage return (bell + return)", x, s_di, 518, 0, 0.35, -0.4, "silhouette_rise_end:16",
              "the entry for window 16 is typed")
    elif tw is not None:
        x = tw[onset(tw, 0.3):][: int(0.8 * RATE)]
        place(bus, "B", "typewriter", x, s_tw, 518, 0, 0.3, -0.4, "silhouette_rise_end:16", "the entry is typed")
    else:
        place(bus, "B", "carriage bell", np.sin(2 * np.pi * 2350 * np.arange(int(0.6 * RATE)) / RATE) * np.exp(-np.arange(int(0.6 * RATE)) / RATE * 7),
              "", 518, 0, 0.25, -0.4, "silhouette_rise_end:16", "the entry is typed", True)
    # held silence through the head turn: everything off f538-f566 (window 55's click at f557 is withheld)
    bus.mute(T(538), T(566))
    cues["B"].append(dict(sound_event="held digital silence (all stems)", source="", t_sound=round(19.0 + T(538), 4), frame=538,
                          offset_ms=0, picture_event_id="head_turn:16", reading="surveillance",
                          claim="the watcher is watched: the apparatus holds its breath; window 55 (f557) is not clicked"))
    shut, s_sh = decode("shutter_holga")
    if shut is None:
        shut, s_sh = decode("shutter_canon")
    if shut is not None:
        x = shut[onset(shut, 0.3):][: int(0.5 * RATE)]
        place(bus, "B", "single camera shutter", x, s_sh, 566, 0, 0.55, win_pan(16) * 0.5, "curtain_settle:16",
              "window 16 photographed")
    else:
        place(bus, "B", "camera shutter", np.concatenate([synth_click(0.02), np.zeros(int(0.06 * RATE)), synth_click(0.03)]), "", 566, 0, 0.5,
              0.2, "curtain_settle:16", "photographed", True)
    return bus

def write_wav(path, bus):
    import wave
    st = np.stack([bus.L, bus.R], 1)
    st /= max(1.0, np.abs(st).max() / 0.7)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(RATE)
        wf.writeframes((st * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    write_wav(os.path.join(out, "A_raw.wav"), build_A())
    write_wav(os.path.join(out, "B_raw.wav"), build_B())
    json.dump(cues, open(os.path.join(out, "cues.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: len(v) for k, v in cues.items() if k != "sources"}))
