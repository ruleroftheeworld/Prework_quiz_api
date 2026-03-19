import uuid
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
            name="Quiz",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("topic", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("difficulty", models.CharField(choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")], default="medium", max_length=10)),
                ("mode", models.CharField(choices=[("learning", "Learning"), ("test", "Test")], default="learning", max_length=10)),
                ("num_questions", models.PositiveIntegerField(default=10)),
                ("time_limit_minutes", models.PositiveIntegerField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("ai_provider", models.CharField(blank=True, max_length=50)),
                ("generation_prompt_hash", models.CharField(blank=True, max_length=64)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_quizzes", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "quizzes",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("text", models.TextField()),
                ("order", models.PositiveIntegerField(default=0)),
                ("explanation", models.TextField(blank=True)),
                ("hint", models.TextField(blank=True)),
                ("correct_option", models.CharField(max_length=1)),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="quizzes.quiz")),
            ],
            options={
                "db_table": "questions",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Option",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("label", models.CharField(max_length=1)),
                ("text", models.TextField()),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="options", to="quizzes.question")),
            ],
            options={
                "db_table": "options",
                "ordering": ["label"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="option",
            unique_together={("question", "label")},
        ),
    ]
