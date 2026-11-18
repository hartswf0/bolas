import json,sys,time,urllib.request,urllib.parse
UA={'User-Agent':'oulipo-film-research/1.0'}
def api(**p):
    p.update(format='json')
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p)
    for k in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30))
        except Exception as e:
            print('retry',e,file=sys.stderr); time.sleep(8*(k+1))
if __name__=='__main__':
    for q in sys.argv[1:]:
        r=api(action='query',list='search',srnamespace=6,srlimit=30,srsearch=q)
        print('==',q)
        for x in r['query']['search']: print(x['title'])
        time.sleep(3)
