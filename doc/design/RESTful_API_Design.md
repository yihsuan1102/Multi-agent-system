# MaiAgent GenAI 自動回覆平台 - RESTful API 設計文件

## 概述

本文件詳細說明 MaiAgent GenAI 自動回覆平台的 RESTful API 設計，包含7支核心API，支援用戶訊息提交、會話記錄查詢、對話管理及場景設定等功能。所有API設計遵循 RESTful 原則，並與資料庫設計保持一致。

## API 概覽

| 編號 | 功能描述 | HTTP 方法 | URI |
|------|----------|-----------|-----|
| 1 | 提交用戶訊息給LLM | POST | `/api/v1/conversations/messages/` |
| 2 | 關鍵字搜尋對話 | GET | `/api/v1/conversations/search` |
| 3 | 顯示所有會話 | GET | `/api/v1/conversations` |
| 4 | 查詢特定會話 | GET | `/api/v1/conversations/{session_id}` |
| 5 | 刪除特定對話 | DELETE | `/api/v1/conversations/{session_id}` |
| 6 | 更新場景設定 | PUT | `/api/v1/scenarios/{scenario_id}` |
| 7 | 建立新場景設定 | POST | `/api/v1/scenarios` |

## 通用規範

### 認證方式
所有API都需要在Header中包含JWT Token：
```
Authorization: Bearer {jwt_token}
```


## API 詳細設計

### 1. 提交用戶訊息給LLM

**目的**：儲存訊息資料再將任務送到 Celery。支援自動建立新會話或使用現有會話。

**HTTP方法**：POST  
**URI**：`/api/v1/conversations/messages/`

**請求標頭**：
```
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**請求資料格式**：
```json
{
  "content": "用戶訊息內容",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",  // 可選，使用現有會話
  "scenario_id": "550e8400-e29b-41d4-a716-446655440100", // 可選，建立新會話時必填
  "llm_model_id": "550e8400-e29b-41d4-a716-446655440200" // 可選
}
```

**請求欄位說明**：
- `content` (string, 必填): 用戶訊息內容
- `session_id` (UUID, 可選): 現有會話ID，如提供則使用現有會話
- `scenario_id` (UUID, 條件必填): 場景ID，當 session_id 未提供時為必填，用於建立新會話
- `llm_model_id` (UUID, 可選): 指定使用的 LLM 模型

**API邏輯**：
1. 如果提供 `session_id`：驗證會話存在且用戶有權限，直接使用該會話
2. 如果未提供 `session_id`：使用 `scenario_id` 建立新會話，然後儲存訊息
3. 儲存成功後發送 Celery 任務處理訊息
4. 回傳會話ID和訊息詳情

**成功回應 (201 Created)**：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "role": "user",
    "content": "用戶訊息內容",
    "sequence_number": 1,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

**錯誤狀態碼及範例**：
- **400 Bad Request**: 請求資料格式錯誤
  ```json
  {
    "detail": "建立新對話時需要指定場景 ID"
  }
  ```
- **401 Unauthorized**: JWT 憑證無效或未提供身份驗證
- **403 Forbidden**: 無場景存取權或會話存取權
  ```json
  {
    "detail": "無場景存取權"
  }
  ```
- **404 Not Found**: 會話或場景不存在
  ```json
  {
    "detail": "會話不存在"
  }
  ```
- **500 Internal Server Error**: 資料庫操作失敗
  ```json
  {
    "detail": "資料庫操作失敗: [具體錯誤訊息]"
  }
  ```
- **503 Service Unavailable**: Celery 服務暫時不可用
  ```json
  {
    "detail": "訊息處理服務暫時不可用: [具體錯誤訊息]"
  }
  ```

---

### 2. 關鍵字搜尋對話

**目的**：根據關鍵字搜尋用戶有權限查看的對話記錄

**HTTP方法**：GET  
**URI**：`/api/v1/conversations/search`

**注意**：此API尚未完整實作，請參考API設計規範。

**錯誤狀態碼**：
- 400 Bad Request: 查詢參數格式錯誤或未通過 Serializers 驗證
- 401 Unauthorized: JWT 憑證無效或未提供身份驗證
- 403 Forbidden: 使用者 Role 沒有搜尋對話的權限
- 500 Internal Server Error: 伺服器遇到未預期的狀況
- 503 Service Unavailable: Elasticsearch 服務超載或系統維護中

---

### 3. 顯示所有會話

**目的**：根據用戶權限顯示可查看的所有會話列表

**HTTP方法**：GET  
**URI**：`/api/v1/conversations`

**查詢參數**：
- `page` (integer, 可選, 預設=1): 頁數
- `page_size` (integer, 可選, 預設=20): 每頁筆數
- `status` (string, 可選): 會話狀態篩選 (Active/Waiting/Replyed/Closed)
- `scenario_id` (UUID, 可選): 場景篩選
- `sort_by` (string, 可選, 預設=last_activity_at): 排序欄位
- `sort_order` (string, 可選, 預設=desc): 排序方向 (asc/desc)

**實際測試案例**：

**成功請求範例**：
```
GET /api/v1/conversations
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功回應 (200 OK)**：
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "title": "會話標題",
        "user": {
          "id": "f47ac10b-58cc-4372-a567-0e02b2c3d478",
          "username": "testuser",
          "name": "Test User",
          "first_name": "Test",
          "last_name": "User"
        },
        "scenario": {
          "id": "f47ac10b-58cc-4372-a567-0e02b2c3d477",
          "name": "測試場景",
          "type": "general",
          "description": "測試場景描述"
        },
        "started_at": "2025-08-26T10:00:00Z",
        "last_activity_at": "2025-08-26T10:30:00Z",
        "status": "Active",
        "message_count": 2
      }
    ],
    "filters": {
      "available_statuses": ["Active", "Waiting", "Replied", "Closed"],
      "available_scenarios": [
        {
          "id": "f47ac10b-58cc-4372-a567-0e02b2c3d477",
          "name": "測試場景"
        }
      ]
    }
  },
  "message": "會話列表取得成功"
}
```

**錯誤請求範例**：
```
GET /api/v1/conversations?page=invalid
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**錯誤回應 (400 Bad Request)**：
```json
{
  "detail": "查詢參數格式錯誤或未通過 Serializers 驗證"
}
```

