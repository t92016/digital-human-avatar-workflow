const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),final=process.argv.includes('--final');
(async()=>{
 const executablePath=JSON.parse(fs.readFileSync(path.join(root,'work/browser.json'),'utf8')).executablePath;
 const browser=await chromium.launch({executablePath,headless:true,args:['--allow-file-access-from-files','--enable-unsafe-swiftshader']});const reports=[];
 try{for(const mode of [1,2,3]){
  const page=await browser.newPage({viewport:{width:1920,height:1080}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.addInitScript(()=>{window.__timelines={};});await page.goto(pathToFileURL(path.join(root,`samples/round11/${final?'':'geometry-'}mode${mode}/index.html`)).href);await page.waitForFunction(()=>window.__puppetReady);
  const result=await page.evaluate(m=>{
   const tl=window.__timelines['mode'+m],cfg=window.__personalBody.cfg,rows=[],bind={arm_left:[370,660],arm_right:[654,660],leg_left:[442,1050],leg_right:[586,1050]};
   for(let i=0;i<=650;i++){
    const t=Math.min(12.999,i*.02);tl.seek(t,false);window.__puppetDraw();const d=JSON.parse(JSON.stringify(window.__rigDiagnostics));
    for(const [name,g]of Object.entries(d.geometry)){
     g.anchor_gap=Math.hypot(g.anchor[0]-bind[name][0],g.anchor[1]-bind[name][1]);if(g.anchor_gap>.00001||g.min_area_ratio<=.05)throw Error('Joint drift/fold '+m+'/'+t+'/'+name);
    }
    if(Math.abs(d.state.arm_right_bend)>Math.abs(cfg.modes[String(m)].right_elbow_deg)+.0001)throw Error('Elbow limit exceeded');
    rows.push({time:t,...d});
   }
   const proof=[];for(const t of [0,1.9,4.8,6,9.8,12.9]){tl.seek(t,false);window.__puppetDraw();const first=document.querySelector('#limbs').toDataURL();tl.seek(12.99,false);tl.seek(.01,false);tl.seek(t,false);window.__puppetDraw();if(first!==document.querySelector('#limbs').toDataURL())throw Error('Unstable repeated seek');proof.push(t);}
   return {rows,identical_after_backward_seek:proof,timing:window.__avatarTest,cycles:window.__personalBody.cycles};
  },mode);
  if(errors.length)throw Error(errors.join('\n'));reports.push({mode,...result});await page.close();console.log('Mode '+mode+': 651 poses, limited elbows, attached roots, no fold, repeatable seek.');
 }}finally{await browser.close();}
 fs.writeFileSync(path.join(root,`work/round11/${final?'final-':''}geometry-check.json`),JSON.stringify({scope:'1953 poses at20ms, positive triangles and fixed roots; no pixel certification',reports},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
