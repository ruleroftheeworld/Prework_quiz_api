from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from users.permissions import IsAdmin, IsApprovedTeacher, IsStudent
from .models import Test, TestAttempt
from .services import TestService, TestAttemptService, TestAnalyticsService
from .serializers import (
    TestCreateSerializer, TestDetailSerializer, TestListSerializer,
    EnrollStudentsSerializer, TestAttemptStartSerializer,
    AnswerSubmitSerializer, TestAttemptResultSerializer,
    StudentBreakdownSerializer, TestAnalyticsSerializer,
)


# ── Teacher Views ────────────────────────────────────────────────────────────

class TestListCreateView(APIView):
    permission_classes = [IsApprovedTeacher]

    def get(self, request):
        tests = Test.objects.filter(teacher=request.user).select_related("analytics")
        paginator = PageNumberPagination(); paginator.page_size = 20
        page = paginator.paginate_queryset(tests, request)
        return paginator.get_paginated_response(TestListSerializer(page, many=True).data)

    def post(self, request):
        serializer = TestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            test = TestService.create_test(request.user, serializer.validated_data)
        except RuntimeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(TestDetailSerializer(test).data, status=status.HTTP_201_CREATED)


class TestDetailView(APIView):
    permission_classes = [IsApprovedTeacher]

    def get(self, request, pk):
        test = TestService.get_test_for_teacher(pk, request.user)
        return Response(TestDetailSerializer(test).data)

    def patch(self, request, pk):
        test = TestService.get_test_for_teacher(pk, request.user)
        if test.status != Test.Status.DRAFT:
            return Response({"detail": "Only draft tests can be edited."},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = TestCreateSerializer(test, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TestDetailSerializer(test).data)

    def delete(self, request, pk):
        test = TestService.get_test_for_teacher(pk, request.user)
        if test.status != Test.Status.DRAFT:
            return Response({"detail": "Only draft tests can be deleted."},
                            status=status.HTTP_400_BAD_REQUEST)
        test.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EnrollStudentsView(APIView):
    permission_classes = [IsApprovedTeacher]

    def post(self, request, pk):
        test = TestService.get_test_for_teacher(pk, request.user)
        serializer = EnrollStudentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = TestService.enroll_students(
            test, serializer.validated_data["emails"], enrolled_by=request.user
        )
        return Response(result, status=status.HTTP_200_OK)


class ReleaseAnswersView(APIView):
    permission_classes = [IsApprovedTeacher]

    def post(self, request, pk):
        test = TestService.get_test_for_teacher(pk, request.user)
        test = TestService.release_answers(test, request.user)
        return Response({"answers_released": test.answers_released})


class TestAnalyticsView(APIView):
    permission_classes = [IsApprovedTeacher]

    def get(self, request, pk):
        test = TestService.get_test_for_teacher(pk, request.user)
        analytics = test.analytics
        return Response(TestAnalyticsSerializer(analytics).data)


class StudentBreakdownView(APIView):
    permission_classes = [IsApprovedTeacher]

    def get(self, request, pk):
        test = TestService.get_test_for_teacher(pk, request.user)
        ordering = request.query_params.get("sort", "-score")
        qs = TestAnalyticsService.get_student_breakdown(test, ordering)
        paginator = PageNumberPagination(); paginator.page_size = 50
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            StudentBreakdownSerializer(page, many=True).data
        )


# ── Student Views ────────────────────────────────────────────────────────────

class AvailableTestsView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        from django.utils import timezone
        from django.db.models import Q
        now = timezone.now()

        # Tests assigned to this student OR public tests in window
        assigned_test_ids = request.user.test_enrollments.values_list("test_id", flat=True)
        tests = Test.objects.filter(
            Q(id__in=assigned_test_ids) | Q(visibility=Test.Visibility.PUBLIC),
            status=Test.Status.ACTIVE,
            start_time__lte=now,
            end_time__gte=now,
        ).select_related("teacher")

        return Response(TestListSerializer(tests, many=True).data)


class StudentTestDetailView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, pk):
        try:
            test = Test.objects.select_related("quiz").get(pk=pk)
        except Test.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(TestDetailSerializer(test).data)


class StartTestAttemptView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        try:
            test = Test.objects.get(pk=pk)
        except Test.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            attempt = TestAttemptService.start_attempt(request.user, test)
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(TestAttemptStartSerializer(attempt).data, status=status.HTTP_201_CREATED)


class TestAnswerView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        attempt = _get_attempt_or_403(pk, request.user)
        serializer = AnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        TestAttemptService.save_answer(
            attempt,
            str(serializer.validated_data["question_id"]),
            serializer.validated_data["selected_option"],
        )
        # TEST mode — never reveal correctness during attempt
        return Response({"saved": True}, status=status.HTTP_200_OK)


class SubmitTestAttemptView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        attempt = _get_attempt_or_403(pk, request.user)
        attempt = TestAttemptService.submit_attempt(attempt)
        return Response(
            TestAttemptResultSerializer(attempt, context={"request": request}).data
        )


class TestResultView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, pk):
        attempt = _get_attempt_or_403(pk, request.user)
        return Response(
            TestAttemptResultSerializer(attempt, context={"request": request}).data
        )


class TestSecurityEventView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        attempt = _get_attempt_or_403(pk, request.user)
        event_type = request.data.get("event_type", "tab_switch")
        attempt = TestAttemptService.record_security_event(attempt, event_type)
        return Response({
            "tab_switch_count": attempt.tab_switch_count,
            "invalidated": attempt.status == TestAttempt.Status.INVALIDATED,
        })


def _get_attempt_or_403(test_id, user):
    try:
        return TestAttempt.objects.select_related("test__quiz", "student").get(
            test_id=test_id, student=user
        )
    except TestAttempt.DoesNotExist:
        from rest_framework.exceptions import NotFound
        raise NotFound("Attempt not found. Start the test first.")