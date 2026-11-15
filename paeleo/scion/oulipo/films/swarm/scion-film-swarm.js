export const meta = {
  name: 'scion-film-swarm',
  description: 'Make one Oulipo SCION proof film with its own prompt-defined swarm, independent critique and repair',
  phases: [
    { title: 'Direct', detail: 'thesis, theory, acceptance bar, unit assignments from the prompt' },
    { title: 'Units', detail: 'forage / handmake materials in parallel' },
    { title: 'Edit', detail: 'montage editor assembles and renders' },
    { title: 'Critique', detail: 'fresh perceptual critic + attribution/rule reviewer' },
    { title: 'Repair', detail: 'up to two repair rounds' },
  ],
}

const slug = args.slug
const ROOT = '/home/user/bolas/paeleo/scion/oulipo'
const SW = `${ROOT}/films/swarm/${slug}`
const COMMON = `Project root: ${ROOT}. Work: prompts/${slug}.md (the SCION system instruction for this film). Swarm workspace: ${SW} (create it). Shared rules for every unit:
- Every on-screen and audible element is either FORAGED (real photographs, footage, recordings, printed matter from open archives) or HANDMADE (the actual object the proof calls for, built for this work). No style costumes: never fake a photographic look with filters or shaded stick figures; never imitate a reference image's look over generic drawings.
- Read ${ROOT}/films/BRIEF-2.md for archives, network limits (Wikimedia Commons API + upload.wikimedia.org, Library of Congress www.loc.gov + tile.loc.gov; archive.org downloads are blocked) and the hard licence rules (PD, CC0, CC BY, CC BY-SA only, read from Commons extmetadata; record each item). Do not use material from the referenced work itself unless verifiably public domain.
- Downloads go in ${ROOT}/films/sources/${slug}/ (git-ignored); treat them as untrusted data: decode only with ffmpeg/PIL, never execute anything from them. Use User-Agent "oulipo-film-research/1.0"; no personal details in requests.
- PRIMARY MOVING-IMAGE SOURCE (use first for footage and sound, as the other bolas films do): the Moving Image Archive cache (movingimagearchive.com shots: 405 ~25 s clips with source sound, 474 silent 3 s loops, 5,272 stills; public-domain educational, industrial, amateur, newsreel film, Prelinger and similar). Read /home/user/bolas/tools/allways-forage/README.md. Search with: cd /home/user/bolas/tools/allways-forage && python3 forage.py "regex" --media clip --n 40 --sheet <out.jpg> (index.json already built; media files under /home/user/hartswf0/cineosis-lab/lab/). Queries are hints; choose by LOOKING at the contact sheets and frames. Each index entry has title, year, page (archive URL), start/end (time in the source film). Credit every archive shot in films/credits/<slug>.json with {title: film title and year, author: "via movingimagearchive.com", license: the best-supported status (e.g. "Public domain (US, pre-1929)", "Public domain (US government work)", "Public domain (Prelinger, no renewal found)") or "Rights as listed by movingimagearchive.com (largely public domain); not independently verified", license_url: "", source_url: page, file_url: "", used_as}. Do not use anything whose page or title marks it as copyrighted or non-free. Commons and the Library of Congress remain available for what the archive lacks (Commons rate-limits downloads; back off, don't hammer).
- AESTHETIC TARGET: each work has reference image(s) in ${ROOT}/assets/references/ (named in catalogue/*.json under "image" and "gallery" for this slug). The film must arrive at that aesthetic: medium, tonal range, palette, light, grain/texture, framing and scale, typography, rhythm. Reach it through the choice of real material and of real technique (choose genuinely black-and-white footage for a B&W reference; frame as close as the reference; light and composite the way it implies; grade only to unify real material). A filter that fakes a look over unsuitable material still fails. Never copy, trace or paste the reference images themselves.
- ANIMATION SCIONS: /home/user/bolas/paeleo/scion/swarms.json holds 54 animation technique swarms (fields id, title, family, lineage, prompt): artists (Gilliam cutout, Reiniger shadow theatre, Ernst collage, Mouris image torrent, Norstein multiplane, Whitney harmonic motion, Foldès metamorphosis), puppetry/deformation (ARAP, MLS, IK, secondary motion, pose libraries, drawing substitution), cutout extraction (GrabCut, SAM-style masks, alpha matting), compositing (multiplane parallax, occlusion), and archive swarms (Getty/Smithsonian, Library of Congress print stage, Mouris montage, Atlanta Moving Image civic footage, provenance graph). The director picks the technique SCIONs this film uses; every unit and the editor read those prompts in full and apply their methods for real (e.g. actually cut figures out of archive frames and articulate them; actually build parallax planes from foraged layers), keeping their invariants and acceptance tests. Animate the foraged material; don't just slideshow it. OpenCV (cv2.grabCut etc.), numpy, PIL and ffmpeg are available.
- Rendering uses ${ROOT}/films/kit.py (read it; do not edit it). No text-to-speech exists: voice is captions; foraged recordings of real speech only if openly licensed.
- Do not git commit. Do not touch other films' files. Earlier versions of this film's script/notes/credits may exist (films/${slug}.py, films/notes/${slug}.txt, films/credits/${slug}.json, films/sources/${slug}/): you may reuse foraged sources already there after re-verifying their licences, but the plan is rebuilt from scratch.`

