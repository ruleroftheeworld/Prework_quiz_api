from rest_framework import serializers
from .models import Quiz, Question, Option


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "label", "text"]


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "hint", "options"]
        # correct_option & explanation intentionally excluded from default output


class QuestionWithAnswerSerializer(QuestionSerializer):
    """Used internally / after submission to reveal answers."""
    class Meta(QuestionSerializer.Meta):
        fields = QuestionSerializer.Meta.fields + ["correct_option", "explanation"]


class QuizListSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id", "topic", "description", "difficulty", "mode",
            "num_questions", "time_limit_minutes", "is_active",
            "question_count", "created_by_username", "created_at",
        ]

    def get_question_count(self, obj):
        return obj.questions.count()


class QuizDetailSerializer(QuizListSerializer):
    questions = serializers.SerializerMethodField()

    class Meta(QuizListSerializer.Meta):
        fields = QuizListSerializer.Meta.fields + ["questions"]

    def get_questions(self, obj):
        # In TEST mode we never expose hint/explanation from the detail endpoint
        questions = obj.questions.prefetch_related("options").order_by("order")
        return QuestionSerializer(questions, many=True).data


class QuizCreateSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=255)
    difficulty = serializers.ChoiceField(choices=Quiz.Difficulty.choices)
    mode = serializers.ChoiceField(choices=Quiz.Mode.choices)
    num_questions = serializers.IntegerField(min_value=1, max_value=50, default=10)
    time_limit_minutes = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs.get("mode") == Quiz.Mode.TEST and not attrs.get("time_limit_minutes"):
            raise serializers.ValidationError(
                {"time_limit_minutes": "TEST mode requires a time limit."}
            )
        return attrs
