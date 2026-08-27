"""add kb_folders and kb_files tables

Revision ID: 0001
Revises:
Create Date: 2026-07-04

This migration adds the two tables needed for the "My Knowledge Base"
personal second-brain feature.  It is written to be idempotent: if the
tables already exist (e.g. because create_all() ran first) they are
skipped rather than raising an error.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# ---------------------------------------------------------------------------
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# ---------------------------------------------------------------------------


def upgrade() -> None:
    bind = op.get_bind()
    existing = inspect(bind).get_table_names()

    # ------------------------------------------------------------------ #
    # kb_folders — one row per registered folder path per user            #
    # ------------------------------------------------------------------ #
    if "kb_folders" not in existing:
        op.create_table(
            "kb_folders",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("path", sa.String(), nullable=False),
            sa.Column("display_name", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("last_synced_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_kb_folders_user_id", "kb_folders", ["user_id"])

    # ------------------------------------------------------------------ #
    # kb_files — one row per indexed file; stores change-detection info   #
    # ------------------------------------------------------------------ #
    if "kb_files" not in existing:
        op.create_table(
            "kb_files",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "folder_id",
                sa.Integer(),
                sa.ForeignKey("kb_folders.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("filepath", sa.String(), nullable=False),
            sa.Column("filename", sa.String(), nullable=False),
            sa.Column("file_type", sa.String(), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("last_modified", sa.Float(), nullable=False),
            sa.Column("indexed_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_kb_files_folder_id", "kb_files", ["folder_id"])
        op.create_index("ix_kb_files_filepath", "kb_files", ["filepath"])


def downgrade() -> None:
    op.drop_table("kb_files")
    op.drop_table("kb_folders")
