const escapeHtml = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function rigSvg(enlarged = false, rig = {}) {
  const image = '<image href="assets/boy.png" width="1122" height="1402"/>';
  const bodyScale = rig.body_scale ?? 1;
  const bodyAnchor = rig.body_scale_anchor || [578,690];
  const headBottom = rig.head_clip_bottom ?? 660;
  const headPivot = rig.head_pivot || [568,655];
  if (!Number.isFinite(bodyScale) || bodyScale<=0 || bodyScale>2 ||
      !Array.isArray(bodyAnchor) || bodyAnchor.length!==2 || !bodyAnchor.every(Number.isFinite) ||
      !Number.isFinite(headBottom) || headBottom<=0 || headBottom>1402 ||
      !Array.isArray(headPivot) || headPivot.length!==2 || !headPivot.every(Number.isFinite)) {
    throw Error('頭身縮放、裁切與接合軸點需為有效數值');
  }
  const join = rig.neck_bridge;
  if (join && (!rig.head_layer || !Array.isArray(join.top) || !Array.isArray(join.bottom) ||
      join.top.length!==3 || join.bottom.length!==3 || ![...join.top,...join.bottom].every(Number.isFinite) ||
      join.top[0]>=join.top[1] || join.bottom[0]>=join.bottom[1] || join.top[2]>=join.bottom[2] ||
      ![join.color_top,join.color_bottom,join.outline].every(c=>/^#[0-9a-f]{6}$/i.test(c)))) {
    throw Error('頸部接合需有獨立頭像、有效上下邊界與六碼色彩');
  }
  let neck = '', neckDefs = '';
  if (join) {
    const [l,r,y]=join.top,[bl,br,by]=join.bottom,mid=(bl+br)/2,cy=(y+by)/2;
    neckDefs=`<linearGradient id="neckSkin" x1="0" y1="0" x2="0" y2="1"><stop stop-color="${join.color_top}"/><stop offset="1" stop-color="${join.color_bottom}"/></linearGradient>`;
    neck=`<g id="neck-bridge"><path d="M${l} ${y}H${r}C${r} ${cy} ${br} ${cy} ${br} ${by}Q${mid} ${by+10} ${bl} ${by}C${bl} ${cy} ${l} ${cy} ${l} ${y}Z" fill="url(#neckSkin)"/><path d="M${l} ${y}C${l} ${cy} ${bl} ${cy} ${bl} ${by}M${r} ${y}C${r} ${cy} ${br} ${cy} ${br} ${by}" fill="none" stroke="${join.outline}" stroke-width="4" stroke-linecap="round"/></g>`;
  }
  const layer = rig.head_layer;
  if (layer && (!/^[^/\\]+\.png$/i.test(layer.file) || !Array.isArray(layer.target_rect) ||
      layer.target_rect.length!==4 || !layer.target_rect.every(Number.isFinite) || layer.target_rect[2]<=0 || layer.target_rect[3]<=0)) {
    throw Error('新頭像需為單一 PNG 檔名及已校準的 target_rect');
  }
  const headImage = layer ? `<image href="assets/${escapeHtml(layer.file)}" x="${layer.target_rect[0]}" y="${layer.target_rect[1]}" width="${layer.target_rect[2]}" height="${layer.target_rect[3]}" preserveAspectRatio="xMidYMid meet"/>` : image;
  const mouthCenter = rig.mouth_center || [578,557];
  if(!Array.isArray(mouthCenter)||mouthCenter.length!==2||!mouthCenter.every(Number.isFinite))throw Error('嘴型中心需為兩個數值');
  const mouthScale = rig.mouth_scale ?? 1;
  if(!Number.isFinite(mouthScale)||mouthScale<=0)throw Error('嘴型比例需為正數');
  const part = (id, clip) => `<g id="${id}"><g clip-path="url(#${clip})">${image}</g></g>`;
  const repaired = rig.version === 'overlapping-shoulder-v1';
  // Full sleeves rotate with the arms. Their round shoulder caps stay underneath
  // the continuous torso, instead of rotating a severed forearm below a fixed sleeve.
  const atlas = '<image href="assets/arm_torso_atlas_v1.png" width="1536" height="1024"/>';
  const sprite = (id, clip, source, target, sx, sy=sx) => `<g id="${id}"><g transform="translate(${target.join(' ')}) scale(${sx} ${sy}) translate(${-source[0]} ${-source[1]})"><g clip-path="url(#${clip})">${atlas}</g></g></g>`;
  const arms = repaired ?
    sprite('arm-left','atlasArmL',[320,295],rig.shoulders.left,.52) +
    sprite('arm-right','atlasArmR',[1215,295],rig.shoulders.right,.52) :
    part('arm-left','armLClip')+part('arm-right','armRClip');
  const torso = repaired ? part('shorts','shortsClip') +
    sprite('torso','atlasTorso',[776,200],[578,650],.635,.555) : part('torso','bodyClip');
  const body = part('leg-left','legLClip')+part('leg-right','legRClip')+arms+torso;
  const bodyMarkup = bodyScale===1 ? body : `<g id="body-proportion" transform="translate(${bodyAnchor.join(' ')}) scale(${bodyScale}) translate(${-bodyAnchor[0]} ${-bodyAnchor[1]})">${body}</g>`;
  // Tight arm silhouettes exclude shirt-edge pixels that became stray lines at large angles.
  const armL = enlarged ? 'M328 806L417 864 363 945 377 985 367 1017 333 1053H220V949L278 924Z' : 'M328 806L425 845 369 944 385 991 380 1062H220V949L278 924Z';
  const armR = enlarged ? 'M733 846L796 804 858 923 902 951V1064H773L759 1007 755 979 765 946Z' : 'M733 846L796 804 858 923 902 951V1064H747L744 990 754 946Z';
  return `<svg id="puppet" viewBox="0 0 1122 1402" width="1122" height="1402" aria-label="阿忠分層角色">
  <defs>
    <clipPath id="headClip"><path d="M0 0H1122V${headBottom}H0Z"/></clipPath>
    <clipPath id="bodyClip"><path d="M480 654H650L750 706 830 804 735 865 756 973 765 1084 725 1117 580 1114 565 1038 550 1116 399 1115 362 1083 380 973 422 866 300 813 383 717Z"/></clipPath>
    <clipPath id="armLClip"><path d="${armL}"/></clipPath>
    <clipPath id="armRClip"><path d="${armR}"/></clipPath>
    <clipPath id="legLClip"><path d="M399 1080H565V1402H280V1190L365 1140Z"/></clipPath>
    <clipPath id="legRClip"><path d="M575 1080H730L780 1160 850 1210V1402H575Z"/></clipPath>
    <clipPath id="shortsClip"><path d="M380 978H756L765 1084 725 1117 580 1114 565 1038 550 1116 399 1115 362 1083Z"/></clipPath>
    <clipPath id="atlasArmL"><rect x="0" y="0" width="455" height="1024"/></clipPath>
    <clipPath id="atlasTorso"><rect x="460" y="0" width="630" height="1024"/></clipPath>
    <clipPath id="atlasArmR"><rect x="1095" y="0" width="441" height="1024"/></clipPath>
    ${neckDefs}
  </defs>
  ${bodyMarkup}${neck}
  <g id="head"> <g clip-path="url(#headClip)">${headImage}</g>
    <g id="mouth" transform="translate(${mouthCenter.join(' ')}) scale(${mouthScale})" stroke="#743b20" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
      <path class="mouth-shape" id="mouth-X" d="M-28 0 Q0 17 28 0" fill="none"/>
      <path class="mouth-shape" id="mouth-A" d="M-27 2 Q0 8 27 2" fill="none"/>
      <g class="mouth-shape" id="mouth-B"><path d="M-34-5Q0-12 34-5L29 13Q0 22-29 13Z" fill="#fff8e8"/><path d="M-28 8H28" stroke-width="3"/></g>
      <g class="mouth-shape" id="mouth-C"><path d="M-33-5Q0-11 33-5Q30 33 0 35Q-30 33-33-5Z" fill="#763221"/><path d="M-18 25Q0 13 18 25" stroke="#ee8b7c" stroke-width="10"/></g>
      <g class="mouth-shape" id="mouth-D"><ellipse cy="10" rx="29" ry="33" fill="#763221"/><path d="M-15 30Q0 18 15 30" stroke="#ee8b7c" stroke-width="10"/></g>
      <ellipse class="mouth-shape" id="mouth-E" cy="5" rx="22" ry="24" fill="#763221"/>
      <ellipse class="mouth-shape" id="mouth-F" cy="3" rx="14" ry="19" fill="#763221"/>
      <g class="mouth-shape" id="mouth-G"><path d="M-28-4Q0-9 28-4L23 15Q0 22-23 15Z" fill="#763221"/><path d="M-23-1H23L18 5H-18Z" fill="#fff8e8" stroke="none"/></g>
      <g class="mouth-shape" id="mouth-H"><path d="M-30-4Q0-10 30-4Q24 25 0 27Q-24 25-30-4Z" fill="#763221"/><path d="M-14 18Q0 8 14 18" stroke="#ee8b7c" stroke-width="10"/></g>
    </g>
  </g></svg>`;
}

function sceneSvg(kind, theme = 'school-safety') {
 const common = 'viewBox="0 0 740 340" width="740" height="340" fill="none" stroke="#315958" stroke-width="6" stroke-linejoin="round"';
 if(theme==='anti-bullying'){
  const pupil=(x,y,shirt,teacher=false)=>`<g transform="translate(${x} ${y})"><circle cy="-80" r="${teacher?34:29}" fill="#ffddb5"/><path d="M-28-89Q-27-119 0-114Q26-114 29-90" fill="#42565d"/><circle cx="-10" cy="-80" r="3" fill="#315958" stroke="none"/><circle cx="10" cy="-80" r="3" fill="#315958" stroke="none"/><path d="M-9-67Q0-60 9-67" stroke-width="4"/><path d="M-27-43Q0-52 27-43L36 36H-36Z" fill="${shirt}"/><path d="M-18 38L-24 83M18 38L24 83" stroke-width="15"/><path d="M-30-34L-57 14M30-34L57 14" stroke-width="12"/></g>`;
  const room='<rect x="35" y="20" width="670" height="265" rx="25" fill="#e9f2e8" stroke="none"/><path d="M35 285H705" stroke="#bbd4c4" stroke-width="10"/>';
  if(kind===0)return `<svg ${common} aria-label="不同同學友善相處示意">${room}${pupil(205,194,'#7db6ce')}${pupil(370,194,'#edba69')}${pupil(535,194,'#a4c48b')}<path d="M270 180Q288 147 305 180M435 180Q453 147 470 180" stroke="#4382a5" stroke-width="9"/><path d="M353 62Q331 40 344 29Q355 22 366 35Q378 22 389 29Q403 42 380 62L367 74Z" fill="#e69d83" stroke="none"/></svg>`;
  if(kind===1)return `<svg ${common} aria-label="同學向老師求助示意">${room}${pupil(245,194,'#7db6ce')}${pupil(505,194,'#a4c48b',true)}<path d="M306 125H399L380 109M399 125L380 141" stroke="#4382a5" stroke-width="9"/><path d="M305 53Q305 37 321 37H391Q407 37 407 53V77Q407 91 391 91H351L332 109V91H321Q305 91 305 77Z" fill="#fff9e7"/><circle cx="356" cy="56" r="4" fill="#c18b3b" stroke="none"/><path d="M356 67V78" stroke="#c18b3b"/></svg>`;
  return `<svg ${common} aria-label="互相尊重友善校園示意">${room}${pupil(205,194,'#a4c48b')}${pupil(370,194,'#7db6ce')}${pupil(535,194,'#edba69')}<path d="M260 208L315 208M425 208L480 208" stroke="#e6ae69" stroke-width="14"/><path d="M332 52Q306 27 326 15Q345 8 365 31Q385 8 404 15Q425 29 397 52L365 82Z" fill="#e69d83" stroke="none"/></svg>`;
 }
 if (kind===0) return `<svg ${common} aria-label="走廊慢行教學示意"><path d="M30 290V35H710V290" fill="#e4f1e9"/><path d="M30 290H710L600 185H140Z" fill="#d0e6da"/><path d="M140 185V35M600 185V35M140 185H600"/><path d="M198 150V68H300V150ZM440 150V68H542V150Z" fill="#fff9e7"/><path d="M225 260H330M400 260H505" stroke="#d69d46" stroke-width="12"/><circle cx="370" cy="116" r="28" fill="#fff2d4"/><path d="M370 145V213M370 166L337 190M370 166L402 190M370 212L350 259M370 212L394 259" stroke-width="12"/></svg>`;
 if (kind===1) return `<svg ${common} aria-label="樓梯靠右教學示意"><path d="M70 285H200V235H330V185H460V135H590V85H680" stroke-width="12"/><path d="M65 225L650 28" stroke="#c28b3d" stroke-width="12"/><path d="M513 260V170M493 195L513 170 533 195" stroke="#37765a" stroke-width="14"/><path d="M603 260V170M583 195L603 170 623 195" stroke="#37765a" stroke-width="14"/><rect x="70" y="36" width="225" height="80" rx="30" fill="#edf5eb" stroke="none"/></svg>`;
 return `<svg ${common} aria-label="主動幫助同學教學示意"><path d="M50 286H690" stroke="#bad4c5" stroke-width="10"/><circle cx="290" cy="105" r="34" fill="#fff2d4"/><circle cx="460" cy="105" r="34" fill="#fff2d4"/><path d="M290 143V222L260 283M290 222L320 283M460 143V222L430 283M460 222L490 283" stroke-width="15"/><path d="M290 165L365 203 460 165" stroke="#4382a5" stroke-width="16"/><path d="M265 165L224 216M485 165L526 216" stroke-width="12"/><path d="M375 79C337 47 321 11 350 10Q372 9 375 29Q384 7 402 11C431 19 410 55 375 79Z" fill="#e79c80" stroke="none"/></svg>`;
}

function buildHtml({config,mode,speech,cues,captions,customCharacter=null}) {
 const lead = config.video_timing?.lead_in_sec ?? 0;
 const tail = config.video_timing?.tail_out_sec ?? 0;
 if(![lead,tail].every(v=>Number.isFinite(v)&&v>=0&&v<=10))throw Error('片頭與片尾停頓需為0至10秒');
 const duration = speech.duration + lead + tail;
 const mouthCues = cues.mouthCues.map(c=>({...c,start:c.start+lead,end:c.end+lead}));
 captions = captions.map(c=>({...c,start:c.start+lead,end:c.end+lead}));
 const presentation = config.presentation;
 if(presentation && captions.length)captions[captions.length-1].end=Math.max(captions[captions.length-1].end,duration-.2);
 if(presentation && (!['school-safety','anti-bullying'].includes(presentation.theme) ||
    !Array.isArray(presentation.scenes) || presentation.scenes.length!==3 ||
    presentation.scenes.some(s=>!['title','detail','caption_prefix'].every(k=>typeof s[k]==='string'&&s[k].length))))throw Error('教材需為支援主題與三段含字幕定位的內容');
 const motion = config.motion_profile || null;
 const names = customCharacter?.modeLabels || (motion ? {1:'手部加大・慢舉手',2:'自然加大・慢動作',3:'活潑加大・慢動作'} : {1:'只有手部',2:'自然微幅',3:'活潑原地'});
 // A new voice has new phrase boundaries. Never reuse the first voice's seconds.
 const sceneStarts = presentation ? [0,...presentation.scenes.slice(1).map(s=>captions.find(c=>c.text.startsWith(s.caption_prefix))?.start)] : motion ? [0,
   captions.find(c=>c.text.startsWith('上下樓梯'))?.start,
   captions.find(c=>c.text.startsWith('看見同學'))?.start] : [0,5.536833,8.010541];
 if(sceneStarts.some(t=>typeof t!=='number')) throw Error('缺少分鏡詞界，需人工核對');
 if(sceneStarts.some((t,i)=>t<0||t>=duration||(i>0&&t<=sceneStarts[i-1])))throw Error('分鏡起點需依音訊遞增');
 const sceneEnds = [...sceneStarts.slice(1),duration];
 const scale = 1080 * config.placement.visible_height_ratio / (config.rig.visible_bbox[3]-config.rig.visible_bbox[1]);
 const left = config.placement.left - config.rig.visible_bbox[0]*scale;
 const top = 1080-config.placement.bottom-config.rig.visible_bbox[3]*scale;
 const title = presentation?.scenes.map(s=>s.title) || ['走廊慢慢走','上下樓梯靠右行','主動幫助同學'];
 const detail = presentation?.scenes.map(s=>s.detail) || ['放慢腳步，安全到教室','靠右行走，留意前方','看見需要，主動關心'];
 const panels = title.map((t,i)=>`<section class="scene clip" id="scene-${i}" data-start="${sceneStarts[i]}" data-duration="${sceneEnds[i]-sceneStarts[i]}" data-track-index="1"><div class="lesson"><div class="step">0${i+1} ／ ${escapeHtml(presentation?.lesson_label || '校園小提醒')}</div><h2>${escapeHtml(t)}</h2><p class="explain">${escapeHtml(detail[i])}</p><div class="drawing">${sceneSvg(i,presentation?.theme)}</div></div></section>`).join('');
 const captionTags = captions.map((c,i)=>`<div id="caption-clip-${i}" class="caption clip" data-start="${c.start}" data-duration="${c.end-c.start}" data-track-index="4" data-layout-allow-caption-zone><span id="caption-${i}">${escapeHtml(c.text)}</span></div>`).join('');
 return `<!doctype html><html lang="zh-Hant"><head><meta charset="UTF-8"><meta name="viewport" content="width=1920,height=1080"><title>${escapeHtml(config.character || '阿忠')}｜模式 ${mode}</title>
 <script src="assets/gsap.min.js"></script><style>
 @font-face{font-family:NotoTC;src:url('assets/NotoSansTC.ttf') format('truetype');font-weight:100 900;font-display:block}
 *{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;font-family:NotoTC,sans-serif;background:#f9f7ef;color:#234846}
 #root{position:relative;width:100%;height:100%;overflow:hidden;background:linear-gradient(130deg,#faf8ef,#eff5e9)}
 #heading{position:absolute;left:96px;top:70px;margin:0;font-size:66px;font-weight:800;letter-spacing:2px}
 .eyebrow{position:absolute;left:100px;top:164px;font-size:26px;color:#48645e;letter-spacing:3px}
 .mode{position:absolute;left:100px;top:265px;font-size:25px;border:2px solid #b4cbbb;border-radius:24px;padding:10px 24px;color:#31584e;background:#f4f8ed}
 .scene{position:absolute;left:645px;top:265px;width:1170px;height:615px}
 .lesson{position:relative;width:100%;height:100%;border-radius:36px;background:#fffdf4;border:2px solid #d4dfca;padding:40px 52px;overflow:hidden;opacity:0}
 .step{font-size:23px;color:#53683b;letter-spacing:4px}.lesson h2{font-size:60px;line-height:1.4;margin:18px 0 12px;font-weight:800}
 .explain{font-size:31px;margin:0;color:#54735e}.drawing{position:absolute;left:365px;top:255px;width:740px;height:340px}
 .drawing svg{display:block}.caption{position:absolute;left:625px;top:916px;width:1190px;height:106px;text-align:center;display:flex;align-items:center;justify-content:center;font-size:42px;font-weight:650;color:#fffdf4}.caption span{opacity:0;width:100%;background:#234846;border-radius:20px;padding:16px 22px}
 #character-region{position:absolute;left:62px;top:493px;width:535px;height:550px;overflow:hidden}
 #rig-scale{position:absolute;left:${left-62}px;top:${top-493}px;transform:scale(${scale});transform-origin:0 0;width:1122px;height:1402px}
 #puppet{display:block;overflow:visible}.mouth-shape{opacity:0}#mouth-X{opacity:1}
 .label{position:absolute;left:101px;top:400px;font-size:28px;color:#31584e;font-weight:650}
 ${presentation?'.eyebrow,.mode,.step{font-size:28px}':''}
 ${customCharacter?.styles || ''}
 </style></head><body><div id="root" data-composition-id="mode${mode}" ${customCharacter?'':'data-start="0" '}data-width="1920" data-height="1080" data-duration="${duration}">
 <h1 id="heading">${escapeHtml(presentation?.title || '一起打造安全、友善的校園')}</h1><div class="eyebrow">${escapeHtml(presentation?.eyebrow || '阿忠陪你學・校園安全與友善')}</div><div class="mode">動作 ${mode}　${names[mode]}</div><div class="label">${escapeHtml(presentation?.character_label || '大家好，我是阿忠！')}</div>
 ${(config.voice_note || config.rig.version==='overlapping-shoulder-v1')?'<div class="voice-note" style="position:absolute;left:101px;top:450px;font-size:'+(presentation?28:21)+'px;color:#48645e">'+escapeHtml(config.voice_note || '手部修復測試｜暫用台灣成人男聲')+'</div>':''}
 ${panels}${customCharacter?`<div id="character-region" data-track-index="2">${customCharacter.html}</div>`:`<div id="character-region" class="clip" data-start="0" data-duration="${duration}" data-track-index="2"><div id="rig-scale" data-layout-allow-overflow>${rigSvg(!!motion,config.rig)}</div></div>`}
 ${captionTags}<audio id="voice" src="assets/voice.wav" data-start="${lead}" data-duration="${speech.duration}" data-track-index="3" data-has-audio="true"></audio></div>
 ${customCharacter?.scripts || ''}<script>
 const MODE=${mode}, DURATION=${duration};
 const motionProfile=${JSON.stringify(motion)};
 const mouthCues=${JSON.stringify(mouthCues)};
 const captions=${JSON.stringify(captions)};
 const tl=gsap.timeline({paused:true});
 ${customCharacter?'':`
 tl.set('.mouth-shape',{opacity:0},0).set('#mouth-X',{opacity:1},0);
 for(const cue of mouthCues){tl.set('.mouth-shape',{opacity:0},cue.start);tl.set('#mouth-'+cue.value,{opacity:1},cue.start)}
 tl.set('.mouth-shape',{opacity:0},${cues.metadata.duration+lead}).set('#mouth-X',{opacity:1},${cues.metadata.duration+lead});
 `}
 const sceneStarts=${JSON.stringify(sceneStarts)};
 for(let i=0;i<3;i++){tl.set('#scene-'+i+' .lesson',{opacity:1},sceneStarts[i]);if(i<2)tl.set('#scene-'+i+' .lesson',{opacity:0},sceneStarts[i+1])}
 for(let i=0;i<captions.length;i++){tl.set('#caption-'+i,{opacity:1},captions[i].start);tl.set('#caption-'+i,{opacity:0},captions[i].end);}
 const beats=motionProfile?[]:[.25,2.2,4.4,6.2,8.4,10.1,12.2,14.1];
 ${customCharacter?'':`
 gsap.set('#arm-left',{svgOrigin:'${config.rig.shoulders?.left?.join(' ') || '373 833'}'});gsap.set('#arm-right',{svgOrigin:'${config.rig.shoulders?.right?.join(' ') || '764 834'}'});
 gsap.set('#head',{svgOrigin:'${(config.rig.head_pivot || [568,655]).join(' ')}'});gsap.set('#leg-left',{svgOrigin:'476 1100'});gsap.set('#leg-right',{svgOrigin:'655 1100'});
 function gesture(target,start,angle,lift=0){tl.to(target,{rotation:angle,y:lift,duration:.38,ease:'sine.inOut'},start).to(target,{rotation:0,y:0,duration:.5,ease:'sine.inOut'},start+.54)}
 beats.forEach((b,i)=>{
   const sign=i%2?1:-1;gesture(i%2?'#arm-right':'#arm-left',b,MODE===3?sign*18:MODE===2?sign*10:sign*7);
   if(MODE>1){gesture('#head',b+.12,sign*(MODE===3?4:1.7));gesture(i%2?'#leg-left':'#leg-right',b+.22,sign*(MODE===3?4.5:1.7),MODE===3?-17:-6)}
 });
 if(motionProfile){
   const p=motionProfile,pose=p.modes[String(MODE)],cycle=p.rise_sec+p.hold_sec+p.lower_sec;
   function raise(target,start,angle,lift=0){
     tl.to(target,{rotation:angle,y:lift,duration:p.rise_sec,ease:'sine.inOut'},start)
       .to(target,{rotation:0,y:0,duration:p.lower_sec,ease:'sine.inOut'},start+p.rise_sec+p.hold_sec);
   }
   for(let b=p.first_raise_sec,i=0;b+cycle<DURATION-.25;b+=p.interval_sec,i++){
     beats.push(b);
     // Existing IDs describe screen sides: screen-right is the character's left.
     raise('#arm-right',b,pose.left_arm_deg);
     if(b+.25+cycle<DURATION-.05)raise('#arm-left',b+.25,pose.other_arm_deg);
     if(MODE>1){
       const sign=i%2?1:-1;
       raise('#head',b+.1,sign*pose.head_deg);
       raise(i%2?'#leg-left':'#leg-right',b+.15,sign*pose.leg_deg,-pose.leg_lift_source_px);
     }
   }
 }
 `}
 ${customCharacter?'':"tl.to({}, {duration:.001},DURATION-.001);"}
 ${customCharacter?'':"window.__timelines=window.__timelines||{};window.__timelines['mode"+mode+"']=tl;"}
 window.__avatarTest={mode:MODE,mouthCues,captions,sceneStarts,motionProfile,beats,duration:DURATION,audioStart:${lead},audioDuration:${speech.duration},sceneCaptionPrefixes:${JSON.stringify(presentation?.scenes.map(s=>s.caption_prefix) || ['','上下樓梯','看見同學'])},scale:${scale},rootPosition:[${left},${top}],voiceAccepted:${!!config.voice_user_accepted},rig:${JSON.stringify(config.rig)}};
 ${customCharacter?.initialize || ''}
 </script></body></html>`;
}
module.exports = { buildHtml, rigSvg };
