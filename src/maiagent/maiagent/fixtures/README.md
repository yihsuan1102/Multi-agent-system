# Maiagent Fixtures 使用說明

## 概述
此目錄包含 maiagent 系統的基礎測試資料 (fixtures)，用於快速建置開發環境和測試環境。

## 目錄結構
```
fixtures/
├── README.md                    # 本說明檔
├── chat/                        # 聊天系統相關資料
│   ├── groups.json             # 群組資料
│   ├── llm_models.json         # LLM 模型設定
│   ├── scenarios.json          # 對話情境
│   ├── scenario_models.json    # 情境與模型關聯
│   ├── group_scenario_access.json  # 群組權限
│   ├── sessions.json           # 對話會話
│   └── messages.json           # 對話訊息
└── users/
    └── users.json              # 使用者資料
```

## 資料內容

### 群組 (Groups)
- IT部門 - 資訊科技部門
- 銷售部門 - 業務銷售部門  
- 客服部門 - 客戶服務部門

### LLM 模型 (LlmModel)
- OpenAI GPT-4o
- OpenAI GPT-3.5-turbo
- Anthropic Claude-3-sonnet

### 對話情境 (Scenarios)
- 客服助手 - 友善耐心的客服對話
- 技術支援 - 專業技術問題解決
- 銷售顧問 - 產品推薦與解決方案

### 使用者 (Users)
- admin - 系統管理員 (密碼: admin123)
- supervisor_it - IT部門主管 (密碼: admin123)  
- supervisor_sales - 銷售部門主管 (密碼: admin123)
- employee_it_001 - IT員工 張小明 (密碼: admin123)
- employee_sales_001 - 銷售員工 李小華 (密碼: admin123)
- employee_cs_001 - 客服員工 王小美 (密碼: admin123)

> 注意：所有使用者的密碼都是 `admin123`，請在正式環境中修改。

## 使用方法

### 1. 載入所有 Fixtures
```bash
cd D:\project\agent\maiagent-api-fix\src\maiagent
python manage.py load_fixtures
```

### 2. 清空後重新載入
```bash
python manage.py load_fixtures --flush
```

### 3. 只載入特定檔案
```bash
python manage.py load_fixtures --specific maiagent/fixtures/chat/groups.json
```

### 4. 模擬執行（不實際載入）
```bash
python manage.py load_fixtures --dry-run
```

### 5. 清空資料
```bash
# 清空所有資料
python manage.py clear_data --all

# 只清空聊天資料
python manage.py clear_data --chat-only

# 只清空使用者資料  
python manage.py clear_data --users-only
```

## 資料依賴關係

載入順序很重要，系統會自動按照以下順序載入：

1. **基礎資料** (無外鍵依賴)
   - groups.json
   - llm_models.json  
   - scenarios.json

2. **關聯資料** (依賴基礎資料)
   - scenario_models.json

3. **使用者資料** (依賴群組)
   - users.json

4. **權限設定** (依賴群組和情境)
   - group_scenario_access.json

5. **會話資料** (依賴使用者和情境)
   - sessions.json
   - messages.json

## 注意事項

1. **外鍵約束**: 所有 UUID 主鍵都是預定義的，請勿隨意修改
2. **資料完整性**: 載入過程使用資料庫事務，如有錯誤會自動回滾
3. **測試環境**: 這些資料僅適用於開發和測試，不應用於正式環境
4. **密碼安全**: 預設密碼僅供測試使用，正式環境請務必修改

## 擴展 Fixtures

要新增更多測試資料：

1. 在對應的 JSON 檔案中加入新記錄
2. 確保 UUID 主鍵唯一且符合格式
3. 檢查外鍵關聯正確性
4. 驗證必填欄位完整性

## 疑難排解

### 常見錯誤

**外鍵約束錯誤**
```
IntegrityError: foreign key constraint fails
```
解決方法：檢查外鍵 UUID 是否正確對應

**唯一約束錯誤**  
```
IntegrityError: duplicate key value violates unique constraint
```
解決方法：檢查是否有重複的唯一欄位值

**JSON 格式錯誤**
```
JSONDecodeError: Expecting ',' delimiter
```
解決方法：檢查 JSON 語法是否正確

### 重置步驟
如果資料有問題，可以完全重置：

1. 清空所有資料：`python manage.py clear_data --all --confirm`
2. 重新載入：`python manage.py load_fixtures`