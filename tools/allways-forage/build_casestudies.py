"""Build the ALLWAYS Sonnet run: an index, an atlas and one case-study page per film.

  python3 tools/allways-forage/build_casestudies.py [--lab /home/user/cineosis-lab]

Reads  allways-sonnet/<NNN-slug>/ (edl.json, ledgers, mp4s, NOTES.md), BRIEF.md,
       assignments.json, status.json, the SCION prompts and the critic review.
Writes <film>/index.html, <film>/poster.jpg, <film>/frames/*.jpg, <film>/cands/*.jpg,
       allways-sonnet/index.html, atlas.html.
Frames and candidate strips are cut from the rendered films and from the local archive cache,
so the page shows the images that were actually looked at. Standard library + PIL + ffmpeg.
"""
import argparse, glob, hashlib, html, json, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
import md

ROOT = Path(__file__).resolve().parents[2]
ALW = ROOT / 'paeleo' / 'allways'
ED = ROOT / 'allways-sonnet'
HERE = Path(__file__).resolve().parent
esc = html.escape
CRITIC_SRC = ED / 'CRITIC-ROUND-1.md'

ALT_LABEL = {
    'alt': 'Alternate cut', 'control': 'Control cut: same sources and order, no registration', 'wide': 'Comparison cut: opens wide',
    'context': 'Context reel: each source clip with its own timing and sound', 'noguides': 'Same film with the fitted guides removed',
    'alt-sourcesound': 'Same picture with the original sound back on', 'alt-silent': 'Same film with all sound removed'}
REPAIRS = {
    '055-words': 'Whiteboard shot removed. The statue now cuts straight back to the opening map.',
    '058-laughs': 'Grey run-out frame and the closing shot of the boys removed (it singled out one boy amid group laughter); the film ends on black. The cut from the man in the car to the stage performer, and the man covering his face, are still open for a human reviewer.',
    '059-ball': 'Jet-intake shot now ends before the source film’s own page-turn effect; end-card text shortened so it is no longer clipped.',
    '061-matter': 'The grain-growth animation is captioned “animated diagram, not filmed metal”.',
    '057-moments': 'Open. The critic advises cutting the opening skate shots, which show no change.',
    '062-colors': 'Open. The critic advises one blue middle chapter and more time for red.',
    '063-breath': 'Open. Needs a breath seen without a face; none exists in the stored footage, so v2 waits for live archive search.',
    '064-parabolas': 'Open. The critic advises larger labels and a hold of at least three seconds on each fitted model.'}
MODEL_NOTE = {  # one-line reading of what each film is, for the cards
    '055-words': 'One verb, never shown, changes sense from cut to cut.',
    '056-symmetry': 'Three pairs of unrelated films side by side, lining up and then parting.',
    '057-moments': 'Small events left to finish, with one long hold.',
    '058-laughs': 'A chain of separate situations built from laughter; the sound is the weak part.',
    '059-ball': 'One rim held at the centre of the screen across thirteen films.',
    '060-losers': 'A position explained by the room it is in; one staged 1953 film.',
    '061-matter': 'What materials keep after pressure, wet, heat and the cut.',
    '062-colors': 'Three colour chapters joined by shots that hold two colours.',
    '063-breath': 'Wind, steam and breath, kept apart. Failed the first critic round.',
    '064-parabolas': 'Curves from different causes, with fitted guides drawn as models.',
    '065-five': 'Five practices from five sources, each given an uninterrupted action.'}
INPUTS = [
    ('[WORK]', 'The film named in the assignment, realising this operator’s hard proof (§4) with found archive footage.'),
    ('[DIRECTION_AND_REFERENCES]', 'The operator’s own §1 theorem and §4 proof. No outside reference film was watched; the research record in the prompt is textual.'),
    ('[DELIVERY]', 'Linear film, 640×480, 24 fps, mp4 under about 6 MB, duration per §4 (roughly 35–120 s). Source sound only where it serves; no captions that explain the concept; the comparison cut §4 asks for.'),
    ('[RESOURCES]', 'tools/allways-forage (index.json, forage.py, render.py), ffmpeg, OpenCV, numpy, PIL, and a local clone of hartswf0/cineosis-lab. The archive’s own site could not be reached from the build environment.'),
    ('[CORPUS_AND_RIGHTS]', 'Only shots from movingimagearchive.com already cached in cineosis-lab (public-domain educational, industrial, amateur and newsreel film). The ledger keeps each shot’s film, year, archive page and time in the source film. No new rights are asserted.'),
    ('[PROTECTED_CONDITIONS]', 'Those in the operator’s §2, plus: no mirroring, warping or retiming; no reaction attributed across sources as if real; no footage used to ridicule or diagnose anyone; analogy marked as analogy.')]


