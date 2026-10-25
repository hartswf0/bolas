# PAE-02 · SCION 03 · Max Ernst — Surreal Collage Grammar · method

## Thesis

One plate from a collage-novel: a porch at dusk, engraved. Its impossible things are fixed in place and its surfaces are
continuous: one burin cuts every part, so you cannot see where the lion, the hand or the lamp were pasted on unless the
film wants you to. The defining passage is the lion. While the person gives orders its head is a lion, cut from a film
and pasted on with its white scissor margin showing. When the person steps aside, the lion leaves the head and settles
over the door as its keystone. There the margin fades: the authority has become architecture. Then the door opens on its
own. At the end the dog lies across the sill below the lion, the way the lion lay in its film. The motif comes back three
times, each time doing a different job: commanding head, keystone, the dog lying couchant at the threshold.
The film would be bland if the lion were only decoration, if the collage were a random pile, or if the dog were a flat
cut-out that flips.

## The swarm (merged roles, one builder)

The SCION prompt names six roles. Here one agent did the building, and the work was split into artifacts each role owns:

| role | artifact |
|---|---|
| archive iconographer | `build/fragments.py`: it picks the found frames, cuts them by their SAM masks, engraves them and copies the sources into `src/`. `build/assets.py` writes the rights ledger (`assets.json`) |
| hybrid form composer | `build/dog.py`, `build/person.py`: the maquettes. The person's lion head and pasted hand are composed in `build/render.py` |
| seam/mat specialist | `build/burin.py`, `build/dogplate.py`: one line language. It also sets the seam rule: margin shown means pasted (foreign), margin hidden means absorbed |
| recurrence dramaturg | `build/timeline.py`: what the lion and the hand do, and when |
| improbable-world builder | `build/plate.py`: the porch, the door, the light coming out, the dusk |
| independent critic | **not me**. I did not approve this film. The critic sees the film, the brief and the bar |

## Native formal language, as built

- **Engraving source fragments.** There are five, cut from three public-domain films: two 3/4 lion heads and a frontal
  lion head (*Andy's Animal Alphabet*), a hand (*The Door to Heaven*), and a miner's safety lamp (*Anthracite: Pre-Shift
  Examinations of Underground Mines*). Each is re-engraved in this plate's burin. The lion gets a radial line system,
  so the mane reads as engraved fur.
- **Hybrid nouns.** The person-lion is the magistrate. The hand-that-swells is the reach. The lion-keystone is authority
  turned into architecture.
- **Transformation rules.**
  - Command → the lion head is on and its margin shows.
  - Stepping aside → the lion flies to the keystone and is swapped from the 3/4 head to the frontal head in mid-flight.
  - Landing (a stone knock) → the door opens on its own and light comes out.
  - Reach → the pasted hand swells to 3.4× along the arm.
  - Offer → the same hand at normal size, held low, with no margin.
- **Compositional seams.** These follow a rule rather than being left to chance. A fragment acting as an intrusion keeps
  its white cut margin. A fragment that has been absorbed loses it. Everything else (dog, person, set) is cut by the same
  burin, so those seams are hidden.
- **Recurring icons and symbolic motifs.** The lion (authority → threshold → the couchant dog), the hand (grab → offer),
  and the light (a sliver through the door left ajar → a hall lit by the lamp).
- **Rights ledger.** `assets.json` lists every fragment with its file, source title, archive URL, clip id, rights and
  operation.

## How the dog is built

The dog uses no picture of a dog. It is a solid maquette, like an anatomical-plate dog, made of 27 typed primitives (round
cones and ellipsoids):

- chest, loin and haunch
- neck, skull, muzzle and nose
- two eyes and two ears
- four legs of three segments each
- a tail of four segments

It is posed by typed parameters (yaw, lie, crouch, head, rest, ear, tail, wag, gaze yaw and gaze pitch) and built at unit
size, then scaled ×1.2. It is ray-marched in the plate's orthographic camera (`build/sdf.py`). The burin then cuts lines
that run *along the form*: the angle around each primitive's axis sets a line count that wraps without a seam. Rings
cross-hatch the deep shadows. The coat has a darker saddle, the dog is lit from the sky above and by the warm light from
the door, and it is outlined at its silhouette and at depth breaks. Because the lines are attached to the body, they do
not boil.

## How the dog moves

- **Position.** `x` comes straight from the score: screen x = 400 + 168·x, with a fixed camera.
- **Turns.**
  - The yaw always passes through 90°, so the dog shows its face to the viewer mid-turn. A solid turning in 3D never goes
    edge-on.
  - The refusal turn runs from 3.42 to 3.92 s, so the back is shown by about 3.9 s.
  - At the turn back (7.46 s) the head comes round first, over the shoulder on the viewer's side, and points at the door
    by about 7.7 s. The body follows by 7.96 s while it rises.
- **Feet** (`build/gait.py`). A planted paw is a constraint and stays put in world coordinates. The paws are lifted in
  the lateral sequence of a walk (LH, LF, RH, RF). The gait clock advances with distance travelled (one stride per
  0.54 m, the same rate as the score's walk phase) and with rotation. Each paw lands where the body will want it half a
  stance later, since the solver looks ahead along the known timeline. In a turn on the spot the paws step quickly, one per
  side at a time.
- **Head low.** During the approach the head is lowered 0.13 below the score's head value, and the measurement says it
  stays below the line of the back.
- **Lying across the sill.** For the last 0.6 m of the approach the dog angles 27° into the doorway (z from 0.62 to
  0.10). It lies with its forequarters in the door opening and its tail out on the boards. This was solved in the
  maquette's own language, since there is no lying dog in any of the kit footage.
- **Looking in.** At 26.4 s the gaze target becomes the hall inside (score `look`), and the head turns about 60° into the
  lit opening. Then the chin goes down onto the paws and the dog stays.

## The invariants (measured: see `invariants.json` and `trace.json`)

`trace.json` is measured from the render. In each frame:

- `x_screen` and `y_screen` are the centroid of the dog's rendered torso pixels.
- `facing` compares the rendered head and tail on screen.
- `posture` comes from the rendered torso height.
- `head_below_back`, `frac_in_frame` and `z_min` are also measured.

`state` is the score decision that drove the frame. It is copied, not measured, and that is said here plainly.

RESULTS_PLACEHOLDER

## Sound

Every sound is synthesized (`build/sound.py`); nothing is recorded.

- The calls are formant voices ("Come here." / "Here!") with a lion's growl pasted under them.
- The soft voice ("It's all right.", "Come in.") is breathy and lower.
- Paper rustles as the hand swells and as the lion flies. A stone knocks when the lion lands.
- The door gives a hinge creak, then a warm low chord: the light, heard.
- The dog makes a claw tick and a pad sound at every touchdown the step solver reports. It sighs when it lies down, and
  its tail knocks the boards while it looks in.

Measured levels are in `build/cache/audio_levels.json`, as RMS over the voiced samples (summarized below).
**I cannot listen.** Whether the voices are intelligible as words, or merely voice-like, is unknown to me. I checked only
spectrograms, which show harmonic, formant-shaped utterances where the voices should be.

## What failed, and what changed (details in `ledger.jsonl`)

LEDGER_PLACEHOLDER

## What I did not do

- No independent critique has happened yet. The verdict belongs to the critic.
- Not used: the kit's archive dog, the archive door, and Quick, Draw!. I looked at all three; the dog is a maquette
  instead.
- No motif graph page or operator page; the deliverables of this brief were followed instead.
- No forked branches were compared.
- Sound was not listened to.
