from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, Documento, engine, get_session
from app.extrator import TIPOS_ACEITOS, ErroExtracao, Extrator, ExtratorGemini
from app.validacao import verificar

TAMANHO_MAXIMO = 10 * 1024 * 1024  # 10 MB


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="NF Extrator",
    description="Extrai dados de notas fiscais (PDF/imagem) com IA, valida e salva no PostgreSQL.",
    version="0.1.0",
    lifespan=lifespan,
)


@lru_cache
def get_extrator() -> Extrator:
    return ExtratorGemini()


SessionDep = Annotated[Session, Depends(get_session)]
ExtratorDep = Annotated[Extrator, Depends(get_extrator)]


def _to_out(doc: Documento) -> dict:
    return {
        "id": doc.id,
        "nome_arquivo": doc.nome_arquivo,
        "status": doc.status,
        "dados": doc.dados,
        "inconsistencias": doc.inconsistencias or [],
        "criado_em": doc.criado_em,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/documentos", status_code=201)
async def enviar_documento(arquivo: UploadFile, session: SessionDep, extrator: ExtratorDep):
    if arquivo.content_type not in TIPOS_ACEITOS:
        raise HTTPException(415, f"Tipo não suportado: {arquivo.content_type}")
    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(400, "Arquivo vazio")
    if len(conteudo) > TAMANHO_MAXIMO:
        raise HTTPException(413, "Arquivo maior que 10 MB")

    doc = Documento(nome_arquivo=arquivo.filename or "sem_nome")
    try:
        nota = extrator.extrair(conteudo, arquivo.content_type)
    except ErroExtracao as e:
        doc.status, doc.dados, doc.inconsistencias = "erro", None, [str(e)]
    else:
        problemas = verificar(nota)
        doc.status = "revisar" if problemas else "processado"
        doc.dados = nota.model_dump(mode="json")
        doc.inconsistencias = problemas

    session.add(doc)
    session.commit()
    return _to_out(doc)


@app.get("/documentos")
def listar_documentos(
    session: SessionDep,
    status: Annotated[str | None, Query(pattern="^(processado|revisar|erro)$")] = None,
):
    consulta = select(Documento).order_by(Documento.id.desc())
    if status:
        consulta = consulta.where(Documento.status == status)
    return [_to_out(d) for d in session.scalars(consulta)]


@app.get("/documentos/{doc_id}")
def obter_documento(doc_id: int, session: SessionDep):
    doc = session.get(Documento, doc_id)
    if doc is None:
        raise HTTPException(404, "Documento não encontrado")
    return _to_out(doc)
