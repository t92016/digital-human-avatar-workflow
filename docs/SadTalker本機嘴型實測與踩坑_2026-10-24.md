# SadTalker 本機嘴型實測與踩坑

本文件保存2026-10-24的安裝決策、失敗原因與驗證方法。當前階段、驗收與下一步一律以根目錄 `專案進度.md` 為準。

本文件下方結果是生成時快照。使用者後續已接受第六輪v2相似度及自然度，微小跳動與眨眼另有 [踩坑及優化紀錄](SadTalker跳動與眨眼踩坑及優化紀錄_2026-10-24.md)；最新驗收見專案進度及小樣manifest，不以舊技術快照的false欄位覆蓋後來驗收。

## 目標與界線

使用者要求以阿德已接受的Q版頭像原嘴做音訊驅動，避免抹嘴後貼通用SVG嘴型。本輪僅做頭像短測；已接受的阿忠示範、阿德身體動作、比例及家豪配音均保留，嘴型未確認前不接回身體。

來源為 `outputs/round05/character/head_closed_v1.png`，1254×1254 RGBA，SHA256 `429a0de57b33eea27a495427068a5e69c609a0df9c60fb6e4b849915e19a47ac`。此圖原本有嘴唇；不是 `head_mouthless_v1.png`，也不是原始真人照片。模型輸入採位元組相同的副本，不另行抹除、重畫嘴型或手動修飾人物。

配音沿用已接受的 TTSMaker 家豪1602（台灣成人男聲）。原始24kHz／11.904秒 WAV 的 SHA256 為 `f6b45786884e8526a927e4d069d701cb3509207815d41b86d1e7c34646ce0478`；本輪只擷取前4.4秒，另存16kHz單聲道PCM16，原音不變。內容為「同學們，不嘲笑、不排擠，也不跟著起鬨。」後接短停頓，不為短測重選聲音或重做網站轉換。

SadTalker依音訊產生表情係數，再生成會動的人臉。它使用原頭像的嘴唇外觀作為來源，但不是移動原嘴像素的無損變形；張口時會重建口腔、牙齒及唇部細節，也可能影響眼鏡、臉型與身份。是否較自然必須看實際小樣，不以程式成功代替驗收。

## 固定來源與環境

