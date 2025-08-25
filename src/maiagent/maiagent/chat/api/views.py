from __future__ import annotations

import json
import time
from typing import Any, Iterable

import requests
from django.conf import settings
from django.db.models import Prefetch, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from maiagent.chat.models import LlmModel, Message, Scenario, Session
from maiagent.chat.tasks import process_message

from .serializers import (
    CreateMessageSerializer,
    MessageSerializer,
    ScenarioSerializer,
    ScenarioUpsertSerializer,
    SessionDetailSerializer,
    SessionListSerializer,
)


class SessionViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    queryset: QuerySet[Session] = Session.objects.all().select_related("scenario").order_by("-last_activity_at")
    serializer_class = SessionListSerializer

    def get_queryset(self) -> QuerySet[Session]:
        user = self.request.user
        qs = self.queryset.filter(user=user)
        status_param = self.request.query_params.get("status")
        scenario_id = self.request.query_params.get("scenario_id")
        if status_param:
            qs = qs.filter(status=status_param)
        if scenario_id:
            qs = qs.filter(scenario_id=scenario_id)
        return qs

    def get_serializer_class(self):  # type: ignore[override]
        if self.action == "retrieve":
            return SessionDetailSerializer
        return super().get_serializer_class()

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        session: Session = self.get_object()
        session_qs = (
            Session.objects.select_related("scenario")
            .prefetch_related(Prefetch("messages", queryset=Message.objects.order_by("sequence_number")))
            .filter(pk=session.pk)
        )
        instance = session_qs.first()
        assert instance is not None
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="messages")
    def post_message(self, request: Request, pk: str | None = None) -> Response:
        session: Session = self.get_object()
        if session.status not in (Session.Status.ACTIVE, Session.Status.REPLYED):
            return Response(
                {"detail": "會話狀態不允許提交訊息"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CreateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        content: str = serializer.validated_data["content"]
        llm_model_id = serializer.validated_data.get("llm_model_id")

        # 建立使用者訊息
        message = Message.objects.create(session=session, role=Message.Role.USER, content=content)

        # 使用者可能選擇非預設 model（暫存用途，記錄一筆 LlmModel 使用行為）
        if llm_model_id:
            # 確認 LlmModel 存在
            get_object_or_404(LlmModel, pk=llm_model_id)

        # 更新 Session 狀態為 Waiting
        session.status = Session.Status.WAITING
        session.save(update_fields=["status", "last_activity_at"])

        # 送 Celery 任務
        try:
            process_message.delay(str(session.id), str(message.id))
        except Exception as exc:  # pragma: no cover - broker 失敗時回傳
            return Response(
                {"detail": f"Broker 任務派送失敗: {exc}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="polling")
    def polling(self, request: Request, pk: str | None = None) -> Response:
        session: Session = self.get_object()
        timeout_seconds = int(request.query_params.get("timeout", 30))
        deadline = time.monotonic() + max(1, min(timeout_seconds, 60))

        while time.monotonic() < deadline:
            session.refresh_from_db(fields=["status", "last_activity_at"])
            if session.status == Session.Status.REPLYED:
                last_assistant = (
                    Message.objects.filter(session=session, role=Message.Role.ASSISTANT)
                    .order_by("-sequence_number")
                    .first()
                )
                if last_assistant:
                    return Response(MessageSerializer(last_assistant).data, status=status.HTTP_200_OK)
                # 沒有找到助手訊息，稍候再試
            time.sleep(1.0)

        # 超時仍未回覆
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request: Request) -> Response:
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"detail": "缺少查詢關鍵字 q"}, status=status.HTTP_400_BAD_REQUEST)

        # 以 ES 作為預設搜尋，如不可用則依規格回傳 503
        es_url = getattr(settings, "ELASTICSEARCH_URL", None)
        if not es_url:
            return Response({"detail": "Elasticsearch 未設定"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            # 簡單查詢示範，實際 index 與 mapping 由資料同步負責
            resp = requests.get(
                f"{es_url}/messages/_search",
                headers={"Content-Type": "application/json"},
                data=json.dumps(
                    {
                        "size": 20,
                        "query": {"match": {"content": {"query": query}}},
                        "sort": [{"created_at": {"order": "desc"}}],
                    }
                ),
                timeout=5,
                verify=getattr(settings, "ELASTICSEARCH_VERIFY_SSL", False),
                auth=(
                    getattr(settings, "ELASTICSEARCH_USERNAME", None),
                    getattr(settings, "ELASTICSEARCH_PASSWORD", None),
                )
                if getattr(settings, "ELASTICSEARCH_USERNAME", None)
                else None,
            )
            if resp.status_code >= 500:
                return Response({"detail": "Elasticsearch 服務不可用"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            if resp.status_code == 404:
                # index 未建立
                return Response({"detail": "索引不存在"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            return Response({"detail": f"Elasticsearch 連線失敗: {exc}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        hits: Iterable[dict[str, Any]] = (data or {}).get("hits", {}).get("hits", [])
        results = [
            {
                "message_id": item.get("_id"),
                "score": item.get("_score"),
                "source": item.get("_source", {}),
            }
            for item in hits
        ]
        return Response({"results": results}, status=status.HTTP_200_OK)


class ScenarioViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin):
    queryset: QuerySet[Scenario] = Scenario.objects.all()
    serializer_class = ScenarioUpsertSerializer

    def get_serializer_class(self):  # type: ignore[override]
        if self.action in ("create", "update", "partial_update"):
            return ScenarioUpsertSerializer
        return ScenarioSerializer


