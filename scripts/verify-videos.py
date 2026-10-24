"""Decode the actual MP4s, validate streams, and compare AAC voice to the source."""
import array
import json
import math
import subprocess
import wave
import argparse
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--round", default="round01")
args = parser.parse_args()
import re
if not re.fullmatch(r"round\d{2}", args.round):
    raise ValueError("輪次必須為 round 加兩位數字")
round_name = args.round
output_dir = root / "outputs" / round_name
speech = json.loads((output_dir / "audio/speech.json").read_text(encoding="utf-8"))
config = json.loads((root / f"config/{round_name}.json").read_text(encoding="utf-8"))
lead = config.get('video_timing',{}).get('lead_in_sec',0)
expected_duration = speech['duration'] + lead + config.get('video_timing',{}).get('tail_out_sec',0)
captions = json.loads((output_dir / "audio/captions.json").read_text(encoding="utf-8"))
ffmpeg, ffprobe = root / "tools/bin/ffmpeg.exe", root / "tools/bin/ffprobe.exe"
if not ffmpeg.exists():
    import imageio_ffmpeg
    import shutil
    ffmpeg, ffprobe = imageio_ffmpeg.get_ffmpeg_exe(), shutil.which("ffprobe")
with wave.open(str(output_dir / "audio/voice.wav"), "rb") as f:
    reference = array.array("h", f.readframes(f.getnframes()))
reports = []
for mode, name in [(1, "mode1_hands"), (2, "mode2_natural"), (3, "mode3_lively")]:
    video = output_dir / (name + ".mp4")
    result = subprocess.run([str(ffprobe), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)], capture_output=True, check=True)
    probe = json.loads(result.stdout)
    picture = next(s for s in probe["streams"] if s["codec_type"] == "video")
    sound = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    assert (picture["width"], picture["height"], picture["r_frame_rate"]) == (1920, 1080, "24/1")
    assert abs(float(probe["format"]["duration"]) - expected_duration) < .1
    decode = subprocess.run([str(ffmpeg), "-v", "error", "-i", str(video), "-f", "null", "-"], capture_output=True, check=True)
    assert not decode.stderr.strip(), decode.stderr
    pcm = subprocess.run([str(ffmpeg), "-v", "error", "-i", str(video), "-vn", "-ar", "16000", "-ac", "1", "-f", "s16le", "-"], capture_output=True, check=True)
    actual = array.array("h", pcm.stdout)
    actual = actual[round(lead*16000):]
    count = min(len(reference), len(actual))
    dot = sum(reference[i] * actual[i] for i in range(count))
    energy = math.sqrt(sum(v * v for v in reference[:count]) * sum(v * v for v in actual[:count]))
    similarity = dot / energy if energy else 0
    assert similarity > .98, f"Unexpected audio mismatch: {similarity}"
    frame_dir = output_dir / "qa"
    frame_dir.mkdir(exist_ok=True)
    motion = config.get('motion_profile')
    proof = motion['first_raise_sec']+motion['rise_sec']+.2 if motion else .7
    phrases = [s['caption_prefix'] for s in config['presentation']['scenes'][1:]] if config.get('presentation') else ['上下樓梯','看見同學']
    other_times = [next(c["start"] for c in captions if c["text"].startswith(phrase)) + lead + .25 for phrase in phrases]
    for time in ([proof, *other_times] if mode == 3 else [proof]):
        output = frame_dir / f"mode{mode}_at_{time}.png"
        subprocess.run([str(ffmpeg), "-y", "-v", "error", "-ss", str(time), "-i", str(video), "-frames:v", "1", str(output)], check=True)
    reports.append({"mode": mode, "file": video.name, "duration": float(probe["format"]["duration"]),
                    "size": video.stat().st_size, "video_codec": picture["codec_name"], "audio_codec": sound["codec_name"],
                    "audio_correlation_to_source_at_configured_offset": round(similarity, 6), "audio_offset_sec":lead,"full_decode_errors": 0,
                    "resolution": [1920, 1080], "fps": 24})
(root / "work" / round_name / "video-verification.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
print(json.dumps(reports, indent=2))
