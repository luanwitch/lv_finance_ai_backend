from django.conf import settings
from django.db import models


class Category(models.Model):

    TYPE_CHOICES = (
        ("income", "Receita"),
        ("expense", "Despesa"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )

    name = models.CharField(
        max_length=80,
    )

    icon = models.CharField(
        max_length=40,
        default="wallet",
    )

    color = models.CharField(
        max_length=20,
        default="#6366F1",
    )

    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = ["name"]

        unique_together = ("user", "name")

        indexes = [
        models.Index(fields=["user"]),
        models.Index(fields=["type"]),
    ]

    def __str__(self):
        return f"{self.name} ({self.type})"
# Create your models here.
