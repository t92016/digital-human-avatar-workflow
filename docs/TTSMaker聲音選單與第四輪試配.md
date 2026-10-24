# TTSMaker 聲音選單與第四輪試配

查證及製作日期：2026-10-23（Asia/Taipei）。最新進度以根目錄 `專案進度.md` 為準。

後續策略更新（2026-10-24）：官方免費字元限制已查證，新作品轉本機TTS優先，本文23款清單保留為TTSMaker備援與既有示範來源；不是已接通的本機聲線庫。詳見 [限制與本機轉向評估](TTSMaker限制與本機語音轉向評估_2026-10-24.md)，不追改阿忠凍結示範或原已接受配音。

## 使用者驗收與固定示範

使用者觀看後表示阿忠＋萌萌1202的聲音與動作均可接受，並指定保存為日後repo效果示範。固定版本在 `examples/azhong-mmeng-1202/`，包含三支原MP4、原配音、字幕、預覽圖、比較頁及23款聲音選單。檔案雜湊、驗收日期與範圍記於manifest；`config/round04.json`更新為本輪聲音已接受。此驗收只適用既有阿忠台詞與成品，不自動延伸到新人物、新台詞或其他聲線。

原`outputs/round04/`、speech metadata與素材包保留生成時快照，下文待驗收等敘述是製作當時的技術紀錄。未重配、重做時間、轉碼或覆寫三支影片。GitHub準備檔只包含這次指定的展示成品；本次沒有推送或部署。

## 互動規則與聲音清單

使用者指定採用免費網站、免註冊、免自行申請 API。每次進入中文配音階段，Agent 主動提供男童、女童、成人男聲、成人女聲四組的名稱、編號及口音，再由使用者選擇。已有確認可沿用，不反覆詢問。

選單唯一資料來源是 `config/ttsmaker-voices.json`。可用命令列列出全部選項，或產生不會自動送出配音的本機互動頁：

```powershell
.\.venv\Scripts\python.exe -m avatar_workflow voices
.\.venv\Scripts\python.exe -m avatar_workflow voices --html outputs/聲音選單.html
```

