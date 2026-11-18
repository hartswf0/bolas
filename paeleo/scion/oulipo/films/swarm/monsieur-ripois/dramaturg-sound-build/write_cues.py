"""U1 dramaturg-sound: writes ledger.json and dialogue-cues.json (SCION #47 cue sheet).
All frame numbers are global film frames at 24 fps (frame = round(t*24)); film 44.0 s = 1056 frames."""
import json
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent
FPS = 24
f = lambda s: int(round(s * FPS))

# ------------------------------------------------------------ captions ---
captions = [
 dict(cue_id="CAP-C1a", claim="C1", shot="S1", fr="« Votre boîte… je l'ai rapportée chez votre tante le 14 mars, »",
      en="Your box... I brought it back to your aunt's on the 14th of March,",
      parts=[dict(text="« Votre boîte… ", onset=f(2.5)), dict(text="je l'ai rapportée ", onset=f(3.4)),
             dict(text="chez votre tante le 14 mars, »", onset=f(4.2))],
      on=f(2.5), off=f(5.4), words={"rapportée": f(3.4), "14 mars": f(4.8)}),
 dict(cue_id="CAP-C1b", claim="C1", shot="S1", fr="« en main propre. »", en="into her own hands.",
      parts=[dict(text="« en main propre. »", onset=f(5.4))], on=f(5.4), off=f(6.6), words={"main propre": f(5.6)}),
 dict(cue_id="CAP-C2a", claim="C2", shot="S1", fr="« Elle l'a ouverte devant moi. »", en="She opened it in front of me.",
      parts=[dict(text="« Elle l'a ouverte devant moi. »", onset=f(7.2))], on=f(7.2), off=f(9.0), words={"ouverte": f(7.6)}),
 dict(cue_id="CAP-C2b", claim="C2", shot="S2c", fr="« La bague y était. »", en="The ring was in it.",
      parts=[dict(text="« La bague y était. »", onset=f(14.8))], on=f(14.8), off=f(16.4), words={"bague": f(15.0)},
      note="over the shadow play; « — selon lui — » label stays on top of picture"),
 dict(cue_id="CAP-S2d", claim="C3-prep (part of C2/C3 account)", shot="S2d", fr="« Je l'ai refermée, je la lui ai donnée. »",
      en="I closed it, I gave it to her.",
      parts=[dict(text="« Je l'ai refermée, ", onset=f(17.6)), dict(text="je la lui ai donnée. »", onset=f(18.5))],
      on=f(17.6), off=f(19.4), words={"refermée": f(17.8)},
      note="caption follows the swallow (frames 406-413): the lid is shut while hidden, the words name it afterwards"),
 dict(cue_id="CAP-C3", claim="C3", shot="S3b", fr="« Rien n'y manquait. »", en="Nothing was missing from it.",
      parts=[dict(text="« Rien n'y", onset=567), dict(text=" manquait. »", onset=586)],
      on=567, off=f(28.5), words={"manquait": 586}, spoken_end=598,
      note="split point « Rien n'y » / « manquait. »; the second half is appended on the same line (no re-layout) at 586 = CUE-3 onset; 567/586 are the approved test-shot frames (23.625 s / 24.417 s)"),
]

title = dict(text="« Rien n'y manquait »", on=f(0.3), full=f(0.8), fade=f(1.5), off=f(2.0), style="white serif italic on black")
style = dict(font="Liberation Serif Italic (system) or equivalent serif italic", size_px_at_960x540=26, color="#f4f2ec",
             edge="1 px dark edge #101010 at 60 %", band=False, position="bottom of 720x540 picture area, baseline 36 px above picture bottom",
             quotes="« » with non-breaking spaces", label_S2="« — selon lui — » top centre of picture, same face 18 px, 80 % opacity, every S2 frame 216-467")

# ------------------------------------------------------------ gesture keys ---
def key(cue_id, clause, onset, who, action, a_on, ease, hold, a_end=None, deg=None, notes="", listener=False, sound=None):
    d = dict(cue_id=cue_id, clause=clause, onset_frame=onset, who=who, action=action, action_onset_frame=a_on,
             action_end_frame=a_end, ease=ease, hold=hold, listener_action=listener)
    if deg is not None: d["value"] = deg
    if sound: d["sound"] = sound
    if notes: d["notes"] = notes
    return d

