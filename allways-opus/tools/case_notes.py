# The builder's own notes for each film of the allways-opus run. exec'd by package_run.py (shares its namespace).
# Everything here is the maker's account; the critics' words are kept separately and verbatim.

STATE = {d: "proof in progress" for d in ("nobody-home", "almost-human", "terra", "split-second", "chase", "kinetic", "zero-memory", "homonym", "anybody", "collective", "planimetric")}
STATE["mnemonil"] = "proof reviewed"

# which critic rounds have packet images kept, and what cut each critic saw
PACKETS = {
    ("homonym", 1): "the first cut, before any repair", ("almost-human", 1): "the first cut, before any repair",
    ("chase", 1): "the first cut, before any repair", ("terra", 1): "the first cut, before any repair",
    ("anybody", 1): "the first cut, before any repair", ("collective", 1): "the first cut, before any repair",
    ("mnemonil", 1): "the first cut, before any repair", ("nobody-home", 1): "the cut before the stray-object flicker was masked",
    ("split-second", 2): "the cut after the pins were added, before the second cutaway was trimmed",
    ("planimetric", 2): "the 1927 doorway take as published", ("kinetic", 2): "the cut after the interval shot and the stopped-hand ending were added",
    ("zero-memory", 2): "the cut before the side-by-side was changed to the stretches where the two states differ",
}

SEEN_LATE = {
    "homonym": "I could not see this film's contact sheets or filmstrips while cutting it: every image read returned a request-limit error. I cut from search titles, Whisper word timings, durations and loudness numbers. After the cut I checked each reason against frames of the final film and corrected two that described things the frames do not show.",
    "almost-human": "I could not see this film's contact sheets or filmstrips while cutting it: every image read returned a request-limit error. I cut from search titles, Whisper word timings, durations and loudness numbers. After the cut I checked each reason against frames of the final film and corrected five that described things the frames do not show (a hand 'climbing' to a collar, a slip 'pocketed', hands 'in the air').",
    "split-second": "The first search sheets for this film failed to load the same way (request-limit errors). The filmstrips for the bowling film and the dives did load and were used. After the cut I checked all twelve reasons against frames and none needed changing.",
}

BUILDER = {
    ("homonym", 1): "The senses are listed more than relayed: fair. The panda frame the critic called a non sequitur was the source clip's own closing cut, caught by a held last frame; trimmed afterwards. The long repeated stretches were shortened.",
    ("almost-human", 1): "True on the line pinned to a gesture and on the missing return; both repaired. The film is still shorter than the 75 s the proof asks for.",
    ("split-second", 1): "True that the pins never arrived. A pin-fall shot from the same bowling film was added, with crash sound from a different one (recorded in the ledger), and the board hold was cut from 8.8 s to 5.5 s.",
    ("split-second", 2): "The pins the critic saw at 12-13 s are the shot added after round 1. The second cutaway was trimmed to before the hand opens after this round. The long run of falls and the napkin ending stand as objections.",
    ("chase", 1): "True about the ending: the girl in the sepia field stands still with nothing moving around her. Replaced by a crowd shot. The tennis court still appears twice (two stretches of one film).",
    ("kinetic", 1): "True: nothing in the first cut was an interval. A whole 10.8 s interval from Master Hands was added, and the film now ends on a stopped hand.",
    ("kinetic", 2): "The critic wants three processes, each with at least three visible repetitions. The film shows each process in one or two short shots; that is below the brief and was not repaired.",
    ("planimetric", 1): "True. The 1951 kitchen take was replaced rather than repaired: an obstruction cannot be staged in found footage, so the take itself had to change.",
    ("planimetric", 2): "The 'white-dot overlay' at 9 s is a rosette on the men's lapels, in the source; the two recognised words are hiss. An obstruction cannot be added to a found take, so this take also falls short; a better one has to be foraged.",
    ("terra", 1): "Partly: the ghosted horse image is the source's own decayed print, and nothing in this film is generated, but the film never says so. The park and harvester shots were reordered so the park comes right before the blank interval. Scratch overlaps at the cuts were not made.",
    ("anybody", 1): "The critic read the two halves as alternating one-second cuts. They play at the same time, each with its own sound. Date labels were too small: enlarged. The film now ends on a held pair. A wider context shot and dropping the 1957 clip were not done.",
    ("collective", 1): "Year and place captions were added to the first five shots and a closing card says the day is assembled. Still only about three distinguishable participants. As far as the ledger shows, the spoken lines sit on their own pictures (the kitchen and table clips), not on the other cultures' footage.",
    ("mnemonil", 1): "Captions were enlarged (26 px on a 720 px frame, about 3.6%). A narrated line over the last 15 seconds was not added.",
    ("zero-memory", 1): "Fair: the first version was four passes of the same five excerpts. A fifth editor, given a shuffled sheet and no list of what is said, was added as the changed recurrence.",
    ("zero-memory", 2): "The side-by-side was changed after this round to show the stretches where state 1 and state 4 differ. The closing statement rests on one trial.",
    ("nobody-home", 1): "No cup and no routine cannot be fixed with this footage; the brief wants a newly recorded room. The 0:23 flicker was real (tracking left a carried object visible for about two seconds) and was masked by hand afterwards. The film already shows the intact and removed passages back to back (0-32 s) before the split screen.",
}

