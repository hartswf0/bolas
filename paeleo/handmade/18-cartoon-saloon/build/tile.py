import sys
from PIL import Image
out, cols = sys.argv[1], int(sys.argv[2]); fs = open(sys.argv[3]).read().split()
ims = [Image.open(f) for f in fs]; w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
T = Image.new('RGB', (w * cols, h * rows), 'white')
for k, im in enumerate(ims): T.paste(im, ((k % cols) * w, (k // cols) * h))
T.save(out)
