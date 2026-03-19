from rest_framework import serializers
from django.utils import timezone
from .models import Test, TestEnrollment, TestAttempt, TestAttemptAnswer, TestAnalytics
from quizzes.serializers import QuestionSerializer


class TestCreateSerializer(serializers.ModelSerializer):
    easy_count   = serializers.IntegerField(min_value=0, default=0)
    medium_count = serializers.IntegerField(min_value=0, default=0)
    hard_count   = serializers.IntegerField(min_value=0, default=0)

    class Meta:
        model = Test
        fields = [
            "title", "description", "subject", "grade_level",
            "easy_count", "medium_count", "hard_count",
            "start_time", "end_time", "time_limit_minutes", "visibility",
        ]

    def validate(self, attrs):
        total = attrs.get("easy_count", 0) + attrs.get("medium_count", 0) + attrs.get("hard_count", 0)
        if not self.partial:
            total = attrs.get("easy_count", 0) + attrs.get("medium_count", 0) + attrs.get("hard_count", 0)
            if total == 0:
                raise serializers.ValidationError("Total questions must be greater than 0.")
        if "start_time" in attrs and "end_time" in attrs:
            if attrs["start_time"] >= attrs["end_time"]:
                raise serializers.ValidationError("end_time must be after start_time.")
            if attrs["start_time"] < timezone.now():
                raise serializers.ValidationError("start_time cannot be in the past.")
        return attrs
        

class TestListSerializer(serializers.ModelSerializer):
    teacher_username = serializers.CharField(source="teacher.username", read_only=True)
    total_questions  = serializers.IntegerField(read_only=True)
    enrolled_count   = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = [
            "id", "title", "subject", "grade_level",
            "easy_count", "medium_count", "hard_count",
            "status", "visibility", "start_time", "end_time",
            "time_limit_minutes", "total_questions", "enrolled_count",
            "answers_released", "teacher_username", "created_at",
        ]

    def get_enrolled_count(self, obj):
        return obj.enrollments.count()


class TestDetailSerializer(TestListSerializer):
    questions = serializers.SerializerMethodField()

    class Meta(TestListSerializer.Meta):
        fields = TestListSerializer.Meta.fields + ["questions"]

    def get_questions(self, obj):
        if not obj.quiz:
            return []
        questions = obj.quiz.questions.prefetch_related("options").order_by("order")
        return QuestionSerializer(questions, many=True).data  # reused — no duplication


class EnrollStudentsSerializer(serializers.Serializer):
    emails = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1, max_length=500,
    )


class TestAttemptStartSerializer(serializers.ModelSerializer):
    test_title = serializers.CharField(source="test.title", read_only=True)
    time_remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model = TestAttempt
        fields = [
            "id", "test_title", "status", "total_questions",
            "current_question_order", "started_at", "expires_at",
            "time_remaining_seconds",
        ]

    def get_time_remaining_seconds(self, obj):
        if obj.expires_at:
            delta = obj.expires_at - timezone.now()
            return max(int(delta.total_seconds()), 0)
        return None


class AnswerSubmitSerializer(serializers.Serializer):
    question_id     = serializers.UUIDField()
    selected_option = serializers.ChoiceField(choices=["A", "B", "C", "D"])


class TestAttemptResultSerializer(serializers.ModelSerializer):
    test_title       = serializers.CharField(source="test.title", read_only=True)
    score_percentage = serializers.FloatField(read_only=True)
    answers          = serializers.SerializerMethodField()
    rank             = serializers.IntegerField(read_only=True)

    class Meta:
        model = TestAttempt
        fields = [
            "id", "test_title", "status", "score", "score_percentage",
            "total_questions", "correct_answers", "time_taken_seconds",
            "started_at", "submitted_at", "rank", "tab_switch_count",
            "suspicious_activity", "answers",
        ]

    def get_answers(self, obj):
        # Only show answers if teacher has released them
        if not obj.test.answers_released:
            return None
        return [
            {
                "question_id": str(a.question_id),
                "question_text": a.question.text,
                "selected_option": a.selected_option,
                "correct_option": a.question.correct_option,
                "is_correct": a.is_correct,
                "explanation": a.question.explanation,
            }
            for a in obj.answers.select_related("question").all()
        ]


class StudentBreakdownSerializer(serializers.ModelSerializer):
    """Per-student row for teacher analytics dashboard."""
    student_email    = serializers.EmailField(source="student.email", read_only=True)
    student_username = serializers.CharField(source="student.username", read_only=True)
    score_percentage = serializers.FloatField(read_only=True)
    accuracy_percent = serializers.FloatField(source="score_percentage", read_only=True)

    class Meta:
        model = TestAttempt
        fields = [
            "id", "student_email", "student_username",
            "score", "score_percentage", "accuracy_percent",
            "correct_answers", "total_questions",
            "time_taken_seconds", "rank", "status",
            "tab_switch_count", "suspicious_activity",
            "submitted_at",
        ]


class TestAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnalytics
        fields = [
            "total_attempts", "submitted_count",
            "average_score", "highest_score", "lowest_score", "score_std_dev",
            "easy_accuracy", "medium_accuracy", "hard_accuracy",
            "score_distribution", "last_computed_at",
        ]