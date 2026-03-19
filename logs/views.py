from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from users.permissions import IsAdmin
from .models import ActivityLog
from .serializers import ActivityLogSerializer


class AdminLogsView(ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = ActivityLogSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        qs = ActivityLog.objects.select_related("user").order_by("-timestamp")
        action = self.request.query_params.get("action")
        user_id = self.request.query_params.get("user_id")
        if action:
            qs = qs.filter(action=action)
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs
