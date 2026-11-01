"""Forage the local archive index.

  python3 forage.py "regex" [--media clip|loop|still|any] [--n 40] [--sheet out.jpg] [--field queries,title,subjects,notes]

Matches a case-insensitive regex against the archive queries that returned a
shot, its film title, CLIP subjects and reading notes. --sheet writes a
contact sheet: one row per shot, 6 frames across the clip (or the still),
labelled with row number and id prefix. Prints rows as: n id media year title | matched query.
"""
import json, os, re, sys, argparse, subprocess, tempfile
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = json.load(open(os.path.join(HERE, 'index.json')))
BY = {e['id']: e for e in IDX}

def frames(e, n=6, w=160, h=120):
    m = e['media']
    if 'clip' in m or 'loop' in m:
        p = m.get('clip') or m.get('loop')
        try:
            d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).decode().strip() or 0)
        except Exception:
            d = 0
        out = []
        with tempfile.TemporaryDirectory() as t:
            for i in range(n):
                ts = d * (i + .5) / n
                f = os.path.join(t, f'{i}.jpg')
                subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{ts:.2f}', '-i', p, '-frames:v', '1', '-vf', f'scale={w}:{h}', '-y', f], check=False)
                out.append(Image.open(f).convert('RGB') if os.path.exists(f) else Image.new('RGB', (w, h)))
        return out, d
    return [Image.open(m['still']).convert('RGB').resize((w, h))], 0

def sheet(rows, path, n=6):
    W, H = 160, 120
    im = Image.new('RGB', (W * n + 150, H * len(rows)), (16, 16, 16))
    dr = ImageDraw.Draw(im)
    for r, e in enumerate(rows):
        fs, d = frames(e, n)
        for i, f in enumerate(fs): im.paste(f, (150 + i * W, r * H))
        dr.text((4, r * H + 4), f"{r}  {e['id'][:8]}", fill=(255, 220, 120))
        dr.text((4, r * H + 20), (e['title'] or '')[:22], fill=(220, 220, 220))
        dr.text((4, r * H + 36), f"{e.get('year')}  {d:.1f}s {'/'.join(e['media'])}", fill=(160, 200, 160))
    im.save(path, quality=80)

def search(rx, media='any', fields=('queries', 'title', 'subjects', 'notes')):
    R = re.compile(rx, re.I); out = []
    for e in IDX:
        if media != 'any' and media not in e['media']: continue
        hits = []
        for f in fields:
            v = e.get(f)
            vals = v if isinstance(v, list) else [v]
            for x in vals:
                s = x['label'] if isinstance(x, dict) else str(x or '')
                if R.search(s): hits.append(s)
        if hits: out.append((e, hits))
    out.sort(key=lambda x: (-('clip' in x[0]['media']), -len(x[1])))
    return out

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('rx'); a.add_argument('--media', default='any')
    a.add_argument('--n', type=int, default=40); a.add_argument('--sheet'); a.add_argument('--field', default='queries,title,subjects,notes')
    a = a.parse_args()
    res = search(a.rx, a.media, a.field.split(','))[:a.n]
    for i, (e, h) in enumerate(res):
        print(f"{i:3d} {e['id'][:8]} {'/'.join(e['media']):16s} {e.get('year')} {e['title'][:40]:40s} | {h[0][:70]}")
    print(len(res), 'shown')
    if a.sheet: sheet([e for e, _ in res], a.sheet)
