"""Write ledger.json (frozen b1 event graph) and panels.json (BaselinePage record) from the page build outputs."""
import json
from pathlib import Path
B = Path(__file__).resolve().parent
SW = B.parent
sp = json.load(open(B / "speech.json"))
chk = json.load(open(B / "page_checks.json"))
PANELS = {"P1": (150, 150, 890, 1090), "P2": (950, 150, 1610, 1090), "P3": (1670, 150, 2400, 1090),
          "P4": (150, 1160, 710, 2100), "P5": (770, 1160, 1740, 2100), "P6": (1800, 1160, 2400, 2100),
          "P7": (150, 2170, 1150, 3150), "P8": (1210, 2170, 2400, 3150)}
ev = [
 dict(id="E0", verb="reads memo", agent="CLERK", objects=["MEMO", "DESK", "PENCIL"], place="OFFICE_DESK", causes=["E1"], caused_by=[],
      fact="The clerk, at his desk, has the memo '4:15 - open SERVICE door. Key in cupboard.' before him.",
      cue="P1: handmade memo slip on the ledger, legible pencil lines; clerk seated, pencil at temple, eyes down.",
      interpretation="He has a job to do at 4:15: fetch the key from the cupboard and open the service door.", panels=["P1"]),
 dict(id="E1", verb="leaves desk", agent="CLERK", objects=["DESK", "MEMO"], place="OFFICE_DESK -> CUPBOARD", causes=["E4"], caused_by=["E0"],
      goal="fetch BRASS_KEY from CUPBOARD",
      fact="The clerk gets up and leaves the desk, heading across the office toward the cupboard and the SERVICE door.",
      cue="P2: same view as P1, the desk left empty but for the memo, only his shoulder leaving the right edge; P3: he walks, standing (cut at the waist by the panel edge), past the closed double cupboard whose right leaf carries the SERVICE card; no desk in frame.",
      interpretation="He is going for the key.", panels=["P2", "P3"]),
 dict(id="E2", verb="asks the time", agent="VISITOR", objects=["TICKET_WINDOW", "COUNTER_BELL"], place="PLATFORM (off-panel)", causes=["E3"], caused_by=[],
      interrupts="E1",
      fact="A visitor outside the ticket window asks 'What time is it?'. (Film only: the counter bell rings once before.)",
      cue="P4: nobody is drawn behind the TICKET OFFICE glass; the balloon tail runs out of the panel's left edge through the window to the platform; the clerk's head, tipped up toward the voice, enters at the right edge.",
      interpretation="Someone on the platform has stopped him on his way.", panels=["P4"]),
 dict(id="E3", verb="answers", agent="CLERK", objects=["CLOCK"], place="OFFICE", causes=["E3b"], caused_by=["E2"],
      fact="The clerk answers 'Ten past four!'; the office clock reads 4:10.",
      cue="P5: clock on the wall at 4:10 (its own hands re-set on the arbor); balloon tail to the clerk's mouth.",
      interpretation="It is five minutes before the 4:15 job.", panels=["P5"]),
 dict(id="E3b", verb="thanks and leaves", agent="VISITOR", objects=["TICKET_WINDOW"], place="PLATFORM (off-panel)", causes=[], caused_by=["E3"],
      fact="'Thanks!' comes from outside; the visitor is gone.",
      cue="P6: the ticket window now empty (no figure behind the glass); balloon tail exits the panel's left edge.",
      interpretation="She has left; the interruption is over.", panels=["P6"]),
 dict(id="E4", verb="opens cupboard", agent="CLERK", objects=["CUPBOARD_DOOR", "BRASS_KEY"], place="CUPBOARD", causes=["E5"], caused_by=["E1"],
      fact="The clerk reaches the cupboard; its door is open on its jamb and the brass key hangs on its hook inside the door, tagged SERVICE.",
      cue="P7: door swung open on the left jamb; key and SERVICE tag on the hook on the door's inner face; clerk arriving at right; SERVICE card on the closed door beside it.",
      interpretation="The goal is within reach.", panels=["P7"]),
 dict(id="E5", verb="forgets", agent="CLERK", objects=["PENCIL", "BRASS_KEY", "SERVICE_DOOR"], place="CUPBOARD", causes=[], caused_by=["E2", "E3", "E4"],
      outcome="goal lost: key stays on its hook, SERVICE door stays closed",
      fact="Before the open cupboard, pencil to chin, the clerk asks himself 'Now... what did I come over here for?'. The key stays on its hook; the service door stays closed.",
      cue="P8: key on its hook on the open door at left, unmoved from P7; his eyes cast down at the shelves, away from it; pencil at his chin; SERVICE card on the still-closed door; balloon tail to his mouth.",
      interpretation="The interruption made him forget the key.", panels=["P8"]),
]
ledger = {"slug": "99-ways-template", "revision": "b1", "frozen": True, "owner": "page-cartoonist",
          "participants": {"CLERK": "the Randolph, Vermont station agent (Rothstein 1937)", "VISITOR": "a woman on the platform, seen once as a soft shape through the ticket-window glass (Bubley 1943 figure)"},
          "objects": ["DESK", "MEMO", "CHAIR", "TICKET_WINDOW", "CLOCK", "CUPBOARD", "CUPBOARD_DOOR", "BRASS_KEY", "SERVICE_DOOR", "PENCIL", "COUNTER_BELL"],
          "places": ["OFFICE_DESK", "TICKET_WINDOW", "CUPBOARD", "PLATFORM (off-panel)"],
          "fixture": {"speakers": {"What time is it?": "VISITOR (off-panel, platform, through the window)", "Ten past four!": "CLERK",
                                   "Thanks!": "VISITOR (off-panel, leaving)", "Now... what did I come over here for?": "CLERK"},
                      "destination": "CUPBOARD, for the BRASS_KEY", "interruption": "E2", "outcome": "goal not achieved; key remains on hook; SERVICE door stays closed"},
          "order": ["E0", "E1", "E2", "E3", "E3b", "E4", "E5"], "events": ev,
          "seed": "section-10 station incident as re-told by Direction 2: visitor, brass key, service door stays closed kept; bell is a sound cue only; envelope and bench dropped; key stays on its hook in the cupboard.",
          "staging_notes": ["r1 (editor): P5 and P8 show the clerk un-mirrored (facing right): in P5 he faces the clock, in P8 he faces away from the key on the door at his left; P4 and P3 show head and torso only (the pencil hand below the frame).", "SERVICE door = the right-hand leaf of the Rothstein double cupboard, carrying the handmade SERVICE sign-card; the key cupboard is its left leaf. (plan.md section 5 placed the SERVICE door at P8's far left edge; it sits at P8's upper right instead, still visible and closed.)",
                            "P8 head keeps its photographed angle (eyes cast down to the shelves); no 2D roll of the head, per the test-shot note. No second photograph of this agent exists at LoC (searched); no replacement head was found that matches."]}
