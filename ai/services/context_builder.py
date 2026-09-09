from ai.services.context import AIContext
from categories.models import Category
from goals.models import Goal

# Ajuste os imports conforme seus apps
from transactions.models import Transaction


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
