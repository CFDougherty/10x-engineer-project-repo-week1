"""Initial schema: collections, prompts, prompt_versions, prompt_meta, pgvector extension.

Revision ID: 001
Revises:
Create Date: 2026-02-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension — idempotent
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "collections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "prompts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "collection_id",
            sa.String(36),
            sa.ForeignKey("collections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tags", sa.ARRAY(sa.String), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("version", sa.Integer, nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "prompt_id",
            sa.String(36),
            sa.ForeignKey("prompts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("collection_id", sa.String(36), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.String), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "prompt_meta",
        sa.Column(
            "id",
            sa.String(36),
            sa.ForeignKey("prompts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("current_version", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_index("ix_prompts_collection_id", "prompts", ["collection_id"])
    op.create_index("ix_prompt_versions_prompt_id", "prompt_versions", ["prompt_id"])
    op.create_index(
        "ix_prompt_versions_prompt_id_version",
        "prompt_versions",
        ["prompt_id", "version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_prompt_versions_prompt_id_version", table_name="prompt_versions")
    op.drop_index("ix_prompt_versions_prompt_id", table_name="prompt_versions")
    op.drop_index("ix_prompts_collection_id", table_name="prompts")
    op.drop_table("prompt_meta")
    op.drop_table("prompt_versions")
    op.drop_table("prompts")
    op.drop_table("collections")
    op.execute("DROP EXTENSION IF EXISTS vector")
