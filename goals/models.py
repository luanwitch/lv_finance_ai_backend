from django.conf import settings
from django.db import models


class Goal(models.Model):

    STATUS_CHOICES = (
        ("active", "Ativa"),
        ("completed", "Concluída"),
        ("paused", "Pausada"),
    )


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="goals",
    )


    title = models.CharField(
        max_length=150,
    )


    description = models.TextField(
        blank=True,
    )


    target_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )


    current_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )


    deadline = models.DateField(
        null=True,
        blank=True,
    )


    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )


    created_at = models.DateTimeField(
        auto_now_add=True,
    )


    updated_at = models.DateTimeField(
        auto_now=True,
    )


    class Meta:

        ordering = [
            "deadline",
            "-created_at"
        ]

        indexes = [

            models.Index(
                fields=["user"]
            ),

            models.Index(
                fields=["status"]
            ),

        ]


    def __str__(self):

        return self.title


    @property
    def progress(self):

        if self.target_amount == 0:

            return 0


        return round(
            (
                self.current_amount /
                self.target_amount
            ) * 100,
            2
        )