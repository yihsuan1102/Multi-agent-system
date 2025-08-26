"""
Clear all data from maiagent models.
This command provides selective data clearing options.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps


class Command(BaseCommand):
    help = 'Clear data from maiagent models'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='清空所有資料表',
        )
        parser.add_argument(
            '--chat-only',
            action='store_true',
            help='只清空 chat 相關資料',
        )
        parser.add_argument(
            '--users-only',
            action='store_true',
            help='只清空使用者資料',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='跳過確認提示（危險！）',
        )
    
    def handle(self, *args, **options):
        if not any([options['all'], options['chat_only'], options['users_only']]):
            self.stdout.write(
                self.style.ERROR('請指定清空範圍: --all, --chat-only, 或 --users-only')
            )
            return
        
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING('警告：此操作將刪除資料，無法復原！')
            )
            confirm = input('請輸入 "yes" 確認執行: ')
            if confirm.lower() != 'yes':
                self.stdout.write('已取消操作')
                return
        
        try:
            with transaction.atomic():
                if options['all'] or options['chat_only']:
                    self._clear_chat_data()
                
                if options['all'] or options['users_only']:
                    self._clear_users_data()
                
                self.stdout.write(
                    self.style.SUCCESS('✓ 資料清空完成')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'清空過程中發生錯誤: {e}')
            )
            raise
    
    def _clear_chat_data(self):
        """清空 chat 相關資料"""
        from maiagent.chat.models import (
            Message, Session, GroupScenarioAccess, 
            ScenarioModel, Scenario, LlmModel, Group
        )
        
        # 按照外鍵依賴順序刪除
        models_to_clear = [
            (Message, '訊息'),
            (Session, '會話'),
            (GroupScenarioAccess, '群組情境權限'),
            (ScenarioModel, '情境模型綁定'),
            (Scenario, '情境'),
            (LlmModel, 'LLM 模型'),
            (Group, '群組'),
        ]
        
        for model_class, name in models_to_clear:
            count = model_class.objects.count()
            if count > 0:
                model_class.objects.all().delete()
                self.stdout.write(f'已清空 {name}: {count} 筆')
    
    def _clear_users_data(self):
        """清空使用者資料"""
        from maiagent.users.models import User
        
        # 保留超級使用者
        regular_users = User.objects.filter(is_superuser=False)
        count = regular_users.count()
        if count > 0:
            regular_users.delete()
            self.stdout.write(f'已清空一般使用者: {count} 筆')
            
        superuser_count = User.objects.filter(is_superuser=True).count()
        if superuser_count > 0:
            self.stdout.write(f'保留超級使用者: {superuser_count} 筆')