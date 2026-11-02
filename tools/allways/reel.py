"""Render YouTube-ready reels from screening.json: the full reel (every film of every run) or a highlights cut.

  python3 tools/allways/reel.py highlights --out /path/to/out
  python3 tools/allways/reel.py full       --out /path/to/out

Each film becomes one 1280x720, 30 fps segment (fitted whole into the frame, never cropped), levelled toward
-16 LUFS from the loudness measured by screening.py, with a lower-third naming the maker and film for its
first seconds. Prompt groups get a title card. Segments are joined without re-encoding. Also writes
chapters.txt, description.md and a thumbnail. Nothing in any run's own files is changed.
Standard library plus ffmpeg and ffprobe.
"""
import argparse, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'paeleo' / 'allways'
W, H, FPS = 1280, 720, 30
TARGET = -16.0
FONT_B = next((p for p in ['/usr/share/fonts/opentype/inter/Inter-Bold.otf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'] if os.path.exists(p)))
FONT_R = next((p for p in ['/usr/share/fonts/opentype/inter/Inter-Regular.otf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if os.path.exists(p)))
COLOR = {'allways-sonnet': '0x9bc4a8', 'allways-opus': '0xe2a65c', 'allways-argon': '0x8fb2e6', 'allways-sol': '0xd98f8f'}
NAME = {'allways-sonnet': 'SONNET', 'allways-opus': 'OPUS', 'allways-argon': 'ARGON', 'allways-sol': 'SOL'}
RUN_ORDER = ['allways-sonnet', 'allways-opus', 'allways-argon', 'allways-sol']
BROLL = ['nobody-home', 'almost-human', 'terra-incognita', 'split-second', 'cut-to-the-chase', 'kinetic', 'zero-memory', 'homonym', 'anybody-anywhere', 'collective-inventories', 'mnemonil', 'planimetric']
FAM = {'scion': 0, 'broll': 1, 'other': 2}


def esc(t):
    return t.replace('\\', '\\\\').replace(':', '\\:').replace("'", '’').replace('%', '\\%').replace(',', '\\,')


def short(t):
    return re.sub(r'\s+', ' ', t.split(' — ')[0]).strip()


def gain_db(c):
    if c.get('silent') or c.get('lufs') is None: return 0.0
    g = TARGET - c['lufs']
    if g > 0:
        g = min(g, 12.0)
        if c.get('peak') is not None: g = min(g, -1.5 - c['peak'])
    return round(g, 1)


def load():
    M = json.loads((OUT / 'screening.json').read_text())
    ops = {e['id']: e['title'] for e in json.loads((OUT / 'scion' / 'scion-allways.json').read_text())}
    return M, ops


def order(films):
    rk = {r: i for i, r in enumerate(RUN_ORDER)}
    def key(f):
        k = int(f['key']) if f['family'] == 'scion' else (BROLL.index(f['key']) if f['family'] == 'broll' and f['key'] in BROLL else 99)
        return (FAM[f['family']], k, f['id'] if f['family'] == 'other' else '', rk.get(f['run'], 9), f['id'])
    return sorted(films, key=key)


# ---------- segments ---------------------------------------------------------------------------------------
def card(lines, dur, accent='0xe2a65c', sizes=(64, 30)):
    return {'kind': 'card', 'lines': lines, 'dur': dur, 'accent': accent, 'sizes': sizes}


def film_seg(f, ss=0.0, t=None, label_extra=''):
    c = f['copies'][0]; dur = c['duration']
    t = min(t, dur - ss) if t else dur - ss
    return {'kind': 'film', 'f': f, 'src': ROOT / c['src'], 'ss': ss, 't': t, 'gain': gain_db(c), 'has_audio': not (c.get('silent') or c.get('lufs') is None),
            'run': f['run'], 'title': short(f['title']) + label_extra, 'excerpt': t < dur - ss - 0.5, 'dur': t}


def scene_start(path, near, span=12.0):
    """First scene cut at or after `near` (within span seconds), so an excerpt opens on a new shot."""
    r = subprocess.run(['ffmpeg', '-nostats', '-ss', f'{max(0, near - 2):.2f}', '-t', f'{span:.1f}', '-i', str(path), '-an', '-vf', "select='gt(scene,0.30)',showinfo", '-f', 'null', '-'],
                       capture_output=True).stderr.decode(errors='replace')
    ts = [float(m) + max(0, near - 2) for m in re.findall(r'pts_time:([\d.]+)', r)]
    ts = [x for x in ts if x >= near - 0.5]
    return round(ts[0], 2) if ts else near


def plan_full(M, ops):
    segs = [card(['ALLWAYS', f'{len(M["films"])} films by four AI film-makers', 'Sonnet · Opus · Argon · Sol  |  cut by hand from public-domain archive footage'], 5.0, sizes=(120, 36))]
    chapters = [(0.0, 'ALLWAYS: all four runs')]
    last = None
    for f in order(M['films']):
        if f['family'] == 'scion': g = ('scion', f['key']); gt = ['SCION %03d' % f['key'], short(ops.get(f['key'], f['title']))]
        elif f['family'] == 'broll': g = ('broll', f['key']); gt = ['B-ROLL OF CIVILIZATION', f['key'].replace('-', ' ').upper()]
        else: g = ('other', 'block'); gt = ['COLLECTIONS AND STUDIES', 'Extra films from the Argon studio']
        if g != last:
            segs.append(dict(card(gt, 2.2, sizes=(88, 42)), chapter=' · '.join(gt) if g[0] != 'other' else gt[0]))
            last = g
        s = film_seg(f)
        if g[0] == 'other': s['chapter'] = short(f['title'])
        segs.append(s)
    segs.append(card(['Made by', 'Sonnet · Opus · Argon · Sol', 'Footage: movingimagearchive.com, public domain per the archive. AI-assisted editing; some films contain computationally altered footage.'], 9.0, sizes=(60, 44)))
    return segs


def plan_highlights(M, ops):
    by = {}
    for f in M['films']: by.setdefault((f['family'], f['key']), []).append(f)
    picks = [('scion', 55), ('scion', 56), ('scion', 59), ('scion', 61), ('scion', 62), ('scion', 64), ('broll', 'nobody-home'), ('broll', 'kinetic')]
    segs = [card(['SAME PROMPT. FOUR AIs.', 'Eight film prompts, answered by Sonnet, Opus, Argon and Sol.'], 5.5, sizes=(84, 34))]
    for fam, key in picks:
        fs = sorted(by.get((fam, key), []), key=lambda f: RUN_ORDER.index(f['run']) if f['run'] in RUN_ORDER else 9)
        if not fs: continue
        title = ['SCION %03d' % key, short(ops.get(key, ''))] if fam == 'scion' else ['B-ROLL OF CIVILIZATION', key.replace('-', ' ').upper()]
        segs.append(dict(card(title + ['%d makers' % len(fs)], 2.6, sizes=(88, 42)), chapter=' · '.join(title)))
        for f in fs:
            d = f['copies'][0]['duration']; ss = scene_start(ROOT / f['copies'][0]['src'], d * 0.2); ss = min(ss, max(0, d - 20))
            segs.append(film_seg(f, ss=ss, t=18.0))
    segs.append(card(['All 132 films, every maker, every prompt', 'in the full reel'], 7.0, sizes=(56, 36)))
    return segs


# ---------- rendering -------------------------------------------------------------------------------------
ENC = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-r', str(FPS), '-g', '60', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-video_track_timescale', '15360',
       '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-ac', '2']


def render(seg, path):
    if seg['kind'] == 'card':
        lines = seg['lines']; sizes = [seg['sizes'][0], seg['sizes'][1]] + [24] * 4
        total = sum(sizes[:len(lines)]) + 22 * (len(lines) - 1) + 40            # bar (5) + gap above the first line
        y = int((H - total) / 2); dt = []; bar_y = y
        y += 40
        for i, t in enumerate(lines):
            dt.append(f"drawtext=fontfile={FONT_B if i < 2 else FONT_R}:text='{esc(t)}':fontcolor=0xf0eadc:fontsize={sizes[i]}:x=(w-text_w)/2:y={y}")
            y += sizes[i] + 22
        vf = (f"color=c=0x0f1211:s={W}x{H}:r={FPS}:d={seg['dur']},drawbox=x=(iw-120)/2:y={bar_y}:w=120:h=5:color={seg['accent']}:t=fill," + ','.join(dt)
              + f",fade=t=in:d=0.25,fade=t=out:st={seg['dur'] - 0.25}:d=0.25,format=yuv420p")
        cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', vf, '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=stereo', '-t', str(seg['dur']), '-map', '0:v', '-map', '1:a', *ENC, str(path)]
    else:
        col = COLOR.get(seg['run'], '0xffffff'); d = seg['dur']
        v = (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=bicubic,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={FPS},"
             f"drawbox=x=40:y=ih-166:w=8:h=108:color={col}:t=fill:enable='between(t,0.3,5.5)',"
             f"drawtext=fontfile={FONT_B}:text='{esc(NAME.get(seg['run'], seg['run']))}':fontcolor={col}:fontsize=26:x=64:y=h-166:box=1:boxcolor=black@0.62:boxborderw=8:enable='between(t,0.3,5.5)',"
             f"drawtext=fontfile={FONT_B}:text='{esc(seg['title'].upper())}':fontcolor=0xf0eadc:fontsize=42:x=64:y=h-126:box=1:boxcolor=black@0.62:boxborderw=8:enable='between(t,0.3,5.5)'")
        if seg['excerpt']: v += f",fade=t=in:d=0.2,fade=t=out:st={d - 0.25:.2f}:d=0.25"
        v += ',format=yuv420p'
        inp = ['-ss', f"{seg['ss']:.2f}", '-t', f"{d:.2f}", '-i', str(seg['src'])]
        if seg['has_audio']:
            af = f"aresample=48000,aformat=channel_layouts=stereo,volume={seg['gain']}dB,alimiter=limit=0.89,afade=t=in:d=0.03,afade=t=out:st={max(0, d - 0.08):.2f}:d=0.08,apad,atrim=0:{d:.2f}"
            cmd = ['ffmpeg', '-v', 'error', '-y', *inp, '-vf', v, '-af', af, '-t', f'{d:.2f}', *ENC, str(path)]
        else:
            cmd = ['ffmpeg', '-v', 'error', '-y', *inp, '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-vf', v, '-map', '0:v', '-map', '1:a', '-t', f'{d:.2f}', *ENC, str(path)]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode or not path.exists(): raise RuntimeError(r.stderr.decode(errors='replace')[-400:])
    return path


def dur_of(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)]).decode().strip())


