export const meta = {
  name: 'scion-film-swarm',
  description: 'Make one Oulipo SCION proof work with its own prompt-defined swarm, blind readers, independent critique, checkpoints and branched repair',
  phases: [
    { title: 'Direct', detail: 'thesis, theory, frozen acceptance bar, reader questions, deliverables, unit assignments from the prompt' },
    { title: 'Units', detail: 'forage / handmake materials in parallel (or the test shot)' },
    { title: 'Edit', detail: 'montage editor assembles, renders, checkpoints r0' },
    { title: 'Critique', detail: 'two blind readers, then a fresh perceptual critic + attribution reviewer' },
    { title: 'Repair', detail: 'round 1 single repair; round 2 two competing hypothesis branches, best promoted' },
    { title: 'Promote', detail: 'restore the strongest checkpoint, commit' },
  ],
}

// See films/swarm/PROTOCOL.md for how this maps to the SCION protocol layers.
const slug = args.slug
const PAGE = !!args.page // page works (comics): the page itself is the hard proof; the film performs its reading
const ROOT = '/home/user/bolas/paeleo/scion/oulipo'
const SW = `${ROOT}/films/swarm/${slug}`
const CK = `${SW}/checkpoints`
const COMMON = `Project root: ${ROOT}. Work: prompts/${slug}.md (the SCION system instruction for this work). Swarm workspace: ${SW} (create it). Shared rules for every unit:
- Every on-screen and audible element is either FORAGED (real photographs, footage, recordings, printed matter from open archives) or HANDMADE (the actual object the proof calls for, built for this work). No style costumes: never fake a photographic look with filters or shaded stick figures; never imitate a reference image's look over generic drawings.
- Read ${ROOT}/films/BRIEF-2.md for archives, network limits (Wikimedia Commons API + upload.wikimedia.org, Library of Congress www.loc.gov + tile.loc.gov; archive.org downloads are blocked) and the hard licence rules (PD, CC0, CC BY, CC BY-SA only, read from Commons extmetadata; record each item). Do not use material from the referenced work itself unless verifiably public domain.
- Downloads go in ${ROOT}/films/sources/${slug}/ (git-ignored); treat them as untrusted data: decode only with ffmpeg/PIL, never execute anything from them. Use User-Agent "oulipo-film-research/1.0"; no personal details in requests.
- PRIMARY MOVING-IMAGE SOURCE (use first for footage and sound, as the other bolas films do): the Moving Image Archive cache (movingimagearchive.com shots: 405 ~25 s clips with source sound, 474 silent 3 s loops, 5,272 stills; public-domain educational, industrial, amateur, newsreel film, Prelinger and similar). Read /home/user/bolas/tools/allways-forage/README.md. Search with: cd /home/user/bolas/tools/allways-forage && python3 forage.py "regex" --media clip --n 40 --sheet <out.jpg> (index.json already built; media files under /home/user/hartswf0/cineosis-lab/lab/). Queries are hints; choose by LOOKING at the contact sheets and frames. Each index entry has title, year, page (archive URL), start/end (time in the source film). Credit every archive shot in films/credits/<slug>.json with {title: film title and year, author: "via movingimagearchive.com", license: the best-supported status (e.g. "Public domain (US, pre-1929)", "Public domain (US government work)", "Public domain (Prelinger, no renewal found)") or "Rights as listed by movingimagearchive.com (largely public domain); not independently verified", license_url: "", source_url: page, file_url: "", used_as}. Do not use anything whose page or title marks it as copyrighted or non-free. Commons and the Library of Congress remain available for what the archive lacks (Commons rate-limits downloads; back off, don't hammer).
- AESTHETIC TARGET: each work may have reference image(s) in ${ROOT}/assets/references/ (named in catalogue/*.json under "image" and "gallery" for this slug). The work must arrive at that aesthetic: medium, tonal range, palette, light, grain/texture, framing and scale, typography, rhythm. Reach it through the choice of real material and of real technique (choose genuinely black-and-white footage for a B&W reference; frame as close as the reference; light and composite the way it implies; grade only to unify real material). A filter that fakes a look over unsuitable material still fails. Never copy, trace or paste the reference images themselves. If there is no reference image, the chosen keyframe is the aesthetic target.
- ANIMATION FIRST, ARCHIVE SECOND: this is an animation project, not an archive edit. Archive material is one source among several, never the default. Consider the full range of animation ideas in swarms.json and beyond: cutout puppetry with articulated joints (Reiniger silhouettes, Gilliam cutouts), multiplane depth (Norstein), harmonic/abstract motion (Whitney), metamorphosis and drawing substitution (Foldès, straight-ahead drawn animation done frame by frame in code), kinetic/typographic animation of the text itself, rotoscoping traced from your own or foraged motion, stop-motion of a handmade object rendered frame by frame, paper/collage animation (Ernst), image-torrent montage (Mouris), procedural/physical simulation, shadow theatre, pixilation. Choose what best carries THIS work's proof and reaches its reference. At least one sequence must be genuinely animated frame by frame (things change shape, move with weight and timing), not only pans and fades over found images.
- ANIMATION SCIONS: /home/user/bolas/paeleo/scion/swarms.json holds 54 animation technique swarms (fields id, title, family, lineage, prompt). The director picks the technique SCIONs this work uses; every unit and the editor read those prompts in full and apply their methods for real, keeping their native primitives, their numeric invariant, their perceptual achievement and their acceptance tests. Animate the foraged material; don't just slideshow it. OpenCV (cv2.grabCut etc.), numpy, PIL and ffmpeg are available.
- Rendering uses ${ROOT}/films/kit.py (read it; do not edit it). No text-to-speech exists: voice is captions; foraged recordings of real speech only if openly licensed.
- CHOSEN DIRECTION (picked by the user from keyframe proposals in ${SW}/proposals/: read proposals.md and look at board.jpg and the chosen kf-N.png): ${args.direction || 'none chosen; derive from the prompt'}. Build that direction; the chosen keyframe is the look to meet or beat. Don't drift to another direction without saying why.${PAGE ? `
- PAGE WORK: the prompt's hard proof is a PAGE (section 6 "draw one page", section 9 deliverables). Deliver BOTH (a) the page itself as ${ROOT}/assets/pages/${slug}.png (print-resolution, at least 2400 px on the long side, real handmade/foraged material, every panel, lettering and route exactly as the proof requires) plus any route lists/annotations section 9 asks for, and (b) the film ${ROOT}/assets/films/${slug}.mp4, which PERFORMS the reading: it walks each route or condition the proof defines over that same page art (camera moves panel to panel, animated reading order, the hinge or fold made visible, panels animated frame by frame where the proof allows), so a viewer experiences the constraint. The page's art and lettering must be identical in page and film.` : ''}
- COMMON SEED: section 10 of the prompt gives the shared station incident (visitor, sealed envelope, bell, brass key, bench, service door stays closed). Use it unless the chosen direction already tells another story; say which in plan.md.
- FROZEN BAR: the acceptance bar in ${SW}/plan.json is fixed once the director writes it. No maker may change it. If a condition proves wrong, write the proposed change and its reason to ${SW}/amendments.md for the operator and keep working to the bar as written.
- TIME BUDGET: this is one short work. Prefer fewer, better shots; stop polishing what already meets the bar. Each unit should finish within about 45 minutes; keep new downloads under ~75 MB.
- Do not git commit. Do not touch other works' files. Earlier versions of this work's script/notes/credits may exist (films/${slug}.py, films/notes/${slug}.txt, films/credits/${slug}.json, films/sources/${slug}/): you may reuse foraged sources already there after re-verifying their licences, but the plan is rebuilt from scratch.`

