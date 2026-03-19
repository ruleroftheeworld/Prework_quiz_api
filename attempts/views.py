from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from .models import Attempt
from .serializers import (
    AttemptStartSerializer,
    AttemptResumeSerializer,
    AnswerSubmitSerializer,
    AttemptResultSerializer,
    AttemptHistorySerializer,
    TabSwitchSerializer,
)
from .services import AttemptService


class StartAttemptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id):
        try:
            attempt = AttemptService.start_attempt(request.user, quiz_id)
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AttemptStartSerializer(attempt).data, status=status.HTTP_201_CREATED)


class AnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        attempt = AttemptService.get_attempt_or_403(pk, request.user)
        serializer = AnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Block hints in TEST mode
        hint_used = serializer.validated_data.get("hint_used", False)
        if hint_used and attempt.quiz.mode == "test":
            hint_used = False  # silently ignore, no error needed

        answer = AttemptService.save_answer(
            attempt=attempt,
            question_id=str(serializer.validated_data["question_id"]),
            selected_option=serializer.validated_data["selected_option"],
            hint_used=hint_used,
        )

        response_data = {
            "question_id": str(answer.question_id),
            "selected_option": answer.selected_option,
            "is_correct": answer.is_correct if attempt.quiz.mode == "learning" else None,
            "explanation": answer.question.explanation if attempt.quiz.mode == "learning" else None,
        }
        return Response(response_data, status=status.HTTP_200_OK)


class SubmitAttemptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        attempt = AttemptService.get_attempt_or_403(pk, request.user)
        attempt = AttemptService.submit_attempt(attempt)
        return Response(
            AttemptResultSerializer(attempt, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class ResumeAttemptView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        attempt = AttemptService.get_attempt_or_403(pk, request.user)
        return Response(AttemptResumeSerializer(attempt).data)


class AttemptHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Attempt.objects
            .filter(user=request.user)
            .select_related("quiz")
            .order_by("-started_at")
        )
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            AttemptHistorySerializer(page, many=True).data
        )


class SuspiciousEventView(APIView):
    """Endpoint to receive TEST mode security events from frontend."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        attempt = AttemptService.get_attempt_or_403(pk, request.user)
        serializer = TabSwitchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = AttemptService.record_suspicious_event(
            attempt, serializer.validated_data["event_type"]
        )
        return Response({
            "tab_switch_count": attempt.tab_switch_count,
            "invalidated": attempt.status == Attempt.Status.INVALIDATED,
        })
