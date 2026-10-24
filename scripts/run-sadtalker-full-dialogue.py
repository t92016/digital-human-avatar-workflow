"""Explicit full-dialogue continuation after the accepted 4.4s head test.

The original 3-5s trial entry stays unchanged. This entry supports <=30s of
already-authorized audio, same pinned model/source, CPU only, new outputs only.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,shutil,subprocess,time,uuid
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'work/sadtalker/source'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def relative(p):return os.path.relpath(p,SOURCE).replace('\\','/')
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('outputs/round11/full-head-v1'));p.add_argument('--threads',type=int,default=4,choices=[2,3,4]);a=p.parse_args()
    out=a.output.resolve();image=ROOT/'outputs/round05/character/head_closed_v1.png';audio=ROOT/'outputs/round05/audio/ttsmaker_original.wav'
    if not out.is_relative_to(ROOT/'outputs') or (out.exists() and any(out.iterdir())):raise ValueError('Use an empty new private output directory')
    assert sha(image)=='429a0de57b33eea27a495427068a5e69c609a0df9c60fb6e4b849915e19a47ac'
    venv=ROOT/'work/sadtalker/venv/Scripts/python.exe';ff=ROOT/'tools/bin/ffmpeg.exe';fp=ROOT/'tools/bin/ffprobe.exe'
    info=json.loads(subprocess.check_output([str(fp),'-v','error','-show_format','-of','json',str(audio)]));seconds=float(info['format']['duration'])
    if not 5<seconds<=30:raise ValueError('This continuation expects 5-30s of the accepted original audio')
    subprocess.run([str(venv),str(ROOT/'scripts/patch-sadtalker-compat.py')],check=True)
    models=json.loads((ROOT/'work/sadtalker/model-download-manifest.json').read_text(encoding='utf-8'))
    for r in models['files']:assert sha(ROOT/r['path'])==r['sha256'],r['name']
    out.mkdir(parents=True,exist_ok=True);run=ROOT/'work/sadtalker/runs'/('full_'+uuid.uuid4().hex[:12]);run.mkdir(parents=True)
    shutil.copy2(image,run/'original.png')
    subprocess.run([str(ff),'-nostdin','-v','error','-n','-i',str(audio),'-ar','16000','-ac','1',str(run/'full.wav')],check=True)
    driver=run/'driver.py';driver.write_text('import os,sys,random,runpy,numpy as np,torch\n'
        'sys.path.insert(0,os.getcwd())\nrandom.seed(42);np.random.seed(42);torch.manual_seed(42)\n'
        f'torch.set_num_threads({a.threads});torch.set_num_interop_threads(1)\n'
        'print("CPU torch",torch.__version__,"threads",torch.get_num_threads(),flush=True)\n'
        'runpy.run_path("inference.py",run_name="__main__")\n',encoding='utf-8')
    command=[str(venv),relative(driver),'--source_image',relative(run/'original.png'),'--driven_audio',relative(run/'full.wav'),
        '--checkpoint_dir',relative(ROOT/'models/sadtalker'),'--result_dir',relative(run/'results'),'--cpu','--size','256','--batch_size','1','--preprocess','full','--still','--pose_style','0','--expression_scale','1.0','--verbose']
    env=os.environ.copy();env.update({'PATH':str(ff.parent)+os.pathsep+env.get('PATH',''),'IMAGEIO_FFMPEG_EXE':str(ff),'SADTALKER_FACE_MODEL_DIR':relative(ROOT/'models/sadtalker/face'),
        'OMP_NUM_THREADS':str(a.threads),'MKL_NUM_THREADS':str(a.threads),'OPENBLAS_NUM_THREADS':str(a.threads),'NUMBA_NUM_THREADS':str(a.threads),'PYTHONUNBUFFERED':'1','PYTHONUTF8':'1','TORCH_FORCE_WEIGHTS_ONLY_LOAD':'1',
        'TORCH_HOME':str(ROOT/'work/sadtalker/torch-cache'),'MPLCONFIGDIR':str(ROOT/'work/sadtalker/matplotlib')})
    record={'status':'running','source_image':image.relative_to(ROOT).as_posix(),'source_image_sha256':sha(image),'source_audio':audio.relative_to(ROOT).as_posix(),'source_audio_sha256':sha(audio),
        'audio_duration':seconds,'audio_16k_sha256':sha(run/'full.wav'),'run_directory':run.relative_to(ROOT).as_posix(),'created_utc':datetime.now(timezone.utc).isoformat(),
        'source_commit':'cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8','model_revision':models['revision'],'device':'cpu','threads':a.threads,'size':256,'batch_size':1,'still':True,'preprocess':'full','pose_style':0,'expression_scale':1.0,'seed':42,'enhancer':None,'command':command[1:],'user_accepted':False}
    def save(): (out/'manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save();start=time.perf_counter();log=run/'inference.log';print('Full dialogue inference log: '+str(log.relative_to(ROOT)),flush=True)
    with log.open('w',encoding='utf-8') as stream:
        proc=subprocess.Popen(command,cwd=SOURCE,env=env,stdout=stream,stderr=subprocess.STDOUT)
        record['pid']=proc.pid;save();last=''
        try:
            while proc.poll() is None:
                time.sleep(10);lines=log.read_text(encoding='utf-8',errors='replace')[-2200:].splitlines();line=next((x for x in reversed(lines) if x.strip()),'initializing')
                if line!=last:print(f'{time.perf_counter()-start:.0f}s: {line}',flush=True);last=line
        finally:
            if proc.poll() is None:proc.terminate();proc.wait()
    record['elapsed_sec']=round(time.perf_counter()-start,3);record['exit_code']=proc.returncode
    if proc.returncode:record['status']='failed';save();raise RuntimeError(log.read_text(encoding='utf-8',errors='replace')[-4000:])
    candidates=list((run/'results').glob('*.mp4'));assert len(candidates)==1
    dest=out/'head_full.mp4'
    subprocess.run([str(ff),'-nostdin','-v','error','-n','-i',str(candidates[0]),'-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(dest)],check=True)
    probe=json.loads(subprocess.check_output([str(fp),'-v','error','-show_format','-show_streams','-of','json',str(dest)]));assert abs(float(probe['format']['duration'])-seconds)<.08
    record.update(status='generated-awaiting-review',video=dest.relative_to(ROOT).as_posix(),video_sha256=sha(dest),probe=probe,raw_output=candidates[0].relative_to(ROOT).as_posix());save();print('Full-dialogue head generated.',flush=True)
if __name__=='__main__':main()
