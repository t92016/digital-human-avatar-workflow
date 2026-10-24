"""Conservative planning thresholds, not claims of official model minima."""
from __future__ import annotations
import json
from pathlib import Path


def recommend(hw: dict, offline: bool = False) -> dict:
    ram = hw.get("ram", {}).get("total_gib")
    available = hw.get("ram", {}).get("available_gib")
    disk = hw.get("project_disk_free_gib")
    candidates = []
    for gpu in hw.get("gpus", []):
        cap = gpu.get("compute_capability")
        try:
            driver_major = int(gpu.get("driver", "0").split(".")[0])
        except ValueError:
            driver_major = 0
        # Do not pool VRAM from different GPUs; assess each usable GPU separately.
        if gpu.get("vendor") == "nvidia" and cap is not None and cap >= 8.0 and driver_major >= 550:
            candidates.append(gpu)
    best = max(candidates, key=lambda g: g.get("vram_mib", 0), default=None)
    vram = best.get("vram_mib", 0) if best else 0
    free_vram = best.get("free_vram_mib", 0) if best else 0
    warnings = []
    if available is not None and available < 4:
        warnings.append("目前可用 RAM 少於 4 GiB；先關閉不需要的程式，使用單一渲染 worker。")
    if disk is not None and disk < 10:
        warnings.append("專案磁碟空間少於 10 GiB；暫緩安裝與模型下載。")
    if hw.get("gpus") and not best:
        warnings.append("GPU 架構／驅動未通過保守 CUDA 篩選，或資料未知；不自動推薦大型 GPU 模型。")
    tier = "lightweight-2d"
    voice = {"primary": "existing-audio" if offline else "edge-tts", "status": "needs-smoke-test",
             "note": "使用者錄音或已確認的配音" if offline else "線上非官方用戶端；先即時查詢台灣聲線並試聽。"}
    policy_path = Path(__file__).resolve().parents[1] / 'config/speech-policy.json'
    if not offline and policy_path.exists():
        policy = json.loads(policy_path.read_text(encoding='utf-8'))
        if policy.get('primary_for_new_work') == 'local-tts':
            voice = {'primary':'local-tts', 'status':policy['integration_status'],
                     'policy':'config/speech-policy.json', 'fallback':policy['fallback_provider'],
                     'runtime_verified':False,
                     'note':'新作品優先評估本機TTS，台灣口音優先；尚未安裝／接通或選定新聲線。現有眨眼測試沿用已接受音檔，不自動換聲。'}
    optional = []
    if ram is not None and ram >= 12:
        optional.append({"id": "breezyvoice-cpu", "status": "candidate-not-installed", "note": "偏重台灣華語；需參考音訊、Windows 依賴整理與速度實測。"})
    if best and vram >= 6 * 1024 and free_vram >= 4 * 1024 and ram is not None and ram >= 16 and available is not None and available >= 8 and disk is not None and disk >= 10:
        optional.append({"id": "qwen3-tts-0.6b", "status": "hardware-candidate-not-runtime-verified", "note": "確認 PyTorch CUDA、模型授權及台灣口音後才試用。"})
        tier = "gpu-voice-2d"
    if best and vram >= 24 * 1024 and free_vram >= 20 * 1024 and ram is not None and ram >= 32 and available is not None and available >= 24 and disk is not None and disk >= 100:
        tier = "gpu-video-candidate"
        optional += [{"id": "infinitetalk", "status": "candidate-not-runtime-verified", "note": "先測 480p 短片；模型／OS／FlashAttention 相容性另驗證。"},
                     {"id": "longcat-avatar-1.5", "status": "candidate-may-need-more-vram", "note": "大型模型，保守門檻只是進入評估，不能保證此顯卡足夠。"}]
    if best and vram >= 24 * 1024 and free_vram < 20 * 1024:
        warnings.append("GPU 總容量足夠但可用顯存不足；先釋放占用，暫不建議影片模型。")
    if hw.get("apple_unified_memory"):
        warnings.append("Apple 統一記憶體不等於 NVIDIA 顯存；不推薦 CUDA 專用影片安裝指令。")
    return {"tier": tier, "recommended_motion_backend": "2d-puppet-rhubarb",
            "preferred_next_evaluation": "infinitetalk-or-longcat-short-test" if tier == "gpu-video-candidate" else "2d-puppet-rhubarb",
            "reason": "先用可重跑的 2D 基線；高規格 GPU 才進入生成式影片比較，不因容量足夠直接宣告相容。",
            "voice": voice,
            "optional_candidates": optional, "selected_gpu": best,
            "auto_install_models": False, "auto_paid_services": False,
            "thresholds_are": "conservative-project-heuristics-not-official-minimums",
            "runtime_verified": False, "warnings": warnings,
            "selection_policy": "硬體可行性優先，再比較口音、角色效果、授權與品質；星數不是品質分數。"}
