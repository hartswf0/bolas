#!/usr/bin/env python3
"""SCION 093 · assembly. Cuts versions A and B from the shared take by their edit-decision lists, lays the identical
added cue under each, builds the diagnostic comparison (both cuts side by side on the take's own clock, each panel black
wherever its version omitted that moment, with retained-interval bars and a playhead), and joins them with plain colour
leaders: amber before A, blue before B, white before the diagnostic. No text anywhere. Writes ../film093/film.mp4 and
loudness.json (comparable loudness is one of 093's controlled variables)."""
import json, os, subprocess, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..'); OUT = os.path.join(ROOT, 'film093'); SRC = os.path.join(ROOT, 'rushes', 'film.mp4')
FPS = 24; W, H = 1280, 720
AMBER, BLUE = '0xf0a35a', '0x8fa8ff'
run = lambda args: subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *args], check=True)
tmp = lambda n: os.path.join(HERE, n)

edl = {v: json.load(open(os.path.join(OUT, f'edl_{v}.json'))) for v in 'AB'}
D = edl['A']['frames'] / FPS
meta = json.load(open(os.path.join(ROOT, 'rushes', 'meta.json')))
SRC_DUR = meta['frames'] / FPS; START = 1.6; SPEED = 3.6; DD = (SRC_DUR - START) / SPEED
subprocess.run(['node', os.path.join(HERE, 'cue.js'), f'{D:.4f}', f'{DD:.4f}'], check=True)
VENC = ['-c:v', 'libx264', '-crf', '24', '-preset', 'slow', '-tune', 'grain', '-pix_fmt', 'yuv420p', '-r', str(FPS)]
AENC = ['-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-ac', '2']

# 1 · the two versions: trim, splice with 25 ms audio fades, concat; then the identical cue under the source sound
for v in 'AB':
    ivs = edl[v]['intervals']; parts = []
    for k, iv in enumerate(ivs):
        a, b = iv['in_s'], iv['out_s']; d = b - a
        parts.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{k}];"
                     f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,afade=t=in:d=0.025,afade=t=out:st={d - 0.025:.4f}:d=0.025[a{k}];")
    cat = ''.join(f'[v{k}][a{k}]' for k in range(len(ivs))) + f'concat=n={len(ivs)}:v=1:a=1[vv][src];'
    mix = f"[src][1:a]amix=inputs=2:weights='1 0.8':normalize=0,atrim=0:{D}[aa]"
    run(['-i', SRC, '-i', tmp('cue.wav'), '-filter_complex', ''.join(parts) + cat + mix, '-map', '[vv]', '-map', '[aa]', *VENC, *AENC, tmp(f'v{v}.mp4')])

# 2 · the diagnostic: the take's clock at 3.6x, each version's panel dark where it cut, bars of what each kept
def kept_expr(v):
    terms = [f"between(t,{(iv['in_s'] - START) / SPEED:.4f},{(iv['out_s'] - START) / SPEED:.4f})" for iv in edl[v]['intervals']]
    return 'not(' + '+'.join(terms) + ')'
PW, PH = 600, 338; BX, BW = 30, 1220
bars = []
for row, (v, col) in enumerate([('A', AMBER), ('B', BLUE)]):
    y = 528 + row * 26
    bars.append(f"drawbox=x={BX}:y={y}:w={BW}:h=12:color=0x2a2420:t=fill")
    for iv in edl[v]['intervals']:
        x0 = BX + BW * (iv['in_s'] - START) / (SRC_DUR - START); x1 = BX + BW * (iv['out_s'] - START) / (SRC_DUR - START)
        bars.append(f"drawbox=x={x0:.1f}:y={y}:w={max(1, x1 - x0):.1f}:h=12:color={col}:t=fill")
fc = (f"[0:v]trim=start={START},setpts=(PTS-STARTPTS)/{SPEED},fps={FPS},scale={PW}:{PH},split=2[pa][pb];"
      f"[pa]drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='{kept_expr('A')}',drawbox=x=0:y=0:w=iw:h=ih:color={AMBER}:t=2[A];"
      f"[pb]drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='{kept_expr('B')}',drawbox=x=0:y=0:w=iw:h=ih:color={BLUE}:t=2[B];"
      f"color=black:s={W}x{H}:r={FPS}:d={DD:.4f}[bg];[bg][A]overlay=30:150[t1];[t1][B]overlay=650:150," + ','.join(bars) + "[t2];"
      f"color=white:s=2x64:r={FPS}:d={DD:.4f}[ph];[t2][ph]overlay=x='{BX}+{BW}*t/{DD:.4f}':y=516:shortest=1[vv]")
run(['-i', SRC, '-i', tmp('diag.wav'), '-filter_complex', fc, '-map', '[vv]', '-map', '1:a', '-af', 'volume=0.3', '-t', f'{DD:.4f}', *VENC, *AENC, tmp('vD.mp4')])

# 3 · leaders: black, a six-frame colour flash, black; then the whole film in order
def leader(name, col):
    run(['-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}:d=0.6', '-f', 'lavfi', '-i', f'color={col}:s={W}x{H}:r={FPS}:d=0.25',
         '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}:d=0.4', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
         '-filter_complex', '[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]', '-map', '[v]', '-map', '3:a', '-t', '1.25', *VENC, *AENC, tmp(name)])
leader('lA.mp4', AMBER); leader('lB.mp4', BLUE); leader('lD.mp4', 'white')
run(['-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}:d=1.5', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-t', '1.5', *VENC, *AENC, tmp('tail.mp4')])
seq = ['lA', 'vA', 'lB', 'vB', 'lD', 'vD', 'tail']
ins = sum((['-i', tmp(f'{s}.mp4')] for s in seq), [])
run([*ins, '-filter_complex', ''.join(f'[{i}:v][{i}:a]' for i in range(len(seq))) + f'concat=n={len(seq)}:v=1:a=1[v][a]',
     '-map', '[v]', '-map', '[a]', *[x if x != '24' else '29' for x in VENC], *AENC, '-movflags', '+faststart', os.path.join(OUT, 'film.mp4')])

# 4 · loudness of each version (integrated LUFS), the controlled variable the critic must not be confounded by
def lufs(f):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', f, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = re.findall(r'I:\s+(-?[\d.]+) LUFS', r); return float(m[-1]) if m else None
loud = {'A': lufs(tmp('vA.mp4')), 'B': lufs(tmp('vB.mp4')), 'diagnostic': lufs(tmp('vD.mp4'))}
json.dump({'integrated_LUFS': loud, 'version_seconds': D, 'diagnostic_seconds': round(DD, 3), 'speed': SPEED}, open(os.path.join(OUT, 'loudness.json'), 'w'), indent=1)
print('film093/film.mp4 written;', loud)
