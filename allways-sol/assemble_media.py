"""Join the publication transfer parts; require exact Git and SHA256 checks."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parent.parent;site=root/'allways-sol';manifest=site/'reconstruct.json'
if not manifest.exists():raise SystemExit('No pending transfer manifest; nothing to reconstruct.')
def allowed(path):
 p=(root/path).resolve()
 if not p.is_relative_to(site.resolve()):raise ValueError('Path outside ALLWAYS collection')
 return p
receipts=[]
for item in json.load(open(manifest))['files']:
 target=allowed(item['target']);target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_suffix('.mp4.assembling');sha256=hashlib.sha256();length=0
 with open(tmp,'wb') as out:
  for part in item['parts']:
   p=allowed(part['path']);b=p.read_bytes()
   if len(b)!=part['bytes'] or hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()!=part['sha']:raise ValueError('Invalid transfer part: '+part['path'])
   out.write(b);sha256.update(b);length+=len(b)
 if length!=item['bytes'] or sha256.hexdigest()!=item['sha256']:raise ValueError('Invalid reconstructed MP4: '+item['target'])
 tmp.replace(target);receipts.append({'file':item['target'],'sha256':sha256.hexdigest(),'bytes':length,'reconstruction':'PASS'})
 print('Verified',item['target'],length,flush=True)
# Validate every published media file, including small files uploaded directly.
catalog=json.load(open(site/'catalog.json'));all_media=[]
for f in catalog['films']:all_media.extend([f['film']]+f['comparisons'])
for item in all_media:
 p=allowed('allways-sol/'+item['url'])
 if p.stat().st_size!=item['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Catalog media mismatch: '+item['url'])
(site/'PUBLICATION.json').write_text(json.dumps({'all_media_hashes':'PASS','media_files':len(all_media),'reconstructed':receipts},indent=2))
incoming=site/'_incoming'
if incoming.exists():shutil.rmtree(incoming)
manifest.unlink();print('All',len(all_media),'media files verified. Transfer parts removed.',flush=True)
