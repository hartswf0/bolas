import sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1]; OUT = sys.argv[2]
src = lambda n: cv2.imread(f"{S}/src/{n}.png")
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIFB = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

def grabcut(img, rect, fg_boxes=(), bg_boxes=(), it=6):
    m = np.zeros(img.shape[:2], np.uint8)
    bg = np.zeros((1, 65)); fg = np.zeros((1, 65))
    cv2.grabCut(img, m, rect, bg, fg, it, cv2.GC_INIT_WITH_RECT)
    for (x0, y0, x1, y1) in fg_boxes: m[y0:y1, x0:x1] = cv2.GC_FGD
    for (x0, y0, x1, y1) in bg_boxes: m[y0:y1, x0:x1] = cv2.GC_BGD
    cv2.grabCut(img, m, None, bg, fg, 3, cv2.GC_INIT_WITH_MASK)
    a = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(a)
    if n > 1:
        k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); a = np.where(lab == k, 255, 0).astype(np.uint8)
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return a

def rgba(img, a, crop):
    x0, y0, x1, y1 = crop
    rgb = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)
    return Image.fromarray(np.dstack([rgb, a[y0:y1, x0:x1]]), "RGBA")

def up(im, s):
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    r, g, b, a = im.split(); a = a.filter(ImageFilter.GaussianBlur(max(1.2, s * 0.9))).point(lambda v: max(0, min(255, (v - 128) * 2 + 128)))
    return Image.merge("RGBA", (r, g, b, a))

def plate(img, blur=0, box=None):
    rgb = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    if box: rgb = rgb.crop(box)
    rgb = rgb.resize((960, 720), Image.LANCZOS)
    return rgb.filter(ImageFilter.GaussianBlur(blur)) if blur else rgb

def frame(pic):  # 4:3 picture pillarboxed into 1280x720
    f = Image.new("RGB", (1280, 720), (8, 8, 8)); f.paste(pic, (160, 0)); return f

def shadow(base, cut, pos, off=(10, 14), r=10, op=110):
    p = 3 * r; a = cut.split()[3].point(lambda v: v * op // 255)
    A = Image.new("L", (cut.width + 2 * p, cut.height + 2 * p), 0); A.paste(a, (p, p))
    A = A.filter(ImageFilter.GaussianBlur(r)); sh = Image.new("RGBA", A.size, (0, 0, 0, 0)); sh.putalpha(A)
    L = Image.new("RGBA", base.size, (0, 0, 0, 0)); L.paste(sh, (pos[0] + off[0] - p, pos[1] + off[1] - p)); base.alpha_composite(L)

def caption(img, text, y=640, size=34):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(SERIF, size)
    w = d.textlength(text, font=f); x = (1280 - w) / 2
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2): d.text((x + dx, y + dy), text, font=f, fill=(0, 0, 0))
    d.text((x, y), text, font=f, fill=(250, 244, 222))

girl_src, car_src = src("girl"), src("car")
GPOLY=[(50,63),(58,72),(70,85),(77,100),(77,115),(73,128),(90,134),(105,140),(110,170),(114,205),(118,240),(2,240),(4,200),(6,170),(10,145),(30,134),(33,125),(30,105),(32,90),(42,74)]
CPOLY=[(0,8),(30,8),(136,22),(162,45),(160,100),(150,115),(112,133),(80,128),(20,105),(0,95)]
def polymask(shape, poly):
    m=np.zeros(shape[:2],np.uint8); cv2.fillPoly(m,[np.array(poly,np.int32)],255); return m
