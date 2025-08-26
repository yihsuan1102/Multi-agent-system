# MaiAgent ChatBot 實作計畫

## 專案概述

基於 Vercel AI Chatbot 模板，實作 GPT-like 聊天界面的 Django + React/HTMX 專案。整合 LangChain 提供 AI 對話功能，使用 Celery 處理非同步任務，並透過 Elasticsearch 提供搜尋功能。

## 總體目標

- 移植 Vercel AI Chatbot 的 UI 元件到 Django 專案
- 實作 GPT-like 界面（左側會話列表、右側對話區域）
- 建立簡單的 RESTful API 提供 AI 回覆功能
- 使用 Docker 容器化整個開發環境
- 整合 LangChain 實作基礎對話功能

## 開發階段規劃

### 階段 1: 建立基礎設施
**目標**: 設置完整的 Docker 開發環境
**成功標準**: 所有服務正常啟動並可互相通訊
**測試**: 各服務健康檢查通過，資料庫連線正常
**狀態**: 已完成

#### 具體任務
- 更新 `docker-compose.local.yml` 新增 Elasticsearch 服務
- 配置 Elasticsearch 基礎設定（不使用 IK 分詞）
- 確保 PostgreSQL、Redis、Celery、Elasticsearch 服務正常運行
- 設置服務間網路連接和健康檢查
- 建立環境變數配置檔案

#### 技術規格
- Elasticsearch 8.x 版本，使用標準分析器
- 配置適當的記憶體限制和 JVM 設定
- 建立持久化 volume 保存資料

---

### 階段 2: 建立資料模型
**目標**: 實作完整的 Django 和 Elasticsearch 資料模型，建立測試資料
**成功標準**: 資料模型創建成功，資料同步機制正常運作，測試資料完備
**測試**: 資料庫遷移成功，Elasticsearch 索引建立正常，兩個測試場景資料完整
**狀態**: 未開始

#### 具體任務
**資料處理邏輯**：
- 實作 Django 模型：User（含 group_id）、Group、Scenario（含 config_json JSONB 欄位）、Session、Message、GroupScenarioAccess、ScenarioModel、LlmModel
- 建立 UUID 主鍵生成機制，確保所有主鍵使用 `uuid_generate_v4()`
- 實作模型間關聯查詢優化：User.group、Session.scenario、Message.session 使用 select_related
- 設計權限查詢邏輯：根據 user.group_id 篩選可存取的 scenarios
- 建立 Message 的序號自動遞增機制（按 session_id 分組）

**邏輯判斷**：
- Session 狀態轉換：Active → Waiting → Replyed → Closed
- 權限繼承：管理人員 group_id=NULL（不受群組限制），主管和員工受群組邊界約束
- Scenario 配置驗證：config_json 必須包含 prompt、llm、memory 三個基本配置
- GroupScenarioAccess 權限檢查：驗證使用者是否可存取特定場景

**Elasticsearch 同步邏輯**：
- Message 模型同步到 ES：每日 23:00 執行，只同步前一天的 messages
- 建立 ES Document 對應 Message 模型，包含 session.title、session.user.username、scenario.name 等關聯欄位
- 實作增量同步機制，避免重複同步已存在的資料

**測試資料規劃**：

**場景1：客服助理場景**
- Group: 「ABC科技公司」（id: test-group-abc）
- Users: 
  - 管理人員：admin_user（group_id=NULL）
  - 主管：supervisor_user（group_id=test-group-abc）
  - 員工：employee_user（group_id=test-group-abc）
- Scenario: 「客服助理」（id: test-scenario-customer-service）
  - config_json: OpenAI GPT-4, temperature=0.7, system prompt="你是專業客服助理"
- Sessions: 3個會話（每個角色各1個）
- Messages: 每個會話 6-8 條訊息（user/assistant 交替）

**場景2：技術支援場景**
- Group: 「XYZ軟體公司」（id: test-group-xyz）
- Users:
  - 主管：tech_supervisor（group_id=test-group-xyz）
  - 員工：tech_employee（group_id=test-group-xyz）
- Scenario: 「技術支援」（id: test-scenario-tech-support）
  - config_json: OpenAI GPT-4, temperature=0.5, system prompt="你是技術支援專家"
- Sessions: 2個會話
- Messages: 每個會話 4-6 條訊息

