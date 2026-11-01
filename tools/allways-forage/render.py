"""Render an ALLWAYS edit decision list (edl.json) to an mp4 plus a source ledger.

  python3 render.py path/to/edl.json [--out film.mp4] [--control]

EDL schema (all times in seconds, all positions normalised 0–1):

{
  "id": "059-ball", "title": "...", "size": [640, 480], "fps": 24,
  "source_gain_db": 0,                 # global gain on source audio
  "score": {"file": "score.wav", "gain_db": -6} | null,   # optional extra track, mixed under
  "events": [
    {"dur": 2.5,                       # event length (required for stills/cards; clip default = out-in)
     "label": "why this shot is here",
     "fade_in": 0, "fade_out": 0,      # video fades from/to black
     "layers": [                       # drawn in order onto a black canvas
       {"src": "<shot id>", "media": "clip|loop|still",
        "in": 0.0,                     # seconds into the clip (clip/loop)
        "box": [0, 0, 1, 1],           # target box on the canvas (x, y, w, h)
        "fit": "cover|contain|register",
        "anchor": [0.5, 0.5],          # register: source point (normalised in source frame)…
        "to": [0.5, 0.5],              # …lands here (normalised in box)
        "k": 1.0,                      # register: output px per source px (uniform scale)
        "audio": true, "gain_db": 0, "afade_in": 0.05, "afade_out": 0.1}
     ],
     "card": {"lines": ["text"], "size": 26}   # optional text card instead of / over layers
    }
  ]
}

Only translation and uniform scaling are applied to sources; there is no
mirroring, rotation, warping or retiming. The ledger records every transform.
"""
import json, os, subprocess, sys, tempfile, argparse, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = {e['id']: e for e in json.load(open(os.path.join(HERE, 'index.json')))}
FONT = '/usr/share/fonts/opentype/inter/Inter-Regular.otf'
if not os.path.exists(FONT):
    FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def probe(p):
    o = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height',
                                 '-show_entries', 'format=duration', '-of', 'json', p]).decode()
    j = json.loads(o)
    v = next(s for s in j['streams'] if s['codec_type'] == 'video')
    has_a = any(s['codec_type'] == 'audio' for s in j['streams'])
    return v['width'], v['height'], float(j['format'].get('duration') or 0), has_a


def media_path(L):
    e = IDX[L['src']]
    m = L.get('media') or ('clip' if 'clip' in e['media'] else 'loop' if 'loop' in e['media'] else 'still')
    return e, m, e['media'][m]


def esc(s):
    return s.replace('\\', '\\\\').replace(':', '\\:').replace("'", "’").replace('%', '\\%')


