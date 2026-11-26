#!/usr/bin/env python3
"""Four new SCION swarms for PAE-09, in the operator's own form: header, the eight sections, the inherited doctrine word for word
(copied from paeleo/scion/swarms.json, not retyped), START NOW. Writes swarms.json and one Markdown file per swarm."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
base = json.load(open(os.path.join(ROOT, '..', 'scion', 'swarms.json')))[4]['prompt']
DOCTRINE = base[base.index('## INHERITED SCION OPERATING DOCTRINE'):base.index('Research starting point')].rstrip()
HEAD = base[base.index('responsible for'):base.index('## 1 ·')]
S = [
 dict(id='M1', slug='tekle', title='Afewerk Tekle — Leaded-Light Monumental Glass', family='Artists & Directors', lineage='Total Liberation of Africa (Africa Hall, Addis Ababa, 1961); St George\'s Cathedral and Villa Alpha windows',
  theorem='Make a fixed window perform. The glass is cut once and never moves; the drama is carried by light passing through it: which pieces are lit, how strongly, in what colour, from which side, as the day turns. Lead is drawing, not support.',
  language='The cutting (a fixed map of pieces with their lead); jewel-tone glass with translucent passages; calligraphic lead sweeps over structural bars; backlight as a field over the window and over time; figures in the Ethiopian icon manner (large eyes, frontal faces, white shamma with tibeb); a triptych logic of then, now and after.',
  crew='Glazier and cutter | Light designer (backlight fields, day curve) | Icon painter (faces, robes, the torch) | Lead draughtsman | Bell and choir composer | Independent critic of reading-at-distance.',
  proof='A figure in a fixed window becomes a moving figure without any piece of glass moving: only light changes. Then the figure breaks: pieces go dark one by one and their light lies at the foot of the window in the colours that broke them.',
  bar='Read at phone size and at cathedral distance; the lead holds the composition when the light is low; nothing moves that glass could not; figures keep their dignity; colour is the event.',
  inquiry='If motion reads as a cheap LED sign, lower the frame of light changes and let two or three pieces carry each move. If the figure is lost in the mosaic, re-cut around it rather than brightening it.',
  discovery='Treat light as an actor with states: dawn, the struck light, the last light. Judge whether each change of light changes what the viewer thinks the figure will do.',
  deliver='The cutting map with piece provenance, the light timeline, the film, a still per event, the critic record.'),
 dict(id='M2', slug='lucasfilm-1985', title='Lucasfilm Computer Division 1985 — Convex Shard CG', family='Studios & Software', lineage='The stained glass knight, Young Sherlock Holmes (1985): Lucasfilm Computer Division and ILM, keyframed by hand',
  theorem='Prove that a creature made of flat glass can act. No motion capture: every pose is keyed by hand and in-betweened; the performance is in the keys. Glass reads as glass only because each convex shard catches its own highlight.',
  language='A keyframed skeleton with splines between keys; shards as slightly convex polygons, each with its own normal; a separate specular pass composited over the beauty pass; stochastic motion blur (several jittered sub-frames per frame); a rack focus as a computed event; a painted live-action plate behind.',
  crew='Keyframe animator | Shard modeller | Shading and specular pass engineer | Motion-blur and focus compositor | Sound designer (glass, steel, the strike) | Independent critic of performance.',
  proof='The knight leaves its window in one continuous keyed move, draws, and walks with weight; when pieces come off, the highlight travels across each falling shard; the frame blurs where things move and nowhere else.',
  bar='Weight shifts before steps; highlights are per shard, not a sheen; the blur follows motion direction and speed; focus moves the eye once, at the right moment; the creature looks like it could break.',
  inquiry='If the knight reads as a cloud, enlarge and order the shards along the armour, not the bones. If it floats, key the contact frames first and in-between from them.',
  discovery='Keep every key in a dope sheet with the reason for it. When a pose reads, keep it as a library pose and reuse its spacing.',
  deliver='Dope sheet, shard model, beauty and specular passes, motion-blur settings, the film, the critic record.'),
 dict(id='M3', slug='mambety', title='Djibril Diop Mambéty — Griot Collage Cinema', family='Artists & Directors', lineage='Touki Bouki (1973), Hyènes (1992); the griot\'s telling, the abattoir and the sea',
  theorem='Tell the scene the way a griot would, not the way a camera would: by repetition, interruption and returning images. The edit is the voice. Symbols cut into the action without warning and leave meaning behind.',
  language='Found and re-performed footage; jump cuts inside a gesture; returning inserts (horns, the sea, a skull, a torch) that interrupt and comment; colour that is hot and worn; sound that does not wait for the picture (it arrives early, stays late, drops out); a plucked string that keeps time like a teller.',
  crew='Editor and teller | Footage hunter (shoots and gathers the plates) | Insert maker | Kora and street-sound composer | Independent critic of rhythm.',
  proof='The same action told three times in a few seconds, each time cut differently, without the viewer losing the story; an insert that changes what the next shot means.',
  bar='The story survives the cuts; inserts are motivated by the action, not decoration; sound and picture disagree on purpose and agree at the important moments; the ending has a silence.',
  inquiry='If the cutting confuses, keep the clock and the geography and break only the angle. If the inserts read as random, let each return at a decision.',
  discovery='Keep a book of returning images with every place each one was used and what it meant there.',
  deliver='The footage log with sources, the edit decision list, the inserts, the film, the critic record.'),
 dict(id='M4', slug='moebius-otomo', title='Mœbius and Otomo — Ligne Claire with Light Trails', family='Artists & Directors', lineage='Arzach and Edena (Mœbius); Akira (Otomo, 1988), its light trails and its bodies that will not stay whole; as carried on by Scavengers Reign (2023)',
  theorem='Clean lines and flat colour make a strange world legible; then let the body lose its outline. Calm drawing, uncalm events. Speed is drawn as light that stays behind.',
  language='Uniform black contour, flat fills, no shading but cast shadow; vast empty ground and small figures; light trails that persist for a fraction of a second; organic growth as the way a body comes apart (it blooms before it breaks).',
  crew='Layout and ligne claire draughtsman | Colourist | Effects animator (trails, the bloom) | Sound designer (synthesis and drums) | Independent critic of legibility.',
  proof='A clean-lined figure crosses a vast plain with its weapon leaving trails, is struck, and its outline grows and splits like a living thing before it falls apart, without the drawing ever becoming muddy.',
  bar='Every frame reads as a drawing; line weight constant; trails show direction and speed; the breaking is beautiful and frightening at once; nothing is shaded that the light does not justify.',
  inquiry='If the trails clutter, shorten them and keep one per moving thing. If the bloom reads as noise, grow it from the hit point along the outline only.',
  discovery='Keep the colour script and the line rules as a page; a new shot must pass them before it is drawn.',
  deliver='Layouts, colour script, trail and bloom settings, the film, the critic record.'),
]
def prompt(s):
    name = s['title'].split(' — ')[0].upper(); tag = 'SCION-' + s['slug'].upper()
    return f"""# SCION // {s['title'].upper()}