phase('Direct')
const COND = { type: 'object', properties: { id: { type: 'string' }, text: { type: 'string' }, kind: { type: 'string', enum: ['blocking', 'advisory'] }, evidence: { type: 'string', enum: ['measured', 'structurally verified', 'perceptually judged'] } }, required: ['id', 'text', 'kind', 'evidence'] }
const PLAN = {
  type: 'object',
  properties: {
    thesis: { type: 'string' },
    defining_beat: { type: 'string', description: 'the beat, its time range in the film, and what a viewer should be able to point to' },
    baseline: { type: 'string' },
    acceptance: { type: 'array', items: COND, description: '4-6 blocking conditions (hard proof, section 7 fixture, real material and animation, aesthetic side-by-side) plus up to 4 advisory ones' },
    reader_questions: { type: 'array', items: { type: 'string' }, description: 'the section 7 questions a blind reader must answer from the work alone (e.g. which line shifted the leverage; which earlier captions license this reading); no hints' },
    intended_reading: { type: 'string', description: 'the answers a reader should reach if the proof works (kept from the readers; given to the critic)' },
    deliverables: { type: 'array', items: { type: 'string' }, description: 'every section 9 deliverable as a file path to produce' },
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
    aesthetic: { type: 'string', description: 'concrete aesthetic target derived from the reference image(s) or chosen keyframe: medium, tone, palette, light, texture, framing, type' },
    techniques: { type: 'array', items: { type: 'object', properties: { id: { type: 'number' }, title: { type: 'string' }, why: { type: 'string' } }, required: ['id', 'title', 'why'] } },
  },
  required: ['aesthetic', 'techniques', 'thesis', 'defining_beat', 'baseline', 'acceptance', 'reader_questions', 'intended_reading', 'deliverables', 'units', 'editor_task'],
}
const plan = await agent(`You are the DIRECTOR of the SCION swarm for "${slug}".
${COMMON}
Read the whole prompt. Write ${SW}/plan.md containing: creative thesis and what would make the result bland; the defining beat and the comparison baseline; the compact Lineage Genome and the Olog from section 3 with typed preconditions, observable consequences and a counterexample for the central operation; the invariants (section 4); a timed shot/sequence list carrying out the Hard proof (section 6) exactly (durations, what is on screen, what is heard)${PAGE ? ', and the page layout with every panel, lettering and route' : ''}; for each element say FORAGED (what to look for, which archive) or HANDMADE (what object). Study the reference image(s) (catalogue/*.json → assets/references/), or the chosen keyframe if there are none, and write an AESTHETIC TARGET section: medium, tonal range, palette (sample actual colours with PIL), light, texture, framing/scale, typography, pacing.
Choose 2–3 animation technique SCIONs from swarms.json that best carry this proof (read their prompts in full; list id, title and why). Plan how each is applied, shot by shot, naming each one's numeric invariant and perceptual achievement.
Assign the swarm units from section 5 of the prompt (merge coupled tasks under one owner, 2–4 units, excluding the montage editor, the blind readers, the critic and the reviewer, which the workflow runs separately; do not give a maker unit a validator's or reader's job). Each unit gets a concrete inspectable output file under ${SW}/ and saves media under ${ROOT}/films/sources/${slug}/<role>/.
THE BAR: write 4–6 BLOCKING conditions (the hard proof works; the section 7 fixture passes; material is genuinely foraged/handmade and genuinely animated; the aesthetic holds side by side with the reference or chosen keyframe) and up to 4 ADVISORY ones. Keep numbers only where they test something real; the decisive judgements are perceptual and must say what a viewer sees. Write the section 7 reader questions (no hints) and, separately, the intended reading. List every section 9 deliverable as a file path. Save the whole bar, questions, intended reading and deliverables to ${SW}/plan.json; it is then frozen. Return the structured plan.`, { label: 'director', phase: 'Direct', schema: PLAN })

