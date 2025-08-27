from __future__ import annotations

import json
import time
from typing import Any, Iterable

import requests
from django.conf import settings
from django.db.models import Prefetch, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.http import Http404
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
    CreateMessageSerializer,
    FlexibleMessageSerializer,
    MessageSerializer,
    ScenarioSerializer,
    ScenarioUpsertSerializer,
    ScenarioUpdateSerializer,
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
        
        # 驗證狀態參數
        if status_param:
            valid_statuses = [choice[0] for choice in Session.Status.choices]
            if status_param not in valid_statuses:
                return qs.none()
            qs = qs.filter(status=status_param)
            
        # 驗證場景 ID 格式
        if scenario_id:
            try:
                import uuid
                uuid.UUID(scenario_id)
                qs = qs.filter(scenario_id=scenario_id)
            except ValueError:
                return qs.none()
                
        return qs

    def get_serializer_class(self):  # type: ignore[override]
        if self.action == "retrieve":
            return SessionDetailSerializer
        return super().get_serializer_class()
    
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        API 3: 顯示所有會話
        GET /api/v1/conversations
        """
        try:
            # 驗證查詢參數
            self._validate_list_query_params(request)
            
            # 獲取分頁查詢集 (權限檢查由 filter_sessions_for_user 處理)
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_response = self.get_paginated_response(serializer.data)
                
                # 按照設計文件格式包裝響應
                response_data = {
                    "success": True,
                    "data": {
                        "conversations": paginated_response.data.get('results', []),
                        "pagination": {
                            "current_page": paginated_response.data.get('page', 1),
                            "page_size": paginated_response.data.get('page_size', 20),
                            "total_pages": paginated_response.data.get('total_pages', 1),
                            "total_count": paginated_response.data.get('count', 0)
                        },
                        "filters": self._get_available_filters(request.user)
                    },
                    "message": "會話列表取得成功",
                    "timestamp": timezone.now().isoformat()
                }
                return Response(response_data, status=status.HTTP_200_OK)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "success": True,
                "data": {
                    "conversations": serializer.data,
                    "filters": self._get_available_filters(request.user)
                },
                "message": "會話列表取得成功",
                "timestamp": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(
                {"detail": "查詢參數格式錯誤或未通過 Serializers 驗證", "errors": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {"detail": str(e) or "使用者 Role 沒有查看會話的權限"},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"detail": "伺服器遇到未預期的狀況"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _validate_list_query_params(self, request: Request) -> None:
        """驗證 list API 的查詢參數"""
        # 驗證 page 和 page_size 參數
        try:
            page = request.query_params.get('page')
            if page is not None:
                page_num = int(page)
                if page_num < 1:
                    raise ValidationError({"page": "頁數必須大於 0"})
        except ValueError:
            raise ValidationError({"page": "頁數必須為整數"})
            
        try:
            page_size = request.query_params.get('page_size')
            if page_size is not None:
                size_num = int(page_size)
                if size_num < 1 or size_num > 100:
                    raise ValidationError({"page_size": "每頁筆數必須在 1-100 之間"})
        except ValueError:
            raise ValidationError({"page_size": "每頁筆數必須為整數"})
            
        # 驗證 status 參數
        status_param = request.query_params.get('status')
        if status_param:
            valid_statuses = [choice[0] for choice in Session.Status.choices]
            if status_param not in valid_statuses:
                raise ValidationError({"status": f"狀態必須為: {', '.join(valid_statuses)}"})
        
        # 驗證 scenario_id 參數
        scenario_id = request.query_params.get('scenario_id')
        if scenario_id:
            try:
                import uuid
                uuid.UUID(scenario_id)
            except ValueError:
                raise ValidationError({"scenario_id": "場景 ID 格式不正確"})
                
        # 驗證 sort_by 和 sort_order 參數
        sort_by = request.query_params.get('sort_by')
        if sort_by:
            valid_sort_fields = ['started_at', 'last_activity_at', 'status']
            if sort_by not in valid_sort_fields:
                raise ValidationError({"sort_by": f"排序欄位必須為: {', '.join(valid_sort_fields)}"})
                
        sort_order = request.query_params.get('sort_order')
        if sort_order and sort_order not in ['asc', 'desc']:
            raise ValidationError({"sort_order": "排序方向必須為 asc 或 desc"})
    
    def _get_available_filters(self, user) -> dict[str, Any]:
        """取得可用的篩選選項"""
        available_statuses = [choice[0] for choice in Session.Status.choices]
        
        # 取得用戶可存取的場景
        available_scenarios = []
        if hasattr(user, 'group') and user.group:
            from maiagent.chat.models import GroupScenarioAccess
            scenario_accesses = GroupScenarioAccess.objects.filter(
                group=user.group
            ).select_related('scenario')
            
            available_scenarios = [
                {
                    "id": str(access.scenario.id),
                    "name": access.scenario.name
                }
                for access in scenario_accesses
            ]
        
        return {
            "available_statuses": available_statuses,
            "available_scenarios": available_scenarios
        }

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        API 4: 查詢特定會話
        GET /api/v1/conversations/{session_id}
        """
        try:
            # 驗證查詢參數
            self._validate_retrieve_query_params(request)
            
            # 獲取會話物件
            session: Session = self.get_object()
            
            # 檢查用戶是否有權限查看該會話
            if not filter_sessions_for_user(Session.objects.filter(pk=session.pk), request.user).exists():
                return Response(
                    {"detail": "使用者 Role 沒有查看該會話的權限"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 檢查是否包含訊息以及分頁參數
            include_messages = request.query_params.get('include_messages', 'true').lower() == 'true'
            message_limit = int(request.query_params.get('message_limit', 100))
            message_offset = int(request.query_params.get('message_offset', 0))
            
            # 使用基本的 retrieve 邏輯
            session_qs = (
                Session.objects.select_related("scenario", "user")
                .prefetch_related(Prefetch("messages", queryset=Message.objects.order_by("sequence_number")))
                .filter(pk=session.pk)
            )
            instance = session_qs.first()
            assert instance is not None
            
            # 序列化資料
            serializer = self.get_serializer(instance)
            serialized_data = serializer.data
            
            # 按照設計文件格式包裝響應
            response_data = {
                "success": True,
                "data": {
                    "session": serialized_data,
                },
                "message": "會話詳情取得成功",
                "timestamp": timezone.now().isoformat()
            }
            
            # 如果包含訊息，添加分頁資訊
            if include_messages:
                total_messages = len(serialized_data.get('messages', []))
                response_data["data"]["message_pagination"] = {
                    "offset": message_offset,
                    "limit": message_limit,
                    "total_count": total_messages,
                    "has_more": False
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(
                {"detail": "查詢參數格式錯誤或未通過 Serializers 驗證", "errors": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {"detail": str(e) or "使用者 Role 沒有查看該會話的權限"},
                status=status.HTTP_403_FORBIDDEN
            )
        except (Session.DoesNotExist, Http404):
            return Response(
                {"detail": "會話不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": "伺服器遇到未預期的狀況"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _validate_retrieve_query_params(self, request: Request) -> None:
        """驗證 retrieve API 的查詢參數"""
        # 驗證 include_messages 參數
        include_messages = request.query_params.get('include_messages')
        if include_messages is not None and include_messages.lower() not in ['true', 'false']:
            raise ValidationError({"include_messages": "必須為 true 或 false"})
        
        # 驗證 message_limit 參數
        try:
            message_limit = request.query_params.get('message_limit')
            if message_limit is not None:
                limit_num = int(message_limit)
                if limit_num < 0 or limit_num > 1000:
                    raise ValidationError({"message_limit": "訊息數量限制必須在 0-1000 之間"})
        except ValueError:
            raise ValidationError({"message_limit": "訊息數量限制必須為整數"})
        
        # 驗證 message_offset 參數  
        try:
            message_offset = request.query_params.get('message_offset')
            if message_offset is not None:
                offset_num = int(message_offset)
                if offset_num < 0:
                    raise ValidationError({"message_offset": "訊息偏移量必須大於或等於 0"})
        except ValueError:
            raise ValidationError({"message_offset": "訊息偏移量必須為整數"})

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        API 5: 刪除特定對話
        DELETE /api/v1/conversations/{session_id}
        """
        try:
            # 檢查會話是否存在
            try:
                session: Session = self.get_object()
            except (Session.DoesNotExist, Http404):
                return Response(
                    {"detail": "會話不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 檢查用戶是否有權限刪除該會話
            if not filter_sessions_for_user(Session.objects.filter(pk=session.pk), request.user).exists():
                return Response(
                    {"detail": "使用者沒有刪除該會話的權限"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 計算要刪除的訊息數量
            messages_count = session.messages.count()
            session_id = str(session.id)
            
            # 執行刪除操作（Django ORM 會自動處理級聯刪除）
            try:
                from django.db import transaction
                with transaction.atomic():
                    session.delete()
            except Exception as e:
                return Response(
                    {"detail": "資料庫服務超載或系統維護中"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # 按照設計文件格式返回刪除詳情
            response_data = {
                "success": True,
                "data": {
                    "deleted_session_id": session_id,
                    "deleted_messages_count": messages_count,
                    "deletion_timestamp": timezone.now().isoformat()
                },
                "message": "會話刪除成功",
                "timestamp": timezone.now().isoformat()
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except PermissionDenied as e:
            return Response(
                {"detail": str(e) or "使用者沒有刪除該會話的權限"},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"detail": "伺服器遇到未預期的狀況"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post_message(self, request: Request) -> Response:
        """
        彈性訊息提交 API - 支援現有會話或自動建立新會話
        POST /api/v1/conversations/messages/
        - 包含 session_id: 使用現有會話
        - 包含 scenario_id: 建立新會話
        """
        from django.db import transaction
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"post_message called with request.data={request.data}")

        # 統一使用 FlexibleMessageSerializer 進行完整驗證
        serializer = FlexibleMessageSerializer(data=request.data)
            
        if not serializer.is_valid():
            logger.error(f"Serializer validation failed: {serializer.errors}")
            return Response({"detail": "請求資料格式錯誤", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Serializer validated successfully: {serializer.validated_data}")
        
        content: str = serializer.validated_data["content"]
        request_session_id = serializer.validated_data.get("session_id")
        scenario_id = serializer.validated_data.get("scenario_id")
        llm_model_id = serializer.validated_data.get("llm_model_id")

        try:
            with transaction.atomic():
                # 案例1：請求體中有 session_id - 使用指定會話
                if request_session_id:
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

                # 案例2：建立新會話
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
                logger.info(f"Creating message: session={session.id}, content={content[:50]}")
                message = Message.objects.create(
                    session=session, 
                    role=Message.Role.USER, 
                    content=content
                )
                logger.info(f"Message created successfully: id={message.id}, sequence={message.sequence_number}")

                # 驗證 LLM model（如果有提供）
                if llm_model_id:
                    logger.info(f"Validating LLM model: {llm_model_id}")
                    llm_model = get_object_or_404(LlmModel, pk=llm_model_id)
                    logger.info(f"LLM model validated: {llm_model.provider}:{llm_model.name}")

                # 更新 Session 狀態為 Waiting
                logger.info(f"Updating session status to WAITING")
                session.status = Session.Status.WAITING
                session.save(update_fields=["status", "last_activity_at"])
                logger.info(f"Session updated successfully")

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
        return self.post_message(request)


class ScenarioViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin):
    queryset: QuerySet[Scenario] = Scenario.objects.all()
    serializer_class = ScenarioUpsertSerializer
    permission_classes = [CanManageScenarios]

    def get_serializer_class(self):  # type: ignore[override]
        if self.action in ("create", "update", "partial_update"):
            return ScenarioUpsertSerializer
        return ScenarioSerializer
    
    @action(detail=True, methods=["get"], url_path="models", permission_classes=[])
    def get_scenario_models(self, request: Request, pk: str | None = None) -> Response:
        """
        GET /api/v1/scenarios/{scenario_id}/models/
        獲取特定場景的可用 LLM 模型
        """
        try:
            scenario: Scenario = self.get_object()
            
            # 獲取此場景關聯的所有 LLM 模型
            from maiagent.chat.models import ScenarioModel
            scenario_models = ScenarioModel.objects.filter(
                scenario=scenario
            ).select_related('llm_model').order_by('-is_default', 'llm_model__provider', 'llm_model__name')
            
            models_data = []
            for sm in scenario_models:
                model = sm.llm_model
                models_data.append({
                    "id": str(model.id),
                    "provider": model.provider,
                    "name": model.name,
                    "display_name": f"{model.provider.title()} {model.name}",
                    "is_default": sm.is_default,
                    "params": model.params
                })
            
            return Response({
                "success": True,
                "data": {
                    "scenario_id": str(scenario.id),
                    "scenario_name": scenario.name,
                    "models": models_data
                },
                "message": "場景模型列表取得成功",
                "timestamp": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "detail": "取得場景模型時發生錯誤"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request: Request, pk: str | None = None) -> Response:
        """
        PUT /api/v1/scenarios/{scenario_id}
        更新場景設定 - 修改該 Scenario 對應的 ScenarioModel 之 model_id
        權限：admin、主管
        """
        try:
            # 獲取場景物件
            scenario: Scenario = self.get_object()
            
            # 驗證請求資料
            serializer = ScenarioUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "detail": "請求資料格式錯誤",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            model_id = serializer.validated_data["model_id"]
            
            # 獲取指定的 LLM 模型
            try:
                from maiagent.chat.models import LlmModel, ScenarioModel
                llm_model = get_object_or_404(LlmModel, pk=model_id)
            except LlmModel.DoesNotExist:
                return Response({
                    "success": False,
                    "detail": "指定的模型不存在"
                }, status=status.HTTP_404_NOT_FOUND)

            # 檢查或建立 ScenarioModel 記錄
            scenario_model, created = ScenarioModel.objects.get_or_create(
                scenario=scenario,
                llm_model=llm_model,
                defaults={'is_default': True}
            )
            
            # 如果該組合已存在，更新為預設
            if not created and not scenario_model.is_default:
                # 將其他模型設為非預設
                ScenarioModel.objects.filter(
                    scenario=scenario,
                    is_default=True
                ).update(is_default=False)
                
                # 設定目前模型為預設
                scenario_model.is_default = True
                scenario_model.save()

            elif created:
                # 新建立的模型，將其他模型設為非預設
                ScenarioModel.objects.filter(
                    scenario=scenario,
                    is_default=True
                ).exclude(pk=scenario_model.pk).update(is_default=False)

            return Response({
                "success": True,
                "data": {
                    "scenario_id": str(scenario.id),
                    "scenario_name": scenario.name,
                    "updated_model": {
                        "id": str(llm_model.id),
                        "provider": llm_model.provider,
                        "name": llm_model.name,
                        "display_name": f"{llm_model.provider.title()} {llm_model.name}",
                        "is_default": True
                    }
                },
                "message": "場景設定更新成功",
                "timestamp": timezone.now().isoformat()
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response({
                "success": False,
                "detail": str(e) or "權限不足"
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({
                "success": False,
                "detail": "伺服器遇到未預期的狀況"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


