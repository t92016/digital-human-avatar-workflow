"""Check real round10 MP4 frames, fine-time joints and original accepted media."""
from pathlib import Path
import argparse,hashlib,json,math,subprocess,wave
import cv2,numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/round10';QA=OUT/'qa';QA.mkdir(exist_ok=True)
FFMPEG=str(ROOT/'tools/bin/ffmpeg.exe');FFPROBE=str(ROOT/'tools/bin/ffprobe.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,a):p.write_bytes(cv2.imencode('.png',a)[1].tobytes())
def sheet(frames,path,crop,cols=4):
    w,h=(385,440);im=Image.new('RGB',(w*cols,(h+25)*math.ceil(len(frames)/cols)),(25,30,37));d=ImageDraw.Draw(im)
    for k,(i,a) in enumerate(frames):
        b=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).crop(crop).resize((w,h),Image.Resampling.LANCZOS)
        x=k%cols*w;y=k//cols*(h+25);im.paste(b,(x,y+25));d.text((x+7,y+6),f'frame {i} / {i/25:.2f}s',fill='white')
    im.save(path)

with wave.open(str(ROOT/'outputs/round06/sadtalker-head-v2/jiahao-sample.wav'),'rb') as f:expected=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float64)
geom=json.loads((ROOT/'work/round10/joint-geometry-check.json').read_text(encoding='utf-8'))
alpha_report=json.loads((OUT/'alpha-continuity-verification.json').read_text(encoding='utf-8'))
assert alpha_report['frames']==330 and not alpha_report['failures']
alpha_records={(r['mode'],r['frame']):r for r in alpha_report['frame_records']}
parser=argparse.ArgumentParser();parser.add_argument('--modes',nargs='+',type=int,choices=[1,2,3],default=[1,2,3]);args=parser.parse_args()
reports=[];failures=[]
for mode in args.modes:
    p=OUT/f'mode{mode}-final.mp4';probe=json.loads(subprocess.run([FFPROBE,'-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,check=True).stdout)
    v=next(x for x in probe['streams'] if x['codec_type']=='video')
    assert [v['width'],v['height']]==[1920,1080] and v['avg_frame_rate']=='25/1' and int(v['nb_frames'])==110
    assert abs(float(probe['format']['duration'])-4.4)<.03
    decoded=subprocess.run([FFMPEG,'-v','error','-i',str(p),'-f','null','-'],capture_output=True,check=True);assert not decoded.stderr
    pcm=subprocess.run([FFMPEG,'-v','error','-i',str(p),'-map','0:a:0','-t','4.4','-f','s16le','-ar','16000','-ac','1','pipe:1'],capture_output=True,check=True).stdout
    a=np.frombuffer(pcm,np.int16).astype(np.float64);n=min(len(expected),len(a));corr=float(np.corrcoef(expected[:n],a[:n])[0,1]);assert corr>.999
    cap=cv2.VideoCapture(str(p.relative_to(ROOT)));records=[];evidence=[];blink=[];i=0
    gRows=geom['reports'][mode-1]['rows']
    while True:
        ok,frame=cap.read()
        if not ok:break
        # No morphology: a gap may not be silently closed by this check.
        roi=frame[80:995,990:1850];mask=(np.max(np.abs(roi.astype(np.int16)-np.array([247,245,242])),axis=2)>32).astype(np.uint8)
        count,labels,stats,_=cv2.connectedComponentsWithStats(mask,8)
        areas=sorted([int(s[cv2.CC_STAT_AREA]) for s in stats[1:] if s[cv2.CC_STAT_AREA]>=20],reverse=True)
        main=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]));sx,sy,sw,sh,area=map(int,stats[main])
        # Pale outsole colors can match the pale background and split a color
        # mask, while the captured opaque alpha remains connected. Retain all
        # observations; only explain tiny islands inside that opaque shoe.
        ar=alpha_records[(mode,i)];alpha=cv2.imdecode(np.frombuffer((ROOT/ar['path']).read_bytes(),np.uint8),cv2.IMREAD_UNCHANGED)[:,:,3]
        color_islands=[];unexplained=[]
        for label in range(1,count):
            if label==main or stats[label,cv2.CC_STAT_AREA]<20:continue
            ex,ey,ew,eh,ea=map(int,stats[label]);iy,ix=np.nonzero(labels==label);iy=iy+80-ar['crop']['y'];ix=ix+990-ar['crop']['x']
            valid=(iy>=0)&(iy<alpha.shape[0])&(ix>=0)&(ix<alpha.shape[1]);coverage=float(np.count_nonzero(alpha[iy[valid],ix[valid]]>=128)/ea)
            island={'area':ea,'bbox':[ex+990,ey+80,ew,eh],'opaque_alpha_coverage':coverage}
            if ea<120 and ey+80>=800 and coverage>=.9:color_islands.append(island)
            else:unexplained.append(island)
        row=gRows[i*2];dip=row['dip'];seeds={name:g['anchor'] for name,g in row['geometry'].items()}
        seeds.update({name+'_joint':g['joint'] for name,g in row['geometry'].items()});seeds['neck']=[512,540]
        rad=math.radians(row['state']['head']);seeds['face']=[512+1.03*240*math.sin(rad),540-1.03*240*math.cos(rad)]
        seed_ok={}
        for name,(x,y) in seeds.items():
            px=round(1100+.58*x)-990;py=round(102+.58*(y+dip))-80
            patch=labels[max(0,py-4):py+5,max(0,px-4):px+5]
            seed_ok[name]=bool(patch.size and np.count_nonzero(patch==main)>=9)
        touches=sx==0 or sy==0 or sx+sw>=860 or sy+sh>=915
        item={'frame':i,'foreground_components_ge20px':len(areas),'component_areas':areas,'opaque_alpha_components_ge20px':ar['opaque_components_ge20px'],'explained_small_outsole_color_islands':color_islands,'unexplained_color_islands':unexplained,'all_joint_and_face_seeds_in_main':all(seed_ok.values()),'seed_checks':seed_ok,'silhouette_touches_roi_boundary':bool(touches),'bbox':[sx+990,sy+80,sw,sh]}
        if unexplained or ar['opaque_components_ge20px']!=1 or not all(seed_ok.values()) or touches:
            failures.append({'mode':mode,**item})
            if len(failures)<10:save(QA/f'failure_mode{mode}_f{i:03d}.png',frame)
        records.append(item)
        if i in [0,18,28,35,46,55,65,75,85,95,109]:save(QA/f'mode{mode}_f{i:03d}.png',frame);evidence.append((i,frame.copy()))
        if 42<=i<=52:blink.append((i,frame.copy()))
        i+=1
    cap.release();assert i==110
    sheet(evidence,QA/f'mode{mode}_body_sequence.png',(1020,80,1800,995))
    sheet(blink,QA/f'mode{mode}_blink_neck_sequence.png',(1220,115,1580,520))
    reports.append({'mode':mode,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'frames':i,'full_decode_errors':0,'audio_correlation_to_jiahao':corr,'max_components_ge20px':max(x['foreground_components_ge20px'] for x in records),'joint_seed_fail_frames':sum(not x['all_joint_and_face_seeds_in_main'] for x in records),'roi_edge_touch_frames':sum(x['silhouette_touches_roi_boundary'] for x in records),'frame_records':records,'probe':probe})
    print('Mode',mode,':',i,'frames; components',reports[-1]['max_components_ge20px'],'; seed failures',reports[-1]['joint_seed_fail_frames'],flush=True)
