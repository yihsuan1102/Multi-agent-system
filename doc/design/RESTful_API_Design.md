# MaiAgent GenAI 自動回覆平台 - RESTful API 設計文件

## 概述

本文件詳細說明 MaiAgent GenAI 自動回覆平台的 RESTful API 設計，包含6支核心API，支援用戶訊息提交、會話記錄查詢、對話管理及場景設定等功能。所有API設計遵循 RESTful 原則，並與資料庫設計保持一致。

## API 概覽

| 編號 | 功能描述 | HTTP 方法 | URI |
|------|----------|-----------|-----|
| 1 | 提交用戶訊息給LLM | POST | `/api/v1/conversations/{session_id}/messages` |
| 2 | 關鍵字搜尋對話 | GET | `/api/v1/conversations/search` |
| 3 | 顯示所有會話 | GET | `/api/v1/conversations` |
| 4 | 查詢特定會話 | GET | `/api/v1/conversations/{session_id}` |
| 5 | 刪除特定對話 | DELETE | `/api/v1/conversations/{session_id}` |
| 6a | 更新場景設定 | PUT | `/api/v1/scenarios/{scenario_id}` |
| 6b | 建立新場景設定 | POST | `/api/v1/scenarios` |

## 通用規範

### 認證方式
所有API都需要在Header中包含JWT Token：
```
Authorization: Bearer {jwt_token}
```

### 通用回應格式
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 錯誤回應格式
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "錯誤描述",
    "details": {}
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## API 詳細設計

### 1. 提交用戶訊息給LLM

**目的**：儲存訊息資料再將任務送到 Celery。

**HTTP方法**：POST  
**URI**：`/api/v1/conversations/{session_id}/messages`

**路徑參數**：
- `session_id` (UUID): 會話唯一識別碼

