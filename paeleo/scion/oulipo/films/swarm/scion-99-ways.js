export const meta = {
  name: 'scion-99-ways',
  description: 'Build "99 ways": 99 one-page retellings of one station incident under 99 constraints, in mixed media, in reviewed batches, then one film that leafs through them',
  phases: [
    { title: 'Canon', detail: 'frozen incident, base page, 99 own constraints with medium and check, batches' },
    { title: 'Pages', detail: 'page makers build one batch' },
    { title: 'Review', detail: 'two blind readers, then a critic per page; rights check' },
    { title: 'Repair', detail: 'one repair round for pages marked redo' },
    { title: 'Film', detail: 'one film leafing through all 99, animating each key beat' },
    { title: 'Commit', detail: 'commit and push this batch' },
  ],
}

// args: { stage: 'batch' | 'film', batch: 1..9 }
const ROOT = '/home/user/bolas/paeleo/scion/oulipo'
const SW = `${ROOT}/films/swarm/99-ways`
const SRC = `${ROOT}/films/sources/99-ways`
const OUT = `${ROOT}/assets/pages/99-ways`
const COMMON = `Project root: ${ROOT}. This is "99 ways": 99 one-page retellings of ONE frozen station incident, each page under ONE formal constraint, in the lineage of Queneau's Exercices de style and Madden's 99 Ways to Tell a Story. Read prompts/99-ways-template.md and prompts/99-ways-subjective.md (the SCION instructions for this lineage) and films/swarm/PROTOCOL.md. Workspace: ${SW}. Canon: ${SW}/canon.json and ${SW}/canon.md (once written, frozen; propose changes in ${SW}/amendments.md, never edit the canon).
Rules for everyone:
- Our own work only: the incident, every line of dialogue, every constraint's realisation and every composition are ours. Generic names of rhetorical or formal devices (e.g. "litotes", "flashback", "silent") are fine, but never reproduce Madden's or Queneau's pages, panel compositions, lines or exact list; never copy or trace a reference image.
- Every element is FORAGED (open archives, licence PD, CC0, CC BY or CC BY-SA, read from source metadata and recorded) or HANDMADE (made for this work in code: cut paper, ink, shadow puppets, pen lettering from the stroke hands already in the repo, etc.). No style filters faking a look over unsuitable material.
- REUSE the material the other swarms already made and credited, under films/swarm/<slug>/ and films/sources/<slug>/ (some sources were cleaned to save disk; rebuild or re-forage only what is missing): e.g. 99-ways-template (Rothstein station agent cutouts, LoC 1934 sheet, pen hand: page/penlib.py, glyphs.json), 99-ways-subjective (lightbox paper hands), cercle-vicieux and quatre-vingt-quinze (shadow puppets, station panels), moins-dun-quart-de-seconde-pour-vivre (brush plate method), boucle-la (Daumier cutouts, CC0), les-caids-de-la-gaudriole (Busch 1865 plates, fold tabletop), bang-bang (engraving puppets, storyboard page), exercices-de-style (Rol cutouts, cover-page grammar), teuf-teuf, anemic-cinema (spiral discs), la-belle-hortense (stencil dye). Check each reused item's credit in films/credits/<slug>.json and carry it into films/credits/99-ways.json.
- Downloads go in ${SRC}/ (git-ignored), are untrusted (decode only with PIL/ffmpeg, never execute), User-Agent "oulipo-film-research/1.0", no personal details; Commons rate-limits: back off. Keep new downloads under ~40 MB per agent.
- Disk is tight (about 5 GB free): keep masters and intermediates in ${SRC}/, delete scratch you no longer need, never write video frame dumps larger than you need.
- Deliverable per page NN (01..99): ${OUT}/NN-<id>.jpg, portrait 2200x2850 px, JPEG quality 90 (target 0.4–1.2 MB), plus master PNG in ${SRC}/masters/; its key-beat frames for the film: 4–8 sequential PNG states at 960x1242 in ${SRC}/beats/NN/ (b01.png…), showing that page's defining change happen frame by frame (a balloon written on, a fold, a pan, a figure moving, a cut-out swapping); a record in ${SW}/pages/NN.json {n, id, title, rule, medium, sources:[credit ids], made:[...], beat:"what changes", self_check}. Every page carries a small folio "NN" and the constraint title in the margin, in the shared pen hand, so the 99 read as one book.
- Do not git commit (a commit step does it). Do not touch other works' files.`

