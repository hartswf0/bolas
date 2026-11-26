"""Writes each swarm's method.md: the builder's account (thesis, materials, limits) and the measured facts from invariants.json."""
import json, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def facts(m):
    r = json.load(open(os.path.join(ROOT, m, 'invariants.json')))
    ev = ', '.join(f"{e['what']} {e['t']:.1f}→{e['found_at']:.2f}" if e['found_at'] is not None else f"{e['what']} {e['t']:.1f}→not found" for e in r['I1']['events'])
    i3 = ', '.join(f"{p['paint']} {p['colour_match']:.0%}" for p in r['I3']['pieces'])
    s = f"""## Measured (from this film's own label mask and pixels, `invariants.json`)

- **I1, events at time:** {'hold' if r['I1']['ok'] else 'do not all hold'}. {ev}.
- **I2, out of the glass:** {'holds' if r['I2']['ok'] else 'fails'}. Inside the window in {r['I2']['inside_before_4_5']:.0%} of frames before 4.5 s, outside it in {r['I2']['outside_after_5_5']:.0%} after 5.5 s.
- **I3, the pieces stay, in their colour:** {'holds' if r['I3']['ok'] else 'fails'}. Hue held by shot: {i3}.
- **I4, the distance follows the score:** {'holds' if r['I4']['ok'] else 'fails'}. {r['I4']['within_15pct']:.0%} of {r['I4']['frames']} frames within ±15 %, r = {r['I4']['r']:.3f}.
"""
    if r.get('skipped_frames'): s += f"- **Frames measured:** {r['measured_frames']} of 576. The other {r['skipped_frames']} are inserts and re-tellings, listed in `trace.json` (`edl`); they are not the master geography.\n"
    return s
