import sys,json,urllib.request,urllib.parse
UA={'User-Agent':'oulipo-film-research/1.0'}
q=sys.argv[1]
u='https://www.loc.gov/photos/?'+urllib.parse.urlencode({'q':q,'fo':'json','c':25})
r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60))
for it in r.get('results',[]):
    print(it.get('id'),'|',it.get('title','')[:90],'|',it.get('date'),'|',(it.get('rights_advisory') or it.get('item',{}).get('rights_advisory') or ['?'])[:1],'|',(it.get('image_url') or [''])[-1][:120])
