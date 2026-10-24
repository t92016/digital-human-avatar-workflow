"""Edge online TTS prototype. Save service timing before authoring video."""
from __future__ import annotations
import hashlib
import json
import subprocess
import wave
from pathlib import Path


async def synthesize(script: Path, voice: str, output: Path, rate: str = "-5%") -> None:
    import edge_tts
    import imageio_ffmpeg
    text = script.read_text(encoding="utf-8-sig").strip()
    voices = await edge_tts.list_voices()
    selected = next((v for v in voices if v["ShortName"] == voice), None)
    if not selected:
        raise ValueError(f"目前服務未提供聲線 {voice}，請重新選擇，不自動換聲。")
    output.mkdir(parents=True, exist_ok=True)
    mp3, wav = output / "voice.mp3", output / "voice.wav"
    if mp3.exists() or wav.exists():
        raise FileExistsError("音檔已存在；請指定新的輸出資料夾以保留版本。")
    boundaries = []
    try:
        with mp3.open("wb") as handle:
            stream = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
            async for chunk in stream.stream():
                if chunk["type"] == "audio":
                    handle.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    boundaries.append({"start": chunk["offset"] / 10_000_000,
                                       "duration": chunk["duration"] / 10_000_000,
                                       "text": chunk["text"], "type": chunk["type"]})
    except Exception:
        # A failed new stream must not be mistaken for a completed audio version.
        mp3.rename(output / "voice.incomplete.mp3")
        raise
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
                    "-i", str(mp3), "-ar", "16000", "-ac", "1", str(wav)], check=True)
    with wave.open(str(wav), "rb") as audio:
        duration = audio.getnframes() / audio.getframerate()
    metadata = {"provider": "edge-tts (unofficial online client)", "package_version": edge_tts.__version__,
                "voice": selected, "rate": rate, "script": text, "script_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "duration": duration, "timing_source": "service WordBoundary (seconds)", "boundaries": boundaries,
                "voice_user_accepted": False, "timeline_status": "provisional-test-only"}
    (output / "speech.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "voices_snapshot.json").write_text(json.dumps(voices, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已產生 {wav}，{duration:.2f} 秒；聲線 {voice}。尚待使用者試聽。")