**無認證請求範例**：
```
GET /api/v1/conversations
```

**錯誤回應 (401 Unauthorized)**：
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**無群組權限請求範例**：
```
GET /api/v1/conversations
Authorization: Bearer [無群組用戶的JWT]
```

**錯誤回應 (403 Forbidden)**：
```json
{
  "detail": "使用者 Role 沒有查看會話的權限"
}
```

**錯誤狀態碼**：
- 400 Bad Request: 查詢參數格式錯誤或未通過 Serializers 驗證
- 401 Unauthorized: JWT 憑證無效或未提供身份驗證
- 403 Forbidden: 使用者 Role 沒有查看會話的權限
- 500 Internal Server Error: 伺服器遇到未預期的狀況
- 503 Service Unavailable: 資料庫服務超載或系統維護中

---

### 4. 查詢特定會話

**目的**：取得特定會話的詳細資訊，包含所有訊息記錄

**HTTP方法**：GET  
**URI**：`/api/v1/conversations/{session_id}`

**路徑參數**：
- `session_id` (UUID): 會話唯一識別碼

**查詢參數**：
- `include_messages` (boolean, 可選, 預設=true): 是否包含訊息列表
- `message_limit` (integer, 可選, 預設=100): 訊息數量限制
- `message_offset` (integer, 可選, 預設=0): 訊息偏移量

**實際測試案例**：

**成功請求範例**：
```
GET /api/v1/conversations/f47ac10b-58cc-4372-a567-0e02b2c3d479
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功回應 (200 OK)**：
```json
{
  "success": true,
  "data": {
    "session": {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "user": {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d478",
        "username": "testuser",
        "name": "Test User",
        "first_name": "Test",
        "last_name": "User"
      },
      "scenario": {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d477",
        "name": "測試場景",
        "type": "general",
        "description": "測試場景描述"
      },
      "messages": [
        {
          "id": "f47ac10b-58cc-4372-a567-0e02b2c3d480",
          "content": "第一條訊息",
          "role": "user",
          "sequence_number": 1,
          "parent_message_id": null,
          "created_at": "2025-08-26T10:01:00Z"
        },
        {
          "id": "f47ac10b-58cc-4372-a567-0e02b2c3d481",
          "content": "第二條訊息",
          "role": "assistant",
          "sequence_number": 2,
          "parent_message_id": "f47ac10b-58cc-4372-a567-0e02b2c3d480",
          "created_at": "2025-08-26T10:01:30Z"
        }
      ]
    }
  },
  "message": "會話詳情取得成功"
}
```

**無效參數請求範例**：
```
GET /api/v1/conversations/f47ac10b-58cc-4372-a567-0e02b2c3d479?message_limit=invalid
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**錯誤回應 (400 Bad Request)**：
```json
{
  "detail": "查詢參數格式錯誤或未通過 Serializers 驗證"
}
```