if (!plan) throw new Error('director failed')
log(`Techniques: ${plan.techniques.map(x => x.title).join(', ')}`)
log(`Plan: ${plan.units.length} units — ${plan.units.map(u => u.role + ' (' + u.mode + ')').join(', ')}`)
const BAR = plan.acceptance.map(c => `${c.id} [${c.kind}, ${c.evidence}] ${c.text}`).join('\n')
const TECH = plan.techniques.map(x => x.id + ' ' + x.title).join('; ')
const summary = () => ({ aesthetic: plan.aesthetic, techniques: plan.techniques, thesis: plan.thesis, beat: plan.defining_beat, acceptance: plan.acceptance, deliverables: plan.deliverables, units: plan.units.map(u => u.role + ':' + u.mode) })

if (args.stage === 'shot') {
  phase('Units')
  const shot = await agent(`You are the TEST-SHOT unit of the SCION swarm for "${slug}". The user will look at this one shot before the full build is approved.
${COMMON}
Read ${SW}/plan.md. Make ONE shot only: the defining beat (${plan.defining_beat}), 5–10 s, from real foraged/handmade material with the chosen techniques genuinely applied (${TECH}) and its sound.${PAGE ? ` Also make the page's defining panels (at least the hinge/turn and its neighbours) as ${SW}/test-page.png at print resolution, with the same art the shot uses.` : ''} Aesthetic target: ${plan.aesthetic}
Write ${SW}/test-shot.mp4 (960x540 or the work's aspect, H.264 + AAC) and ${SW}/test-shot-compare.jpg (the reference or chosen keyframe beside 3 frames from the shot, labelled). Put scripts in ${SW}/test-shot-build/ and media in ${ROOT}/films/sources/${slug}/test-shot/. Record every foraged item (title, author, licence, source_url) in ${SW}/test-shot-ledger.json. Look at your frames before finishing.${args.shotNotes ? ` THIS IS A REDO: the previous test shot was reviewed by the user; move it (test-shot.mp4, test-shot-compare.jpg, test-page.png, test-shot-build/) to ${SW}/test-shot-r1/ first, reuse what works, and fix: ${args.shotNotes}` : ''} Return: what is on screen and heard, sources and licences, how it moves, and its honest weaknesses against the reference and the chosen keyframe.`, { label: 'test shot', phase: 'Units' })
  return { slug, stage: 'shot', plan: summary(), shot }
}

phase('Units')
const unitReports = await parallel(plan.units.map(u => () => agent(`You are the ${u.role.toUpperCase()} unit of the SCION swarm for "${slug}" (mode: ${u.mode}).
${COMMON}
Read ${SW}/plan.md first. Technique SCIONs (read their prompts in /home/user/bolas/paeleo/scion/swarms.json and apply them): ${TECH}. Aesthetic target: ${plan.aesthetic}
Your assignment:
${u.task}${args.shotNotes ? `\nThe test shot (${SW}/test-shot.mp4, test-shot-ledger.json) was approved with notes; reuse its material and build where it works. Notes: ${args.shotNotes}` : ''}
Write your output to ${u.output}. For every foraged item write an evidence record: {id, title, author, license, license_url, source_url, file_url, local_path, what_it_shows, verified_date_or_place (or "unverified"), used_as}. Log absences. For handmade items, record what was made and where. Prepare media for the editor under ${ROOT}/films/sources/${slug}/${u.role.replace(/\W+/g, '-').toLowerCase()}/. Look at what you gather before accepting it. Return a short report: what you produced, the paths, licences, gaps.`, { label: u.role, phase: 'Units' })))

// ---- editing, checkpoints ----
const FILES = `films/${slug}.py, films/credits/${slug}.json, films/notes/${slug}.txt, assets/films/${slug}.mp4, assets/films/${slug}.webp, ${SW}/assembly.md${PAGE ? `, assets/pages/${slug}.png` : ''}`
const checkpointStep = (name) => `When the render is final, save a checkpoint: copy ${FILES} into ${CK}/${name}/ (create it; keep relative paths flat by filename), and write ${CK}/${name}/rev.txt with the time and a one-line description. Never delete an earlier checkpoint.`
const editorPrompt = (extra, name) => `You are the MONTAGE EDITOR of the SCION swarm for "${slug}".
${COMMON}
Read ${SW}/plan.md, ${SW}/plan.json and every unit output in ${SW}/. Unit reports:
${unitReports.map((r, i) => `--- ${plan.units[i].role} ---\n${r || '(unit failed)'}`).join('\n')}
Technique SCIONs (apply their methods and acceptance tests): ${TECH}.
Aesthetic target (compare stills side by side with the reference or chosen keyframe before rendering): ${plan.aesthetic}
Frozen bar:
${BAR}
Your task: ${plan.editor_task}
Build films/${slug}.py (replace any earlier version) that assembles the foraged and handmade material per the plan and the Hard proof, rendering with kit.Film (paste decoded frames; add decoded foraged audio via mix.add; synthesize only where nothing suitable was foraged). Keep runtime within what the proof asks, ≤ 75 s, file ≤ 6 MB. Check stills (python3 films/${slug}.py --stills ...) and look at them; then render the mp4 (python3 films/${slug}.py from the project root).${PAGE ? ` Also produce the page ${ROOT}/assets/pages/${slug}.png from the same art and lettering.` : ''} Produce every deliverable listed in plan.json. Write films/credits/${slug}.json (list of {title, author, license, license_url, source_url, file_url, used_as} for every foraged item that appears, including anything grafted or composited) and films/notes/${slug}.txt (60–110 plain words: what is foraged from where, what is handmade, what is declared or missing). Write ${SW}/assembly.md: timecoded sequence list mapping each segment to evidence IDs, plus any ledger the deliverables ask for.
${extra || ''}
${checkpointStep(name)}
Return: duration, size, a timecoded summary, and known weaknesses.`
let edit = await agent(editorPrompt('', 'r0'), { label: 'editor', phase: 'Edit' })

// ---- review: blind readers, then critic + reviewer ----
const VERDICT = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['pass', 'reference stronger', 'inconclusive'] },
    beats_keyframe: { type: 'boolean', description: 'does the work meet or beat the chosen keyframe' },
    conditions: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, met: { type: 'boolean' }, evidence: { type: 'string' }, label: { type: 'string', enum: ['measured', 'structurally verified', 'perceptually judged (watched)', 'perceptually judged (from frames)', 'unknown'] } }, required: ['id', 'met', 'evidence', 'label'] } },
    largest_gap: { type: 'string' },
    repairs: { type: 'array', items: { type: 'string' } },
    protect: { type: 'string' },
  },
  required: ['verdict', 'beats_keyframe', 'conditions', 'largest_gap', 'repairs', 'protect'],
}
const RIGHTS = {
  type: 'object',
  properties: {
    attribution_ok: { type: 'boolean', description: 'every foraged item on screen/audible is credited with an allowed, correctly read licence and required attribution' },
    blocking_issues: { type: 'array', items: { type: 'string' }, description: 'licence or attribution problems only' },
    process_notes: { type: 'array', items: { type: 'string' }, description: 'claim-scope, labelling and process slips: logged and fixed, not blocking' },
    repairs: { type: 'array', items: { type: 'string' } },
  },
  required: ['attribution_ok', 'blocking_issues', 'process_notes', 'repairs'],
}
const READER = { type: 'object', properties: { answers: { type: 'array', items: { type: 'string' } }, what_i_saw: { type: 'string' }, confusions: { type: 'string' } }, required: ['answers', 'what_i_saw', 'confusions'] }
const viewing = (dir, film) => `Watch it in the intended viewing condition as closely as you can: extract frames at 2 fps into ${dir}/ and view them in order as contact sheets at readable size; for the defining beat (${plan.defining_beat}) also extract every frame at full rate and view them as strips, so motion and timing are judged, not guessed; check the audio (ffmpeg volumedetect, silencedetect, onsets/spectrogram). Film: ${film}.${PAGE ? ` Page: ${ROOT}/assets/pages/${slug}.png (view it whole, then at 100% in tiles).` : ''}`

