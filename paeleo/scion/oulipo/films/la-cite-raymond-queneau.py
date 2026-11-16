"""La Cité Raymond Queneau: screening reel. One locked 30 s picture of a cut-paper cité, played twice.

The picture is the locked master of the swarm build (films/swarm/la-cite-raymond-queneau/out/master.mp4,
built by picture/maquette.py from foraged paper scans). It is decoded once and pasted pixel-exact into
rows 0-463 of each pass; rows 464-539 are a paper band that carries ONLY transcripts of real recorded speech heard in
that pass (out/<ed>-speech.vtt), so a blind reading of the two passes can only come from the sound. The written caption
editions (sound-A/A.vtt, sound-B/B.vtt, fiction) travel in the edition files and are quoted on the end table.
Sound: the editor's level-matched edition mixes (editor/mix.py), placed with place(); kit's master gain
is applied equally to both passes, so they stay level with each other.

  python3 films/la-cite-raymond-queneau.py                -> assets/films/la-cite-raymond-queneau.mp4 (A first)
  python3 films/la-cite-raymond-queneau.py --order BA     -> films/swarm/la-cite-raymond-queneau/out/reel-BA.mp4
  python3 films/la-cite-raymond-queneau.py --stills 5 25  -> films/stills/la-cite-raymond-queneau/
  python3 films/la-cite-raymond-queneau.py --verify       -> decoded-reel PSNR + pass loudness into out/identity-report.json
"""
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from kit_cinema_b import *  # noqa: F401,F403  (kit: Film, Ink, font, colours; Score, place, lufs)

SLUG = "la-cite-raymond-queneau"
SW = HERE / "swarm" / SLUG
SWOUT = SW / "out"
EDSRC = HERE / "sources" / SLUG / "editor"
RAW = EDSRC / "master.rgb24"
PW, PH, NFR = 960, 464, 720
PIC = NFR / FPS                                   # 30.000 s

ORDER = "AB"
if "--order" in sys.argv:
    i = sys.argv.index("--order"); ORDER = sys.argv[i + 1].upper(); del sys.argv[i:i + 2]
assert ORDER in ("AB", "BA")
VERIFY = "--verify" in sys.argv
if VERIFY:
    sys.argv.remove("--verify")

SC = Score([(0.0, 2.5, "title"), (2.5, 4.0, "card1"), (4.0, 34.0, "pass1"), (34.0, 35.5, "card2"),
            (35.5, 65.5, "pass2"), (65.5, 72.0, "end"), (72.0, 75.0, "credits")])
PASS_ED = {"pass1": ORDER[0], "pass2": ORDER[1]}
HASHES = {"pass1": {}, "pass2": {}}
MASTER_SHA = {}
LOUD = {}
TXT = (36, 32, 29)


def jload(p, default=None):
    try:
        return json.load(open(p))
    except Exception:
        return default


# ---------------------------------------------------------------- master frames ---

def master_frames():
    if not RAW.exists() or RAW.stat().st_size != PW * PH * 3 * NFR:
        RAW.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(SWOUT / "master.mp4"), "-f", "rawvideo", "-pix_fmt", "rgb24", str(RAW)], check=True)
    return np.memmap(RAW, np.uint8, "r", shape=(NFR, PH, PW, 3))


MF = master_frames()


# ---------------------------------------------------------------- captions ---

def read_vtt(p):
    cues = []
    for blk in open(p, encoding="utf-8").read().split("\n\n"):
        lines = [ln for ln in blk.strip().split("\n") if ln]
        for j, ln in enumerate(lines):
            m = re.match(r"(\d+):(\d+):([\d.]+)\s+-->\s+(\d+):(\d+):([\d.]+)", ln)
            if m:
                a = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
                b = int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6])
                body = lines[j + 1:]
                fr = body[0] if body else ""
                gl = re.sub(r"</?i>", "", body[1]) if len(body) > 1 else ""
                cues.append((a, b, fr, gl))
    return cues


