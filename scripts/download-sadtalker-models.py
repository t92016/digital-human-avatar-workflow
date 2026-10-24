"""Download only the four pinned CPU-smoke-test weights; verify every SHA256."""
from __future__ import annotations
import concurrent.futures,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(4*1024*1024),b''):h.update(part)
    return h.hexdigest()

def download(row):
    path=(ROOT/row['path']).resolve()
    if not path.is_relative_to(ROOT/'models/sadtalker'):raise ValueError('模型路徑越界')
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if digest(path)!=row['sha256']:raise ValueError('保留但拒用不同內容的模型：'+row['name'])
    else:
        partial=path.with_suffix(path.suffix+'.partial')
        request=urllib.request.Request(row['url'],headers={'User-Agent':'avatar-workflow-sadtalker/1.0'})
        with urllib.request.urlopen(request,timeout=60) as response,partial.open('wb') as stream:
            total=last=0
            while chunk:=response.read(4*1024*1024):
                stream.write(chunk);total+=len(chunk)
                if total-last>=100*1024*1024:
                    print(f'{row["name"]}: {total//1024//1024} MiB',flush=True);last=total
        if digest(partial)!=row['sha256']:raise ValueError('下載SHA256不符，未啟用：'+row['name'])
        if partial.stat().st_size!=row['size']:raise ValueError('模型大小不符')
        partial.rename(path)
    print('Verified '+row['name'],flush=True)
    return row

def main():
    manifest=json.loads((ROOT/'config/sadtalker-models.json').read_text(encoding='utf-8'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(download,manifest['files']))
    dest=ROOT/'work/sadtalker/model-download-manifest.json';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
