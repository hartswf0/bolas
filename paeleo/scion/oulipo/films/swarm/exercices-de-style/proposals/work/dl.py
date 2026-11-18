import json,sys,time,urllib.request,urllib.parse,re
UA={'User-Agent':'oulipo-film-research/1.0'}
out=sys.argv[1]
def get(u,raw=False):
    for i in range(6):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60).read()
            return r if raw else json.loads(r)
        except Exception as e:
            print('retry',e); time.sleep(4+5*i)
for spec in sys.argv[2:]:
    name,title=spec.split('=',1)
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(dict(action='query',format='json',titles=title,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1280))
    p=list(get(u)['query']['pages'].values())[0]; ii=p['imageinfo'][0]; m=ii['extmetadata']
    fu=ii['thumburl'].split('?')[0].replace('thumb.wikimedia.org/wikipedia','upload.wikimedia.org/wikipedia'); ii['thumburl']=fu; b=get(fu,raw=True); open(f'{out}/{name}.jpg','wb').write(b)
    print(json.dumps(dict(name=name,title=title,author=re.sub('<[^>]+>','',m.get('Artist',{}).get('value','')).strip()[:120],license=m.get('LicenseShortName',{}).get('value'),license_url=m.get('LicenseUrl',{}).get('value',''),source_url=ii['descriptionurl'],file_url=ii['thumburl'],bytes=len(b)),ensure_ascii=False))
    time.sleep(2)
