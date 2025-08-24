# MaiAgent GenAI 自動回覆平台 - 資料庫設計文件

## 概述

本文件詳細說明 MaiAgent GenAI 自動回覆平台的資料庫設計，基於使用者權限與場景選擇機制的需求，採用 PostgreSQL 作為主要資料庫，設計了實體關係模型以支援階層式權限控制、群組管理、場景配置與會話管理等核心功能。


## 資料庫技術架構

- **主要資料庫**：PostgreSQL 14+
- **權限管理**：django-role-permissions + 自訂權限模型
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
| role_id | INTEGER | - | FK, NOT NULL | - | 使用者角色（一對一） |
| group_id | UUID | - | FK | NULL | 所屬群組（管理人員可為 NULL） |
| password_hash | VARCHAR | 128 | NOT NULL | - | 密碼雜湊值 |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |
| updated_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 更新時間 |

**備註**：
- 群組代表公司或組織邊界
- 群組場景權限決定成員的場景存取權限
- 直接在 User 表中儲存 role_id 和 group_id
- 一個使用者只能有一個角色和一個群組
- 管理人員的 group_id 為 NULL，表示不受群組限制

**索引設計**：
```sql
CREATE UNIQUE INDEX idx_user_username ON users(username);
CREATE UNIQUE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_role ON users(role_id);
CREATE INDEX idx_user_group ON users(group_id);
CREATE INDEX idx_user_created_at ON users(created_at);
```

#### 1.2 Role (角色表)

**用途**：定義系統中的各種角色類型

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | SERIAL | - | PK, NOT NULL | - | 角色唯一識別碼 |
| name | VARCHAR | 100 | UK, NOT NULL | - | 角色名稱 |
| description | TEXT | - | - | '' | 角色描述 |
| permission_level | INTEGER | - | NOT NULL | 999 | 權限等級（數字越小權限越高） |
| is_system_role | BOOLEAN | - | NOT NULL | false | 是否為系統預設角色 |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |
| updated_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 更新時間 |

**預設資料**：
```sql
INSERT INTO roles (name, description, permission_level, is_system_role) VALUES
('Administrator', '管理人員 - 擁有全域權限，不受群組限制', 1, true),
('Supervisor', '主管 - 可管理群組內的場景與使用者', 2, true),
('Employee', '員工 - 僅能使用被分配的場景', 3, true);
```

#### 1.3 Permission (權限表)

**用途**：定義系統中的各種權限類型

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | SERIAL | - | PK, NOT NULL | - | 權限唯一識別碼 |
| name | VARCHAR | 100 | UK, NOT NULL | - | 權限名稱 |
| codename | VARCHAR | 100 | UK, NOT NULL | - | 權限代碼 |
| description | TEXT | - | - | '' | 權限描述 |
| category | VARCHAR | 50 | NOT NULL | 'general' | 權限分類 |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |

**預設權限資料**：
```sql
INSERT INTO permissions (name, codename, description, category) VALUES
-- 全文檢索權限
('搜尋所有對話', 'search_all_conversations', '關鍵字查詢所有使用者對話紀錄', 'search'),
('搜尋群組對話', 'search_group_conversations', '關鍵字查詢群組內對話紀錄', 'search'),
('搜尋個人對話', 'search_own_conversations', '關鍵字查詢自己對話紀錄', 'search'),

-- 場景管理權限
('調整場景路由', 'adjust_scenario_routing', '調整場景路由與權重', 'scenario'),
('建立場景', 'create_scenario', '建立新的對話場景', 'scenario'),
('修改場景', 'modify_scenario', '修改場景的角色敘述、模型名稱等配置', 'scenario'),
('刪除場景', 'delete_scenario', '刪除場景', 'scenario'),

-- 群組管理權限
('管理群組', 'manage_groups', '群組管理', 'group'),
('管理群組成員', 'manage_group_members', '管理群組成員', 'group'),

-- 場景設定權限
('更新所有使用者場景', 'update_all_user_scenarios', '更新所有使用者場景設定', 'scenario'),
('更新群組使用者場景', 'update_group_user_scenarios', '更新群組內使用者場景設定', 'scenario'),

-- 對話權限
('送出訊息', 'send_message_to_scenario', '送出訊息給場景', 'conversation'),
('使用場景', 'use_scenario', '使用場景進行對話', 'conversation'),

-- 歷史對話檢視權限
('檢視所有使用者對話', 'view_all_user_conversations', '檢視所有使用者歷史對話', 'conversation'),
('檢視群組對話', 'view_group_conversations', '檢視群組內所有使用者歷史對話', 'conversation'),
('檢視個人對話', 'view_own_conversations', '檢視自己歷史對話', 'conversation');
```