const readers = (round, film) => parallel([1, 2].map(n => () => agent(`You are BLIND READER ${n}. You know nothing about how this work was made or what it is meant to show. ${viewing(`${SW}/readers-${round}-${n}`, film)}
Then answer these questions from the work alone, in your own words, citing frames/times or panels:
${plan.reader_questions.map((q, i) => `${i + 1}. ${q}`).join('\n')}
Do not open any file other than the work itself and your frames folder (no prompts, plans, notes, credits or ledgers). Edit nothing else.`, { label: `reader ${n} r${round}`, phase: 'Critique', schema: READER })))

const critic = (round, film, readerAnswers, label) => agent(`You are an INDEPENDENT CRITIC. You have not seen how this was made; judge only what is on screen/page and in its ledger.
Brief: sections 2, 6 and 7 of ${ROOT}/prompts/${slug}.md (read only those). ${viewing(`${SW}/critic-${label || round}`, film)} Review the experience first, diagnostics after.
Frozen bar (judge exactly this; do not add or relax conditions):
${BAR}
Intended reading: ${plan.intended_reading}
Two blind readers answered the section 7 questions from the work alone:
${JSON.stringify(readerAnswers || [], null, 1)}
Compare their answers with the intended reading: where they diverge is evidence the fixture fails.
Open the reference image(s) (catalogue/*.json lists them for slug ${slug}; files in ${ROOT}/assets/references/) and the chosen keyframe in ${SW}/proposals/ and place frames beside them. Verdict: "pass" only if every blocking condition is met and the work is at least as strong as the reference on the qualities the bar names; "reference stronger" if the reference clearly carries the experience better; "inconclusive" if you cannot judge in the intended condition. Say whether it meets or beats the chosen keyframe. Label each condition's evidence honestly (from frames is not watched). Do not replace perceptual judgement with numeric proxies. Return per-condition evidence, the largest gap as a falsifiable condition, concrete repairs, and what to protect. Edit no files except your frames folder.`, { label: `critic ${label || 'r' + round}`, phase: 'Critique', schema: VERDICT })

