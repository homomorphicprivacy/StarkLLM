"""add knowledge_base_folders and knowledge_base_documents tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-07

Adds the full-lifecycle Knowledge Base tables:
  - knowledge_base_folders  (per-user registered folders with is_active flag)
  - knowledge_base_documents (per-file indexing state, chunk counts, error tracking)

These tables complement the lighter-weight kb_folders/kb_files tables (0001)
and are designed to back the full "My Knowledge Base" UI feature with richer
status tracking and per-document chunk counts.

This migration is idempotent: if the tables already exist they are skipped.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# ---------------------------------------------------------------------------
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# ---------------------------------------------------------------------------


def upgrade() -> None:
    bind = op.get_bind()
    existing = inspect(bind).get_table_names()

    # knowledge_base_folders
    if "knowledge_base_folders" not in existing:
        op.create_table(
            "knowledge_base_folders",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("folder_path", sa.String(), nullable=False),
            sa.Column("folder_name", sa.String(), nullable=False),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("last_indexed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_knowledge_base_folders_id", "knowledge_base_folders", ["id"], unique=False)
        op.create_index("ix_knowledge_base_folders_user_id", "knowledge_base_folders", ["user_id"], unique=False)

    # knowledge_base_documents
    if "knowledge_base_documents" not in existing:
        op.create_table(
            "knowledge_base_documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "folder_id",
                sa.Integer(),
                sa.ForeignKey("knowledge_base_folders.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("file_path", sa.String(), nullable=False),
            sa.Column("file_name", sa.String(), nullable=False),
            sa.Column("file_type", sa.String(), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("last_modified", sa.DateTime(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("indexed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_knowledge_base_documents_id", "knowledge_base_documents", ["id"], unique=False)
        op.create_index("ix_knowledge_base_documents_folder_id", "knowledge_base_documents", ["folder_id"], unique=False)
        op.create_index("ix_knowledge_base_documents_file_path", "knowledge_base_documents", ["file_path"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_knowledge_base_documents_file_path", table_name="knowledge_base_documents")
    op.drop_index("ix_knowledge_base_documents_folder_id", table_name="knowledge_base_documents")
    op.drop_index("ix_knowledge_base_documents_id", table_name="knowledge_base_documents")
    op.drop_table("knowledge_base_documents")
    op.drop_index("ix_knowledge_base_folders_user_id", table_name="knowledge_base_folders")
    op.drop_index("ix_knowledge_base_folders_id", table_name="knowledge_base_folders")
    op.drop_table("knowledge_base_folders")
