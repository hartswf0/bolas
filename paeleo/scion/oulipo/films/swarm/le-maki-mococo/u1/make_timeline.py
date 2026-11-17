"""U1 cue designer + staging unit: lay the measured voice into film time, release cues, stage the fictional
responses, write ledgers, branches and credits, then run the P1 fixture check (fixture_check.py)."""
import json, subprocess, sys, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SW = HERE.parent
PREP = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/"
            "u1-reading-cue-staging-reading-designer-cue-designer-staging-unit-merged-they-share-segment-ids-")
READ = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/reading")
M = json.load(open(PREP / "voice_measure.json"))
META = {r["title"]: r for r in json.load(open(HERE / "meta.json")) if not r.get("missing")}
FETCH = json.load(open(HERE / "fetch_log.json"))
TODAY = "2026-11-17 (Commons API extmetadata)"

CUES = [
    dict(cue_id="Q_sound", channel="sound", t_avail=2.0, linked_line=["L1", "L2", "L3", "L4"],
         what="the poem heard once in a real voice (voice_poem.wav), no text, no image"),
    dict(cue_id="Q_text", channel="text", t_avail=15.5, linked_line=["L1", "L2", "L3", "L4"],
         what="the poem typed syllable by syllable on the measured onsets while voice_poem.wav replays"),
    dict(cue_id="Q_image", channel="image", t_avail=38.0, linked_line=["L1"],
         what="the Brehm/Specht engraving of the binturong revealed hanging by its tail from the knot"),
]
REL = {c["cue_id"]: c["t_avail"] for c in CUES}

PLACEMENTS = [
    dict(shot="S1", file="voice_poem.wav", at=2.0, span="L1-L4", cue="Q_sound"),
    dict(shot="S3", file="voice_poem.wav", at=15.5, span="L1-L4", cue="Q_text", note="identical bytes to S1"),
    dict(shot="S6", file="voice_binturong.wav", at=41.0, span="L2.w1", cue="Q_image",
         note="the single word, same take as L2.w1 (after the image cue, not a new cue)"),
    dict(shot="S8", file="voice_L1.wav", at=52.0, span="L1", cue=None, note="L1 only, same takes"),
]
DUR = {"voice_poem.wav": M["duration_s"], "voice_L1.wav": M["L1_duration_s"],
       "voice_binturong.wav": M["binturong_duration_s"]}
for p in PLACEMENTS:
    p["end"] = round(p["at"] + DUR[p["file"]], 3)


def BASE0(p):
    if p["span"] == "L2.w1":
        return [w for w in M["words"] if w["seg_id"] == "L2.w1"][0]["t0"]
    return 0.0


def in_span(seg_id, span):
    if span == "L1-L4":
        return True
    return seg_id == span or seg_id.startswith(span + ".")


def shifted(items, p, base0=0.0):
    out = []
    for it in items:
        if not in_span(it["seg_id"], p["span"]):
            continue
        q = dict(seg_id=it["seg_id"], text=it["text"])
        off = p["at"] - base0
        q["t0"] = round(it["t0"] + off, 3); q["t1"] = round(it["t1"] + off, 3)
        if "nucleus" in it:
            q["nucleus"] = [round(x + off, 3) for x in it["nucleus"]]
        out.append(q)
    return out


def credit_for(stem):
    title = f"File:LL-Q1860 (eng)-{stem}.wav"
    return META[title]


def strip_html(s):
    import re
    return re.sub(r"<[^>]+>", "", s or "").strip()


# ---------------- poem ----------------
POEM_LINES = [l["text"] for l in M["lines"]]
words_by_line = {}
for w in M["words"]:
    words_by_line.setdefault(w["seg_id"].split(".")[0], []).append(w)
poem = dict(revision="poem-r1", lines=[], note="original poem, frozen; display_order = read_order")
order = 0
for li, l in enumerate(M["lines"]):
    ws = []
    for w in words_by_line[l["seg_id"]]:
        order += 1
        syl = [dict(seg_id=s["seg_id"], text=s["text"], stressed=s["stressed"]) for s in M["syllables"]
               if s["word"] == w["seg_id"]]
        ws.append(dict(seg_id=w["seg_id"], text=w["text"], display_order=order, read_order=order, syllables=syl))
    poem["lines"].append(dict(seg_id=l["seg_id"], text=l["text"], display_order=li + 1, read_order=li + 1, words=ws))