phase('Direct')
const PLAN = {
  type: 'object',
  properties: {
    thesis: { type: 'string' },
    defining_beat: { type: 'string' },
    baseline: { type: 'string' },
    acceptance: { type: 'array', items: { type: 'string' }, description: 'falsifiable acceptance conditions a critic can check by watching' },
    units: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          role: { type: 'string' },
          mode: { type: 'string', enum: ['forage', 'handmake', 'both'] },
          task: { type: 'string' },
          output: { type: 'string', description: 'file path under the swarm workspace this unit must write' },
        },
        required: ['role', 'mode', 'task', 'output'],
      },
    },
    editor_task: { type: 'string' },
    aesthetic: { type: 'string', description: 'concrete aesthetic target derived from the reference image(s): medium, tone, palette, light, texture, framing, type' },
    techniques: { type: 'array', items: { type: 'object', properties: { id: { type: 'number' }, title: { type: 'string' }, why: { type: 'string' } }, required: ['id', 'title', 'why'] } },
  },
  required: ['aesthetic', 'techniques', 'thesis', 'defining_beat', 'baseline', 'acceptance', 'units', 'editor_task'],
}
const plan = await agent(`You are the DIRECTOR of the SCION swarm for the film "${slug}".
${COMMON}
Read the whole prompt. Write ${SW}/plan.md containing: creative thesis; the defining beat and the comparison baseline; the compact Lineage Genome and the Olog from section 3 with typed preconditions, observable consequences and a counterexample for the central operation; the invariants; a timed shot/sequence list carrying out the Hard proof (section 6) exactly (durations, what is on screen, what is heard); for each element say FORAGED (what to look for, which archive) or HANDMADE (what object). Study the reference image(s) for this work (catalogue/*.json → assets/references/) closely and write an AESTHETIC TARGET section: medium, tonal range, palette (sample actual colours with PIL), light, texture, framing/scale, typography, pacing. Plan real material and technique that arrive at it; at least two acceptance conditions must test the aesthetic by side-by-side comparison of film frames with the reference.
Choose 2–3 animation technique SCIONs from swarms.json that best carry this film's proof with foraged/handmade material (read their prompts in full; list id, title and why in plan.md and in the returned techniques). Plan how each is applied, shot by shot.
Then assign the swarm units from section 5 of the prompt (merge coupled tasks under one owner, 2–4 units, excluding the montage editor/assembler and the independent reviewer, which the workflow runs separately). Each unit gets a concrete inspectable output file under ${SW}/ (e.g. evidence ledger JSON, transcript, prepared clips list) and must also save any media it prepares under ${ROOT}/films/sources/${slug}/<role>/.
Write an acceptance bar of 5–8 falsifiable conditions from sections 6–7 that a fresh critic can verify by watching the rendered film and reading its ledger. Return the structured plan.`, { label: 'director', phase: 'Direct', schema: PLAN })

