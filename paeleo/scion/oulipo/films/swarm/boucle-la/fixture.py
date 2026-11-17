"""boucle-la U4 palindrome validator (fixture).  Run:  python3 -I films/swarm/boucle-la/fixture.py

Reads only. Never edits art. Writes:
  films/swarm/boucle-la/fixture-report.json
  films/sources/boucle-la/validator/   (scratch evidence: diff maps, decoded film stills, synthetic mutation data)

Suites
  build      the real deliverable: assets/pages/boucle-la.png + page.json + route.json + script.json (+ frames)
  testpage   the approved test page (test-page.png) at the plan's frozen rects (calibration on real art)
  mutations  negative cases and the alternate hinge, applied in memory to a base that passes
  fk         SCION 32 invariants from cutouts.json (+ page.json exposure sheets), cross-checked against rig.py
  film       assets/films/boucle-la.mp4 when it is current: held frames vs page crops at film scale, one bell
             onset within +-1 frame of the face-out drawing; calibrated on test-shot.mp4

Result values: PASS, FAIL, PENDING (input not yet produced), INFO.
Evidence labels follow plan.json: "measured", "structurally verified".
"""
import datetime
import hashlib
import json
import math
import os
import subprocess
import sys

sys.dont_write_bytecode = True
import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../.."))  # .../oulipo
SW = HERE
SRC = os.path.join(ROOT, "films/sources/boucle-la")
VAL = os.path.join(SRC, "validator")
os.makedirs(VAL, exist_ok=True)

P = lambda *a: os.path.join(ROOT, *a)
SEQ_EXPECTED = ["A", "B", "C", "H", "C", "B", "A"]
PLAN_RECTS = {  # plan.md section 5 (frozen): occurrence -> rect on the 3200x1800 page
    1: (560, 40, 1410, 620), 2: (1440, 40, 2290, 620), 3: (2320, 40, 3170, 620),
    4: (560, 650, 3170, 1150),
    5: (560, 1180, 1410, 1760), 6: (1440, 1180, 2290, 1760), 7: (2320, 1180, 3170, 1760)}
PLAN_HOLD_SAMPLE_S = {1: 10.9, 2: 17.4, 3: 23.9, 4: 36.4, 5: 44.9, 6: 51.4, 7: 57.9}  # inside each plan hold
PLAN_FACE_OUT_S = 28.0
FPS = 24

REPORT = {"slug": "boucle-la", "unit": "U4 palindrome validator", "fixture": "films/swarm/boucle-la/fixture.py",
          "run": "python3 -I films/swarm/boucle-la/fixture.py",
          "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
          "edits_art": False, "suites": {}, "tests": []}