# ---------------- audio ----------------
takes = {}
for w in M["words"]:
    for f in w["files"]:
        if f.startswith("GAP"):
            continue
        stem = f.split(" ")[0].rsplit(".", 1)[0]
        takes.setdefault(stem, set()).add(w["seg_id"])
evidence = []
for stem, segs in sorted(takes.items()):
    r = credit_for(stem)
    speaker = stem.split("-")[0]
    word = stem.split("-", 1)[1]
    fl = FETCH.get(stem, {})
    evidence.append(dict(
        id=f"voice-{stem}", title=r["title"], author=f"Speaker and recorder: {speaker} (Lingua Libre)",
        license=r["license"], license_url=r["license_url"], source_url=r["source_url"], file_url=r["file_url"],
        local_path=fl.get("path", ""), local_form=fl.get("form", ""), sha1_commons=r["sha1"],
        what_it_shows=f"a single-word Lingua Libre recording of English '{word}' by volunteer speaker {speaker}",
        verified_date_or_place=TODAY + "; LicenseShortName=" + r["license"],
        used_as=("final voiced /z/ only, spliced onto 'hang' and 'swing'" if word == "is" else
                 "voice: " + ", ".join(sorted(segs)) + (" (+ /z/ splice from 'is')" if word in ("hang", "swing") else ""))))

audio = dict(
    rate=44100, channels=1,
    files={k: dict(path=str(PREP / k), duration_s=DUR[k]) for k in DUR},
    waveform_png=str(PREP / "voice_poem_waveform.png"),
    assembly=dict(word_gaps_s="0.06-0.08 within a line; 0.12 after a comma; 0.35 at line ends",
                  trim="onset: walk back from the peak above -36 dB re word peak tolerating <= 40 ms gaps (keeps the audible /b/ voice bar), 20 ms pre; offset -26 dB, 30 ms post, 6 ms fade-in, 20 ms fade-out; 70 Hz high-pass",
                  loudness="RMS of frames above 25% of the word's peak matched to 0.085 (full scale); poem peak <= 0.89",
                  splices=["L1.w5 'hangs' = Grendelkhan 'hang' + final /z/ of Grendelkhan 'is' (15 ms crossfade)",
                           "L1.w7 'swings' = Grendelkhan 'swing' + the same /z/"],
                  speakers="Grendelkhan (CC0) for every word except 'binturong' and 'popcorn' (Vealhurl, CC BY-SA 4.0)",
                  refrain_takes="only ONE English 'binturong' recording exists on Commons (Vealhurl); all four "
                                "'binturong' in L2/L4 and the S6 single word use that one take (declared; two "
                                "different takes were not possible)"),
    declared_gaps=[w["seg_id"] for w in M["words"] if w.get("gap")],
    measured_in_file=dict(words=M["words"], syllables=M["syllables"]),
    placements=PLACEMENTS,
    film_time={p["shot"]: dict(at=p["at"], end=p["end"], file=p["file"],
                               words=shifted(M["words"], p, BASE0(p)), syllables=shifted(M["syllables"], p, BASE0(p)))
               for p in PLACEMENTS},
    rms_24fps_voice_poem=M["rms_24fps"],
    timing_method=("measured: word onsets/offsets are the sample positions of each trimmed take in the assembly; "
                   "syllable boundaries inside binturong/popcorn/never are the deepest 10 ms RMS-envelope minima "
                   "between voiced humps; nucleus = frames above 45% of the syllable's peak. Checked against "
                   "voice_poem_waveform.png (structurally verified). Listening check: NOT performed by this unit "
                   "(no audio playback here) - perceptual check pending for the editor/critic."),
)

# ---------------- visemes ----------------
vis_film = {}
for p in PLACEMENTS:
    keys = []
    for v in M["visemes"]:
        if not in_span(v["seg_id"], p["span"]):
            continue
        base = 0.0
        if p["span"] == "L2.w1":
            base = [w for w in M["words"] if w["seg_id"] == "L2.w1"][0]["t0"]
        for k in v["keys"]:
            keys.append(dict(t=round(k["t"] - base + p["at"], 3), seg_id=v["seg_id"], shape=k["shape"],
                             jaw=k["jaw"], part=k["part"]))
    # close to rest after the last syllable
    keys.append(dict(t=round(p["end"] + 0.04, 3), seg_id=None, shape="rest", jaw=0.0, part="rest"))
    vis_film[p["shot"]] = keys