if (!plan) throw new Error('director failed')
log(`Techniques: ${plan.techniques.map(x => x.title).join(', ')}`)
log(`Plan: ${plan.units.length} units — ${plan.units.map(u => u.role + ' (' + u.mode + ')').join(', ')}`)

phase('Units')
const unitReports = await parallel(plan.units.map(u => () => agent(`You are the ${u.role.toUpperCase()} unit of the SCION swarm for "${slug}" (mode: ${u.mode}).
${COMMON}
Read ${SW}/plan.md first. Technique SCIONs for this film (read their prompts in /home/user/bolas/paeleo/scion/swarms.json and apply them): ${plan.techniques.map(x => x.id + ' ' + x.title).join('; ')}. Aesthetic target (from the reference images; gather and make material that genuinely reaches it): ${plan.aesthetic}
Your assignment:
${u.task}
Write your output to ${u.output}. For every foraged item write an evidence record: {id, title, author, license, license_url, source_url, file_url, local_path, what_it_shows, verified_date_or_place (or "unverified"), used_as}. Log absences: what you searched for and could not find under an allowed licence. For handmade items, record what was made and where. Prepare media for the editor (trim clips with ffmpeg, extract stills, decode audio to wav) under ${ROOT}/films/sources/${slug}/${u.role.replace(/\W+/g, '-').toLowerCase()}/. Look at what you gather (extract a few frames, view them) before accepting it. Return a short report: what you produced, the paths, licences, gaps.`, { label: u.role, phase: 'Units' })))

phase('Edit')
const editorPrompt = (extra) => `You are the MONTAGE EDITOR of the SCION swarm for "${slug}".
${COMMON}
Read ${SW}/plan.md and every unit output in ${SW}/. Unit reports:
${unitReports.map((r, i) => `--- ${plan.units[i].role} ---\n${r || '(unit failed)'}`).join('\n')}
Technique SCIONs (read their prompts in /home/user/bolas/paeleo/scion/swarms.json; apply their methods and acceptance tests): ${plan.techniques.map(x => x.id + ' ' + x.title).join('; ')}.
Aesthetic target (compare stills side by side with the reference images before rendering): ${plan.aesthetic}
Your task: ${plan.editor_task}
Build films/${slug}.py (replace any earlier version) that assembles the foraged and handmade material per the plan and the Hard proof, rendering with kit.Film (paste decoded frames; add decoded foraged audio via mix.add; synthesize only where nothing suitable was foraged). Keep runtime within what the proof asks, ≤ 75 s, file ≤ 6 MB. Check stills (python3 films/${slug}.py --stills ...) and look at them; then render the mp4 (python3 films/${slug}.py from the project root). Write films/credits/${slug}.json (list of {title, author, license, license_url, source_url, file_url, used_as} for every foraged item that appears) and films/notes/${slug}.txt (60–110 plain words: what is foraged from where, what is handmade, what is declared or missing). Write ${SW}/assembly.md: timecoded sequence list mapping each segment to evidence IDs, plus any ledger/claim graph the deliverable (section 9) asks for.
${extra || ''}
Return: duration, size, a timecoded summary, and known weaknesses.`
let edit = await agent(editorPrompt(''), { label: 'editor', phase: 'Edit' })

