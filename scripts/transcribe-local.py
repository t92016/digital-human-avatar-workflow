"""Local CPU timestamps for downloaded speech. Does not synthesize or upload audio."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import time
import wave
from pathlib import Path

root=Path(__file__).resolve().parents[1]
os.environ.update(HF_HOME=str(root/'work/hf-cache'),HF_HUB_DISABLE_TELEMETRY='1',
                  HF_HUB_DISABLE_XET='1',HF_HUB_DISABLE_SYMLINKS_WARNING='1')
from huggingface_hub import snapshot_download
from faster_whisper import WhisperModel
import numpy as np

parser=argparse.ArgumentParser()
parser.add_argument('--audio',required=True)
parser.add_argument('--output',required=True)
parser.add_argument('--revision',required=True)
parser.add_argument('--prompt',default='繁體中文。',help='依本輪主題提示辨識；不取代實際音訊')
args=parser.parse_args()
target=Path(args.output)
if target.exists():
    raise FileExistsError(target)
started=time.perf_counter()
model_dir=snapshot_download('Systran/faster-whisper-tiny',revision=args.revision,
    local_dir=str(root/'models/faster-whisper-tiny'),allow_patterns=['config.json','model.bin','tokenizer.json','vocabulary.txt'])
threads=max(1,min(4,os.cpu_count() or 1))
model=WhisperModel(model_dir,device='cpu',compute_type='int8',cpu_threads=threads,num_workers=1)
with wave.open(args.audio,'rb') as wav:
    if (wav.getframerate(),wav.getnchannels(),wav.getsampwidth()) != (16000,1,2):
        raise ValueError('請先轉成 16kHz、單聲道、16-bit PCM WAV')
    samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.float32)/32768
# Decode known PCM with the standard library. Avoid PyAV version-specific options.
segments,info=model.transcribe(samples,language='zh',beam_size=5,word_timestamps=True,
    vad_filter=False,temperature=0,condition_on_previous_text=False,
    initial_prompt=args.prompt)
rows=[]
for segment in segments:
    rows.append({'start':segment.start,'end':segment.end,'text':segment.text,
                 'words':[{'text':w.word,'start':w.start,'end':w.end,'probability':w.probability} for w in segment.words or []]})
result={'engine':'faster-whisper','version':importlib.metadata.version('faster-whisper'),
        'model':'Systran/faster-whisper-tiny','revision':args.revision,'device':'cpu','compute_type':'int8','cpu_threads':threads,
        'audio_sha256':hashlib.sha256(Path(args.audio).read_bytes()).hexdigest(),
        'duration':info.duration,'segments':rows,'initial_prompt':args.prompt,'elapsed_sec':time.perf_counter()-started,
        'note':'ASR timestamps are approximate; approved Traditional Chinese script stays authoritative.'}
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