def refine(img, pm, band=5):
    k=np.ones((band*2+1,)*2,np.uint8)
    m=np.full(img.shape[:2],cv2.GC_BGD,np.uint8)
    m[cv2.dilate(pm,k)>0]=cv2.GC_PR_BGD; m[pm>0]=cv2.GC_PR_FGD; m[cv2.erode(pm,k)>0]=cv2.GC_FGD
    bg=np.zeros((1,65));fg=np.zeros((1,65))
    cv2.grabCut(img,m,None,bg,fg,5,cv2.GC_INIT_WITH_MASK)
    a=np.where((m==1)|(m==3),255,0).astype(np.uint8)
    return cv2.morphologyEx(a,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
ga = refine(girl_src, polymask(girl_src.shape, GPOLY))
ca = polymask(car_src.shape, CPOLY)
girl = rgba(girl_src, ga, (0, 58, 128, 240)); car = rgba(car_src, ca, (0, 0, 170, 140))
cv2.imwrite(f"{S}/girl_mask.png", ga); cv2.imwrite(f"{S}/car_mask.png", ca)

# ---- KF1: Prendre le tram (cutout collage) ----------------------------------
bg = plate(src("street"), blur=7, box=(0, 0, 320, 200)).convert("RGBA")
g = up(girl, 3.9)
gx, gy = 480 - g.width // 2 + 40, 720 - g.height + 40
shadow(bg, g, (gx, gy), off=(14, 10), r=16, op=90); bg.alpha_composite(g, (gx, gy))
c = up(car, 1.55)
cx, cy = gx + g.width // 2 - c.width // 2 + 35, gy + int(g.height * 0.56)
shadow(bg, c, (cx, cy), off=(8, 18), r=8, op=150); bg.alpha_composite(c, (cx, cy))
kf1 = frame(bg.convert("RGB")); caption(kf1, "« Le tram ? Je l'ai pris. »  — sur les genoux.")
kf1.save(f"{OUT}/kf-1.png")

# ---- KF2: La queue fait mur (match cut hinge, straight archive) -------------
left = plate(src("carq"), box=(0, 0, 320, 240)); right = plate(src("plaza"), box=(0, 0, 320, 240))
pic = Image.new("RGB", (960, 720))
pic.paste(left.crop((0, 0, 480, 720)), (0, 0)); pic.paste(right.crop((480, 0, 960, 720)), (480, 0))
d = ImageDraw.Draw(pic)
d.rectangle((477, 0, 483, 720), fill=(240, 236, 220))
# match anchor: the queue line, carried across the cut at the same height
for x in (0, 952): d.rectangle((x, 552, x + 8, 568), fill=(255, 120, 40))
fm = ImageFont.truetype(MONO, 20)
d.text((20, 20), "OUT  12.40 s  la file monte", font=fm, fill=(255, 140, 60))
d.text((500, 20), "IN  12.44 s  la file barre", font=fm, fill=(255, 140, 60))
kf2 = frame(pic); caption(kf2, "« Faire la queue » : la file d'attente devient le mur.")
kf2.save(f"{OUT}/kf-2.png")

# ---- KF3: Le ticket troue (handmade prop over foraged plate) ----------------
bg = plate(src("street2"), blur=9, box=(0, 0, 320, 240)).convert("RGBA")
T = Image.new("RGBA", (620, 300), (0, 0, 0, 0)); td = ImageDraw.Draw(T)
td.rounded_rectangle((0, 0, 619, 299), 10, fill=(226, 205, 150, 255))
rng = np.random.default_rng(3)  # paper fibre: real per-pixel noise in the card stock
fib = (rng.normal(0, 7, (300, 620))).astype(np.int16)
arr = np.array(T).astype(np.int16); arr[..., :3] += fib[..., None]; arr = np.clip(arr, 0, 255).astype(np.uint8)
T = Image.fromarray(arr, "RGBA"); td = ImageDraw.Draw(T)
td.rectangle((0, 40, 619, 92), fill=(138, 72, 40, 255))
td.text((24, 46), "MÉTRO  ·  2e CL.", font=ImageFont.truetype(SANSB, 36), fill=(236, 220, 176))
td.text((24, 112), "VALABLE POUR UN SEUL VOYAGE", font=ImageFont.truetype(SANSB, 22), fill=(90, 50, 30))
td.text((24, 146), "N° 0 6 0 0 1 9 6 0", font=ImageFont.truetype(MONO, 26), fill=(90, 50, 30))
td.text((24, 196), "Grève : se présenter à l'autobus.", font=ImageFont.truetype(SERIF, 26), fill=(90, 50, 30))
td.text((24, 236), "Doukipudonktan ?", font=ImageFont.truetype(SERIF, 26), fill=(150, 70, 40))
# the punch hole (real hole in the alpha) reveals the vehicle behind the card
hx, hy, hr = 500, 190, 70
td.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=(0, 0, 0, 0))
HM = Image.new("L", T.size, 0); ImageDraw.Draw(HM).ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=255)
T = T.rotate(-7, resample=Image.BICUBIC, expand=True); HM = np.array(HM.rotate(-7, expand=True))
hys, hxs = np.nonzero(HM > 128); hcx, hcy = int(hxs.mean()), int(hys.mean())
tx, ty = 480 - T.width // 2, 360 - T.height // 2 - 20
# vehicle seen through the hole: the far tram on its turntable, small and sharp
far = Image.fromarray(cv2.cvtColor(car_src, cv2.COLOR_BGR2RGB)).resize((480, 360), Image.LANCZOS).convert("RGBA")
hole_c = (tx + hcx, ty + hcy)
hm = Image.new("L", bg.size, 0); ImageDraw.Draw(hm).ellipse((hole_c[0]-hr-4, hole_c[1]-hr-4, hole_c[0]+hr+4, hole_c[1]+hr+4), fill=255)
layer = Image.new("RGBA", bg.size, (0,0,0,0)); layer.alpha_composite(far, (hole_c[0] - 150, hole_c[1] - 110))
layer.putalpha(Image.fromarray(np.minimum(np.array(layer.split()[3]), np.array(hm)))); bg.alpha_composite(layer)
shadow(bg, T, (tx, ty), off=(16, 22), r=14, op=140)
bg.alpha_composite(T, (tx, ty))
kf3 = frame(bg.convert("RGB")); caption(kf3, "Le ticket, deuxième lecture : une lunette pour viser le tram.")
kf3.save(f"{OUT}/kf-3.png")

# ---- board --------------------------------------------------------------
ref = Image.open(sys.argv[3]).convert("RGB"); ref = ref.resize((int(ref.width * 405 / ref.height), 405))
cell = 720; names = ["REFERENCE  Zazie dans le metro (1960)", "1  Prendre le tram", "2  La queue fait mur", "3  Le ticket troue"]
ims = [ref] + [Image.open(f"{OUT}/kf-{i}.png").resize((720, 405)) for i in (1, 2, 3)]
B = Image.new("RGB", (2 * cell + 30, 2 * (405 + 50) + 20), (18, 18, 18)); bd = ImageDraw.Draw(B)
fl = ImageFont.truetype(SANSB, 22)
for i, (im, n) in enumerate(zip(ims, names)):
    x = 10 + (i % 2) * (cell + 10); y = 10 + (i // 2) * (455)
    B.paste(im, (x + (cell - im.width) // 2, y)); bd.text((x, y + 412), n, font=fl, fill=(240, 230, 210))
B.save(f"{OUT}/board.jpg", quality=90)
print(B.size)