**會話不存在請求範例**：
```
GET /api/v1/conversations/00000000-0000-0000-0000-000000000000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**錯誤回應 (404 Not Found)**：
```json
{
  "detail": "會話不存在"
}
```

**錯誤狀態碼**：
- 400 Bad Request: 查詢參數格式錯誤或未通過 Serializers 驗證
- 401 Unauthorized: JWT 憑證無效或未提供身份驗證
- 403 Forbidden: 使用者 Role 沒有查看該會話的權限
- 404 Not Found: 會話不存在
- 500 Internal Server Error: 伺服器遇到未預期的狀況
- 503 Service Unavailable: 資料庫服務超載或系統維護中

---

### 5. 刪除特定對話

**目的**：刪除指定的會話及其所有相關訊息

**HTTP方法**：DELETE  
**URI**：`/api/v1/conversations/{session_id}`

**路徑參數**：
- `session_id` (UUID): 會話唯一識別碼

**請求標頭**：
```
Authorization: Bearer {jwt_token}
```

**實際測試案例**：

**成功請求範例**：
```
DELETE /api/v1/conversations/f47ac10b-58cc-4372-a567-0e02b2c3d479
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功回應 (200 OK)**：
```json
{
  "success": true,
  "data": {
    "deleted_session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "deleted_messages_count": 2,
    "deletion_timestamp": "2025-08-26T12:00:00Z"
  },
  "message": "會話刪除成功"
}
```

**刪除不存在會話請求範例**：
```
DELETE /api/v1/conversations/00000000-0000-0000-0000-000000000000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**錯誤回應 (404 Not Found)**：
```json
{
  "detail": "會話不存在"
}
```

**錯誤狀態碼**：
- 401 Unauthorized: JWT 憑證無效或未提供身份驗證
- 403 Forbidden: 使用者沒有刪除該會話的權限
- 404 Not Found: 會話不存在
- 500 Internal Server Error: 伺服器遇到未預期的狀況
- 503 Service Unavailable: 資料庫服務超載或系統維護中

---

### 6. 更新場景設定

**目的**：更新已存在場景的配置資訊

**HTTP方法**：PUT  
**URI**：`/api/v1/scenarios/{scenario_id}`

**路徑參數**：
- `scenario_id` (UUID): 場景唯一識別碼

**請求標頭**：
```
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**注意**：此API尚未完整實作，請參考API設計規範。

**錯誤狀態碼**：
- 400 Bad Request: 請求資料格式錯誤或未通過 Serializers 驗證
- 401 Unauthorized: JWT 憑證無效或未提供身份驗證
- 403 Forbidden: 使用者 Role 沒有修改該場景的權限
- 404 Not Found: 場景不存在
- 500 Internal Server Error: 伺服器遇到未預期的狀況
- 503 Service Unavailable: 資料庫服務超載或系統維護中

---

### 7. 建立新場景設定

**目的**：建立新的對話場景配置

**HTTP方法**：POST  
**URI**：`/api/v1/scenarios`

**請求標頭**：
```
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**注意**：此API尚未完整實作，請參考API設計規範。

**錯誤狀態碼**：
- 400 Bad Request: 請求資料格式錯誤或未通過 Serializers 驗證
- 401 Unauthorized: JWT 憑證無效或未提供身份驗證
- 403 Forbidden: 使用者 Role 沒有建立場景的權限
- 500 Internal Server Error: 伺服器遇到未預期的狀況
- 503 Service Unavailable: 資料庫服務超載或系統維護中

## 權限控制

### API權限對應

| API | 管理人員 | 主管 | 員工 | 所需權限 |
|-----|----------|------|------|----------|
| 1. 提交訊息 | ✓ | ✓ | ✓ | send_message_to_scenario |
| 2. 搜尋對話 | 全部對話 | 群組對話 | 個人對話 | search_*_conversations |
| 3. 顯示會話 | 全部會話 | 群組會話 | 個人會話 | view_*_conversations |
| 4. 查詢會話 | 全部會話 | 群組會話 | 個人會話 | view_*_conversations |
| 5. 刪除對話 | ✓ | 群組內 | 僅自己 | 依角色權限 |
| 6. 場景管理 | ✓ | 群組場景 | ✗ | create_scenario, modify_scenario |

### 權限驗證流程

1. **身分驗證**：檢查JWT Token有效性
2. **角色權限**：根據 django-role-permissions 用戶角色檢查操作權限


## 效能考量

### 分頁建議
- 預設每頁20筆
- 最大每頁100筆
- 使用offset-limit分頁機制

### 併發控制
- 訊息提交使用樂觀鎖定
- 場景更新使用版本控制
- 會話狀態使用原子性更新

## 安全考量

### 資料驗證
- 所有輸入資料進行格式驗證


### 存取控制
- 基於角色的存取控制 (RBAC)
- 群組邊界隔離
