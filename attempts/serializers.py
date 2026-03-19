from rest_framework import serializers
from django.utils import timezone
from .models import Attempt, AttemptAnswer

from quizzes.serializers import QuizDetailSerializer, QuestionSerializer, QuestionWithAnswerSerializer


class AttemptAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttemptAnswer
        fields = ["id", "question", "selected_option", "is_correct", "hint_used", "answered_at"]
        read_only_fields = ["id", "is_correct", "answered_at"]


class AnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_option = serializers.ChoiceField(choices=["A", "B", "C", "D"])
    hint_used = serializers.BooleanField(default=False)


class TabSwitchSerializer(serializers.Serializer):
    """Notify backend of a tab switch event in TEST mode."""
    event_type = serializers.ChoiceField(choices=["tab_switch", "blur", "copy_paste", "right_click"])


class AttemptStartSerializer(serializers.ModelSerializer):
    quiz_id = serializers.UUIDField(source="quiz.id", read_only=True)
    quiz_topic = serializers.CharField(source="quiz.topic", read_only=True)
    quiz_mode = serializers.CharField(source="quiz.mode", read_only=True)
    time_remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = [
            "id", "quiz_id", "quiz_topic", "quiz_mode", "status",
            "total_questions", "current_question_order",
            "started_at", "expires_at", "time_remaining_seconds",
        ]

    def get_time_remaining_seconds(self, obj):
        if obj.expires_at:
            delta = obj.expires_at - timezone.now()
            return max(int(delta.total_seconds()), 0)
        return None


class AttemptResumeSerializer(AttemptStartSerializer):
    answered_question_ids = serializers.SerializerMethodField()

    class Meta(AttemptStartSerializer.Meta):
        fields = AttemptStartSerializer.Meta.fields + ["answered_question_ids"]

    def get_answered_question_ids(self, obj):
        return list(
            obj.answers.values_list("question_id", flat=True).order_by("answered_at")
        )


class AttemptResultSerializer(serializers.ModelSerializer):
    quiz = QuizDetailSerializer(read_only=True)
    answers = serializers.SerializerMethodField()
    score_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Attempt
        fields = [
            "id", "quiz", "status", "score", "score_percentage",
            "total_questions", "correct_answers",
            "started_at", "submitted_at", "tab_switch_count",
            "suspicious_activity", "answers",
        ]

    def get_answers(self, obj):
        request = self.context.get("request")
        answers = obj.answers.select_related("question__quiz").prefetch_related("question__options")
        # Reveal correct answers only in learning mode or after submission
        if obj.quiz.mode == "learning" or obj.status == Attempt.Status.SUBMITTED:
            return _build_answer_detail(answers)
        return AttemptAnswerSerializer(answers, many=True).data


def _build_answer_detail(answers):
    result = []
    for ans in answers:
        q = ans.question
        result.append({
            "question_id": str(q.id),
            "question_text": q.text,
            "selected_option": ans.selected_option,
            "correct_option": q.correct_option,
            "is_correct": ans.is_correct,
            "explanation": q.explanation,
            "options": [{"label": o.label, "text": o.text} for o in q.options.all()],
        })
    return result


class AttemptHistorySerializer(serializers.ModelSerializer):
    quiz_topic = serializers.CharField(source="quiz.topic", read_only=True)
    quiz_mode = serializers.CharField(source="quiz.mode", read_only=True)
    quiz_difficulty = serializers.CharField(source="quiz.difficulty", read_only=True)
    score_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Attempt
        fields = [
            "id", "quiz_topic", "quiz_mode", "quiz_difficulty",
            "status", "score", "score_percentage",
            "total_questions", "correct_answers",
            "started_at", "submitted_at",
        ]
