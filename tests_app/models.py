import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from quizzes.models import Quiz, Question


class Test(models.Model):
    """
    A teacher-created, scheduled assessment.
    Wraps a Quiz (for questions) with scheduling,
    enrollment, and answer-release controls.
    """
    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private (invite only)"
        PUBLIC  = "public",  "Public (anyone can join)"

    class Status(models.TextChoices):
        DRAFT     = "draft",     "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        ACTIVE    = "active",    "Active"
        ENDED     = "ended",     "Ended"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conducted_tests",
        limit_choices_to={"role": "teacher"},
    )

    # ── Core metadata ──────────────────────────────────────────
    title        = models.CharField(max_length=255)
    description  = models.TextField(blank=True)
    grade_level  = models.CharField(max_length=100, blank=True,
                    help_text="e.g. Grade 10, Undergraduate Year 2")
    subject      = models.CharField(max_length=255)

    # ── Quiz link (reuses existing question generation) ────────
    # One Quiz is generated and owned by this Test.
    # Quiz.mode is always forced to "test" for conducted tests.
    quiz         = models.OneToOneField(
        Quiz,
        on_delete=models.CASCADE,
        related_name="conducted_test",
        null=True, blank=True,  # null until AI generation completes
    )

    # ── Difficulty distribution (used when generating quiz) ────
    easy_count   = models.PositiveIntegerField(default=0)
    medium_count = models.PositiveIntegerField(default=0)
    hard_count   = models.PositiveIntegerField(default=0)

    # ── Scheduling ─────────────────────────────────────────────
    start_time        = models.DateTimeField()
    end_time          = models.DateTimeField()
    time_limit_minutes = models.PositiveIntegerField()

    # ── Access control ─────────────────────────────────────────
    visibility   = models.CharField(max_length=10, choices=Visibility.choices,
                    default=Visibility.PRIVATE)
    status       = models.CharField(max_length=10, choices=Status.choices,
                    default=Status.DRAFT)

    # ── Post-test flags ────────────────────────────────────────
    answers_released = models.BooleanField(default=False,
                    help_text="When True, students see correct answers + explanations")

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["teacher"]),
            models.Index(fields=["status"]),
            models.Index(fields=["start_time", "end_time"]),
        ]

    def __str__(self):
        return f"{self.title} by {self.teacher.username}"

    @property
    def is_accepting_attempts(self):
        now = timezone.now()
        return (
            self.status == self.Status.ACTIVE
            and self.start_time <= now <= self.end_time
        )

    @property
    def total_questions(self):
        return self.easy_count + self.medium_count + self.hard_count


