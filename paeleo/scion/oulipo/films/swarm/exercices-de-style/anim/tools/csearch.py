import sys, json, urllib.request, urllib.parse, time, io
from PIL import Image, ImageDraw
UA={'User-Agent':'oulipo-film-research/1.0'}
def api(**p):
    p.update(format='json')
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p)
    for i in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30))
        except Exception as e: print('retry',e,file=sys.stderr); time.sleep(5*(i+1))
out=sys.argv[1]; qs=sys.argv[2:]
titles=[]
for q in qs:
    r=api(action='query',list='search',srnamespace=6,srsearch=q,srlimit=24)
    for x in r['query']['search']:
        if x['title'] not in titles and x['title'].lower().endswith(('.jpg','.jpeg','.png','.tif','.tiff')): titles.append(x['title'])
info=[]
for i in range(0,len(titles),20):
    r=api(action='query',prop='imageinfo',iiprop='url|size|extmetadata',iiurlwidth=200,titles='|'.join(titles[i:i+20]))
    for pg in r['query']['pages'].values():
        ii=pg.get('imageinfo',[{}])[0]; em=ii.get('extmetadata',{})
        info.append(dict(title=pg['title'],thumb=ii.get('thumburl'),w=ii.get('width'),h=ii.get('height'),lic=em.get('LicenseShortName',{}).get('value'),date=em.get('DateTimeOriginal',{}).get('value','')[:40]))
cells=[]
for n,x in enumerate(info):
    print(n,x['lic'],x['w'],x['h'],x['title'][:110])
    try:
        im=Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(x['thumb'],headers=UA),timeout=30).read())).convert('RGB'); im.thumbnail((200,200))
    except Exception as e: im=Image.new('RGB',(200,200),'red')
    c=Image.new('RGB',(200,215),'white'); c.paste(im,(0,0)); ImageDraw.Draw(c).text((2,201),str(n),fill='black'); cells.append(c); time.sleep(0.3)
cols=8; rows=(len(cells)+cols-1)//cols
sh=Image.new('RGB',(cols*200,max(1,rows)*215),'white')
for n,c in enumerate(cells): sh.paste(c,((n%cols)*200,(n//cols)*215))
sh.save(out); json.dump(info,open(out+'.json','w'),indent=1)