VTT = {e: read_vtt(SWOUT / f"{e}-speech.vtt") if (SWOUT / f"{e}-speech.vtt").exists() else [] for e in "AB"}   # speech only
WRITTEN = {e: read_vtt(SW / f"sound-{e}" / f"{e}.vtt") for e in "AB"}                                                 # end table only
SPEECH_ANY = any(VTT.values())


def band(img, ed, t, label):
    """Paper band below the picture (rows 464-539): transcripts of recorded speech only (Instrument Serif French, sans gloss)."""
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, PH, W, H], fill=PAPER)
    d.line([(0, PH), (W, PH)], fill=RULE, width=1)
    d.text((16, H - 14), label, font=font("mono", 11), fill=MUTED + (200,), anchor="ls")
    for a, b, fr, gl in VTT[ed]:
        if a - 0.01 <= t < b:
            al = min(1.0, (t - a) / 0.15 + 0.001, (b - t) / 0.15)
            al = max(0.0, al)
            d.text((W / 2, PH + 29), fr, font=font("serif", 24), fill=TXT + (int(255 * al),), anchor="mm")
            d.text((W / 2, PH + 57), gl, font=font("sans", 14), fill=MUTED + (int(255 * al),), anchor="mm")


# ---------------------------------------------------------------- film ---

class ReelFilm(Film):
    """Pass frames are the decoded master, pasted untouched (no grain, no jitter) into rows 0-463."""

    def frame(self, k):
        t = k / self.fps
        name, local, a, b = SC.at(t)
        if name in ("pass1", "pass2"):
            kl = k - int(round(a * self.fps))
            kl = min(max(kl, 0), NFR - 1)
            img = Image.new("RGB", (W, H), PAPER)
            img.paste(Image.fromarray(np.asarray(MF[kl])), (0, 0))
            band(img, PASS_ED[name], kl / self.fps, "1" if name == "pass1" else "2")
            pic = img.tobytes()[: PW * PH * 3]
            HASHES[name][kl] = hashlib.sha1(pic).hexdigest()
            if kl not in MASTER_SHA:
                MASTER_SHA[kl] = hashlib.sha1(np.ascontiguousarray(MF[kl]).tobytes()).hexdigest()
            return img
        return super().frame(k)


    def render(self, out_dir=OUT, preview=None):
        """kit.Film.render with one change: the encoder settings. kit's CRF lets the differing caption band move each
        frame's QP, so the two passes encode differently. Here: constant QP, a fixed B-frame pattern, no scene-cut
        keyframes, and IDR frames forced every 48 frames from each pass start, so both passes see the same GOP."""
        out_dir.mkdir(parents=True, exist_ok=True)
        if preview is None and len(sys.argv) > 1 and sys.argv[1] == "--stills":
            return Film.render(self, out_dir)
        import tempfile
        total = int(round(self.seconds * self.fps))
        k1, k2 = int(SC.start("pass1") * FPS), int(SC.start("pass2") * FPS)
        kf = f"expr:gte(n,{k1})*lte(n,{k1 + NFR - 1})*eq(mod(n-{k1},48),0)+gte(n,{k2})*lte(n,{k2 + NFR - 1})*eq(mod(n-{k2},48),0)+eq(n,0)+eq(n,{k1 + NFR})+eq(n,{k2 + NFR})"
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "a.wav"
            mix = Mix(self.seconds, seed=self.seed)
            self._sound(mix)
            pcm = mix.master()
            with wave.open(str(wav), "wb") as wf:
                wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(RATE); wf.writeframes(pcm.tobytes())
            mp4 = out_dir / f"{self.slug}.mp4"
            cmd = ["ffmpeg", "-y", "-loglevel", "error",
                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.size[0]}x{self.size[1]}", "-r", str(self.fps), "-i", "-",
                   "-i", str(wav),
                   "-c:v", "libx264", "-preset", "slow", "-qp", str(QP), "-pix_fmt", "yuv420p", "-tune", "animation",
                   "-x264-params", "scenecut=0:b-adapt=0:bframes=3:keyint=480:min-keyint=1:open-gop=0",
                   "-force_key_frames", kf,
                   "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(mp4)]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            poster_k = int(self.poster_at * self.fps)
            for k in range(total):
                img = self.frame(k)
                if k == poster_k:
                    img.save(out_dir / f"{self.slug}.webp", quality=82)
                proc.stdin.write(img.tobytes())
                if k % (self.fps * 10) == 0:
                    print(f"  {self.slug}: {k / self.fps:5.1f}s / {self.seconds}s", flush=True)
            proc.stdin.close()
            if proc.wait() != 0:
                raise SystemExit("ffmpeg failed")
        print(f"wrote {mp4} ({mp4.stat().st_size / 1e6:.2f} MB)")


