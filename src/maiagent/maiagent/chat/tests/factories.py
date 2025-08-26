import factory
import uuid
from django.contrib.auth import get_user_model
from factory import django

from maiagent.chat.models import Group, LlmModel, Message, Scenario, Session

User = get_user_model()


class GroupFactory(django.DjangoModelFactory):
    """測試用群組工廠"""
    
    class Meta:
        model = Group
    
    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Test Group {n}")
    description = factory.Faker("text", max_nb_chars=100)


class UserFactory(django.DjangoModelFactory):
    """測試用使用者工廠"""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"testuser{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.com")
    name = factory.Faker("name")
    is_active = True
    group = factory.SubFactory(GroupFactory)


class LlmModelFactory(django.DjangoModelFactory):
    """測試用 LLM 模型工廠"""
    
    class Meta:
        model = LlmModel
    
    id = factory.LazyFunction(uuid.uuid4)
    provider = factory.Iterator(["openai", "anthropic", "google"])
    name = factory.Iterator(["gpt-4", "claude-3", "gemini-pro"])
    params = factory.LazyFunction(lambda: {"temperature": 0.7, "max_tokens": 2000})


class ScenarioFactory(django.DjangoModelFactory):
    """測試用場景工廠"""
    
    class Meta:
        model = Scenario
    
    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Test Scenario {n}")
    config_json = factory.LazyFunction(lambda: {
        "prompt": {
            "system": "You are a helpful assistant",
            "user_template": "User: {user_input}"
        },
        "llm": {
            "provider": "openai", 
            "model": "gpt-4",
            "temperature": 0.7
        },
        "memory": {
            "type": "buffer",
            "window": 10
        }
    })


class SessionFactory(django.DjangoModelFactory):
    """測試用會話工廠"""
    
    class Meta:
        model = Session
    
    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    scenario = factory.SubFactory(ScenarioFactory)
    title = factory.Faker("sentence", nb_words=4)
    status = Session.Status.ACTIVE


class MessageFactory(django.DjangoModelFactory):
    """測試用訊息工廠"""
    
    class Meta:
        model = Message
    
    id = factory.LazyFunction(uuid.uuid4)
    session = factory.SubFactory(SessionFactory)
    role = Message.Role.USER
    content = factory.Faker("text", max_nb_chars=200)