from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import IsAdmin
from .serializers import UserAdminSerializer
from .services import UserService
from analytics.serializers import UserAnalyticsSummarySerializer
from analytics.services import AnalyticsService


class AdminUserListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdmin]
    serializer_class = UserAdminSerializer

    def get_queryset(self):
        return UserService.get_all_users(filters=self.request.query_params.dict())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.admin_create_user(serializer.validated_data, created_by=request.user)
        return Response(UserAdminSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdmin]
    serializer_class = UserAdminSerializer
    queryset = User.objects.all()

    def destroy(self, request, *args, **kwargs):
        UserService.delete_user(kwargs["pk"], deleted_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserScoresView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        summary = AnalyticsService.get_user_summary(user)
        return Response(summary)
