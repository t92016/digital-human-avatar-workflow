"""Full13s teaching QA: source reuse,936 opaque silhouettes,936 real MP4 frames."""
from pathlib import Path
import hashlib,json,math,re,subprocess
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/round11';WORK=ROOT/'work/round11';QA=OUT/'qa';QA.mkdir(exist_ok=True)
FF=ROOT/'tools/bin/ffmpeg.exe';FP=ROOT/'tools/bin/ffprobe.exe'
cfg=json.loads((ROOT/'config/round11.json').read_text(encoding='utf-8'))
NAMES=['mode1_hands.mp4','mode2_natural.mp4','mode3_lively.mp4']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readimg(p):return cv2.imdecode(np.frombuffer(p.read_bytes(),np.uint8),cv2.IMREAD_UNCHANGED)
def png(p,a):p.write_bytes(cv2.imencode('.png',a)[1].tobytes())
def pcm(p):return np.frombuffer(subprocess.check_output([str(FF),'-v','error','-i',str(p),'-map','0:a:0','-t','13','-f','s16le','-ar','16000','-ac','1','pipe:1']),np.int16).astype(np.float64)
def points(diag):
    seeds={n:g['anchor'] for n,g in diag['geometry'].items()};seeds.update({n+'_joint':g['joint'] for n,g in diag['geometry'].items()});seeds['neck']=[512,540]
    a=math.radians(diag['state']['head']);seeds['face']=[512+1.03*240*math.sin(a),540-1.03*240*math.cos(a)]
    return {n:(round(cfg['actor_left']+cfg['actor_scale']*x)-62,round(cfg['actor_top']+cfg['actor_scale']*(y+diag['dip']))-493) for n,(x,y) in seeds.items()}
def seedcheck(labels,main,seeds):
    return {n:bool((patch:=labels[max(0,y-2):y+3,max(0,x-2):x+3]).size and np.count_nonzero(patch==main)>=3) for n,(x,y) in seeds.items()}
def components(mask):
    n,l,s,_=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8);main=1+int(np.argmax(s[1:,cv2.CC_STAT_AREA]));areas=sorted([int(x) for x in s[1:,cv2.CC_STAT_AREA] if x>=12],reverse=True)
    x,y,w,h,_=map(int,s[main]);return n,l,s,main,areas,bool(x==0 or y==0 or x+w>=535 or y+h>=550)
def sheet(frames,p,crop,wh=(480,270)):
    w,h=wh;im=Image.new('RGB',(w*4,(h+24)*math.ceil(len(frames)/4)),(25,30,37));d=ImageDraw.Draw(im)
    for k,(i,a) in enumerate(frames):
        b=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).crop(crop).resize((w,h),Image.Resampling.LANCZOS);x=k%4*w;y=k//4*(h+24);im.paste(b,(x,y+24));d.text((x+7,y+5),f'frame{i} / {i/24:.3f}s',fill='white')
    im.save(p)

records=json.loads((WORK/'alpha-frame-records.json').read_text(encoding='utf-8'));assert len(records)==936
alpha_rows=[];failures=[];index={}
for r in records:
    a=readimg(ROOT/r['path']);assert a.shape==(550,535,4)
    n,l,s,main,areas,touch=components(a[:,:,3]>=128);seeds=seedcheck(l,main,points(r['diagnostics']))
    row={'mode':r['mode'],'frame':r['frame'],'path':r['path'],'sha256':sha(ROOT/r['path']),'opaque_components_ge12px':len(areas),'areas':areas,'seed_checks':seeds,'touches_character_region':touch}
    alpha_rows.append(row);index[(r['mode'],r['frame'])]=(r,row)
    if len(areas)!=1 or not all(seeds.values()) or touch:failures.append({'type':'alpha',**row})
