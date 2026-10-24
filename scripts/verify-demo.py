"""Verify a frozen showcase using only the Python standard library."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def verify(directory: Path) -> tuple[int, int]:
    root = directory.resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("不支援的示範 manifest 版本")
    seen: set[str] = set()
    total = 0
    for entry in manifest["files"]:
        relative = entry["path"]
        portable = PurePosixPath(relative)
        if (not relative or relative in seen or relative == "manifest.json"
                or portable.is_absolute() or ".." in portable.parts
                or "\\" in relative or ":" in relative):
            raise ValueError(f"示範清單含不合法或重複路徑：{relative}")
        seen.add(relative)
        target = (root / relative).resolve(strict=True)
        if not target.is_relative_to(root) or not target.is_file():
            raise ValueError(f"示範檔案不在目錄內：{relative}")
        data = target.read_bytes()
        if len(data) != entry["size_bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"示範檔案雜湊或大小不符：{relative}")
        total += len(data)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != seen | {"manifest.json"}:
        raise ValueError("示範目錄有未列入清單或缺少的檔案")
    if not seen:
        raise ValueError("示範清單不可為空")
    return len(seen), total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="檢查已凍結示範的 SHA256 與檔案清單")
    parser.add_argument("directory", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[1] / "examples/azhong-mmeng-1202")
    args = parser.parse_args()
    count, size = verify(args.directory)
    print(f"示範完整性通過：{count} 個檔案，共 {size:,} bytes。")
