---
name: shutdown-sync
description: 收尾本數位人專案時更新專案進度、檢查公開檔案及秘密；僅依使用者明確授權提交或推送。
---

# 專案收工

此技能隨repo提供，供Codex、OpenCode或能讀Markdown的Agent使用；不依賴這台電腦的全域設定。

1. 以repo根目錄為工作目錄，依AGENTS閱讀README與專案進度；將本階段成果、驗證、限制與下一位Agent第一步集中更新「專案進度.md」。不另建交接文件。
2. 執行 `scripts/shutdown-sync.ps1`，預設只掃描Git候選檔與記錄收工時間。公開影片限config/publication.json及各示範manifest的清單；模型、原始照片、私人圖集、環境及憑證不提交。
3. 掃描失敗時依報告檔名處理，報告不印出秘密。不要用忽略掃描或force-add私人來源來繞過失敗；保留使用者其他變更。
4. 使用者已明確要求commit／push才傳入 `-Commit`／`-Push`。已有本次明確授權則沿用，不重問；推送前確認遠端及已掃描的暫存清單。公開發布另核對具體允許素材。
5. chezmoi僅查看status；不複製Codex auth、OpenCode設定或其他帳密。最後回報實際完成的提交／推送／Pages網址及尚缺項目。

```powershell
.\scripts\shutdown-sync.ps1
# 僅在使用者已授權時：
.\scripts\shutdown-sync.ps1 -Commit -Push -Message 'chore: sync project progress'
```

操作與模型入口見 [另一台電腦指南](../../docs/另一台電腦與OpenCode操作指南.md)。
