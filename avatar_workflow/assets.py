"""An explicit allowlist for private cross-machine test assets; never a repo mirror."""
from __future__ import annotations
import hashlib
import json
import zipfile
import re
from pathlib import Path
from .tools import contained

FILES = ["outputs/round01/character/boy_empty_hands_v1.png", "outputs/round01/character/boy_mouthless_v1.png",
         "outputs/round01/test_script.txt", "outputs/round01/audio/voice.mp3", "outputs/round01/audio/voice.wav",
         "outputs/round01/audio/speech.json", "outputs/round01/audio/mouths.json",
         "outputs/round01/audio/captions.json", "outputs/round01/audio/captions.srt"]


def files_for_round(round_name: str) -> list[str]:
    if not re.fullmatch(r"round\d{2}", round_name):
        raise ValueError("輪次必須為 round 加兩位數字")
    files = [name.replace("outputs/round01/", f"outputs/{round_name}/", 1) for name in FILES]
    if round_name in ("round03", "round04"):
        files.append(f"outputs/{round_name}/character/arm_torso_atlas_v1.png")
    return files


def export_pack(root: Path, output: Path, round_name: str = "round01") -> None:
    if output.exists():
        raise FileExistsError(output)
    files = files_for_round(round_name)
    manifest = {"schema_version": 1, "round": round_name, "purpose": "generated-assets-only", "files": []}
    payloads = []
    for name in files:
        data = (root / name).read_bytes()
        manifest["files"].append({"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        payloads.append((name, data))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in payloads:
            z.writestr(name, data)
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode())
    output.with_suffix(".zip.sha256").write_text(hashlib.sha256(output.read_bytes()).hexdigest() + "\n", encoding="ascii")
    print(f"已建立 {output}；未包含原始照片、帳密、環境或模型。請放在私人雲端位置。")


def import_pack(root: Path, archive: Path) -> None:
    planned = []
    with zipfile.ZipFile(archive) as z:
        if sum(e.file_size for e in z.infolist()) > 100 * 1024**2:
            raise ValueError("素材包超過 100 MiB 上限")
        manifest = json.loads(z.read("manifest.json"))
        if manifest.get("schema_version") != 1:
            raise ValueError("不支援的素材包版本")
        files = files_for_round(manifest.get("round", "round01"))
        if len(set(z.namelist())) != len(z.namelist()):
            raise ValueError("素材包含重複檔名")
        names = [entry["path"] for entry in manifest["files"]]
        if set(names) != set(files) or set(z.namelist()) != set(files + ["manifest.json"]):
            raise ValueError("素材包不符合指定輪次的允許清單")
        for item in manifest["files"]:
            name = item["path"]
            target = contained(root, name)
            data = z.read(name)
            if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError(f"雜湊不符：{name}")
            if target.exists() and target.read_bytes() != data:
                raise FileExistsError(f"保留現有版本，拒絕覆寫：{target}")
            planned.append((target, data))
    # All entries and conflicts are checked before the first write.
    for target, data in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
    print(f"已驗證並匯入 {len(planned)} 個素材。")