#### 技術規格
- **Django 套件**：使用 `django-elasticsearch-dsl` 版本 7.x
- **資料庫**：PostgreSQL UUID 擴展，建立複合索引 (session_id, sequence_number)
- **ES Mapping**：使用標準分析器
- **同步機制**：實作 Celery 定時任務 `sync_messages_to_elasticsearch`，使用 Django signals 觸發即時更新
- **資料驗證**：使用 JSONSchema 驗證 Scenario.config_json 格式
- **測試工具**：建立 Django management command `create_test_data` 生成測試資料
- **遷移腳本**：建立初始 Groups、Scenarios、測試使用者的資料遷移檔案

---

### 階段 3: 移植 UI 元件
**目標**: 從 Vercel AI Chatbot 提取並移植核心 UI 元件，實作 GPT-like 界面
**成功標準**: GPT-like 聊天界面在 Django 中正常顯示，基本交互功能正常，左側會話列表和右側對話區域完整
**測試**: 界面渲染正確，電腦螢幕尺寸上正常運作
**狀態**: 未開始

#### 具體任務
**UI 元件分析與移植**：
- 分析 Vercel AI Chatbot 的 components 目錄結構，提取核心組件：
  - Chat 容器組件（主要佈局）
  - Sidebar 組件（左側會話列表）
  - MessageList 組件（訊息顯示區域）
  - MessageBubble 組件（單條訊息氣泡）
  - InputArea 組件（輸入框和發送按鈕）
  - LoadingIndicator 組件（AI 思考中指示器）

**Django 模板轉換**：
- 將 React/Next.js 組件轉換為 Django 模板（.html）
- 保持 Tailwind CSS 樣式不變，確保視覺一致性
- 提取並適配 JavaScript 交互邏輯，但簡化非必要功能
- 建立組件化的 Django template includes 供重用

**GPT-like 界面佈局與交互**：
- 左側邊欄：會話列表（可收縮/展開）
  - 新建會話按鈕
  - 會話歷史列表（按時間排序）
  - 會話刪除功能
- 主要區域：對話界面
  - 頂部：當前場景名稱和設定
  - 中間：訊息捲動區域（自動捲到最新訊息）
  - 底部：輸入框和發送按鈕
- 電腦版設計：專注於桌面瀏覽器體驗，確保在常見螢幕尺寸（1920x1080、1366x768）正常運作

**交互功能實作**：
- 使用 HTMX 實現無刷新頁面更新
- Long Polling 機制：當 LLM 回覆準備完成時，前端透過 long polling 獲取 AI 回覆並即時顯示
- 輸入框 Enter 鍵發送，Shift+Enter 換行
- 會話列表即時更新（新會話、最新活動時間）
- AI 回覆等待時的載入狀態顯示
- 錯誤訊息顯示：前端能夠接收並顯示來自 Server 和 Celery 的 4XX/5XX 錯誤訊息，提供用戶友好的錯誤提示

#### 技術規格
- **前端技術選擇**：Django Templates + HTMX（主要選擇）
- **樣式框架**：整合既有 Tailwind CSS 配置，使用 @tailwindcss/typography 外掛
- **HTMX 配置**：
  - 使用 hx-post 發送訊息
  - 使用 hx-target 更新訊息列表
  - 使用 hx-swap 控制內容更新方式
  - 使用 hx-trigger 處理輸入事件
- **Long Polling 實作**：
  - 建立 `/api/v1/conversations/{session_id}/polling` 端點進行長輪詢
  - 前端發送訊息後開始 polling，等待 AI 回覆完成
  - 設定合理的 timeout（30-60秒），避免無限等待
  - 實作錯誤重試機制和狀態管理
- **URL 路由設計**：
  - `/chatbot/` - 主要聊天界面
  - `/chatbot/sessions/` - 會話列表 HTMX 端點
  - `/chatbot/sessions/<uuid>/` - 對話詳情 HTMX 端點
  - `/chatbot/messages/` - 訊息 CRUD HTMX 端點
- **靜態資源管理**：使用現有 Webpack 配置，建立新的 chatbot.js 和 chatbot.scss
- **組件文檔**：建立 `/templates/chatbot/components/` 目錄結構，包含使用範例和樣式指南

---

### 階段 4: 實作 RESTful API
**目標**: 建立完整的後端 API 支援前端功能，包含完整的錯誤處理機制
**成功標準**: 7 支 API 端點正常運作，錯誤處理完善，權限控制正確
**測試**: API 單元測試，驗證 API 能夠正常傳遞資料（POST GET PUT DELETE），錯誤處理機制正常
**狀態**: 未開始

#### 具體任務
**API 實作處理邏輯**：

