# Add active_kb_dir_ids to workspaces
"""Add active_kb_dir_ids to workspaces

Revision ID: af83b94b7635
Revises: 0003
Create Date: 2026-08-12 17:59:13.814334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af83b94b7635'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()
    if 'workspaces' in tables:
        cols = [c['name'] for c in insp.get_columns('workspaces')]
        if 'active_kb_dir_ids' not in cols:
            op.add_column('workspaces', sa.Column('active_kb_dir_ids', sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()
    if 'workspaces' in tables:
        cols = [c['name'] for c in insp.get_columns('workspaces')]
        if 'active_kb_dir_ids' in cols:
            op.drop_column('workspaces', 'active_kb_dir_ids')
