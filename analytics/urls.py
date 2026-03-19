from django.urls import path
from .views import MyAnalyticsView

urlpatterns = [
    path("me/", MyAnalyticsView.as_view(), name="my-analytics"),
]
