"""Media for the case pages -> bolas/this-side-up/media/case/<slug>/ (sheets, 1100 px) and media/v/<slug>/<id>.mp4 (640 px web encodes)
plus a poster per version. Versions already encoded for the reader (media/film/*.mp4) are reused, not encoded twice.
python3 build_media.py sheets|versions [slug ...]"""
import os, sys, json, subprocess, time, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import data as D
B = '/home/claude/bolas/this-side-up/'; H = '/home/claude/'
REUSE = {H + 'film/this_side_up_with_credits.mp4': 'film/this-side-up.mp4', H + 'calib/calibration_test.mp4': 'film/calibration.mp4',
         H + 'guide/pose_guide_wordless.mp4': 'film/pose-guide.mp4', H + 'puppet/bullet_time_mockup.mp4': 'film/mockup.mp4',
         H + 'neo/dodge_animatic.mp4': 'film/animatic.mp4', H + 'neo/breakdown.mp4': 'film/breakdown.mp4', H + 'neo/tempus/out/tempus_fugit.mp4': 'film/tf-v1.mp4',
         H + 'neo/tempus/out/tempus_fugit_atlas.mp4': 'film/tf-marble.mp4', H + 'lab/tf3/out/tempus_fugit_v3_cardboard.mp4': 'film/tf-v3.mp4',
         H + 'lab/tf4/out/tempus_fugit_v4_bullet_and_clock.mp4': 'film/tf-v4.mp4', H + 'lab/ice/tempus_fugit_ice_ep1_thaw.mp4': 'film/ice.mp4',
         H + 'lab/fall/out/tempus_fugit_fall_cut6.mp4': 'film/fall.mp4', H + 'lab/tfu/renders/trouttown_tempus_fugit.mp4': 'film/trouttown.mp4',
         H + 'clx/wyg/out/P05-008.boone.mp4': 'film/wyg-cel.mp4', H + 'clx/col/out/P05-008.collage.mp4': 'film/wyg-collage.mp4'}
def dur(p): return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.strip() or 0)
def has_audio(p): return 'audio' in subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout
want = sys.argv[2:]; MAN = json.load(open(B + 'media/case/manifest.json')) if os.path.exists(B + 'media/case/manifest.json') else {}
for c in D.CASES:
    if want and c['slug'] not in want: continue
    m = MAN.setdefault(c['slug'], {'sheets': {}, 'versions': {}})
    if sys.argv[1] == 'sheets':
        od = B + f'media/case/{c["slug"]}/'; os.makedirs(od, exist_ok=True)
        for k, (p, cap) in enumerate([x for x in c['sheets'] if not isinstance(x, str)]):
            name = f'{k + 1:02d}-' + os.path.splitext(os.path.basename(p))[0].replace('.', '-').replace('_', '-').lower() + '.jpg'
            out = od + name; im = cv2.imread(p)
            if im is None: print('unreadable', p); continue
            h, w = im.shape[:2]
            if w > 1100: im = cv2.resize(im, (1100, int(h * 1100 / w)), interpolation=cv2.INTER_AREA)
            if not os.path.exists(out): cv2.imwrite(out, im, [cv2.IMWRITE_JPEG_QUALITY, 74])
            m['sheets'][p] = dict(file=f'media/case/{c["slug"]}/{name}', w=im.shape[1], h=im.shape[0], t=os.path.getmtime(p))
        for r in c.get('rounds', []):
            p = r['sheet']
            if p in m['sheets']: continue
            name = f'round{r["n"]}-' + os.path.splitext(os.path.basename(p))[0].replace('.', '-').replace('_', '-').lower() + '.jpg'
            im = cv2.imread(p); h, w = im.shape[:2]
            if w > 1100: im = cv2.resize(im, (1100, int(h * 1100 / w)), interpolation=cv2.INTER_AREA)
            if not os.path.exists(od + name): cv2.imwrite(od + name, im, [cv2.IMWRITE_JPEG_QUALITY, 74])
            m.setdefault('round_sheets', {})[p] = dict(file=f'media/case/{c["slug"]}/{name}', w=im.shape[1], h=im.shape[0], t=os.path.getmtime(p))
    else:
        od = B + f'media/v/{c["slug"]}/'; os.makedirs(od, exist_ok=True)
        for v in c['versions']:
            src = v.get('src')
            if not src or not os.path.exists(src): continue
            rel = REUSE.get(src) or f'media/v/{c["slug"]}/{v["id"]}.mp4'
            if src in REUSE: rel = 'media/' + rel
            out = B + rel
            if not os.path.exists(out):
                a = ['-c:a', 'aac', '-b:a', '64k', '-ac', '1'] if has_audio(src) else ['-an']
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', 'scale=640:-2,fps=24', '-c:v', 'libx264', '-crf', '31', '-preset', 'slow', '-pix_fmt', 'yuv420p', *a, '-movflags', '+faststart', out], check=True)
            poster = B + f'media/v/{c["slug"]}/{v["id"]}.jpg'
            d = dur(out)
            if not os.path.exists(poster):
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(min(d * .4, d - .2)), '-i', out, '-frames:v', '1', '-q:v', '5', poster], check=True)
            m['versions'][v['id']] = dict(file=rel, poster=f'media/v/{c["slug"]}/{v["id"]}.jpg', dur=round(d, 2), t=v.get('t') or os.path.getmtime(src), mb=round(os.path.getsize(out) / 1e6, 2))
            print(c['slug'], v['id'], m['versions'][v['id']], flush=True)
    json.dump(MAN, open(B + 'media/case/manifest.json', 'w'), indent=0)
print('ok', sys.argv[1])