NOTES = {
 "nobody-home": {
  "summary": "A boy crosses a fixed 1951 room, lifts a chair to the window and leaves it. The same seconds again with him erased: the chair moves by itself, then seventeen seconds of an empty room under his film's own sound. Recorded and derived are shown side by side, and the mask is shown.",
  "worked": ["A locked-off staged room (Speaking of Rubber, Part I, 1951) is the one kind of shot where removal is honest: the pixels behind him are visible elsewhere in the same shot.",
             "The mask comes from 14 clicks on 5 frames, placed by eye; replacement is the per-pixel median of frames where that pixel is unmasked; pixels never revealed are listed in the unknown map and filled by a visible-in-the-log inpaint.",
             "The film shows the intact take, the derived take, a side-by-side, and the mask, each captioned."],
  "failed": ["The first full removal run took about 85 minutes and looked dead, so I wrote a lighter second stage while it was still running. When the first finished it overwrote the patched files; the final files were regenerated from the patched mask.",
             "Tracking left an object he carried visible for about two seconds. I added a hand-drawn box to the mask for 15.0-17.3 s, disclosed in removal.json.",
             "There is no cup and no routine. The brief wants a newly recorded room; this film has archival staged footage, so what is 'ordinary' before the removal rests on one action by one boy."],
  "open": ["Record a room sequence for real (a person enters, places a cup, moves a chair, leaves) and run the same removal on it.", "Give the empty room an event at least every five seconds, as the critic asked."],
  "repairs": ["Masked the stray object that flickered in the empty room at 0:23."]},
 "almost-human": {
  "summary": "A man does up his collar and tie, first in profile and then facing us. Other people's small gestures begin and do not finish: a woman's hand rises to her mouth, a driver looks at his watch and away, a boy finds a loose button. The film returns to the first man, hands at the knot, and holds.",
  "worked": ["Ten searches written as actions ('a man checks his wristwatch and looks away'), not emotions. Instruction and etiquette films answered best.",
             "The long uncut collar sequence is a source film's own 'appearance' lesson, used almost whole because its pause after the adjustment is the point.",
             "The 1927 silent clips carry raised hiss on purpose, so the cut never goes quiet."],
  "failed": ["A line from the source film ('Isn't there a better way to manage ourselves?') had been left over a woman's gesture and assigned her a feeling. The critic was right; I rebuilt the audio under that shot from the source's own sound around the line.", "The first cut ended on a man not seen before and on a moral line. It now returns to the first man."],
  "open": ["48 s against 75 s.", "The proof wants one gesture whose outcome differs between two people inside a pair of shots; the cut shows differences in sequence, not as a pair."],
  "repairs": ["Removed the spoken line from under the woman's gesture.", "Replaced the closing shot with a return to the first man at the same wall, last frame held 3.6 s."]},
 "terra": {
  "summary": "A 1914 aerial of a harbour holds until its grey water starts to read as emulsion. A 1966 earthquake film's black arc crosses a tidal flat. A decayed 1963 print of a harvester and of skaters in a park come back out of white. The film ends on a blank 1915 interval with its own noise raised.",
  "worked": ["Searches for damage (scratches, nitrate decay, light leaks, countdown leaders, worn shore prints) returned many Apollo film-to-video transfers; the useful ones were two decayed 1963 'Mirror of America' prints, a 1914 aerial and a 1915 blank.", "Every source keeps its own sound. The blank's hiss is raised about 20 times so it can be heard as material."],
  "failed": ["The critic found no defect that carries the viewer from one fragment to the next. Cuts are hard cuts; scratch overlaps were not made.", "The decayed prints read as generated to the critic. They are the sources' own damage and nothing in the film is generated, but the film says nothing about that."],
  "open": ["Overlaps of at least eight frames where a scratch from the outgoing shot stays in the incoming one.", "A caption saying which damage is the source's."],
  "repairs": ["Reordered so the park skaters come immediately before the blank interval."]},
 "split-second": {
  "summary": "A bowler's approach is cut away from twice before his hand opens. The third time it opens, the ball goes and the pins fall. Dives, a tower fall and a demolition follow, phase by phase. A woman stays on a board. A cloth is put down.",
  "worked": ["A bowling instruction film (Let's Go Bowling, Part II, 1955) has a clean approach and release that can be cut at exact phases; the cutaways land on the backswing so the viewer waits for the release.", "The consequence sound (pins) comes from a different bowling film (Our Community, 1952), moved on purpose and recorded in the ledger."],
  "failed": ["After the pins the film is a run of falls rather than hands letting go; the dive, tower and fire material is not phase-aligned with the bowler's hand.", "The woman on the board is still a static hold; the napkin ending is not a hand release with visible hands.", "38 s against 50 s."],
  "open": ["Hand-release and hand-transfer shots before the ending.", "Contact sounds are unjudged because I cannot hear."],
  "repairs": ["Added the pins falling after the third release.", "Trimmed the board hold from 8.8 s to 5.5 s.", "Trimmed the second cutaway to before the hand opens."]},
 "chase": {
  "summary": "A runner on a beach at dusk, while a space-agency film praises its people. Running is handed across fifty years: 1922 policemen, a 1938 tennis court, a 1976 athlete waiting, two boys on a lawn, a girl in a 1915 field. The film now ends on a crowd in 2001.",
  "worked": ["A track announcer's line from a 1976 film is moved under the 1922 street as a sound bridge; every bridge is in the ledger.", "Direction is carried left to right across the first four shots."],
  "failed": ["The first ending, a girl standing still in a sepia field for 15 seconds, had no world moving around her. Replaced.", "The tennis court appears twice (two stretches of one film).", "44 s against 60 s."],
  "open": ["A stopped person with traffic or a crowd passing, for at least three seconds, shot as one take.", "The cut at 0:12 does not change place."],
  "repairs": ["Replaced the closing hold with a 2001 street crowd under a bank film's voice."]},
 "kinetic": {
  "summary": "Three kinds of work (a piston being fitted, a mallet and wedge, a tire-bead machine) share seven seconds of one sung work verse, then it breaks. A refinery worker, a man waiting beside hot rail in Belo Horizonte, a complete interval at a machine, and a hand that stops.",
  "worked": ["The verse comes from a 1951 film; each process is cut on its beat, and the coordination is allowed to last only seven seconds.", "The interval (a man looks into a machine, then reaches into it) runs 10.8 s at normal speed."],
  "failed": ["The first cut had no interval at all.", "The critic counts the three processes as one or two short shots each, not repeated movements; that is below the brief.", "59 s against 90 s."],
  "open": ["Three or more visible repetitions of each process before they are coordinated.", "A wide contextual shot of what the close crops leave out."],
  "repairs": ["Added the interval at the machine.", "Replaced the ending with a stopped hand, last frame held."]},
 "zero-memory": {
  "summary": "Fresh editors with no record of each other cut the same twelve excerpts. Three given a list of what each excerpt says made nearly the same five-excerpt film, which the film plays with a black card after each. A fifth editor, given a shuffled sheet and no list, made a different one, set beside the first.",
  "worked": ["The four editors never saw each other's results or this film. Each answer is kept verbatim in audit/log.json.", "The black reset cards and the identical first line make the recurrence recognisable."],
  "failed": ["I gave the first four editors a list of what is spoken in each excerpt. They built on it, so clearing their history changed almost nothing. The finding is about my prompt more than about forgetting.", "The finding rests on one trial; the film says so."],
  "open": ["Repeat with several seeds, several models, and with and without the list.", "Test what an editor does when the same history is cleared but the sheet is shuffled each time."],
  "repairs": ["Added the fifth editor with a shuffled sheet and no list.", "Enlarged the reset cards and held them longer."]},
 "homonym": {
  "summary": "A hand draws a line on a sheet, then a hand draws a tree. A rabbit stretches at a curtain as a narrator says 'draw'. A woman draws a curtain, a hand draws a pen out of a drawer, water is drawn from a well, a line is drawn across a map, spectators are drawn to a hall, a will is read in a drawing room. The film ends on the first hand: the line gets a dot.",
  "worked": ["Searching the lab's own word index (Whisper word timings for 4,559 archive films) for 'draw' found 25 spoken uses. Four of those films are in the cut: 'should draw in the picture', 'a line drawn from the center', 'things that draw people here', 'the drawing room'.", "Where no narrator says the word, the action carries the sense (the curtain, the drawer, the well)."],
  "failed": ["The senses are listed more than relayed: nothing carries a sense across a cut except the pulling arm.", "A held last frame once froze a closing cut of the source (a panda); trimmed.", "48 s against 60 s."],
  "open": ["A pivot that changes the stakes, not only the sense.", "Cut the repeated stretches under 2.5 s as the critic asked (partly done)."],
  "repairs": ["Trimmed the source's closing cut so the film ends on the drawing.", "Shortened the two long repeated stretches."]},
 "anybody": {
  "summary": "Pairs of strangers doing related things, side by side, each half with its own sound and its own date. 1961 and 1944 prepare a place to sit; one has sat down and the other has left the chairs empty. Iraq 1951 lights a fire in silence beside an American kitchen film talking about productivity. Two people sweep.",
  "worked": ["Each side keeps its own sound in its own ear, and a year is printed under each; undated sources say 'date unknown'.", "The inequality is left audible: one half has no sound at all."],
  "failed": ["The first caption text was unreadable; enlarged.", "The critic read the pairs as one-second alternating cuts; they play simultaneously. I could not tell from the sheet whether that is a flaw of the sheet or of the film.", "38 s against 90 s."],
  "open": ["A wider context shot for each side.", "Three pairs were asked for; the cut has four and is not tight."],
  "repairs": ["Enlarged the date and title labels.", "Ended on a held pair (about three seconds of last frames) instead of continuing to cut."]},
 "collective": {
  "summary": "A morning assembled from five films: a woman lays a table, a blind rises in Berlin, a woman at a sink, women washing in a river, a Dutch colonial washing channel and carriers. Each has its year or place on screen, and the film closes on a card saying it is not one morning.",
  "worked": ["Silent sources get another source's room sound under them; every borrowed bed is in the ledger.", "A carrying shot is cut before the camera moves in on a bare-chested woman, which the source film chose and this film declines."],
  "failed": ["Five distinguishable participants were asked for; the cut has about three.", "67 s against 120 s."],
  "open": ["A task left unfinished, explicitly (the sink shot leaves mid-sentence but is not marked).", "A caption naming each handoff."],
  "repairs": ["Added year and place captions and the closing card."]},
 "mnemonil": {
  "summary": "An invented narrator describes her mother in a yard, a kitchen and a field, and the footage does not agree: a different woman, a man in a hat, a roped-off exhibit kitchen at the 1939 World's Fair. The last fifteen seconds name every source and say the speaker is invented.",
  "worked": ["The narration was written after reading the frames, so its details fit (gloves, white dress, red chair, icebox) until the picture contradicts them.", "The voice is synthetic (Kokoro-82M) and labelled as invented in the film and the ledger."],
  "failed": ["The reveal is carried by captions after the speech stops; the critic found that a recap rather than a discovery.", "Captions were first too small."],
  "open": ["A narrated line over the last fifteen seconds.", "74 s against 120 s."],
  "repairs": ["Enlarged all captions."]},
 "planimetric": {
  "summary": "One camera, one doorway, Martinez, California, 1927. Men come out of a building and are stopped by others shaking hands in front of the door. One unbroken 36 seconds with only the source's own hiss, raised.",
  "worked": ["Locked-off found footage with real traffic in a doorway; nothing is cut."],
  "failed": ["The first take (a 1951 family supper with a narrator) was rejected by the critic: no obstruction, narration directing attention. I replaced it instead of repairing it.", "The second take shows one activity in one plane and repeats; no obstruction reroutes anyone.", "36 s against 90 s."],
  "open": ["A better take: two activities at different depths and a small deviation, not a cycle."],
  "repairs": ["Replaced the supper with the doorway take."]},
}


