"""Verify actual round09 MP4s and save frame evidence, not just HTML screenshots."""
from pathlib import Path
import hashlib,json,subprocess,wave
import cv2
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/round09';QA=OUT/'qa';QA.mkdir(exist_ok=True)
FFMPEG=str(ROOT/'tools/bin/ffmpeg.exe');FFPROBE=str(ROOT/'tools/bin/ffprobe.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,a):p.write_bytes(cv2.imencode('.png',a)[1].tobytes())
def sheet(frames,path,crop=None,cols=4):
    w,h=(480,270) if crop is None else (380,430)
    im=Image.new('RGB',(w*cols,(h+25)*((len(frames)+cols-1)//cols)),(25,30,37));d=ImageDraw.Draw(im)
    for k,(i,a) in enumerate(frames):
        b=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB))
        if crop:b=b.crop(crop)
        b=b.resize((w,h),Image.Resampling.LANCZOS);x=k%cols*w;y=k//cols*(h+25)
        im.paste(b,(x,y+25));d.text((x+7,y+6),f'frame {i} / {i/25:.2f}s',fill='white')
    im.save(path)

with wave.open(str(ROOT/'outputs/round06/sadtalker-head-v2/jiahao-sample.wav'),'rb') as f:
    expected=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float64)
reports=[]
for mode in [1,2,3]:
    path=OUT/f'mode{mode}.mp4'
    probe=json.loads(subprocess.run([FFPROBE,'-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,check=True).stdout)
    v=next(x for x in probe['streams'] if x['codec_type']=='video')
    assert [v['width'],v['height']]==[1920,1080] and v['avg_frame_rate']=='25/1' and int(v['nb_frames'])==110
    assert abs(float(probe['format']['duration'])-4.4)<.03
    dec=subprocess.run([FFMPEG,'-v','error','-i',str(path),'-f','null','-'],capture_output=True,check=True)
    assert not dec.stderr,dec.stderr
    pcm=subprocess.run([FFMPEG,'-v','error','-i',str(path),'-map','0:a:0','-t','4.4','-f','s16le','-ar','16000','-ac','1','pipe:1'],capture_output=True,check=True).stdout
    actual=np.frombuffer(pcm,np.int16).astype(np.float64);n=min(len(expected),len(actual))
    corr=float(np.corrcoef(expected[:n],actual[:n])[0,1]);assert corr>.999
    cap=cv2.VideoCapture(str(path.relative_to(ROOT)));rows=[];evidence=[];blink=[];i=0
    while True:
        ok,a=cap.read()
        if not ok:break
        roi=a[85:1000,930:1810]
        foreground=(np.max(np.abs(roi.astype(np.int16)-np.array([247,245,242])),axis=2)>40).astype(np.uint8)*255
        # Close single-pixel codec speckles, fill enclosed highlight holes.
        foreground=cv2.morphologyEx(foreground,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
        num,labels,stats,_=cv2.connectedComponentsWithStats(foreground,8)
        parts=sorted([int(x) for x in stats[1:,cv2.CC_STAT_AREA] if x>=120],reverse=True)
        main=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]));sx,sy,sw,sh,area=map(int,stats[main])
        rows.append({'frame':i,'foreground_components_ge120px':len(parts),'component_areas':parts,
            'main_bbox':[sx+930,sy+85,sw,sh],'silhouette_touches_roi_boundary':bool(sx==0 or sy==0 or sx+sw>=880 or sy+sh>=915)})
        if i in [0,18,35,46,63,80,109]:
            save(QA/f'mode{mode}_f{i:03d}.png',a);evidence.append((i,a.copy()))
        if 42<=i<=52:blink.append((i,a.copy()))
        i+=1
    cap.release();assert i==110
    sheet(evidence,QA/f'mode{mode}_full_sequence.png')
    sheet(evidence,QA/f'mode{mode}_body_sequence.png',crop=(940,75,1760,1000))
    # A face/neck crop verifies that the accepted blink remains visible after body compositing.
    sheet(blink,QA/f'mode{mode}_blink_sequence.png',crop=(1120,75,1510,480))
    reports.append({'mode':mode,'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size,
        'frames':i,'full_decode_errors':0,'audio_samples_compared':n,'audio_correlation_to_jiahao':corr,
        'max_components_ge120px':max(r['foreground_components_ge120px'] for r in rows),
        'roi_edge_touch_frames':sum(r['silhouette_touches_roi_boundary'] for r in rows),'frame_records':rows,'probe':probe})
accepted=ROOT/'outputs/round08/head_local_blink.mp4'
assert sha(accepted)=='3b3957a908896d4e2a62199fda46b91a66c3200c6aa8e61c74394fa230106768'
report={'round':'round09','actual_mp4_reports':reports,'accepted_round08_sha256_unchanged':sha(accepted),
    'scope':'Connected components >=120px in rendered actor ROI after 3x3 closing, threshold40 against flat background; not anatomical or subjective quality certification',
    'user_accepted':False,'new_tts_generated':False,'new_sadtalker_inference':False}
(OUT/'technical-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{k:v for k,v in r.items() if k not in ['frame_records','probe']} for r in reports],ensure_ascii=False,indent=2))
