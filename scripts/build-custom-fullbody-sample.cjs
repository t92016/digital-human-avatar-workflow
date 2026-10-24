/* Round09: own-photo body, accepted head video, deterministic overlapping sprites. */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
const cfg=JSON.parse(fs.readFileSync(path.join(root,'config/round09.json'),'utf8'));
const out=path.join(root,'outputs/round09');
const reviewManifest=path.join(out,'manifest.json');
if(fs.existsSync(reviewManifest)&&JSON.parse(fs.readFileSync(reviewManifest,'utf8')).user_accepted===true)throw Error('Round09 is accepted; use a new round instead of overwriting it.');
const contourRun=spawnSync(path.join(root,'work/sadtalker/venv/Scripts/python.exe'),['scripts/extract-sprite-silhouettes.py'],{cwd:root,encoding:'utf8',windowsHide:true});
if(contourRun.status!==0)throw Error(contourRun.stderr);
const silhouettes=JSON.parse(fs.readFileSync(path.join(root,'work/round09/sprite-contours.json'),'utf8')).paths;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const files={
  'atlas.png':'outputs/round09/character/body_parts_atlas_v1.png',
  'torso.png':'outputs/round09/character/torso_armless_v2.png',
  'head.png':cfg.head_still,
  'head.webm':cfg.head_alpha,
  'still.png':'outputs/round09/character/fullbody_cutout_v2.png',
  'voice.wav':cfg.audio_source,
  'gsap.min.js':'node_modules/gsap/dist/gsap.min.js',
  'NotoSansTC.ttf':'assets/fonts/NotoSansTC.ttf'
};

function sprite(name,part,asset='assets/atlas.png'){
  const [x0,y0,x1,y1]=part.crop;
  const feather=name==='pelvis'?'<defs><linearGradient id="pelvis-gradient" x1="0" y1="765" x2="0" y2="825" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient><mask id="pelvis-mask" maskUnits="userSpaceOnUse" x="150" y="600" width="360" height="291"><rect x="150" y="600" width="360" height="291" fill="url(#pelvis-gradient)"/></mask></defs>':'';
  const key=name.replaceAll('-','_');
  return `<g id="${name}"><g transform="translate(${part.pivot.join(' ')}) scale(${part.scale}) translate(${-part.source_pivot[0]} ${-part.source_pivot[1]})">${feather}<clipPath id="${name}-crop"><path d="${silhouettes[key]}"/></clipPath><g clip-path="url(#${name}-crop)" ${name==='pelvis'?'mask="url(#pelvis-mask)"':''}><image href="${asset}" width="1536" height="1024"/></g></g></g>`;
}
function body(){
  return `<svg id="body" width="1024" height="1536" viewBox="0 0 1024 1536" xmlns="http://www.w3.org/2000/svg">${sprite('leg-left',cfg.leg_left)}${sprite('leg-right',cfg.leg_right)}${sprite('arm-left',cfg.arm_left)}${sprite('arm-right',cfg.arm_right)}${sprite('pelvis',cfg.pelvis)}<image id="torso" href="assets/torso.png" x="${cfg.torso_rect[0]}" y="${cfg.torso_rect[1]}" width="${cfg.torso_rect[2]}" height="${cfg.torso_rect[3]}"/></svg>`;
}
function html(mode,staticOnly=false){
  const id=staticOnly?'ade09-static':`ade09-mode${mode}`;
  const pose=cfg.motion_profile.modes[String(mode)];
  const [hx,hy,hw,hh]=cfg.head_rect;
  return `<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>
  @font-face{font-family:NotoTC;src:url('assets/NotoSansTC.ttf')}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden}#root{position:relative;width:100%;height:100%;background:${staticOnly?'transparent':'#f2f5f7'};font-family:NotoTC,sans-serif;color:#233f4c}.title{position:absolute;left:90px;top:34px;margin:0;font-size:35px;font-weight:700}.sub{position:absolute;left:90px;top:88px;font-size:22px;color:#42616c}.divider{position:absolute;left:910px;top:80px;width:2px;height:900px;background:#d4e0e5}.static{position:absolute;left:160px;top:142px;width:570px;height:855px;object-fit:contain}.left-label,.right-label{position:absolute;top:134px;font-size:25px;font-weight:700}.left-label{left:175px}.right-label{left:1110px}.footer{position:absolute;left:90px;bottom:23px;font-size:21px;color:#42616c}#actor{position:absolute;left:${staticOnly?0:985}px;top:${staticOnly?0:43}px;width:1024px;height:1536px;transform:${staticOnly?'none':'scale(.64)'};transform-origin:0 0}#body{position:absolute;inset:0;overflow:visible}#head-motion{position:absolute;left:${hx}px;top:${hy}px;width:${hw}px;height:${hh}px;transform-origin:${cfg.head_pivot[0]-hx}px ${cfg.head_pivot[1]-hy}px}#head-media{display:block;width:100%;height:100%;object-fit:contain}
  .static{top:183px;width:533px;height:800px}.left-label{top:140px}.right-label{top:30px}.sub,.left-label,.right-label,.footer{font-size:28px}#actor{top:${staticOnly?0:75}px;transform:${staticOnly?'none':'scale(.60)'}}#head-motion{clip-path:inset(0 0 48px 0);mask-image:linear-gradient(to bottom,#000 0px,#000 500px,transparent 517px,transparent 565px)}
  </style></head><body><div id="root" data-composition-id="${id}" data-width="${staticOnly?1024:1920}" data-height="${staticOnly?1536:1080}" data-duration="4.4">
  ${staticOnly?'':`<h1 class="title">阿德・專屬全身短測</h1><div class="sub">黑色 POLO 衫・深色長褲・原地動作</div><div class="divider"></div><img class="static" src="assets/still.png" alt="全身照轉Q版靜態候選"><div class="left-label">全身靜態候選</div><div class="right-label">${pose.label}</div><div class="footer">沿用家豪配音與已接受的對嘴、眨眼　｜　新身體與接合待檢視</div>`}
  <div id="actor" data-layout-allow-overflow="scaled full-size transparent puppet work area; visible silhouette verified separately">${body()}<div id="head-motion">${staticOnly?'<img id="head-media" src="assets/head.png" alt="已接受阿德頭像">':'<video id="head-media" class="clip" src="assets/head.webm" muted playsinline data-start="0" data-duration="4.4" data-track-index="1"></video>'}</div></div>
  ${staticOnly?'':'<audio id="voice" class="clip" src="assets/voice.wav" data-start="0" data-duration="4.4" data-track-index="2" data-volume="1"></audio>'}
  </div><script src="assets/gsap.min.js"></script><script>
  const tl=gsap.timeline({paused:true});
  const config=${JSON.stringify(cfg)};const mode=${mode};const staticOnly=${staticOnly};
  const pose=config.motion_profile.modes[String(mode)];
  gsap.set('#arm-left',{svgOrigin:config.arm_left.pivot.join(' ')});gsap.set('#arm-right',{svgOrigin:config.arm_right.pivot.join(' ')});
  gsap.set('#leg-left',{svgOrigin:config.leg_left.pivot.join(' ')});gsap.set('#leg-right',{svgOrigin:config.leg_right.pivot.join(' ')});
  function gesture(target,start,angle,lift=0){tl.to(target,{rotation:angle,y:-lift,duration:1.05,ease:'sine.inOut'},start);tl.to(target,{rotation:0,y:0,duration:1.05,ease:'sine.inOut'},start+1.75)}
  if(!staticOnly){gesture('#arm-right',.35,pose.left_arm_deg);gesture('#arm-left',.60,pose.other_arm_deg);if(mode>1){gesture('#head-motion',.45,pose.head_deg);gesture('#leg-left',.50,pose.leg_deg,pose.leg_lift);gesture('#leg-right',.75,-pose.leg_deg*.5,pose.leg_lift*.35)}}
  window.__timelines['${id}']=tl;
  </script></body></html>`;
}

