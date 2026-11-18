import sys, json, urllib.request, urllib.parse
titles='|'.join(sys.argv[1:])
u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','titles':titles,'prop':'imageinfo','iiprop':'url|extmetadata|size|mime','iiurlwidth':1600,'format':'json'})
r=urllib.request.Request(u,headers={'User-Agent':'oulipo-film-research/1.0'})
d=json.load(urllib.request.urlopen(r,timeout=30))
out=[]
for p in d['query']['pages'].values():
    ii=p['imageinfo'][0]; em=ii.get('extmetadata',{})
    g=lambda k: em.get(k,{}).get('value','')
    out.append(dict(title=p['title'],license=g('LicenseShortName'),license_url=g('LicenseUrl'),artist=g('Artist'),desc=g('ImageDescription')[:200],url=ii['url'],thumb=ii.get('thumburl'),page=ii['descriptionurl'],size=ii['size']))
print(json.dumps(out,indent=1))
