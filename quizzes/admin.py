from django.contrib import admin
from .models import Quiz, Question, Option


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ["topic", "mode", "difficulty", "num_questions", "created_by", "is_active", "created_at"]
    list_filter = ["mode", "difficulty", "is_active"]
    search_fields = ["topic"]
    inlines = [QuestionInline]
    readonly_fields = ["id", "created_at", "updated_at", "ai_provider"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["quiz", "order", "text"]
    search_fields = ["text"]
    inlines = [OptionInline]
