from decimal import Decimal

from transactions.models import Transaction
from ai.memory.memory_service import MemoryService

from .base import BaseAgent


class FinancialAssistantAgent(BaseAgent):

    name = "assistant"
    title = "Assistente Financeiro"

    def run(self, context):

        transactions = Transaction.objects.filter(
            user=context.user
        )

        total_income = Decimal("0.00")
        total_expense = Decimal("0.00")

        for transaction in transactions:

            if transaction.is_income:
                total_income += transaction.amount

            elif transaction.is_expense:
                total_expense += transaction.amount

       
        balance = total_income - total_expense

        memory_context = MemoryService.get_context(
            context.user,
            query="análise financeira do usuário"
        )

        print(memory_context)
        

        return self.response(
            data={
                "income": float(total_income),
                "expense": float(total_expense),
                "balance": float(balance),
                "transactions": transactions.count(),
                "memory": memory_context,
            },
            recommendations=[
                "Continue registrando suas movimentações financeiras."
            ]
        )