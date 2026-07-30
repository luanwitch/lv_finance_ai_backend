from .base import BaseAgent


class InvoiceAgent(BaseAgent):

    name = "invoice_agent"
    title = "Contas" 

    def run(self, context):

        # Futuramente pode integrar:
        # - tabela Invoice
        # - pagamentos
        # - notificações
        # - calendário
        # - leitura de boletos via IA

        invoices = []

        pending = [
            invoice for invoice in invoices
            if invoice.get("status") == "pending"
        ]

        analysis = {
            "status": "success",
            "total_pending": len(pending),
            "alerts": [],
            "recommendations": []
        }


        if len(pending) > 0:

            analysis["alerts"].append(
                "Você possui contas pendentes próximas do vencimento."
            )

            analysis["recommendations"].append(
                "Priorize pagamentos com juros ou multas."
            )

        else:

            analysis["recommendations"].append(
                "Nenhuma conta pendente encontrada."
            )


        return analysis