# 其他電腦的Agent入口

Repository：https://github.com/t92016/digital-human-avatar-workflow

Pages：https://t92016.github.io/digital-human-avatar-workflow/

請先clone repo，再在repo根目錄工作。這份公開入口適用Codex、OpenCode或能讀Markdown並使用本機工具的Agent；網站不會替你執行模型，也不包含這位使用者的登入設定。

1. 依序閱讀AGENTS.md、README.md、專案進度.md，再讀docs/另一台電腦與OpenCode操作指南.md及其他相關MD。專案進度是唯一最新交接來源。
2. 準備Python 3.12、Node.js 22以上、Git、uv；在Windows執行scripts/setup.ps1 -RenderTools，然後以專案.venv執行python -m avatar_workflow doctor。換機重跑，不沿用舊硬體結論。
3. 需要對嘴才執行scripts/setup-sadtalker-cpu.ps1。它另建Python 3.10.21、CPU torch2.6.0，下載config/sadtalker-models.json所列四個權重並核對SHA256。不要將TTS／生圖依賴混入這個環境。
4. 舊示範配音為已接受TTSMaker音檔；新的本機TTS與Qwen生圖尚未安裝／介接，不可宣稱clone後就有四類台灣聲音庫。已有使用者音檔可先沿用；新聲音需先試聽與驗收。
5. 新人物先取得照片／角色圖、已確認風格與服裝、用途、身體策略、主題／台詞、三模式、位置／大小；完整照片保留本人造型，只有指定才換卡通身體。不要把阿德座標套到任意人物。
6. 使用原有嘴巴的Q版頭像與已確認音訊，先run-sadtalker-head-test.py做3～5秒小樣，再做穩定、局部眨眼、肩頸與連續肘膝，最後接教材／字幕／完整音訊。不要循環短嘴型假裝新台詞。
7. 觀看三組完成MP4不需要私人素材；重建同角色需要另外取得使用者授權的圖層、眼皮、頭像與校準。公開影片不是可編輯rig；目前舊pack命令未涵蓋完整round11，按指南說明缺項，不假造已可一鍵重建。
8. 每次優化在對應docs記踩坑與驗證，驗收與下一步集中專案進度。完成後可讀skills/shutdown-sync/SKILL.md並執行scripts/shutdown-sync.ps1；Commit／Push只依當次使用者授權，模型／私人來源不提交。

完整命令、模型來源、版本及能力界線見[另一台電腦操作指南](docs/另一台電腦與OpenCode操作指南.md)。
