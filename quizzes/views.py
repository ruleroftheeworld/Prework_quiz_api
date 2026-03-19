from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Quiz
from .serializers import (
    QuizCreateSerializer,
    QuizListSerializer,
    QuizDetailSerializer,
)
from .services import QuizService
from users.permissions import IsAdmin


class QuizListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Quiz.objects.filter(is_active=True).select_related("created_by").order_by("-created_at")

        # Filter by mode / difficulty
        mode = request.query_params.get("mode")
        difficulty = request.query_params.get("difficulty")
        topic = request.query_params.get("topic")
        if mode:
            qs = qs.filter(mode=mode)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if topic:
            qs = qs.filter(topic__icontains=topic)

        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)
        serializer = QuizListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            quiz = QuizService.create_quiz(request.user, serializer.validated_data)
        except ValueError as e:
            # Misconfigured AI key or provider
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except RuntimeError as e:
            # AI failed all retries
            return Response(
                {"detail": "Quiz generation failed. Please try again.", "error": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(QuizDetailSerializer(quiz).data, status=status.HTTP_201_CREATED)


class QuizDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        quiz = QuizService.get_quiz_or_404(pk)
        return Response(QuizDetailSerializer(quiz).data)

    def delete(self, request, pk):
        if not request.user.is_admin:
            return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)
        QuizService.delete_quiz(pk, deleted_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