def EXTRAS(d, W, O, jpg):
    out = []
    if d == "nobody-home":
        r = json.load(open(os.path.join(W, "erase", "removal.json")))
        for s, t in (("m.jpg", "mask-montage.jpg"), ("d.jpg", "derived-montage.jpg"), ("leak.jpg", "patch-check.jpg")): jpg(os.path.join(W, "erase", s), os.path.join(O, "img", t))
        Image.open(os.path.join(W, "erase", "unknown.png")).convert("L").save(os.path.join(O, "img", "never-revealed.png"))
        shutil.copy(os.path.join(W, "erase", "removal.json"), os.path.join(O, "removal.json")); shutil.copy(os.path.join(W, "compare.mp4"), os.path.join(O, "compare.mp4"))
        out.append({"title": "Removal: recorded, revealed, invented", "html": f"<p>The person mask comes from SAM 2.1 (small), tracked from clicks placed by eye. Under the mask, each pixel is replaced by the median of the same pixel in nearby frames where it was not masked (a window of about 2.5 s, recomputed every half second; where a pixel was masked for the whole window, the median over the whole shot).</p><p><b>What is recorded, what is revealed, what is invented.</b> The frame outside the mask is recorded. Inside it, the replacement is <i>revealed</i>: computed from recorded pixels of the same shot at other moments, so it shows the room as it was when he stood elsewhere, not what the camera saw at that instant (film grain, flicker and any light change are averaged away). It is not generated. No pixel is hidden in every frame ({r['never_revealed_fraction']*100:.2f}% of the frame), so nothing needed to be invented; any pixel that had been would be white in the map below, and the map is empty.</p><p>Tracking left a carried object visible for about two seconds, and a hand-drawn box was added to the mask for derived seconds 15.0-17.3. The tracked mask and every parameter are in removal.json.</p>",
                    "images": [{"src": "img/mask-montage.jpg", "caption": "The mask, one frame per second."}, {"src": "img/derived-montage.jpg", "caption": "The derived shot, one frame per second: the chair moves and he is gone."}, {"src": "img/patch-check.jpg", "caption": "After the hand patch: derived 15.9 s, 16.6 s, and the published print."}, {"src": "img/never-revealed.png", "caption": "Pixels hidden in every frame (would be white): none."}],
                    "video": {"src": "compare.mp4", "caption": "Recorded (left) and derived (right), as shown in the film."}})
    if d == "zero-memory":
        A = json.load(open(os.path.join(W, "audit", "log.json"))); coll = json.load(open(os.path.join(W, "collection.json")))
        jpg(os.path.join(W, "collection-sheet.jpg"), os.path.join(O, "img", "collection-sheet.jpg")); jpg(os.path.join(W, "control-sheet.jpg"), os.path.join(O, "img", "control-sheet.jpg"))
        for n in ("log.json", "shuffle.json", "collection.json"): shutil.copy(os.path.join(W, "audit", n) if n != "collection.json" else os.path.join(W, n), os.path.join(O, n))
        def row(k, v): return f"<tr><td>{k}</td><td>" + ", ".join(f"{s[0]} {s[1]:g}-{s[2]:g}" for s in (v['shots'] if k == 'control' else [[x['x'] if isinstance(x, dict) else x[0], x['in'] if isinstance(x, dict) else x[1], x['out'] if isinstance(x, dict) else x[2]] for x in v['shots']])) + f"</td><td>{v['reason']}</td></tr>"
        rows = "".join(row(k, v) for k, v in A.items())
        cl = "".join(f"<li><b>{k}</b> {v[0]}, clip {v[1]}, source seconds {v[2]:g}-{v[3]:g}</li>" for k, v in coll.items())
        out.append({"title": "The five editors", "html": "<p>Each editor was a fresh agent with no record of any other. States 1-4 received a sheet of the twelve excerpts (below) <b>plus a list of what is spoken in each</b>. The control received the same excerpts on a shuffled, relabelled sheet <b>with no list</b>. Excerpt letters in the control row are mapped back to the collection's letters. State 4 gave the same answer as state 3, so the film plays states 1, 2, 3 and the control.</p><div class='w'><table><tr><th>state</th><th>shots (excerpt, in-out in seconds)</th><th>the editor's reason</th></tr>" + rows + "</table></div><p>The collection:</p><ul>" + cl + "</ul>",
                    "images": [{"src": "img/collection-sheet.jpg", "caption": "The sheet given to states 1-4."}, {"src": "img/control-sheet.jpg", "caption": "The shuffled sheet given to the control (letters Q-Z, M, N), no list of speech."}]})
    return out
