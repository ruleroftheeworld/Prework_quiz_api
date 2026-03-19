"""
Validates and normalises AI-generated quiz data.
"""

REQUIRED_KEYS = {"question", "options", "correct_option", "explanation", "hint"}
VALID_OPTIONS = {"A", "B", "C", "D"}


class AIResponseValidationError(Exception):
    pass


def validate_questions(data: list, expected_count: int) -> list:
    """
    Validate a list of question dicts coming from the AI.
    Returns cleaned list or raises AIResponseValidationError.
    """
    if not isinstance(data, list):
        raise AIResponseValidationError("Expected a JSON array at root level.")

    if len(data) == 0:
        raise AIResponseValidationError("AI returned an empty question list.")

    cleaned = []
    for idx, item in enumerate(data, start=1):
        try:
            cleaned.append(_validate_question(item, idx))
        except AIResponseValidationError as exc:
            raise AIResponseValidationError(f"Question {idx}: {exc}") from exc

    # Accept partial responses (at least 50% of requested count)
    min_acceptable = max(1, expected_count // 2)
    if len(cleaned) < min_acceptable:
        raise AIResponseValidationError(
            f"Only {len(cleaned)} valid questions returned; need at least {min_acceptable}."
        )

    return cleaned


def _validate_question(item: dict, idx: int) -> dict:
    if not isinstance(item, dict):
        raise AIResponseValidationError("Each question must be a JSON object.")

    missing = REQUIRED_KEYS - item.keys()
    if missing:
        raise AIResponseValidationError(f"Missing keys: {missing}")

    question_text = str(item["question"]).strip()
    if not question_text:
        raise AIResponseValidationError("'question' must not be empty.")

    options = item["options"]
    if not isinstance(options, dict):
        raise AIResponseValidationError("'options' must be a JSON object.")
    if set(options.keys()) != VALID_OPTIONS:
        raise AIResponseValidationError(f"'options' must have exactly keys A, B, C, D. Got: {set(options.keys())}")
    for label, text in options.items():
        if not str(text).strip():
            raise AIResponseValidationError(f"Option '{label}' must not be empty.")

    correct = str(item["correct_option"]).strip().upper()
    if correct not in VALID_OPTIONS:
        raise AIResponseValidationError(f"'correct_option' must be A/B/C/D. Got: {correct}")

    return {
        "question": question_text,
        "options": {k: str(v).strip() for k, v in options.items()},
        "correct_option": correct,
        "explanation": str(item.get("explanation", "")).strip(),
        "hint": str(item.get("hint", "")).strip(),
    }