本次已重新用瀏覽器核對 [TTSMaker 官方中文頁](https://ttsmaker.com/zh-cn) 的動態清單。這是可選聲線，不是人氣排行或已逐款實測的音質名次。同名的普通／多情緒／快速版本沒有重複計數。成人指一般解說方向，官網沒有公開精確年齡；兒童依 Child 標示。

| 分組 | 名稱與編號 | 口音界線 |
| --- | --- | --- |
| 男童 3 款 | 萌萌1202、明明1401、小華1402 | 未標台灣；一般中文候選 |
| 女童 4 款 | 甜甜1203、糖豆1522、雪花1523、莉莉1416 | 未標台灣；一般中文候選 |
| 成人男聲 8 款 | 家豪1602、阿澤349、樊雨999、元芳345、阿飛1508、啊樂1506、小龍1515、柏宇1660 | 只有家豪明列 Taiwan；其餘未標台灣，柏宇為多語種 |
| 成人女聲 8 款 | 菡穎889、雅婷1601、淑芬1606、麗娜1603、婉君1604、瀟瀟204、安妮1406、夢夢346 | 菡穎／雅婷／淑芬明列台灣；麗娜／婉君只標港台風格；其他未標台灣 |

成人女聲「夢夢346」與男童「萌萌1202」不同，不可混淆。男女成人各八款，符合使用者 5～8 款、最多十款的範圍。台灣標示依網站，不把港台風格等同原生台灣口音，也不將簡繁體介面當成口音證據。

網站免費版可能有驗證碼、首次人類驗證及排隊，部分情緒控制屬 Pro；不是無人值守 API。執行時遵守瀏覽器工具對驗證碼的當次同意規範，不繞過驗證。免費額度與條件以當時官網為準，不承諾永久不限量。

## 本輪實際配音

使用者已接受第三輪動作，明確選擇阿忠下一輪為 **萌萌1202**。人物、制服、三種動作參數、左下角及 45% 高度沿用，沒有重新生圖。

已在官方免費頁實際填入定稿繁體中文台詞，選中 1202，WAV／語速1.0／音量100%／normal pitch／無BGM。使用者明確同意本次驗證碼及免費試配後，完成網站驗證、生成並下載 WAV 與 SRT。未註冊、未取得 API key、未付費，未上傳人物照片。原始下載另存於 `outputs/round04/audio/ttsmaker_original.wav`、`ttsmaker_original.srt`，來源與 SHA256、成功頁截圖在 `work/round04/`。

原始 WAV 是16kHz、單聲道、16-bit PCM，13.0839375秒。網站 SRT 只有整段0～13.08秒，不能拿來當逐句同步資料，因此沒有套用舊聲音時間或按字數平均切割。

## 本機詞界、字幕與對嘴

另安裝 `faster-whisper==1.2.1` 作外部音訊對齊的可選工具，使用 [SYSTRAN 官方程式](https://github.com/SYSTRAN/faster-whisper) 與 [官方轉換的 Whisper tiny](https://huggingface.co/Systran/faster-whisper-tiny)，MIT。模型固定 revision `d90ca5fe260221311c53c58e660288d3deb8d356`，權重75,538,270bytes；只下載到專案忽略的 `models/`，無帳號、無音訊上傳。本機用 CPU／int8／4threads，暖機後這段辨識約1.42秒，不含下載。

可選完整依賴鎖定在 `requirements-alignment.lock.txt`，基本原型鎖檔保留。PyAV19與該版 faster-whisper 的路徑解碼參數不相容；本工作流先以標準庫讀已確認格式的 PCM WAV，傳入 float32樣本，沒有修改外部套件或安裝 CUDA。其他音訊需先轉成同格式，再產生 ASR。

tiny辨識得到音訊詞界，但有「滿／慢、共／更、工／更」同音近音文字錯誤；已將四個校稿項目明記於 `work/round04/asr-corrections.json`，只將字幕文字對回已確認原稿，時間仍取自同一新音訊，不改動配音。實際咬字仍待使用者試聽，不能把修正字幕當成聲音已修正。

`import-speech` 先比對音檔SHA256、台詞、聲線及時間範圍；辨識與原稿不符時停止，須有明確校稿，不自動估算等距字幕。產出9段繁體字幕、speech metadata及來源MP3／WAV，Rhubarb1.14.0 phonetic由新WAV產生近似嘴型。字幕及嘴型都是近似時間，主觀精度待驗收；不宣稱強制對齊或逐音素精準。

```powershell
# 首次需要本機外部語音詞界時，安裝可選鎖檔：
uv pip install --python .venv/Scripts/python.exe --only-binary :all: --cache-dir work/uv-cache -r requirements-alignment.lock.txt

# 每輪先由使用者選聲，保存原台詞與網站設定。round04已建立，重跑需用新輪次：
.\.venv\Scripts\python.exe -m avatar_workflow prepare-voice --round round04 --voice-id 1202

# 取得該輪網站WAV後，在本機分析；不向外傳送音訊：
.\.venv\Scripts\python.exe scripts/transcribe-local.py --audio outputs/round04/audio/ttsmaker_original.wav --output work/round04/asr.json --revision d90ca5fe260221311c53c58e660288d3deb8d356
.\.venv\Scripts\python.exe -m avatar_workflow import-speech --round round04 --audio outputs/round04/audio/ttsmaker_original.wav --asr work/round04/asr.json --corrections work/round04/asr-corrections.json
.\.venv\Scripts\python.exe -m avatar_workflow lips --audio outputs/round04/audio/voice.wav --output outputs/round04/audio/mouths.json
node scripts/build-sample.cjs round04
$env:AVATAR_TEST_ROUND='round04'
npm.cmd test
```

上述prepare／ASR／import命令拒絕覆寫已存在結果；這是產生新輪次的流程，不是要求對已完成資料強制重跑。校稿檔必須對應該份ASR，不能沿用另一段音訊的校稿或舊時間。網站目前無免金鑰的自動API；取音仍需網頁步驟，後半段可本機重跑。

## 本輪產出與檢查

三支影片為 `outputs/round04/mode1_hands.mp4`、`mode2_natural.mp4`、`mode3_lively.mp4`，各1920×1080、24fps、13.125秒／315幀、H.264＋AAC、looks。三支完整解碼無錯誤，AAC與來源WAV零位移相關值約0.999976。共用一份萌萌配音；動作從第三輪沿用，因聲音較短，完整舉手週期數依片長決定，不強行截斷回程。

HyperFrames三個check通過；瀏覽器逐嘴型cue、字幕、跳轉一致性、固定位置與模式差異通過。原頭部及身體素材保留；沒有使用新頭像接點改動本輪阿忠。播放器與實際MP4擷取畫面另檢查，聲音仍為 `voice_user_accepted=false`。

播放器為 `outputs/round04/萌萌配音比較.html`，聲音選單為同目錄 `聲音選單.html`。`round04_asset_pack.zip`含10個允許清單素材，匯出及相同內容安全匯入通過；原網站SRT、下載檔與ASR報告屬來源紀錄，不以素材包假裝搬移完整開發環境。換機可匯入已校稿的speech／嘴型／字幕直接build；要重新做ASR才需要可選依賴與模型。
