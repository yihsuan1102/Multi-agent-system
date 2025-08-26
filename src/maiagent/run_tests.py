#!/usr/bin/env python
"""
自動化測試腳本
用於 CI/CD 流程中執行測試並生成報告
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line


def setup_django():
    """設置 Django 環境"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
    django.setup()


def run_specific_tests(test_labels=None):
    """執行指定的測試"""
    if test_labels is None:
        test_labels = [
            'maiagent.chat.tests.api.test_message_submission',
        ]
    
    # 設置測試運行器
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    
    # 執行測試
    failures = test_runner.run_tests(test_labels)
    
    return failures


def run_coverage_tests():
    """執行測試並生成覆蓋率報告"""
    try:
        import coverage
    except ImportError:
        print("警告：coverage 套件未安裝，無法生成覆蓋率報告")
        return run_specific_tests()
    
    # 建立覆蓋率對象
    cov = coverage.Coverage(source=['maiagent'])
    cov.start()
    
    try:
        # 執行測試
        failures = run_specific_tests()
        
        # 停止覆蓋率收集
        cov.stop()
        cov.save()
        
        # 生成報告
        print("\n" + "="*50)
        print("測試覆蓋率報告")
        print("="*50)
        cov.report(show_missing=True)
        
        # 生成 HTML 報告
        html_dir = 'htmlcov'
        cov.html_report(directory=html_dir)
        print(f"\nHTML 覆蓋率報告已生成：{html_dir}/index.html")
        
        return failures
        
    except Exception as e:
        cov.stop()
        print(f"覆蓋率測試執行失敗：{e}")
        return 1


def main():
    """主函數"""
    setup_django()
    
    # 檢查命令行參數
    if len(sys.argv) > 1 and sys.argv[1] == '--coverage':
        failures = run_coverage_tests()
    else:
        failures = run_specific_tests()
    
    # 返回結果
    if failures:
        print(f"\n❌ 測試失敗：{failures} 個測試案例未通過")
        sys.exit(1)
    else:
        print("\n✅ 所有測試通過！")
        sys.exit(0)


if __name__ == '__main__':
    main()