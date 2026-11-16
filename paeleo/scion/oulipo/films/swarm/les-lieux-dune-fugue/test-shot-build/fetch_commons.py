"""Fetch Commons files by title with licence metadata (backs off on 429). Writes meta json."""
import sys,json,time,urllib.request,urllib.parse,re,os
UA={'User-Agent':'oulipo-film-research/1.0'}
DL='/home/user/bolas/paeleo/scion/oulipo/films/sources/les-lieux-dune-fugue/test-shot/dl'
def get(u,tries=6):
    for k in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(40*(k+1)); continue
            raise
    raise SystemExit('gave up '+u)
def strip(h): return re.sub('<[^>]+>','',h or '').strip()
meta={}
mf=DL+'/commons_meta.json'
if os.path.exists(mf): meta=json.load(open(mf))
for title in sys.argv[1:]:
    p=dict(action='query',titles=title,prop='imageinfo',iiprop='url|extmetadata|size|mime',format='json')
    if title.lower().endswith(('.jpg','.png')): p['iiurlwidth']=1600
    r=json.loads(get('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p)))
    pg=list(r['query']['pages'].values())[0]; ii=pg['imageinfo'][0]; em=ii['extmetadata']
    url=(ii.get('thumburl') or ii['url']).split('?')[0]
    fn=re.sub(r'[^A-Za-z0-9._-]','_',title[5:])
    if 'thumburl' in ii: fn=fn.rsplit('.',1)[0]+'.thumb.'+url.rsplit('.',1)[1]
    open(DL+'/'+fn,'wb').write(get(url)); time.sleep(3)
    meta[fn]=dict(title=title,author=strip(em.get('Artist',{}).get('value')),license=em.get('LicenseShortName',{}).get('value'),
      license_url=em.get('LicenseUrl',{}).get('value',''),source_url=ii['descriptionurl'],file_url=url,
      credit=strip(em.get('Credit',{}).get('value'))[:200],usage_terms=em.get('UsageTerms',{}).get('value'))
    print(fn,meta[fn]['license'],meta[fn]['author'][:80])
json.dump(meta,open(mf,'w'),indent=1,ensure_ascii=False)
