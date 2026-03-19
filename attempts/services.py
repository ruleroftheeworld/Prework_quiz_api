from django.utils import timezone
from django.db import transaction
from datetime import timedelta

from .models import Attempt, AttemptAnswer
from quizzes.models import Quiz, Question
from logs.services import LogService
from analytics.services import AnalyticsService


class AttemptService:

    @staticmethod
    @transaction.atomic
    def start_attempt(user, quiz_id: str) -> Attempt:
        quiz = Quiz.objects.prefetch_related("questions").get(pk=quiz_id, is_active=True)

        # TEST MODE: only one attempt allowed
        if quiz.mode == Quiz.Mode.TEST:
            existing = Attempt.objects.filter(
                user=user,
                quiz=quiz,
                status__in=[Attempt.Status.SUBMITTED, Attempt.Status.IN_PROGRESS],
            ).first()
            if existing:
                if existing.status == Attempt.Status.IN_PROGRESS:
                    # Check timeout
                    if existing.is_timed_out:
                        AttemptService._expire_attempt(existing)
                        raise PermissionError("Your previous attempt expired.")
                    # Resume
                    return existing
                raise PermissionError("You have already completed this test. Re-attempts are not allowed.")

        # LEARNING MODE: can have multiple; resume if in-progress exists
        if quiz.mode == Quiz.Mode.LEARNING:
            in_progress = Attempt.objects.filter(
                user=user, quiz=quiz, status=Attempt.Status.IN_PROGRESS
            ).first()
            if in_progress:
                return in_progress

        expires_at = None
        if quiz.mode == Quiz.Mode.TEST and quiz.time_limit_minutes:
            expires_at = timezone.now() + timedelta(minutes=quiz.time_limit_minutes)

        attempt = Attempt.objects.create(
            user=user,
            quiz=quiz,
            total_questions=quiz.questions.count(),
            expires_at=expires_at,
        )

        LogService.log(
            action="quiz_started",
            user=user,
            metadata={
                "attempt_id": str(attempt.id),
                "quiz_id": str(quiz.id),
                "mode": quiz.mode,
                "topic": quiz.topic,
            },
        )
        return attempt

    @staticmethod
    @transaction.atomic
    def save_answer(attempt: Attempt, question_id: str, selected_option: str, hint_used: bool = False) -> AttemptAnswer:
        _assert_attempt_active(attempt)

        try:
            question = Question.objects.get(pk=question_id, quiz=attempt.quiz)
        except Question.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                f"Question {question_id} does not belong to this quiz. "
                "Make sure you are using question IDs from the correct quiz."
            )
        
        is_correct = question.correct_option == selected_option

        answer, _ = AttemptAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                "selected_option": selected_option,
                "is_correct": is_correct,
                "hint_used": hint_used,
            },
        )

        # Update navigation pointer
        Attempt.objects.filter(pk=attempt.pk).update(
            current_question_order=question.order
        )

        LogService.log(
            action="answer_submitted",
            user=attempt.user,
            metadata={
                "attempt_id": str(attempt.id),
                "question_id": str(question_id),
                "is_correct": is_correct,
            },
        )
        return answer

    @staticmethod
    @transaction.atomic
    def submit_attempt(attempt: Attempt) -> Attempt:
        _assert_attempt_active(attempt)

        if attempt.is_timed_out:
            AttemptService._expire_attempt(attempt)
            attempt.refresh_from_db()
            return attempt

        answers = attempt.answers.all()
        correct_count = answers.filter(is_correct=True).count()
        total = attempt.total_questions
        score = round((correct_count / total) * 100, 2) if total > 0 else 0

        attempt.status = Attempt.Status.SUBMITTED
        attempt.submitted_at = timezone.now()
        attempt.correct_answers = correct_count
        attempt.score = score
        attempt.save(update_fields=["status", "submitted_at", "correct_answers", "score"])

        # Update user aggregate stats
        from users.services import UserService
        UserService.update_score(attempt.user, score)

        # Update analytics
        AnalyticsService.record_attempt(attempt)

        LogService.log(
            action="quiz_completed",
            user=attempt.user,
            metadata={
                "attempt_id": str(attempt.id),
                "quiz_id": str(attempt.quiz_id),
                "score": score,
                "mode": attempt.quiz.mode,
            },
        )
        return attempt

    @staticmethod
    @transaction.atomic
    def record_suspicious_event(attempt: Attempt, event_type: str) -> Attempt:
        """Track tab switches and other TEST mode violations."""
        if attempt.quiz.mode != Quiz.Mode.TEST:
            return attempt

        if event_type == "tab_switch":
            Attempt.objects.filter(pk=attempt.pk).update(
                tab_switch_count=attempt.tab_switch_count + 1
            )
            attempt.refresh_from_db()

        THRESHOLD = 3
        if attempt.tab_switch_count >= THRESHOLD:
            Attempt.objects.filter(pk=attempt.pk).update(
                suspicious_activity=True,
                status=Attempt.Status.INVALIDATED,
                invalidation_reason=f"Exceeded {THRESHOLD} tab switches.",
            )
            attempt.refresh_from_db()
            LogService.log(
                action="attempt_invalidated",
                user=attempt.user,
                metadata={
                    "attempt_id": str(attempt.id),
                    "reason": attempt.invalidation_reason,
                    "event_type": event_type,
                },
            )
        return attempt

    @staticmethod
    def get_attempt_or_403(attempt_id: str, user):
        try:
            attempt = Attempt.objects.select_related("quiz", "user").get(pk=attempt_id)
        except Attempt.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Attempt not found.")
        if attempt.user != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Access denied.")
        return attempt

    @staticmethod
    def _expire_attempt(attempt: Attempt) -> None:
        attempt.status = Attempt.Status.EXPIRED
        attempt.submitted_at = timezone.now()
        # Score based on what was answered
        correct = attempt.answers.filter(is_correct=True).count()
        total = attempt.total_questions
        attempt.score = round((correct / total) * 100, 2) if total > 0 else 0
        attempt.correct_answers = correct
        attempt.save(update_fields=["status", "submitted_at", "score", "correct_answers"])


def _assert_attempt_active(attempt: Attempt):
    if attempt.status != Attempt.Status.IN_PROGRESS:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied(f"Attempt is already {attempt.status}.")
    if attempt.is_timed_out:
        AttemptService._expire_attempt(attempt)
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Time limit exceeded. Attempt auto-submitted.")
