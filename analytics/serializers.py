from rest_framework import serializers
from .models import UserAnalytics, TopicScore


class TopicScoreSerializer(serializers.ModelSerializer):
    average_score = serializers.FloatField(read_only=True)

    class Meta:
        model = TopicScore
        fields = ["topic", "attempts", "average_score", "last_attempted"]


class UserAnalyticsSerializer(serializers.ModelSerializer):
    average_score = serializers.FloatField(read_only=True)
    topic_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = UserAnalytics
        fields = [
            "total_attempts",
            "total_quizzes_completed",
            "average_score",
            "highest_score",
            "lowest_score",
            "weak_topics",
            "easy_attempts",
            "easy_score_sum",
            "medium_attempts",
            "medium_score_sum",
            "hard_attempts",
            "hard_score_sum",
            "last_activity",
            "topic_breakdown",
        ]

    def get_topic_breakdown(self, obj):
        topics = TopicScore.objects.filter(user=obj.user).order_by("topic")
        return TopicScoreSerializer(topics, many=True).data


class UserAnalyticsSummarySerializer(serializers.Serializer):
    """Used in admin views to show user performance."""
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    username = serializers.CharField()
    level = serializers.CharField()
    stream = serializers.CharField()
    total_quizzes = serializers.IntegerField()
    average_score = serializers.FloatField()
    highest_score = serializers.FloatField()
    lowest_score = serializers.FloatField()
    weak_topics = serializers.ListField(child=serializers.DictField())
    last_activity = serializers.DateTimeField(allow_null=True)
