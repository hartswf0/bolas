"""Normalize the published ALLWAYS records without changing their verdicts.

Run with Python 3, passing a directory containing downloaded published records.
This is an import snapshot, not a new review of the films.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

BASE = 'https://hartswf0.github.io/bolas/'
ROOT = Path(__file__).resolve().parents[2]
REF = Path(sys.argv[1])


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def all(self, tag=None, cls=None):
        found = []
        for c in self.children:
            if isinstance(c, Node):
                if (not tag or c.tag == tag) and (not cls or cls in c.attrs.get('class', '').split()):
                    found.append(c)
                found += c.all(tag, cls)
        return found

    def text(self):
        return re.sub(r'\s+', ' ', ' '.join(c.text() if isinstance(c, Node) else c for c in self.children)).strip()


class DOM(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {'img', 'meta', 'link', 'br', 'hr', 'input', 'source', 'wbr'}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def read(path):
    return (REF / path).read_text()


def doc(path):
    return DOM(read(path)).root


def first(nodes, default=None):
    return nodes[0] if nodes else default


def seconds(text):
    # Only parse published output timecodes; never infer timings from shot order.
    m = re.match(r'(?:(\d+):)?(\d+(?:\.\d+)?)', text)
    return (float(m[1] or 0)*60 + float(m[2])) if m else None


films = []
argon = json.loads(read('argon-films.json'))
for f in argon:
    b = BASE + 'allways-argon/studio/'
    group = ('work:' + re.sub(r'^BROLL_\d+_', '', f['slug']).replace('_', '-').lower()) if f['cat'] == 'BROLL' else ('operator:' + str(f['scion_id'])) if f['cat'].startswith('SCION') else 'study:' + f['slug']
    shots = [dict(start=s['start_s'], end=s['end_s'], title=s['src_title'], why=s.get('why', ''), action=s.get('action', ''), source=s.get('src_url', ''), sourceIn=s.get('in_s'), sourceOut=s.get('out_s'), thumb=urljoin(b, 'thumbs/'+s['clip_id']+'.jpg') if s.get('clip_id') else '', kind=s['type']) for s in f['edl']]
    films.append(dict(id='argon-'+f['slug'], maker='Argon', title=f['title'], description=f['subtitle'], operator=f['scion_id'], category='Works' if f['cat']=='BROLL' else 'Operators' if f['cat'].startswith('SCION') else 'Studies & collections', group=group, duration=f['dur'], version='v2', video=urljoin(b, f['video']), poster=urljoin(b, f['first_thumb']), case=urljoin(b, '#film='+f['slug']), strip=urljoin(b, f['strip']), shots=shots, verdict='Pass · visual & structural', scope='Published Argon v2 tribunal verdict. Visual and structural review; this import does not establish full audiovisual acceptance.', critic=f['critic'], theorem=f['theorem'], boundary=f['boundary'], lineage=f['lineage'], proof=f['proof_scene'], records=[dict(name='Published manifest', url=urljoin(b, 'manifests/'+f['slug']+'.json'))], comparisons=[]))

sol = json.loads(read('allways-sol/catalog.json'))
for f in sol['films']:
    b = BASE+'allways-sol/'
    shots = []
    if f['id'] == 55:
        ledger = json.loads(read('allways-sol/films/055/records/v04/EDIT_LEDGER.json'))
        shots = [dict(start=s['timeline_in'],end=s['timeline_out'],title=s['source_title'],why=s['observation'],action=s['sense'],source=s['cached_url'],sourceIn=s['clip_in'],sourceOut=s['clip_out'],thumb='frames/sol-055-'+str(i)+'.jpg',kind='shot') for i,s in enumerate(ledger['shots'])]
    films.append(dict(id='sol-'+f['number'],maker='Sol',title=f['title'],description=f['description'],operator=f['id'],category='Operators',group='operator:'+str(f['id']),duration=f['film']['duration'],version=f['version'],video=urljoin(b,f['film']['url']),poster=urljoin(b,f['poster']),case=urljoin(b,'#film'+f['number']),shots=shots,verdict='Source search unfinished' if f['status']=='unfinished' else 'Bounded visual review',scope=f['scope'],criticLinks=[dict(name=x['name'],url=urljoin(b,x['url'])) for x in f['critics']],records=[dict(name=x['name'],url=urljoin(b,x['url'])) for x in f['records']],comparisons=[dict(name=x['filename'],video=urljoin(b,x['url']),duration=x['duration']) for x in f['comparisons']],preparatory=f['status']=='unfinished'))

sonnet = doc('allways-sonnet/index.html')
for card in sonnet.all('a','fcard'):
    rel='allways-sonnet/'+card.attrs['href']
    b=BASE+rel
    page=doc(rel+'index.html')
    label=card.all('span','label')[0].text()
    op=int(re.search(r'SCION (\d+)',label)[1])
    duration=float(re.search(r'· (\d+) s',label)[1])
    shots=[]
    tables=page.all('table','cut')
    for row in tables[0].all('tr') if tables else []:
        td=row.all('td')
        if len(td)!=4:continue
        start=seconds(td[1].text());dur=td[1].all('small')
        if start is None or not dur:continue
        source=first(td[2].all('a'));img=first(td[0].all('img'))
        shots.append(dict(start=start,end=start+float(dur[0].text().split()[0]),title=source.text() if source else td[2].text(),source=urljoin(b,source.attrs['href']) if source else '',why=td[3].text(),thumb=urljoin(b,img.attrs['src']) if img else '',kind='shot'))
    videos=page.all('video')
    critic=first([n for n in page.all('section') if n.attrs.get('id')=='critic'])
    films.append(dict(id='sonnet-'+str(op),maker='Sonnet',title=card.all('h3')[0].text(),description=card.all('p')[0].text(),operator=op,category='Operators',group='operator:'+str(op),duration=duration,version='Published cut',video=urljoin(b,videos[0].attrs['src']),poster=urljoin(b,'poster.jpg'),case=b,shots=shots,verdict=card.all('span','vline')[0].text().replace('critic: ',''),scope='Published Sonnet critic record. Frame sheets and sound levels; no listening or normal-speed screening was reported.',criticText=critic.text() if critic else '',records=[dict(name='Source ledger',url=urljoin(b,a.attrs['href'])) for a in page.all('a') if a.attrs.get('href','').endswith('.ledger.json')],comparisons=[dict(name='Published alternate',video=urljoin(b,v.attrs['src']),duration=None) for v in videos[1:]]))

workmap={'nobody-home':85,'almost-human':57,'terra-incognita':71,'split-second':84,'cut-to-the-chase':91,'kinetic':83,'zero-memory':106,'homonym':55,'anybody-anywhere':56,'collective-inventories':65,'mnemonil':74,'planimetric':86}
for slug,op in workmap.items():
    rel='allways-opus/films/'+slug+'/'
    b=BASE+rel;page=doc(rel+'index.html')
    videos=page.all('video');shots=[]
    for table in page.all('table'):
        if 'why' not in [x.text().lower() for x in table.all('th')]:continue
        for row in table.all('tr'):
            td=row.all('td')
            if len(td)!=5:continue
            start=seconds(td[1].text());d=td[1].all('span')
            if start is None or not d:continue
            dur=seconds(d[0].text());source=first(td[2].all('a'))
            shots.append(dict(start=start,end=start+dur,title=source.text() if source else td[2].text(),source=urljoin(b,source.attrs['href']) if source else '',why=td[4].text(),thumb='',kind='shot'))
    desc=first(page.all('p','lede'));state=first(page.all('span','chip'))
    reports=page.all('pre','report')
    # Verdict is read from the report, retaining inconclusive/reference-stronger results.
    text='\n\n'.join(x.text() for x in reports)
    verdict=re.search(r'VERDICT:\s*([^\.\n]+)',text,re.I)
    duration=re.search(r'(\d+) s',first(page.all('div','player')).text())
    films.append(dict(id='opus-'+slug,maker='Opus 5.5',title=page.all('h1')[0].text(),description=desc.text() if desc else '',operator=op,category='Works',group='work:'+slug,duration=float(duration[1]) if duration else None,version='Published cut',video=urljoin(b,videos[0].attrs['src']),poster=urljoin(b,'poster.jpg'),case=b,shots=shots,verdict=verdict[1][:170] if verdict else 'See critic report',scope='Published Opus blind critic record. Frames and transcripts only; sound remains unjudged until a person listens.',criticText=text,records=[dict(name='Complete case study',url=b)],comparisons=[dict(name='Published comparison '+str(i+1),video=urljoin(b,v.attrs['src']),duration=None) for i,v in enumerate(videos[1:])]))

# The Opus page uses a comma in the display title; its URL is the stable work key.
for f in films:
    if f['group']=='work:anybody-anywhere':f['group']='work:anybody-anywhere'
films.sort(key=lambda f:(f['operator'],f['category'],f['maker'],f['title']))
assert len(films)==132, len(films)
assert len({f['id'] for f in films})==132
assert all(f['video'].startswith('https://') for f in films)
out=dict(imported='2026-11-02',source=BASE+'paeleo/allways/',films=films)
target=ROOT/'paeleo/allways/light-table/catalog.json'
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
print(f'{len(films)} entries; {sum(bool(f["shots"]) for f in films)} with imported cut timings; {target.stat().st_size} bytes')
