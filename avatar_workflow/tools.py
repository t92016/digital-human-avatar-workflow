"""Fixed official portable binary; no shell installation commands."""
from __future__ import annotations
import hashlib
import json
import platform
import subprocess
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

VERSION = "1.14.0"


def install_ffmpeg_windows(root: Path) -> None:
    if platform.system() != "Windows" or platform.machine().lower() not in ("amd64", "x86_64"):
        raise RuntimeError("此 portable FFmpeg 下載限 Windows x64；其他平台請用系統套件管理器安裝 FFmpeg/FFprobe。")
    url = "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip"
    expected = "60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba"
    downloads = root.resolve() / "work/downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / "ffmpeg-9.0.2-essentials_build.zip"
    if not archive.exists():
        part = archive.with_suffix(".zip.part")
        # Small HTTP ranges can resume a connection interrupted during a large download.
        total = 114768076
        start = part.stat().st_size if part.exists() else 0
        if start > total:
            raise ValueError("不明大小的 FFmpeg 暫存下載，請保留檔案並指定新工作目錄。")
        while start < total:
            end = min(total - 1, start + 8 * 1024**2 - 1)
            request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {start}-"):
                    raise RuntimeError("下載伺服器未正確回傳範圍，拒絕混合不明下載內容。")
                block = response.read()
            if len(block) != end - start + 1:
                raise RuntimeError("下載區塊不完整；下次執行會從已完成區塊重試。")
            with part.open("ab") as handle:
                handle.write(block)
            start += len(block)
            print(f"FFmpeg 下載 {start}/{total} bytes", flush=True)
        part.rename(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != expected:
        raise RuntimeError("FFmpeg 封存與供應者公開 SHA256 不符，拒絕解壓及執行。")
    target = root.resolve() / "tools/bin"
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for name in ("ffmpeg.exe", "ffprobe.exe"):
            entry = next(e for e in z.namelist() if e.endswith("/bin/" + name))
            data = z.read(entry)
            destination = target / name
            if destination.exists() and destination.read_bytes() != data:
                raise FileExistsError(destination)
            destination.write_bytes(data)
    (downloads / "ffmpeg_provenance.json").write_text(json.dumps({"url": url, "version": "9.0.2", "sha256": digest,
        "verified_against": url + ".sha256", "antivirus": "not-verified"}, indent=2), encoding="utf-8")
    print("FFmpeg/FFprobe 9.0.2 已通過供應者公開雜湊比對。")


def contained(root: Path, name: str) -> Path:
    # Check both path conventions even when importing a pack on a different OS.
    if "\\" in name or ":" in name:
        raise ValueError(f"不安全的封存路徑：{name}")
    target = (root / name).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"封存路徑超出目標資料夾：{name}")
    return target


def install_rhubarb(root: Path) -> Path:
    root = root.resolve()
    system = {"Windows": "Windows", "Linux": "Linux", "Darwin": "macOS"}.get(platform.system())
    if system is None or platform.machine().lower() not in ("amd64", "x86_64"):
        raise RuntimeError("此自動安裝僅支援官方 x86_64 portable 套件；其他平台需另驗證。")
    name = f"Rhubarb-Lip-Sync-{VERSION}-{system}"
    executable = root / "tools/bin" / name / ("rhubarb.exe" if system == "Windows" else "rhubarb")
    if executable.is_file():
        return executable
    url = f"https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v{VERSION}/{name}.zip"
    archive = root / "work/downloads" / f"{name}.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        request = urllib.request.Request(url, headers={"User-Agent": "talking-character-prototype/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response, archive.open("wb") as handle:
            while block := response.read(1024 * 1024):
                handle.write(block)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    target_root = root / "tools/bin"
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            target = contained(target_root, entry.filename)
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("拒絕封存內的符號連結")
            if not entry.is_dir():
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    raise FileExistsError(target)
                target.write_bytes(z.read(entry))
    if not executable.is_file():
        raise RuntimeError("封存結構與預期不同，未執行未知檔案。")
    if system != "Windows":
        executable.chmod(executable.stat().st_mode | 0o100)
    provenance = {"url": url, "version": VERSION, "sha256": digest,
                  "hash_kind": "locally-computed-not-independent-authentication",
                  "antivirus": "not-verified", "source": "official GitHub release"}
    (archive.parent / "rhubarb_provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return executable


def analyze_lips(root: Path, audio: Path, output: Path, recognizer: str) -> None:
    system = {"Windows": "Windows", "Linux": "Linux", "Darwin": "macOS"}[platform.system()]
    executable = root / f"tools/bin/Rhubarb-Lip-Sync-{VERSION}-{system}" / ("rhubarb.exe" if system == "Windows" else "rhubarb")
    if not executable.is_file():
        raise RuntimeError("請先執行 python -m avatar_workflow tools。")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    # Rhubarb 1.14's Windows path library fails in Chinese project directories.
    # Run its unmodified official binary and data from an owned ASCII temp folder.
    with tempfile.TemporaryDirectory(prefix="avatar-rhubarb-") as folder:
        scratch = Path(folder).resolve()
        if not scratch.is_relative_to(Path(tempfile.gettempdir()).resolve()):
            raise RuntimeError("暫存路徑不在預期根目錄")
        staged_exe = executable
        staged_audio = audio.resolve()
        if platform.system() == "Windows":
            if not str(scratch).isascii():
                raise RuntimeError("Rhubarb 需 ASCII 暫存路徑；請將 TEMP 設為可寫的英數路徑。")
            shutil.copytree(executable.parent, scratch / "tool")
            staged_exe = scratch / "tool" / executable.name
            staged_audio = scratch / "voice.wav"
            shutil.copy2(audio, staged_audio)
        staged_output = scratch / "mouths.json"
        subprocess.run([str(staged_exe), "-r", recognizer, "-f", "json", "--extendedShapes", "GHX",
                        "-o", str(staged_output), str(staged_audio)], check=True, timeout=600)
        data = json.loads(staged_output.read_text(encoding="utf-8"))
        data["metadata"]["soundFile"] = audio.name
        data["metadata"]["recognizer"] = recognizer
        data["metadata"]["toolVersion"] = VERSION
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"嘴型時間已保存：{output}；非英文 phonetic 結果仍需人工檢視。")
