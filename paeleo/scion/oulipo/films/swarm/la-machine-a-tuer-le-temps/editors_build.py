#!/usr/bin/env python3
"""editors_build.py — U3 cut-editors (SCION 27, declarative film compiler).

Compiles each PictureEdit (pure data, integer frames) against the frozen pool
(pool-manifest.json, pool_hash) into:
  sources/la-machine-a-tuer-le-temps/editors/<edit_id>.mp4        rough full-frame cut, no notebook, silent
  sources/la-machine-a-tuer-le-temps/cut-editors/<edit_id>/ledger.json   per-frame {frame, edit_id, event, asset_id, src_frame, md5}
  sources/la-machine-a-tuer-le-temps/cut-editors/<edit_id>/cuts.jpg      frame before/after every cut
  sources/la-machine-a-tuer-le-temps/cut-editors/<edit_id>/strip.jpg     one frame per 12 (on-twos-of-seconds strip)
  sources/la-machine-a-tuer-le-temps/cut-editors/<edit_id>/concat.txt    ffconcat list of the frozen PNGs (replayable)
Usage: python3 -I editors_build.py [render|json|all]
"""
import hashlib, json, math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import validate  # noqa: E402

MAN = validate.load_manifest()
POOL_HASH = MAN["pool_hash"]
SRC = os.path.join(FILMS, "sources", "la-machine-a-tuer-le-temps")
ED_DIR = os.path.join(SRC, "editors")
CE_DIR = os.path.join(SRC, "cut-editors")
ASSET_DIR = os.path.join(SRC, "registrar", "assets")
FPS = 24
ROLE = {a["asset_id"]: a["proof_role"] for a in MAN["assets"]}


def ev(aid, i0, i1, d="fwd", sp=1, why=""):
    n = round((abs(i1 - i0) + 1) / sp)
    return {"asset_id": aid, "role": ROLE[aid], "in": i0, "out": i1, "direction": d,
            "speed": sp, "out_frames": n, "why": why}


A1 = [ev("01", 0, 59, why="the station clock: the shift begins"),
      ev("02", 0, 71, why="a mail-room woman carries a parcel: work"),
      ev("03", 0, 59, why="a conductor checks his watch: timetable"),
      ev("04", 0, 59, why="a soldier at the carriage door: departures"),
      ev("05", 0, 47, why="a red cap, one face among staff"),
      ev("06", 0, 59, why="reservation slips at the counter"),
      ev("07", 0, 71, why="soldiers file out to the trains"),
      ev("08", 0, 47, why="the hall at 1 a.m.: end of shift")]

B1 = [ev("05", 0, 59, sp=0.5, why="long stare opens; look-out"),
      ev("04", 0, 47, why="what he watches: the door"),
      ev("02", 24, 95, why="her look back now answers his; parcel"),
      ev("06", 30, 101, why="the slip left behind, tighter in the push"),
      ev("03", 0, 59, why="someone is timing it"),
      ev("01", 119, 84, d="rev", why="the clock arrives late, pulling away (alibi)"),
      ev("07", 0, 59, why="the getaway"),
      ev("08", 0, 95, why="the empty hall held long")]

# B2: soundtrack fixed (shared bed / mix B unchanged), picture swaps 04<->02 so the stare lands
# on the parcel first and the door second. Each asset keeps its B1 in/out, so total stays 564.
B2 = [B1[0], B1[2], B1[1]] + B1[3:]
# B3: the 05 glance held 7.0 s (168 f) at half speed: src 0->83 (inside W0->W1, ends at zoom ~x1.21).
B3 = [ev("05", 0, 83, sp=0.5, why="glance held 7 s: the stare becomes surveillance")] + B1[1:]
# B4: B1 picture exactly; only the sound cue moves (door latch 12 f INTO 04 instead of 6 f before it).
B4 = list(B1)

EDITS = {
    "A1": {"role": "cut A (baseline, ordinary handoff), pool order 01..08", "events": A1},
    "B1": {"role": "cut B (the parcel seems illicit)", "events": B1},
    "B2-rev-adjacency": {"role": "fallback: 04<->02 swapped (05->02->04), soundtrack fixed", "events": B2},
    "B3-glance-hold": {"role": "fallback: 05 glance held 7.0 s", "events": B3},
    "B4-delayed-cue": {"role": "fallback: B1 picture, door-latch cue delayed 12 f into 04 (sound unit)",
                       "events": B4, "picture_identical_to": "B1"},
}


def expand(events):
    out = []
    for k, e in enumerate(events):
        for a, s in validate.expand(e):
            out.append((k, a, s))
    return out


def recipe_obj(eid, spec):
    evs = spec["events"]
    t = 0
    cuts = []
    for k, e in enumerate(evs):
        cuts.append({"event": k, "asset_id": e["asset_id"], "start_frame": t,
                     "start_tc": f"{t / FPS:.3f}s", "out_frames": e["out_frames"],
                     "seconds": round(e["out_frames"] / FPS, 3)})
        t += e["out_frames"]
    o = {"edit_id": eid, "base_pool_hash": POOL_HASH, "role": spec["role"],
         "events": evs, "total_frames": t, "seconds": round(t / FPS, 3), "cut_points": cuts}
    if "picture_identical_to" in spec:
        o["picture_identical_to"] = spec["picture_identical_to"]
    return o


