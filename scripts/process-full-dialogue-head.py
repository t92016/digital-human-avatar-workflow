"""Wait for the already-running full inference, then stabilize and matte it once."""
from pathlib import Path
import hashlib,json,subprocess,time
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'work/round11/head-postprocess-state.json'
def main():
    cfg=json.loads((ROOT/'config/round11.json').read_text(encoding='utf-8'));manifest=ROOT/'outputs/round11/full-head-v1/manifest.json';start=time.perf_counter()
    def state(status):STATE.write_text(json.dumps({'status':status,'elapsed_sec':time.perf_counter()-start},indent=2),encoding='utf-8')
    state('waiting-for-existing-inference')
    while True:
        d=json.loads(manifest.read_text(encoding='utf-8'))
        if d['status']!='running':break
        if time.perf_counter()-start>7200:raise TimeoutError('Inference is still running; preserve it and inspect its log')
        time.sleep(10)
    if d['status']!='generated-awaiting-review':raise RuntimeError('Full inference did not complete successfully')
    py=ROOT/'work/sadtalker/venv/Scripts/python.exe';dest=ROOT/cfg['head_stabilized']
    state('stabilizing-full-head')
    if not dest.exists():subprocess.run([str(py),str(ROOT/'scripts/stabilize-sadtalker-head.py'),'--input',str(ROOT/cfg['head_full_source']),'--output',str(dest)],check=True)
    else:
        report=json.loads(dest.with_suffix('.json').read_text(encoding='utf-8'));assert report['input_sha256']==hashlib.sha256((ROOT/cfg['head_full_source']).read_bytes()).hexdigest()
    state('local-blinks-and-transparent-head')
    if not (ROOT/cfg['head_alpha']).exists():subprocess.run([str(py),str(ROOT/'scripts/prepare-full-dialogue-head.py')],check=True)
    else:assert (ROOT/cfg['head_alpha']).with_suffix('.json').is_file()
    state('head-ready');print('Full head ready for the13s teaching composition.',flush=True)
if __name__=='__main__':
    try:main()
    except Exception as e:
        STATE.write_text(json.dumps({'status':'failed','error':str(e)},indent=2),encoding='utf-8');raise