**1. 提交訊息 API (POST /api/v1/conversations/{session_id}/messages)**
- 資料處理：
  1. 驗證 session_id 存在和 JWT 認證
  2. 先將使用者訊息記錄到資料庫
  3. 如果使用者選擇非預設 model，一併儲存 LlmModel 記錄
  4. 再將使用者訊息傳送到 Celery broker
- 邏輯判斷：
  - Session 狀態必須為 Active/Replyed 才可接受新訊息
  - 如果資料庫沒有成功記錄資料，回傳 4XX/5XX 錯誤訊息
  - 如果 Celery broker 沒有成功接收任務，回傳 4XX/5XX 錯誤訊息
  - 如果 broker 成功接收任務，回傳 201 狀態碼
- 狀態更新：Session 狀態更新為 Waiting，記錄 last_activity_at

**2. 搜尋對話 API (GET /api/v1/conversations/search)**
- 資料處理：使用 Elasticsearch 搜尋 Message.content，結合 Session 資訊
- 邏輯判斷：只搜尋使用者輸入之關鍵字
- 查詢優化：限制回傳筆數
- 分頁處理：支援 page/page_size 參數，預設每頁 20 筆

**3. 會話列表 API (GET /api/v1/conversations)**
- 資料處理：查詢 Sessions，載入 User、Scenario 關聯資訊
- 邏輯判斷：JWT 認證驗證，基本資料驗證
- 查詢優化：使用 select_related 減少 DB 查詢次數，按 last_activity_at 排序
- 篩選功能：支援按 status、scenario_id 篩選

**4. 會話詳情 API (GET /api/v1/conversations/{session_id})**
- 資料處理：查詢 Session 詳情和所有 Messages，按 sequence_number 排序
- 邏輯判斷：JWT 認證驗證，session_id 存在性檢查
- 分頁支援：支援 message_limit/message_offset 參數管理大量訊息

**5. 刪除會話 API (DELETE /api/v1/conversations/{session_id})**
- 資料處理：級連刪除 Session 和所有相關 Messages
- 邏輯判斷：JWT 認證驗證，session_id 存在性檢查
- 交易安全：使用資料庫交易確保一致性

**6-7. 場景管理 API (PUT/POST /api/v1/scenarios/)**
- 資料處理：驗證 config_json 格式（必須包含 prompt/llm/memory）
- 邏輯判斷：JWT 認證驗證，基本資料格式驗證
- JSON 驗證：實作 JSONSchema 驗證 config_json 格式正確性

**8. Long Polling API (GET /api/v1/conversations/{session_id}/polling)**
- 資料處理：透過 JWT 認證驗證使用者身份，檢查 session 存取權限
- Long Polling 邏輯：
  - 檢查 Session 狀態是否為 Replyed（AI 已回覆）
  - 如果狀態仍為 Waiting，持續等待最多 30-60 秒
  - 當 AI 回覆完成時立即返回最新的 assistant message
  - 如果超時仍無回覆，返回適當的狀態碼讓前端重新 polling
- 錯誤處理：處理 session 不存在、權限不足、超時等情況

**錯誤處理機制**：

**4xx 錯誤處理**：
- 400 Bad Request：資料格式錯誤、Serializer 驗證失敗，回傳詳細錯誤訊息
- 401 Unauthorized：JWT Token 無效或未提供，返回登入提示
- 403 Forbidden：權限不足，明確指出缺少哪種權限
- 404 Not Found：資源不存在，区分是 Session 還是 Scenario 不存在
- 429 Too Many Requests：限流觸發，提供重試時間建議

**5xx 錯誤處理**：
- 500 Internal Server Error：伺服器內部錯誤，記錄完整錯誤日誌
- 503 Service Unavailable：資料庫或 ES 服務不可用，提供重試建議
- 504 Gateway Timeout：上游服務逾時，特別針對 Celery 任務處理

#### 技術規格
- **框架選擇**：Django REST Framework 3.14+，使用 ViewSets 和 Serializers
- **認證機制**：所有 API 都要經過 JWT 認證，使用 `djangorestframework-simplejwt`
- **資料驗證**：使用 DRF Serializers 和 JSONSchema 驗證 config_json
- **分頁機制**：使用 DRF 內置 PageNumberPagination，預設 20 筆/頁，最大 100 筆/頁
- **查詢優化**：
  - 使用 select_related() 和 prefetch_related() 減少 DB 查詢
  - 建立 Redis 緩存常用查詢結果
  - 實作資料庫查詢索引優化
