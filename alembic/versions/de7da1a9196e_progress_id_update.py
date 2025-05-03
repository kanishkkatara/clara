"""progress id update + selected_options to JSON

Revision ID: de7da1a9196e
Revises: 2d5f2776cf8d
Create Date: 2025-05-03 12:42:07.379755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'de7da1a9196e'
down_revision: Union[str, Sequence[str], None] = '2d5f2776cf8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    # 1️⃣ Add new UUID column
    op.add_column('user_question_progress',
        sa.Column('id_uuid', postgresql.UUID(as_uuid=True),
                  nullable=False,
                  server_default=sa.text('gen_random_uuid()'))
    )

    # 2️⃣ Drop old PK & column
    op.drop_constraint('user_question_progress_pkey',
                       'user_question_progress', type_='primary')
    op.drop_column('user_question_progress', 'id')

    # 3️⃣ Rename new column to id and set as PK
    op.alter_column('user_question_progress', 'id_uuid', new_column_name='id')
    op.create_primary_key('user_question_progress_pkey',
                          'user_question_progress', ['id'])

    # 4️⃣ Add selected_options column (Integer)
    op.add_column(
        'user_question_progress',
        sa.Column('selected_options', sa.Integer(), nullable=True)
    )

    # 5️⃣ Convert it to JSONB
    op.alter_column(
        'user_question_progress',
        'selected_options',
        existing_type=sa.INTEGER(),
        type_=postgresql.JSONB(),
        postgresql_using='to_jsonb(selected_options)',
        existing_nullable=True
    )


def downgrade() -> None:
    # 1) drop the primary key constraint on id
    op.drop_constraint(
        'user_question_progress_pkey',
        'user_question_progress',
        type_='primary'
    )

    # 2) drop the uuid id column
    op.drop_column('user_question_progress', 'id')

    # 3) add a fresh integer id column
    op.add_column(
        'user_question_progress',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False)
    )

    # 4) (re-)create the PK constraint
    op.create_primary_key(
        'user_question_progress_pkey',
        'user_question_progress',
        ['id']
    )

    # 5) revert selected_options back to INTEGER
    op.alter_column(
        'user_question_progress',
        'selected_options',
        existing_type=postgresql.JSONB(),
        type_=sa.INTEGER(),
        postgresql_using="(selected_options::text)::integer",
        existing_nullable=False
    )
