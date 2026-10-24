"""Private round10 review page: same-mode old/new, joint close-ups and one audio."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/round10'
manifest=OUT/'manifest.json'
if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8')).get('user_accepted'):
    raise SystemExit('Round10 is accepted; use a new round.')
video_check=json.loads((OUT/'technical-verification.json').read_text(encoding='utf-8'))
alpha_check=json.loads((OUT/'alpha-continuity-verification.json').read_text(encoding='utf-8'))
if video_check.get('actual_frames_checked')!=330 or video_check['failures'] or alpha_check.get('frames')!=330 or alpha_check['failures']:
    raise SystemExit('Complete and pass all 330 video and alpha frame checks before building the review page.')
(OUT/'character').mkdir(exist_ok=True)
static=ROOT/'work/round10/static-final/frame-00-at-0s.png'
if static.exists() and not (OUT/'character/fullbody_articulated.png').exists():shutil.copy2(static,OUT/'character/fullbody_articulated.png')
page='''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>阿德｜彎肘屈膝・第十輪審核</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf3f6;color:#203c4e;font:16px/1.75 "Microsoft JhengHei",sans-serif}main{max-width:1320px;margin:auto;padding:22px}h1{font-size:29px;margin:0}p{margin:10px 0 14px}.tag{font-size:14px;border-radius:20px;background:#fff0cd;color:#714b08;padding:4px 12px;display:inline-block}.controls{display:flex;flex-wrap:wrap;gap:9px;margin:14px 0}button{font:inherit;border:1px solid #74949f;border-radius:9px;background:white;padding:8px 13px;color:#244756;cursor:pointer}button.active{background:#176e72;color:white}.player{background:#111e27;padding:7px;border-radius:12px}video{display:block;width:100%;aspect-ratio:16/9;border-radius:8px}.note{background:white;border-left:4px solid #277f83;padding:12px 16px;margin:18px 0}details{background:white;border-radius:10px;padding:14px;margin:16px 0}summary{cursor:pointer;font-size:19px;font-weight:700}canvas{display:block;width:100%;height:auto;background:#f2f5f7}.zoom{max-width:720px;margin:auto}a{color:#076393}.still{max-height:640px;width:100%;object-fit:contain;background:repeating-conic-gradient(#eef2f5 0% 25%,white 0% 50%) 50% / 20px 20px}.proof{width:100%}.footer{font-size:14px;color:#516b7b}@media(max-width:720px){main{padding:14px}h1{font-size:24px}}
</style></head><body><main><h1>阿德：彎肘、屈膝與肩頸整合</h1><p>左側是已接受的第九輪，右側是本次第十輪；以相同人物尺度、相同家豪配音比較。保留原本的對嘴與眨眼。<span class="tag">新關節與比例待你最後審核</span></p>
<div class="controls"><button data-mode="1">① 手部・彎肘</button><button class="active" data-mode="2">② 自然・彎肘屈膝</button><button data-mode="3">③ 活潑・彎肘屈膝</button><button id="slow">0.5 倍慢速</button><button id="peak">看彎肘與屈膝</button><button id="replay">重播完整動作</button></div>
<div class="player"><video id="player" src="mode2.mp4" controls playsinline preload="auto" poster="qa/mode2_f046.png"></video></div><p id="state">目前：② 自然・彎肘屈膝</p>
<div class="note">本輪一起調整頭身比例、肩頸接合、彎肘與屈膝。請看抬起、停留到放回的完整過程，留意肩、肘、髖、膝與腳踝是否連續，以及整體是否流暢自然。①模式維持只有手部動作。</div>
<details id="closeups"><summary>放大看頭頸、手肘與膝部</summary><div class="controls"><button class="active" data-crop="full">完整人物</button><button data-crop="neck">頭身與肩頸</button><button data-crop="elbow">肩膀與手肘</button><button data-crop="knee">膝部與腳踝</button></div><div class="zoom"><canvas id="zoom" width="780" height="887"></canvas></div></details>
<p><a id="download" href="mode2.mp4" download>下載目前模式 MP4</a>　<a href="character/fullbody_articulated.png" download>下載更新後透明靜態圖</a></p>
<details><summary>查看實際影片的連續動作畫格</summary><img class="proof" id="proof" src="qa/mode2_body_sequence.png" alt="自然模式從抬起、彎曲到放回的實際影片畫格"></details>
<details><summary>查看更新後的全身靜態圖</summary><img class="still" src="character/fullbody_articulated.png" alt="頭身微調後的阿德透明全身圖"></details>
<p class="footer">目前仍是4.4秒整合短測。彎肘與屈膝採連續輪廓變形；未增加張掌或手指動作。第九輪原影片保持不變。<a href="technical-verification.json">逐幀驗證</a> · <a href="alpha-continuity-verification.json">透明輪廓驗證</a> · <a href="manifest.json">版本清單</a></p></main>
<script>
const v=document.querySelector('#player'),state=document.querySelector('#state'),names={1:'① 手部・彎肘',2:'② 自然・彎肘屈膝',3:'③ 活潑・彎肘屈膝'};let current=2,crop='full';
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{const t=v.currentTime,playing=!v.paused,rate=v.playbackRate;current=Number(b.dataset.mode);v.src=`mode${current}.mp4`;v.poster=`qa/mode${current}_f046.png`;v.addEventListener('loadedmetadata',()=>{v.playbackRate=rate;v.currentTime=Math.min(t,4.36);if(playing)v.play()},{once:true});document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===b));document.querySelector('#download').href=`mode${current}.mp4`;document.querySelector('#proof').src=`qa/mode${current}_body_sequence.png`;state.textContent='目前：'+names[current]});
document.querySelector('#slow').onclick=function(){v.playbackRate=v.playbackRate===1?.5:1;this.textContent=v.playbackRate===1?'0.5 倍慢速':'恢復正常速度'};
document.querySelector('#peak').onclick=()=>{v.pause();v.currentTime=1.88};document.querySelector('#replay').onclick=()=>{v.currentTime=0;v.play()};
const canvas=document.querySelector('#zoom'),ctx=canvas.getContext('2d'),rects={full:[1020,80,780,915],neck:[1210,80,410,488],elbow:[1080,390,700,300],knee:[1240,655,360,330]};canvas.width=780;canvas.height=915;
document.querySelectorAll('[data-crop]').forEach(b=>b.onclick=()=>{crop=b.dataset.crop;const r=rects[crop];canvas.width=r[2];canvas.height=r[3];document.querySelectorAll('[data-crop]').forEach(x=>x.classList.toggle('active',x===b))});
function draw(){if(v.readyState>=2&&document.querySelector('#closeups').open){const r=rects[crop];ctx.drawImage(v,...r,0,0,canvas.width,canvas.height)}requestAnimationFrame(draw)}draw();
</script></body></html>'''
page=page.replace('mode2.mp4','mode2-final.mp4').replace('`mode${current}.mp4`','`mode${current}-final.mp4`')
(OUT/'index.html').write_text(page,encoding='utf-8')
files=['index.html','mode1-final.mp4','mode2-final.mp4','mode3-final.mp4','character/fullbody_articulated.png','technical-verification.json','alpha-continuity-verification.json','build-manifest.json']
files += [f'qa/mode{m}_{n}.png' for m in [1,2,3] for n in ['f046','body_sequence','blink_neck_sequence']]
build=json.loads((OUT/'build-manifest.json').read_text(encoding='utf-8'))
data={'round':'round10','user_accepted':False,'scope':'彎肘、屈膝、頭身比例及肩頸整合候選；第九輪動作接受不延伸至本輪','sources':build['sourceRecords'],'baseline_videos':build['baseline_videos'],'files':[{'path':f,'bytes':(OUT/f).stat().st_size,'sha256':hashlib.sha256((OUT/f).read_bytes()).hexdigest()} for f in files]}
manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT/'index.html')
