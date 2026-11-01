"""Minimal Markdown to HTML for the ALLWAYS notes (standard library only).

Supports ATX headings, paragraphs, nested bullet and numbered lists, pipe tables,
fenced code, blockquotes, rules, `code`, **bold**, *italic* and [links](url).
Relative links to .md/.json files are rewritten to GitHub blob links for `repo_dir`.
"""
import html, re

GH = 'https://github.com/hartswf0/bolas/blob/main/'


def inline(t, repo_dir=''):
    codes = []
    t = re.sub(r'`([^`]+)`', lambda m: codes.append(m.group(1)) or f'\x00{len(codes) - 1}\x00', t)
    t = html.escape(t, quote=False)

    def link(m):
        label, url = m.group(1), html.unescape(m.group(2))
        if not re.match(r'^(https?:|#|mailto:)', url):
            parts = (repo_dir.rstrip('/') + '/' + url).split('/')
            out = []
            for p in parts:
                if p == '..' and out: out.pop()
                elif p not in ('.', ''): out.append(p)
            url = GH + '/'.join(out)
        return f'<a href="{html.escape(url)}">{label}</a>'
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', link, t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\*\w])\*([^*\n]+?)\*(?![\*\w])', r'<em>\1</em>', t)
    return re.sub(r'\x00(\d+)\x00', lambda m: '<code>' + html.escape(codes[int(m.group(1))], quote=False) + '</code>', t)


LI = re.compile(r'^(\s*)([-*]|\d+[.)])\s+(.*)$')


def render(md, repo_dir='', h_offset=0, slug=''):
    L = md.replace('\t', '    ').split('\n')
    out, i = [], 0

    def para(buf):
        if buf: out.append('<p>' + inline(' '.join(x.strip() for x in buf), repo_dir) + '</p>')
    buf = []
    while i < len(L):
        ln = L[i]
        if ln.strip().startswith('```'):
            para(buf); buf = []
            j = i + 1; code = []
            while j < len(L) and not L[j].strip().startswith('```'): code.append(L[j]); j += 1
            out.append('<pre><code>' + html.escape('\n'.join(code), quote=False) + '</code></pre>'); i = j + 1; continue
        m = re.match(r'^(#{1,6})\s+(.*)$', ln)
        if m:
            para(buf); buf = []
            n = min(6, len(m.group(1)) + h_offset); txt = m.group(2)
            hid = slug + re.sub(r'[^a-z0-9]+', '-', re.sub(r'<[^>]+>', '', inline(txt)).lower()).strip('-')
            out.append(f'<h{n} id="{hid}">{inline(txt, repo_dir)}</h{n}>'); i += 1; continue
        if re.match(r'^\s*(---+|\*\*\*+)\s*$', ln):
            para(buf); buf = []; out.append('<hr>'); i += 1; continue
        if ln.lstrip().startswith('|') and i + 1 < len(L) and re.match(r'^\s*\|?[\s:\-|]+\|?\s*$', L[i + 1]) and '-' in L[i + 1]:
            para(buf); buf = []
            def cells(s): return [c.strip() for c in s.strip().strip('|').split('|')]
            head = cells(ln); i += 2; rows = []
            while i < len(L) and L[i].lstrip().startswith('|'): rows.append(cells(L[i])); i += 1
            t = '<div class="tablewrap"><table><thead><tr>' + ''.join(f'<th>{inline(c, repo_dir)}</th>' for c in head) + '</tr></thead><tbody>'
            for r in rows: t += '<tr>' + ''.join(f'<td>{inline(c, repo_dir)}</td>' for c in r) + '</tr>'
            out.append(t + '</tbody></table></div>'); continue
        if ln.lstrip().startswith('>'):
            para(buf); buf = []; q = []
            while i < len(L) and L[i].lstrip().startswith('>'): q.append(L[i].lstrip()[1:].strip()); i += 1
            out.append('<blockquote>' + inline(' '.join(q), repo_dir) + '</blockquote>'); continue
        if LI.match(ln):
            para(buf); buf = []
            items = []                      # (indent, ordered, text)
            while i < len(L):
                m2 = LI.match(L[i])
                if m2: items.append([len(m2.group(1)), bool(re.match(r'\d', m2.group(2))), m2.group(3)]); i += 1
                elif L[i].strip() and L[i].startswith('  ') and items: items[-1][2] += ' ' + L[i].strip(); i += 1
                else: break
            stack, html_ = [], ''
            for ind, ordd, text in items:
                while stack and ind < stack[-1][0]:
                    html_ += '</li></' + stack[-1][1] + '>'; stack.pop()
                if not stack or ind > stack[-1][0]:
                    tag = 'ol' if ordd else 'ul'; html_ += f'<{tag}>'; stack.append((ind, tag))
                else:
                    html_ += '</li>'
                html_ += '<li>' + inline(text, repo_dir)
            while stack: html_ += '</li></' + stack[-1][1] + '>'; stack.pop()
            out.append(html_); continue
        if not ln.strip(): para(buf); buf = []; i += 1; continue
        buf.append(ln); i += 1
    para(buf)
    return '\n'.join(out)
