"""Esquemas Pydantic: o formato que a IA deve devolver e o formato da API."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ItemNota(BaseModel):
    descricao: str
    quantidade: Decimal = Field(gt=0)
    valor_unitario: Decimal = Field(ge=0)
    valor_total: Decimal = Field(ge=0)


class NotaFiscalExtraida(BaseModel):
    """Campos que o extrator (LLM) precisa preencher a partir do documento."""

    emitente_nome: str
    emitente_cnpj: str = Field(description="CNPJ do emitente, só dígitos ou formatado")
    numero: str
    data_emissao: date
    valor_total: Decimal = Field(ge=0)
    itens: list[ItemNota] = Field(default_factory=list)


class DocumentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_arquivo: str
    status: str
    dados: NotaFiscalExtraida | None
    inconsistencias: list[str]
    criado_em: datetime
