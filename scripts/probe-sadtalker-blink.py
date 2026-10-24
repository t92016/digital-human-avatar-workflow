"""Diagnostic single-frame blink probes; never apply high gain to a production clip."""
import argparse,json,os,random,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True,help='已保留verbose中間檔的短測目錄')
    parser.add_argument('--output',type=Path,required=True,help='work內新的ASCII目錄')
    parser.add_argument('--frame',type=int,default=66)
    parser.add_argument('--gains',type=float,nargs='+',default=[0,1,2.5])
    args=parser.parse_args();baseline=args.baseline.resolve();out=args.output.resolve()
    if not out.is_relative_to(ROOT/'work') or not out.relative_to(ROOT).as_posix().isascii():raise ValueError('請使用work內ASCII目錄')
    if out.exists() and any(out.iterdir()):raise FileExistsError('請另取新版本目錄')
    m=json.loads((baseline/'manifest.json').read_text(encoding='utf-8'))
    if m['source_commit']!='cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8' or m['size']!=256 or m['preprocess']!='full':
        raise ValueError('此診斷僅驗證固定commit／256／full模式')
    if any(not 0<=g<=8 for g in args.gains):raise ValueError('診斷範圍0～8；大於1不是官方建議值')
    source=ROOT/'work/sadtalker/source';os.chdir(source);sys.path.insert(0,str(source));out.mkdir(parents=True,exist_ok=True)
    os.environ.update(TORCH_FORCE_WEIGHTS_ONLY_LOAD='1',MPLCONFIGDIR=str(out/'mpl'))
    import cv2,numpy as np,torch
    from scipy.io import loadmat,savemat
    from safetensors import safe_open
    from src.generate_batch import generate_blink_seq_randomly
    from src.generate_facerender_batch import get_facerender_data
    from src.facerender.animate import AnimateFromCoeff
    from src.facerender.modules.make_animation import make_animation
    from src.utils.init_path import init_path
    def rel(p):return os.path.relpath(p,source).replace('\\','/')
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    seed=m['seed'];random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    cache=(ROOT/m['raw_model_output']).with_suffix('')
    cp=next(cache.glob('*##*.mat'));first=cache/'first_frame_dir/original.mat';image=first.with_suffix('.png')
    coeff=loadmat(cp)['coeff_3dmm'];n=len(coeff)
    if not 13<=args.frame<n-13:raise ValueError('探測時間點需離片頭片尾至少13幀')
    old=generate_blink_seq_randomly(n).reshape(-1)
    with safe_open(str(ROOT/'models/sadtalker/SadTalker_V0.0.2_256.safetensors'),framework='pt') as sf:
        direction=sf.get_tensor('audio2exp.mapping1.weight')[:,-1].numpy()
    paths=init_path(rel(ROOT/'models/sadtalker'),'src/config',256,False,'full')
    renderer=AnimateFromCoeff(paths,'cpu');probes=[];start=time.perf_counter()
    for gain in args.gains:
        ratio=np.zeros(n,dtype=np.float32);ratio[args.frame-3:args.frame+4]=np.array([.1,.5,.9,1,.9,.5,.1])*gain
        changed=coeff.copy();changed[:,:64]+=(ratio-old)[:,None]*direction[None]
        target=out/f'gain_{gain:g}.mat';savemat(target,{'coeff_3dmm':changed})
        data=get_facerender_data(rel(target),rel(image),rel(first),rel(ROOT/m['run_directory']/'sample.wav'),1,
            still_mode=True,preprocess='full',size=256)
        semantic=data['target_semantics_list'][:,args.frame:args.frame+1]
        with torch.no_grad():frames=make_animation(data['source_image'],data['source_semantics'],semantic,
            renderer.generator,renderer.kp_extractor,renderer.he_estimator,renderer.mapping)
        rgb=(frames[0,0].permute(1,2,0).numpy()*255).clip(0,255).astype(np.uint8)
        name=f'gain_{gain:g}.png';cv2.imwrite(rel(out/name),cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR))
        probes.append({'gain':gain,'outside_default_ratio_range':gain>1,'file':name})
    record={'baseline':baseline.relative_to(ROOT).as_posix(),'source_commit':m['source_commit'],'seed':seed,
        'frame':args.frame,'time_sec':args.frame/25,'pulse':[.1,.5,.9,1,.9,.5,.1],
        'method':'exact ratio contribution adjustment using Audio2Exp final linear layer; 27-frame renderer context',
        'old_blink_nonzero_frames':np.flatnonzero(old).tolist(),'probes':probes,'elapsed_sec':time.perf_counter()-start,
        'diagnostic_only':True,'full_blink_animation_verified':False}
    (out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))

if __name__=='__main__':main()
