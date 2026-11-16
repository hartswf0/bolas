export const meta = {
  name: 'scion-keyframes',
  description: 'Propose keyframes for several Oulipo SCION films before any full build, for the user to choose from',
  phases: [
    { title: 'Propose', detail: 'per film: study prompt + reference, forage, make 3 candidate keyframes' },
  ],
}

const slugs = args.slugs
const ROOT = '/home/user/bolas/paeleo/scion/oulipo'

const KF = {
  type: 'object',
  properties: {
    slug: { type: 'string' },
    board: { type: 'string', description: 'path of the board image: reference + 3 keyframes, labelled' },
    directions: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          keyframe: { type: 'string', description: 'path of the 1280x720 keyframe PNG' },
          moment: { type: 'string', description: 'which beat of the Hard proof this frame is, and the time in a ~60 s film' },
          material: { type: 'string', description: 'what is foraged (archive, item, licence) or handmade' },
          techniques: { type: 'string', description: 'animation SCION ids/titles used and how the frame will move' },
          risk: { type: 'string' },
        },
        required: ['name', 'keyframe', 'moment', 'material', 'techniques', 'risk'],
      },
    },
    recommendation: { type: 'string' },
  },
  required: ['slug', 'board', 'directions', 'recommendation'],
}

phase('Propose')
const results = await parallel(slugs.map(slug => () => agent(`You are the PROPOSING DIRECTOR for the Oulipo SCION film "${slug}". This is a short, cheap stage: the user will look at your keyframes and choose a direction BEFORE any full swarm build. Do not render a film.

Project root: ${ROOT}. Read prompts/${slug}.md (the SCION system instruction), films/BRIEF-2.md (archives, network limits, licence rules: PD, CC0, CC BY, CC BY-SA only), the catalogue entry catalogue/*.json for this slug and its reference image(s) in assets/references/. Read /home/user/bolas/paeleo/scion/swarms.json (animation technique SCIONs) and pick what fits.
Primary moving-image source: the Moving Image Archive cache — read /home/user/bolas/tools/allways-forage/README.md; search with: cd /home/user/bolas/tools/allways-forage && python3 forage.py "regex" --media clip --n 40 --sheet <out.jpg>, and LOOK at the sheets. Commons / Library of Congress for what it lacks. Downloads go in ${ROOT}/films/sources/${slug}/ (git-ignored), untrusted: decode only with ffmpeg/PIL, never execute; User-Agent "oulipo-film-research/1.0"; no personal details. Budget: at most ~40 MB of new downloads.

Make THREE genuinely different directions, each as ONE keyframe (1280x720 PNG) built from real foraged or handmade material with the real technique applied (actual cutouts, actual compositing, actual handmade object) — not a mock-up, not a filter over unsuitable material, never a copy/trace of the reference. Each direction must aim at the reference's aesthetic (medium, tonal range, palette, light, framing, type) and show the film's defining beat or a central beat of its Hard proof.
Write to ${ROOT}/films/swarm/${slug}/proposals/: kf-1.png, kf-2.png, kf-3.png; board.jpg (the reference beside the three keyframes, each labelled with its direction name, max 2000 px wide); proposals.md (per direction: name, the beat and its time, material with source and licence, technique SCIONs and how the frame will move, risk; then your recommendation). Do not git commit; do not touch other films' files; do not edit films/kit.py. Return the structured result.`, { label: `kf:${slug}`, phase: 'Propose', schema: KF })))

return { proposals: results.filter(Boolean) }