#### 1.4 RolePermission (角色權限關聯表)

**用途**：定義角色擁有的權限

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | SERIAL | - | PK, NOT NULL | - | 關聯唯一識別碼 |
| role_id | INTEGER | - | FK, NOT NULL | - | 角色識別碼 |
| permission_id | INTEGER | - | FK, NOT NULL | - | 權限識別碼 |
| is_granted | BOOLEAN | - | NOT NULL | true | 是否授予權限 |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |

**預設角色權限配置**：
```sql
-- 管理人員擁有所有權限
INSERT INTO role_permissions (role_id, permission_id, is_granted)
SELECT 1, id, true FROM permissions;

-- 主管權限配置
INSERT INTO role_permissions (role_id, permission_id, is_granted)
SELECT 2, id, true FROM permissions 
WHERE codename IN (
    'search_group_conversations', 'search_own_conversations',
    'modify_scenario', 'manage_group_members',
    'update_group_user_scenarios', 'send_message_to_scenario',
    'use_scenario', 'view_group_conversations', 'view_own_conversations'
);

-- 員工權限配置
INSERT INTO role_permissions (role_id, permission_id, is_granted)
SELECT 3, id, true FROM permissions 
WHERE codename IN (
    'search_own_conversations', 'send_message_to_scenario',
    'use_scenario', 'view_own_conversations', 'modify_scenario'
);
```

### 2. 群組管理實體

#### 2.1 Group (群組表) - 代表公司

**用途**：儲存公司/組織資訊，每個群組代表一個獨立的公司實體

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 群組唯一識別碼 |
| name | VARCHAR | 255 | NOT NULL | - | 公司名稱 |
| description | TEXT | - | - | '' | 公司描述 |
| company_code | VARCHAR | 50 | UK | NULL | 公司代碼 |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |
| updated_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 更新時間 |

**重要變更**：
- 移除了階層關係（parent_group_id, depth_level, path）
- 群組現在代表獨立的公司實體
- 新增 company_code 用於公司識別

**索引設計**：
```sql
CREATE UNIQUE INDEX idx_groups_company_code ON groups(company_code) WHERE company_code IS NOT NULL;
CREATE INDEX idx_groups_name ON groups(name);
```

### 3. 場景管理實體

#### 3.1 Scenario (場景表)

**用途**：儲存 LangChain 場景配置與設定

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 場景唯一識別碼 |
| name | VARCHAR | 255 | UK, NOT NULL | - | 場景名稱 |
| description | TEXT | - | - | '' | 場景描述 |
| langchain_config | JSONB | - | NOT NULL | '{}' | LangChain 配置 |
| llm_config | JSONB | - | NOT NULL | '{}' | LLM 模型配置 |
| prompt_template | JSONB | - | NOT NULL | '{}' | 提示詞模板 |
| rag_config | JSONB | - | - | NULL | RAG 策略配置 |
| scenario_type | VARCHAR | 50 | NOT NULL | 'general' | 場景類型 |
| version | INTEGER | - | NOT NULL | 1 | 場景版本號 |
| routing_weight | DECIMAL | 5,2 | NOT NULL | 1.0 | 路由權重 |
| routing_priority | INTEGER | - | NOT NULL | 0 | 路由優先級 |
| is_global | BOOLEAN | - | NOT NULL | false | 是否為全域場景 |
| created_by | UUID | - | FK, NOT NULL | - | 建立者識別碼 |
| created_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 建立時間 |
| updated_at | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 更新時間 |


#### 3.2 GroupScenarioAccess (群組場景存取表)

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

### 5. 稽核管理實體

#### 5.1 AuditLog (稽核日誌表)

**用途**：記錄系統中的重要操作，用於安全合規和問題追蹤

