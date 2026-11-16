import json, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maquette as M
HERE = os.path.dirname(os.path.abspath(__file__))
sha = json.load(open(os.path.join(HERE, "..", "out", "master.sha1.json")))
ev = []
for i, f in sorted(M.LIGHT.items(), key=lambda x: x[1]):
    ev.append(dict(id=f"win{i:02d}_on", kind="window_on", frame=f, window=i, step=M.step_of(i), floor=i // 24, bay=i % 24, attack_frames=[f - 2, f - 1, f]))
ev.append(dict(id="win16_off", kind="window_off", frame=M.W16_OFF, window=16))
for j, c in enumerate(M.contact_frames()):
    if c > 346:
        break
    foot = "L" if (j % 2 == 0) else "R"
    ev.append(dict(id=f"step{j:02d}", kind="walker_step", frame=c, foot=foot, contact_hold=[c, c + M.HOLD - 1]))
ev += [dict(id="door_open", kind="door_open", frame=334, span=[334, 346]),
       dict(id="walker_in", kind="walker_step", frame=346, note="passes the threshold; occluded by the jamb 346-362", span=[346, 362]),
       dict(id="door_close", kind="door_close", frame=374, span=[365, 374], note="leaf starts closing at 365, latches (hard stop) at 374"),
       dict(id="silhouette_rise", kind="silhouette_rise", frame=502, span=[502, 518], window=16),
       dict(id="head_turn", kind="head_turn", frame=538, span=[538, 552], settle=[552, 558], window=16, degrees=25, overshoot_deg=2),
       dict(id="curtain_slide", kind="silhouette_rise", frame=552, span=[552, 566], window=16, note="curtain edge slides and settles (kind reused; not in the plan's kind list)"),
       dict(id="lamp_on", kind="lamp_on", frame=660),
       dict(id="cut_192", kind="cut", frame=192, note="S1->S2 (continuous set-up, track slows, push-in begins)"),
       dict(id="cut_384", kind="cut", frame=384, note="KEY CUT to the locked closer framing; window 47 lights on the cut frame"),
       dict(id="cut_624", kind="cut", frame=624, note="hard cut back to the wide framing")]
ev.sort(key=lambda e: (e["frame"], e["id"]))
planes = []
for k in range(M.NFR):
    sh = M.shot_of(k)
    row = dict(k=k, shot=sh["id"], cam=sh["cam"], exposure=round(M.exposure(k), 4))
    for p in M.RATIOS:
        dx, sc, _ = M.plane_params(k, p)
        row[p] = dict(dx_px=round(dx / M.SS, 3), scale=round(sc, 5))
    planes.append(row)
walker = []
for k in range(M.WALK_K0, 363):
    p = M.walker_pose(k)
    walker.append({kk: (round(v, 4) if isinstance(v, float) else ([round(x, 4) for x in v] if isinstance(v, tuple) else v)) for kk, v in p.items()})
edl = dict(
    master=dict(revision=sha["revision"], path="out/master.mp4", sha1="out/master.sha1.json", framemd5="out/master.framemd5",
                frames=720, size=[960, 464], fps=24, encode="libx264 crf 16 preset slow -tune animation yuv420p, 24 fps CFR, video only, encoded once",
                plan="plan-r3", builder="picture/maquette.py frame(k)"),
    event_frames_changed=[],
    window_numbering="i = floor*24 + bay; floor 0 = top floor; bays 0-7 far volume, 8-15 middle, 16-23 near volume of the staggered near row (approved test-shot model); entrance door under bay 16",
    shots=[dict(id="S1", k0=0, k1=191, t=[0.0, 8.0], cam="wide", camera="lateral track left, P6 moves 0->64 px (ease-in), exposure 1.00"),
           dict(id="S2", k0=192, k1=383, t=[8.0, 16.0], cam="tele", camera="r3: same eye-level position, 3.4x longer lens (documentary zoom) centred on the entrance so the walker is ~90-110 px tall; track at half speed (P6 64->96 px) + multiplane push-in scale 1+0.18*ratio*u; exposure 1.00->0.93"),
           dict(id="S3", k0=384, k1=623, t=[16.0, 26.0], cam="key", camera="locked, closer framing of the near block (eye level kept); exposure 0.93->0.78"),
           dict(id="S4", k0=624, k1=719, t=[26.0, 30.0], cam="wide", camera="hard cut to the wide framing, tracks right (P6 0->-220 px), lamp post P7 crosses at 1.25x; exposure 0.78->0.70")],
    plane_ratios=M.RATIOS,
    events=ev,
    plane_offsets_per_frame=planes,
    walker_joint_angles_per_frame=dict(units="radians from vertical, + = forward along the path; foot = (u along path m, lift m); hip_u = metres along the path",
                                       stride_period_s=2 * M.STEP / 24, step_frames=M.STEP, contact_hold_frames=M.HOLD, bag_lag_frames=4, frames=walker),
)
json.dump(edl, open(os.path.join(HERE, "edl.json"), "w"), indent=1)
print(len(ev), "events", sum(1 for e in ev if e["kind"] == "window_on"), "window_on")
