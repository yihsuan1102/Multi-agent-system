# API 安全性與效能設計規範

## API 層面設計

### API 安全性

#### JWT 認證機制 (djangorestframework-simplejwt)
使用 Access Token 有效期設為 15 分鐘，Refresh Token 有效期設為 7 天，確保在安全性與使用體驗間取得平衡。配置自動 Token 刷新機制。

#### 輸入驗證 (Django REST Framework Serializers)
對所有 API 輸入進行嚴格驗證，並過濾 HTML 標籤和特殊字符。使用 Serializer 的 `validate()` 方法實作自定義驗證邏輯，確保資料格式正確性。

#### 速率限制 (django-ratelimit)
使用者每分鐘最多 10 次請求，超過限制時回傳 429 狀態碼並提供重試建議時間。

### API 錯誤處理

#### 輸入驗證失敗 (400 Bad Request)
當 Serializer 驗證失敗時，回傳結構化錯誤訊息包含具體欄位錯誤資訊，並記錄錯誤模式用於後續安全分析。實作統一的錯誤格式 `{"error": "validation_failed", "details": {...}, "timestamp": "..."}`。

#### 身份驗證失敗 (401 Unauthorized)
- Token 過期、無效時立即回傳 401 狀態碼，並在回應標頭中提供刷新 Token 的提示。
- 使用者沒有執行操作的權限時，立即回傳 401 狀態碼。

#### 速率限制超過 (429 Too Many Requests)
回傳 `Retry-After` 標頭指示下次可請求的時間，通常設為 60 秒。