const reviewer = (round) => agent(`You are the ATTRIBUTION AND RULE REVIEWER (independent of the makers).
Read ${ROOT}/prompts/${slug}.md sections 4 and 7, ${ROOT}/films/credits/${slug}.json, ${ROOT}/films/notes/${slug}.txt, ${SW}/assembly.md, ${SW}/plan.json and the unit outputs in ${SW}/. Trace every file the render opens (films/${slug}.py and anything its pieces were built from) to a credits entry. For each foraged item re-check its licence on Commons/LoC (extmetadata LicenseShortName; back off on 429 and say if you relied on cached evidence) and that the attribution the licence requires (author, licence, title or link, modification) is given. BLOCKING: NC/ND/unknown licences, uncredited items, missing required attribution, material from a referenced copyrighted work. NOT BLOCKING (process notes, to be fixed): claim-scope overstatements, unlabeled staging, inaccurate notes or ledgers, bar amendments (check ${SW}/amendments.md). Sample frames from ${ROOT}/assets/films/${slug}.mp4 into ${SW}/review-${round}/ to confirm labels are visible. Edit no files except your review folder.`, { label: `reviewer r${round}`, phase: 'Critique', schema: RIGHTS })

const FILM = `${ROOT}/assets/films/${slug}.mp4`
const review = async (round) => {
  const rs = await readers(round, FILM)
  const [cv, rv] = await parallel([() => critic(round, FILM, rs), () => reviewer(round)])
  return { round, readers: rs, critic: cv, rights: rv }
}
const blockingMet = (cv) => !cv ? -1 : plan.acceptance.filter(c => c.kind === 'blocking').filter(c => (cv.conditions.find(x => x.id === c.id) || {}).met).length
const ok = (r) => r.critic && r.critic.verdict === 'pass' && r.rights && r.rights.attribution_ok
const reportOf = (r) => `CRITIC: ${r.critic ? r.critic.verdict : 'failed'}; beats keyframe: ${r.critic ? r.critic.beats_keyframe : '?'}
Largest gap: ${r.critic ? r.critic.largest_gap : ''}
Unmet: ${r.critic ? r.critic.conditions.filter(c => !c.met).map(c => c.id + ' — ' + c.evidence).join(' | ') : ''}
Repairs: ${r.critic ? r.critic.repairs.join(' | ') : ''}
Protect: ${r.critic ? r.critic.protect : ''}
BLIND READERS: ${JSON.stringify(r.readers)}
RIGHTS: attribution_ok=${r.rights ? r.rights.attribution_ok : '?'}; blocking: ${r.rights ? r.rights.blocking_issues.join(' | ') : ''}; process notes (fix these too): ${r.rights ? r.rights.process_notes.join(' | ') : ''}`

