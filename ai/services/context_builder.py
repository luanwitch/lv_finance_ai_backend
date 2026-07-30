from ai.services.context import AIContext

# Ajuste os imports conforme seus apps
from transactions.models import Transaction
from goals.models import Goal
from categories.models import Category

from .agents.invoice import InvoiceAgent
from .agents.debt import DebtAnalyzerAgent

class ContextBuilder:

    @classmethod
    def build(cls, user):

        transactions = Transaction.objects.filter(user=user)

        goals = Goal.objects.filter(
            user=user
        )

        categories = Category.objects.filter(
            user=user
        )

        return AIContext(
            user=user,
            transactions=transactions,
            goals=goals,
            categories=categories,
            debts=[],
            invoices=[],
            investments=[],
        )