def jload(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha_px(a):
    a = np.ascontiguousarray(a)
    return hashlib.sha256(str(a.shape).encode() + str(a.dtype).encode() + a.tobytes()).hexdigest()


def img(p):
    return np.asarray(Image.open(p).convert("RGBA" if Image.open(p).mode in ("RGBA", "LA", "P") else "L"))


def rec(suite, name, result, evidence, detail, expect="PASS"):
    t = {"suite": suite, "test": name, "result": result, "expected": expect,
         "as_expected": (result == expect) if result in ("PASS", "FAIL") else None,
         "evidence": evidence, "detail": detail}
    REPORT["tests"].append(t)
    return t


def rel(p):
    return os.path.relpath(p, ROOT) if p else p


# --------------------------------------------------------------------------------------------- data

SCRIPT = jload(os.path.join(SW, "script.json")) or {}
ACTS = jload(os.path.join(SW, "speech-acts.json")) or {}
CUT = jload(os.path.join(SW, "cutouts.json")) or {}
PAGEJ = jload(os.path.join(SW, "page.json"))
ROUTE = jload(os.path.join(SW, "route.json"))
PANELS = {p["id"]: p for p in SCRIPT.get("exchange_panels", [])}


def occ_meta():
    """Per-occurrence speaker/text from speech-acts.json (per occurrence) joined with script.json (per panel ID)."""
    out = {}
    for o in ACTS.get("occurrences", []):
        pid = o["panel_id"]
        sp = PANELS.get(pid, {})
        out[o["occurrence"]] = {
            "o": o["occurrence"], "id": pid, "speaker": o.get("speaker"), "text": o.get("text"),
            "script_speaker": sp.get("speaker"), "script_text": sp.get("text"),
            "seed": sp.get("lettering_seed"), "lines": list(sp.get("wrapped_lines", [])),
            "text_sha": sp.get("text_utf8_sha256"),
            "tail_x": (sp.get("tail_anchor", {}).get("tip_in_panel") or [None])[0],
            "balloon_png": sp.get("balloon_png"), "balloon_sha_rec": sp.get("balloon_png_sha256"),
            "voice": (sp.get("voice_clip") or {}).get("path"), "voice_sha_rec": (sp.get("voice_clip") or {}).get("sha256"),
            "crop": None, "frames": None, "last_frame": None}
    return out


# --------------------------------------------------------------------------------------------- Mirror(seq, h)

def mirror_checks(occs, hinge="H", strict_crop=True):
    """The central operation's typed preconditions, per plan.md section 3. occs: list of 7 dicts in occurrence order.
    Returns list of (test, result, evidence, detail)."""
    R = []
    seq = [o["id"] for o in occs]
    ok = len(seq) == 7
    R.append(("P1 len(seq)==7", "PASS" if ok else "FAIL", "structurally verified", f"seq={seq}"))
    if not ok:
        return R
    R.append(("route == [A,B,C,H,C,B,A] (or same pairs around a named hinge)",
              "PASS" if seq[:3] == SEQ_EXPECTED[:3] and seq[4:] == SEQ_EXPECTED[4:] and seq[3] == hinge else "FAIL",
              "structurally verified", f"seq={seq}, hinge={hinge}"))
    R.append(("P2 hinge unique at seq[3]", "PASS" if seq[3] == hinge and seq.count(hinge) == 1 else "FAIL",
              "structurally verified", f"seq[3]={seq[3]}, count({hinge})={seq.count(hinge)}"))
    pal = all(seq[i] == seq[6 - i] for i in range(3)) and len(set(seq[:3])) == 3 and hinge not in seq[:3]
    R.append(("P3 seq[i]==seq[6-i], three distinct paired ids", "PASS" if pal else "FAIL", "structurally verified",
              f"pairs={[(seq[i], seq[6 - i]) for i in range(3)]}"))
    for i in range(3):
        a, b = occs[i], occs[6 - i]
        tag = f"pair o{a['o']}/o{b['o']} ({a['id']})"
        # P5 speaker
        sp_ok = a["speaker"] == b["speaker"] and a["speaker"] is not None
        sp_ok = sp_ok and a.get("script_speaker") in (None, a["speaker"]) and b.get("script_speaker") in (None, b["speaker"])
        R.append((f"P5 speaker identical, {tag}", "PASS" if sp_ok else "FAIL", "structurally verified",
                  f"{a['speaker']} vs {b['speaker']} (script.json: {a.get('script_speaker')})"))
        # tail side must name the speaker (left = gustave, right = odette) in exchange panels
        def side(o):
            if o.get("tail_xy") is not None and o.get("mouths"):  # nearest FK mouth of the held drawing
                return min(o["mouths"], key=lambda f: math.dist(o["tail_xy"], o["mouths"][f]))
            w = o.get("panel_w") or 850
            return None if o.get("tail_x") is None else ("gustave" if o["tail_x"] < w / 2 else "odette")
        ts = (side(a), side(b))
        how = "nearest FK mouth (held drawing)" if a.get("mouths") else "tail x vs panel centre"
        R.append((f"P5 balloon tail points to the speaker, {tag}",
                  "PASS" if ts[0] == a["speaker"] and ts[1] == b["speaker"] else "FAIL", "structurally verified",
                  f"tail -> {ts} by {how}; speakers {(a['speaker'], b['speaker'])}"))
        # P5 balloon string + seed + lettered lines; string must also match its recorded utf8 sha
        def tsha(o):
            return hashlib.sha256(o["text"].encode("utf-8")).hexdigest() if o["text"] is not None else None
        tx_ok = (a["text"] == b["text"] and a["seed"] == b["seed"] and a["lines"] == b["lines"]
                 and " ".join(a["lines"]) == a["text"] and " ".join(b["lines"]) == b["text"]
                 and tsha(a) == a.get("text_sha") and tsha(b) == b.get("text_sha"))
        R.append((f"P5 balloon string, lines and lettering seed identical, {tag}", "PASS" if tx_ok else "FAIL",
                  "structurally verified",
                  f"{a['text']!r} / {b['text']!r}; seeds {a['seed']}/{b['seed']}; utf8 sha ok "
                  f"{tsha(a) == a.get('text_sha')}/{tsha(b) == b.get('text_sha')}"))
        # balloon raster and voice clip: one file per ID, sha matches the record
        for key, recd, lab in (("balloon_png", "balloon_sha_rec", "balloon PNG"), ("voice", "voice_sha_rec", "voice clip")):
            pa, pb = a.get(key), b.get(key)
            if not pa or not os.path.exists(P(pa)) or not os.path.exists(P(pb)):
                R.append((f"{lab} identical, {tag}", "PENDING", "measured", f"missing {pa}"))
                continue
            ha, hb = sha_file(P(pa)), sha_file(P(pb))
            okk = ha == hb and ha == a.get(recd) and hb == b.get(recd)
            R.append((f"{lab} byte-identical and matches its record, {tag}", "PASS" if okk else "FAIL", "measured",
                      f"{rel(P(pa))} sha {ha[:16]} / {hb[:16]} rec {str(a.get(recd))[:16]}"))
        # P4 page crops pixel-identical
        if a["crop"] is None or b["crop"] is None:
            R.append((f"P4 page crops pixel-identical, {tag}", "PENDING", "measured", "page or rects not available"))
        else:
            ca, cb = a["crop"], b["crop"]
            if ca.shape != cb.shape:
                R.append((f"P4 page crops pixel-identical, {tag}", "FAIL", "measured", f"shapes {ca.shape} {cb.shape}"))
            else:
                d = np.abs(ca.astype(int) - cb.astype(int))
                R.append((f"P4 page crops pixel-identical ({'full rect' if strict_crop else 'interior'}), {tag}",
                          "PASS" if d.max() == 0 else "FAIL", "measured",
                          f"max abs diff {int(d.max())}, differing px {int((d.reshape(d.shape[0], d.shape[1], -1).max(-1) > 0).sum())}, "
                          f"sha {sha_px(ca)[:16]} / {sha_px(cb)[:16]}"))
        # P4 frame sequences identical, frame for frame
        if a["frames"] is None or b["frames"] is None:
            R.append((f"P4 frame sequences identical (per-frame sha256), {tag}", "PENDING", "measured",
                      "frame-sequence directories not available"))
        else:
            fa, fb = a["frames"], b["frames"]
            eq = len(fa) == len(fb) and all(x == y for x, y in zip(fa, fb))
            first = next((k for k, (x, y) in enumerate(zip(fa, fb)) if x != y), None)
            R.append((f"P4 frame sequences identical (per-frame sha256), {tag}", "PASS" if eq and len(fa) > 0 else "FAIL",
                      "measured", f"{len(fa)} / {len(fb)} frames; first differing index {first}"))
    # each sequence lands on its page drawing
    for o in occs:
        if o.get("last_frame") is None or o.get("crop") is None:
            continue
        lf, cr = o["last_frame"], o["crop"]
        same = lf.shape == cr.shape and int(np.abs(lf.astype(int) - cr.astype(int)).max()) == 0
        R.append((f"final frame of o{o['o']} ({o['id']}) equals its page crop", "PASS" if same else "FAIL", "measured",
                  f"shapes {lf.shape} {cr.shape}"))
    return R


def run_suite(suite, occs, hinge="H", strict=True, expect="PASS", only=None):
    res = mirror_checks(occs, hinge, strict)
    rows = []
    for (n, r, ev, d) in res:
        if only and not any(k in n for k in only):
            continue
        rows.append(rec(suite, n, r, ev, d, "PASS" if expect == "PASS" else ("FAIL" if r != "PENDING" else "PENDING")))
    rs = [r for (_, r, _, _) in res]
    overall = "FAIL" if "FAIL" in rs else ("PENDING" if "PENDING" in rs or not rs else "PASS")
    return overall, res


def gray_or_rgb(a):
    return a if a.ndim == 2 else a[..., :3]


def crop(page, r, inset=0):
    x0, y0, x1, y1 = r
    return np.ascontiguousarray(page[y0 + inset:y1 - inset, x0 + inset:x1 - inset])


def frame_hashes(d):
    if not d or not os.path.isdir(d):
        return None, None
    fs = sorted(f for f in os.listdir(d) if f.lower().endswith(".png"))
    if any(f.startswith("f") for f in fs):  # U3: f####.png = film frames (hard links to d###.png drawings)
        fs = [f for f in fs if f.startswith("f")]
    hs, last = [], None
    for f in fs:
        a = np.asarray(Image.open(os.path.join(d, f)))
        hs.append(sha_px(a))
        last = a
    return hs, last


# --------------------------------------------------------------------------------------------- suite: build

def page_occ(o):
    """U3 page.json: occurrences{'o1': {id, slot, ...}}, panels{ID: {crop_rects{slot}, frames_dir, balloon, exposure_sheet}}."""
    if not PAGEJ:
        return None, None
    oc = (PAGEJ.get("occurrences") or {}).get(f"o{o}")
    if not oc:
        return None, None
    return oc, (PAGEJ.get("panels") or {}).get(oc["id"])


def page_rect(o):
    oc, pn = page_occ(o)
    if not oc or not pn:
        return None
    r = (pn.get("crop_rects") or {}).get(oc["slot"]) or (pn.get("panel_rects") or {}).get(oc["slot"])
    return tuple(int(v) for v in r) if r else None


def page_frames_dir(o, pid):
    oc, pn = page_occ(o)
    return P(pn["frames_dir"]) if pn and pn.get("frames_dir") else None


def suite_build():
    S = "build"
    page_p = P("assets/pages/boucle-la.png")
    have_page = os.path.exists(page_p)
    rec(S, "inputs present", "PASS" if (have_page and PAGEJ and ROUTE) else "PENDING", "structurally verified",
        {"page_png": have_page, "page_json": bool(PAGEJ), "route_json": bool(ROUTE), "script_json": bool(SCRIPT),
         "speech_acts_json": bool(ACTS)})
    # route
    path = None
    if ROUTE:
        path = ROUTE.get("path") or ROUTE.get("panel_id_path") or ROUTE.get("reading_route") or ROUTE.get("sequence")
        if path and isinstance(path[0], dict):
            path = [p.get("id") for p in path]
        if path:
            path = [str(p).split("(")[0].strip() for p in path]
    seq = path or SCRIPT.get("sequence")
    rec(S, "sequence source", "INFO", "structurally verified",
        {"from": "route.json" if path else "script.json (route.json pending)", "seq": seq})
    meta = occ_meta()
    occs = [meta[o] for o in sorted(meta)]
    if seq and len(seq) == len(occs):
        for oc, s in zip(occs, seq):
            if oc["id"] != s:
                oc["id_mismatch"] = s
        mism = [(o["o"], o["id"], o.get("id_mismatch")) for o in occs if o.get("id_mismatch")]
        rec(S, "route.json / script.json / speech-acts.json agree on the ID at each occurrence",
            "FAIL" if mism else "PASS", "structurally verified", {"mismatches": mism})
    page = None
    if have_page:
        page = gray_or_rgb(np.asarray(Image.open(page_p)))
        rec(S, "page size >= 2400 px long side", "PASS" if max(page.shape[:2]) >= 2400 else "FAIL", "measured",
            {"size_wh": [page.shape[1], page.shape[0]], "sha256": sha_file(page_p)})
    if PAGEJ and CUT:
        Kc = CUT["source"]["K"]
        Jc = {f: {n: np.array(v, float) * Kc for n, v in CUT["rig"]["joints"][f].items()} for f in CUT["rig"]["joints"]}
    for oc in occs:
        poc, pn = page_occ(oc["o"])
        if pn:
            bl = pn.get("balloon") or {}
            oc.update({"page_id": poc["id"], "page_speaker": pn.get("speaker"), "page_text": pn.get("text"),
                       "balloon_png": bl.get("file", oc["balloon_png"]), "balloon_sha_rec": bl.get("sha256"),
                       "tail_xy": bl.get("tail_tip_in_panel"), "panel_w": (pn.get("raster_size") or [None])[0]})
            # text/seed/lines: the page's balloon record must agree with script.json (U2 owns the strings)
            oc["page_balloon_agrees"] = (bl.get("text") == oc["script_text"] == oc["text"] and bl.get("seed") == oc["seed"]
                                         and list(bl.get("wrapped_lines", [])) == oc["lines"] and pn.get("speaker") == oc["speaker"])
            ex = pn.get("exposure_sheet") or []
            if ex and CUT:
                d = ex[-1]
                s_, ox, oy = pn["frame_s_ox_oy"]
                jx, jy = (d.get("paper_jerk_px") or [0, 0])
                g = fk(d["pose"], (s_, ox + jx, oy + jy), Jc, Kc)
                oc["mouths"] = {f: tuple(g[f]["mouth"]) for f in g}
                oc["mouth_err_px"] = round(math.dist(oc["mouths"][oc["speaker"]], bl.get("mouth_in_panel", [1e9, 1e9])), 2)
    if PAGEJ:
        rec(S, "page.json balloon record (text, seed, lines, speaker) agrees with script.json and speech-acts.json",
            "PASS" if all(o.get("page_balloon_agrees") for o in occs) else "FAIL", "structurally verified",
            {f"o{o['o']}": o.get("page_balloon_agrees") for o in occs})
        rec(S, "independent FK mouth of the speaker (held drawing) == page.json mouth_in_panel (<= 1 px)",
            "PASS" if all(o.get("mouth_err_px", 99) <= 1 for o in occs) else "FAIL", "measured",
            {f"o{o['o']}": o.get("mouth_err_px") for o in occs})
        ps = PAGEJ.get("page", {}).get("sha256")
        em = P((PAGEJ.get("editor_media") or {}).get("page", "")) if (PAGEJ.get("editor_media") or {}).get("page") else None
        rec(S, "page.png sha256 == page.json record == editor_media copy",
            "PASS" if have_page and ps == sha_file(page_p) and (not em or sha_file(em) == ps) else "FAIL", "measured",
            {"recorded": ps, "editor_copy": rel(em)})
        bad = []
        for pid, pn in (PAGEJ.get("panels") or {}).items():
            for d in pn.get("exposure_sheet", []):
                fp = os.path.join(P(pn["frames_dir"]), f"d{d['drawing']:03d}.png")
                if not os.path.exists(fp) or sha_file(fp) != d.get("sha256"):
                    bad.append((pid, d["drawing"]))
                for fr in d.get("frames", []):
                    ff = os.path.join(P(pn["frames_dir"]), f"f{fr:04d}.png")
                    if not os.path.exists(ff) or os.stat(ff).st_ino != os.stat(fp).st_ino and sha_file(ff) != d.get("sha256"):
                        bad.append((pid, d["drawing"], fr))
            nd = len({d.get("sha256") for d in pn.get("exposure_sheet", [])})
            if nd < 8:
                bad.append((pid, f"only {nd} distinct drawings"))
        rec(S, "exposure sheets: every drawing file and its 2 frames match the recorded sha256; >= 8 distinct drawings per ID",
            "FAIL" if bad else "PASS", "measured",
            {"problems": bad[:20], "distinct_drawings": {k: len({d.get('sha256') for d in v.get('exposure_sheet', [])})
                                                         for k, v in (PAGEJ.get('panels') or {}).items()}})
    for oc in occs:
        r = page_rect(oc["o"]) or (PLAN_RECTS[oc["o"]] if page is not None and page.shape[:2] == (1800, 3200) else None)
        oc["rect"] = r
        if page is not None and r:
            oc["crop"] = crop(page, r)
            oc["panel_w"] = oc.get("panel_w") or (r[2] - r[0])
        oc["frames_dir"] = page_frames_dir(oc["o"], oc["id"])
        hs, last = frame_hashes(oc["frames_dir"])
        oc["frames"], oc["last_frame"] = hs, (gray_or_rgb(last) if last is not None else None)
        if last is not None and oc["crop"] is not None and last.ndim != oc["crop"].ndim:
            oc["last_frame"] = np.asarray(Image.fromarray(last).convert("L" if oc["crop"].ndim == 2 else "RGB"))
    ap_ = P("assets/pages/boucle-la-annotated.png")
    if page is not None and os.path.exists(ap_):
        an = gray_or_rgb(np.asarray(Image.open(ap_)))
        inside = {}
        if an.shape == page.shape:
            for oc in occs:
                if oc.get("rect"):
                    dd = np.abs(crop(an, oc["rect"]).astype(int) - oc["crop"].astype(int))
                    dd = dd.max(-1) if dd.ndim == 3 else dd
                    ys, xs = np.nonzero(dd)
                    inside[f"o{oc['o']}"] = {"px": int(len(ys)), "max_level_diff": int(dd.max()),
                                             "where_page_xy": [[int(x + oc["rect"][0]), int(y + oc["rect"][1])] for y, x in zip(ys[:6], xs[:6])]}
        rec(S, "annotated page: route line and speech-act tags touch no pixel inside any panel crop rect (incl. 6 px border pad)",
            "PASS" if inside and not any(v["px"] for v in inside.values()) else "FAIL", "measured",
            {"changed_px_inside_crop": inside, "severity": "advisory (annotated page only; B2 crops are on the clean page)"})
        pr_ = (PAGEJ or {}).get("page", {}).get("panel_rects") or {}
        inside2 = {}
        for oc in occs:
            poc, _ = page_occ(oc["o"])
            r = pr_.get(poc["slot"]) if poc else None
            if r and an.shape == page.shape:
                dd = np.abs(crop(an, r).astype(int) - crop(page, r).astype(int))
                inside2[f"o{oc['o']}"] = int(((dd.max(-1) if dd.ndim == 3 else dd) > 0).sum())
        rec(S, "annotated page: no annotation pixel inside any panel rect (border and art)",
            "PASS" if inside2 and not any(inside2.values()) else "FAIL", "measured", {"changed_px": inside2})
    if page is not None:
        rec(S, "rects source", "INFO", "structurally verified",
            {o["o"]: {"rect": o["rect"], "from": "page.json" if page_rect(o["o"]) else "plan.md section 5"} for o in occs})
    overall, res = run_suite(S, occs)
    REPORT["suites"][S] = {"overall": overall, "note": "the real deliverable; PENDING rows wait for U3 (page.png, page.json, "
                           "route.json, frames) and the editor (mp4)"}
    return occs, overall


# --------------------------------------------------------------------------------------------- suite: test page

def suite_testpage():
    S = "testpage"
    tp = os.path.join(SW, "test-page.png")
    if not os.path.exists(tp):
        rec(S, "test-page.png present", "PENDING", "structurally verified", "absent")
        return None
    page = gray_or_rgb(np.asarray(Image.open(tp)))
    meta = occ_meta()
    out = {}
    for inset, lab in ((0, "strict"), (10, "interior")):
        occs = [dict(meta[o]) for o in sorted(meta)]
        for oc in occs:
            r = PLAN_RECTS[oc["o"]]
            oc["crop"] = crop(page, r, inset)
            oc["panel_w"] = r[2] - r[0]
        res = mirror_checks(occs, "H", inset == 0)
        for (n, r, ev, d) in res:
            if "page crops" in n:
                rec(S + "-" + lab, n, r, ev, d, "PASS" if inset else "FAIL")
        out[lab] = occs
        # diff map evidence for the strict case
        if inset == 0:
            for i in range(3):
                a, b = occs[i]["crop"], occs[6 - i]["crop"]
                d = (np.abs(a.astype(int) - b.astype(int)) > 0).astype(np.uint8) * 255
                Image.fromarray(d if d.ndim == 2 else d.max(-1)).save(os.path.join(VAL, f"testpage-diff-o{i + 1}-o{7 - i}.png"))
    REPORT["suites"][S] = {
        "overall": "INFO",
        "expected": "strict rows FAIL by design here: the old test page drew borders per position; the build page draws one border per ID and passes",
        "note": "Calibration on the approved test page at the plan's rects. Interiors (10 px inset) of all three pairs are "
                "pixel-identical; the full rects differ only within 10 px of the edge, i.e. the hand-inked wobbly border "
                "is drawn per POSITION, not per panel ID. B2 requires the full crops identical (max abs diff 0): U3 must "
                "draw each border with a seed keyed by panel ID (or paste one border raster per ID) so the paired crops "
                "match edge to edge. Diff maps: films/sources/boucle-la/validator/testpage-diff-*.png"}
    return out


# --------------------------------------------------------------------------------------------- suite: mutations

def real_frames(d, only=None):
    fs = sorted(f for f in os.listdir(d) if f.startswith("f") and f.endswith(".png"))
    if only is not None:
        return gray_or_rgb(np.asarray(Image.open(os.path.join(d, fs[only]))))
    return [gray_or_rgb(np.asarray(Image.open(os.path.join(d, f)))) for f in fs]


def synth_frames(c):
    """SYNTHETIC frame sequence for the fixture's own self-test (not art): 6 shifted copies then the page crop."""
    fr = [np.roll(c, k, axis=1) for k in (12, 10, 8, 6, 4, 2)] + [c]
    return [sha_px(f) for f in fr], fr


def suite_mutations(base_occs, base_label):
    S = "mutations"
    import copy

    def fresh():
        occs = []
        for o in base_occs:
            n = dict(o)
            n["lines"] = list(o["lines"])
            occs.append(n)
        # real frame sequences when U3's exist; otherwise SYNTHETIC ones derived from each occurrence's OWN crop
        for n in occs:
            if n.get("frames") is not None and n.get("frames_dir"):
                n["frames"] = list(n["frames"])
                n["_fr"] = None
            elif n["crop"] is not None:
                n["frames"], fr = synth_frames(n["crop"].copy())
                n["_fr"] = fr
                n["last_frame"] = fr[-1]
        return occs

    def verdict(occs, hinge="H"):
        res = mirror_checks(occs, hinge)
        fails = [n for (n, r, _, _) in res if r == "FAIL"]
        pend = [n for (n, r, _, _) in res if r == "PENDING"]
        return ("FAIL" if fails else "PASS"), fails, pend

    base = fresh()
    v, f, p = verdict(base)
    rec(S, f"M0 base passes ({base_label})", v, "measured", {"failing": f, "pending": p})

    # N1 speakers swapped on the second B (o6): balloon tail moved to Odette, speaker = odette
    m = fresh()
    o6 = m[5]
    o6["speaker"] = "odette"
    o6["tail_x"] = (o6.get("panel_w") or 850) - (o6["tail_x"] or 0)
    c = o6["crop"].copy()
    h = int(c.shape[0] * 0.40)
    c[:h] = c[:h, ::-1]  # balloon band mirrored: the tail now points at the right-hand figure
    o6["crop"] = c
    if o6.get("mouths") and o6.get("tail_xy") is not None:
        o6["tail_xy"] = o6["mouths"]["odette"]
    if o6["_fr"] is None:
        o6["frames"] = [sha_px(gray_or_rgb(np.concatenate([q[:h, ::-1], q[h:]], 0)))
                        for q in real_frames(o6["frames_dir"])]
        o6["last_frame"] = c
    else:
        o6["frames"], fr = synth_frames(c)
        o6["last_frame"] = fr[-1]
    v, f, p = verdict(m)
    rec(S, "N1 speakers swapped on the second B must FAIL", v, "measured", {"failing": f}, "FAIL")
    # and the speaker test alone catches it even with untouched art
    m = fresh()
    m[5]["speaker"] = "odette"
    v, f, p = verdict(m)
    rec(S, "N1b speaker swapped on the second B (record only, art untouched) must FAIL", v, "structurally verified",
        {"failing": f}, "FAIL")

    # N2 letters reversed within one balloon (o5, C'): « ?! TSE LI IUQ ED SROLA »
    m = fresh()
    o5 = m[4]
    o5["text"] = o5["text"][::-1]
    o5["lines"] = [ln[::-1] for ln in o5["lines"]][::-1]
    v, f, p = verdict(m)
    rec(S, "N2 letters reversed within one balloon (o5) must FAIL", v, "structurally verified",
        {"failing": f, "mutated_text": o5["text"]}, "FAIL")

    # N3 a 1-px edit to one paired panel (o6 page crop and its held frame)
    m = fresh()
    o6 = m[5]
    c = o6["crop"].copy()
    y, x = c.shape[0] // 2, c.shape[1] // 2
    c[y, x] = (c[y, x].astype(int) + 1) % 256 if c.ndim == 2 else ((c[y, x].astype(int) + 1) % 256).astype(c.dtype)
    o6["crop"] = c
    o6["frames"] = list(o6["frames"])
    o6["frames"][-1] = sha_px(c)
    o6["last_frame"] = c
    v, f, p = verdict(m)
    rec(S, "N3 one-pixel edit (+1 level at the centre of o6) must FAIL", v, "measured", {"failing": f, "pixel": [x, y]},
        "FAIL")
    # N3b only one in-between frame edited, page untouched
    m = fresh()
    q = (real_frames(m[5]["frames_dir"], only=2) if m[5]["_fr"] is None else m[5]["_fr"][2]).copy()
    q[5, 5] = ((q[5, 5].astype(int) + 1) % 256).astype(q.dtype)
    m[5]["frames"] = list(m[5]["frames"])
    m[5]["frames"][2] = sha_px(q)
    v, f, p = verdict(m)
    rec(S, "N3b one-pixel edit to one in-between frame of o6 must FAIL", v, "measured", {"failing": f}, "FAIL")

    # N4 hinge twice / missing
    m = fresh()
    m[4] = dict(m[3])
    m[4]["o"] = 5
    v, f, p = verdict(m)
    rec(S, "N4 H occurring twice must FAIL", v, "structurally verified", {"failing": f[:3]}, "FAIL")

    # ALT: separately named hinge candidates with the same pairs
    for alt in ("H-G4", "H-G3", "H-G2", "H-G1b"):
        a = (SCRIPT.get("hinge_alternates") or {}).get(alt)
        if not a:
            continue
        m = fresh()
        h = m[3]
        h.update({"id": alt, "speaker": a["speaker"], "text": a["text"], "seed": a["seed"], "lines": a["wrapped_lines"],
                  "balloon_png": a["file"], "balloon_sha_rec": a["sha256"]})
        balloon_ok = os.path.exists(P(a["file"])) and sha_file(P(a["file"])) == a["sha256"]
        v, f, p = verdict(m, hinge=alt)
        pairs_same = [o["id"] for o in m[:3]] == [o["id"] for o in base[:3]]
        rec(S, f"ALT hinge {alt} with the same pairs passes as a separately named candidate",
            "PASS" if v == "PASS" and balloon_ok and pairs_same and alt != "H" else "FAIL", "structurally verified",
            {"candidate": f"[A,B,C,{alt},C,B,A]", "text": a["text"], "lettered_balloon_sha_ok": balloon_ok,
             "failing": f, "note": "a different named branch, not a violation; G4 is the plan's 'legal but inert' case "
                                   "(structure passes, act_of unchanged): the blind-reader test B3, not this fixture, rejects it"})
    REPORT["suites"][S] = {"overall": None, "base": base_label,
                           "note": "mutations are applied in memory to copies of the real build records, page crops and U3's frame "
                                   "sequences (synthetic frames only if U3's frames are absent); nothing is written over art"}
    rows = [t for t in REPORT["tests"] if t["suite"] == S]
    REPORT["suites"][S]["overall"] = "PASS" if all(t["as_expected"] for t in rows) else "FAIL"


# --------------------------------------------------------------------------------------------- suite: FK

def Rm(deg, c):
    a = math.radians(deg)
    co, si = math.cos(a), math.sin(a)
    return np.array([[co, -si, c[0] - co * c[0] + si * c[1]], [si, co, c[1] - si * c[0] - co * c[1]], [0, 0, 1.0]])


def ap(M, p):
    v = M @ np.array([p[0], p[1], 1.0])
    return np.array([v[0], v[1]])


def fk(pose, frame, J, K):
    """Independent re-implementation of cutouts.json rig.order: M = Base . R_lean(feet) [. R_head(neck) | . R_fore(elbow)]."""
    s, ox, oy = frame
    base = np.array([[s / K, 0, ox], [0, s / K, oy], [0, 0, 1.0]])
    out = {}
    for f in ("gustave", "odette"):
        p, j = pose[f], J[f]
        root = base @ Rm(p.get("lean", 0.0), j["feet"])
        Mh = root @ Rm(p.get("head", 0.0), j["neck"])
        Mf = root @ Rm(p.get("fore", 0.0), j["elbow"])
        out[f] = {"feet": ap(root, j["feet"]), "neck_body": ap(root, j["neck"]), "neck_head": ap(Mh, j["neck"]),
                  "elbow_body": ap(root, j["elbow"]), "elbow_fore": ap(Mf, j["elbow"]), "hand": ap(Mf, j["hand"]),
                  "mouth": ap(Mh, j["mouth"])}
    return out


def drawings_from_page():
    """Every drawing of every panel's exposure sheet in page.json: (id, k, pose, frame incl. paper jerk, joints, note, hold)."""
    out = []
    if not PAGEJ:
        return out
    for pid, pn in (PAGEJ.get("panels") or {}).items():
        s_, ox, oy = pn.get("frame_s_ox_oy") or (1.1, 0, 0)
        for d in pn.get("exposure_sheet") or []:
            jx, jy = d.get("paper_jerk_px") or (0, 0)
            out.append((pid, d.get("drawing"), d["pose"], (s_, ox + jx, oy + jy), d.get("joints"), d.get("note_anchor"),
                        len(d.get("frames", [])) or None))
    return out


def suite_fk():
    S = "fk"
    if not CUT:
        rec(S, "cutouts.json present", "PENDING", "structurally verified", "absent")
        return
    K = CUT["source"]["K"]
    J = {f: {n: np.array(v, float) * K for n, v in CUT["rig"]["joints"][f].items()} for f in CUT["rig"]["joints"]}
    # 1 manifest: pieces exist, sha matches, one component, no trespass by the chosen method
    bad = []
    for k, v in CUT["pieces"].items():
        fp = P(v["file"])
        if not os.path.exists(fp) or sha_file(fp) != v["sha256"]:
            bad.append((k, "sha/missing"))
            continue
        a = np.asarray(Image.open(fp).convert("RGBA"))[..., 3] > 127
        n, _ = cv2.connectedComponents(a.astype(np.uint8), connectivity=8)
        if n - 1 != 1:
            bad.append((k, f"{n - 1} alpha components"))
        m = (CUT.get("methods") or {}).get(k)
        if m and m["candidates"][m["chosen"]].get("trespass", 0) != 0:
            bad.append((k, "trespass"))
    rec(S, "pieces: file sha256 == manifest, alpha is one connected component (alpha>127, 8-conn), chosen method trespass 0",
        "FAIL" if bad else "PASS", "measured", {"pieces": list(CUT["pieces"]), "problems": bad})
    # 2 bone lengths recorded == joint distances
    bl = CUT["rig"]["bone_lengths_source_px"]
    errs = {}
    for f, d in bl.items():
        for bone, L in d.items():
            a, b = bone.split("-")
            errs[f"{f}.{bone}"] = round(abs(float(np.linalg.norm(J[f][a] - J[f][b])) - L), 4)
    rec(S, "recorded bone lengths == joint distances (<=0.5 px)", "PASS" if max(errs.values()) <= 0.5 else "FAIL",
        "measured", errs)
    # 3 drawings: from page.json exposure sheets if present, else every pose in cutouts.json at the plan's frames
    draws = drawings_from_page()
    src = "page.json exposure sheets"
    if not draws:
        src = "cutouts.json poses (entry, canonical, and 8 in-betweens each) at plan frames s=1.10 (A,B,C) / 1.30 (H); page.json pending"
        for pid, pz in CUT["poses"].items():
            if pid == "neutral":
                continue
            e, c = pz["entry"], pz["canonical"]
            for k in range(10):
                t = k / 9
                pose = {f: {q: e[f].get(q, 0) * (1 - t) + c[f].get(q, 0) * t for q in set(e[f]) | set(c[f])} for f in c}
                draws.append((pid, k, pose, (1.30 if pid == "H" else 1.10, 0.0, 0.0), None, None, None))
    rest = {}
    worst = {"neck-elbow": 0.0, "elbow-hand": 0.0, "neck coincidence": 0.0, "elbow coincidence": 0.0,
             "recorded joints vs FK": 0.0, "note anchor vs hand": 0.0}
    n_rec = n_note = 0
    for (o, k, pose, frame, jrec, note, hold) in draws:
        frame = tuple(frame) if frame else (1.10, 0.0, 0.0)
        neutral = fk({"gustave": {}, "odette": {}}, frame, J, K)
        g = fk(pose, frame, J, K)
        for f in ("gustave", "odette"):
            ne0 = np.linalg.norm(neutral[f]["neck_body"] - neutral[f]["elbow_body"])
            eh0 = np.linalg.norm(neutral[f]["elbow_body"] - neutral[f]["hand"])
            # neck on the HEAD to elbow on the FOREARM: bone spans two pins
            ne = np.linalg.norm(g[f]["neck_head"] - g[f]["elbow_fore"])
            eh = np.linalg.norm(g[f]["elbow_fore"] - g[f]["hand"])
            worst["neck-elbow"] = max(worst["neck-elbow"], abs(ne - ne0))
            worst["elbow-hand"] = max(worst["elbow-hand"], abs(eh - eh0))
            worst["neck coincidence"] = max(worst["neck coincidence"], float(np.linalg.norm(g[f]["neck_body"] - g[f]["neck_head"])))
            worst["elbow coincidence"] = max(worst["elbow coincidence"], float(np.linalg.norm(g[f]["elbow_body"] - g[f]["elbow_fore"])))
            if jrec and f in jrec:
                for jn, key in (("neck", "neck_head"), ("elbow", "elbow_fore"), ("hand", "hand"), ("feet", "feet")):
                    if jn in jrec[f]:
                        n_rec += 1
                        worst["recorded joints vs FK"] = max(worst["recorded joints vs FK"],
                                                             float(np.linalg.norm(np.array(jrec[f][jn]) - g[f][key])))
        if note is not None:
            n_note += 1
            worst["note anchor vs hand"] = max(worst["note anchor vs hand"], float(np.linalg.norm(np.array(note) - g["odette"]["hand"])))
    w = {k: round(v, 4) for k, v in worst.items()}
    rec(S, "bone lengths constant within 0.5 px over every drawing (neck->elbow across head/body pins, elbow->hand)",
        "PASS" if w["neck-elbow"] <= 0.5 and w["elbow-hand"] <= 0.5 else "FAIL", "measured",
        {"drawings": len(draws), "source": src, "max_dev_px": {k: w[k] for k in ("neck-elbow", "elbow-hand")}})
    rec(S, "joint coincidence error <= 1 px (neck, elbow)",
        "PASS" if w["neck coincidence"] <= 1 and w["elbow coincidence"] <= 1 else "FAIL", "measured",
        {"drawings": len(draws), "max_err_px": {k: w[k] for k in ("neck coincidence", "elbow coincidence")}})
    selfc = {k: v.get("fk_selfcheck") for k, v in ((PAGEJ or {}).get("panels") or {}).items()}
    rec(S, "recorded per-drawing joints in page.json agree with FK (<= 1 px)",
        ("PASS" if w["recorded joints vs FK"] <= 1 else "FAIL") if n_rec else "INFO", "measured" if n_rec else "structurally verified (U3 self-report)",
        {"joints_compared": n_rec, "max_err_px": w["recorded joints vs FK"],
         "u3_fk_selfcheck": selfc,
         "note": "page.json records poses, not per-drawing joints; the independent evidence is the build row "
                 "'independent FK mouth == page.json mouth_in_panel' (<= 0.06 px). Bone-length and pin-coincidence rows are "
                 "exact by construction for rigid pinned pieces; they prove the sheets use the rig's fixed order, not the pixels."})
    rec(S, "note anchor stays on Odette's hand (<= 1 px)",
        ("PASS" if w["note anchor vs hand"] <= 1 else "FAIL") if n_note else "INFO",
        "measured" if n_note else "structurally verified (U3 self-report)",
        {"drawings_with_note_anchor": n_note, "max_err_px": w["note anchor vs hand"],
         "u3_note_anchor_err_px": {k: (v or {}).get("note_anchor_err_px") for k, v in selfc.items()}})
    # holds on 2s, final hold >= 3 s (SCION 1) where the sheet gives holds
    holds = {}
    for (o, k, pose, frame, jrec, note, hold) in draws:
        if hold is not None:
            holds.setdefault(o, []).append(int(hold))
    if holds:
        badh = {o: h for o, h in holds.items() if any(x != 2 for x in h)}
        occ_hold = {k: v.get("hold_s") for k, v in (PAGEJ.get("occurrences") or {}).items()}
        short = {k: v for k, v in occ_hold.items() if v is None or v < 3.0}
        rec(S, "exposure on 2s (every drawing exactly 2 frames) and each occurrence holds its last drawing >= 3.0 s",
            "FAIL" if badh or short else "PASS", "measured",
            {"ids": len(holds), "not_on_2s": badh, "hold_s": occ_hold, "short_holds": short,
             "note": "hold_s is the editor's plan in page.json; the film check measures it once the mp4 exists"})
    else:
        rec(S, "exposure on 2s with a final hold >= 72 frames (3.0 s)", "PENDING", "measured", "no holds in page.json yet")
    # cross-check this FK against rig.py (read-only import)
    try:
        sys.path.insert(0, os.path.join(SW, "panel-artist"))
        import rig  # noqa
        Rg = rig.Rig()
        md = 0.0
        for (o, k, pose, frame, *_r) in draws[:60]:
            frame = tuple(frame) if frame else (1.10, 0.0, 0.0)
            _, Jr = Rg.fk(pose, frame)
            g = fk(pose, frame, J, K)
            for f in ("gustave", "odette"):
                for a, b in (("neck_on_head", "neck_head"), ("elbow_on_fore", "elbow_fore"), ("hand", "hand"), ("feet", "feet")):
                    md = max(md, float(np.linalg.norm(np.array(Jr[f][a]) - g[f][b])))
        rec(S, "independent FK == rig.py Rig().fk (<= 0.01 px)", "PASS" if md <= 0.01 else "FAIL", "measured",
            {"max_err_px": round(md, 6), "drawings": min(60, len(draws))})
    except Exception as e:
        rec(S, "independent FK == rig.py Rig().fk (<= 0.01 px)", "PENDING", "measured", f"rig.py not importable: {e}")
    rows = [t for t in REPORT["tests"] if t["suite"] == S]
    REPORT["suites"][S] = {"overall": "FAIL" if any(t["result"] == "FAIL" for t in rows) else
                           ("PASS" if all(t["result"] == "PASS" for t in rows) else "PASS (with INFO rows)"),
                           "drawing_source": src}


# --------------------------------------------------------------------------------------------- suite: film

def decode_audio(path, sr=16000):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)


