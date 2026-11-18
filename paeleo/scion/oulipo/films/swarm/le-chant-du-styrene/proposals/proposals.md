# Le Chant du styrène: round 2, three directions

Reference: `assets/references/styreneA.webp`. It shows translucent red and amber runner "trees" with disc parts, glowing on black in a scope frame, with soft blue lights out of focus behind. Round 1 is in `r1/`. The user kept r1 direction 1 (a real sprue photograph cut out on black) and asked for more animation. So direction 1 below is that idea improved, and directions 2 and 3 are animation-led and handmade.

All three frames share the same format. Each is 1280x720 with 2.35 letterbox bars and an alexandrine caption as the voice. The `|` in the caption marks the 6+6 break. All three keyframe scripts are in the session scratchpad (`.../scratchpad/sty2/`: `common.py`, `seg1.py`, `kf1.py`, `kf2.py`, `kf3.py`). New downloads are in `films/sources/le-chant-du-styrene/r2/` (about 2.7 MB).

Planned reverse tour (about 60 s). The process order is raw stock → melt → mould → runner → part. The tour shows it backward:

| time | step (ProcessStep) | shown |
|---|---|---|
| 0–8 s | prologue | the key on the bench (common seed) |
| 8–18 s | S4 finished parts | loose rings, held long enough to read |
| 18–30 s | S3 part ← runner | **dir 1**: the rings fly back onto their runner |
| 30–44 s | S2 runner ← mould ← melt | **dir 2**: the melt drains out of the cavities and runner |
| 44–56 s | S1 melt ← granule | **dir 3**: runner trees turn into pellets |
| 56–60 s | coda | the heap of granules, in silence |

Each direction can stand alone as a whole film, and each is also built to be one step of the combined tour.

---

## 1 · L'anneau revient (foraged photograph, cutout puppetry)

- **Beat / time:** S4 → S3, about 20–28 s. This is the defining beat: a finished part shown, then shown back on the runner that explains it. Four loose rings rise off the table and snap back onto the bare runner's arms, in reverse degating. The red assembly on the right is what the amber runner becomes once all four are home.
- **Verse:** "Chaque anneau s'en revient | au bras qui l'a coulé." Scansion: Cha-qu'an-neau-s'en-re-vient | au-bras-qui-l'a-cou-lé. *Chaque* elides before *anneau*, giving 6+6. **This is the Hard proof's cut on the caesura.** The first ring clicks home exactly on the break.
- **Material:** "Spritzguss teile.jpg" by Gmhofmann, CC BY-SA 4.0, https://commons.wikimedia.org/wiki/File:Spritzguss_teile.jpg. It is a real photograph of two injection-moulded runners. On the left is a degated runner beside its four rings. On the right is a runner with its rings still on. The blue studio lights behind are handmade, and their layout is deliberately not the reference's.
- **Technique and motion:**
  - **#29 GrabCut:** a hue-seeded GrabCut gives six clean cutouts: two runners and four loose rings.
  - **Cutout puppetry:** each ring is its own puppet. Frame by frame (12 fps, on twos), each ring follows an eased arc from its rest point to an arm tip, with staggered starts (overlapping action). In the keyframe the rings are at s = 1.0, 0.72, 0.42 and 0.16 of their paths.
  - **#41 Secondary dynamics:** a spring-damper settle of ±4° on contact.
  - **#44 Multiplane:** the blue lights drift at 0.3x.
  - **#45 Occlusion:** the rings pass in front of the runner.
- **Colour (declared):** no red or amber runner photograph exists on Commons. I searched the categories Sprue, Injection moulding, Nurdles and Polystyrene, and searched for Gussast, Airfix, translucent and red. The photograph's plastic is teal. Its form and its real shading (the V channel) are kept, but the hue is replaced by a translucency ramp: thick sections render deep red, thin sections amber. The left runner is amber and the right runner red, as in the reference's mix. This is a gel substitution, not a found colour, and the credits must say so.
- **Risk:**
  - The colour is substituted. The honest fix is to photograph a real red or amber kit runner, backlit on black.
  - The table photograph is lit from the side, so the plastic reads lit rather than lit through.
  - Rings rotating far from the camera's perspective will look pasted on. Keep rotation under about 10°.
  - It is a hobby-scale part, not 1958 industrial ware.

## 2 · La coulée rendue (procedural melt simulation, run backward)

- **Beat / time:** S3 → S2, about 32–42 s. The central reveal of the Hard proof: the part's negative form. Red melt drains out of the ring cavities and back up the runner toward the sprue. The empty cavities are left as lit recesses in the steel.
- **Verse:** "Le rouge se retire, | et la forme est un creux." Scansion: Le-rou-ge-se-re-ti(re) | et-la-for-m'est-un-creux. *Retire* elides at the break and *forme* elides before *est*, giving 6+6. **This is the cut against the caesura.** The picture cuts to the empty mould on *-ti-*, one syllable early, so you see the hollow before you hear it named.
- **Material:**
  - **Handmade:** the runner and cavity geometry and the fill simulation. The ring cavities are the same rings as in direction 1, which links the two shots.
  - **Foraged:** the mould-half steel is "Injection mold - (11).jpg" by Bricetofly, CC0, https://commons.wikimedia.org/wiki/File:Injection_mold_-_(11).jpg. It is darkened, cooled, defocused, and seen in perspective.
