from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Scenario(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    langchain_config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scenario"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return self.name


class Session(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions"
    )
    scenario = models.ForeignKey(
        Scenario, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions"
    )
    title = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "session"
        indexes = [
            models.Index(fields=["user", "created_at"], name="idx_session_user_created"),
        ]
        ordering = ["-updated_at"]

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"{self.user_id}:{self.title}"


class Message(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_SYSTEM = "system"
    ROLE_CHOICES = (
        (ROLE_USER, "user"),
        (ROLE_ASSISTANT, "assistant"),
        (ROLE_SYSTEM, "system"),
    )

    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    token_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "message"
        indexes = [
            models.Index(fields=["session", "created_at"], name="idx_message_session_created"),
        ]
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"{self.session_id}:{self.role}:{self.created_at.isoformat()}"


