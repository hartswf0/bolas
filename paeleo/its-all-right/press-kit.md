# IT'S ALL RIGHT

**come here · it's all right · come in**
PAE-02 · Bolas · 2026
A film by Watson Hartsoe

Press kit for festival programmers (short film, animation, experimental and expanded-cinema strands).

---

## 1. Loglines

**A.** "Come here" drives a dog away. "It's all right" turns its head. "Come in" brings it to the door, and no further. A film about what words can do. *(29 words)*

**B.** A command fails, a reassurance lands, an invitation is answered on the dog's own terms. One scene, told at once in cut paper, code, archive film and print. *(28 words)*

**C.** Some words push and some words open. A wary dog at dusk hears both, and every telling of it, in every material, has to hear them the same way. *(29 words)*

**Recommended: A.** It puts the three sentences themselves on the page, and each one lands differently. The reader feels the turn before learning anything about method. Use B where the strand cares about translation and materials, and C for a programme note that leads with the idea.

---

## 2. Synopses

### Short synopsis (about 60 words)

Dusk, a porch, a doorway. A person calls a dog: *Come here.* It backs away. Called again and reached for, it turns its back. Then the person stops asking: they sit, the door opens, a hand is offered low. *It's all right*, softly, and the dog's head comes round. It comes, lies across the sill, hears *come in*, looks inside, and stays.

### Long synopsis (about 250 words)

*It's All Right* is a film about the communication act: what words do to a listener who cannot be commanded.

Three sentences are spoken to a dog on a porch at dusk. The first is a directive, *Come here*, and it fails: the dog backs away. Said again, with a hand reaching out, it fails harder, and the dog turns its back. The second sentence makes no demand at all. Before it is spoken the person has already said it with their body: they stepped aside, sat down beside the door, let the door open and the light come out, and offered a hand, low. Then, softly, *it's all right*. The dog's head comes round. It waits, and in its own time comes, head low, and lies down across the sill, half in and half out. Only then comes the third sentence, an invitation: *Come in.* The dog looks into the lit room and stays where it is.

The scene is driven by a written score. A decision machine turns each line and each gesture into pressure, threat, invitation and trust, and its choices are fixed to the frame. The film then tells this one scene in many hands at once: cut paper and engraving, a hand-cut silhouette, a 1930s home movie re-performed, a risograph bent by moving least squares, crepe paper on springs, a wooden toy on brass pins, bones and weights, a state machine, a mask that refuses to invent. Each telling is a translation. The film asks what survives it.

---

## 3. What makes it watchable

### You watch to see whether the line lands

The film is built around three moments when something is said, and each holds attention in a different way.

- **The command, and its failure.** *Come here* is the most ordinary sentence you can say to a dog, and the film shows it as a push. The dog backs away. Called again, with a reach, it turns its back and lies down facing away. The viewer knows exactly what was meant and watches it go wrong.
- **The reassurance.** Then come four seconds in which nothing is asked. The person sits, the door opens, a hand is offered low. The film makes you wait in the turned back. When *it's all right* is spoken, every frame is aimed at one question: does the head come round? It does, on time. The voice is quiet by rule, at least 6 dB below the calls.
- **The invitation.** *Come in* is spoken only after the dog has come to the threshold of its own accord. The dog hears it, looks into the lit room, and stays. The film ends on a listener who understood and answered, and did not obey.

### Many hands, one sentence

