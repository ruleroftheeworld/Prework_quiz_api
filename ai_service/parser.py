"""
Extracts and parses JSON from raw AI text responses.
Handles markdown code fences, leading/trailing text, etc.
"""
import json
import re

from .validators import AIResponseValidationError


def parse_response(raw_text: str) -> list:
    """
    Try multiple strategies to extract a JSON array from raw AI output.
    """
    if not raw_text or not raw_text.strip():
        raise AIResponseValidationError("AI returned an empty response.")

    # Strategy 1: direct JSON parse
    try:
        return _load_json(raw_text)
    except (json.JSONDecodeError, AIResponseValidationError):
        pass

    # Strategy 2: strip markdown code fences
    stripped = re.sub(r"```(?:json)?", "", raw_text).replace("```", "").strip()
    try:
        return _load_json(stripped)
    except (json.JSONDecodeError, AIResponseValidationError):
        pass

    # Strategy 3: extract the first [...] block
    match = re.search(r"\[.*\]", raw_text, re.DOTALL)
    if match:
        try:
            return _load_json(match.group())
        except (json.JSONDecodeError, AIResponseValidationError):
            pass

    raise AIResponseValidationError(
        "Could not extract a valid JSON array from the AI response. "
        f"Raw preview: {raw_text[:300]}"
    )


def _load_json(text: str) -> list:
    data = json.loads(text)
    if not isinstance(data, list):
        raise AIResponseValidationError("Parsed JSON is not an array.")
    return data
