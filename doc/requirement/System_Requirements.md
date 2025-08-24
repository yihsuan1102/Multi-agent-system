# System Requirements

**專案名稱**：MaiAgent GenAI 自動回覆平台

## 系統需求規格

| ID | Description |
| --- | --- |
| SR-01 | 資料儲存：會話與訊息結構 |
| Actor (Who) | 系統 |
| 時機 (When) | 建立/更新會話或訊息時 |
| Act (What) | 儲存會話（使用者、場景、狀態、時間）與訊息（方向、內容） |
| Input、Output | Input：結構化會話與訊息資料／Output：可查詢的會話資料 |
| 備註 |訊息全文檢索欄位 |

| ID | Description |
| --- | --- |
| SR-02 | 非同步任務：AI 生成流程 |
| Actor (Who) | 系統 |
| 時機 (When) | 使用者提交訊息後 |
| Act (What) | 派送任務至工作佇列，呼叫場景，等待場景回寫回覆與狀態 |
| Input、Output | Input：訊息、場景設定／Output：回覆 |
| 備註 | 如果派送任務至工作佇列狀態(失敗或成功)，需要 API 回傳提示使用者 |

| ID | Description |
| --- | --- |
| SR-03 | API：提交訊息 |
| Actor (Who) | 系統 |
| 時機 (When) | 呼叫 POST  |
| Act (What) | 驗證、排入任務、回傳受理狀態 |
| Input、Output | Input：訊息內容／Output：訊息/任務 ID、狀態 |
| 備註 | 產出 OpenAPI 規格；回傳標準錯誤碼 |

| ID | Description |
| --- | --- |
| SR-04 | API：查詢會話與訊息 |
| Actor (Who) | 系統 |
| 時機 (When) | 呼叫 GET |
| Act (What) | 支援篩選（使用者、場景、時間）、排序 |
| Input、Output | Input：查詢參數／Output：分頁結果與統計 |
| 備註 | 避免 N+1 查詢、使用選擇性載入與索引 |

| ID | Description |
| --- | --- |
| SR-05 | API：場景設定管理 |
| Actor (Who) | 系統 |
| 時機 (When) | 呼叫 PUT |
| Act (What) | 更新場景設定 |
| Input、Output | Input：設定 payload／Output：生效時間與結果 |
| 備註 | 目前提供 2 種場景，允許新增；生效範圍為群組底下人員 |

| ID | Description |
| --- | --- |
| SR-06 | 進階全文檢索 |
| Actor (Who) | 系統 |
| 時機 (When) | 觸發搜尋請求時 |
| Act (What) | 搜尋片段 |
| Input、Output | Input：關鍵字／Output：命中結果 |
| 備註 |  |

| ID | Description |
| --- | --- |
| SR-07 | 核心實體與 RBAC |
| Actor (Who) | 系統 |
| 時機 (When) | 存取受保護資源或執行管理操作時 |
| Act (What) | 定義 `使用者` 與 `場景` 兩個核心實體；使用者含三種角色：管理者（admin）、主管、員工；以 RBAC 控制資源存取 |
| Input、Output | Input：認證憑證、角色/群組資訊／Output：授權結果 |
| 備註 |  |
