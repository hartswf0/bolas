import sys
from PIL import Image, ImageDraw, ImageFont
D=sys.argv[1]; out=sys.argv[2]
ref=Image.open("/home/user/bolas/paeleo/scion/oulipo/assets/references/maki.webp").convert("RGB").resize((960,540),Image.LANCZOS)
items=[(ref,"REFERENCE  assets/references/maki.webp (640x360 video still, shown at equal height)"),
       (Image.open(D+"/f_2.10.png"),"SHOT 2.1 s  (film 0:17.6)  TEXT cue: paper mouth says \"hangs\" as it types; the guessed gong hangs on the knot"),
       (Image.open(D+"/f_4.55.png"),"SHOT 4.55 s (film 0:38.5)  IMAGE cue: gong tears into wedges; Brehm binturong on the same knot"),
       (Image.open(D+"/f_9.70.png"),"SHOT 9.7 s  (film 0:53.4)  same glyph box, same knot: red pencil under \"hangs\"")]
F=ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf",17)
sheet=Image.new("RGB",(1920+30,2*(540+36)+20),(40,38,36))
d=ImageDraw.Draw(sheet)
for k,(im,lab) in enumerate(items):
    x=10+(k%2)*(960+10); y=10+(k//2)*(540+36)
    d.text((x+4,y+8),lab,font=F,fill=(240,236,228)); sheet.paste(im,(x,y+34))
sheet.save(out,quality=88)
