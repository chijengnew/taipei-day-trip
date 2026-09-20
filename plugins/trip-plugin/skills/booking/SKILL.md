name: taipei-day-trip-booking
description:
預定台北一日遊導覽行程。
透過 Taipei Day Trip MCP 的搜尋與預定工具完成預定。

# 台北一日遊預定流程

當使用者想預定台北一日遊行程時，依序完成以下步驟。
本流程會用到 Taipei Day Trip MCP 伺服器的兩個工具：
search_attractions（搜尋台北市景點）
add_to_cart（預定景點導覽行程）

## 步驟 1：詢問搜尋關鍵字
詢問使用者想去的景點關鍵字或捷運站名，例如「北投」或「中正紀念堂」。

## 步驟 2：搜尋景點
以使用者提供的關鍵字，呼叫 search_attractions 工具（參數 keyword）。

## 步驟 3：列出景點
將搜尋結果列給使用者選擇，每個景點至少顯示編號（id）與名稱（name）。
若回傳 error，告知搜尋失敗並請使用者重新輸入關鍵字。

## 步驟 4：詢問預定資訊
請使用者以自然語言提供：景點編號、日期、時段（上午 / 下午）。
提醒使用者：上午為 NT$2,000；下午為 NT$2,500。

## 步驟 5：轉換為預定格式
務必把使用者的輸入轉換為工具所需格式：
attraction_id：整數，例如 16
date：YYYY-MM-DD，例如「九月二十號」轉為 2026-09-20（未提年份以今年推算）
time：上午 / 早上 / morning 轉為 "morning"；下午 / afternoon 轉為 "afternoon"
price：morning 為 2000；afternoon 為 2500

## 步驟 6：建立預定
呼叫 add_to_cart 工具，帶入 attraction_id、date、time、price 四個參數。

## 步驟 7：顯示付款連結
若回傳 ok，將回傳 message 中的付款頁面連結顯示給使用者，請他前往完成付款。
若回傳 error，告知預定失敗，請確認 MCP 設定是否已填入有效金鑰。