/* Adapter into the existing teaching composition; all original panels/audio/subtitles remain. */
function personalCharacter({cfg,base,art,contours,mode,geometryOnly=false}){
 const [hx,hy,hw,hh]=base.head_rect,[tx,ty,tw,th]=base.torso_rect,p=base.pelvis;
 return {
 modeLabels:{1:'只有手部',2:'自然版',3:'活潑版'},
 styles:`#ade-actor{position:absolute;left:${cfg.actor_left-62}px;top:${cfg.actor_top-493}px;width:1024px;height:1536px;transform:scale(${cfg.actor_scale});transform-origin:0 0}#body-shared{position:absolute;inset:0}#limbs{position:absolute;left:-180px;top:-80px;width:1400px;height:1680px}#ade-torso{position:absolute;inset:0;width:1024px;height:1536px}#head-motion{position:absolute;left:${hx}px;top:${hy}px;width:${hw}px;height:${hh}px;transform-origin:${cfg.head_pin[0]-hx}px ${cfg.head_pin[1]-hy}px;clip-path:inset(0 0 48px 0);mask-image:linear-gradient(to bottom,#000 0px,#000 500px,transparent 517px,transparent 565px)}#head-media{display:block;width:100%;height:100%;object-fit:contain}#ade-atlas{display:none}`,
 html:`<div id="ade-actor" data-layout-allow-overflow="transparent intrinsic work area; visible silhouette checked per frame"><div id="body-shared"><canvas id="limbs" width="1400" height="1680" data-layout-allow-overflow="transparent padding for connected limbs"></canvas><svg id="ade-torso" viewBox="0 0 1024 1536" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="pelvis-feather" x1="0" y1="765" x2="0" y2="825" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient><mask id="pelvis-mask" maskUnits="userSpaceOnUse" x="150" y="600" width="360" height="291"><rect x="150" y="600" width="360" height="291" fill="url(#pelvis-feather)"/></mask><clipPath id="pelvis-clip"><path d="${contours.pelvis}"/></clipPath></defs><g transform="translate(${p.pivot.join(' ')}) scale(${p.scale}) translate(${-p.source_pivot[0]} ${-p.source_pivot[1]})"><image href="assets/atlas.png" width="1536" height="1024" mask="url(#pelvis-mask)" clip-path="url(#pelvis-clip)"/></g><image href="assets/torso.png" x="${tx}" y="${ty}" width="${tw}" height="${th}"/></svg><div id="head-motion">${geometryOnly?'<img id="head-media" src="assets/head.png" alt="僅內部幾何預覽，完整對嘴尚在生成">':'<video id="head-media" class="clip" src="assets/head.webm" muted playsinline data-start="0" data-duration="13" data-track-index="5"></video>'}</div></div></div><img id="ade-atlas" src="assets/atlas.png" alt="本人服裝材質圖集">`,
 scripts:'<script src="assets/puppet.js"></script>',
 initialize:`
 const cfg=${JSON.stringify(cfg)},base=${JSON.stringify(base)},art=${JSON.stringify(art)},contours=${JSON.stringify(contours)};
 async function attachPersonalBody(){
   const atlas=document.querySelector('#ade-atlas');await atlas.decode();await document.fonts.ready;
   const puppet=new ContinuousPuppet(document.querySelector('#limbs'),atlas,base,art,contours);
   const state={arm_left_upper:0,arm_left_bend:0,arm_right_upper:0,arm_right_bend:0,leg_left_upper:0,leg_left_bend:0,leg_right_upper:0,leg_right_bend:0,head:0};
   const pose=cfg.modes[String(MODE)],timing=cfg.timing,head=document.querySelector('#head-motion'),shared=document.querySelector('#body-shared');
   function draw(){const r=puppet.draw(state);shared.style.transform='translateY('+r.dip+'px)';head.style.transform='rotate('+state.head+'deg) scale('+cfg.head_scale+')';window.__rigDiagnostics={...r,state:Object.fromEntries(Object.entries(state).filter(([k,v])=>typeof v==='number')),mode:MODE};}
   function move(key,angle,start){tl.to(state,{[key]:angle,duration:timing.rise,ease:'sine.inOut'},start);tl.to(state,{[key]:0,duration:timing.lower,ease:'sine.inOut'},start+timing.rise+timing.hold);}
   const cycles=[];
   for(let start=timing.first_raise_sec,i=0;start+timing.rise+timing.hold+timing.lower+timing.other_delay+timing.elbow_delay<DURATION-.15;start+=timing.interval_sec,i++){
    cycles.push(start);move('arm_right_upper',pose.right_upper_deg,start);move('arm_right_bend',pose.right_elbow_deg,start+timing.elbow_delay);move('arm_left_upper',pose.left_upper_deg,start+timing.other_delay);move('arm_left_bend',pose.left_elbow_deg,start+timing.other_delay+timing.elbow_delay);
    if(MODE>1){const reverse=i%2;move('leg_left_upper',reverse?-pose.right_hip_deg:pose.left_hip_deg,start+timing.knee_delay);move('leg_left_bend',reverse?-pose.right_knee_deg:pose.left_knee_deg,start+timing.knee_delay);move('leg_right_upper',reverse?-pose.left_hip_deg:pose.right_hip_deg,start+timing.knee_delay+.12);move('leg_right_bend',reverse?-pose.left_knee_deg:pose.right_knee_deg,start+timing.knee_delay+.12);move('head',(reverse?-1:1)*pose.head_deg,start+.15);}
   }
   tl.eventCallback('onUpdate',draw);draw();window.__puppetReady=true;window.__puppetDraw=draw;window.__personalBody={cfg,cycles,geometryOnly:${geometryOnly}};window.__avatarTest.beats=cycles;window.__timelines['mode${mode}']=tl;
 }attachPersonalBody();`
 };
}
module.exports={personalCharacter};
