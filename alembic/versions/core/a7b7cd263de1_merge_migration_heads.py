"""merge migration heads

Revision ID: a7b7cd263de1
Revises: 4e8effeb4b03, 8e48cd8452d7
Create Date: 2026-03-07 11:16:02.338291

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b7cd263de1'
down_revision: Union[str, Sequence[str], None] = ('4e8effeb4b03', '8e48cd8452d7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
