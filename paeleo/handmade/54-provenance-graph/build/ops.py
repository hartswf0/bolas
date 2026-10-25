"""The operation vocabulary. Each op is pure: (parent outputs, params) -> image or data. Registered with a version, so a
change of behaviour changes every downstream signature."""
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops


def poly_alpha(size, polys, ss=4, blur=0.0):
    W, H = size
    m = Image.new('L', (W * ss, H * ss), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon([(x * ss, y * ss) for x, y in p], fill=255)
    m = m.resize((W, H), Image.LANCZOS)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return m


def op_sam_mask(frame, masks, key, ss=4):
    return poly_alpha(frame.size, masks[str(key)], ss)


def op_cutout(frame, alpha):
    im = frame.convert('RGBA')
    im.putalpha(alpha)
    return im


def op_cut(rgba, poly, mode='keep', feather=0.0):
    """intersect (keep) or subtract (remove) a drawn polygon from a piece's alpha; feather softens the cut line."""
    m = poly_alpha(rgba.size, poly['polys'], 4, feather)
    a = np.asarray(rgba.getchannel('A'), float)
    k = np.asarray(m, float) / 255
    a = a * (k if mode == 'keep' else 1 - k)
    out = rgba.copy()
    out.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
    return out


def op_trim(rgba, pad=2):
    """crop to the alpha bbox; the offset is recorded by the caller as the piece origin."""
    bb = rgba.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
    return rgba.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad))


def op_crop(img, box):
    return img.crop(tuple(box))