The same three sentences are told at once in many formal languages. The pleasure is the pleasure of translation: how does a cut-paper card show *I won't*? (Gilliam's telling turns it over to its blank back, stamped NO.) How does a constraint solver? (Sutherland's prints THE DOG IS NOT SELECTABLE.) How does a 1930s home movie, where a real dog once walked toward a real person with a bowl? Watching several tellings, the viewer starts to hear the lines through the materials. The materials change and the communication does not.

### What critics of the image add

Every telling was judged by a fresh AI critic that saw the picture and heard the sound but never read the maker's notes. Its first question was whether each line *reads as a choice on screen*. The verdicts are written and public. Two tellings never passed; they stay in the film, marked. The audience can trust what it sees, because the failures are on the record.

### The risks, said plainly

- **Repetition.** The scene is short and the same each time. A viewer who does not enjoy variation will tire of the long form.
- **Length.** *Come In*, the long form, runs about 27 minutes.
- **Uneven craft.** Many passes were narrow, and the critics name defects frame by frame: a turn that tangles for a few frames, a back of the head that reads as a cat's. Two tellings did not pass.
- **Thin voices.** The voices are synthesised, mostly with the free Flite speech engine, or played by instruments. Some are not intelligible as words. Because the film's subject is how the lines are said, register and timing carry it more than diction.
- **Machine-made work.** Programmers will ask what a human did. Section 4 answers as far as the record shows.

### How each format answers them

| Format | Running time | What it does |
|---|---|---|
| **IT'S ALL RIGHT** (the synced film) | 41 s | Every telling plays at once in one frame, aligned to the score, with all the soundtracks level-matched together. A timeline marks each choice as it lands. When *it's all right* is spoken, every head comes round together. This answers length and repetition at once: the communication act happens once, in every material. Programmes before a feature or in any shorts block. |
| **COME IN** (through every door) | 26 min 36 s | The same film passing through every door: each telling hands over to the next through a 2.5 s passage of nested door frames, and both keep playing through it, so there is no slate and no stop. Repetition becomes rhythm, and the three sentences become a refrain. For a focus programme, a gallery loop or an expanded-cinema slot. |
| **Trailer** | 64 s | Cuts the same beats across many tellings: each refusal, each turn to the soft voice, the approach handed from telling to telling, the lie across the sill opening out into the full mosaic. |
| **Interactive page** | in preparation | A page where every dog and every person can be seen animated together. |

A 24 s title opener also exists: a push through nested doorways, each layer a different telling at the same moment of the score.

---

## 4. How words enter the dog

The scene is not keyframed. It is written as text, and the text acts.

**The prompts.** The score holds seven typed prompts, in the order they act: *the person calls: Come here* (0.4 s); *call again, and reach for it* (2.8 s); *sit down beside the door* (4.8 s); *open the door* (5.8 s); *offer a hand, low* (6.4 s); *say it softly: it's all right* (7.0 s); *come in* (25.8 s). Each prompt becomes a change of circumstance at a fixed time: a call at 1.0 s, a call and a reach at 3.4 s, sitting beside the door at 5.4 s, the door open at 6.2 s, the hand low at 6.8 s, the soft voice at 7.4 s, 10.4 s and 26.4 s.

**What the dog hears.** The decision machine (`paeleo/threshold/machine.js`) never reads the words. It reads how they are said and what the body does. A voice is a *call*, *soft* or *none*. A hand is *reach*, *low* or *none*. The person stands or sits, in the doorway or beside it, and the door is ajar or open. From these the dog perceives two quantities:

- **Threat:** a reach adds 0.55, a call 0.42, a person standing in the doorway 0.22. The total grows with nearness, plus the pressure the dog remembers.
- **Invitation:** a low hand adds 0.35, sitting 0.30, a soft voice 0.25, an open door 0.15, the person beside the door 0.15. A call *subtracts* 0.30.

It also carries memory. Each new call adds pressure: 0.3, or 0.5 if the dog is already backing away or refusing. Pressure fades slowly while the calling goes on, and faster once it stops. Trust rises with invitation and falls with threat, and a dog that has refused warms up more slowly. The code's comment is "it remembers".

**The decision trace.** Guards in priority order turn those quantities into five states: watch, approach, retreat, lie down, refuse. The score (`paeleo/handmade/score/threshold-score.json`) records the result frame by frame, with the machine's own reasons:

| t (s) | the dog | the machine's reason |
|---|---|---|
| 1.00 | backs away | "threat 0.74 > 0.55 at 3.3 m: backs away" |
| 2.33 | stops to watch | "watches" |
| 3.42 | turns its back | "threat 1.00 and already 4.3 m away: turns its back" |
| 7.46 | turns back to look | "pressure 0.20 gone, invitation 1.00: turns back to look" |
| 14.71 | comes, head low | "trust 0.60 > 0.6, threat 0.00, threshold clear: comes closer" |
| 23.79 | lies across the sill | "reached the sill: lies down there, half in and half out" |
| 26.4 | hears *come in*, looks in, stays | (no change of state) |

Three findings matter for a film about speech:

1. **The command is literally a push.** In the machine, *come here* raises threat and lowers invitation at the same time. Said twice with a reach, it drives threat to its maximum, and the dog refuses.
2. **The reassurance is spoken into a silence the acts have already made.** By 7.4 s the sitting, the open door, the place beside the door and the low hand have raised invitation to 0.95. The soft voice brings it to 1.00, and the turn comes at 7.46 s, the moment the remembered pressure of the calls drops below 0.2. Run the machine without the soft lines and the head still comes round at 7.46 s; the approach comes 0.17 s later and the lying down 0.17 s later. In the machine, then, *it's all right* says aloud what the body has already said, and arrives as the command is forgotten. In the films the line must come first: the critics checked that the voice leads the reactions, and flagged one telling where it began two frames after the head.
3. **The invitation cannot be obeyed, by construction.** The machine has no state for going in. Its position is held at the sill (0.56 m, half in and half out). *Come in* reaches it as one more soft voice. The acting layer (`paeleo/threshold/stage.js`) answers it: a lying dog that is spoken to lifts its head and turns it in through the door, ears up and tail sweeping, for about 1.6 s. Then it turns back, puts its chin on its paws, and stays. The answer is a look.

That is the text-to-act link: written prompts, a written machine, a written trace. Every telling of the film must keep the trace. A script checks four invariants against each telling's own measured trace: the choices within ±0.25 s, the dog never inside the house, commands before refusal and circumstances before approach, and the back shown in the refusal.

---

## 5. How it was made: language all the way down

*It's All Right* is the second test of **PAELEO**, a research programme within Bolas, a site of experiments in authored motion. PAELEO reads two ways: Promptable Augmented Environments Lab, and Language for Ekphrastic Operations. Its method is **PEO**: Prompt, Ekphrasis, Operation, or how a description becomes something that acts. The programme traces a lineage from *imagetext* (text beside a picture) through *environment text* (text pinned to a place) to *worldtext*, "text the place runs on". This film is worldtext: the words are not captions on the scene; the scene runs on them.

**A description that acts.** The first test, PAE-00, gave one sentence-sized description to one swarm, SCION 48, State Machines, whose prompt asked for "characters that can refuse". No one keyframed its dog. It became the machine described above, and its trace became the score. A second test, PAE-01, laid every swarm's visual language over that one paper dog as a lens. The project's own write-up judged that too little: a lens is a filter, not a studio.

**Prompts as text that makes images.** For this film the description and the score were held still, and each telling was made by a different SCION swarm. SCION is a set of standalone prompts, each a page of text that turns one lineage of animation into a working studio. Each prompt states a *creative theorem to prove*; Gilliam's is "Convert found illustrations into surprising physical comedy". It names a *native formal language* of first-class primitives (for SAM 2: "points/boxes/masks; segment proposals; object IDs; confidence proxy; correction strokes"). It sets the smallest crew of roles, a proof, and a bar. All share one doctrine, including "The builder cannot approve its own important work." Each prompt also says it is "inspired by a documented artistic/technical contribution. It is not a claim that the named person wrote or endorsed this system." The artists, researchers and studios named had no part in this film.

In practice each telling was built by one AI builder agent working alone in its folder, with the prompt's roles merged, as most of their method notes state. It worked from the shared brief and the score, and built bottom up from materials whose rights were recorded: public-domain archive film, Quick, Draw! doodles (CC BY 4.0), CC0 museum prints, and its own work. In the brief's words: "unknown is not permission."

**Verdicts as text that judges images.** Each telling then went to a fresh, independent AI critic. The critic had the brief and the swarm's prompt, and judged the picture and the sound; it never read the builder's notes or code. It wrote one entry per choice ("Turning to look: reads"), measured the voices in decibels, ruled on language and rights, and returned a verdict with ranked, falsifiable repair conditions such as "By 7.71 s the head visibly points toward the door." Repairs went back to the builder, and each next round went to a new critic, for up to five rounds. A later critic could and sometimes did fail what an earlier one had passed. Every verdict is published beside its telling.

**Lessons as language hardening into rules.** Builders worked in cohorts. Each later cohort read what the earlier ones had failed at, never their films or code, and the brief grew sentence by sentence:

- "Every frame of both turns must read as a dog."
- "The refusal must show the back."
- "The soft voice must be at least 6 dB quieter than the calls."
- "The dog itself must be made in your language" (after cohort 2).
- "A head turning 'in' must read in depth."

The last rule is the film's subject in miniature. The hardest moment for every telling was the answer to *come in*: a look that must go into the room, not up toward the light or across to the person.

**The two that did not pass.** Two tellings, *Learned layered puppet* and *Neural layered puppet*, failed five rounds in a row. In the reviews' words, "the look-in has failed in different forms every round." Repairs were paused, and each case went "to the person who commissioned the films rather than into another cycle." Both remain in the film, marked *repairs paused after critic round 5*.

**What humans did.** The record documents the agents' work closely: each telling's assets, measured trace, method, build scripts, attempt ledger and every critic report. It is less precise about the human side. Watson Hartsoe commissioned and directed the project and received the two paused cases. [Watson Hartsoe to confirm which texts he wrote himself: the description, the brief, the SCION prompts, the cohort plan, the title.] No human viewing is claimed in the critics' record, and their sound judgements are measurements.

---

## 6. Director's statement (draft)

I wanted to make a film about saying something.

Not about a dog, quite. About three sentences: *Come here*, *It's all right*, *Come in*. The first is the one we reach for first, and it is a demand. The second asks for nothing. The third is an offer, made only after the other has come as far as it wants to. I was interested in why the first fails and the second works, and in what it means for the third to be answered without being obeyed.

So I wrote the scene as a description, and then as a machine that hears how a thing is said rather than what is said. A raised voice is a push. A lowered one, from someone sitting down beside an open door with a hand held low, is room. When I took the soft words out of the machine, the dog still turned. The body had already said it. I find that true of people too. [Watson Hartsoe: a personal sentence on where this scene comes from.]

Then I asked many makers to translate those sentences into their own materials, the way you would hand a short poem to many translators. The makers were AI studios built from prompts, each answering to a critic who could not read its notes. Paper, lace, flip-discs, a 1930s home movie: what survived was the moment the head comes round.

Two of the translations never passed. They failed at the last line, the look into the room. I kept them. [Watson Hartsoe: a sentence on what you did by hand, and what you chose not to do.]

Watson Hartsoe, [city], 2026

---

## 7. Format sheet

| | |
|---|---|
| **Title** | IT'S ALL RIGHT |
| **Subtitle** | one dog · one threshold · many hands |
| **Credit line** | PAE-02 · Bolas |
| **Director** | Watson Hartsoe |
| **Year** | 2026 |
| **Country** | [ ] |
| **Language** | Minimal English voice: "Come here", "It's all right", "Come in". Some voices are instruments or synthesised speech without clear words. No subtitles needed. |
| **Genre** | Experimental animation · animated short · archive / found-footage animation |
| **IT'S ALL RIGHT** (synced film) | 41 s; 1920×1080, 16:9, 24 fps; stereo |
| **COME IN** (through every door) | 26 min 36 s; 1280×720, 16:9, 24 fps, H.264; AAC stereo 48 kHz |
| **Trailer** | 64 s; 1280×720, 16:9, 24 fps; AAC stereo 48 kHz |
| **Title opener** | 24 s; 1280×720, 16:9 |
| **Interactive page** | in preparation |
| **Tellings** | 54, each a 32 s scene on one score, by a different SCION swarm |
| **Colour** | Colour, with black-and-white archive material |
| **Sound** | Synthesised per telling: room tone, crickets, door, paws and voice. The soft voice is always at least 6 dB below the calls. |
| **Rights** | Public-domain archive film; CC0 museum objects (Smithsonian American Art Museum); Quick, Draw! drawings (CC BY 4.0, credited); OFL fonts; own work. A per-asset rights ledger exists for every telling. |
| **Exhibition copy** | [DCP / ProRes: not yet made] |
| **Premiere status** | [ ] |

**Categories to target:** experimental short; animated short; expanded cinema and installation (the synced film on a loop, or *Come In* as a gallery piece); computer animation and research showcases; archive and found-footage strands.

### Where it fits, and why

These are types of festivals and strands, not submissions. Nothing has been submitted or accepted.

- **Animation festivals with experimental competitions** (for example Annecy's Off-Limits, Ottawa, Animafest Zagreb, Fantoche, Stuttgart ITFS, Holland Animation Film Festival). The film is a study of how animation makes a body *answer*. The 41 s synced film suits a shorts block.
- **Short-film festivals with experimental and moving-image strands** (for example Oberhausen, Ann Arbor, IFFR's short and art strands). It is a formal experiment on language: one fixed text, many translations.
- **Expanded cinema, media art and installation** (for example Ars Electronica, transmediale, gallery screenings). *Come In* loops without a seam, and the interactive page, once ready, extends the film into a space.
- **Computer-graphics venues** (for example SIGGRAPH's Computer Animation Festival). Several tellings come from graphics research lineages (as-rigid-as-possible shape manipulation, moving least squares, bounded biharmonic weights, video puppetry), and every method is documented.
- **Archive and found-footage programmes.** Many tellings are made from a 1930s New Jersey home movie and other public-domain films, each with a recorded source.

**Before submitting:** check each festival's rules on AI-generated work and how it must be disclosed. Check premiere rules too: public uploads (YouTube) can cost premiere eligibility at some festivals.

---

## 8. Programme note, social copy, press

### Programme-note blurb (about 100 words)

*Come here*, says a person in a doorway at dusk, and the dog backs away. Said again, with a reaching hand, and it turns its back. Then the person stops asking: they sit, the door opens, a hand is offered low, and a voice says softly, *it's all right*. The dog's head comes round. *It's All Right* is a film about the communication act: commands that push, reassurance that makes room, an invitation answered on the listener's own terms. Driven by a written score, the scene is told at once in many hands: cut paper, code, archive film, print, bones and weights.

### One-line social copy

1. "Come here" pushed it away. "It's all right" turned its head. A film about what words do.
2. One dog, one doorway, three sentences, told in cut paper, code, crepe paper and a 1930s home movie at once.
3. A dog that won't come when called, until someone sits down and says it softly.

### Press quotes

None yet. No reviews or press coverage exist for this film. Do not add quotes until they are published, and attribute them exactly.

---

## 9. Credits

**IT'S ALL RIGHT** · one dog · one threshold · many hands
PAE-02 · Bolas · 2026
Directed by Watson Hartsoe

Told by SCION swarms (autonomous AI animation agents), each judged by independent AI critics. Each SCION name is a lineage of method, not an endorsement: the named artists, researchers, studios and archives did not take part in, write or endorse this work.

Score: the PAELEO threshold machine (`paeleo/threshold/machine.js`) run on the prompt timeline (`tools/paeleo/build_score.js`).

### The tellings

| # | Telling | Kind |
|---|---|---|
| 01 | Terry Gilliam | Cut-out collage |
| 02 | Lotte Reiniger | Silhouette theatre |
| 03 | Max Ernst | Surreal collage grammar |
| 04 | Frank Mouris | Image torrent |
| 05 | Yuri Norstein | Atmospheric multiplane |
| 06 | John Whitney | Harmonic motion |
| 07 | Peter Foldès | Drawn metamorphosis |
| 08 | Ivan Sutherland | Constraint Sketchpad |
| 09 | Takeo Igarashi | As-rigid-as-possible puppetry |
| 10 | MLS deformation | One sheet warped by handles |
| 11 | Video puppetry | Footage cut-outs moved as puppets |
| 12 | Localized weights | Bounded biharmonic weights on a lace mesh |
| 13 | Secondary motion | Paper figures with secondary dynamics |
| 14 | Pose2Pose casting | Nora Willett lineage |
| 15 | Learned layered puppet | A layered puppet fitted to the archive dog · *repairs paused after critic round 5* |
| 16 | JibJab | Cast heads on a cut-out body |
| 17 | South Park lineage | Restricted graphic grammar |
| 18 | Cartoon Saloon lineage | Painterly puppet discipline |
| 19 | Moho Smart Bones | Smart-Bone rig with switch layers |
| 20 | Toon Boom Harmony | Production rig: drawing substitution and node graph |
| 21 | Photo-to-Actor | Photographic actor rigged from stills |
| 22 | Character Animator | Performance puppet with behaviours |
| 23 | Spine runtime | Skeletal runtime with mixed action clips |
| 24 | Live2D lineage | Portrait volume illusion |
| 25 | Rive | Interactive puppet state machines |
| 26 | PixiJS archive stage | GPU scene graph of archive fragments |
| 27 | Remotion | Declarative film compiler |
| 28 | Mask and plate foundry | Compositor's film of archive plates |
| 29 | GrabCut | Cutout extraction |
| 30 | SAM 2 proposals | Evidence-bounded mask proposals |
| 31 | Alpha Matting | Soft-edged matted archive frames |
| 32 | Forward kinematics | Jointed toy moved only by forward kinematics |
| 33 | Inverse kinematics | Joints, chains and planted effectors |
| 34 | As-rigid-as-possible | Engraved mesh, shape kept by a local–global solve |
| 35 | MLS gesture warp | Risograph print bent by moving least squares |
| 36 | BBW auto-rig | Auto-rigged archival silhouettes |
| 37 | Weighted skinning | One skin over a skeleton, weighted per vertex |
| 38 | Dynamic pose selection | Drawing library |
| 39 | Multiview substitution | Turn lab |
| 40 | Tabletop capture | Paper performance, captured and replayed |
| 41 | Secondary dynamics | Inertia and restraint |
| 42 | Neural layered puppet | Parts and joints discovered from a few frames · *repairs paused after critic round 5* |
| 43 | Collage Graph Rewriting | Typed fragments and rewrite rules |
| 44 | Multiplane parallax | Spatial collage in depth, with a moving camera |
| 45 | Occlusion compositing | Who is in front? |
| 46 | Face Landmark Registration | View-matched plates on landmarks |
| 47 | Sound-to-action | Viseme and gesture |
| 48 | State machines | A dog whose refusal is its own decision |
| 49 | Open-content atelier | Museum open-access objects, cut and recomposed |
| 50 | Historical print stage | Library of Congress lineage |
| 51 | Mouris montage research | Montage on a measured cutting score |
| 52 | Gilliam Ephemera | Pinned found prints and substitution |
| 53 | Atlanta Moving Image | Civic footage performer |
| 54 | Provenance graph | Archive-to-puppet lineage |

### Source archives

All film material is public domain, as recorded in each telling's `assets.json`. Most came via the Moving Image Archive from the Internet Archive.

- *Amateur Film New Jersey C* (Home Movies collection, Internet Archive; archive.org/details/NewJerseyC): the archive dog
- *Straight Talk* (NTIS, 1992; archive.org/details/gov.ntis.ava19144vnb1): the door
- *The Door to Heaven* (1941)
- *Top of the Cloud – Time Lapse*
- *Anthracite: Pre-Shift Examinations of Underground Mines*
- *Light of Your Life B*
- *We Learn About the Telephone I*
- *Andy's Animal Alphabet*
- *Billie, the Buffalo Baby*
- *Gateways to the Mind*
- *Vision of the Wild*
- *Robinson Crusoe C*
- *Gift of Green*
- *Golden Gate City*
- *Survival Stresses*
- *Insect Zoo*
- Amateur films from the Wathen (New York World's Fair, 1939–40), Ivan Besse (Britton, South Dakota, 1938–39) and Summers (San Francisco, 1941) collections, and *Amateur Film Northwest*
- Further public-domain titles used as tiles and plates, mainly in tellings 04 and 51 (listed in their `assets.json`)

**Museum objects (telling 49):** CC0 works from the Smithsonian American Art Museum (Smithsonian Open Access), among them Nathaniel Currier, *Woodcock Shooting* (1855), Auguste Edouart, *Boy with Dog*, and José Dolores López, *Screen Door* (ca. 1930–37).

**Drawings:** Quick, Draw! by Google Creative Lab and contributors, CC BY 4.0, drawings identified by `key_id` (tellings 09, 16, 17, 26, 34, 38, 44, 54).

**Kit preparation:** SAM masks, rig keys and the archive shot library came to Bolas through the Secondhand Motion observation pipeline.

### Fonts

Big Shoulders Display, Literata, JetBrains Mono (SIL Open Font License 1.1).

### Tools

Python 3 (numpy, Pillow; scipy in some builds) · Node 22 with Playwright and Chromium · ffmpeg / H.264 / AAC · CMU Flite speech synthesis, run locally through ffmpeg · the PAELEO threshold machine and score · the invariant checker `tools/paeleo/check_handmade.py`.

Full record of every telling (method, assets, trace, build scripts, critic rounds): https://hartswf0.github.io/bolas/paeleo/handmade/

---

## Editor's notes (remove before sending)

- **Fact sources.**
  - Communication mechanics: `paeleo/threshold/machine.js` (perceive, decide and step), `paeleo/threshold/stage.js` (lines 106–110, the look-in), `tools/paeleo/build_score.js` (prompt timeline), `paeleo/handmade/score/threshold-score.json`.
  - The "without the soft lines" result: run `machine.js` on the same timeline minus the 7.4 s and 10.4 s soft-voice events. Transitions come at 1.0, 2.333, 3.417, 7.458, 14.875 and 23.958 s.
  - Critic on voice lead: `52-gilliam-ephemera/reviews/round5.md`.
  - Lessons: `paeleo/handmade/BRIEF.md`.
  - Worldtext lineage and PEO: `paeleo/index.html`.
  - Paused cases: `15-…/reviews/round5.md` and `42-…/reviews/round5.md`.
  - Running times: ffprobe of the files in `scratchpad/collection/`.
- **Subtitle.** Changed from "54 hands" to "many hands" to keep counts out of the title, per the director's note. Confirm.
- **Rendered cuts still carry old titles.** At last check the opener and trailer read "The Threshold, Handmade" with the subtitle "54 hands · one dog · one score", and the trailer card says "The full collection: 54 films". The master and grid files need renaming to IT'S ALL RIGHT and COME IN. Re-render them before sending screeners.
- **Interactive page.** Described only as "in preparation". The existing "Try it" page on `paeleo/index.html` lets a visitor play the PAE-00 dog by changing circumstances; it is not the new page.
- **AI model.** Not named in the repo. Add it only if confirmed.
- **The previous version** of this kit is `press_kit_v1.md`, alongside this file.
