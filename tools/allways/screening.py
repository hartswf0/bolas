"""Build the manifest for the ALLWAYS screening room: every film of every run, one canonical copy each.

  python3 tools/allways/screening.py            # measure new files, write paeleo/allways/screening.json
  python3 tools/allways/screening.py --no-measure   # reuse screening-measure.json only

Reads each run in paeleo/allways/runs.json through the adapter that fits it (see ADAPTERS), checks every
copy with ffprobe and EBU R128 loudness (ffmpeg), and writes:

  paeleo/allways/screening.json          films, copies and per-copy playback gain
  paeleo/allways/screening-measure.json  cache of measurements, keyed by path, size and mtime-free hash of size
  paeleo/allways/screening/posters/      small posters for films that have none

Nothing in a run's own folder is changed. The files are regularised at playback: the screening room fits
every film into one frame (letterbox or pillarbox, no cropping), and scales each copy's volume to a common
loudness. Standard library plus ffmpeg/ffprobe. See RUNS.md, "The screening room".
"""
import argparse, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'paeleo' / 'allways'
TARGET_LUFS = -20.0      # where every copy is brought to
MAX_BOOST = 12.0         # never lift a quiet copy by more than this (dB)
CEILING_DBTP = -1.0      # boosted peaks stay under this
SILENT_BELOW = -60.0     # integrated loudness below this counts as silence


def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def jload(p, default=None):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return default


# ---------- measurement -------------------------------------------------------------------------------
def measure(path):
    """ffprobe geometry/codecs and ebur128 loudness for one file."""
    pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,codec_name,width,height,r_frame_rate',
                         '-show_entries', 'format=duration,size', '-of', 'json', str(path)], capture_output=True)
    j = json.loads(pr.stdout or b'{}')
    v = next((s for s in j.get('streams', []) if s['codec_type'] == 'video'), {})
    a = next((s for s in j.get('streams', []) if s['codec_type'] == 'audio'), None)
    n, d = (v.get('r_frame_rate') or '0/1').split('/')
    m = {'w': v.get('width'), 'h': v.get('height'), 'fps': round(int(n) / max(1, int(d)), 3), 'vcodec': v.get('codec_name'),
         'acodec': a['codec_name'] if a else None, 'duration': round(float(j['format'].get('duration', 0)), 2), 'bytes': int(j['format'].get('size', 0))}
    if a:
        er = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True).stderr.decode(errors='replace')
        tail = er[er.rfind('Summary:'):] if 'Summary:' in er else ''
        li = re.search(r'I:\s+(-?[\d.]+)\s+LUFS', tail); tp = re.search(r'Peak:\s+(-?[\d.]+|-inf)\s+dBFS', tail)
        m['lufs'] = float(li.group(1)) if li else None
        m['peak'] = float(tp.group(1)) if tp and tp.group(1) != '-inf' else None
    return m


def gain_for(m):
    """dB to apply at playback so this copy sits at TARGET_LUFS without clipping."""
    if not m.get('acodec') or m.get('lufs') is None or m['lufs'] < SILENT_BELOW:
        return 0.0, True
    g = TARGET_LUFS - m['lufs']
    if g > 0:
        g = min(g, MAX_BOOST)
        if m.get('peak') is not None: g = min(g, CEILING_DBTP - m['peak'])
        g = max(g, 0.0)
    return round(g, 1), False


class Measurer:
    def __init__(self, cache_path, enabled=True):
        self.path = cache_path; self.enabled = enabled
        self.cache = jload(cache_path, {})
        self.todo = {}

    def need(self, p):
        key = rel(p); st = os.stat(p).st_size
        c = self.cache.get(key)
        if not c or c.get('bytes') != st: self.todo[key] = p
        return key

    def run(self):
        if self.enabled and self.todo:
            print(f'measuring {len(self.todo)} files …', flush=True)
            with ThreadPoolExecutor(4) as ex:
                for key, m in zip(self.todo, ex.map(measure, self.todo.values())):
                    self.cache[key] = m
            Path(self.path).write_text(json.dumps(dict(sorted(self.cache.items())), indent=0))

    def get(self, p):
        return self.cache.get(rel(p), {})


# ---------- adapters: each returns film dicts with copies (paths only; measured afterwards) ------------
def copy(label, kind, path, **kw):
    return {'label': label, 'kind': kind, 'path': Path(path), **kw}


def label_from_suffix(stem, base):
    suf = stem[len(base):].strip('-_') if stem.startswith(base) else stem
    return suf.replace('-', ' ').replace('_', ' ') or 'copy'