visemes = dict(
    classes=["rest", "MBP", "A", "O", "EI", "UW", "FV", "LNT"],
    openness=dict(rest=0.0, MBP=0.0, FV=0.15, LNT=0.3, EI=0.45, UW=0.35, O=0.7, A=1.0),
    jaw_rule="jaw = openness(shape) x (0.65 + 0.35 x rms_rel); rms_rel = syllable RMS peak / loudest syllable "
             "in the poem (linguistic shape separated from measured emphasis, SCION #47 sec. 6), so '-rong' (A) opens "
             "widest although 'bin' is louder. MBP onsets are keyed 50 ms before the measured burst (lip "
             "closure is silent). Recommended picture lead: 1 frame (42 ms) before the audio key.",
    per_syllable=M["visemes"],
    film_time=vis_film,
    silent_gestures=[
        dict(shot="S0", t=[0.0, 2.0], gesture="rest + one 1-degree breath", audio="room tone"),
        dict(shot="S2", t=[10.0, 15.0], gesture="silent 'hm' (UW/pursed) then slight A", audio="room tone"),
        dict(shot="S4", t=[23.5, 31.0], gesture="lip set B; jaw drop 2 deg (thinking)", audio="room tone + creak"),
        dict(shot="S5", t=[31.0, 38.0], gesture="closed; ONE slow breath; no other motion (declared silence)",
             audio="room tone -40 dB"),
        dict(shot="S6", t=[38.0, 41.0], gesture="slow surprise opening (no speech)", audio="paper ticks, no ring"),
        dict(shot="S7", t=[44.0, 52.0], gesture="'O' replacement, then close", audio="room tone"),
    ],
)

# ---------------- responses ----------------
RESP = [
    dict(resp_id="R1", speaker="Reader A (fictional)", t_said=10.0, label_time="0:10", cites=["Q_sound"],
         quoted_span="A gong? Something you strike — bin, tu, RONG.",
         hypothesis="The name is an onomatopoeia: a struck metal object (a gong) whose 'RONG' is its ring.",
         next_observation="Seeing the words spelled should test whether it is a thing that is struck or a name; "
                          "a verb like 'rings' in the text would confirm, 'never rings' would contradict.",
         on_screen_label="READER A (fictional) · 0:10 · cites: sound", shot="S2"),
    dict(resp_id="R2", speaker="Reader B (fictional)", t_said=24.0, label_time="0:24", cites=["Q_sound", "Q_text"],
         quoted_span="It hangs and swings… a lantern? A bell that's gone quiet?",
         hypothesis="Something suspended that sways but makes no sound: a lantern, or a bell that 'never rings'.",
         next_observation="A picture of the thing on the cord would test whether it is an object at all; "
                          "'smells of popcorn' does not yet fit a lantern.",
         on_screen_label="READER B (fictional) · 0:24 · cites: sound, text", shot="S4"),
    dict(resp_id="R3", speaker="Reader A (fictional)", t_said=44.0, label_time="0:44", cites=["Q_image", "Q_text"],
         quoted_span="Oh — it hangs by its tail. 'Never rings': it was never a gong.",
         hypothesis="A binturong is an animal that hangs by its tail; 'never rings' now reads literally as a denial "
                    "of the gong guess. Shift caused by the image (the tail on the knot), checked against the text.",
         next_observation="Hearing L1 again should test whether 'hangs' and 'swings' now read as the animal's "
                          "own movement; the popcorn smell is unverified by the picture.",
         on_screen_label="READER A (fictional) · 0:44 · cites: image (0:38), text", shot="S7",
         shift=dict(from_resp="R1", clue="by its tail", clue_cue="Q_image")),
    dict(resp_id="R4", speaker="Reader B (fictional)", t_said=48.5, label_time="0:48", cites=["Q_image", "Q_text"],
         quoted_span="Maybe. It still swings like a lantern — I'd want to see it move.",
         hypothesis="Accepts the animal provisionally but keeps the lantern reading alive: the engraving is a still, "
                    "so 'swings' is not yet shown.",
         next_observation="Moving footage of a binturong (not released in this film) would decide whether it swings; "
                          "the reading stays open.",
         on_screen_label="READER B (fictional) · 0:48", shot="S7", alternate_of="R3", min_hold_s=2.5),
]
for r in RESP:
    r["consent"] = "fictional — no participant"
    r["quoted_span_source"] = "plan.md §6 (frozen), printed verbatim"

