# 台北一日遊 Plugin (Taipei Day Trip)

Codex plugin（Agent Plugins 可攜格式）：搜尋台北市景點並預訂一日遊導覽行程。

## 內容
`plugin.json`：可攜 plugin manifest（name: taipei-day-trip）
`mcp.json`：Taipei Day Trip MCP 伺服器設定（remote streamable-http，金鑰以環境變數帶入）
`skills/booking/SKILL.md`：預定流程 Skill

## 使用前設定
1. 登入台北一日遊網站（線上：http://43.206.8.196:8000/）→ 會員中心 → 產生金鑰，複製金鑰。
2. 將金鑰設為環境變數 `TAIPEI_MCP_TOKEN`：
   - Codex CLI：在啟動 codex 的同一個終端機執行
     `export TAIPEI_MCP_TOKEN=你的金鑰`
   - ChatGPT Desktop（macOS）：執行 `launchctl setenv TAIPEI_MCP_TOKEN 你的金鑰`，再完全重開 App
3. `mcp.json` 的 `bearer_token_env_var` 已指向 `TAIPEI_MCP_TOKEN`，Codex 會自動帶上 Authorization 標頭，金鑰不需寫進任何檔案。

## 載入與觸發
- Codex CLI：於專案根目錄 `codex plugin marketplace add ./`，再啟動 `codex`。
- ChatGPT Desktop：於 Plugins 介面啟用本 plugin。
- 觸發：輸入「預訂台北一日遊行程」，依提示輸入關鍵字、景點編號、日期、時段即可完成預訂。