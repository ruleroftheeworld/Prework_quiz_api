from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[
                    ("user_registered", "User Registered"),
                    ("user_login", "User Login"),
                    ("quiz_created", "Quiz Created"),
                    ("quiz_started", "Quiz Started"),
                    ("answer_submitted", "Answer Submitted"),
                    ("quiz_completed", "Quiz Completed"),
                    ("attempt_invalidated", "Attempt Invalidated"),
                    ("admin_created_user", "Admin Created User"),
                    ("admin_deleted_user", "Admin Deleted User"),
                    ("admin_deleted_quiz", "Admin Deleted Quiz"),
                ], db_index=True, max_length=50)),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "activity_logs",
                "ordering": ["-timestamp"],
            },
        ),
    ]
