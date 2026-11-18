import sys, time, numpy as np, cv2
sys.path.insert(0, '.')
import lightbox as lb, e4
S = '/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/'
t0 = time.time(); page = lb.make_page(); np.save(S + 'page.npy', page.astype(np.float32)); print('page', time.time() - t0)
sh = e4.Shot(page)
ts = [float(x) for x in sys.argv[1:]]
ims = []
for t in ts:
    t1 = time.time(); im = sh.render(t); print(t, time.time() - t1)
    im = cv2.resize(im, (1280, 720), interpolation=cv2.INTER_AREA)
    ims.append(im)
rows = [np.hstack(ims[i:i + 2]) if i + 1 < len(ims) else np.hstack([ims[i], np.zeros_like(ims[i])]) for i in range(0, len(ims), 2)]
cv2.imwrite(S + 'stills.jpg', cv2.cvtColor(np.vstack(rows), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
for r in sh.log: print({k: r[k] for k in ('t', 'drawing', 'dial_area_px', 'cuff_x', 'pin_residual')}, r['right'].get('idx_residual'), r['right'].get('joint_deg'))
