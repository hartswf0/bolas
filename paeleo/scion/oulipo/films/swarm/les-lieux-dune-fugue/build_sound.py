#!/usr/bin/env python3
"""U3 build_sound.py -- decode foraged sound (ffmpeg only), choose segments, write sound_cues.json,
and render an audio-only preview mix with kit.Mix to check the cue sheet (ducking, bell window,
declared digital silence). Does not touch picture.

Foraged files (untrusted data) live in films/sources/les-lieux-dune-fugue/sound/dl/ and are only ever
decoded by ffmpeg to 44.1 kHz WAV stems in films/sources/les-lieux-dune-fugue/sound/.
Where a foraged file is absent (Commons upload host returned HTTP 429 / retry-after 600), the cue
falls back to the handmade kit.Mix stem from synth_stems.py and says so.
"""
import json, math, os, subprocess, sys, wave
import numpy as np

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
sys.path.insert(0, ROOT + "/films")
import kit  # noqa: E402

SRC = ROOT + "/films/sources/les-lieux-dune-fugue"
DL, SND = SRC + "/sound/dl", SRC + "/sound"
NSW = SRC + "/narration-sound-writer"
STEMS = NSW + "/stems"
HERE = ROOT + "/films/swarm/les-lieux-dune-fugue"
R = 44100
DUR = 57.0
SILENCE = (44.0, 57.0)
BELL_WIN = (32.0, 41.0)
CUTS = [0.0, 8.0, 19.0, 28.0, 44.0, 52.0, 57.0]
# contact times from paper_stage.py (S1_CONTACT, S4_CONTACT_L, S4_CONTACT_R) and leaf motion
T1_CONTACT, T4_OPEN, T4_LOWER, T4_CONTACT_L, T4_CONTACT_R = 7.0, 31.0, 41.0, 43.1, 43.5

FORAGED = {  # Commons extmetadata read via the API (LicenseShortName / LicenseUrl / Artist), 2026-11-16
    "BELL-MURBACH": dict(file="Church_Bells_of_Murbach.flac", title="Church Bells of Murbach", author="Amada44",
        license="CC BY-SA 3.0", license_url="https://creativecommons.org/licenses/by-sa/3.0",
        source_url="https://commons.wikimedia.org/wiki/File:Church_Bells_of_Murbach.flac",
        file_url="https://upload.wikimedia.org/wikipedia/commons/9/94/Church_Bells_of_Murbach.flac",
        what_it_shows="'The Bells of the Abby of Murbach, France.' Field recording of the abbey bells.",
        verified_date_or_place="2018-04-21 (Commons DateTimeOriginal), Murbach, Haut-Rhin, France (description)"),
    "DOOR-CLOSE": dict(file="Close_door_Gravity_Sound.wav", title="Close door (Gravity Sound)", author="Gravity Sound",
        license="CC BY 4.0", license_url="https://creativecommons.org/licenses/by/4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Close_door_(Gravity_Sound).wav",
        file_url="https://upload.wikimedia.org/wikipedia/commons/f/fa/Close_door_%28Gravity_Sound%29.wav",
        what_it_shows="'close door' by Gravity Sound: a single door closing (foley library).", verified_date_or_place="unverified"),
    "DOOR-SQUEAK": dict(file="Close_squeaky_door_Gravity_Sound.wav", title="Close squeaky door (Gravity Sound)", author="Gravity Sound",
        license="CC BY 4.0", license_url="https://creativecommons.org/licenses/by/4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Close_squeaky_door_(Gravity_Sound).wav",
        file_url="https://upload.wikimedia.org/wikipedia/commons/a/aa/Close_squeaky_door_%28Gravity_Sound%29.wav",
        what_it_shows="'close squeaky door' by Gravity Sound: hinge squeak then a close.", verified_date_or_place="unverified"),
    "GARDEN": dict(file="Bourne_Garden_2020-08-28_0943.mp3", title="Bourne Garden 2020-08-28 0943", author="Robert EA Harvey",
        license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Bourne_Garden_2020-08-28_0943.mp3",
        file_url="https://upload.wikimedia.org/wikipedia/commons/0/02/Bourne_Garden_2020-08-28_0943.mp3",
        what_it_shows="Garden ambience recorded for Geograph images at Bourne Wood: 'mostly birdsong, and some distant traffic'. Only the first 3 MB (HTTP Range) fetched.",
        verified_date_or_place="2020-08-28 (Commons DateTimeOriginal), Bourne, Lincolnshire, England (Geograph description)"),
    "STREET": dict(file="Urban_Street_on_a_Rainy_Afternoon.flac", title="Urban Street on a Rainy Afternoon", author="Extemporalist",
        license="CC0", license_url="http://creativecommons.org/publicdomain/zero/1.0/deed.en",
        source_url="https://commons.wikimedia.org/wiki/File:Urban_Street_on_a_Rainy_Afternoon.flac",
        file_url="https://upload.wikimedia.org/wikipedia/commons/8/8c/Urban_Street_on_a_Rainy_Afternoon.flac",
        what_it_shows="'Moderate traffic on a 2 lane urban street in Kelowna on a rainy afternoon... raindrops on hard surfaces... crows.' Only the first 5 MB (HTTP Range) fetched.",
        verified_date_or_place="2015-02-09 (Commons DateTimeOriginal), Kelowna, BC, Canada (description)"),
}