def op_flip(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def op_erode_alpha(rgba, px=1):
    a = rgba.getchannel('A').filter(ImageFilter.MinFilter(2 * px + 1)).filter(ImageFilter.GaussianBlur(0.6))
    out = rgba.copy(); out.putalpha(a)
    return out


def op_recolor(rgba, ramp, gain=1.0, lift=0.0):
    """gradient map: luminance -> a drawn colour ramp (list of [pos, [r,g,b]]). gain/lift are contrast controls."""
    rgb = np.asarray(rgba.convert('RGB'), float) / 255
    L = (0.3 * rgb[..., 0] + 0.59 * rgb[..., 1] + 0.11 * rgb[..., 2])
    L = np.clip((L - 0.5) * gain + 0.5 + lift, 0, 1)
    stops = ramp['stops']
    xs = np.array([s[0] for s in stops]); cs = np.array([s[1] for s in stops], float)
    out = np.stack([np.interp(L, xs, cs[:, c]) for c in range(3)], -1)
    im = Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    if rgba.mode == 'RGBA':
        im.putalpha(rgba.getchannel('A'))
    return im


def op_texture_shape(tex, poly, size, offset=(0, 0)):
    """fill a drawn polygon with fur cut from a texture (a crop of the archive frame): a made piece with found surface."""
    W, H = size
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    t = tex.convert('RGBA').resize((W, H), Image.BICUBIC) if tex.size != (W, H) else tex.convert('RGBA')
    base.paste(t, (0, 0))
    base.putalpha(poly_alpha((W, H), poly['polys'], 4, 0.6))
    return base


def op_strokes(drawing, size, width, color, pad=8):
    """render a Quick, Draw! drawing (strokes [[x...],[y...]] in 0..255) as lines, scaled into size."""
    W, H = size
    ss = 4
    im = Image.new('RGBA', (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    st = drawing['drawing']
    xs = [x for s in st for x in s[0]]; ys = [y for s in st for y in s[1]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    k = min((W - 2 * pad) / max(1, x1 - x0), (H - 2 * pad) / max(1, y1 - y0))
    ox = (W - (x1 - x0) * k) / 2; oy = (H - (y1 - y0) * k) / 2
    for s in st:
        pts = [((ox + (x - x0) * k) * ss, (oy + (y - y0) * k) * ss) for x, y in zip(s[0], s[1])]
        if len(pts) > 1:
            d.line(pts, fill=tuple(color) + (255,), width=int(width * ss), joint='curve')
        for p in (pts[0], pts[-1]):
            r = width * ss / 2
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=tuple(color) + (255,))
    return im.resize((W, H), Image.LANCZOS)


def op_fill_strokes(drawing, size, color, pad=8):
    """a Quick, Draw! outline filled solid (its closed loops), for a silhouette."""
    W, H = size
    st = drawing['drawing']
    xs = [x for s in st for x in s[0]]; ys = [y for s in st for y in s[1]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    k = min((W - 2 * pad) / max(1, x1 - x0), (H - 2 * pad) / max(1, y1 - y0))
    ox = (W - (x1 - x0) * k) / 2; oy = (H - (y1 - y0) * k) / 2
    polys = [[(ox + (x - x0) * k, oy + (y - y0) * k) for x, y in zip(s[0], s[1])] for s in st if len(s[0]) > 2]
    a = poly_alpha((W, H), polys, 4)
    im = Image.new('RGBA', (W, H), tuple(color) + (255,))
    im.putalpha(a)
    return im


def op_luma_gate(rgba, lo, soft=0.05):
    """remove dark pixels (cast shadow wrongly inside a SAM mask): alpha *= smoothstep(lo, lo+soft, luma)."""
    rgb = np.asarray(rgba.convert('RGB'), float) / 255
    L = 0.3 * rgb[..., 0] + 0.59 * rgb[..., 1] + 0.11 * rgb[..., 2]
    k = np.clip((L - lo) / soft, 0, 1)
    a = np.asarray(rgba.getchannel('A'), float) * k
    out = rgba.copy(); out.putalpha(Image.fromarray(a.astype(np.uint8)))
    return out


def op_largest_blob(rgba, thr=40):
    """keep the largest connected alpha region (drop SAM islands), 4-connected flood fill in numpy."""
    a = np.asarray(rgba.getchannel('A'))
    m = a > thr
    H, W = m.shape
    lab = np.zeros((H, W), np.int32); n = 0; sizes = {}
    for y in range(H):
        for x in range(W):
            if m[y, x] and not lab[y, x]:
                n += 1; st = [(y, x)]; lab[y, x] = n; c = 0
                while st:
                    yy, xx = st.pop(); c += 1
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        y2, x2 = yy + dy, xx + dx
                        if 0 <= y2 < H and 0 <= x2 < W and m[y2, x2] and not lab[y2, x2]:
                            lab[y2, x2] = n; st.append((y2, x2))
                sizes[n] = c
    if not sizes:
        return rgba
    big = max(sizes, key=sizes.get)
    keep = Image.fromarray(((lab == big) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
    out = rgba.copy(); out.putalpha(ImageChops.multiply(rgba.getchannel('A'), keep))
    return out


def op_scale(img, k):
    return img.resize((max(1, round(img.size[0] * k)), max(1, round(img.size[1] * k))), Image.LANCZOS)


def op_silhouette(rgba, color):
    im = Image.new('RGBA', rgba.size, tuple(color) + (255,))
    im.putalpha(rgba.getchannel('A'))
    return im


def op_grade(img, mul, add=(0, 0, 0), sat=1.0):
    a = np.asarray(img.convert('RGB'), float)
    g = a.mean(-1, keepdims=True)
    a = g + (a - g) * sat
    a = a * np.array(mul) + np.array(add)
    out = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGB')
    if img.mode == 'RGBA':
        out = out.convert('RGBA'); out.putalpha(img.getchannel('A'))
    return out


def register_all(G):
    G.register('sam_mask', 1, op_sam_mask, 'rasterise the documented SAM polygons of one frame into an alpha matte (4x supersampled)')
    G.register('cutout', 1, op_cutout, 'apply an alpha matte to a frame: the crop mask becomes the piece edge')
    G.register('cut', 1, op_cut, 'segment a piece along a drawn cut polygon (keep or remove), optionally feathered')
    G.register('trim', 1, op_trim, 'crop a piece to its alpha bounding box')
    G.register('crop', 1, op_crop, 'crop a rectangle')
    G.register('flip', 1, op_flip, 'mirror left-right (used to change which way a whole view faces, never as a turn)')
    G.register('erode_alpha', 1, op_erode_alpha, 'shrink a matte edge to drop background halo')
    G.register('recolor', 1, op_recolor, 'gradient-map luminance onto a drawn colour ramp (the dusk palette)')
    G.register('texture_shape', 1, op_texture_shape, 'fill a drawn polygon with surface cut from an archive crop')
    G.register('strokes', 1, op_strokes, 'render Quick, Draw! strokes as lines')
    G.register('fill_strokes', 1, op_fill_strokes, 'fill Quick, Draw! loops solid')
    G.register('luma_gate', 1, op_luma_gate, 'drop dark (shadow) pixels from inside a SAM matte')
    G.register('largest_blob', 1, op_largest_blob, 'keep the largest connected region of a matte')
    G.register('scale', 1, op_scale, 'resample by a factor (Lanczos)')
    G.register('silhouette', 1, op_silhouette, 'fill a matte with one colour (a shadow figure)')
    G.register('grade', 1, op_grade, 'per-channel multiply/add and saturation')


def op_draw(shapes, size, bg=(0, 0, 0, 0), ss=2):
    """vector shapes drawn by this swarm (data in a drawn node): poly / rect / line / ellipse, RGBA colours."""
    W, H = size
    im = Image.new('RGBA', (W * ss, H * ss), tuple(bg))
    d = ImageDraw.Draw(im)
    for s in shapes['shapes']:
        t = s['t']
        P = [(x * ss, y * ss) for x, y in s.get('pts', [])]
        fill = tuple(s['fill']) if s.get('fill') else None
        ol = tuple(s['outline']) if s.get('outline') else None
        w = int(round(s.get('w', 1) * ss))
        if t == 'poly':
            d.polygon(P, fill=fill, outline=ol)
        elif t == 'rect':
            d.rectangle([P[0], P[1]], fill=fill, outline=ol, width=w)
        elif t == 'line':
            d.line(P, fill=ol or fill, width=w, joint='curve')
        elif t == 'ellipse':
            d.ellipse([P[0], P[1]], fill=fill, outline=ol, width=w)
    return im.resize((W, H), Image.LANCZOS)


def op_vgradient(stops, size):
    W, H = size
    ys = np.linspace(0, 1, H)
    xs = np.array([s[0] for s in stops['stops']]); cs = np.array([s[1] for s in stops['stops']], float)
    col = np.stack([np.interp(ys, xs, cs[:, c]) for c in range(cs.shape[1])], -1)
    a = np.repeat(col[:, None, :], W, 1)
    mode = 'RGBA' if cs.shape[1] == 4 else 'RGB'
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), mode).convert('RGBA')


def op_composite(*parents, size, placements, bg=(0, 0, 0, 0)):
    """assemble placed parents into one plate. placements: [[parent_index, 3x3 matrix rows, opacity]]."""
    import compose
    canvas = Image.new('RGBA', tuple(size), tuple(bg))
    for idx, M, op in placements:
        compose.place(canvas, parents[idx].convert('RGBA'), np.array(M, float), op)
    return canvas


def op_luma_alpha(img, lo=0.3, hi=0.9, opacity=1.0):
    """alpha from luminance (for clouds, glows): the brighter, the more present."""
    rgb = np.asarray(img.convert('RGB'), float) / 255
    L = 0.3 * rgb[..., 0] + 0.59 * rgb[..., 1] + 0.11 * rgb[..., 2]
    a = np.clip((L - lo) / (hi - lo), 0, 1) * 255 * opacity
    out = img.convert('RGBA'); out.putalpha(Image.fromarray(a.astype(np.uint8)))
    return out


def op_radial(size, color, falloff=2.0):
    W, H = size
    y, x = np.mgrid[0:H, 0:W]
    r = np.hypot((x - W / 2) / (W / 2), (y - H / 2) / (H / 2))
    a = np.clip(1 - r, 0, 1) ** falloff
    im = np.zeros((H, W, 4)); im[..., :3] = color[:3]; im[..., 3] = a * color[3]
    return Image.fromarray(im.astype(np.uint8), 'RGBA')


def op_tile(img, size):
    W, H = size
    out = Image.new('RGBA', (W, H))
    t = img.convert('RGBA')
    for y in range(0, H, t.size[1]):
        for x in range(0, W, t.size[0]):
            out.paste(t, (x, y))
    return out


def op_mask_with(img, matte):
    """use another node's alpha as this one's alpha (e.g. stone texture inside a drawn wall section)."""
    out = img.convert('RGBA').resize(matte.size, Image.BICUBIC) if img.size != matte.size else img.convert('RGBA')
    a = ImageChops.multiply(out.getchannel('A'), matte.getchannel('A'))
    out = out.copy(); out.putalpha(a)
    return out


def register_world(G):
    G.register('draw', 1, op_draw, 'vector shapes drawn by the swarm from recorded coordinates')
    G.register('vgradient', 1, op_vgradient, 'vertical colour gradient from a drawn ramp')
    G.register('composite', 1, op_composite, 'cast placed parents onto one plate with recorded matrices')
    G.register('luma_alpha', 1, op_luma_alpha, 'alpha from luminance')
    G.register('radial', 1, op_radial, 'radial glow')
    G.register('tile', 1, op_tile, 'repeat a texture to fill a size')
    G.register('mask_with', 1, op_mask_with, "take another node's alpha")
    G.register('tile_bond', 1, op_tile_bond, 'tile a texture in offset, mirrored courses')
    G.register('room_shade', 1, op_room_shade, 'darken the room away from the lamp')


def op_alpha_union(a, b):
    out = a.convert('RGBA').copy()
    out.putalpha(ImageChops.lighter(a.getchannel('A'), b.getchannel('A')))
    return out


def op_beam_v1(size, lamp_px, door_box_px, color, reach_px):
    """the light that comes out of the open door: lamp-centred falloff, clipped to what the doorway lets through
    (rays from the lamp past the lintel), over the porch. Synthesised; the geometry is recorded in the params."""
    W, H = size
    y, x = np.mgrid[0:H, 0:W].astype(float)
    lx, ly = lamp_px
    x_out, y_top, y_floor = door_box_px
    # ray from the lamp through the top of the doorway: everything below it, right of the doorway, is lit
    slope = (y_top - ly) / (x_out - lx)
    under = y >= ly + slope * (x - lx) - 6
    right = x >= x_out
    above_floor = y <= y_floor + 2
    d = np.hypot(x - lx, y - ly)
    fall = np.clip(1 - (d - (x_out - lx)) / reach_px, 0, 1) ** 1.6
    a = (under & right & above_floor) * fall
    im = np.zeros((H, W, 4)); im[..., :3] = color[:3]; im[..., 3] = a * color[3]
    return Image.fromarray(im.clip(0, 255).astype(np.uint8), 'RGBA')


def register_more(G):
    G.register('alpha_union', 1, op_alpha_union, 'union of two mattes over the same frame')
    G.register('beam', 2, op_beam, 'synthesise the doorway light on the porch from recorded doorway geometry')
    G.register('hgradient', 1, op_hgradient, 'horizontal light gradient (the light running through the doorway)')


def op_beam(size, door_px, color, reach_px, ppm, h1=0.7, h2=2.2):
    """the doorway light on the porch: strongest on the boards by the sill, thinning with height and distance."""
    W, H = size
    y, x = np.mgrid[0:H, 0:W].astype(float)
    x_out, y_floor = door_px
    hy = (y_floor - y) / ppm
    hf = np.where(hy >= -0.02, np.exp(-np.clip(hy, 0, None) / h1) * 0.8 + 0.2 * np.exp(-np.clip(hy, 0, None) / h2), 0)
    dx = np.clip((x - x_out) / reach_px, 0, None)
    df = np.clip(1 - dx, 0, 1) ** 1.7 * (x >= x_out - 4)
    a = hf * df
    im = np.zeros((H, W, 4)); im[..., :3] = color[:3]; im[..., 3] = a * color[3]
    return Image.fromarray(im.clip(0, 255).astype(np.uint8), 'RGBA')


def op_tile_bond(img, size):
    """tile a texture like coursed stone: rows offset by half, every other tile mirrored, so no grid shows."""
    W, H = size
    out = Image.new('RGBA', (W, H))
    t = img.convert('RGBA'); tf = t.transpose(Image.FLIP_LEFT_RIGHT); tv = t.transpose(Image.FLIP_TOP_BOTTOM)
    tw, th = t.size
    for r, y in enumerate(range(0, H, th)):
        off = -(tw // 2) * (r % 2)
        for c, x in enumerate(range(off, W, tw)):
            pick = [t, tf, tv][(r * 2 + c) % 3]
            out.paste(pick, (x, y))
    return out


def op_room_shade(size, box_px, lamp_px, radius_px, strength, color=(0, 0, 0)):
    """the dark that the lamp does not reach, inside the room only."""
    W, H = size
    y, x = np.mgrid[0:H, 0:W].astype(float)
    d = np.hypot(x - lamp_px[0], y - lamp_px[1]) / radius_px
    a = np.clip(d, 0, 1) ** 1.3 * strength
    x0, y0, x1, y1 = box_px
    inside = (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
    im = np.zeros((H, W, 4)); im[..., :3] = color; im[..., 3] = a * 255 * inside
    return Image.fromarray(im.clip(0, 255).astype(np.uint8), 'RGBA')


def op_hgradient(size, color, a0, a1):
    W, H = size
    a = np.linspace(a0, a1, W)[None, :].repeat(H, 0)
    yy = np.linspace(1, 0, H)[:, None]
    a = a * (0.75 + 0.25 * yy)
    im = np.zeros((H, W, 4)); im[..., :3] = color; im[..., 3] = a * 255
    return Image.fromarray(im.clip(0, 255).astype(np.uint8), 'RGBA')
