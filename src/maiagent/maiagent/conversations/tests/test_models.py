import pytest

from django.utils import timezone

from maiagent.conversations.models import Scenario, Session, Message
from maiagent.users.models import User


@pytest.mark.django_db
def test_create_session_and_message():
    user = User.objects.create_user(username="u1", password="x")
    scenario = Scenario.objects.create(name="S1")
    session = Session.objects.create(user=user, scenario=scenario, title="T1")
    m1 = Message.objects.create(session=session, role=Message.ROLE_USER, content="hello", created_at=timezone.now())
    m2 = Message.objects.create(session=session, role=Message.ROLE_ASSISTANT, content="hi", created_at=timezone.now())
    assert session.messages.count() == 2
    assert m1.role == "user"
    assert m2.role == "assistant"