def have(k):
    p = DL + "/" + FORAGED[k]["file"]
    return os.path.exists(p) and os.path.getsize(p) > 1000


def decode(k, out_name):
    """ffmpeg-only decode of an untrusted download to a 44.1 kHz stereo 16-bit WAV stem."""
    src, out = DL + "/" + FORAGED[k]["file"], SND + "/" + out_name
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-map_metadata", "-1", "-ac", "2", "-ar", str(R),
                    "-c:a", "pcm_s16le", out], check=True)
    return out


def read_wav(p):
    with wave.open(p) as w:
        ch, n = w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), np.int16).astype(np.float64) / 32768
    x = x.reshape(-1, ch).mean(1)
    return x


def write_wav(p, x):
    x = np.asarray(x, np.float64)
    pk = np.abs(x).max()
    if pk > 0:
        x = x / pk * 0.5
    with wave.open(p, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(R)
        w.writeframes((np.stack([x, x], 1) * 32767).astype(np.int16).tobytes())


def env_db(x, win=2205):
    e = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, "same") + 1e-12)
    return 20 * np.log10(e)


def lp(x, hz):
    m = kit.Mix(1.0)
    return m.lowpass(x, hz)


def fades(x, a=0.02, b=0.02):
    n = len(x); e = np.ones(n); ia, ib = max(1, int(a * R)), max(1, int(b * R))
    e[:ia] = np.linspace(0, 1, ia); e[n - ib:] = np.linspace(1, 0, ib)
    return x * e


