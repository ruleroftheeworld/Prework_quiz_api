from django.utils import timezone
from django.db import transaction

from .models import UserAnalytics, TopicScore

WEAK_TOPIC_THRESHOLD = 60.0  # below this % is "weak"


class AnalyticsService:

    @staticmethod
    @transaction.atomic
    def record_attempt(attempt) -> None:
        """Called after an attempt is submitted or expired."""
        from attempts.models import Attempt

        if attempt.status not in (Attempt.Status.SUBMITTED, Attempt.Status.EXPIRED):
            return

        score = attempt.score or 0.0
        quiz = attempt.quiz
        user = attempt.user

        analytics, _ = UserAnalytics.objects.get_or_create(user=user)

        analytics.total_attempts += 1
        analytics.total_quizzes_completed += 1
        analytics.total_score_sum += score
        analytics.highest_score = max(analytics.highest_score, score)
        analytics.lowest_score = min(analytics.lowest_score, score)
        analytics.last_activity = timezone.now()

        difficulty = quiz.difficulty
        if difficulty == "easy":
            analytics.easy_attempts += 1
            analytics.easy_score_sum += score
        elif difficulty == "medium":
            analytics.medium_attempts += 1
            analytics.medium_score_sum += score
        elif difficulty == "hard":
            analytics.hard_attempts += 1
            analytics.hard_score_sum += score

        analytics.save()

        # Update per-topic score
        topic_score, _ = TopicScore.objects.get_or_create(user=user, topic=quiz.topic)
        topic_score.attempts += 1
        topic_score.score_sum += score
        topic_score.save()

        # Recompute weak topics
        AnalyticsService._refresh_weak_topics(user, analytics)

    @staticmethod
    def _refresh_weak_topics(user, analytics: UserAnalytics) -> None:
        weak = []
        topic_scores = TopicScore.objects.filter(user=user)
        for ts in topic_scores:
            if ts.average_score < WEAK_TOPIC_THRESHOLD:
                weak.append({"topic": ts.topic, "avg_score": ts.average_score})
        analytics.weak_topics = sorted(weak, key=lambda x: x["avg_score"])
        analytics.save(update_fields=["weak_topics"])

    @staticmethod
    def get_user_summary(user) -> dict:
        try:
            analytics = UserAnalytics.objects.get(user=user)
        except UserAnalytics.DoesNotExist:
            analytics = None

        return {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "level": user.level,
            "stream": user.stream,
            "total_quizzes": analytics.total_quizzes_completed if analytics else 0,
            "average_score": analytics.average_score if analytics else 0.0,
            "highest_score": analytics.highest_score if analytics else 0.0,
            "lowest_score": analytics.lowest_score if analytics else 0.0,
            "weak_topics": analytics.weak_topics if analytics else [],
            "last_activity": analytics.last_activity if analytics else None,
        }
