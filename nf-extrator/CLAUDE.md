# Instruções para agentes de código

## Projeto
API FastAPI que extrai dados de notas fiscais com LLM, valida com regras de negócio e salva no PostgreSQL.

## Comandos
- Testes: `pytest`
- Lint: `ruff check .` (corrigir com `ruff check --fix .`)
- Subir tudo: `docker compose up --build`

## Regras
- Todo resultado de LLM passa por `app/validacao.py` antes de ser marcado como `processado`. Nunca pule a validação.
- Testes não chamam APIs externas: use `ExtratorFalso` de `tests/conftest.py`.
- Valores monetários sempre como `Decimal`, nunca `float`.
- Nova regra de validação = novo teste em `tests/test_validacao.py` com um caso que passa e um que falha.
- Antes de concluir uma tarefa: `ruff check .` e `pytest` precisam passar.
- Código, mensagens de erro e commits em português.
