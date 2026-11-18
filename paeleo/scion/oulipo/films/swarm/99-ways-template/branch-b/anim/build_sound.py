"""Foley stems for 99-ways-template (rig-animator, U3). Writes anim/sound/*.wav (44.1 kHz mono 16-bit) + sound.json.
Sources are decoded with ffmpeg to films/sources/99-ways-template/rig-animator/wav/ (data only). FORAGED first:
Moving Image Archive clip sound (room tone), Commons PD / CC BY-SA / CC BY recordings; kit.Mix synthesis only for
what was not found (counter bell, paper handling), declared in sound.json.
Run: python3 -I build_sound.py"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "films"))
import kit  # noqa: E402

SRC = ROOT / "films" / "sources" / "99-ways-template" / "rig-animator"
WAV = SRC / "wav"
OUT = HERE / "sound"
OUT.mkdir(exist_ok=True)
R = 44100
mx = kit.Mix(1, rate=R, seed=7)          # used for its filters/envelopes and the declared synthesis


def rd(name):
    w = wave.open(str(WAV / name))
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    assert w.getframerate() == R
    return x


def seg(x, a, b, fi=0.004, fo=0.03):
    y = x[int(a * R):int(b * R)].copy()
    ni, no = int(fi * R), int(fo * R)
    y[:ni] *= np.linspace(0, 1, ni)
    y[-no:] *= np.linspace(1, 0, no)
    return y


def norm(y, peak_db):
    p = np.abs(y).max() + 1e-12
    return y / p * 10 ** (peak_db / 20)


def rms_db(y):
    return float(20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-12))


def gate_tail(y, t=0.12):
    e = np.ones(len(y))
    n0 = int(t * R)
    if n0 < len(y):
        e[n0:] = np.exp(-np.arange(len(y) - n0) / (0.03 * R))
    return y * e


def write(name, y):
    y = np.clip(y, -1, 1)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(R)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    return {"file": f"anim/sound/{name}", "seconds": round(len(y) / R, 3), "peak_dbfs": round(float(20 * np.log10(np.abs(y).max() + 1e-12)), 1)}


def onsets(x, lo, hi, n, min_gap=0.25):
    """Strongest transient peaks (100 Hz envelope rise) between lo and hi seconds."""
    hop = R // 200
    e = np.array([np.sqrt((x[i:i + hop] ** 2).mean() + 1e-12) for i in range(int(lo * R), int(hi * R) - hop, hop)])
    db = 20 * np.log10(e)
    rise = db - np.concatenate([np.full(4, db[0]), db[:-4]])
    order = np.argsort(-rise)
    picks = []
    for i in order:
        t = lo + i * hop / R
        if all(abs(t - p) > min_gap for p in picks):
            picks.append(t)
        if len(picks) == n:
            break
    return sorted(picks)


MIA = {"title": "Panama by Air (Reel 4) (1914)", "author": "via movingimagearchive.com",
       "license": "Public domain (US, pre-1929)", "license_url": "",
       "source_url": "https://www.movingimagearchive.com/sources/panama-by-air-reel-4-1a07ad16?clip=d3c1f500-55a9-50c7-9ca4-11791246582d",
       "file_url": "", "local_path": "films/sources/99-ways-template/rig-animator/mia/d3c1f500.wav (decoded from the cineosis-lab clip cache)",
       "clip_in_source_film_s": [517.651, 530.597]}


def commons(title, author, lic, lic_url, page, url, local):
    return {"title": title, "author": author, "license": lic, "license_url": lic_url, "source_url": page, "file_url": url,
            "local_path": f"films/sources/99-ways-template/rig-animator/commons/raw/{local}"}


META = json.load(open(SRC / "commons" / "meta1.json"))


def cm(fn):
    m = META["File:" + fn]
    import re
    au = re.sub("<[^>]+>", "", m.get("artist") or "").strip()
    return commons("File:" + fn, au, m["license"], m.get("license_url") or "", m["descurl"], m["url"].split("?")[0], fn.replace(" ", "_"))


stems, ledger = {}, []

# --- room tone: the 1914 film's own optical/transfer noise floor (silent film, real recorded noise of the print)
x = rd("mia_panama_by_air_1914.wav")
base = x[int(0.5 * R):int(12.5 * R)]
L = len(base)
xf = int(1.0 * R)
loop = base.copy()
loop[:xf] = base[:xf] * np.linspace(0, 1, xf) + base[-xf:] * np.linspace(1, 0, xf)
loop = loop[:L - xf]
loop = mx.band(loop, 60, 7000)
loop = loop / (np.sqrt((loop ** 2).mean()) + 1e-12) * 10 ** (-42 / 20)
stems["room_tone"] = write("room_tone.wav", loop)
ledger.append(dict(MIA, id="room_tone", what_it_shows="the noise floor of a 1914 silent film print's sound transfer: steady hiss with faint crackle, no voice or music (spectrum and level checked: -48 dBFS median, no onsets)",
                   used_as="room tone bed under the whole film (S0-S12); 11 s seamless loop (1 s crossfade), band 60-7000 Hz, RMS -42 dBFS",
                   verified_date_or_place="title/year on movingimagearchive.com page; pre-1929 US film", in_out_s=[0.5, 12.5]))

# --- clock tick (PD): single ticks of a real clock
x = rd("Clock_ticking.wav")
t1, t2 = 3.07, 4.08
tick = gate_tail(seg(x, t1 - 0.02, t1 + 0.16), 0.09)
tock = gate_tail(seg(x, t2 - 0.02, t2 + 0.16), 0.09)
stems["clock_tick"] = write("clock_tick.wav", norm(tick, -14))
stems["clock_tick_close"] = write("clock_tick_close.wav", norm(tock, -8))
stems["pencil_tap"] = write("pencil_tap.wav", norm(mx.band(tick, 1500, 9000), -20))
c = cm("Clock ticking.ogg")
ledger.append(dict(c, id="clock_tick", what_it_shows="a mechanical clock ticking once a second, close-miked, quiet room",
                   used_as="clock_tick (tick at 3.07 s), clock_tick_close (tock at 4.08 s, louder, S5), pencil_tap (the same tick band-passed 1.5-9 kHz, quiet: the pencil tapped on the temple, S1)",
                   verified_date_or_place="Commons extmetadata read 2026-11-17", in_out_s=[[3.05, 3.23], [4.06, 4.24]]))

# --- door creak + slam-free swing (PD)
x = rd("Squeaky_door.wav")
creak = seg(x, 4.55, 5.75, 0.02, 0.15)
stems["door_creak"] = write("door_creak.wav", norm(creak, -10))
ledger.append(dict(cm("Squeaky door.ogg"), id="door_creak", what_it_shows="a squeaking hinge as a door is swung, then shut (the shut at 7.0 s is not used)",
                   used_as="door_creak (4.55-5.75 s): the cupboard door's swing on its jamb, S7 f42-f54", verified_date_or_place="Commons extmetadata read 2026-11-17",
                   in_out_s=[4.55, 5.75]))

# --- latch (PD)
x = rd("Door_handle_creaking.wav")
latch = gate_tail(seg(x, 0.30, 0.62, 0.002, 0.05), 0.15)
stems["door_latch"] = write("door_latch.wav", norm(latch, -12))
ledger.append(dict(cm("Door handle creaking.ogg"), id="door_latch", what_it_shows="a door handle turned, its latch clicking and creaking",
                   used_as="door_latch (0.30-0.62 s): the cupboard latch gives, S7 f40", verified_date_or_place="Commons extmetadata read 2026-11-17",
                   in_out_s=[0.30, 0.62]))

# --- chair scrape (PD)
x = rd("Creaky_wooden_swivel_chair.wav")
chair = seg(x, 3.66, 4.25, 0.01, 0.12)
chair = np.concatenate([chair, seg(x, 4.40, 4.75, 0.01, 0.12) * 0.7])
stems["chair_scrape"] = write("chair_scrape.wav", norm(chair, -10))
ledger.append(dict(cm("Creaky wooden swivel chair.ogg"), id="chair_scrape", what_it_shows="a wooden swivel chair creaking and shifting as someone moves in it",
                   used_as="chair_scrape (3.66-4.25 + 4.40-4.75 s): the clerk rises from his chair, S2 f22", verified_date_or_place="Commons extmetadata read 2026-11-17",
                   in_out_s=[[3.66, 4.25], [4.40, 4.75]]))

# --- footsteps (PD): individual heel strikes cut from a recording of people walking (hard floor, reverberant hall)
x = rd("Church_people_walking_steps_with_reverb.wav")
picks = onsets(x, 1.0, 29.0, 12, 0.6)
steps = []
for i, t in enumerate(picks):
    s = gate_tail(seg(x, t - 0.01, t + 0.30, 0.002, 0.08), 0.10)
    s = mx.band(s, 90, 6000)                # cut the hall's rumble and air; keep the heel and the board knock
    steps.append(norm(s, -12))
for i, s in enumerate(steps[:6]):
    stems[f"footstep_{i + 1}"] = write(f"footstep_{i + 1}.wav", s)
# receding steps (S6, out of frame: she leaves along the platform): 6 strikes, ~0.55 s apart, fading and darkening
rec = np.zeros(int(4.0 * R))
for i in range(6):
    s = mx.band(steps[(i + 3) % len(steps)], 90, 3500 - i * 450) * 10 ** (-(4 + 4 * i) / 20)
    a = int((0.1 + 0.55 * i) * R)
    rec[a:a + len(s)] += s[:len(rec) - a]
stems["steps_receding"] = write("steps_receding.wav", rec)
ledger.append(dict(cm("Church people walking steps with reverb.ogg"), id="footsteps", what_it_shows="people walking on a hard floor in a reverberant church; individual heel strikes are audible over the hall",
                   used_as="footstep_1..6 (single strikes gated to 0.12 s + 30 ms decay, band 90-6000 Hz: the clerk's steps on the office boards, S2/S3/S4/S7) and steps_receding (6 strikes fading and darkening: the visitor leaving, S6)",
                   verified_date_or_place="Commons extmetadata read 2026-11-17", in_out_s=[round(p, 2) for p in picks]))

# --- paper tap (PD): a dull thud, thinned to a light paper landing
x = rd("Dull_thud.wav")
tap = gate_tail(mx.band(x[:int(0.3 * R)], 700, 9000), 0.05)
stems["paper_tap"] = write("paper_tap.wav", norm(tap, -16))
ledger.append(dict(cm("Dull thud.ogg"), id="paper_tap", what_it_shows="a short dull thud of something soft landing",
                   used_as="paper_tap: band-passed 0.7-9 kHz and shortened so it reads as a card landing; every balloon land frame (S4 f40, S5 f56, S6 f16, S8 f84)",
                   verified_date_or_place="Commons extmetadata read 2026-11-17", in_out_s=[0.0, 0.3]))

# --- distant platform (CC BY 3.0): an old train heard at a distance
x = rd("Train_sounds_from_Iowa_-_Glaneur_de_sons.wav")
plat = seg(x, 40.0, 50.0, 0.8, 1.5)
plat = mx.band(plat, 60, 1400)
plat = plat / (np.sqrt((plat ** 2).mean()) + 1e-12) * 10 ** (-34 / 20)
stems["platform_distant"] = write("platform_distant.wav", plat)
ledger.append(dict(cm("Train sounds from Iowa - Glaneur de sons.ogg"), id="platform_distant", what_it_shows="an old tourist train in Iowa: engine and wheels at a distance, outdoor air",
                   used_as="platform_distant (40-50 s, low-passed 1.4 kHz, RMS -34 dBFS): the platform beyond the ticket window, S6 and S11",
                   verified_date_or_place="Commons extmetadata read 2026-11-17", in_out_s=[40.0, 50.0],
                   attribution="Glaneur de sons, CC BY 3.0 (credit required)"))

# --- SYNTHESIZED (declared): counter bell, paper handling
m = kit.Mix(2.6, rate=R, seed=11)
m.bell(0.0, freq=2350, seconds=2.4, gain=0.6)
m.click(0.0, gain=0.25, bright=7000, seconds=0.01)
bell = (m.L + m.R) / 2.828
stems["counter_bell"] = write("counter_bell.wav", norm(bell, -9))
m = kit.Mix(1.6, rate=R, seed=12)
for i, (a, d) in enumerate([(0.05, 0.22), (0.42, 0.16), (0.80, 0.30)]):
    nz = m.band(m.noise(d, "pink"), 900, 7500) * m.env(int(d * R), 0.02, d * 0.6, 0.2, d * 0.3)
    m.add(nz, a, 0.35)
ph = (m.L + m.R) / 2.828
stems["paper_handling"] = write("paper_handling.wav", norm(ph, -22))
synth = [{"id": "counter_bell", "made_with": "kit.Mix.bell (inharmonic struck-bell partials) at 2350 Hz + kit.Mix.click strike, 2.4 s decay",
          "why": "no openly licensed desk/counter bell recording was found: Commons searches 'service bell', 'desk bell', 'reception bell', 'hotel bell', 'bell ding' (2026-11-17) gave only church bells, a bicycle bell and speech; the Moving Image Archive clip cache has no isolated bell",
          "used_as": "the counter bell rung once by the visitor, S4 f14 (and S10/S11)"},
         {"id": "paper_handling", "made_with": "kit.Mix pink noise band-passed 0.9-7.5 kHz, three enveloped bursts",
          "why": "no openly licensed paper-handling recording found in time (Commons 'sound effect paper' returned none; 'Gravity Sound paper' returned only PDFs)",
          "used_as": "S0: the sheet laid down as the borders rule in (quiet)"}]

absences = [
    {"wanted": "Moving Image Archive clip foley (footsteps, door, bell, clock)", "searched": "index.json: all 188 clips with audio; regex station|office|clock|door|train|railroad|footstep|walk|room|desk|bell|ticket|platform; auditioned by spectrum: Wreckless 1935, This Is My Railroad 1940, Dating: Do's and Don'ts 1949, Going Steady? 1951, Valley Town 1940 (2 clips), Space Ship Takeoff 1937, Panama by Air 1914",
     "result": "all but Panama by Air carry narration, dialogue or score over the sound; only Panama by Air (silent film, transfer noise) is usable, as room tone"},
    {"wanted": "footsteps on wooden boards", "result": "no PD/CC footsteps-on-wood file reachable (Commons 'footsteps wooden floor', 'walking on wooden floor', 'Gravity Sound footsteps' empty or rate-limited); heel strikes cut from the PD church-walking recording instead"},
    {"wanted": "chair drag on boards", "result": "Drag chair (Gravity Sound, CC BY 4.0) download refused (HTTP 429 x4); PD Creaky wooden swivel chair used"},
    {"wanted": "cupboard door close/latch", "result": "Cupboarddoorclose.ogg (CC BY-SA 3.0) download refused (429); PD Door handle creaking used for the latch"},
    {"wanted": "spiral-stair steps (Pasos en escalera de caracol, CC BY-SA 4.0)", "result": "download refused (429); not needed"},
    {"wanted": "room tone of an office", "result": "Ambient classroom mono (PD) downloaded and rejected on listening analysis: continuous chatter onsets every ~0.25 s at -14 dBFS"}]

json.dump({"rate": R, "format": "mono 16-bit WAV", "stems": stems, "foraged": ledger, "synthesized_declared": synth,
           "absences": absences, "voice": "none: voice is balloons (no text-to-speech; no speech recording used)",
           "cue_sheet": "per-shot cue frames are in anim/timing.json shots.<S>.sounds (cue names = stem names; 'footstep' = footstep_1..6 in rotation)",
           "mix_guidance": {"room_tone": "loop under everything at 0 dB (already -42 dBFS RMS)", "footstep": "-6 dB in S2/S3, -9 dB in S4/S7",
                            "counter_bell": "0 dB, pan -0.3 (window side)", "paper_tap": "0 dB on every balloon land frame",
                            "door_creak": "start at S7 f42, ends ~f71 (1.2 s)", "platform_distant": "S6 from f24 at -6 dB, pan -0.5; S11 at 0 dB",
                            "S8": "silence after the tap except room tone; one clock_tick at f140"}},
          open(OUT / "sound.json", "w"), indent=1)
print(json.dumps(stems, indent=0)[:1500])
