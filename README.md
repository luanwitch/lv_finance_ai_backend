# LV Finance — Backend (Django REST)

API do app LV Finance: transações, metas, gamificação, insights e assistente IA.

## Regra de ouro: TESTE AUTOMATIZADO ≠ DESENVOLVIMENTO MANUAL

| Contexto | Banco | Garantia |
|---|---|---|
| Desenvolvimento manual (navegador/demonstrações) | **`dev.sqlite3`** (local, **PERSISTENTE**) | Nunca é apagado nem recriado; sobrevive a restarts |
| Testes automatizados (`manage.py test`) | SQLite **em memória** (`:memory:`) | Nunca toca `dev.sqlite3`, nunca cria banco de teste no Postgres/Neon |
| Produção (Render etc.) | PostgreSQL via `DATABASE_URL` | Configurado por ambiente |

### Como o banco é resolvido (`config/settings.py`)

1. Se rodando testes (`"test" in sys.argv`) → `sqlite://:memory:` **sempre**, mesmo que
   `DATABASE_URL` esteja definida no ambiente ou no `.env`.
2. Se `DATABASE_URL` estiver definida → usada via `dj_database_url`
   (produção: Postgres; dev manual: `sqlite:///dev.sqlite3`).
3. Sem nenhuma das anteriores → fallback local: `dev.sqlite3` na raiz do projeto.

> **SEPARAÇÃO DEV/PRODUÇÃO:** o `.env` local **não** contém URL de produção —
> `DATABASE_URL` fica **vazio**, então `manage.py runserver`, `migrate`, `shell`
> e demais comandos usam o **`dev.sqlite3`** isolado. A URL do Neon é definida
> apenas como variável de ambiente no painel do **Render** (`DATABASE_URL`),
> nunca no `.env`. O `start_dev.ps1` ainda garante (e bloqueia) que o banco
> efetivo seja o `dev.sqlite3` (`accounts.W001` avisa se alguém setar uma URL
> remota com `DJANGO_DEBUG=True`).

## Servidor de desenvolvimento manual

```powershell
.\start_dev.ps1              # porta 8010, aplica migrations pendentes (idempotente)
.\start_dev.ps1 -Port 8020   # outra porta
.\start_dev.ps1 -CheckOnly   # só mostra a configuração efetiva e sai
```

- O script imprime o caminho absoluto do banco efetivo antes de iniciar.
- Migrations são aplicadas de forma idempotente; o banco **não é recriado nem apagado**.
- O frontend (pasta irmã `lv_finance_ia/lv-finance-ia`) consome esta API em
  `VITE_API_URL` (padrão `http://127.0.0.1:8000/api/`; ajuste se usar outra porta).

## Arquivos de banco

| Arquivo | Papel |
|---|---|
| `dev.sqlite3` | **Banco local persistente de desenvolvimento manual. NUNCA apagar.** |
| `tmp_validation.sqlite3` | Cópia temporária usada em validações pontuais; pode ser removida manualmente quando não estiver em uso (nunca confundir com o `dev.sqlite3`). |
| `db.sqlite3` | Legado do template inicial do Django, fora de uso. |

Todos os arquivos `*.sqlite3` estão no `.gitignore` — bancos locais não vão para o git.

## Endpoints principais (prefixo `/api`)

- `auth/register/`, `auth/login/`, `auth/refresh/`, `auth/me/` (JWT SimpleJWT)
- `transactions/transactions/` (CRUD) e `transactions/transactions/summary/`
- `goals/` (CRUD)
- `gamification/profile/`, `gamification/achievements/`, `gamification/challenges/` (somente leitura)
- `health/` (checa conexão com o banco ativo)

## Validação de qualidade

### Backend (Django)

Ferramentas de quality são de **desenvolvimento** (nunca vão para produção):

```powershell
pip install -r requirements-dev.txt   # instala o Ruff (uma vez por ambiente)
```

Comandos oficiais de validação:

```powershell
ruff check .                                  # lint + qualidade do código
python manage.py test                         # suíte de testes (SQLite em memória)
python manage.py check                        # checagem de configuração do Django
python manage.py makemigrations --check --dry-run   # nenhuma migration pendente
```

> Atalho para o executável do Ruff dentro da venv: `venv\Scripts\ruff.exe check .`
> Se um comando estiver fora do `PATH`, use o caminho da venv correspondente
> (`venv\Scripts\python.exe`).

Configuração do Ruff: `pyproject.toml` (imports, pyupgrade, bugbear, simplificação;
migrations são excluídas por serem código gerado; `RUF012` é ignorado por conflitar
com padrões idiomáticos do Django/DRF, ex. `permission_classes` e `Meta`).

### Frontend (TanStack Start — pasta irmã `lv_finance_ia/lv-finance-ia`)

```powershell
npm run lint        # ESLint (configuração existente em eslint.config.js)
npm run typecheck   # tsc --noEmit
npm run test        # Vitest
npm run build       # Vite build (client + SSR + Nitro)
```

> Antes de validar, instale as dependências com `npm install` (ou `bun install`,
> se usá-los) na primeira vez.
