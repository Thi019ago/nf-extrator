import os

# Sem DATABASE_URL (rodando local sem Docker), os testes usam SQLite em arquivo.
# No CI, a variável aponta para um PostgreSQL de verdade.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from datetime import date  # noqa: E402
from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.extrator import ErroExtracao  # noqa: E402
from app.main import app, get_extrator  # noqa: E402
from app.schemas import ItemNota, NotaFiscalExtraida  # noqa: E402


def nota_exemplo(**alteracoes) -> NotaFiscalExtraida:
    dados = dict(
        emitente_nome="Papelaria Exemplo Ltda",
        emitente_cnpj="11.222.333/0001-81",
        numero="000123",
        data_emissao=date(2026, 10, 15),
        valor_total=Decimal("35.00"),
        itens=[
            ItemNota(descricao="Caderno", quantidade=Decimal("2"),
                     valor_unitario=Decimal("12.50"), valor_total=Decimal("25.00")),
            ItemNota(descricao="Caneta", quantidade=Decimal("4"),
                     valor_unitario=Decimal("2.50"), valor_total=Decimal("10.00")),
        ],
    )
    dados.update(alteracoes)
    return NotaFiscalExtraida(**dados)


class ExtratorFalso:
    """Substitui o Gemini nos testes: sem rede, sem custo, resultado previsível."""

    def __init__(self, nota: NotaFiscalExtraida | None = None, erro: str | None = None):
        self.nota, self.erro = nota, erro

    def extrair(self, conteudo: bytes, mime_type: str) -> NotaFiscalExtraida:
        if self.erro:
            raise ErroExtracao(self.erro)
        return self.nota or nota_exemplo()


@pytest.fixture(autouse=True)
def banco_limpo():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def usar_extrator():
    def _usar(extrator):
        app.dependency_overrides[get_extrator] = lambda: extrator
    return _usar
