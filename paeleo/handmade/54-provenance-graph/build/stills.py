"""stills/ (the four the brief asks for, from the lossless scene frames) and proof/ sheets of the hard passages."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lineage import FOLDER, REPO
FR = os.path.join(FOLDER, 'build', 'cache', 'frames')


def frame(i):
    return Image.open(os.path.join(FR, 'scene_%04d.png' % i)).convert('RGB')


def main():
    os.makedirs(os.path.join(FOLDER, 'stills'), exist_ok=True); os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
    for t in (3.6, 9.0, 19.0, 28.0):
        frame(int(round(t * 24))).save(os.path.join(FOLDER, 'stills', 'still_%04.1fs.jpg' % t), quality=90)
    f = ImageFont.truetype(os.path.join(REPO, 'tools/paeleo/fonts/f14.woff2'), 14)
    def sheet(name, idx, box, cols=6, scale=0.5):
        w, h = int((box[2] - box[0]) * scale), int((box[3] - box[1]) * scale)
        rows = (len(idx) + cols - 1) // cols
        out = Image.new('RGB', (w * cols, h * rows), (0, 0, 0))
        for k, i in enumerate(idx):
            im = frame(i).crop(box).resize((w, h), Image.LANCZOS)
            ImageDraw.Draw(im).text((4, 4), 'i%03d %.2fs' % (i, i / 24), font=f, fill=(255, 230, 120))
            out.paste(im, ((k % cols) * w, (k // cols) * h))
        out.save(os.path.join(FOLDER, 'proof', name), quality=88)
    sheet('turn_away_3.3-4.1s.jpg', list(range(80, 99)), (820, 300, 1280, 600))
    sheet('turn_back_7.3-8.3s.jpg', list(range(176, 200)), (820, 300, 1280, 600))
    sheet('approach_head_low.jpg', list(range(353, 575, 18)), (0, 0, 1280, 720), cols=4, scale=0.3)
    sheet('lie_and_look_in_23.6-29.5s.jpg', list(range(566, 712, 10)), (0, 0, 1280, 720), cols=5, scale=0.3)
    sheet('retreat_1-2.5s.jpg', list(range(22, 62, 3)), (820, 300, 1280, 600))
    print('stills and proof sheets written')


if __name__ == '__main__':
    main()
