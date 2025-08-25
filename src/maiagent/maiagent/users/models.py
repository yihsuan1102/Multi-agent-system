from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, ForeignKey, SET_NULL
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Default custom user model for maiagent.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    class Role:
        ADMIN = "admin"
        SUPERVISOR = "supervisor"
        EMPLOYEE = "employee"
        CHOICES = (
            (ADMIN, "admin"),
            (SUPERVISOR, "supervisor"),
            (EMPLOYEE, "employee"),
        )
    role = CharField(max_length=32, choices=Role.CHOICES, default=Role.EMPLOYEE)
    # 群組邊界：管理員 group 可為 NULL
    group = ForeignKey("chat.Group", on_delete=SET_NULL, null=True, blank=True, related_name="users")
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
