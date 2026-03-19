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
            name="UserAnalytics",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("total_attempts", models.PositiveIntegerField(default=0)),
                ("total_quizzes_completed", models.PositiveIntegerField(default=0)),
                ("total_score_sum", models.FloatField(default=0.0)),
                ("highest_score", models.FloatField(default=0.0)),
                ("lowest_score", models.FloatField(default=100.0)),
                ("weak_topics", models.JSONField(default=list)),
                ("easy_attempts", models.PositiveIntegerField(default=0)),
                ("easy_score_sum", models.FloatField(default=0.0)),
                ("medium_attempts", models.PositiveIntegerField(default=0)),
                ("medium_score_sum", models.FloatField(default=0.0)),
                ("hard_attempts", models.PositiveIntegerField(default=0)),
                ("hard_score_sum", models.FloatField(default=0.0)),
                ("last_activity", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="analytics", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "user_analytics",
            },
        ),
        migrations.CreateModel(
            name="TopicScore",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("topic", models.CharField(max_length=255)),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("score_sum", models.FloatField(default=0.0)),
                ("last_attempted", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="topic_scores", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "topic_scores",
                "ordering": ["topic"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="topicscore",
            unique_together={("user", "topic")},
        ),
    ]
