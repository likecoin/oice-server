"""add is hidden to macro

Revision ID: dcd9d5f2c7
Revises: 8ca2da3be2
Create Date: 2015-09-07 19:32:20.418439

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'dcd9d5f2c7'
down_revision = '8ca2da3be2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'macro', sa.Column('is_hidden', sa.Boolean, server_default='0')
    )


def downgrade():
    op.drop_column('macro', 'is_hidden')