master = [
 key("CUE-0", "(silence; room tone in at 1.5 s)", f(2.0), "her", "box HELD in both hands at lap height (fingers occlude box edges), head 0 deg", f(2.0),
     "none", "hold to CUE-1b", listener=True, notes="expressive hold: she listens; no motion without a reason"),
 key("CUE-1", "CAP-C1a « je l'ai rapportée »", f(3.4), "him", "lean in, torso/head 0 -> +3 deg (toward her), drawings on twos", f(3.4),
     "ease-in-out (smoothstep)", f"hold +3 to {f(4.4)}, back to 0 by {f(5.0)}", a_end=f(3.9), deg=3.0, sound="cushion creak at frame 82"),
 key("CUE-1h", "CAP-C1a + CAP-C1b (whole of C1)", f(2.5), "her", "head HOLDS at 0 deg (no reaction to C1: P4 / no early suspicion)", f(2.5),
     "none", "0 deg until CUE-3", listener=True, deg=0.0),
 key("CUE-1b", "CAP-C1b « en main propre »", f(5.4), "her", "sets the box down on her lap: hands lower 0 -> 1 (box drops ~38 px at 720x540), contact, 2 px settle bounce, fingers stay on box sides", f(5.5),
     "ease-in (accelerate) then contact at 144, 1-frame squash, settle by 150", "hold box on lap (fingers on its sides) to end", a_end=144, listener=True,
     sound="soft lap set-down at frame 144 (fabric-muffled wood/metal tick)",
     notes="she accepts the object: E1 materially corroborates C1 in front of the viewer"),
 key("CUE-2a", "CAP-C2a « Elle l'a ouverte devant moi »", f(7.2), "her", "thumbs press the clasp; lid lifts 0 -> 10 % (one drawing), held at the cut", 185,
     "ease-out, 2 drawings", "lid at 10 % to the cut at 216", a_end=196, listener=True, deg=0.10, sound="clasp tick (dry) at frame 186",
     notes="she checks the thing he names, with her hands, not her head (head still under C2); master only. Baseline: thumbs rest, lid stays closed"),
 key("CUT-S2", "end of CAP-C2a", f(9.0), "edit", "hard cut to shadow theatre; warm paper +5 %, « — selon lui — », muffled reverberant bed", f(9.0), "cut", "S2 216-467"),
 key("SH-1", "(teller's image) door", f(9.0), "shadow R.", "door opens (3 drawings), R. enters, 8-pose walk on twos, far arm bent behind back", f(9.0),
     "on twos", "", a_end=f(12.0), sound="latch 220, hinge 222-236, footsteps 240 252 264 276 (muffled)"),
 key("SH-2", "(teller's image) offer", f(12.0), "shadow R.", "offers box with near hand (6 drawings); far hand inside torso silhouette", f(12.0), "on twos", "", a_end=f(14.5),
     sound="box tick into the aunt's hands at 341 (muffled)"),
 key("SH-3", "CAP-C2b « La bague y était »", f(14.8), "shadow aunt", "aunt opens lid (4 drawings started at 348, before the line: the image shows what the line will name); ring as punched light ring; earring swings", f(14.5),
     "on twos; earring pendulum secondary", "", a_end=f(16.5), sound="soft hinge creak 349-362 (muffled)",
     notes="teller-side action: the image may precede the clause because it is his illustration, not a listener reaction (P4 applies to listener actions only)"),
 key("SH-4", "(teller's image) the swallow", f(16.5), "shadow R.", "closes lid with near hand while body turns ~10 deg; box behind torso 406-413 (8 frames); elbow +6 deg; box re-emerges closed; handed to aunt, set on her lap", f(16.9),
     "on ones during swallow", "", a_end=f(19.5), sound="lid shut, muffled, at 408 (inside the swallow; heard, not seen); set-down tick 456; NO ring sound (declared silence)"),
 key("CUT-S3a", "after CAP-S2d", 468, "edit", "hard cut to present insert: open box on her lap, ring slot EMPTY at the same normalised position as the ring in S2c; tint neutral; dry sound", 468, "cut",
     "insert 468-515 (slight motion: 1.5 % slow push-in + her breathing lift 1 px)", sound="room tone + clock return dry on frame 468"),
 key("CUT-S3b", "(silence)", 516, "edit", "cut to two-shot, box open on her lap", 516, "cut", ""),
 key("CUE-3pre", "(breath before C3)", 552, "him", "lean in starts, planned 0 -> +4 deg by 605", 552, "ease-in-out", "", a_end=605, deg=4.0,
     notes="he leans in to close the case"),
 key("CUE-3", "CAP-C3 « manquait. »", 586, "her", "head (with hat brim) drops -11 deg toward the box", 586, "ease-out over 8 frames (586-594)",
     "hold -11 deg to S4 turn at 734", a_end=594, deg=-11.0, listener=True, notes="first moving frame of her head == onset of « manquait » (acceptance 4: +-2 frames)"),
 key("CUE-3s", "CAP-C3 (her drop)", 586, "him", "lean STOPS where it is (~+2.6 deg); he holds still: he notices", 586, "ease-out to stop", "hold to CUE-3h",
     a_end=591, notes="last moving frame <= 592 (within 6 frames of the drop)"),
 key("CUE-3h", "(silence after C3: silence animates thought)", 648, "him", "far (right) hand comes forward from behind his thigh onto his knee: the hand the shadow hid", 648,
     "ease-in-out, on twos", "hold on knee to end", a_end=672, sound="small fabric rustle 648-672",
     notes="answers the swallow: the gesture the telling concealed is now shown in the room"),
 key("CUE-4", "(object event) slip falls from his breast pocket", 706, "him/object", "folded slip slides out (accelerate), falls to the sofa cushion between them, one small bounce, settles", 706,
     "gravity: accelerate 706-718, contact 718, bounce 6 px 718-722, settle 725", "rest on cushion", a_end=725, sound="paper tick on contact 718, whisper 718-726"),
 key("CUE-4L", "slip landing sound (frame 718)", 718, "her", "head turns from the box toward the slip (-11 -> -6 deg, 4 deg toward him)", 734,
     "ease-in-out 10 frames", "hold to insert", a_end=744, listener=True, notes="impact cue -> reaction spaced 16 frames (#47: impact and reaction appropriately spaced)"),
 key("CUE-4i", "(insert) receipt", 756, "her hand", "unfolds the receipt (3 drawings: 756, 770, 784); slow hold on the date line « Engagé le 14 mars 1953 »", 756,
     "on drawings", "hold 784-863", a_end=784, listener=True, sound="fold opening 756, 770, 784; clock"),
 key("CUE-5a", "(no caption) receipt into slot", 888, "her", "lays the receipt in the empty slot", 893, "ease-in-out", "", a_end=922, listener=True, sound="paper into velvet 918"),
 key("CUE-5b", "(no caption) lid", f(39.5) - 8, "her", "closes the lid (2 drawings), click on contact", f(39.5) - 8, "ease-in", "lid closed to end", a_end=f(39.5),
     listener=True, sound="lid click (dry, close) at 948"),
 key("CUE-5c", "lid click (frame 948)", 948, "her", "turns her head away from him +8 deg (toward frame edge) and holds", f(40.5), "ease-in-out 10 frames",
     "hold to black at 1032", a_end=f(40.5) + 10, deg=8.0, listener=True),
 key("CUE-5d", "(her turn away)", 972, "him", "does not move (declared hold)", 972, "none", "hold to black", listener=False),
 key("END", "(silence)", f(42.0), "sound", "room tone fades 1008-1032; black 1032-1055; silence", f(42.0), "linear fade", ""),
]

