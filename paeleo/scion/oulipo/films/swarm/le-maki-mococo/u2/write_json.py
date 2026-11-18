"""Write films/swarm/le-maki-mococo/mouth_rig.json from u2/build_out.json + the rig's own tables."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SW = HERE.parent
sys.path.insert(0, str(SW))
import mouth_rig as M  # noqa: E402

B = json.load(open(HERE / "build_out.json"))
SRC = "films/sources/le-maki-mococo"
MEDIA = f"{SRC}/u2-paper-mouth-puppet-and-kinetic-type-mouth-shape-designer-pose-library-typesetter-"
T = dict(skin_dE76="< 12 from #CA9A8A", lip_dE76="< 15 from #9D565D", lip_span_h=">= 0.35 (open)",
         lip_span_w=">= 0.22 (open)", skin_max_x_frac="< 0.45, cut by top and bottom edges",
         field_mean="mean >= 250", dark="cavity is the only dark mass (luma<80 <= 4% of frame)")


def passfail(m, open_pose):
    r = dict(skin=m["skin_dE76"] < 12, lip=m["lip_dE76"] < 15, skin_left=m["skin_max_x_frac"] < 0.45,
             skin_cut=m["skin_touches_top"] and m["skin_touches_bottom"], field=min(m["field_mean_right_half"]) >= 250,
             dark_le_4pct=m["frac_below80"] <= 0.04)
    if open_pose:
        r.update(lip_h=m["lip_span_h"] >= 0.35, lip_w=m["lip_span_w"] >= 0.22)
    return r


def voice_records():
    words = ["in", "the", "dark", "it", "hang", "and", "swing", "is"]
    hashes = {"in": "8/86", "the": "0/09", "dark": "f/f9", "it": "9/9f", "hang": "3/39", "and": "6/6b", "swing": "9/9f",
              "is": "8/8e"}
    out = []
    for w in words:
        t = f"LL-Q1860 (eng)-Grendelkhan-{w}.wav"
        u = t.replace(" ", "_")
        out.append(dict(
            id=f"voice-{w}", title=f"File:{t}", author="Speaker and recorder: Grendelkhan (Lingua Libre)",
            license="CC0", license_url="http://creativecommons.org/publicdomain/zero/1.0/deed.en",
            source_url=f"https://commons.wikimedia.org/wiki/File:{u}",
            file_url=f"https://upload.wikimedia.org/wikipedia/commons/{hashes[w]}/{u.replace('(', '%28').replace(')', '%29')}",
            local_path=f"{SRC}/test-shot/voice/{w}.{'wav' if w in ('and', 'dark') else 'mp3'}",
            what_it_shows="one English word spoken by a volunteer (Lingua Libre word recording)",
            verified_date_or_place="licence read from Commons extmetadata LicenseShortName = CC0 on 2026-11-17 "
                                   "(re-verification of the 2026-11-16 test-shot record)",
            used_as=("only its final /z/ spliced onto 'hang' and 'swing' -> 'hangs', 'swings'" if w == "is" else
                     f"voice of '{w}{'s' if w in ('hang', 'swing') else ''}' in L1 (provisional S1/S3/S8 assembly "
                     f"{MEDIA}/voice_L1.wav)")))
    return out


poses = {pid: dict(params=M.POSES[pid], key_pose=pid in M.KEY_POSES,
                   drawings={ls: dict(upper=f"{SRC}/mouth/pieces/lip{ls}_{pid}_up.png",
                                      lower=f"{SRC}/mouth/pieces/lip{ls}_{pid}_lo.png") for ls in ("A", "B")})
         for pid in M.POSE_IDS}
open_poses = {"A", "O", "surprise", "LNT", "EI"}
metrics = {k: dict(v, pass_=passfail(v, k.split(":")[1] in open_poses)) for k, v in B["metrics"].items()}
cf = B["compare_frame"]

doc = dict(
    unit="U2 · paper-mouth puppet and kinetic type (mouth-shape designer + pose library + typesetter)",
    revision="U2-r2 (rebuilt from the approved test shot with the user's fixes)",
    timing_status=B["status"],
    timing_note=("PROVISIONAL: U1's cue_timeline.json was not present when U2 ran. L1 onsets are measured from the "
                 "CC0 Lingua Libre assembly (envelope onset/nucleus/coda); L2-L4 in S1/S3 are ESTIMATED placeholders "
                 "(0.16 s syllables). mouth_rig.film_events() switches to cue_timeline.json automatically when it "
                 "exists (audio.syllables / audio.sections[S1|S3|S8] with seg_id + onset/offset)."),
    files=dict(
        rig="films/swarm/le-maki-mococo/mouth_rig.py",
        build="films/swarm/le-maki-mococo/u2/build.py", measure="films/swarm/le-maki-mococo/u2/measure.py",
        pieces_dir=f"{SRC}/mouth/pieces/", pose_sheet=f"{SRC}/mouth/pose_sheet.png",
        compare=f"{SRC}/mouth/compare_maki.png", mouth_test=f"{SRC}/mouth/mouth_test.mp4",
        provisional_onsets=f"{SRC}/mouth/provisional_onsets.json",
        editor_media=dict(voice_L1=f"{MEDIA}/voice_L1.wav", still_S3_hangs=f"{MEDIA}/still_S3_hangs.png",
                          still_S8_underline=f"{MEDIA}/still_S8_underline.png")),
    api=dict(
        mouth_layer="mouth_layer(t, track, lip_set='A'|'B'|callable) -> PIL RGBA 960x540, transparent field; "
                    "12 fps on twos (pose and jaw sampled on even 24 fps frames)",
        make_track="make_track(events, breaths, seconds) -> Track; decodes once (#38); Track.frame(t)->(pose,jaw)",
        film_events="film_events(timeline=None) -> (events, onsets_by_section, status) for S1/S3/S8 + gestures",
        decode="decode(targets, min_hold=2, on_twos=True) -> pose id per 24 fps frame",
        type_layer="type_layer(t, syllable_onsets, glyph_table=GLYPHS, ink=1, darken=None, cursor=True) -> RGBA",
        underline_layer="underline_layer(t, t0=52.0, t1=54.0) -> RGBA (red pencil under 'hangs', two strokes)",
        lip_set_at="lip_set_at(t): 'B' in S4 23.5-31.0, else 'A'",
        glyph_table="glyph_table() / GLYPHS; HANGS_BOX", usage=(
            "ev, on, st = M.film_events(); tr = M.make_track(ev, M.BREATHS, 66); "
            "frame.alpha_composite(M.mouth_layer(t, tr, M.lip_set_at(t))); "
            "frame.alpha_composite(M.type_layer(t, on['S3'])) ...")),
    handmade=[
        dict(id="paper-mouth", what="articulated cut-paper mouth in profile facing right: skin upper face with nose "
             "base, ala and nostril (washi base sheet + tissue under-sheets: cheek pad, philtrum column, ala), upper "
             "lip (substitution), lower lip (substitution) with glaze sheen and soft glints, upper teeth strip, lower "
             "teeth, cavity, tongue hint (2 drawings), jaw/chin group (chin pad + labiomental crease tissue), neck",
             where="films/swarm/le-maki-mococo/mouth_rig.py (geometry tables HEAD, ALA, JAW, ...; class Rig)",
             method="original landmark geometry, Catmull-Rom outline + scissor-wobble facets, anti-aliased masks, "
                    "glue-dome relief lit soft frontal-left from above, under-sheet ridges and tint, long kozo "
                    "fibres + cloudy formation (skin only), crepe striations on lip paper, lit cut edges, small "
                    "warm cast shadows; jaw groups on one FK pin at HINGE (-250, 40), clamp 0-10 deg",
             not_traced="geometry placed by eye from anatomy; maki.webp was only measured (palette/luma/framing)"),
        dict(id="lip-sets", what="two lip-paper colourways: A warm rose, B cool mauve", values=M.LIP_SETS),
        dict(id="kinetic-type", what="poem typeset in Caladea 30 px (OFL system font), warm ink #2a2422, rose "
             "cursor, letters landing on syllable onsets in 3 frames; column x 455-735, y 120-330", where="mouth_rig.py"),
        dict(id="red-pencil", what="two-stroke red-pencil underline under 'hangs' with pressure and paper-tooth "
             "skips", where="mouth_rig.underline_layer"),
        dict(id="room-tone", what="kit Mix.room in mouth_test.mp4 (declared synth, not speech)")],
    foraged=voice_records(),
    absences=[
        "No openly licensed recording of L2-L4 (binturong, smells, of, popcorn, never, rings) was foraged by U2: "
        "that is U1's assignment; U2 did not search for them to avoid duplicate Commons traffic. S1/S3 L2-L4 visemes "
        "are estimated placeholders until U1's cue_timeline.json lands.",
        "Moving Image Archive cache not searched by U2: the mouth is handmade by design (plan §6, element ledger)."],
    pose_library=dict(ids=M.POSE_IDS, count_per_set=len(M.POSE_IDS), key_poses_protected=sorted(M.KEY_POSES),
                      hinge=M.HINGE, jaw_clamp_deg=[0, M.JAW_MAX], poses=poses),
    decoder=dict(
        method="Viterbi over 24 fps frames; states (pose, held>=2); switches only on even frames (on twos) and only "
               "from a held state (min hold 2 frames); transition cost 0.15 + 0.10*|openness diff| + 0.6 for "
               "open<->closed (A/surprise <-> MBP/hm); match cost 1-sim, x3 for a mismatched key pose (O, surprise, "
               "MBP) so closures and the surprise are never averaged away",
        flicker_runs_lt_2_frames=B["flicker"],
        S1_path_12fps=B["S1_path"], S3_path_12fps_L1=B["S3_path"]),
    gestures=dict(events=M.gesture_events(), breaths=[dict(t_center=a, seconds=b, deg=c) for a, b, c in M.BREATHS],
                  note="silence is a hold; exactly one breath in S0 and one slow breath in S5 (declared); S2 'hm' then "
                       "slight open; S4 lip set B + jaw eases to 2.8 deg (thinking); S6 slow surprise; S7 'O' then "
                       "closes"),
    type=dict(font="Caladea-Regular 30 px", rows=M.ROWS, hangs_box=M.HANGS_BOX, glyph_table=M.GLYPHS,
              landing_frames=3, note="boxes are a pure function of the frozen poem string (poem-r1); invariant: "
                                    "assert glyph_table() == GLYPHS on every frame"),
    aesthetic=dict(targets=T, reference=B["reference"],
                   compare_frame=dict(cf, pass_=passfail(cf, True), file=f"{SRC}/mouth/compare_maki.png"),
                   per_pose=metrics,
                   notes=["dark_inside_cavity_frac = share of luma<80 pixels inside the cavity mask (whole frame incl. "
                          "type); outside it are only the nostril and lip-corner crease lines; in the compare frame "
                          "the poem's ink is also <80",
                          "fixes vs approved test shot: softer modelled skin (glue-dome relief + tissue under-sheets, "
                          "long visible fibres, no flat speckle); thinner, lighter upper lip; more teeth (extended "
                          "premolar strip, taller incisors, lower teeth), cavity lighter toward the front and only "
                          "deep at the back; gloss is a soft glaze sheen + glints, no sticker strip"]),
)
json.dump(doc, open(SW / "mouth_rig.json", "w"), indent=1, default=str)
print("wrote", SW / "mouth_rig.json")
