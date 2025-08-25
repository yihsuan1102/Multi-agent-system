from __future__ import annotations

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Message
from .documents import MessageDocument


@receiver(post_save, sender=Message)
def index_message_on_save(sender, instance: Message, **kwargs):
    # Autosync is enabled, but keep explicit indexing as safety for bulk-disabled cases
    MessageDocument().update(instance)


@receiver(post_delete, sender=Message)
def delete_message_on_delete(sender, instance: Message, **kwargs):
    try:
        MessageDocument().delete(instance)
    except Exception:
        # Avoid raising in signals; ES may be unavailable
        pass