for(const mode of [0,1,2,3]){
  const staticOnly=mode===0;const dest=path.join(root,'samples/round09',staticOnly?'static':`mode${mode}`);
  fs.mkdirSync(path.join(dest,'assets'),{recursive:true});
  for(const [name,src]of Object.entries(files))fs.copyFileSync(path.join(root,src),path.join(dest,'assets',name));
  fs.writeFileSync(path.join(dest,'index.html'),html(mode||1,staticOnly),'utf8');
}
const parts=path.join(out,'parts');fs.mkdirSync(parts,{recursive:true});
const atlasData=fs.readFileSync(path.join(root,files['atlas.png'])).toString('base64');
for(const name of ['arm_left','arm_right','pelvis','leg_left','leg_right']){
  const [x0,y0,x1,y1]=cfg[name].crop;
  fs.writeFileSync(path.join(parts,`${name}.svg`),`<svg xmlns="http://www.w3.org/2000/svg" width="${x1-x0}" height="${y1-y0}" viewBox="${x0} ${y0} ${x1-x0} ${y1-y0}"><clipPath id="silhouette"><path d="${silhouettes[name]}"/></clipPath><image href="data:image/png;base64,${atlasData}" width="1536" height="1024" clip-path="url(#silhouette)"/></svg>`);
}
fs.copyFileSync(path.join(root,files['torso.png']),path.join(parts,'torso_armless.png'));
const sourceRecords=Object.fromEntries(Object.entries(files).filter(([n])=>!n.endsWith('.js')&&!n.endsWith('.ttf')).map(([name,file])=>[name,{path:file,sha256:sha(fs.readFileSync(path.join(root,file)))}]));
fs.writeFileSync(path.join(out,'build-manifest.json'),JSON.stringify({round:'round09',head_route:2,sourceRecords,config_sha256:sha(fs.readFileSync(path.join(root,'config/round09.json'))),user_accepted:false},null,2));
console.log('Built static + three private round09 compositions and six separate body-part assets.');
