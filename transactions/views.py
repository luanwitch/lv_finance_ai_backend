from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import action

from rest_framework.response import Response
from django.db.models import Sum

from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ModelViewSet):

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(
        detail=False,
        methods=["get"],
        url_path="summary"
    )
    def summary(self, request):

        transactions = self.get_queryset()

        total_income = (
            transactions
            .filter(type="income")
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

        total_expense = (
            transactions
            .filter(type="expense")
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

        balance = total_income - total_expense

        return Response({
            "balance": balance,
            "income": total_income,
            "expense": total_expense,
            "transactions": transactions.count(),
        })