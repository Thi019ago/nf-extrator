"""Extração de campos de notas fiscais com LLM multimodal.

O Gemini lê PDF e imagem diretamente (faz o papel do OCR) e devolve JSON no
formato de `NotaFiscalExtraida`. A interface `Extrator` permite trocar o
modelo (ou usar um extrator falso nos testes) sem mexer na API.
"""

import os
from typing import Protocol

from app.schemas import NotaFiscalExtraida

TIPOS_ACEITOS = {"application/pdf", "image/png", "image/jpeg", "image/webp"}

PROMPT = """Você recebe uma nota fiscal brasileira (NF-e/DANFE, NFS-e ou cupom).
Extraia os campos pedidos no esquema JSON.
- Datas no formato AAAA-MM-DD.
- Valores numéricos com ponto decimal, sem "R$".
- Se um item não tiver quantidade explícita, use 1.
- Não invente dados: copie o que está no documento."""


class ErroExtracao(Exception):
    pass


class Extrator(Protocol):
    def extrair(self, conteudo: bytes, mime_type: str) -> NotaFiscalExtraida: ...


class ExtratorGemini:
    def __init__(self, api_key: str | None = None, modelo: str | None = None):
        from google import genai  # import tardio: os testes não precisam da lib

        chave = api_key or os.environ.get("GEMINI_API_KEY")
        if not chave:
            raise ErroExtracao("Defina a variável de ambiente GEMINI_API_KEY")
        self._client = genai.Client(api_key=chave)
        self._modelo = modelo or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    def extrair(self, conteudo: bytes, mime_type: str) -> NotaFiscalExtraida:
        from google.genai import types

        resposta = self._client.models.generate_content(
            model=self._modelo,
            contents=[types.Part.from_bytes(data=conteudo, mime_type=mime_type), PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=NotaFiscalExtraida,
                temperature=0,
            ),
        )
        if resposta.parsed is None:
            raise ErroExtracao("O modelo não devolveu um JSON válido")
        return resposta.parsed
