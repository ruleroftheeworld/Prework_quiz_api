import uuid
from django.db import models
from django.conf import settings
from quizzes.models import Quiz, Question


class Attempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Submitted"
        EXPIRED = "expired", "Expired"
        INVALIDATED = "invalidated", "Invalidated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)

    score = models.FloatField(null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Set for TEST mode")

    # TEST mode security tracking
    tab_switch_count = models.PositiveIntegerField(default=0)
    suspicious_activity = models.BooleanField(default=False)
    invalidation_reason = models.CharField(max_length=255, blank=True)

    # Current position for navigation
    current_question_order = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "attempts"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Attempt({self.user.email} | {self.quiz.topic} | {self.status})"

    @property
    def is_timed_out(self):
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False

    @property
    def score_percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 2)


class AttemptAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attempt_answers")
    selected_option = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now=True)
    hint_used = models.BooleanField(default=False)

    class Meta:
        db_table = "attempt_answers"
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"Answer(Q:{self.question_id} | {self.selected_option} | correct={self.is_correct})"
