from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .hardware import detect, save_report
from .recommend import recommend


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="數位人工作流：硬體檢測與保守推薦")
    subs = parser.add_subparsers(dest="action", required=True)
    doctor = subs.add_parser("doctor", help="唯讀檢測硬體，不下載模型、不呼叫付費服務")
    doctor.add_argument("--offline", action="store_true")
    doctor.add_argument("--output", default="work/hardware/report.json")
    speech = subs.add_parser("speech", help="免費線上配音原型；不複製個人聲音")
    speech.add_argument("--script", required=True)
    speech.add_argument("--voice", default="zh-TW-YunJheNeural")
    speech.add_argument("--output", default="outputs/round01/audio")
    speech.add_argument("--rate", default="-5%")
    bootstrap = subs.add_parser("tools", help="下載固定版本的官方 Rhubarb portable 工具")
    bootstrap.add_argument("--root", default=".")
    bootstrap.add_argument("--ffmpeg", action="store_true", help="另下載有公開 SHA256 的 Windows FFmpeg/FFprobe")
    lips = subs.add_parser("lips", help="以音訊分析產生非英文近似嘴型時間")
    lips.add_argument("--audio", required=True)
    lips.add_argument("--output", default="outputs/round01/audio/mouths.json")
    lips.add_argument("--recognizer", choices=["phonetic", "pocketSphinx"], default="phonetic")
    pack = subs.add_parser("pack", help="建立僅包含指定測試素材的可攜包")
    pack.add_argument("--output")
    pack.add_argument("--round", default="round01")
    unpack = subs.add_parser("unpack", help="安全匯入素材包，不覆寫內容不同的檔案")
    unpack.add_argument("archive")
    voices = subs.add_parser("voices", help="主動列出男童／女童及成人中文聲音選單")
    voices.add_argument("--html", help="另產生可點選的本機聲音選單，不自動合成")
    prepare = subs.add_parser("prepare-voice", help="先列聲音選單，再保存已選聲線與台詞")
    prepare.add_argument("--round", required=True)
    prepare.add_argument("--voice-id", required=True)
    external = subs.add_parser("import-speech", help="匯入網站配音及本機 ASR 詞界，保留定稿台詞")
    external.add_argument("--round", required=True)
    external.add_argument("--audio", required=True)
    external.add_argument("--asr", required=True)
    external.add_argument("--corrections")
    subs.add_parser("templates", help="列出八種頭像風格與可沿用的身體範本")
    args = parser.parse_args()
    if args.action == "doctor":
        hw = detect(Path.cwd())
        report = {"hardware": hw, "recommendations": recommend(hw, args.offline)}
        save_report(report, Path(args.output))
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.action == "speech":
        import asyncio
        from .speech import synthesize
        asyncio.run(synthesize(Path(args.script), args.voice, Path(args.output), args.rate))
    elif args.action == "tools":
        from .tools import install_rhubarb, install_ffmpeg_windows
        print(install_rhubarb(Path(args.root)))
        if args.ffmpeg:
            install_ffmpeg_windows(Path(args.root))
    elif args.action == "lips":
        from .tools import analyze_lips
        analyze_lips(Path.cwd(), Path(args.audio), Path(args.output), args.recognizer)
    elif args.action in ("pack", "unpack"):
        from .assets import export_pack, import_pack
        if args.action == "pack":
            export_pack(Path.cwd(), Path(args.output or f"outputs/{args.round}_asset_pack.zip"), args.round)
        else:
            import_pack(Path.cwd(), Path(args.archive))
    elif args.action == "voices":
        from .voices import load_catalog, menu_text, write_menu_html
        print(menu_text(load_catalog()))
        if args.html:
            write_menu_html(Path(args.html))
    elif args.action == "prepare-voice":
        from .voices import prepare_request
        prepare_request(Path.cwd(), args.round, args.voice_id)
    elif args.action == "import-speech":
        from .external_speech import import_speech
        import_speech(Path.cwd(),args.round,Path(args.audio),Path(args.asr),Path(args.corrections) if args.corrections else None)
    elif args.action == "templates":
        from .templates import template_menu
        print(template_menu())


if __name__ == "__main__":
    main()
