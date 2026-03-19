from django.urls import path
from .views import AdminLogsView

urlpatterns = [
    path("", AdminLogsView.as_view(), name="admin-logs"),
]
