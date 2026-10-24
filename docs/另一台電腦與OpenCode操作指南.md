# 另一台電腦與OpenCode操作指南

本文件說明目前已完成工作流的部署與操作，不新增較複雜的製片階段。最新驗收、發布狀態及接續第一步集中在根目錄「專案進度.md」。

## 從公開網址開始

- Repo：https://github.com/t92016/digital-human-avatar-workflow
- Pages：https://t92016.github.io/digital-human-avatar-workflow/
- 純文字入口：Pages根目錄agent.md；原碼、指令與模型清單亦可由GitHub取得。

OpenCode的[官方規則文件](https://opencode.ai/docs/rules/)支援repo根目錄AGENTS.md。Codex及其他Agent也可照同一閱讀順序：AGENTS、README、專案進度，再讀相關docs。不要用/init覆蓋掉已有規範，也不要建立第二個PROJECT_STATUS或handoff。若Agent支援Skill，可按其技能安裝機制引用本repo的skills/shutdown-sync；不需搬移原電腦的全域設定。

## 看影片與重建的差別

公開三組各三支MP4可直接觀看、下載；皆是既有完成片的位元組副本，無須模型。部署同一套軟體環境需依下列步驟下載模型；原樣重建同一人物還需私人圖層、頭像、眼皮、音訊與校準。Git不包含這些私人來源，也不以完成MP4冒充可編輯素材包。

## Windows安裝順序

準備Python3.12、Node.js22以上、Git與uv。確認python實際為3.12，或將setup的PythonCommand指定為該Python的完整路徑。所有命令在clone後的repo根目錄執行；不要複製舊機器.venv、node_modules、驅動或二進位快取。

```powershell
git clone https://github.com/t92016/digital-human-avatar-workflow.git
cd digital-human-avatar-workflow
.\scripts\setup.ps1 -PythonCommand python -RenderTools
.\.venv\Scripts\python.exe -m avatar_workflow doctor
.\scripts\setup-sadtalker-cpu.ps1
```

setup建立主環境並安裝requirements-prototype.lock.txt與package-lock.json；RenderTools下載官方來源的Rhubarb、FFmpeg／FFprobe及獨立Chrome渲染瀏覽器。HyperFrames0.8.191、GSAP3.14.2、Playwright1.62.1依lock，不直接upgrade來追新版。模型安裝可分開做，觀看示範不需這些安裝。

SadTalker腳本固定Python3.10.21、CPU torch2.6.0／torchvision0.21.0與requirements-sadtalker-cpu.lock.txt，原碼commit為cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8。相容修正在patch-sadtalker-compat.py，無GFPGAN美顏。各來源與驗證細節見既有SadTalker踩坑MD，不能把CPU鎖定檔直接切CUDA就算GPU相容已驗證。

| 權重 | 本機目的路徑 | 大約大小 |
| --- | --- | ---: |
| SadTalker_V0.0.2_256.safetensors | models/sadtalker/ | 725MB |
| mapping_00109-model.pth.tar | models/sadtalker/ | 156MB |
| alignment_WFLW_4HG.pth | models/sadtalker/face/ | 194MB |
| detection_Resnet50_Final.pth | models/sadtalker/face/ | 109MB |

正式URL、精確大小、SHA256、權重revision在config/sadtalker-models.json；download-sadtalker-models.py只下載這四個。前兩個可與上游hash比對，facexlib兩檔保留本專案固定hash，不能把自行計算稱為上游簽章。全部權重約1.10GiB，留在models，Git忽略。

## 選用ASR、TTS與生圖

新的外部配音若需詞界，可於主環境安裝requirements-alignment.lock.txt，再使用scripts/transcribe-local.py；模型為Systran/faster-whisper-tiny，revision與int8／CPU參數在config/local-alignment.json，權重約75.5MB，會放本機快取。先看 `--help` 的實際參數，不把ASR結果當定稿台詞；校稿保留原詞界。

本機TTS仍待安裝／介接：BreezyVoice與Qwen3-TTS的來源、隔離環境及參考聲需求在config/speech-policy.json與既有TTS研究。台灣口音／童趣年齡感須聽樣本確認，voices命令列的是TTSMaker備援清單。圖片優先使用已指定工具；無GPT Image能力才評估Qwen-Image等本機候選，先看生圖研究中的授權、完整管線需求與實測狀態。不是clone後自動安裝全部大型模型。

## 製作順序與命令地圖

| 階段 | 現有入口 | 必要輸入／限制 |
| --- | --- | --- |
| 角色／模式選單 | python -m avatar_workflow templates | 僅需求選單，非任意人物一鍵綁定 |
| 原嘴頭像短測 | scripts/run-sadtalker-head-test.py | 已確認Q版原嘴頭像、WAV，3～5秒，新輸出目錄 |
| 穩定頭像 | scripts/stabilize-sadtalker-head.py | 髮部ROI須逐角色校準，只處理頭像層 |
| 局部眨眼 | scripts/compose-local-blink.py | 已校準眼區與眼皮材質；ade-blink-round08.json只對阿德有效 |
| 阿忠歷史三模式 | scripts/build-sample.cjs round04 | 需原私人圖集與原音；公開examples不是可編輯圖集 |
| 本人身體基本動作 | scripts/build-custom-fullbody-sample.cjs | round09私人材質、頭像與alpha；尚非通用新人物入口 |
| 連續彎肘／屈膝 | scripts/build-articulated-fullbody.cjs | round10專用校準、WebGL及材質重疊 |
| 本人13秒完整教材 | scripts/build-personal-body-teaching.cjs | round11專用完整頭像與本人圖層；腳本含此人物已固定來源 |
| 實際渲染 | scripts/hf.cjs check／render | 語音先接受、素材齊備，才建時間軸與三模式 |

```powershell
.\.venv\Scripts\python.exe scripts/run-sadtalker-head-test.py --image private_inputs/my-character/head.png --audio private_inputs/my-character/voice.wav --output outputs/my-head-test --seconds 4.4
```

上例是使用者自行提供的本機素材。run-sadtalker-full-dialogue.py為阿德已接受原音5～30秒的專用接續，不能只換輸出目錄就聲稱任意新台詞／新人物已支援。正式三模式樣例保留在config/round04、round05、round11；新台詞要重做音訊詞界、字幕、對嘴與背景，不循環短頭像。

## 私人素材與肢體

身體動作使用SVG／GSAP或連續WebGL網格，素材必須有完整袖子及肩髖重疊；彎肘／膝須保留連續材質，不能旋轉裁斷四肢。頭身比例、頸部／膚色、眼皮、關節及活動範圍逐角色校準。三模式留在指定區域，教學面板與字幕優先。

舊pack／unpack提供round01～04素材允許清單的基礎，尚未涵蓋完整round05／09／11及局部眼皮。要原樣重建本人角色，先由素材持有人提供完整的私人圖層與校準，或依新人物重新製作；不能用公開MP4反推原圖後宣稱無損復原。這項缺口不影響安裝對嘴環境與觀看展示，也不在本次發布中假稱已完成。

## 硬體、驗證與收工

doctor報告在work/hardware，不提交。舊GPU走CPU也可保持已接受素材與1080p，但時間不同；本機已有一次13秒完整頭像CPU推論約31分鐘的紀錄，不能直接推估另一台速度。若無法合理生圖，使用已接受素材或在另一台較強電腦生成，品質不自動降低。量化／加速版重新做人物比對。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
npm.cmd test
.\.venv\Scripts\python.exe scripts/verify-publication.py
.\scripts\shutdown-sync.ps1
```

公開驗證檢查三組九支影片雜湊、尺寸／時長、本機連結與排除規則；影片新優化另依對應逐幀腳本與目視驗收。收工技能在skills/shutdown-sync/SKILL.md，預設只掃描與記時間，Commit／Push須沿用當次明確授權。所有完成事項、失敗與下一步只更新專案進度。
