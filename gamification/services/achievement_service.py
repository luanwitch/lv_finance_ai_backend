"""Avaliação e desbloqueio de conquistas.

As definições vivem em gamification/achievements (fonte da verdade).
O catálogo no banco é apenas um espelho consultável, sincronizado por
`sync_definitions`.
"""

import logging

from django.db import IntegrityError

from ..achievements import ACHIEVEMENTS
from ..challenges import CHALLENGES
from ..models import Achievement, Challenge, UserAchievement
from .xp_service import award_xp

logger = logging.getLogger(__name__)

ACHIEVEMENT_UNLOCKED_EVENT = "achievement_unlocked"

# Cache de processo: evita resincronizar o catálogo a cada evento.
_definitions_synced = False


def sync_definitions(force=False):
    """Sincroniza as definições de código com o banco (upsert)."""
    global _definitions_synced

    if _definitions_synced and not force:
        return

    for definition in ACHIEVEMENTS:
        Achievement.objects.update_or_create(
            code=definition["code"],
            defaults={
                "name": definition["name"],
                "description": definition["description"],
                "icon": definition["icon"],
                "category": definition["category"],
                "metric": definition["metric"],
                "threshold": definition["threshold"],
                "xp_reward": definition["xp_reward"],
            },
        )

    for definition in CHALLENGES:
        Challenge.objects.update_or_create(
            code=definition["code"],
            defaults={
                "name": definition["name"],
                "description": definition["description"],
                "icon": definition["icon"],
                "metric": definition["metric"],
                "target": definition["target"],
                "xp_reward": definition["xp_reward"],
            },
        )

    _definitions_synced = True


def evaluate_achievements(user, metrics):
    """Desbloqueia conquistas cujas condições foram atendidas.

    Retorna a lista das definições recém-desbloqueadas.
    """
    codes = [definition["code"] for definition in ACHIEVEMENTS]
    catalog = {
        achievement.code: achievement
        for achievement in Achievement.objects.filter(
            code__in=codes, is_active=True
        )
    }

    unlocked_codes = set(
        UserAchievement.objects.filter(user=user).values_list(
            "achievement__code", flat=True
        )
    )

    newly_unlocked = []

    for definition in ACHIEVEMENTS:
        code = definition["code"]

        if code in unlocked_codes:
            continue

        achievement = catalog.get(code)
        if achievement is None:
            continue

        value = metrics.get(definition["metric"], 0)
        if value < definition["threshold"]:
            continue

        try:
            _, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement,
            )
        except IntegrityError:
            # Desbloqueado concorrentemente — ignora.
            continue

        if not created:
            continue

        award_xp(
            user,
            amount=definition["xp_reward"],
            reason=f"Conquista desbloqueada: {definition['name']}",
            event_type=ACHIEVEMENT_UNLOCKED_EVENT,
            idempotency_key=f"{ACHIEVEMENT_UNLOCKED_EVENT}:{code}:{user.pk}",
            related_object_type="achievement",
            related_object_id=achievement.pk,
        )

        newly_unlocked.append(definition)

    return newly_unlocked


def get_achievements_state(user):
    """Retorna [(conquista, unlocked_at|None)] ordenado por categoria."""
    sync_definitions()

    unlocked = {
        user_achievement.achievement_id: user_achievement.unlocked_at
        for user_achievement in UserAchievement.objects.filter(
            user=user
        ).select_related("achievement")
    }

    return [
        (achievement, unlocked.get(achievement.id))
        for achievement in Achievement.objects.all().order_by(
            "category", "threshold"
        )
    ]


def unlocked_count(user):
    return UserAchievement.objects.filter(user=user).count()


def latest_unlocks(user, since=None):
    """Conquistas desbloqueadas a partir de `since` (datetime)."""
    queryset = UserAchievement.objects.filter(user=user).select_related(
        "achievement"
    )
    if since is not None:
        queryset = queryset.filter(unlocked_at__gte=since)
    return queryset.order_by("-unlocked_at")
