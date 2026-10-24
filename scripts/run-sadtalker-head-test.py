"""Run a short, isolated, CPU-only original-mouth SadTalker experiment."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,time,uuid
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'work/sadtalker/source'

def sha(path):
    with path.open('rb') as f:
        h=hashlib.sha256()
        for part in iter(lambda:f.read(4*1024*1024),b''):h.update(part)
    return h.hexdigest()

def relative(path):return os.path.relpath(path,SOURCE).replace('\\','/')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',type=Path,required=True)
    p.add_argument('--audio',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=4.4)
    args=p.parse_args()
    if not 3<=args.seconds<=5:raise ValueError('第一階段限3至5秒，長片另做分段評估')
    image=args.image.resolve();audio=args.audio.resolve();output=args.output.resolve()
    if not image.is_file() or not audio.is_file():raise FileNotFoundError('缺少已確認的頭像／音訊')
    if not output.is_relative_to(ROOT/'outputs'):raise ValueError('私人試驗須另存專案outputs內')
    if output.exists() and any(output.iterdir()):raise FileExistsError('輸出目錄非空，請另取版本名稱')
    venv=ROOT/'work/sadtalker/venv/Scripts/python.exe'
    if not venv.exists():raise RuntimeError('請先安裝獨立SadTalker環境')
    subprocess.run([str(venv),str(ROOT/'scripts/patch-sadtalker-compat.py')],check=True)
    models=json.loads((ROOT/'work/sadtalker/model-download-manifest.json').read_text(encoding='utf-8'))
    for row in models['files']:
        if sha(ROOT/row['path'])!=row['sha256']:raise ValueError('模型完整性不符：'+row['name'])
    output.mkdir(parents=True,exist_ok=True)
    run=ROOT/'work/sadtalker/runs'/('test_'+uuid.uuid4().hex[:12]);run.mkdir(parents=True)
    shutil.copy2(image,run/'original.png')
    assert sha(image)==sha(run/'original.png')
    ffmpeg=ROOT/'tools/bin/ffmpeg.exe';ffprobe=ROOT/'tools/bin/ffprobe.exe'
    if not ffmpeg.is_file() or not ffprobe.is_file():raise RuntimeError('請先完成專案FFmpeg／FFprobe工具安裝')
    subprocess.run([str(ffmpeg),'-nostdin','-y','-v','error','-i',str(audio),'-t',str(args.seconds),
        '-ar','16000','-ac','1',str(run/'sample.wav')],check=True)
    driver=run/'driver.py'
    driver.write_text('import os, sys, random, runpy, numpy as np, torch\n'
        'sys.path.insert(0, os.getcwd())\n'
        'random.seed(42); np.random.seed(42); torch.manual_seed(42)\n'
        'torch.set_num_threads(2); torch.set_num_interop_threads(1)\n'
        'print("CPU torch",torch.__version__,"threads",torch.get_num_threads(),flush=True)\n'
        'runpy.run_path("inference.py",run_name="__main__")\n',encoding='utf-8')
    command=[str(venv),relative(driver),'--source_image',relative(run/'original.png'),
        '--driven_audio',relative(run/'sample.wav'),'--checkpoint_dir',relative(ROOT/'models/sadtalker'),
        '--result_dir',relative(run/'results'),'--cpu','--size','256','--batch_size','1',
        '--preprocess','full','--still','--pose_style','0','--expression_scale','1.0','--verbose']
    env=os.environ.copy()
    env.update({'PATH':str(ffmpeg.parent)+os.pathsep+env.get('PATH',''),'IMAGEIO_FFMPEG_EXE':str(ffmpeg),
        'SADTALKER_FACE_MODEL_DIR':relative(ROOT/'models/sadtalker/face'),
        'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','NUMBA_NUM_THREADS':'2',
        'PYTHONUNBUFFERED':'1','PYTHONUTF8':'1','TORCH_FORCE_WEIGHTS_ONLY_LOAD':'1',
        'TORCH_HOME':str(ROOT/'work/sadtalker/torch-cache'),'MPLCONFIGDIR':str(ROOT/'work/sadtalker/matplotlib')})
    record={'schema_version':1,'created_utc':datetime.now(timezone.utc).isoformat(),
        'source_image':os.path.relpath(image,ROOT),'source_image_sha256':sha(image),'original_mouth_not_erased':True,
        'source_audio':os.path.relpath(audio,ROOT),'source_audio_sha256':sha(audio),
        'sample_duration_requested':args.seconds,'sample_audio_sha256':sha(run/'sample.wav'),
        'source_commit':'cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8','model_revision':models['revision'],
        'device':'cpu','torch_threads':2,'size':256,'batch_size':1,'preprocess':'full','still':True,
        'enhancer':None,'seed':42,'run_directory':os.path.relpath(run,ROOT),'command':command[1:],
        'user_accepted':False,'body_integrated':False,'status':'running'}
    manifest=output/'manifest.json'
    def save():manifest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save();start=time.perf_counter();log=run/'inference.log'
    print('Starting local head-only inference; log: '+os.path.relpath(log,ROOT),flush=True)
    with log.open('w',encoding='utf-8') as stream:
        proc=subprocess.Popen(command,cwd=SOURCE,env=env,stdout=stream,stderr=subprocess.STDOUT)
        try:
            last=''
            while proc.poll() is None:
                time.sleep(10)
                tail=log.read_text(encoding='utf-8',errors='replace')[-1800:].splitlines()
                line=next((s for s in reversed(tail) if s.strip()),'initializing')
                if line!=last:print(f'{time.perf_counter()-start:.0f}s: {line}',flush=True);last=line
        finally:
            if proc.poll() is None:proc.terminate();proc.wait()
    record['inference_elapsed_sec']=round(time.perf_counter()-start,3)
    record['inference_exit_code']=proc.returncode
    if proc.returncode:
        record['status']='failed';save()
        raise RuntimeError(log.read_text(encoding='utf-8',errors='replace')[-6500:])
    candidates=list((run/'results').glob('*.mp4'))
    if len(candidates)!=1:record['status']='failed-missing-output';save();raise RuntimeError('模型未產出唯一MP4')
    dst=output/'head_test.mp4'
    subprocess.run([str(ffmpeg),'-nostdin','-y','-v','error','-i',str(candidates[0]),'-c:v','libx264',
        '-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',
        '-movflags','+faststart',str(dst)],check=True)
    info=json.loads(subprocess.check_output([str(ffprobe),'-v','error','-show_format','-show_streams','-of','json',str(dst)]))
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    aud=next(s for s in info['streams'] if s['codec_type']=='audio')
    assert video['codec_name']=='h264' and aud['codec_name']=='aac'
    assert abs(float(info['format']['duration'])-args.seconds)<.08
    decoded=subprocess.run([str(ffmpeg),'-nostdin','-v','error','-i',str(dst),'-f','null','-'],check=True,capture_output=True)
    if decoded.stderr.strip():raise RuntimeError('MP4解碼出現錯誤：'+decoded.stderr.decode('utf-8',errors='replace'))
    shutil.copy2(image,output/'original-head.png');shutil.copy2(run/'sample.wav',output/'jiahao-sample.wav')
    record.update(status='generated-awaiting-visual-review',video_sha256=sha(dst),video_file=dst.name,
        duration=float(info['format']['duration']),resolution=[video['width'],video['height']],fps=video['r_frame_rate'],
        complete_decode_passed=True,raw_model_output=os.path.relpath(candidates[0],ROOT))
    save();print(json.dumps(record,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