def tc(t):
    t = int(t); return f'{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}' if t >= 3600 else f'{t // 60}:{t % 60:02d}'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['full', 'highlights', 'package']); ap.add_argument('--out', required=True); ap.add_argument('--jobs', type=int, default=4); ap.add_argument('--limit', type=int)
    a = ap.parse_args(); out = Path(a.out)
    if a.mode == 'package': return package(out)
    seg_dir = out / f'seg-{a.mode}'; seg_dir.mkdir(parents=True, exist_ok=True)
    M, ops = load()
    segs = plan_full(M, ops) if a.mode == 'full' else plan_highlights(M, ops)
    if a.limit: segs = segs[:a.limit]
    paths = [seg_dir / f'{i:03d}.mp4' for i in range(len(segs))]
    print(f'{len(segs)} segments', flush=True)
    todo = [(s, p) for s, p in zip(segs, paths) if not p.exists()]
    done = 0
    with ThreadPoolExecutor(a.jobs) as ex:
        futs = [ex.submit(render, s, p) for s, p in todo]
        for fu in futs:
            fu.result(); done += 1
            if done % 10 == 0: print(f'  rendered {done}/{len(todo)}', flush=True)
    # chapters from measured durations
    t = 0.0; chap = []
    for s, p in zip(segs, paths):
        if s.get('chapter'): chap.append((t, s['chapter']))
        t += dur_of(p)
    if segs and segs[0]['kind'] == 'card': chap.insert(0, (0.0, 'ALLWAYS: all four runs')) if not chap or chap[0][0] > 0 else None
    lst = out / f'list-{a.mode}.txt'; lst.write_text(''.join(f"file '{p}'\n" for p in paths))
    final = out / f'allways-{a.mode}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', '-movflags', '+faststart', str(final)], check=True)
    (out / f'chapters-{a.mode}.txt').write_text('\n'.join(f'{tc(x)} {n}' for x, n in chap) + '\n')
    print(final, f'{dur_of(final) / 60:.1f} min', f'{final.stat().st_size / 1e6:.0f} MB', f'{len(chap)} chapters')


