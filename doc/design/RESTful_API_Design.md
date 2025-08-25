# MaiAgent GenAI 自動回覆平台 - RESTful API 設計文件

## 概述

本文件詳細說明 MaiAgent GenAI 自動回覆平台的 RESTful API 設計，包含7支核心API，支援用戶訊息提交、會話記錄查詢、對話管理及場景設定等功能。所有API設計遵循 RESTful 原則，並與資料庫設計保持一致。

## API 概覽

| 編號 | 功能描述 | HTTP 方法 | URI |
|------|----------|-----------|-----|
| 1 | 提交用戶訊息給LLM | POST | `/api/v1/conversations/{session_id}/messages` |
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
- 400 Bad Request: 請求資料格式錯誤或未通過 Serializers 驗證
- 401 Unauthorized: JWT 憑證無效或未提供身份驗證
- 403 Forbidden: 使用者 Role 沒有使用該場景的權限
- 404 Not Found: 會話不存在
- 500 Internal Server Error: 伺服器遇到未預期的狀況
- 503 Service Unavailable: 伺服器、資料庫或 Celery 超載，或系統維護中

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
          "type": "general",
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
          "type": "general",
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
        "type": "general",
        "description": "協助客戶進行產品諮詢",
        "config_json": {
          "prompt": {
            "system": "你是一個專業的客服助理",
            "user_template": "客戶問題：{user_input}"
          },
          "llm": {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7
          },
          "memory": {
            "type": "buffer",
            "window": 10
          }
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

**請求資料格式**：
```json
{
  "name": "更新後的場景名稱",
  "description": "更新後的場景描述",
  "type": "general",
  "config_json": {
    "prompt": {
      "system": "你是一個專業的客服助理",
      "user_template": "客戶問題：{user_input}"
    },
    "llm": {
      "provider": "openai",
      "model": "gpt-4-turbo",
      "temperature": 0.8
    },
    "memory": {
      "type": "buffer",
      "window": 10
    }
  }
}
```

**請求欄位說明**：
- `name` (string, 可選): 場景名稱
- `description` (string, 可選): 場景描述
- `type` (string, 可選): 場景類型（如 LLMChain、SequentialChain、agent 等）
- `config_json` (object, 可選): 場景配置，僅包含 `prompt`、`llm`、`memory`

**成功回應 (200 OK)**：
```json
{
  "success": true,
  "data": {
    "scenario": {
      "id": "550e8400-e29b-41d4-a716-446655440100",
      "name": "更新後的場景名稱",
      "description": "更新後的場景描述",
      "type": "general",
      "config_json": {
        "prompt": {
          "system": "你是一個專業的客服助理",
          "user_template": "客戶問題：{user_input}"
        },
        "llm": {
          "provider": "openai",
          "model": "gpt-4-turbo",
          "temperature": 0.8
        },
        "memory": {
          "type": "buffer",
          "window": 10
        }
      },
      "created_at": "2024-01-01T09:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  },
  "message": "場景更新成功",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

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

**請求資料格式**：
```json
{
  "name": "新場景名稱",
  "description": "新場景描述",
  "type": "technical_support",
  "config_json": {
    "prompt": {
      "system": "你是一個專業的技術支援專家",
      "user_template": "技術問題：{user_input}"
    },
    "llm": {
      "provider": "openai",
      "model": "gpt-4",
      "temperature": 0.7
    },
    "memory": {
      "type": "buffer",
      "window": 10
    }
  }
}
```

**請求欄位說明**：
- `name` (string, 必填): 場景名稱
- `description` (string, 可選): 場景描述
- `type` (string, 可選, 預設="general"): 場景類型
- `config_json` (object, 必填): 場景配置，僅包含 `prompt`、`llm`、`memory`

**成功回應 (201 Created)**：
```json
{
  "success": true,
  "data": {
    "scenario": {
      "id": "550e8400-e29b-41d4-a716-446655440101",
      "name": "新場景名稱",
      "description": "新場景描述",
      "type": "technical_support",
      "config_json": {
        "prompt": {
          "system": "你是一個專業的技術支援專家",
          "user_template": "技術問題：{user_input}"
        },
        "llm": {
          "provider": "openai",
          "model": "gpt-4",
          "temperature": 0.7
        },
        "memory": {
          "type": "buffer",
          "window": 10
        }
      },
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  },
  "message": "場景建立成功",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

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