- **API 文檔**：使用 `drf-spectacular` 生成 OpenAPI/Swagger 文檔
- **錯誤回報**：整合 Django logging，建立統一錯誤回報格式
- **測試框架**：使用 pytest-django 和 DRF 的 APITestCase 進行 API 單元測試
  - 測試 API 能夠正常傳遞資料（POST GET PUT DELETE）
  - 測試錯誤處理機制（4XX/5XX 錯誤狀況）
  - 測試 JWT 認證機制
  - 測試資料驗證和序列化

#### API 列表
| 編號 | API 端點 | HTTP 方法 | 描述 | JWT 認證 |
|------|----------|-----------|------|----------|
| 1 | `/api/v1/conversations/{session_id}/messages` | POST | 提交訊息 | ✓ |
| 2 | `/api/v1/conversations/search` | GET | 搜尋對話 | ✓ |
| 3 | `/api/v1/conversations` | GET | 顯示會話列表 | ✓ |
| 4 | `/api/v1/conversations/{session_id}` | GET | 查詢會話詳情 | ✓ |
| 5 | `/api/v1/conversations/{session_id}` | DELETE | 刪除會話 | ✓ |
| 6 | `/api/v1/scenarios/{scenario_id}` | PUT | 更新場景 | ✓ |
| 7 | `/api/v1/scenarios` | POST | 建立場景 | ✓ |
| 8 | `/api/v1/conversations/{session_id}/polling` | GET | Long Polling | ✓ |

---

### 階段 5: 權限機制與場景管理
**目標**: 建立完整的權限機制，實作角色定義腳本和場景資料管理
**成功標準**: 權限系統正常運作，場景資料讀取正確，不同角色存取權限正確
**測試**: 簡單單元測試，驗證不同角色使用者存取範圍正確，權限檢查通過
**狀態**: 未開始

#### 具體任務
**權限系統設計**：
- 實作 django-role-permissions 整合，定義 3 個基本角色：admin、supervisor、employee
- 建立角色與操作權限對應表（參考 Operations_and_Permissions_Mapping.md）
- 實作群組邊界管理：一個使用者只能屬於一個群組，管理員 group_id=NULL
- 設計動態權限檢查機制：根據 user.role + user.group_id 決定存取範圍

**邏輯判斷與資料篩選**：
- 實作群組場景權限檢查：透過 GroupScenarioAccess 模型檢查群組是否可存取特定場景
- 實作階層式資料篩選：
  - 員工：只能看自己的 Sessions (user_id = current_user.id)
  - 主管：可看群組內所有 Sessions (user.group_id = current_user.group_id)
  - 管理員：可看所有 Sessions (無限制)
- 實作場景存取檢查：使用者只能使用群組已授權的場景

**角色定義腳本開發**：
- 建立 Django management command `setup_roles_and_permissions`
- 實作角色與權限的對應關係（根據 Operations_and_Permissions_Mapping.md）
- 建立測試用戶初始化腳本：建立 3 種角色的測試帳號
- 建立群組與場景授權腳本：自動給群組分配預設場景

**權限檢查實作**：
- 建立 DRF Permission Classes：`HasScenarioAccess`、`CanViewConversations`、`CanManageScenarios`
- 實作 View-level 權限裝飾器：`@require_permission('operation_name')`
- 實作 Model-level 權限檢查：在 QuerySet 中自動篩選用戶可存取的資料
- 建立權限錯誤統一處理：403 Forbidden 回應格式標準化

**權限管理界面**：
- 建立 Django Admin 整合：管理員可在 Admin 界面管理群組和權限
- 實作群組場景授權界面：主管可在前端界面管理群組內成員的場景存取權
- 建立權限檢查 API 端點：`GET /api/v1/users/permissions` 返回當前用戶權限列表

**場景資料管理**：
- 實作場景資料讀取功能：從 Scenario 模型的 config_json 欄位讀取場景配置
- 建立 JSON Schema 驗證 config_json 格式（必須包含 prompt 基本配置）
- 建立場景資料驗證機制，確保資料格式正確

#### 技術規格
- **權限框架**：使用 `django-role-permissions` 3.x 版本
- **權限存儲**：在 User 模型中直接存儲 role 和 group_id，避免過度複雜的多層關聯
- **DRF 整合**：建立自定 Permission Classes 繼承 BasePermission
- **群組管理**：使用 Django 內建 Group 模型的擴展版本
- **查詢優化**：
  - 使用 select_related('user__group', 'scenario') 減少權限檢查的 DB 查詢
  - 實作權限緩存機制，避免重複檢查
