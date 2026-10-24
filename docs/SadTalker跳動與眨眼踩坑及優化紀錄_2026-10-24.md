# SadTalker 跳動與眨眼：踩坑及優化紀錄

本文件保存一次具體優化實驗的問題、方法、採用／放棄依據與限制。跨Agent的當前階段及驗收以根目錄 `專案進度.md` 為唯一來源。使用者要求今後每項動作／功能優化都留下相應MD紀錄，此規則已寫入AGENTS。

## 基準與需求

使用者已接受第六輪阿德SadTalker頭像的相似度及自然度；微小跳動即使無法改善也可接受，希望研究穩定及偶爾眨眼。基準 `outputs/round06/sadtalker-head-v2/ade_sadtalker_4_4s.mp4`，4.4秒／1254×1254／25fps／110幀，SHA256 `bebe9f3f48857570140216cb28291404eddcb1cf0afaaa214e16e0a48130cafa`。已在原manifest另記使用者驗收，沒有改動影片。舊技術報告的false屬生成時快照，不能推翻後來的驗收。

本輪不重配音、不改嘴型台詞、不接回身體。仍使用Python3.10.21／CPU torch2.6.0／OpenCV4.8.1／256版模型及原固定commit，沒有新增權重或修改依賴。環境及授權來源見 [首次安裝實測](SadTalker本機嘴型實測與踩坑_2026-10-24.md)。

## 跳動：觀察、處理及結果

