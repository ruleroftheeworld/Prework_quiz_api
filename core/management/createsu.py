import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Create superuser from environment variables"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        email = os.environ.get("SUPERUSER_EMAIL", "admin@admin.com")
        username = os.environ.get("SUPERUSER_USERNAME", "admin")
        password = os.environ.get("SUPERUSER_PASSWORD", "admin123")

        if User.objects.filter(email=email).exists():
            self.stdout.write(f"Superuser {email} already exists.")
            return

        User.objects.create_superuser(email=email, username=username, password=password)
        self.stdout.write(f"Superuser {email} created successfully.")
