/* Generates native SVG/GSAP compositions; never edits the character bitmap. */
const fs = require('node:fs');
const path = require('node:path');
const { buildHtml } = require('../video/composition.cjs');
const root = path.resolve(__dirname, '..');
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8').replace(/^\uFEFF/, ''));
const round = process.argv[2] || 'round01';
if (!/^round\d{2}$/.test(round)) throw Error('輪次必須為 round 加兩位數字');
const config = read(`config/${round}.json`);
if (config.rig?.head_layer?.status === 'closed-mouth-static-preview-only') {
  throw Error('本輪仍為帶閉嘴線條的靜態頭像預覽；先完成角色驗收與無嘴底圖校準，再製作對嘴，避免重疊嘴巴。');
}
const speech = read(`outputs/${round}/audio/speech.json`);
if (speech.script !== config.script) throw Error('配音與設定台詞不一致');
const cues = read(`outputs/${round}/audio/mouths.json`);
const captions = read(`outputs/${round}/audio/captions.json`);
if (speech.voice.ShortName !== config.voice) throw Error('聲線與輪次設定不一致');
if (Math.abs(cues.metadata.duration - speech.duration) > .08) throw Error('嘴型與音檔長度不一致');
for (const mode of config.motion_modes) {
  const dir = path.join(root, `samples/${round}`, `mode${mode}`);
  fs.mkdirSync(path.join(dir, 'assets'), { recursive: true });
  const copies = [
    [`outputs/${round}/character/boy_mouthless_v1.png`, 'boy.png'],
    [`outputs/${round}/audio/voice.wav`, 'voice.wav'],
    ['assets/fonts/NotoSansTC.ttf', 'NotoSansTC.ttf'],
    ['assets/fonts/OFL.txt', 'OFL.txt'],
    ['node_modules/gsap/dist/gsap.min.js', 'gsap.min.js']
  ];
  if (config.rig.atlas) copies.push([`outputs/${round}/character/${config.rig.atlas}`, config.rig.atlas]);
  if (config.rig.head_layer) {
    const file=config.rig.head_layer.file;
    if(path.basename(file)!==file || !/\.png$/i.test(file))throw Error('頭像需為 character 資料夾中的 PNG 檔名');
    copies.push([`outputs/${round}/character/${file}`,file]);
  }
  for (const [from, to] of copies) fs.copyFileSync(path.join(root, from), path.join(dir, 'assets', to));
  fs.writeFileSync(path.join(dir, 'index.html'), buildHtml({ config, mode, speech, cues, captions }), 'utf8');
  fs.writeFileSync(path.join(dir, 'hyperframes.json'), JSON.stringify({ paths: { assets: 'assets' }, media: { autoProxy: false } }, null, 2));
  fs.writeFileSync(path.join(dir, 'meta.json'), JSON.stringify({ name: `${config.character || '阿忠'}模式${mode}` }));
  fs.writeFileSync(path.join(dir, 'index.motion.json'), JSON.stringify({
    duration: speech.duration+(config.video_timing?.lead_in_sec || 0)+(config.video_timing?.tail_out_sec || 0),
    assertions: [{kind:'staysInFrame', selector:'#character-region'}, {kind:'appearsBy', selector:'#heading', bySec:.1}]
  }, null, 2));
}
console.log(`已建立 ${round} 三種原地動作比較；${config.voice_user_accepted?'聲音已接受，影片待檢視':'時間軸為尚待聲音驗收的測試版本'}。`);
