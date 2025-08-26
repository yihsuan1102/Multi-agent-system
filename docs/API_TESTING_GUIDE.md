# MaiAgent API 自動化測試文檔

## 概述

本文檔說明 MaiAgent API 1（彈性訊息提交 API）的自動化測試方案，包含測試案例、測試資料、執行方式和 CI/CD 整合。

## 測試覆蓋範圍

### 功能測試

1. **正常流程測試**
   - ✅ 使用現有會話提交訊息（URL 中指定 session_id）
   - ✅ 使用現有會話提交訊息（請求體中指定 session_id）
   - ✅ 自動建立新會話並提交訊息
   - ✅ 指定 LLM 模型提交訊息
   - ✅ 完整對話流程測試

2. **錯誤處理測試**
   - ✅ 未認證請求 (401)
   - ✅ 空白內容 (400)
   - ✅ 建立新會話時缺少 scenario_id (400)
   - ✅ 不存在的會話 (404)
   - ✅ 不存在的場景 (404)
   - ✅ 無場景存取權 (403)
   - ✅ 已關閉的會話 (400)
   - ✅ Celery 服務失敗 (503)
   - ✅ 不存在的 LLM 模型 (404)

3. **整合測試**
   - ✅ 完整對話流程
   - ✅ 權限控制驗證
   - ✅ 資料庫事務測試

## 測試資料結構

### 測試群組
- `測試客服群組` (11111111-1111-1111-1111-111111111111)
- `測試技術群組` (22222222-2222-2222-2222-222222222222)

### 測試場景
- `客服助理測試場景` (33333333-3333-3333-3333-333333333333)
- `技術支援測試場景` (44444444-4444-4444-4444-444444444444)
- `無權限場景` (55555555-5555-5555-5555-555555555555)

### 測試使用者
- `testuser1` - 客服群組員工
- `testuser2` - 技術群組員工  
- `admin_user` - 管理員

### 測試 LLM 模型
- `OpenAI GPT-4` (66666666-6666-6666-6666-666666666666)
- `Anthropic Claude-3` (77777777-7777-7777-7777-777777777777)

## 測試執行方式

### 本地執行

#### Windows
```batch
# 執行完整測試套件
test_api.bat

# 僅執行測試（不含覆蓋率）
cd src\maiagent
python run_tests.py

# 執行覆蓋率測試
cd src\maiagent  
python run_tests.py --coverage
```

#### Linux/macOS
```bash
# 執行完整測試套件
./test_api.sh

# 僅執行測試
cd src/maiagent
python run_tests.py

# 執行覆蓋率測試
cd src/maiagent
python run_tests.py --coverage
```

### CI/CD 執行

測試會在以下情況自動執行：
- Push 到 `main`, `develop`, `feature/api-*` 分支
- 建立 Pull Request 到 `main`, `develop` 分支

## 測試案例詳情

### 1. 正常流程測試案例

#### test_submit_message_with_existing_session_url
**測試目標：** 驗證使用 URL 中 session_id 提交訊息  
**測試步驟：**
1. 建立測試會話
2. 發送 POST 請求到 `/api/v1/conversations/{session_id}/messages/`
3. 驗證回應狀態碼為 201
4. 驗證回應包含正確的 session_id 和訊息內容
5. 驗證資料庫中已儲存訊息
6. 驗證 Celery 任務已發送

#### test_submit_message_create_new_session
**測試目標：** 驗證自動建立新會話功能  
**測試步驟：**
1. 發送 POST 請求到 `/api/v1/conversations/messages/`，包含 scenario_id
2. 驗證回應狀態碼為 201
3. 驗證回傳新的 session_id
4. 驗證新會話已在資料庫中建立
5. 驗證會話狀態為 WAITING

### 2. 錯誤處理測試案例

#### test_submit_message_without_authentication
**測試目標：** 驗證未認證請求處理  
**預期結果：** 401 Unauthorized

#### test_submit_message_no_scenario_access
**測試目標：** 驗證無場景存取權處理  
**測試步驟：**
1. 建立使用者無權限的場景
2. 嘗試使用該場景建立會話
3. 驗證回應狀態碼為 403
4. 驗證錯誤訊息為 "無場景存取權"

## API 回應格式驗證

### 成功回應 (201 Created)
```json
{
  "session_id": "會話UUID",
  "message": {
    "id": "訊息UUID",
    "role": "user",
    "content": "使用者輸入內容",
    "sequence_number": 整數,
    "created_at": "ISO時間格式"
  }
}
```

### 錯誤回應格式
```json
{
  "detail": "具體錯誤訊息"
}
```

## 測試環境設定

### 資料庫設定
- 使用 SQLite 記憶體資料庫進行測試
- 每個測試案例都有獨立的資料庫狀態
- 自動載入測試 fixtures

### Celery 模擬
- 使用 `unittest.mock.patch` 模擬 Celery 任務
- 驗證任務調用但不執行實際處理
- 可模擬 Celery 失敗情境

### 認證處理
- 使用 JWT Token 進行 API 認證
- 測試案例自動生成有效 Token
- 支援測試未認證情境

## 覆蓋率目標

- **整體覆蓋率：** > 90%
- **API views.py：** > 95%
- **serializers.py：** > 90%
- **關鍵錯誤處理路徑：** 100%

## 測試報告

### 測試執行報告
測試完成後會生成以下報告：
- 測試通過/失敗統計
- 執行時間統計
- 錯誤詳情（如有）

### 覆蓋率報告
- 終端文字報告
- HTML 詳細報告 (`htmlcov/index.html`)
- 逐行覆蓋率分析

## 維護指南

### 新增測試案例
1. 在 `test_message_submission.py` 中新增測試方法
2. 使用 factory 生成測試資料
3. 使用 `patch` 模擬外部依賴
4. 驗證回應格式和狀態碼

### 更新測試資料
1. 修改 `fixtures/test/` 中的 JSON 檔案
2. 確保 UUID 一致性
3. 更新相關測試案例

### CI/CD 配置調整
1. 修改 `.github/workflows/api_tests.yml`
2. 確保環境變數正確設定
3. 測試本地執行成功後再提交

## 常見問題

### Q: 測試資料庫連線失敗
**A:** 檢查 `config/settings/test.py` 中的資料庫設定，確保使用記憶體資料庫

### Q: JWT Token 認證失敗  
**A:** 確保 `SECRET_KEY` 在測試環境中正確設定

### Q: Celery 相關測試失敗
**A:** 檢查 `patch` 裝飾器是否正確應用，確保模擬了 `process_message.delay`

### Q: 權限測試失敗
**A:** 檢查測試資料中的群組和場景存取權設定是否正確

## 最佳實踐

1. **測試隔離：** 每個測試案例獨立，不依賴其他測試
2. **資料清理：** 使用 Django 的 TestCase 自動處理資料庫清理
3. **模擬外部服務：** 使用 mock 避免依賴真實的 Celery/LLM 服務
4. **斷言明確：** 每個斷言都有明確的測試目的
5. **錯誤訊息檢查：** 不僅檢查狀態碼，也驗證錯誤訊息內容