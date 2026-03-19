from django.contrib import admin
from .models import UserAnalytics, TopicScore


@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    list_display = ["user", "total_quizzes_completed", "average_score", "highest_score", "last_activity"]
    search_fields = ["user__email"]
    readonly_fields = ["updated_at"]


@admin.register(TopicScore)
class TopicScoreAdmin(admin.ModelAdmin):
    list_display = ["user", "topic", "attempts", "average_score", "last_attempted"]
    search_fields = ["user__email", "topic"]
