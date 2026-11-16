import json,sys,re,time,urllib.request,urllib.parse
UA={'User-Agent':'oulipo-film-research/1.0'}
def get(u):
    for i in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30))
        except Exception as e:
            time.sleep(3+4*i)
    return {}
for q in sys.argv[1:]:
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(dict(action='query',format='json',generator='search',gsrnamespace=6,gsrlimit=10,gsrsearch=q,prop='imageinfo',iiprop='url|extmetadata|size',iiextmetadatafilter='LicenseShortName|Artist',iiurlwidth=1280))
    d=get(u); print('##',q)
    for p in d.get('query',{}).get('pages',{}).values():
        ii=p['imageinfo'][0];m=ii.get('extmetadata',{})
        print(p['title'][:80],'|',m.get('LicenseShortName',{}).get('value'),'|',re.sub('<[^>]+>','',m.get('Artist',{}).get('value',''))[:40],'|',ii['width'],ii['height'],'|',ii.get('thumburl'))
    time.sleep(2)
