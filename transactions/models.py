from django.conf import settings
from django.db import models


class Transaction(models.Model):
    TYPE_CHOICES = (
        ("income", "Receita"),
        ("expense", "Despesa"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    title = models.CharField(
        max_length=150,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    category = models.CharField(
        max_length=60,
    )

    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
    )

    date = models.DateField()

    description = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # Adicionando indices
    class Meta:
        ordering = ["-date", "-created_at"]

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["date"]),
            models.Index(fields=["type"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.amount}"

    @property
    def is_income(self):
        return self.type == "income"

    @property
    def is_expense(self):
        return self.type == "expense"