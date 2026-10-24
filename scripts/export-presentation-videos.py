"""Copy the six existing MP4s into named private presentation folders, losslessly."""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODES=[('mode1_hands.mp4','01_只有手部.mp4'),
       ('mode2_natural.mp4','02_手腳與頭部_自然版.mp4'),
       ('mode3_lively.mp4','03_手腳與頭部_活潑版.mp4')]
GROUPS=[('阿忠介紹校園安全','examples/azhong-mmeng-1202/media',13.125),
        ('阿德推廣校園反霸凌（阿忠身體）','outputs/round05',13.0)]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ffprobe=ROOT/'tools/bin/ffprobe.exe'
    if not ffprobe.exists():
        found=shutil.which('ffprobe')
        if not found:raise RuntimeError('需要既有FFprobe驗證MP4，請先完成專案工具安裝')
        ffprobe=Path(found)
    planned=[]
    for folder,source,seconds in GROUPS:
        for old,new in MODES:
            src=ROOT/source/old;dst=ROOT/folder/new
            sha=digest(src)
            if dst.exists() and digest(dst)!=sha:
                raise FileExistsError(f'保留不同內容的既有檔案：{dst}')
            result=subprocess.run([str(ffprobe),'-v','error','-show_format','-show_streams','-of','json',str(src)],capture_output=True,check=True)
            info=json.loads(result.stdout)
            video=next(s for s in info['streams'] if s['codec_type']=='video')
            audio=next(s for s in info['streams'] if s['codec_type']=='audio')
            assert (video['codec_name'],audio['codec_name'])==('h264','aac')
            assert (video['width'],video['height'],video['r_frame_rate'])==(1920,1080,'24/1')
            assert abs(float(info['format']['duration'])-seconds)<.01
            planned.append((src,dst,{'source':src.relative_to(ROOT).as_posix(),'destination':dst.relative_to(ROOT).as_posix(),
                'sha256':sha,'size_bytes':src.stat().st_size,'duration':float(info['format']['duration']),
                'resolution':[1920,1080],'fps':24,'video_codec':'h264','audio_codec':'aac','reencoded':False}))
    for src,dst,row in planned:
        dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():shutil.copyfile(src,dst)
        assert digest(dst)==row['sha256']
    report=ROOT/'work/presentation-export/manifest.json';report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps({'schema_version':1,'purpose':'private-presentation-copies','source_versions_preserved':True,
                                 'files':[p[2] for p in planned]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'folders':[g[0] for g in GROUPS],'mp4_count':len(planned),'all_hashes_identical':True,'reencoded':False},ensure_ascii=False))

if __name__=='__main__':main()
