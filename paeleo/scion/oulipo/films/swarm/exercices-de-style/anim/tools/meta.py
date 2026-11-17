import sys, json, urllib.request, urllib.parse, time, re
UA={'User-Agent':'oulipo-film-research/1.0'}
out=[]
for t in sys.argv[1:]:
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(dict(action='query',prop='imageinfo',iiprop='url|size|extmetadata',format='json',titles=t))
    for i in range(6):
        try: r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30)); break
        except Exception as e: print('retry',e,file=sys.stderr); time.sleep(10*(i+1))
    p=list(r['query']['pages'].values())[0]; ii=p['imageinfo'][0]; em=ii['extmetadata']
    g=lambda k: re.sub('<[^>]+>','',str(em.get(k,{}).get('value','')))[:400]
    d=dict(title=t,url=ii['url'],page=ii['descriptionurl'],size=[ii['width'],ii['height']],license=g('LicenseShortName'),license_url=g('LicenseUrl'),artist=g('Artist'),date=g('DateTimeOriginal'),desc=g('ImageDescription'),credit=g('Credit'),copyrighted=g('Copyrighted'),restrictions=g('Restrictions'))
    out.append(d); print(json.dumps(d,ensure_ascii=False,indent=1))
