"""SCION 45 · Assembly: title card (3 s) + the 768 scene frames + end card (3 s) + sound -> film.mp4 (H.264/AAC, faststart),
the four stills, and a frame-count check. Also writes the proof gallery (holdout mattes, the DAG at key frames)."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.abspath(os.path.join(HERE, '..'))
C = os.path.join(HERE, 'cache')
sys.path.insert(0, HERE)


def run(cmd):
    print(' '.join(cmd)[:200]); subprocess.run(cmd, check=True)


def film():
    n = len([f for f in os.listdir(os.path.join(C, 'frames')) if f.endswith('.jpg')])
    assert n == 768, 'scene frames: %d' % n
    out = os.path.join(F, 'film.mp4')
    run(['ffmpeg', '-loglevel', 'error', '-y',
         '-loop', '1', '-framerate', '24', '-t', '3', '-i', os.path.join(C, 'card_title.png'),
         '-framerate', '24', '-i', os.path.join(C, 'frames/s%04d.jpg'),
         '-loop', '1', '-framerate', '24', '-t', '3', '-i', os.path.join(C, 'card_end.png'),
         '-i', os.path.join(C, 'scene_audio.wav'),
         '-filter_complex',
         '[0:v]format=yuv420p,fade=t=out:st=2.5:d=0.5[a];[1:v]format=yuv420p,fade=t=in:st=0:d=0.25[b];'
         '[2:v]format=yuv420p,fade=t=in:st=0:d=0.4[c];[a][b][c]concat=n=3:v=1:a=0[v]',
         '-map', '[v]', '-map', '3:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-maxrate', '2300k', '-bufsize', '4600k',
         '-pix_fmt', 'yuv420p', '-r', '24', '-c:a', 'aac', '-b:a', '160k', '-t', '38', '-movflags', '+faststart', out])
    p = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                        'stream=nb_read_frames,width,height,r_frame_rate:format=duration,size', '-of', 'json', out],
                       capture_output=True, text=True)
    info = json.loads(p.stdout)
    print(json.dumps(info))
    st = info['streams'][0]
    assert int(st['nb_read_frames']) == 912, 'film frames %s' % st['nb_read_frames']
    assert int(info['format']['size']) <= 12 * 1024 * 1024
    return info


def stills():
    os.makedirs(os.path.join(F, 'stills'), exist_ok=True)
    for t in (3.6, 9.0, 19.0, 28.0):
        i = int(round(t * 24))
        Image.open(os.path.join(C, 'frames/s%04d.jpg' % i)).convert('RGB').save(os.path.join(F, 'stills/still_%04.1fs.jpg' % t), quality=92)


def proof():
    """Holdout mattes and the DAG at the defining frames, re-rendered with their layers."""
    import scene
    os.makedirs(os.path.join(F, 'proof'), exist_ok=True)
    fnt = ImageFont.truetype(os.path.join(HERE, '../../../../tools/paeleo/fonts/f14.woff2'), 15)
    for t in (3.9, 18.3, 25.0, 27.2):
        i = int(round(t * 24))
        fr, rec, layers = scene.render(i, verify=True)
        by = {L.name: L for L in layers}
        tiles = []
        base = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8))
        tiles.append(('composite t=%.2f s' % t, base))
        for nm in ('dog_in', 'dog_out', 'jamb_R', 'porch_post', 'person_in', 'person_out'):
            if nm in by:
                a = by[nm].a
                im = Image.fromarray((np.clip(fr * 0.25 + a[..., None] * np.array([0.9, 0.75, 0.3]), 0, 1) * 255).astype(np.uint8))
                tiles.append(('matte: ' + nm, im))
        Wt, Ht = 640, 360
        cols = 2; rows = (len(tiles) + 1) // 2 + 1
        sheet = Image.new('RGB', (cols * Wt, rows * Ht), (14, 14, 20)); d = ImageDraw.Draw(sheet)
        for k, (lab, im) in enumerate(tiles):
            x, y = (k % cols) * Wt, (k // cols) * Ht
            sheet.paste(im.resize((Wt, Ht)), (x, y)); d.text((x + 8, y + 6), lab, font=fnt, fill=(255, 230, 120))
        y = ((len(tiles) + 1) // 2) * Ht + 10
        d.text((10, y), 'composite order (back -> front): ' + ' < '.join(rec['order']), font=fnt, fill=(220, 220, 220))
        d.text((10, y + 24), 'acyclic: %s   split needed (cycle if merged): %s   verifier max diff %.3f, px>2%%: %s' % (
            rec['acyclic'], rec['split_needed'], rec.get('verify_max_diff', -1), rec.get('verify_px_over_2pct')), font=fnt, fill=(220, 220, 220))
        for k, (a, b, c) in enumerate([e for e in rec['edges'] if 'dog' in e[0] or 'dog' in e[1] or 'person' in e[0] or 'person' in e[1]][:12]):
            d.text((10 + (k % 2) * 640, y + 52 + (k // 2) * 20), '%s  behind  %s   (%d px overlap)' % (a, b, c), font=fnt, fill=(170, 200, 255))
        sheet.save(os.path.join(F, 'proof/layers_%04.1fs.jpg' % t), quality=88)


def operator():
    """A mobile-readable operator page next to the film (local file; links are relative)."""
    m = json.load(open(os.path.join(F, 'measured.json')))
    inv = json.load(open(os.path.join(F, 'invariants.json'))) if os.path.exists(os.path.join(F, 'invariants.json')) else {}
    rows = ''.join('<tr><td>%s</td><td>%.2f</td><td>%s</td><td>%s</td></tr>' % (c['choice'], c['score_t'],
                   '-' if c['measured_onset_t'] is None else '%.3f' % c['measured_onset_t'], '-' if c['dt'] is None else '%+.3f' % c['dt'])
                   for c in m['choices'])
    A = m['assertions']
    html = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SCION 45 operator</title><style>
:root{--bg:#10111b;--ink:#e2dacc;--dim:#9a9aa8;--warm:#f0b268}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}
main{max-width:760px;margin:0 auto;padding:16px}
h1{font-size:1.3rem;margin:.2em 0}a{color:var(--warm)}video{width:100%%;border-radius:6px;background:#000}
table{border-collapse:collapse;width:100%%;font-size:.9rem}td,th{border-bottom:1px solid #2a2b3a;padding:4px 6px;text-align:left}
.k{color:var(--dim)}</style></head><body><main>
<h1>PAE-02 · SCION 45 · Occlusion Compositing</h1>
<p class="k">current revision: scene-v9 / dog-v6 · critic verdict: <b>not yet judged</b> (an independent critic has not seen this film)</p>
<video src="film.mp4" controls playsinline preload="metadata" poster="stills/still_28.0s.jpg"></video>
<h2>Choices, measured on the render</h2><table><tr><th>choice</th><th>score t</th><th>measured onset</th><th>dt</th></tr>%s</table>
<h2>Occlusion assertions</h2><ul>
<li>DAG acyclic every frame: %s</li><li>alpha valid every frame: %s</li>
<li>frames where the dog had to be split at the jamb (a cycle if merged): %d</li>
<li>order flips while overlapping (pops): %d</li><li>verifier (per-pixel depth re-composite) frames disagreeing &gt;50 px: %d of %d</li>
<li>PAELEO invariants (check_handmade.py): %s</li></ul>
<p>Next blocking failure: whatever the independent critic finds first; see <a href="method.md">method.md</a> for the known weak points.</p>
<p><a href="trace.json">trace.json</a> · <a href="measured.json">measured.json</a> · <a href="assets.json">assets.json</a> ·
<a href="ledger.jsonl">ledger</a> · <a href="proof/">proof gallery</a> · <a href="build/make.sh">build/make.sh</a></p>
</main></body></html>''' % (rows, A['dag_acyclic_every_frame'], A['alpha_valid_every_frame'], len(A['frames_where_dog_needed_split']),
                            len(A['order_flips_with_overlap']), len(A['verifier_frames_disagreeing_over_50px']), A['verifier_frames'],
                            'ALL OK' if inv.get('all_ok') else ('not run' if not inv else 'FAILS'))
    open(os.path.join(F, 'operator.html'), 'w').write(html)


if __name__ == '__main__':
    what = sys.argv[1:] or ['film', 'stills', 'proof', 'operator']
    if 'operator' in what:
        operator()
    if 'stills' in what:
        stills()
    if 'film' in what:
        film()
    if 'proof' in what:
        proof()
