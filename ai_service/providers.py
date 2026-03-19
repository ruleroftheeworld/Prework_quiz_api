"""
Thin wrappers around each AI provider.
Each caller accepts (system_prompt, user_prompt) and returns raw text.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiCaller:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set in your .env file. "
                "Get a free key at https://aistudio.google.com/app/apikey"
            )
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # NOTE: Do NOT pass system_instruction= here — it requires SDK >= 0.5
        # and causes TypeError on older installs. We prepend it into the prompt instead.
        self._model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    def call(self, system_prompt: str, user_prompt: str) -> str:
        # Combine system + user prompt into a single string (works with all SDK versions)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self._model.generate_content(full_prompt)
        return response.text


class OpenAICaller:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set in your .env file. "
                "Get a key at https://platform.openai.com/api-keys"
            )
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def call(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content


class GroqCaller:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set in your .env file. "
                "Get a free key at https://console.groq.com/keys"
            )
        from groq import Groq
        self._client = Groq(api_key=settings.GROQ_API_KEY)

    def call(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content


def get_provider_caller():
    provider = settings.AI_PROVIDER.lower()
    if provider == "gemini":
        return GeminiCaller()
    elif provider == "openai":
        return OpenAICaller()
    elif provider == "groq":
        return GroqCaller()
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {provider}. Choose gemini, openai, or groq.")
