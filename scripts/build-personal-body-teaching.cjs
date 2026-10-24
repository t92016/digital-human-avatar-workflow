const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {buildHtml}=require('../video/composition.cjs'),{personalCharacter}=require('../video/personal-body-character.cjs');
const root=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const cfg=read('config/round11.json'),base=read(cfg.body_config),art=read(cfg.articulation_config),teaching=read(cfg.teaching_config);
const geometryOnly=process.argv.includes('--geometry-preview');
const contours=read('work/round09/sprite-contours.json').paths;
const speech=read('outputs/round05/audio/speech.json'),cues=read('outputs/round05/audio/mouths.json'),captions=read('outputs/round05/audio/captions.json');
if(speech.script!==teaching.script||Math.abs(speech.duration+.3+.796-13)>.0001)throw Error('Original teaching timeline mismatch');
if(!geometryOnly&&!fs.existsSync(path.join(root,cfg.head_alpha)))throw Error('Full-dialogue head is not ready; do not replace it by looping a short clip.');
const out=path.join(root,'outputs/round11');fs.mkdirSync(out,{recursive:true});
const sources={'atlas.png':'outputs/round09/character/body_parts_atlas_v1.png','torso.png':'outputs/round09/character/torso_armless_v2.png','head.png':base.head_still,'voice.wav':'outputs/round05/audio/voice.wav','gsap.min.js':'node_modules/gsap/dist/gsap.min.js','puppet.js':'video/articulated-puppet.js','NotoSansTC.ttf':'assets/fonts/NotoSansTC.ttf','OFL.txt':'assets/fonts/OFL.txt'};
if(!geometryOnly)sources['head.webm']=cfg.head_alpha;
for(const mode of [1,2,3]){
 const dest=path.join(root,'samples/round11',`${geometryOnly?'geometry-':''}mode${mode}`);fs.mkdirSync(path.join(dest,'assets'),{recursive:true});
 for(const [name,src] of Object.entries(sources))fs.copyFileSync(path.join(root,src),path.join(dest,'assets',name));
 const customCharacter=personalCharacter({cfg,base,art,contours,mode,geometryOnly});
 fs.writeFileSync(path.join(dest,'index.html'),buildHtml({config:teaching,mode,speech,cues,captions,customCharacter}),'utf8');
 fs.writeFileSync(path.join(dest,'hyperframes.json'),JSON.stringify({paths:{assets:'assets'},media:{autoProxy:false}}));
}
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex');
const record={round:'round11',geometryOnly,config:cfg,sourceRecords:Object.fromEntries(Object.entries(sources).map(([n,p])=>[n,{path:p,sha256:sha(p)}])),original_teaching_sources:['config/round05.json','outputs/round05/audio/speech.json','outputs/round05/audio/captions.json','video/composition.cjs','video/personal-body-character.cjs'].map(p=>({path:p,sha256:sha(p)})),user_accepted:false};
fs.writeFileSync(path.join(out,geometryOnly?'geometry-build-manifest.json':'build-manifest.json'),JSON.stringify(record,null,2));
console.log('Built round11 '+(geometryOnly?'internal static-head geometry previews':'full teaching compositions')+'; original speech, panels and captions reused.');
