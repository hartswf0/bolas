import sys,json,urllib.request,urllib.parse,time
UA={'User-Agent':'oulipo-film-research/1.0'}
def api(p):
    p.update(format='json')
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p)
    for k in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40))
        except Exception as e: print('ERR',e,file=sys.stderr); time.sleep(5*(k+1))
q=sys.argv[1]
r=api(dict(action='query',generator='search',gsrsearch=q+' filetype:bitmap',gsrnamespace=6,gsrlimit=int(sys.argv[2]) if len(sys.argv)>2 else 15,prop='imageinfo',iiprop='url|size|extmetadata',iiurlwidth=320))
for p in (r or {}).get('query',{}).get('pages',{}).values():
    ii=p['imageinfo'][0];em=ii.get('extmetadata',{})
    print(p['title'],'|',ii['width'],'x',ii['height'],'|',em.get('LicenseShortName',{}).get('value'),'|',ii.get('thumburl'))
