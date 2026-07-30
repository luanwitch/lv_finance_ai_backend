import requests

from .base_provider import BaseProvider


class OllamaProvider(BaseProvider):

    MODEL = "qwen3.6"

    URL = "http://localhost:11434/api/generate"


    def generate(self, prompt):

        response = requests.post(

            self.URL,

            json={

                "model": self.MODEL,

                "prompt": prompt,

                "stream": False
            }

        )

        response.raise_for_status()

        return response.json()["response"]