print('Alpha936 frames; failures',len(failures),flush=True)
(OUT/'alpha-continuity-verification.json').write_text(json.dumps({'frames':936,'threshold':128,'minimum_component_area':12,'morphology_used':False,'frame_records':alpha_rows,'failures':failures},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not failures,json.dumps(failures[:2])
bg=readimg(WORK/'character-background.png')[:,:,:3].astype(np.int16);reports=[]
legacy=json.loads((WORK/'legacy-source.json').read_text(encoding='utf-8'))
for mode,name in enumerate(NAMES,1):
    p=OUT/name;probe=json.loads(subprocess.check_output([str(FP),'-v','error','-show_streams','-show_format','-of','json',str(p)]));v=next(x for x in probe['streams'] if x['codec_type']=='video')
    assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1920,1080,'24/1',312)
    assert abs(float(probe['format']['duration'])-13)<.01
    dec=subprocess.run([str(FF),'-v','error','-i',str(p),'-f','null','-'],capture_output=True,check=True);assert not dec.stderr
    old=ROOT/cfg['legacy_folder']/cfg['filenames'][mode-1]
    if not old.exists():old=ROOT/cfg['legacy_renamed_folder']/cfg['filenames'][mode-1]
    assert sha(old)==legacy['files'][mode-1]['sha256'];a,b=pcm(old),pcm(p);ns=min(len(a),len(b));corr=float(np.corrcoef(a[:ns],b[:ns])[0,1]);assert corr>.999
    text=(ROOT/f'samples/round11/mode{mode}/index.html').read_text(encoding='utf-8');original=(ROOT/f'samples/round05/mode{mode}/index.html').read_text(encoding='utf-8')
    # Studio adds editor-only IDs to some saved originals. Ignore only that
    # attribute; all actual SVG, content, layout and timing stay byte-compared.
    text=re.sub(r' data-hf-id="[^"]*"','',text);original=re.sub(r' data-hf-id="[^"]*"','',original)
    scene_pattern=r'<section class="scene clip"[\s\S]*?</section>';caption_pattern=r'<div id="caption-clip-\d+"[\s\S]*?</div>'
    assert re.findall(scene_pattern,text)==re.findall(scene_pattern,original),'Teaching panels differ'
    assert re.findall(caption_pattern,text)==re.findall(caption_pattern,original),'Caption timing/text differ'
    cap=cv2.VideoCapture(str(p.relative_to(ROOT)));i=0;rows=[];evidence=[]
    while True:
        ok,frame=cap.read()
        if not ok:break
        roi=frame[493:1043,62:597];n,l,s,main,areas,touch=components(np.max(np.abs(roi.astype(np.int16)-bg),axis=2)>24)
        r,ar=index[(mode,i)];seeds=seedcheck(l,main,points(r['diagnostics']));alpha=readimg(ROOT/ar['path'])[:,:,3];islands=[];bad=[]
        for label in range(1,n):
            if label==main or s[label,cv2.CC_STAT_AREA]<12:continue
            x,y,w,h,area=map(int,s[label]);coverage=float(np.mean(alpha[l==label]>=128));item={'area':area,'bbox':[x+62,y+493,w,h],'opaque_alpha_coverage':coverage}
            if area<80 and y+493>=950 and coverage>=.9:islands.append(item)
            else:bad.append(item)
        row={'frame':i,'color_components_ge12px':len(areas),'opaque_alpha_components':ar['opaque_components_ge12px'],'seed_checks':seeds,'touches_character_region':touch,'small_outsole_color_islands':islands,'unexplained_components':bad};rows.append(row)
        if bad or not all(seeds.values()) or touch:
            failures.append({'type':'mp4','mode':mode,**row})
            if len(failures)<8:png(QA/f'failure_m{mode}_f{i:03d}.png',frame)
        if i in [0,24,46,72,96,120,144,168,192,216,240,264,288,311]:
            png(QA/f'mode{mode}_f{i:03d}.png',frame);evidence.append((i,frame.copy()))
        i+=1
    cap.release();assert i==312
    sheet(evidence,QA/f'mode{mode}_full_sequence.png',(0,0,1920,1080))
    sheet(evidence,QA/f'mode{mode}_body_sequence.png',(62,493,597,1043),(300,310))
    reports.append({'mode':mode,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'probe':probe,'frames':i,'complete_decode_errors':0,'audio_correlation_to_original_video':corr,'teaching_panels_identical':True,'captions_identical':True,'max_color_components':max(r['color_components_ge12px'] for r in rows),'joint_seed_fail_frames':sum(not all(r['seed_checks'].values()) for r in rows),'region_touch_frames':sum(r['touches_character_region'] for r in rows),'frame_records':rows})
    print('MP4 mode',mode,'312 frames; audio',corr,'failures',len(failures),flush=True)
geom=json.loads((WORK/'geometry-check.json').read_text(encoding='utf-8'));gs=[g for r in geom['reports'] for f in r['rows'] for g in f['geometry'].values()]
report={'round':'round11','frames':sum(r['frames'] for r in reports),'alpha_frames':936,'geometry_poses':1953,'min_mesh_area_ratio':min(g['min_area_ratio'] for g in gs),'max_anchor_gap':max(g['anchor_gap'] for g in gs),'actual_mp4_reports':reports,'failures':failures,'scope':'All export frames, no morphology; transparent alpha and 10 joint/face/neck seeds cross-check RGB foreground. Small shoe color islands are retained and explained only within connected opaque shoes. Current character/three cycles only.','user_accepted':False}
(OUT/'technical-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');assert not failures,json.dumps(failures[:3])
