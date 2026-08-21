"""Avaliação e progresso de desafios.

Os desafios são fixos (definidos em gamification/challenges) e seu
progresso é derivado das mesmas métricas determinísticas das
conquistas. A conclusão concede XP uma única vez (idempotência por
chave única no XPTransaction + status do UserChallenge).
"""

import logging

from django.db import IntegrityError
from django.utils import timezone

from ..models import Challenge, UserChallenge
from .xp_service import award_xp

logger = logging.getLogger(__name__)

CHALLENGE_COMPLETED_EVENT = "challenge_completed"


def evaluate_challenges(user, metrics):
    """Atualiza progresso e conclui desafios quando aplicável.

    Retorna a lista das definições recém-concluídas.
    """
    from .achievement_service import sync_definitions

    sync_definitions()

    codes = [definition["code"] for definition in _active_definitions()]
    catalog = {
        challenge.code: challenge
        for challenge in Challenge.objects.filter(code__in=codes)
    }

    states = {
        user_challenge.challenge_id: user_challenge
        for user_challenge in UserChallenge.objects.filter(user=user)
    }

    newly_completed = []

    for definition in _active_definitions():
        code = definition["code"]
        challenge = catalog.get(code)
        if challenge is None:
            continue

        state = states.get(challenge.id)
        if state is None:
            try:
                state, _ = UserChallenge.objects.get_or_create(
                    user=user,
                    challenge=challenge,
                    defaults={"progress": 0},
                )
            except IntegrityError:
                continue

        if state.status == "completed":
            continue

        value = int(metrics.get(definition["metric"], 0))
        target = definition["target"]

        # O progresso é monotônico: mantém o maior valor já alcançado.
        progress = max(state.progress, min(max(0, value), target))

        min_count = definition.get("min_count")
        qualifies = value >= target
        if min_count is not None:
            base_metric = metrics.get("current_month_transactions", 0)
            qualifies = qualifies and base_metric >= min_count

        state.progress = progress

        if qualifies:
            state.status = "completed"
            state.completed_at = timezone.now()
            state.save(
                update_fields=["progress", "status", "completed_at", "updated_at"]
            )

            award_xp(
                user,
                amount=definition["xp_reward"],
                reason=f"Desafio concluído: {definition['name']}",
                event_type=CHALLENGE_COMPLETED_EVENT,
                idempotency_key=f"{CHALLENGE_COMPLETED_EVENT}:{code}:{user.pk}",
                related_object_type="challenge",
                related_object_id=challenge.pk,
            )

            newly_completed.append(definition)
        else:
            state.save(update_fields=["progress", "updated_at"])

    return newly_completed


def get_challenges_state(user):
    """Retorna [(desafio, UserChallenge|None)] ordenado por dificuldade."""
    from .achievement_service import sync_definitions

    sync_definitions()

    states = {
        user_challenge.challenge_id: user_challenge
        for user_challenge in UserChallenge.objects.filter(
            user=user
        ).select_related("challenge")
    }

    return [
        (challenge, states.get(challenge.id))
        for challenge in Challenge.objects.all().order_by("target")
    ]


def completed_count(user):
    return UserChallenge.objects.filter(user=user, status="completed").count()


def _active_definitions():
    from ..challenges import CHALLENGES

    return CHALLENGES
