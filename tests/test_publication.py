import importlib.util,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('public_scan',ROOT/'scripts/secret-scan.py');scan=importlib.util.module_from_spec(spec);spec.loader.exec_module(scan)
class PublicBoundaryTests(unittest.TestCase):
 def test_secret_report_does_not_echo_value(self):
  token='gh'+'p_'+'A'*36
  result=scan.inspect_bytes('config/example.json',token.encode(),{})
  self.assertEqual(result[0]['category'],'github-token');self.assertNotIn(token,str(result))
 def test_model_and_private_paths_are_rejected(self):
  self.assertIn('model-or-installation-binary',[r['category'] for r in scan.inspect_bytes('weights.safetensors',b'123',{})])
  self.assertIn('private-or-local-directory',[r['category'] for r in scan.inspect_bytes('private_inputs/source.md',b'hello',{})])
 def test_changed_or_unlisted_media_is_rejected(self):
  self.assertTrue(scan.inspect_bytes('examples/other/photo.png',b'photo',{}))
  self.assertTrue(scan.inspect_bytes('examples/ade-personal-body/media/poster.png',b'changed',{'examples/ade-personal-body/media/poster.png':'0'*64}))
 def test_scans_actual_index_not_clean_working_copy(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);subprocess.run(['git','init','-q',str(root)],check=True)
   p=root/'sample.md';p.write_text('gh'+'p_'+'B'*36,encoding='utf-8');subprocess.run(['git','-C',tmp,'add','sample.md'],check=True)
   p.write_text('clean working copy',encoding='utf-8')
   self.assertFalse(scan.scan(root,staged=True)['ok']);self.assertTrue(scan.scan(root,staged=False)['ok'])
if __name__=='__main__':unittest.main()
