"""U2: write script.json, speech-acts.json, sound.json from lettering.json and the prepared sound grains.
Run: python3 -I records.py   (after letter.py)"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SW = os.path.join(ROOT, "films/swarm/boucle-la")
DW = os.path.join(ROOT, "films/sources/boucle-la/dialogue-writer")
L = json.load(open(os.path.join(DW, "lettering/lettering.json")))
TODAY = "2026-11-17"


def sha(rel):
    return hashlib.sha256(open(os.path.join(ROOT, rel), "rb").read()).hexdigest()


def rel(p):
    return os.path.relpath(p, ROOT)


SND = rel(os.path.join(DW, "sound"))
GS_PAGE = "https://www.movingimagearchive.com/sources/going-steady?clip=983d6d92-e09d-59ae-b20b-6bbb1ec9f189"
WT_PAGE = ("https://www.movingimagearchive.com/sources/working-together-a-case-history-in-labor-management-cooperation-1f8b859c"
           "?clip=28f53082-ba26-5045-8f59-ad48b6285a70")
ARCH_LIC = "Rights as listed by movingimagearchive.com (largely public domain); not independently verified"

VOICE = {
    "A": dict(file=f"{SND}/voice-A-female.wav", src="going-steady", clip_in=2.40, clip_out=4.05, film_in=534.834 + 2.40,
              film_out=534.834 + 4.05, sex="female"),
    "C": dict(file=f"{SND}/voice-C-female.wav", src="going-steady", clip_in=7.25, clip_out=8.85, film_in=534.834 + 7.25,
              film_out=534.834 + 8.85, sex="female"),
    "B": dict(file=f"{SND}/voice-B-male.wav", src="working-together", clip_in=15.77, clip_out=17.32, film_in=701.001 + 15.77,
              film_out=701.001 + 17.32, sex="male"),
    "H": dict(file=f"{SND}/voice-H-male.wav", src="working-together", clip_in=11.19, clip_out=13.34, film_in=701.001 + 11.19,
              film_out=701.001 + 13.34, sex="male"),
}
MIX_NOTE = ("OFF by default. The user's note on the approved test shot says: drop the English narration voice, keep only "
            "the bell and paper sounds. These grains are real English speech (1951 US educational films). They are prepared "
            "and logged so the editor or operator can restore them; the default mix is bell + rustle (+ optional room tone) only. "
            "Balloons carry the voice (captions), as the brief allows.")

SPEAKER = {"A": "odette", "B": "gustave", "C": "odette", "H": "gustave"}
TAIL_TO = {"odette": "Odette's mouth (right figure)", "gustave": "Gustave's mouth/cheek (left figure); in H from the left to the back of his head"}


def exchange_panels():
    out = []
    for k in "ABCH":
        b = L["balloons"][k]
        v = VOICE[k]
        out.append(dict(
            id=k, speaker=b["speaker"], text=b["text"], text_utf8_sha256=hashlib.sha256(b["text"].encode()).hexdigest(),
            lettering_seed=b["seed"], seed_rule="sum(map(ord, id + text)); line i uses seed + 13*i",
            wrapped_lines=b["wrapped_lines"], cap_px=b["cap"], pen_px=b["pen"], balloon_outline_px=b["outline"],
            balloon_png=b["file"], balloon_png_sha256=b["sha256"], balloon_size=b["size"],
            balloon_offset_in_panel=b["offset_in_panel"],
            tail_anchor=dict(tip_in_panel=b["tail_tip_in_panel"], points_to=TAIL_TO[b["speaker"]],
                             status="PROVISIONAL (test-shot rig). U3: compute the tip from U1's mouth anchor in the canonical "
                                    "pose and re-render with `python3 -I letter.py --tail %s X Y`; text, seed and letterforms "
                                    "do not change, and both occurrences of the pair use the one re-rendered PNG." % k),
            occurrences=[i + 1 for i, s in enumerate("ABCHCBA") if s == k],
            voice_clip=dict(path=v["file"], sha256=sha(v["file"]), source=v["src"], voice=v["sex"],
                            in_s_in_archive_clip=v["clip_in"], out_s_in_archive_clip=v["clip_out"],
                            in_s_in_source_film=round(v["film_in"], 3), out_s_in_source_film=round(v["film_out"], 3),
                            duration_s=round(v["clip_out"] - v["clip_in"], 3), sample_rate=48000, channels=1,
                            start_on="the frame the balloon appears (speaker's head accent)", in_mix_default=False,
                            mix_note=MIX_NOTE),
        ))
    return out


def main():
    script = dict(
        slug="boucle-la", unit="U2 dialogue-writer", owner="dialogue-writer", date=TODAY,
        base_revision=dict(plan_json_sha256=sha("films/swarm/boucle-la/plan.json"),
                           kf_common_sha256=sha("films/swarm/boucle-la/proposals/kf_common.py"),
                           letter_py_sha256=sha("films/swarm/boucle-la/dialogue-writer-build/letter.py")),
        read_set=["films/swarm/boucle-la/plan.md", "films/swarm/boucle-la/plan.json", "proposals/kf_common.py",
                  "test-shot-ledger.json", "test-shot-build/shot.py"],
        write_set=["films/swarm/boucle-la/script.json", "speech-acts.json", "hinge-alternatives.md",
                   "films/sources/boucle-la/dialogue-writer/**"],
        acceptance="Each pair of occurrences resolves to ONE balloon PNG and ONE voice file (byte identical by construction); "
                   "every line reads as a different act after H (speech-acts.json); lettering legible at 1920 px page fit.",
        sequence=list("ABCHCBA"),
        lines_decision="The proposal's four lines are kept verbatim (they are also the plan's frozen 'Balloon (exact)' "
                       "strings). Each is reversible: see speech-acts.json.",
        exchange_panels=exchange_panels(),
        note=dict(face_text=L["note"]["face_text"], files={k: v for k, v in L["note"].items() if isinstance(v, dict)},
                  how=L["note"]["note"]),
        furniture=L["furniture"],
        hinge_alternates=L["alternates"],
        lettering_manifest=rel(os.path.join(DW, "lettering/lettering.json")),
        build=["films/swarm/boucle-la/dialogue-writer-build/letter.py", "films/swarm/boucle-la/dialogue-writer-build/records.py"],
        sound_manifest="films/swarm/boucle-la/sound.json",
        sound_default_mix=dict(
            bell=dict(path=f"{SND}/bell.wav", strike_onset_s_in_file=0.31,
                      place="file 0.31 s on the face-out drawing of H (plan: film 28.0 s), exactly once"),
            rustle=dict(path=f"{SND}/rustle.wav", onset_s_in_file=0.84, place="the note turn in H (plan: from 27.0 s)"),
            voices="off (user note)"),
        evidence=[],
        handmade=[
            dict(item="all balloons A B C H and hinge alternates H-G1b, H-G2, H-G3, H-G4",
                 how="single-stroke pen alphabet (proposals/kf_common.py glyph polylines), round pen at cap*0.26, track 0.8, "
                     "supersampled x3, irregular superellipse balloon with pointed tail, 5 px outline; seeded per balloon",
                 where="films/sources/boucle-la/dialogue-writer/lettering/"),
            dict(item="note card face « À MA CHÈRE / ODETTE », back with crease, alternate face « MON CHER / ALFRED »",
                 how="cut-card quad with pen outline, lettered in the same hand", where="lettering/note-*.png"),
            dict(item="margin: LE MOT, OU QUI L'A / LAISSÉ ?, loop arrow, route A B C H C B A, ÉTUDE · OUBAPO, "
                      "D'APRÈS DAUMIER, 1839; panel IDs; film-only speech-act tags",
                 how="same pen alphabet; loop arrow a wobbly pen ellipse with arrowhead", where="lettering/*.png, margin-column.png"),
        ],
        absences=[
            "No openly licensed FRENCH real-speech recording was found in the archive cache: the only French-language clip "
            "(Toute La Bande, 1970) has no verifiable free status and was not used.",
            "Voice grains are English and band-unlimited; per the user's note they are not in the default mix.",
            "Room tone not foraged by this unit (the plan lists it as optional; the editor may take silence).",
            "Tail anchors are provisional until U1's rig mouth anchors exist.",
        ],
    )
    sound = json.load(open(os.path.join(HERE, "sound_evidence.json")))
    script["evidence"] = sound["items"]
    json.dump(script, open(os.path.join(SW, "script.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(sound, open(os.path.join(SW, "sound.json"), "w"), ensure_ascii=False, indent=1)
    print("script.json, sound.json written")


if __name__ == "__main__":
    main()
