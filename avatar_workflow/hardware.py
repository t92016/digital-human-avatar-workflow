"""Read-only, cross-platform hardware detection; no model downloads/imports."""
from __future__ import annotations
import csv
import ctypes
import importlib.util
import io
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def command(args: list[str], timeout: int = 8) -> tuple[str, str | None]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                                encoding="utf-8", errors="replace", check=False)
        return (result.stdout.strip(), None) if result.returncode == 0 else ("", result.stderr.strip()[:200] or "command failed")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", type(exc).__name__


def memory_info() -> dict:
    total = available = None
    try:
        if sys.platform == "win32":
            from ctypes import wintypes
            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", wintypes.DWORD), ("load", wintypes.DWORD)] + [
                    (n, ctypes.c_ulonglong) for n in ("total", "available", "page_total", "page_available", "virtual_total", "virtual_available", "extended")]
            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                total, available = status.total, status.available
        elif sys.platform.startswith("linux"):
            fields = {line.split(":")[0]: int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()}
            total, available = fields.get("MemTotal"), fields.get("MemAvailable")
        elif sys.platform == "darwin":
            out, error = command(["sysctl", "-n", "hw.memsize"])
            total = int(out) if not error else None
            # macOS uses unified memory on Apple Silicon. Do not label it VRAM.
    except (OSError, ValueError, AttributeError):
        pass
    return {"total_gib": round(total / 2**30, 2) if total else None,
            "available_gib": round(available / 2**30, 2) if available is not None else None}


def parse_nvidia(output: str, with_compute: bool) -> list[dict]:
    gpus = []
    for row in csv.reader(io.StringIO(output)):
        if len(row) < 4:
            continue
        try:
            name, total, free, driver = [v.strip() for v in row[:4]]
            cap = float(row[4].strip()) if with_compute and len(row) > 4 and row[4].strip() not in ("N/A", "[N/A]", "[Not Supported]") else None
            gpus.append({"vendor": "nvidia", "name": name, "vram_mib": int(float(total)),
                         "free_vram_mib": int(float(free)), "driver": driver, "compute_capability": cap})
        except ValueError:
            continue
    return gpus


def nvidia_info() -> tuple[list[dict], list[str]]:
    executable = shutil.which("nvidia-smi")
    if not executable and sys.platform == "win32":
        candidate = Path(os.environ.get("WINDIR", "C:/Windows")) / "System32/nvidia-smi.exe"
        executable = str(candidate) if candidate.is_file() else None
    if not executable:
        return [], ["nvidia-smi 不存在；不假定其他 GPU 可執行 CUDA。"]
    base = [executable, "--format=csv,noheader,nounits"]
    query = "name,memory.total,memory.free,driver_version"
    out, error = command(base + ["--query-gpu=" + query + ",compute_cap"])
    if not error:
        return parse_nvidia(out, True), []
    out, error = command(base + ["--query-gpu=" + query])
    return (parse_nvidia(out, False), ["舊驅動未提供 compute capability，架構相容性需另查。"]) if not error else ([], ["nvidia-smi 查詢失敗；保留輕量路線。"])


def find_browser() -> str | None:
    override = os.environ.get("AVATAR_CHROME")
    if override and Path(override).is_file():
        return override
    candidates = []
    if sys.platform == "win32":
        for variable, suffix in [("PROGRAMFILES", "Google/Chrome/Application/chrome.exe"),
                                 ("PROGRAMFILES(X86)", "Microsoft/Edge/Application/msedge.exe"),
                                 ("LOCALAPPDATA", "Google/Chrome/Application/chrome.exe")]:
            if os.environ.get(variable):
                candidates.append(Path(os.environ[variable]) / suffix)
    elif sys.platform == "darwin":
        candidates += [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                       Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")]
    for name in ("chromium", "chromium-browser", "google-chrome", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    return next((str(p) for p in candidates if p.is_file()), None)


def detect(root: Path) -> dict:
    gpus, notes = nvidia_info()
    disk = shutil.disk_usage(root)
    cpu = platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown")
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    return {"schema_version": 1, "os": platform.system(), "machine_arch": platform.machine(),
            "cpu_description": cpu,
            "logical_cpus": os.cpu_count(), "ram": memory_info(), "gpus": gpus,
            "apple_unified_memory": sys.platform == "darwin" and platform.machine() == "arm64",
            "project_disk_free_gib": round(disk.free / 2**30, 2),
            "runtime": {"python": platform.python_version(), "node": shutil.which("node"),
                        "ffmpeg": shutil.which("ffmpeg"), "browser": find_browser(),
                        "torch_installed": importlib.util.find_spec("torch") is not None,
                        "cuda_execution_tested": False}, "notes": notes}


def save_report(report: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
