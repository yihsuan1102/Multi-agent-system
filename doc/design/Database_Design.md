# MaiAgent GenAI 自動回覆平台 - 資料庫設計文件

## 概述

本文件詳細說明 MaiAgent GenAI 自動回覆平台的資料庫設計，基於使用者權限與場景選擇機制的需求，採用 PostgreSQL 作為主要資料庫，設計了實體關係模型以支援階層式權限控制、群組管理、場景配置與會話管理等核心功能。


## 資料庫技術架構

- **主要資料庫**：PostgreSQL 14+
- **權限管理**：django-role-permissions + group
- **權限邊界**：群組 = 公司，角色 = 職位

## 核心實體設計

### 1. 使用者管理實體

#### 1.1 User (使用者表)

**用途**：儲存系統使用者的基本資訊

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 使用者唯一識別碼 |
| username | VARCHAR | 150 | UK, NOT NULL | - | 使用者名稱 |
| email | VARCHAR | 254 | UK, NOT NULL | - | 電子郵件地址 |
| first_name | VARCHAR | 150 | - | '' | 名字 |
| last_name | VARCHAR | 150 | - | '' | 姓氏 |
| group_id | UUID | - | FK | NULL | 所屬群組（管理人員可為 NULL） |
| password | VARCHAR | 128 | NOT NULL | - | 密碼雜湊值 |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |
| updated_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 更新時間 |

**備註**：
- 群組代表公司或組織邊界
- 群組場景權限決定成員的場景存取權限
- 直接在 User 表中儲存 role_id 和 group_id
- 一個使用者只能有一個角色和一個群組
- 管理人員的 group_id 為 NULL，表示不受群組限制


### 2. 群組管理實體

#### 2.1 Group (群組表) - 代表公司

**用途**：儲存公司/組織資訊，每個群組代表一個獨立的公司實體

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 群組唯一識別碼 |
| name | VARCHAR | 255 | NOT NULL | - | 公司名稱 |
| description | TEXT | - | - | '' | 公司描述 |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |
| updated_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 更新時間 |



### 3. 場景管理實體

#### 3.1 Scenario (場景表)

**用途**：儲存 LangChain 場景配置與設定

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 場景唯一識別碼 |
| name | VARCHAR | 255 | UK, NOT NULL | - | 場景名稱 |
| type | VARCHAR | 50 | NOT NULL | 'general' | 場景類型(LLMChain、SequentialChain、agent) |
| description | TEXT | - | - | '' | 場景描述 |
| config_json | JSONB | - | NOT NULL | '{}' | 場景配置（含提示詞、RAG、工具設定等整合） |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |
| updated_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 更新時間 |


#### 3.2 LlmModel (模型表)

用途：儲存系統可存取的模型清單

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 模型唯一識別碼 |
| display_name | VARCHAR | 100 | NOT NULL | - | 顯示名稱 |
| is_active | BOOLEAN | - | NOT NULL | true | 是否啟用 |

#### 3.3 ScenarioModel (場景-模型關聯表)

用途：定義每個場景可使用的模型集合

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 關聯唯一識別碼 |
| scenario_id | UUID | - | FK, NOT NULL | - | 場景識別碼 |
| model_id | UUID | - | FK, NOT NULL | - | 模型識別碼 |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |


#### 3.4 GroupScenarioAccess (群組場景存取表)

**用途**：記錄群組對場景的存取權限，群組內所有使用者繼承此權限

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 存取唯一識別碼 |
| group_id | UUID | - | FK, NOT NULL | - | 群組識別碼 |
| scenario_id | UUID | - | FK, NOT NULL | - | 場景識別碼 |
| access_type | VARCHAR | 20 | NOT NULL | 'use' | 存取類型（use/manage） |
| granted_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 授予時間 |
| granted_by | UUID | - | FK, NOT NULL | - | 授予者識別碼 |

**重要說明**：
- 群組的場景存取權限會自動繼承給群組內的所有使用者
- 主管可以決定群組內低權限使用者的場景存取
- 管理人員不受此限制，可存取所有場景

### 4. 會話管理實體

#### 4.1 Session (會話表)

**用途**：記錄使用者的對話會話

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 會話唯一識別碼 |
| title | VARCHAR | 255 | - | '新對話' | 會話標題 |
| user_id | UUID | - | FK, NOT NULL | - | 使用者識別碼 |
| scenario_id | UUID | - | FK, NOT NULL | - | 使用場景識別碼 |
| started_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 開始時間 |
| last_activity_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 最後活動時間 |
| status | VARCHAR | 20 | NOT NULL | 'Active' | 會話狀態 |
| model_id | UUID | - | FK | NULL | 指定本會話使用的模型（若為 NULL 則使用場景/系統預設） |

說明：若 `model_id` 有值，該會話與 AI 對話時將採用此模型，覆寫場景/系統預設模型。

#### Session 狀態說明

| 狀態 | 英文代碼 | 說明 | 觸發條件 | 可轉換到 |
|------|---------|------|----------|----------|
| 活躍中 | Active | 會話剛建立，等待使用者輸入 | 會話建立時 | Waiting, Closed |
| 等待中 | Waiting | 使用者已送出訊息，等待 AI 回覆 | 使用者送出訊息後 | Replyed, Closed |
| 已回覆 | Replyed | AI 已回覆，等待使用者下一步操作 | AI 成功回覆後 | Waiting, Closed |
| 已關閉 | Closed | 會話結束（使用者主動關閉、封存或逾時） | 使用者關閉或系統逾時 | - |

#### 狀態轉換流程
```
Active → Waiting → Replyed → Waiting → ... → Closed
    ↓         ↓       ↑
  Closed    Closed  Closed
```

#### 4.2 Message (訊息表)

**用途**：儲存會話中的所有訊息

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 訊息唯一識別碼 |
| session_id | UUID | - | FK, NOT NULL | - | 所屬會話識別碼 |
| content | TEXT | - | NOT NULL | - | 訊息內容 |
| message_type | VARCHAR | 20 | NOT NULL | 'user' | 訊息類型（user/assistant/system） |
| parent_message_id | UUID | - | FK | NULL | 父訊息識別碼（用於訊息樹） |
| sequence_number | INTEGER | - | NOT NULL | 1 | 會話中的序號 |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |

 

## 權限模型

### 權限繼承機制

```
權限計算邏輯：

1. 管理人員 :
   - group_id = NULL (不受群組限制)
   - 可存取所有場景
   - 擁有所有操作權限

2. 主管:
   - 屬於特定群組
   - 可存取群組被授權的所有場景
   - 可決定群組內員工的場景存取權限
   - 擁有群組管理權限

3. 員工:
   - 屬於特定群組
   - 只能存取被群組授權且被主管分配的場景
   - 僅有基本對話權限

```


## 資料庫關係圖

### 實體關係

1. **User ↔ Role**：多對一關係（一個使用者一個角色）
2. **User ↔ Group**：多對一關係（一個使用者最多一個群組）
3. **Role ↔ Permission**：多對多關係（透過 RolePermission）
4. **Group ↔ Scenario**：多對多關係（透過 GroupScenarioAccess）
5. **Scenario ↔ LlmModel**：多對多關係（透過 ScenarioModel）
6. **Session ↔ User**：多對一關係
7. **Session ↔ Scenario**：多對一關係
8. **Message ↔ Session**：多對一關係

### 權限繼承流程

```
管理人員: 全域權限 (不受群組限制)
    ↓
群組場景權限 ← 主管分配 → 群組內使用者
    ↓
員工: 繼承群組場景權限
```
