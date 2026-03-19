from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .health import health_check

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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