def thumbnail(out, M):
    """1280x720 cover: one poster per maker in a 2x2 grid, with a title bar."""
    pick = {'allways-sonnet': 'sonnet-59', 'allways-opus': 'opus-nobody-home', 'allways-argon': 'argon-scion-059-ball-graphic-constancy', 'allways-sol': 'sol-59'}
    ids = {f['id']: f for f in M['films']}
    posters = []
    for run in ['allways-sonnet', 'allways-opus', 'allways-argon', 'allways-sol']:
        f = ids.get(pick[run]) or next(x for x in M['films'] if x['run'] == run)
        posters.append(ROOT / f['poster'])
    fc = ''.join(f'[{i}:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,eq=contrast=1.08:saturation=1.1[t{i}];' for i in range(4))
    names = ['SONNET', 'OPUS', 'ARGON', 'SOL']; cols = ['0x9bc4a8', '0xe2a65c', '0x8fb2e6', '0xd98f8f']; xs = [20, 660, 20, 660]; ys = [370, 370, 730 - 360, 730 - 360]
    fc += '[t0][t1][t2][t3]xstack=inputs=4:layout=0_0|640_0|0_360|640_360[g];'
    lab = ','.join(f"drawtext=fontfile={FONT_B}:text='{n}':fontcolor={c}:fontsize=34:x={x}:y={y}:box=1:boxcolor=black@0.7:boxborderw=10" for n, c, x, y in zip(names, cols, [20, 660, 20, 660], [20, 20, 640, 640]))
    fc += f"[g]drawbox=x=0:y=250:w=1280:h=220:color=black@0.72:t=fill,drawtext=fontfile={FONT_B}:text='FOUR AIs':fontcolor=0xf0eadc:fontsize=118:x=(w-text_w)/2:y=262,drawtext=fontfile={FONT_B}:text='ONE ARCHIVE. 132 FILMS.':fontcolor=0xe2a65c:fontsize=58:x=(w-text_w)/2:y=392,{lab}[o]"
    args = ['ffmpeg', '-v', 'error', '-y']
    for pth in posters: args += ['-i', str(pth)]
    subprocess.run(args + ['-filter_complex', fc, '-map', '[o]', '-frames:v', '1', '-q:v', '3', str(out / 'thumbnail.jpg')], check=True)


