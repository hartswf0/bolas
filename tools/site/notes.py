"""Production notes as a guided read. A notes file is split at its ## headings; each part gets a line from a guide
character and the pictures that belong to it:
  - film stills at the moment the text describes. Every film was OCR'd at one frame a second (scratchpad ocr/run.sh);
    quoted lines and sign names in the notes are found in that text, so a row that quotes "You are Odysseus." gets the
    frame where that line is on screen, with a button that plays the film from there;
  - process sheets whose file names carry the passage or sign the text names (x14-0, s39 ...).
Long tables become cards, one per row, when their rows find pictures; otherwise they stay tables, folded when long."""
import os, re, json, html, subprocess, markdown
esc = html.escape
OCR = '/tmp/claude-0/-home-claude/6076dc87-a15e-52b2-839b-b8f3e08107ac/scratchpad/ocr'
R = '/home/claude/bolas'
MD = lambda t: markdown.markdown(t, extensions=['tables', 'fenced_code', 'sane_lists'])
STOP = set('the a an and of to in on at is it his her he she they we i you for with as by from that this was are be not no or but its their them all one'.split())

def norm(t): return re.sub(r'[^a-z0-9 ]+', ' ', t.lower().replace('’', "'")).split()
class Film:
    def __init__(s, fid, dur):
        s.id = fid; s.dur = dur; p = f'{OCR}/{fid}.json'
        raw = json.load(open(p)) if os.path.exists(p) else {}
        s.t = {int(k): set(norm(v)) for k, v in raw.items()}; s.raw = {int(k): ' '.join(norm(v)) for k, v in raw.items()}
        s.secs = sorted(s.t)
    def ban(s, quotes):
        """seconds that show two or more of the notes' quoted lines at once are a credit roll or a title card listing them"""
        qs = [' '.join(norm(q)) for q in quotes if len(' '.join(norm(q))) >= 8]
        bad = [k for k in s.secs if sum(q in s.raw[k] for q in qs) >= 2]
        for k in bad:
            for j in range(k - 2, k + 3): s.t.pop(j, None); s.raw.pop(j, None)
        s.secs = sorted(s.t)
    def find(s, phrase, after=0, need=.67):
        """first second (from `after`) whose on-screen text holds most of the phrase's words, using a 2-second window"""
        exact = ' '.join(norm(phrase))
        if len(exact) >= 10:
            for k in s.secs:
                if k >= after and exact in s.raw.get(k, '') + ' ' + s.raw.get(k + 1, ''): return k
        ws = [w for w in norm(phrase) if w not in STOP and len(w) > 2]
        if len(ws) < 2: return None
        best = (0, None)
        for k in s.secs:
            if k < after: continue
            seen = s.t[k] | s.t.get(k + 1, set())
            sc = sum(w in seen for w in ws) / len(ws)
            if sc > best[0] + 1e-9: best = (sc, k)
            if sc >= .999: break
        return best[1] if best[0] >= need else None

def still(fid, t):
    """a 640-wide frame of the film at t seconds, cached under media/notes"""
    rel = f'media/notes/{fid}/{t:04d}.jpg'; p = os.path.join(R, rel)
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', f'{R}/media/films/{fid}.mp4', '-frames:v', '1', '-vf', 'scale=640:-2', '-q:v', '4', p])
    return rel if os.path.exists(p) else None

def mmss(t): return f'{t // 60}:{t % 60:02d}'

