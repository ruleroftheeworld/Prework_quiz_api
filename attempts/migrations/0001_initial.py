import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("quizzes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Attempt",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("in_progress", "In Progress"), ("submitted", "Submitted"), ("expired", "Expired"), ("invalidated", "Invalidated")], default="in_progress", max_length=20)),
                ("score", models.FloatField(blank=True, null=True)),
                ("total_questions", models.PositiveIntegerField(default=0)),
                ("correct_answers", models.PositiveIntegerField(default=0)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("tab_switch_count", models.PositiveIntegerField(default=0)),
                ("suspicious_activity", models.BooleanField(default=False)),
                ("invalidation_reason", models.CharField(blank=True, max_length=255)),
                ("current_question_order", models.PositiveIntegerField(default=1)),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="quizzes.quiz")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "attempts",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="AttemptAnswer",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("selected_option", models.CharField(blank=True, max_length=1)),
                ("is_correct", models.BooleanField(blank=True, null=True)),
                ("answered_at", models.DateTimeField(auto_now=True)),
                ("hint_used", models.BooleanField(default=False)),
                ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="attempts.attempt")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempt_answers", to="quizzes.question")),
            ],
            options={
                "db_table": "attempt_answers",
            },
        ),
        migrations.AlterUniqueTogether(
            name="attemptanswer",
            unique_together={("attempt", "question")},
        ),
    ]
