"""Import a chosen voice using audio-derived timing and an exact approved script."""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from .captions import spoken, make_captions, to_srt
from .voices import load_catalog
from .assets import files_for_round


def reviewed_boundaries(asr: dict, script: str, corrections: list[dict]) -> list[dict]:
    words=[dict(w) for segment in asr['segments'] for w in segment['words']]
    for item in corrections:
        index=item['word_index']
        if words[index]['text'] != item['from']:
            raise ValueError('校稿項目與 ASR 原文不一致；不套用過期校稿')
        words[index]['text']=item['to']
    if ''.join(spoken(w['text']) for w in words) != spoken(script):
        raise ValueError('辨識文字與定稿不符，請先校稿；不平均估算字幕時間')
    previous=0.0
    for word in words:
        if not 0 <= word['start'] < word['end'] <= asr['duration']+.05 or word['start'] < previous-.001:
            raise ValueError('ASR 時間碼異常')
        previous=word['end']
    return [{'text':w['text'],'start':w['start'],'duration':round(w['end']-w['start'],6),
             'type':'LocalASRWord','probability':w.get('probability')} for w in words]


def import_speech(root: Path, round_name: str, audio: Path, asr_file: Path, corrections_file: Path | None=None) -> None:
    files_for_round(round_name)
    config=json.loads((root/f'config/{round_name}.json').read_text(encoding='utf-8-sig'))
    request=json.loads((root/f'outputs/{round_name}/voice_request.json').read_text(encoding='utf-8'))
    selected=next(v for v in load_catalog()['voices'] if v['id']==request['voice']['id'])
    if config['voice'] != 'TTSMaker:'+selected['id'] or request['script'] != config['script']:
        raise ValueError('音訊需求與輪次聲線／台詞不一致')
    asr=json.loads(asr_file.read_text(encoding='utf-8'))
    digest=hashlib.sha256(audio.read_bytes()).hexdigest()
    if asr['audio_sha256'] != digest:
        raise ValueError('時間資料不是來自這份音訊')
    corrections=json.loads(corrections_file.read_text(encoding='utf-8')) if corrections_file else []
    words=reviewed_boundaries(asr,config['script'],corrections)
    with wave.open(str(audio),'rb') as wav:
        if (wav.getframerate(),wav.getnchannels(),wav.getsampwidth()) != (16000,1,2):
            raise ValueError('請先將配音轉成 16kHz 單聲道 16-bit PCM WAV 再做 ASR')
        duration=wav.getnframes()/wav.getframerate()
    if abs(duration-asr['duration'])>.05:
        raise ValueError('音檔與 ASR 長度不同')
    metadata={'provider':'TTSMaker free website','voice':{'ShortName':config['voice'],'Name':selected['name'],
              'provider_voice_id':selected['id'],'Locale':config['voice_locale'],'classification':selected['official_label']},
              'script':config['script'],'script_sha256':hashlib.sha256(config['script'].encode()).hexdigest(),
              'source_audio_sha256':digest,'source_url':request['source_url'],'settings':request['settings'],
              'duration':duration,'boundaries':words,'timing_source':'local faster-whisper audio-derived word timestamps; approximate',
              'alignment':{k:asr[k] for k in ['engine','version','model','revision','device','compute_type']},
              'reviewed_asr_corrections':corrections,'voice_user_accepted':bool(config.get('voice_user_accepted',False)),
              'timeline_status':'voice-accepted-audio-baseline' if config.get('voice_user_accepted') else 'provisional-test-only'}
    captions=make_captions(metadata)
    output=root/f'outputs/{round_name}/audio'
    output.mkdir(parents=True,exist_ok=True)
    names=['voice.wav','voice.mp3','speech.json','captions.json','captions.srt']
    if any((output/n).exists() for n in names):
        raise FileExistsError('配音已存在，請另存輪次，不覆寫')
    import imageio_ffmpeg
    ffmpeg=root/'tools/bin/ffmpeg.exe'
    if not ffmpeg.exists():
        ffmpeg=Path(imageio_ffmpeg.get_ffmpeg_exe())
    with tempfile.TemporaryDirectory(dir=root/'work') as temporary:
        stage=Path(temporary)
        shutil.copyfile(audio,stage/'voice.wav')
        subprocess.run([str(ffmpeg),'-v','error','-i',str(audio),'-codec:a','libmp3lame','-q:a','2',str(stage/'voice.mp3')],check=True)
        (stage/'speech.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
        (stage/'captions.json').write_text(json.dumps(captions,ensure_ascii=False,indent=2),encoding='utf-8')
        (stage/'captions.srt').write_text(to_srt(captions),encoding='utf-8')
        for name in names:
            shutil.move(str(stage/name),output/name)
    status='聲音已接受，字幕與對嘴仍待影片驗收' if metadata['voice_user_accepted'] else '待試聽驗收'
    print(f'已匯入 {selected["name"]} {selected["id"]}，{duration:.3f} 秒，{len(captions)} 段定稿字幕；{status}。')
