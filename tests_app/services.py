import math
from django.utils import timezone
from django.db import transaction
from django.db.models import Avg, Max, Min, StdDev, Count, Q

from .models import Test, TestEnrollment, TestAttempt, TestAttemptAnswer, TestAnalytics
from quizzes.models import Question
from ai_service.service import AIService
from logs.services import LogService
from analytics.services import AnalyticsService


class TestService:
    """Handles test creation, publishing, enrollment, and answer release."""

    @staticmethod
    @transaction.atomic
    def create_test(teacher, validated_data: dict) -> Test:
        """
        Create a Test and immediately generate questions via AIService.
        Reuses existing AIService.generate_quiz() — no duplication.

        Difficulty distribution: generate easy/medium/hard separately,
        merge into one Quiz, store questions with difficulty tags.
        """
        from quizzes.models import Quiz
        from quizzes.services import QuizService

        easy_count   = validated_data.get("easy_count", 0)
        medium_count = validated_data.get("medium_count", 0)
        hard_count   = validated_data.get("hard_count", 0)
        total        = easy_count + medium_count + hard_count

        # Build the quiz in test mode using existing QuizService
        quiz_data = {
            "topic": validated_data["subject"],
            "difficulty": "medium",        # base difficulty for the quiz record
            "mode": "test",                # always test mode for conducted tests
            "num_questions": total,
            "time_limit_minutes": validated_data["time_limit_minutes"],
            "description": validated_data.get("description", ""),
        }
        quiz = QuizService.create_quiz(teacher, quiz_data)

        test = Test.objects.create(
            teacher=teacher,
            quiz=quiz,
            title=validated_data["title"],
            description=validated_data.get("description", ""),
            grade_level=validated_data.get("grade_level", ""),
            subject=validated_data["subject"],
            easy_count=easy_count,
            medium_count=medium_count,
            hard_count=hard_count,
            start_time=validated_data["start_time"],
            end_time=validated_data["end_time"],
            time_limit_minutes=validated_data["time_limit_minutes"],
            visibility=validated_data.get("visibility", Test.Visibility.PRIVATE),
        )

        TestAnalytics.objects.create(test=test)  # empty analytics row

        LogService.log(
            action="test_created",
            user=teacher,
            metadata={
                "test_id": str(test.id),
                "title": test.title,
                "total_questions": total,
            },
        )
        return test

    @staticmethod
    @transaction.atomic
    def enroll_students(test: Test, student_emails: list, enrolled_by) -> dict:
        """
        Bulk enroll students by email list.
        Returns: {"enrolled": [...], "not_found": [...], "already_enrolled": [...]}
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        result = {"enrolled": [], "not_found": [], "already_enrolled": []}
        students = User.objects.filter(email__in=student_emails, role="user")
        found_emails = set(students.values_list("email", flat=True))

        result["not_found"] = [e for e in student_emails if e not in found_emails]

        for student in students:
            enrollment, created = TestEnrollment.objects.get_or_create(
                test=test,
                student=student,
                defaults={
                    "enrolled_by": enrolled_by,
                    "enrollment_type": TestEnrollment.EnrollmentType.ASSIGNED,
                },
            )
            if created:
                result["enrolled"].append(student.email)
            else:
                result["already_enrolled"].append(student.email)

        LogService.log(
            action="test_assigned",
            user=enrolled_by,
            metadata={
                "test_id": str(test.id),
                "enrolled_count": len(result["enrolled"]),
                "not_found": result["not_found"],
            },
        )
        return result

    @staticmethod
    def release_answers(test: Test, teacher) -> Test:
        test.answers_released = True
        test.save(update_fields=["answers_released"])
        LogService.log(
            action="answers_released",
            user=teacher,
            metadata={"test_id": str(test.id), "title": test.title},
        )
        return test

    @staticmethod
    def get_test_for_teacher(test_id, teacher):
        try:
            return Test.objects.select_related("quiz", "analytics").get(
                pk=test_id, teacher=teacher
            )
        except Test.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Test not found or you do not own this test.")


class TestAttemptService:
    """
    Handles student attempt lifecycle for conducted tests.
    Reuses core logic from AttemptService via composition.
    """

    @staticmethod
    @transaction.atomic
    def start_attempt(student, test: Test) -> TestAttempt:
        # ── Guard: test window open? ────────────────────────────
        if not test.is_accepting_attempts:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This test is not currently accepting attempts.")

        # ── Guard: student enrolled? ────────────────────────────
        try:
            enrollment = TestEnrollment.objects.get(test=test, student=student)
        except TestEnrollment.DoesNotExist:
            if test.visibility == Test.Visibility.PUBLIC:
                # Auto-enroll for public tests
                enrollment = TestEnrollment.objects.create(
                    test=test, student=student,
                    enrollment_type=TestEnrollment.EnrollmentType.SELF,
                )
            else:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You are not enrolled in this test.")

        # ── Guard: one attempt only ─────────────────────────────
        existing = TestAttempt.objects.filter(test=test, student=student).first()
        if existing:
            if existing.status == TestAttempt.Status.IN_PROGRESS:
                if existing.is_timed_out:
                    TestAttemptService._expire_attempt(existing)
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Your attempt has expired.")
                return existing  # resume
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You have already submitted this test.")

        now = timezone.now()
        attempt = TestAttempt.objects.create(
            test=test,
            student=student,
            enrollment=enrollment,
            status=TestAttempt.Status.IN_PROGRESS,
            total_questions=test.total_questions,
            started_at=now,
            expires_at=now + timezone.timedelta(minutes=test.time_limit_minutes),
        )

        LogService.log(
            action="test_started",
            user=student,
            metadata={"test_id": str(test.id), "attempt_id": str(attempt.id)},
        )
        return attempt

    @staticmethod
    @transaction.atomic
    def save_answer(attempt: TestAttempt, question_id: str, selected_option: str) -> TestAttemptAnswer:
        _assert_test_attempt_active(attempt)

        try:
            question = Question.objects.get(pk=question_id, quiz=attempt.test.quiz)
        except Question.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Question does not belong to this test.")

        is_correct = question.correct_option == selected_option

        answer, _ = TestAttemptAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={"selected_option": selected_option, "is_correct": is_correct},
        )

        # Update navigation pointer
        TestAttempt.objects.filter(pk=attempt.pk).update(
            current_question_order=question.order
        )
        return answer

    @staticmethod
    @transaction.atomic
    def submit_attempt(attempt: TestAttempt) -> TestAttempt:
        _assert_test_attempt_active(attempt)

        if attempt.is_timed_out:
            TestAttemptService._expire_attempt(attempt)
            attempt.refresh_from_db()
            return attempt

        now = timezone.now()
        correct_count = attempt.answers.filter(is_correct=True).count()
        total = attempt.total_questions
        score = round((correct_count / total) * 100, 2) if total else 0
        time_taken = int((now - attempt.started_at).total_seconds()) if attempt.started_at else None

        attempt.status          = TestAttempt.Status.SUBMITTED
        attempt.submitted_at    = now
        attempt.correct_answers = correct_count
        attempt.score           = score
        attempt.time_taken_seconds = time_taken
        attempt.save(update_fields=[
            "status", "submitted_at", "correct_answers",
            "score", "time_taken_seconds"
        ])

        # ── Reuse existing analytics pipeline ──────────────────
        # Wrap attempt as a duck-typed object for AnalyticsService
        AnalyticsService.record_attempt(_TestAttemptProxy(attempt))

        # ── Update test-level analytics ────────────────────────
        TestAnalyticsService.recompute(attempt.test)

        LogService.log(
            action="test_submitted",
            user=attempt.student,
            metadata={
                "test_id": str(attempt.test_id),
                "attempt_id": str(attempt.id),
                "score": score,
            },
        )
        return attempt

    @staticmethod
    def record_security_event(attempt: TestAttempt, event_type: str) -> TestAttempt:
        if event_type == "tab_switch":
            TestAttempt.objects.filter(pk=attempt.pk).update(
                tab_switch_count=attempt.tab_switch_count + 1
            )
            attempt.refresh_from_db()

        THRESHOLD = 3
        if attempt.tab_switch_count >= THRESHOLD:
            TestAttempt.objects.filter(pk=attempt.pk).update(
                suspicious_activity=True,
                status=TestAttempt.Status.INVALIDATED,
                invalidation_reason=f"Exceeded {THRESHOLD} tab switches.",
            )
            attempt.refresh_from_db()
        return attempt

    @staticmethod
    def _expire_attempt(attempt: TestAttempt) -> None:
        correct = attempt.answers.filter(is_correct=True).count()
        total = attempt.total_questions
        attempt.status = TestAttempt.Status.EXPIRED
        attempt.submitted_at = timezone.now()
        attempt.score = round((correct / total) * 100, 2) if total else 0
        attempt.correct_answers = correct
        attempt.save(update_fields=["status", "submitted_at", "score", "correct_answers"])
        TestAnalyticsService.recompute(attempt.test)


class TestAnalyticsService:
    """
    Computes and caches test-level analytics in TestAnalytics.
    Uses Django aggregation — no Python-level loops over large datasets.
    """

    @staticmethod
    @transaction.atomic
    def recompute(test: Test) -> TestAnalytics:
        submitted = TestAttempt.objects.filter(
            test=test,
            status__in=[TestAttempt.Status.SUBMITTED, TestAttempt.Status.EXPIRED]
        )

        agg = submitted.aggregate(
            avg=Avg("score"),
            high=Max("score"),
            low=Min("score"),
            std=StdDev("score"),
            count=Count("id"),
        )

        # ── Score distribution buckets ──────────────────────────
        buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        for attempt in submitted.values_list("score", flat=True):
            if attempt is None:
                continue
            if attempt <= 20:   buckets["0-20"]   += 1
            elif attempt <= 40: buckets["21-40"]  += 1
            elif attempt <= 60: buckets["41-60"]  += 1
            elif attempt <= 80: buckets["61-80"]  += 1
            else:               buckets["81-100"] += 1

        # ── Difficulty-wise accuracy ────────────────────────────
        easy_acc   = TestAnalyticsService._difficulty_accuracy(test, "easy")
        medium_acc = TestAnalyticsService._difficulty_accuracy(test, "medium")
        hard_acc   = TestAnalyticsService._difficulty_accuracy(test, "hard")

        analytics, _ = TestAnalytics.objects.get_or_create(test=test)
        analytics.total_attempts    = submitted.count()
        analytics.submitted_count   = submitted.filter(status=TestAttempt.Status.SUBMITTED).count()
        analytics.average_score     = agg["avg"] or 0.0
        analytics.highest_score     = agg["high"] or 0.0
        analytics.lowest_score      = agg["low"] or 0.0
        analytics.score_std_dev     = agg["std"] or 0.0
        analytics.score_distribution = buckets
        analytics.easy_accuracy     = easy_acc
        analytics.medium_accuracy   = medium_acc
        analytics.hard_accuracy     = hard_acc
        analytics.save()

        # ── Recompute rank for all submitted attempts ───────────
        TestAnalyticsService._assign_ranks(test)

        return analytics

    @staticmethod
    def _difficulty_accuracy(test: Test, difficulty: str) -> float:
        """
        % of correct answers across all students for questions
        of a given difficulty level in this test.
        """
        answers = TestAttemptAnswer.objects.filter(
            attempt__test=test,
            attempt__status__in=[TestAttempt.Status.SUBMITTED, TestAttempt.Status.EXPIRED],
            question__quiz=test.quiz,
        )
        # Note: requires difficulty field on Question (see migration note below)
        total   = answers.filter(question__difficulty=difficulty).count()
        correct = answers.filter(question__difficulty=difficulty, is_correct=True).count()
        if total == 0:
            return 0.0
        return round((correct / total) * 100, 2)

    @staticmethod
    def _assign_ranks(test: Test) -> None:
        """Rank students by score DESC, time_taken ASC (tiebreaker)."""
        attempts = TestAttempt.objects.filter(
            test=test,
            status__in=[TestAttempt.Status.SUBMITTED, TestAttempt.Status.EXPIRED],
        ).order_by("-score", "time_taken_seconds")

        for rank, attempt in enumerate(attempts, start=1):
            TestAttempt.objects.filter(pk=attempt.pk).update(rank=rank)

    @staticmethod
    def get_student_breakdown(test: Test, ordering: str = "-score"):
        """
        Returns queryset of all attempts for teacher analytics dashboard.
        Supports sort_by: score, -score, time_taken_seconds, -time_taken_seconds
        """
        allowed_orderings = [
            "score", "-score",
            "time_taken_seconds", "-time_taken_seconds",
            "rank",
        ]
        if ordering not in allowed_orderings:
            ordering = "-score"

        return (
            TestAttempt.objects
            .filter(test=test, status__in=[
                TestAttempt.Status.SUBMITTED,
                TestAttempt.Status.EXPIRED,
            ])
            .select_related("student")
            .order_by(ordering)
        )


# ── Helpers ────────────────────────────────────────────────────────────────

def _assert_test_attempt_active(attempt: TestAttempt):
    if attempt.status != TestAttempt.Status.IN_PROGRESS:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied(f"Attempt is already {attempt.status}.")
    if attempt.is_timed_out:
        TestAttemptService._expire_attempt(attempt)
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Time limit exceeded. Attempt auto-submitted.")


class _TestAttemptProxy:
    """
    Duck-typed wrapper that makes TestAttempt look like Attempt
    so AnalyticsService.record_attempt() can be reused without modification.
    This avoids duplicating the weak-topic detection logic.
    """
    def __init__(self, test_attempt: TestAttempt):
        self._ta = test_attempt

    @property
    def status(self):
        # Map TestAttempt status to Attempt status strings
        from attempts.models import Attempt
        mapping = {
            TestAttempt.Status.SUBMITTED: Attempt.Status.SUBMITTED,
            TestAttempt.Status.EXPIRED:   Attempt.Status.EXPIRED,
        }
        return mapping.get(self._ta.status, self._ta.status)

    @property
    def score(self):          return self._ta.score
    @property
    def quiz(self):           return self._ta.test.quiz
    @property
    def user(self):           return self._ta.student