原版已使用 `--still`。查核[官方固定commit的渲染資料程式](https://github.com/OpenTalker/SadTalker/blob/cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8/src/generate_facerender_batch.py)，still固定的是部分3DMM姿態資料，表情仍變化；後續mapping與逐格生成也可能有細微形變。因此「再開still就會完全不動」是錯誤假設。本輪直接量測影像，沒有把某一個神經網路環節當成已證明的唯一根因。

採用小幅剛性穩定候選，實作 `scripts/stabilize-sadtalker-head.py`：

1. 頭髮ROI為影像正規化座標 `[0.18,0.08,0.83,0.38]`，避開眼睛、嘴巴；以首幀為參考。
2. 縮至約35%解析度，以OpenCV ECC估計平移與旋轉（Euclidean，不估縮放），最多60次迭代、epsilon1e-5、Gaussian5。
3. 相關分數低於0.8、中心位移超20px或旋轉超1.5°即停止，保留來源，不把小幅校正套成大型鏡頭移動。逐幀逆向warp以立方插值回原尺寸，黑色邊界。
4. H.264 CRF16／fast／2threads，AAC音軌直接複製；維持原幀數、播放速度與時間。不跨幀平均嘴型，不做補幀。

輸出 `outputs/round07/head_stabilized.mp4`，SHA256 `de3f5881ac890d10a7fab4feb75ef7675ee2677a777a33d0d20658179b243b9d`。本次處理及量測約13.55秒，這是重用既有成片的後處理，不是SadTalker初次生成速度變快。

| 頭髮ROI剛性位移指標 | 原版 | 穩定候選 |
| --- | ---: | ---: |
| 相鄰畫格中心位移RMS（px） | 1.054854 | 0.071717 |
| 相對首幀的最大中心位移（px） | 9.793080 | 0.224533 |
| 最大旋轉絕對值（度） | 0.302078 | 0.058468 |

相鄰位移指標約降低93.2%。這是以同一頭髮ROI估計的剛性位移，不是全部臉部形變、對嘴精度或自然度分數。指標變小不能代替使用者觀看；局部眼鏡、臉頰與下顎仍可能有生成變形。

完整MP4解碼0錯誤，維持1254×1254／25fps／110幀／4.4秒；AAC解碼成16kHz PCM後與基準位元組相同，PCM SHA256 `4a6a79498eca71f08cdafe89c9600004e61a67a510a8a822e774c03fb060b48a`。已目視16張每0.28秒的實際MP4取樣，未見新增邊界裁切；並非全110幀人工逐張驗收。

穩定候選尚待使用者比較。此方法只用在固定說話頭像層；之後再由身體合成層加入已選的原地頭部／全身動作。不得對整張教材成片套此校正，否則會帶動背景或抵消使用者想保留的角色動作。其他角色的ROI須重新校準，不宣稱任意人物自動適用。

## 眨眼：原生機制與踩坑

[官方generate_batch.py](https://github.com/OpenTalker/SadTalker/blob/cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8/src/generate_batch.py)本來就會產生隨機眨眼序列，預設5幀脈衝為 `[0.5,0.9,1,0.9,0.5]`；use_blink預設true。`still`不等於關掉眨眼。原版seed42、110幀重播得到50～54、72～76、88～92幀三組脈衝。已擷取第一組連續眼部畫格，此Q版大眼閉合非常輕微，不能因程式開關為true就宣稱眼睛已自然完全閉上。

眨眼強度不是官方CLI的獨立 `--blink_strength` 參數，不可捏造該命令。本輪從[Audio2Exp最後線性層](https://github.com/OpenTalker/SadTalker/blob/cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8/src/audio2exp_models/networks.py)提取ratio對64維表情係數的方向，以 `(新ratio－原ratio)×最後一欄權重` 調整已快取係數，保留同一音訊。渲染仍使用原27幀語意context，不是任意畫一條閉眼線。

探測固定66幀／2.64秒，7幀脈衝形狀 `[0.1,0.5,0.9,1,0.9,0.5,0.1]`；峰值0、2.5、4、6、8各生成一張模型畫格，每張純渲染約9～10秒，不含初始化。結果：

- 0為去除眨眼ratio貢獻的對照；不是原完整影片的逐像素副本。
- 2.5、4：眼睛更收合，但仍沒有自然完全閉上，其他表情已有變動。
- 6、8：眼睛更接近閉合，但嘴角、臉型、姿態明顯改變，8仍不是可直接採用的穩定完整閉眼。

大於1是超出官方預設脈衝範圍的研究用外插值，非官方推薦設定。眨眼ratio影響整組表情係數，不是只影響眼皮；不能為追求明顯閉眼而破壞已接受的嘴型與相似度。因此本輪**不採用高增益結果、不加入新的眨眼動畫**。探測只有五個峰值單格，沒有驗證連續開閉、所有過渡或後續長片的不規則間隔。

後續若要明顯閉眼，建議另評估同角色閉眼關鍵圖／局部眼皮動畫，或使用同角色眨眼參考短片，先看眼鏡及眼型再做短測。官方 `--ref_eyeblink` 是參考影片入口，但會替換64維表情參考資料，不能當成完全不影響其他表情的純眼皮開關。這些替代方法本輪尚未實作／驗證。長片可設不等間隔的眨眼並保留種子以便重現；具體頻率及幅度仍須看本角色，不把隨機等同自然。

## 重跑入口與產物

```powershell
# 獨立SadTalker環境已安裝，且私人基準片已存在：
.\work\sadtalker\venv\Scripts\python.exe scripts/stabilize-sadtalker-head.py --input outputs/round06/sadtalker-head-v2/ade_sadtalker_4_4s.mp4 --output outputs/新版本/head_stabilized.mp4
# 診斷入口需要原短測的verbose快取，輸出必須是新的work內ASCII目錄：
.\work\sadtalker\venv\Scripts\python.exe scripts/probe-sadtalker-blink.py --baseline outputs/round06/sadtalker-head-v2 --output work/sadtalker/new-blink-probe --frame 66 --gains 0 2.5 4 6 8
# 此比較頁建置器專為本次阿德探測檔名校準：
.\.venv\Scripts\python.exe scripts/build-sadtalker-stability-preview.py
```

實際探測由 `work/sadtalker/refine07/probe-blink.py` 執行，記錄在probe.json與probe-strong.json；後來整理成可攜腳本 `scripts/probe-sadtalker-blink.py`，此入口完成語法／help檢查，沒有為重驗包裝而再次渲染相同五張圖，也沒有乾淨換機驗證。未取得私人verbose快取的其他Agent不能只clone repo就重播本樣本，須先依原嘴短測流程產生自己的快取。

私人頁 `outputs/round07/index.html`，本機 `http://127.0.0.1:3028/`，只綁127.0.0.1並服務round07目錄。包含原／穩定MP4、五張研究用單格圖及技術報告；圖庫預設收合，避免把失敗探測誤當新成片。桌面繁體字已目視，兩影片載入、播放互斥、播放時鐘、0.5倍速、390px無水平溢出檢查通過；JS／HTTP錯誤及外部請求0。

回復方式：直接使用保留的第六輪原MP4，無須回退模型或依賴。新素材與影片都在忽略的work／outputs內，不新增GitHub公開素材例外。

## 本機「無配額」的精確說法

SadTalker本機對嘴端沒有服務商按次、字數或影片秒數的配額；它接收音訊，不直接將台詞唸成語音。TTSMaker等配音來源的免費額度、驗證碼及網站規則仍另計。現在短測入口限制3～5秒是本專案的測試保護，不是模型的商業配額。

硬體與環境相容後，速度、CPU／GPU占用及記憶體的確影響運作；但資源不足並不總是只變慢，也可能記憶體不足、磁碟不足或驅動不相容而失敗。總RAM／VRAM不能取代當下可用容量的檢查。GT710本輪走CPU成功，沒有據此證明其CUDA可用。

原始渲染會暫存整段預測畫格再堆疊，長度增加會提高記憶體與磁碟需求，不能保證任意長音訊一次完成。建議先短測、按句子切成短段、逐步增加長度並量測，之後驗證拼接及閉嘴停頓；本專案尚未完成自動長片分段拼接。製作時減少其他高負載程式；較強筆電仍先doctor，再驗證相容性、速度及角色品質，不能只把本機環境整份搬走。

## 額外安裝／操作踩坑

- 探測腳本首次載入Matplotlib嘗試寫使用者font cache而遭拒，並未造成模型失敗。後續將 `MPLCONFIGDIR` 指向work，不放寬使用者目錄權限。
- PowerShell中複雜 `python -c` 巢狀雙引號造成SyntaxError，未生成預定腳本。改以UTF8 `.py` 檔／apply_patch編輯並明確呼叫獨立Python，不繼續疊加shell跳脫字元；沒有因此修改任何角色素材。

今後每項功能依本紀錄結構保存：現象／基準→原因或推論→方法及參數→實際驗證→採用／放棄與限制→回復方式。不要只寫「已優化」或把執行成功等同品質驗收。
