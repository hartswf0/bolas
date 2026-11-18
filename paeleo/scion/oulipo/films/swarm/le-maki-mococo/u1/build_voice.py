"""U1 reading designer: assemble the poem voice from real Lingua Libre word recordings and MEASURE its timing.

Inputs are decoded only with ffmpeg (untrusted data). Nothing is synthesized: every sample in the voice files
is a sample of a foraged recording, trimmed, faded, gain-matched and placed with silence between words.
Splices (declared): 'hangs' = Grendelkhan 'hang' + final /z/ of Grendelkhan 'is'; 'swings' likewise.
Outputs (in OUT): voice_poem.wav, voice_L1.wav, voice_binturong.wav, waveform PNG, voice_measure.json.
"""
import json, subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/reading")
OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/"
           "u1-reading-cue-staging-reading-designer-cue-designer-staging-unit-merged-they-share-segment-ids-")
RATE = 44100
HOP = 441                      # 10 ms analysis hop
TARGET_RMS = 0.085             # loudness match on voiced frames

POEM = [
    ["In", "the", "dark", "it", "hangs", "and", "swings,"],
    ["binturong,", "binturong,"],
    ["smells", "of", "popcorn,", "never", "rings —"],
    ["binturong,", "binturong."],
]
# word key -> source stem(s) in SRC
SOURCE = {
    "in": "Grendelkhan-in", "the": "Grendelkhan-the", "dark": "Grendelkhan-dark", "it": "Grendelkhan-it",
    "hangs": ("Grendelkhan-hang", "z"), "and": "Grendelkhan-and", "swings": ("Grendelkhan-swing", "z"),
    "binturong": "Vealhurl-binturong", "smells": "Grendelkhan-smells", "of": "Grendelkhan-of",
    "popcorn": ["Vealhurl-popcorn", ("Grendelkhan-pop", "Grendelkhan-corn")], "never": "Grendelkhan-never", "rings": "Grendelkhan-rings",
}
# syllables, with phone-class plan per syllable: (onset, nucleus, coda) viseme classes (None = no such part)
SYL = {
    "in": [("in", None, "EI", "LNT")],
    "the": [("the", "LNT", "A", None)],
    "dark": [("dark", "LNT", "A", "LNT")],
    "it": [("it", None, "EI", "LNT")],
    "hangs": [("hangs", None, "A", "EI")],
    "and": [("and", None, "A", "LNT")],
    "swings": [("swings", "UW", "EI", "EI")],
    "binturong": [("bin", "MBP", "EI", "LNT"), ("tu", "LNT", "UW", None), ("rong", "UW", "A", "LNT")],
    "smells": [("smells", "MBP", "EI", "LNT")],     # s-m: lips close on the m
    "of": [("of", None, "A", "FV")],
    "popcorn": [("pop", "MBP", "O", "MBP"), ("corn", "LNT", "O", "LNT")],
    "never": [("nev", "LNT", "EI", "FV"), ("er", None, "A", None)],
    "rings": [("rings", "UW", "EI", "LNT")],
}
STRESS = {"binturong": 0, "popcorn": 0, "never": 0}   # index of stressed syllable
OPEN = {"rest": 0.0, "MBP": 0.0, "FV": 0.15, "LNT": 0.3, "EI": 0.45, "UW": 0.35, "O": 0.7, "A": 1.0}


def key(w):
    return w.strip(",.— ").lower()


def decode(stem):
    for ext in (".wav", ".mp3"):
        p = SRC / (stem + ext)
        if p.exists():
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(RATE),
                                  "-af", "highpass=f=70", "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout
            return np.frombuffer(raw, np.float32).astype(np.float64), p.name
    raise FileNotFoundError(stem)


def env(x):
    n = len(x) // HOP
    return np.sqrt(np.mean(x[: n * HOP].reshape(n, HOP) ** 2, 1) + 1e-12)


def trim(x, db=-26, db_on=-36, pre=2, post=2):
    e = env(x)
    idx = np.nonzero(e > e.max() * 10 ** (db / 20))[0]
    # onset: walk back from the peak through frames above the offset threshold, tolerating gaps <= 40 ms;
    # an earlier isolated blip (click/breath separated by a longer silence) is excluded
    thr = e.max() * 10 ** (db_on / 20)
    on = int(np.argmax(e)); gap = 0
    for i in range(on, -1, -1):
        if e[i] > thr:
            on, gap = i, 0
        else:
            gap += 1
            if gap > 4:
                break
    a, b = max(0, on - pre) * HOP, min(len(x), (idx[-1] + 1 + post) * HOP)
    y = x[a:b] - np.mean(x[a:b])
    f = int(0.006 * RATE)
    y[:f] *= np.linspace(0, 1, f)
    g = int(0.02 * RATE)
    y[-g:] *= np.linspace(1, 0, g)
    return y, a / RATE