json.dump(ledger, open(SW / "ledger.json", "w"), indent=1)

vp = {"P1": "objective eye level, medium-wide: desk, clerk seated (Rothstein's own framing)",
      "P2": "same camera as P1, shifted 0.2 panel right: the desk left empty",
      "P3": "same scale, toward the back of the office: cupboard + SERVICE door",
      "P4": "inside the ticket office, at the TICKET OFFICE window (narrow vertical)",
      "P5": "medium close on the clerk under the office clock",
      "P6": "the ticket window again, empty (narrow vertical)",
      "P7": "wide on the cupboard, door open on its jamb",
      "P8": "medium close: clerk before the open cupboard, key in view"}
evid = {"P1": ["clerk seated at desk", "memo slip legible: 4:15 - open / SERVICE door. / Key in cupboard.", "pencil at temple"],
        "P2": ["desk empty, memo still on it", "clerk rising out of the right edge"],
        "P3": ["clerk mid-step", "closed door with SERVICE sign-card", "cupboard"],
        "P4": ["visitor as soft shape behind frosted TICKET OFFICE glass", "clerk's head turned to the window", "tail exits left edge"],
        "P5": ["clock at 4:10", "clerk answering"],
        "P6": ["empty ticket window", "Thanks! tail exits left edge"],
        "P7": ["cupboard door open on jamb", "brass key on hook with SERVICE tag", "SERVICE door closed"],
        "P8": ["key on hook, unmoved", "clerk's eyes away from the key", "pencil at chin", "SERVICE door closed"]}
film = {"P1": [4, 9], "P2": [9, 14], "P3": [14, 19], "P4": [19, 24], "P5": [24, 29], "P6": [29, 34], "P7": [34, 39], "P8": [39, 46]}
evmap = {"P1": ["E0"], "P2": ["E1"], "P3": ["E1"], "P4": ["E2"], "P5": ["E3"], "P6": ["E3b"], "P7": ["E4"], "P8": ["E5"]}
fk = chk["fk"]
panels = {"slug": "99-ways-template", "revision": "b1", "page": "assets/pages/99-ways-template.png", "page_px": [2550, 3300], "dpi": 300,
          "margins_px": 150, "gutters_px": {"horizontal": 60, "vertical": 70}, "tiers": [[150, 1090], [1160, 2100], [2170, 3150]],
          "route_R0": ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"], "balloon_order": "top-left first within a panel",
          "tone": chk["tone"], "rest_identity": chk["rest_identity"],
          "panels": [{"id": k, "bounds_px": list(PANELS[k]), "events": evmap[k], "viewpoint": vp[k],
                      "speech": sp.get(k, []), "visible_evidence": evid[k], "film_in_out_s": film[k],
                      "rest_layers": f"films/swarm/99-ways-template/page/rest/{k}/layers.json",
                      "rig_rest": fk.get(k), **({"key_hook": fk[k + ".key"]} if k + ".key" in fk else {})} for k in PANELS],
          "pose_pencil_to_chin": chk["pose_chin"],
          "coords": "speech/balloon/rig coordinates are panel-local px (add bounds x0,y0 for page px); rig matrices map source S3 px (Rothstein master/3) to panel px"}
json.dump(panels, open(SW / "panels.json", "w"), indent=1)
print("ok")