- **測試策略**：
  - 建立權限單元測試，測試所有角色的權限組合
  - 建立整合測試，模擬不同角色訪問 API 的情境
- **管理命令腳本**：
  - `setup_roles_and_permissions` - 初始化角色和權限
  - `create_test_users` - 建立測試用戶
  - `assign_group_scenarios` - 群組場景授權
- **安全考量**：
  - 實作權限升級防護：防止權限提升攻擊
  - 實作會話級權限檢查：每個 API 請求都要驗證權限
- **場景管理技術規格**：
  - **資料讀取**：從 Scenario.config_json 讀取場景配置資料
  - **資料驗證**：使用 JSONSchema 驗證配置格式
  - **資料格式**：config_json 包含 prompt 等基本配置資訊

---

### 階段 6: Celery 任務處理系統
**目標**: 建立基本的非同步任務處理系統，處理訊息記錄和資料同步
**成功標準**: 訊息處理任務穩定執行，錯誤處理機制完善，資料同步正常
**測試**: 簡單單元測試，驗證任務執行正常，錯誤重試機制正常
**狀態**: 未開始

#### 具體任務
**Celery 任務處理邏輯**：

**1. 訊息處理任務 (`process_message`)**
- 資料處理：接收 session_id 和 user_message_id，查詢 Session 和 Message 資訊
- 場景讀取：從 Session.scenario.config_json 讀取場景配置資料
- 模擬回覆：產生簡單的模擬 AI 回覆（可以是當前時間戳或預設回應）
- 狀態更新：保存 AI 回覆 Message，更新 Session 狀態為 Replyed

**2. ES 資料同步任務 (`sync_messages_to_elasticsearch`)**
- 定時執行：每日 23:00 自動同步前一天的 Message 資料
- 增量同步：只處理尚未同步的 Message，避免重複處理
- 資料轉換：將 Django Message 模型轉換為 ES Document 格式
- 驗證機制：同步後驗證 ES 中的資料正確性

**3. 系統監控任務 (`system_health_check`)**
- 服務狀態檢查：定時檢查 PostgreSQL、Redis、Elasticsearch 連線狀態
- Worker 狀態監控：檢查 Celery Worker 負載和健康狀態
- 告警機制：當服務不可用或過載時發送告警通知

**Worker 和 Broker 錯誤處理**（參考 Celery_Design.md）：

**Broker 連線錯誤處理**：
- 指數退避重試：初始延遲 1 秒，最大延遲 60 秒，最多重試 5 次
- 連線失敗時自動切換到備用 Broker（Redis 叢集模式）
- TLS 1.3 加密連線，使用 `rediss://` 協定，配置最小加密強度 AES-256

**LLM API 錯誤處理**：
- 401 Unauthorized：立即停止任務並記錄 API Key 狀態，不進行重試
- 429 Rate Limited：指數退避策略重試，初始延遲 2 秒，最大延遲 300 秒，最多重試 5 次
- 5xx Server Error：立即重試 1 次，若仍失敗則延遲 10 秒後最多重試 3 次
- 503 Service Unavailable：等待 60 秒後重試，最多重試 2 次
- 請求逾時：設定 30 秒逾時，逾時後自動重試最多 3 次，每次重試間隔 5 秒

**回應解析錯誤處理**：
- LLM API 回傳格式異常時，記錄原始回應內容並回傳預設錯誤訊息
- 實作回應格式驗證機制，解析失敗的任務標記為需人工處理
- 避免無限重試消耗資源，設定最大重試次數限制

**場景資料處理**：
- 場景讀取：從 Scenario.config_json 讀取場景配置資料
- 配置驗證：使用 JSONSchema 驗證 config_json 格式（包含 prompt 基本配置）
- 場景緩存：將場景配置資料緩存，避免重複讀取
- 簡單回覆：根據場景配置產生簡單的模擬回覆

#### 技術規格
**Celery 配置（參考 Celery_Design.md）**：
- **Broker 配置**：單一 Redis Broker，使用 TLS 1.3 加密，mkcert 自簽憑證
- **連線池管理**：Redis 連線池最大 20 連線，最小保持 5 連線，逾時 30 秒
- **Worker 配置**：Worker 進程數 = CPU 核心數 x 2，每個 Worker 最大任務數 10 後自動重啟
- **任務路由**：
  - AI 訊息處理：`ai_queue` (高優先級)
  - ES 資料同步：`sync_queue` (低優先級)
  - 系統監控：`monitor_queue` (中優先級)

