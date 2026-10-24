"""Apply narrow, recorded compatibility changes to the ignored pinned checkout."""
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'work/sadtalker/source'
PIN='cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8'

def main():
    current=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()
    if current!=PIN:raise ValueError('SadTalker來源commit不同，請先核對相容修改')
    changes={
      'src/facerender/animate.py':[
       ('from src.utils.face_enhancer import enhancer_generator_with_len, enhancer_list',
        '# Optional enhancer is imported only when explicitly requested.'),
       ('        if enhancer:\n','        if enhancer:\n            from src.utils.face_enhancer import enhancer_generator_with_len, enhancer_list\n')],
      'src/face3d/util/preprocess.py':[
       ('trans_params = np.array([w0, h0, s, t[0], t[1]])',
        'trans_params = np.array([w0, h0, s, float(t[0]), float(t[1])], dtype=np.float32)')],
      'src/face3d/extract_kp_videos_safe.py':[
       ("root_path = 'gfpgan/weights'","root_path = os.environ.get('SADTALKER_FACE_MODEL_DIR', 'gfpgan/weights')")]
    }
    records=[]
    for name,patches in changes.items():
        p=SOURCE/name;text=p.read_text(encoding='utf-8');old=text
        for before,after in patches:
            if after in text:continue
            if text.count(before)!=1:raise ValueError('修改定位不唯一：'+name)
            text=text.replace(before,after,1)
        if text!=old:p.write_text(text,encoding='utf-8')
        records.append({'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    record={'source_repo':'https://github.com/OpenTalker/SadTalker','source_commit':PIN,'patched_files':records,
            'scope':['lazy optional enhancer import; no face restoration used','NumPy scalar alignment','project-local face model directory']}
    (ROOT/'work/sadtalker/compatibility-manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__':main()