# ------------------------------------------------------------------ the guide's lines
GUIDE = [
 (r'running order|^the experiment|^the six plates|^passages|^per shot|found-odyssey-style-lab', 'point', "Here it is in order. Click a frame and the film plays from there."),
 (r'observed and generated|^picture|^drawn', 'shrug', "This part separates what came from the archive from what was made here."),
 (r'^sound|blending and sound', 'point', "This part is about the sound. Watch with it on."),
 (r'^files$', 'peek', "The code, if you want to open it."),
 (r'review|verdict|critic|result', 'jump', "This is where the blind reviews come in."),
 (r'fix|changes|next|what fails|what carries', 'shrug', "What broke, and what was changed because of it."),
 (r'fourth-wall|devices', 'wave', "These are the tricks for talking to you directly. Like this."),
 (r'brand', 'point', "The look, written down so every episode matches."),
 (r'how each passage|pipeline|integration', 'point', "How one passage is put together, step by step."),
]
def guide_for(head, body):
    h = head.lower()
    for rx, pose, line in GUIDE:
        if re.search(rx, h): return pose, line
    s = re.sub(r'[*_`|#>\[\]]', '', body).strip().split('\n')[0]
    s = re.split(r'(?<=[.!?])\s', s)[0]
    return 'point', (s if len(s) < 130 else s[:127].rsplit(' ', 1)[0] + '…') or head

# ------------------------------------------------------------------ pictures for a piece of text
QUOTE = re.compile(r'["“]([^"”]{6,140})["”]')
SIGN = re.compile(r'\*\*(?:\d+[ab]? )?([A-Z][a-z]) (\d+[ab]?)\*\*,? ([A-Z][A-Za-z\- ]+)|\*\*(\d+[ab]?) ([A-Z][a-z]) · ([^*]+)\*\*')
def keys(text):
    out = []
    for q in QUOTE.findall(text): out.append(('q', q))
    for m in SIGN.finditer(text): out.append(('s', (m.group(3) or m.group(6) or '').strip()))
    for m in re.finditer(r'\b\d+[ab]? [A-Z][a-z] · ([A-Z][A-Za-z\- ]+?)(?= —| \(|,|\*|$)', text): out.append(('s', m.group(1).strip()))
    m = re.match(r'\s*\**(\d{1,2}[ab]?)\**\s+([A-Z][a-z]+(?: [a-z]+){0,4})', text)
    if m: out.append(('s', m.group(2)))
    return out
def pics_for(text, film, after=0):
    """film moments for a piece of text: quoted lines first (the moment the line is on screen), then sign cards (+5 s)"""
    hits = []
    if not film or not film.secs: return hits
    for kind, k in keys(text):
        t = film.find(k, after)
        if t is None and after: t = film.find(k)
        if t is None: continue
        t = min(int(film.dur) - 1, t + (5 if kind == 's' else 0))
        hits.append((t, k if kind == 'q' else None))
    if any(q for _, q in hits): hits = [h for h in hits if h[1]]     # the moment of the line beats the start of the act
    seen = set(); out = []
    for t, q in hits:
        if any(abs(t - u) < 3 for u in seen): continue
        seen.add(t); out.append((t, q))
    return out[:3]
def sheets_for(text, images, used):
    toks = set()
    for a, b in re.findall(r'\b(\d{1,2})\.(\d)\b', text): toks.add(f'x{a}-{b}')
    m = re.match(r'\s*\**(\d{1,2})\b', text)
    if m: n = m.group(1); toks |= {f'hb{n}', f's{n}', f'c{n}', f'g{n}'}
    out = [i for i in images if i['src'] not in used and any(re.search(rf'(^|[-/]){t}(k)?\.jpg$', i['src']) for t in toks)]
    for i in out: used.add(i['src'])
    return out[:3]

# ------------------------------------------------------------------ rendering
def split_sections(md):
    title = ''; intro = []; secs = []; cur = None
    for line in md.split('\n'):
        if line.startswith('# ') and not title: title = line[2:].strip(); continue
        if line.startswith('## '): cur = [line[3:].strip(), []]; secs.append(cur); continue
        (cur[1] if cur else intro).append(line)
    return title, '\n'.join(intro).strip(), [(h, '\n'.join(b).strip()) for h, b in secs]

def table_blocks(body):
    """split a section body into ('md', text) and ('table', header, rows) blocks"""
    out = []; buf = []; lines = body.split('\n'); i = 0
    while i < len(lines):
        if lines[i].startswith('|') and i + 1 < len(lines) and re.match(r'^\|[-| :]+\|$', lines[i + 1].strip()):
            if buf: out.append(('md', '\n'.join(buf))); buf = []
            head = [c.strip() for c in lines[i].strip().strip('|').split('|')]; rows = []; i += 2
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            out.append(('table', head, rows)); continue
        buf.append(lines[i]); i += 1
    if buf: out.append(('md', '\n'.join(buf)))
    return out