def render_event(ev, i, W, H, fps, tmp, control=False):
    dur = ev.get('dur')
    inputs, fv, fa, ledger = [], [], [], []
    fv.append(f'color=black:s={W}x{H}:r={fps}:d={{DUR}}[c0]')
    cur = 'c0'
    amix = []
    for j, L in enumerate(ev.get('layers', [])):
        e, m, p = media_path(L)
        sw, sh, sd, has_a = probe(p)
        t_in = float(L.get('in', 0))
        if dur is None:
            dur = float(L.get('out', sd)) - t_in
        bx, by, bw, bh = L.get('box', [0, 0, 1, 1])
        BX, BY, BW, BH = bx * W, by * H, bw * W, bh * H
        fit = L.get('fit', 'cover')
        if control and fit == 'register':
            fit = 'cover'
        if fit == 'register':
            k = float(L.get('k', 1.0))
            ax, ay = L.get('anchor', [.5, .5]); tx, ty = L.get('to', [.5, .5])
            ox = BX + tx * BW - ax * sw * k; oy = BY + ty * BH - ay * sh * k
        else:
            k = (max if fit == 'cover' else min)(BW / sw, BH / sh)
            ox = BX + (BW - sw * k) / 2; oy = BY + (BH - sh * k) / 2
        n = sum(1 for x in inputs if x == '-i')
        if m == 'still':
            inputs += ['-loop', '1', '-framerate', str(fps), '-t', '{DUR}', '-i', p]
        else:
            inputs += (['-stream_loop', '-1'] if m == 'loop' or L.get('loop') else []) + ['-ss', f'{t_in:.3f}', '-t', '{DUR}', '-i', p]
        sw2, sh2 = max(2, round(sw * k)), max(2, round(sh * k))
        # crop the scaled layer to its box so neighbouring panels do not overlap
        fv.append(f'[{n}:v]fps={fps},scale={sw2}:{sh2}:flags=lanczos,setsar=1,format=rgba[s{j}]')
        fv.append(f'color=black@0:s={int(BW)}x{int(BH)}:r={fps}:d={{DUR}},format=rgba[b{j}]')
        fv.append(f'[b{j}][s{j}]overlay=x={ox - BX:.1f}:y={oy - BY:.1f}:shortest=1[l{j}]')
        fv.append(f'[{cur}][l{j}]overlay=x={BX:.0f}:y={BY:.0f}:shortest=1[c{j + 1}]')
        cur = f'c{j + 1}'
        if L.get('audio', True) and has_a and m != 'still':
            g = float(L.get('gain_db', 0)); fi = float(L.get('afade_in', .04)); fo = float(L.get('afade_out', .08))
            fa.append(f'[{n}:a]aresample=48000,aformat=channel_layouts=stereo,volume={g}dB,'
                      f'afade=t=in:d={fi},afade=t=out:st={{DUROUT{fo}}}:d={fo}[a{j}]')
            amix.append(f'[a{j}]')
        ledger.append({'src': e['id'], 'film': e['title'], 'year': e['year'], 'page': e['page'], 'media': m,
                       'source_start': e['start'], 'clip_in': t_in, 'clip_out': t_in + (dur if m != 'still' else 0),
                       'film_time_in': None if m == 'still' or e['start'] is None else round(e['start'] + t_in, 2),
                       'transform': {'fit': fit, 'scale': round(k, 4), 'offset_px': [round(ox, 1), round(oy, 1)],
                                     'anchor': L.get('anchor'), 'to': L.get('to'), 'box': [bx, by, bw, bh]},
                       'audio': bool(L.get('audio', True) and has_a and m != 'still'), 'gain_db': L.get('gain_db', 0)})
    dur = float(dur or 2)
    card = ev.get('card')
    if card:
        lines = card['lines']; sz = card.get('size', 24)
        y0 = card['y'] * H if 'y' in card else H / 2 - (len(lines) - 1) * sz * .8   # 'y': caption position (fraction of height)
        for li, t in enumerate(lines):
            fv.append(f"[{cur}]drawtext=fontfile={FONT}:text='{esc(t)}':fontcolor=0xf0eadc:fontsize={sz}:"
                      f"x=(w-text_w)/2:y={y0 + li * sz * 1.6:.0f}"
                      + (':box=1:boxcolor=black@0.55:boxborderw=6' if 'y' in card else '') + f"[t{li}]")
            cur = f't{li}'
    fvi, fvo = float(ev.get('fade_in', 0)), float(ev.get('fade_out', 0))
    post = 'format=yuv420p'
    if fvi: post = f'fade=t=in:d={fvi},' + post
    if fvo: post = f'fade=t=out:st={dur - fvo:.3f}:d={fvo},' + post
    fv.append(f'[{cur}]{post}[vout]')
    if amix:
        fa.append(f'{"".join(amix)}amix=inputs={len(amix)}:normalize=0,apad,atrim=0:{dur:.3f}[aout]')
    else:
        fa.append(f'anullsrc=r=48000:cl=stereo,atrim=0:{dur:.3f}[aout]')
    graph = ';'.join(fv + fa).replace('{DUR}', f'{dur:.3f}')
    import re
    graph = re.sub(r'\{DUROUT([0-9.]+)\}', lambda mm: f'{max(0, dur - float(mm.group(1))):.3f}', graph)
    inputs = [x.replace('{DUR}', f'{dur + .5:.3f}') for x in inputs]
    out = os.path.join(tmp, f'{i:03d}.mp4')
    cmd = ['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', graph, '-map', '[vout]', '-map', '[aout]',
           '-t', f'{dur:.3f}', '-r', str(fps), '-c:v', 'libx264', '-crf', '14', '-preset', 'veryfast',
           '-c:a', 'pcm_s16le', '-ar', '48000', out]
    subprocess.run(cmd, check=True)
    return out, dur, ledger


def main():
    a = argparse.ArgumentParser(); a.add_argument('edl'); a.add_argument('--out'); a.add_argument('--control', action='store_true')
    a = a.parse_args()
    E = json.load(open(a.edl)); base = os.path.dirname(os.path.abspath(a.edl))
    W, H = E.get('size', [640, 480]); fps = E.get('fps', 24)
    out = a.out or os.path.join(base, E['id'] + ('-control' if a.control else '') + '.mp4')
    led, t = [], 0.0
    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for i, ev in enumerate(E['events']):
            p, d, lg = render_event(ev, i, W, H, fps, tmp, a.control)
            parts.append(p)
            led.append({'n': i, 't_in': round(t, 3), 't_out': round(t + d, 3), 'label': ev.get('label', ''),
                        'card': (ev.get('card') or {}).get('lines'), 'layers': lg})
            t += d
        lst = os.path.join(tmp, 'list.txt')
        open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
        cat = os.path.join(tmp, 'cat.mkv')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', cat], check=True)
        sg = float(E.get('source_gain_db', 0)); sc = E.get('score')
        if sc and os.path.exists(os.path.join(base, sc['file'])):
            fa = (f"[0:a]volume={sg}dB[s];[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={sc.get('gain_db', 0)}dB[m];"
                  f"[s][m]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[a]")
            ins = ['-i', cat, '-i', os.path.join(base, sc['file'])]
        else:
            fa = f'[0:a]volume={sg}dB,alimiter=limit=0.89[a]'; ins = ['-i', cat]
        subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', fa, '-map', '0:v', '-map', '[a]',
                        '-c:v', 'libx264', '-crf', '23', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                        '-c:a', 'aac', '-b:a', '128k', out], check=True)
    h = hashlib.sha256(open(a.edl, 'rb').read()).hexdigest()[:12]
    lp = os.path.splitext(out)[0] + '.ledger.json'
    json.dump({'film': E['id'], 'title': E.get('title'), 'edl_sha': h, 'control': a.control, 'duration': round(t, 3),
               'size': [W, H], 'fps': fps, 'events': led}, open(lp, 'w'), indent=1)
    print(out, f'{t:.1f}s', lp)


if __name__ == '__main__':
    main()