def final_z():
    """Final voiced sibilant of Grendelkhan 'is' (high zero-crossing tail)."""
    x, _ = trim(decode("Grendelkhan-is")[0])
    n = len(x) // HOP
    zc = np.array([np.mean(np.abs(np.diff(np.sign(x[i * HOP:(i + 1) * HOP])))) for i in range(n)])
    e = env(x)
    hi = np.nonzero((zc > 0.25) & (e > e.max() * 0.03))[0]
    hi = hi[hi > n * 0.35]
    a = (hi[0] if len(hi) else int(n * 0.6)) * HOP
    z = x[a:].copy()
    f = int(0.012 * RATE)
    z[:f] *= np.linspace(0, 1, f)
    return z, a / RATE


ZCACHE = None


def have(stem):
    return any((SRC / (stem + e)).exists() for e in (".wav", ".mp3"))


def word_audio(k):
    """Returns (samples, meta) or (None, meta) for a declared gap (no allowed recording obtained)."""
    global ZCACHE
    s = SOURCE[k]
    if isinstance(s, list):                       # alternatives in order of preference
        for alt in s:
            if isinstance(alt, str) and have(alt):
                s = alt; break
            if isinstance(alt, tuple) and all(have(a) for a in alt):
                ys, offs = [], []
                for a in alt:
                    y, off = trim(decode(a)[0]); ys.append(y); offs.append(off)
                closure = np.zeros(int(0.03 * RATE))   # the /p/-/k/ closure between the two recorded words
                return np.concatenate([ys[0], closure, ys[1]]), dict(
                    files=[a + (".wav" if (SRC / (a + ".wav")).exists() else ".mp3") for a in alt],
                    trim_start_s=round(offs[0], 3), splice="recorded 'pop' + 30 ms silence + recorded 'corn'")
        else:
            return None, dict(files=["GAP"], gap=True)
    if isinstance(s, tuple) and not have(s[0]) or isinstance(s, str) and not have(s):
        return None, dict(files=["GAP"], gap=True)
    if isinstance(s, tuple):
        if ZCACHE is None:
            ZCACHE = final_z()
        x, f0 = decode(s[0])
        base, off = trim(x)
        z = ZCACHE[0]
        f = int(0.015 * RATE)
        y = np.concatenate([base[:-f], base[-f:] * np.linspace(1, 0.4, f) + z[:f] * 0.8 * np.linspace(0.3, 1, f),
                            z[f:] * 0.8])
        return y, dict(files=[f0, "Grendelkhan-is (final /z/ from %.3f s)" % ZCACHE[1]], trim_start_s=round(off, 3),
                       splice="recorded '%s' + final /z/ of the same speaker's 'is'" % s[0].split("-")[1])
    x, f0 = decode(s)
    y, off = trim(x)
    return y, dict(files=[f0], trim_start_s=round(off, 3))


def loud(y):
    e = env(y)
    v = e[e > e.max() * 0.25]
    r = np.sqrt(np.mean(v ** 2))
    return y * (TARGET_RMS / r)


def smooth(e, k=3):
    return np.convolve(e, np.ones(k) / k, mode="same")


def syllable_split(y, n):
    """Syllable boundaries at energy-envelope minima between the n strongest voiced humps."""
    if n == 1:
        return []
    e = smooth(env(y), 3)
    pk = e.max()
    # candidate minima, away from the ends
    cands = [i for i in range(3, len(e) - 3) if e[i] <= e[i - 1] and e[i] <= e[i + 1] and e[i] < pk * 0.8]
    # score: depth relative to the maxima on either side
    scored = []
    for i in cands:
        l, r = e[:i].max(), e[i + 1:].max()
        scored.append((min(l, r) - e[i], i))
    scored.sort(reverse=True)
    picks = []
    for d, i in scored:
        if all(abs(i - j) > 4 for j in picks):
            picks.append(i)
        if len(picks) == n - 1:
            break
    return sorted(p * HOP / RATE for p in picks)