def package(out):
    M, ops = load()
    runs = {}
    for f in M['films']: runs[f['run']] = runs.get(f['run'], 0) + 1
    thumbnail(out, M)
    for mode, title, blurb in [
        ('highlights', 'Same Film Prompt, Four AIs: Watch What Each One Made',
         'Eight film prompts, each answered by different AI film-makers (Sonnet, Opus, Argon and Sol) using the same pool of public-domain archive footage. Every cut here is a short excerpt; the full films are in the long reel.'),
        ('full', 'Four AIs Cut 132 Short Films From Old Public-Domain Footage (All Four Runs)',
         'Every film made by four AI film-makers (Sonnet, Opus, Argon and Sol) from public-domain educational, industrial, amateur and newsreel footage. Grouped by prompt, so you can watch the same prompt answered by each maker one after another. Use the chapters to jump.')]:
        ch = (out / f'chapters-{mode}.txt'); chapters = ch.read_text().strip().split('\n') if ch.exists() else []
        head = (f'{blurb}\n\nWHO MADE WHAT\n' + '\n'.join(f'{NAME[r].title()}: {runs.get(r, 0)} films' for r in RUN_ORDER if r in runs) +
                '\n\nHOW IT WAS MADE\nEach film was cut by hand from archive shots (search, contact sheets, an edit list with a reason for every shot), then reviewed by a separate AI critic where noted. Nobody has screened every film at speed. Volume is levelled per film; every film is shown whole, never cropped.\n'
                '\nDISCLOSURE\nEdited with AI assistance. The footage is real archival film; a few films contain computationally altered footage (for example, people removed from a room) and say so in their notes. Footage: movingimagearchive.com, public domain according to the archive.\n'
                '\nEVERYTHING, WITH THE PROMPTS AND REASONS\nhttps://hartswf0.github.io/bolas/paeleo/allways/#runs\nhttps://hartswf0.github.io/bolas/paeleo/allways/screening.html\n')
        tail = '\n#AI #FilmEditing #ArchiveFootage #ExperimentalFilm #PublicDomain'
        room = 4900 - len(head) - len(tail) - 40
        body, used = [], 0
        for ln in chapters:
            if used + len(ln) + 1 > room: body.append('\n(Chapter list continues in the pinned comment.)'); break
            body.append(ln); used += len(ln) + 1
        (out / f'youtube-{mode}.md').write_text(f'TITLE\n{title}\n\nDESCRIPTION\n{head}\nCHAPTERS\n' + '\n'.join(body) + tail + '\n\nTAGS\nAI film, AI editing, archive footage, public domain film, experimental film, found footage, Claude, Gemini, OpenAI, supercut\n')
        print(mode, 'description chars', len(head) + used + len(tail))


if __name__ == '__main__':
    main()
