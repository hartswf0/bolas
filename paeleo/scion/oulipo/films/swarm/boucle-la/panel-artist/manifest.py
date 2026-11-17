"""Write films/swarm/boucle-la/cutouts.json (pieces, rig, poses, licence, evidence), run the rig self-checks and
render the contact sheet cutouts.jpg.  Run after cutouts.py:  python3 -I manifest.py"""
import datetime
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SW = os.path.join(ROOT, "films/swarm/boucle-la")
MEDIA = os.path.join(ROOT, "films/sources/boucle-la/panel-artist")
CUT = os.path.join(MEDIA, "cut")
DBG = os.path.join(MEDIA, "masks")

rep = json.load(open(os.path.join(CUT, "cut-report.json")))
G = rep["geometry_thumb"]
K = rep["K"]


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


joints = {f: {"feet": G["FEET"][f], "neck": G["NECK_PIN"][f], "elbow": G["ELBOW_PIN"][f], "hand": G["HAND"][f],
              "mouth": {"gustave": [474, 404], "odette": [566, 401]}[f]} for f in ("gustave", "odette")}
bones = {f: {"feet-neck": dist(j["feet"], j["neck"]) * K, "feet-elbow": dist(j["feet"], j["elbow"]) * K,
             "neck-elbow": dist(j["neck"], j["elbow"]) * K, "elbow-hand": dist(j["elbow"], j["hand"]) * K,
             "neck-mouth": dist(j["neck"], j["mouth"]) * K} for f, j in joints.items()}


def P(gl=0, gh=0, gf=0, ol=0, oh=0, of=0, turn=0, tilt=0):
    return {"gustave": {"lean": gl, "head": gh, "fore": gf},
            "odette": {"lean": ol, "head": oh, "fore": of, "note_turn": turn, "note_tilt": tilt}}


# canonical held drawings (= the page panel) and entry drawings, image-space degrees (see rig.py signs)
POSES = {
    "neutral": {"pose": P(), "reads_as": "the print as Daumier drew it (hands meeting)"},
    "A": {"canonical": P(gl=-1.5, gh=-8, gf=14, ol=-2.0, oh=-7, of=38, turn=0, tilt=-10),
          "entry": P(gl=0, gh=0, gf=4, ol=0.6, oh=2, of=6, turn=0, tilt=-4),
          "accent_drawing": "her head nod -7 lands with the note at the top of the raise",
          "reads_as": "ACCUSE: Odette's forearm raised, the note held up at his face, her head tilted forward and down at him; Gustave's head drawn back, his hand withdrawn"},
    "B": {"canonical": P(gl=-3.0, gh=-16, gf=-58, ol=0.5, oh=4, of=-10, turn=0, tilt=6),
          "entry": P(gl=0.8, gh=4, gf=8, ol=0, oh=2, of=10, turn=0, tilt=-2),
          "accent_drawing": "head jerk overshoot gh=-19 one drawing after the forearm flips (head lags), settle to -16",
          "reads_as": "'MOI ?!' SHRUG: Gustave's forearm flipped up, open hand palm-out beside his chest, head jerked back nose-up, body back; her note lowered"},
    "C": {"canonical": P(gl=-1.0, gh=-4, gf=22, ol=-5.0, oh=-9, of=20, turn=0, tilt=-16),
          "entry": P(gl=0, gh=-2, gf=10, ol=0.8, oh=1, of=8, turn=0, tilt=-6),
          "accent_drawing": "the lean leads from the feet; her head arrives one drawing later (-11 overshoot, settle -9)",
          "reads_as": "PRESSING LEAN: Odette's whole body leans forward about the feet, the note pushed toward him; his forearm down"},
    "H": {"canonical": P(gl=2.5, gh=9, gf=-22, ol=2.5, oh=10, of=26, turn=180, tilt=-4),
          "entry": P(gl=0, gh=0, gf=0, ol=0, oh=0, of=16, turn=0, tilt=-4),
          "accent_drawing": "heads swing in (gh +7, oh -6) over 6 drawings; note turns back->face over 6 drawings (substitution at edge-on, turn=90); on face-out she recoils: lean +2.5 leads, head +10 lags one drawing (overshoot +12)",
          "reads_as": "REVEAL: he leans in pointing at the note with his open hand, she recoils head back; the note face-out between them at chest height"},
}
NOTE = {"anchor": "odette hand (rig joint odette.hand), the note's right edge held in her grip",
        "size_thumb": [92, 60], "size_previous_test_shot": [118, 78],
        "why": "slightly smaller relative to the hands (user note), still legible: at page scale 1.1 it is ~101x66 px, at H scale 1.3 ~120x78 px; lettering cap >= 14 px",
        "offset_from_anchor_thumb": [-0.42, -0.42], "offset_units": "fractions of note w,h (card centre left of and above the hand)",
        "turn": "0 = back to reader, 180 = face out; substitute back->face drawing at 90 (edge-on)"}


