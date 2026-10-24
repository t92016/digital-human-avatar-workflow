/* Render transparent, isolated character frames for pixel connectivity analysis.
   This changes only browser presentation for QA; bitmap sources stay untouched. */
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {spawnSync} = require('node:child_process');
const root=path.resolve(__dirname,'..');
const round=process.argv[2] || 'round03';
if(!/^round\d{2}$/.test(round))throw Error('輪次必須為round加兩位數字');
(async()=>{
  const executablePath=JSON.parse(fs.readFileSync(path.join(root,'work/browser.json'),'utf8')).executablePath;
  const browser=await chromium.launch({executablePath,headless:true,args:['--disable-gpu','--allow-file-access-from-files']});
  const reports=[];
  try{
    for(const mode of [1,2,3]){
      const dir=path.join(root,`work/${round}/continuity/mode${mode}`);
      fs.mkdirSync(dir,{recursive:true});
      const page=await browser.newPage({viewport:{width:1920,height:1080}});
      await page.goto(pathToFileURL(path.join(root,`samples/${round}/mode${mode}/index.html`)).href);
      await page.evaluate(()=>document.fonts.ready.then(()=>true));
      await page.addStyleTag({content:'html,body,#root{background:transparent!important}#root> :not(#character-region){visibility:hidden!important}'});
      // Full first cycle at 0.1 s intervals, plus later peak poses.
      const timing=await page.evaluate(()=>({duration:window.__avatarTest.duration,beats:window.__avatarTest.beats,rise:window.__avatarTest.motionProfile.rise_sec}));
      const times=[...Array.from({length:33},(_,i)=>Number((i*.1).toFixed(2))),...timing.beats.slice(1).map(t=>t+timing.rise+.2),timing.duration-.05];
      for(let i=0;i<times.length;i++){
        const points=await page.evaluate(t=>{
          const d=window.__avatarTest;window.__timelines['mode'+d.mode].seek(t,false);
          const anchors={};
          for(const side of ['left','right']){
            const [x,y]=d.rig.shoulders[side];
            const p=new DOMPoint(x,y).matrixTransform(document.getElementById('arm-'+side).getScreenCTM());
            const fixed=new DOMPoint(x,y).matrixTransform((document.getElementById('body-proportion') || document.getElementById('puppet')).getScreenCTM());
            anchors[side]={moving:[p.x,p.y],fixed:[fixed.x,fixed.y],gap:Math.hypot(p.x-fixed.x,p.y-fixed.y)};
          }
          return anchors;
        },times[i]);
        for(const p of Object.values(points))if(p.gap>.01)throw Error('肩膀關節位置漂移');
        const file=path.join(dir,`frame-${String(i).padStart(3,'0')}.png`);
        await page.screenshot({path:file,omitBackground:true,clip:{x:62,y:493,width:535,height:550}});
        reports.push({mode,time:times[i],file:path.relative(root,file),anchors:points});
      }
      await page.close();
      console.log(`模式 ${mode} 已擷取 ${times.length} 個透明角色畫面`);
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(root,`work/${round}/continuity-frames.json`),JSON.stringify(reports,null,2));
  const result=spawnSync(path.join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python'),[path.join(root,'scripts/check-arm-continuity.py'),'--round',round],{stdio:'inherit',windowsHide:true});
  if(result.status)process.exitCode=result.status;
})().catch(e=>{console.error(e);process.exitCode=1;});
