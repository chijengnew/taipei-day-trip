# 台北一日遊 Plugin (Taipei Day Trip)

Codex plugin（Agent Plugins 可攜格式）：搜尋台北市景點並預定一日遊導覽行程。

## 內容
- `plugin.json`：可攜 plugin manifest（name: taipei-day-trip）
- `mcp.json`：Taipei Day Trip MCP 伺服器設定（remote streamable-http + Bearer 金鑰）
- `skills/booking/SKILL.md`：預定流程 Skill

## 使用前設定
1. 登入台北一日遊網站 → 會員中心 → 產生金鑰。
2. 將金鑰填入 `mcp.json` 的 `Authorization: Bearer` 欄位。

## 載入與觸發（Codex）
1. 將 `plugins/trip-plugin` 資料夾放進 Codex 專案。
2. 在 Codex session 執行 `/plugins` 瀏覽並啟用本 plugin。
3. 在輸入框輸入 `@taipei-day-trip 預定台北市一日遊行程` 觸發。