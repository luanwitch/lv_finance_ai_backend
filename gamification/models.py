from django.conf import settings
from django.db import models

from .achievements import ACHIEVEMENT_CATEGORIES


class UserGamification(models.Model):
    """Perfil de gamificação de um usuário (XP, streak e contadores)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gamification",
    )

    total_xp = models.PositiveIntegerField(
        default=0,
    )

    current_streak = models.PositiveIntegerField(
        default=0,
    )

    longest_streak = models.PositiveIntegerField(
        default=0,
    )

    last_activity_date = models.DateField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        verbose_name = "Gamificação do usuário"
        verbose_name_plural = "Gamificações dos usuários"

    def __str__(self):

        return f"Gamificação de {self.user_id}"


class Achievement(models.Model):
    """Catálogo de conquistas — espelho consultável das definições em
    gamification/achievements/__init__.py (fonte da verdade)."""

    code = models.SlugField(
        max_length=80,
        unique=True,
    )

    name = models.CharField(
        max_length=120,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    icon = models.CharField(
        max_length=16,
        default="🏆",
    )

    category = models.CharField(
        max_length=40,
        choices=ACHIEVEMENT_CATEGORIES,
    )

    metric = models.CharField(
        max_length=60,
    )

    threshold = models.PositiveIntegerField(
        default=1,
    )

    xp_reward = models.PositiveIntegerField(
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = ["category", "threshold"]

    def __str__(self):

        return self.name


class UserAchievement(models.Model):
    """Conquista desbloqueada por um usuário."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_achievements",
    )

    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="unlocked_by",
    )

    unlocked_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = ["-unlocked_at"]

        unique_together = ("user", "achievement")

        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self):

        return f"{self.user_id} -> {self.achievement.code}"


class XPTransaction(models.Model):
    """Histórico imutável de alterações de XP.

    O `idempotency_key` único garante que a mesma recompensa nunca seja
    concedida duas vezes, mesmo sob requisições concorrentes.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="xp_transactions",
    )

    amount = models.IntegerField()

    reason = models.CharField(
        max_length=200,
    )

    event_type = models.CharField(
        max_length=60,
    )

    related_object_type = models.CharField(
        max_length=60,
        blank=True,
        default="",
    )

    related_object_id = models.BigIntegerField(
        null=True,
        blank=True,
    )

    idempotency_key = models.CharField(
        max_length=220,
        unique=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["event_type"]),
        ]

    def __str__(self):

        return f"{self.amount:+d} XP ({self.event_type})"


class Challenge(models.Model):
    """Catálogo de desafios — espelho das definições em
    gamification/challenges/__init__.py (fonte da verdade)."""

    code = models.SlugField(
        max_length=80,
        unique=True,
    )

    name = models.CharField(
        max_length=120,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    icon = models.CharField(
        max_length=16,
        default="🎯",
    )

    metric = models.CharField(
        max_length=60,
    )

    target = models.PositiveIntegerField()

    xp_reward = models.PositiveIntegerField(
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = ["target"]

    def __str__(self):

        return self.name


class UserChallenge(models.Model):
    """Progresso de um usuário em um desafio."""

    STATUS_CHOICES = (
        ("active", "Em andamento"),
        ("completed", "Concluído"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_challenges",
    )

    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name="progress_of",
    )

    progress = models.PositiveIntegerField(
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = ["status", "challenge__target"]

        unique_together = ("user", "challenge")

        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self):

        return f"{self.user_id} -> {self.challenge.code} ({self.progress}/{self.challenge.target})"
