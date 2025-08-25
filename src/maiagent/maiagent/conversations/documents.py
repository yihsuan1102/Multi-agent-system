from __future__ import annotations

from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry

from .models import Message


messages_index = Index("messages")
messages_index.settings(
    number_of_shards=1,
    number_of_replicas=0,
)


@registry.register_document
class MessageDocument(Document):
    session_id = fields.IntegerField(attr="session_id")
    user_id = fields.IntegerField(attr="session__user_id")
    scenario_id = fields.IntegerField(attr="session__scenario_id")

    class Index:
        name = "messages"

    class Django:
        model = Message
        fields = [
            "id",
            "role",
            "content",
            "token_count",
            "created_at",
        ]
        ignore_signals = False
        auto_refresh = True


