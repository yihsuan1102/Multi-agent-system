#!/usr/bin/env python
"""
測試驗證腳本
驗證測試設置是否正確
"""
import os
import sys
import django
from django.conf import settings
from django.apps import apps


def setup_django():
    """設置 Django 環境"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
    django.setup()


def validate_test_structure():
    """驗證測試結構"""
    issues = []
    
    # 檢查測試文件
    test_files = [
        'maiagent/chat/tests/__init__.py',
        'maiagent/chat/tests/api/__init__.py', 
        'maiagent/chat/tests/api/test_message_submission.py',
        'maiagent/chat/tests/factories.py',
    ]
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            issues.append(f"❌ 缺少測試文件：{test_file}")
        else:
            print(f"✅ 測試文件存在：{test_file}")
    
    # 檢查測試資料
    fixture_files = [
        'maiagent/chat/fixtures/test/test_groups.json',
        'maiagent/chat/fixtures/test/test_scenarios.json',
        'maiagent/chat/fixtures/test/test_llm_models.json',
        'maiagent/chat/fixtures/test/test_group_scenario_access.json',
    ]
    
    for fixture_file in fixture_files:
        if not os.path.exists(fixture_file):
            issues.append(f"❌ 缺少測試資料：{fixture_file}")
        else:
            print(f"✅ 測試資料存在：{fixture_file}")
    
    return issues


def validate_models():
    """驗證模型設置"""
    issues = []
    
    try:
        from maiagent.chat.models import Session, Message, Scenario, Group, LlmModel
        print("✅ 所有模型匯入成功")
        
        # 檢查模型字段
        session_fields = [f.name for f in Session._meta.fields]
        required_session_fields = ['id', 'user', 'scenario', 'status', 'created_at']
        
        for field in required_session_fields:
            if field not in session_fields:
                issues.append(f"❌ Session 模型缺少字段：{field}")
            else:
                print(f"✅ Session 字段存在：{field}")
        
    except ImportError as e:
        issues.append(f"❌ 模型匯入失敗：{e}")
    
    return issues


def validate_serializers():
    """驗證序列化器"""
    issues = []
    
    try:
        from maiagent.chat.api.serializers import FlexibleMessageSerializer
        print("✅ FlexibleMessageSerializer 匯入成功")
        
        # 檢查必要字段
        serializer = FlexibleMessageSerializer()
        fields = serializer.fields.keys()
        required_fields = ['content', 'session_id', 'scenario_id']
        
        for field in required_fields:
            if field not in fields:
                issues.append(f"❌ FlexibleMessageSerializer 缺少字段：{field}")
            else:
                print(f"✅ 序列化器字段存在：{field}")
        
    except ImportError as e:
        issues.append(f"❌ 序列化器匯入失敗：{e}")
    
    return issues


def validate_views():
    """驗證視圖"""
    issues = []
    
    try:
        from maiagent.chat.api.views import SessionViewSet
        print("✅ SessionViewSet 匯入成功")
        
        # 檢查方法
        viewset = SessionViewSet()
        if hasattr(viewset, 'post_message'):
            print("✅ post_message 方法存在")
        else:
            issues.append("❌ post_message 方法不存在")
            
        if hasattr(viewset, 'post_message_no_session'):
            print("✅ post_message_no_session 方法存在")
        else:
            issues.append("❌ post_message_no_session 方法不存在")
        
    except ImportError as e:
        issues.append(f"❌ 視圖匯入失敗：{e}")
    
    return issues


def main():
    """主函數"""
    print("=====================================")
    print("MaiAgent API 測試驗證")
    print("=====================================\n")
    
    setup_django()
    
    all_issues = []
    
    # 驗證測試結構
    print("1. 檢查測試結構...")
    issues = validate_test_structure()
    all_issues.extend(issues)
    print()
    
    # 驗證模型
    print("2. 檢查模型...")
    issues = validate_models()
    all_issues.extend(issues)
    print()
    
    # 驗證序列化器
    print("3. 檢查序列化器...")
    issues = validate_serializers()
    all_issues.extend(issues)
    print()
    
    # 驗證視圖
    print("4. 檢查視圖...")
    issues = validate_views()
    all_issues.extend(issues)
    print()
    
    # 總結
    print("=====================================")
    if all_issues:
        print("❌ 發現問題：")
        for issue in all_issues:
            print(f"  {issue}")
        print(f"\n總計 {len(all_issues)} 個問題需要解決")
        sys.exit(1)
    else:
        print("✅ 所有驗證通過！測試環境設置正確")
        print("可以開始執行測試：python run_tests.py")
        sys.exit(0)


if __name__ == '__main__':
    main()