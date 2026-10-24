"""Make an alpha video layer from an accepted head-on-black clip, without a model pass."""
from pathlib import Path
import argparse, hashlib, json, subprocess, time
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=Path('outputs/round08/head_local_blink.mp4'))
    p.add_argument('--output',type=Path,default=Path('outputs/round09/character/head_accepted_alpha.webm'))
    args=p.parse_args();src=args.input.resolve();dest=args.output.resolve()
    if not dest.is_relative_to(ROOT/'outputs') or dest.exists():
        raise ValueError('Use a new private output filename')
    expected='3b3957a908896d4e2a62199fda46b91a66c3200c6aa8e61c74394fa230106768'
    if hashlib.sha256(src.read_bytes()).hexdigest()!=expected:
        raise ValueError('Accepted round08 source hash mismatch')
    start=time.perf_counter();cv2.setNumThreads(1)
    cap=cv2.VideoCapture(str(src.relative_to(ROOT)));fps=cap.get(cv2.CAP_PROP_FPS)
    w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dest.parent.mkdir(parents=True,exist_ok=True)
    command=[str(ROOT/'tools/bin/ffmpeg.exe'),'-nostdin','-v','error','-n','-f','rawvideo',
        '-pix_fmt','bgra','-video_size',f'{w}x{h}','-framerate',str(fps),'-i','pipe:0',
        '-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-lossless','1','-auto-alt-ref','0',
        '-deadline','good','-cpu-used','4','-threads','2','-row-mt','1',str(dest)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    records=[];count=0
    try:
        while True:
            ok,frame=cap.read()
            if not ok:break
            # Only the exterior black background is removed. Fill all enclosed
            # dark areas so hair, nostrils, eyes and mouth never turn transparent.
            raw=(np.max(frame,axis=2)>10).astype(np.uint8)
            n,labels,stats,_=cv2.connectedComponentsWithStats(raw,8)
            biggest=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
            solid=(labels==biggest).astype(np.uint8)*255
            flooded=solid.copy();cv2.floodFill(flooded,np.zeros((h+2,w+2),np.uint8),(0,0),255)
            solid=cv2.bitwise_or(solid,cv2.bitwise_not(flooded))
            alpha=cv2.GaussianBlur(solid,(0,0),.65)
            ys,xs=np.nonzero(alpha>128)
            records.append({'frame':count,'bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],
                'mouth_alpha_min':int(alpha[850:1000,520:750].min()),
                'eye_alpha_min':int(alpha[600:695,420:860].min())})
            if records[-1]['mouth_alpha_min']!=255 or records[-1]['eye_alpha_min']!=255:
                raise AssertionError('A facial interior region became transparent')
            proc.stdin.write(np.dstack([frame,alpha]).tobytes());count+=1
    finally:
        cap.release();proc.stdin.close();err=proc.stderr.read();proc.wait()
    if proc.returncode:raise RuntimeError(err.decode(errors='replace'))
    if count!=110 or fps!=25:raise ValueError('Unexpected accepted source timing')
    report={'source':src.relative_to(ROOT).as_posix(),'source_sha256':expected,
        'output':dest.relative_to(ROOT).as_posix(),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
        'method':'largest connected foreground from >10 RGB max; flood-fill enclosed dark areas; 0.65px silhouette feather',
        'frames':count,'fps':fps,'duration_sec':count/fps,'codec':'VP9 lossless yuva420p; alpha_mode=1',
        'rgb_before_encoding_unchanged':True,'no_full_face_model':True,
        'scope':'edge matte only; dark hair and facial interiors filled opaque; subjectively inspect outline/neck on new body',
        'records':records,'elapsed_sec':time.perf_counter()-start}
    dest.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False))

if __name__=='__main__':main()