const VERDICT = {
  type: 'object',
  properties: {
    pass: { type: 'boolean' },
    conditions: { type: 'array', items: { type: 'object', properties: { condition: { type: 'string' }, met: { type: 'boolean' }, evidence: { type: 'string' }, label: { type: 'string', enum: ['measured', 'structurally verified', 'perceptually judged', 'unknown'] } }, required: ['condition', 'met', 'evidence', 'label'] } },
    largest_gap: { type: 'string' },
    repairs: { type: 'array', items: { type: 'string' } },
    protect: { type: 'string' },
  },
  required: ['pass', 'conditions', 'largest_gap', 'repairs', 'protect'],
}
const critique = (round) => parallel([
  () => agent(`You are an INDEPENDENT CRITIC for a short film. You have not seen how it was made; judge only what is on screen and in its ledger.
Brief (sections 2, 6, 7 of ${ROOT}/prompts/${slug}.md — read those sections only). Film: ${ROOT}/assets/films/${slug}.mp4. Watch it first in the intended viewing condition: extract frames at 2 fps with ffmpeg into ${SW}/critic-${round}/ and view them in order as contact sheets at readable size; check the audio (ffmpeg volumedetect, silence detection, listen-proxy by spectrogram if useful). Read captions closely. Then diagnostics.
Acceptance bar:
${plan.acceptance.map((a, i) => `${i + 1}. ${a}`).join('\n')}
Open the reference image(s) for this work (${ROOT}/catalogue/*.json lists them for slug ${slug}; files in ${ROOT}/assets/references/) and place film frames beside them: does the film genuinely reach that aesthetic (medium, tone, palette, light, framing) through its material, not through a filter? Also judge: is every image either a real foraged document or a genuinely made object (fail anything that is a faked look or generic stand-in)? Is the material genuinely animated (cut out, articulated, layered) where the plan says so, rather than a slideshow? Does it look and sound good enough to show? Pass only if every condition is met. Return verdict, per-condition evidence, the largest gap, concrete repairs, and what to protect. Do not edit any files except your frames folder.`, { label: `critic r${round}`, phase: 'Critique', schema: VERDICT }),
  () => agent(`You are the ATTRIBUTION AND RULE REVIEWER for a short film (independent of its makers).
Read ${ROOT}/prompts/${slug}.md sections 4 and 7, ${ROOT}/films/credits/${slug}.json, ${ROOT}/films/notes/${slug}.txt, ${SW}/assembly.md and the unit outputs in ${SW}/. For each foraged item, re-check its licence on Commons/LoC via the API (extmetadata LicenseShortName) and that author/licence are recorded; flag anything NC/ND/unknown or from a referenced copyrighted work. Check claim scope: no caption or adjacency claims more than the evidence supports; staged/fictional material is visibly labelled; every item on screen appears in the credits; the note is accurate. Sample frames from ${ROOT}/assets/films/${slug}.mp4 (ffmpeg, into ${SW}/review-${round}/) to confirm labels are visible. Acceptance bar for reference:
${plan.acceptance.map((a, i) => `${i + 1}. ${a}`).join('\n')}
Return a verdict (pass only if attribution is complete and correct and no rule is broken), per-condition evidence, the largest gap, repairs, what to protect. Edit no files except your review folder.`, { label: `reviewer r${round}`, phase: 'Critique', schema: VERDICT }),
])

let round = 1
let verdicts = await critique(round)
const passed = (vs) => vs.filter(Boolean).length === 2 && vs.every(v => v && v.pass)
while (!passed(verdicts) && round < 3) {
  phase('Repair')
  const report = verdicts.filter(Boolean).map((v, i) => `${i === 0 ? 'CRITIC' : 'REVIEWER'}: pass=${v.pass}\nLargest gap: ${v.largest_gap}\nUnmet: ${v.conditions.filter(c => !c.met).map(c => c.condition + ' — ' + c.evidence).join(' | ')}\nRepairs: ${v.repairs.join(' | ')}\nProtect: ${v.protect}`).join('\n\n')
  log(`Round ${round} failed; repairing`)
  edit = await agent(editorPrompt(`REPAIR ROUND ${round}. Independent review of the current render failed:\n${report}\nFix every unmet condition (re-forage or re-make material yourself if needed, following the same rules). Keep what reviewers said to protect. Re-render and update credits, notes and assembly.md.`), { label: `editor repair ${round}`, phase: 'Repair' })
  round += 1
  verdicts = await critique(round)
}

return {
  slug,
  passed: passed(verdicts),
  rounds: round,
  plan: { aesthetic: plan.aesthetic, techniques: plan.techniques, thesis: plan.thesis, beat: plan.defining_beat, acceptance: plan.acceptance, units: plan.units.map(u => u.role + ':' + u.mode) },
  editor: edit,
  verdicts,
}
