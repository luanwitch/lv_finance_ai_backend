from .base_provider import BaseProvider


class OpenAIProvider(BaseProvider):

    def generate(self, prompt):

        raise NotImplementedError(
            "OpenAI Provider ainda não implementado."
        )