"""SQLAlchemy ORM models for PromptLab — PostgreSQL with pgvector."""

from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CollectionDB(Base):
    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    prompts: Mapped[List["PromptDB"]] = relationship(
        "PromptDB", back_populates="collection", lazy="select"
    )


class PromptDB(Base):
    __tablename__ = "prompts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    collection_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True
    )
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # pgvector: nullable groundwork — no embedding generation yet
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)

    collection: Mapped[Optional["CollectionDB"]] = relationship(
        "CollectionDB", back_populates="prompts"
    )
    versions: Mapped[List["PromptVersionDB"]] = relationship(
        "PromptVersionDB", back_populates="prompt", cascade="all, delete-orphan"
    )
    meta: Mapped[Optional["PromptMetaDB"]] = relationship(
        "PromptMetaDB", back_populates="prompt", uselist=False, cascade="all, delete-orphan"
    )


class PromptVersionDB(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    collection_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    prompt: Mapped["PromptDB"] = relationship("PromptDB", back_populates="versions")


class PromptMetaDB(Base):
    __tablename__ = "prompt_meta"

    id: Mapped[str] = mapped_column(
        String(36), ForeignKey("prompts.id", ondelete="CASCADE"), primary_key=True
    )
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    prompt: Mapped["PromptDB"] = relationship("PromptDB", back_populates="meta")
