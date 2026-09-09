def build_prompt(
    total_income: float,
    total_expense: float,
    balance: float,
    memory_context: str,
) -> str:
    return f"""
Você é um consultor financeiro especialista.

Dados financeiros

Receitas:
{total_income}

Despesas:
{total_expense}

Saldo:
{balance}

Informações importantes sobre o usuário:

{memory_context}

Responda de forma personalizada.
"""