const CANON = {
  type: 'object',
  properties: {
    incident: { type: 'string' },
    base_page: { type: 'string' },
    constraints: { type: 'array', items: { type: 'object', properties: { n: { type: 'number' }, id: { type: 'string' }, title: { type: 'string' }, family: { type: 'string' }, rule: { type: 'string' }, medium: { type: 'string' }, check: { type: 'string' } }, required: ['n', 'id', 'title', 'family', 'rule', 'medium', 'check'] } },
    batches: { type: 'array', items: { type: 'array', items: { type: 'number' } } },
  },
  required: ['incident', 'base_page', 'constraints', 'batches'],
}
const PAGEREV = { type: 'object', properties: { pages: { type: 'array', items: { type: 'object', properties: { n: { type: 'number' }, verdict: { type: 'string', enum: ['pass', 'redo'] }, incident_holds: { type: 'boolean' }, constraint_reads: { type: 'boolean' }, material_ok: { type: 'boolean' }, evidence: { type: 'string' }, repair: { type: 'string' } }, required: ['n', 'verdict', 'incident_holds', 'constraint_reads', 'material_ok', 'evidence', 'repair'] } }, batch_note: { type: 'string' } }, required: ['pages', 'batch_note'] }
const READ = { type: 'object', properties: { pages: { type: 'array', items: { type: 'object', properties: { n: { type: 'number' }, what_happens: { type: 'string' }, the_rule: { type: 'string' }, differs_from_page_01: { type: 'string' } }, required: ['n', 'what_happens', 'the_rule', 'differs_from_page_01'] } } }, required: ['pages'] }
const RIGHTS = { type: 'object', properties: { ok: { type: 'boolean' }, blocking: { type: 'array', items: { type: 'string' } }, notes: { type: 'array', items: { type: 'string' } } }, required: ['ok', 'blocking', 'notes'] }

let canon
if (args.stage !== 'film') {
  phase('Canon')
  canon = await agent(`You are the CANON EDITOR of "99 ways".
${COMMON}
If ${SW}/canon.json already exists, read it and return it unchanged (it is frozen). Otherwise write it:
1. THE INCIDENT, frozen, in our own words: the station agent of 99-ways-template (a 1937 railway agent at Randolph station) goes to the cupboard for the SERVICE key, is interrupted by a stranger at the ticket window asking the time, answers, is thanked, reaches the open cupboard with the brass key in plain view, and forgets why he came; the service door stays closed. List the events E0–E5 with our own dialogue lines (the time question, the answer, the thanks, and an OUR-OWN self-addressed line of forgetting; never Madden's line). Every page must keep these facts or declare in its rule exactly which it omits or reframes.
2. THE BASE PAGE (page 01, "Template"): the eight-panel objective version, built from the existing 99-ways-template page kit with the self-addressed line in our own words (re-render it as page 01 now, to the deliverable spec).
3. 99 CONSTRAINTS of our own, in families (point of view; time and order; voice and language; genre; medium and material; layout and page grammar; reduction and expansion; formal/Oulipian rule such as lipogram, palindrome, permutation, fold, crossing routes; reader and object). For each: n, short id (kebab), title, family, the rule in one sentence, the MEDIUM it will be made in (choose the medium that best shows the constraint, from the kits listed, spreading media across the 99 so no medium dominates more than ~20 pages), and a CHECK a blind reader could perform ("a reader can name the narrator", "panels read in reverse", "no letter e appears"). Include constraints that are animation-friendly for the film. Avoid repeating Madden's sequence; order by our own logic.
4. BATCHES: 9 batches of 11 page numbers (batch 1 = pages 1–11 and must include page 01 plus a spread of families and media so it is a fair sample).
Write ${SW}/canon.json and a readable ${SW}/canon.md. Return the structured canon.`, { label: 'canon', phase: 'Canon', schema: CANON })
  if (!canon) throw new Error('canon failed')
}

