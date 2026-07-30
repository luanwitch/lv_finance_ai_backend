from decimal import Decimal

from .base import BaseAgent


class AnomalyDetectorAgent(BaseAgent):

    name = "anomaly"
    title = "Detector de Gastos"


    def run(self, context):

        transactions = context.transactions


        expenses = [
            transaction
            for transaction in transactions
            if transaction.type == "expense"
        ]


        alerts = []

        recommendations = []


        if not expenses:

            return self.response(
                data={
                    "anomalies": []
                }
            )


        total_expense = sum(
            transaction.amount
            for transaction in expenses
        )


        average_expense = (
            total_expense / len(expenses)
        )


        anomalies = []


        for transaction in expenses:


            if transaction.amount > (
                average_expense * Decimal("2")
            ):


                difference = (
                    transaction.amount - average_expense
                )


                anomalies.append({

                    "title": transaction.title,

                    "category": transaction.category,

                    "amount": float(
                        transaction.amount
                    ),

                    "average": float(
                        average_expense
                    ),

                    "difference": float(
                        difference
                    )

                })


                alerts.append(
                    f"O gasto '{transaction.title}' está acima do seu padrão."
                )


                recommendations.append(
                    "Revise esse gasto e verifique se ele era necessário."
                )


        return self.response(

            data={
                "total_expenses": float(
                    total_expense
                ),

                "average_expense": float(
                    average_expense
                ),

                "anomalies": anomalies
            },

            alerts=alerts,

            recommendations=recommendations
        )