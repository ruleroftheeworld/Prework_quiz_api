from django.urls import path
from .admin_views import AdminUserListCreateView, AdminUserDetailView, AdminUserScoresView

urlpatterns = [
    path("users/", AdminUserListCreateView.as_view(), name="admin-users"),
    path("users/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("users/<int:pk>/scores/", AdminUserScoresView.as_view(), name="admin-user-scores"),
]
