"""Reuse calibrated local eyelids and a conservative matte on the complete dialogue.

Input is the separately stabilized full SadTalker head. Only the eye support is
composited; then the video edge is matted and held across original lead/tail.
"""
from pathlib import Path
import hashlib,importlib.util,json,math,subprocess,time
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('local_blink',ROOT/'scripts/compose-local-blink.py');blink=importlib.util.module_from_spec(spec);spec.loader.exec_module(blink)
def main():
    start=time.perf_counter();cv2.setNumThreads(1)
    cfg=json.loads((ROOT/'config/round11.json').read_text(encoding='utf-8'));eyes=json.loads((ROOT/'config/ade-blink-round08.json').read_text(encoding='utf-8'))
    src=ROOT/cfg['head_stabilized'];out=ROOT/cfg['head_alpha']
    if out.exists():raise FileExistsError('Preserve existing head layer; select a new version')
    out.parent.mkdir(parents=True,exist_ok=True);qa=ROOT/'outputs/round11/head-qa';qa.mkdir(exist_ok=True)
    reference=blink.load_image(ROOT/eyes['reference_image']);donor=blink.load_image(ROOT/eyes['closed_reference'])
    cap=cv2.VideoCapture(str(src.relative_to(ROOT)));fps=cap.get(cv2.CAP_PROP_FPS);count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    assert fps==25 and (w,h)==(1254,1254) and 290<=count<=300,(fps,w,h,count)
    command=[str(ROOT/'tools/bin/ffmpeg.exe'),'-nostdin','-v','error','-n','-f','rawvideo','-pix_fmt','bgra','-video_size',f'{w}x{h}','-framerate','25','-i','pipe:0','-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-lossless','1','-auto-alt-ref','0','-deadline','good','-cpu-used','4','-threads','2','-row-mt','1',str(out)]
    encoder=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    current=-1;cached=None;records=[];examples=[];outside_max=0
    def source_frame():
        nonlocal current,outside_max
        ok,frame=cap.read()
        if not ok:raise RuntimeError('Unexpected end of full head')
        current+=1;closure=0
        for b in cfg['blink_source_start_frames']:
            if 0<=current-b<len(eyes['closure']):closure=eyes['closure'][current-b]
        composed,support,tracking=blink.compose(frame,reference,donor,closure,eyes['eyes'])
        diff=np.abs(composed.astype(np.int16)-frame.astype(np.int16));outside=int(diff[support==0].max()) if np.any(support==0) else 0
        outside_max=max(outside_max,outside);assert outside==0
        raw=(np.max(composed,axis=2)>10).astype(np.uint8);n,labels,stats,_=cv2.connectedComponentsWithStats(raw,8)
        main=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]));solid=(labels==main).astype(np.uint8)*255
        fill=solid.copy();cv2.floodFill(fill,np.zeros((h+2,w+2),np.uint8),(0,0),255);solid=cv2.bitwise_or(solid,cv2.bitwise_not(fill));alpha=cv2.GaussianBlur(solid,(0,0),.65)
        assert int(alpha[850:1000,520:750].min())==255 and int(alpha[600:695,420:860].min())==255
        ys,xs=np.nonzero(alpha>=128);records.append({'source_frame':current,'closure':closure,'tracking':tracking,'outside_eye_max_difference':outside,'bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]})
        if any(b-1<=current<=b+len(eyes['closure']) for b in cfg['blink_source_start_frames']):
            blink.save_image(qa/f'source_f{current:03d}.png',composed)
            examples.append((f'f{current} / {current/25+.3:.2f}s',composed.copy()))
        return np.dstack([composed,alpha])
    try:
        for j in range(325):
            wanted=max(0,min(count-1,math.floor((j/25-.3)*25+1e-6)))
            while current<wanted or cached is None:cached=source_frame()
            encoder.stdin.write(cached.tobytes())
    finally:
        cap.release();encoder.stdin.close();err=encoder.stderr.read();encoder.wait()
    if encoder.returncode:raise RuntimeError(err.decode(errors='replace'))
    blink.contact_sheet(examples,qa/'blink_eyes.png',eyes=True,cols=6)
    report={'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'output':out.relative_to(ROOT).as_posix(),'output_sha256':sha(out),'source_frames':count,'processed_source_frames':len(records),'output_frames':325,'fps':25,'duration':13,'lead_in_sec':.3,'tail_held_to':13,'blink_source_start_frames':cfg['blink_source_start_frames'],'closure_pattern':eyes['closure'],'method':'Existing calibrated opaque eyelid occlusion, no change outside eye support; largest silhouette matte and filled dark interiors; 0.65px edge feather; clone first/last frames for original lead/tail','outside_eye_max_preencode_difference':outside_max,'eye_reference_sha256':sha(ROOT/eyes['reference_image']),'closed_donor_sha256':sha(ROOT/eyes['closed_reference']),'records':records,'elapsed_sec':time.perf_counter()-start,'user_accepted':False}
    out.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False))
if __name__=='__main__':main()
