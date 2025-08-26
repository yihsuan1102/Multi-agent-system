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
from maiagent.users.permissions import (
    CanManageScenarios,
    filter_sessions_for_user,
    require_permission,
    user_has_scenario_access,
)

from .serializers import (
    FlexibleMessageSerializer,
    MessageSerializer,
    ScenarioSerializer,
    ScenarioUpsertSerializer,
    SessionDetailSerializer,
    SessionListSerializer,
)


class SessionViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    queryset: QuerySet[Session] = Session.objects.all().select_related("scenario", "user__group").order_by("-last_activity_at")
    serializer_class = SessionListSerializer

    def get_queryset(self) -> QuerySet[Session]:
        user = self.request.user
        qs = filter_sessions_for_user(self.queryset, user)
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
    @require_permission("send_message_to_scenario")  
    def post_message(self, request: Request, pk: str | None = None) -> Response:
        """
        彈性訊息提交 API - 支援現有會話或自動建立新會話
        POST /api/v1/conversations/{session_id}/messages/ (現有會話)
        POST /api/v1/conversations/messages/ (自動建立)
        """
        from django.db import transaction

        # 使用彈性 serializer
        serializer = FlexibleMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        content: str = serializer.validated_data["content"]
        request_session_id = serializer.validated_data.get("session_id")
        scenario_id = serializer.validated_data.get("scenario_id")
        llm_model_id = serializer.validated_data.get("llm_model_id")

        try:
            with transaction.atomic():
                # 案例1：URL 中有 pk (session_id) - 使用現有會話
                if pk:
                    session: Session = self.get_object()
                    # 檢查場景存取權
                    if not user_has_scenario_access(request.user, session.scenario_id):
                        return Response({"detail": "無場景存取權"}, status=status.HTTP_403_FORBIDDEN)
                    # 檢查會話狀態
                    if session.status not in (Session.Status.ACTIVE, Session.Status.REPLYED):
                        return Response(
                            {"detail": "會話狀態不允許提交訊息"}, status=status.HTTP_400_BAD_REQUEST
                        )

                # 案例2：請求體中有 session_id - 使用指定會話
                elif request_session_id:
                    try:
                        session = get_object_or_404(Session, pk=request_session_id)
                        # 檢查使用者權限
                        if not filter_sessions_for_user(Session.objects.filter(pk=session.pk), request.user).exists():
                            return Response(
                                {"detail": "無權限存取該會話"}, 
                                status=status.HTTP_403_FORBIDDEN
                            )
                        # 檢查場景存取權
                        if not user_has_scenario_access(request.user, session.scenario_id):
                            return Response({"detail": "無場景存取權"}, status=status.HTTP_403_FORBIDDEN)
                        # 檢查會話狀態
                        if session.status not in (Session.Status.ACTIVE, Session.Status.REPLYED):
                            return Response(
                                {"detail": "會話狀態不允許提交訊息"}, status=status.HTTP_400_BAD_REQUEST
                            )
                    except Session.DoesNotExist:
                        return Response({"detail": "會話不存在"}, status=status.HTTP_404_NOT_FOUND)

                # 案例3：建立新會話
                else:
                    if not scenario_id:
                        return Response(
                            {"detail": "建立新對話時需要指定場景 ID"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    scenario = get_object_or_404(Scenario, pk=scenario_id)
                    # 檢查場景存取權
                    if not user_has_scenario_access(request.user, scenario_id):
                        return Response({"detail": "無場景存取權"}, status=status.HTTP_403_FORBIDDEN)
                    
                    # 建立新會話
                    session = Session.objects.create(
                        user=request.user,
                        scenario=scenario,
                        status=Session.Status.ACTIVE
                    )

                # 建立使用者訊息
                message = Message.objects.create(
                    session=session, 
                    role=Message.Role.USER, 
                    content=content
                )

                # 驗證 LLM model（如果有提供）
                if llm_model_id:
                    get_object_or_404(LlmModel, pk=llm_model_id)

                # 更新 Session 狀態為 Waiting
                session.status = Session.Status.WAITING
                session.save(update_fields=["status", "last_activity_at"])

        except Exception as exc:
            return Response(
                {"detail": f"資料庫操作失敗: {exc}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 發送 Celery 任務
        try:
            process_message.delay(str(session.id), str(message.id))
        except Exception as exc:
            return Response(
                {"detail": f"訊息處理服務暫時不可用: {exc}"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # 回傳成功回應，包含 session_id（對新建立的會話特別有用）
        return Response({
            "session_id": str(session.id),
            "message": MessageSerializer(message).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="polling")
    @require_permission("use_scenario")
    def polling(self, request: Request, pk: str | None = None) -> Response:
        session: Session = self.get_object()
        # 可見性檢查
        if not filter_sessions_for_user(Session.objects.filter(pk=session.pk), request.user).exists():
            return Response({"detail": "無權限存取該會話"}, status=status.HTTP_403_FORBIDDEN)
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

    @action(detail=False, methods=["post"], url_path="messages")
    @require_permission("send_message_to_scenario")
    def post_message_no_session(self, request: Request) -> Response:
        """
        處理無 session_id 的訊息提交 - 路由到 post_message
        POST /api/v1/conversations/messages/
        """
        return self.post_message(request, pk=None)


class ScenarioViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin):
    queryset: QuerySet[Scenario] = Scenario.objects.all()
    serializer_class = ScenarioUpsertSerializer
    permission_classes = [CanManageScenarios]

    def get_serializer_class(self):  # type: ignore[override]
        if self.action in ("create", "update", "partial_update"):
            return ScenarioUpsertSerializer
        return ScenarioSerializer


