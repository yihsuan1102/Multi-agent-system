from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from rolepermissions.roles import assign_role

from maiagent.chat.models import Group
from maiagent.users.models import User
import uuid


class Command(BaseCommand):
    help = "建立測試使用者與群組：admin/supervisor/employee"

    @transaction.atomic
    def handle(self, *args, **options):
        # 建立群組
        group_abc, _ = Group.objects.get_or_create(name="ABC科技公司", defaults={"id": uuid.uuid4()})

        # 建立使用者
        admin_user, _ = User.objects.get_or_create(username="admin_user", defaults={"email": "admin@example.com"})
        admin_user.set_password("admin123")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.group = None
        admin_user.role = User.Role.ADMIN
        admin_user.save()
        assign_role(admin_user, "admin")

        supervisor_user, _ = User.objects.get_or_create(
            username="supervisor_user", defaults={"email": "supervisor@example.com"}
        )
        supervisor_user.set_password("supervisor123")
        supervisor_user.group = group_abc
        supervisor_user.role = User.Role.SUPERVISOR
        supervisor_user.save()
        assign_role(supervisor_user, "supervisor")

        employee_user, _ = User.objects.get_or_create(
            username="employee_user", defaults={"email": "employee@example.com"}
        )
        employee_user.set_password("employee123")
        employee_user.group = group_abc
        employee_user.role = User.Role.EMPLOYEE
        employee_user.save()
        assign_role(employee_user, "employee")

        self.stdout.write(self.style.SUCCESS("測試使用者已建立/更新完成"))


