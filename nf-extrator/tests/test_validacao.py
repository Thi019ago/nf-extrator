from datetime import date
from decimal import Decimal

import pytest

from app.schemas import ItemNota
from app.validacao import cnpj_valido, verificar
from tests.conftest import nota_exemplo


@pytest.mark.parametrize("cnpj", ["11.222.333/0001-81", "11222333000181", "45.997.418/0001-53"])
def test_cnpj_valido(cnpj):
    assert cnpj_valido(cnpj)


@pytest.mark.parametrize("cnpj", ["11.222.333/0001-82", "11111111111111", "123", ""])
def test_cnpj_invalido(cnpj):
    assert not cnpj_valido(cnpj)


def test_nota_correta_nao_tem_inconsistencias():
    assert verificar(nota_exemplo(), hoje=date(2026, 11, 10)) == []


def test_soma_dos_itens_diferente_do_total():
    problemas = verificar(nota_exemplo(valor_total=Decimal("40.00")), hoje=date(2026, 11, 10))
    assert len(problemas) == 1
    assert "Soma dos itens (35.00)" in problemas[0]


def test_item_com_conta_errada():
    item_errado = ItemNota(descricao="Caderno", quantidade=Decimal("2"),
                           valor_unitario=Decimal("12.50"), valor_total=Decimal("30.00"))
    nota = nota_exemplo(itens=[item_errado], valor_total=Decimal("30.00"))
    problemas = verificar(nota, hoje=date(2026, 11, 10))
    assert any("Item 1 (Caderno)" in p for p in problemas)


def test_data_no_futuro_e_cnpj_invalido():
    nota = nota_exemplo(data_emissao=date(2030, 1, 1), emitente_cnpj="00.000.000/0000-01")
    problemas = verificar(nota, hoje=date(2026, 11, 10))
    assert len(problemas) == 2
