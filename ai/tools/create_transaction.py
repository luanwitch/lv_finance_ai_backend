from transactions.models import Transaction
from django.utils import timezone

class CreateTransactionTool:

    @staticmethod
    def execute(user, data):

        transaction = Transaction.objects.create(
            user=user,
            title=data.get["title"],
            amount=data.get["amount"],
            category=data.get(
                "category",
                "Outros"
            ),
            type=data.get["type"],

            date=timezone.now().date(),

            description=data.get(
                "description",
                ""
            )
        
        )

        return {
            "message": "Transação criada com sucesso",
            "trasaction_id": transaction.id

        }