late_diff = [
 dict(cue_id="CUE-3", clause="CAP-C3 « manquait. » (line spoken_end 598)", onset_frame=586, who="her",
      action="head drops -11 deg toward the box", action_onset_frame=610, action_end_frame=618, ease="ease-out over 8 frames",
      hold="hold -11 deg to 734", value=-11.0, listener_action=True,
      notes="--late: line end 598 + 12 = 610; the word lands, then she checks"),
 dict(cue_id="CUE-3s", clause="CAP-C3 (her late drop)", onset_frame=586, who="him", action="lean completes to +4 deg at 605 (he is not stopped by her), then freezes when she drops", action_onset_frame=610,
      action_end_frame=610, ease="none (already at rest)", hold="hold +4 deg to CUE-3h", listener_action=False),
]

def p4(keys):
    out = []
    for k in keys:
        if not k.get("listener_action"): continue
        out.append(dict(cue_id=k["cue_id"], onset_frame=k["onset_frame"], action_onset_frame=k["action_onset_frame"],
                        holds=k["action_onset_frame"] >= k["onset_frame"]))
    return out

late_keys = [next((d for d in late_diff if d["cue_id"] == k["cue_id"]), k) for k in master]
assertions = dict(
  rule="P4: for every listener action, action_onset_frame >= onset_frame of its clause, in every cut",
  master=p4(master), late=p4(late_keys),
  head_still_under_C1_C2=dict(frames=[f(2.5), 585], her_head_deg=0.0, holds=True),
  master_head_on_word=dict(first_moving=586, manquait_onset=586, tol=2, holds=True),
  late_head_after_line=dict(first_moving=610, line_end=598, min_gap=12, holds=610 - 598 >= 12),
  his_stop_within_6=dict(her_drop=586, his_last_moving=591, holds=591 - 586 <= 6),
  cut_back_frame_dry=dict(frame=468, reverb_wet=0.0, tint_shift=0.0, label=False),
)
assert all(a["holds"] for a in assertions["master"] + assertions["late"])

