"""Verify the public Pages assets and local links without installing models."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for key,value in attrs:
   if key in ('src','href') and value:self.links.append(value)
def main():
 data=json.loads((ROOT/'config/publication.json').read_text(encoding='utf-8'));assert len(data['groups'])==3
 videos=[]
 for g in data['groups']:
  assert len(g['videos'])==3 and (ROOT/g['poster']).is_file() and (ROOT/g['page']/'index.html').is_file()
  for row in g['videos']:
   p=ROOT/row['path'];assert p.stat().st_size==row['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
   fp=ROOT/'tools/bin/ffprobe.exe'
   if fp.is_file():
    probe=json.loads(subprocess.check_output([str(fp),'-v','error','-show_streams','-show_format','-of','json',str(p)]));v=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'24/1');assert abs(float(probe['format']['duration'])-g['duration'])<.05
   videos.append(row['path'])
 pages=[ROOT/'index.html',ROOT/'guide.html',*list((ROOT/'showcases').glob('*/index.html'))];count=0
 for p in pages:
  s=p.read_text(encoding='utf-8');assert '\ufffd' not in s;parser=Links();parser.feed(s)
  for link in parser.links:
   parts=urlsplit(link)
   if parts.scheme or not parts.path:continue
   target=(p.parent/unquote(parts.path)).resolve();assert target.is_relative_to(ROOT) and target.exists(),(p,link)
   count+=1
 manifest=json.loads((ROOT/'examples/azhong-mmeng-1202/manifest.json').read_text(encoding='utf-8'))
 for row in manifest['files']:assert hashlib.sha256((ROOT/'examples/azhong-mmeng-1202'/row['path']).read_bytes()).hexdigest()==row['sha256']
 report={'ok':True,'groups':3,'videos':videos,'html_pages':len(pages),'local_links':count,'frozen_azhong_files':len(manifest['files']),'models_uploaded':False}
 dest=ROOT/'work/publication/media-and-links.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=True))
if __name__=='__main__':main()