QUARANTINE = [dict(resp_id="X1", speaker="Reader A (fictional)", t_said=10.0, cites=["Q_image"],
                   quoted_span="an animal that hangs by its tail",
                   note="plan §4 counterexample; must FAIL P1 (release(Q_image)=38 > 10) and is never shown")]

# ---------------- ledgers ----------------
speakers = sorted({e["author"] for e in evidence})
fiction = dict(
    readers=[dict(role="Reader A (fictional)", real_person=False, consent="fictional — no participant",
                  shown_as="caption only, labelled '(fictional)' on screen"),
             dict(role="Reader B (fictional)", real_person=False, consent="fictional — no participant",
                  shown_as="caption only, labelled '(fictional)' on screen")],
    real_people=[dict(who="Grendelkhan (Lingua Libre volunteer speaker)", what="single-word recordings",
                      consent_scope="self-published on Wikimedia Commons under CC0 1.0",
                      presented_as="the reading voice; never as Reader A or B; credited by username"),
                 dict(who="Vealhurl (Lingua Libre volunteer speaker)", what="'binturong' and 'popcorn' recordings",
                      consent_scope="self-published on Wikimedia Commons under CC BY-SA 4.0 (attribution required)",
                      presented_as="the reading voice; never as Reader A or B; credited by username")],
    note="The words are re-ordered into a poem the speakers never read; this is a declared word-collage, "
         "permitted by CC0/CC BY-SA. The voice is not presented as either speaker's own reading of the poem.",
    invalidates="any change of consent scope (licence) of a voice file invalidates exports that include it",
)
silences = dict(
    declared_silences=[
        dict(t=[0.0, 2.0], what="room tone only before Q_sound"),
        dict(t=[round(PLACEMENTS[0]["end"], 3), 15.5], what="room tone; no voice (Reader A's guess is a caption)"),
        dict(t=[round(PLACEMENTS[1]["end"], 3), 41.0], what="no voice; S5 31.0-38.0 is the declared expressive "
                                                          "silence at room tone -40 dB"),
        dict(t=[round(PLACEMENTS[2]["end"], 3), 52.0], what="no voice; readers are captions"),
        dict(t=[round(PLACEMENTS[3]["end"], 3), 65.0], what="no voice; end card in silence from 60.0"),
    ],
    declared_word_gaps=[dict(seg_id=w["seg_id"], text=w["text"], file_time=[w["t0"], w["t1"]],
                             what="silent span inside voice_poem.wav; mouth mouths the word silently (nominal timing)")
                        for w in M["words"] if w.get("gap")],
    synthesized_effects=[
        dict(what="room tone", how="kit Mix.room, very low", where="throughout"),
        dict(what="paper ticks as gong wedges are pinned (S2) and fall (S6)", how="kit Mix.click / band noise",
             where="11.5-14 s and 38.0-39.6 s (times from gong_rig.events())"),
        dict(what="one cord creak", how="kit band-passed noise", where="S4, about 24.5 s"),
        dict(what="paper flop as the animal's weight settles", how="kit Mix.thud, low gain", where="about 39.6 s"),
        dict(what="red-pencil scratch", how="band-passed noise shaped by stroke speed", where="52-54 s"),
    ],
    forbidden=["any ring or bell tone (invariant 7: the gong never rings)", "any synthetic speech"],
    no_tts="every audible word is a sample of a Lingua Libre recording",
)
branches = dict(image_first=dict(
    status="staged prediction, not rendered (render only if the editor's budget allows, flag --image-first)",
    is_new_condition=True,
    note="Not a repair of the main film: a separate condition with its own trace. Same poem, voice and layout; "
         "~15 s variant.",
    cues=[dict(cue_id="Q_image", t_avail=2.0), dict(cue_id="Q_sound", t_avail=3.0),
          dict(cue_id="Q_text", t_avail=None, note="not released inside the 15 s variant")],
    voice=dict(file="voice_poem.wav", at=3.0, end=round(3.0 + M["duration_s"], 3)),
    responses=[
        dict(resp_id="B1", speaker="Reader A (fictional)", t_said=round(3.0 + M["duration_s"] + 0.5, 2),
             cites=["Q_image", "Q_sound"], consent="fictional — no participant",
             quoted_span="An animal hanging — a kind of monkey? The bin-tu-rong is its name.",
             hypothesis="The word names the pictured animal; no gong is ever imagined.",
             next_observation="The text would only confirm the name; 'hangs' carries no shift.",
             staged=True),
        dict(resp_id="B2", speaker="Reader B (fictional)", t_said=round(3.0 + M["duration_s"] + 2.5, 2),
             cites=["Q_image", "Q_sound"], consent="fictional — no participant",
             quoted_span="It hangs by its tail. 'Swings' — from a branch.",
             hypothesis="'Hangs' and 'swings' describe the animal from the first hearing.",
             next_observation="Nothing left to revise: the defining beat at 'hangs' has no before/after.",
             staged=True),
    ],
    predicted_difference="guess 1 is an animal, never a gong; the 'hangs' glyph never changes meaning, so the "
                         "defining beat is absent - this is the baseline the main film is measured against.",
))