QP = 28
film = ReelFilm(SLUG if ORDER == "AB" else "reel-BA", seconds=SC.total, boil=0, wobble=0.0, seed=7)
film.poster_at = SC.start("pass1") + 21.0


def card_number(ink, s):
    ink.fill(PAPER)
    ink.text((W / 2, H / 2 - 8), s, "serif", 96, TXT, anchor="mm")


def end_table(ink):
    ident = jload(SWOUT / "identity-report.json", {})
    mixr = jload(SWOUT / "mix.json", {})
    rev = ident.get("master_revision", "?")[:12]
    n = sum(1 for k, h in HASHES["pass1"].items() if HASHES["pass2"].get(k) == h)
    same = f"{n} / {NFR} picture frames identical in both passes (sha1, before encoding)" if HASHES["pass2"] else \
        "reel passes: sha1 compared during the render"
    eds = ident.get("editions", {})
    md5 = " · ".join(f"{e} {eds[e]['match']}/{eds[e]['of']}" for e in ("A", "B", "X", "silent") if e in eds)
    me = mixr.get("editions", {})
    la = me.get("A", {}).get("integrated_lufs_final_mp4", -23.0)
    lb = me.get("B", {}).get("integrated_lufs_final_mp4", -23.0)
    ta = me.get("A", {}).get("true_peak_dbtp_final_mp4", 0)
    tb = me.get("B", {}).get("true_peak_dbtp_final_mp4", 0)
    name = {"A": "A · domestic: someone coming home", "B": "B · surveillance: someone being logged"}
    cA = json.load(open(SW / "sound-A" / "cues-A.json")); cB = json.load(open(SW / "sound-B" / "cues-B.json"))
    def at(cues, f0, f1):
        own = ("16", "silhouette_rise", "head_turn", "curtain_slide")          # window 16's own events only
        return [c for c in sorted(cues, key=lambda c: c["t_sound"]) if f0 <= c["frame"] <= f1 and c.get("source_ledger_id")
                and any(o in c["picture_event_id"] for o in own)]
    def lab(c):
        return f'f{c["frame"]} ' + c["sound_event"].split(" (")[0].split(",")[0]
    a16 = " · ".join(dict.fromkeys(lab(c) for c in at(cA, 492, 566)))
    b16 = " · ".join(dict.fromkeys(lab(c) for c in at(cB, 492, 566)))
    if not any("held silence" in x for x in b16.split(" · ")):
        b16 = b16.replace("f566", "silence f538–565 · f566")
    ink.fill(PAGE)
    ink.text((W / 2, 46), "what changed, and what did not", "serif", 30, TXT, anchor="mm")
    rows = [("pass 1 was", name[ORDER[0]]),
            ("pass 2 was", name[ORDER[1]]),
            ("picture", same),
            ("editions", f"framemd5 vs master ({rev}): {md5}"),
            ("loudness", f"A {la:.1f} LUFS, TP {ta:.1f} dBTP  ·  B {lb:.1f} LUFS, TP {tb:.1f} dBTP  (ebur128)"),
            ("window 16, f492–566", "A: " + a16),
            ("", "B: " + b16),
            ("written editions", "A « " + WRITTEN["A"][-1][2].strip(" .") + " »   ·   B « " + WRITTEN["B"][-1][2].strip(" .") + " »  (in the files, not shown above)")]
    y = 96
    for lab, s_ in rows:
        ink.text((48, y + 4), lab, "mono", 12, MUTED)
        ink.text((222, y), s_, "serif", 20 if len(s_) < 74 else (17 if len(s_) < 92 else 14), TXT)
        y += 48 if lab.startswith("pass 2") or lab == "editions" else 42
    ink.text((W / 2, H - 30), "fiction: a paper model; names and log entries invented · attribution on the next card and in the notes",
             "mono", 11, MUTED, anchor="mm")


