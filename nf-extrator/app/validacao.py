"""Regras de negócio que conferem o resultado da IA.

A IA pode errar. Em vez de confiar cegamente, conferimos o que dá para conferir
com regras determinísticas e marcamos o documento para revisão humana.
"""

from datetime import date
from decimal import Decimal

from app.schemas import NotaFiscalExtraida

TOLERANCIA = Decimal("0.01")


def so_digitos(texto: str) -> str:
    return "".join(c for c in texto if c.isdigit())


def cnpj_valido(cnpj: str) -> bool:
    """Valida os dois dígitos verificadores do CNPJ."""
    d = so_digitos(cnpj)
    if len(d) != 14 or d == d[0] * 14:
        return False

    def digito(base: str, pesos: list[int]) -> str:
        resto = sum(int(n) * p for n, p in zip(base, pesos, strict=True)) % 11
        return "0" if resto < 2 else str(11 - resto)

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    dv1 = digito(d[:12], pesos1)
    dv2 = digito(d[:12] + dv1, pesos2)
    return d[12:] == dv1 + dv2


def verificar(nota: NotaFiscalExtraida, hoje: date | None = None) -> list[str]:
    """Devolve a lista de inconsistências encontradas (vazia = tudo certo)."""
    hoje = hoje or date.today()
    problemas: list[str] = []

    if not cnpj_valido(nota.emitente_cnpj):
        problemas.append(f"CNPJ do emitente inválido: {nota.emitente_cnpj}")

    if nota.data_emissao > hoje:
        problemas.append(f"Data de emissão no futuro: {nota.data_emissao.isoformat()}")

    for i, item in enumerate(nota.itens, start=1):
        esperado = item.quantidade * item.valor_unitario
        if abs(esperado - item.valor_total) > TOLERANCIA:
            problemas.append(
                f"Item {i} ({item.descricao}): quantidade x valor unitário = {esperado:.2f}, "
                f"mas o total do item é {item.valor_total:.2f}"
            )

    if nota.itens:
        soma = sum((item.valor_total for item in nota.itens), Decimal("0"))
        if abs(soma - nota.valor_total) > TOLERANCIA:
            problemas.append(
                f"Soma dos itens ({soma:.2f}) diferente do valor total da nota "
                f"({nota.valor_total:.2f})"
            )

    return problemas
