from decimal import Decimal

from transactions.models import Transaction
from goals.models import Goal


class ScoreCalculator:

    def calculate(self, context):

        score = 1000

        income = sum(
            transaction.amount
            for transaction in context.transactions
            if transaction.type == "income"
        )

        expense = sum(
            transaction.amount
            for transaction in context.transactions
            if transaction.type == "expense"
        )

        balance = income - expense

        if balance < 0:
            score -= 100
        else:
            score += 50

        if income > 0:

            expense_percent = (expense / income) * 100

            if expense_percent > 100:
                score -= 150

            elif expense_percent > 70:
                score -= 50

        if len(context.goals) > 0:
            score += 50

            completed = sum(
                1
                for goal in context.goals
                if goal.status == "completed"
            )

            if completed == len(context.goals):
                score += 100

        if len(context.investments) > 0:
            score += 50

        score = max(0, min(1000, int(score)))

        return score