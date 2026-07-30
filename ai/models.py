from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.
class Memory(models.Model):

    MEMORY_TYPES = [
        ("goal", "Goal"),
        ("habit", "Habit"),
        ("debt", "Debt"),
        ("income", "Income"),
        ("expense", "Expense"),
        ("general", "General"),
    ]

    # Criando o relacionametno:;
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memories"
    )

    content = models.TextField()

    memory_type = models.CharField(
        max_length=20,
        choices=MEMORY_TYPES,
        default="general"
    )

    importance = models.IntegerField(
        default=5
    )

    embedding = models.JSONField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.content[:50]

class ChatMessage(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    role = models.CharField(
        max_length=20
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.message[:40]}"    