def pose_list():
    out = {"neutral": POSES["neutral"]["pose"]}
    for k in "ABCH":
        out[k] = POSES[k]["canonical"]
        out[k + "_entry"] = POSES[k]["entry"]
    return out


def selfcheck(R):
    """Maker self-checks (not validation): bone lengths constant, joints coincide, note anchor on hand."""
    worst = {"bone_dev_px": 0.0, "joint_err_px": 0.0}
    frame = (1.1, 0, 0)
    ref = None
    import random
    rs = random.Random(5)
    poses = list(pose_list().values()) + [P(*[rs.uniform(-20, 20) for _ in range(6)]) for _ in range(40)]
    for pose in poses:
        Ms, J = R.fk(pose, frame)
        for f in ("gustave", "odette"):
            j = J[f]
            worst["joint_err_px"] = max(worst["joint_err_px"], dist(j["neck"], j["neck_on_head"]), dist(j["elbow"], j["elbow_on_fore"]))
            b = {"neck-elbow": dist(j["neck"], j["elbow"]), "elbow-hand": dist(j["elbow"], j["hand"]),
                 "feet-neck": dist(j["feet"], j["neck"])}
            exp = {k: bones[f][k] / K * 1.1 for k in b}
            for k in b:
                worst["bone_dev_px"] = max(worst["bone_dev_px"], abs(b[k] - exp[k]))
    assert worst["bone_dev_px"] <= 0.5 and worst["joint_err_px"] <= 1.0, worst
    return {k: round(v, 6) for k, v in worst.items()} | {"poses_tested": len(poses), "frame_scale": 1.1}


def note_card(face, w, h):
    """Contact-sheet stand-in for U2's handmade note (plain card + crease / two pen lines); not page art."""
    im = Image.new("L", (w, h), 251)
    d = ImageDraw.Draw(im)
    d.rectangle([1, 1, w - 2, h - 2], outline=13, width=2)
    if face:
        d.line([(w * 0.15, h * 0.35), (w * 0.85, h * 0.35)], fill=13, width=3)
        d.line([(w * 0.25, h * 0.65), (w * 0.75, h * 0.65)], fill=13, width=3)
    else:
        d.line([(w * 0.52, 3), (w * 0.5, h - 3)], fill=150, width=1)
    return np.asarray(im, np.float32)


def put_note(canvas, J, pose, s):
    th = pose["odette"].get("note_turn", 0)
    w, h = int(NOTE["size_thumb"][0] * s), int(NOTE["size_thumb"][1] * s)
    card = note_card(th > 90, w, h)
    c = max(0.05, abs(math.cos(math.radians(th))))
    hx, hy = J["odette"]["hand"]
    tilt = math.radians(pose["odette"].get("note_tilt", 0))
    cx, cy = hx - 0.42 * w, hy - 0.42 * h
    pts = []
    for x, y in [(-c * w / 2, -h / 2), (c * w / 2, -h / 2), (c * w / 2, h / 2), (-c * w / 2, h / 2)]:
        pts.append((cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)))
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (w, 0), (w, h), (0, h)]), np.float32(pts))
    H_, W_ = canvas.shape
    g = cv2.warpPerspective(card, M, (W_, H_), flags=cv2.INTER_LINEAR, borderValue=251)
    a = cv2.warpPerspective(np.ones_like(card), M, (W_, H_), flags=cv2.INTER_LINEAR, borderValue=0)
    canvas[:] = canvas * (1 - a) + g * a
    return (cx, cy)


