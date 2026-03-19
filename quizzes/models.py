import uuid
from django.db import models
from django.conf import settings


class Quiz(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    class Mode(models.TextChoices):
        LEARNING = "learning", "Learning"
        TEST = "test", "Test"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_quizzes",
    )
    topic = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.LEARNING)
    num_questions = models.PositiveIntegerField(default=10)
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Only for TEST mode")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # AI generation metadata
    ai_provider = models.CharField(max_length=50, blank=True)
    generation_prompt_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "quizzes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.topic} ({self.mode} | {self.difficulty})"


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True, help_text="Shown in LEARNING mode after answering")
    hint = models.TextField(blank=True, help_text="Available in LEARNING mode")
    correct_option = models.CharField(max_length=1)  # 'A', 'B', 'C', 'D'
    difficulty = models.CharField(
        max_length=10,
        choices=Quiz.Difficulty.choices,
        default=Quiz.Difficulty.MEDIUM,
        db_index=True,
    )

    class Meta:
        db_table = "questions"
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order}: {self.text[:60]}"


class Option(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=1)  # 'A', 'B', 'C', 'D'
    text = models.TextField()

    class Meta:
        db_table = "options"
        ordering = ["label"]
        unique_together = ("question", "label")

    def __str__(self):
        return f"{self.label}: {self.text[:50]}"