def prepare():
    """Returns {stem_id: dict(path, source, ...)} for every stem the cue sheet places."""
    os.makedirs(STEMS, exist_ok=True)
    st = {}
    synth = lambda name: STEMS + "/" + name + ".wav"
    # present P01 tone (shot 1 and 4): foraged street, low-passed as if heard through a stone courtyard
    if have("STREET"):
        x = read_wav(decode("STREET", "street_rainy_kelowna_full.wav"))
        seg = lp(x[int(4 * R):int(4 * R) + int(16.5 * R)], 900)
        write_wav(STEMS + "/present_tone_street_lp900.wav", fades(seg, 0.3, 0.3))
        st["present"] = dict(path=STEMS + "/present_tone_street_lp900.wav", src="STREET", loop=True,
                             proc="source 4.0-20.5 s, lowpass 900 Hz (through-the-courtyard), looped with 0.3 s crossfade")
        wide = x[int(4 * R):int(4 * R) + int(11.5 * R)]
        write_wav(STEMS + "/junction_tone_street_lp2500.wav", fades(lp(wide, 2500), 0.05, 0.05))
        st["junction"] = dict(path=STEMS + "/junction_tone_street_lp2500.wav", src="STREET", proc="source 4.0-15.5 s, lowpass 2.5 kHz (wider, open junction)")
    else:
        st["present"] = dict(path=synth("present_tone_44s"), src=None, loop=False, proc="kit.Mix: pink air lowpass 700 Hz + brown rumble 220 Hz with slow swell + 50 Hz hum at -28 dB")
        st["junction"] = dict(path=synth("present_tone_44s"), src=None, proc="same synthesized tone, wider (cue gain/pan spread)")
    # park tone (shot 3)
    if have("GARDEN"):
        x = read_wav(decode("GARDEN", "garden_bourne_head.wav"))
        seg = x[int(5 * R):int(5 * R) + int(9.0 * R)]
        write_wav(STEMS + "/park_tone_garden.wav", fades(seg, 0.02, 0.02))
        st["park"] = dict(path=STEMS + "/park_tone_garden.wav", src="GARDEN", proc="source 5.0-14.0 s, unprocessed")
    else:
        st["park"] = dict(path=synth("park_tone_9s"), src=None, proc="kit.Mix: band pink wind 150-2500 Hz with gusts, brown low wind, 7 synthesized chirps")
    # creak (shot 4 opening + closing)
    if have("DOOR-SQUEAK"):
        x = read_wav(decode("DOOR-SQUEAK", "door_squeak_gravity.wav"))
        e = env_db(x); on = int(np.argmax(e > e.max() - 30))
        seg = lp(x[on:on + int(1.6 * R)], 2500)
        write_wav(STEMS + "/creak_foraged.wav", fades(seg, 0.01, 0.3))
        st["creak"] = dict(path=STEMS + "/creak_foraged.wav", src="DOOR-SQUEAK", proc="first 1.6 s from onset, lowpass 2.5 kHz; editor may play at 0.62x speed (pitched down, heavier leaf)")
    else:
        st["creak"] = dict(path=synth("creak"), src=None, proc="kit.Mix: band noise 300-900 Hz, 7 Hz stick-slip AM, sin^2 envelope")
    # thud (shot 1 at 7.0, shot 4 at 43.5) and knock (43.1)
    if have("DOOR-CLOSE"):
        x = read_wav(decode("DOOR-CLOSE", "door_close_gravity.wav"))
        i = int(np.argmax(np.abs(x) > 0.5 * np.abs(x).max()))
        seg = lp(x[max(i - 200, 0):max(i - 200, 0) + int(0.6 * R)], 3000)
        write_wav(STEMS + "/thud_foraged.wav", fades(seg, 0.002, 0.25))
        st["thud"] = dict(path=STEMS + "/thud_foraged.wav", src="DOOR-CLOSE", pre_roll_s=200 / R, layered_with=synth("thud_heavy"),
                          proc="from 200 samples before the impact peak, 0.6 s, lowpass 3 kHz; layered with the kit thud body (62 Hz) for the weight of a carriage-door leaf")
    else:
        st["thud"] = dict(path=synth("thud_heavy"), src=None, pre_roll_s=0.0, proc="kit.Mix thud 62 Hz 0.35 s + wood click 1.8 kHz + latch rattle at +0.11 s")
    st["knock"] = dict(path=synth("knock_light"), src=None, pre_roll_s=0.0, proc="kit.Mix thud 85 Hz + click (the left leaf meeting the frame)")
    # remembered bell (memory only)
    if have("BELL-MURBACH"):
        x = read_wav(decode("BELL-MURBACH", "bells_murbach.wav"))
        sp = len(x) / (9.0 * R)          # 6.66 s peal played slower (pitched down ~0.74x) to fill the 9 s memory
        x = np.interp(np.arange(0, len(x) - 1, sp), np.arange(len(x)), x)
        seg = x[: int(9.0 * R)] if len(x) >= int(9.0 * R) else np.pad(x, (0, int(9.0 * R) - len(x)))
        seg = lp(seg, 650)
        write_wav(STEMS + "/bell_remembered_murbach_lp650.wav", fades(seg, 1.2, 1.0))
        st["bell"] = dict(path=STEMS + "/bell_remembered_murbach_lp650.wav", src="BELL-MURBACH", proc="whole 6.66 s peal resampled to 9.0 s (playback ~0.74x: pitched down, slower strokes, remembered), lowpass 650 Hz (far, muffled), fade in 1.2 s / out 1.0 s")
    else:
        st["bell"] = dict(path=synth("bell_far_lp650"), src=None, proc="kit.Mix bell 311 Hz inharmonic partials, lowpass 650 Hz, 4-tap far room tail; struck at 32.4 and 36.6")
    return st


