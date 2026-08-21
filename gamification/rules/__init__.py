"""
Configuração centralizada da gamificação do LV Finance.

Todos os valores de XP, requisitos de nível e marcos de sequência
ficam definidos aqui. Nenhum outro módulo deve declarar valores de
XP espalhados pelo código.

A camada é 100% determinística (sem IA). O módulo
`gamification.future_ai` documenta o ponto de extensão futuro.
"""

# ---------------------------------------------------------------------------
# Níveis — XP acumulado necessário para alcançar cada nível.
# A lista deve permanecer ordenada por xp_required crescente.
# ---------------------------------------------------------------------------

LEVELS = [
    {"level": 1, "name": "Iniciante", "xp_required": 0},
    {"level": 2, "name": "Organizado", "xp_required": 100},
    {"level": 3, "name": "Controlador", "xp_required": 300},
    {"level": 4, "name": "Planejador", "xp_required": 600},
    {"level": 5, "name": "Investidor", "xp_required": 1000},
    {"level": 6, "name": "Especialista", "xp_required": 1600},
    {"level": 7, "name": "Mestre Financeiro", "xp_required": 2500},
]

# ---------------------------------------------------------------------------
# Recompensas de XP por evento.
# A chave é o event_type passado para gamification.services.handle_event.
#
# Observação: "first_transaction" substitui (não soma com)
# "transaction_created" na primeira transação do usuário.
# ---------------------------------------------------------------------------

XP_REWARDS = {
    "first_transaction": 50,
    "transaction_created": 5,
    "category_created": 10,
    "goal_created": 30,
    "goal_updated": 5,
    "goal_completed": 100,
    "month_closed": 100,
}

# ---------------------------------------------------------------------------
# Streak / sequência de acompanhamento financeiro.
# Bônus progressivo concedido UMA única vez por marco.
# ---------------------------------------------------------------------------

STREAK_MILESTONES = [7, 14, 30, 60, 90]

STREAK_BONUSES = {
    7: 20,
    14: 30,
    30: 50,
    60: 75,
    90: 100,
}

# ---------------------------------------------------------------------------
# Mecanismos anti-abuso.
# ---------------------------------------------------------------------------

# XP por atualização de meta: no máximo uma vez por dia por meta,
# evitando farm repetindo PATCHs na mesma meta.
GOAL_UPDATE_XP_COOLDOWN_DAYS = 1

# Janela (em meses) analisada para métricas de fechamento de mês.
MONTH_ANALYSIS_WINDOW = 12


def resolve_level(total_xp):
    """Retorna (nível_atual, próximo_ou_None) a partir do XP total."""
    current = LEVELS[0]
    next_level = None

    for entry in LEVELS:
        if total_xp >= entry["xp_required"]:
            current = entry
        else:
            next_level = entry
            break

    return current, next_level


def level_progress(total_xp):
    """Calcula o progresso do usuário dentro do nível atual."""
    current, next_level = resolve_level(total_xp)
    base_xp = current["xp_required"]
    xp_in_level = total_xp - base_xp

    if next_level is None:
        return {
            "level": current["level"],
            "level_name": current["name"],
            "level_xp": xp_in_level,
            "xp_for_next_level": None,
            "next_level_name": None,
            "progress_percent": 100,
        }

    span = next_level["xp_required"] - base_xp
    percent = int((xp_in_level / span) * 100) if span > 0 else 100

    return {
        "level": current["level"],
        "level_name": current["name"],
        "level_xp": xp_in_level,
        "xp_for_next_level": next_level["xp_required"] - total_xp,
        "next_level_name": next_level["name"],
        "progress_percent": min(100, max(0, percent)),
    }
