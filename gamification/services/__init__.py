"""
Camada de serviços da gamificação.

A fachada pública para o restante do sistema é:

    from gamification.services import handle_event, run_periodic_checks

Todas as regras são determinísticas (sem IA). O ponto de extensão
para uma futura camada de IA está documentado em
`gamification/future_ai/__init__.py`.
"""

from .gamification_service import (
    EVENT_CATEGORY_CREATED,
    EVENT_GOAL_COMPLETED,
    EVENT_GOAL_CREATED,
    EVENT_GOAL_UPDATED,
    EVENT_TRANSACTION_CREATED,
    handle_event,
    run_periodic_checks,
)

__all__ = [
    "handle_event",
    "run_periodic_checks",
    "EVENT_CATEGORY_CREATED",
    "EVENT_GOAL_COMPLETED",
    "EVENT_GOAL_CREATED",
    "EVENT_GOAL_UPDATED",
    "EVENT_TRANSACTION_CREATED",
]