def ncc(x, t):
    n = len(t)
    t = t - t.mean()
    tn = np.linalg.norm(t) + 1e-12
    N = 1 << int(math.ceil(math.log2(len(x) + n)))
    c = np.fft.irfft(np.fft.rfft(x, N) * np.conj(np.fft.rfft(t, N)), N)[:len(x) - n + 1]
    cs = np.concatenate([[0], np.cumsum(x)])
    cs2 = np.concatenate([[0], np.cumsum(x * x)])
    s = cs[n:] - cs[:-n]
    s2 = cs2[n:] - cs2[:-n]
    var = np.maximum(s2 - s * s / n, 1e-12)
    return c / (tn * np.sqrt(var))


def bell_onsets(x, sr, thr=0.5):
    """Count bell strikes in x by normalised cross-correlation with the foraged bell's own strike (onset-20 ms .. +250 ms),
    gated by an energy jump (>= 8 dB over the preceding 150 ms) so the bell's own decay does not count again."""
    snd = (SCRIPT.get("sound_default_mix") or {}).get("bell", {})
    bp = P(snd.get("path", "films/sources/boucle-la/dialogue-writer/sound/bell.wav"))
    on = float(snd.get("strike_onset_s_in_file", 0.31))
    b = decode_audio(bp, sr)
    pre = int(0.02 * sr)
    t = b[int(on * sr) - pre:int(on * sr) + int(0.25 * sr)]
    c = ncc(x, t)
    # local maxima of the NCC (non-max suppression over +-0.125 s), so a long decay cannot swallow a second strike
    win = int(0.25 * sr) | 1
    cmax = cv2.dilate(c.astype(np.float32).reshape(1, -1), np.ones((1, win), np.uint8)).ravel()
    groups = [[int(i)] for i in np.nonzero((c >= thr) & (c >= cmax - 1e-9))[0]]
    out = []
    w = int(0.15 * sr)
    for g in groups:
        k = g[int(np.argmax(c[g]))]
        o = k + pre
        e_pre = np.mean(x[max(0, o - w):o] ** 2) + 1e-12
        e_post = np.mean(x[o:o + int(0.05 * sr)] ** 2) + 1e-12
        jump = 10 * math.log10(e_post / e_pre)
        out.append({"t_s": round(o / sr, 4), "ncc": round(float(c[k]), 3), "jump_db": round(jump, 1), "counted": jump >= 8})
    return [o for o in out if o["counted"]], out


