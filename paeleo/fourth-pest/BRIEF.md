# PAE-05 · The fourth pest: the brief

A cartoon short made from a garden scarecrow show, a tortoise, a public-health comic and one historical poster. The swarm is
SCION 17 (South Park: repeatable graphic grammar), the lab's strongest cartoon prompt (see `../hen-and-egg/PROMPT.md`):
flat cut-out figures, whole drawings swapped on twos, a mouth or eye change doing the acting, and one flat stage.

## Where the characters come from

Every figure is a new cut-out drawing made after a photograph. No photograph, logo or poster is stored or copied here.

| figure | after | role |
|---|---|---|
| **The Astronaut** | a white-suit scarecrow with a domed visor, chest box and tape stripes | scares with lights and a beep |
| **The Paperclip** | a scarecrow bent from silver dryer-duct hose, googly eyes and felt brows | offers help no one asked for |
| **Darth Hayder** | a cape, a papier-mâché helmet with red eyes, and straw poking out at every joint (the placard's name) | scares by breathing, loses a straw to the sparrow |
| **The Medic** and **the Bug** | a round-headed medic with a shield and a cheerful green bug, from a public-health comic | the campaign: carries the Four Pests sign |
| **The Bear** | a giant pink bear covered in drawings, sitting in mums and pumpkins | is sat in; its garden gets eaten |
| **The Beekeeper** | a pumpkin-headed beekeeper wearing the hive, with rainbow bees on wires | sends the bees |
| **The Painter** | a grinning pumpkin head on a chair, hands on hips, a table of painted pumpkins | grins |
| **The Sleeper** | a burlap-faced scarecrow asleep on a folding chair, a crow on the chair back | sleeps through all of it |
| **The Tortoise** | a radiated tortoise | crosses the whole garden, one step at a time; the film's clock |
| **The Sparrow** | the sparrow on the 1958 Four Pests poster, struck by the sword with the mosquito, the fly and the rat | the one the scarecrows are for |

## The story (the chronicle)

> Dusk in the garden. The scarecrows stand in a row; the Sleeper snores; his crow watches. At the front, a tortoise starts walking.
> The Medic marches in with the Bug and plants a sign: a sword through four pests, a mosquito, a fly, a rat and a sparrow. "Drive out the four pests!"
> A sparrow lands on the sign. Therefore the scarecrows try, one by one, to scare it. The Astronaut flashes and beeps: the sparrow sits on his arm. The Paperclip offers help: the sparrow pecks him. Darth Hayder breathes: the sparrow pulls a straw out of his neck. The Painter grins: the sparrow sits on his stem. The Beekeeper sends the bees: the sparrow ducks.
> Therefore they all do it at once, and the Medic shakes the sword. The sparrow flies away. They cheer.
> A green cloud comes over the wall. Locusts. They eat the mums and bite the pumpkins. The scarecrows flash, beep, breathe and grin, and the locusts do not care: a scarecrow is for birds.
> The sparrow comes back, with five more. They eat the locusts, every one.
> The Medic looks at the sign, crosses out the sparrow and draws a bedbug in its place. The sparrows settle on the scarecrows. The Sleeper is still asleep. The tortoise arrives and eats a bitten pumpkin.

History, kept true: China's Four Pests campaign (1958) named rats, flies, mosquitoes and sparrows. The killing of sparrows
was followed by plagues of locusts and other insects, and in 1960 sparrows were taken off the list and replaced by bedbugs.

## The score (40 s at 24 fps, 960 frames)

| t (s) | event | choice |
|---|---|---|
| 3.0 | the Medic enters with the sign | |
| 6.4 | | the sparrow **lands** on the sign |
| 8.5 · 10.5 · 12.5 · 14.5 · 16.5 | each scarecrow's scare | the sparrow **stays** (within reach of the scarer) |
| 18.4 | all scare at once | |
| 18.8 | | the sparrow **leaves** (off frame by 19.6) |
| 23.5 | locusts come over the wall | |
| 24–30 | locusts eat; scares fail | the scarecrows **fail** (no locust leaves) |
| 30.0 | | the sparrow **returns** with the flock |
| 33.9 | | the last locust is **eaten** |
| 35.2 | | the Medic **crosses out** the sparrow |
| 37.6 | | the sparrow **perches** by the crow |
| 38.0 | | the tortoise **arrives** |

## Invariants

1. The sparrow stays through every single scare and leaves only after the joint one.
2. The locusts arrive only after the sparrow has gone, and no scare moves them.
3. Every locust that arrives is eaten, by a sparrow that is at that locust when it disappears.
4. The tortoise only ever moves forward, and only while a foot is lifted.
5. The Sleeper's eyes never open.
6. The cut-out grammar holds: whole drawings swapped on twos; positions are the only thing interpolated.