def contact(R):
    W = 2400
    sheet = Image.new("L", (W, 2300), 251)
    d = ImageDraw.Draw(sheet)
    # row 1: pieces on white, each at the same scale
    x = 20
    s = 0.55
    for k in ["gustave_head", "gustave_body", "gustave_fore", "odette_head", "odette_body", "odette_fore", "backdrop"]:
        im = Image.open(os.path.join(ROOT, rep["pieces"][k]["file"]))
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        bg = Image.new("L", im.size, 230)
        bg.paste(im.convert("L"), (0, 0), im.split()[3])
        if x + im.width > W:
            break
        sheet.paste(bg, (x, 40))
        d.text((x, 20), f"{k} [{rep['pieces'][k]['method']}]", fill=13)
        x += im.width + 20
    # row 2: the four canonical poses (+ neutral) composited on white, at panel scale
    fw, fh = 460, 520
    y = 800
    for i, k in enumerate(["neutral", "A", "B", "C", "H"]):
        pose = POSES["neutral"]["pose"] if k == "neutral" else POSES[k]["canonical"]
        sc = 0.80
        frame = (sc, fw / 2 - 495 * sc, 30 - 300 * sc)
        g, cov, J = R.render(pose, frame, (fw, fh), ground=13 if k == "H" else 251, backdrop=(k != "H"))
        g = g.copy()
        put_note(g, J, pose, sc)
        for f in ("gustave", "odette"):
            for jn in ("neck", "elbow", "hand"):
                cv2.circle(g, tuple(int(v) for v in J[f][jn]), 4, 128, 1)
        sheet.paste(Image.fromarray(g.astype(np.uint8)), (20 + i * (fw + 10), y))
        d.text((20 + i * (fw + 10), y - 18), f"{k}: " + (POSES[k]["reads_as"][:52] if k != "neutral" else "rest = print"), fill=13)
    # row 3: mattes over the print + failure masks for the hands
    vis = Image.open(os.path.join(DBG, "mattes_vis.jpg")).convert("L")
    box = [int(v * K) for v in (220, 280, 780, 820)]
    vv = vis.crop(box).resize((560, 540))
    sheet.paste(vv, (20, 1350))
    d.text((20, 1330), "chosen silhouettes (red/blue) + head/forearm cuts (green) on the print", fill=13)
    xx = 600
    for k in ["gustave_fore_manual", "odette_fore_manual", "gustave_head_grabcut", "gustave_head_tonal", "odette_head_grabcut"]:
        f = Image.open(os.path.join(DBG, f"fail_{k}.png")).convert("RGB")
        part = k.rsplit("_", 1)[0]
        cb = {"gustave_fore": (340, 500, 600, 640), "odette_fore": (500, 520, 700, 650),
              "gustave_head": (360, 290, 520, 460), "odette_head": (540, 300, 690, 460)}[part]
        crop = Image.open(os.path.join(ROOT, rep["source"])).convert("RGB").crop([int(v * K) for v in cb])
        fm = f.crop([int(v * K) for v in cb])
        mix = Image.blend(crop, fm, 0.45).convert("L").resize((340, int(340 * crop.height / crop.width)))
        sheet.paste(mix, (xx, 1350))
        d.text((xx, 1330), "fail " + k, fill=13)
        xx += 360
    d.text((20, 2260), "boucle-la U1 cutouts: Daumier, Moeurs conjugales no.3 (1839), Rijksmuseum RP-P-OB-41.183, CC0 | levels only, no threshold | pins: neck, elbow, hand (circles)", fill=13)
    sheet = sheet.convert("RGB")
    sheet.save(os.path.join(SW, "cutouts.jpg"), quality=90)