# ---------------- credits (kit schema) ----------------
credits = []
for e in evidence:
    credits.append(dict(title=e["title"], author=e["author"], license=e["license"], license_url=e["license_url"],
                        source_url=e["source_url"], file_url=e["file_url"], used_as=e["used_as"]))

absences = [
    dict(searched="Lingua Libre English 'hangs' (intitle LL-Q1860 (eng) ... -hangs.wav), any speaker",
         result="none on Commons; built from Grendelkhan 'hang' + /z/ of 'is' (declared splice)"),
    dict(searched="Lingua Libre English 'swings' by Grendelkhan",
         result="not found (only Arlo Barnes-swings, CC0, different speaker); kept the one-speaker splice "
                "'swing' + /z/ (as in the approved test shot)"),
    dict(searched="a second English 'binturong' recording (Lingua Libre any speaker; Wiktionary En-us-/En-uk-"
                  "binturong.ogg; Commons full-text 'binturong filetype:audio')",
         result="none: only LL-Q1860 (eng)-Vealhurl-binturong.wav (plus a French LL-Q150 recording, not used). "
                "Refrains reuse the one take (declared)."),
    dict(searched="'popcorn' by Grendelkhan", result="not found; used Vealhurl-popcorn (real word recording). "
                                                    "Grendelkhan 'pop' + 'corn' downloaded as fallback, unused"),
    dict(searched="Wiktionary En-us-hangs.ogg", result="missing on Commons"),
]
GAPS = [w["seg_id"] + " '" + w["text"] + "'" for w in M["words"] if w.get("gap")]
if GAPS:
    absences.append(dict(searched="download of the verified Grendelkhan smells/of/never/rings/pop/corn/ring and "
                                  "Vealhurl popcorn originals (licences verified: CC0 / CC BY-SA 4.0)",
                         result="DECLARED GAP: upload.wikimedia.org answered HTTP 429 to every attempt (originals and "
                                "mp3 transcodes) for ~45 min; words " + ", ".join(GAPS) + " are silent spans of "
                                "nominal length (0.24 s/syllable), mouthed silently. Rerun u1/fetch3.py, "
                                "u1/build_voice.py, u1/make_timeline.py to fill them (licences already recorded)."))
handmade = [dict(what="voice assembly (word-collage, trims, gaps, two /z/ splices) - no synthesis",
                 where=str(HERE / "build_voice.py")),
            dict(what="cue timeline, staged fictional responses, ledgers", where=str(HERE / "make_timeline.py")),
            dict(what="waveform/segmentation check image", where=str(PREP / "voice_poem_waveform.png"))]

tl = dict(
    slug="le-maki-mococo", unit="U1 reading/cue/staging", revision="cue_timeline r1", poem_revision="poem-r1",
    generated=str(datetime.date.today()), base=dict(plan="plan.md rev P1", prompt="prompts/le-maki-mococo.md"),
    owner="U1", read_set=["plan.md", "reading/*", "meta.json"], write_set=["cue_timeline.json",
                                                                         "credits_reading.json", str(PREP)],
    poem=poem, audio=audio, visemes=visemes, cues=CUES, responses=RESP, quarantined_counterexamples=QUARANTINE,
    fiction_consent_ledger=fiction, declared_silences_and_synth=silences, branches=branches,
    evidence=evidence, absences=absences, handmade=handmade,
)
out = SW / "cue_timeline.json"
json.dump(tl, open(out, "w"), indent=1, ensure_ascii=False)
json.dump(credits, open(SW / "credits_reading.json", "w"), indent=1, ensure_ascii=False)
# fixture check writes its result back into the timeline
r = subprocess.run([sys.executable, "-I", str(HERE / "fixture_check.py"), str(out)], capture_output=True, text=True)
print(r.stdout, r.stderr)
sys.exit(r.returncode)