def generated_run(run, order, cases):
    """A generated run (RUNS.md): films.json plus films/<slug>/<slug>.mp4. Other mp4s in the folder are copies."""
    base = ROOT / run['path'].strip('/')
    films = []
    for f in (jload(base / 'films.json', {}) or {}).get('films', []):
        d = base / 'films' / f['slug']
        mp4 = d / f'{f["slug"]}.mp4'
        if not mp4.exists(): continue
        extra = [copy(label_from_suffix(p.stem, f['slug']) if p.stem != 'compare' else 'comparison', 'comparison', p) for p in sorted(d.glob('*.mp4')) if p != mp4]
        films.append({'run': run['id'], 'family': 'broll', 'key': f['slug'], 'title': f.get('title', f['slug']), 'sub': '',
                      'state': f.get('state', ''), 'verdict': f.get('verdict', ''), 'case': cases(run, f['slug']),
                      'poster': (d / 'poster.jpg') if (d / 'poster.jpg').exists() else None,
                      'copies': [copy('current cut', 'canonical', mp4)] + extra})
    return films


def adapter_generated(run, order):
    return generated_run(run, order, lambda r, slug: f'{r["path"].strip("/")}/films/{slug}/')


def adapter_argon_studio(run, order):
    """allways-argon/studio: manifests/*.json (one per film) and films/<slug>.mp4. Argon's 12 run films join as older copies."""
    base = ROOT / run['path'].strip('/')
    argon_run = ROOT / 'allways-argon'
    run_copies = {}
    for f in (jload(argon_run / 'films.json', {}) or {}).get('films', []):
        mp4 = argon_run / 'films' / f['slug'] / f'{f["slug"]}.mp4'
        if mp4.exists(): run_copies[slugify(f['slug'])] = (f, mp4)
    films = []
    for mf in sorted((base / 'manifests').glob('*.json')):
        m = jload(mf, {})
        slug = m.get('slug') if isinstance(m, dict) else None
        mp4 = base / 'films' / f'{slug}.mp4' if slug else None
        if not mp4 or not mp4.exists(): continue
        fam = 'broll' if slug.startswith('BROLL_') else 'scion' if slug.startswith('SCION_') else 'other'
        key = slugify(re.sub(r'^BROLL_\d+_', '', slug)) if fam == 'broll' else m.get('scion_id') if fam == 'scion' else slugify(slug)
        verdict = ''
        ct = m.get('critic_tribunal') or {}
        vk = sorted(k for k in ct if 'verdict' in k)
        if vk: verdict = str(ct[vk[-1]]).replace('_', ' ')
        copies = [copy('studio cut (v2)', 'canonical', mp4)]
        if fam == 'broll' and key in run_copies:
            copies.append(copy('earlier run cut', 'older', run_copies[key][1]))
        films.append({'run': 'allways-argon', 'family': fam, 'key': key, 'title': re.sub(r'\s+', ' ', m.get('title', slug)), 'sub': m.get('subtitle', ''),
                      'state': 'studio ' + m.get('version', ''), 'verdict': verdict, 'case': f'{run["path"].strip("/")}/cases/{slug}.html',
                      'poster': None, 'copies': copies, '_id': 'argon-' + slugify(slug)})
    return films


def adapter_sol(run, order):
    base = ROOT / run['path'].strip('/')
    cat = jload(base / 'catalog.json', {}) or {}
    films = []
    for f in cat.get('films', []):
        m = f.get('film') or {}
        if not m.get('url') or not (base / m['url']).exists(): continue
        copies = [copy(f'{f.get("version", "")} cut'.strip(), 'canonical', base / m['url'])]
        for c in f.get('comparisons', []):
            if (base / c['url']).exists():
                copies.append(copy(re.sub(r'^ALLWAYS_\d+_|_V\d+\.mp4$|\.mp4$', '', c.get('filename', 'comparison')).replace('_', ' ').lower() or 'comparison', 'comparison', base / c['url']))
        films.append({'run': run['id'], 'family': 'scion', 'key': f['id'], 'title': f['title'], 'sub': f.get('description', ''),
                      'state': f.get('status', ''), 'verdict': f.get('status', '') if m.get('kind') == 'film' else 'unfinished source study',
                      'case': f'{run["path"].strip("/")}/index.html#film{f["number"]}', 'poster': (base / f['poster']) if f.get('poster') and (base / f['poster']).exists() else None,
                      'copies': copies})
    return films