def plain(t): return re.sub(r'\s+', ' ', re.sub(r'[*_`]', '', t)).strip()
def first(t, n=150):
    t = re.split(r'(?<=[.!?])\s', plain(t))[0]
    return t if len(t) <= n else t[:n - 1].rsplit(' ', 1)[0] + '…'
def row_say(head, row):
    d = {h.lower(): plain(c) for h, c in zip(head, row)}
    part = d.get('part') or d.get('shot') or d.get('scene') or d.get('passage') or d.get('sign') or ''
    line = d.get('the line'); act = d.get('the gesture') or d.get('what happens') or d.get('what it does') or d.get('content') or d.get('how it plays') or ''
    if line and line not in ('(none)', '—'): return first(f'{part}: listen for {line}. ' + (first(act, 110) if act else ''), 190)
    return None
CRIT = re.compile(r'Critic: (WEAK|MET|MISSES|MEETS[^,]*),? ([^.]*)\. Repair: ([^.]*)')
def para_say(p, who):
    m = CRIT.search(plain(p))
    if m and who == 'critic': return f"I said {m.group(1).lower()}: {m.group(2)}. The fix: {m.group(3)}."
    return None
def inline(t): return MD(t).replace('<p>', '').replace('</p>', '')
def moment(fid, t, q, up, here):
    src = still(fid, t)
    if not src: return ''
    href = f'#t={t}' if here else f'{up}films/{fid}/#t={t}'
    cap = f'“{esc(q)}”' if q else 'the start of this part, just after its card'
    return f'<a class="moment" href="{href}" data-t="{t if here else ""}"><img src="{up}{src}" alt="" loading="lazy"><span><b>{mmss(t)}</b> {cap}</span></a>'
def sheet_cap(c):
    m = re.fullmatch(r'([gscx])(\d+)', c)
    if m: return {'g': 'camera fit grid', 's': 'frame strip', 'c': 'check', 'x': 'passage'}[m[1]] + f', sign {m[2]}'
    return c if len(c) > 6 else 'working sheet'
def sheet(i, up): c = sheet_cap(i["caption"]); return f'<a class="moment sheet" href="{up}{i["src"]}" data-lb><img src="{up}{i["src"]}" alt="{esc(c)}" loading="lazy"><span><b>sheet</b> {esc(c)}</span></a>'