def phases(e, a, b):
    """Within syllable span [a,b) (in env frames): onset (below 45% of syllable peak), nucleus, coda."""
    seg = e[a:b]
    if len(seg) == 0:
        return (a, a, b, b)
    pk = seg.max()
    above = np.nonzero(seg > pk * 0.45)[0]
    return a, a + above[0], a + above[-1] + 1, b


def build():
    lines_out, parts, t = [], [], 0.0
    words, sylls = [], []
    prov = {}
    for li, line in enumerate(POEM):
        lid = f"L{li + 1}"
        for wi, w in enumerate(line):
            k = key(w)
            y, meta = word_audio(k)
            if y is None:
                # DECLARED GAP: no allowed recording obtained; silent span of nominal (NOT measured) length,
                # 0.24 s per syllable; the mouth mouths it silently.
                y = np.zeros(int(0.24 * len(SYL[k]) * RATE))
                meta = dict(files=["GAP (silent, nominal 0.24 s/syllable, not measured)"], gap=True,
                            trim_start_s=None)
            else:
                y = loud(y)
            wid = f"{lid}.w{wi + 1}"
            t0 = t
            t1 = t + len(y) / RATE
            take = meta["files"][0]
            words.append(dict(seg_id=wid, text=w, key=k, t0=round(t0, 3), t1=round(t1, 3), take=take, **meta))
            prov.setdefault(take, []).append(wid)
            # syllables
            plan = SYL[k]
            gap = bool(meta.get("gap"))
            dur = len(y) / RATE
            cuts = [dur * i / len(plan) for i in range(1, len(plan))] if gap else syllable_split(y, len(plan))
            bounds = [0.0] + cuts + [len(y) / RATE]
            e = smooth(env(y), 2)
            gmax = None
            for si, (sname, on, nu, co) in enumerate(plan):
                a, b = int(bounds[si] * 100), int(bounds[si + 1] * 100)
                if gap:   # nominal phases 25/75 % (declared, not measured)
                    pa, pn, pc, pb = a, a + (b - a) // 4, a + 3 * (b - a) // 4, b
                else:
                    pa, pn, pc, pb = phases(e, a, b)
                seg = e[a:b] if b > a else e[a:a + 1]
                sylls.append(dict(seg_id=f"{wid}.s{si + 1}", text=sname, word=wid,
                                  t0=round(t0 + a / 100, 3), t1=round(t0 + b / 100, 3),
                                  nucleus=[round(t0 + pn / 100, 3), round(t0 + pc / 100, 3)],
                                  stressed=(STRESS.get(k, 0) == si) if len(plan) > 1 else True,
                                  plan=dict(onset=on, nucleus=nu, coda=co),
                                  rms_peak=float(seg.max()), gap=gap,
                                  timing=("NOMINAL (declared gap, silent mouthing)" if gap else "measured"),
                                  _phase_frames=(pa, pn, pc, pb), _t0w=t0))
            parts.append(y)
            t = t1
            last_word = wi == len(line) - 1
            if last_word and li < len(POEM) - 1:
                g = 0.35
            elif w.endswith(","):
                g = 0.12
            else:
                g = [0.06, 0.07, 0.08, 0.06, 0.07, 0.06, 0.08, 0.06][wi % 8]
            if not (last_word and li == len(POEM) - 1):
                parts.append(np.zeros(int(round(g * RATE))))
                t += round(g * RATE) / RATE
        lines_out.append(dict(seg_id=lid, text=" ".join(line)))
    wav = np.concatenate(parts)
    peak = np.abs(wav).max()
    if peak > 0.89:
        wav *= 0.89 / peak
    # jaw from RMS, normalised over the whole poem
    gmax = max(s["rms_peak"] for s in sylls)
    for s in sylls:
        s["rms_rel"] = 0.5 if s["gap"] else round(s["rms_peak"] / gmax, 3)   # gap: nominal half-open mouthing
    return dict(wav=wav, lines=lines_out, words=words, sylls=sylls, prov=prov)