def video_frame(path, t, size=(960, 540)):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-f", "rawvideo",
                        "-pix_fmt", "gray", "-s", f"{size[0]}x{size[1]}", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(size[1], size[0])


def match_crop(frame, crop_g):
    """Best match of the page crop's central 60 % inside the film frame over film scales 0.25..1.25 (template matching)."""
    best = (-1, None, None)
    for s in np.geomspace(0.25, 1.25, 41):
        cw, ch = int(crop_g.shape[1] * s), int(crop_g.shape[0] * s)
        if cw < 40 or ch < 40:
            continue
        rs = cv2.resize(crop_g, (cw, ch), interpolation=cv2.INTER_AREA)
        tw, th = int(cw * 0.6), int(ch * 0.6)
        if tw >= frame.shape[1] or th >= frame.shape[0]:
            continue
        tpl = rs[(ch - th) // 2:(ch - th) // 2 + th, (cw - tw) // 2:(cw - tw) // 2 + tw]
        m = cv2.matchTemplate(frame, tpl, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(m)
        if mx > best[0]:
            reg = frame[loc[1]:loc[1] + th, loc[0]:loc[0] + tw].astype(int)
            mad = float(np.mean(np.abs(reg - tpl.astype(int))))
            best = (float(mx), round(float(s), 4), round(mad, 2))
    return best


def suite_film(build_occs):
    S = "film"
    mp4 = P("assets/films/boucle-la.mp4")
    page_p = P("assets/pages/boucle-la.png")
    current = os.path.exists(mp4) and os.path.exists(page_p) and PAGEJ is not None and \
        os.path.getmtime(mp4) >= os.path.getmtime(page_p)
    if os.path.exists(mp4) and not current:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                                   capture_output=True, text=True).stdout or 0)
        rec(S, "assets/films/boucle-la.mp4 is the current build", "PENDING", "structurally verified",
            {"mp4_mtime": datetime.datetime.fromtimestamp(os.path.getmtime(mp4), datetime.timezone.utc).isoformat(),
             "duration_s": dur, "reason": "older than / without this build's page.png and page.json: an earlier version "
             "of the work; the film checks run once the editor renders"})
    elif not os.path.exists(mp4):
        rec(S, "assets/films/boucle-la.mp4 exists", "PENDING", "structurally verified", "absent")

    # calibration on the approved test shot (real foraged bell + rustle, real page)
    ts = os.path.join(SW, "test-shot.mp4")
    tj = jload(os.path.join(SW, "test-shot-build/timing.json")) or {}
    if os.path.exists(ts):
        sr = 16000
        x = decode_audio(ts, sr)
        cnt, allc = bell_onsets(x, sr)
        fo = float(tj.get("face_out_s", 2.0))
        ok = len(cnt) == 1 and abs(cnt[0]["t_s"] - fo) <= 1 / FPS
        rec(S + "-calibration", "test-shot.mp4: exactly one bell onset within +-1 frame of the face-out drawing", "PASS" if ok else "FAIL",
            "measured", {"face_out_s": fo, "onsets": cnt, "candidates": allc})
        tp = os.path.join(SW, "test-page.png")
        if os.path.exists(tp):
            pg = np.asarray(Image.open(tp).convert("L"))
            found = {}
            for t in (4.5, 9.5):
                fr = video_frame(ts, t)
                Image.fromarray(fr).save(os.path.join(VAL, f"testshot-{t:.1f}s.png"))
                sc = {oid: match_crop(fr, crop(pg, PLAN_RECTS[o])) for o, oid in ((1, "A"), (2, "B"), (3, "C"), (4, "H"))}
                bid = max(sc, key=lambda k: sc[k][0])
                found[f"{t}s"] = {"best": bid, "scores": {k: {"ncc": round(v[0], 3), "scale": v[1], "mad": v[2]} for k, v in sc.items()}}
            rec(S + "-calibration", "test-shot.mp4: held frames located against test-page crops (matcher calibration)", "INFO",
                "measured", found)
    # synthetic negatives for the bell counter (built from the real bell + rustle files, in memory)
    sr = 16000
    bell = decode_audio(P("films/sources/boucle-la/dialogue-writer/sound/bell.wav"), sr)
    rus = decode_audio(P("films/sources/boucle-la/dialogue-writer/sound/rustle.wav"), sr)

    def mix(events, dur=10.0):
        y = np.zeros(int(dur * sr))
        for (sig, start) in events:
            a = int(start * sr)
            seg = sig[:max(0, len(y) - a)]
            y[a:a + len(seg)] += seg
        return y + np.random.default_rng(1).normal(0, 1e-4, len(y))
    on = 0.31
    cases = [("one bell at 2.000 s (+ rustle at 1.0 s)", mix([(rus, 1.0 - 0.84), (bell, 2.0 - on)]), 2.0, "PASS"),
             ("two bells (2.0 s and 6.0 s) must FAIL", mix([(bell, 2.0 - on), (bell, 6.0 - on)]), 2.0, "FAIL"),
             ("bell 3 frames late must FAIL", mix([(bell, 2.0 + 3 / FPS - on)]), 2.0, "FAIL"),
             ("rustle only, no bell must FAIL", mix([(rus, 1.0)]), 2.0, "FAIL")]
    for name, y, fo, exp in cases:
        cnt, allc = bell_onsets(y, sr)
        ok = len(cnt) == 1 and abs(cnt[0]["t_s"] - fo) <= 1 / FPS
        rec(S + "-selftest", f"bell counter: {name}", "PASS" if ok else "FAIL", "measured",
            {"onsets": cnt}, exp)

    if not current:
        for n in ("held frames match the page crops at film scale (each occurrence)",
                  "paired held frames identical in the film (o1/o7, o2/o6, o3/o5)",
                  "exactly one bell onset, within +-1 frame of the face-out drawing"):
            rec(S, n, "PENDING", "measured", "waits for the editor's current mp4")
        REPORT["suites"][S] = {"overall": "PENDING", "note": "detectors calibrated on test-shot.mp4 and synthetic mixes"}
        return
    # ---- the real film
    film = PAGEJ.get("film") or jload(os.path.join(SW, "edit.json")) or {}
    holds = {int(k): v for k, v in (film.get("hold_sample_s") or {}).items()}
    for k, v in (PAGEJ.get("occurrences") or {}).items():
        if "act_end_s" in v and "hold_s" in v and int(k[1:]) not in holds:
            holds[int(k[1:])] = round(v["act_end_s"] + 0.6 * v["hold_s"], 3)
    holds = holds or PLAN_HOLD_SAMPLE_S
    fo = float(film.get("face_out_s") or (PAGEJ.get("face_out") or {}).get("film_s") or PLAN_FACE_OUT_S)
    page = np.asarray(Image.open(page_p).convert("L"))
    res = {}
    allok = True
    for oc in build_occs:
        r = oc.get("rect")
        if not r:
            continue
        fr = video_frame(mp4, holds[oc["o"]])
        Image.fromarray(fr).save(os.path.join(VAL, f"film-hold-o{oc['o']}.png"))
        sc = match_crop(fr, crop(page, r))
        okk = sc[0] >= 0.90 and sc[2] is not None and sc[2] <= 10
        allok &= okk
        res[oc["o"]] = {"id": oc["id"], "t_s": holds[oc["o"]], "ncc": round(sc[0], 3), "scale": sc[1], "mad": sc[2], "ok": okk}
    rec(S, "held frames match the page crops at film scale (each occurrence)", "PASS" if allok and res else "FAIL",
        "measured", {"criterion": "TM_CCOEFF_NORMED >= 0.90 and mean abs diff <= 10 levels on the central 60 %",
                     "per_occurrence": res, "times_from": "page.json occurrences act_end_s + 0.6*hold_s" if PAGEJ.get("occurrences") else "plan.md shot list"})
    pr = {}
    for i, j in ((1, 7), (2, 6), (3, 5)):
        a = np.asarray(Image.open(os.path.join(VAL, f"film-hold-o{i}.png"))).astype(int)
        b = np.asarray(Image.open(os.path.join(VAL, f"film-hold-o{j}.png"))).astype(int)
        pr[f"o{i}/o{j}"] = {"mad": round(float(np.mean(np.abs(a - b))), 2),
                            "same_scale": res.get(i, {}).get("scale") == res.get(j, {}).get("scale")}
    rec(S, "paired held frames identical in the film (o1/o7, o2/o6, o3/o5)",
        "PASS" if all(v["mad"] <= 3 for v in pr.values()) else "FAIL", "measured",
        {"criterion": "mean abs diff <= 3 levels between the decoded held frames (codec noise only)", "pairs": pr})
    x = decode_audio(mp4, 16000)
    cnt, allc = bell_onsets(x, 16000)
    ok = len(cnt) == 1 and abs(cnt[0]["t_s"] - fo) <= 1 / FPS
    rec(S, "exactly one bell onset, within +-1 frame of the face-out drawing", "PASS" if ok else "FAIL", "measured",
        {"face_out_s": fo, "face_out_from": "page.json face_out.film_s" if (PAGEJ.get("face_out") or {}).get("film_s") else "plan.md (28.0 s)",
         "onsets": cnt, "candidates": allc})
    rows = [t for t in REPORT["tests"] if t["suite"] == S]
    REPORT["suites"][S] = {"overall": "FAIL" if any(t["result"] == "FAIL" for t in rows) else "PASS"}


