from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserAnalytics
from .serializers import UserAnalyticsSerializer


class MyAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        analytics, _ = UserAnalytics.objects.get_or_create(user=request.user)
        return Response(UserAnalyticsSerializer(analytics).data)
