"""
Reset user passwords for development/testing purposes.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from maiagent.users.models import User


class Command(BaseCommand):
    help = 'Reset all user passwords to a common development password'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='新密碼 (預設: admin123)',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='只重設特定使用者的密碼',
        )
    
    def handle(self, *args, **options):
        password = options['password']
        hashed_password = make_password(password)
        
        if options['user']:
            # 重設特定使用者密碼
            try:
                user = User.objects.get(username=options['user'])
                user.password = hashed_password
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 已重設使用者 {user.username} 的密碼')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ 找不到使用者: {options["user"]}')
                )
                return
        else:
            # 重設所有使用者密碼
            count = User.objects.all().update(password=hashed_password)
            self.stdout.write(
                self.style.SUCCESS(f'✓ 已重設 {count} 個使用者的密碼為: {password}')
            )
        
        # 顯示可用的使用者帳號
        self.stdout.write('\n可用的登入帳號:')
        for user in User.objects.all().order_by('username'):
            role_info = f"({user.role})" if hasattr(user, 'role') else ""
            self.stdout.write(f'  {user.username} - {user.name or user.email} {role_info}')