def visemes(sylls):
    out = []
    for s in sylls:
        pa, pn, pc, pb = s.pop("_phase_frames")
        t0w = s.pop("_t0w")
        keys = []
        p = s["plan"]
        # linguistic requirement (shape openness) separated from emphasis (measured loudness), SCION #47 sec. 6
        jaw = 0.65 + 0.35 * s["rms_rel"]
        if p["onset"]:
            a = t0w + pa / 100
            if p["onset"] == "MBP":
                a -= 0.05          # lips close before the burst (closure is silent; measured burst at pn)
            keys.append(dict(t=round(a, 3), shape=p["onset"], jaw=round(OPEN[p["onset"]] * jaw, 3), part="onset"))
        keys.append(dict(t=round(t0w + pn / 100, 3), shape=p["nucleus"], jaw=round(OPEN[p["nucleus"]] * jaw, 3),
                         part="nucleus"))
        if p["coda"]:
            keys.append(dict(t=round(t0w + pc / 100, 3), shape=p["coda"], jaw=round(OPEN[p["coda"]] * jaw, 3),
                             part="coda"))
        s.pop("rms_peak")
        out.append(dict(seg_id=s["seg_id"], text=s["text"], keys=keys, emphasis=round(jaw, 3),
                        silent=s["gap"]))
    return out


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(RATE); wf.writeframes(pcm.tobytes())


def waveform_png(path, x, words, sylls, vis, title):
    W, H = 2400, 520
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", 15)
    except Exception:
        f = ImageFont.load_default()
    T = len(x) / RATE
    X = lambda t: int(20 + (W - 40) * t / T)
    mid = 200
    n = W - 40
    for i in range(n):
        a, b = int(i * len(x) / n), int((i + 1) * len(x) / n)
        seg = x[a:b]
        if len(seg):
            d.line([(20 + i, mid - seg.max() * 330), (20 + i, mid - seg.min() * 330)], fill=(90, 80, 75))
    e = env(x)
    pts = [(X(i / 100), mid - 10 - e[i] / e.max() * 150) for i in range(len(e))]
    d.line(pts, fill=(200, 60, 70), width=2)
    for w in words:
        d.rectangle([X(w["t0"]), 350, X(w["t1"]), 372], outline=(42, 36, 34))
        d.text((X(w["t0"]) + 2, 352), w["text"], fill=(42, 36, 34), font=f)
    for s in sylls:
        d.line([(X(s["t0"]), 20), (X(s["t0"]), 345)], fill=(60, 120, 200), width=1)
        d.text((X(s["t0"]) + 2, 380), s["text"], fill=(60, 120, 200), font=f)
    for v in vis:
        for k in v["keys"]:
            d.text((X(k["t"]), 410 + 22 * ["onset", "nucleus", "coda"].index(k["part"])), k["shape"],
                   fill=(120, 90, 30), font=f)
    for s in range(int(T) + 1):
        d.line([(X(s), 490), (X(s), 500)], fill=0)
        d.text((X(s) + 2, 500), f"{s}s", fill=0, font=f)
    d.text((20, 2), title + "  (grey: waveform; red: 10 ms RMS envelope; blue: measured syllable onsets; "
           "brown: viseme keys onset/nucleus/coda)", fill=0, font=f)
    im.save(path)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    v = build()
    vis = visemes(v["sylls"])
    wav = v["wav"]
    write_wav(OUT / "voice_poem.wav", wav)
    l1_end = [w for w in v["words"] if w["seg_id"] == "L1.w7"][0]["t1"]
    write_wav(OUT / "voice_L1.wav", wav[: int(round(l1_end * RATE)) + int(0.03 * RATE)])
    b = [w for w in v["words"] if w["seg_id"] == "L2.w1"][0]
    bw = wav[int(round(b["t0"] * RATE)): int(round(b["t1"] * RATE))]
    write_wav(OUT / "voice_binturong.wav", bw)
    waveform_png(OUT / "voice_poem_waveform.png", wav, v["words"], v["sylls"], vis, "voice_poem.wav")
    meas = dict(duration_s=round(len(wav) / RATE, 3), L1_duration_s=round(l1_end + 0.03, 3),
                binturong_duration_s=round(len(bw) / RATE, 3), lines=v["lines"], words=v["words"],
                syllables=v["sylls"], visemes=vis, provenance=v["prov"])
    # 24 fps jaw track (RMS envelope, normalised) for the poem
    e = env(wav)
    fps = 24
    tr = [round(float(e[int(i * 100 / fps): int((i + 1) * 100 / fps)].max() / e.max()), 3)
          for i in range(int(len(wav) / RATE * fps))]
    meas["rms_24fps"] = tr
    json.dump(meas, open(OUT / "voice_measure.json", "w"), indent=1)
    print(json.dumps({k: meas[k] for k in ("duration_s", "L1_duration_s", "binturong_duration_s")}))
    for w in v["words"]:
        print(w["seg_id"], w["text"], w["t0"], w["t1"], w["take"])
    for s in v["sylls"]:
        print("  ", s["seg_id"], s["text"], s["t0"], s["t1"], s["nucleus"], s["rms_rel"])
