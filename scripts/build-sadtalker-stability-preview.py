"""Private A/B page for the calibrated Ade stabilization experiment."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'outputs/round07';out.mkdir(exist_ok=True)
baseline=ROOT/'outputs/round06/sadtalker-head-v2/ade_sadtalker_4_4s.mp4'
copy=out/'baseline_accepted.mp4'
if copy.exists() and hashlib.sha256(copy.read_bytes()).digest()!=hashlib.sha256(baseline.read_bytes()).digest():
    raise FileExistsError('保留不同內容的既有基準片，請另取比較目錄')
if not copy.exists():shutil.copy2(baseline,copy)
for gain in ['0','2.5','4.0','6.0','8.0']:
    src=ROOT/f'work/sadtalker/refine07/probe_gain_{gain}.png'
    if src.exists():shutil.copy2(src,out/f'blink_probe_{gain}.png')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>阿德｜穩定優化比較</title>
<style>*{box-sizing:border-box}body{margin:0;background:#edf3f8;color:#18334b;font:16px/1.75 "Microsoft JhengHei",sans-serif}main{max-width:1160px;padding:24px;margin:auto}h1{font-size:28px;margin:0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;background:white;border:1px solid #c8d8e5;border-radius:14px;padding:16px}figcaption{font-size:19px;font-weight:700;margin-bottom:10px}video{width:100%;aspect-ratio:1;background:#080a0f;border-radius:8px}p{margin:10px 0 18px}.note{padding:12px 16px;background:white;border-left:5px solid #d69b25;margin:18px 0}a{color:#075f9f}h2{font-size:22px}.probes{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}.probes img{width:100%;background:black}.probes figcaption{font-size:15px}.probes figure{padding:10px}button{font:inherit;border:1px solid #7898b4;background:white;border-radius:8px;padding:6px 12px;cursor:pointer}small{font-size:14px}@media(max-width:700px){.grid{grid-template-columns:1fr}main{padding:16px}h1{font-size:23px}}</style>
<main><h1>阿德：頭部跳動穩定優化</h1><p>相同4.4秒家豪配音、25fps。原版相似度與自然度已接受；右側是新的穩定化候選。</p>
<div class="grid"><figure><figcaption>原版｜已接受的SadTalker小樣</figcaption><video src="baseline_accepted.mp4" controls playsinline preload="metadata"></video><p><a href="baseline_accepted.mp4" download>下載原版MP4</a></p></figure><figure><figcaption>優化版｜小幅位移校正</figcaption><video src="head_stabilized.mp4" controls playsinline preload="metadata"></video><p><a href="head_stabilized.mp4" download>下載穩定化MP4</a></p></figure></div>
<p><button id="slow">兩段慢速 ×0.5</button> 播放任一影片會暫停另一段，避免聲音重疊。</p>
<div class="note">以頭髮區估計的逐格位移RMS：1.05 → 0.07像素（約降低93%）。這只量測該區域的整體位移；局部臉部形變仍可能存在。沒有改變幀序或配音時間，也沒有將相鄰嘴型平均混合。尚未接回身體。</div>
<h2>眨眼能力測試</h2><p>原生已啟用隨機眨眼，但這張Q版大眼的閉合較弱。以下是同一個時間點的單格參數探測；強度超出原生範圍後會改變臉型與嘴角，因此<strong>未套入上方影片</strong>，也不當成自然完整閉眼已通過。</p>
<details><summary>查看眨眼參數的單格比較與副作用</summary><div class="probes">PROBES</div><p>2.5以上為研究用外插強度，非官方建議值。後續若要明顯閉眼，優先評估同角色閉眼關鍵圖／局部眼皮動作，或校準眨眼參考影片，另做短測驗收。</p></details>
<p>本頁與成品皆為私人本機輸出。<a href="head_stabilized.json">穩定化參數與量測</a></p></main>
<script>const videos=[...document.querySelectorAll('video')];videos.forEach(v=>v.addEventListener('play',()=>videos.filter(x=>x!==v).forEach(x=>x.pause())));document.getElementById('slow').onclick=function(){let rate=videos[0].playbackRate===1?0.5:1;videos.forEach(v=>v.playbackRate=rate);this.textContent=rate===1?'兩段慢速 ×0.5':'恢復正常 ×1'};</script></html>'''
probes=''.join(f'<figure><figcaption>強度 {g}</figcaption><img src="blink_probe_{g}.png" alt="研究用強度{g}的眨眼模型畫格"></figure>' for g in ['0','2.5','4.0','6.0','8.0'] if (out/f'blink_probe_{g}.png').exists())
page=page.replace('PROBES',probes)
if (out/'manifest.json').exists() and json.loads((out/'manifest.json').read_text(encoding='utf-8')).get('user_accepted'):
    page=page.replace('右側是新的穩定化候選。','右側穩定效果也已接受，後續以此為基準。')
(out/'index.html').write_text(page,encoding='utf-8')
print(out/'index.html')
