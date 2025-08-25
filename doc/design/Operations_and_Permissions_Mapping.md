# MaiAgent GenAI 自動回覆平台 - 操作與權限對應

## 概述

基於資料庫設計，本文件定義了操作類型與權限的對應關係。權限設計遵循：一個使用者一個角色、一個群組，群組即公司，管理人員擁有全域權限。

## 操作類型定義

### 1. 全文檢索操作
- **操作代碼**: `search_all_conversations` - 搜尋所有使用者對話紀錄
- **操作代碼**: `search_group_conversations` - 搜尋群組（公司）內對話紀錄  
- **操作代碼**: `search_own_conversations` - 搜尋自己對話紀錄

### 2. 場景管理操作
- **操作代碼**: `create_scenario` - 建立場景
- **操作代碼**: `modify_scenario` - 修改場景
- **操作代碼**: `delete_scenario` - 刪除場景
- **操作代碼**: `adjust_scenario_routing` - 調整場景路由與權重
- **操作代碼**: `set_scenario_global` - 設定場景為全域場景

### 3. 群組管理操作（公司管理）
- **操作代碼**: `create_group` - 建立群組（公司）
- **操作代碼**: `manage_group` - 管理群組基本資訊
- **操作代碼**: `assign_user_to_group` - 分配使用者到群組
- **操作代碼**: `assign_scenario_to_group` - 分配場景給群組

### 4. 群組內場景分配操作
- **操作代碼**: `assign_scenario_to_group_member` - 分配群組場景給群組成員
- **操作代碼**: `manage_group_scenario_access` - 管理群組內場景存取權限

### 5. 對話操作
- **操作代碼**: `send_message_to_scenario` - 送出訊息給場景
- **操作代碼**: `use_scenario` - 使用場景進行對話

### 6. 歷史對話檢視操作
- **操作代碼**: `view_all_conversations` - 檢視所有使用者歷史對話
- **操作代碼**: `view_group_conversations` - 檢視群組內所有使用者歷史對話
- **操作代碼**: `view_own_conversations` - 檢視自己歷史對話

## 簡化的角色與操作權限對應表

| 操作類型 | 管理人員 | 主管 | 員工 | 說明 |
|---------|---------|------|------|------|
| **全文檢索操作** |
| search_all_conversations | ✅ | ❌ | ❌ | 管理人員可搜尋所有對話 |
| search_group_conversations | ✅ | ✅ | ❌ | 主管可搜尋群組內對話 |
| search_own_conversations | ✅ | ✅ | ✅ | 所有角色可搜尋自己的對話 |
| **場景管理操作** |
| create_scenario | ✅ | ❌ | ❌ | 僅管理人員可建立場景 |
| modify_scenario | ✅ | ⚠️* | ❌ | 主管僅能修改群組內場景 |
| delete_scenario | ✅ | ❌ | ❌ | 僅管理人員可刪除場景 |
| adjust_scenario_routing | ✅ | ❌ | ❌ | 僅管理人員可調整路由 |
| set_scenario_global | ✅ | ❌ | ❌ | 僅管理人員可設定全域場景 |
| **群組管理操作** |
| create_group | ✅ | ❌ | ❌ | 僅管理人員可建立群組（公司） |
| manage_group | ✅ | ❌ | ❌ | 僅管理人員可管理群組資訊 |
| assign_user_to_group | ✅ | ❌ | ❌ | 僅管理人員可分配使用者到群組 |
| assign_scenario_to_group | ✅ | ❌ | ❌ | 僅管理人員可分配場景給群組 |
| **群組內場景分配操作** |
| assign_scenario_to_group_member | ✅ | ✅ | ❌ | 主管可分配群組場景給員工 |
| manage_group_scenario_access | ✅ | ✅ | ❌ | 主管可管理群組內場景存取 |
| **對話操作** |
| send_message_to_scenario | ✅ | ✅ | ✅ | 所有角色可發送訊息 |
| use_scenario | ✅ | ✅ | ✅ | 所有角色可使用已授權場景 |
| **歷史對話檢視操作** |
| view_all_conversations | ✅ | ❌ | ❌ | 僅管理人員可檢視所有對話 |
| view_group_conversations | ✅ | ✅ | ❌ | 主管可檢視群組內對話 |
| view_own_conversations | ✅ | ✅ | ✅ | 所有角色可檢視自己對話 |

**註釋**：
- *主管僅能修改群組內已獲授權場景的部分參數

## 操作權限配置

### Python 配置
```python
ROLE_OPERATION_MAPPING = {
    1: {  # Administrator
        'search_all_conversations',
        'search_group_conversations', 
        'search_own_conversations',
        'create_scenario',
        'modify_scenario',
        'delete_scenario',
        'adjust_scenario_routing',
        'set_scenario_global',
        'create_group',
        'manage_group',
        'assign_user_to_group',
        'assign_scenario_to_group',
        'assign_scenario_to_group_member',
        'manage_group_scenario_access',
        'send_message_to_scenario',
        'use_scenario',
        'view_all_conversations',
        'view_group_conversations',
        'view_own_conversations'
    },
    2: {  # Supervisor
        'search_group_conversations',
        'search_own_conversations', 
        'modify_scenario',  # 限制範圍
        'assign_scenario_to_group_member',
        'manage_group_scenario_access',
        'send_message_to_scenario',
        'use_scenario',
        'view_group_conversations',
        'view_own_conversations'
    },
    3: {  # Employee
        'search_own_conversations',
        'send_message_to_scenario',
        'use_scenario',
        'view_own_conversations'
    }
}
```
