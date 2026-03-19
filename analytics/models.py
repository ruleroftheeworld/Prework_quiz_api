from django.db import models
from django.conf import settings


class UserAnalytics(models.Model):
    """Denormalized per-user analytics, updated after each attempt."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analytics",
    )
    total_attempts = models.PositiveIntegerField(default=0)
    total_quizzes_completed = models.PositiveIntegerField(default=0)
    total_score_sum = models.FloatField(default=0.0)
    highest_score = models.FloatField(default=0.0)
    lowest_score = models.FloatField(default=100.0)

    # Weak topics stored as JSON list of {"topic": ..., "avg_score": ...}
    weak_topics = models.JSONField(default=list)

    # Per-difficulty breakdowns
    easy_attempts = models.PositiveIntegerField(default=0)
    easy_score_sum = models.FloatField(default=0.0)
    medium_attempts = models.PositiveIntegerField(default=0)
    medium_score_sum = models.FloatField(default=0.0)
    hard_attempts = models.PositiveIntegerField(default=0)
    hard_score_sum = models.FloatField(default=0.0)

    last_activity = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_analytics"

    def __str__(self):
        return f"Analytics({self.user.email})"

    @property
    def average_score(self):
        if self.total_quizzes_completed == 0:
            return 0.0
        return round(self.total_score_sum / self.total_quizzes_completed, 2)


class TopicScore(models.Model):
    """Per-topic score tracking for each user."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topic_scores",
    )
    topic = models.CharField(max_length=255)
    attempts = models.PositiveIntegerField(default=0)
    score_sum = models.FloatField(default=0.0)
    last_attempted = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_scores"
        unique_together = ("user", "topic")
        ordering = ["topic"]

    @property
    def average_score(self):
        if self.attempts == 0:
            return 0.0
        return round(self.score_sum / self.attempts, 2)
