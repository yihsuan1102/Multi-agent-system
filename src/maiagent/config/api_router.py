from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from maiagent.users.api.views import UserViewSet
from maiagent.chat.api.views import ScenarioViewSet, SessionViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("v1/conversations", SessionViewSet, basename="conversation")
router.register("v1/scenarios", ScenarioViewSet, basename="scenario")


app_name = "api"
urlpatterns = router.urls