def src_text(s):
    if s.get("src"):
        f = FORAGED[s["src"]]
        return f"FORAGED: {f['title']} ({f['author']}, Wikimedia Commons, {f['license']})"
    return "synthesized (kit)"


def cue_sheet(st):
    cues = []

    def add(cid, t0, t1, stem, gain, pan, note, **kw):
        s = st[stem]
        d = dict(id=cid, at=round(t0, 4), until=round(t1, 4), stem=stem, file=os.path.relpath(s["path"], ROOT),
                 gain=gain, pan=pan, source=src_text(s), source_id=s.get("src"), license=FORAGED[s["src"]]["license"] if s.get("src") else "handmade (kit.Mix synthesis, this work)",
                 processing=s["proc"], note=note)
        d.update(kw)
        cues.append(d)

    add("C01", 0.0, 8.0, "present", 0.22, 0.0, "P01-A present courtyard/street tone, low; hard cut at 8.0", fade_s=[0.3, 0.01])
    add("C02", 5.5, 6.6, "creak", 0.10, -0.35, "left leaf lifted ~18 deg (shot 1); quiet", speed=0.62)
    add("C03", T1_CONTACT - st["thud"]["pre_roll_s"], T1_CONTACT + 0.6, "thud", 0.50, -0.25, "shot 1 contact at 7.0: door thud with short wooden rattle (impact sample aligned to the contact frame)",
        sync="leaf contact frame 7.0 (paper_stage S1_CONTACT)")
    add("C04", 8.0, 19.0, "junction", 0.26, 0.0, "P02 street tone, slightly wider (stereo spread by two placements)", spread=[-0.4, 0.4], fade_s=[0.01, 0.01])
    add("C05", 19.0, 28.0, "park", 0.30, 0.1, "P03 present park tone: wind and a few birds", fade_s=[0.01, 0.01])
    add("C06", 28.0, 44.0, "present", 0.22, 0.0, "P01-B present tone; ducked -6 dB from 32.0 to 41.0 under the bell (0.5 s ramps); hard cut to 0 at 44.0",
        duck=dict(db=-6.0, window=[32.0, 41.0], ramp_s=0.5), fade_s=[0.01, 0.0])
    add("C07", T4_OPEN + 0.05, T4_OPEN + 2.2, "creak", 0.16, -0.3, "leaves open 31.0 (right leaf 4 frames late)", speed=0.62)
    add("C08", T4_OPEN + 4 / 24 + 0.05, T4_OPEN + 2.0, "creak", 0.10, 0.3, "right leaf creak, 4 frames late", speed=0.70)
    if st["bell"].get("src"):
        add("C09", BELL_WIN[0], BELL_WIN[1], "bell", 0.24, 0.35, "REMEMBERED BELL: under the memory only (dislocated; belongs to the bench, not the door). Silent outside 32.0-41.0.",
            belongs_to="memory (F5, P03 winter)", fade_s=[1.2, 1.0])
    else:
        add("C09a", 32.4, 36.6, "bell", 0.24, 0.35, "REMEMBERED BELL stroke 1: under the memory only (dislocated). Silent outside 32.0-41.0.", belongs_to="memory (F5, P03 winter)", fade_s=[0.002, 0.3])
        add("C09b", 36.6, 40.8, "bell", 0.20, 0.35, "REMEMBERED BELL stroke 2, ends before 41.0 (fade 0.6 s).", belongs_to="memory (F5, P03 winter)", fade_s=[0.002, 0.6])
    add("C10", T4_LOWER + 0.1, T4_LOWER + 1.3, "creak", 0.12, -0.2, "leaves lowered by hand from 41.0", speed=0.62)
    add("C11", T4_CONTACT_L, T4_CONTACT_L + 0.35, "knock", 0.22, -0.2, "left leaf contact 43.1: knock", sync="paper_stage S4_CONTACT_L")
    add("C12", T4_CONTACT_R - st["thud"]["pre_roll_s"], T4_CONTACT_R + 0.5, "thud", 0.55, 0.0, "right leaf contact 43.5: THUD, then flat stone; must decay before 44.0 (tail cut at 44.0)",
        sync="paper_stage S4_CONTACT_R")
    return cues


