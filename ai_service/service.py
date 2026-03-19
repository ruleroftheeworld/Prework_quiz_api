"""
AIService: orchestrates prompt building, API calling, parsing, and validation.
Includes retry logic with exponential back-off.
"""
import logging
import time

from django.conf import settings

from .prompt_builder import build_prompt, SYSTEM_INSTRUCTION
from .providers import get_provider_caller
from .parser import parse_response
from .validators import validate_questions, AIResponseValidationError

logger = logging.getLogger(__name__)

MAX_RETRIES = getattr(settings, "AI_MAX_RETRIES", 3)
RETRY_DELAY_SECONDS = 2


class AIService:
    def __init__(self):
        self._caller = get_provider_caller()

    def generate_quiz(
        self,
        topic: str,
        difficulty: str,
        mode: str,
        num_questions: int,
        user_level: str,
        user_stream: str,
    ) -> list:
        """
        Generate quiz questions.
        Returns a validated list of question dicts.
        Raises RuntimeError if all retries fail.
        """
        prompt = build_prompt(
            topic=topic,
            difficulty=difficulty,
            mode=mode,
            num_questions=num_questions,
            user_level=user_level,
            user_stream=user_stream,
        )

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(
                    "AI generation attempt %d/%d | provider=%s | topic=%s",
                    attempt, MAX_RETRIES, settings.AI_PROVIDER, topic,
                )
                raw = self._caller.call(SYSTEM_INSTRUCTION, prompt)
                parsed = parse_response(raw)
                validated = validate_questions(parsed, expected_count=num_questions)
                logger.info("AI generation succeeded with %d questions.", len(validated))
                return validated

            except AIResponseValidationError as exc:
                last_error = exc
                logger.warning("Validation error on attempt %d: %s", attempt, exc)
            except Exception as exc:
                last_error = exc
                logger.error("AI API error on attempt %d: %s", attempt, exc)

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)

        raise RuntimeError(
            f"Quiz generation failed after {MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )
