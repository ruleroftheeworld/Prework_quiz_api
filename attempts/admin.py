from django.contrib import admin
from .models import Attempt, AttemptAnswer


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    readonly_fields = ["question", "selected_option", "is_correct", "hint_used", "answered_at"]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ["user", "quiz", "status", "score", "started_at", "submitted_at", "suspicious_activity"]
    list_filter = ["status", "suspicious_activity"]
    search_fields = ["user__email", "quiz__topic"]
    readonly_fields = ["id", "started_at"]
    inlines = [AttemptAnswerInline]
