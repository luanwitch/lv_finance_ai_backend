from rest_framework import serializers

from .models import Transaction
from categories.serializers import CategorySerializer


class TransactionSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(
        source="category_fk", read_only=True
    )

    class Meta:
        model = Transaction
        fields = (
            "id",
            "title",
            "amount",
            "category",
            "category_fk",
            "category_detail",
            "type",
            "date",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "O valor deve ser maior que zero."
            )

        return value