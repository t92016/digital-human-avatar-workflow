"""Make a private, offline comparison page and inspection contact sheets."""
from __future__ import annotations
import argparse,html,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);args=p.parse_args()
    folder=args.directory.resolve();m=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if not m.get('complete_decode_passed'):raise ValueError('需要先完成實際MP4生成與解碼驗證')
    video=folder/m['video_file'];ffmpeg=ROOT/'tools/bin/ffmpeg.exe'
    for filename,filters in [
        ('qa_full_grid.png',"select='not(mod(n,7))',scale=312:312,tile=4x4"),
        ('qa_mouth_grid.png',"select='not(mod(n,7))',crop=420:260:440:820,tile=4x4")]:
        subprocess.run([str(ffmpeg),'-nostdin','-y','-v','error','-i',str(video),
            '-vf',filters,'-frames:v','1','-update','1',str(folder/filename)],check=True)
    page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>阿德｜SadTalker原嘴短測</title><style>
*{box-sizing:border-box}body{margin:0;background:#f0f4f8;color:#17304a;font-family:"Microsoft JhengHei",sans-serif;line-height:1.65}main{max-width:1120px;margin:auto;padding:24px}h1{font-size:28px;margin:0 0 8px}p{margin:8px 0 16px}.tag{background:#fff0bd;border-radius:8px;padding:8px 12px;display:inline-block}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;background:white;border:1px solid #ccd9e6;border-radius:14px;padding:16px}figcaption{font-size:19px;font-weight:700;margin-bottom:10px}img,video{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:#080a0f;border-radius:8px}canvas{display:block;width:100%;aspect-ratio:420/260;background:#080a0f;border-radius:8px}h2{font-size:21px;margin:28px 0 12px}small{display:block;margin-top:8px}button,a.button{font:inherit;padding:8px 14px;border:1px solid #8ba6bf;border-radius:8px;background:white;color:#17304a;cursor:pointer;margin:10px 8px 0 0}a{color:#075da8}details img{aspect-ratio:auto;background:white;margin:12px 0}.note{background:white;border-left:5px solid #cf890a;padding:12px 16px;margin-top:20px}@media(max-width:700px){main{padding:16px}.grid{grid-template-columns:1fr}h1{font-size:24px}}
</style><main><h1>阿德：用原本的嘴巴測試音訊對嘴</h1>
<p class="tag">頭像小樣，尚待你的嘴型驗收；這輪尚未接回校服身體。</p>
<p>家豪1602台灣成人男聲 · DURATION秒 · CPU／256版模型 · 無美顏修復</p>
<div class="grid"><figure><figcaption>原頭像：嘴唇保留的輸入原圖</figcaption><img id="source" src="original-head.png" alt="阿德原Q版頭像，原本嘴唇未抹除"><small>位元組相同副本，非去嘴底圖。</small></figure>
<figure><figcaption>SadTalker：由同一音訊驅動</figcaption><video id="sample" src="VIDEO" controls playsinline preload="auto" poster="poster.png"></video><button id="speed">慢速檢查 ×0.5</button><a class="button" href="VIDEO" download>下載MP4</a><small>請按播放聽聲音。看張嘴、閉嘴、停頓，以及眼鏡／臉型是否變形。</small></figure></div>
<h2>嘴部同步放大</h2><div class="grid"><figure><figcaption>原圖嘴唇</figcaption><canvas id="mouthOriginal" width="420" height="260"></canvas></figure><figure><figcaption>影片當前畫格</figcaption><canvas id="mouthVideo" width="420" height="260"></canvas></figure></div>
<p>測試台詞：同學們，不嘲笑、不排擠，也不跟著起鬨。</p>
<div class="note">模型會重建嘴唇、口腔與下顎細節，不能保證與原嘴像素完全一致。全圖輸出為RESOLUTION，內部仍使用256版模型；放大會看見柔化。原PNG的透明背景尚未處理成影片alpha，黑底不是最終合成版。</div>
<details><summary>逐格檢查（每0.28秒，從0秒到4.2秒）</summary><p>這些是實際MP4擷取畫格，不是HTML角色動畫。</p><img src="qa_full_grid.png" alt="16張完整頭像畫格"><img src="qa_mouth_grid.png" alt="16張嘴部中間畫格"></details>
<p><a href="jiahao-sample.wav">試聽這次原始短音訊</a> · <a href="manifest.json">參數及來源記錄</a></p></main>
<script>
const image=document.getElementById('source'),video=document.getElementById('sample');
function draw(media,id){if(!(media.naturalWidth||media.videoWidth))return;const c=document.getElementById(id),g=c.getContext('2d');const w=media.naturalWidth||media.videoWidth,h=media.naturalHeight||media.videoHeight;g.fillStyle='#080a0f';g.fillRect(0,0,c.width,c.height);g.drawImage(media,w*440/1254,h*820/1254,w*420/1254,h*260/1254,0,0,c.width,c.height)}
image.addEventListener('load',()=>draw(image,'mouthOriginal'));if(image.complete)draw(image,'mouthOriginal');
['loadeddata','seeked','timeupdate'].forEach(event=>video.addEventListener(event,()=>draw(video,'mouthVideo')));
if(video.requestVideoFrameCallback){function tick(){draw(video,'mouthVideo');video.requestVideoFrameCallback(tick)}video.requestVideoFrameCallback(tick)}
document.getElementById('speed').addEventListener('click',function(){video.playbackRate=video.playbackRate===1?.5:1;this.textContent=video.playbackRate===1?'慢速檢查 ×0.5':'恢復正常 ×1';});
</script></html>'''
    page=page.replace('DURATION',str(m['duration'])).replace('VIDEO',html.escape(video.name,quote=True)).replace('RESOLUTION','×'.join(map(str,m['resolution'])))
    if m.get('user_accepted'):
        page=page.replace('頭像小樣，尚待你的嘴型驗收；這輪尚未接回校服身體。','此版頭像相似度與自然度已接受；跳動與眨眼另做優化，尚未接回身體。')
    (folder/'index.html').write_text(page,encoding='utf-8')
    subprocess.run([str(ffmpeg),'-nostdin','-y','-v','error','-i',str(video),'-ss','1.2',
        '-frames:v','1','-update','1',str(folder/'poster.png')],check=True)
    print(str(folder/'index.html'))

if __name__=='__main__':main()
