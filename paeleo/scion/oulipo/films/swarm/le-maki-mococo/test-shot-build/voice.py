"""#47 Sound-to-action: assemble L1 from real Lingua Libre recordings (speaker Grendelkhan, CC0) and MEASURE its timing.

Decoded only with ffmpeg. 'hangs' and 'swings' = recorded 'hang'/'swing' + the final voiced sibilant cut from the
same speaker's recorded 'is' (a splice of real speech, declared in the ledger). Phone spans inside each word are
placed from the measured energy envelope (onset / nucleus / coda), not invented.
"""
import json
import subprocess
from pathlib import Path

import numpy as np

VOICE = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/test-shot/voice")
RATE = 44100
L1 = ["in", "the", "dark", "it", "hangs", "and", "swings"]
# phone classes per word: (fraction of word assigned by measured envelope) -> pose class
PHONES = {
    "in": [("onset", "EI"), ("nucleus", "EI"), ("coda", "LNT")],
    "the": [("onset", "LNT"), ("nucleus", "A"), ("coda", "A")],
    "dark": [("onset", "LNT"), ("nucleus", "A"), ("coda", "LNT")],
    "it": [("onset", "EI"), ("nucleus", "EI"), ("coda", "LNT")],
    "hangs": [("onset", "A"), ("nucleus", "A"), ("coda", "EI")],
    "and": [("onset", "A"), ("nucleus", "A"), ("coda", "LNT")],
    "swings": [("onset", "UW"), ("nucleus", "EI"), ("coda", "EI")],
}


def load(word):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(VOICE / f"{word}.wav"), "-ac", "1", "-ar", str(RATE),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def env(x, hop=441):
    n = len(x) // hop
    return np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, 1) + 1e-12)


def trim(x, db=-34):
    e = env(x)
    thr = e.max() * 10 ** (db / 20)
    idx = np.nonzero(e > thr)[0]
    a, b = max(0, idx[0] - 2) * 441, min(len(x), (idx[-1] + 3) * 441)
    y = x[a:b] - np.mean(x[a:b])
    f = int(0.008 * RATE)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def sibilant_from_is():
    """Final /z/ of the speaker's 'is': the tail where zero-crossing rate is high."""
    x = trim(load("is"))
    hop = 441
    n = len(x) // hop
    zc = np.array([np.mean(np.abs(np.diff(np.sign(x[i * hop:(i + 1) * hop])))) for i in range(n)])
    e = env(x)
    hi = np.nonzero((zc > 0.25) & (e > e.max() * 0.03))[0]
    hi = hi[hi > n * 0.35]
    a = (hi[0] if len(hi) else int(n * 0.6)) * hop
    z = x[a:].copy()
    f = int(0.012 * RATE)
    z[:f] *= np.linspace(0, 1, f)
    return z, dict(start_s=a / RATE, dur_s=len(z) / RATE)


def word_audio(w, zcache):
    if w in ("hangs", "swings"):
        base = trim(load(w[:-1]))
        z = zcache[0] * 0.8
        f = int(0.015 * RATE)
        out = np.concatenate([base[:-f], base[-f:] * np.linspace(1, 0.4, f) + z[:f] * np.linspace(0.3, 1, f), z[f:]])
        return out
    return trim(load(w))


def measure(x, t_word):
    """Split a word into onset/nucleus/coda from its energy envelope (10 ms hop)."""
    e = env(x)
    pk = e.max()
    above = np.nonzero(e > pk * 0.45)[0]
    n0, n1 = above[0], above[-1] + 1
    T = len(e) / 100
    return dict(onset=(0.0, n0 / 100), nucleus=(n0 / 100, n1 / 100), coda=(n1 / 100, T)), e / pk


def assemble(words, gaps):
    zc = sibilant_from_is()
    parts, words_out, phones, envs = [], [], [], []
    t = 0.0
    for k, w in enumerate(words):
        x = word_audio(w, zc)
        x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * 0.075          # loudness match (RMS)
        spans, e = measure(x, t)
        words_out.append(dict(text=w, t0=round(t, 3), t1=round(t + len(x) / RATE, 3)))
        for part, v in PHONES[w]:
            a, b = spans[part]
            if b - a > 0.005:
                phones.append(dict(word=w, part=part, v=v, t0=round(t + a, 3), t1=round(t + b, 3)))
        parts.append(x)
        envs.append(e)
        t += len(x) / RATE
        g = gaps[k] if k < len(gaps) else 0
        if g:
            parts.append(np.zeros(int(g * RATE))); envs.append(np.zeros(int(g * 100)))
            t += g
    wav = np.concatenate(parts)
    envall = np.concatenate(envs)
    return dict(wav=wav, words=words_out, phones=phones, env=envall.tolist(), zsplice=zc[1])


def build():
    l1 = assemble(L1, [0.06, 0.08, 0.10, 0.07, 0.09, 0.08])
    hg = assemble(["hangs"], [])
    return {"L1": l1, "hangs": hg}


if __name__ == "__main__":
    v = build()
    import wave
    for k in v:
        pcm = (np.clip(v[k]["wav"] / max(1e-9, np.abs(v[k]["wav"]).max()) * 0.9, -1, 1) * 32767).astype(np.int16)
        with wave.open(str(VOICE / f"voice_{k}.wav"), "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(RATE); wf.writeframes(pcm.tobytes())
        print(k, json.dumps(v[k]["words"]), len(v[k]["wav"]) / RATE)
        print(json.dumps(v[k]["phones"]))