def md5_index():
    return {a["asset_id"]: a["frame_md5"] for a in MAN["assets"]}


def render(eid, spec):
    from PIL import Image, ImageDraw
    seq = expand(spec["events"])
    d = os.path.join(CE_DIR, eid)
    os.makedirs(d, exist_ok=True)
    os.makedirs(ED_DIR, exist_ok=True)
    idx = md5_index()
    ledger = []
    for f, (k, a, s) in enumerate(seq):
        ledger.append({"frame": f, "segment": "cut", "edit_id": eid, "event": k,
                       "asset_id": a, "src_frame": s, "md5": idx[a][s]})
    json.dump({"edit_id": eid, "base_pool_hash": POOL_HASH, "ledger": ledger},
              open(os.path.join(d, "ledger.json"), "w"), indent=0)
    # ffconcat list of the frozen PNGs, one entry per output frame
    with open(os.path.join(d, "concat.txt"), "w") as fh:
        fh.write("ffconcat version 1.0\n")
        for _, a, s in seq:
            fh.write(f"file '{os.path.join(ASSET_DIR, a, f'{s:04d}.png')}'\nduration {1 / FPS:.10f}\n")
        _, a, s = seq[-1]
        fh.write(f"file '{os.path.join(ASSET_DIR, a, f'{s:04d}.png')}'\n")
    # verify every frame pixel by pixel against the manifest (md5 of RGB24) — unique files only
    seen = {}
    for _, a, s in seq:
        if (a, s) not in seen:
            p = os.path.join(ASSET_DIR, a, f"{s:04d}.png")
            seen[(a, s)] = validate.rgb_md5_png(p) == idx[a][s]
    bad = [k for k, ok in seen.items() if not ok]
    out = os.path.join(ED_DIR, f"{eid}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i",
                    os.path.join(d, "concat.txt"), "-frames:v", str(len(seq)), "-r", str(FPS),
                    "-fps_mode", "cfr", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
    n = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                            "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", out],
                           capture_output=True, text=True).stdout.strip())
    # review sheets (editor's working media, not film frames)
    tw, th = 320, 180

    def thumb(a, s):
        return Image.open(os.path.join(ASSET_DIR, a, f"{s:04d}.png")).convert("RGB").resize((tw, th))
    starts = [c["start_frame"] for c in recipe_obj(eid, spec)["cut_points"]]
    pairs = [(starts[i] - 1, starts[i]) for i in range(1, len(starts))]
    sheet = Image.new("RGB", (tw * 2 + 30, (th + 22) * len(pairs) + 10), (236, 229, 213))
    dr = ImageDraw.Draw(sheet)
    for r, (f0, f1) in enumerate(pairs):
        y = 5 + r * (th + 22)
        for c, f in enumerate((f0, f1)):
            k, a, s = seq[f]
            sheet.paste(thumb(a, s), (10 + c * (tw + 10), y))
            dr.text((10 + c * (tw + 10), y + th + 3), f"{eid} f{f} ({f / FPS:.2f}s) ev{k} {a}[{s}]", fill=(66, 58, 47))
    sheet.save(os.path.join(d, "cuts.jpg"), quality=85)
    step = 12
    fr = list(range(0, len(seq), step))
    cols = 10
    rows = math.ceil(len(fr) / cols)
    sw, sh = 160, 90
    strip = Image.new("RGB", (cols * sw, rows * (sh + 14)), (236, 229, 213))
    ds = ImageDraw.Draw(strip)
    for i, f in enumerate(fr):
        k, a, s = seq[f]
        x, y = (i % cols) * sw, (i // cols) * (sh + 14)
        strip.paste(thumb(a, s).resize((sw - 4, sh)), (x + 2, y))
        ds.text((x + 4, y + sh + 1), f"{f / FPS:4.1f}s {a}", fill=(66, 58, 47))
    strip.save(os.path.join(d, "strip.jpg"), quality=85)
    return {"mp4": os.path.relpath(out, FILMS), "frames_rendered": n, "frames_expected": len(seq),
            "pool_md5_mismatches": [f"{a}[{s}]" for a, s in bad],
            "mp4_sha256": hashlib.sha256(open(out, "rb").read()).hexdigest(),
            "ledger": os.path.relpath(os.path.join(d, "ledger.json"), FILMS),
            "cuts_sheet": os.path.relpath(os.path.join(d, "cuts.jpg"), FILMS),
            "strip_sheet": os.path.relpath(os.path.join(d, "strip.jpg"), FILMS)}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    res = {}
    if mode in ("render", "all"):
        for eid, spec in EDITS.items():
            if eid == "B4-delayed-cue":
                continue
            res[eid] = render(eid, spec)
            print(eid, res[eid]["frames_rendered"], res[eid]["frames_expected"], res[eid]["pool_md5_mismatches"])
        json.dump(res, open(os.path.join(CE_DIR, "render-record.json"), "w"), indent=1)
    if mode in ("json", "all"):
        recs = {eid: recipe_obj(eid, spec) for eid, spec in EDITS.items()}
        json.dump({"edits": list(recs.values())}, open(os.path.join(CE_DIR, "recipes-only.json"), "w"), indent=1)
        print(json.dumps({k: (v["total_frames"], v["seconds"]) for k, v in recs.items()}))
