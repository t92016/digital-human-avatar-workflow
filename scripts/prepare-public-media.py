"""Export only the user's three explicitly authorized finished demonstrations."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst):
 if dst.exists() and sha(src)!=sha(dst):raise FileExistsError(dst)
 dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():shutil.copy2(src,dst)
 assert sha(src)==sha(dst)

def main():
 groups=[
  dict(id='azhong',title='阿忠｜校園安全',subtitle='阿忠校服身體・萌萌1202配音',folder='azhong-mmeng-1202',duration=13.125,topic='校園安全',body='阿忠校服身體',voice='萌萌1202（普通話童聲，未標台灣口音）',description='走廊慢慢走、上下樓梯靠右行，還有主動幫助同學。',note='這組保留已驗收的卡通人物、配音與早期2D嘴型。'),
  dict(id='ade-school',title='阿德｜反霸凌・阿忠身體',subtitle='阿德大頭＋阿忠校服身體・家豪1602配音',folder='ade-school-body',duration=13,topic='校園反霸凌',body='阿忠校服身體',voice='家豪1602（供應商標示Taiwan Male）',description='同一個阿德頭像，接上阿忠的校服身體，宣導尊重同學與勇敢求助。',note='保留原換頭版本與早期嘴型；本人身體版另呈現後續自然對嘴與眨眼。'),
  dict(id='ade-personal',title='阿德｜反霸凌・個人身體',subtitle='阿德本人服裝與身形・家豪1602配音',folder='ade-personal-body',duration=13,topic='校園反霸凌',body='本人黑色POLO衫、長褲與鞋',voice='家豪1602（供應商標示Taiwan Male）',description='保留本人造型，整合自然對嘴、局部眨眼，以及較平緩的彎肘與原地屈膝。',note='使用完整原音驅動SadTalker，整合穩定與局部眨眼。三模式已獲使用者接受。'),
 ]
 filenames=['mode1_hands.mp4','mode2_natural.mp4','mode3_lively.mp4']
 chinese=['01_只有手部.mp4','02_手腳與頭部_自然版.mp4','03_手腳與頭部_活潑版.mp4']
 legacy=json.loads((ROOT/'work/round11/legacy-source.json').read_text(encoding='utf-8'))
 for group in groups:
  dest=ROOT/'examples'/group['folder'];media=dest/'media'
  if group['id']=='azhong':
   existing=json.loads((dest/'manifest.json').read_text(encoding='utf-8'))
   for r in existing['files']:assert sha(dest/r['path'])==r['sha256']
  else:
   source=ROOT/('阿德推廣校園反霸凌（阿忠身體）' if group['id']=='ade-school' else '阿德推廣校園反霸凌（個人身體）')
   for i,name in enumerate(chinese):
    if group['id']=='ade-school':assert sha(source/name)==legacy['files'][i]['sha256']
    copy(source/name,media/filenames[i])
   if group['id']=='ade-personal':copy(source/'poster.png',media/'poster.png')
   elif not (media/'poster.png').exists():
    subprocess.run([str(ROOT/'tools/bin/ffmpeg.exe'),'-nostdin','-v','error','-n','-ss','1.9','-i',str(media/filenames[1]),'-frames:v','1',str(media/'poster.png')],check=True)
   rows=[{'path':f'media/{name}','bytes':(media/name).stat().st_size,'sha256':sha(media/name)} for name in [*filenames,'poster.png']]
   manifest={'schema_version':1,'id':group['id'],'publication_authorized_on':'2026-10-24','authorization':'User explicitly requested a public GitHub repo and Pages showcasing these three completed groups, each with three motion modes.','scope':'Finished MP4s and their preview image only; no original photographs, editable character layers, model weights, credentials or private environment.','files':rows}
   (dest/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  group['poster']=f"examples/{group['folder']}/media/poster.png"
  group['page']=f"showcases/{group['id']}/"
  group['resolution']=[1920,1080];group['fps']=24
  group['videos']=[{'mode':i+1,'path':f"examples/{group['folder']}/media/{name}",'bytes':(media/name).stat().st_size,'sha256':sha(media/name)} for i,name in enumerate(filenames)]
 data={'schema_version':1,'repository':'https://github.com/t92016/digital-human-avatar-workflow','pages':'https://t92016.github.io/digital-human-avatar-workflow/','authorized_on':'2026-10-24','groups':groups}
 (ROOT/'config/publication.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Prepared 3 public groups / 9 original MP4s; no video re-encoding.')
if __name__=='__main__':main()
