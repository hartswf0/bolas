import sys, json, urllib.request, urllib.parse
def api(params):
    params.update(format='json')
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)
    r=urllib.request.Request(u,headers={'User-Agent':'oulipo-film-research/1.0'})
    return json.load(urllib.request.urlopen(r,timeout=30))
q=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 12
d=api({'action':'query','generator':'search','gsrsearch':q,'gsrnamespace':6,'gsrlimit':n,'prop':'imageinfo','iiprop':'url|extmetadata|size|mime'})
for p in (d.get('query',{}).get('pages',{}) or {}).values():
    ii=p['imageinfo'][0]; em=ii.get('extmetadata',{})
    print(p['title'],'|',em.get('LicenseShortName',{}).get('value'),'|',ii.get('size'),ii.get('width'),ii.get('height'),ii['mime'],'|',em.get('Artist',{}).get('value','')[:60].replace('\n',' '))
