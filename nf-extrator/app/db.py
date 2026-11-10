import os
from collections.abc import Iterator
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://nf:nf@localhost:5432/nf_extrator"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Documento(Base):
    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    # processado | revisar | erro
    status: Mapped[str] = mapped_column(String(20), index=True)
    dados: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    inconsistencias: Mapped[list] = mapped_column(JSON, default=list)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
