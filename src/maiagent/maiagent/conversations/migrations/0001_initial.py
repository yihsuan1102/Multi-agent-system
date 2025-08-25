from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Scenario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128, unique=True)),
                ("description", models.TextField(blank=True)),
                ("langchain_config", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "scenario",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("is_archived", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("scenario", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sessions", to="conversations.scenario")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sessions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "session",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(fields=["user", "created_at"], name="idx_session_user_created"),
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("user", "user"), ("assistant", "assistant"), ("system", "system")], max_length=16)),
                ("content", models.TextField()),
                ("token_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="conversations.session")),
            ],
            options={
                "db_table": "message",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["session", "created_at"], name="idx_message_session_created"),
        ),
    ]


