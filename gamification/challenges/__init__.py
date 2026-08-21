"""
Catálogo de desafios (challenges) do LV Finance.

Desafios são metas de curto prazo com progresso mensurável. Assim
como as conquistas, são avaliados contra as métricas de
`gamification.services.metrics_service.compute_metrics`.

O campo `metric` referencia uma chave das métricas. Opcionalmente um
desafio pode definir `min_count`: quantidade mínima de registros para
que o desafio possa ser concluído (evita conclusão trivial).
"""

CHALLENGES = [
    {
        "code": "challenge_starting",
        "name": "Começando",
        "description": "Registre suas primeiras 5 transações.",
        "icon": "🚀",
        "metric": "transactions_count",
        "target": 5,
        "xp_reward": 50,
    },
    {
        "code": "challenge_organization",
        "name": "Organização",
        "description": "Categorize todas as suas transações do mês.",
        "icon": "🗂️",
        "metric": "current_month_categorized_ratio",
        "target": 100,
        "min_count": 5,
        "xp_reward": 100,
    },
    {
        "code": "challenge_goal",
        "name": "Meta",
        "description": "Crie uma meta financeira.",
        "icon": "🎯",
        "metric": "goals_count",
        "target": 1,
        "xp_reward": 50,
    },
    {
        "code": "challenge_consistency",
        "name": "Consistência",
        "description": "Acompanhe suas finanças durante 7 dias.",
        "icon": "🔥",
        "metric": "longest_streak",
        "target": 7,
        "xp_reward": 100,
    },
]