**請求標頭**：
```
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**請求資料格式**：
```json
{
  "content": "用戶訊息內容",
  "message_type": "user",
  "parent_message_id": "550e8400-e29b-41d4-a716-446655440000" // 可選，用於對話分支
}
```

**請求欄位說明**：
- `content` (string, 必填): 用戶訊息內容，對應Message表的content欄位
- `message_type` (string, 必填): 訊息類型，固定為"user"
- `parent_message_id` (UUID, 可選): 父訊息識別碼，用於建立訊息樹狀結構

**成功回應 (201 Created)**：
```json
{
  "success": true,
  "data": {
    "user_message": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "content": "用戶訊息內容",
      "message_type": "user",
      "sequence_number": 5,
      "created_at": "2024-01-01T12:00:00Z"
    },
    "assistant_message": {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "content": "AI 回應內容",
      "message_type": "assistant",
      "sequence_number": 6,
      "created_at": "2024-01-01T12:00:05Z"
    },
    "session_status": "Replyed"
  },
  "message": "訊息發送成功",
  "timestamp": "2024-01-01T12:00:05Z"
}
```

**錯誤狀態碼**：
- 400 Bad Request: 請求資料格式錯誤
- 401 Unauthorized: 認證失敗
- 403 Forbidden: 沒有使用該場景的權限
- 404 Not Found: 會話不存在
- 429 Too Many Requests: 請求過於頻繁
- 500 Internal Server Error: 資料庫錯誤
- 503 Service Unavailable: 資料庫暫時無法使用
- 504 Gateway Timeout: 資料庫交易執行超時

---

### 2. 關鍵字搜尋對話

**目的**：根據關鍵字搜尋用戶有權限查看的對話記錄

**HTTP方法**：GET  
**URI**：`/api/v1/conversations/search`

**查詢參數**：
- `q` (string, 必填): 搜尋關鍵字
- `page` (integer, 可選, 預設=1): 頁數
- `page_size` (integer, 可選, 預設=20): 每頁筆數
- `start_date` (string, 可選): 開始日期 (ISO 8601格式)
- `end_date` (string, 可選): 結束日期 (ISO 8601格式)

**請求範例**：
```
GET /api/v1/conversations/search?q=報價&page=1&page_size=10&start_date=2024-01-01T00:00:00Z
```

**成功回應 (200 OK)**：
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "產品報價諮詢",
        "scenario": {
          "id": "550e8400-e29b-41d4-a716-446655440100",
          "name": "客服助理",
          "description": "協助客戶進行產品諮詢"
        },
        "started_at": "2024-01-01T10:00:00Z",
        "last_activity_at": "2024-01-01T10:30:00Z",
        "status": "Closed",
        "message_count": 12,
        "matched_messages": [
          {
            "content": "請問貴公司產品的報價如何計算？",
            "created_at": "2024-01-01T10:05:00Z",
            "highlight": "請問貴公司產品的<mark>報價</mark>如何計算？"
          }
        ]
      }
    ],
    "pagination": {
      "current_page": 1,
      "page_size": 10,
      "total_pages": 5,
      "total_count": 47
    }
  },
  "message": "搜尋完成",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**錯誤狀態碼**：
- 400 Bad Request: 查詢參數格式錯誤
- 401 Unauthorized: 認證失敗
- 500 Internal Server Error: Elasticsearch服務錯誤或資料庫連線失敗
- 503 Service Unavailable: 搜尋服務暫時無法使用
- 504 Gateway Timeout: 搜尋查詢超時

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

**請求範例**：
```
GET /api/v1/conversations?page=1&page_size=15&status=Active&sort_by=started_at&sort_order=desc
```

**成功回應 (200 OK)**：
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "產品諮詢會話",
        "user": {
          "id": "550e8400-e29b-41d4-a716-446655440200",
          "username": "john_doe",
          "first_name": "John",
          "last_name": "Doe"
        },
        "scenario": {
          "id": "550e8400-e29b-41d4-a716-446655440100",
          "name": "客服助理",
          "description": "協助客戶進行產品諮詢"
        },
        "started_at": "2024-01-01T10:00:00Z",
        "last_activity_at": "2024-01-01T11:30:00Z",
        "status": "Active",
        "message_count": 8
      }
    ],
    "pagination": {
      "current_page": 1,
      "page_size": 15,
      "total_pages": 3,
      "total_count": 42
    },
    "filters": {
      "available_statuses": ["Active", "Waiting", "Replyed", "Closed"],
      "available_scenarios": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440100",
          "name": "客服助理"
        }
      ]
    }
  },
  "message": "會話列表取得成功",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**錯誤狀態碼**：
- 400 Bad Request: 查詢參數格式錯誤
- 401 Unauthorized: 認證失敗
- 500 Internal Server Error: 資料庫查詢錯誤或系統內部錯誤
- 503 Service Unavailable: 資料庫服務暫時無法使用

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

**請求範例**：
```
GET /api/v1/conversations/550e8400-e29b-41d4-a716-446655440000?include_messages=true&message_limit=50
```

**成功回應 (200 OK)**：
```json
{
  "success": true,
  "data": {
    "session": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "產品諮詢會話",
      "user": {
        "id": "550e8400-e29b-41d4-a716-446655440200",
        "username": "john_doe",
        "first_name": "John",
        "last_name": "Doe"
      },
      "scenario": {
        "id": "550e8400-e29b-41d4-a716-446655440100",
        "name": "客服助理",
        "description": "協助客戶進行產品諮詢",
        "langchain_config": {
          "model": "gpt-4",
          "temperature": 0.7
        }
      },
      "started_at": "2024-01-01T10:00:00Z",
      "last_activity_at": "2024-01-01T11:30:00Z",
      "status": "Active"
    },
    "messages": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "content": "您好，我想了解貴公司的產品",
        "message_type": "user",
        "sequence_number": 1,
        "parent_message_id": null,
        "created_at": "2024-01-01T10:01:00Z"
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "content": "您好！很高興為您介紹我們的產品。請問您對哪類產品比較感興趣？",
        "message_type": "assistant",
        "sequence_number": 2,
        "parent_message_id": "550e8400-e29b-41d4-a716-446655440001",
        "created_at": "2024-01-01T10:01:30Z"
      }
    ],
    "message_pagination": {
      "offset": 0,
      "limit": 50,
      "total_count": 8,
      "has_more": false
    }
  },
  "message": "會話詳情取得成功",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**錯誤狀態碼**：