def render(cues, st):
    mix = kit.Mix(DUR, seed=5)
    cache = {}

    def stem(stid, speed=1.0):
        key = (stid, speed)
        if key not in cache:
            x = read_wav(st[stid]["path"])
            if speed != 1.0:
                idx = np.arange(0, len(x) - 1, speed)
                x = np.interp(idx, np.arange(len(x)), x)
            cache[key] = x / max(np.abs(x).max(), 1e-9)
        return cache[key]

    for c in cues:
        x = stem(c["stem"], c.get("speed") or 1.0)
        n = int(round((c["until"] - c["at"]) * R))
        if st[c["stem"]].get("loop") or len(x) < n and c["stem"] in ("present", "junction", "park"):
            reps = int(math.ceil(n / len(x))) + 1
            x = np.tile(x, reps)
        x = x[:n].copy()
        fs = c.get("fade_s", [0.01, 0.05])
        x = fades(x, max(fs[0], 1 / R), max(fs[1], 1 / R))
        if c.get("duck"):
            tt = c["at"] + np.arange(len(x)) / R
            a, b = c["duck"]["window"]; r = c["duck"]["ramp_s"]
            g = 10 ** (c["duck"]["db"] / 20)
            w = np.clip((tt - a) / r, 0, 1) * np.clip((b - tt) / r, 0, 1)
            x *= 1 - (1 - g) * w
            c["duck_gain_linear"] = round(g, 4)
        if c.get("spread"):
            for p in c["spread"]:
                mix.add(x, c["at"], c["gain"] * 0.71, p)
        else:
            mix.add(x, c["at"], c["gain"], c["pan"])
        if c["stem"] == "thud" and st["thud"].get("layered_with"):
            body = read_wav(st["thud"]["layered_with"]); body /= max(np.abs(body).max(), 1e-9)
            mix.add(body, c["at"] + st["thud"]["pre_roll_s"], c["gain"] * 0.6, c["pan"])
    # bell window guard: nothing of the bell outside 32-41 (cue is cut to the window by construction)
    # DECLARED DIGITAL SILENCE (applied after every add; the editor must also apply it after any reverb/master)
    i = int(SILENCE[0] * R)
    mix.L[i:] = 0.0
    mix.R[i:] = 0.0
    pcm = mix.master()
    pcm[i:] = 0
    return pcm


