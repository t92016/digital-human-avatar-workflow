/* Every final export timestamp, same attached puppet, transparent browser QA. */
const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
(async()=>{
 const cfg=JSON.parse(fs.readFileSync(path.join(root,'config/round11.json'),'utf8'));
 const executablePath=JSON.parse(fs.readFileSync(path.join(root,'work/browser.json'),'utf8')).executablePath;
 const browser=await chromium.launch({executablePath,headless:true,args:['--allow-file-access-from-files','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const records=[];
 try{for(const mode of [1,2,3]){
  const page=await browser.newPage({viewport:{width:1920,height:1080}});await page.addInitScript(()=>{window.__timelines={};});
  await page.goto(pathToFileURL(path.join(root,`samples/round11/mode${mode}/index.html`)).href);await page.waitForFunction(()=>window.__puppetReady);
  await page.addStyleTag({content:'html,body,#root{background:transparent!important}#root> :not(#character-region){visibility:hidden!important}'});
  await page.waitForFunction(()=>document.querySelector('#head-media').readyState>=2);
  await page.evaluate(async()=>{const v=document.querySelector('#head-media');await v.play();await new Promise(r=>v.requestVideoFrameCallback(r));v.pause();});
  const dir=path.join(root,`work/round11/alpha/mode${mode}`);fs.mkdirSync(dir,{recursive:true});
  for(let i=0;i<312;i++){
   const time=i/24,diag=await page.evaluate(async({time,mode})=>{
    window.__timelines['mode'+mode].seek(time,false);window.__puppetDraw();const v=document.querySelector('#head-media');
    if(Math.abs(v.currentTime-time)>.0001)await new Promise(r=>{v.addEventListener('seeked',r,{once:true});v.currentTime=time;});
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return window.__rigDiagnostics;
   },{time,mode});
   const file=path.join(dir,`f${String(i).padStart(3,'0')}.png`),[x,y,width,height]=cfg.character_region;
   await page.screenshot({path:file,omitBackground:true,clip:{x,y,width,height}});records.push({mode,frame:i,time,path:path.relative(root,file),diagnostics:diag});
  }
  if(mode===1){
   await page.addStyleTag({content:'html,body{background:#f9f7ef!important}#root{background:linear-gradient(130deg,#faf8ef,#eff5e9)!important}#character-region{visibility:hidden!important}'});
   await page.screenshot({path:path.join(root,'work/round11/character-background.png'),clip:{x:62,y:493,width:535,height:550}});
  }
  console.log('Mode '+mode+':312 transparent export-time frames.');await page.close();
 }}finally{await browser.close();}
 fs.writeFileSync(path.join(root,'work/round11/alpha-frame-records.json'),JSON.stringify(records,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