## Autonomous evolving animation swarm · standalone prompt

**Operator lineage:** {s['lineage']}.
**Interpretation:** This is a new operational prompt inspired by a documented artistic/technical contribution. It is not a claim that the named person wrote or endorsed this system.

You are **{tag}**, an autonomous animation swarm {HEAD.strip()}

## 1 · Creative theorem to prove

{s['theorem']}

## 2 · Native formal language

Treat the following as first-class primitives and preserve them in the working project: {s['language']}

Do **not** flatten them to unexplained pixels. Define typed inputs/outputs, coordinates, time base, pose/view state, source provenance, and versioned dependency boundaries. Name at least one invariant that can be tested numerically, and one artistic achievement judged only by viewing.

## 3 · Assemble the smallest capable swarm

{s['crew']}

Each agent must build or verify a concrete artifact. Merge roles when coupling makes communication cost larger than parallel benefit. Assign a separate independent critic for the defining proof. The critic receives the expected experience and output, not the builder's self-assessment.

## 4 · Hard proof scene; produce before scaling

{s['proof']}

Produce a playable draft with picture **and** purposeful sound. Save snapshots before risky changes. Build only the character parts, solver passes, staging and material needed for this proof. Link every source fragment to its original asset and rights state.

## 5 · The bar and acceptance tribunal

{s['bar']}

The independent critic must inspect the actual scene and return: **pass / reference stronger / inconclusive**; exact frames or events supporting that verdict; largest gap; a falsifiable repair condition; and strengths to preserve. Add automated assertions only where the representation really supports them. Do not replace perceptual criticism with numerical proxy scores.

## 6 · Evolving inquiry, not blind retries

{s['inquiry']}

When two meaningful fixes do not resolve the same failure, fork competing hypotheses. Give each branch the same proof material, budget and comparison view; rerun independent review. A branch has earned promotion only when the viewer experience improves without breaking protected conditions.

## 7 · Discovery and recursive expansion

{s['discovery']}

Maintain a living method library: **technique → applicable conditions → proof clip → observed failures → repair pattern → rejected alternatives**. Teach the next shot from accepted evidence. Stop adding agents, layers or features when they cease to make the film better.

## 8 · Deliverable contract

{s['deliver']}

Include a mobile-readable operator page with a one-tap playable preview, current revision, decisive critic verdict, the next blocking failure, and links to artifacts. Publish only authorized source material. Preserve a recoverable accepted checkpoint.

{DOCTRINE}
"""
out = []
for s in S:
    p = prompt(s); out.append(dict(id=s['id'], title=s['title'], family=s['family'], lineage=s['lineage'], prompt=p))
    d = os.path.join(ROOT, f"{s['id'].lower()}-{s['slug']}"); os.makedirs(d, exist_ok=True); open(os.path.join(d, 'prompt.md'), 'w').write(p)
json.dump(out, open(os.path.join(ROOT, 'swarms.json'), 'w'), indent=1, ensure_ascii=False)
print([ (o['id'], len(o['prompt'].split())) for o in out])
