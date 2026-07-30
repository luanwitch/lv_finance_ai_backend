import json

from ai.memory.memory_service import MemoryService
from ai.services.memory_extractor import MemoryExtractor
from ai.services.ollama_service import OllamaService
from ai.tools.tool_executor import ToolExecutor
from transactions.models import Transaction


class ChatService:

    def chat(self, user, message):

        # Aprende antes de responder
        MemoryExtractor.process(
            user,
            message
        )

        # Busca memórias relacionadas
        memory_context = ""
        
        transactions = Transaction.objects.filter(
            user=user
        )

        income = sum(
            t.amount
            for t in transactions
            if t.is_income
        )

        expense = sum(
            t.amount
            for t in transactions
            if t.is_expense
        )

        balance = income - expense

        prompt = f""""
Você é o agente financeiro do LV Finance IA.

Sua função é conversar com o usuário e executar ações no sistema quando necessário.

A mensagem atual do usuário sempre tem prioridade sobre memórias antigas.

Analise primeiro a intenção da mensagem atual.


DADOS FINANCEIROS ATUAIS:

Receita:
{income}

Despesa:
{expense}

Saldo:
{balance}


MEMÓRIAS IMPORTANTES DO USUÁRIO:

{memory_context}


MENSAGEM ATUAL DO USUÁRIO:

{message}



FERRAMENTAS DISPONÍVEIS:

1. create_goal
2. create_transaction



===============================
REGRA PARA CRIAR METAS
===============================

Use create_goal SOMENTE quando o usuário quiser criar um objetivo financeiro.

Exemplos:

- quero juntar dinheiro
- quero economizar
- quero guardar dinheiro
- quero alcançar uma meta
- quero viajar e preciso juntar dinheiro
- quero comprar algo no futuro


Formato obrigatório:

{{
    "tool":"create_goal",
    "data":{{
        "name":"nome da meta",
        "target_amount":valor
    }},
    "answer":"mensagem de confirmação"
}}


Exemplo:

Usuário:
"Quero juntar 3000 reais para morar na Irlanda"


Resposta:

{{
    "tool":"create_goal",
    "data":{{
        "name":"Morar na Irlanda",
        "target_amount":3000
    }},
    "answer":"Criei sua meta para morar na Irlanda."
}}




===============================
REGRA PARA REGISTRAR GASTOS
===============================

Se o usuário informar que dinheiro saiu da conta, SEMPRE use create_transaction.

Nunca responda apenas conversa normal nesses casos.


Palavras e situações:

- paguei
- comprei
- gastei
- débito
- pagamento
- conta
- despesa
- custo
- boleto
- fatura


Exemplos:

"Paguei 150 reais de internet"

"Comprei um mouse por 120 reais"

"Gastei 80 reais no mercado"

"Minha conta de luz foi 200 reais"


Todas essas mensagens DEVEM gerar create_transaction.


Formato obrigatório:

{{
    "tool":"create_transaction",
    "data":{{
        "title":"nome da transação",
        "amount":valor,
        "category":"categoria",
        "type":"expense",
        "description":"detalhes da transação"
    }},
    "answer":"mensagem de confirmação"
}}


Exemplo:

Usuário:
"Paguei 150 reais de internet"


Resposta:

{{
    "tool":"create_transaction",
    "data":{{
        "title":"Internet",
        "amount":150,
        "category":"Contas",
        "type":"expense",
        "description":"Pagamento de internet"
    }},
    "answer":"Registrei sua despesa de internet."
}}


===============================
SEM AÇÃO
===============================

Se a mensagem não precisar criar ou alterar dados no sistema:


{{
    "tool":null,
    "data":null,
    "answer":"resposta normal"
}}

REGRAS FINAIS:

- Responda SOMENTE JSON válido.
- Nunca use markdown.
- Nunca use ```json.
- Nunca explique o raciocínio.
- Escolha apenas UMA ferramenta por resposta.
- Não invente ferramentas.
"""


        print("======== MENSAGEM RECEBIDA ========")
        print(message)

        print("======== PROMPT ENVIADO PARA IA ========")
        print(prompt)

        print("====================================")
        answer = OllamaService().generate(prompt)

        print("=" * 80)
        print(prompt)
        print("=" * 80)


        # Remove bloco markdown caso Ollama retorne ```json
        clean_answer = (
            answer
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )


        try:

            data = json.loads(clean_answer)

        except json.JSONDecodeError:

            return {
                "answer": answer
            }


        print("TOOL RECEBIDA:")
        print(data)


        tool_result = None


        if data.get("tool"):

            tool_result = ToolExecutor.execute(
                user,
                data["tool"],
                data["data"]
            )

            print("RESULTADO DA TOOL:")
            print(tool_result)


        return {
            "answer": data.get(
                "answer",
                ""
            ),
            "tool_result": tool_result
        }