def measure(pcm, cues):
    i0 = int(SILENCE[0] * R)
    tail = pcm[i0:]
    rms = lambda a, b: float(np.sqrt((pcm[int(a * R):int(b * R)].astype(np.float64) ** 2).mean()) / 32768 + 1e-12)
    m = dict(silence_window=list(SILENCE), silence_samples=int(tail.size), silence_all_zero=bool(np.all(tail == 0)),
             silence_seconds=round(tail.shape[0] / R, 3), last_nonzero_s=round(float(np.max(np.nonzero(np.any(pcm != 0, 1))[0]) / R), 4),
             peak_dbfs=round(20 * math.log10(np.abs(pcm).max() / 32768 + 1e-12), 2),
             rms_db=dict(shot1=round(20 * math.log10(rms(0.5, 5.0)), 1), shot2=round(20 * math.log10(rms(8.5, 18.5)), 1),
                         shot3=round(20 * math.log10(rms(19.5, 27.5)), 1), shot4_pre=round(20 * math.log10(rms(28.5, 30.9)), 1),
                         shot4_memory=round(20 * math.log10(rms(33.0, 40.5)), 1)))
    bell = [c for c in cues if c["stem"] == "bell"]
    m["bell_inside_memory_window"] = all(c["at"] >= BELL_WIN[0] and c["until"] <= BELL_WIN[1] for c in bell)
    m["bell_cues"] = [c["id"] for c in bell]
    m["duck_db_present_under_bell"] = next(c["duck"]["db"] for c in cues if c["id"] == "C06")
    m["no_cue_in_silence"] = all(c["until"] <= SILENCE[0] + 1e-9 for c in cues)
    m["pass"] = m["silence_all_zero"] and m["silence_seconds"] >= 6.0 and m["bell_inside_memory_window"] and m["no_cue_in_silence"]
    return m


if __name__ == "__main__":
    st = prepare()
    cues = cue_sheet(st)
    pcm = render(cues, st)
    with wave.open(NSW + "/preview_mix.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(R); w.writeframes(pcm.tobytes())
    m = measure(pcm, cues)
    used = sorted({c["source_id"] for c in cues if c["source_id"]})
    evidence, absences = [], []
    for k, f in FORAGED.items():
        rec = dict(id=k, title=f["title"], author=f["author"], license=f["license"], license_url=f["license_url"],
                   source_url=f["source_url"], file_url=f["file_url"],
                   local_path=os.path.relpath(DL + "/" + f["file"], ROOT) if have(k) else None,
                   what_it_shows=f["what_it_shows"], verified_date_or_place=f["verified_date_or_place"],
                   used_as=[c["id"] for c in cues if c["source_id"] == k], downloaded=have(k))
        evidence.append(rec)
    doc = dict(film="les-lieux-dune-fugue", unit="U3 narration-sound-writer", revision="r1 2026-11-16", rate=R, duration_s=DUR,
               time_base="film seconds; cue 'at' is the first sample; gain is linear into kit.Mix.add; pan -1 left .. +1 right",
               editor_recipe=["for each cue: x = wav(file) (mono mean), resample by 'speed' if set, loop beds to length, cut to [at, until), apply fade_s and duck, then mix.add(x, at, gain, pan) (twice at 'spread' pans with gain*0.71 if spread is set)",
                              "thud cues: also add the kit thud body (layered_with) at the contact time, gain*0.6",
                              "apply any reverb BEFORE zeroing; then set mix.L[int(44.0*R):] = mix.R[int(44.0*R):] = 0 and zero the int16 PCM again after master()",
                              "voice is captions only (voice_score.json); no TTS"],
               silence=[dict(window=[44.0, 57.0], samples=0, declared=True, covers=["shot 5 P03 retour (44.0-52.0)", "shot 6 record card (52.0-57.0)"], seconds=13.0,
                             note="every audio sample is 0; the P03 hold 44.0-52.0 alone is 8.0 s >= 6 s")],
               bell_rule=dict(window=list(BELL_WIN), rule="the bell plays under the memory only; present tone ducked 6 dB for the same window"),
               cues=cues, stems={k: dict(file=os.path.relpath(v["path"], ROOT), source=src_text(v), processing=v["proc"]) for k, v in st.items()},
               preview=dict(file=os.path.relpath(NSW + "/preview_mix.wav", ROOT), measured=m),
               foraged_evidence=evidence, foraged_used=used)
    prev = HERE + "/sound_cues.json"
    extra = {}
    if os.path.exists(prev):
        old = json.load(open(prev, encoding="utf-8"))
        extra = {k: old[k] for k in ("absences", "searched", "rejected") if k in old}
    doc.update(extra)
    json.dump(doc, open(prev, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(m, indent=1)); print("foraged used:", used)