def credits_card(ink):
    cr = jload(HERE / "credits" / f"{SLUG}.json", [])
    by = [c for c in cr if c["license"].upper().startswith("CC BY")]
    ink.fill(PAPER)
    ink.text((W / 2, 40), "attribution (CC BY / CC BY-SA)", "serif", 24, TXT, anchor="mm")
    y = 78
    for c in by:
        t = re.sub(r"\.(ogg|wav|mp3|jpg|png)$", "", c["title"].split(":")[0])
        ink.text((60, y), f"{t} · {c['author']} · {c['license']}", "sans", 13 if len(by) < 12 else 12, TXT)
        ink.text((60, y + 16), c["source_url"], "mono", 9, MUTED)
        y += 34 if len(by) < 11 else 30
    pd_n = len(cr) - len(by)
    ink.text((60, y + 6), f"and {pd_n} public-domain / CC0 / no-known-restriction items: full list in credits/{SLUG}.json and the notes",
             "sans", 12, MUTED)
    ink.text((W / 2, H - 52), "soundtracks of editions B and C and of this reel: CC BY-SA 4.0 (they adapt W.carter's CC BY-SA wind)",
             "mono", 11, TXT, anchor="mm")
    ink.text((W / 2, H - 32), "picture: cut-paper model by the film, from foraged scans incl. Library of Congress, Music Division, Federal Theatre Project Collection",
             "mono", 10, MUTED, anchor="mm")


@film.picture
def frame(t, ink):
    name, local, a, b = SC.at(t)
    if name == "title":
        ink.fill(PAPER)
        ink.text((W / 2, H / 2 - 54), "after La Cité Raymond Queneau, Azam & Firode 1998", "mono", 14, MUTED, anchor="mm")
        ink.text((W / 2, H / 2 + 2), "one picture, two soundtracks", "serif", 46, TXT, anchor="mm")
        ink.text((W / 2, H / 2 + 52), "a 30 s cut-paper cité, played twice", "sans", 15, MUTED, anchor="mm")
        ink.text((W / 2, H / 2 + 92), "fiction: a paper model, not the real estate; any names and logs are invented", "mono", 12, MUTED, anchor="mm")
        ink.text((W / 2, H / 2 + 112), ("words under the picture transcribe real recorded voices only" if SPEECH_ANY else
                                        "no voice is recorded: the passes carry no captions; listen"), "mono", 12, MUTED, anchor="mm")
    elif name == "card1":
        card_number(ink, "1")
    elif name == "card2":
        card_number(ink, "2")
    elif name == "end":
        end_table(ink)
    else:
        credits_card(ink)


def read_mix(ed):
    p = HERE / jload(SWOUT / "mix.json")["editions"][ed]["wav"]
    w = wave.open(str(p))
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    return x.reshape(-1, 2)


@film.sound
def sound(mix):
    st = {e: read_mix(e) for e in "AB"}
    place(mix, st[ORDER[0]], SC.start("pass1"))
    place(mix, st[ORDER[1]], SC.start("pass2"))
    # replicate kit.Mix.master's one overall gain, so both passes are reported as heard (equal gain on both)
    full = np.stack([mix.L, mix.R], 1)
    peak = np.abs(full).max()
    g = 0.89 / max(peak, 1.0)
    if peak < 0.25:
        rms = math.sqrt(((full * g) ** 2).mean())
        g *= min(4.0, 0.2 / max(rms, 1e-6), 0.89 / max(np.abs(full * g).max(), 1e-9))
    for e in "AB":
        LOUD[e] = lufs(st[e] * g)
    LOUD["master_gain_db"] = 20 * math.log10(g)
    print(f"  reel passes after kit master gain {LOUD['master_gain_db']:+.2f} dB: A {LOUD['A']:.2f} · B {LOUD['B']:.2f} LUFS (kit lufs)")
    assert abs(LOUD["A"] - LOUD["B"]) <= 0.5


