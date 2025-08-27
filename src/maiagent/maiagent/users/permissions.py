from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from rest_framework.permissions import BasePermission
from rolepermissions.checkers import has_permission

from maiagent.users.models import User


def filter_sessions_for_user(queryset: QuerySet, user: User) -> QuerySet:
    """根據角色回傳可見的 Session 查詢集。

    - 管理員：可見所有 Sessions
    - 主管：可見群組內所有 Sessions（同 group）
    - 員工：僅可見自己的 Sessions
    """
    if not user.is_authenticated:
        return queryset.none()
    if user.role == User.Role.ADMIN:
        return queryset
    if user.role == User.Role.SUPERVISOR and user.group_id:
        return queryset.filter(user__group_id=user.group_id)
    return queryset.filter(user=user)


def user_has_scenario_access(user: User, scenario_id: Any) -> bool:
    """檢查使用者是否可使用指定 scenario。

    規則：
    - 管理員：允許
    - 其他：檢查 GroupScenarioAccess 是否授權
    """
    if user.role == User.Role.ADMIN:
        return True
    if not user.group_id:
        return False
    from maiagent.chat.models import GroupScenarioAccess  # 避免循環引用

    return GroupScenarioAccess.objects.filter(group_id=user.group_id, scenario_id=scenario_id).exists()


class CanManageScenarios(BasePermission):
    """建立/更新場景的權限檢查。

    - create: 需要 `create_scenario`
    - update/partial_update: 需要 `modify_scenario`
      若使用者為 supervisor，僅允許更新群組內已授權的 scenario
    """

    def has_permission(self, request, view) -> bool:  # type: ignore[override]
        action = getattr(view, "action", None)
        if action == "create":
            return has_permission(request.user, "create_scenario")
        if action in {"update", "partial_update"}:
            return has_permission(request.user, "modify_scenario")
        return True

    def has_object_permission(self, request, view, obj) -> bool:  # type: ignore[override]
        action = getattr(view, "action", None)
        if action in {"update", "partial_update"}:
            user: User = request.user  # type: ignore[assignment]
            if user.role == User.Role.ADMIN:
                return True
            # 主管需為群組內授權之場景
            return user_has_scenario_access(user, getattr(obj, "id", None))
        return True


def require_permission(operation_name: str):
    """簡易裝飾器：檢查使用者是否擁有 operation 權限，否則回傳 403。"""

    def decorator(func):
        from functools import wraps
        from rest_framework.response import Response
        from rest_framework import status

        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not has_permission(request.user, operation_name):
                return Response({"detail": "權限不足"}, status=status.HTTP_403_FORBIDDEN)
            return func(self, request, *args, **kwargs)

        return wrapper

    return decorator


