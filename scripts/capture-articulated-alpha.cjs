/* Actual browser alpha silhouettes at every export frame; original assets untouched. */
const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
(async()=>{
 const executablePath=JSON.parse(fs.readFileSync(path.join(root,'work/browser.json'),'utf8')).executablePath;
 const browser=await chromium.launch({executablePath,headless:true,args:['--allow-file-access-from-files','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const modes=process.argv.slice(2).length?process.argv.slice(2).map(Number):[1,2,3];if(modes.some(m=>![1,2,3].includes(m)))throw Error('Invalid mode');
 const recordFile=path.join(root,'work/round10/alpha-frame-records.json');
 const all=fs.existsSync(recordFile)?JSON.parse(fs.readFileSync(recordFile,'utf8')).filter(r=>!modes.includes(r.mode)):[];
 try{
  for(const mode of modes){
   const dest=path.join(root,`work/round10/alpha-v2/mode${mode}`);fs.mkdirSync(dest,{recursive:true});
   const page=await browser.newPage({viewport:{width:1920,height:1080}});
   await page.addInitScript(()=>{window.__timelines={};});
   await page.goto(pathToFileURL(path.join(root,`samples/round10/mode${mode}/index.html`)).href);
   await page.waitForFunction(()=>window.__puppetReady);
   await page.addStyleTag({content:'html,body,#root{background:transparent!important}#root> :not(#actor){visibility:hidden!important}'});
   await page.waitForFunction(()=>document.querySelector('#head-media').readyState>=2);
   // Explicitly present a muted video frame before auditing frame zero.
   await page.evaluate(async()=>{
    const v=document.querySelector('#head-media');
    await Promise.race([v.play(),new Promise((_,reject)=>setTimeout(()=>reject(Error('Video warm-up timed out')),5000))]);
    await Promise.race([new Promise(r=>v.requestVideoFrameCallback(r)),new Promise((_,reject)=>setTimeout(()=>reject(Error('No presented video frame')),5000))]);
    v.pause();
    if(v.currentTime!==0)await new Promise(r=>{const done=()=>r();v.addEventListener('seeked',done,{once:true});v.currentTime=0;setTimeout(done,1500);});
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
   });
   console.log('Video ready for mode '+mode);
   for(let i=0;i<110;i++){
    const d=await page.evaluate(async ({time,mode})=>{
     window.__timelines['ade10-mode'+mode].seek(time,false);window.__puppetDraw();
     const v=document.querySelector('#head-media');
     if(v.readyState<2)await new Promise(r=>v.addEventListener('loadeddata',r,{once:true}));
     if(Math.abs(v.currentTime-time)>.0001){await new Promise(r=>{v.addEventListener('seeked',r,{once:true});v.currentTime=time;});}
     await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
     return window.__rigDiagnostics;
    },{time:i/25,mode});
    const file=path.join(dest,`f${String(i).padStart(3,'0')}.png`);
    const crop={x:990,y:30,width:860,height:965};
    await page.screenshot({path:file,omitBackground:true,clip:crop});
    all.push({mode,frame:i,time:i/25,path:path.relative(root,file),crop,diagnostics:d});
   }
   console.log(`Mode ${mode}: 110 transparent actual browser frames.`);await page.close();
  }
 }finally{await browser.close();}
 all.sort((a,b)=>a.mode-b.mode||a.frame-b.frame);fs.writeFileSync(recordFile,JSON.stringify(all,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
