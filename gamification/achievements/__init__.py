"""
Catálogo de conquistas (achievements) do LV Finance.

Cada conquista é avaliada contra métricas agregadas do usuário
computadas em `gamification.services.metrics_service.compute_metrics`.

O desbloqueio ocorre quando `metrics[metric] >= threshold` e ainda
não exista UserAchievement para o par (usuário, conquista) — a
unicidade é garantida por constraint no banco.
"""

CATEGORY_FIRST_STEPS = "first_steps"
CATEGORY_ORGANIZATION = "organization"
CATEGORY_GOALS = "goals"
CATEGORY_CONSISTENCY = "consistency"
CATEGORY_CONTROL = "control"

ACHIEVEMENT_CATEGORIES = [
    (CATEGORY_FIRST_STEPS, "Primeiros passos"),
    (CATEGORY_ORGANIZATION, "Organização"),
    (CATEGORY_GOALS, "Metas"),
    (CATEGORY_CONSISTENCY, "Consistência"),
    (CATEGORY_CONTROL, "Controle financeiro"),
]

ACHIEVEMENTS = [
    # ------------------------------------------------------------------
    # Primeiros passos
    # ------------------------------------------------------------------
    {
        "code": "first_transaction",
        "name": "Primeira transação",
        "description": "Você registrou sua primeira transação.",
        "icon": "🎯",
        "category": CATEGORY_FIRST_STEPS,
        "metric": "transactions_count",
        "threshold": 1,
        "xp_reward": 25,
    },
    {
        "code": "first_category",
        "name": "Primeira categoria",
        "description": "Você criou sua primeira categoria.",
        "icon": "🗂️",
        "category": CATEGORY_FIRST_STEPS,
        "metric": "categories_count",
        "threshold": 1,
        "xp_reward": 25,
    },
    {
        "code": "first_goal",
        "name": "Primeira meta",
        "description": "Você definiu sua primeira meta financeira.",
        "icon": "🏁",
        "category": CATEGORY_FIRST_STEPS,
        "metric": "goals_count",
        "threshold": 1,
        "xp_reward": 25,
    },
    # ------------------------------------------------------------------
    # Organização
    # ------------------------------------------------------------------
    {
        "code": "transactions_10",
        "name": "10 transações registradas",
        "description": "Você registrou 10 transações.",
        "icon": "📊",
        "category": CATEGORY_ORGANIZATION,
        "metric": "transactions_count",
        "threshold": 10,
        "xp_reward": 30,
    },
    {
        "code": "transactions_50",
        "name": "50 transações registradas",
        "description": "Você registrou 50 transações.",
        "icon": "📈",
        "category": CATEGORY_ORGANIZATION,
        "metric": "transactions_count",
        "threshold": 50,
        "xp_reward": 60,
    },
    {
        "code": "transactions_100",
        "name": "100 transações registradas",
        "description": "Você registrou 100 transações.",
        "icon": "💎",
        "category": CATEGORY_ORGANIZATION,
        "metric": "transactions_count",
        "threshold": 100,
        "xp_reward": 100,
    },
    # ------------------------------------------------------------------
    # Metas
    # ------------------------------------------------------------------
    {
        "code": "goal_created",
        "name": "Criou uma meta",
        "description": "Você criou uma meta financeira.",
        "icon": "✍️",
        "category": CATEGORY_GOALS,
        "metric": "goals_count",
        "threshold": 1,
        "xp_reward": 25,
    },
    {
        "code": "goal_completed",
        "name": "Concluiu uma meta",
        "description": "Você concluiu uma meta financeira.",
        "icon": "✅",
        "category": CATEGORY_GOALS,
        "metric": "goals_completed_count",
        "threshold": 1,
        "xp_reward": 50,
    },
    {
        "code": "goals_completed_3",
        "name": "Concluiu 3 metas",
        "description": "Você concluiu 3 metas financeiras.",
        "icon": "🏅",
        "category": CATEGORY_GOALS,
        "metric": "goals_completed_count",
        "threshold": 3,
        "xp_reward": 100,
    },
    # ------------------------------------------------------------------
    # Consistência
    # ------------------------------------------------------------------
    {
        "code": "streak_7",
        "name": "7 dias acompanhando",
        "description": "Você manteve 7 dias de sequência acompanhando suas finanças.",
        "icon": "🔥",
        "category": CATEGORY_CONSISTENCY,
        "metric": "longest_streak",
        "threshold": 7,
        "xp_reward": 30,
    },
    {
        "code": "streak_30",
        "name": "30 dias acompanhando",
        "description": "Você manteve 30 dias de sequência acompanhando suas finanças.",
        "icon": "🌟",
        "category": CATEGORY_CONSISTENCY,
        "metric": "longest_streak",
        "threshold": 30,
        "xp_reward": 80,
    },
    {
        "code": "streak_90",
        "name": "90 dias acompanhando",
        "description": "Você manteve 90 dias de sequência acompanhando suas finanças.",
        "icon": "🚀",
        "category": CATEGORY_CONSISTENCY,
        "metric": "longest_streak",
        "threshold": 90,
        "xp_reward": 150,
    },
    # ------------------------------------------------------------------
    # Controle financeiro
    #
    # Definições determinísticas (proxy, pois o sistema não possui
    # orçamentos formais):
    #   - mês completo: mês fechado com ao menos 1 receita e 1
    #     despesa registradas;
    #   - mês dentro do orçamento: mês fechado em que as despesas não
    #     ultrapassaram as receitas.
    # ------------------------------------------------------------------
    {
        "code": "first_month_complete",
        "name": "Primeiro mês completo",
        "description": "Você registrou receitas e despesas em um mês completo.",
        "icon": "🗓️",
        "category": CATEGORY_CONTROL,
        "metric": "months_complete_count",
        "threshold": 1,
        "xp_reward": 50,
    },
    {
        "code": "first_month_within_budget",
        "name": "Mês dentro do orçamento",
        "description": "Suas despesas não ultrapassaram suas receitas em um mês.",
        "icon": "🧮",
        "category": CATEGORY_CONTROL,
        "metric": "months_within_budget_count",
        "threshold": 1,
        "xp_reward": 75,
    },
    {
        "code": "three_months_within_budget",
        "name": "3 meses dentro do orçamento",
        "description": "3 meses consecutivos sem gastar mais do que recebeu.",
        "icon": "🛡️",
        "category": CATEGORY_CONTROL,
        "metric": "consecutive_months_within_budget",
        "threshold": 3,
        "xp_reward": 200,
    },
]
