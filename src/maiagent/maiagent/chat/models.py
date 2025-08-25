import uuid
from typing import Any, Dict

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max


def validate_scenario_config_json(config: Dict[str, Any]) -> None:
    required_keys = {"prompt", "llm", "memory"}
    if not isinstance(config, dict):
        raise ValidationError("config_json 必須為物件")
    missing = required_keys - set(config.keys())
    if missing:
        raise ValidationError(f"config_json 缺少必要鍵: {', '.join(sorted(missing))}")


class Group(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_group"
        verbose_name = "Group"
        verbose_name_plural = "Groups"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class LlmModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    provider = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    params = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_llm_model"
        unique_together = ("provider", "name")
        indexes = [models.Index(fields=["provider", "name"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.provider}:{self.name}"


class Scenario(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    name = models.CharField(max_length=255, unique=True)
    config_json = models.JSONField(validators=[validate_scenario_config_json])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_scenario"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class ScenarioModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name="scenario_models")
    llm_model = models.ForeignKey(LlmModel, on_delete=models.PROTECT, related_name="scenario_bindings")
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "chat_scenario_model"
        unique_together = ("scenario", "llm_model")
        indexes = [models.Index(fields=["scenario", "is_default"])]


class Session(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "Active", "Active"
        WAITING = "Waiting", "Waiting"
        REPLYED = "Replyed", "Replyed"
        CLOSED = "Closed", "Closed"

    id = models.UUIDField(primary_key=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT, related_name="sessions")
    title = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    last_activity_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_session"
        indexes = [
            models.Index(fields=["user", "last_activity_at"]),
            models.Index(fields=["scenario", "status"]),
        ]


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "user"
        ASSISTANT = "assistant", "assistant"

    id = models.UUIDField(primary_key=True, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    sequence_number = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_message"
        unique_together = ("session", "sequence_number")
        indexes = [models.Index(fields=["session", "sequence_number"])]

    def save(self, *args: Any, **kwargs: Any) -> None:
        # 序號自動遞增（按 session 群組），避免競態：鎖住 Session 進行分配
        if self.sequence_number in (None, 0):
            with transaction.atomic():
                Session.objects.select_for_update().get(pk=self.session_id)
                max_seq = (
                    Message.objects.filter(session_id=self.session_id).aggregate(max_seq=Max("sequence_number"))
                )["max_seq"]
                self.sequence_number = (max_seq or 0) + 1
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class GroupScenarioAccess(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="scenario_accesses")
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name="group_accesses")

    class Meta:
        db_table = "chat_group_scenario_access"
        unique_together = ("group", "scenario")
        indexes = [models.Index(fields=["group", "scenario"])]


