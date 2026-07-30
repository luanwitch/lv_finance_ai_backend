import json

from ai.services.ollama_service import OllamaService


class ToolAgent:

    def detect(self, message):

        prompt = f"""
Você é um classificador.

Sua única função é decidir se o usuário quer executar
alguma ação.

Se SIM responda SOMENTE JSON.

Exemplo:

{{
    "tool":"create_transaction",
    "data":{{
        "title":"Mercado",
        "amount":120,
        "type":"expense"
    }}
}}

Se NÃO:

{{
    "tool":null,
    "data":null
}}

Mensagem:

{message}
"""

        response = OllamaService().generate(prompt)

        try:
            return json.loads(response)

        except Exception:

            return {
                "tool": None,
                "data": None
            }