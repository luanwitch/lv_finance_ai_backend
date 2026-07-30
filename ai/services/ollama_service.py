import requests


class OllamaService:

    BASE_URL = "http://localhost:11434/api/generate"
    MODEL = "qwen2.5:7b"

    def generate(self, prompt):

        response = requests.post(
            self.BASE_URL,
            json={
                "model": self.MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        print("STATUS:", response.status_code)
        print("RESPOSTA BRUTA:")
        print(response.text)

        response.raise_for_status()

        data = response.json()

        print(data)

        return data.get("response", "")