baseline=json.loads((OUT/'build-manifest.json').read_text(encoding='utf-8'))['baseline_videos']
for x in baseline:assert sha(ROOT/x['path'])==x['sha256']
assert sha(ROOT/'outputs/round08/head_local_blink.mp4')=='3b3957a908896d4e2a62199fda46b91a66c3200c6aa8e61c74394fa230106768'
allgeo=[x for r in geom['reports'] for row in r['rows'] for x in row['geometry'].values()]
report={'round':'round10','actual_mp4_reports':reports,'actual_frames_checked':sum(x['frames'] for x in reports),'fine_time_poses':663,'min_mesh_area_ratio':min(x['min_area_ratio'] for x in allgeo),'max_anchor_gap_source_px':max(x['anchor_gap'] for x in allgeo),'failures':failures,'scope':'Listed MP4 frames: no morphology, threshold32, components>=20px, ten face/neck/root/elbow/knee seed neighborhoods; cross-check full opaque alpha per frame. Tiny outsole color islands <120px at y>=800 are explained only when >=90% lies inside the connected opaque alpha. All raw color counts retained. Geometry sampled every20ms. Not a proof for unseen motions, future characters or infinite duration.','user_accepted':False,'baselines_unchanged':True}
(OUT/'technical-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not failures,json.dumps(failures[:3])