def sh(*a, **k):
    return subprocess.run(a, capture_output=True, **k)


def tc(t):
    return f'{int(t // 60)}:{t % 60:04.1f}'


def tone(v):
    v = v.lower()
    return 'fail' if 'fail' in v else 'pass' if 'pass' in v else 'mid' if 'inconclusive' in v else 'open'


def frame(video, t, out, w=320):
    if not os.path.exists(out):
        sh('ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', str(video), '-frames:v', '1', '-vf', f'scale={w}:-2', '-q:v', '5', str(out))


def strip(e, out, n=4, w=128, h=96):
    if os.path.exists(out): return
    p = e['media'].get('clip') or e['media'].get('loop')
    ims = []
    if p:
        try: d = float(sh('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p).stdout.decode().strip() or 0)
        except Exception: d = 0
        for i in range(n):
            r = sh('ffmpeg', '-v', 'error', '-ss', f'{d * (i + .5) / n:.2f}', '-i', p, '-frames:v', '1', '-vf', f'scale={w}:{h}', '-f', 'image2pipe', '-vcodec', 'png', '-')
            try:
                import io; ims.append(Image.open(io.BytesIO(r.stdout)).convert('RGB'))
            except Exception: pass
    elif 'still' in e['media']:
        ims = [Image.open(e['media']['still']).convert('RGB').resize((w * 2, h * 2))]
    if not ims: return
    W = sum(i.width for i in ims); im = Image.new('RGB', (W, ims[0].height)); x = 0
    for i in ims: im.paste(i, (x, 0)); x += i.width
    im.save(out, quality=72)


def read(p, default=''):
    return Path(p).read_text() if Path(p).exists() else default


def copy_block(bid, label, text, open_=False, note=''):
    safe = text.replace('</script', '<\\/script')
    return (f'<details class="prompt"{" open" if open_ else ""}><summary><span>{esc(label)}</span><small>{len(text):,} characters</small></summary>'
            f'{f"<p class=note>{note}</p>" if note else ""}'
            f'<div class="pbar"><button type="button" class="btn" data-copy="{bid}">Copy</button></div>'
            f'<script type="text/plain" id="{bid}">{safe}</script><pre>{esc(text)}</pre></details>')


JS = r'''<script>
function copyText(t,b){var o=b.textContent;function ok(){b.textContent='Copied';setTimeout(function(){b.textContent=o},1400)}
function fb(){var a=document.createElement('textarea');a.value=t;a.style.position='fixed';a.style.opacity=0;document.body.appendChild(a);a.select();try{document.execCommand('copy');ok()}catch(e){b.textContent='Select text and copy'}document.body.removeChild(a)}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(ok,fb)}else{fb()}}
document.addEventListener('click',function(e){var b=e.target.closest('[data-copy]');if(!b)return;var ids=b.getAttribute('data-copy').split(',');
copyText(ids.map(function(i){return document.getElementById(i).textContent}).join('\n\n----\n\n'),b)});
</script>'''


def head(title, desc, depth, extra=''):
    up = '../' * depth                      # depth 1: allways-sonnet/ ; depth 2: allways-sonnet/<film>/
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="theme-color" content="#f4f1e9">'
            f'<link rel="icon" href="{up}favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{up}tools/paeleo/fonts/local.css">'
            f'<link rel="stylesheet" href="{up}paeleo/allways/allways.css"><link rel="stylesheet" href="{up}allways-sonnet/case.css">{extra}</head>')


def crumbs(depth, tail):
    up = '../' * depth
    return (f'<header class="site-header"><div class="wrap sitebar"><div class="parents"><a href="{up}">CRASH LAB</a><span>/</span><a href="{up}paeleo/">PAELEO</a><span>/</span>'
            f'<a href="{up}paeleo/allways/">ALLWAYS</a><span>/</span><a href="{up}paeleo/allways/#runs">RUNS</a>{tail}</div></div></header>')


def ghfix(page, folder):
    """Rewrite relative .md links to GitHub blob links (GitHub Pages would serve raw text)."""
    import posixpath
    def f(m):
        u = m.group(1)
        if re.match(r'^(https?:|#)', u): return m.group(0)
        return 'href="https://github.com/hartswf0/bolas/blob/main/' + posixpath.normpath(posixpath.join(folder, u)) + '"'
    return re.sub(r'href="([^"#]+\.md)"', f, page)


def main():
    global ATLAS_CRUMB, IDX_CRUMB
    ATLAS_CRUMB = crumbs(1, '<span>/</span><a href="./">SONNET</a><span>/ ATLAS</span>')
    IDX_CRUMB = crumbs(1, '<span>/ SONNET</span>')
    ap = argparse.ArgumentParser(); ap.add_argument('--lab', default='/home/user/cineosis-lab'); a = ap.parse_args()
    IDX = json.load(open(HERE / 'index.json')); BYID = {e['id']: e for e in IDX}
    PFX = {}
    for e in IDX: PFX.setdefault(e['id'][:8], []).append(e['id'])
    SCION = {e['id']: e for e in json.load(open(ALW / 'scion' / 'scion-allways.json'))}
    BRIEF = read(ED / 'BRIEF.md'); ASG = json.load(open(ED / 'assignments.json')); STATUS = json.load(open(ED / 'status.json'))
    crit = read(CRITIC_SRC) or ''
    CRIT = {}
    for m in re.finditer(r'^## (\d{3}) .*?(?=^## |\Z)', crit, re.S | re.M): CRIT[m.group(1)] = m.group(0)
    films = sorted(p.name for p in ED.iterdir() if p.is_dir() and re.match(r'\d{3}-', p.name))
    cards = []
    for fi, fid in enumerate(films):
        d = ED / fid; num = int(fid[:3]); op = SCION[num]
        led = json.load(open(d / f'{fid}.ledger.json')); edl = json.load(open(d / 'edl.json'))
        main_mp4 = d / f'{fid}.mp4'; size_kb = main_mp4.stat().st_size // 1000
        name = fid[4:].replace('-', ' ').title(); op_short = op['title'].split(' — ')[0]
        (d / 'frames').mkdir(exist_ok=True); (d / 'cands').mkdir(exist_ok=True)
        # poster
        pf = d / 'poster.jpg'
        if not pf.exists(): frame(main_mp4, led['duration'] * .3, pf, 640)
        # per-event frames
        for ev in led['events']: frame(main_mp4, (ev['t_in'] + ev['t_out']) / 2, d / 'frames' / f'e{ev["n"]:02d}.jpg')
        used = {l['src'] for ev in led['events'] for l in ev['layers']}
        # candidates mentioned in the notes
        notes = read(d / 'NOTES.md')
        cand = {}
        for ln in notes.split('\n'):
            for tok in re.findall(r'(?<![0-9a-f])([0-9a-f]{8})(?![0-9a-f])', ln):
                if tok in PFX and len(PFX[tok]) == 1 and tok not in cand:
                    cand[tok] = re.sub(r'\s+', ' ', re.sub(r'[*_`|]', '', ln)).strip(' -•')[:300]
        for u in used: cand.setdefault(u[:8], '')
        order = sorted(cand, key=lambda t: (not any(u.startswith(t) for u in used), t))[:30]
        with ThreadPoolExecutor(6) as ex: list(ex.map(lambda t: strip(BYID[PFX[t][0]], d / 'cands' / f'{t}.jpg'), order))
        cand_html = ''
        for t in order:
            e = BYID[PFX[t][0]]; u = e['id'] in used
            if not (d / 'cands' / f'{t}.jpg').exists(): continue
            cand_html += (f'<figure class="cand{" used" if u else ""}"><img loading="lazy" src="cands/{t}.jpg" alt="Frames across {esc(e["title"])}"><figcaption>'
                          f'<b>{esc(e["title"])}</b> <span>{e["year"] or "undated"} · {"in the cut" if u else "considered"} · <code>{t}</code></span>'
                          f'{f"<p>{esc(cand[t])}</p>" if cand[t] else ""}</figcaption></figure>')
        # curated working sheets
        sheets_html = ''
        cp = d / 'forage' / 'captions.json'
        if cp.exists():
            for c in json.load(open(cp)):
                sheets_html += f'<figure class="wsheet"><a href="forage/{c["file"]}"><img loading="lazy" src="forage/{c["file"]}" alt="{esc(c["caption"][:110])}"></a><figcaption>{esc(c["caption"])}</figcaption></figure>'
        # shot table
        rows = ''
        for ev in led['events']:
            ls = ev['layers']; lab = re.sub(r'\s+', ' ', ev['label'] or '')
            srcs = ''
            for l in ls:
                ft = f' · source film at {tc(l["film_time_in"])}' if l.get('film_time_in') is not None else ''
                tr = l['transform']
                reg = f' · registered, scale ×{tr["scale"]}' if tr['fit'] == 'register' else f' · {tr["fit"]}'
                snd = ' · source sound' + (f' {l["gain_db"]:+g} dB' if l.get('gain_db') else '') if l['audio'] else ' · muted'
                if l['media'] == 'still': snd = ' · held still'
                srcs += (f'<div class="src"><a href="{esc(l["page"] or "#")}">{esc(l["film"] or "?")}</a> <span>({l["year"] or "undated"}){ft}{reg}{snd}</span></div>')
            if not ls: srcs = '<div class="src"><span>' + esc(' / '.join((ev.get('card') or ['black'])) ) + '</span></div>'
            rows += (f'<tr><td class="th"><img loading="lazy" src="frames/e{ev["n"]:02d}.jpg" alt="Frame at {tc((ev["t_in"] + ev["t_out"]) / 2)}"></td>'
                     f'<td class="tt">{tc(ev["t_in"])}<br><small>{ev["t_out"] - ev["t_in"]:.1f} s</small></td><td>{srcs}</td><td class="why">{esc(lab)}</td></tr>')
        # alternates
        alts = ''
        for p in sorted(d.glob(f'{fid}-*.mp4')):
            suf = p.stem[len(fid) + 1:]; lbl = ALT_LABEL.get(suf, suf.replace('-', ' ').capitalize())
            alts += f'<figure class="alt"><video controls preload="none" playsinline src="{p.name}"></video><figcaption>{esc(lbl)}<br><small>{p.stat().st_size // 1000} KB</small></figcaption></figure>'
        # critic
        verdict = STATUS.get(fid, 'critic review pending')
        crit_html = md.render(CRIT[f'{num:03d}'], h_offset=1, slug=f'c{num}-') if f'{num:03d}' in CRIT else '<p>No independent critic round has been run on this film yet.</p>'
        repair = REPAIRS.get(fid, '')
        # prompts
        scion_md = read(next(iter((ALW / 'scion' / 'prompts').glob(f'scion-{num:03d}-*.md'))))
        asg = ASG[fid]
        asg_txt = asg['text'] if not asg['agent'] else f'{asg["text"]}\n\n(Read the shared brief before starting.)'
        inputs_txt = '\n'.join(f'- `{k}`: {v}' for k, v in INPUTS)
        prompts = (
            f'<div class="pbar big"><button type="button" class="btn solid" data-copy="p-asg,p-in,p-scion,p-brief">Copy the full run prompt</button>'
            f'<span class="note">Assignment, SCION inputs, operator prompt and shared brief, joined. Paste into a capable agent with this repository and a local cineosis-lab clone.</span></div>'
            + copy_block('p-asg', 'The assignment given for this film', asg_txt, True,
                         'Sent verbatim to the agent that made this film.' if asg['agent'] else 'No agent was given this film; this records how it was made.')
            + copy_block('p-in', 'How the SCION inputs were answered', 'SCION inputs as answered for this run (reconstructed from the brief and assignment):\n' + inputs_txt, False,
                         'The operator prompt asks for six inputs. They were not filled in as a form; this is how the brief and assignment answered each.')
            + copy_block('p-scion', f'The operator: SCION {num:03d} in full', scion_md, False, 'Verbatim from <a href="../../paeleo/allways/scion/prompts/' + next(iter((ALW / 'scion' / 'prompts').glob(f'scion-{num:03d}-*.md'))).name + '">scion/prompts</a>.')
            + copy_block('p-brief', 'The shared brief given to every film-maker', BRIEF, False, 'The same brief for all eleven films. Also in <a href="../BRIEF.md">BRIEF.md</a>.')
            + copy_block('p-edl', 'The edit list (edl.json)', read(d / 'edl.json'), False,
                         f'Render with <code>python3 tools/allways-forage/render.py allways-sonnet/{fid}/edl.json</code>. Each layer names a shot, an in-point and a transform.'))
        # process timeline
        nc = len([t for t in cand]); nev = len([e for e in led['events'] if e['layers']])
        steps = [
            ('Forage', f'{nc} shots from the notes appear below; {len(used)} reached the cut.' if nc else 'See the forage log.'),
            ('Choose', f'{len(used)} source shots from {len({BYID[u]["title"] for u in used if u in BYID})} films, chosen from frames and sound levels.'),
            ('Cut', f'{nev} shots over {led["duration"]:.0f} s, edit list {led["edl_sha"]}.'),
            ('Render', f'{led["size"][0]}×{led["size"][1]} at {led["fps"]} fps, {size_kb:,} KB, with a ledger of every source and transform.'),
            ('Critic', verdict.split(' · ')[0].replace('critic: ', '').capitalize() if 'critic:' in verdict else 'Not yet reviewed'),
            ('Repair', 'Applied' if fid in ('055-words', '058-laughs', '059-ball', '061-matter') else 'Open' if fid in REPAIRS else 'Not yet reviewed')]
        steps_html = ''.join(f'<li><b>{a_}</b><span>{esc(b_)}</span></li>' for a_, b_ in steps)
        # nav
        prv = films[(fi - 1) % len(films)]; nxt = films[(fi + 1) % len(films)]
        notes_html = md.render(notes, f'allways-sonnet/{fid}', h_offset=2, slug='n-')
        notes_html = re.sub(r'<h3 id="n-[^"]*">[^<]*</h3>\s*', '', notes_html, count=1)  # drop the file's own title
        alt_block = f'<section id="alternates"><h2>Comparison and alternate cuts</h2><div class="alts">{alts}</div></section>' if alts else ''
        film_crumb = crumbs(2, '<span>/</span><a href="../">SONNET</a><span>/ %03d</span>' % num)
        page = head(f'{name} · ALLWAYS Sonnet case study', f'How the {name} film was made from archive footage: forage, frames, cut, critic round and the prompts to repeat it.', 2) + \
            f'<body class="case"><a class="skip" href="#main">Skip to content</a>{film_crumb}' + f'''
<main id="main" class="wrap">
<section class="caseTop"><div><span class="label">SCION {num:03d} · {esc(op_short)} · case study</span><h1>{esc(name)}</h1>
<p class="lede">{esc(MODEL_NOTE[fid])}</p>
<p class="theorem"><span class="label">The operator’s theorem</span>{esc(re.search(r"## 1 · Creative theorem to prove\n\n(.+?)\n", scion_md).group(1))}</p>
<p class="vline v-{tone(verdict)}"><span class="dot"></span>{esc(verdict)}</p>
<nav class="jump" aria-label="On this page"><a href="#process">Process</a><a href="#frames">Cut, shot by shot</a><a href="#forage">Forage</a><a href="#critic">Critic</a><a href="#prompts">Prompts</a><a href="#notes">Working notes</a></nav></div>
<div class="player"><video controls preload="metadata" playsinline poster="poster.jpg" src="{fid}.mp4"></video>
<p class="cap">{led["duration"]:.0f} s · {size_kb:,} KB · found footage from movingimagearchive.com · <a href="{fid}.ledger.json">source ledger</a></p></div></section>
<section id="process"><h2>How it was made</h2><ol class="steps">{steps_html}</ol></section>
<section id="frames"><h2>The cut, shot by shot</h2><p class="lead">Each frame below was taken from the middle of the shot in the finished film. The last column is the reason recorded in the edit list for putting it there. Times are in this film; “source film at” is where the shot sits in the original.</p>
<div class="tablewrap"><table class="cut"><thead><tr><th>Frame</th><th>In</th><th>Source</th><th>Why it is here</th></tr></thead><tbody>{rows}</tbody></table></div></section>
{alt_block}
<section id="forage"><h2>What was found, and what was not</h2>{f'<h3 class="sub">The sheets the film-maker worked from</h3><div class="wsheets">{sheets_html}</div><h3 class="sub">Shots named in the notes</h3>' if sheets_html else ''}<p class="lead">Contact strips of the shots the notes name, four frames across each clip. Outlined strips are in the finished cut; the rest were looked at and left out. The sentence under each is the note written when it was considered.</p>
<div class="cands">{cand_html or "<p>No candidate ids were recorded in the notes for this film.</p>"}</div>
<p class="note">The whole local archive of 405 sound clips is in the <a href="../atlas.html">atlas</a>.</p></section>
<section id="critic"><h2>Critic round</h2>
<p class="note">Written by a separate agent that read frame sheets, cut lengths and sound levels. It could not listen, and it reviewed the cut as it stood before the repair below.</p>
<div class="md critic">{crit_html}</div>
{f'<div class="repair"><span class="label">Repair after this round</span><p>{esc(repair)}</p></div>' if repair else ''}</section>
<section id="prompts"><h2>The prompts, to copy</h2><p class="lead">Everything needed to run this film again. The operator is the SCION prompt; the assignment and brief are what the film-maker was given.</p>{prompts}</section>
<section id="notes"><h2>Working notes as written</h2><p class="note">The film-maker’s own NOTES.md, unedited. Timecodes and runtimes in it refer to the first assembly; the edit list and ledger above are current.</p><div class="md">{notes_html}</div></section>
<nav class="pn"><a href="../{prv}/">← {esc(prv[4:].replace("-", " ").title())}</a><a href="../">All films</a><a href="../{nxt}/">{esc(nxt[4:].replace("-", " ").title())} →</a></nav>
</main><footer><div class="wrap"><div class="footer-row"><p>ALLWAYS Sonnet run · proofs in progress, not released works. Source footage © its holders; shots link back to movingimagearchive.com.</p></div></div></footer>{JS}</body></html>'''
        (d / 'index.html').write_text(ghfix(page, f'allways-sonnet/{fid}'))
        cards.append(dict(id=fid, num=num, name=name, op=op_short, dur=round(led['duration']), verdict=verdict, note=MODEL_NOTE[fid], kb=size_kb, srcs=len(used)))
        print(fid, len(order), 'candidates', len(led['events']), 'events')
    # ---- run index
    grid = ''.join(
        f'<a class="fcard" href="{c["id"]}/"><img loading="lazy" src="{c["id"]}/poster.jpg" alt="Still from {esc(c["name"])}" width="640" height="480"><div><span class="label">SCION {c["num"]:03d} · {c["dur"]} s</span>'
        f'<h3>{esc(c["name"])}</h3><p>{esc(c["note"])}</p><span class="vline v-{tone(c["verdict"])}"><span class="dot"></span>{esc(c["verdict"])}</span></div></a>' for c in cards)
    stats = {'shots': len(IDX), 'clips': sum('clip' in e['media'] for e in IDX), 'loops': sum('loop' in e['media'] for e in IDX), 'stills': sum('still' in e['media'] for e in IDX)}
    total_src = sum(c['srcs'] for c in cards)
    idx_page = head('ALLWAYS Sonnet run', 'Eleven conceptual microfilms cut by hand from archive footage, each with its forage, frames, critic round and prompts.', 1) + \
        f'<body class="case"><a class="skip" href="#main">Skip to content</a>{IDX_CRUMB}' + f'''
<main id="main" class="wrap">
<section class="caseTop one"><div><span class="label">ALLWAYS run · SCION 055–065 · October 2026</span><h1>Sonnet</h1>
<p class="lede">Eleven films, one for each conceptual-microfilm operator, foraged and cut by hand from public-domain footage on movingimagearchive.com. Every film comes with the images that were looked at, the reason for each shot, an independent critic round where one has run, and the prompts to make it again.</p>
<p class="note">Other runs at the same operators are listed in the <a href="../paeleo/allways/#runs">Runs section of ALLWAYS</a>.</p></div></section>
<section><h2>The films</h2><div class="fgrid">{grid}</div></section>
<section id="method"><h2>How the run was made</h2>
<ol class="steps wide"><li><b>Index</b><span>{stats["shots"]:,} archive shots held in a local cache: {stats["clips"]} clips with sound, {stats["loops"]} silent loops, {stats["stills"]:,} stills, each with the archive queries that returned it, CLIP subjects, colour and sound features.</span></li>
<li><b>Forage</b><span>Text search first, then shape, colour and sound scans, then eyes: contact sheets of every clip, read frame by frame. The archive’s own search was unreachable, so nothing was searched live.</span></li>
<li><b>Choose</b><span>Each shot picked for what its frames show, not for the words that found it. Substitutions for the prompts’ imagined scenes are listed in each film’s notes.</span></li>
<li><b>Cut</b><span>An edit list per film. Sources are only moved and uniformly scaled; nothing is mirrored, warped or retimed. {total_src} source shots in all.</span></li>
<li><b>Render</b><span>One renderer produces the film and a ledger: source film, year, archive page, time in the source and transform for every shot.</span></li>
<li><b>Critic</b><span>A separate agent reviewed eight of the films from frame sheets and sound levels. It could not listen. Three films have not been reviewed yet.</span></li>
<li><b>Repair</b><span>Four films repaired from the first round; four have open repairs. A human screening has not happened.</span></li></ol></section>
<section id="limits"><h2>What this run cannot claim</h2><ul class="plain">
<li>Nobody has listened to or watched these at speed. Picture and sound were judged from still frames, cut lengths and sound-level plots.</li>
<li>The critic is an AI agent. Its verdicts are readings, not audience results.</li>
<li>The prompts imagine newly filmed material. These are found-footage substitutes, and each film says what it had to swap.</li>
<li>Source footage keeps its holders’ rights; this is a research proof, not a release.</li></ul></section>
<section id="files"><h2>Everything else</h2><div class="links">
<a href="atlas.html">Atlas of all 405 local sound clips</a><a href="BRIEF.md">The shared brief</a><a href="CRITIC-ROUND-1.md">Critic round 1, with the repair log</a><a href="assignments.json">Assignments as sent</a>
<a href="../tools/allways-forage/README.md">The forage toolkit</a></div>
<div class="pbar big" style="margin-top:22px"><button type="button" class="btn solid" data-copy="p-brief">Copy the shared brief</button></div><script type="text/plain" id="p-brief">{BRIEF.replace("</script", "<\\/script")}</script></section>
</main><footer><div class="wrap"><div class="footer-row"><p>ALLWAYS Sonnet run · a cinema practice by Watson Hartsoe within PAELEO.</p></div></div></footer>{JS}</body></html>'''
    (ED / 'index.html').write_text(ghfix(idx_page, 'allways-sonnet'))
    # ---- atlas
    at = json.load(open(ED / 'atlas' / 'atlas.json'))
    rows = json.dumps([[r['n'], s['file'], r['id'][:8], r['title'], r['year']] for s in at for r in s['rows']])
    secs = ''.join(f'<section class="sheet" id="s{s["start"]}"><h3>Rows {s["start"]}–{s["start"] + len(s["rows"]) - 1}</h3><img loading="lazy" src="atlas/{s["file"]}" alt="Contact sheet of clips {s["start"]} to {s["start"] + len(s["rows"]) - 1}, eight frames across each"></section>' for s in at)
    (ED / 'atlas.html').write_text(head('Atlas of local archive clips · ALLWAYS Sonnet', 'Contact sheets of the 405 sound clips every film in the edition was foraged from.', 1) +
        f'<body class="case"><a class="skip" href="#main">Skip to content</a>{ATLAS_CRUMB}' + f'''
<main id="main" class="wrap"><section class="caseTop one"><div><span class="label">The forage floor</span><h1>Atlas</h1><p class="lede">All 405 local sound clips, eight frames across each, sorted by film title. Each row shows its number, the first eight letters of its id and its film. Most films in this edition were picked from these sheets by eye.</p>
<label class="find" for="q">Find a film</label><input id="q" type="search" placeholder="title, year or id" autocomplete="off"><ul id="hits" class="hits"></ul></div></section>{secs}</main>
<script>var R={rows};var q=document.getElementById('q'),h=document.getElementById('hits');q.addEventListener('input',function(){{var s=q.value.trim().toLowerCase();h.textContent='';if(s.length<2)return;R.filter(function(r){{return (r[3]+' '+r[4]+' '+r[2]).toLowerCase().indexOf(s)>=0}}).slice(0,40).forEach(function(r){{var li=document.createElement('li'),a=document.createElement('a');a.href='#s'+(Math.floor(r[0]/24)*24);a.textContent='row '+r[0]+' · '+r[3]+' ('+(r[4]||'undated')+') · '+r[2];li.appendChild(a);h.appendChild(li)}})}});</script></body></html>''')
    print('run index and atlas written')


if __name__ == '__main__':
    main()
