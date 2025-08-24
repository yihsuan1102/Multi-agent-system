# MaiAgent GenAI 自動回覆平台 - 操作與權限對應

## 概述

基於資料庫設計，本文件定義了操作類型與權限的對應關係。權限設計遵循：一個使用者一個角色、一個群組，群組即公司，管理人員擁有全域權限。

## 簡化的操作類型定義

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

## 權限檢查邏輯

### 1. 簡化的基礎權限檢查
```python
def check_operation_permission(user, operation_code):
    """檢查使用者是否有執行特定操作的權限"""
    
    # 管理人員擁有所有權限
    if user.role_id == 1:  # Administrator
        return True
    
    # 根據角色檢查權限
    role_operations = ROLE_OPERATION_MAPPING.get(user.role_id, set())
    return operation_code in role_operations
```

### 2. 資源範圍權限檢查
```python
def check_resource_scope_permission(user, operation_code, resource=None):
    """檢查使用者在特定資源範圍內的操作權限"""
    
    # 基礎權限檢查
    if not check_operation_permission(user, operation_code):
        return False
    
    # 管理人員有全部權限
    if user.role_id == 1:
        return True
    
    # 主管權限範圍檢查
    if user.role_id == 2:  # Supervisor
        if operation_code in ['search_group_conversations', 'view_group_conversations']:
            # 檢查是否在同一群組
            return resource and hasattr(resource, 'user') and resource.user.group_id == user.group_id
        
        elif operation_code == 'modify_scenario':
            # 檢查場景是否屬於群組
            return resource and GroupScenarioAccess.objects.filter(
                group_id=user.group_id,
                scenario_id=resource.id
            ).exists()
        
        elif operation_code == 'assign_scenario_to_group_member':
            # 檢查目標使用者是否在同一群組
            return resource and resource.group_id == user.group_id
    
    # 員工權限範圍檢查
    elif user.role_id == 3:  # Employee
        if operation_code in ['search_own_conversations', 'view_own_conversations']:
            return resource and resource.user_id == user.id
        
        elif operation_code == 'use_scenario':
            # 檢查是否可存取場景
            return can_access_scenario(user, resource)
    
    return False
```

### 3. 場景存取權限檢查
```python
def can_access_scenario(user, scenario):
    """簡化的場景存取權限檢查"""
    
    # 管理人員可存取所有場景
    if user.role_id == 1:
        return True
    
    # 檢查全域場景
    if scenario.is_global:
        return True
    
    # 檢查群組場景權限
    if user.group_id:
        return GroupScenarioAccess.objects.filter(
            group_id=user.group_id,
            scenario_id=scenario.id
        ).exists()
    
    return False
```

## 操作實現範例

### 1. 全文檢索實現
```python
def search_conversations(user, query, scope='own'):
    """根據權限範圍進行對話搜尋"""
    
    # 檢查操作權限
    operation_map = {
        'all': 'search_all_conversations',
        'group': 'search_group_conversations', 
        'own': 'search_own_conversations'
    }
    
    if not check_operation_permission(user, operation_map[scope]):
        raise PermissionDenied(f"無權限執行 {scope} 範圍的搜尋")
    
    # 根據範圍和使用者角色構建查詢
    if scope == 'all' and user.role_id == 1:
        # 管理人員搜尋所有對話
        conversations = Session.objects.all()
    elif scope == 'group' and user.group_id:
        # 搜尋群組內對話
        conversations = Session.objects.filter(user__group_id=user.group_id)
    else:
        # 搜尋自己的對話
        conversations = Session.objects.filter(user=user)
    
    # 使用 Elasticsearch 進行全文檢索
    return search_in_elasticsearch(conversations, query)
```

### 2. 群組場景分配實現
```python
def assign_scenario_to_group_member(supervisor, scenario, target_user):
    """主管分配群組場景給群組成員"""
    
    # 檢查基礎權限
    if not check_operation_permission(supervisor, 'assign_scenario_to_group_member'):
        raise PermissionDenied("無權限分配場景給群組成員")
    
    # 檢查是否在同一群組
    if supervisor.group_id != target_user.group_id:
        raise PermissionDenied("只能分配場景給同群組成員")
    
    # 檢查場景是否屬於群組
    if not GroupScenarioAccess.objects.filter(
        group_id=supervisor.group_id,
        scenario_id=scenario.id
    ).exists():
        raise PermissionDenied("此場景未分配給您的群組")
    
    # 執行分配（這裡可以是建立使用者場景權限記錄）
    # 由於簡化設計，群組成員自動繼承群組場景權限
    # 這裡主要是記錄分配行為
    
    # 記錄操作日誌
    log_operation(supervisor, 'assign_scenario_to_group_member', {
        'scenario_id': scenario.id,
        'target_user_id': target_user.id,
        'group_id': supervisor.group_id
    })
```

### 3. 場景建立與分配實現
```python
def create_and_assign_scenario(admin, scenario_config, target_groups=None, is_global=False):
    """管理人員建立場景並分配給群組"""
    
    # 檢查管理人員權限
    if admin.role_id != 1:
        raise PermissionDenied("只有管理人員可以建立場景")
    
    # 建立場景
    scenario = Scenario.objects.create(
        name=scenario_config['name'],
        description=scenario_config['description'],
        langchain_config=scenario_config['langchain_config'],
        llm_config=scenario_config['llm_config'],
        prompt_template=scenario_config['prompt_template'],
        is_global=is_global,
        created_by=admin
    )
    
    # 如果是全域場景，所有群組都可使用
    if is_global:
        scenario.is_global = True
        scenario.save()
    
    # 分配給特定群組
    elif target_groups:
        for group in target_groups:
            GroupScenarioAccess.objects.create(
                group=group,
                scenario=scenario,
                access_type='use',
                granted_by=admin
            )
    
    # 記錄操作日誌
    log_operation(admin, 'create_scenario', {
        'scenario_id': scenario.id,
        'is_global': is_global,
        'target_groups': [g.id for g in target_groups] if target_groups else []
    })
    
    return scenario
```

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

### 資料庫配置
```sql
-- 簡化的操作類型表
CREATE TABLE operations (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    requires_group_check BOOLEAN DEFAULT false,
    requires_resource_check BOOLEAN DEFAULT false
);

-- 簡化的角色操作權限表
CREATE TABLE role_operations (
    id SERIAL PRIMARY KEY,
    role_id INTEGER REFERENCES roles(id),
    operation_id INTEGER REFERENCES operations(id),
    is_granted BOOLEAN DEFAULT true,
    resource_scope VARCHAR(50) DEFAULT 'any', -- 'any', 'group', 'own'
    UNIQUE(role_id, operation_id)
);
```

## 場景權限繼承機制

### 群組場景權限繼承
```python
def get_user_accessible_scenarios(user):
    """取得使用者可存取的場景"""
    
    # 管理人員可存取所有場景
    if user.role_id == 1:
        return Scenario.objects.all()
    
    # 其他使用者：全域場景 + 群組場景
    scenarios = Scenario.objects.filter(is_global=True)
    
    if user.group_id:
        group_scenarios = Scenario.objects.filter(
            groupscenarioaccess__group_id=user.group_id
        )
        scenarios = scenarios.union(group_scenarios)
    
    return scenarios.distinct()

def get_supervisor_manageable_scenarios(supervisor):
    """取得主管可管理的場景"""
    
    if supervisor.role_id != 2 or not supervisor.group_id:
        return Scenario.objects.none()
    
    return Scenario.objects.filter(
        groupscenarioaccess__group_id=supervisor.group_id,
        groupscenarioaccess__access_type='manage'
    )
```

