"""Beat-5 pair still (S1 11.0 s vs S5c 58.234 s), aesthetic side-by-side vs styleBook.webp with measured dE76,
INV-DOOR hash check over the rendered test shot, and a Reiniger S3 proof frame.  Run: python3 stills.py"""
import sys, json, subprocess, io
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import es_lib as L
import test_shot_s5c as TS

X = json.load(open(HERE / 'exposure.json'))
A = json.load(open(HERE.parent / 'incident' / 'anthology.json'))
OUT = L.MEDIA
V = TS.V

def s1_frame(t):
    s1 = X['S1']; k = int(round(t * 24))
    img = L.page(1).convert('RGBA')
    img.alpha_composite(L.ghost('Gare', (300, -170), 560).crop((0, 0, L.W, L.H)))
    L.set_title(img, [('Le', L.RED), ('registre', L.BLACK)], x=30, base=70, size=48, seed=8)
    st = Image.open(L.SRC / 'forager-cutout-rigger' / 'station_berlin1927.png')
    img.alpha_composite(L.deckle(st, (250, 180)), (34, 108))
    L.paste_door(img, *s1['door_xy'])
    bx = s1['bench']; img.alpha_composite(L.bench_eye(bx['x'], bx['y'], bx['w']))
    if t >= s1['key_on_bench']['from_film_t']:
        kk = L.key(70); kb = s1['key_on_bench']; img.alpha_composite(L.with_shadow(kk, off=(1, 2), blur=2, alpha=0.3), (kb['x'], kb['y'] - kk.size[1]))
    f = s1['frames'][str((k // 2) * 2)]
    V.draw(img, tuple(f['hip']), f['sc'], dict(lean=f['lean'], head=f['head'], arm=f['arm'], hem=f['hem'],
                                              legs={'near': tuple(f['near']), 'far': tuple(f['far'])}))
    d = ImageDraw.Draw(img); y = 104
    for c in A['variants']['baseline']['claims']:
        if c['t_in'] <= t and c['id'] != 'baseline.7':
            txt = c['text'] + (' La porte de service reste fermée.' if c['id'] == 'baseline.6' else '')
            d.text((545, y), txt if len(txt) < 30 else txt[:30].rsplit(' ', 1)[0], font=L.font(L.SERIF_R, 16), fill=L.BLACK)
            if len(txt) >= 30:
                y += 22; d.text((545, y), txt[len(txt[:30].rsplit(' ', 1)[0]) + 1:], font=L.font(L.SERIF_R, 16), fill=L.BLACK)
            y += 26
    L.band(img, 'Le registre', 'Exercice 1 · sans opérateur', '18:06')
    L.strip(img, TS.cells(), ring=4)
    return img.convert('RGB')

def measure(img, page_box, band_box):
    a = np.asarray(img.convert('RGB'))
    pg = a[page_box[1]:page_box[3], page_box[0]:page_box[2]].reshape(-1, 3)
    bd = a[band_box[1]:band_box[3], band_box[0]:band_box[2]].reshape(-1, 3)
    pm, bm = np.median(pg, 0), np.median(bd, 0)
    return pm, bm

def red_median(img, box):
    a = np.asarray(img.convert('RGB'))[box[1]:box[3], box[0]:box[2]].reshape(-1, 3).astype(int)
    m = (a[:, 0] > 150) & (a[:, 1] < 90) & (a[:, 2] < 60)
    return np.median(a[m], 0) if m.sum() > 20 else None

def frame_of(mp4, t):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', str(mp4), '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
    return Image.open(io.BytesIO(raw)).convert('RGB')

if __name__ == '__main__':
    loc = X['S5c']['pair_frame']['local_t']
    a = s1_frame(11.0); b = TS.render(loc, int(round(loc * 24))).convert('RGB')
    a.save(OUT / 's1-baseline-11.0.png'); b.save(OUT / 's5c-58.234.png')
    pair = Image.new('RGB', (1920 + 20, 600), (30, 26, 20)); pair.paste(a, (0, 40)); pair.paste(b, (980, 40))
    d = ImageDraw.Draw(pair)
    d.text((10, 10), 'S1 Le registre, 11.0 s: eye level, the key just placed, plain register', font=L.font(L.SANS, 18), fill=(255, 255, 255))
    d.text((990, 10), 'S5c Narré par la clé, 58.234 s: key height, same visitor, same bench colours, same door', font=L.font(L.SANS, 18), fill=(255, 255, 255))
    pair.save(OUT / 'beat5-pair.jpg', quality=90)
    # ---- aesthetic side-by-side
    ref = Image.open(L.ROOT / 'assets' / 'references' / 'styleBook.webp').convert('RGB')
    rp, rb = measure(ref, (20, 20, 120, 140), (40, 470, 360, 560))
    rr = red_median(ref, (110, 90, 300, 190))
    frames = {'S5c 58.234': b, 'S5c 63.0 (empty bench)': TS.render(6.833, 164).convert('RGB'), 'S1 11.0': a}
    rows = []
    for name, f in frames.items():
        pm, bm = measure(f, (660, 200, 770, 245) if 'S1' not in name else (300, 400, 420, 420), (300, 500, 700, 520))
        fr = red_median(f, (20, 20, 380, 90))
        g = np.asarray(f)[0:330, 40:300]
        rows.append(dict(frame=name, page=('#%02x%02x%02x' % tuple(int(v) for v in pm)), dE_page=round(L.dE(pm, (253, 219, 140)), 2),
                         band=('#%02x%02x%02x' % tuple(int(v) for v in bm)), dE_band=round(L.dE(bm, (142, 132, 123)), 2),
                         title_red=('#%02x%02x%02x' % tuple(int(v) for v in fr)) if fr is not None else None,
                         dE_red=round(L.dE(fr, (214, 40, 10)), 2) if fr is not None else None))
    ghostL = float(L.lab(L.GHOST)[0]); pageL = float(L.lab(L.PAGE)[0])
    meas = dict(reference=dict(page=('#%02x%02x%02x' % tuple(int(v) for v in rp)), band=('#%02x%02x%02x' % tuple(int(v) for v in rb)),
                               red=('#%02x%02x%02x' % tuple(int(v) for v in rr)) if rr is not None else None,
                               dE_ref_page_vs_target=round(L.dE(rp, (253, 219, 140)), 2)),
                frames=rows, ghost_L=round(ghostL, 1), page_L=round(pageL, 1), ghost_lighter_than_page=ghostL > pageL,
                visitor_chroma_before_tint=None)
    wk = np.asarray(Image.open(L.PM / 'dl' / 'homme_marchant_1920.jpg').convert('RGB'), np.float32)
    meas['visitor_source_chroma'] = round(float(np.abs(wk - wk.mean(2, keepdims=True)).mean()), 3)
    meas['visitor_source_mode'] = Image.open(L.PM / 'dl' / 'homme_marchant_1920.jpg').mode
    rh = ref.resize((int(ref.size[0] * 540 / ref.size[1]), 540))
    sbs = Image.new('RGB', (rh.size[0] + 960 + 20, 540 + 170), (30, 26, 20)); sbs.paste(rh, (0, 0)); sbs.paste(b, (rh.size[0] + 20, 0))
    d = ImageDraw.Draw(sbs); y = 548
    d.text((10, y), 'styleBook.webp (reference, resized; never pasted into the film)  |  test-shot frame 58.234 s', font=L.font(L.SANS, 16), fill=(255, 255, 255)); y += 24
    for r in rows:
        d.text((10, y), f"{r['frame']}: page {r['page']} dE76 {r['dE_page']} (<=10)  band {r['band']} dE76 {r['dE_band']} (<=10)  title red {r['title_red']} dE76 {r['dE_red']} (<=15)", font=L.font(L.MONO, 14), fill=(255, 255, 255)); y += 22
    d.text((10, y), f"ghost #fdefb1 L*={meas['ghost_L']} > page L*={meas['page_L']}  |  Rol 57642 source mode {meas['visitor_source_mode']}, chroma {meas['visitor_source_chroma']} (<6)", font=L.font(L.MONO, 14), fill=(255, 255, 255))
    sbs.save(OUT / 'aesthetic-side-by-side.jpg', quality=90)
    # ---- INV-DOOR over the rendered test shot (pre-encode frames from the renderer, door box per frame)
    hs = set()
    for k in range(0, X['S5c']['frames'], 12):
        t = k / 24
        img = TS.render(t, k).convert('RGB')
        dx = X['S5c']['door_xy'][0] + TS.DOOR_SIGN * TS.ix(0.55 * TS.cam(t))
        box = (dx, X['S5c']['door_xy'][1], dx + 150, X['S5c']['door_xy'][1] + 300)
        if box[2] <= L.W:
            hs.add(L.door_hash(img, box, occluded_below=X['S5c']['bench_top'] - 14))
    meas['inv_door'] = dict(frames_checked=len(range(0, X['S5c']['frames'], 12)), distinct_hashes_where_fully_in_frame=len(hs), hashes=sorted(hs))
    # ---- S3 Reiniger proof frame: silhouette of the same rig behind the frosted pane, bell head-up frame
    s3 = X['S3']; sil = V.silhouette_pieces(); pane = L.frosted_pane((360, 250))
    sheet = Image.new('RGB', (3 * 380, 290), (30, 26, 20))
    for i, kk in enumerate([s3['bell_onset_frame'] - 2, s3['bell_onset_frame'] + 2, s3['bell_onset_frame'] + 6]):
        k2 = str((kk // 2) * 2); fr = s3['frames'].get(k2) or s3['frames'][str(min(int(x) for x in s3['frames']))]
        head = s3['bell_head_on_ones'].get(str(kk), fr['head'])
        lay = Image.new('RGBA', (L.W, L.H), (0, 0, 0, 0))
        sil.draw(lay, tuple(fr['hip']), fr['sc'], dict(lean=fr['lean'], head=head, arm=fr['arm'], hem=fr['hem'],
                 legs={'near': tuple(fr['near']), 'far': tuple(fr['far'])}), shadow=False)
        px, py = s3['pane']['x'], s3['pane']['y']
        m = lay.getchannel('A').crop((px, py, px + 360, py + 250))
        lit = L.shadow_through_glass(pane, m, blur=fr['blur_px'])
        g = L.guichet((440, 330), (40, 62, 400, 312))
        cardi = Image.new('RGBA', (440, 330), (0, 0, 0, 0)); cardi.paste(lit, (40, 62)); cardi.alpha_composite(g)
        cardi = cardi.resize((360, 270)); sheet.paste(cardi.convert('RGB'), (10 + i * 380, 10))
    sheet.save(OUT / 's3-reiniger-proof.jpg', quality=90)
    json.dump(meas, open(OUT / 'measurements.json', 'w'), indent=1)
    print(json.dumps(meas, indent=1))
