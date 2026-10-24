"""Account-free voice intake. This module never calls a synthesis endpoint."""
from __future__ import annotations
import html
import json
from pathlib import Path

GROUPS = {"boy":"男童", "girl":"女童", "man":"成人男聲", "woman":"成人女聲"}


def load_catalog() -> dict:
    path = Path(__file__).resolve().parents[1] / "config/ttsmaker-voices.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    ids = [v["id"] for v in catalog["voices"]]
    if len(ids) != len(set(ids)) or any(v["group"] not in GROUPS for v in catalog["voices"]):
        raise ValueError("聲線編號或分組有誤")
    return catalog


def menu_text(catalog: dict) -> str:
    lines = ["TTSMaker 中文聲音選單｜先選聲音，再配音", catalog["access"]]
    for key, label in GROUPS.items():
        lines.append(f"\n{label}：")
        for v in catalog["voices"]:
            if v["group"] == key:
                lines.append(f"  {v['id']:>4}　{v['name']}｜{v['accent']}")
    lines.extend(["\n兒童沒有公開精確年齡；港台風格不直接標成台灣口音。",
                  "請選擇聲線編號；沒有使用者選擇時不得自動代選。", catalog["source_url"]])
    return "\n".join(lines)


def prepare_request(root: Path, round_name: str, voice_id: str) -> Path:
    from .assets import files_for_round
    files_for_round(round_name)  # Validate before using a round as a path.
    catalog = load_catalog()
    print(menu_text(catalog))  # A request always presents all choices first.
    selected = next((v for v in catalog["voices"] if v["id"] == str(voice_id)), None)
    if selected is None:
        raise ValueError("不支援這個聲線編號，請從選單重新選擇")
    config = json.loads((root / f"config/{round_name}.json").read_text(encoding="utf-8-sig"))
    if config.get("voice") != f"TTSMaker:{voice_id}":
        raise ValueError("所選聲線與輪次設定不同，保留原設定並停止")
    output = root / f"outputs/{round_name}"
    output.mkdir(parents=True, exist_ok=True)
    target = output / "voice_request.json"
    if target.exists():
        raise FileExistsError("聲音需求已存在，請另存輪次，不覆寫")
    request = {"schema_version":1,"provider":"TTSMaker","voice":selected,
               "source_url":catalog["source_url"],"script":config["script"],
               "settings":{"format":"wav","speed":1,"volume":100,"pitch":"normal","bgm":False},
               "status":"prepared-not-synthesized","voice_user_accepted":False,
               "user_voice_choice_confirmed":True,
               "motion_status":"user-accepted" if config.get('motion_user_accepted') else "needs-review",
               "motion_accepted_from":config.get('motion_accepted_from')}
    target.write_text(json.dumps(request, ensure_ascii=False, indent=2),encoding="utf-8")
    (output / "test_script.txt").write_text(config["script"]+"\n",encoding="utf-8")
    print(f"\n本輪已選：{selected['name']} {voice_id}；台詞與設定已準備，尚未生成聲音。")
    return target


def write_menu_html(target: Path) -> None:
    catalog = load_catalog()
    if target.exists():
        raise FileExistsError(target)
    groups = []
    for key, label in GROUPS.items():
        rows = "".join(f"<label><input type='radio' name='voice' value='{v['id']}'> <strong>{html.escape(v['name'])} {v['id']}</strong><small>{html.escape(v['accent'])}</small></label>" for v in catalog["voices"] if v["group"]==key)
        groups.append(f"<fieldset><legend>{label}</legend>{rows}</fieldset>")
    source = """<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>中文聲音選單</title>
<style>body{font-family:Microsoft JhengHei,sans-serif;max-width:1100px;margin:32px auto;padding:0 24px;background:#f5f6ed;color:#234846;line-height:1.8}h1{margin-bottom:0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}fieldset{border:1px solid #99b1a3;border-radius:16px;background:white}legend{font-size:23px;font-weight:bold}label{display:block;padding:8px;border-bottom:1px solid #e4ebe2;cursor:pointer}small{display:block;margin-left:25px;font-size:14px}#chosen{position:sticky;bottom:0;padding:15px;background:#234846;color:white;border-radius:12px}a{color:#28654f}@media(max-width:700px){.grid{grid-template-columns:1fr}}</style>
<h1>中文聲音選單</h1><p>男童 3 款、女童 4 款、成人男女各 8 款。先選聲音，再製作配音；這裡不會自動送出或產生費用。</p><p>台灣標示依官方清單；其他聲線不冒充台灣口音。網站可能有驗證碼與排隊。<a href='https://ttsmaker.com/zh-cn' target='_blank' rel='noopener'>開啟官方免費試聽與配音頁</a></p><div class='grid'>"""
    source += "".join(groups) + """</div><p id='chosen' role='status'>尚未選聲音。請先試聽，再將聲線編號告訴工作流。</p><script>for(const input of document.querySelectorAll('input'))input.onchange=()=>{document.getElementById('chosen').textContent='你選擇：'+input.parentElement.querySelector('strong').textContent+'。請將這個編號告訴工作流，再到官網試聽／產生台詞。';};</script></html>"""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source,encoding="utf-8")
