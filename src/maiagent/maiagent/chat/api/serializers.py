from __future__ import annotations

from typing import Any

from rest_framework import serializers

from maiagent.chat.models import LlmModel, Message, Scenario, Session


class LlmModelSerializer(serializers.ModelSerializer[LlmModel]):
    class Meta:
        model = LlmModel
        fields = ["id", "provider", "name", "params", "created_at"]


class ScenarioSerializer(serializers.ModelSerializer[Scenario]):
    class Meta:
        model = Scenario
        fields = ["id", "name", "config_json", "created_at"]


class MessageSerializer(serializers.ModelSerializer[Message]):
    class Meta:
        model = Message
        fields = [
            "id",
            "role",
            "content",
            "sequence_number",
            "created_at",
        ]
        read_only_fields = ["id", "sequence_number", "created_at"]


class SessionListSerializer(serializers.ModelSerializer[Session]):
    scenario = ScenarioSerializer(read_only=True)

    class Meta:
        model = Session
        fields = [
            "id",
            "title",
            "status",
            "last_activity_at",
            "scenario",
        ]


class SessionDetailSerializer(serializers.ModelSerializer[Session]):
    scenario = ScenarioSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Session
        fields = [
            "id",
            "title",
            "status",
            "last_activity_at",
            "scenario",
            "messages",
        ]


class CreateMessageSerializer(serializers.Serializer[Any]):
    content = serializers.CharField(allow_blank=False, trim_whitespace=True)
    llm_model_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        content: str = attrs.get("content", "")
        if not content.strip():
            raise serializers.ValidationError({"content": "訊息內容不可為空"})
        return attrs


class ScenarioUpsertSerializer(serializers.ModelSerializer[Scenario]):
    class Meta:
        model = Scenario
        fields = ["id", "name", "config_json"]