def adapter_sonnet(run, order):
    base = ROOT / run['path'].strip('/')
    status = jload(base / 'status.json', {}) or {}
    names = {}
    films = []
    for d in sorted(p for p in base.iterdir() if p.is_dir() and re.match(r'\d{3}-', p.name)):
        mp4 = d / f'{d.name}.mp4'
        if not mp4.exists(): continue
        num = int(d.name[:3])
        copies = [copy('current cut', 'canonical', mp4)]
        for p in sorted(d.glob(f'{d.name}-*.mp4')):
            copies.append(copy(label_from_suffix(p.stem, d.name), 'comparison', p))
        films.append({'run': run['id'], 'family': 'scion', 'key': num, 'title': d.name[4:].replace('-', ' ').title(), 'sub': '',
                      'state': 'proof in progress', 'verdict': status.get(d.name, 'critic review pending'),
                      'case': f'{run["path"].strip("/")}/{d.name}/', 'poster': (d / 'poster.jpg') if (d / 'poster.jpg').exists() else None, 'copies': copies})
    return films


ADAPTERS = {'allways-opus': adapter_generated, 'allways-argon': None, 'allways-argon-studio': adapter_argon_studio,
            'allways-sol': adapter_sol, 'allways-sonnet': adapter_sonnet}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--no-measure', action='store_true'); a = ap.parse_args()
    runs = jload(OUT / 'runs.json', {}).get('runs', [])
    order = {r['id']: i for i, r in enumerate(runs)}
    films, skipped = [], []
    for r in runs:
        if r['id'] in ADAPTERS:
            ad = ADAPTERS[r['id']]
            if ad is None: continue          # allways-argon's twelve join the studio's films as copies
            films += ad(r, order)
        elif r.get('kind') != 'linked' and (ROOT / r['path'].strip('/') / 'films.json').exists():
            films += adapter_generated(r, order)      # any new generated run that follows RUNS.md is included as is
        else:
            skipped.append(r['id'])
    ms = Measurer(OUT / 'screening-measure.json', not a.no_measure)
    for f in films:
        for c in f['copies']: c['_key'] = ms.need(c['path'])
    ms.run()
    # posters for films without one
    pdir = OUT / 'screening' / 'posters'; pdir.mkdir(parents=True, exist_ok=True)
    out_films = []
    runmeta = {r['id']: r for r in runs}
    for f in films:
        fid = f.get('_id') or (f['run'].replace('allways-', '') + '-' + slugify(str(f['key'])))
        main_c = f['copies'][0]
        mm = ms.get(main_c['path'])
        poster = f['poster']
        if poster is None:
            pp = pdir / f'{fid}.jpg'
            if not pp.exists():
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0.5, mm.get("duration", 10) * 0.3):.2f}', '-i', str(main_c['path']), '-frames:v', '1', '-vf', 'scale=320:-2', '-q:v', '6', str(pp)])
            poster = pp
        copies = []
        for c in f['copies']:
            m = ms.get(c['path']); g, silent = gain_for(m)
            copies.append({'label': c['label'], 'kind': c['kind'], 'src': rel(c['path']), 'bytes': m.get('bytes'), 'duration': m.get('duration'),
                           'w': m.get('w'), 'h': m.get('h'), 'fps': m.get('fps'), 'lufs': m.get('lufs'), 'peak': m.get('peak'), 'gain_db': g, 'silent': silent})
        out_films.append({'id': fid, 'run': f['run'], 'family': f['family'], 'key': f['key'], 'title': f['title'], 'sub': f['sub'], 'state': f['state'],
                          'verdict': f['verdict'], 'case': f['case'], 'poster': rel(poster), 'duration': mm.get('duration'), 'copies': copies})
    # one run id per card: Argon's studio shows as Argon
    names = {r['id']: r.get('name', r['id']) for r in runs}
    names['allways-argon'] = 'Argon'
    out = {'target_lufs': TARGET_LUFS, 'max_boost_db': MAX_BOOST, 'ceiling_dbtp': CEILING_DBTP,
           'runs': [{'id': r['id'], 'name': names[r['id']], 'maker': r.get('maker', ''), 'href': rel(ROOT / r['path'].strip('/')) + '/'} for r in runs
                    if r['id'] in {f['run'] for f in out_films}],
           'run_order': ['allways-sonnet', 'allways-opus', 'allways-argon', 'allways-sol'],
           'films': out_films}
    # the studio's run is Argon: fold the two Argon registry entries into one run
    seen = set(); runs_out = []
    for r in out['runs']:
        if r['id'] in seen: continue
        seen.add(r['id']); runs_out.append(r)
    out['runs'] = runs_out
    (OUT / 'screening.json').write_text(json.dumps(out, indent=0, ensure_ascii=False))
    n_c = sum(len(f['copies']) for f in out_films)
    print(f'{len(out_films)} films, {n_c} copies, {len(runs_out)} runs; not included (no adapter): {skipped or "none"}')
    odd = [f['id'] for f in out_films if not f['copies'][0].get('w')]
    if odd: print('unmeasured:', odd)


if __name__ == '__main__':
    main()
