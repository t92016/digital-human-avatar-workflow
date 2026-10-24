/* Fine-time mesh, attachment, floor and seek-repeatability checks. */
const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
(async()=>{
 const executablePath=JSON.parse(fs.readFileSync(path.join(root,'work/browser.json'),'utf8')).executablePath;
 const browser=await chromium.launch({executablePath,headless:true,args:['--allow-file-access-from-files','--enable-unsafe-swiftshader']});
 const reports=[];
 try{
  for(const mode of [1,2,3]){
   const page=await browser.newPage({viewport:{width:1920,height:1080}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
   await page.addInitScript(()=>{window.__timelines={};});
   await page.goto(pathToFileURL(path.join(root,`samples/round10/mode${mode}/index.html`)).href);
   await page.waitForFunction(()=>window.__puppetReady);
   const result=await page.evaluate(async m=>{
    const tl=window.__timelines['ade10-mode'+m],rows=[],bind={arm_left:[370,660],arm_right:[654,660],leg_left:[442,1050],leg_right:[586,1050]};
    for(let i=0;i<=220;i++){
     const time=Math.min(4.399,i*.02);tl.seek(time,false);window.__puppetDraw();
     const d=structuredClone(window.__rigDiagnostics);
     for(const [name,g]of Object.entries(d.geometry)){
      g.anchor_gap=Math.hypot(g.anchor[0]-bind[name][0],g.anchor[1]-bind[name][1]);
      if(g.anchor_gap>.00001||g.min_area_ratio<=.05)throw Error('Attachment drift or mesh fold at '+m+'/'+time+'/'+name+': '+JSON.stringify(g));
     }
     rows.push({time,dip:d.dip,geometry:d.geometry,state:d.state});
    }
    const canvas=document.querySelector('#limbs'),proof=[];
    for(const time of [0,.8,1.5,1.88,2.6,3.4,4.36]){
     tl.seek(time,false);window.__puppetDraw();const first=canvas.toDataURL();
     tl.seek(4.39,false);tl.seek(.01,false);tl.seek(time,false);window.__puppetDraw();
     if(canvas.toDataURL()!==first)throw Error('Canvas changes after backward seek at '+time);
     proof.push({time,identical_after_backward_seek:true});
    }
    tl.seek(0,false);window.__puppetDraw();const first=canvas.toDataURL();tl.seek(4.36,false);window.__puppetDraw();
    if(canvas.toDataURL()!==first)throw Error('Final body pose does not return to rest.');
    return {rows,proof,final_pose_matches_rest:true};
   },mode);
   if(errors.length)throw Error(errors.join('\n'));
   reports.push({mode,...result,browser_errors:errors});await page.close();
   console.log('Mode '+mode+': 221 fine-time poses; four anchors fixed; no fold; 7 repeatable seeks.');
  }
 }finally{await browser.close();}
 const out=path.join(root,'work/round10/joint-geometry-check.json');fs.writeFileSync(out,JSON.stringify({scope:'663 poses at 20ms intervals, four shared continuous limb meshes; no pixel or anatomical certification',reports},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
