from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase,Mapped, mapped_column
from pydantic import BaseModel
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    stored_path: Mapped[str]
    uploaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class DocumentCreate(BaseModel):
    filename: str



class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    content: Mapped[str]
    embedding: Mapped[list[float]] = mapped_column(Vector(3072))