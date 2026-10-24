"""Scan Git candidates or the actual index; never echo matching secret values."""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
PRIVATE={'private_inputs','outputs','work','models','node_modules','.venv','venv','cache','.git','.codex','.agents','.aws','素材照片','阿忠介紹校園安全','阿德推廣校園反霸凌','阿德推廣校園反霸凌（阿忠身體）','阿德推廣校園反霸凌（個人身體）'}
MODEL_EXT={'.safetensors','.ckpt','.pth','.pt','.onnx','.gguf','.pkl','.pickle','.tflite','.bin','.exe','.dll','.zip','.7z'}
TEXT_EXT={'.md','.py','.json','.ps1','.js','.cjs','.mjs','.css','.html','.txt','.yml','.yaml','.toml','.svg'}
RULES={
 'github-token':re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}'),
 'api-secret':re.compile(rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}'),
 'aws-key':re.compile(rb'AKIA[0-9A-Z]{16}'),
 'private-key':re.compile(b'-----BEGIN '+rb'(?:(?:RSA|EC|OPENSSH) )?PRIVATE KEY-----'),
 'service-account':re.compile(rb'"type"\s*:\s*"service_account"'),
}

def allowed_binary(root=ROOT):
 allowed={}
 for folder in ['examples/azhong-mmeng-1202','examples/ade-school-body','examples/ade-personal-body']:
  mf=root/folder/'manifest.json'
  if not mf.exists():continue
  for row in json.loads(mf.read_text(encoding='utf-8'))['files']:
   p=(root/folder/row['path']).resolve()
   if not p.is_relative_to((root/folder).resolve()):raise ValueError('Manifest path escape')
   allowed[p.relative_to(root).as_posix()]=row['sha256']
 allowed['assets/fonts/NotoSansTC.ttf']='864727d210d54f2537bbe23b3a839436c3992af72de9322af5270897246bd44f'
 return allowed

def inspect_bytes(name,data,allowed):
 p=PurePosixPath(name);issues=[]
 if p.parts[0] in PRIVATE or p.parts[:2]==('tools','bin') or p.parts[0]=='samples':issues.append('private-or-local-directory')
 if p.suffix.lower() in MODEL_EXT or '.pth.' in p.name:issues.append('model-or-installation-binary')
 if (p.name.startswith('.env') and p.name!='.env.example') or p.suffix.lower() in {'.pem','.key','.p12','.pfx'}:issues.append('credential-file')
 if len(data)>50*1024**2:issues.append('oversized-file')
 if p.suffix.lower() not in TEXT_EXT and p.name not in {'.gitignore','.gitattributes','.nojekyll','LICENSE','OFL.txt'}:
  if name not in allowed or hashlib.sha256(data).hexdigest()!=allowed[name]:issues.append('unlisted-or-changed-binary')
 if p.suffix.lower() in TEXT_EXT or p.name in {'.gitignore','.gitattributes','.nojekyll','LICENSE'}:
  try:data.decode('utf-8')
  except UnicodeDecodeError:issues.append('not-utf8')
  for key,pattern in RULES.items():
   if pattern.search(data):issues.append(key)
 return [{'path':name,'category':i} for i in issues]

def scan(root=ROOT,staged=False):
 args=['git','diff','--cached','--name-only','--diff-filter=ACMR','-z'] if staged else ['git','ls-files','--cached','--others','--exclude-standard','-z']
 names=sorted(set(x for x in subprocess.check_output(args,cwd=root).decode('utf-8').split('\0') if x))
 allowed=allowed_binary(root);issues=[];rows=[]
 for name in names:
  data=subprocess.check_output(['git','show',':'+name],cwd=root) if staged else (root/name).read_bytes()
  issues+=inspect_bytes(name,data,allowed);rows.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
 return {'ok':not issues,'mode':'staged-index' if staged else 'git-candidates','files':len(rows),'bytes':sum(r['bytes'] for r in rows),'issues':issues,'entries':rows}

def main():
 p=argparse.ArgumentParser();p.add_argument('--staged',action='store_true');p.add_argument('--report',type=Path,default=Path('work/publication/secret-scan.json'));a=p.parse_args()
 report=scan(staged=a.staged);dest=(ROOT/a.report).resolve()
 if not dest.is_relative_to(ROOT/'work'):raise ValueError('Private scan reports belong in work/')
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='entries'},ensure_ascii=True))
 raise SystemExit(0 if report['ok'] else 1)
if __name__=='__main__':main()
