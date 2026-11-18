#!/usr/bin/env python3
"""validate.py — frozen-pool validator for La Machine a tuer le temps (SCION 27 / 54).

Subcommands (all exit 0 on pass, 1 on fail; JSON report on stdout):

  manifest [--deep]            recompute pool_hash from pool-manifest.json; with --deep also
                               re-hash every master TIFF (sha256) and every asset PNG (md5 of RGB24)
  recipe RECIPES.json [--full-pool EDIT_ID ...] [--sound SOUND.json]
                               check typed preconditions (plan §4) of every PictureEdit
  ledger LEDGER.json [--recipes RECIPES.json] [--frames DIR]
                               check a render ledger: every cut frame's md5 is the pool's
                               frame_md5[asset][src]; notebook print appearances are
                               translation-only at one uniform scale; optionally the cut
                               sequence equals the expanded recipe; optionally the real
                               rendered frames (DIR/NNNN.png) hash to the ledger md5
  fixture                      §8 verification fixture incl. must-fail cases
  framemd5 A.mp4 B.mp4 [--expect-audio-differs]
                               ffmpeg framemd5 of the video streams must be identical
  all                          manifest + fixture

Data contracts
--------------
PictureEdit (in RECIPES.json, either {"edits":[...]} or {"A1":{...},...} or a list):
  {"edit_id": "B1", "base_pool_hash": "...", "events": [
     {"asset_id": "05", "in": 0, "out": 59, "direction": "fwd", "speed": 0.5, "out_frames": 120}, ...]}
  ("asset" is accepted as an alias of "asset_id"; "src_in"/"src_out" of in/out.)
Expansion (deterministic, integer frames): n_src = |out-in|+1, step = +1 fwd / -1 rev,
  out_frames = round(n_src/speed), src_k = in + step*floor(k*speed), k = 0..out_frames-1.
Ledger (LEDGER.json, either a list or {"ledger":[...]}), one entry per output frame:
  cut frame:      {"frame": 870, "segment": "S7", "edit_id": "B1", "asset_id": "05", "src_frame": 0, "md5": "..."}
  notebook frame: {"frame": 700, "segment": "S5", "asset_id": "notebook",
                   "prints": [{"asset_id": "05", "dx": 253.19, "dy": 105.84, "scale": 0.2101,
                               "rot": 0, "print_md5": "<md5 of the frozen toned card print at that scale>"}]}
  md5 = md5 of the frame's RGB24 bytes (1280x720x3, row-major) == ffmpeg -pix_fmt rgb24 framemd5.
"""
import hashlib, json, math, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "pool-manifest.json")
FILMS = os.path.abspath(os.path.join(HERE, "..", ".."))
DIRS = {"fwd", "rev"}
SPEEDS = {0.5, 1, 1.0, 2, 2.0}


# ----------------------------------------------------------------- manifest
def load_manifest(path=MANIFEST):
    with open(path) as f:
        return json.load(f)


def canonical(man):
    """The hashed object: sorted assets with source_sha256, print_op, window_path, frame_md5."""
    assets = []
    for a in sorted(man["assets"], key=lambda a: a["asset_id"]):
        assets.append({"asset_id": a["asset_id"], "source_sha256": a["source_sha256"],
                       "print_op": a["print_op"], "window_path": a["window_path"],
                       "frame_md5": a["frame_md5"]})
    obj = {"slug": man["slug"], "N": man["N"], "size": man["size"],
           "print_op": man["print_op"], "assets": assets}
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def pool_hash(man):
    return hashlib.sha256(canonical(man).encode()).hexdigest()


def pool_index(man):
    return {a["asset_id"]: a["frame_md5"] for a in man["assets"]}


