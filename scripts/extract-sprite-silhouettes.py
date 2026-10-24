"""Analyze generated atlas alpha to produce native SVG clipping paths; leave PNGs unchanged."""
from pathlib import Path
import hashlib,json
import cv2
import numpy as np

root=Path(__file__).resolve().parents[1]
cfg=json.loads((root/'config/round09.json').read_text(encoding='utf-8'))
src=root/'outputs/round09/character/body_parts_atlas_v1.png'
a=cv2.imdecode(np.frombuffer(src.read_bytes(),np.uint8),cv2.IMREAD_UNCHANGED)
paths={}
for name in ['arm_left','arm_right','pelvis','leg_left','leg_right']:
    x0,y0,x1,y1=cfg[name]['crop']
    mask=(a[y0:y1,x0:x1,3]>100).astype(np.uint8)*255
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    c=max(contours,key=cv2.contourArea)
    c=cv2.approxPolyDP(c,.45,True)[:,0,:]+np.array([x0,y0])
    paths[name]='M'+' L'.join(f'{x} {y}' for x,y in c)+' Z'
dest=root/'work/round09/sprite-contours.json'
dest.write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
    'threshold':100,'method':'largest external alpha contour, native SVG clip only; original atlas untouched',
    'paths':paths},indent=2)+'\n',encoding='utf-8')
print('Extracted five native SVG silhouette clips; original raster assets unchanged.')
