from .base import BaseAgent


class InvestmentAgent(BaseAgent):

    name = "investment_agent"
    title = "Investimentos"


    def run(self, context):

        return self.response(
            data={
                "profile": "moderado"
            },
            recommendations=[
                "Criar reserva de emergência",
                "Investir mensalmente"
            ]
        )