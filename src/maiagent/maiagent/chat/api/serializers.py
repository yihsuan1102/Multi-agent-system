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


class FlexibleMessageSerializer(serializers.Serializer[Any]):
    """支援彈性 session 建立的訊息提交 serializer"""
    content = serializers.CharField(allow_blank=False, trim_whitespace=True)
    session_id = serializers.UUIDField(required=False, allow_null=True)
    scenario_id = serializers.UUIDField(required=False, allow_null=True)  # 新 session 需要
    llm_model_id = serializers.UUIDField(required=False, allow_null=True)
    message_type = serializers.CharField(default="user", read_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        content: str = attrs.get("content", "")
        session_id = attrs.get("session_id")
        scenario_id = attrs.get("scenario_id")
        
        if not content.strip():
            raise serializers.ValidationError({"content": "訊息內容不可為空"})
        
        # 如果沒有 session_id，則 scenario_id 為必填
        if not session_id and not scenario_id:
            raise serializers.ValidationError({
                "scenario_id": "建立新對話時需要指定場景 ID"
            })
        
        return attrs


