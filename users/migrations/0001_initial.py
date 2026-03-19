from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("username", models.CharField(max_length=150, unique=True)),
                ("full_name", models.CharField(blank=True, max_length=255)),
                ("role", models.CharField(choices=[("user", "User"), ("admin", "Admin")], default="user", max_length=10)),
                ("level", models.CharField(choices=[("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced")], default="beginner", max_length=20)),
                ("stream", models.CharField(choices=[("computer_science", "Computer Science"), ("non_technical", "Non Technical")], default="computer_science", max_length=30)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_seen", models.DateTimeField(blank=True, null=True)),
                ("total_score", models.FloatField(default=0.0)),
                ("quizzes_taken", models.PositiveIntegerField(default=0)),
                ("groups", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "db_table": "users",
                "ordering": ["-date_joined"],
            },
        ),
    ]
