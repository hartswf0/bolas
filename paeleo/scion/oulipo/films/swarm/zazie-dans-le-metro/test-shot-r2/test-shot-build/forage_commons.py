import sys, json, time, urllib.request, urllib.parse
OUT=sys.argv[1]
UA={'User-Agent':'oulipo-film-research/1.0'}
def api(params, tries=8):
    params=dict(params, format='json')
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)
    w=20
    for k in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30))
        except Exception as e:
            print('retry',k,e,flush=True); time.sleep(w); w*=1.6
    raise SystemExit('gave up')
def meta(pages):
    out=[]
    for p in (pages or {}).values():
        if 'imageinfo' not in p: continue
        ii=p['imageinfo'][0]; em=ii.get('extmetadata',{}); g=lambda k: em.get(k,{}).get('value','')
        out.append(dict(title=p['title'],license=g('LicenseShortName'),license_url=g('LicenseUrl'),artist=g('Artist'),
          desc=g('ImageDescription')[:300],date=g('DateTimeOriginal'),url=ii['url'],thumb=ii.get('thumburl'),page=ii['descriptionurl'],size=ii['size'],mime=ii['mime'],
          duration=ii.get('duration')))
    return out
res={}
d=api({'action':'query','titles':'File:Kraft tileable 1024x1024.png|File:Texture 15.JPG|File:Texture 16.JPG','prop':'imageinfo','iiprop':'url|extmetadata|size|mime','iiurlwidth':1280})
res['paper_titles']=meta(d['query']['pages']); json.dump(res,open(OUT,'w'),indent=1); time.sleep(8)
for q in ['wind gust recording','strong wind ogg','street ambience Paris','city square ambience','hand bell ring','paper rustle','cardboard','paper texture']:
    d=api({'action':'query','generator':'search','gsrsearch':q+(' filetype:audio' if 'paper texture' not in q else ' filetype:bitmap'),'gsrnamespace':6,'gsrlimit':12,'prop':'imageinfo','iiprop':'url|extmetadata|size|mime','iiurlwidth':1280})
    res[q]=meta(d.get('query',{}).get('pages')); json.dump(res,open(OUT,'w'),indent=1); print('ok',q,len(res[q]),flush=True); time.sleep(10)
print('done')