| 欄位名稱 | 資料類型 | 長度 | 限制 | 預設值 | 用途描述 |
|---------|---------|------|------|--------|----------|
| id | UUID | - | PK, NOT NULL | uuid_generate_v4() | 日誌唯一識別碼 |
| user_id | UUID | - | FK | NULL | 操作使用者識別碼 |
| action_type | VARCHAR | 50 | NOT NULL | - | 操作類型（create/update/delete/access） |
| resource_type | VARCHAR | 50 | NOT NULL | - | 資源類型（user/role/group/scenario/session） |
| resource_id | VARCHAR | 255 | - | NULL | 資源識別碼 |
| old_values | JSONB | - | - | NULL | 操作前的值 |
| new_values | JSONB | - | - | NULL | 操作後的值 |
| ip_address | INET | - | - | NULL | IP 地址 |
| user_agent | TEXT | - | - | NULL | 使用者代理 |
| result | VARCHAR | 20 | NOT NULL | 'success' | 操作結果（success/failure/error） |
| timestamp | TIMESTAMP | - | NOT NULL | CURRENT_TIMESTAMP | 操作時間 |

## 權限模型

### 權限繼承機制

```
簡化的權限計算邏輯：

1. 管理人員 (role_id = 1):
   - group_id = NULL (不受群組限制)
   - 可存取所有場景
   - 擁有所有操作權限

2. 主管 (role_id = 2):
   - 屬於特定群組
   - 可存取群組被授權的所有場景
   - 可決定群組內員工的場景存取權限
   - 擁有群組管理權限

3. 員工 (role_id = 3):
   - 屬於特定群組
   - 只能存取被群組授權且被主管分配的場景
   - 僅有基本對話權限

權限檢查流程：
IF user.role_id = 1 THEN 全部權限
ELSE IF user.role_id = 2 THEN 群組管理權限 + 群組場景權限
ELSE 基本權限 + 被分配的場景權限
```

### 場景存取控制

```sql
-- 檢查使用者是否可存取場景
CREATE OR REPLACE FUNCTION can_access_scenario(user_id UUID, scenario_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    user_role INTEGER;
    user_group UUID;
    has_access BOOLEAN := FALSE;
BEGIN
    -- 取得使用者角色和群組
    SELECT role_id, group_id INTO user_role, user_group
    FROM users WHERE id = user_id;
    
    -- 管理人員可存取所有場景
    IF user_role = 1 THEN
        RETURN TRUE;
    END IF;
    
    -- 檢查全域場景
    SELECT is_global INTO has_access
    FROM scenarios WHERE id = scenario_id;
    
    IF has_access THEN
        RETURN TRUE;
    END IF;
    
    -- 檢查群組場景權限
    IF user_group IS NOT NULL THEN
        SELECT EXISTS(
            SELECT 1 FROM group_scenario_access
            WHERE group_id = user_group AND scenario_id = scenario_id
        ) INTO has_access;
    END IF;
    
    RETURN has_access;
END;
$$ LANGUAGE plpgsql;
```

## 資料庫關係圖

### 實體關係

1. **User ↔ Role**：多對一關係（一個使用者一個角色）
2. **User ↔ Group**：多對一關係（一個使用者最多一個群組）
3. **Role ↔ Permission**：多對多關係（透過 RolePermission）
4. **Group ↔ Scenario**：多對多關係（透過 GroupScenarioAccess）
5. **Session ↔ User**：多對一關係
6. **Session ↔ Scenario**：多對一關係
7. **Message ↔ Session**：多對一關係

### 權限繼承流程

```
管理人員: 全域權限 (不受群組限制)
    ↓
群組場景權限 ← 主管分配 → 群組內使用者
    ↓
員工: 繼承群組場景權限
```

## 索引策略

### 主要索引

```sql
-- 使用者相關索引
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_users_group ON users(group_id);

-- 群組場景存取索引
CREATE INDEX idx_group_scenario_access_group ON group_scenario_access(group_id);
CREATE INDEX idx_group_scenario_access_scenario ON group_scenario_access(scenario_id);
CREATE UNIQUE INDEX idx_group_scenario_access_unique ON group_scenario_access(group_id, scenario_id);

-- 會話相關索引
CREATE INDEX idx_sessions_user_activity ON sessions(user_id, last_activity_at);
CREATE INDEX idx_sessions_scenario ON sessions(scenario_id);
CREATE INDEX idx_messages_session_sequence ON messages(session_id, sequence_number);

-- 場景索引
CREATE INDEX idx_scenarios_global ON scenarios(is_global) WHERE is_global = true;
CREATE INDEX idx_scenarios_type ON scenarios(scenario_type);
```

