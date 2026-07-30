from decimal import Decimal

from .base import BaseAgent


class BudgetPlannerAgent(BaseAgent):

    name = "budget"
    title = "Planejamento Financeiro"

    def run(self, context):

        total_income = Decimal("0.00")
        total_expense = Decimal("0.00")

        for transaction in context.transactions:

            if transaction.is_income:
                total_income += transaction.amount

            elif transaction.is_expense:
                total_expense += transaction.amount

        balance = total_income - total_expense

        if total_income > 0:
            expense_percent = round(
                (total_expense / total_income) * 100,
                2
            )
        else:
            expense_percent = 0

        return self.response(
            data={
                "income": float(total_income),
                "expense": float(total_expense),
                "balance": float(balance),
                "expense_percent": float(expense_percent)
            },
            recommendations=[
                "Tente manter seus gastos abaixo de 70% da sua renda."
            ]
        )