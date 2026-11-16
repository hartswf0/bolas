"""Steps 3-4 (editor): attach(master, mix) -> editions with -c:v copy; framemd5 identity; negative controls.

Writes out/edition-{A,B,X,C}.mp4, out/control-silent.mp4, out/A.vtt, out/B.vtt, out/identity-report.json
(the reel PSNR block is added later by films/la-cite-raymond-queneau.py --verify).
"""
import json, os, shutil, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mix import ebur128  # noqa: E402

SW = os.path.dirname(HERE)
OUT = os.path.join(SW, "out")
FILMS = os.path.abspath(os.path.join(SW, "..", ".."))
ED = os.path.join(FILMS, "sources", "la-cite-raymond-queneau", "editor")
MASTER = os.path.join(OUT, "master.mp4")
QUAR = os.path.join(OUT, "quarantine")
# which captions travel with which edition (X: A's captions to 16.0 s, then B's)
CAPS = {"A": "A.vtt", "B": "B.vtt", "X": "X.vtt", "C": None, "silent": None}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(" ".join(cmd) + "\n" + r.stderr[-2000:])
    return r


def framemd5(path):
    r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-map", "0:v:0", "-f", "framemd5", "-"])
    head = {}
    rows = []
    for ln in r.stdout.splitlines():
        if ln.startswith("#"):
            if ":" in ln:
                k, v = ln[1:].split(":", 1); head[k.strip()] = v.strip()
            continue
        p = [x.strip() for x in ln.split(",")]
        rows.append((int(p[2]), int(p[3]), int(p[4]), p[5]))   # pts, duration, size, md5
    return head, rows


def master_rows():
    head, rows = {}, []
    for ln in open(os.path.join(OUT, "master.framemd5")):
        ln = ln.strip()
        if ln.startswith("#"):
            if ":" in ln:
                k, v = ln[1:].split(":", 1); head[k.strip()] = v.strip()
            continue
        p = [x.strip() for x in ln.split(",")]
        rows.append((int(p[2]), int(p[3]), int(p[4]), p[5]))
    return head, rows


def compare(rows, mrows):
    n = sum(1 for a, b in zip(rows, mrows) if a == b)
    return {"frames": len(rows), "match": n, "of": len(mrows), "pass": len(rows) == len(mrows) and n == len(mrows)}


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=index,codec_type,codec_name,width,height,r_frame_rate,time_base,nb_frames",
             "-of", "json", path])
    return json.loads(r.stdout)["streams"]


FICTION_X = ("NOTE FICTION: written edition X (voice-crossover diagnostic). Edition A's written lines before 16.0 s, "
             "edition B's from 16.0 s. The model and every line are invented; captions are written text, not transcripts of recorded speech.")


def speech_in(ed):
    return has_cues(os.path.join(OUT, f"{ed}-speech.vtt"))


def drop_crossover_if_unspoken(txt, ed):
    """repair 2: a written line at 16.0-17.5 s implies speech there; keep it only if real speech is heard in that edition."""
    # the only caption allowed at the key cut is the transcript of what is actually heard (out/<ed>-speech.vtt);
    # a written line there would put words in a voice that does not say them, so it is always dropped
    blocks = txt.split("\n\n")
    keep = [b for b in blocks if not ("-->" in b and b.split("-->")[0].strip().split("\n")[-1].startswith("00:00:16."))]
    return "\n\n".join(keep)


def write_x_vtt():
    """X carries A's captions before the key cut and B's from it (the voice crossover)."""
    a = open(os.path.join(SW, "sound-A", "A.vtt"), encoding="utf-8").read().split("\n\n")
    b = open(os.path.join(SW, "sound-B", "B.vtt"), encoding="utf-8").read().split("\n\n")
    keep = ["WEBVTT\nKind: captions\nLanguage: fr", FICTION_X]
    for blk in a:
        if "-->" in blk and blk.split("-->")[0].strip().split("\n")[-1] < "00:00:16.000":
            keep.append(blk.strip())
    for blk in b:
        if "-->" in blk and blk.split("-->")[0].strip().split("\n")[-1] >= "00:00:16.000":
            keep.append(blk.strip())
    open(os.path.join(OUT, "X.vtt"), "w", encoding="utf-8").write(drop_crossover_if_unspoken("\n\n".join(keep) + "\n", "X"))


def has_cues(p):
    return p is not None and os.path.exists(p) and "-->" in open(p, encoding="utf-8").read()


