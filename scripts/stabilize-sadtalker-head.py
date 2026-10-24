"""Conservative rigid stabilization for an already accepted, stationary head video."""
from __future__ import annotations
import argparse,hashlib,json,math,subprocess,time
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def measure(frame,template,mask,initial):
    small=cv2.resize(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY),template.shape[::-1]).astype(np.float32)/255
    score,warp=cv2.findTransformECC(template,small,initial.copy(),cv2.MOTION_EUCLIDEAN,
        (cv2.TERM_CRITERIA_COUNT|cv2.TERM_CRITERIA_EPS,60,1e-5),mask,5)
    return float(score),warp

def metrics(rows):
    xy=np.array([r['center_displacement_px'] for r in rows])
    return {'displacement_std_px':np.std(xy,axis=0).tolist(),
        'adjacent_displacement_rms_px':float(np.sqrt(np.mean(np.sum(np.diff(xy,axis=0)**2,axis=1)))),
        'max_displacement_px':float(np.max(np.linalg.norm(xy,axis=1))),
        'max_rotation_deg':max(abs(r['rotation_deg']) for r in rows)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();src=args.input.resolve();dest=args.output.resolve()
    if not dest.is_relative_to(ROOT/'outputs'):raise ValueError('私人影片須另存outputs')
    if dest.exists():raise FileExistsError('保留既有版本，請另取檔名')
    dest.parent.mkdir(parents=True,exist_ok=True);start=time.perf_counter();cv2.setNumThreads(1)
    capture=cv2.VideoCapture(str(src.relative_to(ROOT)))
    ok,first=capture.read()
    if not ok:raise RuntimeError('無法讀取影片')
    h,w=first.shape[:2];fps=capture.get(cv2.CAP_PROP_FPS);scale=round(w*.35)/w
    template=cv2.resize(cv2.cvtColor(first,cv2.COLOR_BGR2GRAY),(round(w*scale),round(h*scale))).astype(np.float32)/255
    th,tw=template.shape;mask=np.zeros_like(template,dtype=np.uint8)
    mask[round(th*.08):round(th*.38),round(tw*.18):round(tw*.83)]=255
    command=[str(ROOT/'tools/bin/ffmpeg.exe'),'-nostdin','-y','-v','error','-f','rawvideo','-pixel_format','bgr24',
        '-video_size',f'{w}x{h}','-framerate',str(fps),'-i','pipe:0','-i',str(src),'-map','0:v:0','-map','1:a:0',
        '-c:v','libx264','-crf','16','-preset','fast','-threads','2','-pix_fmt','yuv420p','-c:a','copy',
        '-movflags','+faststart',str(dest)]
    encoder=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    before=[];previous=np.eye(2,3,dtype=np.float32);frame=first;index=0
    try:
        while True:
            score,warp=measure(frame,template,mask,previous)
            center=np.array([tw/2,th/2]);displacement=(warp[:,:2]@center+warp[:,2]-center)/scale
            angle=math.degrees(math.atan2(float(warp[1,0]),float(warp[0,0])))
            if score<.8 or np.linalg.norm(displacement)>20 or abs(angle)>1.5:
                raise ValueError('穩定估計超出小幅範圍，保留原片並停止；不可自動套大型鏡頭移動')
            full=warp.copy();full[:,2]/=scale
            result=cv2.warpAffine(frame,full,(w,h),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0))
            encoder.stdin.write(result.tobytes());previous=warp
            before.append({'frame':index,'correlation':score,'center_displacement_px':displacement.tolist(),'rotation_deg':angle})
            index+=1;ok,frame=capture.read()
            if not ok:break
    finally:
        capture.release();encoder.stdin.close();err=encoder.stderr.read();encoder.wait()
    if encoder.returncode:raise RuntimeError(err.decode('utf-8',errors='replace'))
    after=[];cap=cv2.VideoCapture(str(dest.relative_to(ROOT)));previous=np.eye(2,3,dtype=np.float32)
    while True:
        ok,frame=cap.read()
        if not ok:break
        score,warp=measure(frame,template,mask,previous);previous=warp
        center=np.array([tw/2,th/2]);d=(warp[:,:2]@center+warp[:,2]-center)/scale
        after.append({'frame':len(after),'correlation':score,'center_displacement_px':d.tolist(),
            'rotation_deg':math.degrees(math.atan2(float(warp[1,0]),float(warp[0,0])))})
    cap.release()
    report={'input':src.relative_to(ROOT).as_posix(),'output':dest.relative_to(ROOT).as_posix(),
        'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
        'method':'ECC Euclidean alignment to first frame; hair ROI only; no temporal frame blend',
        'roi_normalized':[.18,.08,.83,.38],'frames':index,'fps':fps,'before':metrics(before),'after':metrics(after),
        'transforms_before':before,'transforms_after':after,'elapsed_sec':time.perf_counter()-start,
        'audio_stream_copied':True,'user_accepted':False,'body_integrated':False,
        'metric_scope':'hair ROI rigid displacement only; not facial deformation or subjective quality'}
    dest.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if not k.startswith('transforms_')},ensure_ascii=False))

if __name__=='__main__':main()