- **Technique and motion:**
  - **Procedural simulation:** a fill-time field T(x) is computed along the runner tree. It is path length from the sprue, with slower flow inside the cavities and a lag at the channel walls. Each frame shows the melt where T + η(x) < τ, and τ falls from its maximum to 0. That is the fill run backward: far cavities empty first, and the runner drains last, into the sprue mouth.
  - **Stop-motion boil:** η is smooth noise that gives a viscous, irregular meniscus. It is reseeded on twos, so the front boils like hand-animated stop-motion.
  - **Colour:** comes from melt thickness. Deep red is the full channel, and the thin film at the front is amber. The melt's light spills onto the steel.
  - **#8 Constraint sketchpad:** the cavity and the part come from one layout function, so the hollow matches the part exactly. This is a verifiable process edge.
  - **#44 Multiplane:** a slow tilt across the mould face with shallow focus.
  - The direction the shot plays and the process order are labelled separately, as the SCION invariant requires.
- **Risk:**
  - It can read as a diagram or a neon sign if the plastic stays flat. The full build needs refraction or caustics in the melt and fewer symmetric branches.
  - The glow is an aesthetic choice. Molten polystyrene does not glow visibly, so the glow is motivated as pigmented plastic lit through, not as heat.
  - The steel photograph is modern aluminium tooling.

## 3 · Arbres harmoniques (Whitney harmonic motion + metamorphosis into granule)

- **Beat / time:** S2 → S1, about 46–54 s. This is the last step to raw stock. Runner trees, branched like the reference's plastic trees but not traced from it, are cut into pellets. The pellets leave on harmonic orbits and settle as a heap of granules.
- **Verse:** "L'objet était un arbre, | et l'arbre était du grain." Scansion: L'ob-jet-é-tait-un-ar(bre) | et-l'ar-br'é-tait-du-grain, 6+6 with elision at the break. This line can also serve as the film's recap. The cut to the heap falls on the caesura.
- **Material:** handmade. Translucent rods and discs are shaded from a distance field (thin edges pass more light), with an upper catch-light and bloom. The pellets are the same rods, cut at a fixed 9 px pitch, so each granule is literally a piece of the tree. Both planes of trees and the blue lights are handmade. Nothing is foraged.
- **Technique and motion:**
  - **#6 Whitney harmonic orchestra:** tree *i*'s branch level *k* swings at a frequency proportional to *k* · ω_i. The whole forest falls back into perfect alignment every 12 s, and the cut to the next step lands on that alignment.
  - **Pellet orbits:** pellet *j* moves on a "permutation" figure, with an angle set by *j* mod *f* and a radius proportional to *j*. At integer *f* the cloud locks into an *f*-armed pinwheel. The keyframe shows *f* = 3.
  - **#7 Foldès metamorphosis:** with a dissolve parameter g, each tree in the frame is a later stage of one continuous transformation, from left to right: whole, beading, cloud, pinwheel, heap. In the film, g rises over time on a single tree and is held on twos.
  - **#44 Multiplane:** the back plane of whole, defocused trees parallaxes at 0.5x.
- **Risk:**
  - It is the most abstract direction. Without a real object it can drift into screensaver territory, so it has to be anchored by direction 1 or 2 and by the heap's hard cut.
  - The pellet arms currently overlap into continuous "worms". They need spacing jitter.
  - The rods glow evenly, which reads as neon. The full build needs variable wall thickness and some opacity.

---

## Recommendation

Build **1 + 2 + 3 as one reverse tour**, with **1 · L'anneau revient** as the spine. It is the direction the user chose, and it is the only one that holds a real foraged object long enough to make the defining beat legible: part, then runner. It now moves as cutout puppetry rather than an archive pan.

Cut into **2 · La coulée rendue** for the negative form. Its rings are the same rings, so the shape match carries across the cut. It also carries the cut against the caesura.

End on **3 · Arbres harmoniques** for the last edge to raw stock and the heap coda. That way two of the three steps are pure animation, and the one photographic step is animated too.

If only one direction is built, build **2**. It is the most controllable, it proves the process edge (cavity = part) inside a single frame, and it is closest to the reference's red-on-black glow.

Before the swarm build:

- Forage or photograph a genuinely red or amber runner to replace the gel substitution in direction 1.
- Add the Commons items above to `films/credits/le-chant-du-styrene.json`:
  - Gmhofmann, CC BY-SA 4.0.
  - Bricetofly, CC0.