def render(md_path, film=None, fid=None, images=(), up='', here=True, who='bola', case=None, hello=''):
    """the notes as a guided read; returns (html, number of pictures placed)"""
    text = re.sub(r'(?m)^(?![-*] |\d+\. |\s)(.+)\n(?=[-*] |\d+\. )', r'\1\n\n', open(md_path).read())   # a list needs a blank line before it
    title, intro, secs = split_sections(text)
    if film: film.ban(QUOTE.findall(text))
    used = set(); placed = 0; cursor = 0; parts = []; toc = []
    if not secs: secs = [('The record', intro)]; intro = ''
    elif re.search(r'(?m)^\|', intro) or len(intro.split()) > 90: secs.insert(0, ('What it is', intro)); intro = ''
    # the findings file is one long section of bold-led paragraphs, one per sign: give each its own card
    for n, (head, body) in enumerate(secs):
        pose, line = guide_for(head, body)
        if n == 0 and pose == 'point': pose = 'wave'
        blocks = table_blocks(body); inner = ''
        for b in blocks:
            if b[0] == 'md':
                paras = re.split(r'\n\s*\n', b[1].strip())
                signs = [p for p in paras if SIGN.match(p.strip())]
                if len(signs) >= 4:   # one card per sign paragraph
                    other = ''.join(MD(p) for p in paras if p not in signs)
                    cards = ''
                    for p in signs:
                        ms = pics_for(p, film, cursor); sh = sheets_for(p, images, used)
                        if ms: cursor = ms[0][0]
                        pics = ''.join(moment(fid, t, q, up, here) for t, q in ms[:1]) + ''.join(sheet(i, up) for i in sh[:1]); placed += bool(pics)
                        ps = para_say(p, who); cards += f'<div class="beat"{f" data-say={chr(34)}{esc(ps)}{chr(34)}" if ps else ""}>{f"<div class=pics>{pics}</div>" if pics else ""}<div class="btxt">{MD(p)}</div></div>'
                    inner += other + f'<div class="beats">{cards}</div>'
                else:
                    inner += MD(b[1])
                continue
            _, head_r, rows = b
            rowpics = []; again = {}
            for r in rows:
                t = ' '.join(r); ms = pics_for(t, film, cursor); sh = sheets_for(t, images, used)
                if ms and ms[0][1] is None:      # the same sign card again: the next passage under it starts about 15 s later
                    n0 = again.get(ms[0][0], 0); again[ms[0][0]] = n0 + 1
                    if n0: ms = [(min(int(film.dur) - 1, ms[0][0] + 15 * n0), None)] + ms[1:]
                if ms: cursor = max(cursor, ms[0][0])
                rowpics.append((ms, sh))
            if sum(bool(m or s) for m, s in rowpics) >= max(1, len(rows) // 3):
                cards = ''
                for r, (ms, sh) in zip(rows, rowpics):
                    pics = ''.join(moment(fid, t, q, up, here) for t, q in ms[:2]) + ''.join(sheet(i, up) for i in sh[:2]); placed += bool(pics)
                    fields = ''.join(f'<div><dt>{esc(h)}</dt><dd>{inline(c)}</dd></div>' for h, c in zip(head_r, r) if c and c not in ('(none)', '—'))
                    rs = row_say(head_r, r); cards += f'<div class="beat"{f" data-say={chr(34)}{esc(rs)}{chr(34)}" if rs else ""}>{f"<div class=pics>{pics}</div>" if pics else ""}<dl class="btxt">{fields}</dl></div>'
                inner += f'<div class="beats">{cards}</div>'
                if not any(m for m, _ in rowpics): line = "Each card pairs a passage with the contact sheet it was reviewed from. Click a sheet to see it full size."
            else:
                tbl = MD('| ' + ' | '.join(head_r) + ' |\n|' + '---|' * len(head_r) + '\n' + '\n'.join('| ' + ' | '.join(r) + ' |' for r in rows))
                inner += f'<details class="bigtable"><summary>Show the table ({len(rows)} rows)</summary>{tbl}</details>' if len(rows) > 10 else tbl
        sid = f'n{n + 1}'; toc.append(f'<a href="#{sid}">{esc(head)}</a>')
        parts.append(f'<section class="nsec" id="{sid}" data-say="{esc(line)}" data-pose="{pose}"><h2>{esc(head)}</h2><p class="gline">{esc(line)}</p>{inner}</section>')
    rest = [i for i in images if i['src'] not in used][:8]
    if rest:
        parts.append(f'<section class="nsec" id="nsheets" data-say="These are the sheets that were checked while this was made." data-pose="point"><h2>Sheets from the making</h2>'
                     f'<div class="sheets">{"".join(sheet(i, up) for i in rest)}</div>{f"<p class=more><a href={up}process/{case}/>The full case study</a></p>" if case else ""}</section>')
        toc.append('<a href="#nsheets">Sheets</a>')
    first = esc((hello + ' ' if hello else '') + 'I\'ll walk you through how this was made. Click any frame to play the film from that moment.')
    out = f"""<section class="notes" style="--cam:clamp(100px,11vw,150px)"><aside class="guide"><div class="gbox"><p class="gsay">{first}</p><div class="stand"><span class="cam gs" data-who="{who}" data-c="{who}-point" data-say="[]"></span></div></div></aside>
<div class="ncontent"><p class="eyebrow nsec nintro" data-say="{first}" data-pose="wave">Production notes{' · ' + esc(title) if title else ''}</p>{MD(intro) if intro else ''}<nav class="ntoc">{''.join(toc)}</nav>{''.join(parts)}</div></section>"""
    return out, placed
