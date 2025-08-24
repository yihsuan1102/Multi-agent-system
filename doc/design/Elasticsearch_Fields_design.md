# Elasticsearch 會話檢索欄位設計文件

## 概述

本文件定義了 MaiAgent GenAI 自動回覆平台中，用於 Elasticsearch 全文會話關鍵字檢索的欄位設計。此設計支援管理人員進行跨使用者、跨時間範圍的對話內容檢索，並整合了系統的權限控制機制。

## 基礎必需欄位

| 欄位名稱 | 資料類型 | 用途 | 說明 |
|---------|---------|------|------|
| `session_id` | keyword | 會話識別 | 對應系統中的 Session ID，用於唯一識別會話 |
| `message_id` | keyword | 訊息識別 | 對應系統中的 Message ID，用於唯一識別訊息 |
| `user_id` | keyword | 使用者識別 | 查詢特定使用者的對話記錄 |
| `user_name` | text + keyword | 使用者名稱搜尋 | 支援全文搜尋和精確匹配，方便按使用者名稱檢索 |
| `message_content` | text | 訊息內容檢索 | 主要檢索目標，支援中文分詞的全文搜尋 |
| `created_at` | date | 訊息時間篩選 | 支援時間範圍查詢，格式：yyyy-MM-dd HH:mm:ss |
| `message_type` | keyword | 訊息類型區分 | 區分 user（使用者）、assistant（AI）、system（系統）訊息 |
| `group_id` | keyword | 群組權限控制 | 對應使用者所屬群組（公司），用於權限邊界控制 |
| `scenario_id` | keyword | 場景識別 | 對應使用的場景 ID，用於按場景分類檢索對話 |
| `status` | keyword | 會話狀態 | 會話當前狀態：Active（活躍）、Waiting（等待）、Replyed（已回覆）、Closed（已關閉） |

## 完整 Elasticsearch Mapping 配置

```json
{
  "mappings": {
    "properties": {
      "session_id": {
        "type": "keyword",
        "doc_values": true,
        "index": true
      },
      "message_id": {
        "type": "keyword",
        "doc_values": true,
        "index": true
      },
      "user_id": {
        "type": "keyword",
        "doc_values": true,
        "index": true
      },
      "user_name": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "message_content": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart",
        "highlight": {
          "max_analyzed_offset": 1000000
        }
      },
      "created_at": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
      },
      "message_type": {
        "type": "keyword",
        "doc_values": true
      },
      "group_id": {
        "type": "keyword",
        "doc_values": true,
        "index": true
      },
      "scenario_id": {
        "type": "keyword",
        "doc_values": true,
        "index": true
      },
      "status": {
        "type": "keyword",
        "doc_values": true
      }
    }
  },
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "ik_max_word": {
          "type": "ik_max_word"
        },
        "ik_smart": {
          "type": "ik_smart"
        }
      }
    },
    "max_result_window": 50000,
    "refresh_interval": "1s"
  }
}
```

## 索引策略說明

### 1. 欄位類型選擇

- **keyword**：用於精確匹配和聚合查詢的欄位（ID、狀態類型）
- **text**：用於全文搜尋的欄位（訊息內容、使用者名稱）
- **date**：時間欄位，支援時間範圍查詢

### 2. 中文分詞設定

- 使用 IK 分詞器支援中文全文檢索
- `ik_max_word`：索引時最大化分詞，提升召回率
- `ik_smart`：搜尋時智慧分詞，提升精確度