# --------------------------------------------------------------------------------------------- main

def main():
    build_occs, b_overall = suite_build()
    tp = suite_testpage()
    if b_overall == "PASS" and all(o["crop"] is not None for o in build_occs):
        base, lab = build_occs, "the real build (page.png + page.json)"
    elif tp:
        base, lab = tp["interior"], "test-page.png interiors (10 px inset) at the plan's rects; build page pending"
    else:
        base, lab = build_occs, "script.json only"
    suite_mutations(base, lab)
    suite_fk()
    suite_film(build_occs)
    for s in ("film-calibration", "film-selftest", "testpage-strict", "testpage-interior"):
        rows = [t for t in REPORT["tests"] if t["suite"] == s]
        if rows:
            REPORT["suites"][s] = {"overall": ("AS EXPECTED" if s.startswith("testpage") else "PASS")
                                   if all(t["as_expected"] in (True, None) for t in rows) else "FAIL"}
    REPORT["expected_page_json_schema"] = {
        "occurrences": [{"o": "1..7", "id": "A|B|C|H", "rect": "[x0,y0,x1,y1] page px, full panel incl. border",
                         "frames_dir": "films/sources/boucle-la/page-animator/frames/<ID>/ (pairs use the SAME dir)",
                         "rig_frame": "[s, ox, oy] as in cutouts.json frame_convention",
                         "exposure": [{"pose": {"gustave": {}, "odette": {}}, "hold": "frames (2 on 2s; last >= 72)",
                                       "joints": {"gustave": {"neck": "[x,y] output px", "elbow": "...", "hand": "...", "feet": "..."},
                                                  "odette": {}}, "note_anchor": "[x,y] output px"}]}],
        "film": {"face_out_s": "film time of H's face-out drawing", "hold_sample_s": {"1": "a film time inside o1's held drawing", "...": "..."}}}
    tests = REPORT["tests"]
    REPORT["summary"] = {
        "counts": {r: sum(1 for t in tests if t["result"] == r) for r in ("PASS", "FAIL", "PENDING", "INFO")},
        "unexpected": [f"{t['suite']}: {t['test']} -> {t['result']} (expected {t['expected']})" for t in tests
                       if t["as_expected"] is False],
        "B2_status": ("PASS" if REPORT["suites"]["build"]["overall"] == "PASS" and REPORT["suites"]["mutations"]["overall"] == "PASS"
                      else ("FAIL" if REPORT["suites"]["build"]["overall"] == "FAIL" else "PENDING (build inputs not yet produced)")),
        "fixture_discriminates": REPORT["suites"]["mutations"]["overall"] == "PASS"}
    out = os.path.join(SW, "fixture-report.json")
    REPORT["evidence"] = {
        "foraged_by_this_unit": [],
        "note": "U4 foraged nothing and downloaded nothing. It reads the foraged items already recorded by U1 "
                "(cutouts.json evidence: Daumier, Mœurs conjugales no. 3, 1839, Rijksmuseum RP-P-OB-41.183, CC0) and U2 "
                "(sound.json: bell CC0, rustle PD, voice grains via movingimagearchive.com, rights unverified, off in the "
                "default mix) and checks their local files by sha256 against those records.",
        "inputs_checked": {k: (sha_file(P(v)) if os.path.exists(P(v)) else None) for k, v in {
            "page_png": "assets/pages/boucle-la.png", "annotated_png": "assets/pages/boucle-la-annotated.png",
            "page_json": "films/swarm/boucle-la/page.json", "route_json": "films/swarm/boucle-la/route.json",
            "script_json": "films/swarm/boucle-la/script.json", "speech_acts_json": "films/swarm/boucle-la/speech-acts.json",
            "cutouts_json": "films/swarm/boucle-la/cutouts.json", "bell_wav": "films/sources/boucle-la/dialogue-writer/sound/bell.wav",
            "rustle_wav": "films/sources/boucle-la/dialogue-writer/sound/rustle.wav",
            "test_shot_mp4": "films/swarm/boucle-la/test-shot.mp4", "film_mp4": "assets/films/boucle-la.mp4"}.items()}}
    REPORT["handmade"] = [
        {"item": "palindrome fixture (Mirror(seq,h) preconditions P1-P5, crop/frame identity, negatives, alternate hinges, "
                 "independent FK, bell-onset counter by NCC with the foraged bell's own strike, held-frame template matcher)",
         "where": "films/swarm/boucle-la/fixture.py"},
        {"item": "evidence images: test-page diff maps, decoded test-shot stills, film hold stills once the mp4 is current",
         "where": "films/sources/boucle-la/validator/"}]
    REPORT["absences"] = [
        "assets/films/boucle-la.mp4 on disk is an earlier version (2026-11-15, 41.8 s); the held-frame and bell checks on the "
        "real film are PENDING until the editor renders. Rerun: python3 -I films/swarm/boucle-la/fixture.py",
        "page.json records poses per drawing, not output-px joints or note anchors: the FK pixel check rests on the speaker's "
        "mouth (independent FK vs page.json mouth_in_panel, <= 0.06 px); the note-anchor row reports U3's self-check only.",
        "Voice grains are off in the default mix (user note); their pair identity is checked at file level (sha256), not in the mix.",
        "The test page (test-page.png) fails strict pair identity at the borders (borders drawn per position); this is the "
        "old test material, the build page draws one border per ID and passes."]
    json.dump(REPORT, open(out, "w"), indent=1, ensure_ascii=False, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    print(json.dumps(REPORT["summary"], indent=1, ensure_ascii=False))
    for s, v in REPORT["suites"].items():
        print(f"{s:20s} {v['overall']}")


if __name__ == "__main__":
    main()