# ---------------------------------------------------------------- verify ---

def decode_pass(mp4, k0):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", f"select='between(n\\,{k0}\\,{k0 + NFR - 1})'",
                             "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)


def ebur(mp4, a, b):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-af", f"atrim={a}:{b},ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", s)[1]), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", s)[1])


def verify():
    rep = jload(SWOUT / "identity-report.json", {})
    reels = {}
    for tag, mp4, order in (("AB", OUT / f"{SLUG}.mp4", "AB"), ("BA", SWOUT / "reel-BA.mp4", "BA")):
        if not mp4.exists():
            continue
        k1, k2 = int(SC.start("pass1") * FPS), int(SC.start("pass2") * FPS)
        p1, p2 = decode_pass(mp4, k1), decode_pass(mp4, k2)
        fs = W * H * 3
        ps, n = [], 0
        while True:
            a, b = p1.stdout.read(fs), p2.stdout.read(fs)
            if len(a) < fs or len(b) < fs:
                break
            x = np.frombuffer(a, np.uint8).reshape(H, W, 3)[:PH].astype(np.float32)
            y = np.frombuffer(b, np.uint8).reshape(H, W, 3)[:PH].astype(np.float32)
            mse = float(((x - y) ** 2).mean())
            ps.append(99.0 if mse == 0 else 10 * math.log10(255 ** 2 / mse))
            n += 1
        p1.wait(); p2.wait()
        ps = np.array(ps)
        la = ebur(mp4, SC.start("pass1"), SC.start("pass1") + PIC)
        lb = ebur(mp4, SC.start("pass2"), SC.start("pass2") + PIC)
        pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", str(mp4)],
                                       capture_output=True, text=True).stdout)["format"]
        reels[tag] = {"path": str(mp4.relative_to(HERE.parent)), "order": order, "duration_s": float(pr["duration"]), "bytes": int(pr["size"]),
                      "picture_region_frames_compared": n, "psnr_db_min": round(float(ps.min()), 2), "psnr_db_mean": round(float(ps.mean()), 2),
                      "psnr_db_p5": round(float(np.percentile(ps, 5)), 2), "frames_below_45db": int((ps < 45).sum()),
                      "pass_psnr_ge_45": bool(ps.min() >= 45),
                      "pass1_lufs_tp": la, "pass2_lufs_tp": lb, "pass_lu_difference": round(abs(la[0] - lb[0]), 2),
                      "sha1_before_encoding": jload(SWOUT / f"reel-{tag}-sha1.json", {})}
        print(tag, reels[tag])
    rep["reels"] = reels
    rep["reel_note"] = "presentation derivative, not the fixture: pass pictures sha1-identical before encoding; after lossy encoding compared by PSNR on rows 0-463"
    json.dump(rep, open(SWOUT / "identity-report.json", "w"), indent=1)


if __name__ == "__main__":
    if VERIFY:
        verify()
        raise SystemExit
    stills = len(sys.argv) > 1 and sys.argv[1] == "--stills"
    film.render(out_dir=OUT if ORDER == "AB" else SWOUT)
    if not stills:
        eq = sum(1 for k, h in HASHES["pass1"].items() if HASHES["pass2"].get(k) == h)
        em = sum(1 for k, h in HASHES["pass1"].items() if MASTER_SHA.get(k) == h)
        res = {"order": ORDER, "frames_pass1": len(HASHES["pass1"]), "frames_pass2": len(HASHES["pass2"]),
               "pass1_eq_pass2": eq, "pass1_eq_decoded_master": em, "of": NFR, "pass": eq == NFR and em == NFR,
               "loudness_kit_lufs_after_master_gain": LOUD}
        json.dump(res, open(SWOUT / f"reel-{ORDER}-sha1.json", "w"), indent=1)
        print("reel picture identity:", res)
        assert res["pass"], "reel passes differ"
