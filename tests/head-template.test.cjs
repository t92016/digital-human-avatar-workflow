const test=require('node:test');const assert=require('node:assert/strict');
const {rigSvg}=require('../video/composition.cjs');
test('independent portrait slot preserves body textures and uses calibrated mouth',()=>{
  const rig={head_layer:{file:'new-head.png',target_rect:[190,45,709,615]},mouth_center:[570,540],mouth_scale:.9};
  const result=rigSvg(false,rig);
  assert.match(result,/href="assets\/new-head.png" x="190" y="45" width="709" height="615"/);
  assert.match(result,/id="torso"/);
  assert.match(result,/href="assets\/boy.png"/);
  assert.match(result,/translate\(570 540\) scale\(0.9\)/);
  for(const file of ['../private.png','sub/head.png','sub\\head.png']){
    assert.throws(()=>rigSvg(false,{...rig,head_layer:{...rig.head_layer,file}}));
  }
});