## 資料完整性約束

### 外鍵約束

```sql
-- 使用者約束
ALTER TABLE users 
ADD CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(id),
ADD CONSTRAINT fk_users_group FOREIGN KEY (group_id) REFERENCES groups(id);

-- 群組場景存取約束
ALTER TABLE group_scenario_access 
ADD CONSTRAINT fk_group_scenario_access_group FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
ADD CONSTRAINT fk_group_scenario_access_scenario FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
ADD CONSTRAINT fk_group_scenario_access_granted_by FOREIGN KEY (granted_by) REFERENCES users(id);

-- 會話約束
ALTER TABLE sessions 
ADD CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
ADD CONSTRAINT fk_sessions_scenario FOREIGN KEY (scenario_id) REFERENCES scenarios(id);

-- 訊息約束
ALTER TABLE messages 
ADD CONSTRAINT fk_messages_session FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
ADD CONSTRAINT fk_messages_parent FOREIGN KEY (parent_message_id) REFERENCES messages(id);
```

### 檢查約束

```sql
-- 權限等級檢查
ALTER TABLE roles 
ADD CONSTRAINT ck_roles_permission_level CHECK (permission_level > 0 AND permission_level <= 999);

-- 訊息類型檢查
ALTER TABLE messages 
ADD CONSTRAINT ck_messages_type CHECK (message_type IN ('user', 'assistant', 'system'));

-- 會話狀態檢查
ALTER TABLE sessions 
ADD CONSTRAINT ck_sessions_status CHECK (status IN ('Active', 'Waiting', 'Replyed', 'Closed'));

-- 存取類型檢查
ALTER TABLE group_scenario_access 
ADD CONSTRAINT ck_group_scenario_access_type CHECK (access_type IN ('use', 'manage'));

-- 路由權重檢查
ALTER TABLE scenarios 
ADD CONSTRAINT ck_scenarios_routing_weight CHECK (routing_weight >= 0 AND routing_weight <= 100);
```

## 業務邏輯約束

### 管理人員特殊規則

```sql
-- 管理人員不能有群組 (group_id 必須為 NULL)
ALTER TABLE users 
ADD CONSTRAINT ck_users_admin_no_group 
CHECK (
    CASE 
        WHEN role_id = 1 THEN group_id IS NULL 
        ELSE TRUE 
    END
);

-- 非管理人員必須有群組
ALTER TABLE users 
ADD CONSTRAINT ck_users_non_admin_has_group 
CHECK (
    CASE 
        WHEN role_id != 1 THEN group_id IS NOT NULL 
        ELSE TRUE 
    END
);
```

## 簡化帶來的優勢

### 1. 設計簡化
- 移除了複雜的多對多關係
- 減少了中間表的數量
- 明確的權限邊界定義

### 2. 查詢效能提升
- 減少了 JOIN 操作
- 簡化了權限檢查邏輯
- 優化了索引設計

### 3. 維護性改善
- 清晰的業務邏輯映射
- 減少了資料一致性問題
- 簡化了權限管理流程

### 4. 擴展性保持
- 仍支援新角色類型的添加
- 保持了場景管理的靈活性
- 維持了稽核追蹤能力

## 總結

簡化後的資料庫設計具備以下特點：

1. **極簡關係**：一對一、一對多關係為主，最小化複雜度
2. **清晰邊界**：群組 = 公司，角色 = 職位，權限邊界明確
3. **高效權限**：簡化的權限繼承機制，查詢效能優化
4. **彈性管理**：管理人員超群組權限，主管群組內管理
5. **安全可靠**：保持稽核追蹤，滿足合規要求

此設計為 MaiAgent GenAI 自動回覆平台提供了簡潔而強大的資料基礎，在保持功能完整性的同時大幅提升了系統的可維護性和效能。