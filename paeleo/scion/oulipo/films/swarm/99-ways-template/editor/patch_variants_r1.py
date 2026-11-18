"""Editor r1: repair-round changes to variants/build_variants.py (original kept as editor/build_variants.r0.py).
D1: the forgetting line in the production's own words (B.FORGOT).
D2: the shop's neon sign is covered by a HANDMADE 'TICKET OFFICE' card hung inside the glass; the awning is covered
by a HANDMADE station nameboard 'RANDOLPH'; the visitor's two lines move into the panels where she stands (V1, V4)
with tails to her mouth (her mouth is open in the Bubley photograph)."""
p = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways-template/variants/build_variants.py'
s = open('/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways-template/editor/build_variants.r0.py').read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:70], s.count(a))
    s = s.replace(a, b)


rep('''["What the hell", "was I looking", "for, anyway?"], 68,''', '''B.FORGOT, 64,''')
rep('''def bp(Mplate, p):            # Bubley master px -> panel px
    return apply(Mplate, p)''', '''def bp(Mplate, p):            # Bubley master px -> panel px
    return apply(Mplate, p)


VIS_MOUTH = (2985, 1710)      # her mouth, Bubley master px (open: she is speaking in the photograph)
NAMEBOARD = [(880, 430), (4600, 430), (4600, 812), (880, 812)]   # over the shop awning (master px)


def ticket_board(P, poly_px, seed):
    """HANDMADE (r1): a white card lettered TICKET OFFICE in the page hand, hung inside the glass where the shop's
    neon sign was; it covers the neon so the front reads as a ticket window."""
    shp = P.c.shape[:2]
    q = np.array(poly_px, np.float64)
    c = q.mean(0)
    q = c + (q - c) * np.array([0.92, 0.86])
    m = B.fillmask(shp, q)
    P.paper("ticket_board", m, (243, 241, 234))
    hgt = q[:, 1].max() - q[:, 1].min()
    ink = np.zeros(shp, np.uint8)
    ink = B.lettering_onto(ink, ["TICKET"], hgt * 0.30, (c[0], c[1] - hgt * 0.20), 0, seed, weight=0.17)
    ink = B.lettering_onto(ink, ["OFFICE"], hgt * 0.30, (c[0], c[1] + hgt * 0.22), 0, seed + 1, weight=0.17)
    P.ink("ticket_board.ink", ink)


def nameboard(P, Mp, seed):
    """HANDMADE (r1): the station nameboard, black card with the name cut out of white paper strokes, laid over the
    shop awning at the head of the station front (V1 and V4, the same camera)."""
    shp = P.c.shape[:2]
    q = [bp(Mp, p) for p in NAMEBOARD]
    m = B.fillmask(shp, q)
    P.paper("nameboard.margin", B.scissor(m, 8), PAPER_CUT)
    P.over("nameboard", np.array([30, 29, 28], np.float32), m.astype(np.float32) / 255)
    qa = np.array(q)
    hgt = qa[:, 1].max() - max(0.0, qa[:, 1].min())
    cx = (qa[:, 0].min() + min(qa[:, 0].max(), shp[1])) / 2
    cy = (max(0.0, qa[:, 1].min()) + qa[:, 1].max()) / 2
    ink = np.zeros(shp, np.uint8)
    ink = B.lettering_onto(ink, ["RANDOLPH"], hgt * 0.50, (cx, cy + hgt * 0.04), 0, seed, weight=0.15)
    P.ink("nameboard.letters", ink, np.array([238, 236, 228], np.float32))''')
# V1: no neon decal; card; nameboard; her question
rep('''    through_glass(P, I.c, gm, plate, transmission_top=0.62, transmission_bottom=0.40, decal=neon_decal(plate, [bp(Mp, p) for p in SIGN]))
    lay_visitor(P, Mp)                   # she is a cut piece laid back on her own place at the window
    SPEECH["V1"] = []''', '''    through_glass(P, I.c, gm, plate, transmission_top=0.62, transmission_bottom=0.40)
    ticket_board(P, [bp(Mp, p) for p in SIGN], 301)
    nameboard(P, Mp, 311)
    lay_visitor(P, Mp)                   # she is a cut piece laid back on her own place at the window
    mouth = bp(Mp, VIS_MOUTH)
    b = B.balloon(P, "b_what_time", ["What time", "is it?"], 66, (mouth[0] + 400, 250), (mouth[0] + 30, mouth[1] - 20), 221,
                  tail_w=0.24, bend=-0.10)
    b.update(speaker="VISITOR", tail_target="her mouth (she stands at the ticket window, on the platform)")
    SPEECH["V1"] = [b]
    FK["V1"] = {"visitor_mouth_px": list(map(float, mouth))}''')
rep('''    through_glass(P, I.c, gm, plate, decal=neon_decal(plate, [bp(Mp, p) for p in SIGN]))
    b = B.balloon(P, "b_what_time", ["What time", "is it?"], 66, (700, 430), (w * 0.52, h + 30), 221, tail_w=0.26, bend=0.10)
    b.update(speaker="VISITOR", tail_target="off-panel bottom: the viewpoint is hers")
    SPEECH["V2"] = [b]''', '''    through_glass(P, I.c, gm, plate)
    ticket_board(P, [bp(Mp, p) for p in SIGN], 302)
    SPEECH["V2"] = []              # r1: her question is spoken in V1, where she is seen''')
rep('''    through_glass(P, I.c, gm, plate, transmission_top=0.84, transmission_bottom=0.62, decal=neon_decal(plate, [bp(Mp, p) for p in SIGN]))''',
    '''    through_glass(P, I.c, gm, plate, transmission_top=0.84, transmission_bottom=0.62)
    ticket_board(P, [bp(Mp, p) for p in SIGN], 303)''')
rep('''    b2 = B.balloon(P, "b_thanks", ["Thanks!"], 62, (780, 700), (w * 0.60, h + 30), 261, tail_w=0.30, bend=0.10)
    b2.update(speaker="VISITOR", tail_target="off-panel bottom: hers")
    SPEECH["V3"] = [b1, b2]''', '''    SPEECH["V3"] = [b1]            # r1: her thanks is spoken in V4, where she is seen leaving''')
rep('''    through_glass(P, I.c, gm, plate, transmission_top=0.62, transmission_bottom=0.40, decal=neon_decal(plate, [bp(Mp, p) for p in SIGN]))
    # she walks off''', '''    through_glass(P, I.c, gm, plate, transmission_top=0.62, transmission_bottom=0.40)
    ticket_board(P, [bp(Mp, p) for p in SIGN], 304)
    nameboard(P, Mp, 311)
    # she walks off''')
rep('''    lay_visitor(P, Mv)
    SPEECH["V4"] = []''', '''    lay_visitor(P, Mv)
    mouth = apply(Mv, VIS_MOUTH)
    b = B.balloon(P, "b_thanks", ["Thanks!"], 64, (mouth[0] + 330, mouth[1] - 300), (mouth[0] + 24, mouth[1] - 14), 261,
                  tail_w=0.28, bend=0.10)
    b.update(speaker="VISITOR", tail_target="her mouth, as she leaves along the platform")
    SPEECH["V4"] = [b]
    FK["V4"] = {"visitor_mouth_px": list(map(float, mouth))}''')
open(p, 'w').write(s)
print("patched")
