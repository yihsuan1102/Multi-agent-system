from __future__ import annotations

from datetime import datetime

from celery import shared_task

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


