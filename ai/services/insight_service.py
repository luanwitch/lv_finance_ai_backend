from ai.services.prompt_builder import PromptBuilder
from ai.services.ollama_service import OllamaService


class InsightService:

    def generate(self, context):

        prompt = PromptBuilder.build(context)

        print("=" * 80)
        print(prompt)
        print("=" * 80)

        answer = OllamaService().generate(prompt)

        print("=" * 80)
        print(answer)
        print("=" * 80)
       

        return {

            "status": "success",

            "analysis": answer

        }