def main():
    lic = json.load(open(os.path.join(MEDIA, "licence-check.json"))) if os.path.exists(os.path.join(MEDIA, "licence-check.json")) else {}
    cj = {
        "slug": "boucle-la", "unit": "panel-artist (U1)",
        "date": datetime.date.today().isoformat(),
        "source": {"file": rep["source"], "sha256": rep["source_sha256"], "K": K,
                   "note": "geometry in 960-px-wide view px ('thumb'); x K = source px. If the original-resolution file replaces the 1920 px file, rerun cutouts.py then manifest.py: all geometry rescales."},
        "licence": lic,
        "pieces": rep["pieces"],
        "methods": rep["methods"],
        "method_note": "SCION 29: per piece three candidates (seeded grabCut on the colour print; tonal matte on blurred luminance; manual contour = hand-placed scissor snips) scored by components==1, trespass==0 into the other figure's hand-marked region, interior paper lost < 2%, then least dark backdrop along the edge. Seeds: masks/seeds_<piece>.png (0 BG, 85 FG, 170 PR_BG, 255 PR_FG). Failure masks: masks/fail_<piece>_<method>.png (red = paper lost, blue = beyond the hand-marked part, orange = dark backdrop on the cut edge). Candidates: masks/cand_<piece>_<method>.png.",
        "joints_note": "Heads sit BEHIND their bodies; the neck underlap (disk r=24 thumb px about the neck pin, inside the body) tucks under Daumier's drawn collar line, so no straight cut or throat gap shows when the head turns. Forearms sit ON TOP; the round elbow cap (r=20) lies over the upper sleeve. The torso area the forearm vacates is re-clothed with the same figure's own shirt crayon (cloned patch, reclothed_px per body). Seams follow drawn lines; the white scissor margin (3.5 thumb px ~ 3.8 page px) is only on the silhouette's outside edge.",
        "levels_note": "Per-piece levels only (black point, white point, gamma) on red-weighted luminance 0.70R+0.30G; paper #E4C9B1 -> page white; backdrop (99,90,81) and the darkest crayon -> solid ink; crayon grain kept. No threshold, no posterize, no sharpening, no added grain.",
        "rig": {
            "graph": ["feet(root, lean) -> body", "body -> neck pin -> head", "body -> elbow pin -> forearm(+hand)",
                      "forearm -> hand anchor", "odette hand anchor -> note"],
            "order": "M_piece = Base(frame) . R_lean(feet) [. R_head(neck) | . R_fore(elbow)]; root->leaf, fixed",
            "draw_order": ["backdrop", "gustave_head", "gustave_body", "gustave_fore", "odette_head", "odette_body", "odette_fore", "note (U2/U3)"],
            "joints_thumb": joints,
            "joints": joints,
            "bone_lengths_source_px": {f: {k: round(v, 3) for k, v in b.items()} for f, b in bones.items()},
            "angle_convention": "image-space degrees, clockwise positive (y down). gustave: lean + toward her; head + nods in, - jerks back; fore - raises. odette: lean - toward him, + recoils; head - forward/down, + back; fore + raises.",
            "frame_convention": "frame=(s, ox, oy): s = output px per thumb px; (ox,oy) = output position of thumb (0,0). Panel A/B/C plan: s~1.10; H: s~1.30.",
            "module": "films/swarm/boucle-la/panel-artist/rig.py (Rig().fk / Rig().render)",
            "note": NOTE,
        },
        "poses": POSES,
    }
    json.dump(cj, open(os.path.join(SW, "cutouts.json"), "w"), indent=1, ensure_ascii=False)
    import rig
    Rg = rig.Rig()
    cj["rig"]["selfcheck"] = selfcheck(Rg)
    json.dump(cj, open(os.path.join(SW, "cutouts.json"), "w"), indent=1, ensure_ascii=False)
    contact(Rg)
    print(json.dumps(cj["rig"]["selfcheck"]))


if __name__ == "__main__":
    main()
