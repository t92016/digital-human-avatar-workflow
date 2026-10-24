"""Verify opaque alpha connectivity, without filling gaps or altering frames."""
from pathlib import Path
import hashlib,json,math
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1]
records=json.loads((ROOT/'work/round10/alpha-frame-records.json').read_text(encoding='utf-8'))
assert len(records)==330
rows=[];failures=[]
for r in records:
    p=ROOT/r['path'];a=cv2.imdecode(np.frombuffer(p.read_bytes(),np.uint8),cv2.IMREAD_UNCHANGED)
    crop=r.get('crop',{'x':990,'y':100,'width':860,'height':895})
    assert a.shape==(crop['height'],crop['width'],4)
    mask=(a[:,:,3]>=128).astype(np.uint8)
    count,labels,stats,_=cv2.connectedComponentsWithStats(mask,8)
    areas=sorted([int(s[cv2.CC_STAT_AREA]) for s in stats[1:] if s[cv2.CC_STAT_AREA]>=20],reverse=True)
    main=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]));sx,sy,sw,sh,area=map(int,stats[main])
    diag=r['diagnostics'];dip=diag['dip'];seeds={n:g['anchor'] for n,g in diag['geometry'].items()}
    seeds.update({n+'_joint':g['joint'] for n,g in diag['geometry'].items()});seeds['neck']=[512,540]
    angle=math.radians(diag['state']['head']);seeds['face']=[512+1.03*240*math.sin(angle),540-1.03*240*math.cos(angle)]
    seed_checks={}
    for name,(x,y) in seeds.items():
        px=round(1100+.58*x)-crop['x'];py=round(102+.58*(y+dip))-crop['y']
        patch=labels[max(0,py-4):py+5,max(0,px-4):px+5];seed_checks[name]=bool(patch.size and np.count_nonzero(patch==main)>=9)
    touches=sx==0 or sy==0 or sx+sw>=crop['width'] or sy+sh>=crop['height']
    item={'mode':r['mode'],'frame':r['frame'],'path':r['path'],'crop':crop,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'opaque_components_ge20px':len(areas),'component_areas':areas,'seed_checks':seed_checks,'silhouette_touches_crop':bool(touches)}
    rows.append(item)
    if len(areas)!=1 or not all(seed_checks.values()) or touches:failures.append(item)
report={'scope':'330 transparent browser frames, same source and time as exports, software WebGL. Alpha>=128, 8-connectivity, area>=20px, no morphology or hole fill; ten face/neck/root/elbow/knee seed neighborhoods.','frames':len(rows),'max_components':max(r['opaque_components_ge20px'] for r in rows),'failures':failures,'frame_records':rows}
(ROOT/'outputs/round10/alpha-continuity-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['frames','max_components']}),'; failure frames:',len(failures))
assert not failures,json.dumps(failures[:2])
