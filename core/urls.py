from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .health import health_check
from django.http import JsonResponse

def setup_admin(request):
    import os
    from django.contrib.auth import get_user_model
    User = get_user_model()
    email = os.environ.get("SUPERUSER_EMAIL", "admin@test.com")
    username = os.environ.get("SUPERUSER_USERNAME", "admin")
    password = os.environ.get("SUPERUSER_PASSWORD", "QuizAdmin@2024!")
    if User.objects.filter(email=email).exists():
        return JsonResponse({"status": "already exists", "email": email})
    User.objects.create_superuser(email=email, username=username, password=password)
    return JsonResponse({"status": "created", "email": email})

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/auth/", include("users.urls")),
    path("api/quizzes/", include("quizzes.urls")),
    path("api/attempts/", include("attempts.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/admin/", include("users.admin_urls")),
    path("api/logs/", include("logs.urls")),
    path("api/tests/", include("tests_app.urls")),
    path("setup-admin/", setup_admin),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


