# User Requirements

**專案名稱**：MaiAgent GenAI 自動回覆平台

## 使用者需求規格

| ID | Description |
| --- | --- |
| UR-01 | 提交訊息並獲得 AI 回覆 |
| Actor (Who) | 使用者 |
| 時機 (When) | 使用者在前端輸入訊息並送出時 |
| Act (What) | 系統接收訊息並生成回覆，回覆顯示於介面且可延續多輪對話 |
| Input、Output | Input：使用者訊息／Output：AI 回覆 |
| 備註 | 回覆透過非同步任務生成，需可回傳處理中/已完成/失敗狀態 |

| ID | Description |
| --- | --- |
| UR-02 | 檢視個人會話歷史（進入對話總頁） |
| Actor (Who) | 使用者 |
| 時機 (When) | 進入對話頁 |
| Act (What) | 預設載入由進到遠之會話歷史標題；若無既有會話則顯示空狀態。兩者皆顯示建立新會話按鈕 |
| Input、Output | Input：使用者 ID／Output：會話列表、總筆數 |
| 備註 | 支援分頁、排序（時間、來源） |

| ID | Description |
| --- | --- |
| UR-03 | 檢視單個既有會話歷史 |
| Actor (Who) | 使用者 |
| 時機 (When) | 點擊既有會話時 |
| Act (What) | 立即載入所選會話之歷史訊息與回覆，依時間序排列並定位至最新訊息 |
| Input、Output | Input：會話 ID／Output：會話內容 |
| 備註 | 支援分頁、排序（時間、來源） |

| ID | Description |
| --- | --- |
| UR-04 | 管理者檢視與管理對話紀錄 |
| Actor (Who) | 管理者（admin）、主管 |
| 時機 (When) | 登入後台時 |
| Act (What) | 檢視會話列表、篩選特定會話、查看會話細節|
| Input、Output | Input：查詢條件（時間、使用者、場景、關鍵字）／Output：對話列表與明細 |
| 備註 | 權限控管，不同角色可見範圍不同 |

| ID | Description |
| --- | --- |
| UR-05 | 主管檢視所屬人員對話紀錄 |
| Actor (Who) | 主管 |
| 時機 (When) | 主管登入後台或查詢特定期間時 |
| Act (What) | 僅能檢視其所屬部門/群組員工之會話與訊息內容 |
| Input、Output | Input：部門/群組、時間範圍、關鍵字／Output：符合條件之會話與訊息 |
| 備註 | 權限邊界由 RBAC 控制，不得越權讀取 |

| ID | Description |
| --- | --- |
| UR-06 | 管理場景設定 |
| Actor (Who) | 管理者（admin）、主管 |
| 時機 (When) | 需要調整業務規則或模型策略時 |
| Act (What) | 調整場景設定（模型、路由規則等） |
| Input、Output | Input：場景參數／Output：調整成功與否 |
| 備註 |  |

| ID | Description |
| --- | --- |
| UR-07 | 進階全文檢索對話 |
| Actor (Who) | 管理者 |
| 時機 (When) | 需快速定位特定內容時 |
| Act (What) | 以關鍵字與欄位條件搜尋對話內容 |
| Input、Output | Input：關鍵字、欄位條件／Output：符合的對話與訊息 |
| 備註 | 顯示前後文片段 |

| ID | Description |
| --- | --- |
| UR-08 | 多 AI 模型支援與策略切換 |
| Actor (Who) | 管理者 |
| 時機 (When) | 需切換模型或調整路由策略時 |
| Act (What) | 指定模型、設定路由或設定路由數值 |
| Input、Output | Input：現有路由列表、路由數值／Output：生效中的策略 |
| 備註 |  |

| ID | Description |
| --- | --- |
| UR-09 | 送出訊息時選擇場景 |
| Actor (Who) | 使用者（員工、主管、管理者） |
| 時機 (When) | 建立會話時 |
| Act (What) | 指定場景（目前 2 種，未來可新增），系統依場景套用對應 RAG 與模型策略 |
| Input、Output | Input：場景代號、訊息內容／Output：訊息狀態或 AI 回覆 |
| 備註 | |
