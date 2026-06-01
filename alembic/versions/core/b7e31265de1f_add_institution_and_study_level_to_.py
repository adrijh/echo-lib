"""add institution and study_level to campaign_details

Revision ID: b7e31265de1f
Revises: cd0478f30a03
Create Date: 2026-06-01 09:03:53.146749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e31265de1f'
down_revision: Union[str, Sequence[str], None] = 'cd0478f30a03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('campaign_details', sa.Column('institution', sa.String(), nullable=True))
    op.add_column('campaign_details', sa.Column('study_level', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('campaign_details', 'study_level')
    op.drop_column('campaign_details', 'institution')
