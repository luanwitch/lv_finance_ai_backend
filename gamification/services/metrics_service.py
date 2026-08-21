"""Cálculo de métricas agregadas usadas por conquistas e desafios.

Todas as métricas são determinísticas e derivadas exclusivamente de
dados já existentes no banco (transações, categorias, metas e perfil
de gamificação) — nada é duplicado.
"""

from datetime import date

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from categories.models import Category
from goals.models import Goal
from transactions.models import Transaction

from ..models import UserGamification
from ..rules import MONTH_ANALYSIS_WINDOW


def get_profile(user):
    """Retorna o perfil de gamificação criando-o se necessário."""
    profile, _ = UserGamification.objects.get_or_create(user=user)
    return profile


def compute_metrics(user, profile=None):
    """Computa o conjunto completo de métricas do usuário."""
    if profile is None:
        profile = get_profile(user)

    today = timezone.localdate()

    metrics = {
        "transactions_count": Transaction.objects.filter(user=user).count(),
        "categories_count": Category.objects.filter(user=user).count(),
        "goals_count": Goal.objects.filter(user=user).count(),
        "goals_completed_count": Goal.objects.filter(
            user=user, status="completed"
        ).count(),
        "current_streak": profile.current_streak,
        "longest_streak": profile.longest_streak,
    }

    metrics.update(_closed_months_metrics(user, today))
    metrics.update(_current_month_metrics(user, today))

    return metrics


def _previous_month(today):
    """Retorna (ano, mês) do mês anterior ao informado."""
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def _months_window_start(today):
    """Primeiro dia do primeiro mês da janela de análise.

    A janela cobre os últimos MONTH_ANALYSIS_WINDOW meses FECHADOS
    (o mês corrente não é incluído, pois ainda está em aberto).
    """
    year, month = today.year, today.month
    for _ in range(MONTH_ANALYSIS_WINDOW):
        year, month = _previous_month(date(year, month, 1))
    return date(year, month, 1)


def _closed_months_metrics(user, today):
    """Métricas sobre meses já fechados.

    Definições determinísticas:
      - mês completo: possui ao menos 1 receita E 1 despesa;
      - mês dentro do orçamento: despesas <= receitas, com receita
        registrada e ao menos 1 transação no mês.
    """
    window_start = _months_window_start(today)
    current_month_start = today.replace(day=1)

    rows = (
        Transaction.objects.filter(
            user=user,
            date__gte=window_start,
            date__lt=current_month_start,
        )
        .annotate(month_start=TruncMonth("date"))
        .values("month_start")
        .annotate(
            income=Sum("amount", filter=Q(type="income")),
            expense=Sum("amount", filter=Q(type="expense")),
            total=Count("id"),
        )
        .order_by("-month_start")
    )

    months_complete = 0
    months_within_budget = 0
    consecutive_within_budget = 0

    for index, row in enumerate(rows):
        income = row["income"] or 0
        expense = row["expense"] or 0
        total = row["total"] or 0

        is_complete = total > 0 and income > 0 and expense > 0
        is_within_budget = (
            total > 0
            and income > 0
            and expense <= income
        )

        if is_complete:
            months_complete += 1
        if is_within_budget:
            months_within_budget += 1

        # A sequência consecutiva só conta a partir do mês fechado
        # mais recente.
        if index == 0 and not is_within_budget:
            consecutive_within_budget = 0
        elif is_within_budget:
            consecutive_within_budget += 1

    last_row = rows.first() if rows is not None else None

    last_closed_month_key = None
    if last_row is not None:
        month_start = last_row["month_start"]
        last_closed_month_key = f"{month_start.year}-{month_start.month:02d}"

    last_closed_month_complete = bool(
        last_row
        and (last_row["total"] or 0) > 0
        and (last_row["income"] or 0) > 0
        and (last_row["expense"] or 0) > 0
    )

    return {
        "months_complete_count": months_complete,
        "months_within_budget_count": months_within_budget,
        "consecutive_months_within_budget": consecutive_within_budget,
        "last_closed_month_key": last_closed_month_key,
        "last_closed_month_complete": last_closed_month_complete,
    }


def _current_month_metrics(user, today):
    """Métricas do mês corrente (ainda em aberto)."""
    month_start = today.replace(day=1)

    queryset = Transaction.objects.filter(user=user, date__gte=month_start)
    total = queryset.count()

    # Considera categorizada a transação com FK de categoria ou com a
    # antiga coluna textual preenchida (compatibilidade com dados legados).
    categorized = queryset.filter(
        Q(category_fk__isnull=False) | ~Q(category="")
    ).count()

    ratio = int(round((categorized / total) * 100)) if total > 0 else 0

    return {
        "current_month_transactions": total,
        "current_month_categorized": categorized,
        "current_month_categorized_ratio": min(100, max(0, ratio)),
    }