class TestEnrollment(models.Model):
    """
    Links a student to a test.
    For PRIVATE tests: teacher explicitly enrolls students.
    For PUBLIC tests: students self-enroll on first access.
    """
    class EnrollmentType(models.TextChoices):
        ASSIGNED  = "assigned",  "Assigned by Teacher"
        SELF      = "self",      "Self Enrolled"

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test       = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="enrollments")
    student    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_enrollments",
    )
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="teacher_enrollments",
        help_text="Teacher who assigned this, null if self-enrolled",
    )
    enrollment_type = models.CharField(
        max_length=10,
        choices=EnrollmentType.choices,
        default=EnrollmentType.ASSIGNED,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "test_enrollments"
        unique_together = ("test", "student")  # one enrollment per student per test
        indexes = [
            models.Index(fields=["test", "student"]),
            models.Index(fields=["student"]),
        ]


class TestAttempt(models.Model):
    """
    A student's attempt at a conducted test.

    DESIGN DECISION: We do NOT subclass the existing Attempt model
    because TestAttempt has different foreign keys (Test instead of Quiz)
    and additional teacher-side fields (time_taken, rank).

    However, we DELEGATE to AttemptService for core answer-saving
    and scoring logic — no duplication.
    """
    class Status(models.TextChoices):
        NOT_STARTED  = "not_started",  "Not Started"
        IN_PROGRESS  = "in_progress",  "In Progress"
        SUBMITTED    = "submitted",    "Submitted"
        EXPIRED      = "expired",      "Expired"
        INVALIDATED  = "invalidated",  "Invalidated"

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test       = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="attempts")
    student    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_attempts",
    )
    enrollment = models.OneToOneField(
        TestEnrollment,
        on_delete=models.CASCADE,
        related_name="attempt",
        null=True, blank=True,
    )

    status     = models.CharField(max_length=15, choices=Status.choices,
                    default=Status.NOT_STARTED)

    # ── Scoring ────────────────────────────────────────────────
    score               = models.FloatField(null=True, blank=True)
    total_questions     = models.PositiveIntegerField(default=0)
    correct_answers     = models.PositiveIntegerField(default=0)

    # ── Timing ─────────────────────────────────────────────────
    started_at          = models.DateTimeField(null=True, blank=True)
    submitted_at        = models.DateTimeField(null=True, blank=True)
    expires_at          = models.DateTimeField(null=True, blank=True)
    time_taken_seconds  = models.PositiveIntegerField(null=True, blank=True,
                            help_text="Actual seconds from start to submit")

    # ── Security ───────────────────────────────────────────────
    tab_switch_count    = models.PositiveIntegerField(default=0)
    suspicious_activity = models.BooleanField(default=False)
    invalidation_reason = models.CharField(max_length=255, blank=True)

    # ── Navigation ─────────────────────────────────────────────
    current_question_order = models.PositiveIntegerField(default=1)

    # ── Analytics snapshot (computed on submit, cached here) ───
    rank                = models.PositiveIntegerField(null=True, blank=True,
                            help_text="Rank within this test, computed after all submissions")

    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "test_attempts"
        unique_together = ("test", "student")  # one attempt per student per test
        ordering = ["-score", "time_taken_seconds"]  # natural leaderboard order
        indexes = [
            models.Index(fields=["test", "status"]),
            models.Index(fields=["test", "score"]),
            models.Index(fields=["student"]),
        ]

    @property
    def is_timed_out(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def score_percentage(self):
        if not self.total_questions:
            return 0.0
        return round((self.correct_answers / self.total_questions) * 100, 2)


class TestAttemptAnswer(models.Model):
    """
    Per-question answer for a TestAttempt.
    Mirrors AttemptAnswer but references TestAttempt and Question.
    NOT reusing AttemptAnswer model to keep TestAttempt self-contained
    and avoid FK conflicts.
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt         = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name="answers")
    question        = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="test_answers")
    selected_option = models.CharField(max_length=1, blank=True)
    is_correct      = models.BooleanField(null=True, blank=True)
    answered_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "test_attempt_answers"
        unique_together = ("attempt", "question")
        indexes = [
            models.Index(fields=["attempt"]),
        ]


class TestAnalytics(models.Model):
    """
    Aggregated analytics for a Test, computed and cached after submissions.
    Avoids expensive GROUP BY queries on every teacher dashboard load.
    """
    test             = models.OneToOneField(Test, on_delete=models.CASCADE,
                        related_name="analytics")

    total_attempts   = models.PositiveIntegerField(default=0)
    submitted_count  = models.PositiveIntegerField(default=0)

    # ── Score stats ────────────────────────────────────────────
    average_score    = models.FloatField(default=0.0)
    highest_score    = models.FloatField(default=0.0)
    lowest_score     = models.FloatField(default=100.0)
    score_std_dev    = models.FloatField(default=0.0)

    # ── Difficulty-wise correct % ──────────────────────────────
    easy_accuracy    = models.FloatField(default=0.0)
    medium_accuracy  = models.FloatField(default=0.0)
    hard_accuracy    = models.FloatField(default=0.0)

    # ── Score distribution buckets (JSON) ─────────────────────
    # e.g. {"0-20": 2, "21-40": 5, "41-60": 10, "61-80": 8, "81-100": 3}
    score_distribution = models.JSONField(default=dict)

    last_computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "test_analytics"
        