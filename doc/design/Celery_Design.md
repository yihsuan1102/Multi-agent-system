#  Celery 安全性與效能設計規範

## Celery 層面設計

#### broker 數量一個

### Celery 安全性

#### Broker SSL 加密
Redis Broker 使用 TLS 1.3 加密連線，配置憑證驗證和最小加密強度為 AES-256。設定連線字串為 `rediss://` 協定，並使用 mkcert 自簽憑證。

### Celery 效能

#### 連線池管理
Redis 連線池設定最大連線數為 20，最小保持連線數為 5，連線超時時間為 30 秒。Worker 進程數設定為 CPU 核心數的 2 倍，每個 Worker 最大任務數限制為 10 後自動重啟防止記憶體洩漏。

### Celery 錯誤處理

#### Broker 連線失敗
實作指數退避重試機制，初始延遲 1 秒，最大延遲 60 秒，最多重試 5 次。連線失敗時自動切換到備用 Broker。

#### Worker 超時錯誤 (requests.exceptions.Timeout)
設定 LLM API 請求超時為 30 秒，超時後自動重試最多 3 次，每次重試間隔 5 秒。

#### 外部 LLM API 錯誤回應
- **401 Unauthorized**: 立即停止任務並記錄 API Key 狀態，不進行重試
- **429 Rate Limited**: 使用指數退避策略重試，初始延遲 2 秒，最大延遲 300 秒，最多重試 5 次
- **5xx Server Error**: 立即重試 1 次，若仍失敗則延遲 10 秒後最多重試 3 次
- **503 Service Unavailable**: 等待 60 秒後重試，最多重試 2 次

#### Response Parsing Error
當 LLM API 回傳格式異常時，記錄原始回應內容並回傳預設錯誤訊息給使用者。實作回應格式驗證機制，解析失敗的任務標記為需人工處理，避免無限重試消耗資源。


