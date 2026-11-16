cd /home/user/bolas/paeleo/scion/oulipo/films/swarm/la-mort-en-ce-jardin/world-build
python3 -I compose.py /home/user/bolas/paeleo/scion/oulipo/films/sources/la-mort-en-ce-jardin/world /home/user/bolas/paeleo/scion/oulipo/films/swarm/la-mort-en-ce-jardin 2>&1 | grep -A3 -i "error\|Trace" | head
cd /home/user/bolas/paeleo/scion/oulipo/films/sources/la-mort-en-ce-jardin/world/test && python3 -c "
import json;d=json.load(open('stats.json'))
for k,v in list(d.items())[:2]: print(k, v['stats'], v.get('max_scale'))
from PIL import Image
a=Image.open('wide_L-S1_t1.5.png');b=Image.open('close_L-S5_t19.0.png')
S=Image.new('RGB',(1600,540));S.paste(a,(0,0));S.paste(b,(800,0));S.save('/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/w/t.jpg')"
