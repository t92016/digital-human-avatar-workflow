/* Round10: continuous elbows/knees with the accepted round09 outfit and head. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),out=path.join(root,'outputs/round10');
const cfg=JSON.parse(fs.readFileSync(path.join(root,'config/round10.json'),'utf8'));
const base=JSON.parse(fs.readFileSync(path.join(root,cfg.base_config),'utf8'));
const oldManifest=path.join(out,'manifest.json');
if(fs.existsSync(oldManifest)&&JSON.parse(fs.readFileSync(oldManifest,'utf8')).user_accepted)throw Error('Accepted round: use a new round.');
const contours=JSON.parse(fs.readFileSync(path.join(root,'work/round09/sprite-contours.json'),'utf8')).paths;
const files={'atlas.png':'outputs/round09/character/body_parts_atlas_v1.png','torso.png':'outputs/round09/character/torso_armless_v2.png','head.webm':base.head_alpha,'head.png':base.head_still,'voice.wav':base.audio_source,'gsap.min.js':'node_modules/gsap/dist/gsap.min.js','puppet.js':'video/articulated-puppet.js','NotoSansTC.ttf':'assets/fonts/NotoSansTC.ttf'};
function html(mode,staticOnly=false){
  const id=`ade10-${staticOnly?'static':'mode'+mode}`,label=cfg.modes[String(mode)].label;
  const [hx,hy,hw,hh]=base.head_rect,[tx,ty,tw,th]=base.torso_rect,p=base.pelvis;
  return `<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>
  @font-face{font-family:NotoTC;src:url('assets/NotoSansTC.ttf')}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden}#root{width:100%;height:100%;position:relative;font-family:NotoTC,sans-serif;background:${staticOnly?'transparent':'#f2f5f7'};color:#233f4c}.title{position:absolute;left:64px;top:20px;font-size:34px;font-weight:700}.label{position:absolute;top:75px;font-size:28px;font-weight:700}.old-label{left:110px}.new-label{left:1110px}.divider{position:absolute;left:950px;top:105px;height:870px;width:2px;background:#ccdce3}.footer{position:absolute;left:64px;bottom:20px;font-size:28px}.old-window{position:absolute;left:65px;top:115px;width:738px;height:832.5px;overflow:hidden}.old-window video{position:absolute;left:-846px;top:-67.5px;width:1728px;height:972px;max-width:none}#actor{position:absolute;left:${staticOnly?0:1100}px;top:${staticOnly?0:102}px;width:1024px;height:1536px;transform:${staticOnly?'none':'scale(.58)'};transform-origin:0 0}#body-shared{position:absolute;inset:0}#limbs{position:absolute;left:-180px;top:-80px;width:1400px;height:1680px}#torso{position:absolute;inset:0;width:1024px;height:1536px}#head-motion{position:absolute;left:${hx}px;top:${hy}px;width:${hw}px;height:${hh}px;transform-origin:${cfg.head_pin[0]-hx}px ${cfg.head_pin[1]-hy}px;clip-path:inset(0 0 48px 0);mask-image:linear-gradient(to bottom,#000 0px,#000 500px,transparent 517px,transparent 565px)}#head-media{display:block;width:100%;height:100%;object-fit:contain}#atlas{display:none}
  .old-window{left:45px;top:102px;width:792.6667px;height:894.1667px}.old-window video{left:-908.6667px;top:-72.5px;width:1856px;height:1044px}.label{top:65px;z-index:3}.old-label{left:64px}.new-label{top:25px}
  </style></head><body><div id="root" data-composition-id="${id}" data-width="${staticOnly?1024:1920}" data-height="${staticOnly?1536:1080}" data-duration="4.4">
  ${staticOnly?'':`<div class="title">阿德・關節與接合整合審核</div><div class="label old-label">已接受：第九輪</div><div class="label new-label">第十輪：${label}</div><div class="divider"></div><div class="old-window"><video id="old" class="clip" src="assets/baseline.mp4" muted playsinline data-start="0" data-duration="4.4" data-track-index="3" data-layout-allow-overflow="intentional crop of accepted actor from original comparison"></video></div><div class="footer">同一配音與眨眼　｜　彎肘・屈膝・肩頸與頭身微調</div>`}
  <div id="actor" data-layout-allow-overflow="transparent puppet work area; actual silhouette and joints checked per frame"><div id="body-shared"><canvas id="limbs" width="1400" height="1680" data-layout-allow-overflow="transparent padding for bent limbs"></canvas><svg id="torso" viewBox="0 0 1024 1536" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="pelvis-feather" x1="0" y1="765" x2="0" y2="825" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient><mask id="pelvis-mask" maskUnits="userSpaceOnUse" x="150" y="600" width="360" height="291"><rect x="150" y="600" width="360" height="291" fill="url(#pelvis-feather)"/></mask><clipPath id="pelvis-clip"><path d="${contours.pelvis}"/></clipPath></defs><g transform="translate(${p.pivot.join(' ')}) scale(${p.scale}) translate(${-p.source_pivot[0]} ${-p.source_pivot[1]})"><image href="assets/atlas.png" width="1536" height="1024" mask="url(#pelvis-mask)" clip-path="url(#pelvis-clip)"/></g><image href="assets/torso.png" x="${tx}" y="${ty}" width="${tw}" height="${th}"/></svg><div id="head-motion">${staticOnly?'<img id="head-media" src="assets/head.png" alt="阿德原頭像">':'<video id="head-media" class="clip" src="assets/head.webm" muted playsinline data-start="0" data-duration="4.4" data-track-index="1"></video>'}</div></div></div><img id="atlas" src="assets/atlas.png" alt="私人服裝材質圖集">${staticOnly?'':'<audio id="voice" class="clip" src="assets/voice.wav" data-start="0" data-duration="4.4" data-track-index="2" data-volume="1"></audio>'}
  </div><script src="assets/gsap.min.js"></script><script src="assets/puppet.js"></script><script>
  const base=${JSON.stringify(base)},config=${JSON.stringify(cfg)},contours=${JSON.stringify(contours)},mode=${mode},staticOnly=${staticOnly};
  async function build(){
    const atlas=document.querySelector('#atlas');await atlas.decode();await document.fonts.ready;
    const puppet=new ContinuousPuppet(document.querySelector('#limbs'),atlas,base,config,contours);
    const state={arm_left_upper:0,arm_left_bend:0,arm_right_upper:0,arm_right_bend:0,leg_left_upper:0,leg_left_bend:0,leg_right_upper:0,leg_right_bend:0,head:0};
    const head=document.querySelector('#head-motion'),shared=document.querySelector('#body-shared');
    function draw(){const r=puppet.draw(state);shared.style.transform='translateY('+r.dip+'px)';head.style.transform='rotate('+state.head+'deg) scale('+config.head_scale+')';window.__rigDiagnostics={...r,state:Object.fromEntries(Object.entries(state).filter(([k,v])=>typeof v==='number')),mode,head_pin:config.head_pin};}
    const tl=gsap.timeline({paused:true,onUpdate:draw}),p=config.modes[String(mode)],t=config.timing;
    function gesture(key,angle,start){tl.to(state,{[key]:angle,duration:t.rise,ease:'sine.inOut'},start);tl.to(state,{[key]:0,duration:t.lower,ease:'sine.inOut'},start+t.rise+t.hold);}
    if(!staticOnly){
      gesture('arm_right_upper',p.right_upper_deg,t.start);gesture('arm_right_bend',p.right_elbow_deg,t.start+t.elbow_delay);
      gesture('arm_left_upper',p.left_upper_deg,t.start+t.other_delay);gesture('arm_left_bend',p.left_elbow_deg,t.start+t.other_delay+t.elbow_delay);
      if(mode>1){gesture('leg_left_upper',p.left_hip_deg,t.start+t.knee_delay);gesture('leg_left_bend',p.left_knee_deg,t.start+t.knee_delay);gesture('leg_right_upper',p.right_hip_deg,t.start+t.knee_delay+.12);gesture('leg_right_bend',p.right_knee_deg,t.start+t.knee_delay+.12);gesture('head',p.head_deg,t.start+.15);}
    }
    draw();window.__puppetReady=true;window.__puppetDraw=draw;window.__timelines['${id}']=tl;
  }build();
  </script></body></html>`;
}
for(const mode of [0,1,2,3]){
  const dest=path.join(root,'samples/round10',mode?`mode${mode}`:'static');fs.mkdirSync(path.join(dest,'assets'),{recursive:true});
  for(const [n,s]of Object.entries(files))fs.copyFileSync(path.join(root,s),path.join(dest,'assets',n));
  if(mode)fs.copyFileSync(path.join(root,`outputs/round09/mode${mode}.mp4`),path.join(dest,'assets/baseline.mp4'));
  fs.writeFileSync(path.join(dest,'index.html'),html(mode||2,mode===0),'utf8');
}
fs.mkdirSync(out,{recursive:true});
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex');
fs.writeFileSync(path.join(out,'build-manifest.json'),JSON.stringify({round:'round10',version:{hyperframes:require('../node_modules/hyperframes/package.json').version,gsap:require('../node_modules/gsap/package.json').version},config:cfg,sourceRecords:Object.fromEntries(Object.entries(files).map(([n,p])=>[n,{path:p,sha256:sha(p)}])),baseline_videos:[1,2,3].map(n=>({path:`outputs/round09/mode${n}.mp4`,sha256:sha(`outputs/round09/mode${n}.mp4`)})),user_accepted:false},null,2));
console.log('Built round10 continuous-mesh three-mode comparison and static pose.');