if (args.stage === 'batch') {
  const b = args.batch || 1
  const nums = canon.batches[b - 1]
  const cs = nums.map(n => canon.constraints.find(c => c.n === n)).filter(Boolean)
  const groups = [cs.slice(0, 4), cs.slice(4, 8), cs.slice(8)].filter(g => g.length)
  const desc = (g) => g.map(c => `${String(c.n).padStart(2, '0')} ${c.id} — ${c.title} [${c.family}; medium: ${c.medium}] rule: ${c.rule} | check: ${c.check}`).join('\n')
  phase('Pages')
  await parallel(groups.map((g, i) => () => agent(`You are PAGE MAKER ${i + 1} of batch ${b} of "99 ways".
${COMMON}
Read ${SW}/canon.md first and look at page 01 (${OUT}/01-*.jpg) as the baseline. Make these pages, one at a time, each to the deliverable spec, LOOKING at each page at full size before moving on (the incident must hold, the constraint must be visible without explanation, the medium must be real material genuinely made, the lettering legible at phone width):
${desc(g)}${(g.some(c => c.n === 1)) ? '\n(Page 01 is made by the canon editor; skip it if it exists and is to spec.)' : ''}
Return per page: what is on it, sources reused or foraged with licences, the beat frames made, and honest weaknesses.`, { label: `pages ${g.map(c => c.n).join(',')}`, phase: 'Pages' })))

  phase('Review')
  const files = `${OUT}/ pages ${nums.map(n => String(n).padStart(2, '0')).join(', ')} (files NN-*.jpg) and page 01`
  const readers = await parallel([1, 2].map(k => () => agent(`You are BLIND READER ${k}. You know nothing about how these pages were made. Look at ${files}, each at full size (view in 2x2 tiles if needed). Page 01 is the baseline telling. For every other page, say in your own words what happens, what rule or device governs the page (name it if you can), and how it differs from page 01. Do not open any other file. Edit nothing.`, { label: `reader ${k} b${b}`, phase: 'Review', schema: READ })))
  const critic = await agent(`You are the INDEPENDENT CRITIC for batch ${b} of "99 ways". Read ${SW}/canon.md (the incident and the constraints for pages ${nums.join(', ')}) and the page records in ${SW}/pages/. Look at each page at full size beside page 01, and at its beat frames in ${SRC}/beats/NN/. Two blind readers reported (compare with the intended rules; a reader missing the rule is evidence the constraint does not read):
${JSON.stringify(readers, null, 1)}
For each page decide pass or redo. Pass only if: the incident holds (or the declared omission is clear); the constraint reads from the page alone; the material is real (foraged or genuinely made, no filter costume, no stand-in clip-art); it looks good enough to print in the book; folio and title present; beat frames show a real change. Give evidence and, for redo, a concrete falsifiable repair. Edit no files.`, { label: `critic b${b}`, phase: 'Review', schema: PAGEREV })
  const rights = await agent(`You are the ATTRIBUTION REVIEWER for batch ${b} of "99 ways". For pages ${nums.join(', ')}: read ${SW}/pages/NN.json and films/credits/99-ways.json; check every foraged item used is credited with an allowed licence (re-read Commons/LoC metadata for new items; back off on 429); check no page reproduces Madden's or Queneau's text, compositions or lines. Blocking: uncredited items, NC/ND/unknown licences, copied material. Edit no files.`, { label: `rights b${b}`, phase: 'Review', schema: RIGHTS })

  const redo = (critic ? critic.pages.filter(p => p.verdict === 'redo') : [])
  let repair = null
  if (redo.length || (rights && !rights.ok)) {
    phase('Repair')
    repair = await agent(`You are the REPAIR MAKER for batch ${b} of "99 ways".
${COMMON}
Fix these pages (one repair each; keep what works; re-render to spec and update their records and beat frames):
${redo.map(p => `${String(p.n).padStart(2, '0')}: ${p.repair} (critic evidence: ${p.evidence})`).join('\n')}
Rights issues to fix: ${rights ? rights.blocking.concat(rights.notes).join(' | ') : 'none'}
Look at each repaired page at full size. Return what you changed per page and anything still weak.`, { label: `repair b${b}`, phase: 'Repair' })
  }

  phase('Commit')
  await agent(`You are the COMMITTER for batch ${b} of "99 ways". Make a contact sheet of all pages done so far: ${SW}/contact-b${b}.jpg (pages in order, 6 per row, 300 px wide each, folio under each). Write ${SW}/batch-${b}.json with the critic verdicts ${JSON.stringify(critic ? critic.pages.map(p => ({ n: p.n, verdict: p.verdict })) : [])} and whether a repair ran (${!!repair}). Then: cd /home/user/bolas && git add paeleo/scion/oulipo/films/swarm/99-ways paeleo/scion/oulipo/assets/pages/99-ways paeleo/scion/oulipo/films/credits/99-ways.json (skip missing), commit "99 ways: batch ${b}" with trailer lines "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" and "Claude-Session: https://claude.ai/code/session_012XUjiSZ2P4CmYc3BGshy5Q", push to origin ccr-f14a901a-67gkmo (retry on index.lock after 20 s; on rejection pull --no-rebase --no-edit then push; never force). Return the commit id and the contact sheet path.`, { label: `commit b${b}`, phase: 'Commit' })
  return { batch: b, pages: nums, readers, critic, rights, repaired: !!repair, contact: `${SW}/contact-b${b}.jpg` }
}

if (args.stage === 'film') {
  phase('Film')
  const film = await agent(`You are the FILM EDITOR of "99 ways".
${COMMON}
Build films/99-ways.py with kit.Film (read films/kit.py; do not edit it): a film that leafs through all 99 pages in order, as a book. For each page: a short page turn (real paper turn, not a dissolve), a hold on the whole page, then its key beat played from ${SRC}/beats/NN/ frame by frame on twos, then the next page; about 1.2–2.0 s per page (longer for page 01 and a few highlights), total under 3 minutes and under 25 MB at 960x1242 or a 1280x720 frame with the page centred on a dark table. Sound: one quiet paper-turn foley per page and a station room tone, foraged and credited, or declared silence. Render assets/films/99-ways.mp4 (and .webp poster), look at frames across the whole film before finishing. Also assemble the book PDF ${OUT}/99-ways-book.pdf from the 99 page JPGs (with a title page and contents listing each constraint). Write films/credits/99-ways.json (complete), films/notes/99-ways.txt (90–130 words). Then commit those files and push (same rules: trailer lines "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" and "Claude-Session: https://claude.ai/code/session_012XUjiSZ2P4CmYc3BGshy5Q", branch ccr-f14a901a-67gkmo, never force). Return duration, size and the commit id.`, { label: 'film', phase: 'Film' })
  return { stage: 'film', film }
}
