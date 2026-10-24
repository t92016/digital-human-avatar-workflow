const test = require('node:test');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const http = require('node:http');

test('all modes: real mouth cues, deterministic seeking, fixed root, mode separation', {timeout:90000}, async () => {
  const root = path.resolve(__dirname,'..');
  const round = process.env.AVATAR_TEST_ROUND || 'round01';
  assert.match(round,/^round\d{2}$/);
  const python = path.join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
  let browserPath;
  if(fs.existsSync(path.join(root,'work/browser.json'))) browserPath=JSON.parse(fs.readFileSync(path.join(root,'work/browser.json'),'utf8')).executablePath;
  if(!browserPath) browserPath=spawnSync(python,['-c','from avatar_workflow.hardware import find_browser;print(find_browser() or "")'],{encoding:'utf8',windowsHide:true}).stdout.trim();
  const browser = await chromium.launch({executablePath:browserPath,headless:true,args:['--disable-gpu']});
  const server=http.createServer((req,res)=>{
    const local=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
    if(!local.startsWith(root+path.sep)){res.writeHead(403).end();return;}
    const type={'.html':'text/html; charset=utf-8','.js':'application/javascript','.ttf':'font/ttf','.png':'image/png','.wav':'audio/wav'}[path.extname(local)]||'application/octet-stream';
    res.setHeader('Content-Type',type);fs.createReadStream(local).on('error',()=>res.writeHead(404).end()).pipe(res);
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin=`http://127.0.0.1:${server.address().port}`;
  const summaries=[];
  try {
    for(const mode of [1,2,3]){
      const page=await browser.newPage({viewport:{width:1920,height:1080}});
      console.log('驗證輪次／模式',round,mode);
      await page.goto(`${origin}/samples/${round}/mode${mode}/index.html`,{waitUntil:'domcontentloaded',timeout:20000});
      await page.evaluate(()=>document.fonts.ready.then(()=>true));
      console.log('字型載入完成',mode);
      const report=await page.evaluate(()=>{
        const data=window.__avatarTest,tl=window.__timelines['mode'+data.mode];
        const state=t=>{tl.seek(t,false);return Object.fromEntries(['head','arm-left','arm-right','leg-left','leg-right','rig-scale'].map(id=>[id,getComputedStyle(document.getElementById(id)).transform]));};
        const proofTime=data.motionProfile ? data.beats[0]+data.motionProfile.rise_sec+.2 : .7;
        const base=state(0),pose=state(proofTime),later=state(3.2);state(.7);const sameLater=JSON.stringify(later)===JSON.stringify(state(3.2));
        const handPoint=t=>{tl.seek(t,false);const hand=data.rig.version==='overlapping-shoulder-v1'?[data.rig.shoulders.right[0]+(1370-1215)*.52,data.rig.shoulders.right[1]+(785-295)*.52]:[815,1000];const p=new DOMPoint(...hand).matrixTransform(document.getElementById('arm-right').getScreenCTM());return {x:p.x,y:p.y};};
        const restingHand=handPoint(0);
        const raisedHands=data.motionProfile ? data.beats.map(b=>handPoint(b+data.motionProfile.rise_sec+.2)) : [];
        const handAfter=handPoint(data.duration-.05);
        const errors=[];
        for(const cue of data.mouthCues){
          tl.seek((cue.start+cue.end)/2,false);
          const visible=[...document.querySelectorAll('.mouth-shape')].filter(e=>Number(getComputedStyle(e).opacity)>.5).map(e=>e.id);
          if(visible.length!==1||visible[0]!=='mouth-'+cue.value)errors.push({cue,visible});
        }
        const captionErrors=[];
        for(let i=0;i<data.captions.length;i++){
          const c=data.captions[i];tl.seek((c.start+c.end)/2,false);
          const visible=[...document.querySelectorAll('.caption span')].filter(e=>Number(getComputedStyle(e).opacity)>.5);
          if(visible.length!==1||visible[0].textContent!==c.text)captionErrors.push(i);
        }
        const sceneErrors=[];
        for(let i=1;i<3;i++){
          const expected=data.captions.find(c=>c.text.startsWith(data.sceneCaptionPrefixes[i])).start;
          if(data.motionProfile&&Math.abs(data.sceneStarts[i]-expected)>.001)sceneErrors.push(i);
        }
        return {mode:data.mode,base,pose,sameLater,mouthCueCount:data.mouthCues.length,errors,captionErrors,
          proofTime,restingHand,raisedHands,handAfter,sceneErrors,enhanced:!!data.motionProfile};
      });
      assert.equal(report.sameLater,true);
      assert.deepEqual(report.errors,[]);
      assert.deepEqual(report.captionErrors,[]);
      assert.deepEqual(report.sceneErrors,[]);
      if(report.enhanced){
        assert.ok(report.raisedHands.length>=3);
        for(const hand of report.raisedHands){
          assert.ok(hand.y < report.restingHand.y-70,'角色左手必須明顯高於原位置');
          assert.ok(hand.x>62 && hand.x<597 && hand.y>493 && hand.y<1043,'左手留在活動範圍');
        }
        assert.ok(Math.abs(report.handAfter.y-report.restingHand.y)<1,'最後放回原位');
      }
      assert.equal(report.base['rig-scale'],report.pose['rig-scale']);
      assert.notEqual(report.base['arm-left'],report.pose['arm-left']);
      for(const part of ['head','leg-left','leg-right']){
        if(mode===1)assert.equal(report.base[part],report.pose[part]);
      }
      if(mode>1){assert.notEqual(report.base.head,report.pose.head);assert.notEqual(report.base['leg-right'],report.pose['leg-right']);}
      summaries.push(report);
      // GSAP timelines are thenable; returning one would wait forever while paused.
      await page.evaluate(t=>{window.__timelines['mode'+window.__avatarTest.mode].seek(t,false);},report.proofTime);
      await page.screenshot({path:path.join(root,`outputs/${round}/mode${mode}_motion_proof.png`)});
      await page.close();
    }
    assert.notEqual(summaries[1].pose.head,summaries[2].pose.head);
    fs.writeFileSync(path.join(root,`work/${round}/animation-verification.json`),JSON.stringify(summaries,null,2));
  } finally {await browser.close();server.close();}
});
