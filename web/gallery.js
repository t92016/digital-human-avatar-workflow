const root=new URL('../',import.meta.url),url=p=>new URL(p,root).href;
const modeNames=['① 只有手部','② 自然版','③ 活潑版'];
const modeDescriptions=['手部抬放，頭部與雙腳維持原地。適合穩定的專業解說。','手部配合腳部與頭部微幅動作，保留自然停頓。','較活潑的原地手腳與頭部動作，適合小學宣導。'];
const text=(tag,value,className)=>{const e=document.createElement(tag);e.textContent=value;if(className)e.className=className;return e};
async function start(){
 const response=await fetch(url('config/publication.json'));if(!response.ok)throw Error('示範清單尚未載入，請稍後重新整理。');
 const data=await response.json();
 if(document.body.dataset.page==='home'){
  const previews=document.querySelector('#hero-previews');previews.replaceChildren();
  for(const [i,g] of data.groups.entries()){
   const figure=document.createElement('figure'),pic=document.createElement('img');pic.src=url(g.poster);pic.alt=g.title;figure.append(pic);previews.append(figure);
   const card=document.createElement('a');card.className='card';card.href=url(g.page);card.setAttribute('aria-label',`觀看${g.title}的三種動作`);
   const thumb=document.createElement('div');thumb.className='card-thumb';const image=document.createElement('img');image.src=url(g.poster);image.alt=g.subtitle;image.loading='lazy';thumb.append(image,text('span',`0${i+1} / 完成示範`,'card-number'),text('span','▶','play-badge'));
   const copy=document.createElement('div');copy.className='card-copy';copy.append(text('span',g.body,'tag'),text('h3',g.title),text('p',g.description));const bottom=document.createElement('div');bottom.className='card-bottom';bottom.append(text('span',`約13秒 · ${g.resolution[1]}p`),text('strong','切換三種動作 →'));copy.append(bottom);card.append(thumb,copy);document.querySelector('#showcase-cards').append(card);
  }return;
 }
 if(document.body.dataset.page!=='showcase')return;
 const group=data.groups.find(g=>g.id===document.body.dataset.group);if(!group)throw Error('找不到這組示範。');
 document.title=`${group.title}｜三種動作`;document.querySelector('#group-title').textContent=group.title;document.querySelector('#group-subtitle').textContent=group.subtitle;
 const links=document.querySelector('#group-switch');for(const g of data.groups){const a=text('a',g.id==='azhong'?'阿忠校園安全':g.id==='ade-school'?'阿德＋阿忠身體':'阿德個人身體');a.href=url(g.page);if(g.id===group.id){a.className='current';a.setAttribute('aria-current','page')}links.append(a)}
 const details=document.querySelector('#details');for(const [label,value] of [['主題',group.topic],['角色身體',group.body],['配音',group.voice],['影片規格',`${group.duration}秒 · 1920×1080 · 24fps`]])details.append(text('dt',label),text('dd',value));
 document.querySelector('#version-note').textContent=group.note;
 const video=document.querySelector('#player'),download=document.querySelector('#download'),buttons=[...document.querySelectorAll('[data-mode]')];let current=2,rate=1,requestId=0;
 video.poster=url(group.poster);
 function update(mode){current=mode;buttons.forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.mode)===mode)));download.href=url(group.videos[mode-1].path);download.download=group.id+'-'+['hands','natural','lively'][mode-1]+'.mp4';document.querySelector('#mode-description').textContent=modeDescriptions[mode-1];document.querySelector('#status').textContent=`目前：${modeNames[mode-1]} · ${rate===1?'正常速度':'0.5倍速'}`;}
 function choose(mode,keepTime=true){const token=++requestId,t=keepTime?video.currentTime:0,playing=!video.paused;video.pause();update(mode);video.src=url(group.videos[mode-1].path);video.addEventListener('loadedmetadata',()=>{if(token!==requestId)return;video.playbackRate=rate;video.currentTime=Math.min(t,Math.max(0,video.duration-.05));if(playing)video.play().catch(()=>{})},{once:true});video.load();}
 buttons.forEach(b=>b.addEventListener('click',()=>choose(Number(b.dataset.mode))));
 document.querySelector('#slow').addEventListener('click',event=>{rate=rate===1?.5:1;video.playbackRate=rate;event.currentTarget.textContent=rate===1?'0.5倍慢速':'恢復正常速度';update(current)});
 document.querySelector('#replay').addEventListener('click',()=>{video.currentTime=0;video.play().catch(()=>{})});
 document.querySelector('#peak').addEventListener('click',()=>{video.pause();video.currentTime=1.9});
 const zoom=document.querySelector('#zoom'),ctx=zoom.getContext('2d'),zoomDetails=document.querySelector('#zoom-details');
 function draw(){if(zoomDetails.open&&video.readyState>=2){const r=group.id==='ade-personal'?[62,493,535,550]:[36,480,570,565];ctx.clearRect(0,0,535,550);ctx.drawImage(video,...r,0,0,535,550)}requestAnimationFrame(draw)}draw();
 video.addEventListener('error',()=>{document.querySelector('#status').textContent='影片載入失敗。可使用下載連結，或重新整理此頁。'});choose(2,false);
}
start().catch(error=>{const target=document.querySelector('#showcase-cards')||document.querySelector('#status');if(target){target.textContent=error.message;target.classList.add('error')}});
