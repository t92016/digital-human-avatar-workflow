"""Copy verified round11 MP4s to the requested private folder and build its player."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/round11'
cfg=json.loads((ROOT/'config/round11.json').read_text(encoding='utf-8'));dest=(ROOT/cfg['delivery_folder']).resolve()
if not dest.is_relative_to(ROOT) or dest.parent!=ROOT:raise ValueError('Delivery folder must be directly inside this workspace')
check=json.loads((OUT/'technical-verification.json').read_text(encoding='utf-8'))
if check['frames']!=936 or check['alpha_frames']!=936 or check['failures']:raise ValueError('Complete all final video and alpha checks before export')
if (dest/'manifest.json').exists() and json.loads((dest/'manifest.json').read_text(encoding='utf-8')).get('user_accepted'):raise ValueError('Accepted delivery must remain frozen; use a new version')
dest.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst):
    if dst.exists() and sha(dst)!=sha(src):raise FileExistsError('Existing different file: '+str(dst))
    if not dst.exists():shutil.copy2(src,dst)
    assert sha(src)==sha(dst)
for row,name in zip(check['actual_mp4_reports'],cfg['filenames']):
    src=ROOT/row['path'];assert sha(src)==row['sha256'];copy(src,dest/name)
copy(OUT/'qa/mode2_f046.png',dest/'poster.png')
copy(OUT/'technical-verification.json',dest/'technical-verification.json')
page='''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>阿德推廣校園反霸凌｜個人身體</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf3f6;color:#203c4e;font:16px/1.7 "Microsoft JhengHei",sans-serif}main{max-width:1280px;margin:auto;padding:22px}h1{font-size:29px;margin:0}p{margin:10px 0 16px}.controls{display:flex;flex-wrap:wrap;gap:9px;margin:14px 0}button{font:inherit;border:1px solid #74949f;border-radius:9px;background:white;padding:8px 13px;color:#244756;cursor:pointer}button.active{background:#176e72;color:white}.frame{padding:7px;border-radius:12px;background:#111e27}video{display:block;width:100%;aspect-ratio:16/9;border-radius:7px}.note{background:white;border-left:4px solid #277f83;padding:12px 16px;margin:18px 0}details{background:white;border-radius:10px;padding:14px;margin:16px 0}summary{font-size:19px;cursor:pointer}.zoom{max-width:480px;margin:12px auto}canvas{width:100%;height:auto;display:block}a{color:#076393}.downloads{display:flex;gap:14px;flex-wrap:wrap}.tag{display:inline-block;background:#fff0cd;color:#714b08;border-radius:16px;padding:3px 11px;font-size:14px}.footer{font-size:14px;color:#516b7b}@media(max-width:720px){main{padding:14px}h1{font-size:24px}}
</style></head><body><main><h1>阿德推廣校園反霸凌（個人身體）</h1><p>手肘彎曲幅度已減小約一半，沿用本人黑色POLO衫與長褲。台詞、家豪配音、解說圖片及字幕與原阿忠身體版本相同；三版皆13秒、1920×1080。<span class="tag">修正版待你審核</span></p>
<div class="controls"><button data-mode="1">① 只有手部</button><button data-mode="2" class="active">② 自然版</button><button data-mode="3">③ 活潑版</button><button id="slow">0.5 倍慢速</button><button id="peak">看手肘修正</button><button id="replay">完整重播</button></div>
<div class="frame"><video id="player" src="02_手腳與頭部_自然版.mp4" controls playsinline preload="auto" poster="poster.png"></video></div><p id="state">目前：② 自然版</p>
<div class="note">請留意抬手、停留到放回的完整過程：手肘是否更自然，肩頸與膝踝是否保持相連。①只有手部動作；②自然版、③活潑版加入原地的頭部與腳部動作。</div>
<details id="closeups"><summary>放大檢查人物與手肘</summary><div class="zoom"><canvas id="zoom" width="535" height="550"></canvas></div></details>
<p><a id="download" href="02_手腳與頭部_自然版.mp4" download>下載目前模式 MP4</a></p><div class="downloads"><a href="01_只有手部.mp4" download>下載①只有手部</a><a href="02_手腳與頭部_自然版.mp4" download>下載②自然版</a><a href="03_手腳與頭部_活潑版.mp4" download>下載③活潑版</a></div>
<p class="footer">原版保留於「阿德推廣校園反霸凌（阿忠身體）」；新舊MP4分開保存。本頁及影片均為私人本機檔案。<a href="technical-verification.json">驗證紀錄</a> · <a href="manifest.json">版本清單</a></p></main>
<script>
const files={1:'01_只有手部.mp4',2:'02_手腳與頭部_自然版.mp4',3:'03_手腳與頭部_活潑版.mp4'},names={1:'① 只有手部',2:'② 自然版',3:'③ 活潑版'},v=document.querySelector('#player');
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{const t=v.currentTime,playing=!v.paused,rate=v.playbackRate,m=Number(b.dataset.mode);v.src=files[m];v.addEventListener('loadedmetadata',()=>{v.playbackRate=rate;v.currentTime=Math.min(t,12.95);if(playing)v.play()},{once:true});document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===b));document.querySelector('#download').href=files[m];document.querySelector('#state').textContent='目前：'+names[m]});
document.querySelector('#slow').onclick=function(){v.playbackRate=v.playbackRate===1?.5:1;this.textContent=v.playbackRate===1?'0.5 倍慢速':'恢復正常速度'};document.querySelector('#peak').onclick=()=>{v.pause();v.currentTime=1.9};document.querySelector('#replay').onclick=()=>{v.currentTime=0;v.play()};const ctx=document.querySelector('#zoom').getContext('2d');function draw(){if(v.readyState>=2&&document.querySelector('#closeups').open)ctx.drawImage(v,62,493,535,550,0,0,535,550);requestAnimationFrame(draw)}draw();
</script></body></html>'''
(dest/'index.html').write_text(page,encoding='utf-8')
files=['index.html',*cfg['filenames'],'poster.png','technical-verification.json']
data={'round':'round11','purpose':'private-personal-body-teaching-delivery','duration_sec':13,'resolution':[1920,1080],'fps':24,'elbow_degrees':[21,24,29],'user_accepted':False,'source_round':'round05 speech/panels/captions + round09 personal body + full-dialogue SadTalker','legacy_folder_name':cfg['legacy_renamed_folder'],'files':[{'path':n,'bytes':(dest/n).stat().st_size,'sha256':sha(dest/n)} for n in files]}
(dest/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(dest)
