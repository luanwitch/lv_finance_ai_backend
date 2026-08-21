"""Orquestrador da gamificação.

Ponto ÚNICO de integração com o restante do sistema:
    handle_event(event_type, user, obj)

Chamado a partir dos hooks de transactions/categories/goals. Todas as
falhas são registradas em log e engolidas — um erro na gamificação
NUNCA deve quebrar a operação financeira original.
"""

import logging

from django.db import transaction as db_transaction
from django.utils import timezone

from ..rules import (
    GOAL_UPDATE_XP_COOLDOWN_DAYS,
    XP_REWARDS,
)
from .achievement_service import evaluate_achievements, sync_definitions
from .challenge_service import evaluate_challenges
from .metrics_service import compute_metrics, get_profile
from .streak_service import register_activity
from .xp_service import award_xp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tipos de evento
# ---------------------------------------------------------------------------

EVENT_TRANSACTION_CREATED = "transaction_created"
EVENT_FIRST_TRANSACTION = "first_transaction"
EVENT_CATEGORY_CREATED = "category_created"
EVENT_GOAL_CREATED = "goal_created"
EVENT_GOAL_UPDATED = "goal_updated"
EVENT_GOAL_COMPLETED = "goal_completed"

# Eventos que caracterizam atividade financeira para o streak.
ACTIVITY_EVENTS = frozenset(
    {
        EVENT_TRANSACTION_CREATED,
        EVENT_CATEGORY_CREATED,
        EVENT_GOAL_CREATED,
        EVENT_GOAL_UPDATED,
        EVENT_GOAL_COMPLETED,
    }
)

MONTH_CLOSED_EVENT = "month_closed"


def handle_event(event_type, user, obj=None):
    """Processa um evento do sistema e aplica as regras de gamificação."""
    try:
        with db_transaction.atomic():
            _process(event_type, user, obj)
    except Exception:
        logger.exception(
            "Falha ao processar evento de gamificação (event=%s, user=%s)",
            event_type,
            getattr(user, "pk", None),
        )


def run_periodic_checks(user):
    """Reavaliação preguiçosa (lazy) sem evento direto.

    Usado ao consultar o perfil: detecta fechamentos de mês, novas
    conquistas e desafios que dependem apenas do passar do tempo.
    """
    try:
        with db_transaction.atomic():
            sync_definitions()
            profile = get_profile(user)
            metrics = compute_metrics(user, profile)
            evaluate_achievements(user, metrics)
            evaluate_challenges(user, metrics)
            _award_month_close_if_due(user, metrics)
    except Exception:
        logger.exception(
            "Falha na reavaliação de gamificação (user=%s)",
            getattr(user, "pk", None),
        )


def _process(event_type, user, obj):
    sync_definitions()

    profile = get_profile(user)

    # 1) Atividade do dia (streak + bônus de marcos).
    if event_type in ACTIVITY_EVENTS:
        register_activity(profile)

    # 2) Métricas atualizadas (o objeto já foi persistido pelo hook).
    metrics = compute_metrics(user, profile)

    # 3) XP direto do evento — idempotente por chave única.
    _award_direct_xp(event_type, user, obj, metrics)

    # 4) Conquistas e desafios.
    evaluate_achievements(user, metrics)
    evaluate_challenges(user, metrics)

    # 5) Fechamento de mês (mês anterior completo).
    _award_month_close_if_due(user, metrics)


def _award_direct_xp(event_type, user, obj, metrics):
    """Concede o XP imediato associado ao evento, se houver."""
    object_id = getattr(obj, "pk", None)

    if event_type == EVENT_TRANSACTION_CREATED:
        # A primeira transação rende o bônus dedicado (em vez do XP
        # padrão). A chave única impede re-concessão mesmo que o
        # usuário apague tudo e recomece.
        if metrics.get("transactions_count", 0) == 1:
            award_xp(
                user,
                amount=XP_REWARDS[EVENT_FIRST_TRANSACTION],
                reason="Primeira transação registrada",
                event_type=EVENT_FIRST_TRANSACTION,
                idempotency_key=f"{EVENT_FIRST_TRANSACTION}:{user.pk}",
                related_object_type="transaction",
                related_object_id=object_id,
            )
        else:
            award_xp(
                user,
                amount=XP_REWARDS[EVENT_TRANSACTION_CREATED],
                reason="Nova transação registrada",
                event_type=EVENT_TRANSACTION_CREATED,
                idempotency_key=f"{EVENT_TRANSACTION_CREATED}:{object_id}",
                related_object_type="transaction",
                related_object_id=object_id,
            )

    elif event_type == EVENT_CATEGORY_CREATED:
        award_xp(
            user,
            amount=XP_REWARDS[EVENT_CATEGORY_CREATED],
            reason="Nova categoria criada",
            event_type=EVENT_CATEGORY_CREATED,
            idempotency_key=f"{EVENT_CATEGORY_CREATED}:{object_id}",
            related_object_type="category",
            related_object_id=object_id,
        )

    elif event_type == EVENT_GOAL_CREATED:
        award_xp(
            user,
            amount=XP_REWARDS[EVENT_GOAL_CREATED],
            reason="Nova meta financeira criada",
            event_type=EVENT_GOAL_CREATED,
            idempotency_key=f"{EVENT_GOAL_CREATED}:{object_id}",
            related_object_type="goal",
            related_object_id=object_id,
        )

    elif event_type == EVENT_GOAL_UPDATED:
        # Cooldown por meta (GOAL_UPDATE_XP_COOLDOWN_DAYS): repetir
        # atualizações dentro da mesma janela não gera XP adicional
        # (anti-abuso).
        today = timezone.localdate()
        bucket = today.toordinal() // max(1, GOAL_UPDATE_XP_COOLDOWN_DAYS)
        award_xp(
            user,
            amount=XP_REWARDS[EVENT_GOAL_UPDATED],
            reason="Meta atualizada",
            event_type=EVENT_GOAL_UPDATED,
            idempotency_key=(
                f"{EVENT_GOAL_UPDATED}:{object_id}:{bucket}"
            ),
            related_object_type="goal",
            related_object_id=object_id,
        )

    elif event_type == EVENT_GOAL_COMPLETED:
        award_xp(
            user,
            amount=XP_REWARDS[EVENT_GOAL_COMPLETED],
            reason="Meta concluída",
            event_type=EVENT_GOAL_COMPLETED,
            idempotency_key=f"{EVENT_GOAL_COMPLETED}:{object_id}",
            related_object_type="goal",
            related_object_id=object_id,
        )


def _award_month_close_if_due(user, metrics):
    """Premia o fechamento do último mês fechado com controle financeiro."""
    if not metrics.get("last_closed_month_complete"):
        return

    month_key = metrics.get("last_closed_month_key")
    if not month_key:
        return

    award_xp(
        user,
        amount=XP_REWARDS[MONTH_CLOSED_EVENT],
        reason=f"Mês {month_key} fechado com controle financeiro",
        event_type=MONTH_CLOSED_EVENT,
        idempotency_key=f"{MONTH_CLOSED_EVENT}:{user.pk}:{month_key}",
        related_object_type="month",
        related_object_id=None,
    )
