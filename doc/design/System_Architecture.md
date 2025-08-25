# MaiAgent 系統架構圖

## 系統架構概述

本架構圖展示了 MaiAgent GenAI 自動回覆平台的核心系統架構，包含主要實體、資料儲存和資料流向。

## 架構圖

```mermaid
flowchart TB
 subgraph MaiAgent["MaiAgent"]
        Server["Server"]
        PostgreSQL["PostgreSQL"]
        Elasticsearch["Elasticsearch"]
        Celery["Celery"]
        UserData["使用者資料"]
        SessionData["會話資料"]
        MessageData["訊息資料"]
        ScenarioData["場景資料"]
        SearchIndex["搜尋索引"]
        TaskQueue["任務佇列"]
        TaskResult["任務結果"]
  end
    PostgreSQL -.-> UserData & SessionData & MessageData & ScenarioData
    Elasticsearch -.-> SearchIndex
    Celery -.-> TaskQueue & TaskResult
    Server -- 會話資料、會話查詢 --> PostgreSQL
    PostgreSQL -- AI回覆、會話列表、搜尋結果 --> Server
    Server -- 提交訊息 --> Celery
    Celery -- 任務狀態、AI回覆 --> Server
    Server -- 全文檢索 --> Elasticsearch
    Elasticsearch -- 搜尋結果 --> Server
    Server -- 訊息資料 --> Celery
    Celery -- 任務狀態 --> PostgreSQL
    PostgreSQL -- 訊息索引 --> Elasticsearch
    MaiAgent -- 會話資料、場景配置 --> LLMs
    LLMs -- AI回覆 --> MaiAgent

     UserData:::data
     SessionData:::data
     MessageData:::data
     ScenarioData:::data
     SearchIndex:::data
     TaskQueue:::data
     TaskResult:::data
    classDef default fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000
    classDef data fill:#f9f9f9,stroke:#000000,stroke-width:1px,color:#000000

```

## 架構說明

### 主要實體 (Entities)
- **MaiAgent**: 主要系統平台，包含四個核心組件
- **LLM**: 各種 LLMs


### MaiAgent 核心組件 (Components)
- **Server**: 應用伺服器，處理請求和回應協調
- **PostgreSQL**: 主要關聯式資料庫，儲存結構化資料
- **Elasticsearch**: 全文檢索引擎，提供進階搜尋功能
- **Celery**: 非同步任務佇列系統，處理 AI 生成任務

### 資料存儲 (Data)
- **使用者資料**: 使用者基本資訊與權限
- **會話資料**: 對話會話的基本資訊
- **訊息資料**: 對話訊息內容
- **場景資料**: AI 場景配置與設定
- **搜尋索引**: Elasticsearch 的全文檢索索引
- **任務佇列**: Celery 的非同步任務佇列
- **任務結果**: 任務執行結果與狀態
