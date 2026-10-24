"""Reusable intake choices. Private body textures are imported separately."""
from __future__ import annotations
import json
from pathlib import Path


def template_menu() -> str:
    path=Path(__file__).resolve().parents[1]/'config/avatar-templates.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    lines=['角色製作選單｜先確認風格與身體方案','\n頭像風格：']
    lines.extend(f'  {s["id"]}｜{s["name"]}' for s in data['head_styles'])
    lines.append('\n身體方案：')
    lines.extend(f'  {s["id"]}｜{s["name"]}：{s["generation"]}' for s in data['body_choices'])
    lines.extend(['\n全身動作：①只有手部　②手腳與頭部自然動作　③活潑原地動作',
                  '角色位置、大小由使用者決定；不得在畫面中走動。',
                  '套用阿忠身體：只製作新頭像，保留制服、身體與動作。',
                  data['selection_rule'],
                  '模板素材另由私人素材包取得，Git repo 不包含人物圖。'])
    return '\n'.join(lines)
