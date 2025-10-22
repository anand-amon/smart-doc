from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import uuid
from .database import Base

def _uuid() -> str:
    return str(uuid.uuid4())

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    stored_path: Mapped[str] = mapped_column(String, nullable=False)  # local path for dev
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    results: Mapped[list["Result"]] = relationship(
        "Result", back_populates="document", cascade="all, delete-orphan"
    )

class Result(Base):
    __tablename__ = "results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"), index=True)
    ocr_confidence: Mapped[float] = mapped_column(Float)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    api_cost: Mapped[float] = mapped_column(Float, default=0.0)
    extracted_json: Mapped[dict] = mapped_column(JSON)  # works in SQLite+Postgres
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped[Document] = relationship("Document", back_populates="results")
