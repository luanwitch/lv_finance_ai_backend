CATEGORY_MAP = {
    "salario": ("Salário", "💼", "income"),
    "alimentacao": ("Alimentação", "🍽️", "expense"),
    "transporte": ("Transporte", "🚗", "expense"),
    "moradia": ("Moradia", "🏠", "expense"),
    "saude": ("Saúde", "💊", "expense"),
    "educacao": ("Educação", "📚", "expense"),
    "lazer": ("Lazer", "🎉", "expense"),
    "investimentos": ("Investimentos", "📈", "expense"),
    "outros": ("Outros", "✨", "expense"),
}

CATEGORY_SLUGS = frozenset(CATEGORY_MAP)
