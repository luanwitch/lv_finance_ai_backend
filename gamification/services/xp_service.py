"""Concessão idempotente de XP.

Toda alteração de XP cria um XPTransaction com `idempotency_key`
única. Se a chave já existir, a recompensa é ignorada — o banco
garante a unicidade mesmo sob chamadas concorrentes.
"""

import logging

from django.db import IntegrityError
from django.db.models import F
from django.db import transaction as db_transaction

from ..models import UserGamification, XPTransaction

logger = logging.getLogger(__name__)


def get_profile(user):
    """Retorna (criando se necessário) o perfil de gamificação."""
    profile, _ = UserGamification.objects.get_or_create(user=user)
    return profile


def award_xp(
    user,
    *,
    amount,
    reason,
    event_type,
    idempotency_key,
    related_object_type="",
    related_object_id=None,
):
    """Concede XP ao usuário de forma idempotente.

    Retorna True quando o XP foi concedido agora e False quando a
    recompensa já havia sido registrada (chave duplicada).
    """
    if amount <= 0:
        return False

    try:
        with db_transaction.atomic():
            XPTransaction.objects.create(
                user=user,
                amount=amount,
                reason=reason,
                event_type=event_type,
                related_object_type=related_object_type or "",
                related_object_id=related_object_id,
                idempotency_key=idempotency_key,
            )

            profile = get_profile(user)
            UserGamification.objects.filter(pk=profile.pk).update(
                total_xp=F("total_xp") + amount
            )

        return True

    except IntegrityError:
        # Recompensa já concedida anteriormente — idempotência.
        logger.debug(
            "XP duplicado ignorado (key=%s, user=%s)",
            idempotency_key,
            getattr(user, "pk", None),
        )
        return False
