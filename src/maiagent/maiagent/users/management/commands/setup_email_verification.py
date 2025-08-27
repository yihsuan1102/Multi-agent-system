"""
Setup email verification for all users.
This command ensures all users have verified email addresses.
"""

from django.core.management.base import BaseCommand
from allauth.account.models import EmailAddress
from maiagent.users.models import User


class Command(BaseCommand):
    help = 'Setup email verification for all users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--disable-verification',
            action='store_true',
            help='禁用電子郵件驗證要求',
        )
        parser.add_argument(
            '--verify-all',
            action='store_true', 
            help='將所有現有電子郵件地址設為已驗證',
        )
    
    def handle(self, *args, **options):
        if options['disable_verification']:
            self._disable_email_verification()
        
        if options['verify_all']:
            self._verify_all_emails()
        
        if not any([options['disable_verification'], options['verify_all']]):
            self.stdout.write(
                self.style.WARNING('請指定選項: --disable-verification 或 --verify-all')
            )
            self._show_current_status()
    
    def _disable_email_verification(self):
        """提示如何禁用電子郵件驗證"""
        self.stdout.write(
            self.style.SUCCESS('已在設定檔中將 ACCOUNT_EMAIL_VERIFICATION 設為 "none"')
        )
        self.stdout.write('請重啟 Django 服務以使設定生效：')
        self.stdout.write('docker compose -f docker-compose.local.yml restart django')
    
    def _verify_all_emails(self):
        """將所有電子郵件地址設為已驗證"""
        # 為沒有 EmailAddress 記錄的使用者建立記錄
        users_without_email_record = User.objects.exclude(
            emailaddress__isnull=False
        )
        
        for user in users_without_email_record:
            if user.email:
                EmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    verified=True,
                    primary=True
                )
                self.stdout.write(f'為使用者 {user.username} 建立已驗證的電子郵件記錄')
        
        # 更新所有現有記錄為已驗證
        updated_count = EmailAddress.objects.all().update(
            verified=True,
            primary=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ 已將 {updated_count} 個電子郵件地址設為已驗證')
        )
    
    def _show_current_status(self):
        """顯示目前的驗證狀態"""
        total_users = User.objects.count()
        verified_emails = EmailAddress.objects.filter(verified=True).count()
        unverified_emails = EmailAddress.objects.filter(verified=False).count()
        
        self.stdout.write('\n目前狀態:')
        self.stdout.write(f'  總使用者數: {total_users}')
        self.stdout.write(f'  已驗證電子郵件: {verified_emails}')
        self.stdout.write(f'  未驗證電子郵件: {unverified_emails}')
        
        if unverified_emails > 0:
            self.stdout.write(
                self.style.WARNING(f'\n有 {unverified_emails} 個電子郵件地址尚未驗證')
            )
            self.stdout.write('執行 --verify-all 來驗證所有電子郵件地址')