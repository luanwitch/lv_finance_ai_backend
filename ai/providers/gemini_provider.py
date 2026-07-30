from .base_provider import BaseProvider


class GeminiProvider(BaseProvider):

    def generate(self, prompt):

        raise NotImplementedError(
            "Gemini Provider ainda não implementado."
        )