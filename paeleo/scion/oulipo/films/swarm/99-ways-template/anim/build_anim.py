"""Build the rig-animator deliverables from timeline.py + panels.py:
anim/rig.json, anim/timing.json, anim/fk_test.json, anim/strips/S4.png S7.png S8.png.
Run: python3 -I build_anim.py   (renders every frame of S1-S8 once; S0 is checked at its end frame)"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import panels  # noqa: E402
from panels import bp  # noqa: E402

FPS = 24
ORDER = ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
PAGE = np.asarray(Image.open(bp.PAGE_OUT).convert("RGB")).astype(np.float32)


def page_crop(key):
    x0, y0, x1, y1 = bp.PANELS[key]
    return PAGE[y0:y1, x0:x1]


def mad(a, b):
    return round(float(np.abs(np.clip(np.round(a), 0, 255) - b).mean()), 3)


def main():
    strips = {"S4", "S7", "S8"}
    (HERE / "strips").mkdir(exist_ok=True)
    timing = {"fps": FPS, "poses": "on twos (12 poses/s); a key holds until the next key; balloon drops are impact objects on "
                                   "ones (4 frames: -150, -55, +9 px bounce, land), then held", "shots": {}}
    fk = {"per_shot": {}, "criteria": {"pivot_drift_px_max": 1.5, "key_offset": "constant (|delta| <= 0.5 px)",
                                       "jamb": "fixed (|delta| <= 0.5 px)"}}
    t0 = 0
    for shot in ORDER:
        sh = panels.SHOTS[shot]
        n = sh["frames"]
        rec = {"panel": sh["panel"], "film_in_f": t0, "film_out_f": t0 + n, "film_in_s": round(t0 / FPS, 3),
               "frames": n, "keys": [{"f": k["f"], "label": k["label"], "rest": k["state"] == {},
                                      "state": k["state"]} for k in sh["keys"]],
               "balloons": [dict(b, drop_frames=[b["land"] - 3, b["land"] - 2, b["land"] - 1, b["land"]],
                                 read_hold_until=b["land"] + 36) for b in sh.get("balloons", [])],
               "action_end_f": sh.get("action_end"), "holds": sh.get("holds", {}), "sounds": sh.get("sounds", [])}
        if shot == "S0":
            rec["note"] = ("32 hand-ruled border strokes (8 panels x top,right,bottom,left), each drawn over two poses on twos from f6; "
                           "each panel's art is laid on the pose its box closes; panels.s0_frame(f)")
            rec["last_stroke_done_f"] = panels.S0_DONE_FRAME
            end = panels.s0_frame(n - 1)
            rec["end_frame_vs_page_mean_abs"] = mad(end, PAGE)
            timing["shots"][shot] = rec
            t0 += n
            continue
        key = sh["panel"]
        meas, thumbs = [], []
        last_state = None
        for f in range(n):
            st = panels.state_at(shot, f)
            img = panels.render_panel(key, st)
            if shot in strips:
                im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
                w = 220
                thumbs.append((f, im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)))
            ms = panels.measurements(key, st)
            js = json.dumps(st, sort_keys=True)
            if js != last_state:
                meas.append({"f": f, "m": ms})
                last_state = js
        crop = page_crop(key)
        ae = sh.get("action_end")
        rec["action_end_vs_page_mean_abs"] = mad(panels.render_panel(key, panels.state_at(shot, ae)), crop) if ae is not None else None
        rec["last_frame_vs_page_mean_abs"] = mad(panels.render_panel(key, panels.state_at(shot, n - 1)), crop)
        for b in rec["balloons"]:
            b["land_vs_page_mean_abs"] = mad(panels.render_panel(key, panels.state_at(shot, b["land"])), crop) \
                if b["land"] >= (ae or 0) else "action still running at land; final frame checked"
        # pose count on twos: number of distinct states, and that every pose change falls on an even frame
        changes = [m["f"] for m in meas]
        rec["distinct_poses"] = len(changes)
        rec["pose_changes_on_twos"] = all((f % 2 == 0) or any(b["land"] - 3 <= f <= b["land"] for b in sh.get("balloons", []))
                                          for f in changes)
        timing["shots"][shot] = rec
        # FK
        drift = [v for c in meas for m in c["m"] for k, v in m.items() if k.endswith("_pivot_drift_px")]
        door = [dict(f=c["f"], **m) for c in meas for m in c["m"] if "door_theta_deg" in m]
        fs = {"pivot_drift_px_max": round(max(drift), 6) if drift else None, "n_poses": len(meas)}
        if door:
            jt = np.array([d["jamb_top_px"] for d in door])
            jb = np.array([d["jamb_bottom_px"] for d in door])
            fs["jamb_top_px_max_delta"] = round(float(np.abs(jt - jt[0]).max()), 6)
            fs["jamb_bottom_px_max_delta"] = round(float(np.abs(jb - jb[0]).max()), 6)
            fs["door_poses"] = [{"f": d["f"], "theta_deg": round(d["door_theta_deg"], 2), "face": d["face"],
                                 "scaleX": round(d.get("scaleX", d.get("swing_scaleX", 0)), 3)} for d in door]
            offs = [d["key_offset_px"] for d in door if d.get("key_offset_px")]
            if offs:
                o = np.array(offs)
                fs["key_offset_px"] = o[0].round(4).tolist()
                fs["key_offset_max_delta_px"] = round(float(np.abs(o - o[0]).max()), 6)
                fs["key_hook_px_by_pose"] = [{"f": d["f"], "hook": np.round(d["hook_px"], 2).tolist(),
                                              "ring": np.round(d["ring_px"], 2).tolist()} for d in door if d.get("hook_px")]
        clerk = [dict(f=c["f"], **m) for c in meas for m in c["m"] if "collar_px" in m]
        if shot == "S8" and clerk:
            fs["tip_to_chin_px_by_pose"] = [{"f": c["f"], "tip_to_chin": round(c["tip_to_chin_px"], 1)} for c in clerk]
        fk["per_shot"][shot] = fs
        if shot in strips:
            cols = 12
            tw, th = thumbs[0][1].size
            rows = (len(thumbs) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * (tw + 4) + 4, rows * (th + 22) + 4), (255, 255, 255))
            dr = ImageDraw.Draw(sheet)
            keyf = {k["f"] for k in sh["keys"]}
            lands = {b["land"] for b in sh.get("balloons", [])}
            for i, (f, im) in enumerate(thumbs):
                x, y = 4 + (i % cols) * (tw + 4), 4 + (i // cols) * (th + 22)
                sheet.paste(im, (x, y + 18))
                tag = f"{shot} f{f:03d}" + (" KEY" if f in keyf else "") + (" LAND" if f in lands else "") + \
                      (" END" if f == ae else "")
                dr.text((x + 2, y + 3), tag, fill=(0, 0, 0))
            sheet.save(HERE / "strips" / f"{shot}.png", optimize=True)
        t0 += n
    timing["total_frames_S0_S8"] = t0
    # FK summary
    allmax = max(v["pivot_drift_px_max"] for v in fk["per_shot"].values() if v["pivot_drift_px_max"] is not None)
    ko = [v for v in fk["per_shot"].values() if "key_offset_max_delta_px" in v]
    jd = [max(v["jamb_top_px_max_delta"], v["jamb_bottom_px_max_delta"]) for v in fk["per_shot"].values() if "jamb_top_px_max_delta" in v]
    fk["summary"] = {"pivot_drift_px_max_all": allmax, "pivot_drift_pass": allmax <= 1.5,
                     "key_offset_max_delta_px": max(v["key_offset_max_delta_px"] for v in ko) if ko else None,
                     "key_offset_pass": all(v["key_offset_max_delta_px"] <= 0.5 for v in ko),
                     "jamb_max_delta_px": max(jd) if jd else None, "jamb_pass": all(d <= 0.5 for d in jd),
                     "rest_identity": {s: timing["shots"][s].get("last_frame_vs_page_mean_abs", timing["shots"][s].get("end_frame_vs_page_mean_abs"))
                                       for s in ORDER},
                     "method": "drift = distance between a child's pivot carried by its parent's matrix and by its own matrix, "
                               "for every distinct pose rendered (page px; panels are at page scale). Key offset = key ring "
                               "minus hook point, per door pose. Jamb = door's hinge-edge endpoints per door pose."}
    fk["lamp_piece"] = {k: v for k, v in panels.LAMP.items() if k in ("pivot", "fit", "fg_area", "components")}
    json.dump(timing, open(HERE / "timing.json", "w"), indent=1)
    json.dump(fk, open(HERE / "fk_test.json", "w"), indent=1)
    print(json.dumps(fk["summary"], indent=1))


if __name__ == "__main__":
    main()
