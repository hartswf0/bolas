import json,sys,time,urllib.request,urllib.error,os
UA={'User-Agent':'oulipo-film-research/1.0'}
d=json.load(open(sys.argv[2]))
dest=sys.argv[1]
for t in sys.argv[3:]:
    url=d[t]['url'].split('?')[0]; fn=os.path.join(dest,url.rsplit('/',1)[1])
    if os.path.exists(fn): print('have',fn); continue
    for i in range(8):
        try:
            data=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60).read()
            open(fn,'wb').write(data); print('got',fn,len(data),flush=True); break
        except urllib.error.HTTPError as e:
            if e.code==429:
                w=int(e.headers.get('retry-after','20'))+5; print('429 wait',w,flush=True); time.sleep(w); continue
            raise
    time.sleep(5)