MESA = "a Black man in his sixties with a long white beard and gold-lensed round glasses, in a cream wide-brimmed hat, a white guayabera-style shirt{badge}, khaki trousers and dark boots"
M = {
'm1-tekle': ("SCION-TEKLE · Afewerk Tekle: leaded-light monumental glass", f"""## Thesis
One window, cut once, and **no piece of glass moves for 24 seconds.** The figures, the blow and the fallen pieces are all light passing through fixed glass.

- **The cutting.** A Voronoi cutting of about 4,970 pieces. It is finer where the story will pass (the glazier cuts knowing the score) and coarser in the dune and the wall.
- **The lead.** It draws the architecture (dune line, wall, lancet, sill, steps, floor joints) and sweeps calligraphically over the nave.
- **Each frame.** Every piece takes the light that most of it receives: the figure's colour, crisp by majority, or the backlight through its own pot colour. Its body texture and the lead never change.
- **The knight's pieces.** The knight is first a figure in the window's own blue glass. Where paint takes it, its pieces go dark, and pieces of the floor glass light up in the paint's colour.
- **The light.** The columns of light and the day curve are a light timeline over the same glass.

## Made of
- the cutting (`build/render.py`, `cutting()`);
- the figures as light (`build/figures.py`):
  - **Uncle Mesa:** {MESA.format(badge=' with the MESA CHIP badge')};
  - **the knight:** plates of silver, gold and red with a red glass sword;
- the sound: a breathing choir chord, bells at the events, glass chimes for each shot's pieces and a low bell for the fall.
""", """## Judged, not measured
Whether the motion reads as glass and not as an LED sign, whether the figures keep their dignity at this piece size, and whether colour is the event.

## Known limits
At this piece size Uncle Mesa's face and glasses are only a few pieces of glass. His beard and hat read, but his face does not. The icon manner (large eyes, frontal faces) is not achieved: grisaille painting would be fired onto fixed glass and could not move.
"""),
'm2-lucasfilm-1985': ("SCION-LUCASFILM-1985 · Lucasfilm Computer Division 1985: convex shard CG", f"""## Thesis
A creature of flat glass acts, because every pose is keyed by hand and every shard catches its own highlight.

- **The dope sheet.** `build/dopesheet.py`; each key's reason is in `dopesheet.json`.
  - Uncle Mesa's poses: settle, aim, recoil, down, kneel, sit.
  - The knight's poses: look, crouch, air, land, draw, guard, raise, strike.
  - The walk is a keyed cycle (contact, down, passing, up) laid step by step, with Catmull-Rom in-betweens. There is no motion capture and no procedural walk.
- **Ground contact.** The lowest point of each pose is put on the ground, so weight lands.
- **The knight's shards.** 160 convex shards with their own normals, so the highlight travels across the armour and across every falling shard as it tumbles.
- **The passes.** A beauty pass and a separate specular pass with bloom.
- **Motion blur.** Four jittered sub-frames per frame across a 180° shutter.
- **The rack focus.** One computed rack: on Uncle Mesa coming down, to the knight in the far window at the head turn, and back when it leaps.
- **Uncle Mesa** is painted as the plate actor, soft, with a key-light gradient and his own grain: {MESA.format(badge=' with the MESA CHIP badge')}.

## Made of
- `build/dopesheet.py` (the keys) and `build/render.py` (FK, the shard skin, the passes, the plate, the sound);
- the sound: low strings, boot heels on the keyed contacts, glass-and-steel feet, the sword's ring, a glass cascade per shot and the strike's thud.
""", """## Judged, not measured
Whether the weight shifts before steps, whether the highlights read as per shard, and whether the knight looks like it could break.

## Known limits
The plate is a painted backdrop, not live action, and Uncle Mesa is a painted figure standing in for the plate actor. The feet can slide a little during the advance, because the keyed cycle is not locked to the score's speed.
"""),
'm3-mambety': ("SCION-MAMBETY · Djibril Diop Mambéty: griot collage cinema", f"""## Thesis
The scene is told the way a griot would tell it: the clock is kept and the angle is broken.

- **Torn from the game's own pictures.** Everything is paper cut from the MESA CHIP stills and its two recorded clips (`build/footage.py`).
  - The backdrop is strips torn from five frames.
  - The figures are stiff cards. For each card the footage hunter cut the material from the frame whose colour and grain came closest, and logged it in `assets.json`.
- **Holds and jump cuts.** The master holds and jumps on a plucked rhythm of 2, 1, 1, 3, 1, 2, 1, 1, 2, 3 frames, and cuts on the frame at each event.
- **The walk** is two cards swapped on each hold.
- **Told more than once.** The first hit and the fall are each told three times: the master, then the same moment again in a closer crop, then again mirrored and closer, while the clock goes on underneath. The shatter is told twice.
- **Returning images** interrupt at decisions:
  - the zebu horns from the game's horned motorcycle, three times;
  - the sea, twice;
  - the kanaga, the game's own shatter and a mural, once each.
- **The ending.** It ends on the sea, in silence.
- **The grade.** Hot and worn: saturated and warm, with flicker, grain, scratches, dust and gate weave.

## Made of
- **Uncle Mesa:** {MESA.format(badge='')}, cut as seven cards.
- **The knight:** a card of 52 torn pieces of the game's silver, gold and red glass.
- **The sound:**
  - a Karplus-Strong plucked string keeps the teller's time over a street hum;
  - each shot arrives a little before its picture;
  - the fall is heard three times, as it is told;
  - a low horn sounds under the horns;
  - the street stops for the last silence.
""", """## Judged, not measured
Whether the story survives the cuts, whether the inserts are motivated, and whether sound and picture disagree on purpose.

## Known limits
The figures are cut from the footage's colour, not from footage of people. The game's frames show Uncle Mesa mostly from behind, so the hunter took his materials (shirt, hat, skin, khaki) and the swarm drew the cards. The invariants are measured only on master frames. The re-tellings and inserts are left out of the measurement and listed with their times in `trace.json`.
"""),
'm4-moebius-otomo': ("SCION-MOEBIUS-OTOMO · Mœbius and Otomo: ligne claire with light trails", f"""## Thesis
Clean lines and flat colour make a strange world legible. Then the body is let go of its outline.

- **The line.** One black contour of constant weight: 2 px at film size, drawn at 2× and reduced.
- **The colour.** Fills are flat. The only darkness is cast shadow: every figure throws a flat sheared shadow away from the light.
- **The place.** A vast pale glass floor in bands, the dune overhead with round openings, flat columns of light (one moves with the score) and small figures.
- **Light trails.** Speed is drawn as light that stays behind: the sword's tip, the knight's leap out of the window, and every paint shot from muzzle to target.
- **The bloom.** Where paint takes the knight, each freed piece blooms first: its outline grows coral lobes for 0.22 s, then it splits off and falls. At the last shot the whole knight blooms at once.

## Made of
- **Uncle Mesa:** {MESA.format(badge=' with a gold badge')}.
- **The knight:** panels of silver, steel, gold and red, with a red plume and a red glass sword.
- **The sound:**
  - a synth pad;
  - drums that come in with the gun and drive toward each break;
  - a zap for each shot, a rising shimmer for each bloom and a crash as the pieces let go;
  - a big drum and crash for the last bloom.
""", """## Judged, not measured
Whether every frame reads as a drawing, whether the trails show direction and speed, and whether the breaking is beautiful and frightening at once.

## Known limits
The figures are small and simple, close to stick-and-panel construction: Mœbius's hands, folds and faces are not attempted. The knight's panels are a regular grid, not a designed armour.
"""),
}
REPAIRS = {
 'm1-tekle': "- **Lead around the held poses.** The window is re-cut with lead around the poses where the figures hold: the knight in the window, Uncle Mesa aiming, lying and seated. When a figure is there, the lead draws it. When it has gone, the outline stays in the glass as the window's memory. This keeps the theorem, since the glass still never moves.\n- **The face.** A large eye in the icon manner and a round gold lens of their own.\n- **The visor.** Larger, and it swings further when the knight turns its head.\n- **The first hit.** It is aimed at the shoulder.\n- **The fall, the rise and the sit.** Acted: the knees give before he falls, and each move takes 6 frames or more.\n- **The mirror floor.** Reflections are stronger.\n- **A coda light.** It crosses the floor and lights the pieces as it passes.\n\n**After round 2:**\n- **The light draws the contour.** A ring of unlit glass is left around every lit figure, so dark glass draws the contour of every pose and not only the held ones.\n- **The mirror.** The reflection in the floor is foreshortened, as seen from above.\n- **The window remembers.** In the coda, the knight's outline glows in the empty window.\n- **Two lenses** for Uncle Mesa.\n- **The later shots** lie under the earlier ones on the floor.\n\n**After round 3:**\n- **Every held pose gets its own cut:** the knight on the pier, and Uncle Mesa holding his ground at 15–20 s.\n- **The sword** is held high, off him, after he rises.\n- **The empty window flashes** in each shot's colour.",
 'm2-lucasfilm-1985': "- **The rack focus.** It finishes on the knight before the head turn, and the visor swings further.\n- **The hat.** It stays on the floor until he takes it up as he rises, so it is never in two places.\n- **The get-up.** It takes 0.65 s, with one knee down and a hand on the floor.\n- **The gun.** It stays down once he sits.\n- **Uncle Mesa.** The beard is now distinct from the shirt (whiter, with its own edge, longer), with two round gold lenses, guayabera pleats and pockets.\n- **The step.** Brighter.\n- **A coda light.** It crosses the pile.\n- **Motion blur.** Six sub-frames instead of four.\n- **The paint is matte** and holds its colour in shadow. Brighter light scales the glass rather than clipping it, and the light shafts multiply what they fall on, so every shard keeps its hue.\n- **The later shots** lie under the earlier ones.",
 'm3-mambety': "- **The coda.** A close shot of the pile with a light crossing it, in the silence. The sea no longer ends the film.\n- **The mirror.** A reflection in the floor of the action.\n- **The horns take the paint.** Each return of the horns carries every colour fired so far, so the third return comes back painted in all six.\n- **The step.** Drawn, with a lit edge.\n- **The head turn.** The visor swings a third of the helmet.\n- **The knight.** It strides, with the sword raised off him.\n- **Uncle Mesa.** Two gold lenses, a yellow badge card, and khaki cut from a cleaner patch of footage.",
 'm4-moebius-otomo': "- **The mirror floor.** Every figure is reflected about its foot line: flat, lined, lower in value.\n- **A coda light.** It crosses the pile, and the pieces brighten under it.\n- **The pieces.** Each keeps a core of the knight's own glass under the paint, and the sword falls at its own scale.\n- **The knight.** It strides, with the sword raised off him.\n- **The fall and the rise.** Acted: the knees give first.\n- **Uncle Mesa.** An eye, a nose, a round gold-rimmed lens, a long tapering beard, guayabera pleats and pockets, and a yellow badge.\n- **The last bloom.** A push-in (19.54–20.1 s, not measured).\n- **The hits.** Sharper, with glass chimes.\n\n**After round 2:**\n- **The push-in** stays inside the drawing, with no black bars.\n- **The pieces** brighten under the coda light, scaled so they keep their hue.\n- **The tracers** are wider and persist longer.\n- **The knight has two legs.**\n- **The scene** moves in from the left edge.\n- **The badge** sits clear of the beard, and the pleats are darker.\n- **The last shot's pieces** lie under the earlier ones.",
}
HEAD = "**Film:** `film.mp4` (960×540, 24 fps, H.264 + AAC, 24 s). **Rebuild:** `python3 build/render.py` (numpy, Pillow, scipy, ffmpeg).\n\n"
if __name__ == '__main__':
    for m, (title, a, b) in M.items():
        try: f = facts(m)
        except Exception as e: f = f"## Measured\n\n(not yet: {e})\n"
        open(os.path.join(ROOT, m, 'method.md'), 'w').write(f"# {title}. PAE-09, MESA CHIP\n\n{HEAD}{a}\n## Repairs after critic round 1\n\n{REPAIRS[m]}\n\n{f}\n{b}")
    print('ok')