def attach(ed, wav, vtt, dst):
    """repair 2: the mp4 carries ONLY a transcript of real recorded speech (mov_text), when such speech is heard.
    The written editions (fiction) are NOT muxed: mp4/mov_text cannot keep a subtitle track non-default or titled
    (ffmpeg's mov muxer writes default=1 and drops the title), so they ship as labelled sidecar files instead."""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", MASTER, "-i", wav]
    sp = os.path.join(OUT, f"{ed}-speech.vtt")
    has = has_cues(sp)
    if has:
        cmd += ["-i", sp]
    cmd += ["-map", "0:v", "-map", "1:a"] + (["-map", "2"] if has else [])
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "160k"]
    if has:
        cmd += ["-c:s", "mov_text", "-metadata:s:s:0", "language=fre",
                "-metadata:s:s:0", "handler_name=transcript of recorded speech only"]
    cmd += ["-movflags", "+faststart", dst]
    run(cmd)
    if vtt:   # sidecar: the written edition, fiction-labelled in its name and its first NOTE
        shutil.copy(vtt, dst[:-4] + ".written-fiction.vtt")


def subtitle_streams(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "s", "-show_entries", "stream=index,codec_name:stream_disposition=default:stream_tags",
             "-of", "json", path])
    return json.loads(r.stdout).get("streams", [])


