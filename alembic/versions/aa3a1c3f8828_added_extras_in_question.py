"""added extras in question

Revision ID: aa3a1c3f8828
Revises: de7da1a9196e
Create Date: 2025-05-07 19:16:21.474633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'aa3a1c3f8828'
down_revision: Union[str, None] = 'de7da1a9196e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add only the new `extras` JSONB column on questions
    op.add_column(
        'questions',
        sa.Column(
            'extras',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb")
        )
    )


def downgrade() -> None:
    # Remove the `extras` column
    op.drop_column('questions', 'extras')
