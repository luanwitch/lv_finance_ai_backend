from .base import BaseAgent


class DebtAnalyzerAgent(BaseAgent):

    name = "debt_analyzer_agent"
    title = "Análise de Dívidas" 


    def run(self, context):

        # Futuramente:
        # - buscar dívidas cadastradas
        # - analisar juros
        # - calcular prioridade de pagamento
        # - sugerir renegociação
        # - criar plano de quitação

        debts = []


        total_debt = sum(
            debt.get("amount", 0)
            for debt in debts
        )


        recommendations = []
        alerts = []


        if total_debt > 0:

            alerts.append(
                "Você possui dívidas cadastradas que precisam de acompanhamento."
            )

            recommendations.extend([
                "Priorize dívidas com maiores juros.",
                "Evite criar novas parcelas enquanto reduz o saldo atual.",
                "Monte um plano mensal de quitação."
            ])

        else:

            recommendations.append(
                "Nenhuma dívida cadastrada. Continue mantendo uma boa organização financeira."
            )


        return {
            "status": "success",
            "total_debt": total_debt,
            "alerts": alerts,
            "recommendations": recommendations
        }