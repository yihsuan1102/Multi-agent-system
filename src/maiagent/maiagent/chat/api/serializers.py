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


class UserSerializer(serializers.Serializer[Any]):
    """簡化的用戶序列化器"""
    id = serializers.UUIDField()
    username = serializers.CharField()
    name = serializers.CharField()
    
    # 為了與API設計文件兼容，提供 first_name 和 last_name
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    
    def get_first_name(self, obj) -> str:
        """從 name 字段中提取名字"""
        if hasattr(obj, 'name') and obj.name:
            parts = obj.name.split(' ', 1)
            return parts[0] if parts else ""
        return ""
    
    def get_last_name(self, obj) -> str:
        """從 name 字段中提取姓氏"""
        if hasattr(obj, 'name') and obj.name:
            parts = obj.name.split(' ', 1)
            return parts[1] if len(parts) > 1 else ""
        return ""


class ScenarioListSerializer(serializers.ModelSerializer[Scenario]):
    """簡化的場景序列化器"""
    type = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    
    class Meta:
        model = Scenario
        fields = ["id", "name", "type", "description"]
    
    def get_type(self, obj: Scenario) -> str:
        """從 config_json 中取得類型，預設為 general"""
        config = obj.config_json or {}
        return config.get('type', 'general')
    
    def get_description(self, obj: Scenario) -> str:
        """從 config_json 中取得描述，預設為空字串"""
        config = obj.config_json or {}
        return config.get('description', '')


class SessionListSerializer(serializers.ModelSerializer[Session]):
    user = UserSerializer(read_only=True)
    scenario = ScenarioListSerializer(read_only=True)
    message_count = serializers.SerializerMethodField()
    started_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Session
        fields = [
            "id",
            "title",
            "user", 
            "scenario",
            "started_at",
            "last_activity_at",
            "status",
            "message_count",
        ]

    def get_message_count(self, obj: Session) -> int:
        """取得會話的訊息數量"""
        return obj.messages.count()


class MessageDetailSerializer(serializers.ModelSerializer[Message]):
    """詳細訊息序列化器"""
    message_type = serializers.CharField(source='role')
    parent_message_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            "id",
            "content", 
            "message_type",
            "sequence_number",
            "parent_message_id",
            "created_at",
        ]
    
    def get_parent_message_id(self, obj: Message) -> str | None:
        """取得前一條訊息的 ID (如果存在)"""
        if obj.sequence_number and obj.sequence_number > 1:
            previous_message = Message.objects.filter(
                session=obj.session,
                sequence_number=obj.sequence_number - 1
            ).first()
            return str(previous_message.id) if previous_message else None
        return None


class SessionDetailSerializer(serializers.ModelSerializer[Session]):
    user = UserSerializer(read_only=True)
    scenario = ScenarioSerializer(read_only=True)
    messages = MessageDetailSerializer(many=True, read_only=True)
    started_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Session
        fields = [
            "id",
            "title",
            "user",
            "scenario",
            "started_at",
            "last_activity_at", 
            "status",
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