**場景配置管理**：
- **場景讀取**：從資料庫讀取 Scenario.config_json 資料
- **配置緩存**：使用 Redis 緩存場景配置，提升讀取效能
- **模擬回覆**：根據場景設定產生簡單的回覆內容

**監控與日誌系統**：
- **任務狀態追蹤**：使用 Celery 內建 Result Backend 記錄任務狀態
- **錯誤日誌**：整合 Django logging，記錄所有任務錯誤詳細資訊
- **告警機制**：
  - Worker 離線或異常告警
  - 任務佇列過長告警

**測試與驗證**：
- **簡單單元測試**：使用 `celery.contrib.testing.worker` 測試框架，驗證任務基本功能

---

### 階段 7: 系統整合
**目標**: 整合所有組件實現完整 GPT-like 聊天平台
**成功標準**: 完整對話流程正常，基本功能運作正常
**測試**: 簡單單元測試，驗證系統整合正常
**狀態**: 未開始

#### 具體任務
**系統整合**：

**1. 前後端整合**
- UI 與 API 整合：連接移植的 Vercel AI Chatbot UI 元件與 Django REST API
- 實作完整對話流程：用戶發送訊息 → API 驗證權限 → 儲存 Message → 觸發 Celery 任務 → LangChain 處理 → AI 回覆
- 會話狀態管理：Active → Waiting → Replyed 的完整轉換，前端即時顯示狀態
- 即時搜尋功能：整合 Elasticsearch 全文搜尋，支援按角色篩選範圍

**2. 用戶體驗優化**
- 錯誤處理與提示：4xx/5xx 錯誤的用戶友好提示、網路連線錯誤的重試機制

#### 技術規格
**測試框架與工具**：
- **單元測試**：pytest-django + DRF APITestCase + factory_boy 生成測試資料
- **整合測試**：pytest + Docker Compose 搭建完整測試環境
- **端到端測試**：Playwright + Django LiveServerTestCase


**監控與日誌工具**：
- **監控系統**：Django 內建 Health Check + 自定的監控 API
- **日誌系統**：Django logging + structlog 結構化日誌
- **錯誤追蹤**：Sentry SDK 整合
- **效能分析**：Django Debug Toolbar + django-silk (僅開發環境)

**部署與環境管理**：
- **開發環境**：Docker Compose Local 配置，包含所有服務
- **測試環境**：獨立的 Docker Compose 配置，簡化非必要服務



## 技術棧

### 後端技術
- **框架**: Django 4.x + Django REST Framework
- **資料庫**: PostgreSQL 14+
- **搜尋引擎**: Elasticsearch 8.x（標準分析器）
- **任務佇列**: Celery + Redis
- **AI 框架**: LangChain（基礎配置）
- **容器化**: Docker + Docker Compose

### 前端技術
- **主要選擇**: Django Templates + HTMX
- **備用選擇**: Django + React
- **樣式框架**: Tailwind CSS
- **打包工具**: Webpack（現有配置）

### 開發工具
- **版本控制**: Git
- **代碼檢查**: Ruff + Black
- **測試框架**: pytest-django + factory_boy + Playwright
- **API 文檔**: drf-spectacular (OpenAPI/Swagger)
- **效能監控**: Django-silk (開發環境) + 自定監控 API (生產環境)
- **日誌系統**: Django logging + structlog 結構化日誌

---

## 注意事項

1. **遵循 CLAUDE.md 開發指導原則**：精簡優於複雜，游進式開發，最多嘗試 3 次後重新評估
2. **每個階段完成後更新狀態**：確保 IMPLEMENTATION_PLAN.md 中的狀態追蹤正確
3. **遇到問題時及時記錄和調整**：記錄失敗原因和解決方案，避免重複同樣錯誤
4. **保持代碼品質和可維護性**：每次提交都要通過 linter 和測試，沒有 TODO 留在代碼中
5. **注重安全性和效能考量**：實作完整的權限檢查和錯誤處理機制
6. **不使用 Flower**：使用自定的監控 API 和日誌系統進行 Celery 任務監控
7. **參考文件**：在實作過程中參考 doc/design/ 目錄下的設計文件
8. **錯誤回報機制**：API、Celery worker、broker 都需具備完整的錯誤回報和日誌記錄
9. **實作範圍**：只實作需求中必要的邏輯判斷和 CRUD 操作，避免過度設計
10. **測試資料管理**：在任務描述中列出所有測試資料和場景，確保測試覆蓋率