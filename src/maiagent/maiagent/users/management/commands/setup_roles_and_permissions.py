from __future__ import annotations

from django.core.management.base import BaseCommand
from rolepermissions.roles import assign_role

from maiagent.users.models import User


class Command(BaseCommand):
    help = "初始化使用者角色（若存在 admin 使用者，指派 admin 角色）"

    def handle(self, *args, **options):
        # 基礎示範：將 is_superuser 的使用者指派 Admin 角色
        admins = User.objects.filter(is_superuser=True)
        count = 0
        for user in admins:
            assign_role(user, "admin")
            if user.role != User.Role.ADMIN:
                user.role = User.Role.ADMIN
                user.save(update_fields=["role"])
            count += 1
        self.stdout.write(self.style.SUCCESS(f"已指派 admin 角色：{count} 位使用者"))


