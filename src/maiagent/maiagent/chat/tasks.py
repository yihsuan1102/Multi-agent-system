from __future__ import annotations

from datetime import datetime
import logging
import ssl

from celery import shared_task
from django.conf import settings
from django.db import connection
from redis import Redis

from .models import Message, Session


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_message(self, session_id: str, user_message_id: str) -> None:
    session = Session.objects.select_related("scenario").get(pk=session_id)

    # 這裡先以簡單回覆代替 LLM 呼叫
    reply_text = f"[auto-reply] 收到訊息於 {datetime.utcnow().isoformat()}Z"

    Message.objects.create(session=session, role=Message.Role.ASSISTANT, content=reply_text)

    # 更新 Session 狀態為 Replyed
    session.status = Session.Status.REPLYED
    session.save(update_fields=["status", "last_activity_at"])


@shared_task(bind=True, name="maiagent.chat.tasks.system_health_check", max_retries=0)
def system_health_check(self) -> dict:
    """簡易系統健康檢查：資料庫與 Redis broker。

    返回各服務狀態，僅做基本可用性檢查。
    """
    logger = logging.getLogger(__name__)
    results: dict = {"database": "unknown", "redis_broker": "unknown"}

    # Database health check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        results["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        results["database"] = f"error: {exc}"
        logger.exception("Database health check failed")

    # Redis (broker) health check
    try:
        if getattr(settings, "REDIS_SSL", False):
            client = Redis.from_url(settings.REDIS_URL, ssl_cert_reqs=ssl.CERT_NONE)
        else:
            client = Redis.from_url(settings.REDIS_URL)
        client.ping()
        results["redis_broker"] = "ok"
    except Exception as exc:  # noqa: BLE001
        results["redis_broker"] = f"error: {exc}"
        logger.exception("Redis health check failed")

    return results
