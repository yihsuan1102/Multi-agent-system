"""
Load initial fixtures for the maiagent system.
This command loads all fixture data in the correct order to avoid foreign key constraints.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction
from django.apps import apps


class Command(BaseCommand):
    help = 'Load all fixtures for maiagent system in correct order'
    
    # 定義載入順序（避免外鍵約束錯誤）
    FIXTURE_ORDER = [
        # 1. 先載入沒有外鍵依賴的基礎資料
        'maiagent/fixtures/chat/groups.json',
        'maiagent/fixtures/chat/llm_models.json',
        'maiagent/fixtures/chat/scenarios.json',
        
        # 2. 載入依賴基礎資料的關聯表
        'maiagent/fixtures/chat/scenario_models.json',
        
        # 3. 載入使用者資料（依賴 groups）
        'maiagent/fixtures/users/users.json',
        
        # 4. 載入群組權限設定
        'maiagent/fixtures/chat/group_scenario_access.json',
        
        # 5. 最後載入會話資料（依賴 users 和 scenarios）
        'maiagent/fixtures/chat/sessions.json',
        'maiagent/fixtures/chat/messages.json',
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='清空資料庫後再載入 fixtures（危險操作！）',
        )
        parser.add_argument(
            '--specific',
            type=str,
            help='只載入特定的 fixture 檔案（相對路徑）',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模擬執行，不實際載入資料',
        )
    
    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('模擬執行模式 - 不會實際載入資料')
            )
        
        if options['flush'] and not options['dry_run']:
            self.stdout.write(
                self.style.WARNING('警告：即將清空資料庫！')
            )
            confirm = input('請輸入 "yes" 確認清空資料庫: ')
            if confirm.lower() != 'yes':
                self.stdout.write('已取消操作')
                return
            
            self.stdout.write('清空資料庫...')
            call_command('flush', '--noinput')
        
        # 如果指定特定檔案
        if options['specific']:
            fixtures = [options['specific']]
        else:
            fixtures = self.FIXTURE_ORDER
        
        self.stdout.write(f'準備載入 {len(fixtures)} 個 fixture 檔案...')
        
        try:
            with transaction.atomic():
                for fixture_path in fixtures:
                    if options['dry_run']:
                        self.stdout.write(f'[模擬] 載入 {fixture_path}')
                        continue
                        
                    self.stdout.write(f'載入 {fixture_path}...')
                    try:
                        call_command('loaddata', fixture_path, verbosity=0)
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ 成功載入 {fixture_path}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'✗ 載入 {fixture_path} 失敗: {e}')
                        )
                        raise CommandError(f'載入 fixture 失敗: {e}')
                
                if not options['dry_run']:
                    self.stdout.write(
                        self.style.SUCCESS('✓ 所有 fixtures 載入完成！')
                    )
                    
                    # 自動設置電子郵件驗證
                    self._setup_email_verification()
                    
                    # 顯示載入統計
                    self._show_loading_stats()
                    
        except Exception as e:
            if not options['dry_run']:
                self.stdout.write(
                    self.style.ERROR(f'載入過程中發生錯誤，所有變更已回滾: {e}')
                )
            raise
    
    def _show_loading_stats(self):
        """顯示載入的資料統計"""
        from maiagent.chat.models import Group, LlmModel, Scenario, Session, Message
        from maiagent.users.models import User
        
        stats = {
            '群組': Group.objects.count(),
            'LLM 模型': LlmModel.objects.count(),
            '情境': Scenario.objects.count(),
            '使用者': User.objects.count(),
            '會話': Session.objects.count(),
            '訊息': Message.objects.count(),
        }
        
        self.stdout.write('\n資料載入統計:')
        for model_name, count in stats.items():
            self.stdout.write(f'  {model_name}: {count} 筆')
    
    def _setup_email_verification(self):
        """自動設置電子郵件驗證"""
        from allauth.account.models import EmailAddress
        from maiagent.users.models import User
        
        # 為沒有 EmailAddress 記錄的使用者建立已驗證記錄
        users_without_email_record = User.objects.exclude(
            emailaddress__isnull=False
        )
        
        created_count = 0
        for user in users_without_email_record:
            if user.email:
                EmailAddress.objects.get_or_create(
                    user=user,
                    email=user.email,
                    defaults={'verified': True, 'primary': True}
                )
                created_count += 1
        
        # 更新所有記錄為已驗證
        EmailAddress.objects.all().update(verified=True, primary=True)
        
        if created_count > 0:
            self.stdout.write(f'已為 {created_count} 個使用者建立已驗證的電子郵件記錄')