def rgb_md5_png(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    return hashlib.md5(im.tobytes()).hexdigest()


def cmd_manifest(argv):
    man = load_manifest()
    errs = []
    ph = pool_hash(man)
    if ph != man["pool_hash"]:
        errs.append(f"pool_hash mismatch: recorded {man['pool_hash']} computed {ph}")
    for a in man["assets"]:
        if len(a["frame_md5"]) != man["N"]:
            errs.append(f"{a['asset_id']}: {len(a['frame_md5'])} frame md5 != N")
        W0, W1 = a["window_path"]["W0"], a["window_path"]["W1"]
        cb = a["clean_bounds"]
        for nm, W in (("W0", W0), ("W1", W1)):
            if not (cb[0] - 1e-6 <= W[0] < W[2] <= cb[2] + 1e-6 and cb[1] - 1e-6 <= W[1] < W[3] <= cb[3] + 1e-6):
                errs.append(f"{a['asset_id']} {nm} outside clean bounds")
            if abs((W[2] - W[0]) / (W[3] - W[1]) - 16 / 9) > 1e-3:
                errs.append(f"{a['asset_id']} {nm} not 16:9")
    deep = {}
    if "--deep" in argv:
        for a in man["assets"]:
            src = os.path.join(FILMS, a["local_path"])
            h = hashlib.sha256()
            with open(src, "rb") as f:
                for b in iter(lambda: f.read(1 << 20), b""):
                    h.update(b)
            if h.hexdigest() != a["source_sha256"]:
                errs.append(f"{a['asset_id']}: source sha256 changed")
            d = os.path.join(FILMS, a["frame_dir"])
            bad = [i for i in range(man["N"]) if rgb_md5_png(os.path.join(d, f"{i:04d}.png")) != a["frame_md5"][i]]
            if bad:
                errs.append(f"{a['asset_id']}: {len(bad)} PNG frames differ from frame_md5 (first {bad[0]})")
            deep[a["asset_id"]] = "ok" if not bad else f"{len(bad)} bad"
    return {"check": "manifest", "pool_hash": ph, "deep": deep or None, "errors": errs}


# ------------------------------------------------------------------- recipe
def _edits(obj):
    if isinstance(obj, list):
        return obj
    if "edits" in obj:
        e = obj["edits"]
        return e if isinstance(e, list) else [dict(v, edit_id=v.get("edit_id", k)) for k, v in e.items()]
    if "events" in obj:
        return [obj]
    return [dict(v, edit_id=v.get("edit_id", k)) for k, v in obj.items() if isinstance(v, dict) and "events" in v]


def _ev(e):
    return (e.get("asset_id", e.get("asset")), e.get("in", e.get("src_in")), e.get("out", e.get("src_out")),
            e.get("direction", "fwd"), e.get("speed", 1), e.get("out_frames"))


def expand(ev):
    aid, i0, i1, d, sp, n = _ev(ev)
    step = 1 if d == "fwd" else -1
    return [(aid, i0 + step * math.floor(k * sp)) for k in range(n)]


def check_edit(ed, man, full_pool=False):
    errs = []
    N = man["N"]
    pool = pool_index(man)
    eid = ed.get("edit_id", "?")
    if ed.get("base_pool_hash") != man["pool_hash"]:
        errs.append(f"{eid}: base_pool_hash {ed.get('base_pool_hash')} != pool_hash")
    total = 0
    for k, e in enumerate(ed.get("events", [])):
        aid, i0, i1, d, sp, n = _ev(e)
        tag = f"{eid}[{k}]"
        if aid not in pool:
            errs.append(f"{tag}: asset {aid!r} not in pool")
        for nm, v in (("in", i0), ("out", i1)):
            if not isinstance(v, int) or isinstance(v, bool) or not (0 <= v <= N - 1):
                errs.append(f"{tag}: {nm}={v!r} outside 0..{N-1}")
        if d not in DIRS:
            errs.append(f"{tag}: direction {d!r} not in {sorted(DIRS)}")
        if sp not in SPEEDS:
            errs.append(f"{tag}: speed {sp!r} not in {{0.5,1,2}}")
        if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
            errs.append(f"{tag}: out_frames={n!r} not a positive int")
            continue
        if isinstance(i0, int) and isinstance(i1, int) and sp in SPEEDS:
            want = round((abs(i1 - i0) + 1) / sp)
            if n != want:
                errs.append(f"{tag}: out_frames {n} != round((|out-in|+1)/speed) = {want}")
            if d == "fwd" and i1 < i0 or d == "rev" and i1 > i0:
                errs.append(f"{tag}: direction {d} contradicts in={i0} out={i1}")
            if not errs or all(not x.startswith(tag) for x in errs):
                for a2, s in expand(e):
                    if not (0 <= s <= N - 1):
                        errs.append(f"{tag}: expands to off-pool frame {s}")
                        break
        if "md5" in e or "frame_md5" in e:  # an event that brings its own pixels must resolve
            for m in (e.get("md5") or e.get("frame_md5") or []):
                if aid in pool and m not in pool[aid]:
                    errs.append(f"{tag}: md5 {m} not in pool frame_md5[{aid}]")
        total += n
    if "total_frames" in ed and ed["total_frames"] != total:
        errs.append(f"{eid}: total_frames {ed['total_frames']} != sum(out_frames) {total}")
    if full_pool:
        ids = sorted(_ev(e)[0] for e in ed.get("events", []))
        if ids != sorted(pool):
            errs.append(f"{eid}: asset multiset {ids} != pool {sorted(pool)} (each once)")
    return {"edit_id": eid, "frames": total, "errors": errs}


def cmd_recipe(argv):
    man = load_manifest()
    path = argv[0]
    full = set()
    if "--full-pool" in argv:
        i = argv.index("--full-pool") + 1
        while i < len(argv) and not argv[i].startswith("--"):
            full.add(argv[i]); i += 1
    obj = json.load(open(path))
    eds = _edits(obj)
    res = [check_edit(e, man, e.get("edit_id") in full) for e in eds]
    errs = [x for r in res for x in r["errors"]]
    if "--sound" in argv:
        snd = json.load(open(argv[argv.index("--sound") + 1]))
        byid = {e.get("edit_id"): e for e in eds}
        for c in snd.get("cues", []):
            dep = c.get("sync_dep", "none")
            if dep in (None, "none"):
                continue
            eid, idx = (dep.get("edit_id"), dep.get("event")) if isinstance(dep, dict) else (c.get("edit_id"), dep)
            if eid in byid and not (isinstance(idx, int) and 0 <= idx < len(byid[eid]["events"])):
                errs.append(f"cue {c.get('id', c)}: sync_dep {dep} does not name an event of {eid}")
    return {"check": "recipe", "edits": res, "errors": errs}


# ------------------------------------------------------------------- ledger
def check_ledger(entries, man, recipes=None, frames_dir=None):
    pool = pool_index(man)
    N = man["N"]
    errs = []
    scale = {}
    pmd5 = {}
    cut_seq = {}
    n_cut = n_nb = 0
    for e in entries:
        f = e.get("frame")
        aid = e.get("asset_id")
        if aid == "notebook" or e.get("segment_kind") == "notebook" or "prints" in e:
            n_nb += 1
            for p in e.get("prints", []):
                pa = p.get("asset_id")
                if pa not in pool:
                    errs.append(f"frame {f}: notebook print {pa!r} not in pool")
                    continue
                if p.get("rot", 0) not in (0, 0.0):
                    errs.append(f"frame {f}: print {pa} rotated ({p['rot']}) — translation only")
                for bad in ("shear", "warp", "tint", "crop"):
                    if p.get(bad):
                        errs.append(f"frame {f}: print {pa} has {bad} — translation only")
                s = p.get("scale")
                if s is not None:
                    if pa in scale and abs(scale[pa] - s) > 1e-9:
                        errs.append(f"frame {f}: print {pa} scale {s} != {scale[pa]} (uniform scale only)")
                    scale.setdefault(pa, s)
                m = p.get("print_md5")
                if m is not None:
                    if pa in pmd5 and pmd5[pa] != m:
                        errs.append(f"frame {f}: print {pa} pixels changed (print_md5 {m} != {pmd5[pa]})")
                    pmd5.setdefault(pa, m)
            continue
        n_cut += 1
        src = e.get("src_frame")
        if aid not in pool:
            errs.append(f"frame {f}: asset {aid!r} not in pool")
            continue
        if not isinstance(src, int) or not (0 <= src <= N - 1):
            errs.append(f"frame {f}: src_frame {src!r} outside 0..{N-1}")
            continue
        if e.get("md5") != pool[aid][src]:
            errs.append(f"frame {f}: md5 {e.get('md5')} != pool {aid}[{src}]")
        cut_seq.setdefault(e.get("edit_id") or e.get("segment"), []).append((f, aid, src))
        if frames_dir:
            fp = os.path.join(frames_dir, f"{f:04d}.png")
            if os.path.exists(fp) and rgb_md5_png(fp) != e.get("md5"):
                errs.append(f"frame {f}: rendered {fp} md5 != ledger md5")
    if recipes:
        for ed in _edits(recipes):
            eid = ed.get("edit_id")
            if eid not in cut_seq:
                continue
            want = [x for ev in ed["events"] for x in expand(ev)]
            got = [(a, s) for _, a, s in sorted(cut_seq[eid])]
            if got != want:
                k = next((i for i, (g, w) in enumerate(zip(got, want)) if g != w), min(len(got), len(want)))
                errs.append(f"{eid}: ledger sequence differs from recipe at cut frame {k} "
                            f"(got {got[k] if k < len(got) else None}, want {want[k] if k < len(want) else None}); "
                            f"len {len(got)} vs {len(want)}")
            fr = [f for f, _, _ in sorted(cut_seq[eid])]
            if fr and fr != list(range(fr[0], fr[0] + len(fr))):
                errs.append(f"{eid}: cut frames not contiguous")
            # repair round 1: the recipe's serialised film frames must equal where
            # the ledger actually places the cut and each of its events
            if fr and "film_start_frame" in ed and ed["film_start_frame"] != fr[0]:
                errs.append(f"{eid}: recipe film_start_frame {ed['film_start_frame']} != ledger first cut frame {fr[0]}")
            acc = fr[0] if fr else 0
            for i, ev in enumerate(ed["events"]):
                cps = [c for c in ed.get("cut_points", []) if c.get("event") == i]
                if fr and cps and "film_frame" in cps[0] and cps[0]["film_frame"] != acc:
                    errs.append(f"{eid}: cut_points[{i}].film_frame {cps[0]['film_frame']} != ledger frame {acc}")
                acc += ev["out_frames"]
    return {"cut_frames": n_cut, "notebook_frames": n_nb, "errors": errs}


def cmd_ledger(argv):
    man = load_manifest()
    obj = json.load(open(argv[0]))
    entries = obj["ledger"] if isinstance(obj, dict) else obj
    rec = json.load(open(argv[argv.index("--recipes") + 1])) if "--recipes" in argv else None
    fd = argv[argv.index("--frames") + 1] if "--frames" in argv else None
    r = check_ledger(entries, man, rec, fd)
    r["check"] = "ledger"
    return r


# ----------------------------------------------------------------- framemd5
def framemd5(path):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:v:0", "-pix_fmt", "rgb24",
                          "-f", "framemd5", "-"], capture_output=True, text=True, check=True).stdout
    return [ln.split(",")[-1].strip() for ln in out.splitlines() if ln and not ln.startswith("#")]


