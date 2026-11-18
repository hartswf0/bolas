"""Cut the foraged LoC figures once (GrabCut + hand hints) and cache masks; writes previews."""
import sys; sys.path.insert(0, '.')
from common import *
S = '/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad'
os.makedirs(OUT + '/src/cache', exist_ok=True)
def run(name, f, rect, fg, bg, clip=()):
    g = grey(SRC + '/loc/' + f)
    m = grabcut(g, rect, fg, bg)
    for p in clip: cv2.fillPoly(m, [np.array(p, np.int32)], 0)
    np.save(OUT + f'/src/cache/{name}.npy', m)
    x0, y0, x1, y1 = rect
    prev = np.where(m > 0, g, g * .25 + 160)[y0:y1, x0:x1]
    Image.fromarray(prev.astype(np.uint8)).save(f'{S}/cut_{name}.png')
# Luciana: centre woman with the apple (OWI-23899-D)
run('luciana', '8d16982v.jpg', (372, 36, 672, 468),
    fg=[[(540, 90), (640, 70), (690, 120), (660, 250), (600, 300), (520, 290), (510, 200)],
        [(590, 230), (655, 230), (660, 300), (600, 330)],
        [(470, 200), (540, 200), (560, 300), (520, 380), (470, 360)],
        [(430, 172), (505, 158), (505, 345), (402, 345), (398, 240)]],
    bg=[[(372, 250), (384, 250), (384, 470), (372, 470)], [(372, 36), (480, 36), (420, 150), (372, 190)], [(655, 300), (672, 280), (672, 468), (640, 468)],
        [(672, 36), (700, 36), (700, 468), (672, 468)]],
    clip=[[(372, 36), (507, 36), (507, 131), (500, 158), (392, 181), (372, 186)]])
# Renzo: seated young man, far left on the curb (8c00283v)
run('renzo', '8c00283v.jpg', (112, 302, 338, 640),
    fg=[[(205, 330), (250, 320), (262, 380), (240, 400), (210, 395)],
        [(190, 410), (290, 400), (300, 470), (200, 480)]],
    bg=[[(325, 302), (338, 302), (338, 640), (320, 640)]])
