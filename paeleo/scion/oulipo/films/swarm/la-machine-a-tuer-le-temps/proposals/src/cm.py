import json,sys,time,urllib.request,urllib.parse,os,re
UA={'User-Agent':'oulipo-film-research/1.0'}
out=sys.argv[1]; w=sys.argv[2]; titles=sys.argv[3:]
def get(u):
    for i in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60).read()
        except Exception as e:
            print('retry',e); time.sleep(5*(i+1))
meta=[]
for t in titles:
    q='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','titles':'File:'+t,'prop':'imageinfo','iiprop':'url|extmetadata|size','iiurlwidth':w})
    d=json.loads(get(q)); p=list(d['query']['pages'].values())[0]; ii=p['imageinfo'][0]; m=ii['extmetadata']
    fn=re.sub(r'[^A-Za-z0-9._-]','_',t)
    ii['thumburl']=ii['thumburl'].replace('thumb.wikimedia.org/','upload.wikimedia.org/').split('?')[0]; b=get(ii['thumburl']); open(os.path.join(out,fn),'wb').write(b)
    rec=dict(title=t,author=re.sub('<[^>]+>','',m.get('Artist',{}).get('value','')),license=m.get('LicenseShortName',{}).get('value'),license_url=m.get('LicenseUrl',{}).get('value'),source_url=ii['descriptionurl'],file_url=ii['thumburl'],size=len(b),orig=(ii['width'],ii['height']))
    print(json.dumps(rec)); meta.append(rec); time.sleep(2)
json.dump(meta,open(os.path.join(out,'meta-%d.json'%int(time.time())),'w'),indent=1)