- 官方程式：[OpenTalker/SadTalker](https://github.com/OpenTalker/SadTalker)，固定 commit `cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8`，主程式Apache2.0；第三方元件及權重另依原來源授權。
- 權重清單依[官方下載腳本](https://github.com/OpenTalker/SadTalker/blob/cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8/scripts/download_models.sh)，主模型與mapping使用維護者的[Hugging Face鏡像](https://huggingface.co/vinthony/SadTalker-V002rc/tree/df6f230f2fbec618d69e47229ea32dd224fc9c5c)，固定revision `df6f230f2fbec618d69e47229ea32dd224fc9c5c`。
- 人臉定位權重來自[facexlib官方release](https://github.com/xinntao/facexlib/releases/tag/v0.1.0)。來源URL、大小及SHA256保存於 `config/sadtalker-models.json`。
- Python 3.10.21、CPU PyTorch 2.6.0+cpu、torchvision 0.21.0+cpu、NumPy1.23.5、Pillow9.5.0、librosa0.9.2、facexlib0.3.0、safetensors0.5.3。完整已解析版本在 `requirements-sadtalker-cpu.lock.txt`；直接依賴在 `requirements-sadtalker-cpu.txt`。
- 所有新環境、Python runtime、原始碼及快取放在 `work/`，權重在 `models/sadtalker/`，不改主專案Python3.12 `.venv`，不安裝全域Python套件。
- 此PC：i5-7500／4邏輯核心、RAM15.92GiB、GT710 2GB。這次明確使用CPU，不將GT710當作已相容CUDA顯卡。其他電腦先重跑doctor，不複製這個venv或沿用此PC速度。

只下載四個必要權重，共1,184,014,224 bytes（約1.10GiB）：256版safetensors、full模式mapping_00109、FAN人臉關鍵點及RetinaFace定位。沒有下載512版、GFPGAN美顏、背景修復、Gradio網站或其他非必要模型。

主模型及mapping下載檔與HF公布的LFS SHA256比對；兩個facexlib檔案從官方release下載後自行計算雜湊，沒有把它們冒充為已比對獨立官方雜湊。重跑下載器時四檔均比對專案固定記錄；這是完整性與可重現檢查，不能單獨證明任何第三方程式絕無惡意。PyTorch舊格式權重以 `TORCH_FORCE_WEIGHTS_ONLY_LOAD=1` 載入，不全域關閉安全載入。

## 已遇問題與修正

| 現象 | 原因與處理 |
| --- | --- |
| Git clone回報 `schannel: SEC_E_NO_CREDENTIALS (0x8009030e)` | 以單次命令 `git -c http.sslBackend=openssl clone ...` 成功。保留TLS驗證，未改全域Git設定。 |
| uv嘗試建立使用者全域Python捷徑／登錄檔遭拒 | 專案內Python及venv已可執行，無須放寬權限。正式安裝腳本加入 `uv python install 3.10.21 --no-bin --no-registry`，並將安裝目錄／快取指定到work。 |
| uv freeze預設讀使用者快取遭拒 | 所有uv步驟均設定 `UV_CACHE_DIR=work/uv-cache`；不因此要求系統權限。 |
| `librosa`匯入失敗：`No module named pkg_resources` | 新版setuptools已不提供該舊介面。獨立環境固定setuptools80.9.0，未升級／修改主環境。 |
| 自製runpy啟動器找不到 `src` | 將SadTalker原始碼目錄加入該子程序的 `sys.path`，並以source為工作目錄。首個失敗紀錄保留在 `outputs/round06/sadtalker-head-v1/manifest.json`，沒有影片。 |
| 舊程式會在未啟用美顏時仍匯入GFPGAN | 將可選face_enhancer匯入移到 `if enhancer` 內；本輪不安裝／啟用美顏套件，減少依賴並避免再改臉。 |
| 對齊函式混合NumPy純量與單元素陣列 | 將`t[0]`、`t[1]`轉為純量，產生明確float32參數陣列；避免NumPy新版ragged-array問題。這是預先針對原始碼相容性修正，不宣稱本輪已實際出現該錯誤。 |
| OpenCV／舊子程序可能不支援含中文的檔名 | 將頭像原檔複製到work下ASCII暫存檔名，傳入相對路徑；輸入內容與SHA256不變。原始中文路徑保留。這是相容性預防，本輪沒有改名或覆寫使用者素材。 |
| full模式出現 `MP4V` tag不支援、fallback至 `mp4v` | 官方貼回程式使用OpenCV的MPEG-4編碼，fallback後成功完成，不是模型失敗。另用FFmpeg轉出H.264／AAC供瀏覽器播放，原模型MP4保留在work。 |

三處來源修改由 `scripts/patch-sadtalker-compat.py` 依固定commit及唯一字串定位套用，可重複執行；變更清單及雜湊記在忽略的 `work/sadtalker/compatibility-manifest.json`。此分支未實測美顏功能，不能在未補裝其依賴時聲稱支援GFPGAN。

## 重跑與驗證方法

先跑doctor，再執行README的安裝／短測命令。安裝腳本與下載器不覆寫不同內容的模型，推論輸出目錄若非空即拒絕，另取v3、v4等版本即可。新電腦需要另取得使用者授權的私人Q版頭像與音訊，GitHub不附這些私人素材。

本次參數：CPU、2threads、batch_size1、size256、preprocess full、still、pose_style0、expression_scale1.0、seed42、無enhancer。`full`用mapping_00109；不要誤以mapping_00229替代。頭部固定模式仍可能有表情、眼睛與下顎變化，不保證完全沒有頭部形變。

先看定位與3DMM是否成功，再看生成影片；MP4經FFprobe檢查實際規格並完整解碼，另外檢視嘴型張合的中間畫格與原圖差異。輸出是模型產物的H.264／AAC可播放副本，原模型結果、完整stdout／stderr及失敗嘗試保留在work；1254px的全圖不代表模型以1254px解析度生成臉部，內部仍為256版。

人物原PNG有透明背景，SadTalker這條RGB影片路徑不保存alpha；本輪只看頭像嘴型，不把黑背景當作最終去背方案。接回身體前需要另驗證遮罩、輪廓、短頸與衣領，不直接沿用SVG嘴型的接合判定。

## 此樣本的實際結果

已產出 `outputs/round06/sadtalker-head-v2/ade_sadtalker_4_4s.mp4`，4.4秒／25fps／110幀、1254×1254、H.264＋AAC，1,133,058bytes。SHA256 `bebe9f3f48857570140216cb28291404eddcb1cf0afaaa214e16e0a48130cafa`。人臉定位、3DMM、音訊驅動、逐格生成與full模式貼回都成功；模型子程序含初始化及輪詢等待約1130.234秒（18分50秒），不含下載、套件安裝與最後H.264轉碼。逐格生成約9秒／格；運算中觀察到程序峰值工作集2.398GiB，這是取樣時的累計峰值，不是對未量測部分或全機RAM需求的保證。

這台PC能執行本機頭像短測，但速度不適合直接做長篇教學片；不能將4.4秒成功概括為任意長度或所有卡通皆可。這次沒有啟用GPU、美顏、512模型、身體合成或字幕新時間軸，也未實作長片自動切段。

技術檢查：FFprobe規格符合、完整解碼0錯誤；AAC解碼與16kHz短音訊在零位移的相關值0.999794915，都是70400取樣。這證明聲音內容與時間位置一致，不代表已通過逐音素嘴唇同步評分。原1254PNG與原24kHz聲音的SHA256保持不變；阿忠凍結示範10檔雜湊檢查也通過。

已目視實際MP4擷取的16張中間畫格（0～4.2秒、每0.28秒）：可見張口、收合與停頓時閉嘴，唇色／輪廓大致延續原圖，未見取樣眼鏡斷裂；全臉、眼鏡與嘴唇有明顯柔化，口腔與局部細節屬模型重新生成。這只是本樣本的取樣觀察，不等於已看遍110幀、所有音素精準或使用者接受。成片manifest仍為 `user_accepted=false`、`body_integrated=false`。

私人比較頁 `index.html` 可正常／0.5倍播放，含原圖並排與嘴部同步放大；本機入口 `http://127.0.0.1:3027/`。可在這個資料夾執行 `python -m http.server 3027 --bind 127.0.0.1` 重開，避免把專案根目錄當公開伺服器。瀏覽器實測影片metadata、播放時鐘、跳轉、慢速切換及390px無水平溢出，JS／HTTP錯誤及外部請求均0；桌面頁繁體字已目視。技術JSON、瀏覽器JSON、截圖與contact sheet保留在該私人輸出目錄。

重建比較頁：`python scripts/build-sadtalker-preview.py outputs/round06/sadtalker-head-v2`。目前標題與嘴部近景區域專為阿德1254PNG校準；其他人物須調整標籤與嘴部座標，不宣稱任意圖片自動定位。這輪只有頭像試驗，沒有建立完整round06身體／字幕專案，不要直接執行 `build-sample.cjs round06` 或把舊pack命令當成完整素材搬移。

本PC安裝腳本已在既有環境再執行一次成功：58套件相容、四權重固定雜湊通過，未重建或改寫來源素材；這不是另一台乾淨電腦實測。doctor已重跑，其主環境報告PyTorch未安裝、PATH未發現FFmpeg，原因是模型在獨立子環境、FFmpeg由專案完整路徑呼叫；不因此重複全域安裝或聲稱子環境失敗。詳細驗收及下一步只更新於 `專案進度.md`。

## 本機配額與長片

對嘴端本機執行，沒有網站按次、文字字數或試用點數的配額；它接收音訊而不是直接唸文字，不含免費TTS服務。TTSMaker網站本身的字數／驗證碼／排隊限制仍另計。本輪既有音訊不需重新上網轉換。

音訊長度仍受RAM、磁碟及運算時間限制。原始渲染程式會暫存整段預測畫格，記憶體隨長度增加；不能承諾任意時長一次成功。此短測入口限制3～5秒是工作流的測試保護，並非模型的字數／秒數上限。長片未實作或驗證自動分段拼接；後續需按語句切段、保留停頓、檢查片段交界及聲畫同步，再擴大長度。若此PC過慢，較強筆電重新doctor後再選合適GPU環境，不把這份CPU鎖定檔誤當成CUDA安裝流程。
