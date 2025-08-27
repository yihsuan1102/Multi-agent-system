from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "chat"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("test/", TemplateView.as_view(template_name="chat/test_manual.html"), name="test"),
    path("debug/", TemplateView.as_view(template_name="chat/debug.html"), name="debug"),
    path("simple/", TemplateView.as_view(template_name="chat/simple_test.html"), name="simple"),
    path("", views.chat_room_view, name="room"),
]