- 400 Bad Request: 查詢參數格式錯誤
- 401 Unauthorized: 認證失敗
- 403 Forbidden: 沒有查看該會話的權限
- 404 Not Found: 會話不存在
- 500 Internal Server Error: 資料庫查詢錯誤或訊息載入失敗
- 503 Service Unavailable: 資料庫服務暫時無法使用

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

**成功回應 (200 OK)**：
```json
{
  "success": true,
  "data": {
    "deleted_session_id": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_messages_count": 12,
    "deletion_timestamp": "2024-01-01T12:00:00Z"
  },
  "message": "會話刪除成功",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**錯誤狀態碼**：
- 401 Unauthorized: 認證失敗
- 403 Forbidden: 沒有刪除該會話的權限
- 404 Not Found: 會話不存在
- 409 Conflict: 會話狀態不允許刪除 (例如：正在處理中)
- 500 Internal Server Error: 資料庫刪除操作失敗
- 503 Service Unavailable: 資料庫服務暫時無法使用

---

### 6a. 更新場景設定

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

**請求資料格式**：
```json
{
  "name": "更新後的場景名稱",
  "description": "更新後的場景描述",
  "langchain_config": {
    "model": "gpt-4-turbo",
    "temperature": 0.8,
    "max_tokens": 2000
  },
  "llm_config": {
    "provider": "openai",
    "api_version": "2024-02-01"
  },
  "prompt_template": {
    "system_prompt": "你是一個專業的客服助理",
    "user_prompt_template": "客戶問題：{user_input}",
    "context_template": "參考資訊：{context}"
  },
  "rag_config": {
    "enabled": true,
    "vector_store": "elasticsearch",
    "similarity_threshold": 0.7
  },
  "routing_weight": 1.5,
  "routing_priority": 1
}
```

**請求欄位說明**：
- `name` (string, 可選): 場景名稱
- `description` (string, 可選): 場景描述
- `langchain_config` (object, 可選): LangChain配置，對應Scenario表的langchain_config欄位
- `llm_config` (object, 可選): LLM模型配置，對應llm_config欄位
- `prompt_template` (object, 可選): 提示詞模板，對應prompt_template欄位
- `rag_config` (object, 可選): RAG策略配置，對應rag_config欄位
- `routing_weight` (decimal, 可選): 路由權重
- `routing_priority` (integer, 可選): 路由優先級

**成功回應 (200 OK)**：
```json
{
  "success": true,
  "data": {
    "scenario": {
      "id": "550e8400-e29b-41d4-a716-446655440100",
      "name": "更新後的場景名稱",
      "description": "更新後的場景描述",
      "langchain_config": {
        "model": "gpt-4-turbo",
        "temperature": 0.8,
        "max_tokens": 2000
      },
      "llm_config": {
        "provider": "openai",
        "api_version": "2024-02-01"
      },
      "prompt_template": {
        "system_prompt": "你是一個專業的客服助理",
        "user_prompt_template": "客戶問題：{user_input}",
        "context_template": "參考資訊：{context}"
      },
      "rag_config": {
        "enabled": true,
        "vector_store": "elasticsearch",
        "similarity_threshold": 0.7
      },
      "scenario_type": "general",
      "version": 2,
      "routing_weight": 1.5,
      "routing_priority": 1,
      "is_global": false,
      "created_by": "550e8400-e29b-41d4-a716-446655440200",
      "created_at": "2024-01-01T09:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  },
  "message": "場景更新成功",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**錯誤狀態碼**：
- 400 Bad Request: 請求資料格式錯誤
- 401 Unauthorized: 認證失敗
- 403 Forbidden: 沒有修改該場景的權限
- 404 Not Found: 場景不存在
- 422 Unprocessable Entity: 配置資料驗證失敗
- 500 Internal Server Error: 資料庫更新失敗或配置驗證系統錯誤
- 502 Bad Gateway: LangChain配置驗證服務無回應
- 503 Service Unavailable: 場景配置服務暫時無法使用

---

### 6b. 建立新場景設定

**目的**：建立新的對話場景配置

**HTTP方法**：POST  
**URI**：`/api/v1/scenarios`

**請求標頭**：
```
Content-Type: application/json
Authorization: Bearer {jwt_token}
```

**請求資料格式**：
```json
{
  "name": "新場景名稱",
  "description": "新場景描述",
  "langchain_config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1500
  },
  "llm_config": {
    "provider": "openai",
    "api_version": "2024-02-01"
  },
  "prompt_template": {
    "system_prompt": "你是一個專業的技術支援專家",
    "user_prompt_template": "技術問題：{user_input}",
    "context_template": "技術文檔：{context}"
  },
  "rag_config": {
    "enabled": false
  },
  "scenario_type": "technical_support",
  "routing_weight": 1.0,
  "routing_priority": 0,
  "is_global": false
}
```

**請求欄位說明**：
- `name` (string, 必填): 場景名稱
- `description` (string, 可選): 場景描述
- `langchain_config` (object, 必填): LangChain配置
- `llm_config` (object, 必填): LLM模型配置
- `prompt_template` (object, 必填): 提示詞模板
- `rag_config` (object, 可選): RAG策略配置
- `scenario_type` (string, 可選, 預設="general"): 場景類型
- `routing_weight` (decimal, 可選, 預設=1.0): 路由權重
- `routing_priority` (integer, 可選, 預設=0): 路由優先級
- `is_global` (boolean, 可選, 預設=false): 是否為全域場景

**成功回應 (201 Created)**：
```json
{
  "success": true,
  "data": {
    "scenario": {
      "id": "550e8400-e29b-41d4-a716-446655440101",
      "name": "新場景名稱",
      "description": "新場景描述",
      "langchain_config": {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1500
      },
      "llm_config": {
        "provider": "openai",
        "api_version": "2024-02-01"
      },
      "prompt_template": {
        "system_prompt": "你是一個專業的技術支援專家",
        "user_prompt_template": "技術問題：{user_input}",
        "context_template": "技術文檔：{context}"
      },
      "rag_config": {
        "enabled": false
      },
      "scenario_type": "technical_support",
      "version": 1,
      "routing_weight": 1.0,
      "routing_priority": 0,
      "is_global": false,
      "created_by": "550e8400-e29b-41d4-a716-446655440200",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  },
  "message": "場景建立成功",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**錯誤狀態碼**：
- 400 Bad Request: 請求資料格式錯誤
- 401 Unauthorized: 認證失敗
- 403 Forbidden: 沒有建立場景的權限
- 409 Conflict: 場景名稱已存在
- 422 Unprocessable Entity: 配置資料驗證失敗
- 500 Internal Server Error: 資料庫插入失敗或配置驗證系統錯誤
- 502 Bad Gateway: LangChain配置驗證服務無回應
- 503 Service Unavailable: 場景建立服務暫時無法使用

## 常見 5XX 伺服器錯誤

### 5XX 錯誤概述

5XX系列錯誤表示伺服器端發生錯誤，無法完成有效的請求。在MaiAgent平台中，這些錯誤通常與以下系統組件相關：

### 主要5XX錯誤類型

#### 500 Internal Server Error (內部伺服器錯誤)
**常見情境**：
- 資料庫連線中斷或查詢失敗
- LLM服務呼叫異常
- 配置驗證系統錯誤
- Django應用程式內部異常
- Celery任務執行失敗

**錯誤回應範例**：
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "系統內部錯誤，請稍後再試",
    "details": {
      "error_id": "550e8400-e29b-41d4-a716-446655440999",
      "component": "database",
      "trace_id": "abc123"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 502 Bad Gateway (閘道錯誤)
**常見情境**：
- LangChain服務無回應
- 外部LLM API（OpenAI、Claude等）無法連接
- 配置驗證服務異常
- 微服務間通訊失敗

**錯誤回應範例**：
```json
{
  "success": false,
  "error": {
    "code": "BAD_GATEWAY",
    "message": "外部服務暫時無法使用",
    "details": {
      "upstream_service": "langchain",
      "retry_after": 30
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 503 Service Unavailable (服務無法使用)
**常見情境**：
- Celery任務佇列過載
- 資料庫服務暫停維護
- Elasticsearch服務重啟
- 系統負載過高，暫時停止服務
- LLM API配額已達上限

**錯誤回應範例**：
```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "服務暫時無法使用，請稍後重試",
    "details": {
      "retry_after": 60,
      "reason": "high_load",
      "estimated_recovery": "2024-01-01T12:05:00Z"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 504 Gateway Timeout (閘道超時)
**常見情境**：
- LLM回應時間超過設定閾值
- Celery任務執行超時
- 複雜搜尋查詢超時
- 資料庫查詢執行時間過長

**錯誤回應範例**：
```json
{
  "success": false,
  "error": {
    "code": "GATEWAY_TIMEOUT",
    "message": "請求處理超時，請重新嘗試",
    "details": {
      "timeout_duration": "30s",
      "operation": "llm_response",
      "suggestion": "請簡化您的問題或稍後重試"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 5XX錯誤處理策略

#### 伺服器端監控
1. **錯誤追蹤**：
   - 所有5XX錯誤自動記錄到稽核日誌
   - 包含錯誤ID、追蹤ID、堆疊資訊
   - 整合告警系統

2. **健康檢查**：
   - 定期檢查各服務狀態
   - 監控回應時間和錯誤率
   - 自動故障轉移機制

### API別5XX錯誤對應

| API | 500 | 502 | 503 | 504 |
|-----|-----|-----|-----|-----|
| 1. 提交訊息 | 資料庫錯誤 | LLM服務異常 | Celery過載 | LLM超時 |
| 2. 搜尋對話 | 系統錯誤 | - | ES服務停止 | 查詢超時 |
| 3. 顯示會話 | 資料庫錯誤 | - | DB維護 | - |
| 4. 查詢會話 | 載入失敗 | - | DB服務停止 | - |
| 5. 刪除對話 | 刪除失敗 | - | DB維護 | - |
| 6. 場景管理 | 驗證錯誤 | 配置服務異常 | 服務維護 | - |

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
2. **角色權限**：根據用戶角色檢查操作權限
3. **資源權限**：檢查是否有存取特定資源的權限
4. **群組邊界**：非管理人員僅能操作群組內資源

## 效能考量

### 快取策略
- 場景配置快取 (30分鐘)
- 用戶權限快取 (15分鐘)
- 搜尋結果快取 (5分鐘)

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
- SQL注入防護
- XSS攻擊防護

### 存取控制
- 基於角色的存取控制 (RBAC)
- 群組邊界隔離
- 敏感資料遮罩

### 稽核日誌
- 記錄所有API呼叫
- 追蹤權限變更
- 監控異常行為

## 總結

本RESTful API設計提供了完整的MaiAgent平台核心功能，包含：

1. **對話管理**：支援訊息提交、會話查詢與刪除
2. **搜尋功能**：提供關鍵字搜尋與篩選功能  
3. **場景管理**：支援場景配置的建立與更新
4. **權限控制**：基於角色的細粒度權限管理
5. **安全保障**：完整的認證、授權與稽核機制

所有API設計都與資料庫設計保持一致，確保系統的完整性與可維護性。