def audiomd5(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0?", "-f", "md5", "-"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def cmd_framemd5(argv):
    a, b = argv[0], argv[1]
    fa, fb = framemd5(a), framemd5(b)
    errs = []
    if len(fa) != len(fb):
        errs.append(f"frame count {len(fa)} != {len(fb)}")
    diff = [i for i, (x, y) in enumerate(zip(fa, fb)) if x != y]
    if diff:
        errs.append(f"{len(diff)} video frames differ (first {diff[0]})")
    res = {"check": "framemd5", "frames": [len(fa), len(fb)], "errors": errs}
    if "--expect-audio-differs" in argv:
        ma, mb = audiomd5(a), audiomd5(b)
        res["audio_md5"] = [ma, mb]
        if ma == mb:
            errs.append("audio streams identical but were expected to differ")
    return res


# ------------------------------------------------------------------ fixture
def _ev_full(aid, i0, i1, d="fwd", sp=1):
    return {"asset_id": aid, "in": i0, "out": i1, "direction": d, "speed": sp,
            "out_frames": round((abs(i1 - i0) + 1) / sp)}


def _ledger_for(ed, man, start=0):
    pool = pool_index(man)
    return [{"frame": start + k, "segment": "fx", "edit_id": ed["edit_id"], "asset_id": a, "src_frame": s,
             "md5": pool[a][s] if a in pool and 0 <= s < man["N"] else "0" * 32}
            for k, (a, s) in enumerate(x for ev in ed["events"] for x in expand(ev))]


def cmd_fixture(argv):
    man = load_manifest()
    ph = man["pool_hash"]
    A = {"edit_id": "A_fx", "base_pool_hash": ph,
         "events": [_ev_full(a, 0, 23) for a in ("01", "02", "04", "07")]}
    B = {"edit_id": "B_fx", "base_pool_hash": ph,
         "events": [_ev_full("07", 0, 23), _ev_full("04", 0, 23, sp=0.5), _ev_full("02", 23, 0, "rev"),
                    _ev_full("01", 0, 47, sp=2)]}
    X9 = json.loads(json.dumps(B)); X9["edit_id"] = "X9_insert"
    X9["events"].insert(2, _ev_full("X9", 0, 11))
    O130 = json.loads(json.dumps(A)); O130["edit_id"] = "out130"
    O130["events"][1].update({"out": 130, "out_frames": 131})
    BADN = json.loads(json.dumps(A)); BADN["edit_id"] = "bad_out_frames"; BADN["events"][0]["out_frames"] = 25
    STALE = json.loads(json.dumps(A)); STALE["edit_id"] = "stale_pool"; STALE["base_pool_hash"] = "0" * 64
    cases = []

    def case(name, expect_pass, res_errs):
        ok = (not res_errs) == expect_pass
        cases.append({"case": name, "expect": "pass" if expect_pass else "fail",
                      "got": "pass" if not res_errs else "fail", "ok": ok, "errors": res_errs[:3]})

    for ed in (A, B):
        case(f"recipe {ed['edit_id']} membership", True, check_edit(ed, man)["errors"])
        case(f"ledger {ed['edit_id']} resolves", True,
             check_ledger(_ledger_for(ed, man), man, {"edits": [ed]})["errors"])
    case("same multiset A_fx vs B_fx", True,
         [] if sorted(_ev(e)[0] for e in A["events"]) == sorted(_ev(e)[0] for e in B["events"]) else ["multiset differs"])
    case("X9 insert (asset not in pool)", False, check_edit(X9, man)["errors"])
    case("out = 130 (off-pool frame)", False, check_edit(O130, man)["errors"])
    case("out_frames inconsistent with in/out/speed", False, check_edit(BADN, man)["errors"])
    case("stale base_pool_hash", False, check_edit(STALE, man)["errors"])
    led = _ledger_for(B, man)
    led[5] = dict(led[5], md5="d41d8cd98f00b204e9800998ecf8427e")  # an off-pool frame (e.g. a red-tinted 05)
    case("ledger with an off-pool frame md5", False, check_ledger(led, man)["errors"])
    led2 = _ledger_for(A, man)
    led2.insert(10, {"frame": 10, "asset_id": "notebook",
                     "prints": [{"asset_id": "05", "dx": 1, "dy": 2, "scale": 0.2, "rot": 1.5}]})
    case("notebook print rotated", False, check_ledger(led2, man)["errors"])
    nb = [{"frame": i, "asset_id": "notebook",
           "prints": [{"asset_id": "05", "dx": 10 + 3 * i, "dy": 5, "scale": 0.21, "print_md5": "a" * 32}]} for i in range(4)]
    case("notebook print translated only", True, check_ledger(nb, man)["errors"])
    nb[2]["prints"][0]["scale"] = 0.25
    case("notebook print rescaled mid-move", False, check_ledger(nb, man)["errors"])
    # framemd5: two mp4s from the same pool frames, different audio stems
    try:
        fm = _fixture_mp4(man, A)
        case("audio-only swap keeps framemd5", True, fm["same"])
        case("picture change alters framemd5", False, fm["changed"])
    except Exception as ex:  # ffmpeg missing etc.
        case("framemd5 fixture ran", True, [f"could not run: {ex}"])
    errs = [f"{c['case']}: expected {c['expect']}, got {c['got']}" for c in cases if not c["ok"]]
    return {"check": "fixture", "pool_hash": ph, "cases": cases, "errors": errs}


def _fixture_mp4(man, ed):
    byid = {a["asset_id"]: a for a in man["assets"]}
    seq = [x for ev in ed["events"] for x in expand(ev)][:48]
    with tempfile.TemporaryDirectory() as td:
        for k, (a, s) in enumerate(seq):
            os.symlink(os.path.join(FILMS, byid[a]["frame_dir"], f"{s:04d}.png"), os.path.join(td, f"{k:04d}.png"))
        alt = os.path.join(td, "alt")
        os.mkdir(alt)
        for k, (a, s) in enumerate(seq):
            src = (a, s) if k != 20 else ("05", 0)  # one substituted frame
            os.symlink(os.path.join(FILMS, byid[src[0]]["frame_dir"], f"{src[1]:04d}.png"), os.path.join(alt, f"{k:04d}.png"))

        def mk(frames, aud, out):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", os.path.join(frames, "%04d.png"),
                            "-f", "lavfi", "-i", aud, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "ultrafast",
                            "-qp", "18", "-pix_fmt", "yuv420p", "-threads", "1", "-c:a", "aac", "-shortest", out], check=True)
        m1, m2, m3 = (os.path.join(td, n) for n in ("bed.mp4", "mix.mp4", "alt.mp4"))
        mk(td, "sine=frequency=440:duration=2", m1)
        mk(td, "anoisesrc=d=2:c=pink:a=0.1", m2)
        mk(alt, "sine=frequency=440:duration=2", m3)
        same = cmd_framemd5([m1, m2, "--expect-audio-differs"])["errors"]
        changed = cmd_framemd5([m1, m3])["errors"]
    return {"same": same, "changed": changed}


# --------------------------------------------------------------------- main
def main(argv):
    if not argv:
        print(__doc__); return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "all":
        res = [cmd_manifest(rest), cmd_fixture(rest)]
        out = {"check": "all", "results": res, "errors": [e for r in res for e in r["errors"]]}
    else:
        out = {"manifest": cmd_manifest, "recipe": cmd_recipe, "ledger": cmd_ledger,
               "fixture": cmd_fixture, "framemd5": cmd_framemd5}[cmd](rest)
    out["verdict"] = "PASS" if not out["errors"] else "FAIL"
    print(json.dumps(out, indent=1))
    return 0 if not out["errors"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
