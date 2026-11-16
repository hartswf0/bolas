import sys,json,urllib.request,urllib.parse,time,re
UA={'User-Agent':'oulipo-film-research/1.0'}
p=dict(action='query',titles='|'.join(sys.argv[1:]),prop='imageinfo',iiprop='url|size|extmetadata|mime',format='json')
u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p)
for k in range(6):
    try: r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60)); break
    except Exception as e: print('ERR',e,file=sys.stderr); time.sleep(10*(k+1))
out=[]
for pg in r['query']['pages'].values():
    ii=pg['imageinfo'][0]; em=ii['extmetadata']
    out.append(dict(title=pg['title'],author=re.sub('<[^>]+>','',em.get('Artist',{}).get('value','')).strip(),license=em.get('LicenseShortName',{}).get('value'),license_url=em.get('LicenseUrl',{}).get('value',''),source_url=ii['descriptionurl'],file_url=ii['url'],size=ii.get('size'),mime=ii.get('mime'),credit=re.sub('<[^>]+>','',em.get('Credit',{}).get('value',''))[:200]))
print(json.dumps(out,indent=1))
