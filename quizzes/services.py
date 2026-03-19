import hashlib
import json
from django.conf import settings
from django.db import transaction

from .models import Quiz, Question, Option
from ai_service.service import AIService
from logs.services import LogService


class QuizService:

    @staticmethod
    @transaction.atomic
    def create_quiz(user, validated_data: dict) -> Quiz:
        """Generate quiz via AI and persist to database."""
        ai_service = AIService()

        questions_data = ai_service.generate_quiz(
            topic=validated_data["topic"],
            difficulty=validated_data["difficulty"],
            mode=validated_data["mode"],
            num_questions=validated_data["num_questions"],
            user_level=user.level,
            user_stream=user.stream,
        )

        quiz = Quiz.objects.create(
            created_by=user,
            topic=validated_data["topic"],
            description=validated_data.get("description", ""),
            difficulty=validated_data["difficulty"],
            mode=validated_data["mode"],
            num_questions=len(questions_data),
            time_limit_minutes=validated_data.get("time_limit_minutes"),
            ai_provider=settings.AI_PROVIDER,
        )

        QuizService._persist_questions(quiz, questions_data)

        LogService.log(
            action="quiz_created",
            user=user,
            metadata={
                "quiz_id": str(quiz.id),
                "topic": quiz.topic,
                "mode": quiz.mode,
                "difficulty": quiz.difficulty,
                "num_questions": quiz.num_questions,
            },
        )
        return quiz

    @staticmethod
    def _persist_questions(quiz: Quiz, questions_data: list) -> None:
        for idx, q_data in enumerate(questions_data, start=1):
            question = Question.objects.create(
                quiz=quiz,
                text=q_data["question"],
                order=idx,
                correct_option=q_data["correct_option"],
                explanation=q_data.get("explanation", ""),
                hint=q_data.get("hint", ""),
                difficulty=q_data.get("difficulty", "medium"),
            )
            for label, text in q_data["options"].items():
                Option.objects.create(
                    question=question,
                    label=label,
                    text=text,
                )

    @staticmethod
    def get_quiz_or_404(quiz_id: str) -> Quiz:
        try:
            return (
                Quiz.objects.prefetch_related("questions__options")
                .select_related("created_by")
                .get(pk=quiz_id, is_active=True)
            )
        except Quiz.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Quiz not found.")

    @staticmethod
    @transaction.atomic
    def delete_quiz(quiz_id: str, deleted_by) -> None:
        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Quiz not found.")
        topic = quiz.topic
        quiz.delete()
        LogService.log(
            action="admin_deleted_quiz",
            user=deleted_by,
            metadata={"quiz_id": str(quiz_id), "topic": topic},
        )
