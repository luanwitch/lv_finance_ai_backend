"""Streak (sequência de acompanhamento financeiro).

Regras:
  - apenas UMA ação por dia conta: múltiplos eventos no mesmo dia não
    alteram a sequência;
  - ação em dia consecutivo incrementa a sequência;
  - qualquer lacuna reinicia a sequência em 1;
  - bônus de marco (7/14/30/60/90 dias) é concedido uma única vez.
"""

from django.utils import timezone

from ..models import XPTransaction
from ..rules import STREAK_BONUSES, STREAK_MILESTONES
from .xp_service import award_xp

STREAK_BONUS_EVENT = "streak_bonus"


def register_activity(profile, activity_date=None):
    """Registra atividade do dia e atualiza o streak.

    Retorna a lista de marcos de streak premiados nesta chamada.
    """
    user = profile.user
    today = activity_date or timezone.localdate()

    if profile.last_activity_date == today:
        return []

    if profile.last_activity_date is not None:
        delta_days = (today - profile.last_activity_date).days
        profile.current_streak = (
            profile.current_streak + 1 if delta_days == 1 else 1
        )
    else:
        profile.current_streak = 1

    profile.longest_streak = max(
        profile.longest_streak, profile.current_streak
    )
    profile.last_activity_date = today
    profile.save(
        update_fields=[
            "current_streak",
            "longest_streak",
            "last_activity_date",
            "updated_at",
        ]
    )

    return _award_due_bonuses(user, profile)


def _award_due_bonuses(user, profile):
    """Concede os bônus de marcos já alcançados e ainda não premiados."""
    eligible = [
        milestone
        for milestone in STREAK_MILESTONES
        if profile.current_streak >= milestone
    ]

    if not eligible:
        return []

    keys_by_milestone = {
        f"{STREAK_BONUS_EVENT}:{user.pk}:{milestone}": milestone
        for milestone in eligible
    }

    already_awarded = set(
        XPTransaction.objects.filter(
            user=user,
            event_type=STREAK_BONUS_EVENT,
            idempotency_key__in=list(keys_by_milestone.keys()),
        ).values_list("idempotency_key", flat=True)
    )

    awarded = []
    for key, milestone in keys_by_milestone.items():
        if key in already_awarded:
            continue

        granted = award_xp(
            user,
            amount=STREAK_BONUSES[milestone],
            reason=f"Bônus de sequência de {milestone} dias",
            event_type=STREAK_BONUS_EVENT,
            idempotency_key=key,
            related_object_type="streak_milestone",
            related_object_id=milestone,
        )

        if granted:
            awarded.append(milestone)

    return awarded
