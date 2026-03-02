"""Resize embedding vector from 1536 to 384 dims for all-MiniLM-L6-v2.

Revision ID: 002
Revises: 001
Create Date: 2026-03-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector has no registered cast between different vector dimensions,
    # so ALTER COLUMN TYPE is not supported. Drop-and-recreate is the only
    # safe path. The column is nullable and currently NULL for all rows.
    op.drop_column("prompts", "embedding")
    op.add_column("prompts", sa.Column("embedding", Vector(384), nullable=True))


def downgrade() -> None:
    op.drop_column("prompts", "embedding")
    op.add_column("prompts", sa.Column("embedding", Vector(1536), nullable=True))