const history = []
let cur = await review(1)
history.push({ checkpoint: 'r0', ...cur })

// Round 1 repair: one editor.
if (!ok(cur)) {
  phase('Repair')
  log('Round 1 failed; single repair')
  edit = await agent(editorPrompt(`REPAIR ROUND 1. Independent review of checkpoint r0 failed:\n${reportOf(cur)}\nFix every unmet blocking condition and every rights issue (re-forage or re-make material yourself if needed, same rules). Keep what the critic said to protect. Re-render and update credits, notes and assembly.md.`, 'r1'), { label: 'editor repair 1', phase: 'Repair' })
  cur = await review(2)
  history.push({ checkpoint: 'r1', ...cur })
}

// Round 2: competing hypotheses on separate branches, judged side by side, the better one promoted.
if (!ok(cur)) {
  phase('Repair')
  log('Round 2: branching on two hypotheses')
  const HYP = { type: 'object', properties: { gap: { type: 'string' }, a: { type: 'string' }, b: { type: 'string' }, comparison: { type: 'string' } }, required: ['gap', 'a', 'b', 'comparison'] }
  const hyp = await agent(`Two reviews of "${slug}" have failed. Review history:\n${history.map(h => `== ${h.checkpoint} ==\n${reportOf(h)}`).join('\n')}\nRead ${SW}/plan.md and look at checkpoint r1 (${CK}/r1/). State the persisting gap, then TWO meaningfully different explanations of why it persists (e.g. pose readability vs. staging; material mismatch vs. timing), each with the repair it implies, and the smallest side-by-side comparison that decides between them. Edit no files.`, { label: 'hypotheses', phase: 'Repair', schema: HYP })
  if (!hyp) throw new Error('hypotheses agent failed; r1 is the latest checkpoint')
  const branch = (k, h) => agent(`You are BRANCH EDITOR ${k.toUpperCase()} for "${slug}".
${COMMON}
Start from checkpoint r1 (${CK}/r1/). Work ONLY in ${SW}/branch-${k}/: copy films/${slug}.py there as ${slug}.py, change its output path so it renders ${SW}/branch-${k}/${slug}.mp4${PAGE ? ` and ${SW}/branch-${k}/${slug}.png` : ''}, and do not write to assets/, films/${slug}.py, credits or notes. Persisting gap: ${hyp.gap}. Your hypothesis: ${h}. Apply the repair it implies, and only that, keeping everything the critic said to protect: ${cur.critic ? cur.critic.protect : ''}. Also fix these rights issues in a branch copy of the credits/notes (${SW}/branch-${k}/credits.json, notes.txt): ${cur.rights ? cur.rights.blocking_issues.concat(cur.rights.process_notes).join(' | ') : ''}. Render, look at the frames, write ${SW}/branch-${k}/branch.md (what changed and why). Return a short report.`, { label: `branch ${k}`, phase: 'Repair' })
  await parallel([() => branch('a', hyp.a), () => branch('b', hyp.b)])
  const [ra, rb] = await parallel([() => readers('a', `${SW}/branch-a/${slug}.mp4`), () => readers('b', `${SW}/branch-b/${slug}.mp4`)])
  const [ca, cb] = await parallel([
    () => critic(3, `${SW}/branch-a/${slug}.mp4`, ra, 'branch-a'),
    () => critic(3, `${SW}/branch-b/${slug}.mp4`, rb, 'branch-b'),
  ])
  const score = (c) => (c ? (c.verdict === 'pass' ? 100 : 0) + blockingMet(c) * 10 + (c.beats_keyframe ? 1 : 0) : -1)
  const win = score(ca) >= score(cb) ? 'a' : 'b'
  const wc = win === 'a' ? ca : cb
  log(`Branch ${win} wins (${score(ca)} vs ${score(cb)}); comparison: ${hyp.comparison}`)
  if (score(wc) > score(cur.critic)) {
    edit = await agent(`You are the PROMOTION EDITOR for "${slug}". Branch ${win} (${SW}/branch-${win}/) beat checkpoint r1 in independent review. Promote it: make its ${slug}.py the project's films/${slug}.py with the normal output paths, move its credits/notes changes into films/credits/${slug}.json and films/notes/${slug}.txt, update ${SW}/assembly.md, re-render from the project root (python3 films/${slug}.py), and check the render matches the branch. ${checkpointStep('r2')} Write ${SW}/branches.md recording both hypotheses, both verdicts and why ${win} won. Return a short report.`, { label: 'promote branch', phase: 'Repair' })
    const rv = await reviewer(3)
    cur = { round: 3, readers: win === 'a' ? ra : rb, critic: wc, rights: rv }
    history.push({ checkpoint: 'r2', ...cur })
  } else {
    log('Neither branch beat r1; r1 is kept')
  }
}

