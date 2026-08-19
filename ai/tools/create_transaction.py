from transactions.models import Transaction
from categories.models import Category
from django.utils import timezone


class CreateTransactionTool:

    @staticmethod
    def execute(user, data):

        category = None
        category_id = data.get("category_id")
        category_name = data.get("category", "")

        if category_id:
            category = Category.objects.filter(
                id=category_id, user=user
            ).first()
        elif category_name:
            category = Category.objects.filter(
                name__iexact=category_name, user=user
            ).first()

        transaction = Transaction.objects.create(
            user=user,
            title=data.get("title", ""),
            amount=data.get("amount", 0),
            category=category.name if category else data.get("category", ""),
            category_fk=category,
            type=data.get("type", "expense"),
            date=timezone.now().date(),
            description=data.get("description", ""),
        )

        return {
            "message": "Transação criada com sucesso",
            "transaction_id": transaction.id,
        }
