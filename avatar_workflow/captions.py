"""Match exact approved punctuation to actual service word timings."""
from __future__ import annotations
import re


def spoken(text: str) -> str:
    return "".join(c for c in text if c.isalnum())


def make_captions(speech: dict) -> list[dict]:
    words = speech["boundaries"]
    text = speech["script"]
    if spoken(text) != "".join(spoken(w["text"]) for w in words):
        raise ValueError("字幕與配音回傳文字不同，請人工校對，不估算等距時間。")
    spans, position = [], 0
    for word in words:
        length = len(spoken(word["text"]))
        spans.append((position, position + length, word))
        position += length
    captions, cursor = [], 0
    for segment in re.findall(r"[^，。！？：、]+[，。！？：、]?", text):
        length = len(spoken(segment))
        matching = [w for start, end, w in spans if start < cursor + length and end > cursor]
        if not matching:
            continue
        start = matching[0]["start"]
        end = matching[-1]["start"] + matching[-1]["duration"]
        captions.append({"start": round(start, 6), "end": round(end, 6), "text": segment})
        cursor += length
    # Hold short punctuation pauses, but never overlap the next caption.
    for i, c in enumerate(captions):
        next_start = captions[i + 1]["start"] if i + 1 < len(captions) else speech["duration"]
        c["end"] = round(min(next_start, c["end"] + 0.18), 6)
    return captions


def to_srt(captions: list[dict]) -> str:
    def timestamp(value: float) -> str:
        ms = round(value * 1000)
        return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"
    return "\n\n".join(f"{i}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n{c['text']}" for i, c in enumerate(captions, 1)) + "\n"