// ---- promote the strongest checkpoint, commit ----
phase('Promote')
const rank = (h) => (ok(h) ? 1000 : 0) + (h.rights && h.rights.attribution_ok ? 100 : 0) + blockingMet(h.critic) * 10 + (h.critic && h.critic.beats_keyframe ? 1 : 0)
const best = history.reduce((a, b) => (rank(b) >= rank(a) ? b : a))
const last = history[history.length - 1]
await agent(`You are the CHECKPOINT KEEPER for "${slug}" in ${ROOT}. ${best.checkpoint !== last.checkpoint ? `The strongest reviewed checkpoint is ${best.checkpoint}, not the latest (${last.checkpoint}). Restore it: copy the files in ${CK}/${best.checkpoint}/ back to their places (${FILES}), and check the mp4 plays (ffprobe). Keep the note text exactly as saved in that checkpoint.` : `The latest checkpoint ${best.checkpoint} is the strongest; check that the files in place (${FILES}) match ${CK}/${best.checkpoint}/ and that the mp4 plays (ffprobe).`}
Write ${SW}/review-history.json: ${JSON.stringify(history.map(h => ({ checkpoint: h.checkpoint, critic: h.critic && h.critic.verdict, beats_keyframe: h.critic && h.critic.beats_keyframe, blocking_met: blockingMet(h.critic), attribution_ok: h.rights && h.rights.attribution_ok })))} plus a "promoted": "${best.checkpoint}" field.
Then commit ONLY this work's files: cd /home/user/bolas && git add paeleo/scion/oulipo/films/swarm/${slug} paeleo/scion/oulipo/films/${slug}.py paeleo/scion/oulipo/films/credits/${slug}.json paeleo/scion/oulipo/films/notes/${slug}.txt paeleo/scion/oulipo/assets/films/${slug}.mp4 paeleo/scion/oulipo/assets/films/${slug}.webp${PAGE ? ` paeleo/scion/oulipo/assets/pages/${slug}.png` : ''} (skip missing paths; never add an mp4 that ffprobe rejects), then git commit -m "${slug}: swarm build, promoted ${best.checkpoint}" with the trailer lines "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" and "Claude-Session: https://claude.ai/code/session_012XUjiSZ2P4CmYc3BGshy5Q", and git push origin ccr-f14a901a-67gkmo. If git reports index.lock, wait 20 s and retry (another build may be committing); if push is rejected, git pull --no-rebase --no-edit origin ccr-f14a901a-67gkmo then push. Do not use --force. Return what was promoted and the commit id.`, { label: 'checkpoint keeper', phase: 'Promote' })

return {
  slug,
  passed: ok(best),
  promoted: best.checkpoint,
  plan: summary(),
  editor: edit,
  history: history.map(h => ({ checkpoint: h.checkpoint, critic: h.critic, rights: h.rights, readers: h.readers })),
}
