#!/bin/bash
# API 測試自動化腳本
# 適用於 Linux/macOS 環境

set -e  # 遇到錯誤立即退出

echo "======================================="
echo "MaiAgent API 自動化測試"
echo "======================================="

# 切換到專案目錄
cd "$(dirname "$0")/src/maiagent"

# 檢查虛擬環境
if [ ! -f "venv/bin/activate" ]; then
    echo "錯誤：找不到虛擬環境，請先建立虛擬環境"
    echo "執行：python -m venv venv"
    exit 1
fi

# 啟動虛擬環境
source venv/bin/activate

echo "正在執行測試..."
echo

# 執行資料庫遷移（測試環境）
python manage.py migrate --settings=config.settings.test

# 載入測試資料
echo "載入測試資料..."
python manage.py loaddata maiagent/chat/fixtures/test/test_groups.json --settings=config.settings.test
python manage.py loaddata maiagent/chat/fixtures/test/test_scenarios.json --settings=config.settings.test
python manage.py loaddata maiagent/chat/fixtures/test/test_llm_models.json --settings=config.settings.test
python manage.py loaddata maiagent/chat/fixtures/test/test_group_scenario_access.json --settings=config.settings.test

# 執行測試
echo
echo "執行 API 測試..."
python run_tests.py

# 執行覆蓋率測試
echo "執行覆蓋率測試..."
python run_tests.py --coverage

echo
echo "✅ 測試完成！"