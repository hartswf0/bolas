# fetch.py OUTDIR WIDTH "File:..." ... -> downloads thumbnails, writes meta json per file
import sys,json,urllib.request,urllib.parse,time,os,re
UA={'User-Agent':'oulipo-film-research/1.0'}
out,width=sys.argv[1],sys.argv[2]; titles=sys.argv[3:]
def get(u,raw=False):
    for k in range(5):
        try:
            d=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60).read()
            return d if raw else json.loads(d)
        except Exception as e:
            print('ERR',e,u[:90],file=sys.stderr); time.sleep(8*(k+1))
p=dict(action='query',titles='|'.join(titles),prop='imageinfo',iiprop='url|size|extmetadata',iiurlwidth=width,format='json')
r=get('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p))
os.makedirs(out,exist_ok=True)
for pg in r['query']['pages'].values():
    ii=pg['imageinfo'][0]; em=ii['extmetadata']
    tu=ii['thumburl'].replace('thumb.wikimedia.org/wikipedia/commons/thumb','upload.wikimedia.org/wikipedia/commons/thumb').split('?')[0]
    slug=re.sub(r'[^A-Za-z0-9]+','_',pg['title'][5:])[:60]
    fn=f'{out}/{slug}.jpg'
    if not os.path.exists(fn):
        d=get(tu,raw=True)
        if d: open(fn,'wb').write(d)
        time.sleep(2)
    meta=dict(title=pg['title'],author=re.sub('<[^>]+>','',em.get('Artist',{}).get('value','')).strip(),
      license=em.get('LicenseShortName',{}).get('value'),license_url=em.get('LicenseUrl',{}).get('value',''),
      source_url=ii['descriptionurl'],file_url=tu,size=[ii['width'],ii['height']],
      date=re.sub('<[^>]+>','',em.get('DateTimeOriginal',{}).get('value','')))
    json.dump(meta,open(fn[:-4]+'.json','w'),indent=1); print(fn,meta['license'],meta['author'][:40])
