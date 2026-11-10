# NF Extrator

![CI](https://github.com/SEU_USUARIO/nf-extrator/actions/workflows/ci.yml/badge.svg)

API em **FastAPI** que recebe uma nota fiscal (PDF ou imagem), extrai os dados com um **LLM multimodal** (Gemini), **confere o resultado com regras de negócio** e salva no **PostgreSQL**.

Notas que não passam na conferência não são descartadas nem aceitas às cegas: vão para a fila de **revisão humana**, com a lista do que está errado.

```
 PDF / imagem ──► POST /documentos ──► LLM extrai campos (JSON tipado)
                                            │
                                            ▼
                              Validação determinística
                       (CNPJ, contas dos itens, soma, data)
                                            │
                     ┌──────────────────────┼─────────────────┐
                     ▼                      ▼                 ▼
               "processado"            "revisar"           "erro"
                     └──────────── PostgreSQL ───────────────┘
```

## Por que a validação importa

Um LLM pode ler um "8" como "3" ou trocar um dígito do CNPJ. Em automação contábil, um erro silencioso é pior que um erro visível. Por isso, todo resultado da IA passa por regras que não dependem de IA:

| Regra | O que pega |
|---|---|
| Dígitos verificadores do CNPJ | CNPJ lido errado |
| `quantidade × valor unitário = total do item` | número de item lido errado |
| Soma dos itens = valor total da nota | item faltando ou total errado |
| Data de emissão não pode estar no futuro | data lida errado |

## Stack

Python 3.12 · FastAPI · Pydantic · SQLAlchemy 2 · PostgreSQL 16 · Google Gemini (`google-genai`) · pytest · Ruff · Docker · GitHub Actions

## Como rodar

### Com Docker (recomendado)

```bash
cp .env.example .env          # coloque sua GEMINI_API_KEY
docker compose up --build
```

Documentação interativa: http://localhost:8000/docs

```bash
curl -F "arquivo=@minha-nota.pdf;type=application/pdf" http://localhost:8000/documentos
```

### Local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
docker compose up -d db
export GEMINI_API_KEY=...
uvicorn app.main:app --reload
```

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/documentos` | Envia PDF/PNG/JPEG/WEBP (até 10 MB), extrai, valida e salva |
| `GET` | `/documentos?status=revisar` | Lista documentos (filtro opcional: `processado`, `revisar`, `erro`) |
| `GET` | `/documentos/{id}` | Detalhe de um documento |
| `GET` | `/health` | Verificação de saúde |

Exemplo de resposta:

```json
{
  "id": 7,
  "nome_arquivo": "nota.pdf",
  "status": "revisar",
  "dados": {
    "emitente_nome": "Papelaria Exemplo Ltda",
    "emitente_cnpj": "11.222.333/0001-81",
    "numero": "000123",
    "data_emissao": "2026-10-15",
    "valor_total": "40.00",
    "itens": [{"descricao": "Caderno", "quantidade": "2", "valor_unitario": "12.50", "valor_total": "25.00"}]
  },
  "inconsistencias": ["Soma dos itens (25.00) diferente do valor total da nota (40.00)"],
  "criado_em": "2026-11-10T03:40:00Z"
}
```

## Testes

```bash
pytest            # usa SQLite se DATABASE_URL não estiver definida
DATABASE_URL=postgresql+psycopg://nf:nf@localhost:5432/nf_extrator pytest   # PostgreSQL
```

Os testes trocam o Gemini por um `ExtratorFalso` (injeção de dependência do FastAPI): rodam sem internet, sem custo e com resultado previsível. No CI (GitHub Actions) rodam contra um **PostgreSQL real**, junto com lint (Ruff) e build da imagem Docker.

## Estrutura

```
app/
  main.py        rotas FastAPI
  extrator.py    interface Extrator + implementação com Gemini
  validacao.py   regras de negócio (CNPJ, somas, datas)
  schemas.py     modelos Pydantic (formato exigido do LLM e da API)
  db.py          SQLAlchemy + modelo Documento
tests/           testes de API e de validação
```

## Próximos passos

- [ ] Extrair também impostos (ICMS, ISS) e CFOP dos itens
- [ ] Sugerir a conta contábil de cada nota (classificação de lançamentos)
- [ ] Conciliar notas com linhas de extrato bancário (OFX/CSV)
- [ ] Processamento assíncrono em fila para lotes grandes
- [ ] Migrações com Alembic

## Desenvolvimento com IA

Este projeto foi desenvolvido com apoio de **Claude Code**. O arquivo [`CLAUDE.md`](CLAUDE.md) guarda as convenções que o agente segue no repositório.
