"""Private review page + six-part download archive for round09."""
from pathlib import Path
import hashlib,json,shutil,zipfile

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/round09'
previous=OUT/'manifest.json'
if previous.exists() and json.loads(previous.read_text(encoding='utf-8')).get('user_accepted'):
    raise SystemExit('Round09 is accepted; use a new round instead of overwriting it.')
PNG=OUT/'character/fullbody_assembled.png'
src=ROOT/'work/round09/static-final/frame-00-at-0s.png'
if src.exists() and not PNG.exists():shutil.copy2(src,PNG)
parts=['parts/arm_left.svg','parts/arm_right.svg','parts/pelvis.svg','parts/leg_left.svg','parts/leg_right.svg','parts/torso_armless.png']
with zipfile.ZipFile(OUT/'body_parts.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for name in parts:z.write(OUT/name,Path(name).name)
page='''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>阿德｜專屬全身・第九輪</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf3f6;color:#203c4e;font:16px/1.7 "Microsoft JhengHei",sans-serif}main{max-width:1240px;padding:24px;margin:auto}h1{font-size:29px;margin:0}p{margin:10px 0 17px}.tag{display:inline-block;font-size:14px;border-radius:20px;background:#fff0cd;color:#714b08;padding:3px 12px}.controls{display:flex;flex-wrap:wrap;gap:9px;margin:16px 0}button{font:inherit;border:1px solid #74949f;border-radius:9px;background:white;padding:8px 13px;color:#244756;cursor:pointer}button.active{background:#176e72;color:white}.video-wrap{background:#111e27;border-radius:12px;padding:8px}video{display:block;width:100%;aspect-ratio:16/9;border-radius:8px}.note{padding:12px 16px;background:white;border-left:4px solid #277f83;margin:18px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0;background:white;border:1px solid #ccdce4;border-radius:12px;padding:15px}figcaption{font-size:18px;font-weight:700}figure img{display:block;width:100%;height:620px;object-fit:contain;background:repeating-conic-gradient(#eef2f5 0% 25%,#fff 0% 50%) 50% / 20px 20px;border-radius:6px;margin-top:12px}.parts{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.parts img{height:280px}.parts figcaption{font-size:16px}canvas{width:100%;height:auto;background:#f2f5f7}.crop{max-width:620px;margin:12px auto}h2{font-size:23px;margin:25px 0 12px}a{color:#076393}details{background:white;padding:14px;border-radius:9px;margin:16px 0}.footer{font-size:14px;color:#516b7b}@media(max-width:720px){main{padding:15px}.grid{grid-template-columns:1fr}.parts{grid-template-columns:1fr 1fr}figure img{height:520px}.parts img{height:240px}h1{font-size:25px}}
</style></head><body><main><h1>阿德：專屬全身動作短測</h1><p>依本人全身照製作黑色 POLO 衫、深色長褲與運動鞋。採用已接受的阿德對嘴、眨眼頭像，三種模式皆為相同家豪配音、4.4 秒。<span class="tag">本輪全身造型與接合待您檢視</span></p>
<div class="controls"><button data-mode="1">① 只有手部</button><button class="active" data-mode="2">② 手腳與頭部・自然</button><button data-mode="3">③ 手腳與頭部・活潑</button><button id="slow">0.5 倍慢速</button><button id="peak">看閉眼與抬手</button></div>
<div class="video-wrap"><video id="player" src="mode2.mp4" controls playsinline preload="auto"></video></div><p id="state">目前：② 手腳與頭部・自然</p>
<div class="note">請留意頸部與衣領、肩膀抬起及放回、褲子與腿部接縫，以及閉眼／嘴型是否維持。這是放大素材比較，尚未改成教材成片。彎肘、屈膝與張掌仍屬後續功能。</div>
<details><summary>放大檢查動態人物</summary><div class="crop"><canvas id="zoom" width="820" height="925"></canvas></div></details>
<p><a id="download" href="mode2.mp4" download>下載目前模式 MP4</a>　<a href="body_parts.zip" download>下載六份身體分層素材</a>　<a href="character/head_accepted_alpha.webm" download>下載透明說話眨眼頭部</a></p>
<h2>全身靜態圖</h2><div class="grid"><figure><figcaption>照片轉 Q 版候選</figcaption><img src="character/fullbody_cutout_v2.png" alt="本人服裝的完整Q版人物"><a href="character/fullbody_cutout_v2.png" download>下載透明 PNG</a></figure><figure><figcaption>分層後接回已接受頭像</figcaption><img src="character/fullbody_assembled.png" alt="專屬身體與原Q版頭像接合靜態"><a href="character/fullbody_assembled.png" download>下載組合透明 PNG</a></figure></div>
<h2>拆解的六個部位</h2><p>手臂包含完整袖子與肩部重疊材質，腿部包含長褲與鞋子；原始圖集保留。</p><div class="parts">PARTS</div>
<details><summary>查看實際影片的連續畫格</summary><img style="width:100%" src="qa/mode3_body_sequence.png" alt="活潑模式實際MP4完整抬手放回取樣"><a href="technical-verification.json">技術驗證</a> · <a href="manifest.json">來源與版本清單</a></details>
<p class="footer">新身體、去背邊緣與動作整合另行驗收；第八輪原頭像影片保持不變。分層 ZIP 只含身體部位，不是完整跨電腦重建包。全部為私人本機輸出。</p></main>
<script>const v=document.querySelector('#player'),s=document.querySelector('#state');let current=2;const names={1:'① 只有手部',2:'② 手腳與頭部・自然',3:'③ 手腳與頭部・活潑'};document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{const t=v.currentTime,playing=!v.paused,rate=v.playbackRate;current=Number(b.dataset.mode);v.src=`mode${current}.mp4`;v.playbackRate=rate;v.addEventListener('loadedmetadata',()=>{v.currentTime=Math.min(t,4.36);if(playing)v.play()},{once:true});document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===b));document.querySelector('#download').href=`mode${current}.mp4`;s.textContent='目前：'+names[current]});document.querySelector('#slow').onclick=function(){v.playbackRate=v.playbackRate===1?.5:1;this.textContent=v.playbackRate===1?'0.5 倍慢速':'恢復正常速度'};document.querySelector('#peak').onclick=()=>{v.pause();v.currentTime=1.88};const ctx=document.querySelector('#zoom').getContext('2d');function draw(){if(v.readyState>=2)ctx.drawImage(v,940,75,820,925,0,0,820,925);requestAnimationFrame(draw)}draw();</script></body></html>'''
labels=['畫面左手臂（含袖子）','畫面右手臂（含袖子）','骨盆與腰部','畫面左腿與鞋','畫面右腿與鞋','無手臂軀幹']
page=page.replace('PARTS',''.join(f'<figure><figcaption>{label}</figcaption><img loading="lazy" src="{name}" alt="{label}"><a href="{name}" download>下載部位</a></figure>' for label,name in zip(labels,parts)))
(OUT/'index.html').write_text(page,encoding='utf-8')
files=['index.html','mode1.mp4','mode2.mp4','mode3.mp4','body_parts.zip','character/fullbody_cutout_v2.png','character/fullbody_assembled.png','character/head_accepted_alpha.webm',*parts,'qa/mode3_body_sequence.png','technical-verification.json','build-manifest.json']
source=json.loads((OUT/'build-manifest.json').read_text(encoding='utf-8'))
manifest={'round':'round09','head_route':2,'sources':source['sourceRecords'],'user_accepted':False,
    'scope':'專屬全身造型、頭身接合及三種原地動作候選；舊頭像驗收不延伸到新身體',
    'files':[{'path':name,'bytes':(OUT/name).stat().st_size,'sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest()} for name in files]}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT/'index.html')
