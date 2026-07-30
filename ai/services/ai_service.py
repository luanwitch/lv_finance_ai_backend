from django.conf import settings

from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openai_provider import OpenAIProvider
from ai.providers.claude_provider import ClaudeProvider
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.deepseek_provider import DeepSeekProvider


class AIService:

    PROVIDERS = {

        "ollama": OllamaProvider,

        "openai": OpenAIProvider,

        "claude": ClaudeProvider,

        "gemini": GeminiProvider,

        "deepseek": DeepSeekProvider,
    }


    @classmethod
    def provider(cls):

        provider_name = getattr(
            settings,
            "AI_PROVIDER",
            "ollama"
        )

        provider_class = cls.PROVIDERS.get(
            provider_name,
            OllamaProvider
        )

        return provider_class()


    @classmethod
    def generate(cls, prompt):

        return cls.provider().generate(prompt)