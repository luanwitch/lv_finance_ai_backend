from .base import BaseAgent
from ai.memory.memory_service import MemoryService


class FinancialInsightAgent(BaseAgent):

    name = "financial_insight"
    title = "Analista Financeiro IA"


    def run(self, context):

        memories = MemoryService.get_context(
            context.user,
            "problemas financeiros hábitos metas e comportamento"
        )

        recommendations = []

        if "dívida" in memories.lower():
            recommendations.append(
                "Priorize um plano para redução das dívidas."
            )

        if "gasto" in memories.lower():
            recommendations.append(
                "Analise seus gastos variáveis para encontrar oportunidades de economia."
            )

        return self.response(
            data={
                "memory_context": memories
            },
            recommendations=recommendations
        )