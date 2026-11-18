import json,sys,time
from cs import api
titles=sys.argv[1:]
r=api(action='query',prop='imageinfo',iiprop='url|extmetadata|size|mime',titles='|'.join(titles),iiurlwidth=1280)
for p in r['query']['pages'].values():
    ii=p.get('imageinfo',[{}])[0]; m=ii.get('extmetadata',{})
    g=lambda k:(m.get(k,{}).get('value','') or '')[:150]
    print(json.dumps(dict(title=p['title'],lic=g('LicenseShortName'),licurl=g('LicenseUrl'),artist=g('Artist'),date=g('DateTimeOriginal'),size=ii.get('size'),dur=ii.get('duration'),mime=ii.get('mime'),url=ii.get('url'),thumb=ii.get('thumburl'),desc=g('ImageDescription')),ensure_ascii=False))
