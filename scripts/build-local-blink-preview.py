"""Build a private, self-contained review page for the calibrated Ade blink."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=Path('outputs/round08'))
    args = parser.parse_args()
    out = args.directory.resolve()
    if not out.is_relative_to(ROOT/'outputs'):
        raise ValueError('Private preview must stay in outputs')
    manifest = json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    source = ROOT/manifest['source']
    baseline = out/'baseline_stabilized.mp4'
    if baseline.exists() and baseline.read_bytes() != source.read_bytes():
        raise FileExistsError('Different baseline already exists')
    if not baseline.exists():
        shutil.copy2(source, baseline)
    page = '''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,">
<title>阿德｜局部眨眼短測・第八輪</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#edf2f6;color:#20384b;font:16px/1.7 "Microsoft JhengHei",sans-serif}main{max-width:1120px;margin:auto;padding:26px}h1{font-size:30px;line-height:1.35;margin:8px 0}p{margin:8px 0 18px}.eyebrow{font-size:13px;letter-spacing:.13em;color:#247077}.tag{display:inline-block;border-radius:30px;padding:4px 12px;background:#fff2d5;color:#704800;font-size:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0;padding:16px;border:1px solid #c6d7e1;border-radius:14px;background:#fff}figcaption{font-size:19px;font-weight:700;margin-bottom:10px}video{display:block;width:100%;aspect-ratio:1;background:#000;border-radius:7px}canvas{display:block;width:100%;height:auto;border-radius:6px;margin-top:12px;background:#000}.label{display:block;font-size:13px;color:#536b7d;margin-top:10px}.controls{display:flex;flex-wrap:wrap;gap:9px;margin:20px 0 12px}button{font:inherit;padding:8px 14px;border:1px solid #608695;border-radius:8px;background:white;color:#21495b;cursor:pointer}button.primary{background:#146e70;color:#fff;border-color:#146e70}button.active{box-shadow:inset 0 0 0 2px #146e70}button:focus-visible,a:focus-visible{outline:3px solid #ebad37;outline-offset:3px}.note{border-left:4px solid #2b8585;background:white;padding:12px 16px;margin:20px 0}a{color:#075f91}h2{font-size:22px;margin:26px 0 10px}.keys{width:100%;border-radius:8px}.footer{font-size:14px;color:#50697a}#state{font-variant-numeric:tabular-nums;color:#416070}details{background:white;border:1px solid #c6d7e1;border-radius:10px;padding:14px;margin:18px 0}summary{cursor:pointer;font-weight:700}@media(max-width:700px){main{padding:16px}.grid{grid-template-columns:1fr}h1{font-size:25px}figure{padding:12px}}
</style></head><body><main>
<span class="eyebrow">阿德 Q 版頭像 · ROUND 08</span><h1>局部眨眼短測</h1>
<p>沿用已接受的穩定頭像與家豪配音。約 <strong>1.76～2.00 秒</strong>出現一次閉眼、張眼，整段 4.4 秒。<span class="tag">本輪眨眼待您檢視</span></p>
<div class="controls"><button id="play" class="primary">播放比較</button><button id="blink">重播眨眼</button><button id="normal" class="active">正常速度</button><button id="slow">0.5 倍慢速</button><button id="peak">停在閉眼畫面</button></div>
<p id="state" aria-live="polite">準備播放 · 右側播放家豪配音</p>
<div class="grid">
<figure><figcaption>基準｜已接受的穩定片</figcaption><video id="base" src="baseline_stabilized.mp4" muted playsinline preload="auto" aria-label="已接受的穩定基準"></video><span class="label">眼部同步放大</span><canvas id="base-eye" width="980" height="356" aria-label="基準眼部放大"></canvas></figure>
<figure><figcaption>新短測｜局部眼皮開閉</figcaption><video id="edit" src="head_local_blink.mp4" controls playsinline preload="auto" aria-label="第八輪局部眨眼短測"></video><span class="label">眼部同步放大</span><canvas id="edit-eye" width="980" height="356" aria-label="局部眨眼眼部放大"></canvas></figure>
</div>
<div class="note">請留意雙眼是否自然閉合、張開後是否回到原眼型，以及眼鏡、嘴型與臉型是否維持。正常／慢速共用同一支影片；慢速播放只用於觀察過渡。</div>
<h2>開眼 → 半閉 → 全閉</h2><img class="keys" src="keyframes_eyes.png" alt="由左至右：開眼、半閉眼、全閉眼的合成關鍵圖">
<details><summary>查看實際影片的完整開閉畫格</summary><p>連續畫格來自輸出的 MP4，包含眨眼前、閉合、重新張眼。</p><img class="keys" src="qa/blink_sequence_eyes.png" alt="第42至52幀完整眼部開閉過程"></details>
<p><a href="head_local_blink.mp4" download>下載眨眼短測 MP4</a>　<a href="baseline_stabilized.mp4" download>下載原穩定片</a>　<a href="manifest.json">製作與驗證資料</a></p>
<p class="footer">此輪只測頭像局部眨眼。原音軌直接沿用；嘴唇、下顎與幀序沿用基準。尚未接回身體或教材字幕。素材留在本機。</p>
</main><script>
const base=document.querySelector('#base'),edit=document.querySelector('#edit'),state=document.querySelector('#state');
const videos=[base,edit];let mode='full';let syncing=false;
const status=()=>{state.textContent=`${edit.paused?'已暫停':'播放中'} · ${edit.currentTime.toFixed(2)} / 4.40 秒 · ${edit.playbackRate===1?'正常':'0.5 倍慢速'} · 右側播放家豪配音`;document.querySelector('#play').textContent=edit.paused?(edit.currentTime>=4.3?'重新播放比較':'播放比較'):'暫停比較'};
async function seek(t){videos.forEach(v=>v.pause());videos.forEach(v=>v.currentTime=t);status()}
async function play(){if(edit.readyState<2)await new Promise(r=>edit.addEventListener('canplay',r,{once:true}));base.currentTime=edit.currentTime;await Promise.all(videos.map(v=>v.play()));status()}
document.querySelector('#play').onclick=async()=>{mode='full';if(!edit.paused){videos.forEach(v=>v.pause());return}if(edit.currentTime>4.3)await seek(0);await play()};
document.querySelector('#blink').onclick=async()=>{mode='blink';await seek(1.48);await play()};
document.querySelector('#peak').onclick=async()=>{mode='full';await seek(1.88)};
for(const [id,rate]of[['normal',1],['slow',.5]])document.getElementById(id).onclick=()=>{videos.forEach(v=>v.playbackRate=rate);for(const b of ['normal','slow'])document.getElementById(b).classList.toggle('active',b===id);status()};
edit.addEventListener('play',()=>{base.currentTime=edit.currentTime;base.playbackRate=edit.playbackRate;base.play();status()});edit.addEventListener('pause',()=>{base.pause();status()});
edit.addEventListener('seeking',()=>{if(!syncing){syncing=true;base.currentTime=edit.currentTime;syncing=false}});
edit.addEventListener('ratechange',()=>base.playbackRate=edit.playbackRate);edit.addEventListener('ended',()=>{base.pause();document.querySelector('#play').textContent='重新播放比較';status()});
function draw(){for(const[id,v]of[['base-eye',base],['edit-eye',edit]])if(v.readyState>=2)document.getElementById(id).getContext('2d').drawImage(v,390,554,490,178,0,0,980,356);if(!edit.paused&&Math.abs(base.currentTime-edit.currentTime)>.06)base.currentTime=edit.currentTime;if(mode==='blink'&&edit.currentTime>=2.28){videos.forEach(v=>v.pause());mode='full'}if(!edit.paused)status();requestAnimationFrame(draw)}draw();
Promise.all(videos.map(v=>v.readyState>=2?Promise.resolve():new Promise(r=>v.addEventListener('loadeddata',r,{once:true})))).then(status);
</script></body></html>'''
    (out/'index.html').write_text(page, encoding='utf-8')
    public_files = ['index.html', 'head_local_blink.mp4', 'baseline_stabilized.mp4',
        'keyframes_eyes.png', 'keyframes.png', 'key_open.png', 'key_half.png', 'key_closed.png',
        'qa/blink_sequence_eyes.png', 'qa/blink_sequence_full.png']
    manifest['files'] = [{'path': name, 'bytes': (out/name).stat().st_size,
        'sha256': hashlib.sha256((out/name).read_bytes()).hexdigest()} for name in public_files]
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(out/'index.html')


if __name__ == '__main__':
    main()
