import requests

from .base_embedding import BaseEmbedding


class NomicEmbedding(BaseEmbedding):

    URL = "http://localhost:11434/api/embeddings"

    MODEL = "nomic-embed-text:latest"


    def embed(self, text):

        response = requests.post(

            self.URL,

            json={

                "model": self.MODEL,

                "prompt": text

            }

        )

        response.raise_for_status()

        return response.json()["embedding"]