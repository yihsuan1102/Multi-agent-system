@echo off
REM API 測試自動化腳本
REM 適用於 Windows 環境

echo =======================================
echo MaiAgent API 自動化測試
echo =======================================

REM 切換到專案目錄
cd /d "D:\project\agent\maiagent-api-fix\src\maiagent"

REM 檢查虛擬環境
if not exist "venv\Scripts\activate.bat" (
    echo 錯誤：找不到虛擬環境，請先建立虛擬環境
    echo 執行：python -m venv venv
    pause
    exit /b 1
)

REM 啟動虛擬環境
call venv\Scripts\activate.bat

echo 正在執行測試...
echo.

REM 執行資料庫遷移（測試環境）
python manage.py migrate --settings=config.settings.test

REM 載入測試資料
echo 載入測試資料...
python manage.py loaddata maiagent\chat\fixtures\test\test_groups.json --settings=config.settings.test
python manage.py loaddata maiagent\chat\fixtures\test\test_scenarios.json --settings=config.settings.test  
python manage.py loaddata maiagent\chat\fixtures\test\test_llm_models.json --settings=config.settings.test
python manage.py loaddata maiagent\chat\fixtures\test\test_group_scenario_access.json --settings=config.settings.test

REM 執行測試
echo.
echo 執行 API 測試...
python run_tests.py

REM 檢查測試結果
if %errorlevel% equ 0 (
    echo.
    echo ✅ 所有測試通過！
    echo.
) else (
    echo.
    echo ❌ 測試失敗，請檢查錯誤訊息
    echo.
    pause
    exit /b 1
)

REM 執行覆蓋率測試
echo 執行覆蓋率測試...
python run_tests.py --coverage

echo.
echo 測試完成！
pause