baseline = dict(
  definition="same script, --baseline: identical timing; (1) S3a insert 468-515 replaced by the two-shot held with the lid CLOSED (CUE-2a lid lift omitted: thumbs rest on the lid); (2) her head 0 deg throughout (CUE-3, CUE-4L, CUE-5c removed); his lean CUE-3pre runs to +4 and holds (no stop, nothing to notice), CUE-3h kept; (3) S4/S5 (receipt fall, insert, receipt into slot, lid close, turn) removed: two-shot held 696-1008, then fade",
  sound="identical beds; receipt, lid and slot sounds (718-948) removed; clock continues",
  expected_reading="C1 and E2 consistent; nothing contests him")

cues = dict(
  slug="monsieur-ripois", fps=FPS, frames_total=f(44.0), base_plan="films/swarm/monsieur-ripois/plan.md §6", time_base="global film frames, 0 = film start",
  owner="U1 dramaturg-sound", swarm_technique="#47 Sound-to-Action: every gesture keyed to a speech or sound event; holds and silences are scored",
  title_card=title, caption_style=style, captions=captions,
  viseme_track=dict(value=None, reason="voice is captions only (no TTS, no foraged speech); the photo-cutout mouths are not animated, so there is no mouth flapping in silence. Speaking is carried by caption timing and his lean (CUE-1, CUE-3pre); her silence is scored as holds."),
  gesture_keys=dict(master=master, late=late_keys, late_diff=late_diff, baseline=baseline),
  silences=[dict(frames=[586, 706], what="no caption, no voice; clock only + his hand rustle at 648: the look is the event"),
            dict(frames=[948, 1032], what="no caption; lid click then clock; her turn away is the answer"),
            dict(frames=[406, 413], what="no ring sound during the swallow (declared silence; the lid shut is heard at 408)")],
  assertions=assertions,
)
(OUT / "dialogue-cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1))

# ------------------------------------------------------------ ledger ---
ledger = dict(
 slug="monsieur-ripois", revision="U1 ledger v1 (2026-11-16), base plan.md as read 2026-11-16, prompt prompts/monsieur-ripois.md",
 note="The event ledger is ground truth and independent of every telling; it is never shown on screen as such.",
 events=[
  dict(event_id="EV1", when="14 March 1953, afternoon", who=["R. (André Ripois)", "the aunt"], where="the aunt's flat",
       what="R. brings the borrowed silver box, with the ring in its slot, back to the listener's aunt."),
  dict(event_id="EV2", when="14 March 1953, same visit", who=["the aunt", "R."],
       what="The aunt opens the box and sees the ring. R. closes the lid; as he turns, the box passes behind his body and he palms the ring with his far hand. The aunt receives the closed box."),
  dict(event_id="EV3", when="14 March 1953, the same day, after the visit", who=["R."], where="Mont-de-Piété, bureau auxiliaire n° 7 (fictional number)",
       what="R. pawns « une bague or, un brillant » for 9 000 F; a receipt is issued to the depositor « A. R. »."),
  dict(event_id="EV4", when="later (before the present encounter)", who=["the aunt", "the listener"],
       what="The aunt passes the box to the listener; the ring slot is empty."),
 ],
 claims=[
  dict(claim_id="C1", speaker="R.", target_listener="the woman (the aunt's niece)", text="« Votre boîte… je l'ai rapportée chez votre tante le 14 mars, en main propre. »",
       asserted_event="EV1", truth="true", desired_effect="credibility: establish himself as the honest returner; draw her closer",
       timeline_position=dict(told_at_frames=[60, 158], refers_to="EV1 (14 March)"), origin="dialogue-cues.json CAP-C1a, CAP-C1b"),
  dict(claim_id="C2", speaker="R.", target_listener="the woman", text="« Elle l'a ouverte devant moi. » / « La bague y était. »",
       asserted_event="EV2 (first half: the aunt opened it and saw the ring)", truth="true but partial",
       desired_effect="move any doubt onto the aunt and onto the time after his visit",
       timeline_position=dict(told_at_frames=[[173, 216], [355, 394]], refers_to="EV2 opening"), origin="dialogue-cues.json CAP-C2a, CAP-C2b"),
  dict(claim_id="C3", speaker="R.", target_listener="the woman", text="« Je l'ai refermée, je la lui ai donnée. » … « Rien n'y manquait. »",
       asserted_event="EV2 complete, with nothing removed", truth="false (EV2 second half, EV3)",
       desired_effect="closure: end the question and be cleared",
       timeline_position=dict(told_at_frames=[[422, 466], [567, 684]], refers_to="EV2 closing / hand-over"), origin="dialogue-cues.json CAP-S2d, CAP-C3"),
 ],
 evidence=[
  dict(evidence_id="E1", what="the silver box itself, held then set on her lap (closed, S1)", shot="S1", frames=[48, 215],
       event_relation=dict(kind="supports", event_id="EV1"), relation_to_claims=dict(C1="corroborates"),
       perspective="room", certainty="observed", role="the corroborating image",
       origin="HANDMADE box (present_puppets.py render_twoshot, box-spec.json) on FORAGED LoC 2017831564 plate"),
  dict(evidence_id="E2", what="the shadow-theatre flashback: entry, offer, aunt opens lid, ring visible, the swallow, hand-over", shot="S2a-S2d", frames=[216, 467],
       event_relation=dict(kind="supports", event_id="EV1", also_supports="EV2 first half", silent_on="the palm (EV2 second half)"),
       relation_to_claims=dict(C1="illustrates", C2="illustrates", C3="illustrates (but hides the decisive gesture)"),
       perspective="teller", certainty="subjective", marking="warm paper +5 %, « — selon lui — », lowpassed reverberant sound bed; all three removed on frame 468",
       origin="HANDMADE shadow_theatre.py render_flashback"),
  dict(evidence_id="E3a", what="the open box on her lap with the ring slot EMPTY (same box, same slot geometry as the ring in S2c)", shot="S3a, S3b", frames=[468, 695],
       event_relation=dict(kind="ambiguous", event_id="EV2", note="contests C3 (something is missing now) but not who took it or when (EV4 vs EV2)"),
       relation_to_claims=dict(C3="contests (ambiguous)"), perspective="material", certainty="material",
       role="the ambiguous image", origin="HANDMADE box state 'open-empty' (render_box_insert)"),
  dict(evidence_id="E3b", what="the pawn receipt that slips from his breast pocket: « Engagé le 14 mars 1953 · une bague or, un brillant · Déposant : A. R. »", shot="S4, S5", frames=[706, 1031],
       event_relation=dict(kind="contests", event_id="EV2", dates="EV3 = the day of EV1", supports="EV3"),
       relation_to_claims=dict(C3="contests directly", C1="its date confirms the visit day, turning his alibi against him"),
       perspective="material", certainty="material", origin="HANDMADE receipt (render_receipt_insert)"),
 ],
 listener_state=[
  dict(t=[0.0, 2.0], frames=[0, 47], hears="silence, room tone from 1.5 s", sees="title", infers="nothing", withholds="—"),
  dict(t=[2.0, 9.0], frames=[48, 215], hears="C1, C2a", sees="the closed box in her own hands (E1), then on her lap", infers="the box did come back (E1 corroborates C1)", withholds="judgement; she opens the lid a crack (CUE-2a) but does not look at him", acts="sets the box down on « en main propre »; thumbs open the clasp on « ouverte »"),
  dict(t=[9.0, 19.5], frames=[216, 467], hears="his account (C2b, the closing line), muffled", sees="nothing of the room: the viewer sees HIS image (E2, marked as his)", infers="(viewer) the ring was there when he closed it; the box passed behind him for 8 frames", withholds="—"),
  dict(t=[19.5, 24.4], frames=[468, 585], hears="clock, dry; « Rien n'y »", sees="the empty slot (E3a) where the told ring stood", infers="something is missing now; not yet whose doing", withholds="her head stays still"),
  dict(t=[24.4, 29.0], frames=[586, 695], hears="« manquait. », then silence and clock", sees="the empty slot; his hand coming to his knee", infers="contradiction: his 'nothing was missing' against the empty slot (the look)", withholds="speech", acts="head drops -11 deg on the word"),
  dict(t=[29.0, 36.0], frames=[696, 863], hears="paper falling, unfolding", sees="the receipt dated 14 March (E3b)", infers="he pawned the ring the same day he returned the box", withholds="speech", acts="turns to the slip; unfolds it"),
  dict(t=[36.0, 43.0], frames=[864, 1031], hears="lid click, clock", sees="him not moving", infers="decided", withholds="any reply", acts="lays the receipt in the empty slot, closes the lid, turns her head away from him"),
 ],
 agendas=dict(
  teller=dict(who="R.", wants_now=["to be cleared of the missing ring", "to be let closer (the lean)"], tactic="tell the return as complete and witnessed; let the flashback illustrate it; name the closing only after it has passed unseen", resistance="the box on her lap; the receipt in his pocket"),
  listener=dict(who="the woman", wants_now=["to locate the ring", "to decide whether to trust him"], tactic="listen without reacting; check the object, not his face", decision="ends the encounter: receipt into the slot, lid closed, turns away"),
 ),
 cut_links=[
  dict(cut="S1 -> S2 at 216", claim="C2a", to_evidence="E2", listener_after="(off-screen) the viewer takes his perspective, marked as his", preconditions=["P1 C2 != E2", "P2 perspective encoded"]),
  dict(cut="S2 -> S3a at 468", claim="C3 (closing line)", to_evidence="E3a", listener_after="sees empty slot at the told ring position", preconditions=["P3 same box geometry; slot centre within 5 % box width on screen"], consequence="O1, O3"),
  dict(cut="S3a -> S3b at 516", claim="C3 « Rien n'y manquait »", to_evidence="E3a held (box open on lap)", listener_after="head drop on 586", preconditions=["P4"], consequence="O2"),
  dict(cut="S3b -> S4 insert at 756", claim="C3 / C1 date", to_evidence="E3b", listener_after="infers same-day pawning; acts in S5"),
 ],
 variants=dict(
  master="as dialogue-cues.json gesture_keys.master",
  baseline=baseline["definition"] + ". Expected: C1 and E2 read consistent; nothing contests him.",
  late="identical to master except her head drop onset at 610 (= line end 598 + 12) and his lean not stopped by her (completes at 605). Divergent leverage: early = the word itself triggers her check; late = the word lands, then she checks.",
  replay_equivalence="E2 (frames 216-467) is frame-identical across master, baseline and --late",
 ),
 invariants_checked_here=["each claim and each evidence item has its own id and origin", "C3 and E2 both survive as distinct entries", "every pivotal line (C1, C2, C3) has a listener consequence with frame numbers (CUE-1b, CUE-2a, CUE-3)", "P4 holds in master and --late (see dialogue-cues.json assertions)"],
)
(OUT / "ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=1))
print("ok", len(master), "keys")