def silent_check(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a", "-f", "s16le", "-ac", "2", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, np.int16)
    return {"decoded_samples_per_channel": len(x) // 2, "max_abs_sample": int(np.abs(x).max()) if len(x) else 0}


def main():
    sha = json.load(open(os.path.join(OUT, "master.sha1.json")))
    rev = sha["revision"]
    for v in ("A", "B"):
        txt = open(os.path.join(SW, f"sound-{v}", f"{v}.vtt"), encoding="utf-8").read()
        assert "NOTE FICTION" in txt, v
        open(os.path.join(OUT, f"{v}.vtt"), "w", encoding="utf-8").write(drop_crossover_if_unspoken(txt, v))
    write_x_vtt()
    mhead, mrows = master_rows()
    mfresh_head, mfresh = framemd5(MASTER)
    rep = {"master_revision": rev, "master": {"path": "out/master.mp4", "frames": len(mrows), "dimensions": mhead.get("dimensions 0"),
                                              "timebase": mhead.get("tb 0"), "streams": probe(MASTER),
                                              "framemd5_recomputed_equals_stored": mfresh == mrows},
           "editions": {}, "negative_controls": {}}
    mixrep = json.load(open(os.path.join(OUT, "mix.json")))
    for ed in ("A", "B", "X", "C", "silent"):
        dst = os.path.join(OUT, "control-silent.mp4" if ed == "silent" else f"edition-{ed}.mp4")
        vtt = os.path.join(OUT, CAPS[ed]) if CAPS[ed] else None
        attach(ed, os.path.join(FILMS, mixrep["editions"][ed]["wav"]), vtt, dst)
        head, rows = framemd5(dst)
        c = compare(rows, mrows)
        c.update({"path": os.path.relpath(dst, SW), "dimensions": head.get("dimensions 0"), "timebase": head.get("tb 0"),
                  "subtitle_streams": subtitle_streams(dst),
                  "written_edition_sidecar": os.path.relpath(dst[:-4] + ".written-fiction.vtt", SW) if vtt else None,
                  "streams": probe(dst), "bytes": os.path.getsize(dst)})
        if ed == "silent":
            c["audio"] = silent_check(dst)
            c["audio"]["digital_zero"] = c["audio"]["max_abs_sample"] == 0
        else:
            I, tp, lra = ebur128(dst)
            c["audio"] = {"integrated_lufs_aac": I, "true_peak_dbtp_aac": tp, "lra_lu": lra,
                          "pass": abs(I + 23.0) <= 0.5 and tp is not None and tp <= -1.0}
            mixrep["editions"][ed]["integrated_lufs_final_mp4"] = I
            mixrep["editions"][ed]["true_peak_dbtp_final_mp4"] = tp
        if not c["pass"]:
            os.makedirs(QUAR, exist_ok=True); shutil.move(dst, os.path.join(QUAR, os.path.basename(dst)))
            c["quarantined"] = True
        rep["editions"][ed] = c
        print(ed, c["match"], "/", c["of"], c.get("audio"))
    mixrep["A_minus_B_lu_final_mp4"] = round(mixrep["editions"]["A"]["integrated_lufs_final_mp4"] - mixrep["editions"]["B"]["integrated_lufs_final_mp4"], 2)
    json.dump(mixrep, open(os.path.join(OUT, "mix.json"), "w"), indent=1)
    # negative controls: both must FAIL, then are deleted
    tmpd = os.path.join(ED, "negctl"); os.makedirs(tmpd, exist_ok=True)
    wavB = os.path.join(FILMS, mixrep["editions"]["B"]["wav"])
    shift = os.path.join(tmpd, "B-shift1.mp4")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-itsoffset", "0.041667", "-i", MASTER, "-i", wavB, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", shift])
    drop = os.path.join(tmpd, "B-drop0.mp4")   # frame 0 dropped (stream copy cannot drop a single frame, so this re-encodes)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", MASTER, "-i", wavB, "-map", "0:v", "-map", "1:a",
         "-vf", "trim=start_frame=1,setpts=PTS-STARTPTS", "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", drop])
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    burn = os.path.join(tmpd, "B-burned.mp4")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", MASTER, "-i", wavB, "-map", "0:v", "-map", "1:a",
         "-vf", f"drawtext=fontfile={font}:text='Fenêtre suivante.':x=(w-tw)/2:y=h-48:fontsize=24:fontcolor=white:enable='between(n,384,623)',"
                "drawbox=x=920:y=16:w=14:h=14:color=red@1:t=fill:enable='between(n,384,623)'",
         "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-tune", "animation", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", burn])
    for name, p, what in (("one_frame_shift", shift, "B muxed with the video delayed one frame (-itsoffset 1/24, stream copy)"),
                          ("frame0_dropped", drop, "B with frame 0 dropped (re-encoded)"),
                          ("burned_caption", burn, "B with a caption and a red REC mark burned into frames 384-623 (re-encoded)")):
        head, rows = framemd5(p)
        c = compare(rows, mrows)
        hash_only = sum(1 for a, b in zip(rows, mrows) if a[3] == b[3])
        if name == "burned_caption":
            c["frames_384_623_hash_equal"] = sum(1 for k, (a, b) in enumerate(zip(rows, mrows)) if 384 <= k <= 623 and a[3] == b[3])
        c.update({"what": what, "md5_only_matches": hash_only, "expected": "FAIL", "result": "PASS" if c["pass"] else "FAIL",
                  "control_ok": not c["pass"], "deleted": True})
        rep["negative_controls"][name] = c
        os.remove(p)
        print("negative control", name, c["match"], "/", c["of"], c["result"])
    os.rmdir(tmpd)
    req = ("A", "B", "X", "silent")
    rep["required_editions_720_of_720"] = all(rep["editions"][e]["pass"] for e in req)
    rep["all_editions_720_of_720"] = all(v["pass"] for v in rep["editions"].values())
    rep["negative_controls_all_fail"] = all(v["control_ok"] for v in rep["negative_controls"].values())
    rep["comparison"] = "each decoded frame's (pts, duration, size, md5) from ffmpeg -f framemd5 must equal the master's, in order, 720/720"
    # repair 1: blind screening sequences for fresh viewers: silent control first, then A and B unlabelled,
    # no captions at all (so a reading can only come from sound), plus the B-first counterpart
    rep["screening"] = {}
    for tag, order in (("S-A-B", ("silent", "A", "B")), ("S-B-A", ("silent", "B", "A"))):
        lst = os.path.join(ED, f"concat-{tag}.txt")
        dst = os.path.join(OUT, f"screening-{tag}.mp4")
        parts = []
        for e in order:
            p = os.path.join(ED, f"scr-{e}.mp4")
            if not os.path.exists(p):
                run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", MASTER, "-i", os.path.join(FILMS, mixrep["editions"][e]["wav"]),
                     "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", p])
            parts.append(p)
        open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", dst])
        head, rows = framemd5(dst)
        segs = [{"match": sum(1 for a, b in zip(rows[i * 720:(i + 1) * 720], mrows) if a[2:] == b[2:])} for i in range(3)]   # size+md5 (pts run on)
        rep["screening"][tag] = {"path": os.path.relpath(dst, SW), "order": list(order), "captions": None,
                                 "segments_720_of_720": [x["match"] for x in segs], "frames": len(rows), "bytes": os.path.getsize(dst),
                                 "note": "90 s blind sequence: silent control, then two unlabelled passes; md5 per frame equal to the master in each segment"}
        os.remove(lst)
        print("screening", tag, [x["match"] for x in segs])
    for e in ("silent", "A", "B"):
        p = os.path.join(ED, f"scr-{e}.mp4")
        if os.path.exists(p): os.remove(p)
    json.dump(rep, open(os.path.join(OUT, "identity-report.json"), "w"), indent=1)
    print("identity:", rep["all_editions_720_of_720"], "neg controls fail:", rep["negative_controls_all_fail"])


if __name__ == "__main__":
    main()
