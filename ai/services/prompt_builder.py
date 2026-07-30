from ai.memory.memory_service import MemoryService

class PromptBuilder:

    @staticmethod
    def build(context):

        memory_context = MemoryService.get_context(
                    context.user,
                    "análise financeira do usuário"
                )

        income = sum(

            transaction.amount

            for transaction in context.transactions

            if transaction.type == "income"

        )

        expense = sum(

            transaction.amount

            for transaction in context.transactions

            if transaction.type == "expense"

        )

        balance = income - expense

        prompt = f"""
Você é um consultor financeiro profissional.

Analise os dados abaixo.

Receita:
{income}

Despesa:
{expense}

Saldo:
{balance}

Quantidade de metas:
{len(context.goals)}

Quantidade de investimentos:
{len(context.investments)}

Memórias importantes do usuário:

{memory_context}

Considere essas memórias como fatos importantes sobre o usuário.

Forneça:

1. Resumo financeiro

2. Pontos positivos

3. Pontos negativos

4. Três recomendações PERSONALIZADAS considerando também as memórias.

Responda em português.
"""

        return prompt