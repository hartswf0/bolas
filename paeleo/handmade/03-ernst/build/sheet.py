"""proof sheets: render chosen scene times (or read rendered frames) into a labelled contact sheet (proof/)."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))


def sheet(times, out, cols=4, crop=None, from_frames=True, scale=0.5):
    import render
    ims = []
    for t in times:
        i = int(round(t * 24))
        p = os.path.join(render.OUT, 's%04d.png' % i)
        if from_frames and os.path.exists(p):
            im = Image.open(p).convert('RGB')
        else:
            im, _ = render.render_frame(i)
        if crop:
            im = im.crop(crop)
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 70, 18), fill=(255, 255, 255))
        d.text((3, 2), '%.2fs' % t, fill=(200, 0, 0))
        ims.append(im)
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    o = Image.new('RGB', (w * cols, h * rows), (90, 90, 90))
    for k, im in enumerate(ims):
        o.paste(im, ((k % cols) * w, (k // cols) * h))
    o.save(out)


if __name__ == '__main__':
    times = [float(x) for x in sys.argv[2].split(',')]
    crop = tuple(int(v) for v in sys.argv[3].split(',')) if len(sys.argv) > 3 and sys.argv[3] != '-' else None
    scale = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    cols = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    sheet(times, sys.argv[1], cols=cols, crop=crop, scale=scale)
