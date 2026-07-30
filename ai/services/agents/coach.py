from .base import BaseAgent

class CoachAgent(BaseAgent):

    name = "coach"
    title = "Coach Financeiro"

    def run(self, context):

        return {
            "name": self.name,
            "title": "Coach Financeiro",
            "status": "coming_soon",
            "data": {},
            "recommendations": [
                "Em breve o Coach Financeiro estará disponível."
            ],
            "alerts": []
        }