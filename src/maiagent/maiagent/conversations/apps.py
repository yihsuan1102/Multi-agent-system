from django.apps import AppConfig


class ConversationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "maiagent.conversations"
    verbose_name = "Conversations"

    def ready(self) -> None:  # pragma: no cover - import side effects
        # Import signals on startup
        from . import signals  # noqa: F401
        return super().ready()


